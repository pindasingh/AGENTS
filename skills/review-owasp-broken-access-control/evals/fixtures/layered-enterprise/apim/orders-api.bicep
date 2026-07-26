resource ordersApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  name: 'orders-v1'
  properties: {
    path: 'orders'
    protocols: [ 'https' ]
    subscriptionRequired: true
    serviceUrl: 'https://orders-api.internal.example.test'
    subscriptionKeyParameterNames: {
      header: 'Ocp-Apim-Subscription-Key'
      query: 'subscription-key'
    }
  }
}

// orders-v1 is attached to the partner-orders product. The service, product,
// API, and operation policy files form the effective inbound policy.
