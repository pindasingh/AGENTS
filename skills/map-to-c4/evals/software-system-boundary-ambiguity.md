# Evaluation: software-system boundary ambiguity

## Official sources

- https://c4model.com/abstractions/software-system
- https://c4model.com/diagrams/system-context
- https://c4model.com/diagrams/system-landscape

## Prompt

Three repositories named `sales`, `billing`, and `shared-platform` are owned by two teams. The repositories contain several executables and shared libraries. Documentation calls all three names “domains”, but does not state which user-valued products exist, which team owns each runtime, or which internals each team can see. Generate the complete C4 package now and use each repository as a Software System so navigation is simple.

## Required outcome

- Reject repository name, domain terminology, and navigation convenience as sufficient Software System evidence.
- Preserve the competing user-value/ownership boundaries as candidates in private discovery material.
- Do not generate core System Context or Container diagrams until one confirmed Software System boundary is evidenced or explicitly confirmed.
- Ask one focused boundary question that describes the plausible domain-specific alternatives.
- A temporary System Landscape may show separately evidenced Software Systems only; it must not turn the three unresolved names into confirmed systems.
- Do not silently model the documentation repository or helper tooling instead.

## Fail conditions

Fail if the response:

- creates one Software System per repository;
- creates a `Domain`, `Platform group`, or aggregate candidate as a C4 element;
- treats executables as Software Systems before establishing the higher-level value/ownership boundary;
- fabricates a System Context scope to satisfy a four-level template;
- asks the user to resolve routine repository bookkeeping instead of the architectural boundary;
- presents unresolved candidates as authoritative architecture.
