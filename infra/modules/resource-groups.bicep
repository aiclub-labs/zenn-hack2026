targetScope = 'subscription'

param project string
param location string
param tags object

resource devRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${project}-dev'
  location: location
  tags: union(tags, { env: 'dev' })
}

resource sharedRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${project}-shared'
  location: location
  tags: union(tags, { env: 'shared' })
}

resource prodRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${project}-prod'
  location: location
  tags: union(tags, { env: 'prod' })
}

output devRgName string = devRg.name
output sharedRgName string = sharedRg.name
output prodRgName string = prodRg.name
