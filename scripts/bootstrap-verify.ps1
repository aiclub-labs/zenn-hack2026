<#
.SYNOPSIS
  Verification — wraps §2.5 (subscription health + $200 credit) and §5 (post-deploy verification).

.PARAMETER Mode
  - Credit: only check signup health + $200 credit
  - PostDeploy: only check Phase 2 outputs
  - Auto (default): both, post-deploy is skipped if .azure/ doesn't exist
#>

[CmdletBinding()]
param(
  [ValidateSet('Auto','Credit','PostDeploy')]
  [string] $Mode = 'Auto'
)

$ErrorActionPreference = 'Continue'  # we want to keep going past warnings
$Project = $env:PROJECT
if (-not $Project) { $Project = 'hack2026' }
$Location = $env:AZURE_LOCATION
if (-not $Location) { $Location = 'swedencentral' }

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  Write-Error "az CLI not found on PATH"
  exit 1
}

function Write-Section($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor White }
function Write-Pass($t)    { Write-Host "PASS: $t" -ForegroundColor Green }
function Write-Fail($t)    { Write-Host "FAIL: $t" -ForegroundColor Red; throw $t }
function Write-Warn2($t)   { Write-Host "WARN: $t" -ForegroundColor Yellow }

function Test-Credit {
  Write-Section "Subscription health + `$200 credit"

  $subState = az account show --query state -o tsv 2>$null
  if (-not $subState) { Write-Fail "az account show failed — not logged in?" }
  $subName = az account show --query name -o tsv
  Write-Host "Active sub: $subName (state=$subState)"
  if ($subState -ne 'Enabled') { Write-Fail "sub state is $subState, expected Enabled" }
  Write-Pass "sub state Enabled"

  $subId = az account show --query id -o tsv
  $spendingLimit = az rest --method get `
    --url "https://management.azure.com/subscriptions/$subId`?api-version=2020-01-01" `
    --query "subscriptionPolicies.spendingLimit" -o tsv 2>$null
  if (-not $spendingLimit) { $spendingLimit = 'Unknown' }
  Write-Host "Spending limit: $spendingLimit"
  switch ($spendingLimit) {
    'On'  { Write-Pass "spending limit On (Free Trial protection active)" }
    'Off' { Write-Warn2 "spending limit Off — sub has been converted to PAYG. Card will be charged on usage." }
    default { Write-Warn2 "spending limit unknown — check portal" }
  }

  Write-Host ""
  Write-Host "Quota check (region $Location):"
  az vm list-usage --location $Location `
    --query "[?contains(name.value,'cores')].{name:name.localizedValue, current:currentValue, limit:limit}" `
    -o table 2>$null

  Write-Host ""
  Write-Host "Tenant users:"
  az ad user list --query "[?mail!=null].{upn:userPrincipalName, oid:id}" -o table
}

function Test-PostDeploy {
  Write-Section "Resource groups (tagged project=$Project)"
  $rgCount = az group list --tag "project=$Project" --query "length(@)" -o tsv 2>$null
  if (-not $rgCount) { $rgCount = '0' }
  Write-Host "Found $rgCount resource group(s)"
  az group list --tag "project=$Project" -o table 2>$null
  if ([int]$rgCount -lt 1) { Write-Fail "no RGs tagged project=$Project — has 'azd provision' run?" }
  Write-Pass "$rgCount RG(s) found"

  Write-Section "Deployment status"
  az deployment sub list `
    --query "[?starts_with(name,'$Project') || starts_with(name,'main')].{name:name, state:properties.provisioningState, ts:properties.timestamp}" `
    -o table 2>$null

  Write-Section "Key Vault"
  $kv = az keyvault list --query "[?tags.project=='$Project'].name | [0]" -o tsv 2>$null
  if (-not $kv) {
    Write-Warn2 "no KV tagged project=$Project — falling back to first KV"
    $kv = az keyvault list --query "[0].name" -o tsv 2>$null
  }
  if ($kv) {
    az keyvault show -n $kv --query "{name:name, rbac:properties.enableRbacAuthorization, softDelete:properties.enableSoftDelete}" -o json
    $kvId = az keyvault show -n $kv --query id -o tsv
    Write-Host "Role assignments on KV:"
    az role assignment list --scope $kvId `
      --query "[].{role:roleDefinitionName, principal:principalName}" -o table
    Write-Pass "KV $kv reachable"
  } else { Write-Warn2 "no Key Vault found" }

  Write-Section "Application Insights"
  $appi = az resource list --resource-type microsoft.insights/components `
    --query "[?tags.project=='$Project'].name | [0]" -o tsv 2>$null
  if ($appi) { Write-Pass "App Insights present: $appi" }
  else { Write-Warn2 "no App Insights found tagged project=$Project" }

  Write-Section "Storage Account (deny-public policy)"
  $sa = az storage account list --query "[?tags.project=='$Project'].name | [0]" -o tsv 2>$null
  if ($sa) {
    az storage account show -n $sa `
      --query "{name:name, public:allowBlobPublicAccess, https:enableHttpsTrafficOnly, tls:minimumTlsVersion}" -o json
    Write-Pass "Storage $sa configured"
  } else { Write-Warn2 "no Storage tagged project=$Project" }

  Write-Section "Container Apps Environment"
  $caeState = az containerapp env list `
    --query "[?tags.project=='$Project'].properties.provisioningState | [0]" -o tsv 2>$null
  if ($caeState) {
    Write-Host "CAE state: $caeState"
    if ($caeState -eq 'Succeeded') { Write-Pass "CAE provisioned" } else { Write-Warn2 "CAE state: $caeState" }
  } else { Write-Warn2 "no CAE found tagged project=$Project" }

  Write-Section "Budget"
  az consumption budget list `
    --query "[?contains(name,'$Project')].{name:name, amount:amount, current:currentSpend.amount}" `
    -o table 2>$null
}

switch ($Mode) {
  'Credit'      { Test-Credit }
  'PostDeploy'  { Test-PostDeploy }
  'Auto' {
    Test-Credit
    if ((Test-Path '.azure') -or (Test-Path 'scaffold/.azure')) {
      Test-PostDeploy
    } else {
      Write-Host ""
      Write-Warn2 "(skipping post-deploy checks: no .azure/ — run 'azd provision' first, or pass -Mode PostDeploy to force)"
    }
  }
}

Write-Host ""
Write-Host "Verification complete." -ForegroundColor Green
