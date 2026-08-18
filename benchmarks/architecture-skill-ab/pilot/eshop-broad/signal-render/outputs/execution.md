# Benchmark execution

## Exact evaluation prompt

"Using only the supplied Microsoft eShopOnContainers evidence, create the most useful broad architecture diagram for an engineer who needs to understand the system's callers, ownership boundaries, runtime services, stores, external infrastructure, and major directed HTTP, persistence, messaging, and notification relationships. This is a structural overview, not a request timeline. Do not invent unsupported components or interactions. Preserve the source used to generate the diagram and make the final artifact self-contained and reviewable offline."

## Artifacts

- `architecture/architecture.ts` — authoritative TypeScript Signal model.
- `architecture/signal.ts` — dependency-free typed DSL used by the model.
- `architecture/architecture.json` — data-only `$ref` projection.
- `architecture/index.html` — deterministic, self-contained offline diagram.
- `validation.txt` — exact validation commands and observed results.

## Scope and uncertainties

Only `skills/build-signal-graph/evals/fixtures/eshop-checkout/` was treated as system evidence. The model emphasizes the requested structural overview while retaining selectable web/mobile acceptance, successful completion, stock-rejection, and payment-failure paths.

- The fixture identifies one owned eShop application composed of separate runtime microservices, but does not provide finer team ownership; no team boundaries were invented.
- RabbitMQ is shown together with Azure Service Bus as alternatives behind one event-bus infrastructure identity, not as simultaneous brokers.
- The fixture requires a payment-failure branch and cancelled notification outcome but gives fewer implementation details than the successful branch. Those relationships are modeled only at the explicitly stated service/event/state-transition level.
- SignalR is evidenced as a downstream order-status consumer. The diagram labels its consumption as client notification but does not invent a separate notification transport, client callback endpoint, or notification store.
- The fixture does not evidence a Payment-owned database, so none is shown.
- Fraud, card-network, shipping, and email components are intentionally absent.
