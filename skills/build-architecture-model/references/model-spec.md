# Architecture discovery model specification

## Design contract

The model separates repository-local observations from model reconciliation:

```text
subject.json + decisions.json + scans/*.json --agent reconciliation--> model.json
progress.json --records the agent's stage and completed gates
```

The agent writes every artifact directly; this skill does not require bundled scripts or validators. All files are strict UTF-8 JSON with `schemaVersion: 1`. The shapes and reconciliation rules in this document and [reconciled-model.md](reconciled-model.md) are normative, not illustrative.

Do not add top-level keys or emit an alternate architecture representation. Before handing the model to another skill, re-read every artifact and confirm that `progress.json` has no active source, every requested source is complete with all gates true, recorded source identities/revisions match their scans, and `model.json` contains the reconciliation of all scans and decisions.

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
  }
}
```

Allowed stages are `pending`, `scanning`, `validating`, `reconciling`, `reviewing`, and `complete`. Gates become true only in their displayed order. A complete entry requires all gates true plus a `sourceId` and exact `revision` matching its scan. If a scan or model artifact changes, reset the affected gate and every later gate before continuing.

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

Operations are keyed and owned by a local runtime:

```json
{
  "name": "Submit order",
  "owner": "orders-api",
  "trigger": "submit-order-v2",
  "steps": [
    {
      "order": 1,
      "at": "orders-api",
      "action": "Validates the order",
      "evidence": []
    },
    {
      "order": 2,
      "uses": "orders-database-write",
      "action": "Stores the accepted order",
      "evidence": []
    }
  ]
}
```

Each step has exactly one of:

- `at`: a local unit where an architecturally meaningful rule executes;
- `uses`: an outbound dependency owned by the operation runtime.

Orders are contiguous positive integers. Add `next` only when a non-linear path matters; it can be an order number, `"end"`, an array of orders, or a condition-to-order map.

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

Author `model.json` exactly as specified in [reconciled-model.md](reconciled-model.md). That reference defines the required and optional fields for `sources`, `nodes`, `interfaces`, `relationships`, `flows`, `systemBoundaries`, `gaps`, `conflicts`, source findings, and model evidence.

During reconciliation, create channel-to-consumer relationships from inbound event/message interfaces and mark compatible publisher/consumer contracts as corroborated. Incompatible versions or fingerprints become conflicts. The reconciled model remains C4-neutral; downstream mapping decides which facts become Software Systems, Containers, Components, Code elements, or supporting evidence.
