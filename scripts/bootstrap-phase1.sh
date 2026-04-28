#!/usr/bin/env bash
# Phase 1 of azure-setup: the 5 imperative commands Bicep can't replace.
# Run *after* the Azure account is open and `az login` works.
#
# Usage:
#   ./scripts/bootstrap-phase1.sh <sub_id_or_name> <member1_upn> <member2_upn> <member3_upn> [<budget_email>]
#
# Outcome:
#   - subscription selected
#   - all required RPs registered (idempotent)
#   - infra/main.parameters.json populated with member objectIds + owner + budget email
#   - what-if printed for review
#
# Re-runnable: every step is idempotent.

set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 <sub_id_or_name> <m1_upn> <m2_upn> <m3_upn> [budget_email]" >&2
  exit 1
fi

SUB="$1"
M1_UPN="$2"
M2_UPN="$3"
M3_UPN="$4"
BUDGET_EMAIL="${5:-$M1_UPN}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARAMS="$REPO_ROOT/infra/main.parameters.json"
LOCATION="${AZURE_LOCATION:-swedencentral}"

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found (needed to update parameters.json)" >&2; exit 1; }

echo "==> [1/5] az login (skipped if cached)"
az account show >/dev/null 2>&1 || az login --only-show-errors

echo "==> [2/5] Select subscription: $SUB"
az account set --subscription "$SUB"
SUB_ID="$(az account show --query id -o tsv)"
echo "    subscriptionId=$SUB_ID"

echo "==> [3/5] Register resource providers (idempotent)"
for rp in Microsoft.App Microsoft.ContainerRegistry Microsoft.CognitiveServices \
          Microsoft.KeyVault Microsoft.Storage Microsoft.OperationalInsights \
          Microsoft.Insights Microsoft.ManagedIdentity Microsoft.Consumption \
          Microsoft.Authorization; do
  state="$(az provider show --namespace "$rp" --query registrationState -o tsv)"
  if [[ "$state" != "Registered" ]]; then
    echo "    registering $rp (was: $state)"
    az provider register --namespace "$rp" --only-show-errors >/dev/null
  fi
done

echo "==> [4/5] Resolve member objectIds and update parameters.json"
M1_OID="$(az ad user show --id "$M1_UPN" --query id -o tsv)"
M2_OID="$(az ad user show --id "$M2_UPN" --query id -o tsv)"
M3_OID="$(az ad user show --id "$M3_UPN" --query id -o tsv)"
echo "    $M1_UPN -> $M1_OID"
echo "    $M2_UPN -> $M2_OID"
echo "    $M3_UPN -> $M3_OID"

# By convention member 1 is the designated Owner. Override OWNER_OID env to change.
OWNER_OID="${OWNER_OID:-$M1_OID}"

tmp="$(mktemp)"
jq \
  --argjson members "$(printf '["%s","%s","%s"]' "$M1_OID" "$M2_OID" "$M3_OID")" \
  --arg owner "$OWNER_OID" \
  --argjson emails "$(printf '["%s"]' "$BUDGET_EMAIL")" \
  '
  .parameters.memberObjectIds.value = $members |
  .parameters.ownerObjectId.value = $owner |
  .parameters.budgetContactEmails.value = $emails
  ' "$PARAMS" > "$tmp"
mv "$tmp" "$PARAMS"
echo "    wrote $PARAMS"

echo "==> [5/5] What-if preview"
az deployment sub what-if \
  --location "$LOCATION" \
  --template-file "$REPO_ROOT/infra/main.bicep" \
  --parameters @"$PARAMS"

echo ""
echo "Phase 1 complete."
echo "Next: review the diff above, then run Phase 2:"
echo "  azd env new hack2026 && azd provision"
echo "  # or"
echo "  az deployment sub create -l $LOCATION -f infra/main.bicep -p @infra/main.parameters.json"
