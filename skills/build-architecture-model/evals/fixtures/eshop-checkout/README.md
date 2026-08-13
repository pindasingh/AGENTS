# Microsoft eShopOnContainers shared architecture fixture

This fixture is a curated evidence set from Microsoft's public, MIT-licensed `dotnet-architecture/eShopOnContainers` reference application (`dev` branch). Both architecture skills receive the same files and must model the same checkout/order process. Do not add a fraud service, card network, shipping service, or email service: none is evidenced in this selected public flow.

Primary public sources:

- Repository: https://github.com/dotnet-architecture/eShopOnContainers/tree/dev
- Microsoft architecture guide: https://learn.microsoft.com/dotnet/architecture/cloud-native/introduce-eshoponcontainers-reference-app
- API gateways: https://github.com/dotnet-architecture/eShopOnContainers/wiki/API-gateways
- RabbitMQ event bus: https://learn.microsoft.com/dotnet/architecture/microservices/multi-container-microservice-net-applications/rabbitmq-event-bus-development-test-environment
- Integration-event guidance: https://learn.microsoft.com/dotnet/architecture/microservices/multi-container-microservice-net-applications/integration-event-based-microservice-communications
- Execution trace: https://github.com/dotnet-architecture/eShopOnContainers/wiki/Serilog-and-Seq

## Architectural truth to recover

1. Web and mobile clients enter through distinct BFF/API gateways over HTTP/REST.
2. Basket API owns the checkout HTTP endpoint and reads the customer's basket from Redis.
3. Basket publishes `UserCheckoutAcceptedIntegrationEvent` and then returns HTTP 202 Accepted. The order is not synchronously created inside that HTTP request.
4. Ordering consumes the checkout event, dispatches an idempotent `CreateOrderCommand`, creates the order in Ordering SQL, and records/publishes integration events after the transaction.
5. `OrderStartedIntegrationEvent` is consumed by Basket to delete the checked-out basket.
6. `OrderStatusChangedToAwaitingValidationIntegrationEvent` is consumed by Catalog, which validates/decrements stock in Catalog SQL and publishes either stock-confirmed or stock-rejected.
7. Ordering consumes the stock result. The confirmed branch changes order state and leads to `OrderStatusChangedToStockConfirmedIntegrationEvent`; the rejected branch cancels the order.
8. Payment consumes stock-confirmed and publishes payment-succeeded in the sample flow. Ordering consumes payment-succeeded, marks the order paid in Ordering SQL, and publishes the paid status.
9. RabbitMQ (or the replaceable Azure Service Bus implementation) is the event-bus infrastructure. Publish, broker delivery, subscription handling, and resulting state changes are distinct architectural operations.
10. Correlation/idempotency uses the checkout request ID and integration event IDs.

Required path variants are: HTTP checkout acceptance, asynchronous successful order completion, stock rejection, and payment failure. The asynchronous path must link back to the accepted checkout without pretending the browser waits for completion.
