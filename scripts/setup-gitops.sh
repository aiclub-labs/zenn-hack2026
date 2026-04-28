#!/usr/bin/env bash
# Phase 5 of azure-setup: GitHub OIDC federation + gh variable/secret config.
# Wraps §7.1 (App Reg + federated credentials + sub RBAC) and §7.2 (gh CLI).
#
# Usage:
#   ./scripts/setup-gitops.sh <repo_owner> <repo_name>
#
# Idempotent: re-running over an existing app registration / FIC / variable is a no-op.

set -uo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <repo_owner> <repo_name>" >&2
  exit 1
fi

REPO_OWNER="$1"
REPO_NAME="$2"
REPO="$REPO_OWNER/$REPO_NAME"

APP_NAME="${APP_NAME:-ghactions-hack2026}"
LOCATION="${AZURE_LOCATION:-swedencentral}"

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }
command -v gh >/dev/null || { echo "gh CLI not found" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found" >&2; exit 1; }

SUB_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
echo "Sub: $SUB_ID  Tenant: $TENANT_ID  Repo: $REPO"

# ---------- 1. App Registration ----------
echo "==> [1/4] App Registration: $APP_NAME"
APP_ID="$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")"
if [[ -z "$APP_ID" ]]; then
  APP_ID="$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)"
  echo "    created: appId=$APP_ID"
else
  echo "    exists: appId=$APP_ID (no-op)"
fi
SP_OID="$(az ad sp list --display-name "$APP_NAME" --query "[0].id" -o tsv 2>/dev/null || echo "")"
if [[ -z "$SP_OID" ]]; then
  az ad sp create --id "$APP_ID" --only-show-errors >/dev/null
  SP_OID="$(az ad sp show --id "$APP_ID" --query id -o tsv)"
  echo "    SP created: $SP_OID"
else
  echo "    SP exists: $SP_OID (no-op)"
fi

# ---------- 2. Federated credentials ----------
echo "==> [2/4] Federated credentials (main + pull_request)"
existing_fics="$(az ad app federated-credential list --id "$APP_ID" --query "[].name" -o tsv 2>/dev/null || echo "")"

if echo "$existing_fics" | grep -qx "github-main"; then
  echo "    github-main FIC exists (no-op)"
else
  az ad app federated-credential create --id "$APP_ID" --parameters \
    "{\"name\":\"github-main\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"repo:$REPO:ref:refs/heads/main\",\"audiences\":[\"api://AzureADTokenExchange\"]}" \
    --only-show-errors >/dev/null
  echo "    github-main FIC created"
fi

if echo "$existing_fics" | grep -qx "github-pr"; then
  echo "    github-pr FIC exists (no-op)"
else
  az ad app federated-credential create --id "$APP_ID" --parameters \
    "{\"name\":\"github-pr\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"repo:$REPO:pull_request\",\"audiences\":[\"api://AzureADTokenExchange\"]}" \
    --only-show-errors >/dev/null
  echo "    github-pr FIC created"
fi

# ---------- 3. Sub-scope RBAC for the SP ----------
echo "==> [3/4] Grant Contributor + User Access Administrator on sub"
for ROLE in Contributor 'User Access Administrator'; do
  if az role assignment create \
    --assignee-object-id "$SP_OID" \
    --assignee-principal-type ServicePrincipal \
    --role "$ROLE" \
    --scope "/subscriptions/$SUB_ID" \
    --only-show-errors >/dev/null 2>&1; then
    echo "    $ROLE granted"
  else
    echo "    $ROLE may already exist (idempotent)"
  fi
done

# ---------- 4. GitHub variables + secrets ----------
echo "==> [4/4] gh variable + gh secret set"

# Variables (non-sensitive)
gh variable set AZURE_CLIENT_ID         --repo "$REPO" --body "$APP_ID"      && echo "    AZURE_CLIENT_ID set"
gh variable set AZURE_TENANT_ID         --repo "$REPO" --body "$TENANT_ID"   && echo "    AZURE_TENANT_ID set"
gh variable set AZURE_SUBSCRIPTION_ID   --repo "$REPO" --body "$SUB_ID"      && echo "    AZURE_SUBSCRIPTION_ID set"
gh variable set AZURE_LOCATION          --repo "$REPO" --body "$LOCATION"    && echo "    AZURE_LOCATION set"

# Secrets — pulled from infra/main.parameters.json if present
PARAMS="$(dirname "${BASH_SOURCE[0]}")/../infra/main.parameters.json"
if [[ -f "$PARAMS" ]]; then
  MEMBER_OIDS_JSON="$(jq -c '.parameters.memberObjectIds.value' "$PARAMS")"
  OWNER_OID="$(jq -r '.parameters.ownerObjectId.value' "$PARAMS")"
  EMAILS_JSON="$(jq -c '.parameters.budgetContactEmails.value' "$PARAMS")"

  if [[ -n "$MEMBER_OIDS_JSON" && "$MEMBER_OIDS_JSON" != "null" && "$MEMBER_OIDS_JSON" != "[]" ]]; then
    gh secret set MEMBER_OBJECT_IDS --repo "$REPO" --body "$MEMBER_OIDS_JSON" && echo "    MEMBER_OBJECT_IDS set"
  else
    echo "    MEMBER_OBJECT_IDS skipped (parameters.json empty)"
  fi
  if [[ -n "$OWNER_OID" && "$OWNER_OID" != "null" && "$OWNER_OID" != "" ]]; then
    gh secret set OWNER_OBJECT_ID --repo "$REPO" --body "$OWNER_OID" && echo "    OWNER_OBJECT_ID set"
  else
    echo "    OWNER_OBJECT_ID skipped (parameters.json empty)"
  fi
  if [[ -n "$EMAILS_JSON" && "$EMAILS_JSON" != "null" && "$EMAILS_JSON" != "[]" ]]; then
    gh secret set BUDGET_CONTACT_EMAILS --repo "$REPO" --body "$EMAILS_JSON" && echo "    BUDGET_CONTACT_EMAILS set"
  else
    echo "    BUDGET_CONTACT_EMAILS skipped (parameters.json empty)"
  fi
else
  echo "    parameters.json not found — set MEMBER_OBJECT_IDS / OWNER_OBJECT_ID / BUDGET_CONTACT_EMAILS manually with 'gh secret set'"
fi

echo
echo "GitOps setup complete."
echo "Verify:"
echo "  gh variable list --repo $REPO"
echo "  gh secret list --repo $REPO"
echo
echo "Next: open a no-op PR touching infra/main.bicep to trigger infra-ci.yml"
