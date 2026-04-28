#!/usr/bin/env bash
# Teardown — wraps §9. Order matters: locks first, then resources.
#
# Usage:
#   ./scripts/teardown.sh                    # safe: prompts before each destructive step
#   ./scripts/teardown.sh --yes              # skip prompts (use only when sure)
#   ./scripts/teardown.sh --dry-run          # print what would happen, don't act
#
# Idempotent: missing resources are skipped silently.

set -uo pipefail

PROJECT="${PROJECT:-hack2026}"
LOCATION="${AZURE_LOCATION:-swedencentral}"
SHARED_RG="rg-${PROJECT}-shared"
DEV_RG="rg-${PROJECT}-dev"
PROD_RG="rg-${PROJECT}-prod"
LOCK_NAME="nodelete-shared"

YES=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES=1 ;;
    --dry-run|-n) DRY=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }

run() {
  if [[ $DRY -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

confirm() {
  if [[ $YES -eq 1 || $DRY -eq 1 ]]; then return 0; fi
  read -r -p "$1 [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

SUB_NAME="$(az account show --query name -o tsv)"
SUB_ID="$(az account show --query id -o tsv)"
echo "Active sub: $SUB_NAME ($SUB_ID)"
echo
confirm "Proceed with teardown of project='$PROJECT' on this sub?" || { echo "Aborted."; exit 0; }

echo "==> [1/5] Drop the shared-RG delete-lock"
if az lock show --name "$LOCK_NAME" -g "$SHARED_RG" >/dev/null 2>&1; then
  run "az lock delete --name '$LOCK_NAME' -g '$SHARED_RG'"
else
  echo "    no $LOCK_NAME lock on $SHARED_RG (no-op)"
fi

echo "==> [2/5] Delete + purge AOAI account (releases custom-domain reservation)"
AOAI_NAME="$(az cognitiveservices account list -g "$SHARED_RG" --query "[?kind=='OpenAI'].name | [0]" -o tsv 2>/dev/null || echo "")"
if [[ -n "$AOAI_NAME" ]]; then
  AOAI_LOC="$(az cognitiveservices account show -g "$SHARED_RG" -n "$AOAI_NAME" --query location -o tsv 2>/dev/null || echo "$LOCATION")"
  run "az cognitiveservices account delete -g '$SHARED_RG' -n '$AOAI_NAME'"
  run "az cognitiveservices account purge -l '$AOAI_LOC' -g '$SHARED_RG' -n '$AOAI_NAME'"
else
  echo "    no AOAI account in $SHARED_RG (no-op)"
fi

echo "==> [3/5] Delete resource groups"
for rg in "$DEV_RG" "$SHARED_RG" "$PROD_RG"; do
  if az group show -n "$rg" >/dev/null 2>&1; then
    run "az group delete -n '$rg' --yes --no-wait"
  else
    echo "    $rg not present (no-op)"
  fi
done

echo "==> [4/5] Wait for RG deletions to complete"
for rg in "$DEV_RG" "$SHARED_RG" "$PROD_RG"; do
  if [[ $DRY -eq 1 ]]; then
    echo "[dry-run] wait for $rg deletion"; continue
  fi
  while az group show -n "$rg" >/dev/null 2>&1; do
    echo "    waiting for $rg ..."
    sleep 15
  done
done

echo "==> [5/5] Purge soft-deleted Key Vaults"
deleted_kvs="$(az keyvault list-deleted --query "[?properties.tags.project=='$PROJECT'].name" -o tsv 2>/dev/null || echo "")"
if [[ -n "$deleted_kvs" ]]; then
  while IFS= read -r kv; do
    [[ -z "$kv" ]] && continue
    run "az keyvault purge --name '$kv' --location '$LOCATION'"
  done <<<"$deleted_kvs"
else
  echo "    no soft-deleted KVs tagged project=$PROJECT (no-op)"
fi

echo
echo "==> Verification:"
remaining_rgs="$(az group list --tag "project=$PROJECT" --query "length(@)" -o tsv 2>/dev/null || echo "0")"
remaining_kvs="$(az keyvault list-deleted --query "[?properties.tags.project=='$PROJECT'] | length(@)" -o tsv 2>/dev/null || echo "0")"
echo "  RGs remaining: $remaining_rgs (expect 0)"
echo "  Soft-deleted KVs remaining: $remaining_kvs (expect 0)"
echo
echo "Teardown complete."
echo "Reminder: any AOAI usage past PAYG conversion is now stopped — confirm card balance via portal."
