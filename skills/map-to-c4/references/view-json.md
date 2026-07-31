# C4 view definition

Use one JSON file per diagram under `.c4-work/views/`. Start from the level-specific template listed in `SKILL.md`, replace every example value, and add elements and relationships directly. This private definition is the reviewable source for the static SVG and HTML page.

## Top-level contract

Required fields are `id`, `title`, `diagramType`, `description`, `scope`, `elements`, `relationships`, `navigation`, and `links`. `diagramType` is `System Context`, `Container`, `Component`, `Code`, `System Landscape`, `Dynamic`, or `Deployment`.

A scope has a stable view-local `id`, `name`, C4 `type`, short `description`, and provenance. A Container or Component scope also requires `technology`, using `Unknown` when unavailable. System Context and Container scopes use a confirmed `modelBoundaryId`. Component scopes also use their model `modelElementId`. Code scopes use exact `evidenceRefs` when the component is not first-class in the reconciled model. System Landscape uses `modelBoundaryIds` for every included confirmed system. Dynamic reuses the provenance of its chosen static scope. Deployment uses exact environment/deployment `evidenceRefs` plus model IDs for reused Software Systems and Containers.

## Elements

Each element requires `id`, `name`, `type`, and `description`. Containers and Components require `technology`, using `Unknown` when necessary. `insideScope` is required for Container, Component, and Code views. Deployment elements additionally require `parent` when nested; the parent resolves to the scope or another included deployment element.

Use `modelElementId` for a model node, `modelBoundaryId` for a confirmed Software System, and non-empty `evidenceRefs` for evidenced lower-level or deployment identities absent from the reconciled model. Allowed level semantics are:

- System Context: People and Software Systems directly connected to the scoped Software System;
- Container: in-scope Containers and directly connected People or external Software Systems;
- Component: in-scope Components of one Container and direct supporting Containers, People, or Software Systems;
- Code: observed code elements inside one Component only.
- System Landscape: evidenced People and confirmed Software Systems within the named organisational scope.
- Dynamic: elements reused from one compatible static abstraction level; no workflow pseudo-elements.
- Deployment: Deployment Nodes, Infrastructure Nodes, Software System Instances, and Container Instances in one named environment.

Do not add grouping pseudo-elements to solve layout problems.

## Relationships

Each relationship requires a stable `id`, a resolvable `source`, a resolvable `destination`, and a specific directional `description`. An endpoint resolves when it equals `scope.id` or one `elements[].id`; this permits the scoped Software System to be the primary System Context element without duplicating it in `elements`. Container relationships also require `technology`. System Context relationships omit implementation detail.

Use non-empty `modelRelationshipIds` when model relationships support the direction. Use `evidenceRefs` for lower-level relationships; a Component-to-model connector can retain both. Dynamic relationships additionally require unique contiguous positive `order` values.

The matching SVG must contain one visible connector per relationship, with the same ID, endpoints, label, direction, and provenance in `data-*` attributes. Relationship tables are supplementary.

## Evidence-reference format

Use strings of the form `<source-id>:<relative-path>[:<lineStart>-<lineEnd>][#<symbol>]`, with forward-slash paths. Example: `orders-api:src/Application/SubmitOrderHandler.cs:18-31#Handle`. The source ID and path must resolve to a scan and source anchor. In SVG, serialize several references in `data-evidence-refs` by joining the exact strings with ` | `; do not abbreviate them.

For every SVG element and connector, retain only the applicable provenance attributes:

- model-backed scope: `data-model-boundary-id`;
- model-backed element: `data-model-element-id`;
- model-backed connector: `data-model-relationship-ids`, joined with ` | `;
- lower-level scope, element, or connector: `data-evidence-refs` using the canonical format above.

## Navigation and notes

`navigation` and `links` contain ordinary page links outside the SVG:

```json
{"label": "Level 3 — Zoom into Orders API components", "href": "containers/orders-api/components.html"}
```

`notes` may contain concise architecture conclusions. Never expose raw evidence, skill execution details, or validation claims in public pages.

## Completion check

Review the JSON for required keys, unique IDs, resolvable endpoints, level semantics, provenance, exact correspondence with SVG elements/connectors, and working local links.
