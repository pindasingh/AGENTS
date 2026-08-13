---
name: build-signal-graph
description: Discover a software system and express its end-to-end architecture as a type-checked TypeScript Signal DSL covering people, systems, services, HTTP endpoints, stores, messages, topics, subscriptions, consumers, external dependencies, and executable flows. Use for architecture discovery, producer/consumer mapping, relationship analysis, impact analysis, or a code-native alternative to JSON architecture models.
---

# Build Signal Graph

Create an architecture definition in TypeScript. The declarations and their typed references are the model; do not create JSON shards, generic node/edge records, or a C4 diagram.

Read [references/typescript-dsl.md](references/typescript-dsl.md). Copy [assets/signal.ts](assets/signal.ts) and [assets/architecture.ts](assets/architecture.ts) into the target model directory, then replace the example with discovered facts. Read [references/comparison.md](references/comparison.md) only when the user asks to compare architecture-building approaches.

## Output

```text
architecture/
  signal.ts          # DSL and type constraints
  architecture.ts    # the system model
```

Use additional TypeScript modules when the model becomes difficult to review, grouped by business capability or deployable system—not by arbitrary record kind. Keep one root `architecture.ts` that imports and exports the complete architecture.

## Model the system

1. Establish the requested scope and inspect its repositories, deployment configuration, interfaces, schemas, call sites, stores, and message bindings.
2. Declare stable architectural concepts with the most specific constructor: `actor`, `system`, `service`, `endpoint`, `store`, `external`, `message`, `topic`, `subscription`, or `consumer`.
3. Connect declarations by object reference. Never reproduce a declaration's name as an ID string.
4. Express end-to-end behavior with `flow`. Use typed step operations such as `request`, `respond`, `read`, `write`, `publish`, `deliver`, and `consume`; do not introduce generic edges or a `mode` field.
5. Represent materially different success, rejection, failure, retry, and background continuations as separate named flows. Keep a synchronous response before later background work in its actual order.
6. Attach `evidence(...)` to declarations whose identity or relationship would otherwise be disputable. Record repository, revision, relative path, observation, and `observed`, `inferred`, or `unknown` certainty.
7. Leave an uncertain relationship absent or mark its declaration unknown. Do not make the model compile by inventing a caller, destination, contract, or consumer.
8. Run TypeScript type checking and inspect the declarations and flows before handoff.

## Semantics

- `system` is an owned software/product boundary; `service` is an independently executing part of a system.
- `endpoint` belongs to a service or external dependency and owns typed request and response schemas.
- `message` owns one payload schema. `topic` permits explicit messages. `subscription` selects a message from a topic. `consumer` binds a service to that subscription.
- `store` is a logical state boundary owned by a system.
- `request` invokes an endpoint; `respond` completes that invocation. Do not label either synchronous or asynchronous with metadata—the flow makes waiting and continuation visible.
- `publish`, `deliver`, and `consume` are distinct steps. This preserves broker routing, fan-out, subscription ownership, and handler responsibility.
- Type compatibility is an acceptance gate: endpoint inputs must match request schemas, published values must match message schemas, and consumers must match their subscriptions.

## Quality gate

Do not report completion until:

- `tsc --noEmit` succeeds under strict checking;
- every declaration is exported and included in the root `architecture(...)` definition;
- every relationship is expressed through a typed reference or flow step rather than a duplicated string identity;
- every selected flow starts from an evidenced trigger and ends with a response, terminal effect, or explicit one-way publication;
- HTTP request and response behavior, message publication/routing/consumption, and store access appear in their real order;
- schemas and ownership references are specific enough for TypeScript to reject incompatible wiring;
- unknowns remain honest and evidence does not claim more than the inspected source proves.

Apply every machine-readable case in `evals/evals.json`. An eval fails when the resulting TypeScript omits an evidenced boundary or operation, invents an unsupported dependency, collapses synchronous acceptance into asynchronous completion, or fails strict type checking.

## Handoff

Point the user to `architecture/architecture.ts`. Summarize the modeled systems and flows, any relationships intentionally omitted as unresolved, and the exact type-check command. The TypeScript source is the review surface and authority; generated JSON or diagrams, if separately requested, are disposable projections.
