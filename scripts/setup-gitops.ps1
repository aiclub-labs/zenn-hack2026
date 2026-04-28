<#
.SYNOPSIS
  Phase 5 of azure-setup — PowerShell 7+ sibling of setup-gitops.sh.

.DESCRIPTION
  Creates an App Registration + 2 federated credentials (main, pull_request),
  grants sub-scope Contributor + User Access Administrator on the SP,
  sets gh variables and secrets pulled from infra/main.parameters.json.
  Idempotent.

.PARAMETER RepoOwner
  GitHub repo owner (org or user).

.PARAMETER RepoName
  GitHub repo name.

.PARAMETER AppName
  Display name for the App Registration. Defaults to "ghactions-hack2026".
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $RepoOwner,
  [Parameter(Mandatory)] [string] $RepoName,
  [string] $AppName = 'ghactions-hack2026'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Location = $env:AZURE_LOCATION
if (-not $Location) { $Location = 'swedencentral' }

foreach ($cmd in @('az','gh','jq')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "$cmd not found on PATH."
  }
}

$Repo = "$RepoOwner/$RepoName"
$SubId = az account show --query id -o tsv
$TenantId = az account show --query tenantId -o tsv
Write-Host "Sub: $SubId  Tenant: $TenantId  Repo: $Repo"

# ---------- 1. App Registration ----------
Write-Host "==> [1/4] App Registration: $AppName"
$AppId = az ad app list --display-name $AppName --query "[0].appId" -o tsv 2>$null
if (-not $AppId) {
  $AppId = az ad app create --display-name $AppName --query appId -o tsv
  Write-Host "    created: appId=$AppId"
} else {
  Write-Host "    exists: appId=$AppId (no-op)"
}
$SpOid = az ad sp list --display-name $AppName --query "[0].id" -o tsv 2>$null
if (-not $SpOid) {
  az ad sp create --id $AppId --only-show-errors | Out-Null
  $SpOid = az ad sp show --id $AppId --query id -o tsv
  Write-Host "    SP created: $SpOid"
} else {
  Write-Host "    SP exists: $SpOid (no-op)"
}

# ---------- 2. Federated credentials ----------
Write-Host "==> [2/4] Federated credentials (main + pull_request)"
$existingFics = (az ad app federated-credential list --id $AppId --query "[].name" -o tsv 2>$null) -split "`n" | Where-Object { $_ }

if ($existingFics -contains 'github-main') {
  Write-Host "    github-main FIC exists (no-op)"
} else {
  $body = "{`"name`":`"github-main`",`"issuer`":`"https://token.actions.githubusercontent.com`",`"subject`":`"repo:${Repo}:ref:refs/heads/main`",`"audiences`":[`"api://AzureADTokenExchange`"]}"
  az ad app federated-credential create --id $AppId --parameters $body --only-show-errors | Out-Null
  Write-Host "    github-main FIC created"
}

if ($existingFics -contains 'github-pr') {
  Write-Host "    github-pr FIC exists (no-op)"
} else {
  $body = "{`"name`":`"github-pr`",`"issuer`":`"https://token.actions.githubusercontent.com`",`"subject`":`"repo:${Repo}:pull_request`",`"audiences`":[`"api://AzureADTokenExchange`"]}"
  az ad app federated-credential create --id $AppId --parameters $body --only-show-errors | Out-Null
  Write-Host "    github-pr FIC created"
}

# ---------- 3. Sub-scope RBAC for the SP ----------
Write-Host "==> [3/4] Grant Contributor + User Access Administrator on sub"
foreach ($role in @('Contributor','User Access Administrator')) {
  & az role assignment create `
    --assignee-object-id $SpOid `
    --assignee-principal-type ServicePrincipal `
    --role $role `
    --scope "/subscriptions/$SubId" `
    --only-show-errors *> $null
  Write-Host "    $role granted (or pre-existing — idempotent)"
}

# ---------- 4. GitHub variables + secrets ----------
Write-Host "==> [4/4] gh variable + gh secret set"

# Variables
gh variable set AZURE_CLIENT_ID       --repo $Repo --body $AppId
Write-Host "    AZURE_CLIENT_ID set"
gh variable set AZURE_TENANT_ID       --repo $Repo --body $TenantId
Write-Host "    AZURE_TENANT_ID set"
gh variable set AZURE_SUBSCRIPTION_ID --repo $Repo --body $SubId
Write-Host "    AZURE_SUBSCRIPTION_ID set"
gh variable set AZURE_LOCATION        --repo $Repo --body $Location
Write-Host "    AZURE_LOCATION set"

# Secrets from parameters.json
$paramsPath = Join-Path $PSScriptRoot '..' 'infra' 'main.parameters.json'
if (Test-Path $paramsPath) {
  $memberOidsJson = jq -c '.parameters.memberObjectIds.value' $paramsPath
  $ownerOid = jq -r '.parameters.ownerObjectId.value' $paramsPath
  $emailsJson = jq -c '.parameters.budgetContactEmails.value' $paramsPath

  if ($memberOidsJson -and $memberOidsJson -notin @('null','[]','')) {
    gh secret set MEMBER_OBJECT_IDS --repo $Repo --body $memberOidsJson
    Write-Host "    MEMBER_OBJECT_IDS set"
  } else { Write-Host "    MEMBER_OBJECT_IDS skipped (parameters.json empty)" }

  if ($ownerOid -and $ownerOid -ne 'null' -and $ownerOid -ne '') {
    gh secret set OWNER_OBJECT_ID --repo $Repo --body $ownerOid
    Write-Host "    OWNER_OBJECT_ID set"
  } else { Write-Host "    OWNER_OBJECT_ID skipped (parameters.json empty)" }

  if ($emailsJson -and $emailsJson -notin @('null','[]','')) {
    gh secret set BUDGET_CONTACT_EMAILS --repo $Repo --body $emailsJson
    Write-Host "    BUDGET_CONTACT_EMAILS set"
  } else { Write-Host "    BUDGET_CONTACT_EMAILS skipped (parameters.json empty)" }
} else {
  Write-Host "    parameters.json not found — set MEMBER_OBJECT_IDS / OWNER_OBJECT_ID / BUDGET_CONTACT_EMAILS manually"
}

Write-Host ""
Write-Host "GitOps setup complete."
Write-Host "Verify:"
Write-Host "  gh variable list --repo $Repo"
Write-Host "  gh secret list --repo $Repo"
Write-Host ""
Write-Host "Next: open a no-op PR touching infra/main.bicep to trigger infra-ci.yml"
