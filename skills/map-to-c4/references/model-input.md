# Architecture model input contract

`map-to-c4` consumes the complete sharded `.architecture-model/` directory produced by `build-architecture-model`. Read that skill's `references/model-spec.md` and `references/sharded-graph.md` completely.

## Authority and mutability

- `sources/*/scan.json` contains repository-local observations and repository-discovery evidence.
- `decisions.json` contains explicit identity and system-boundary decisions.
- Domain, node, component, interface, relationship, operation, and path shards are canonical architecture authority.
- `index.json` is a generated navigation/hash manifest; it is not a copied model and contains no detailed architecture records.
- Numbered Markdown and ASCII are generated operation-path projections.
- C4 view JSON and rendered artifacts are presentation projections and never architecture authority.

Before mapping, run the build skill's final validator and review its completion gate. Never accept `index.json`, one operation path, or one projection as a standalone handoff. If raw repositories were supplied without a model, run `build-architecture-model` first. Do not create a second evidence ledger inside this skill.

## Deterministic preflight

Perform every check before creating a view:

1. Run the trusted absolute `architecture_model.py validate <model-root>` command.
2. Require `progress.activeSourceId` to be null, every source complete with revision-matched gates, and every path review complete.
3. Require generated `index.json` to match current shards and generated projections.
4. Resolve every index artifact path and hash, graph owner/endpoint/interface/path reference, source finding, and evidence source/path.
5. Confirm reciprocal domain/component/operation/path hierarchy links.
6. Confirm `decisions.systemBoundaries` references resolving graph nodes and use only `confirmed` boundaries for required C4 scopes.
7. Review gaps, conflicts, partial paths, unavailable repository candidates, and uncovered interfaces. Return to the build skill when any item blocks a truthful view.

Fail closed: do not repair, reinterpret, or supplement canonical graph shards inside this skill.

## Mapping rules

The discovery graph is intentionally C4-neutral:

| Architecture graph fact | C4 assessment |
|---|---|
| runtime node | Candidate Application Container; candidate Software System only when value/ownership boundary evidence supports it |
| store node | Candidate Data Store Container for its logical owner |
| channel node | Candidate owned Data Store Container or communication detail condensed into a relationship |
| library node | Supporting code/evidence; not a Container without independent runtime behavior |
| external node | Candidate external Software System; confirm ownership/identity |
| person node | Candidate Person |
| interface shard | Relationship and responsibility evidence |
| relationship shard | Directed C4 relationship evidence |
| component shard | Candidate C4 Component inside its `ownerNodeId` runtime |
| operation path | Candidate Dynamic diagram interactions |
| confirmed system boundary | Permitted core System Context/Container scope |

The selected domain/scope is not automatically a C4 Software System. Only confirmed system boundaries can anchor core Context and Container diagrams.

## Projection traceability

Retain canonical provenance:

- graph node ID → `modelElementId`;
- confirmed boundary ID → `modelBoundaryId`;
- graph relationship IDs → `modelRelationshipIds`;
- component ID → `modelElementId` when projecting that first-class component;
- exact source anchors → `evidenceRefs` for lower-level code/deployment facts absent from the graph.

Example Container element:

```json
{
  "id": "container-orders-api",
  "modelElementId": "runtime.orders-api",
  "name": "Orders API",
  "type": "Container: Application",
  "description": "Accepts and manages orders.",
  "technology": ".NET 8, ASP.NET Core",
  "insideScope": true
}
```

A view can aggregate several graph relationships only when they share projected source, destination, direction, compatible technology, and a truthful concise purpose. Preserve every supporting relationship ID. Never aggregate opposite directions or incompatible contract versions.

When omitting an explicit channel from a Container view, condense publisher-to-consumer only when compatible producer/channel/consumer evidence establishes that path. Preserve fan-out, subscriptions, conflicts, and unresolved ownership.

## Uncertainty gate

- `corroborated`: preferred for cross-repository relationships.
- `observed`: usable when direct evidence establishes the interaction; expose material target uncertainty.
- `inferred`: do not render as established fact without explicit review.
- `conflicting`: never flatten into one connector.
- `unknown`: retain as a gap.

Do not claim a complete C4 package while relevant conflicts, gaps, or repository-discovery limitations make required boundaries or relationships unreliable.

## Level-specific use

### System Context

Collapse confirmed boundary members to the scoped Software System. Aggregate only direct graph relationships crossing that boundary. Omit endpoint/technology detail from visible labels while retaining relationship IDs privately.

### Container

Map runtime and logical-store members of one confirmed boundary. Use relationship technology/protocol and useful API/event versions. Keep shared physical hosting as Deployment information.

### Component and Code

Use first-class component shards only inside their `ownerNodeId` runtime. Component responsibility and operation links support selection, while path steps and relationship IDs support direction. Do not infer extra components from folders, layers, package names, or incidental classes.

Code scopes and code relationships use exact evidence references. Keep these anchors private and do not turn public pages into evidence ledgers.

### Dynamic

Project one selected canonical operation path. Preserve its sequence order and reuse compatible static graph elements. Every interaction carries graph relationship IDs or exact evidence references. Do not invent workflow pseudo-elements or infer order from graph adjacency.
