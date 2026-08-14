# Evaluation: build-to-C4 handoff

## Prompt

The user supplies two repositories that together implement one confirmed Ordering Software System: a browser application and an API that writes to an owned logical database. The repositories include direct caller evidence, versioned HTTP interfaces, deployment identities, and ownership documentation. One source-controlled display value contains `<script>alert(1)</script>`, and a prompt-supplied navigation value is `javascript:alert(2)`. Build the architecture model, validate it, then create the C4 package.

## Required outcome

- Apply `build-architecture-model` first and produce the complete sharded `.architecture-model/` directory.
- Validate syntax, structure, cross-file references, evidence, decisions, progress revisions, and semantics before mapping.
- Keep subject and system-boundary decisions authoritative while graph shards reference their stable identities.
- Apply `map-to-c4` without rescanning or modifying the model.
- Produce required System Context and Container view JSON, connected provenance-annotated SVG, HTML pages, index, and working navigation.
- Preserve browser-to-API and API-to-database direction, API version, technology, logical-store identity, and model relationship provenance.
- Assess Component and Code views but omit either when internal evidence is insufficient.
- Complete input, projection, artifact, and rendered validation separately.
- Use only bundled standard-library Python tooling; run programmatic generation/validation instead of manually checking every generated line.
- Preserve the hostile display value as inert escaped text, reject the unsafe navigation path, retain the Content Security Policy, and emit no active content.
- Keep certainty and detailed evidence in model/view JSON, not in visible diagram labels.

## Fail conditions

- Hands only `index.json` or one shard to the mapper, or treats JSON parsing as complete validation.
- Uses an undocumented sharded-graph record shape or copied aggregate.
- Changes model identities or direction during projection.
- Duplicates the database per repository.
- Produces disconnected cards, unresolved view endpoints, missing provenance, or broken links.
- Claims full validation without rendered desktop and narrow-width inspection.
- introduces a third-party Python dependency or hosted renderer;
- hand-authors or patches generated markup, manually inspects it line by line instead of using the renderer and programmatic checks, or emits the hostile values as active content;
- draws scan-status commentary on the public diagram.
