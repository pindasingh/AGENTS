# Benchmark material shortlist

The pilot uses the existing curated eShopOnContainers evidence pack. The following public repositories provide a balanced expansion corpus. Repository metadata, revisions, and license files were verified from GitHub on 2026-08-18.

## Recommended core corpus

| Material | Architecture/input shape | Fixed revision | License | Best comparison requests |
|---|---|---|---|---|
| [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) | Single repository, one Spring Boot deployable, package-level owner/pet/visit/vet capabilities, relational persistence | [`88e37c15cf6fc8490b01bc3e8e2c800cec1ac272`](https://github.com/spring-projects/spring-petclinic/commit/88e37c15cf6fc8490b01bc3e8e2c800cec1ac272) | Apache-2.0 | Broad monolith architecture; add-visit request sequence |
| [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices) | Same business domain split across API gateway, customers, visits, vets, config, discovery, and admin services | [`305a1f13e4f961001d4e6cb50a9db51dc3fc5967`](https://github.com/spring-petclinic/spring-petclinic-microservices/commit/305a1f13e4f961001d4e6cb50a9db51dc3fc5967) | Apache-2.0 | Broad microservice architecture; owner-details aggregation sequence |
| [GoogleCloudPlatform microservices-demo](https://github.com/GoogleCloudPlatform/microservices-demo) | Larger polyglot microservices monorepo using Kubernetes and gRPC | [`34ffea9175946982c3088ed84994fe6019ad6e92`](https://github.com/GoogleCloudPlatform/microservices-demo/commit/34ffea9175946982c3088ed84994fe6019ad6e92) | Apache-2.0 | Broad production-like topology; checkout sequence; endpoint impact trace |
| [Microsoft eShopOnContainers](https://github.com/dotnet-architecture/eShopOnContainers) | Event-driven microservices with HTTP acceptance, persistence, message bus, consumers, and outcome branches | [`b6965936842cab32553543c1abe8a68714956f44`](https://github.com/dotnet-architecture/eShopOnContainers/commit/b6965936842cab32553543c1abe8a68714956f44) (`dev`) | MIT | Broad event-driven topology; checkout acceptance and asynchronous order sequence |

Spring PetClinic and its microservices variant are especially valuable because they hold the business domain roughly constant while changing the deployment architecture. This directly tests the requirement that architecture family should not determine the winner.

## Evidence packs to curate

Do not benchmark against whole repositories that continue changing. For each fixed revision, copy a compact evidence pack containing only architecture-relevant files and retain the upstream license and attribution.

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
- Kubernetes manifests for runtime identities, service names, and configuration;
- frontend call sites;
- checkout-service orchestration;
- cart/Redis, product catalog, currency, payment, shipping, email, recommendation, and ad service entry points;
- feature-flag or telemetry infrastructure only when evidenced and within prompt scope.

This is the large-system readability and scope-control case. The gold manifest should be generated from source and deployment evidence, not copied from a pre-existing diagram alone.

### eShopOnContainers

The repository already contains a compact curated fixture at `skills/build-signal-graph/evals/fixtures/eshop-checkout`. Before the final benchmark, resolve its internal contradiction: the fixture requires a payment-failure path but supplies no payment-failure contract, consumer, state transition, or terminal write. Gold truth should require an explicit unknown gap and forbid invented payment-failure details.

## Anti-memorization and uncertainty variants

For each core evidence pack, add two derived cases:

1. **Anonymized variant:** deterministically rename services, contracts, and stores while preserving relationships. This tests evidence recovery rather than recall of a famous sample application.
2. **Evidence-ablation variant:** remove one producer, consumer, or deployment file and ask the pair to mark unresolved relationships. This measures precision and uncertainty discipline.

Keep these variants structurally isomorphic to their source fixture and record every transformation in the gold manifest.

## Proposed balanced run set

| Case | Family | Requested view |
|---|---|---|
| PetClinic monolith | Single deployable | Broad architecture |
| PetClinic monolith | Single deployable | Add-visit sequence |
| PetClinic microservices | Distributed | Broad architecture |
| PetClinic microservices | Distributed | Owner-details aggregation sequence |
| Google microservices-demo | Larger distributed system | Broad architecture |
| Google microservices-demo | Larger distributed system | Checkout sequence or endpoint impact |
| eShopOnContainers | Event-driven distributed system | Broad architecture |
| eShopOnContainers | Event-driven distributed system | Checkout-to-outcome sequence |
| One anonymized fixture | Architecture-neutral control | Same view as source case |
| One evidence-ablation fixture | Incomplete evidence control | Diagram plus explicit unknowns |

Run each case three times per pair and macro-average by family and requested view.
