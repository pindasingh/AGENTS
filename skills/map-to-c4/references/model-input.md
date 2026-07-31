# Architecture model input contract

`map-to-c4` consumes the reconciled `model.json` produced by the sibling `build-architecture-model` skill. Read that skill's `references/model-spec.md` for the complete discovery schema.

## Authority and mutability

- `scans/*.json` contain repository-local observations.
- `decisions.json` contains explicit identity and system-boundary decisions.
- `model.json` is agent-reconciled working memory. Edit it only while applying `build-architecture-model`, with every claim supported by scans or confirmed decisions.
- C4 view JSON and rendered artifacts are projections; they do not become architecture authority.

Before mapping, review every artifact using the completion check in `build-architecture-model/SKILL.md`. Resolve broken references, unsupported claims, conflicts, and blocking gaps there.

If raw repositories were supplied without a model, run `build-architecture-model` first. Do not recreate a second evidence ledger or overlap model inside `map-to-c4`.

## Mapping rules

The discovery model is intentionally C4-neutral:

| Architecture model fact | C4 assessment |
|---|---|
| `runtime` | Candidate Application Container; candidate Software System only when value/ownership boundary evidence supports it |
| `store` | Candidate Data Store Container for its logical owner |
| `channel` | Candidate owned Data Store Container, or communication detail condensed into a relationship |
| `library` | Supporting code/evidence; not a Container without independent runtime behavior |
| `external` | Candidate external Software System; confirm actual ownership/identity |
| `person` | Candidate Person |
| inbound/outbound interface | Relationship and responsibility evidence |
| model relationship | Directed C4 relationship evidence |
| flow | Candidate Dynamic diagram interactions |
| confirmed system boundary | Permitted core System Context/Container scope |

The selected subject—whether a system, product, platform, service estate, or business domain—is not automatically a C4 Software System. Only boundaries with `status: confirmed` can anchor core System Context and Container diagrams. Preserve candidate, rejected, and conflicting boundaries privately.

## Projection traceability

Every rendered scope, element, and relationship must retain provenance. Use model node IDs as `modelElementId`, confirmed boundary IDs as `modelBoundaryId`, and model relationship IDs as `modelRelationshipIds` whenever those first-class facts exist. The current discovery schema does not model internal Components and code elements; use exact source anchors in non-empty `evidenceRefs` for those lower-level identities and relationships. Never attach a model ID to a lower-level item merely to satisfy validation.

Example Container element:

```json
{
  "id": "container-orders-api",
  "modelElementId": "runtime.orders-api.12ab34",
  "name": "Orders API",
  "type": "Container: Application",
  "description": "Accepts and manages orders.",
  "technology": ".NET 8, ASP.NET Core",
  "insideScope": true
}
```

Example relationship:

```json
{
  "id": "rel-mfe-orders-api",
  "modelRelationshipIds": ["rel.runtime-orders-mfe.call-orders-v2.91cd"],
  "source": "container-orders-mfe",
  "destination": "container-orders-api",
  "description": "Submits and manages orders using API v2",
  "technology": "HTTPS/JSON"
}
```

A view can aggregate several endpoint-level model relationships only when they have the same projected source, destination, direction, compatible technology, and a truthful concise purpose. Preserve every supporting ID. Never aggregate opposite directions or incompatible API/event versions.

When a channel is omitted from a Container view, a publisher-to-consumer relationship may be condensed only when compatible producer/channel/consumer evidence establishes that path. List both model edge IDs and name the channel/protocol in the label or technology. Do not hide fan-out, competing consumers, version conflicts, or unresolved ownership through condensation.

## Uncertainty gate

- `corroborated`: preferred for cross-repository relationships.
- `observed`: usable when one repository directly establishes an outbound dependency, but expose material target uncertainty.
- `inferred`: do not render as established fact without explicit review.
- `conflicting`: never flatten into one connector; resolve or show affected alternatives outside a core diagram.
- `unknown`: retain as a gap.

Do not claim a complete C4 package while relevant model conflicts or gaps make a required System Context/Container relationship or boundary unreliable.

## Level-specific use

### System Context

Collapse confirmed boundary members to the scoped Software System. Aggregate only direct model relationships crossing that boundary. Omit technology and endpoint/version detail from the visible label, while retaining model relationship IDs in the view source.

### Container

Map runtime and logical-store members of one confirmed boundary. Use technology/protocol and architecturally useful API/event versions on relationships. Keep shared physical hosting as Deployment information.

### Component and Code

The discovery model may not contain enough internal evidence for these optional levels. Do not infer components from Clean Architecture project names, folders, MediatR handlers, packages, or layers alone. Create lower-level views only from evidenced cohesive interfaces and code identities.

A Component scope uses the model runtime's `modelElementId` and containing confirmed `modelBoundaryId`. Each in-scope Component uses `evidenceRefs`; model supporting Containers retain `modelElementId`. A Component relationship can use the runtime-level `modelRelationshipIds` only when those edges support the same direction and the Component source anchor narrows responsibility truthfully; otherwise use relationship `evidenceRefs`.

A Code scope, every code element, and every code relationship use exact `evidenceRefs`. Keep these anchors in private view JSON and SVG `data-*` metadata; do not turn the public page into an evidence ledger. The manual provenance self-check applies to Component and Code views even though model node projection does not.

### Dynamic

Project selected model flows and boundary-crossing relationship steps. Generate display order from the selected flow. Internal steps can explain significant rules, but C4 Dynamic interactions must reuse static-model elements rather than inventing workflow nodes. A Dynamic scope and its reused elements carry the same model IDs or lower-level `evidenceRefs` as their static definitions; every interaction carries `modelRelationshipIds` or exact `evidenceRefs`.
