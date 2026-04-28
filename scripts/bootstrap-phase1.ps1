<#
.SYNOPSIS
  Phase 1 of azure-setup — PowerShell 7+ sibling of bootstrap-phase1.sh.

.DESCRIPTION
  Runs the 5 imperative commands Bicep can't replace:
    1. az login (if not cached)
    2. az account set --subscription
    3. Register all required resource providers (idempotent)
    4. Resolve member UPNs -> objectIds
    5. Patch infra/main.parameters.json (in-place)
    6. Run what-if for review

  Re-runnable: every step is idempotent.

.PARAMETER SubscriptionId
  Sub ID or name of the hackathon subscription (post-redemption).

.PARAMETER MemberUpns
  Array of 3 member UPNs. The first is treated as the Designated Owner unless -OwnerOid is supplied.

.PARAMETER BudgetEmail
  Where budget threshold alerts go. Defaults to the first member UPN.

.PARAMETER OwnerOid
  Override which member becomes Owner. Defaults to objectId of MemberUpns[0].

.PARAMETER Location
  Azure region. Defaults to swedencentral (or $env:AZURE_LOCATION if set).

.EXAMPLE
  ./bootstrap-phase1.ps1 `
    -SubscriptionId 00000000-0000-0000-0000-000000000000 `
    -MemberUpns @('a@aiclub2026.onmicrosoft.com','b@...','c@...') `
    -BudgetEmail budget@aiclub2026.onmicrosoft.com
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $SubscriptionId,
  [Parameter(Mandatory)] [string[]] $MemberUpns,
  [string] $BudgetEmail,
  [string] $OwnerOid,
  [string] $Location = $(if ($env:AZURE_LOCATION) { $env:AZURE_LOCATION } else { 'swedencentral' })
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($MemberUpns.Count -ne 3) {
  throw "MemberUpns must contain exactly 3 UPNs (got $($MemberUpns.Count))."
}
if (-not $BudgetEmail) { $BudgetEmail = $MemberUpns[0] }

foreach ($cmd in @('az','jq')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "$cmd not found on PATH. See azure-setup.md §1.3."
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$paramsPath = Join-Path $repoRoot 'infra/main.parameters.json'
if (-not (Test-Path $paramsPath)) {
  throw "Expected $paramsPath to exist (run from a clean scaffold/ checkout)."
}

Write-Host "==> [1/5] az login (skipped if cached)"
& az account show *> $null
if ($LASTEXITCODE -ne 0) { az login --only-show-errors | Out-Null }

Write-Host "==> [2/5] Select subscription: $SubscriptionId"
az account set --subscription $SubscriptionId
$subId = az account show --query id -o tsv
Write-Host "    subscriptionId=$subId"

Write-Host "==> [3/5] Register resource providers (idempotent)"
$providers = @(
  'Microsoft.App','Microsoft.ContainerRegistry','Microsoft.CognitiveServices',
  'Microsoft.KeyVault','Microsoft.Storage','Microsoft.OperationalInsights',
  'Microsoft.Insights','Microsoft.ManagedIdentity','Microsoft.Consumption',
  'Microsoft.Authorization'
)
foreach ($rp in $providers) {
  $state = az provider show --namespace $rp --query registrationState -o tsv
  if ($state -ne 'Registered') {
    Write-Host "    registering $rp (was: $state)"
    az provider register --namespace $rp --only-show-errors | Out-Null
  }
}

Write-Host "==> [4/5] Resolve member objectIds"
$memberOids = @()
foreach ($upn in $MemberUpns) {
  $oid = az ad user show --id $upn --query id -o tsv
  if (-not $oid) { throw "Could not resolve $upn — has the invitation been accepted?" }
  Write-Host "    $upn -> $oid"
  $memberOids += $oid
}
if (-not $OwnerOid) { $OwnerOid = $memberOids[0] }

# Patch parameters.json via jq for cross-platform consistency with the bash variant.
$membersJson = ($memberOids | ForEach-Object { '"' + $_ + '"' }) -join ','
$emailsJson = '"' + $BudgetEmail + '"'

$tmp = New-TemporaryFile
$jqScript = @'
.parameters.memberObjectIds.value = $members |
.parameters.ownerObjectId.value = $owner |
.parameters.budgetContactEmails.value = $emails
'@
& jq `
  --argjson members "[$membersJson]" `
  --arg owner $OwnerOid `
  --argjson emails "[$emailsJson]" `
  $jqScript $paramsPath > $tmp.FullName
if ($LASTEXITCODE -ne 0) { throw "jq failed to patch $paramsPath" }
Move-Item -Force $tmp.FullName $paramsPath
Write-Host "    wrote $paramsPath"

Write-Host "==> [5/5] What-if preview"
az deployment sub what-if `
  --location $Location `
  --template-file (Join-Path $repoRoot 'infra/main.bicep') `
  --parameters "@$paramsPath"

Write-Host ""
Write-Host "Phase 1 complete."
Write-Host "Next: review the diff above, then run Phase 2:"
Write-Host "  azd env new hack2026; azd provision"
Write-Host "  # or"
Write-Host "  az deployment sub create -l $Location -f infra/main.bicep -p `@$paramsPath"
