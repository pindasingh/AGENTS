# Evaluation: canonical architecture-model projection

## Official sources

- https://c4model.com/tooling
- https://c4model.com/diagrams/container
- https://c4model.com/diagrams/dynamic
- https://c4model.com/diagrams/notation

## Prompt

A validated build-architecture-model canonical model contains an Orders MFE, API, worker, logical SQL schema, message channel, versioned interfaces, directed relationships, one compatible event path, one conflicting old event consumer, and a confirmed Orders Software System boundary. The user asks for C4 diagrams and also supplies the raw repositories.

## Required outcome

- Treat generated `canonical.json` as the repository-derived authority and do not independently rescan or create a second overlap/evidence model.
- Validate the canonical model and read its confirmed boundary, conflicts, gaps, nodes, relationships, and flows.
- Map the MFE/API/worker and logical schema according to C4 Container semantics; classify or condense the channel according to official queue/topic guidance.
- Preserve canonical relationship direction and materially relevant API/event versions.
- Do not flatten the conflicting old consumer into the compatible event connector.
- Put `modelBoundaryId`, `modelElementId`, and every supporting `modelRelationshipIds` in core view JSON.
- Validate canonical projection before rendering.
- Use canonical flows for selected Dynamic diagrams without inventing order.

## Fail conditions

Fail if the response:

- rescans repositories or creates a competing canonical model without returning to the gather skill;
- hand-edits generated `canonical.json`;
- uses an unconfirmed domain aggregate instead of the confirmed Software System boundary;
- reverses a relationship or hides an incompatible contract version through aggregation;
- duplicates the shared logical database per service;
- emits a core relationship with no canonical relationship provenance;
- invents Dynamic interactions absent from canonical flows;
- treats a library/framework as a Container without runtime evidence.
