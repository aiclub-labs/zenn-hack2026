// Grant data-plane RBAC on the AI Search service to Container App MIs.
// "Search Index Data Contributor" (8ebe5a00-799e-43f5-93ac-243d3dce84a7) lets the
// api app upsert/merge documents into the corpus index without an admin key.

targetScope = 'resourceGroup'

@description('Name of the AI Search service.')
param searchServiceName string

@description('Principal IDs (Container App system MIs) that need data-plane write access.')
param principalIds array

// Search Index Data Contributor
var roleDefinitionId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'

resource search 'Microsoft.Search/searchServices@2024-03-01-preview' existing = {
  name: searchServiceName
}

resource assignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for pid in principalIds: if (!empty(pid)) {
  name: guid(search.id, pid, roleDefinitionId)
  scope: search
  properties: {
    principalId: pid
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/${roleDefinitionId}'
    principalType: 'ServicePrincipal'
  }
}]
