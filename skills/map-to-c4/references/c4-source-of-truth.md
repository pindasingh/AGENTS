# C4 source of truth

The official C4 website is normative. This reference is a portable digest, not a replacement. When this file, the skill, a user preference, a renderer convention, or repository terminology conflicts with the official C4 definitions, follow the official C4 definitions and state the conflict.

## Normative core diagram pages

Read these pages before generating C4 diagrams when live access is available:

1. [System Context diagram](https://c4model.com/diagrams/system-context)
2. [Container diagram](https://c4model.com/diagrams/container)
3. [Component diagram](https://c4model.com/diagrams/component)
4. [Code diagram](https://c4model.com/diagrams/code)

Supporting official definitions and review material:

- [Abstractions](https://c4model.com/abstractions)
- [Software System](https://c4model.com/abstractions/software-system)
- [Container](https://c4model.com/abstractions/container)
- [Component](https://c4model.com/abstractions/component)
- [Code](https://c4model.com/abstractions/code)
- [Microservices](https://c4model.com/abstractions/microservices)
- [Queues and topics](https://c4model.com/abstractions/queues-and-topics)
- [Abstraction FAQ](https://c4model.com/abstractions/faq)
- [Diagrams](https://c4model.com/diagrams)
- [System Landscape diagram](https://c4model.com/diagrams/system-landscape)
- [Notation](https://c4model.com/diagrams/notation)
- [Review checklist](https://c4model.com/diagrams/checklist)
- [Diagram FAQ](https://c4model.com/diagrams/faq)
- [Dynamic diagram](https://c4model.com/diagrams/dynamic)
- [Deployment diagram](https://c4model.com/diagrams/deployment)
- [Tooling](https://c4model.com/tooling)
- [General FAQ](https://c4model.com/faq)

## Abstraction hierarchy

A software system consists of one or more containers. Each container contains one or more components. Each component is implemented by one or more code elements. People use software systems.

### Software System

- Highest level of abstraction.
- Delivers value to users, human or otherwise.
- Includes the system being modelled and other systems on which it depends or that depend on it.
- Often aligns with ownership, responsibility, visibility of internals, a team boundary, repository boundaries, coordinated deployment, or some combination—but none is an absolute test.
- Product domains, bounded contexts, business capabilities, feature teams, tribes, and squads are not usually software systems.

### Container

- An application or data store.
- A runtime boundary around executing code or stored data.
- Not a Docker/containerisation definition.
- Examples include server-side web applications, client-side web applications, desktop applications, mobile apps, console/batch applications, serverless functions, databases/schemas, blob/content stores, file systems, and shell scripts.
- A module, library, JAR, assembly, DLL, package, or folder is typically not a container because it is an organisational/code construct rather than a runtime construct.
- Owned cloud buckets and database schemas are generally containers even when hosted by an external provider, because they are integral architecture under the team’s control.
- Deployment is a separate concern from the container abstraction.
- A mostly server-rendered web application is usually one container; a substantial browser application and its server are two containers because they are separate process spaces communicating remotely.
- A queue or topic can be treated as a data-store container. The generic message bus is not automatically the container because that representation hides producer/consumer coupling. A genuine point-to-point queue can instead be named on the relationship and omitted as an explicit element.

### Component

- A grouping of related functionality encapsulated behind a well-defined interface.
- Exists inside one container.
- Is not separately deployable; components in a container execute in the same process space.
- Steps up one abstraction level from classes, interfaces, functions, files, objects, and similar language constructs.
- Grouping strategy depends on the codebase and can reflect layers, features, modules, ports/adapters, or another architecture, but packaging does not itself prove component identity.
- JARs, assemblies, DLLs, modules, packages, namespaces, and folders are typically not components, though a one-to-one mapping can exist when supported by architecture.
- Shared helper/supporting code may cross several components and should not automatically become a component.
- Reverse engineering and automation are encouraged for larger codebases and long-lived documentation.

### Code

- Code elements are the programming-language building blocks implementing a component.
- Examples include classes, interfaces, enums, functions, objects, and database tables where appropriate to the chosen code view.

## Four static structure diagram levels

The four core static diagrams provide different zoom levels and stories. The official site states that all four are not always needed; System Context and Container diagrams are sufficient for most teams. Component and Code diagrams are optional and should add value.

### Level 1 — System Context

- **Scope:** one software system.
- **Primary element:** the in-scope software system.
- **Supporting elements:** directly connected people and external software systems.
- **Purpose:** zoomed-out big picture showing the system in the centre, its users, and systems it interacts with.
- **Detail:** focus on people and software systems, not technologies, protocols, or implementation detail.
- **Audience:** everybody, technical and non-technical, inside and outside the team.
- **Recommendation:** recommended for all software development teams.

### Level 2 — Container

- **Scope:** one software system.
- **Primary elements:** containers inside that software system.
- **Supporting elements:** directly connected people and software systems.
- **Purpose:** high-level architecture, distribution of responsibilities, major technology choices, and communication.
- **Audience:** software architects, developers, operations/support, and other technical stakeholders.
- **Recommendation:** recommended for all software development teams.
- **Exclusion:** clustering, load balancers, replication, failover, and environment-specific infrastructure belong in Deployment diagrams.

### Level 3 — Component

- **Scope:** one container.
- **Primary elements:** components inside that container.
- **Supporting elements:** directly connected containers, people, and software systems.
- **Purpose:** responsibilities and technology/implementation details of components.
- **Audience:** software architects and developers.
- **Recommendation:** optional; create only when it adds value and consider automating long-lived documentation.

### Level 4 — Code

- **Scope:** one component.
- **Primary elements:** code elements inside that component.
- **Notation:** UML class diagrams, entity-relationship diagrams, or similar code-oriented views.
- **Purpose:** explain implementation of an important or complex component.
- **Audience:** software architects and developers.
- **Recommendation:** optional and not recommended for most long-lived documentation because IDE/tooling can generate it on demand.
- **Detail:** show only attributes and methods needed to tell the intended story.
- **Automation:** ideally generated by an IDE, UML tool, static analysis, or another repeatable mechanism.

## Supporting diagrams

### System Landscape

Shows people and multiple software systems over an enterprise, organisation, department, or similar broader scope. It is effectively a System Context diagram without one focused Software System. Useful when several repositories or systems must be understood together. It does not replace a System Context diagram for each in-scope software system. The official site recommends it particularly for larger organisations.

### Dynamic

- Shows how static-model elements collaborate at runtime for a feature, story, or use case.
- May use software systems, containers, or components.
- Based on UML communication/collaboration concepts and can use collaboration or sequence style.
- Uses numbered interactions to indicate order.
- Optional; use sparingly for interesting, recurring, or complicated interactions.
- Does not replace any core static level.

### Deployment

Captures environment-specific mapping of Software System and/or Container instances to nested deployment nodes. Infrastructure nodes can represent supporting DNS, load balancers, firewalls, and similar services. Use separate diagrams per environment where needed. Do not put this detail on Container diagrams. The official site recommends Deployment diagrams.

## Notation rules

C4 is notation independent. It does not mandate blue/grey boxes, a renderer, diagram language, or fixed visual style.

Every diagram should:

- stand mostly on its own without narrative;
- have a title that states diagram type and scope;
- have a key/legend explaining shapes, colours, borders, lines, arrowheads, icons, and other notation;
- explain acronyms and abbreviations for the intended audience.

Every element should:

- have a name;
- explicitly state its C4 type;
- have a short responsibility description;
- state technology for every container and component;
- use consistent visual semantics.

Every relationship should:

- be unidirectional;
- have a label consistent with direction and intent;
- use a specific description rather than a vague single word such as `Uses`;
- state technology/protocol for inter-container communication;
- use understandable and consistently explained line/arrow styling.

Colours must be consistent and usable for black-and-white printing and colour-vision differences. Meaning must not rely on colour alone.

Dependency direction and data-flow direction are both valid relationship choices. Whichever is chosen, the label must be specific and match the arrow direction.

Alternative visualisations are allowed. Traditional boxes and arrows are common but not mandatory. UML, ArchiMate, and other notations can express C4 abstractions if the types and meaning remain clear.

## Rendering acceptance profile used by this skill

The official notation guidance repeatedly requires lines/arrows to be directional, labelled, and understandable. Therefore, when this skill emits a boxes-and-lines C4 view:

- relationships must be visible connectors on the same canvas as their source and destination elements;
- each connector must have an arrowhead and specific label;
- inter-container connectors must include protocol/technology;
- scoped children must be visibly enclosed by the correct software-system, container, or component boundary;
- a detached relationship list cannot replace connectors;
- an HTML card grid is not accepted as a rendered C4 diagram;
- renderer source and the rendered SVG/PNG must both be retained;
- the rendered artifact must be visually inspected before validation can pass.

This is a strict rendering profile within C4’s notation independence; it does not redefine the C4 abstractions.

Do not create pseudo-elements such as software-system groups or data-store groups to condense unresolved elements. Condense using filtered views while preserving real element identities.

A candidate software-system boundary can remain in discovery material, but it cannot anchor a core four-level diagram package merely for navigation. Component views require evidenced interfaces/dependencies. Code views require observed code-element identities and static relationships; summary prose and guessed class names are not sufficient.

## Official review checklist

### General

- Does the diagram have a title?
- Is the diagram type understandable?
- Is the scope understandable?
- Does it have a key/legend?

### Elements

- Does every element have a name?
- Is every element’s abstraction type clear?
- Is every element’s responsibility understandable?
- Are technology choices clear where applicable?
- Are acronyms and abbreviations understandable?
- Are all colours, shapes, icons, border styles, and size differences explained?

### Relationships

- Does every arrow have a label describing relationship intent?
- Does each description match arrow direction?
- Are relationship technologies/protocols clear where applicable?
- Are acronyms and abbreviations understandable?
- Are all colours, arrowheads, and line styles explained?

## Modelling, terminology, and scale

The official tooling guidance recommends separating a canonical, non-visual model (a directed graph of elements and relationships) from the filtered views rendered as diagrams. Reuse identities rather than copying and independently renaming boxes across diagrams.

Organisations may change the words used for the four abstractions if everybody explicitly understands the mapping. Additional abstraction levels are possible but are an advanced manoeuvre requiring precise definitions; they must not be a shortcut for organisational groupings such as layers, libraries, bounded contexts, or subsystems.

Do not force a large model onto one canvas. Split a crowded view into multiple simpler filtered diagrams at the same abstraction level, focused by business area, functional grouping, bounded context, use case, feature, or dependency neighbourhood. Preserve the same model identities and do not mix levels. Alternative visualisations can supplement the traditional boxes-and-arrows view.

C4 focuses on the static structure of custom-built software systems. Supplement it with UML, BPMN, ArchiMate, entity-relationship, state, timing, or other appropriate views for business processes, workflows, state machines, domain/data models, and concerns C4 does not cover. Libraries, frameworks, and SDKs are often better documented with code-oriented notation or through a C4 usage example rather than being forced into a Software System hierarchy.

## Applying C4 to repositories

The official definitions describe architecture, not repository bookkeeping. Therefore:

- Never use one-repository-equals-one-system as an axiom.
- Never use directory/package/namespace identity as automatic component identity.
- Use runtime, ownership, responsibility, interface, dependency, and deployment evidence to map repositories into the official abstractions.
- Preserve uncertainty where repository evidence cannot establish an official C4 boundary.
- Keep repository overlap reconciliation as an evidence-management concern; do not change C4 definitions to accommodate duplicated or fragmented source.

### Microservices and split repositories

Apply the official runtime definition of Container rather than repository naming:

- independently running APIs, workers, schedulers, consumers, and functions are normally Application Containers within an established Software System boundary;
- an owned database/schema or storage boundary is a Data Store Container;
- shared libraries, contract packages, generated clients, migration tooling, modules, and folders are not Containers merely because they have separate repositories;
- a microservice can be a Software System only when the higher-level value/ownership/responsibility boundary supports that classification;
- domains and bounded contexts remain organisational concepts rather than C4 element types.

### Consumers across domains

On a System Context diagram, a separately owned machine consumer is represented as an external Software System connected to the in-scope Software System. On the Container diagram, that same external Software System connects to the specific API/application Container and the relationship states protocol/technology. Human consumers are People. A broad cross-domain view uses a System Landscape of peer Software Systems; it does not use `Domain` as a C4 element type.
