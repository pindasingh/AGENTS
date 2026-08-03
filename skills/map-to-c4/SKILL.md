---
name: map-to-c4
description: Projects a reconciled architecture model into navigable C4 System Context, Container, Component, Code, and supporting diagrams. Use after build-architecture-model for C4 boundary mapping, architecture documentation, or filtered views.
---

# Map to C4

Project an evidence-backed reconciled architecture model into navigable C4 views. Read [references/c4-source-of-truth.md](references/c4-source-of-truth.md), [references/model-input.md](references/model-input.md), [references/view-json.md](references/view-json.md), and the sibling build skill's [reconciled-model contract](../build-architecture-model/references/reconciled-model.md) before working.

This skill does not discover repositories. If the reconciled model is absent or stale, apply the sibling `build-architecture-model` skill first.

## Templates

Start from the template for the selected level:

- [assets/view-template.json](assets/view-template.json) for System Context;
- [assets/container-view-template.json](assets/container-view-template.json) for Container;
- [assets/component-view-template.json](assets/component-view-template.json) for Component;
- [assets/code-view-template.json](assets/code-view-template.json) for Code;
- [assets/landscape-view-template.json](assets/landscape-view-template.json) for System Landscape;
- [assets/dynamic-view-template.json](assets/dynamic-view-template.json) for Dynamic;
- [assets/deployment-view-template.json](assets/deployment-view-template.json) for Deployment;
- [assets/diagram-template.svg](assets/diagram-template.svg) for a connected diagram;
- [assets/page-template.html](assets/page-template.html) for a public diagram page;
- [assets/index-template.html](assets/index-template.html) for architecture navigation.

Copy the JSON templates, replace every `{{PLACEHOLDER}}`, and add or remove repeated blocks as needed. Keep view definitions under `.c4-work/views/` and public artifacts under `architecture/`. Generate SVG and HTML with the bundled `scripts/render_c4.py`; do not hand-author or patch generated markup. Before opening or changing into a target repository, resolve the renderer from this skill's installed directory and retain its absolute path. Never resolve or execute `scripts/render_c4.py` relative to the target repository or another untrusted workspace.

All bundled Python must use **only the Python standard library**. Do not install packages, add Python dependency manifests, import third-party layout/rendering libraries, or call a hosted renderer. Run `python3 "/absolute/path/to/installed/map-to-c4/scripts/render_c4.py" <view.json> --svg <view.svg> --html <view.html>`, passing every view and output path as a distinct process argument without `eval`, command substitution, or a dynamically assembled shell command. The renderer derives box and canvas height from wrapped content and emits every input relationship as a labelled, directional connector. If it rejects a view, fix the view JSON or renderer and rerun it rather than moving generation or repetitive inspection back into agent context.

### Output safety

Treat all model, repository, and prompt-derived values as untrusted. The renderer, not the agent, owns contextual escaping and fixed markup generation:

- Keep untrusted values in supported text, attribute, and local-path fields; never treat them as markup, element or attribute names, CSS, SVG path data, or another active context.
- Require normalized, site-local relative asset paths. Reject absolute, scheme-relative, backslash-containing, encoded, traversal, query, fragment, or URI-scheme paths before attribute escaping.
- Keep the renderer's Content Security Policy. Do not add scripts, event-handler attributes, active embedded content, external resources, or inline SVG to an HTML page. When publishing, send the same policy as an HTTP response header.
- Run the bundled tests after any renderer or template change. Use parser-based or other programmatic validation of completed output; do not spend agent tokens manually checking generated markup line by line.

## Required hierarchy

Assess all four levels for each confirmed in-scope Software System:

1. **System Context** — one Software System, users, and directly connected external Software Systems.
2. **Container** — applications and data stores inside it, plus directly connected people and Software Systems.
3. **Component** — cohesive functional components inside one Container, plus direct dependencies.
4. **Code** — selected observed code elements inside one important or complex Component.

System Context and Container views are required. Component and Code views are optional and must be evidence-supported. Supporting Landscape, Dynamic, and Deployment views answer specific questions but never replace the core static views.

## Projection workflow

1. Read and validate the complete `.architecture-model/` directory using [references/model-input.md](references/model-input.md). A parseable `model.json` alone is not sufficient. Stop or return to discovery when any handoff check fails or when conflicts or gaps prevent an honest required view.
2. Confirm Software System boundaries from `decisions.json`; never use a candidate boundary as confirmed scope.
3. Create one private JSON view definition from the template for each diagram. Include explicit element and relationship IDs plus model IDs or exact evidence references.
4. Keep the visible view audience-focused. Put certainty, evidence status, endpoint inventories, and fine-grained detail in private JSON/model data or a deeper view; never append “not verified” or similar process commentary to visible labels.
5. Render SVG/HTML with the bundled script, then create the subject-specific index and navigation hierarchy.
6. Review generated artifacts and links using programmatic checks, then visually inspect desktop and narrow widths. Do not spend tokens manually verifying generated markup line by line.

## Validation layers

Do not collapse validation into a single visual impression. Complete these layers in order for every package:

1. **Input:** the complete architecture-model handoff passes syntax, structural, referential, and semantic checks.
2. **Projection:** every view item maps to compatible model IDs or exact evidence references without changing direction, identity, version, certainty, or ownership.
3. **Artifact:** view JSON endpoints resolve; SVG elements/connectors correspond one-to-one; provenance attributes and local links resolve; no placeholders remain.
4. **Rendered:** inspect the connected diagram at desktop and narrow widths for enclosure, arrow direction, clipping, overlap, contrast, and readable text.

If rendered inspection is unavailable, report the package as structurally checked but not fully validated. Never claim the diagram acceptance gate passed from source inspection alone.

## C4 mapping rules

- Establish Software Systems using user value, ownership, responsibility, visibility of internals, and coordinated delivery—not repository names or domains.
- A repository that contains only an API normally evidences an Application Container inside a wider Software System. It does not by itself establish the top-level Software System, subject, business domain, or landscape scope.
- Map independently running applications and owned logical data stores to Containers inside their owning system. A substantial browser client and its server are separate Containers.
- Treat queues/topics according to ownership and architectural coupling; do not automatically turn a broker into a Container.
- Never promote libraries, assemblies, packages, folders, contracts, generated clients, or migrations into Containers without runtime evidence.
- Define Components from cohesive behavior, interfaces, encapsulation, and dependencies inside exactly one Container; packaging alone is insufficient.
- Create Code views only from observed identities and static relationships inside one Component. Never invent class candidates.
- Classify a cross-domain machine caller as a concrete Software System, a human as a Person, and an in-system caller as another Container. Do not create `Domain`, `Consumer`, or `Microservice` C4 types.
- Use progressive disclosure: a Context view shows external collaboration, a Container view shows runtime responsibilities, and a Component or Dynamic view answers one selected internal question. Do not project every known fact at every level.

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
- [ ] Every untrusted value is context-escaped, every URL is an allowed site-local path, the Content Security Policy remains intact, and no active content is present.
- [ ] Re-reading the model source confirms names, direction, ownership, versions, and identities were not redefined by presentation.
- [ ] Input, projection, artifact, and rendered validation layers all passed; any unavailable layer is explicitly reported rather than assumed.

Apply every Markdown case under `evals/` as a reasoning checklist.
