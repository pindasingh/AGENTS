# Build-architecture-model reasoning evaluations

Apply every case to changes in gathering instructions and to representative agent runs. Any fail condition is a regression.

## Persisted stage tracking

### Prompt

The agent resumes after context compaction, sees some scan files, assumes the work is near completion, and proposes jumping directly to the final response.

### Required outcome

Read `progress.json`, resume its single active source at the recorded stage, and advance its gates in order. A source cannot become complete until its scan is written and self-checked, canonical reconciliation is updated, and gaps and conflicts are reviewed. Final completion requires no active source and every requested source complete with all gates true.

### Fail conditions

- Uses conversation memory or file presence instead of the workflow ledger to infer the current stage.
- Starts a second repository while another source is active.
- Marks a source complete with a false or missing gate, or without a matching scan revision.
- Reports final completion while the ledger contains an active or unfinished source.

## Canonical output contract

### Prompt

After scanning a repository, the agent offers a polished Markdown architecture report and a hand-maintained JSON file whose fields resemble the canonical model.

### Required outcome

Treat `.architecture-model/` as the only model deliverable, author findings only in the prescribed scan shape, and reconcile them into the prescribed `canonical.json` shape. Re-read the scans, decisions, canonical model, and progress gates before handoff. Keep any final prose to a status summary and pointers to the artifacts.

### Fail conditions

- Substitutes Markdown, diagrams, or an alternate JSON format for the required model directory.
- Adds free-form top-level fields to a scan.
- Calls a stale `canonical.json` canonical when it does not reflect every current scan and decision.
- Completes without re-reading the artifacts and satisfying every progress gate.

## Repository-by-repository checkpointing

### Prompt

The user supplies seven repositories. The agent proposes reading all repositories, holding findings in conversation context, and writing one model at the end.

### Required outcome

Initialize the model and ledger, scan one repository, self-check its scan, reconcile and re-read `canonical.json`, review gaps/conflicts, mark its gates complete, and only then continue. Read the updated canonical model and progress ledger before each next scan.

### Fail conditions

- Defers all persisted output until the final repository.
- Updates `canonical.json` without reconciling it from the current scans and decisions.
- Copies one repository's findings into another repository's scan.

## API caller and version

### Prompt

API A exposes `POST /api/v2/orders`. MFE B has a generated v1 client. No v2 caller is found.

### Required outcome

Record the v2 inbound interface and v1 outbound client separately. Do not claim MFE B calls v2. Preserve the incompatible version and an unresolved v2 caller when caller coverage matters.

### Fail conditions

- Infers B as the v2 caller from similar names.
- Drops either version.
- Rewrites both observations to an unversioned `Orders API` relationship.

## Event producer and consumer

### Prompt

API A publishes `OrderSubmitted` v3 to topic `order-submitted`. Worker B consumes v3 from subscription `search`. Worker C consumes v2 from subscription `legacy`.

### Required outcome

Record the channel once, separate directional publish/delivery relationships, compatible v3 corroboration, and the v2 conflict. Preserve subscriptions and contract evidence.

### Fail conditions

- Merges v2 and v3.
- Reverses consumer-to-producer runtime direction.
- Treats MassTransit as the business service.
- Creates one aggregate consumer relationship that loses B/C identities.

## Shared database

### Prompt

API A and workers B/C use the same SQL server and `Orders/fulfilment` schema. API D uses the same server/database but the `billing` schema.

### Required outcome

Create one logical fulfilment store with A/B/C access relationships and a separate billing store for D. Preserve read/write/migration purposes independently. Physical co-hosting is deployment evidence, not logical-store identity.

### Fail conditions

- Creates one database per repository.
- Merges fulfilment and billing because the server matches.
- Infers shared identity from a common configuration key alone.

## React MFE and design system

### Prompt

A React shell runtime-loads two Module Federation remotes. All three use the same MobX helpers and design-system package.

### Required outcome

Record evidenced independently delivered browser runtimes and host-to-remote loading direction. Record MobX/design-system artifacts as library dependencies, not runtime services.

### Fail conditions

- Creates a service/container candidate for each MobX store or package.
- Omits runtime MFE composition.
- Reverses remote-loading direction.

## Rules and payload detail

### Prompt

An endpoint has 45 DTO fields and 20 field-validation rules. A tenant-routing rule chooses one of two downstream APIs, and an event uses `tenantId` and `orderId` for routing/correlation.

### Required outcome

Retain contract name/version/schema or fingerprint, `tenantId`/`orderId`, and the routing rule. Do not copy all DTO fields or ordinary field validators.

### Fail conditions

- Copies the complete payload and validation implementation into the architecture model.
- Omits the routing decision or key correlation fields.
- Invents payload fields absent from source.

## Unavailable runtime configuration

### Prompt

An outbound base address is injected from an unavailable secret/configuration service. Only the options key `PaymentsBaseUrl` is visible.

### Required outcome

Record the observed outbound dependency candidate, configuration key, searches, and gap. Do not identify a concrete Payments system without corroborating evidence.

### Fail conditions

- Converts the options-key name directly into a confirmed runtime identity.
- Omits the unresolved dependency because it cannot be mapped.
- Claims complete coverage without the configuration gap.
