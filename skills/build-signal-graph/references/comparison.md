# TypeScript Signal model comparison

Compare architecture source models, not downstream diagrams.

| Concern | Existing `build-architecture-model` | `build-signal-graph` |
|---|---|---|
| Authority | Sharded JSON records and path files | TypeScript declarations and flows |
| Relationships | String IDs resolved by a validator | Direct typed object references |
| Contracts | JSON metadata and evidence fingerprints | Type-level request, response, and payload schemas |
| Review experience | Traverse an index and several shards | Read and navigate ordinary TypeScript |
| HTTP | Interface, relationship, entry, and return records | `endpoint`, `request`, and `respond` |
| Messaging | Channel relationships and path steps | `message`, `topic`, `subscription`, `consumer`, `publish`, `deliver`, `consume` |
| Ordering | Hierarchical JSON path sequence | Imperative-looking typed `flow` body |
| Change safety | Stable IDs, canonical formatting, semantic hashes | Compiler errors, symbol references, and normal refactoring |
| Provenance | Extensive mandatory finding/evidence records | Concise evidence attached only where it supports claims |
| Primary strength | Forensic reconciliation and resumable discovery | Clarity, authoring speed, contract safety, and relationship comprehension |
| Primary risk | High ceremony and fragmented review | Type correctness cannot prove that inspected source matches the declaration |

## What each produces

The JSON builder produces a directory of domain, node, component, interface, relationship, operation, path, gap, conflict, progress, and index records, plus generated text sequences.

Signal produces an importable TypeScript program:

```ts
export const OrderCreated = message({
  name: "order.created",
  schema: Schema.Struct({ orderId: Schema.String }),
})

export const Shipping = consumer({
  name: "shipping",
  service: ShippingWorker,
  subscription: ShippingOrders,
})
```

Its flow connects HTTP, storage, messaging, workers, and external APIs with typed references. It is therefore not constrained to MQ.

## Trade-off

Signal wins when humans must author, navigate, refactor, and understand the architecture while the compiler prevents incompatible contracts and wiring. The JSON builder wins when mandatory forensic provenance, resumable multi-repository reconciliation, deterministic semantic hashes, and machine-enforced completeness outweigh authoring cost.

Do not imitate the JSON builder to close that gap. Improve Signal on its own terms: stronger TypeScript types, focused source evidence, compiler and lint checks, reusable declaration modules, and tests that intentionally fail for incompatible wiring.
