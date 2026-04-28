targetScope = 'resourceGroup'

param project string
param location string
param tags object

var suffix = substring(uniqueString(resourceGroup().id), 0, 6)

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' = {
  name: 'kv-${project}-${suffix}'
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: 'st${project}${suffix}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource artifacts 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  name: '${storage.name}/default/artifacts'
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-${project}-${suffix}'
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    sku: { name: 'PerGB2018' }
  }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${project}-${suffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${project}-${suffix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

// Shared RG lock — prevents accidental RG deletion from torching secrets + telemetry
resource lock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'nodelete-shared'
  properties: {
    level: 'CanNotDelete'
    notes: 'Shared resources — delete only via explicit teardown runbook.'
  }
}

output keyVaultId string = kv.id
output keyVaultName string = kv.name
output storageId string = storage.id
output storageAccountName string = storage.name
output appInsightsConnectionString string = appi.properties.ConnectionString
output containerAppsEnvId string = cae.id
