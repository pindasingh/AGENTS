# Evaluation: build-to-C4 handoff

## Prompt

The user supplies two repositories that together implement one confirmed Ordering Software System: a browser application and an API that writes to an owned logical database. The repositories include direct caller evidence, versioned HTTP interfaces, deployment identities, and ownership documentation. Build the architecture model, validate it, then create the C4 package.

## Required outcome

- Apply `build-architecture-model` first and produce the complete five-part `.architecture-model/` directory.
- Validate syntax, structure, cross-file references, evidence, decisions, progress revisions, and semantics before mapping.
- Make `model.subject` and `model.systemBoundaries` exact mirrors of their authoritative files.
- Apply `map-to-c4` without rescanning or modifying the model.
- Produce required System Context and Container view JSON, connected provenance-annotated SVG, HTML pages, index, and working navigation.
- Preserve browser-to-API and API-to-database direction, API version, technology, logical-store identity, and model relationship provenance.
- Assess Component and Code views but omit either when internal evidence is insufficient.
- Complete input, projection, artifact, and rendered validation separately.

## Fail conditions

- Hands only `model.json` to the mapper or treats JSON parsing as complete validation.
- Uses an undocumented reconciled-model record shape.
- Changes model identities or direction during projection.
- Duplicates the database per repository.
- Produces disconnected cards, unresolved view endpoints, missing provenance, or broken links.
- Claims full validation without rendered desktop and narrow-width inspection.
