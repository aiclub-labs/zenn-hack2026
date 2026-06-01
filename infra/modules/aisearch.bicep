// Azure AI Search (Basic SKU) + index corpus-${env} provisioned via deployment script.
// Index schema per contracts.md §3.
// Note: index/data-plane provisioning is not supported by Bicep; we expose
// endpoint + admin role assignments and rely on a separate script (scripts/provision_search_index.py)
// to create the index using Managed Identity.

targetScope = 'resourceGroup'

@description('Short project prefix.')
param project string

@description('Environment suffix (dev|prod).')
param env string

@description('Primary location.')
param location string

@description('Resource tags.')
param tags object

var suffix = substring(uniqueString(resourceGroup().id, env), 0, 6)
var serviceName = 'srch-${project}-${env}-${suffix}'

resource search 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: serviceName
  location: location
  tags: tags
  sku: {
    name: 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false  // admin key only for bootstrap; runtime uses MI
    semanticSearch: 'free'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

output serviceName string = search.name
output serviceId string = search.id
output endpoint string = 'https://${search.name}.search.windows.net'
output indexName string = 'corpus-${env}'
