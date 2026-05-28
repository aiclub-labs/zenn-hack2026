// Grant Cosmos DB Built-in Data Contributor to a list of principal IDs.
// Split from cosmos.bicep to break the dependency cycle:
//   cosmos -> outputs endpoint -> containerapps -> outputs principalIds -> back here.

targetScope = 'resourceGroup'

@description('Cosmos account name (must already exist in this RG).')
param cosmosAccountName string

@description('Principal IDs (Container App MSIs) to grant Data Contributor.')
param principalIds array

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: cosmosAccountName
}

var dataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource assignments 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = [for pid in principalIds: if (!empty(pid)) {
  parent: account
  name: guid(account.id, pid, dataContributorRoleId)
  properties: {
    roleDefinitionId: '${account.id}/sqlRoleDefinitions/${dataContributorRoleId}'
    principalId: pid
    scope: account.id
  }
}]
