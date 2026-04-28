targetScope = 'subscription'

param project string
param amount int
param contactEmails array

resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: '${project}-budget'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: '2026-04-01'
      endDate: '2026-12-31'
    }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: contactEmails
        locale: 'en-us'
      }
      actual100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: contactEmails
        locale: 'en-us'
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: contactEmails
        locale: 'en-us'
      }
    }
  }
}
