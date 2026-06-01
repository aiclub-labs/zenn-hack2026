// Azure AI Foundry (Agent Service) workspace placeholder.
// Foundry Workflow agent is in preview (swedencentral). The workflow definition
// itself is provisioned out-of-band via Foundry SDK / portal; this module sets up
// the underlying AI Hub + Project that the workflow attaches to.

targetScope = 'resourceGroup'

@description('Short project prefix.')
param project string

@description('Environment suffix (dev|prod).')
param env string

@description('Primary location (must be a Foundry-preview region; swedencentral).')
param location string = 'swedencentral'

@description('Tags.')
param tags object

@description('Storage account ID for the hub.')
param storageAccountId string

@description('Key Vault ID for the hub.')
param keyVaultId string

@description('App Insights ID for the hub (optional).')
param appInsightsId string = ''

var suffix = substring(uniqueString(resourceGroup().id, env), 0, 6)
var hubName = 'aih-${project}-${env}-${suffix}'
var projectName = 'aip-${project}-${env}-${suffix}'

resource hub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: hubName
  location: location
  tags: tags
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'hack2026 dialogue-delta Foundry hub'
    storageAccount: storageAccountId
    keyVault: keyVaultId
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'dialogue-delta-formalization'
    hubResourceId: hub.id
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

// NOTE: Foundry Workflow agent definition (FOUNDRY_WORKFLOW_ID) is created via
// scripts/provision_foundry_workflow.py once the project exists. The script
// reads the project name from FOUNDRY_PROJECT env and writes the resulting
// workflow ID back to Key Vault / Container Apps env.

output hubId string = hub.id
output projectId string = aiProject.id
output projectName string = aiProject.name
output projectPrincipalId string = aiProject.identity.principalId
