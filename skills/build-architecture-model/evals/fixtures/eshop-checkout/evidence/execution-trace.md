# Published execution facts

Microsoft's eShop logging guide documents that handling `UserCheckoutAcceptedIntegrationEvent` begins a transaction, creates an order, commits, and publishes `OrderStartedIntegrationEvent` plus `OrderStatusChangedToSubmittedIntegrationEvent`. It also documents `OrderStatusChangedToStockConfirmedIntegrationEvent` being handled by Ordering SignalR Hub and Payment API; Payment then publishes `OrderPaymentSuccededIntegrationEvent`.

The Microsoft architecture guide documents separate microservices with their own persistent storage and coordination through a message bus. The API gateway guide documents HTTP/REST from BFFs to microservices and gRPC from aggregators to microservices. The RabbitMQ guide documents publish, broker channel, subscription, and handler behavior.
