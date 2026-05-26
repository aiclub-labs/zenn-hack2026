// Subscription-scoped entry point. Everything (RGs, shared resources, RBAC,
// budget, policy) is declared here and in ./modules. Deploy via azd (`azd up`)
// or direct CLI: `az deployment sub create -l <loc> -f infra/main.bicep -p @infra/main.parameters.json`.

targetScope = 'subscription'

@description('Short project prefix — drives RG names and resource naming.')
@minLength(3)
@maxLength(10)
param project string = 'hack2026'

@description('Primary location for RGs and most resources. Override if AOAI region constraint forces a move.')
param location string = 'swedencentral'

@description('Entra ID objectIds of team members. Required for RBAC. Resolve via `az ad user show --id <upn> --query id`.')
param memberObjectIds array

@description('Entra ID objectId of the designated Owner (subset of memberObjectIds).')
param ownerObjectId string

@description('Monthly budget ceiling in USD. Alert fires at 80% and 100%.')
param budgetAmount int = 180

@description('Email(s) to notify on budget threshold breach.')
param budgetContactEmails array

@description('Common tags applied to every RG and resource.')
param tags object = {
  project: 'hack2026'
  managedBy: 'bicep'
}

@description('Environment label (dev|prod) — drives resource naming + index suffix.')
@allowed([ 'dev', 'prod' ])
param env string = 'dev'

@description('Existing Key Vault name to publish dialogue-delta secrets into.')
param kvName string = 'kv-hack2026-tyu3o4'

@description('Feature tag applied to dialogue-delta-formalization resources.')
param projectTag string = 'hack2026'

@description('Container registry login server for Container Apps image pulls.')
param containerRegistryServer string = ''

@description('Azure OpenAI endpoint (plain).')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI small/large deployment names.')
param azureOpenAIDeploymentSmall string = 'gpt-5.4-mini'
param azureOpenAIDeploymentLarge string = 'gpt-5.4'

@description('KV secret URI (versionless) for AOAI API key.')
param azureOpenAIApiKeySecretUri string = ''

var featureTags = union(tags, {
  feature: 'dialogue-delta-formalization'
  env: env
  project: projectTag
})

// ---------- Resource Groups ----------
module rgs 'modules/resource-groups.bicep' = {
  name: 'rgs'
  params: {
    project: project
    location: location
    tags: tags
  }
}

// ---------- Shared resources (Key Vault, Storage, LAW, AppI, CAE) ----------
// scope must be resolvable at deployment-start (BCP120), so derive RG name from `project` directly
// rather than from rgs.outputs. Implicit ordering preserved via dependsOn.
module shared 'modules/shared.bicep' = {
  name: 'shared'
  scope: resourceGroup('rg-${project}-shared')
  dependsOn: [
    rgs
  ]
  params: {
    project: project
    location: location
    tags: tags
  }
}

// ---------- RBAC for team ----------
module rbac 'modules/rbac.bicep' = {
  name: 'rbac'
  params: {
    subscriptionId: subscription().subscriptionId
    devRgName: rgs.outputs.devRgName
    sharedRgName: rgs.outputs.sharedRgName
    memberObjectIds: memberObjectIds
    ownerObjectId: ownerObjectId
    keyVaultId: shared.outputs.keyVaultId
    storageId: shared.outputs.storageId
  }
}

// ---------- Budget + cost alert ----------
module budget 'modules/budget.bicep' = {
  name: 'budget'
  params: {
    project: project
    amount: budgetAmount
    contactEmails: budgetContactEmails
  }
}

// ---------- Policy guardrails ----------
module policy 'modules/policy.bicep' = {
  name: 'policy'
  params: {}
}

// ---------- dialogue-delta-formalization: Cosmos DB ----------
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  scope: resourceGroup('rg-${project}-${env}')
  dependsOn: [ rgs ]
  params: {
    project: project
    env: env
    location: location
    tags: featureTags
  }
}

// ---------- dialogue-delta-formalization: AI Search ----------
module aisearch 'modules/aisearch.bicep' = {
  name: 'aisearch'
  scope: resourceGroup('rg-${project}-${env}')
  dependsOn: [ rgs ]
  params: {
    project: project
    env: env
    location: location
    tags: featureTags
  }
}

// ---------- dialogue-delta-formalization: Container Apps ----------
module containerapps 'modules/containerapps.bicep' = {
  name: 'containerapps'
  scope: resourceGroup('rg-${project}-${env}')
  dependsOn: [ rgs, shared, cosmos, aisearch ]
  params: {
    project: project
    env: env
    location: location
    tags: featureTags
    containerAppsEnvId: shared.outputs.containerAppsEnvId
    appInsightsConnectionString: shared.outputs.appInsightsConnectionString
    cosmosEndpoint: cosmos.outputs.endpoint
    aiSearchEndpoint: aisearch.outputs.endpoint
    aiSearchIndex: aisearch.outputs.indexName
    keyVaultUri: 'https://${kvName}.vault.azure.net/'
    containerRegistryServer: containerRegistryServer
    azureOpenAIEndpoint: azureOpenAIEndpoint
    azureOpenAIDeploymentSmall: azureOpenAIDeploymentSmall
    azureOpenAIDeploymentLarge: azureOpenAIDeploymentLarge
    azureOpenAIApiKeySecretUri: azureOpenAIApiKeySecretUri
  }
}

// ---------- dialogue-delta-formalization: Cosmos data-plane RBAC ----------
module cosmosRoles 'modules/cosmos-roles.bicep' = {
  name: 'cosmosRoles'
  scope: resourceGroup('rg-${project}-${env}')
  dependsOn: [ cosmos, containerapps ]
  params: {
    cosmosAccountName: cosmos.outputs.accountName
    principalIds: concat(containerapps.outputs.appPrincipalIds, [ containerapps.outputs.slaCronJobPrincipalId ])
  }
}

// ---------- dialogue-delta-formalization: KV secret placeholders + role grants ----------
module kvSecrets 'modules/keyvault-secrets.bicep' = {
  name: 'kvSecrets'
  scope: resourceGroup('rg-${project}-shared')
  dependsOn: [ shared, containerapps ]
  params: {
    keyVaultName: kvName
    tags: featureTags
    secretReaderPrincipalIds: concat(containerapps.outputs.appPrincipalIds, [ containerapps.outputs.slaCronJobPrincipalId ])
    cosmosEndpoint: cosmos.outputs.endpoint
    aiSearchEndpoint: aisearch.outputs.endpoint
  }
}

// ---------- dialogue-delta-formalization: Foundry (Agent Service) ----------
module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  scope: resourceGroup('rg-${project}-${env}')
  dependsOn: [ rgs, shared ]
  params: {
    project: project
    env: env
    location: location
    tags: featureTags
    storageAccountId: shared.outputs.storageId
    keyVaultId: shared.outputs.keyVaultId
    // appInsightsId omitted — shared.bicep exports only the connection string.
    // Foundry hub treats appInsights as optional; wire later via aiproject portal if needed.
  }
}

output COSMOS_ENDPOINT string = cosmos.outputs.endpoint
output COSMOS_DATABASE string = cosmos.outputs.databaseName
output AISEARCH_ENDPOINT string = aisearch.outputs.endpoint
output AISEARCH_INDEX string = aisearch.outputs.indexName
output FOUNDRY_PROJECT string = foundry.outputs.projectName
output API_FQDN string = containerapps.outputs.apiFqdn
output SLA_CRON_JOB_NAME string = containerapps.outputs.slaCronJobName

// Outputs consumed by azd + app config
output AZURE_KEY_VAULT_NAME string = shared.outputs.keyVaultName
output AZURE_STORAGE_ACCOUNT_NAME string = shared.outputs.storageAccountName
output AZURE_APPINSIGHTS_CONNECTION_STRING string = shared.outputs.appInsightsConnectionString
output AZURE_CONTAINER_APPS_ENV_ID string = shared.outputs.containerAppsEnvId
output AZURE_SHARED_RG string = rgs.outputs.sharedRgName
output AZURE_DEV_RG string = rgs.outputs.devRgName
output AZURE_PROD_RG string = rgs.outputs.prodRgName
