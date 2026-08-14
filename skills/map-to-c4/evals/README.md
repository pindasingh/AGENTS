# Map-to-C4 evaluations

These evaluations use the live official pages at [c4model.com](https://c4model.com/) as the normative source and the build-architecture-model reconciled model as repository-derived input. They cover:

- Software System boundary uncertainty and repository overlap;
- Containers, web process boundaries, managed data stores, microservices, queues, and topics;
- correct System Context, Container, Component, and Code scopes;
- evidence thresholds and optional lower-level views;
- notation and the official review checklist;
- System Landscape, Dynamic, and Deployment views;
- architecture-model traceability, filtered views, scale, terminology, and C4's scope limits.

Each Markdown file is a reasoning eval with a prompt, required result, and explicit fail conditions. A response fails if it matches any fail condition, even if other parts are correct. Official URLs in each file identify the grading authority.

Apply each Markdown case as a reasoning checklist to the agent response being reviewed. An outer evaluation system may stage inputs and grade the listed required results and fail conditions.

Review the artifacts directly: all four eligible core view types must use connected provenance-annotated SVG; abstraction levels must not be mixed; Dynamic interactions must be numbered; public pages must contain subject-specific navigation; and the geometry, provenance, and link checks in `SKILL.md` must be completed.
