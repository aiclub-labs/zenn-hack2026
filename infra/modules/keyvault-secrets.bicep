// Key Vault secret placeholders + role assignments.
// Targets the existing kv-hack2026-tyu3o4 vault (contracts.md §7).
// Secret VALUES are NOT set by Bicep (would force secrets into source/state).
// Operators populate values out-of-band via:
//   az keyvault secret set --vault-name <kv> -n <SECRET_NAME> -f -
// This module only ensures the placeholder names exist with empty/sentinel value.

targetScope = 'resourceGroup'

@description('Existing Key Vault name (e.g. kv-hack2026-tyu3o4).')
param keyVaultName string

@description('Principal IDs (Container Apps / Foundry MI) that need Key Vault Secrets User role.')
param secretReaderPrincipalIds array = []

@description('Tags.')
param tags object

@description('Cosmos endpoint to publish as non-secret config (kept here for symmetry).')
param cosmosEndpoint string = ''

@description('AI Search endpoint.')
param aiSearchEndpoint string = ''

var secretNames = [
  'DISCORD-WEBHOOK-URL-SCHEMA-UPDATES'
  'DISCORD-WEBHOOK-URL-PENDING-REVIEW'
  'DISCORD-WEBHOOK-URL-EXPIRED'
  'DISCORD-WEBHOOK-URL-COST-ALERT'
  'COSMOS-CONNECTION-STRING'
  'AISEARCH-ADMIN-KEY'
  'AOAI-API-KEY'
]

// KV secret names disallow underscores → use hyphens. Client code maps back.

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: keyVaultName
}

resource secrets 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = [for n in secretNames: {
  parent: kv
  name: n
  tags: tags
  properties: {
    value: 'PLACEHOLDER_SET_VIA_CLI'
    attributes: {
      enabled: true
    }
  }
}]

// Key Vault Secrets User role (4633458b-17de-408a-b874-0445c86b69e6)
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource readerRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for pid in secretReaderPrincipalIds: {
  name: guid(kv.id, pid, kvSecretsUserRoleId)
  scope: kv
  properties: {
    principalId: pid
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
  }
}]

output keyVaultUri string = kv.properties.vaultUri
output secretNames array = secretNames
output publishedCosmosEndpoint string = cosmosEndpoint
output publishedSearchEndpoint string = aiSearchEndpoint
