# Architecture discovery and workflow specification

## 1. Design contract

The architecture model uses schema version 2 and separates repository observations, reconciled graph entities, operation paths, and generated projections:

```text
subject + decisions + sources/*/scan
                  |
                  v agent reconciliation
independent domain/node/component/interface/relationship/operation/path shards
                  |
                  +-- deterministic index --> index.json
                  +-- deterministic render --> numbered Markdown + ASCII
```

There is no aggregate `model.json`. A canonical fact exists once in its own shard. References use stable IDs. `index.json` is generated and contains only paths, hashes, and hierarchy summaries.

All JSON is strict UTF-8, `schemaVersion: 2`, sorted by the bundled formatter, and terminated by LF. Set-like arrays, including caller alternatives, are canonicalized; sequence order and participant first-endpoint order remain semantic.

## 2. Top-level control artifacts

### subject.json

Use [../assets/subject-template.json](../assets/subject-template.json). The user-selected scope ID starts with `domain.`. `discoveryRoots` records local roots or supplied repositories. `requestedSources` contains accepted `source.*` IDs, not checkout paths. Update both when repository discovery expands the source queue.

### decisions.json

Use [../assets/decisions-template.json](../assets/decisions-template.json).

- `identityOverrides`: explicit local-observation to stable graph ID decisions.
- `targetOverrides`: explicit outbound-target to graph node/interface decisions.
- `repositoryOverrides`: explicit candidate location/repository to stable source ID decisions.
- `systemBoundaries`: candidate/confirmed/rejected/conflicting boundary decisions for downstream mapping.

Do not encode guesses as overrides.

### progress.json

Use [../assets/progress-template.json](../assets/progress-template.json). `sources` exactly matches source shards and `pathReviews` exactly matches operation path shards.

Source gates advance in this order:

1. `scanWritten`
2. `scanValidated`
3. `graphUpdated`
4. `gapsReviewed`
5. `conflictsReviewed`

A complete source has all gates true and a `revision` equal to `scan.source.revision`. Only `activeSourceId` may be in progress.

Path-review gates advance in this order:

1. `canonicalPathValidated`
2. `numberedSequenceGenerated`
3. `asciiDiagramGenerated`
4. `projectionsValidated`

A complete review has `stage: "complete"` and all gates true. Changing a source, graph shard, path, or projection resets the affected gate and all later gates.

## 3. Source scan

One `sources/<source-id>/scan.json` contains only repository-local observations. Use [../assets/scan-template.json](../assets/scan-template.json).

Required top-level fields are:

- `schemaVersion`, `id`, and `source`;
- `discoveredRepositories`;
- `units`, `components`, and `operations`;
- `gaps`.

`source` records exact `location`, `repository`, `revision`, `branch`, status, and coverage. Status is `pending`, `scanning`, `partial`, `blocked`, or `complete`.

### Repository discovery candidates

Each `discoveredRepositories` item has:

```json
{
  "id": "source.eligibility-api",
  "location": "../eligibility-api",
  "repository": "https://example/eligibility-api.git",
  "reason": "Generated client metadata and deployment identity match the outbound target",
  "status": "candidate",
  "evidence": ["src/Clients/EligibilityClient.g.cs and deploy/values.yaml"]
}
```

Status is `candidate`, `accepted`, `rejected`, or `unavailable`. Preserve candidates even after rejection or failed access. An accepted candidate gets its own source shard and progress entry before scanning.

### Evidence anchors

Repository-local evidence has `path` and `observation`; `symbol`, `lineStart`, and `lineEnd` are optional. Paths are relative to the source root. Reconciled evidence additionally has `sourceId`.

### Units

Repository-local units use kinds:

- `runtime`: independently executing API, worker, browser app/MFE, job, function, CLI, or scheduler;
- `store`: logical database/schema, index, bucket, or file store;
- `channel`: queue, topic, or another logical message channel;
- `library`: linked/package code;
- `external`: separately owned or unresolved machine dependency;
- `person`: directly evidenced actor.

A repository can contain several runtimes and a runtime can use artifacts from several repositories. Project/repository boundaries are evidence, not runtime identity.

Each unit records name, responsibility, technology, identity, inbound interfaces, outbound dependencies, and evidence. Preserve exact deployment, service, data-store, channel, package, and contract identities.

### Repository-local components

Use a component only for cohesive, stable execution responsibility inside a runtime. Require declaration, interface, registration, or implementation evidence. Record local owner, name, responsibility, technology, optional provided interface/role, and evidence.

Do not manufacture components from folders, layers, every class, variable names, receiver names, or framework objects.

### Inbound interfaces

Kinds are `http`, `grpc`, `event`, `message`, `job`, `ui`, `file`, and `other`. Capture applicable fields:

- owner and purpose;
- method/path/service or channel/subscription/consumer group;
- version and contract name/schema/fingerprint;
- authentication, routing, filtering, and caller-affecting rules;
- evidence.

An inbound interface does not prove a caller.

### Outbound dependencies

Kinds are `request`, `event`, `message`, `data`, `search`, `file`, `library`, `ui-load`, and `other`. Capture source, destination identity, purpose, technology, contract/version, rules, and evidence.

Use strong target identity in this order: confirmed override, deployment identity, exact store/channel identity, configured service address plus compatible interface, compatible contract/fingerprint, generated-client origin, package identity, then name only as a candidate.

### Repository-local operations

Operations are evidence-backed ordered slices used to stitch end-to-end paths. Each is owned by a local runtime, names its trigger interface, and contains contiguous positive-integer steps.

Each step records:

- `at` a local unit/component or `uses` a local outbound dependency;
- kind, action, input, output/effect, boundary, and evidence;
- optional branch/next semantics when architecturally meaningful.

Record separate call and return/effect steps when later control or data matters. Include touched configuration, feature flags, stores, channels, external APIs, telemetry, and cross-domain dependencies. Do not copy ordinary implementation instructions or complete payload schemas.

## 4. Reconciliation rules

Read [sharded-graph.md](sharded-graph.md) before writing graph shards.

- Reconcile by stable identity, never scan order.
- Keep incompatible API/event versions separate and create conflicts.
- Derive callers from compatible outbound-to-inbound evidence.
- Distinguish physical database host from logical database/schema/index.
- Keep package dependencies separate from runtime interactions.
- Preserve unmatched targets, callers, and continuations as concrete gaps.
- Update reciprocal links together: domain ↔ component, domain ↔ operation, component ↔ operation, operation ↔ path.
- Reconcile after each source rather than loading all repositories into conversation memory.

## 5. Deterministic tool transaction

After authored JSON changes:

1. Run `format` to canonicalize JSON and set-like arrays.
2. Run `render` to replace every operation-path projection.
3. Run `index` to regenerate paths, content hashes, semantic hashes, hierarchy, and the overall semantic hash.
4. Run final `validate`.

`validate --allow-incomplete` is only for checking an initialized/in-progress model. Never use it as final completion evidence.

The index contains:

- `contentHash`: canonical complete JSON, including provenance;
- `semanticHash`: canonical architecture meaning with evidence/source-finding material removed;
- `modelSemanticHash`: combined semantic identity of scope/decisions, graph entities, and paths; repository locations, requested-source queue, source revisions, and evidence anchors do not alter it by themselves;
- projection content hashes.

Use `diff` between saved indexes. A revision or evidence-line change can be evidence-only. A behavior, identity, relationship, component responsibility, operation, or sequence change is semantic. Projection changes without a canonical path change indicate drift.

## 6. Validation layers

Final validation must cover all layers:

1. **Syntax and canonicalization** — valid version-2 UTF-8 JSON and canonical formatting.
2. **Closed structure** — required/optional fields and enums only.
3. **References** — every ID resolves and reciprocal hierarchy references agree.
4. **Graph semantics** — ownership and relationship direction are compatible.
5. **Path semantics** — exact participants, sequence hierarchy, endpoints, terminal outcome, gaps, and coverage.
6. **Workflow** — revision-matched complete sources and complete path reviews.
7. **Projection** — generated Markdown and ASCII equal deterministic rendering byte for byte.
8. **Index** — generated index exactly matches current shards and projections.

Any failure blocks handoff.
