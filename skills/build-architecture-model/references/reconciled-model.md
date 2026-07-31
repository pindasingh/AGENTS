# Reconciled architecture model contract

This is the closed, normative contract for `.architecture-model/model.json`. Read it with `model-spec.md`. Every keyed collection may be empty, but every record that exists must use the shape defined here. Do not add top-level fields or alternate record shapes.

## Common records

### Model evidence

Every model claim carries at least one source-qualified anchor:

```json
{
  "sourceId": "orders-api",
  "path": "src/Api/Program.cs",
  "symbol": "Program",
  "lineStart": 12,
  "lineEnd": 42,
  "observation": "Starts the Orders HTTP application"
}
```

Required fields are `sourceId`, `path`, and `observation`. `symbol`, `lineStart`, and `lineEnd` are optional. When either line is present both are required, positive, and `lineEnd` is not less than `lineStart`. `sourceId` must resolve in `model.sources`; paths are relative to that source.

### Source finding

Use structured findings rather than ad-hoc strings:

```json
{
  "sourceId": "orders-api",
  "unitId": "orders-api",
  "interfaceId": "submit-order-v2",
  "outboundId": "write-orders",
  "operationId": "submit-order",
  "stepOrder": 2
}
```

`sourceId` and `unitId` are required. Add only the keys that identify the originating observation: `interfaceId`, `outboundId`, `operationId`, and `stepOrder`. Each supplied key must resolve inside the named scan. A finding identifies one local observation; use several findings when a model fact reconciles several observations.

### Certainty

`certainty` is exactly one of `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`.

## Top-level shape

```json
{
  "schemaVersion": 1,
  "subject": {},
  "sources": {},
  "nodes": {},
  "interfaces": {},
  "relationships": {},
  "flows": {},
  "systemBoundaries": {},
  "gaps": {},
  "conflicts": {}
}
```

All ten keys are required and no other top-level keys are allowed. `subject` exactly copies `subject.json.subject`, including `aliases` and `exclusions`.

## Sources

Key `sources` by scan `source.id`:

```json
"orders-api": {
  "path": "../orders-api",
  "repository": "https://example/orders-api.git",
  "revision": "0123456789abcdef",
  "branch": "main",
  "scanPath": "scans/orders-api.json"
}
```

All five fields are required and must exactly match the scan. `scanPath` is relative to `.architecture-model/` and must resolve to that scan.

## Nodes

Key nodes by stable model ID:

```json
"runtime.orders-api": {
  "kind": "runtime",
  "subtype": "api",
  "name": "Orders API",
  "responsibility": "Accepts and manages orders",
  "technology": [".NET 8", "ASP.NET Core"],
  "identity": {"deploymentIdentity": "orders-api"},
  "ownership": "Fulfilment team",
  "certainty": "observed",
  "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api"}],
  "evidence": [{"sourceId": "orders-api", "path": "src/Api/Program.cs", "observation": "Starts the Orders API"}]
}
```

Required fields are `kind`, `name`, `responsibility`, `technology`, `identity`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`. `subtype` and `ownership` are optional. `kind` uses the discovery kinds from `model-spec.md`. `technology` is an array of strings and `identity` is an object containing observed identity keys; either may be empty when genuinely unknown.

## Interfaces

Key interfaces by stable model ID:

```json
"interface.orders-api.submit-order-v2": {
  "owner": "runtime.orders-api",
  "kind": "http",
  "purpose": "Submits an order",
  "method": "POST",
  "path": "/api/v2/orders",
  "version": "v2",
  "contract": {"name": "SubmitOrder", "version": "v2", "format": "JSON"},
  "rules": ["Requires an authenticated customer"],
  "certainty": "observed",
  "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "interfaceId": "submit-order-v2"}],
  "evidence": [{"sourceId": "orders-api", "path": "src/Api/Controllers/OrdersController.cs", "observation": "Defines POST /api/v2/orders"}]
}
```

Required fields are `owner`, `kind`, `purpose`, `rules`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`. `owner` resolves to a node. Preserve the applicable observed interface fields from `model-spec.md`: `method`, `path`, `service`, `version`, `channel`, and `contract`. Do not add fields that were not observed.

## Relationships

```json
"relationship.orders-api.write-orders": {
  "from": "runtime.orders-api",
  "to": "store.orders",
  "kind": "data",
  "purpose": "Creates and updates orders",
  "technology": "Entity Framework Core/SQL Server",
  "interface": {"database": "Orders", "schema": "fulfilment"},
  "rules": [],
  "certainty": "observed",
  "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "outboundId": "write-orders"}],
  "evidence": [{"sourceId": "orders-api", "path": "src/Infrastructure/OrdersDbContext.cs", "observation": "Writes accepted orders"}]
}
```

Required fields are `from`, `to`, `kind`, `purpose`, `technology`, `rules`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`. Both endpoints resolve to nodes and direction follows runtime interaction. `interface` and `contract` are optional observed objects. Preserve incompatible versions as separate relationships and conflicts.

## Flows

```json
"flow.submit-order": {
  "name": "Submit order",
  "owner": "runtime.orders-api",
  "trigger": "interface.orders-api.submit-order-v2",
  "certainty": "observed",
  "steps": [
    {
      "order": 1,
      "at": "runtime.orders-api",
      "action": "Validates the order",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 1}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Validates the command"}]
    },
    {
      "order": 2,
      "relationshipId": "relationship.orders-api.write-orders",
      "action": "Stores the accepted order",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 2}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Persists the order"}]
    }
  ]
}
```

Required fields are `name`, `owner`, `trigger`, `certainty`, and non-empty `steps`. `owner` resolves to a runtime node and `trigger` to an interface owned by it. Orders are contiguous positive integers. Each step has exactly one of `at` or `relationshipId`; it also has `action`, non-empty `sourceFindings`, and non-empty `evidence`. `at` resolves to a node and `relationshipId` resolves to a relationship. Optional `next` uses the scan operation form.

## System boundaries

`model.systemBoundaries` exactly mirrors `decisions.systemBoundaries`; keys and record values must be identical:

```json
"system.fulfilment": {
  "name": "Fulfilment",
  "responsibility": "Coordinates fulfilment",
  "status": "confirmed",
  "members": ["runtime.orders-api", "store.orders"],
  "evidence": ["Confirmed by the architecture owner"]
}
```

Every member resolves to a model node. Status is `candidate`, `confirmed`, `rejected`, or `conflicting`. Only confirmed boundaries may anchor required C4 views.

## Gaps

```json
"gap.orders-api.payments-base-address": {
  "description": "The payments base address is injected externally",
  "impact": "The exact target cannot be corroborated",
  "searches": ["Searched appsettings files", "Searched deployment manifests"],
  "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "outboundId": "call-payments"}]
}
```

Required fields are `description`, `impact`, non-empty `searches`, and non-empty `sourceFindings`.

## Conflicts

```json
"conflict.order-submitted-version": {
  "description": "Publisher and legacy consumer use incompatible event versions",
  "impact": "The legacy delivery path cannot be shown as compatible",
  "status": "open",
  "alternatives": [
    {"value": "v3", "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "outboundId": "publish-order-submitted"}]},
    {"value": "v2", "sourceFindings": [{"sourceId": "legacy-worker", "unitId": "legacy-worker", "interfaceId": "consume-order-submitted-v2"}]}
  ]
}
```

Required fields are `description`, `impact`, `status`, and at least two `alternatives`. Status is `open` or `resolved`. Each alternative has `value` and non-empty `sourceFindings`. A resolved conflict additionally requires `resolution` and must not silently rewrite the underlying observations.

## Handoff validation

Before another skill consumes the directory, re-read all files and verify:

- top-level keys and every nested record match this contract;
- every model source maps one-to-one to a completed progress entry and scan with the same path, revision, branch, and source ID;
- every source finding and evidence source/path resolves;
- every owner, endpoint, interface, boundary member, flow reference, and operation step resolves;
- `model.subject` equals `subject.json.subject` and `model.systemBoundaries` equals `decisions.systemBoundaries`;
- every identity override names an existing scan unit and resolves to a model node, and every target override names an existing outbound dependency and resolves to a model node;
- every current scan is reconciled and no stale model record cites a replaced observation;
- conflicts and gaps are retained instead of flattened into established relationships.

Failure at any item means the model is not ready for handoff.
