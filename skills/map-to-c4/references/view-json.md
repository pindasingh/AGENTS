# Bundled renderer view JSON

Use one JSON file per C4 diagram. Keep these source views in the private `.c4-work/views/` directory and render static SVG/HTML into the public architecture site.

When projecting a canonical architecture model, read [canonical-input.md](canonical-input.md). Every scope, element, and relationship requires provenance. Use canonical `modelBoundaryId`, `modelElementId`, and `modelRelationshipIds` where the discovery model has first-class identities; use non-empty `evidenceRefs` for evidenced Component/Code identities and lower-level relationships that are not represented canonically. Provenance is retained in SVG metadata but not shown as public evidence prose.

## Required top-level fields

```json
{
  "id": "stable-view-id",
  "title": "Container diagram — System Name",
  "diagramType": "Container",
  "description": "One sentence describing this view.",
  "scope": {"modelBoundaryId": "system.confirmed-boundary-id"},
  "elements": [],
  "relationships": [],
  "navigation": [],
  "links": []
}
```

`diagramType` is one of `System Context`, `Container`, `Component`, `Code`, or `Dynamic`. The bundled renderer does not currently render System Landscape or Deployment notation; use another already available renderer for those optional views.

## Scope

```json
{
  "id": "stable-scope-element-id",
  "name": "Scope name",
  "type": "Software System",
  "description": "Scope responsibility.",
  "technology": "Required when scope is a Container or Component"
}
```

Expected scope types:

- System Context: `Software System`
- Container: `Software System`
- Component: `Container`
- Code: `Component`

The System Context scope is rendered as the central element. Other scope types are rendered as an enclosing boundary. System Context views must omit technology and implementation detail.

Provenance by scope:

- System Context and Container: confirmed `modelBoundaryId`.
- Component: confirmed `modelBoundaryId` plus the scoped runtime's canonical `modelElementId`.
- Code: one or more source `evidenceRefs` establishing the scoped Component.
- Dynamic: `modelBoundaryId`, `modelElementId`, or `evidenceRefs`, matching the reused static-model scope.

## Elements

```json
{
  "id": "stable-element-id",
  "name": "Element name",
  "type": "Container",
  "description": "Short responsibility.",
  "technology": "Technology or Unknown",
  "insideScope": true,
  "modelElementId": "runtime.canonical-element-id"
}
```

`insideScope` is required except on System Context views. Set it to `true` for children of the scoped boundary and `false` for directly connected supporting elements. Canonical System Context/Container elements use `modelElementId`. In-scope Component and Code elements use source anchors such as `"evidenceRefs": ["orders-api:src/Orders/Handler.cs:24"]`; supporting canonical Containers/Systems continue to use `modelElementId`.

The renderer enforces level semantics:

- System Context elements are People or Software Systems directly connected to the scoped Software System.
- Container in-scope elements are Containers; supporting elements are directly connected People or Software Systems.
- Component in-scope elements are Components; supporting elements are directly connected Containers, People, or Software Systems.
- Code elements are code-level children inside the scoped Component; outside-scope elements are not accepted.

Technology is required for every Container and Component. Code element types may use names such as `Class`, `Interface`, `Function`, `Table`, or `Dataclass`. Pseudo-group element types are rejected.

Optional explicit placement is supported when automatic layout is insufficient:

```json
"position": {"x": 350, "y": 200, "width": 250, "height": 135}
```

## Relationships

```json
{
  "id": "stable-relationship-id",
  "source": "source-element-id",
  "destination": "destination-element-id",
  "description": "Specific directional intent",
  "technology": "Protocol/technology or Unknown",
  "modelRelationshipIds": ["rel.canonical-relationship-id"]
}
```

Every endpoint must be included in the view. Self-relationships are rejected. Technology/protocol is mandatory on Container-view relationships under this skill's strict rendering profile, while System Context relationships must omit it. Use `modelRelationshipIds` when canonical edges support the exact rendered direction. For a purely lower-level relationship, use `evidenceRefs` instead. A Component-to-canonical-Container connector may retain both canonical relationship IDs and the source anchor proving which Component makes the call.

The renderer creates a visible labelled arrow and emits both view-local IDs and provenance metadata. The validator checks connector endpoints, boundary containment, provenance, collisions, and local links.

Dynamic relationships additionally require a unique positive integer `order`; the renderer prefixes that number to the visible interaction label:

```json
{"id": "checkout-1", "order": 1, "source": "person-customer", "destination": "container-web", "description": "Starts checkout"}
```

Represent separate source/destination pairs as separate relationships. Do not collapse several callers into phrases such as `Each component`.

## Navigation

Navigation is ordinary page chrome outside the SVG; diagram elements remain static.

```json
"navigation": [
  {"label": "Architecture", "href": "../../../index.html"}
],
"links": [
  {"label": "Zoom into components", "href": "containers/example/components.html"}
]
```

Do not add links to SVG elements, JavaScript interaction, zoom handlers, or tooltips.

## Rich static page content

Each generated diagram page contains the connected SVG plus subject-specific heading, summary, scope metadata, element/responsibility table, directional relationship table, breadcrumbs, zoom links, and optional architecture notes. Add concise public notes with:

```json
"notes": ["Retries are handled by the worker; the API does not wait for fulfilment."]
```

Do not put raw evidence ledgers or skill-process metadata in public notes.

## Deterministic site render plan

Use `scripts/render_c4_package.py` to generate the complete static site, including `architecture/index.html`, into staging; validate it; and replace public output only after every check passes. Start from `assets/render-plan.json`.

```json
{
  "projectRoot": "../..",
  "architectureRoot": "architecture",
  "canonical": ".architecture-model/canonical.json",
  "site": {
    "title": "Orders architecture",
    "description": "How customers place and fulfil orders.",
    "systems": [{"id": "orders", "name": "Orders", "description": "Accepts and fulfils orders."}]
  },
  "views": [
    {
      "systemId": "orders",
      "source": ".c4-work/views/orders-context.json",
      "svg": "systems/orders/context.svg",
      "html": "systems/orders/context.html"
    },
    {
      "systemId": "orders",
      "source": ".c4-work/views/orders-containers.json",
      "svg": "systems/orders/containers.svg",
      "html": "systems/orders/containers.html"
    }
  ]
}
```

All plan paths are relative and constrained to their declared roots. Every view names a `systemId`, and the package renderer rejects a plan unless every listed software system has both System Context and Container views. The generated site is static and requires no JavaScript.

## Commands

```bash
python scripts/validate_canonical_projection.py <canonical.json> <view-or-directory> [...]
python scripts/render_c4.py <view.json> --svg <diagram.svg> --html <diagram.html>
python scripts/render_c4_package.py <render-plan.json>
python scripts/validate_c4_package.py <architecture-directory>
```
