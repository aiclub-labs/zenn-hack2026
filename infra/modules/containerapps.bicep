// Container Apps: 5 apps on existing Container Apps Environment.
// - api, web-chat, web-admin, web-review: scale-to-zero (min=0, idle 5m)
// - agent-runner: min=1 always (covers 9-19 JST workflow needs; trivial cost on serverless plan)
// All apps run with System-Assigned Managed Identity.

targetScope = 'resourceGroup'

@description('Short project prefix.')
param project string

@description('Environment suffix (dev|prod).')
param env string

@description('Primary location.')
param location string

@description('Tags.')
param tags object

@description('Container Apps Environment resource ID (from shared.bicep).')
param containerAppsEnvId string

@description('Placeholder container image. Real images are pushed by azd / CI.')
param placeholderImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('App Insights connection string for OTEL.')
param appInsightsConnectionString string = ''

@description('Cosmos DB endpoint.')
param cosmosEndpoint string = ''

@description('AI Search endpoint.')
param aiSearchEndpoint string = ''

@description('AI Search index name.')
param aiSearchIndex string = 'corpus-${env}'

@description('Key Vault URI.')
param keyVaultUri string = ''

@description('Container registry login server (e.g. acr.azurecr.io). Empty disables registry binding.')
param containerRegistryServer string = ''

@description('Azure OpenAI endpoint (plain).')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI small deployment name. Defaults aligned with infra/main.bicep (Issue #42).')
param azureOpenAIDeploymentSmall string = 'gpt-5.4-mini'

@description('Azure OpenAI large deployment name. Defaults aligned with infra/main.bicep (Issue #42).')
param azureOpenAIDeploymentLarge string = 'gpt-5.4'

@description('KV secret URI (versionless) for Azure OpenAI API key. Empty disables KV-backed AOAI key.')
param azureOpenAIApiKeySecretUri string = ''

var apps = [
  {
    name: 'api'
    minReplicas: 0
    maxReplicas: 3
    targetPort: 8000
    external: true
  }
  {
    name: 'web-chat'
    minReplicas: 0
    maxReplicas: 2
    targetPort: 80
    external: true
  }
  {
    name: 'web-admin'
    minReplicas: 0
    maxReplicas: 2
    targetPort: 80
    external: true
  }
  {
    name: 'web-review'
    minReplicas: 0
    maxReplicas: 2
    targetPort: 80
    external: true
  }
  {
    name: 'agent-runner'
    minReplicas: 1
    maxReplicas: 2
    targetPort: 8000
    external: false
  }
]

var commonEnv = concat([
  { name: 'ENV', value: env }
  { name: 'DEV_SKIP_AUTH', value: env == 'dev' ? 'true' : 'false' }
  { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
  { name: 'COSMOS_DATABASE', value: 'dialogue_delta' }
  { name: 'AISEARCH_ENDPOINT', value: aiSearchEndpoint }
  { name: 'AISEARCH_INDEX', value: aiSearchIndex }
  { name: 'KEY_VAULT_URI', value: keyVaultUri }
  { name: 'APPINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
  { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
  { name: 'AZURE_OPENAI_DEPLOYMENT_SMALL', value: azureOpenAIDeploymentSmall }
  { name: 'AZURE_OPENAI_DEPLOYMENT_LARGE', value: azureOpenAIDeploymentLarge }
], empty(azureOpenAIApiKeySecretUri) ? [] : [
  { name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-api-key' }
])

var commonSecrets = empty(azureOpenAIApiKeySecretUri) ? [] : [
  {
    name: 'azure-openai-api-key'
    keyVaultUrl: azureOpenAIApiKeySecretUri
    identity: 'system'
  }
]

resource containerApps 'Microsoft.App/containerApps@2024-03-01' = [for app in apps: {
  name: 'ca-${project}-${env}-${app.name}'
  location: location
  tags: union(tags, { app: app.name, 'azd-service-name': app.name })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvId
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: commonSecrets
      ingress: {
        external: app.external
        targetPort: app.targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: empty(containerRegistryServer) ? [] : [
        {
          server: containerRegistryServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: app.name
          image: placeholderImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: commonEnv
        }
      ]
      scale: {
        minReplicas: app.minReplicas
        maxReplicas: app.maxReplicas
        // 5min idle scale-to-zero handled by CAE default cooldown
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}]

// ---------------------------------------------------------------------------
// M-12: SLA cron — Container Apps Job, hourly trigger, no ingress.
// ---------------------------------------------------------------------------
resource slaCronJob 'Microsoft.App/jobs@2024-03-01' = {
  name: 'aca-sla-cron-${env}'
  location: location
  tags: union(tags, { app: 'sla-cron' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvId
    configuration: {
      secrets: commonSecrets
      triggerType: 'Schedule'
      replicaTimeout: 300
      replicaRetryLimit: 1
      scheduleTriggerConfig: {
        cronExpression: '0 * * * *'
        parallelism: 1
        replicaCompletionCount: 1
      }
    }
    template: {
      containers: [
        {
          name: 'sla-cron'
          image: placeholderImage
          command: [ 'python', '-m', 'app.agents.formalization.sla_cron' ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: commonEnv
        }
      ]
    }
  }
}

output appNames array = [for (a, i) in apps: containerApps[i].name]
output appPrincipalIds array = [for (a, i) in apps: containerApps[i].identity.principalId]
output apiFqdn string = containerApps[0].properties.configuration.ingress.fqdn
output slaCronJobName string = slaCronJob.name
output slaCronJobPrincipalId string = slaCronJob.identity.principalId
