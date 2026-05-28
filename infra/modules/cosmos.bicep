// Cosmos DB Serverless account + dialogue_delta database + 12 containers.
// All containers use partition key /pk (sector#unit). See contracts.md §2.

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
var accountName = 'cosmos-${project}-${env}-${suffix}'

var containerNames = [
  'schemas'
  'schema_audit_log'
  'schema_candidate_log'
  'prompt_templates'
  'dialogue_turns'
  'delta_events'
  'hearout_records'
  'formalization_queue'
  'truth_judgment_logs'
  'corpus_meta'
  'citation_audit_log'
  'error_logs'
]

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      { name: 'EnableServerless' }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    minimalTlsVersion: 'Tls12'
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: account
  name: 'dialogue_delta'
  properties: {
    resource: {
      id: 'dialogue_delta'
    }
  }
}

resource containers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = [for name in containerNames: {
  parent: database
  name: name
  properties: {
    resource: {
      id: name
      partitionKey: {
        paths: [ '/pk' ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/"_etag"/?' } ]
      }
    }
  }
}]

output accountName string = account.name
output accountId string = account.id
output endpoint string = account.properties.documentEndpoint
output databaseName string = database.name
