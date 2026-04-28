<#
.SYNOPSIS
  Teardown — PowerShell 7+ sibling of teardown.sh. Order matters: locks first, then resources.

.PARAMETER Yes
  Skip confirmation prompts.

.PARAMETER DryRun
  Print actions without executing.

.PARAMETER Project
  Project prefix. Defaults to "hack2026".
#>

[CmdletBinding()]
param(
  [switch] $Yes,
  [switch] $DryRun,
  [string] $Project = 'hack2026'
)

$ErrorActionPreference = 'Continue'

$Location = $env:AZURE_LOCATION
if (-not $Location) { $Location = 'swedencentral' }

$SharedRg = "rg-$Project-shared"
$DevRg    = "rg-$Project-dev"
$ProdRg   = "rg-$Project-prod"
$LockName = 'nodelete-shared'

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "az CLI not found" }

function Invoke-Run([string] $cmd) {
  if ($DryRun) { Write-Host "[dry-run] $cmd"; return }
  Invoke-Expression $cmd
}

function Confirm-Action([string] $msg) {
  if ($Yes -or $DryRun) { return $true }
  $ans = Read-Host "$msg [y/N]"
  return $ans -match '^[Yy]$'
}

$subName = az account show --query name -o tsv
$subId   = az account show --query id -o tsv
Write-Host "Active sub: $subName ($subId)"
Write-Host ""
if (-not (Confirm-Action "Proceed with teardown of project='$Project' on this sub?")) {
  Write-Host "Aborted."; return
}

Write-Host "==> [1/5] Drop the shared-RG delete-lock"
& az lock show --name $LockName -g $SharedRg *> $null
if ($LASTEXITCODE -eq 0) {
  Invoke-Run "az lock delete --name $LockName -g $SharedRg"
} else {
  Write-Host "    no $LockName lock on $SharedRg (no-op)"
}

Write-Host "==> [2/5] Delete + purge AOAI account (releases custom-domain reservation)"
$aoaiName = az cognitiveservices account list -g $SharedRg --query "[?kind=='OpenAI'].name | [0]" -o tsv 2>$null
if ($aoaiName) {
  $aoaiLoc = az cognitiveservices account show -g $SharedRg -n $aoaiName --query location -o tsv 2>$null
  if (-not $aoaiLoc) { $aoaiLoc = $Location }
  Invoke-Run "az cognitiveservices account delete -g $SharedRg -n $aoaiName"
  Invoke-Run "az cognitiveservices account purge -l $aoaiLoc -g $SharedRg -n $aoaiName"
} else {
  Write-Host "    no AOAI account in $SharedRg (no-op)"
}

Write-Host "==> [3/5] Delete resource groups"
foreach ($rg in @($DevRg, $SharedRg, $ProdRg)) {
  & az group show -n $rg *> $null
  if ($LASTEXITCODE -eq 0) {
    Invoke-Run "az group delete -n $rg --yes --no-wait"
  } else {
    Write-Host "    $rg not present (no-op)"
  }
}

Write-Host "==> [4/5] Wait for RG deletions to complete"
foreach ($rg in @($DevRg, $SharedRg, $ProdRg)) {
  if ($DryRun) { Write-Host "[dry-run] wait for $rg deletion"; continue }
  do {
    & az group show -n $rg *> $null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "    waiting for $rg ..."
      Start-Sleep -Seconds 15
    } else { break }
  } while ($true)
}

Write-Host "==> [5/5] Purge soft-deleted Key Vaults"
$deletedKvs = (az keyvault list-deleted --query "[?properties.tags.project=='$Project'].name" -o tsv 2>$null) -split "`n" | Where-Object { $_ }
if ($deletedKvs.Count -gt 0) {
  foreach ($kv in $deletedKvs) {
    Invoke-Run "az keyvault purge --name $kv --location $Location"
  }
} else {
  Write-Host "    no soft-deleted KVs tagged project=$Project (no-op)"
}

Write-Host ""
Write-Host "==> Verification:"
$remainingRgs = az group list --tag "project=$Project" --query "length(@)" -o tsv 2>$null
$remainingKvs = az keyvault list-deleted --query "[?properties.tags.project=='$Project'] | length(@)" -o tsv 2>$null
if (-not $remainingRgs) { $remainingRgs = '0' }
if (-not $remainingKvs) { $remainingKvs = '0' }
Write-Host "  RGs remaining: $remainingRgs (expect 0)"
Write-Host "  Soft-deleted KVs remaining: $remainingKvs (expect 0)"
Write-Host ""
Write-Host "Teardown complete." -ForegroundColor Green
Write-Host "Reminder: any AOAI usage past PAYG conversion is now stopped — confirm card balance via portal."
