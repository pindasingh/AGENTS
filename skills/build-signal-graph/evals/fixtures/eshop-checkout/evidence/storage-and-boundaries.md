# Published deployment boundaries

- Browser and mobile applications are separate callers.
- Web and mobile BFF/API gateways are separate ingress runtimes.
- Basket, Ordering, Catalog, and Payment are separate microservices.
- Basket persistence is Redis in the reference deployment.
- Ordering and Catalog own separate relational databases.
- RabbitMQ is the development/test event-bus implementation; Azure Service Bus is an alternative implementation behind the abstraction.
- Ordering SignalR Hub is a downstream consumer of order-status integration events.
