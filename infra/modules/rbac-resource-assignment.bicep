targetScope = 'resourceGroup'

param principalId string
param roleDefinitionId string
param resourceId string

resource assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceId, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/${roleDefinitionId}'
    principalType: 'User'
  }
}
