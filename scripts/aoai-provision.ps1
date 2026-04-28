<#
.SYNOPSIS
  AOAI provisioning — PowerShell 7+ sibling of aoai-provision.sh.
  Wraps §6.1–6.2. Idempotent.

.PARAMETER Region
  Azure region with the required AOAI models (D7 outcome).

.PARAMETER Name
  AOAI account name. Defaults to "aoai-hack2026".

.PARAMETER ResourceGroup
  Resource group hosting the account. Defaults to "rg-hack2026-shared".
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string] $Region,
  [string] $Name = 'aoai-hack2026',
  [string] $ResourceGroup = 'rg-hack2026-shared'
)

$ErrorActionPreference = 'Stop'

$Deployments = @(
  @{ Name = 'gpt-4o-mini';            Model = 'gpt-4o-mini';            Version = '2024-07-18'; Capacity = 50 }
  @{ Name = 'gpt-4o';                 Model = 'gpt-4o';                 Version = '2024-11-20'; Capacity = 10 }
  @{ Name = 'text-embedding-3-small'; Model = 'text-embedding-3-small'; Version = '1';          Capacity = 50 }
)

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "az CLI not found" }

Write-Host "==> [1/4] Check RG $ResourceGroup exists"
& az group show -n $ResourceGroup *> $null
if ($LASTEXITCODE -ne 0) {
  throw "RG $ResourceGroup not found — has Phase 2 (azd provision) run?"
}

Write-Host "==> [2/4] Create AOAI account $Name in $Region"
& az cognitiveservices account show -g $ResourceGroup -n $Name *> $null
if ($LASTEXITCODE -eq 0) {
  Write-Host "    $Name already exists (no-op)"
} else {
  az cognitiveservices account create `
    -g $ResourceGroup -n $Name -l $Region `
    --kind OpenAI --sku S0 `
    --custom-domain $Name `
    --assign-identity `
    --yes `
    --only-show-errors | Out-Null
  Write-Host "    $Name created"
}

Write-Host "==> [3/4] Deploy models"
foreach ($d in $Deployments) {
  & az cognitiveservices account deployment show `
    -g $ResourceGroup -n $Name --deployment-name $d.Name *> $null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "    deployment $($d.Name) exists (no-op)"
  } else {
    az cognitiveservices account deployment create `
      -g $ResourceGroup -n $Name `
      --deployment-name $d.Name `
      --model-name $d.Model --model-version $d.Version `
      --model-format OpenAI `
      --sku-name Standard --sku-capacity $d.Capacity `
      --only-show-errors | Out-Null
    Write-Host "    deployment $($d.Name) ($($d.Model) v$($d.Version), cap=$($d.Capacity)) created"
  }
}

Write-Host "==> [4/4] Stash credentials in Key Vault"
$kv = az keyvault list -g $ResourceGroup --query "[0].name" -o tsv 2>$null
if (-not $kv) {
  $kv = az keyvault list --query "[?tags.project=='hack2026'].name | [0]" -o tsv 2>$null
}
if (-not $kv) {
  Write-Host "    no Key Vault found — skipping secret stash. Add manually after locating KV." -ForegroundColor Yellow
  return
}
Write-Host "    KV: $kv"

$key = az cognitiveservices account keys list -g $ResourceGroup -n $Name --query key1 -o tsv
$endpoint = az cognitiveservices account show -g $ResourceGroup -n $Name --query properties.endpoint -o tsv

az keyvault secret set --vault-name $kv --name AZURE-OPENAI-API-KEY  --value $key      --only-show-errors | Out-Null
az keyvault secret set --vault-name $kv --name AZURE-OPENAI-ENDPOINT --value $endpoint --only-show-errors | Out-Null
Write-Host "    secrets AZURE-OPENAI-API-KEY + AZURE-OPENAI-ENDPOINT stashed in $kv"

Write-Host ""
Write-Host "AOAI provisioning complete."
Write-Host "  Endpoint: $endpoint"
$depList = (az cognitiveservices account deployment list -g $ResourceGroup -n $Name --query "[].name" -o tsv) -split "`n" -join ' '
Write-Host "  Deployments: $depList"
Write-Host ""
Write-Host "App code should resolve secrets from Key Vault using Managed Identity."
Write-Host "If 429 (quota=0) on first call, file a quota request via portal — 24h lead time."
