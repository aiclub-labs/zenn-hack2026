targetScope = 'subscription'

param subscriptionId string
param devRgName string
param sharedRgName string
param memberObjectIds array
param ownerObjectId string
param keyVaultId string
param storageId string

// Built-in role definition IDs — see Microsoft Learn for full list.
var roles = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  owner: '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
  kvSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
  storageBlobContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

// Contributor on dev + shared RGs for every team member
module contribDev 'rbac-rg-assignment.bicep' = [for (id, i) in memberObjectIds: {
  name: 'rbac-contrib-dev-${i}'
  scope: resourceGroup(devRgName)
  params: {
    principalId: id
    roleDefinitionId: roles.contributor
  }
}]

module contribShared 'rbac-rg-assignment.bicep' = [for (id, i) in memberObjectIds: {
  name: 'rbac-contrib-shared-${i}'
  scope: resourceGroup(sharedRgName)
  params: {
    principalId: id
    roleDefinitionId: roles.contributor
  }
}]

// Key Vault + Storage data-plane access for every member
module kvAccess 'rbac-resource-assignment.bicep' = [for (id, i) in memberObjectIds: {
  name: 'rbac-kv-${i}'
  scope: resourceGroup(sharedRgName)
  params: {
    principalId: id
    roleDefinitionId: roles.kvSecretsOfficer
    resourceId: keyVaultId
  }
}]

module storageAccess 'rbac-resource-assignment.bicep' = [for (id, i) in memberObjectIds: {
  name: 'rbac-storage-${i}'
  scope: resourceGroup(sharedRgName)
  params: {
    principalId: id
    roleDefinitionId: roles.storageBlobContributor
    resourceId: storageId
  }
}]

// Owner at subscription scope is established by sub creation (signup user is Account Admin → Owner).
// Bicep-stamping a second Owner assignment for the same principal collides with the sub-creation one
// (ARM: RoleAssignmentExists). The signup-time assignment is stable for the life of the sub.
// `ownerObjectId` is retained as a parameter for documentation / future re-designation but unused here.
