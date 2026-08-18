# Benchmark material shortlist

The pilot uses the existing curated eShopOnContainers evidence pack. The following public repositories provide a balanced calibration and fixture-construction corpus. Repository metadata, revisions, and license files were verified from GitHub on 2026-08-18. Public and eShop-derived cases are not hidden confirmatory evidence because the model may know them and the paired skill specifications already encode eShop expectations.

## Recommended core corpus

| Material | Architecture/input shape | Fixed revision | License | Best comparison requests |
|---|---|---|---|---|
| [Microsoft eShopOnWeb](https://github.com/dotnet-architecture/eShopOnWeb) | Archived canonical single-repository clean-architecture/monolith sample with explicit project references, composition roots, adapters, and deployable hosts | [`4da8212117e87d808d4bbc7da6286fd2147ce606`](https://github.com/dotnet-architecture/eShopOnWeb/commit/4da8212117e87d808d4bbc7da6286fd2147ce606) | MIT | Broad logical/deployment architecture; checkout request sequence |
| [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) | Single repository, one Spring Boot deployable, package-level owner/pet/visit/vet capabilities, relational persistence | [`88e37c15cf6fc8490b01bc3e8e2c800cec1ac272`](https://github.com/spring-projects/spring-petclinic/commit/88e37c15cf6fc8490b01bc3e8e2c800cec1ac272) | Apache-2.0 | Broad monolith architecture; add-visit request sequence |
| [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices) | Same business domain split across API gateway, customers, visits, vets, config, discovery, and admin services | [`305a1f13e4f961001d4e6cb50a9db51dc3fc5967`](https://github.com/spring-petclinic/spring-petclinic-microservices/commit/305a1f13e4f961001d4e6cb50a9db51dc3fc5967) | Apache-2.0 | Broad microservice architecture; owner-details aggregation sequence |
| [GoogleCloudPlatform microservices-demo](https://github.com/GoogleCloudPlatform/microservices-demo) | Larger polyglot microservices monorepo using Kubernetes and gRPC | [`34ffea9175946982c3088ed84994fe6019ad6e92`](https://github.com/GoogleCloudPlatform/microservices-demo/commit/34ffea9175946982c3088ed84994fe6019ad6e92) | Apache-2.0 | Broad production-like topology; checkout sequence; endpoint impact trace |
| [Microsoft eShopOnContainers](https://github.com/dotnet-architecture/eShopOnContainers) | Event-driven microservices with HTTP acceptance, persistence, message bus, consumers, and outcome branches | [`b6965936842cab32553543c1abe8a68714956f44`](https://github.com/dotnet-architecture/eShopOnContainers/commit/b6965936842cab32553543c1abe8a68714956f44) (`dev`) | MIT | Broad event-driven topology; checkout acceptance and asynchronous order sequence |
| [AsyncAPI Streetlights MQTT](https://github.com/asyncapi/spec/blob/3afe09b227f408fc4547e294c6cf90dcd280f4db/examples/streetlights-mqtt-asyncapi.yml) | Compact machine-readable event topology with broker, MQTT protocol, channels, send/receive operations, messages, payloads, and bindings | [`3afe09b227f408fc4547e294c6cf90dcd280f4db`](https://github.com/asyncapi/spec/commit/3afe09b227f408fc4547e294c6cf90dcd280f4db) | Apache-2.0 | Event topology; operation/message direction; protocol-aware diagram |

Spring PetClinic and its microservices variant are especially valuable because they hold the business domain roughly constant while changing the deployment architecture. This directly tests the requirement that architecture family should not determine the winner. eShopOnWeb adds a stronger project-reference oracle for distinguishing logical modules from deployable runtime boundaries, while AsyncAPI supplies a compact machine-readable directionality oracle.

## Evidence packs to curate

Do not benchmark against whole repositories that continue changing. For each fixed revision, copy a compact evidence pack containing only architecture-relevant files and retain the upstream license and attribution.

### Microsoft eShopOnWeb

Candidate evidence:

- `eShopOnWeb.sln` for the complete project inventory;
- `src/Web/Program.cs`, `src/Web/Configuration/ConfigureCoreServices.cs`, and `ConfigureWebServices.cs` for composition and concrete registrations;
- `src/Web/Web.csproj`, `src/PublicApi/PublicApi.csproj`, `src/ApplicationCore/ApplicationCore.csproj`, and `src/Infrastructure/Infrastructure.csproj` for the dependency graph;
- `src/ApplicationCore/` for domain/application responsibilities;
- `src/Infrastructure/` for persistence and external adapters;
- Dockerfiles and `docker-compose.yml` for runtime/deployment boundaries.

Project references and registrations are the primary oracle. The gold manifest must not equate every project or namespace with a microservice, and it must derive deployable hosts from host projects and deployment configuration rather than from folder names.

### Spring PetClinic monolith

Candidate evidence:

- `README.md`, `pom.xml`, and runtime configuration;
- `owner/OwnerController.java`, `PetController.java`, and `VisitController.java`;
- owner/pet/visit repositories and domain entities;
- `vet/VetController.java` and its repository;
- relational schema and datasource configuration;
- container/deployment configuration when it changes the runtime boundary.

The gold manifest should distinguish one deployable service from internal package responsibilities. A diagram that turns every controller into an independent service should lose precision.

### Spring PetClinic microservices

Candidate evidence:

- `README.md` and `docker-compose.yml`;
- API-gateway routes and owner-details aggregation code;
- customers, visits, and vets service controllers/repositories;
- config-server and discovery-server configuration;
- database configuration for each business service;
- tracing/monitoring components only when the selected prompt includes operational infrastructure.

The gold manifest should keep business services, platform services, stores, and gateway responsibilities distinct.

### Google microservices-demo

Candidate evidence:

- `README.md`, `protos/demo.proto`, and `skaffold.yaml`;
- `docs/architecture-diagram.png` as a secondary expected overview, never as the sole oracle;
- Kubernetes manifests for runtime identities, service names, and configuration;
- frontend call sites;
- checkout-service orchestration;
- cart/Redis, product catalog, currency, payment, shipping, email, recommendation, and ad service entry points;
- feature-flag or telemetry infrastructure only when evidenced and within prompt scope.

This is the large-system readability and scope-control case. The gold manifest should be generated from source and deployment evidence, not copied from a pre-existing diagram alone.

### eShopOnContainers

The repository already contains a compact curated fixture at `skills/build-signal-graph/evals/fixtures/eshop-checkout`. Before the final benchmark, resolve its internal contradiction: the fixture requires a payment-failure path but supplies no payment-failure contract, consumer, state transition, or terminal write. Gold truth should require an explicit unknown gap and forbid invented payment-failure details.

### AsyncAPI Streetlights MQTT

Use exactly:

- `examples/streetlights-mqtt-asyncapi.yml` as the machine-readable topology oracle;
- `spec/asyncapi.md` only to resolve the semantics of servers, channels, operations, messages, and MQTT bindings.

The gold manifest can be generated mechanically: one MQTT server, four channels, one receive operation, three send operations, the exact channel addresses, their associated messages, payload schemas, and QoS binding. Penalize omitted channels, reversed send/receive direction, invented consumers, or incorrect message/channel associations. This case tests explicit event-contract comprehension rather than repository discovery, so report it separately from source-discovery accuracy.

### Optional executable event-infrastructure case

[AWS Serverless Patterns](https://github.com/aws-samples/serverless-patterns) revision [`c407694899b1bfa4575b76e106e259e44d0a15fb`](https://github.com/aws-samples/serverless-patterns/commit/c407694899b1bfa4575b76e106e259e44d0a15fb) provides compact infrastructure oracles. The root repository uses a permissive license file, although GitHub does not return an SPDX identifier for it. Start with `eventbridge-sns/README.md`, `eventbridge-sns/template.yaml`, and `eventbridge-sns/event.json`: the SAM template explicitly declares the EventBridge rule, event pattern, SNS target, and publish policy. Use this as an optional fan-out/routing test rather than letting AWS-specific notation dominate the core score.

## Anti-memorization and uncertainty variants

For each core evidence pack, add two derived cases:

1. **Anonymized variant:** deterministically rename services, contracts, and stores while preserving relationships. This tests evidence recovery rather than recall of a famous sample application.
2. **Evidence-ablation variant:** remove one producer, consumer, or deployment file and ask the pair to mark unresolved relationships. This measures precision and uncertainty discipline.

Keep these variants structurally isomorphic to their source fixture and record every transformation in the gold manifest.

## Proposed balanced run set

| Case | Family | Requested view |
|---|---|---|
| eShopOnWeb | Single-repository clean architecture | Broad logical/deployment architecture |
| eShopOnWeb | Single-repository clean architecture | Checkout sequence |
| PetClinic monolith | Single deployable | Broad architecture |
| PetClinic monolith | Single deployable | Add-visit sequence |
| PetClinic microservices | Distributed | Broad architecture |
| PetClinic microservices | Distributed | Owner-details aggregation sequence |
| Google microservices-demo | Larger distributed system | Broad architecture |
| Google microservices-demo | Larger distributed system | Checkout sequence or endpoint impact |
| eShopOnContainers | Event-driven distributed system | Broad architecture |
| eShopOnContainers | Event-driven distributed system | Checkout-to-outcome sequence |
| AsyncAPI Streetlights | Explicit event contract | Event topology and directionality |
| One anonymized fixture | Architecture-neutral control | Same view as source case |
| One evidence-ablation fixture | Incomplete evidence control | Diagram plus explicit unknowns |

For a compact harness calibration, use eShopOnWeb broad architecture, Google microservices-demo broad architecture, eShopOnContainers checkout sequence, and AsyncAPI Streetlights event topology. Run each three times per pair. Expand to the PetClinic architecture-controlled pair and other cases after the scoring machinery behaves reliably. Use the unseen/renamed six-case matrix in `blind-protocol.md` for the confirmatory winner decision. Macro-average by family and requested view.
