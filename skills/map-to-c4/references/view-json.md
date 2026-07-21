# Bundled renderer view JSON

Use one JSON file per C4 diagram. Keep these source views in the private `.c4-work/views/` directory and render static SVG/HTML into the public architecture site.

When projecting a gathered canonical model, read [canonical-input.md](canonical-input.md). System Context, Container, and Dynamic view scopes require `modelBoundaryId`; their elements require `modelElementId`; and their relationships require `modelRelationshipIds`. These provenance fields are retained in source JSON but do not add visual clutter.

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

`insideScope` is required except on System Context views. Set it to `true` for children of the scoped boundary and `false` for directly connected supporting elements.

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

Every endpoint must be included in the view. Self-relationships are rejected. Technology/protocol is mandatory on Container-view relationships under this skill's strict rendering profile, while System Context relationships must omit it. The renderer creates a visible labelled arrow and model annotations consumed by the validator.

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

## Commands

```bash
python scripts/render_c4.py <view.json> --svg <diagram.svg> --html <diagram.html>
python scripts/validate_c4_package.py <architecture-directory>
```
