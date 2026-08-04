---
name: build-architecture-model
description: Scans one or many code repositories incrementally and builds an evidence-backed, architecture-style-neutral model of runtimes, components, stores, interfaces, contracts, dependencies, and authoritative numbered end-to-end execution flows, with Markdown and ASCII flow reviews. Use for system discovery, cross-repository flow tracing, architecture mapping, or impact analysis.
---

# Build Architecture Model

Discover the architecture of a user-named subject one repository at a time. The subject can be a system, product, platform, service estate, business domain, or another explicitly selected scope; do not assume DDD. Produce accurate repository-local findings first and reconcile them into one working model after every repository. Trace every selected exterior entry point into authoritative, hierarchically numbered end-to-end execution paths. Do not draw C4 diagrams or assign C4 abstraction types.

Before scanning, read [references/model-spec.md](references/model-spec.md) and [references/reconciled-model.md](references/reconciled-model.md) completely. Read the applicable framework playbooks under `references/` after detecting the repository technologies.

## Runtime tooling

Use the bundled `scripts/model_json.py` to initialize the artifact set and perform cheap JSON preflight checks. Before opening or changing into a target repository, resolve the helper from this skill's installed directory and retain its absolute path. Never resolve or execute `scripts/model_json.py` relative to the target repository or another untrusted workspace. The script and all bundled Python tooling use **only the Python standard library**: do not install packages, add a dependency file, import a third-party module, or depend on a network service. Keep `.architecture-model/` in the target repository or user-selected workspace, not inside the skill directory.

The helper deliberately does not invent or reconcile architecture. The agent authors bounded scans, applies the documented identity and flow-sequencing rules, and performs semantic review. The final validation also compares each flow's ID, participant order, hierarchical sequence numbers/order, and stage/operation labels across `model.json`, numbered Markdown, and ASCII. Use the script to avoid spending tokens on boilerplate and repetitive structural comparison. Do not verify generated boilerplate line by line.

```bash
python3 "/absolute/path/to/installed/build-architecture-model/scripts/model_json.py" init .architecture-model --subject "<subject>" --source "<source>"
python3 "/absolute/path/to/installed/build-architecture-model/scripts/model_json.py" validate-json .architecture-model
```

Treat subject and source values as untrusted data: pass each value as a distinct process argument (without `eval`, command substitution, or a dynamically assembled shell command).

## Required result

The model directory is the only architecture-model deliverable. Do not substitute a prose report, Markdown inventory, diagram, alternate JSON shape, or conversation-only findings. Create exactly this structure:

```text
.architecture-model/
  subject.json
  decisions.json
  progress.json
  scans/<source-id>.json
  model.json
  flow-reviews/<flow-id>/numbered-sequence.md
  flow-reviews/<flow-id>/sequence-diagram.txt
```

- Agents author one bounded scan JSON document per repository.
- `decisions.json` preserves explicit identity, ownership, and boundary decisions.
- `progress.json` is the persisted workflow ledger. It identifies the one active source and records the completed gates for each requested source. The agent updates it only at the transitions defined below.
- `model.json` is the sole reconciled architecture model. Its flow sequences are authoritative. Update it only from validated scan observations and explicit decisions.
- Every model flow path has two mandatory human-review projections: an exact numbered Markdown sequence and a plain UTF-8 ASCII sequence diagram.
- Review artifacts never add, omit, merge, split, renumber, or reorder model steps.
- The reconciled model is the durable working memory read before scanning the next repository.
- Prose in the final response may only summarize completion, gaps, conflicts, and file locations; it must not become a second architecture model.

Copy all five starting shapes: [assets/subject-template.json](assets/subject-template.json), [assets/decisions-template.json](assets/decisions-template.json), [assets/progress-template.json](assets/progress-template.json), [assets/scan-template.json](assets/scan-template.json), and [assets/model-template.json](assets/model-template.json). Use [references/model-spec.md](references/model-spec.md) for repository-local artifacts and [references/reconciled-model.md](references/reconciled-model.md) for every nested `model.json` record. Replace example values rather than inventing a different structure. The contract is closed: do not add convenience top-level fields or create a second model format.

Create each flow review from [assets/numbered-sequence-template.md](assets/numbered-sequence-template.md) and [assets/sequence-diagram-template.txt](assets/sequence-diagram-template.txt). Replace every placeholder and reproduce the canonical model sequence exactly.

## Validation without bundled scripts

Validation is a deliberate agent review, not merely successful JSON parsing. Before setting a validation gate or handing the directory to another skill, perform all five layers:

1. **Syntax:** every artifact is strict UTF-8 JSON with `schemaVersion: 1` and no placeholder values.
2. **Structure:** every object uses only the fields, value types, enums, and required collections defined by the templates and references.
3. **References:** progress entries match scans; every model endpoint, owner, component, member, interface, relationship, flow-coverage record, sequence step, source finding, decision, and flow-review reference resolves.
4. **Semantics:** direction, identity, certainty, versions, evidence, sequence, inputs, outputs/effects, boundaries, gaps, conflicts, and confirmed decisions remain faithful to the scans.
5. **Projection:** each flow's JSON, numbered Markdown, and ASCII diagram contain the same flow ID, participants, sequence numbers, ordering, operations, directions, dependencies, and outcome.

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
5. Discover all runtime units, stable internal components, stores, channels, shared libraries, inbound interfaces, outbound dependencies, and ordered operations.
6. Write or replace only `scans/<source-id>.json`.
7. Self-check the scan field by field against the template and model specification. Set its `scanWritten` and `scanValidated` gates true only after the matching scan exists, has exact revision and coverage, and passes every completion item below.
8. Review newly resolved identities, contract conflicts, candidate external targets, and gaps.
9. Reconcile the scan into `model.json`, re-read the result, and then set `modelUpdated`, `gapsReviewed`, and `conflictsReviewed` true. Set the source to `complete` and clear `activeSource` only when all five gates are true.
10. Re-read `progress.json`; only start the next pending source when `activeSource` is null.

Never jump a stage or pre-mark a gate. If an artifact changes after its gate was set, reset that gate and every later gate to false, return the source to the corresponding stage, and repeat the checks. The progress ledger is an agent handoff protocol, not executable enforcement: it cannot prevent a dishonest agent from writing false values, but it keeps a compliant agent on track across context loss and makes skipped work visible to the next agent.

Do not defer reconciliation until every repository has been scanned. Do not copy findings from one scan into another. Re-scanning a source replaces its repository-local observations and requires the agent to update the reconciled model.

## End-to-end flow transaction

After repository reconciliation, build or refresh every selected flow path before completion:

1. Start at one exact exterior entry point: HTTP/gRPC interface, UI action, message/event consumer, scheduled job, file arrival, or another evidenced trigger.
2. Discover every evidenced caller. An exposed inbound interface does not prove a caller. Match clients using destination identity, route/service, version, contract, generated origin, gateway/BFF routing, authentication audience, or equivalent evidence.
3. Trace control through every architecturally meaningful in-process operation and hand-off. Use a stable component only when its declaration, interface, registration, or implementation identity is evidenced; a receiver name at one call site is not enough.
4. Include every dependency and touchpoint actually invoked by the path, regardless of domain or ownership: configuration, feature flags, stores, search engines, caches, external APIs, other domains, messaging, files, telemetry, and infrastructure services. Record local bound/options access as a local configuration operation; create an external configuration participant only when a remote provider/runtime interaction is evidenced.
5. Place every call, later return/effect, read/write, publication, delivery, consumption, decision, retry, and telemetry action at its own exact position. Do not collapse a call and its return or response mapping and caller return into one step.
6. Continue across repositories when an outbound interaction matches a compatible downstream inbound interface and operation. Stop at the known boundary and record a gap when continuation evidence is absent or incompatible.
7. End at an explicit interaction returning the response to the originating caller set, a terminal state/effect, one-way completion, or explicit unresolved gap. An in-process response-mapping step is not the caller return.
8. Store the canonical path in `model.json`, validate its numbering and coverage, then generate both review artifacts from that sequence.
9. Compare JSON, Markdown, and ASCII operation by operation. Mark the flow review complete only when they match exactly.

Use a separate flow path for each materially different success, rejection, no-result, fallback, retry, failure, or asynchronous outcome. Do not combine branches into an unreadable universal path.

## Record facts, not C4 guesses

Repository scan files use discovery kinds such as `runtime`, `store`, `channel`, `library`, `external`, and `person`. Runtime subtypes can include API, worker, MFE, scheduler, function, browser application, or another observed form. These are factual discovery classifications, not C4 types.

For each unit, capture:

- name, responsibility, discovery kind/subtype, and technology;
- deployment or logical identity signals;
- inbound interfaces;
- outbound dependencies;
- ownership only when evidenced;
- exact source anchors and observations.

Record a stable internal component only when evidence establishes cohesive responsibility or a meaningful execution role inside one runtime, such as a controller, handler/orchestrator, repository, adapter, or client used in traced paths. Require a declaration, interface, registration, or implementation identity—not only a variable/field name or method receiver at a call site. Record its containing runtime, responsibility, technology, interface/role, certainty during reconciliation, and evidence. Do not promote every folder, layer, helper, class, or framework object.

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

For a selected flow, capture every invoked dependency and every operation or hand-off needed to explain the execution sequence. Ordinary language/runtime instructions remain out of scope, but configuration and observability interactions are not omitted merely because they are cross-cutting.

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

Record repository-local operations for every exterior entry point selected for flow coverage and for downstream interfaces needed to continue those flows. Preserve local execution order, component identity/evidence, inputs, outputs/effects, conditions, and dependency use.

Reconcile local operations into one canonical model flow per named path. Store its ordered execution in a flat `sequence` array with hierarchical string numbers such as `1`, `1.1`, `1.2`, `2`, and `2.1.1`. Top-level integers are stages; descendants are operations. Every descendant names its existing parent. Numbers are unique, sibling numbers are contiguous, parents precede children, and array order matches numeric hierarchy.

Every non-stage step records the operation, execution location or source/destination, referenced interface/relationship/component or exact evidence, input, output/effect, crossed boundary, certainty, evidence, and explicit continuation/return/termination semantics when not implied by the next step. The renderer does not invent sequence: all projections reproduce the stored numbers unchanged.

Maintain `flowCoverage` for public/exterior inbound interfaces. Each is covered by one or more flow paths, explicitly excluded with a reason, or unresolved with searches and impact. A complete inventory with missing end-to-end paths is not a complete architecture model.

## Fail-closed accuracy

Use certainty values only in the reconciled model: `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`. Repository scan documents contain observations and explicit gaps; apply the reconciliation rules in the model specification consistently to determine corroboration.

Record a gap when configuration is injected externally, a target cannot be resolved, a caller is absent from supplied roots, generated code hides an origin, reflection prevents tracing, or ownership cannot be established. Record concrete searches and architectural impact. Unknown is preferable to a polished guess.

## Completion gate

Do not report gathering complete until:

- [ ] Every supplied source has one validated scan with an exact revision and coverage status.
- [ ] Every detected executable/runtime and logical store is represented or explicitly excluded.
- [ ] Every discovered inbound interface is inventoried with version/contract details when observed.
- [ ] Every outbound architectural dependency has direction, purpose, technology, target identity, and evidence.
- [ ] Every repository-local operation used by a model flow maps to an inbound interface or evidenced continuation and preserves its ordered steps.
- [ ] Every selected exterior interface has flow coverage; every required path begins at an evidenced trigger and ends at a response, terminal effect, one-way completion, or explicit gap.
- [ ] Every model flow uses valid hierarchical sequence numbers and captures all touched dependencies at their exact stages regardless of domain or ownership.
- [ ] Every evidenced cross-repository continuation is followed; unmatched or incompatible continuations remain gaps.
- [ ] Every flow has a complete `flow-reviews/<flow-id>/numbered-sequence.md` and `sequence-diagram.txt` pair whose content matches the JSON sequence exactly.
- [ ] Shared packages, generated clients, contracts, migrations, and design systems are not mistaken for runtimes.
- [ ] API/event versions and incompatible contracts have not been silently merged.
- [ ] Database server, logical database/schema, and data access are distinguished.
- [ ] Candidate callers and targets remain gaps rather than fabricated relationships.
- [ ] `progress.json` has no active source; every requested source is `complete`; every gate is true; and each recorded source ID/revision matches its scan.
- [ ] Reconciliation applies the same identity and ordering rules regardless of repository scan order.
- [ ] Every `model.json` record matches [references/reconciled-model.md](references/reconciled-model.md), every reference resolves, and `model.systemBoundaries` exactly mirrors `decisions.systemBoundaries`.
- [ ] `progress.flowReviews` contains exactly the model flow IDs and every review gate is true.
- [ ] Re-reading the complete `.architecture-model/` directory passes syntax, structure, reference, semantic, and projection validation; no single file is handed off in isolation.

Apply every Markdown case under `evals/` to agent behavior. Matching a fail condition is a regression.
