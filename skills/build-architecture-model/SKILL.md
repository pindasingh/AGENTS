---
name: build-architecture-model
description: Discover one or many related code repositories and build an evidence-backed, sharded architecture graph organized as domain → components → operations → authoritative numbered end-to-end paths. Use whenever a user needs cross-repository system discovery, caller tracing from web/mobile/CLI/jobs/messages, dependency and impact analysis, reproducible sequence diagrams, architecture change detection, or an architecture model for downstream mapping. Prefer this skill over a prose inventory or one large JSON model.
---

# Build Architecture Model

Build a navigable architecture graph for a user-selected domain or other scope. Discover repository-local facts, reconcile stable graph entities, and trace each selected operation from every evidenced caller through components and dependencies to a response, terminal effect, or explicit gap.

The model is deliberately **sharded**. Never create a monolithic `model.json`. `index.json` contains only references, hierarchy, and hashes; detailed facts live in independently reviewable files. Operation paths are the execution authority. Markdown and ASCII are deterministic projections generated from those paths, not separately authored interpretations.

Before gathering, read [references/model-spec.md](references/model-spec.md) and [references/sharded-graph.md](references/sharded-graph.md) completely. After detecting technologies, read the applicable framework playbooks under `references/`. Use [examples/order-submission/README.md](examples/order-submission/README.md) when the user needs to inspect a concrete result before or during a run.

## Trusted standard-library tooling

Resolve `scripts/architecture_model.py` from this installed skill directory before changing into an untrusted repository. Retain and invoke that absolute path. The helper uses only the Python standard library; do not install packages or use a network-backed renderer.

```bash
python "/absolute/skill/path/scripts/architecture_model.py" init .architecture-model --subject "<scope>" --source "<root-or-repository>"
python "/absolute/skill/path/scripts/architecture_model.py" format .architecture-model
python "/absolute/skill/path/scripts/architecture_model.py" render .architecture-model
python "/absolute/skill/path/scripts/architecture_model.py" index .architecture-model
python "/absolute/skill/path/scripts/architecture_model.py" validate .architecture-model
python "/absolute/skill/path/scripts/architecture_model.py" diff before/index.json after/index.json --output changes/latest.json
```

Pass subject and source values as distinct process arguments. Do not use `eval`, command substitution, or a dynamically assembled shell command.

The agent discovers and reconciles architecture. The helper provides deterministic initialization, canonical JSON formatting, indexing, rendering, semantic/evidence change classification, and fail-closed structural/reference validation. It cannot decide architectural identity or replace evidence review.

## Required output

Create only this architecture-model directory:

```text
.architecture-model/
  index.json
  subject.json
  decisions.json
  progress.json
  sources/<source-id>/scan.json
  domains/<domain-id>.json
  nodes/<node-id>.json
  components/<component-id>.json
  interfaces/<interface-id>.json
  relationships/<relationship-id>.json
  operations/<operation-id>/operation.json
  operations/<operation-id>/paths/<path-id>.json
  gaps/<gap-id>.json
  conflicts/<conflict-id>.json
  projections/<operation-id>/<path-id>/numbered-sequence.md
  projections/<operation-id>/<path-id>/sequence-diagram.txt
  changes/<comparison-id>.json                 # when comparing snapshots
```

Do not add a reconciled aggregate containing copied entities. A fact has one canonical shard and is connected elsewhere by stable ID. This prevents unrelated changes from rewriting a large document and lets agents load only the domain, component, operation, or path relevant to the task.

## Model hierarchy

Use these layers consistently:

1. **Domain/scope** references its source repositories, components, and operations. It is the user's architecture scope, not automatically a DDD bounded context.
2. **Node** represents independently executing runtimes, stores, channels, libraries, external systems, or people.
3. **Component** is a stable execution responsibility inside one runtime. It references every operation it fulfils.
4. **Operation** is a named capability or externally triggered behavior. It references owning components, trigger interfaces, and one or more path variants.
5. **Path** is one exact success, rejection, no-result, fallback, retry, failure, or asynchronous execution. Its hierarchical numbered sequence is authoritative.
6. **Relationship** is one reusable directed graph edge. Path steps reference it at the exact point where it is used.

Do not create components from folders, layers, receiver names, or every class. Require declaration, registration, interface, or implementation evidence establishing a stable responsibility.

## Repository discovery and source queue

The initial sources are discovery roots, not necessarily the complete repository set. While scanning each source:

1. Inspect repository remotes, workspace/solution manifests, deployment descriptors, service discovery, configured clients, generated-client origins, package metadata, infrastructure, integration tests, and documentation.
2. Record every plausible related repository in `scan.discoveredRepositories` with its location/repository identity, reason, evidence, and status: `candidate`, `accepted`, `rejected`, or `unavailable`.
3. Use strong deployment, destination, contract, channel, or generated-origin identity before names.
4. Add an accepted repository as a new source shard and progress entry before opening it. Do not hide queue expansion in conversation memory.
5. Preserve rejected and unavailable candidates so future agents know what was searched and why tracing stopped.

Never claim a caller or downstream continuation merely because similarly named code or an exposed route exists. Match caller outbound evidence to a compatible destination, method/path or channel, version, and contract. Record incompatibility as a conflict and missing continuation as a gap.

## Per-source transaction

`progress.json` is the resumable ledger. Only one source may be active.

1. Read repository instructions and record exact repository, revision, branch, and coverage.
2. Set the selected source to `scanning` and `activeSourceId` to its ID.
3. Inventory executables, stores, channels, independently delivered front ends/MFEs, interfaces, outbound dependencies, stable internal components, and ordered local operations.
4. Write only `sources/<source-id>/scan.json` for repository-local observations and discovered repository candidates.
5. Validate the scan shape and evidence before setting `scanWritten` and `scanValidated`.
6. Reconcile observations into canonical entity shards. Reuse stable IDs through strong identity; do not duplicate an existing fact.
7. Update reciprocal domain/component/operation references and review gaps/conflicts.
8. Canonically format and rebuild `index.json`; then set `graphUpdated`, `gapsReviewed`, and `conflictsReviewed`.
9. Mark the source complete and clear `activeSourceId` only when its revision and all gates match.

Reconciliation is incremental: finish and persist one source transaction before scanning the next. A rescan replaces its local observations and updates only affected graph shards and operation paths.

## Operation path transaction

For every selected exterior trigger and materially different outcome:

1. Identify the operation, owning components, exact trigger interface, and every evidenced caller: web/MFE, mobile, CLI, API, scheduler, event producer, file source, or person.
2. Trace the call through middleware, controllers, handlers, components, adapters, clients, stores, channels, configuration, feature flags, telemetry, and downstream implementations.
3. Continue across accepted repositories when destination/interface/channel identity and contracts are compatible.
4. Place each call, return/effect, read/write, publication, delivery, consumption, decision, retry, and telemetry action at its real execution position. Do not collapse a request with its later return.
5. Include every touched dependency regardless of domain or ownership. Keep unrelated components in the domain catalogue when they support other operations, but exclude them from this path's participant set.
6. End with a distinct return to the originating caller set, terminal state/effect, one-way completion, or unresolved gap.
7. Store the canonical path under `operations/<operation-id>/paths/`. Use root integers for stages and hierarchical descendants for operations: `1`, `1.1`, `1.2`, `2`, `2.1`.
8. Link asynchronous or related paths using `continuesFromPathIds`, `causedByPathIds`, and correlation metadata rather than flattening every branch into one sequence.
9. Run `format`, `render`, `index`, and `validate`. Never manually edit generated projection files.

Every path participant must be touched by the sequence, and every touched node/component must be a participant. Each non-stage step records endpoints/location, operation, input, output/effect, boundary, continuation, certainty, source findings, and evidence. Reference relationships/interfaces/gaps whenever applicable.

## Determinism and change interpretation

Stable output is part of correctness:

- Use stable IDs derived from confirmed architecture identity, not scan order, absolute checkout path, or incidental names.
- Keep ordered arrays only where order is semantic: path sequence and first-endpoint participant order. Caller alternatives and other set-like collections are canonicalized, as are JSON keys.
- Generate projections exclusively with `render`; identical canonical paths must produce byte-identical Markdown and ASCII.
- Rebuild `index.json` after shard changes. It records canonical content hashes, semantic hashes with provenance removed, and the overall model semantic hash.
- Compare snapshots with `diff`. Interpret categories as:
  - `semanticChanges`: architecture behavior or identity changed;
  - `evidenceOnlyChanges`: provenance/revision anchors changed but architecture meaning did not;
  - `projectionChanges`: generated output changed and must correspond to a path change;
  - `controlChanges`: subject, decisions, or workflow ledger changed;
  - `added`/`removed`: graph artifacts appeared or disappeared.
- An unchanged commit, a no-op rescan, or a different repository scan order must not create semantic changes.
- A changed commit may legitimately produce no semantic change. Do not rewrite architecture merely because source revision or line numbers changed.

## Validation and feedback cycle

Run validation before claiming completion. It must fail on stale indexes, incomplete sources/path reviews, invalid nested shapes/enums, unresolved references, non-reciprocal hierarchy links, relationship direction mismatches, incorrect participants, invalid sequence hierarchy, non-terminal outcomes, coverage/gap inconsistencies, noncanonical JSON, or projection drift.

Give the user a fast review surface rather than a black-box assurance:

1. Point to `index.json` for the overall hierarchy and hashes.
2. Point to each requested domain, component, and operation shard.
3. Point to numbered Markdown and ASCII projections for eyeballing execution.
4. If updating an existing model, generate `changes/<comparison-id>.json` and summarize semantic versus evidence-only changes.
5. Report exact gaps, conflicts, unavailable repositories, and coverage limitations. Never replace artifacts with a polished prose claim that they are correct.

## Completion gate

Do not report completion until:

- every accepted source has a complete revision-matched scan and progress entry;
- discovered repository candidates are accepted, rejected, or unavailable with evidence;
- domain/component/operation links are reciprocal;
- every relevant exterior interface is covered, explicitly excluded with a reason, or unresolved through gaps;
- callers and cross-repository continuations are corroborated rather than name-matched;
- every operation path has a terminal outcome and exact touched participant set;
- every dependency appears at its execution position with direction and evidence;
- all path reviews are complete and projections were generated, not hand-authored;
- `format`, `render`, `index`, and final `validate` succeed;
- the user receives concrete artifact paths and, for updates, a classified change report.

Apply every machine-readable case in `evals/evals.json` and every regression scenario under `evals/`. A fail condition is a skill regression.
