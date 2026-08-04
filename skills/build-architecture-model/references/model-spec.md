# Architecture discovery model specification

## Design contract

The model separates repository-local observations from model reconciliation:

```text
subject.json + decisions.json + scans/*.json --agent reconciliation--> model.json
model.json flows --exact projection--> flow-reviews/*/{numbered-sequence.md,sequence-diagram.txt}
progress.json --records source and flow-review stages and completed gates
```

The agent writes every artifact directly; this skill does not require bundled scripts or validators. All files are strict UTF-8 JSON with `schemaVersion: 1`. The shapes and reconciliation rules in this document and [reconciled-model.md](reconciled-model.md) are normative, not illustrative.

Do not add undocumented top-level keys or emit an alternate architecture representation. Before handoff, re-read every artifact and confirm that `progress.json` has no active source, every requested source is complete with all gates true, recorded source identities/revisions match their scans, every model flow has a complete review record, and `model.json` contains the reconciliation of all scans and decisions.

## progress.json

Create the ledger when initializing the model. It is keyed by the exact entries in `subject.requestedSources`, and only one source may be active:

```json
{
  "schemaVersion": 1,
  "activeSource": "../orders-api",
  "sources": {
    "../orders-api": {
      "sourceId": "orders-api",
      "revision": "0123456789abcdef",
      "stage": "reconciling",
      "gates": {
        "scanWritten": true,
        "scanValidated": true,
        "modelUpdated": false,
        "gapsReviewed": false,
        "conflictsReviewed": false
      }
    },
    "../search-worker": {
      "stage": "pending",
      "gates": {
        "scanWritten": false,
        "scanValidated": false,
        "modelUpdated": false,
        "gapsReviewed": false,
        "conflictsReviewed": false
      }
    }
  },
  "flowReviews": {
    "flow.submit-order.success": {
      "stage": "validating",
      "gates": {
        "canonicalFlowValidated": true,
        "numberedSequenceWritten": true,
        "asciiDiagramWritten": true,
        "projectionsValidated": false
      }
    }
  }
}
```

Source stages are `pending`, `scanning`, `validating`, `reconciling`, `reviewing`, and `complete`. Flow-review stages are `pending`, `authoring`, `validating`, and `complete`. Gates become true only in their displayed order. A complete source requires all source gates true plus a `sourceId` and exact `revision` matching its scan. A complete flow review requires all four review gates true. If a scan, model flow, or projection changes, reset the affected gate and every later gate before continuing.

`progress.flowReviews` has exactly one entry per `model.flows` key and no extras. Create or reset it after flow reconciliation. A flow cannot be complete merely because its JSON parses. `model.flowCoverage` has exactly one entry per reconciled inbound interface: covered, explicitly excluded, or unresolved through a recorded gap. A flat inventory cannot pass by silently omitting relevant flow work.

Repository scan documents are deliberately self-contained. Evidence is embedded beside each observation to avoid fragile evidence-reference graphs. The reconciled model uses stable references and is the only reconciled handoff artifact.

## subject.json

```json
{
  "schemaVersion": 1,
  "subject": {
    "id": "fulfilment",
    "name": "Fulfilment",
    "description": "Software supporting fulfilment operations",
    "aliases": ["Shipping"],
    "requestedSources": ["../orders-api", "../search-worker"],
    "exclusions": []
  }
}
```

The subject is the user-selected architecture scope. It can be a system, product, platform, service estate, business domain, or another named scope. It is not automatically a DDD domain or C4 Software System.

## decisions.json

```json
{
  "schemaVersion": 1,
  "identityOverrides": {
    "source-id:local-unit-id": "runtime.stable-id"
  },
  "targetOverrides": {
    "source-id:local-unit-id:outbound-id": "runtime.target-id"
  },
  "systemBoundaries": {
    "system.fulfilment": {
      "name": "Fulfilment",
      "responsibility": "Coordinates fulfilment",
      "status": "confirmed",
      "members": ["runtime.orders-api.abc123", "store.orders.def456"],
      "evidence": ["Confirmed by the architecture owner"]
    }
  }
}
```

Use overrides only for explicit identity decisions. System boundary status is `candidate`, `confirmed`, `rejected`, or `conflicting`. A C4 mapper must not use a candidate boundary as a confirmed System Context scope.

## Repository scan

```json
{
  "schemaVersion": 1,
  "source": {
    "id": "orders-api",
    "path": "../orders-api",
    "repository": "https://example/orders-api.git",
    "revision": "0123456789abcdef",
    "branch": "main",
    "scanStatus": "complete",
    "coverage": {
      "included": ["src/**", "deploy/**"],
      "excluded": ["bin/**", "obj/**"],
      "limitations": []
    }
  },
  "units": {},
  "components": {},
  "operations": {},
  "gaps": []
}
```

`scanStatus` is `complete`, `partial`, or `blocked`. Complete means the supplied source was fully inspected under the recorded coverage, not that production architecture is completely known.

## Evidence anchor

Every unit, interface, dependency, and operation step requires evidence:

```json
{
  "path": "src/Api/Program.cs",
  "symbol": "Program",
  "lineStart": 12,
  "lineEnd": 42,
  "observation": "Registers and starts the Orders HTTP application"
}
```

Paths are relative to the source root. `symbol` and line ranges are optional; `path` and `observation` are required.

## Unit

Units are keyed by a repository-local ID:

```json
{
  "kind": "runtime",
  "subtype": "api",
  "name": "Orders API",
  "responsibility": "Accepts and manages orders",
  "technology": [".NET 8", "ASP.NET Core"],
  "identity": {
    "deploymentIdentity": "orders-api"
  },
  "ownership": "Fulfilment team",
  "inbound": [],
  "outbound": [],
  "evidence": []
}
```

Allowed `kind` values:

- `runtime`: independently executing code, including browser applications and MFEs when independently delivered;
- `store`: logical database/schema, index, bucket, or file store;
- `channel`: queue, topic, or another logical message channel;
- `library`: linked/package code that does not run independently;
- `external`: unresolved or separately owned machine dependency;
- `person`: human actor when directly evidenced.

`subtype` is extensible and descriptive. It is not used as a C4 type.

## Internal component

Components are keyed by repository-local ID and exist inside one runtime unit:

```json
{
  "owner": "orders-api",
  "name": "Submit Order Handler",
  "responsibility": "Orchestrates order submission",
  "technology": [".NET", "MediatR"],
  "interface": "Handles SubmitOrderCommand",
  "evidence": [
    {
      "path": "src/Application/SubmitOrderHandler.cs",
      "symbol": "SubmitOrderHandler",
      "observation": "Handles and orchestrates SubmitOrderCommand"
    }
  ]
}
```

`owner`, `name`, `responsibility`, `technology`, and non-empty `evidence` are required. `owner` resolves to a local runtime. `interface` is optional. Create a component only for cohesive behavior or a stable execution role used in a traced operation, supported by its declaration, interface, registration, or implementation. A variable/field name or method receiver at a call site does not establish a component. Smaller or incompletely identified local steps execute at the runtime with exact evidence and, when material, a gap.

Strong identity examples:

```json
{"deploymentIdentity": "orders-api"}
{"technology": "SQL Server", "server": "sales", "database": "Orders", "schema": "fulfilment"}
{"transport": "Azure Service Bus", "namespace": "sales", "topic": "order-submitted"}
{"package": "Company.DesignSystem", "version": "5.2.0"}
```

Use `modelId` only when an existing confirmed model identity is known.

## Inbound interface

```json
{
  "id": "submit-order-v2",
  "kind": "http",
  "purpose": "Submits an order",
  "method": "POST",
  "path": "/api/v2/orders",
  "version": "v2",
  "contract": {
    "name": "SubmitOrder",
    "version": "v2",
    "format": "JSON",
    "schemaPath": "openapi/orders-v2.json",
    "fingerprint": "sha256:...",
    "keyFields": ["orderId", "customerId"]
  },
  "rules": ["Requires an authenticated customer"],
  "evidence": []
}
```

Allowed kinds are `http`, `grpc`, `event`, `message`, `job`, `ui`, `file`, and `other`.

Event/message interfaces require a channel:

```json
{
  "id": "consume-order-submitted-v3",
  "kind": "event",
  "purpose": "Indexes accepted orders",
  "version": "v3",
  "channel": {
    "technology": "MassTransit",
    "transport": "Azure Service Bus",
    "namespace": "sales",
    "topic": "order-submitted",
    "subscription": "search-indexer"
  },
  "contract": {"name": "OrderSubmitted", "version": "v3", "fingerprint": "sha256:..."},
  "rules": ["Processes accepted orders only"],
  "evidence": []
}
```

Do not list callers on an inbound interface unless direct caller evidence exists. During reconciliation, derive callers from outbound observations.

## Outbound dependency

```json
{
  "id": "call-payments-v2",
  "kind": "request",
  "purpose": "Authorises payment",
  "technology": "HTTPS/JSON",
  "target": {
    "kind": "runtime",
    "deploymentIdentity": "payments-api",
    "name": "Payments API"
  },
  "interface": {
    "method": "POST",
    "path": "/api/v2/authorisations",
    "version": "v2"
  },
  "contract": {"name": "AuthorisePayment", "version": "v2", "fingerprint": "sha256:..."},
  "rules": ["Invoked only for card payments"],
  "evidence": []
}
```

Allowed kinds are `request`, `event`, `message`, `data`, `search`, `file`, `library`, `ui-load`, and `other`.

Target examples:

```json
{"unitId": "local-database"}
{"modelId": "runtime.confirmed-payments"}
{"kind": "runtime", "deploymentIdentity": "payments-api"}
{"kind": "store", "technology": "SQL Server", "server": "sales", "database": "Orders", "schema": "fulfilment"}
{"kind": "channel", "transport": "Azure Service Bus", "namespace": "sales", "topic": "order-submitted"}
{"kind": "library", "package": "Company.DesignSystem", "version": "5.2.0"}
```

A target with `unitId` references another unit in the same scan. Other targets are reconciled by exact normalized identity. Names alone do not establish identity.

## Operation

Operations are repository-local ordered slices keyed and owned by a local runtime. They provide evidence for later cross-repository flow stitching:

```json
{
  "name": "Submit order",
  "owner": "orders-api",
  "trigger": "submit-order-v2",
  "steps": [
    {
      "order": 1,
      "at": "orders-api",
      "component": "submit-order-handler",
      "kind": "local-operation",
      "action": "Validates the order",
      "input": "SubmitOrderCommand",
      "output": "Validated command",
      "boundary": "in-process",
      "evidence": []
    },
    {
      "order": 2,
      "uses": "orders-database-write",
      "component": "submit-order-handler",
      "kind": "data-write",
      "action": "Stores the accepted order",
      "input": "Accepted order",
      "output": "Persisted order",
      "boundary": "data-store",
      "evidence": []
    }
  ]
}
```

Each step has exactly one of:

- `at`: a local unit where an architecturally meaningful rule executes;
- `uses`: an outbound dependency owned by the operation runtime.

`component` is optional and resolves to a local component owned by the operation runtime. Required step fields are `order`, `kind`, `action`, `input`, `output`, `boundary`, and non-empty `evidence`. Orders are contiguous positive integers. Add `next` only when a non-linear local path matters; it can be an order number, `"end"`, an array of orders, or a condition-to-order map. Record a call's later return/effect as its own step when it changes control or data needed by the end-to-end trace.

A bound/local configuration read remains an `at` operation on the runtime or evidenced component with `kind: "config-read"`; it does not create an external configuration unit or outbound dependency. Record an external configuration target only when source or deployment evidence establishes a remote provider interaction at runtime.

Allowed operation step kinds are `entry`, `local-operation`, `interaction`, `return`, `decision`, `data-read`, `data-write`, `config-read`, `feature-evaluation`, `publish`, `deliver`, `consume`, `telemetry`, `retry`, `outcome`, and `gap`.

Allowed boundaries are `in-process`, `runtime`, `data-store`, `search-store`, `message-channel`, `configuration`, `observability`, `external-service`, `file`, and `other`.

## Flow review artifacts

For every reconciled model flow at `flows.<flow-id>`, create:

```text
flow-reviews/<flow-id>/numbered-sequence.md
flow-reviews/<flow-id>/sequence-diagram.txt
```

`numbered-sequence.md` contains the flow ID, trigger, callers, exact participant IDs in model order, contract, path/outcome, coverage, the complete hierarchical numbered execution, and unresolved points. Each operation states its location/endpoints, dependency, input, output/effect, boundary, certainty, and evidence summary. Render each stage/operation label exactly as stored in the model so the bundled validator can compare it.

`sequence-diagram.txt` is plain UTF-8 ASCII readable in a monospaced terminal. List participant IDs as contiguous `P1`, `P2`, and so on in exact model order. Render every non-stage operation as `<number> <source alias(es)> -> <destination alias(es)> : <exact operation label> ...`; render local operations with the same alias on both sides. Every arrow carries the exact model sequence number, endpoints/direction, and exact stage/operation label. A request/response path shows its final return arrow to the originating caller set as a separate numbered interaction. Long flows may use consecutive stage panels but must not omit or reorder steps.

The model is authoritative. Generate both artifacts only after validating the canonical flow, then compare all three representations. Their flow ID, callers, participants, sequence numbers, order, operations, directions, dependencies, inputs/outputs/effects, and outcome must match. Run the bundled final validator, which deterministically checks flow ID, participants, sequence numbers/order, labels, and ASCII endpoints/direction; manually review dependency, input/output/effect, evidence, and outcome semantics. Any mismatch resets `projectionsValidated` and later completion state.

## Gap

```json
{
  "id": "payments-base-address",
  "description": "The payments base address is injected from an unavailable secret store",
  "impact": "The exact target system cannot be corroborated",
  "searches": ["Searched appsettings files", "Searched deployment manifests"]
}
```

Never turn a gap into a guessed relationship.

## Reconciled model

Author `model.json` exactly as specified in [reconciled-model.md](reconciled-model.md). That reference defines the required and optional fields for `sources`, `nodes`, `components`, `interfaces`, `relationships`, `flows`, `flowCoverage`, `systemBoundaries`, `gaps`, `conflicts`, source findings, and model evidence.

During reconciliation, create channel-to-consumer relationships from inbound event/message interfaces and mark compatible publisher/consumer contracts as corroborated. Incompatible versions or fingerprints become conflicts. The reconciled model remains C4-neutral; downstream mapping decides which facts become Software Systems, Containers, Components, Code elements, or supporting evidence.
