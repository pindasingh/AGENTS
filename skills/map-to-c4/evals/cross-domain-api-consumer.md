# Evaluation: another domain consumes an API

## Official sources

- https://c4model.com/abstractions/software-system
- https://c4model.com/diagrams/system-context
- https://c4model.com/diagrams/container
- https://c4model.com/diagrams/system-landscape
- https://c4model.com/diagrams/notation

## Prompt

A Fulfilment Software System exposes an HTTP API Container. A separately owned Billing Software System calls that API. Billing belongs to another business domain and is implemented in several repositories. A human operations user also uses Fulfilment directly.

Classify Billing and show it at each relevant C4 level without treating a business domain as a C4 element.

## Required classification

- `Billing` is an **External Software System** relative to a System Context diagram scoped to Fulfilment.
- The business domain name is organisational context; the concrete Billing Software System is the C4 element.
- The human operations user is a **Person**.
- On Fulfilment’s System Context diagram, draw `Billing Software System → Fulfilment Software System` with a specific intent label. Do not include protocol/implementation detail at this level.
- On Fulfilment’s Container diagram, draw `Billing Software System → Fulfilment API Container` and label the HTTP protocol/technology.
- On a broader System Landscape diagram, show Billing and Fulfilment as peer Software Systems with a directional relationship.
- In Billing’s own model, Fulfilment appears as an external Software System; Billing’s internal repositories are resolved into Billing’s own Containers according to runtime/data boundaries.
- If the caller were another Container inside the same Software System rather than a separately owned system, classify it as a Container, not an External Software System.
- If the consumer were human, classify it as a Person rather than a Software System.

## Fail conditions

Fail the evaluation if the response:

- draws a box whose C4 type is `Domain`;
- models every Billing repository as an external Software System;
- models Billing as a Person because it is called a consumer;
- connects Billing only to a generic domain boundary on the Container diagram instead of the API Container;
- includes Billing’s internal Containers on a Fulfilment System Context diagram;
- omits relationship direction or intent;
- omits protocol/technology on the cross-system relationship at Container level;
- merges Billing and Fulfilment into one Software System merely because their business domains interact.
