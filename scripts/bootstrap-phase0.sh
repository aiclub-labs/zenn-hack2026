#!/usr/bin/env bash
# Phase 0 of azure-setup: post-signup tenant + sub configuration.
# Wraps §2.2 (rename + tag), §2.3 (member invites), §2.4 (sub-RBAC), §2.5 (verify).
# Run *after* completing the signup flow (§2.1) and after `az login` works.
#
# Usage:
#   ./scripts/bootstrap-phase0.sh <sub_id> <m1_upn> <m2_upn> <m3_upn> [<budget_email>]
#
# Outcome:
#   - subscription renamed to hack2026 + tagged
#   - tenant display name set to "AI Club" (best-effort)
#   - members 2 & 3 invited via Graph (member 1 is the signup account, already in tenant)
#   - sub-scope RBAC: m1 -> Owner, m2/m3 -> Contributor
#   - verification block printed
#
# Re-runnable: every step is idempotent.

set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 <sub_id> <m1_upn> <m2_upn> <m3_upn> [budget_email]" >&2
  exit 1
fi

SUB_ID="$1"
M1_UPN="$2"
M2_UPN="$3"
M3_UPN="$4"
BUDGET_EMAIL="${5:-$M1_UPN}"

PROJECT="${PROJECT:-hack2026}"
TENANT_DISPLAY_NAME="${TENANT_DISPLAY_NAME:-AI Club}"

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }

echo "==> [1/6] az login (skipped if cached)"
az account show >/dev/null 2>&1 || az login --only-show-errors

echo "==> [2/6] Select subscription: $SUB_ID"
az account set --subscription "$SUB_ID"
SUB_NAME="$(az account show --query name -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
echo "    current name=$SUB_NAME tenant=$TENANT_ID"

echo "==> [3/6] Rename + tag the subscription"
if [[ "$SUB_NAME" != "$PROJECT" ]]; then
  az account update --subscription "$SUB_ID" --name "$PROJECT" --only-show-errors >/dev/null
  echo "    renamed -> $PROJECT"
else
  echo "    already named $PROJECT (no-op)"
fi
az tag update --resource-id "/subscriptions/$SUB_ID" --operation Merge \
  --tags project="$PROJECT" event=microsoft-agent-hackathon-2026 managedBy=bicep \
  --only-show-errors >/dev/null
echo "    tags merged"

echo "==> [4/6] Rename tenant display name -> '$TENANT_DISPLAY_NAME' (best-effort)"
CURRENT_TENANT_NAME="$(az rest --method get \
  --url "https://graph.microsoft.com/v1.0/organization/$TENANT_ID" \
  --query displayName -o tsv 2>/dev/null || echo "")"
if [[ "$CURRENT_TENANT_NAME" != "$TENANT_DISPLAY_NAME" && -n "$CURRENT_TENANT_NAME" ]]; then
  if az rest --method patch \
    --url "https://graph.microsoft.com/v1.0/organization/$TENANT_ID" \
    --headers "Content-Type=application/json" \
    --body "{\"displayName\":\"$TENANT_DISPLAY_NAME\"}" >/dev/null 2>&1; then
    echo "    renamed: '$CURRENT_TENANT_NAME' -> '$TENANT_DISPLAY_NAME'"
  else
    echo "    skipped (insufficient Graph permissions; do it manually if desired)"
  fi
else
  echo "    already '$TENANT_DISPLAY_NAME' (no-op)"
fi

echo "==> [5/6] Invite members 2 and 3 via Graph (idempotent)"
existing_users="$(az ad user list --query "[].mail" -o tsv 2>/dev/null || true)"
for UPN in "$M2_UPN" "$M3_UPN"; do
  if echo "$existing_users" | grep -qx "$UPN"; then
    echo "    $UPN already in tenant (no-op)"
    continue
  fi
  if az rest --method post \
    --url "https://graph.microsoft.com/v1.0/invitations" \
    --headers "Content-Type=application/json" \
    --body "{\"invitedUserEmailAddress\":\"$UPN\",\"inviteRedirectUrl\":\"https://portal.azure.com\",\"sendInvitationMessage\":true}" \
    >/dev/null 2>&1; then
    echo "    invited $UPN"
  else
    echo "    invite failed for $UPN (may already have a pending invite)"
  fi
done

echo "==> [6/6] Sub-scope RBAC + verify"
M1_OID="$(az ad user show --id "$M1_UPN" --query id -o tsv 2>/dev/null || echo "")"
if [[ -z "$M1_OID" ]]; then
  echo "    cannot resolve $M1_UPN — invitation not yet accepted? skipping RBAC"
else
  # Owner for member 1
  az role assignment create \
    --assignee-object-id "$M1_OID" \
    --assignee-principal-type User \
    --role Owner \
    --scope "/subscriptions/$SUB_ID" \
    --only-show-errors >/dev/null 2>&1 || echo "    Owner for $M1_UPN may already exist (idempotent)"
  echo "    $M1_UPN -> Owner on sub"
fi

for UPN in "$M2_UPN" "$M3_UPN"; do
  OID="$(az ad user show --id "$UPN" --query id -o tsv 2>/dev/null || echo "")"
  if [[ -z "$OID" ]]; then
    echo "    cannot resolve $UPN — invitation pending. Re-run after acceptance."
    continue
  fi
  az role assignment create \
    --assignee-object-id "$OID" \
    --assignee-principal-type User \
    --role Contributor \
    --scope "/subscriptions/$SUB_ID" \
    --only-show-errors >/dev/null 2>&1 || echo "    Contributor for $UPN may already exist (idempotent)"
  echo "    $UPN -> Contributor on sub"
done

echo ""
echo "==> Verification:"
az account show --query "{name:name, id:id, state:state, tenant:tenantId}" -o table
echo ""
echo "Role assignments on /subscriptions/$SUB_ID:"
az role assignment list --scope "/subscriptions/$SUB_ID" \
  --query "[].{role:roleDefinitionName, principal:principalName}" -o table
echo ""
echo "Users in tenant:"
az ad user list --query "[?mail!=null].{upn:userPrincipalName, oid:id, mail:mail}" -o table
echo ""
echo "Spending limit:"
az rest --method get \
  --url "https://management.azure.com/subscriptions/$SUB_ID?api-version=2020-01-01" \
  --query "{name:displayName, spendingLimit:subscriptionPolicies.spendingLimit, state:state}"

echo ""
echo "Phase 0 complete."
echo "Budget contact email recorded for Phase 1: $BUDGET_EMAIL"
echo "Next: ./scripts/bootstrap-phase1.sh $SUB_ID $M1_UPN $M2_UPN $M3_UPN $BUDGET_EMAIL"
