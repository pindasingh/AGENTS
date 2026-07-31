# C4 view definition

Use one JSON file per diagram under `.c4-work/views/`. Start from `assets/view-template.json`, replace every example value, and add elements and relationships directly. This private definition is the reviewable source for the static SVG and HTML page.

## Top-level contract

Required fields are `id`, `title`, `diagramType`, `description`, `scope`, `elements`, `relationships`, `navigation`, and `links`. `diagramType` is `System Context`, `Container`, `Component`, `Code`, or `Dynamic`.

A scope has a stable view-local `id`, `name`, C4 `type`, short `description`, and provenance. System Context and Container scopes use a confirmed `modelBoundaryId`. Component scopes also use their model `modelElementId`. Code scopes use exact `evidenceRefs` when the component is not first-class in the reconciled model.

## Elements

Each element requires `id`, `name`, `type`, and `description`. Containers and Components require `technology`, using `Unknown` when necessary. `insideScope` is required except for System Context views.

Use `modelElementId` for a model element. Use non-empty `evidenceRefs` for evidenced Component or Code identities absent from the reconciled model. Allowed level semantics are:

- System Context: People and Software Systems directly connected to the scoped Software System;
- Container: in-scope Containers and directly connected People or external Software Systems;
- Component: in-scope Components of one Container and direct supporting Containers, People, or Software Systems;
- Code: observed code elements inside one Component only.

Do not add grouping pseudo-elements to solve layout problems.

## Relationships

Each relationship requires a stable `id`, included `source` and `destination` element IDs, and a specific directional `description`. Container relationships also require `technology`. System Context relationships omit implementation detail.

Use non-empty `modelRelationshipIds` when model relationships support the direction. Use `evidenceRefs` for lower-level relationships; a Component-to-model connector can retain both. Dynamic relationships additionally require unique contiguous positive `order` values.

The matching SVG must contain one visible connector per relationship, with the same ID, endpoints, label, direction, and provenance in `data-*` attributes. Relationship tables are supplementary.

## Navigation and notes

`navigation` and `links` contain ordinary page links outside the SVG:

```json
{"label": "Level 3 — Zoom into Orders API components", "href": "containers/orders-api/components.html"}
```

`notes` may contain concise architecture conclusions. Never expose raw evidence, skill execution details, or validation claims in public pages.

## Completion check

Review the JSON for required keys, unique IDs, resolvable endpoints, level semantics, provenance, exact correspondence with SVG elements/connectors, and working local links.
