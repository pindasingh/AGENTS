---
name: map-to-c4
description: Projects a validated canonical architecture model into navigable C4 System Context, Container, Component, Code, and supporting diagrams. Use after build-architecture-model for C4 boundary mapping, architecture documentation generation, filtered views, or validating C4 diagrams against repository evidence.
compatibility: Requires a build-architecture-model canonical model and Python 3. Uses bundled standard-library validation and SVG rendering; no paid product, external renderer, package installation, network service, model provider, or agent-specific feature is required.
---

# Map to C4

Project an evidence-backed canonical architecture model into a navigable C4 model and rendered views.

Before doing any work, read [references/c4-source-of-truth.md](references/c4-source-of-truth.md) and [references/canonical-input.md](references/canonical-input.md) completely. The official C4 pages linked there are normative. If live access is available, read the current official pages too. Never redefine a C4 abstraction to fit repository layout, discovery terminology, or a preferred visual style.

This skill does not perform repository discovery. If the user supplies raw repositories or the canonical model is absent/stale, load and run the sibling `build-architecture-model` skill first. Its generated `canonical.json` is architecture working memory and the only repository-derived input to this skill. Never hand-edit it or create a competing evidence ledger.

## Required result

Use the four-level C4 hierarchy without forcing all four diagrams:

1. **System Context** — one software system, its users, and directly connected external software systems.
2. **Container** — applications and data stores inside one software system, plus directly connected people and software systems.
3. **Component** — cohesive functional components inside one container, plus directly connected containers, people, and software systems.
4. **Code** — selected code elements inside one important or complex component.

Assess all four levels for every in-scope software system. System Context and Container diagrams are required and are sufficient for most teams. Generate Component and Code diagrams only where the code and architectural value support them, as the official guidance recommends. Track omitted optional views internally; never render a coverage matrix, omission assessment, or skill-compliance manifest in the engineer-facing architecture site. Never fabricate a level merely to fill a slot.

Supporting System Landscape, Dynamic, or Deployment diagrams may be added when they answer a real question. They do not replace the applicable core static views.

## Diagram acceptance gate

For this skill, a C4 diagram is a rendered, connected architectural view—not a collection of cards followed by a relationship list.

A generated diagram MUST:

- place all included elements on one diagram canvas;
- render every included relationship as a visible unidirectional connector from the actual source element to the actual destination element;
- place the relationship description on or immediately beside that connector;
- show the scoped software-system, container, or component boundary spatially around its children where the level requires it;
- preserve enough whitespace that connectors, arrowheads, labels, and element text are legible;
- include the title, element metadata, technologies, and key required by official C4 notation guidance.

A relationship table or ordered list may supplement a diagram, but it NEVER substitutes for visible connectors. An HTML/CSS grid of disconnected boxes is an element catalogue, not a C4 diagram. Arrow characters used as list markers are not relationships. Navigation links between cards are not relationships.

Use the bundled dependency-free renderer by default:

```bash
python scripts/render_c4.py assets/preflight-view.json --svg <temporary-path>/preflight.svg --html <temporary-path>/preflight.html
```

It writes native static SVG using only Python’s standard library. It requires no account, licence, download, package installation, network access, or external renderer. Structurizr, C4-PlantUML, Mermaid, and Graphviz are optional alternatives only when already available or explicitly requested.

Before creating or replacing any public architecture page, run the bundled preflight, inspect the SVG, and confirm it contains two elements joined by one visible labelled arrow. If the bundled renderer fails, fix the view data or renderer; do not fall back to disconnected cards or relationship prose and do not ask the user to install a paid/external product.

Create each project view as JSON using `assets/preflight-view.json` as the minimal example and [references/view-json.md](references/view-json.md) as the schema, then render it with:

```bash
python scripts/render_c4.py <view.json> --svg <diagram.svg> --html <diagram.html>
```

Generated diagrams are static. Do not add clickable diagram elements, JavaScript zooming, tooltips, canvas interaction, or other “diagram magic.” Ordinary breadcrumbs and index-page links outside the SVG are sufficient. Preserve browser-native page zoom and pinch zoom: use SVG viewboxes, responsive full-width images, and never disable scaling with viewport settings such as `user-scalable=no`.

Every rendered view must have an explicit internal view definition listing its included element IDs and relationship IDs. Rendered SVG must annotate elements with `data-c4-element-id` and connectors with `data-c4-relationship-id`, `data-source-id`, `data-destination-id`, and `data-label` (post-process renderer output if necessary). The rendered connector count must match the included relationship count. Inspect the actual rendered artifact before reporting success.

The bundled renderer uses deterministic obstacle-aware orthogonal routing. It routes connectors around element boxes, allocates separate ports/lanes, places labels only in collision-free regions, and draws a white underlay at unavoidable non-planar crossings. Rendering fails when it cannot place a route or label safely. The bundled validator independently rejects element overlap, label/element overlap, label/label overlap, connectors crossing unrelated elements or labels, and collinear connector overlap. Reliability means fail-closed: no diagram is accepted with a detected collision.

Keep each view readable:

- include only elements and relationships needed for that diagram’s story;
- do not turn System Context into an inventory of editors, browsers, source-control tools, libraries, or implementation utilities unless they are architecturally significant direct dependencies;
- use explicit positions in the view JSON when automatic layout creates crossed lines or overlapping labels;
- split a dense subject into multiple filtered diagrams at the same C4 level rather than shrinking text or dumping every relationship into one view;
- keep labels concise and move operational detail into adjacent architecture content;
- make the public index show the actual System → Container → Component → Code zoom path so deeper levels are discoverable without a coverage matrix.

Reject the output if any of these is true:

- elements are disconnected and relationships exist only as prose;
- a line has no direction or label;
- a label’s direction does not match its relationship;
- connectors terminate ambiguously, cross element text, or are unreadable;
- a boundary contains elements that are not children of that boundary;
- a pseudo-element was invented only to make layout or navigation easier;
- validation claims “pass” without inspecting the rendered diagram.

## Non-negotiable C4 boundaries

- A repository is evidence, not automatically a software system.
- A product domain, bounded context, business capability, team, tribe, squad, namespace, package, folder, module, library, assembly, or JAR is not automatically a software system, container, or component.
- A software system is the highest C4 abstraction and delivers value to users.
- A container is an application or data store and represents a runtime boundary. “Container” does not mean Docker or another infrastructure container.
- A component is related functionality encapsulated behind a well-defined interface inside one container. Components are not separately deployable.
- Code elements are language-level building blocks inside one component.
- Deployment infrastructure is not a container diagram. Use a Deployment diagram when environment-specific infrastructure is evidenced.
- Business processes, workflows, state machines, and domain models are outside C4's static-structure scope; supplement C4 with an appropriate notation rather than relabelling them as C4 elements.

Candidate identities belong in the discovery model and overlap report. Do not invent an aggregate candidate software system merely to obtain a page hierarchy or force four levels. A core System Context diagram requires an evidenced or explicitly user-confirmed software-system boundary. If that boundary cannot be established, stop core diagram generation, present the competing candidates, and request a boundary decision.

Do not invent pseudo-types such as `External Software System group`, `Container group`, or `Data-store group`. Show separately evidenced C4 elements, use multiple filtered views, or omit unresolved elements. Visual condensation must not create a false architectural identity.

## Workflow

### 0. Validate and select the modelled subject

Locate `.architecture-model/canonical.json`, `subject.json`, and `decisions.json`. Validate the canonical model before mapping:

```bash
python ../build-architecture-model/scripts/architecture_model.py validate <model-dir>
```

If validation fails, return to `build-architecture-model`; do not repair generated data here. Confirm every requested source has the expected revision and scan status. Read canonical gaps and conflicts before deciding that a C4 view is supportable.

Use the canonical subject as navigation scope, not automatically as a Software System. The public index title, descriptions, systems, diagrams, and links must use subject-specific architectural language. Reject generic repository or skill-process boilerplate.

### 1. Resolve C4 Software System boundaries

Read `canonical.systemBoundaries`. Preserve every confirmed decision exactly. Do not reopen it, change member identity, or ask the user to reconfirm unless the user explicitly requests remodelling or new gathered evidence creates a recorded conflict.

When no confirmed boundary exists, assess candidates using user value, ownership, responsibility, implementation visibility, and independent delivery evidence from the canonical model. Present competing subject-specific boundaries in plain language once and store the resulting decision in `.architecture-model/decisions.json`; then rerun the model compiler. Until a boundary is confirmed, use a System Landscape or stop core diagram generation rather than inventing a scope.

A domain, repository collection, team, library set, or convenient page hierarchy is not a Software System boundary.

### 2. Project canonical discovery nodes

Create C4 identities from canonical nodes without rescanning repositories:

- confirmed boundary -> one scoped Software System;
- member `runtime` -> normally an Application Container;
- member logical `store` -> normally a Data Store Container;
- `channel` -> owned Data Store Container only when C4 queue/topic guidance supports it, otherwise communication detail on a relationship;
- `library` -> supporting evidence, not a runtime Container;
- separately owned/confirmed external machine dependency -> external Software System;
- human actor -> Person.

One canonical node keeps one identity across every view. Use canonical node IDs as `modelElementId`; view-local IDs are presentation IDs only. Do not duplicate a shared logical database per service or merge separate schemas because they share a server.

For optional Component and Code views, use only evidenced cohesive interfaces/code identities. The current gathering model primarily guarantees runtime, store, interface, contract, relationship, and flow evidence; omit lower levels when that evidence does not establish them.

### 3. Project canonical relationships and flows

Every C4 connector must derive from one or more canonical relationship IDs and preserve source-to-destination direction. Put those IDs in `modelRelationshipIds` in the view JSON.

Aggregate endpoint relationships only when projected source, destination, direction, technology, and purpose are compatible. Preserve materially different API/event versions; never hide a contract conflict through aggregation. For event paths, a publisher-to-consumer connector can condense publisher -> channel -> consumer only when compatible contracts corroborate the complete directed path; retain both model relationship IDs and name the channel/protocol.

Use canonical flows for selected Dynamic diagrams. Include boundary-crossing steps and only architecturally meaningful internal rules. Generate visual sequence numbers from the selected ordered flow; do not invent missing operation order.

### 4. Build explicit filtered view definitions

Create renderer view JSON only after the C4 projection is established. System Context, Container, and Dynamic scopes require `modelBoundaryId`; elements require `modelElementId`; relationships require `modelRelationshipIds`. Validate projection traceability before rendering:

```bash
python scripts/validate_canonical_projection.py <model-dir>/canonical.json <view-json-or-directory> [...]
```

Keep the canonical model separate from views. Views filter and aggregate the model; they never redefine names, types, direction, ownership, versions, or identities. Do not draw first and infer the model from the picture later.

### 5. Identify software systems

Use value, ownership, responsibility, visibility of internals, team boundary, and coordinated delivery/deployment as evidence. A repository can contain multiple software systems; one software system can span multiple repositories.

Do not use product domains or bounded contexts as substitutes for software systems. They may organize navigation or scope, but the C4 element must still be a person, software system, container, component, or code element. Never promote a conceptual domain/platform aggregate to an in-scope software system solely “for navigability.”

For microservices, ownership determines the zoom boundary. Services owned as implementation details by one team are normally one or more Containers inside that team's Software System. A service owned independently by another team can be a separate Software System, with its applications and data stores becoming that system's Containers. Do not preserve an old C4 type after the evidenced ownership boundary changes.

### 6. Identify containers

Inside each software system, find applications and data stores that must run or exist for the system to work, including:

- server-side or client-side applications;
- desktop or mobile applications;
- console/batch applications;
- serverless functions;
- databases/schemas;
- blob/content stores;
- file systems;
- independently executed scripts.

A mostly server-rendered web application is usually one Container. A substantial browser application and its server are two Containers because they occupy separate process spaces and communicate remotely. Treat an owned database schema, cloud bucket, or similar managed data boundary as a Container even when an external provider hosts the service; deployment location remains a separate concern.

For messaging, model the architectural coupling rather than the broker topology. A queue or topic can be an owned Data Store Container; the generic message bus/broker is not automatically a C4 Container. For a genuine point-to-point interaction, the queue may instead be omitted and named in a directional relationship (for example, `Sends orders via queue X`). Record ownership explicitly when queues or topics connect separately owned Software Systems.

Do not classify ordinary libraries, modules, assemblies, packages, or folders as containers. Distinguish runtime boundaries from deployment infrastructure.

#### Microservices and repository-per-runtime layouts

Do not translate the user’s informal word `component` directly into the C4 Component abstraction. In a microservice architecture:

- each independently running API, worker, scheduler, consumer, serverless function, or service is usually an Application Container inside its owning Software System;
- each owned database/schema, blob store, or file store is usually a Data Store Container;
- a repository containing only a shared library, contracts, generated client, migrations tooling, or packaging is not automatically a Container;
- a microservice can instead be a Software System when independent value, ownership, responsibility, and visibility boundaries establish it as such;
- a business domain can contain or be touched by several Software Systems, but the domain itself is not a C4 element;
- one repository can contain several Containers, and one Container can be assembled from several repositories.

First establish Software System ownership/value boundaries, then map repositories to runtime/data Containers, then identify Components inside each Container. Preserve a repository-to-element evidence mapping so duplicated contracts, generated clients, migrations, and shared libraries do not become duplicate architecture elements.

#### Consumers from another domain

Classify the concrete caller, not the organisational domain label:

- a separately owned machine caller is an external **Software System** on the scoped system’s System Context diagram;
- on the Container diagram, connect that external Software System to the exact API/worker-facing Container and label protocol/technology;
- a human caller is a **Person**;
- a caller inside the same Software System is another **Container**;
- use a System Landscape diagram to show peer Software Systems across several domains;
- do not create a C4 element typed `Domain`, `Consumer`, or `Microservice` when Person, Software System, Container, Component, or Code Element is the actual abstraction.

The same canonical element keeps one C4 type. Its visual role can be in-scope in its own diagrams and external/supporting in another system’s diagrams without changing identity.

### 7. Identify components

Within one container, group code elements into cohesive units of related functionality behind well-defined interfaces. Use behavior, public interfaces, dependency direction, encapsulation, and architectural role. Packaging can support the decision but cannot make it by itself.

A Component diagram requires enough evidence to name the component boundary, interface/responsibility, and dependencies. Do not infer generic components such as “API clients”, “orchestration”, or “services” from prose summaries alone unless code and interfaces establish that cohesive grouping.

Exclude code-level noise that does not help architecture discussions. Shared helpers may remain supporting code rather than being promoted to components.

For large or long-lived codebases, prefer reproducible reverse engineering over manual diagrams.

### 8. Select code views

Choose only important or complex components. Show code elements needed to tell the architectural story, such as classes, interfaces, functions, objects, or database tables. Hide attributes and methods that add noise. Prefer generation from IDEs, UML tooling, static analysis, or a repeatable script.

A Code diagram requires actual code-element identities and static relationships from source or trustworthy generated analysis. Narrative summaries, screenshots that omit declarations, or guessed class names are insufficient. Never put an unnamed or invented `Class candidate` on a Code diagram. Omit the view and state the evidence gap instead.

A Code diagram has the scope of one component. Do not produce a repository-wide class diagram and label it a C4 Code diagram. Boxes plus a detached prose list of calls are not a UML class, entity-relationship, or equivalent connected Code diagram.

### 9. Render the four levels

Create renderer-native diagram source first, render it to SVG/PNG, embed or link that artifact from the documentation page, and retain the source beside it. The surrounding page may contain context tables, but the rendered artifact is the diagram.

#### Level 1 — System Context

For each software system:

- place the in-scope software system at the centre;
- show directly connected people and external software systems around it;
- draw and label every included person/system relationship on the diagram canvas;
- keep technology, protocol, and implementation detail out;
- describe the value and intent of each relationship.

#### Level 2 — Container

For each software system:

- show its applications and data stores;
- show responsibility distribution and major technology choices;
- show communication between containers with visible labelled connectors;
- include directly connected people and external software systems and connect them on the canvas;
- label inter-container relationships with technology/protocol;
- do not show clustering, replicas, load balancers, or environment topology here.

#### Level 3 — Component

For each selected container:

- show components inside that one container;
- include each component’s responsibility and technology/implementation detail;
- show directly connected containers, people, and software systems with visible labelled connectors;
- do not mix components from several container scopes into one Component diagram.

#### Level 4 — Code

For each selected component:

- show only code elements inside that one component;
- use a connected UML class, entity-relationship, or another suitable code notation;
- draw the static relationships between included code elements;
- include only detail needed for the story;
- generate from tooling where practical.

### 10. Add supporting views correctly

- **System Landscape:** show people and peer Software Systems across an enterprise, organisation, department, or similar broad scope. It is a System Context diagram without one focused Software System; it does not replace each in-scope system's System Context diagram.
- **Dynamic:** use only for significant stories, features, or complicated collaborations. Reuse Software Systems, Containers, or Components from the static model, number interactions in runtime order, and put requests, events, commands, responses, and mutation intent on unidirectional relationship labels. Dependency or data-flow direction is acceptable, but the wording must match the arrow.
- **Deployment:** show instances of Software Systems/Containers mapped onto nested deployment nodes in one named environment. Infrastructure nodes such as DNS, load balancers, and firewalls belong here rather than on the Container diagram. Create separate views when environments differ.

Supporting diagrams never replace the core static views. The bundled JSON renderer supports the four core types and Dynamic views; use an already available suitable renderer for System Landscape or Deployment views and retain stable model annotations in the SVG.

## Navigation and condensation

Never put the entire architecture on one page.

Generate a hierarchy such as:

```text
architecture/
  index.html                         # useful architecture navigation only
  systems/<system-id>/context.html  # Level 1
  systems/<system-id>/containers.html # Level 2
  systems/<system-id>/containers/<container-id>/components.html # Level 3
  systems/<system-id>/containers/<container-id>/components/<component-id>/code.html # Level 4
  flows/<flow-id>.html              # optional dynamic views
.architecture-model/                  # canonical architecture working model
.c4-work/                            # private C4 projections, views, and validation
```

Use breadcrumbs and links to zoom in/out. The C4 zoom chain is System Context → Container, selected Container → Component, and selected Component → Code. Component and Code views remain optional: create and link them only where they add value. When a lower-level view exists, provide an obvious ordinary page link outside the static SVG that names both the target scope and level (for example, `Level 3 — Zoom into <container> components`). Diagram elements themselves do not need to be clickable. Each diagram page must have one scope and one abstraction level. Provide indexes rather than duplicating diagrams.

When a view becomes crowded, create several filtered views at the same abstraction level, each telling a focused part of the same story. Keep canonical element names, types, and relationship identities consistent across those views. Do not solve scale by mixing abstraction levels or by creating fake grouping elements.

The public `architecture/index.html` is a subject-specific architecture index, not a skill execution report. Its heading and summary must name the modelled domain/system and explain its architectural purpose. It should contain only useful navigation: software systems and their responsibilities, links to Context and Container diagrams, the actual System → Container → Component → Code zoom paths, and optional Dynamic/Deployment views. Do not expose generic repository descriptions, host documentation tooling, a four-level coverage matrix, omitted-view reasoning, evidence ledger, overlap report, validation checklist, repository inventory, corrected-scope narrative, confidence dashboard, or other skill/process metadata. Keep canonical model artifacts under `.architecture-model/` and C4 projection artifacts under `.c4-work/`; leave both unlinked unless the user explicitly requests an audit report.

Repository-to-model mappings, identity reconciliation, and conflicts remain authoritative in `.architecture-model/`; do not duplicate them under `.c4-work/`. Expose only architectural conclusions and relevant uncertainty on the affected diagram page.

Keep element descriptions short. Put detailed interfaces, operations, and state mutations in adjacent architecture tables or linked detail pages rather than bloating diagram boxes. Keep raw evidence and skill compliance out of the public site.

## Official notation requirements

The C4 model is notation independent; this means visual notation may vary, not that relationships may be removed from the diagram. Organisational terminology may replace the words used by C4 only when the mapping is explicitly defined and understandable; do not change the underlying hierarchy. Adding a new abstraction level is an advanced exception that requires a precise definition and must not be used merely for organisational groupings. Do not claim that a particular colour or shape is mandatory. Whatever notation is chosen, every diagram must stand mostly on its own and include:

- a title naming diagram type and scope;
- a key/legend;
- explicit element types;
- a short responsibility description for every element;
- technology for every container and component, explicitly `Unknown` when unavailable;
- a visible connector and arrowhead for every included unidirectional relationship;
- a specific label on or immediately beside every connector;
- technology/protocol on inter-container relationships;
- explained acronyms, colours, shapes, icons, border styles, line styles, arrowheads, and size differences;
- consistent, accessible colour use that does not rely on colour alone.

Avoid vague labels such as `Uses`.

## Validation

Run the official review checklist captured in the reference before completion. Validation is a failing gate, not a public narrative page that automatically says `Pass`. Do not generate `architecture/validation.html` or link validation from the public index.

For each view, compare its view definition with the rendered artifact:

1. every included element ID is rendered exactly once unless the notation explicitly requires repetition;
2. every included relationship ID has a visible connector;
3. connector source, destination, direction, label, and protocol match the canonical model;
4. no rendered element or connector lacks a model ID;
5. the scoped boundary encloses exactly the in-scope children;
6. the rendered output was opened or previewed at normal desktop width and checked for overlap, crossed labels, readable font size, and legibility;
7. the validator’s geometry checks report no element, label, or connector collision.

If any check cannot be performed, mark validation incomplete. Do not claim the diagram passes.

Run the canonical and projection validators before the package validator:

```bash
python ../build-architecture-model/scripts/architecture_model.py validate <model-dir>
python scripts/validate_canonical_projection.py <model-dir>/canonical.json <view-json-or-directory> [...]
python scripts/validate_c4_package.py <path-to-architecture-directory>
```

A non-zero exit is a hard failure. Fix the owning model scan/decision, C4 projection, or package as appropriate; never bypass, weaken, or replace a validator with a prose checklist.

Also verify:

- [ ] Every requested repository has a validated model scan at the intended revision.
- [ ] Canonical conflicts and gaps affecting required views were resolved or explicitly block completion.
- [ ] Canonical identity and reconciliation came from the generated architecture model, not a second C4-local inventory.
- [ ] Every core-view element and relationship retains canonical model IDs.
- [ ] Every system has System Context and Container diagrams.
- [ ] Every implemented container was assessed for a Component diagram.
- [ ] Important/complex components were assessed for a Code diagram.
- [ ] Optional-view assessment remains private and no coverage matrix appears on the public index.
- [ ] The public index contains architecture navigation rather than skill, evidence, overlap, or validation metadata.
- [ ] Every page has one clear C4 scope and level.
- [ ] Every diagram page embeds or links a real rendered diagram artifact and its source.
- [ ] Every included relationship is a visible labelled connector between its model elements.
- [ ] Relationship lists/tables are supplementary rather than substitutes for connectors.
- [ ] No aggregate candidate system, external-system group, or data-store group was invented for layout.
- [ ] Component diagrams use evidenced cohesive interfaces and dependencies.
- [ ] Code diagrams use observed code identities and connected static relationships.
- [ ] Optional Dynamic diagrams do not replace core levels.
- [ ] Uncertainty and conflicting snapshots remain explicit.
- [ ] No repository structure was blindly promoted into a C4 abstraction.
- [ ] Independently running APIs/workers and owned schemas were assessed as Containers rather than mislabeled Components.
- [ ] Shared libraries, contracts, generated clients, and migrations were not promoted to runtime Containers without evidence.
- [ ] Cross-domain machine consumers are concrete Software Systems connected to the specific API Container at Level 2.
- [ ] The output contains no project-specific assumptions from this skill.

## Skill evaluations

Run `python evals/run_evals.py` after changing this skill, its renderer, schema, or validation rules. Then apply every reasoning evaluation to the proposed behavior; the executable runner checks suite integrity and deterministic rendering/validation contracts, while the Markdown cases grade architectural reasoning.

- [Canonical model projection](evals/canonical-model-projection.md)
- [Software-system boundary ambiguity](evals/software-system-boundary-ambiguity.md)
- [Microservices split across repositories](evals/microservices-repo-per-runtime.md)
- [Microservice ownership transition](evals/microservices-ownership-transition.md)
- [Cross-domain API consumer](evals/cross-domain-api-consumer.md)
- [Web clients and managed data stores](evals/web-clients-and-managed-data-stores.md)
- [Queues and topics](evals/queues-and-topics.md)
- [Core diagram scopes](evals/core-diagram-scopes.md)
- [Component and Code evidence](evals/component-and-code-evidence.md)
- [Notation and relationship quality](evals/notation-and-relationship-quality.md)
- [Supporting diagrams](evals/supporting-diagrams.md)
- [Model, views, and scale](evals/model-views-and-scale.md)
- [Scope and extension requests](evals/scope-and-extension-requests.md)

Any response matching a listed fail condition indicates a regression in the skill.
