# Validation notes

## Checks performed

- Confirmed the authoritative source starts with `flowchart LR` and uses stable, unique identifiers.
- Compared the diagram and HTML relationship index against every file in the supplied fixture.
- Confirmed visible boundaries for callers, ingress runtimes, Basket, Ordering, Catalog, Payment, service-owned stores, and event-bus infrastructure.
- Confirmed direction and labels for HTTP checkout, Redis and relational persistence, event publication/delivery, stock outcomes, payment success, and the evidenced SignalR consumer.
- Confirmed HTTP 202 is shown after checkout event publication and is not connected to asynchronous order completion.
- Confirmed RabbitMQ and Azure Service Bus are represented as implementation alternatives rather than simultaneous required brokers.
- Confirmed the HTML is self-contained: inline CSS, no scripts, remote resources, fonts, images, or network links.
- Confirmed the Mermaid source embedded in `architecture-review.html` exactly matches `architecture.mmd` after HTML text decoding.

## Rendering status

No Mermaid renderer was invoked or available through the selected skill pair. Therefore, no syntax-rendering or layout claim is made. `architecture.mmd` is the authoritative portable source; `architecture-review.html` is an offline semantic review artifact with an embedded source copy, ownership overview, and directed relationship index.

## Evidence gaps intentionally left unresolved

- The fixture requires a payment-failure path variant but does not provide the failure event contract, consumer, or resulting order state. No payment-failure edge was invented.
- The fixture identifies Ordering SignalR Hub as a downstream event consumer, but does not identify its notification recipient or transport edge. The diagram stops at the hub.
- The fixture establishes consumption of `OrderStatusChangedToAwaitingValidationIntegrationEvent`, but does not identify its producer in the supplied excerpts. The delivery is shown without an invented producer.
- Payment persistence is not specified, so no Payment store is shown.
