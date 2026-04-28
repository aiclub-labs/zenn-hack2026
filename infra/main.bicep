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

// Outputs consumed by azd + app config
output AZURE_KEY_VAULT_NAME string = shared.outputs.keyVaultName
output AZURE_STORAGE_ACCOUNT_NAME string = shared.outputs.storageAccountName
output AZURE_APPINSIGHTS_CONNECTION_STRING string = shared.outputs.appInsightsConnectionString
output AZURE_CONTAINER_APPS_ENV_ID string = shared.outputs.containerAppsEnvId
output AZURE_SHARED_RG string = rgs.outputs.sharedRgName
output AZURE_DEV_RG string = rgs.outputs.devRgName
output AZURE_PROD_RG string = rgs.outputs.prodRgName
