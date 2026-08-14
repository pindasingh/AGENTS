# Sharded architecture graph contract

This is the normative contract for reconciled schema-version-2 artifacts. Read it with [model-spec.md](model-spec.md). Every artifact has one stable ID, one canonical file, and references other artifacts by ID. Do not duplicate records into `index.json` or create an aggregate model.

## Stable IDs and file locations

IDs match `[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*` and contain no path separators. Use semantic prefixes:

| Artifact | ID example | Canonical path |
|---|---|---|
| Source | `source.orders-api` | `sources/source.orders-api/scan.json` |
| Domain | `domain.fulfilment` | `domains/domain.fulfilment.json` |
| Node | `runtime.orders-api`, `store.orders` | `nodes/<id>.json` |
| Component | `component.orders-api.submit-handler` | `components/<id>.json` |
| Interface | `interface.orders-api.submit-order-v2` | `interfaces/<id>.json` |
| Relationship | `relationship.orders-api.write-orders` | `relationships/<id>.json` |
| Operation | `operation.submit-order` | `operations/<id>/operation.json` |
| Path | `path.submit-order.success` | `operations/<operation-id>/paths/<id>.json` |
| Gap/conflict | `gap.*`, `conflict.*` | `gaps/<id>.json`, `conflicts/<id>.json` |

Stable IDs follow confirmed deployment, contract, store/channel, or implementation identity. Do not derive them from scan order, temporary checkout roots, array positions, or presentation labels.

## Common provenance records

### Reconciled evidence

```json
{
  "sourceId": "source.orders-api",
  "path": "src/Api/OrdersController.cs",
  "symbol": "Submit",
  "lineStart": 20,
  "lineEnd": 42,
  "observation": "Defines POST /api/v2/orders"
}
```

`sourceId`, `path`, and `observation` are required. `sourceId` resolves to a source shard. `symbol` and a complete valid line range are optional.

### Source finding

```json
{
  "sourceId": "source.orders-api",
  "unitId": "orders-api",
  "componentId": "submit-order-handler",
  "interfaceId": "submit-order-v2",
  "operationId": "submit-order",
  "stepOrder": 2
}
```

`sourceId` is required. Add only local identifiers needed to locate the observation: `unitId`, `componentId`, `interfaceId`, `outboundId`, `operationId`, and `stepOrder`.

### Certainty

Use exactly `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`.

## Domain shard

Use [../assets/domain-template.json](../assets/domain-template.json). Required fields are:

- `schemaVersion`, `id`, `name`, and `description`;
- `sourceIds`, `componentIds`, and `operationIds`.

The arrays are references, not copied records. Every component and operation reciprocally names the same domain. A component not touched by one path remains in the domain if it fulfils another domain operation.

## Node shard

Use [../assets/node-template.json](../assets/node-template.json). Required fields are:

- `schemaVersion`, `id`, `kind`, `name`, `responsibility`;
- technology array and identity object;
- certainty, non-empty source findings, and non-empty evidence.

`subtype` and `ownership` are optional. Kinds are `runtime`, `store`, `channel`, `library`, `external`, and `person`.

Nodes are independently meaningful graph participants. Internal components do not become runtime nodes.

## Component shard

Use [../assets/component-template.json](../assets/component-template.json). Required fields are:

- `schemaVersion`, `id`, `domainId`, and `ownerNodeId`;
- name, responsibility, technology, and `operationIds`;
- certainty, non-empty source findings, and non-empty evidence.

`interface` is optional. `ownerNodeId` resolves to a runtime node. Each operation in `operationIds` reciprocally contains this component in `ownerComponentIds`.

A component represents stable execution responsibility, not arbitrary code structure. Smaller local operations can execute at their runtime with exact evidence without creating a component.

## Interface shard

Use [../assets/interface-template.json](../assets/interface-template.json). Required fields are:

- `schemaVersion`, `id`, `ownerNodeId`, `kind`, `purpose`, and `rules`;
- `coverage`;
- certainty, non-empty source findings, and non-empty evidence.

Applicable optional protocol fields are `method`, `path`, `service`, `version`, `channel`, and `contract`. Interface kinds are `http`, `grpc`, `event`, `message`, `job`, `ui`, `file`, and `other`.

Coverage is:

```json
{
  "status": "covered",
  "operationPathIds": ["path.submit-order.success"],
  "reason": "Successful state-changing path traced to response",
  "gapIds": []
}
```

Status is `covered`, `excluded`, or `unresolved`:

- covered requires resolving operation paths;
- excluded requires empty path/gap arrays and a concrete scope reason;
- unresolved requires one or more resolving gaps and may include partial paths.

Every exterior interface has explicit coverage. Internal interfaces may be excluded with a reason rather than silently omitted.

## Relationship shard

Use [../assets/relationship-template.json](../assets/relationship-template.json). Required fields are:

- `schemaVersion`, `id`, `fromId`, `toId`, `kind`, and `purpose`;
- technology, rules, certainty, non-empty source findings, and non-empty evidence.

`interfaceId` and `contract` are optional. Both endpoints resolve to nodes. Direction follows runtime interaction. Kinds are `request`, `event`, `message`, `data`, `search`, `file`, `library`, `ui-load`, and `other`.

A component path step can narrow a runtime endpoint, but its referenced relationship must remain compatible with the component's owning runtime and cannot reverse direction.

## Operation shard

Use [../assets/operation-template.json](../assets/operation-template.json). Required fields are:

- `schemaVersion`, `id`, `domainId`, `name`, and `description`;
- non-empty `ownerComponentIds`;
- non-empty `triggerInterfaceIds`;
- non-empty `pathIds`.

Every reference is reciprocal. An operation is the stable behavior/capability. It can have several exact path variants without combining them into an unreadable universal sequence.

## Operation path shard

A path is one authoritative execution variant. Required fields are:

- `schemaVersion`, `id`, `operationId`, `name`, `kind`, and `description`;
- non-empty `triggerInterfaceIds`;
- callers, non-empty participants, certainty, and non-empty sequence;
- outcome and coverage.

Kinds are `success`, `rejection`, `no-result`, `fallback`, `retry`, `failure`, `asynchronous`, and `other`.

Optional cross-path linkage:

- `continuesFromPathIds`: this path continues an earlier path;
- `causedByPathIds`: an earlier path caused this execution;
- `correlation`: observed request/message/correlation identity.

Use these links for accepted HTTP work followed by background processing, retries represented as separate review stories, or other related paths.

### Callers

Each caller has `nodeId`, `relationshipId`, certainty, non-empty source findings, and non-empty evidence. The relationship starts at the caller node and terminates at a trigger-owner runtime through a compatible interface. Several callers are alternatives unless evidence says they execute together.

An empty caller array is allowed only for a non-caller trigger or when explicit gaps and unresolved coverage explain missing caller evidence.

### Participants

Each participant has `id` and `role`. IDs resolve to nodes or components. The participant set equals the exact set touched by sequence endpoints—no omissions and no unrelated domain members. Participant order controls stable `P1`, `P2`, and so on in the ASCII projection.

### Sequence hierarchy

The sequence is a flat array in exact execution order. `number` matches `^[1-9][0-9]*(\.[1-9][0-9]*)*$`.

- Root records are contiguous stages `1`, `2`, `3`, and so on.
- Descendants name `parent` by removing their final number segment.
- Parents precede children.
- Siblings are contiguous and array order equals numeric hierarchy.
- Numbers never originate in a renderer.

A stage requires `number`, `kind: "stage"`, `name`, non-empty source findings, and non-empty evidence.

Every non-stage requires:

- `number`, `parent`, `kind`, and `operation`;
- `input`, `output`, `boundary`, `continuation`, and certainty;
- non-empty source findings and evidence;
- exactly one execution form.

Execution forms are:

1. `at` for local execution;
2. `source` plus `destination` for an interaction;
3. `callerRelationshipIds` plus `destination` and `interfaceId` for entry;
4. `source` plus `callerRelationshipIds` and `interfaceId` for return to caller alternatives.

Optional references are `relationshipId`, `interfaceId`, and `gapIds`. A first-class interaction uses its relationship. An invoked/handled interface uses its interface ID. An unresolved step names its gaps.

Non-stage kinds are `entry`, `local-operation`, `interaction`, `return`, `decision`, `data-read`, `data-write`, `config-read`, `feature-evaluation`, `publish`, `deliver`, `consume`, `telemetry`, `retry`, `outcome`, and `gap`.

Boundaries are `in-process`, `runtime`, `data-store`, `search-store`, `message-channel`, `configuration`, `observability`, `external-service`, `file`, and `other`.

Continuation is `continue`, `return`, `terminate`, `one-way`, or `unresolved`.

Calls and later returns/effects use separate steps when they alter control, state, or data. A request/response path ends with a separate return to its originating caller set; local response mapping is not that boundary crossing.

### Outcome and coverage

Outcome requires `kind`, `at`, and `description`. `at` resolves to a step whose continuation is `return`, `terminate`, `one-way`, or `unresolved`.

Coverage is:

```json
{
  "status": "complete",
  "unresolvedGapIds": [],
  "knownOmissions": []
}
```

Status is `complete`, `partial`, or `blocked`. Complete requires empty unresolved gaps and omissions. Every unresolved gap ID resolves to a gap shard.

## Gap and conflict shards

Use [../assets/gap-template.json](../assets/gap-template.json). A gap requires `schemaVersion`, ID, description, impact, searches, and non-empty source findings.

A conflict requires `schemaVersion`, ID, description, impact, status, non-empty alternatives, and source findings. Status is `open` or `resolved`; resolved conflicts additionally explain resolution. Preserve incompatible observations rather than rewriting them into agreement.

## Generated index

`index.json` is produced by the `index` command and matches [../assets/index-template.json](../assets/index-template.json). It contains:

- references and hashes grouped by artifact collection;
- domain and operation hierarchy summaries;
- projection references and hashes;
- one overall model semantic hash;
- hashed references to subject, decisions, and progress; subject and decision semantics contribute to the overall model semantic hash.

It contains no responsibilities, technologies, evidence, sequence steps, or copied graph records. Editing it manually is invalid; regenerate it.

## Deterministic projections

For each path, `render` writes:

```text
projections/<operation-id>/<path-id>/numbered-sequence.md
projections/<operation-id>/<path-id>/sequence-diagram.txt
```

The numbered view includes path/operation identity, triggers, callers, participants, outcome, coverage, exact hierarchical sequence, endpoint/location, kind, boundary, input, output, relationship/interface, continuation, certainty, and evidence summary.

The ASCII view assigns participant aliases in canonical path order, preserves every exact sequence number and label, and renders local execution as self-arrows. It is suitable for terminal review and line-oriented diffs.

Generated projections are never architecture authority and never manually repaired. Change the path when evidence proves it wrong; otherwise rerun `render`.

## Handoff checks

Before handoff, confirm:

- the index equals a fresh generated index;
- every source revision/progress entry agrees;
- every graph reference resolves and reciprocal hierarchy links match;
- relationship and caller directions are compatible;
- participants exactly match path endpoints;
- sequence hierarchy and outcomes are valid;
- coverage and gaps agree;
- generated projections equal deterministic rendering;
- a snapshot diff classifies changes when updating an existing model.
