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
  "componentId": "submit-order-handler",
  "interfaceId": "submit-order-v2",
  "outboundId": "write-orders",
  "operationId": "submit-order",
  "stepOrder": 2
}
```

`sourceId` is required. `unitId` is required except for a component-only finding, where `componentId` plus its resolvable owner establishes the unit. Add only the keys that identify the originating observation: `componentId`, `interfaceId`, `outboundId`, `operationId`, and `stepOrder`. Each supplied key must resolve inside the named scan. A finding identifies one local observation; use several findings when a model fact reconciles several observations.

### Certainty

`certainty` is exactly one of `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`.

## Top-level shape

```json
{
  "schemaVersion": 1,
  "subject": {},
  "sources": {},
  "nodes": {},
  "components": {},
  "interfaces": {},
  "relationships": {},
  "flows": {},
  "flowCoverage": {},
  "systemBoundaries": {},
  "gaps": {},
  "conflicts": {}
}
```

All twelve keys are required and no other top-level keys are allowed. `subject` exactly copies `subject.json.subject`, including `aliases` and `exclusions`.

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

## Components

Key components by stable model ID:

```json
"component.orders-api.submit-order-handler": {
  "owner": "runtime.orders-api",
  "name": "Submit Order Handler",
  "responsibility": "Orchestrates order submission",
  "technology": [".NET", "MediatR"],
  "interface": "Handles SubmitOrderCommand",
  "certainty": "observed",
  "sourceFindings": [
    {"sourceId": "orders-api", "componentId": "submit-order-handler"}
  ],
  "evidence": [
    {"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Handles SubmitOrderCommand"}
  ]
}
```

Required fields are `owner`, `name`, `responsibility`, `technology`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`. `owner` resolves to a runtime node. `interface` is optional. A component is a stable execution responsibility inside one runtime, evidenced by a declaration, interface, registration, or implementation—not automatically a folder, layer, namespace, assembly, variable, field, method receiver, handler, repository, client, or class name. Small or incompletely identified local operations remain flow steps at their runtime with evidence and need not become components.

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

Each flow record represents one named end-to-end path. It is not a bag of every branch in a scenario. Flow keys match `^flow\.[a-z0-9][a-z0-9._-]*$` and contain no path separators so the same ID can safely name its review directory.

```json
"flow.submit-order": {
  "name": "Submit order — successful path",
  "scenario": "Submit order",
  "path": "successful",
  "description": "Accepts and stores a valid order",
  "owner": "runtime.orders-api",
  "trigger": "interface.orders-api.submit-order-v2",
  "callers": [
    {
      "nodeId": "runtime.orders-web",
      "relationshipId": "relationship.orders-web.submit-order-v2",
      "certainty": "corroborated",
      "sourceFindings": [
        {"sourceId": "orders-web", "unitId": "orders-web", "outboundId": "submit-order-v2"}
      ],
      "evidence": [
        {"sourceId": "orders-web", "path": "src/api/orders.ts", "observation": "Calls POST /api/v2/orders"}
      ]
    }
  ],
  "participants": [
    {"id": "runtime.orders-web", "role": "Initiates the request"},
    {"id": "runtime.orders-api", "role": "Handles and orchestrates the request"},
    {"id": "component.orders-api.submit-order-handler", "role": "Validates and stores the order"},
    {"id": "store.orders", "role": "Persists the accepted order"}
  ],
  "certainty": "observed",
  "sequence": [
    {
      "number": "1",
      "kind": "stage",
      "name": "Request enters the Orders API",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 1}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Validates the command"}]
    },
    {
      "number": "1.1",
      "parent": "1",
      "kind": "entry",
      "callerRelationshipIds": ["relationship.orders-web.submit-order-v2"],
      "destination": "runtime.orders-api",
      "interfaceId": "interface.orders-api.submit-order-v2",
      "operation": "Sends POST /api/v2/orders",
      "input": "SubmitOrder request v2",
      "output": "Accepted HTTP request",
      "boundary": "runtime",
      "continuation": "continue",
      "certainty": "corroborated",
      "sourceFindings": [{"sourceId": "orders-web", "unitId": "orders-web", "outboundId": "submit-order-v2"}],
      "evidence": [{"sourceId": "orders-web", "path": "src/api/orders.ts", "observation": "Calls POST /api/v2/orders"}]
    },
    {
      "number": "1.2",
      "parent": "1",
      "kind": "local-operation",
      "at": "component.orders-api.submit-order-handler",
      "operation": "Validates the submitted order",
      "input": "SubmitOrderCommand",
      "output": "Validated command",
      "boundary": "in-process",
      "continuation": "continue",
      "certainty": "observed",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 1}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Validates the command"}]
    },
    {
      "number": "1.3",
      "parent": "1",
      "kind": "data-write",
      "source": "component.orders-api.submit-order-handler",
      "destination": "store.orders",
      "relationshipId": "relationship.orders-api.write-orders",
      "operation": "Stores the accepted order",
      "input": "Accepted order",
      "output": "Persisted order",
      "boundary": "data-store",
      "continuation": "continue",
      "certainty": "observed",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 2}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Application/SubmitOrderHandler.cs", "observation": "Persists the order"}]
    },
    {
      "number": "2",
      "kind": "stage",
      "name": "Response returns to the originating caller",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 2}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Api/Controllers/OrdersController.cs", "observation": "Returns the submit-order response"}]
    },
    {
      "number": "2.1",
      "parent": "2",
      "kind": "return",
      "source": "runtime.orders-api",
      "callerRelationshipIds": ["relationship.orders-web.submit-order-v2"],
      "interfaceId": "interface.orders-api.submit-order-v2",
      "operation": "Returns SubmitOrderResponse v2 to the originating caller",
      "input": "Persisted order result",
      "output": "SubmitOrderResponse v2",
      "boundary": "runtime",
      "continuation": "return",
      "certainty": "corroborated",
      "sourceFindings": [{"sourceId": "orders-api", "unitId": "orders-api", "operationId": "submit-order", "stepOrder": 2}],
      "evidence": [{"sourceId": "orders-api", "path": "src/Api/Controllers/OrdersController.cs", "observation": "Returns the response to the HTTP caller"}]
    }
  ],
  "outcome": {
    "kind": "success",
    "at": "2.1",
    "description": "The originating caller receives SubmitOrderResponse v2"
  },
  "coverage": {
    "status": "complete",
    "unresolvedContinuations": [],
    "knownOmissions": []
  }
}
```

Required flow fields are `name`, `scenario`, `path`, `description`, `owner`, `trigger`, `callers`, non-empty `participants`, `certainty`, non-empty `sequence`, `outcome`, and `coverage`. `owner` resolves to a runtime node and `trigger` to an interface owned by it. A caller record requires `nodeId`, `relationshipId`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`; both IDs resolve and the relationship must terminate at the trigger owner through a compatible interface. `callers` may be empty only when caller discovery produced an explicit gap referenced by `flowCoverage`.

Each participant has `id` and `role`; `id` resolves to a node or component. The participant set contains every element touched by the sequence and no element included only because of domain/ownership membership.

### Sequence records

The `sequence` is a flat array in authoritative execution order. `number` is a string matching `^[1-9][0-9]*(\.[1-9][0-9]*)*$`. Numbers are unique. Root stages are contiguous integers. A non-root record has `parent` equal to the number with its final segment removed; the parent exists earlier. Siblings are contiguous and array order matches numeric hierarchy.

A stage record requires `number`, `kind: "stage"`, `name`, non-empty `sourceFindings`, and non-empty `evidence`.

Every non-stage record requires:

- `number`, `parent`, `kind`, `operation`, `input`, `output`, `boundary`, `continuation`, `certainty`, non-empty `sourceFindings`, and non-empty `evidence`;
- exactly one execution form: `at` for a local operation; `source` plus `destination` for an interaction; `callerRelationshipIds` plus `destination` and `interfaceId` for an `entry` step; or `source` plus `callerRelationshipIds` and `interfaceId` for a terminal caller `return` step;
- `relationshipId` when a first-class model relationship supports the interaction;
- `interfaceId` when an interface is invoked or handles the step.

`at`, `source`, and `destination` resolve to nodes or components. Every `callerRelationshipIds` entry resolves to one flow caller's relationship, and every flow caller appears in the entry and terminal-return steps; these are alternative initiators/recipients, not simultaneous calls. `relationshipId` resolves to a relationship and its projected endpoints/direction remain compatible with the step; a component-to-node step may narrow the runtime source but must not reverse it. `interfaceId` resolves to an interface compatible with the destination/handler.

Allowed non-stage kinds are `entry`, `local-operation`, `interaction`, `return`, `decision`, `data-read`, `data-write`, `config-read`, `feature-evaluation`, `publish`, `deliver`, `consume`, `telemetry`, `retry`, `outcome`, and `gap`. Allowed boundaries are `in-process`, `runtime`, `data-store`, `search-store`, `message-channel`, `configuration`, `observability`, `external-service`, `file`, and `other`. Allowed continuation values are `continue`, `return`, `terminate`, `one-way`, and `unresolved`.

Calls and their later returns/effects occupy separate sequence positions when the return/effect changes control, state, or data needed by the trace. A request/response flow ends with a distinct return interaction to its originating caller set; local mapping cannot substitute for that boundary crossing. A one-way publish uses `one-way`; a missing continuation uses `unresolved` and must correspond to an unresolved-continuation entry and model gap.

A local options/configuration access uses `kind: "config-read"`, `boundary: "configuration"`, and an `at` execution form. It may reference configuration-file/provider evidence without manufacturing an external node or relationship. Use an external configuration participant only when a remote runtime interaction is evidenced.

`outcome` requires `kind`, `at`, and `description`; `at` resolves to a sequence number whose continuation terminates or returns the path. `coverage.status` is `complete`, `partial`, or `blocked`; `unresolvedContinuations` and `knownOmissions` are arrays of gap IDs or explicit, reviewable omission descriptions. `complete` requires both arrays empty.

### Flow coverage

Key `flowCoverage` by public/exterior interface ID:

```json
"interface.orders-api.submit-order-v2": {
  "status": "covered",
  "flowIds": ["flow.submit-order"],
  "reason": "Successful state-changing path traced from caller to persistence",
  "evidence": [
    {"sourceId": "orders-api", "path": "src/Api/Controllers/OrdersController.cs", "observation": "Defines the exterior entry point"}
  ]
}
```

Required fields are `status`, `flowIds`, `reason`, and non-empty `evidence`. Status is `covered`, `excluded`, or `unresolved`. `covered` requires one or more resolving flow IDs. `excluded` requires an empty `flowIds` array and a concrete scope/value reason. `unresolved` requires an empty or partial `flowIds` array plus a referenced model gap in `gapIds`. Every reconciled inbound interface has exactly one coverage record. Use `excluded` with a concrete scope/value reason for an internal-only or otherwise irrelevant interface; never omit it silently.

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
- every owner, endpoint, component, interface, boundary member, flow-coverage record, sequence reference, and operation step resolves;
- `model.subject` equals `subject.json.subject` and `model.systemBoundaries` equals `decisions.systemBoundaries`;
- every identity override names an existing scan unit and resolves to a model node, and every target override names an existing outbound dependency and resolves to a model node;
- every current scan is reconciled and no stale model record cites a replaced observation;
- conflicts and gaps are retained instead of flattened into established relationships.
- every flow sequence passes hierarchical numbering, participant, direction, continuation, outcome, and coverage checks;
- `progress.flowReviews` exactly matches `model.flows`, every gate is true, and each Markdown/ASCII artifact matches its authoritative JSON flow operation by operation.

Failure at any item means the model is not ready for handoff.
