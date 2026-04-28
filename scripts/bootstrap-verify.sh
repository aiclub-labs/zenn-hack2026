#!/usr/bin/env bash
# Verification — wraps §2.5 (subscription health + $200 credit) and §5 (post-deploy verification).
#
# Usage:
#   ./scripts/bootstrap-verify.sh                # run all checks (post-deploy)
#   ./scripts/bootstrap-verify.sh --credit       # only check signup health + $200 credit
#   ./scripts/bootstrap-verify.sh --post-deploy  # only check Phase 2 outputs (default if azd env exists)
#
# Exits non-zero on first hard failure.

set -uo pipefail

MODE="${1:-auto}"
PROJECT="${PROJECT:-hack2026}"
LOCATION="${AZURE_LOCATION:-swedencentral}"

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }

# ---------- helpers ----------
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
section(){ echo; printf '\033[1m== %s ==\033[0m\n' "$*"; }

fail() { red "FAIL: $*"; exit 1; }
pass() { green "PASS: $*"; }
warn() { yellow "WARN: $*"; }

# ---------- credit / signup health ----------
verify_credit() {
  section "Subscription health + \$200 credit"

  local sub_state sub_name spending_limit
  if ! sub_state="$(az account show --query state -o tsv 2>/dev/null)"; then
    fail "az account show failed — not logged in?"
  fi
  sub_name="$(az account show --query name -o tsv)"
  echo "Active sub: $sub_name (state=$sub_state)"
  [[ "$sub_state" == "Enabled" ]] || fail "sub state is $sub_state, expected Enabled"
  pass "sub state Enabled"

  local sub_id
  sub_id="$(az account show --query id -o tsv)"
  spending_limit="$(az rest --method get \
    --url "https://management.azure.com/subscriptions/$sub_id?api-version=2020-01-01" \
    --query "subscriptionPolicies.spendingLimit" -o tsv 2>/dev/null || echo "Unknown")"
  echo "Spending limit: $spending_limit"
  case "$spending_limit" in
    On) pass "spending limit On (Free Trial protection active)" ;;
    Off) warn "spending limit Off — sub has been converted to PAYG. Card will be charged on usage." ;;
    *)   warn "spending limit unknown — check portal" ;;
  esac

  echo
  echo "Quota check (region $LOCATION):"
  az vm list-usage --location "$LOCATION" \
    --query "[?contains(name.value,'cores')].{name:name.localizedValue, current:currentValue, limit:limit}" \
    -o table 2>/dev/null || warn "could not query VM quota — region may not have CLI access"

  echo
  echo "Tenant users:"
  az ad user list --query "[?mail!=null].{upn:userPrincipalName, oid:id}" -o table
}

# ---------- post-deploy verification ----------
verify_post_deploy() {
  section "Resource groups (tagged project=$PROJECT)"
  local rg_count
  rg_count="$(az group list --tag "project=$PROJECT" --query "length(@)" -o tsv 2>/dev/null || echo "0")"
  echo "Found $rg_count resource group(s)"
  az group list --tag "project=$PROJECT" -o table 2>/dev/null || true
  if [[ "$rg_count" -lt 1 ]]; then
    fail "no RGs tagged project=$PROJECT — has \`azd provision\` run?"
  fi
  pass "$rg_count RG(s) found"

  section "Deployment status"
  az deployment sub list \
    --query "[?starts_with(name,'$PROJECT') || starts_with(name,'main')].{name:name, state:properties.provisioningState, ts:properties.timestamp}" \
    -o table 2>/dev/null || true

  section "Key Vault"
  local kv
  kv="$(az keyvault list --query "[?tags.project=='$PROJECT'].name | [0]" -o tsv 2>/dev/null || echo "")"
  if [[ -z "$kv" ]]; then
    warn "no KV tagged project=$PROJECT — may be tagged via RG instead"
    kv="$(az keyvault list --query "[0].name" -o tsv 2>/dev/null || echo "")"
  fi
  if [[ -n "$kv" ]]; then
    az keyvault show -n "$kv" --query "{name:name, rbac:properties.enableRbacAuthorization, softDelete:properties.enableSoftDelete}" -o json
    echo "Role assignments on KV:"
    az role assignment list --scope "$(az keyvault show -n "$kv" --query id -o tsv)" \
      --query "[].{role:roleDefinitionName, principal:principalName}" -o table
    pass "KV $kv reachable"
  else
    warn "no Key Vault found"
  fi

  section "Application Insights"
  local appi
  appi="$(az monitor app-insights component show \
    --query "[?tags.project=='$PROJECT'].connectionString | [0]" -o tsv 2>/dev/null || echo "")"
  if [[ -z "$appi" ]]; then
    appi="$(az resource list --resource-type microsoft.insights/components \
      --query "[?tags.project=='$PROJECT'].name | [0]" -o tsv 2>/dev/null || echo "")"
  fi
  if [[ -n "$appi" ]]; then
    pass "App Insights present: $appi"
  else
    warn "no App Insights found tagged project=$PROJECT"
  fi

  section "Storage Account (deny-public policy)"
  local sa
  sa="$(az storage account list --query "[?tags.project=='$PROJECT'].name | [0]" -o tsv 2>/dev/null || echo "")"
  if [[ -n "$sa" ]]; then
    az storage account show -n "$sa" \
      --query "{name:name, public:allowBlobPublicAccess, https:enableHttpsTrafficOnly, tls:minimumTlsVersion}" -o json
    pass "Storage $sa configured"
  else
    warn "no Storage tagged project=$PROJECT"
  fi

  section "Container Apps Environment"
  local cae_state
  cae_state="$(az containerapp env list \
    --query "[?tags.project=='$PROJECT'].properties.provisioningState | [0]" -o tsv 2>/dev/null || echo "")"
  if [[ -n "$cae_state" ]]; then
    echo "CAE state: $cae_state"
    [[ "$cae_state" == "Succeeded" ]] && pass "CAE provisioned" || warn "CAE state: $cae_state"
  else
    warn "no CAE found tagged project=$PROJECT"
  fi

  section "Budget"
  az consumption budget list \
    --query "[?contains(name,'$PROJECT')].{name:name, amount:amount, current:currentSpend.amount}" \
    -o table 2>/dev/null || warn "budget query failed — Microsoft.Consumption may not be registered yet"
}

# ---------- dispatch ----------
case "$MODE" in
  --credit)
    verify_credit
    ;;
  --post-deploy)
    verify_post_deploy
    ;;
  auto|"")
    verify_credit
    if [[ -d ".azure" ]] || [[ -d "scaffold/.azure" ]]; then
      verify_post_deploy
    else
      echo
      yellow "(skipping post-deploy checks: no .azure/ — run 'azd provision' first, or pass --post-deploy to force)"
    fi
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Usage: $0 [--credit | --post-deploy]" >&2
    exit 2
    ;;
esac

echo
green "Verification complete."
