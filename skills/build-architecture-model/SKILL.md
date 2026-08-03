---
name: build-architecture-model
description: Scans one or many code repositories incrementally and builds an evidence-backed, C4-neutral reconciled architecture model of runtimes, stores, interfaces, contracts, dependencies, operations, conflicts, and gaps. Use before architecture mapping, C4 generation, cross-repository dependency analysis, system discovery, or architecture impact analysis.
---

# Build Architecture Model

Discover the architecture of a user-named subject one repository at a time. The subject can be a system, product, platform, service estate, business domain, or another explicitly selected scope; do not assume DDD. Produce accurate repository-local findings first and reconcile them into one reconciled working model after every repository. Do not draw C4 diagrams in this skill or assign C4 abstraction types during discovery.

Before scanning, read [references/model-spec.md](references/model-spec.md) and [references/reconciled-model.md](references/reconciled-model.md) completely. Read the applicable framework playbooks under `references/` after detecting the repository technologies.

## Runtime tooling

Use `scripts/model_json.py` to initialize the artifact set and perform cheap JSON preflight checks. The script and all bundled Python tooling use **only the Python standard library**: do not install packages, add a dependency file, import a third-party module, or depend on a network service. Keep `.architecture-model/` in the target repository or user-selected workspace, not inside the skill directory.

The helper deliberately does not invent or reconcile architecture. The agent authors bounded scans, applies the documented identity rules, and performs semantic review; use the script to avoid spending tokens on boilerplate and repetitive syntax inspection. Do not verify generated boilerplate line by line.

```bash
python3 scripts/model_json.py init .architecture-model --subject "<subject>" --source "<source>"
python3 scripts/model_json.py validate-json .architecture-model
```

## Required result

The model directory is the only architecture-model deliverable. Do not substitute a prose report, Markdown inventory, diagram, alternate JSON shape, or conversation-only findings. Create exactly this structure:

```text
.architecture-model/
  subject.json
  decisions.json
  progress.json
  scans/<source-id>.json
  model.json
```

- Agents author one bounded scan JSON document per repository.
- `decisions.json` preserves explicit identity, ownership, and boundary decisions.
- `progress.json` is the persisted workflow ledger. It identifies the one active source and records the completed gates for each requested source. The agent updates it only at the transitions defined below.
- `model.json` is the sole reconciled architecture model. Update it only from validated scan observations and explicit decisions.
- The reconciled model is the durable working memory read before scanning the next repository.
- Prose in the final response may only summarize completion, gaps, conflicts, and file locations; it must not become a second architecture model.

Copy all five starting shapes: [assets/subject-template.json](assets/subject-template.json), [assets/decisions-template.json](assets/decisions-template.json), [assets/progress-template.json](assets/progress-template.json), [assets/scan-template.json](assets/scan-template.json), and [assets/model-template.json](assets/model-template.json). Use [references/model-spec.md](references/model-spec.md) for repository-local artifacts and [references/reconciled-model.md](references/reconciled-model.md) for every nested `model.json` record. Replace example values rather than inventing a different structure. The contract is closed: do not add convenience top-level fields or create a second model format.

## Validation without bundled scripts

Validation is a deliberate agent review, not merely successful JSON parsing. Before setting a validation gate or handing the directory to another skill, perform all four layers:

1. **Syntax:** every artifact is strict UTF-8 JSON with `schemaVersion: 1` and no placeholder values.
2. **Structure:** every object uses only the fields, value types, enums, and required collections defined by the templates and references.
3. **References:** progress entries match scans; every model endpoint, owner, member, interface, relationship, flow step, source finding, and decision reference resolves.
4. **Semantics:** direction, identity, certainty, versions, evidence, gaps, conflicts, and confirmed decisions remain faithful to the scans.

If any layer fails, reset the affected progress gate and later gates, repair the authoritative artifact, and repeat the review. Do not describe a model as validated when only its JSON syntax was checked.

## Scope authority

The user's named subject selects the scope without determining its architecture type. Record its name, description, aliases, supplied roots, and exclusions in `subject.json`. Do not assume the subject is a DDD domain, bounded context, or C4 Software System. Do not search only for subject-name words; broadly inventory every supplied repository so wiring with unrelated terminology is not missed.

Repository structure is evidence, not architecture truth. One repository can contain several runtime units, and one runtime can be assembled from several repositories. A shared package is not a running service. A Docker image is deployment evidence, not a C4 classification.

## Per-repository transaction

For each source, complete this bounded cycle before opening the next source. Whenever starting or resuming, read `progress.json` first; its `activeSource`, `stage`, and gates are authoritative, not conversation memory.

1. Read repository instructions.
2. Identify the exact repository, revision, branch, and scan coverage.
3. Select the next `pending` source, set only that entry to `scanning`, set `activeSource`, and then read the current `subject.json`, `decisions.json`, and `model.json`.
4. Inventory solutions/workspaces, build outputs, executable entry points, deployment descriptors, configuration, generated code, tests, and documentation.
5. Discover all runtime units, stores, channels, shared libraries, inbound interfaces, outbound dependencies, and architecturally meaningful operations.
6. Write or replace only `scans/<source-id>.json`.
7. Self-check the scan field by field against the template and model specification. Set its `scanWritten` and `scanValidated` gates true only after the matching scan exists, has exact revision and coverage, and passes every completion item below.
8. Review newly resolved identities, contract conflicts, candidate external targets, and gaps.
9. Reconcile the scan into `model.json`, re-read the result, and then set `modelUpdated`, `gapsReviewed`, and `conflictsReviewed` true. Set the source to `complete` and clear `activeSource` only when all five gates are true.
10. Re-read `progress.json`; only start the next pending source when `activeSource` is null.

Never jump a stage or pre-mark a gate. If an artifact changes after its gate was set, reset that gate and every later gate to false, return the source to the corresponding stage, and repeat the checks. The progress ledger is an agent handoff protocol, not executable enforcement: it cannot prevent a dishonest agent from writing false values, but it keeps a compliant agent on track across context loss and makes skipped work visible to the next agent.

Do not defer reconciliation until every repository has been scanned. Do not copy findings from one scan into another. Re-scanning a source replaces its repository-local observations and requires the agent to update the reconciled model.

## Record facts, not C4 guesses

Repository scan files use discovery kinds such as `runtime`, `store`, `channel`, `library`, `external`, and `person`. Runtime subtypes can include API, worker, MFE, scheduler, function, browser application, or another observed form. These are factual discovery classifications, not C4 types.

For each unit, capture:

- name, responsibility, discovery kind/subtype, and technology;
- deployment or logical identity signals;
- inbound interfaces;
- outbound dependencies;
- ownership only when evidenced;
- exact source anchors and observations.

For every inbound interface, capture what is observed and architecturally useful:

- HTTP/gRPC method, path/service, and API version;
- event/message channel, subscription or consumer group, and event version;
- scheduled-job trigger;
- request, response, event, or command contract identity;
- schema location or fingerprint and only key correlation/routing/security fields;
- authentication, routing rules, and filters when they affect callers or architectural paths.

For every outbound dependency, capture:

- source and intended target identity;
- dependency kind and explicit purpose;
- technology/protocol;
- API, event, or contract version;
- destination route, service, store/schema, queue/topic, package, or remote identity;
- rules that affect whether or where the dependency is invoked;
- evidence.

`from` and `to` in each model relationship define runtime direction. Do not replace direction with a vague `dependsOn`. Keep compile/package dependencies distinct from runtime requests, message flow, data access, and UI composition.

## Right level of detail

Enumerate every public inbound interface and every outbound architectural dependency so relationship coverage can be evaluated. Do not copy full payloads or reproduce ordinary implementation detail.

Capture a payload schema reference, version, fingerprint, and key fields when useful for matching or architecture. Do not copy every DTO property.

Capture rules that change:

- authorization or accepted callers;
- routing, partitioning, or filtering;
- whether a downstream call/message occurs;
- ownership or state progression;
- retry, outbox, idempotency, or compensation behavior when architecturally significant.

Do not capture every field validator, object mapping, logging statement, MediatR pipeline behavior, helper method, or framework call.

MediatR, CQS, MassTransit, MobX, and design systems are mechanisms or shared artifacts unless evidence establishes a separately running boundary. Use framework-specific wiring to trace operations, not to manufacture nodes.

## Identity and reconciliation

Use strong identity signals before names:

1. explicit confirmed override in `decisions.json`;
2. deployment/runtime identity;
3. exact database/catalog/schema, bucket, index, queue, or topic identity;
4. exact configured service address and compatible interface;
5. compatible contract name, version, and fingerprint;
6. generated client/server origin or integration test evidence;
7. package identity;
8. names and textual similarity only as candidate evidence.

Never merge incompatible API or event versions silently. Never infer an inbound caller merely because an endpoint exists. Reconcile callers only from outbound findings matched to compatible inbound interfaces. Leave unmatched targets as candidates or gaps.

A shared physical database host and a shared logical data store are different facts. Distinguish server/cluster, database/catalog, schema, index, and migration ownership. Several services using one logical store produce several directional relationships to one model store identity; they do not produce duplicate databases.

Use `decisions.json` for explicit identity/target overrides and candidate/confirmed/rejected system boundaries. Preserve confirmed decisions across rescans. Do not encode uncertain guesses as decisions.

## Operations and flows

Record one operation for a concrete inbound interface when it adds architectural value. Use a short ordered step list. A step either executes at a local unit or uses one of the owner's outbound dependencies. Add `next` only for an evidenced branch, parallel continuation, failure, or retry that materially changes the architectural story.

Do not build a detailed causal/event-sourcing model. Keep local implementation steps only when they explain a meaningful rule or boundary crossing. Map local dependency references to model relationships during reconciliation; downstream tools can turn selected flows into Dynamic diagrams.

## Fail-closed accuracy

Use certainty values only in the reconciled model: `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`. Repository scan documents contain observations and explicit gaps; apply the reconciliation rules in the model specification consistently to determine corroboration.

Record a gap when configuration is injected externally, a target cannot be resolved, a caller is absent from supplied roots, generated code hides an origin, reflection prevents tracing, or ownership cannot be established. Record concrete searches and architectural impact. Unknown is preferable to a polished guess.

## Completion gate

Do not report gathering complete until:

- [ ] Every supplied source has one validated scan with an exact revision and coverage status.
- [ ] Every detected executable/runtime and logical store is represented or explicitly excluded.
- [ ] Every discovered inbound interface is inventoried with version/contract details when observed.
- [ ] Every outbound architectural dependency has direction, purpose, technology, target identity, and evidence.
- [ ] Every operation selected for Dynamic/Component analysis maps to an inbound interface and evidenced steps; other public interfaces remain inventoried without forced flow detail.
- [ ] Shared packages, generated clients, contracts, migrations, and design systems are not mistaken for runtimes.
- [ ] API/event versions and incompatible contracts have not been silently merged.
- [ ] Database server, logical database/schema, and data access are distinguished.
- [ ] Candidate callers and targets remain gaps rather than fabricated relationships.
- [ ] `progress.json` has no active source; every requested source is `complete`; every gate is true; and each recorded source ID/revision matches its scan.
- [ ] Reconciliation applies the same identity and ordering rules regardless of repository scan order.
- [ ] Every `model.json` record matches [references/reconciled-model.md](references/reconciled-model.md), every reference resolves, and `model.systemBoundaries` exactly mirrors `decisions.systemBoundaries`.
- [ ] Re-reading the complete `.architecture-model/` directory passes syntax, structure, reference, and semantic validation; no single file is handed off in isolation.

Apply every Markdown case under `evals/` to agent behavior. Matching a fail condition is a regression.
