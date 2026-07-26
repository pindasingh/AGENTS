# Evaluation: microservice ownership transition

## Official sources

- https://c4model.com/abstractions/software-system
- https://c4model.com/abstractions/container
- https://c4model.com/abstractions/microservices

## Prompt

System X initially has one team. Services A and B each run an API and own a database schema. Later, Team A independently owns Service A, can deploy it without System X, and hides its implementation from Team X. Team X retains the UI and Service B. Explain the C4 model before and after this ownership change.

## Required outcome

- Before the split, X is one Software System; each service is represented by its API and schema Containers inside X.
- A “microservice” is not an extra C4 abstraction or necessarily one box.
- After the split, Service A can be promoted to a Software System because the prompt establishes independent ownership, responsibility, visibility, and delivery.
- Service A's API and schema remain Containers, now inside Service A's Software System boundary.
- Team X's System Context shows Service A as an external Software System; X's Container view does not expose Service A's internal Containers.
- Service A receives its own System Context and Container views.
- Service B remains Containers inside X while it remains Team X's implementation detail.

## Fail conditions

Fail if the response:

- always classifies every microservice as either a Component or Software System;
- leaves Service A as a Container inside X after accepting the stated ownership boundary;
- promotes Service B without equivalent evidence;
- models an API plus database as one Container;
- shows another team's internal Containers on X's System Context diagram;
- uses team names as C4 elements.
