# Evaluation: Component and Code evidence

## Official sources

- https://c4model.com/abstractions/component
- https://c4model.com/abstractions/code
- https://c4model.com/diagrams/component
- https://c4model.com/diagrams/code
- https://c4model.com/diagrams/faq

## Prompt

A repository summary says an API probably has “controllers, business logic, services, utilities, and data access”. Only a deployment manifest and README are available; source declarations and interfaces are absent. The user asks for Component and Code diagrams and suggests using folders as Components and inventing representative class names.

## Required outcome

- Do not infer Components from generic prose, layer words, folder/package names, JARs, assemblies, or namespaces alone.
- A Component requires cohesive related functionality behind a well-defined interface inside one Container; it is not separately deployable.
- Shared utilities do not automatically become a Component.
- A Code view requires observed language-level identities and static relationships inside one selected Component.
- Omit both optional views and record the evidence gap privately rather than fabricating them.
- When lower-level evidence does exist, require exact `evidenceRefs` for Component/Code scopes, elements, and relationships instead of misusing canonical runtime IDs.
- Explain that Component diagrams should add value and long-lived Component/Code views should be automated or generated on demand where practical.
- Still produce the evidenced System Context and Container views if their boundaries are established.

## Fail conditions

Fail if the response:

- makes each folder, package, JAR, assembly, or layer a Component by default;
- treats a separately deployable service as a Component;
- invents interfaces, classes, functions, methods, tables, or static relationships;
- creates an unnamed `Class candidate`;
- creates a repository-wide Code diagram;
- claims optional views are required for C4 completeness;
- emits a Component or Code identity/relationship without exact source-evidence provenance.
