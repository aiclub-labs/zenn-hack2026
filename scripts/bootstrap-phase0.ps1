<#
.SYNOPSIS
  Phase 0 of azure-setup — PowerShell 7+ sibling of bootstrap-phase0.sh.

.DESCRIPTION
  Wraps §2.2 (rename + tag), §2.3 (member invites), §2.4 (sub-RBAC), §2.5 (verify).
  Run after completing the signup flow (§2.1) and after `az login` works.
  Re-runnable: every step is idempotent.

.PARAMETER SubscriptionId
  Sub ID of the freshly-signed-up Free Trial subscription (or already-renamed hack2026 sub).

.PARAMETER MemberUpns
  Array of 3 member UPNs. The first is the signup account (already in tenant); 2 and 3 are invited.
  Member 1 becomes Owner on the sub; 2 and 3 become Contributors.

.PARAMETER BudgetEmail
  Email used by Phase 1 / budget Bicep module. Defaults to MemberUpns[0].

.PARAMETER Project
  Project prefix used as sub name. Defaults to "hack2026".

.PARAMETER TenantDisplayName
  Tenant display name. Defaults to "AI Club".

.EXAMPLE
  ./bootstrap-phase0.ps1 `
    -SubscriptionId 00000000-0000-0000-0000-000000000000 `
    -MemberUpns @('a@aiclub2026.onmicrosoft.com','b@...','c@...') `
    -BudgetEmail budget@aiclub2026.onmicrosoft.com
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $SubscriptionId,
  [Parameter(Mandatory)] [string[]] $MemberUpns,
  [string] $BudgetEmail,
  [string] $Project = 'hack2026',
  [string] $TenantDisplayName = 'AI Club'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($MemberUpns.Count -ne 3) {
  throw "MemberUpns must contain exactly 3 UPNs (got $($MemberUpns.Count))."
}
if (-not $BudgetEmail) { $BudgetEmail = $MemberUpns[0] }

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  throw "az CLI not found on PATH."
}

$M1_UPN = $MemberUpns[0]
$M2_UPN = $MemberUpns[1]
$M3_UPN = $MemberUpns[2]

Write-Host "==> [1/6] az login (skipped if cached)"
& az account show *> $null
if ($LASTEXITCODE -ne 0) { az login --only-show-errors | Out-Null }

Write-Host "==> [2/6] Select subscription: $SubscriptionId"
az account set --subscription $SubscriptionId
$subName = az account show --query name -o tsv
$tenantId = az account show --query tenantId -o tsv
Write-Host "    current name=$subName tenant=$tenantId"

Write-Host "==> [3/6] Rename + tag the subscription"
if ($subName -ne $Project) {
  az account update --subscription $SubscriptionId --name $Project --only-show-errors | Out-Null
  Write-Host "    renamed -> $Project"
} else {
  Write-Host "    already named $Project (no-op)"
}
az tag update --resource-id "/subscriptions/$SubscriptionId" --operation Merge `
  --tags "project=$Project" 'event=microsoft-agent-hackathon-2026' 'managedBy=bicep' `
  --only-show-errors | Out-Null
Write-Host "    tags merged"

Write-Host "==> [4/6] Rename tenant display name -> '$TenantDisplayName' (best-effort)"
$currentName = ''
try {
  $currentName = az rest --method get `
    --url "https://graph.microsoft.com/v1.0/organization/$tenantId" `
    --query displayName -o tsv 2>$null
} catch {}
if ($currentName -and $currentName -ne $TenantDisplayName) {
  $body = "{`"displayName`":`"$TenantDisplayName`"}"
  try {
    az rest --method patch `
      --url "https://graph.microsoft.com/v1.0/organization/$tenantId" `
      --headers "Content-Type=application/json" `
      --body $body | Out-Null
    Write-Host "    renamed: '$currentName' -> '$TenantDisplayName'"
  } catch {
    Write-Host "    skipped (insufficient Graph permissions; do it manually if desired)"
  }
} else {
  Write-Host "    already '$TenantDisplayName' (no-op)"
}

Write-Host "==> [5/6] Invite members 2 and 3 via Graph (idempotent)"
$existingMails = @()
try { $existingMails = az ad user list --query "[].mail" -o tsv 2>$null | Where-Object { $_ } } catch {}
foreach ($upn in @($M2_UPN, $M3_UPN)) {
  if ($existingMails -contains $upn) {
    Write-Host "    $upn already in tenant (no-op)"
    continue
  }
  $body = "{`"invitedUserEmailAddress`":`"$upn`",`"inviteRedirectUrl`":`"https://portal.azure.com`",`"sendInvitationMessage`":true}"
  try {
    # Capture the response — this tenant routinely fails to deliver invitation emails,
    # so we MUST print inviteRedeemUrl for the operator to hand-deliver (Discord DM, etc).
    $inviteResponseRaw = az rest --method post `
      --url "https://graph.microsoft.com/v1.0/invitations" `
      --headers "Content-Type=application/json" `
      --body $body
    if ($inviteResponseRaw) {
      $inviteResponse = $inviteResponseRaw | ConvertFrom-Json
      Write-Host "    invited $upn"
      Write-Host "      OID:        $($inviteResponse.invitedUser.id)"
      Write-Host "      UPN:        $($inviteResponse.invitedUser.userPrincipalName)"
      Write-Host "      RedeemURL:  $($inviteResponse.inviteRedeemUrl)"
      Write-Host "      ^ HAND-DELIVER this URL to the invitee — email delivery is unreliable in this tenant."
    } else {
      Write-Host "    invited $upn (no response payload)"
    }
  } catch {
    Write-Host "    invite failed for $upn (may already have a pending invite)"
  }
}

Write-Host "==> [6/6] Sub-scope RBAC + verify"
$m1Oid = az ad user show --id $M1_UPN --query id -o tsv 2>$null
if (-not $m1Oid) {
  Write-Host "    cannot resolve $M1_UPN — skipping RBAC"
} else {
  & az role assignment create `
    --assignee-object-id $m1Oid `
    --assignee-principal-type User `
    --role Owner `
    --scope "/subscriptions/$SubscriptionId" `
    --only-show-errors *> $null
  Write-Host "    $M1_UPN -> Owner on sub"
}

foreach ($upn in @($M2_UPN, $M3_UPN)) {
  $oid = az ad user show --id $upn --query id -o tsv 2>$null
  if (-not $oid) {
    Write-Host "    cannot resolve $upn — invitation pending. Re-run after acceptance."
    continue
  }
  & az role assignment create `
    --assignee-object-id $oid `
    --assignee-principal-type User `
    --role Contributor `
    --scope "/subscriptions/$SubscriptionId" `
    --only-show-errors *> $null
  Write-Host "    $upn -> Contributor on sub"
}

Write-Host ""
Write-Host "==> Verification:"
az account show --query "{name:name, id:id, state:state, tenant:tenantId}" -o table
Write-Host ""
Write-Host "Role assignments on /subscriptions/${SubscriptionId}:"
az role assignment list --scope "/subscriptions/$SubscriptionId" `
  --query "[].{role:roleDefinitionName, principal:principalName}" -o table
Write-Host ""
Write-Host "Users in tenant:"
az ad user list --query "[?mail!=null].{upn:userPrincipalName, oid:id, mail:mail}" -o table
Write-Host ""
Write-Host "Spending limit:"
az rest --method get `
  --url "https://management.azure.com/subscriptions/$SubscriptionId`?api-version=2020-01-01" `
  --query "{name:displayName, spendingLimit:subscriptionPolicies.spendingLimit, state:state}"

Write-Host ""
Write-Host "Phase 0 complete."
Write-Host "Budget contact email recorded for Phase 1: $BudgetEmail"
Write-Host "Next: ./scripts/bootstrap-phase1.ps1 -SubscriptionId $SubscriptionId -MemberUpns @('$M1_UPN','$M2_UPN','$M3_UPN') -BudgetEmail $BudgetEmail"
