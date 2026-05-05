targetScope = 'subscription'

// TODO(post-M4): flip default to 'Default' once shared RG is stable. Track in STATUS.md follow-ups.
@description('Policy enforcement mode. Use DoNotEnforce on first provision (avoids RequestDisallowedByPolicy race against Storage creation), then flip to Default after the shared resources land.')
@allowed([
  'Default'
  'DoNotEnforce'
])
param enforcementMode string = 'DoNotEnforce'

// Built-in: "Storage accounts should disallow public access" — deny effect
var denyPublicBlobPolicyId = '/providers/Microsoft.Authorization/policyDefinitions/4fa4b6c0-31ca-4c0d-b10d-24b96f62a751'

resource denyPublicBlob 'Microsoft.Authorization/policyAssignments@2024-04-01' = {
  name: 'deny-storage-public'
  properties: {
    displayName: 'Deny public blob access'
    policyDefinitionId: denyPublicBlobPolicyId
    enforcementMode: enforcementMode
  }
}
