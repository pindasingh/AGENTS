---
name: map-to-c4
description: Projects a reconciled architecture model into navigable C4 System Context, Container, Component, Code, and supporting diagrams. Use after build-architecture-model for C4 boundary mapping, architecture documentation, or filtered views.
---

# Map to C4

Project an evidence-backed reconciled architecture model into navigable C4 views. Read [references/c4-source-of-truth.md](references/c4-source-of-truth.md), [references/model-input.md](references/model-input.md), and [references/view-json.md](references/view-json.md) before working.

This skill does not discover repositories. If the reconciled model is absent or stale, apply the sibling `build-architecture-model` skill first.

## Templates

Start from:

- [assets/view-template.json](assets/view-template.json) for the private view definition;
- [assets/diagram-template.svg](assets/diagram-template.svg) for a connected diagram;
- [assets/page-template.html](assets/page-template.html) for a public diagram page;
- [assets/index-template.html](assets/index-template.html) for architecture navigation.

Copy the templates, replace every `{{PLACEHOLDER}}`, and add or remove repeated blocks as needed. Author the view JSON, SVG, and HTML directly. Keep view definitions under `.c4-work/views/` and public artifacts under `architecture/`.

## Required hierarchy

Assess all four levels for each confirmed in-scope Software System:

1. **System Context** — one Software System, users, and directly connected external Software Systems.
2. **Container** — applications and data stores inside it, plus directly connected people and Software Systems.
3. **Component** — cohesive functional components inside one Container, plus direct dependencies.
4. **Code** — selected observed code elements inside one important or complex Component.

System Context and Container views are required. Component and Code views are optional and must be evidence-supported. Supporting Landscape, Dynamic, and Deployment views answer specific questions but never replace the core static views.

## Projection workflow

1. Read and self-check the complete reconciled model. Stop or return to discovery when conflicts or gaps prevent an honest required view.
2. Confirm Software System boundaries from `decisions.json`; never use a candidate boundary as confirmed scope.
3. Create one private JSON view definition from the template for each diagram. Include explicit element and relationship IDs plus model IDs or exact evidence references.
4. Lay out the SVG directly. Put all included elements on one canvas, place scoped boundaries around their children, then draw one visible labelled directional connector per relationship.
5. Create the HTML page from the template with breadcrumbs, the SVG, responsibilities, directional relationship details, architecture notes, and zoom links.
6. Create the subject-specific index and navigation hierarchy.
7. Review every JSON, SVG, HTML file, and local link using the completion check below.

## C4 mapping rules

- Establish Software Systems using user value, ownership, responsibility, visibility of internals, and coordinated delivery—not repository names or domains.
- Map independently running applications and owned logical data stores to Containers inside their owning system. A substantial browser client and its server are separate Containers.
- Treat queues/topics according to ownership and architectural coupling; do not automatically turn a broker into a Container.
- Never promote libraries, assemblies, packages, folders, contracts, generated clients, or migrations into Containers without runtime evidence.
- Define Components from cohesive behavior, interfaces, encapsulation, and dependencies inside exactly one Container; packaging alone is insufficient.
- Create Code views only from observed identities and static relationships inside one Component. Never invent class candidates.
- Classify a cross-domain machine caller as a concrete Software System, a human as a Person, and an in-system caller as another Container. Do not create `Domain`, `Consumer`, or `Microservice` C4 types.

## Diagram acceptance gate

Every diagram must:

- have one scope and abstraction level, a title, key, short responsibilities, explicit element types, and technology for Containers/Components (`Unknown` when unavailable);
- place all included elements on one SVG canvas and spatially enclose in-scope children where required;
- render every included relationship as a visible unidirectional `<path>` or `<line>` from source to destination with an arrowhead and a nearby specific label;
- include protocol/technology on Container relationships and omit implementation detail at System Context level;
- retain `data-c4-element-id` on elements and `data-c4-relationship-id`, `data-source-id`, `data-destination-id`, and `data-label` on connectors;
- retain model provenance (`data-model-boundary-id`, `data-model-element-id`, `data-model-relationship-ids`) or exact lower-level `data-evidence-refs`;
- use a responsive `viewBox`, readable text, adequate whitespace, and accessible color/shape distinctions without JavaScript or disabled browser zoom.

A relationship list, arrow character, or disconnected cards never substitutes for connectors.

## Navigation

Use ordinary links outside static SVGs:

```text
architecture/
  index.html
  systems/<system-id>/context.html
  systems/<system-id>/containers.html
  systems/<system-id>/containers/<container-id>/components.html
  systems/<system-id>/containers/<container-id>/components/<component-id>/code.html
  flows/<flow-id>.html
.c4-work/views/
```

Keep evidence ledgers, validation notes, coverage matrices, and skill-process metadata out of the public site. The index should contain only subject-specific architecture explanation and useful navigation.

## Completion check

For every completed view, read the private JSON and rendered artifacts back and verify:

- [ ] Scope, element, and relationship IDs are unique; every endpoint resolves and every item has model or evidence provenance.
- [ ] Every included element appears exactly once and every included relationship has exactly one visible labelled connector in the correct direction.
- [ ] Connector start/end points touch their declared elements; arrowheads point toward destinations.
- [ ] Scoped boundaries enclose exactly their in-scope children.
- [ ] Elements, labels, and connectors do not overlap or cross unrelated elements; inspect at normal desktop width and a narrow viewport.
- [ ] Titles, types, responsibilities, technologies, legend, and relationship protocols meet the level rules.
- [ ] All local links resolve, zoom paths name their target scope/level, and every confirmed Software System has Context and Container pages.
- [ ] Component/Code views contain only evidenced cohesive boundaries/identities; optional diagrams do not replace required views.
- [ ] Public pages contain architecture conclusions rather than raw evidence or execution metadata.
- [ ] Re-reading the model source confirms names, direction, ownership, versions, and identities were not redefined by presentation.

Apply every Markdown case under `evals/` as a reasoning checklist.
