---
name: build-architecture-model
description: Scans one or many code repositories incrementally and builds an evidence-backed, C4-neutral canonical architecture model of runtimes, stores, interfaces, contracts, dependencies, operations, conflicts, and gaps. Use before architecture mapping, C4 generation, cross-repository dependency analysis, system discovery, or architecture impact analysis.
compatibility: Requires repository read access and Python 3. The bundled model compiler and validators use only Python's standard library.
---

# Build Architecture Model

Discover the architecture of a user-named subject one repository at a time. The subject can be a system, product, platform, service estate, business domain, or another explicitly selected scope; do not assume DDD. Produce accurate repository-local findings first and compile them deterministically into a canonical working model after every repository. Do not draw C4 diagrams in this skill or assign C4 abstraction types during discovery.

Before scanning, read [references/model-spec.md](references/model-spec.md) completely. Read the applicable framework playbooks under `references/` after detecting the repository technologies.

## Harness portability

This skill follows the Agent Skills directory format: the skill root is this directory, `SKILL.md` is the required entrypoint, and bundled files are addressed with paths relative to this skill root. It is safe to install as a personal, project, or plugin skill in any harness that supports Agent Skills.

Do not assume the agent's shell working directory is the skill root. When running a bundled script or reading a bundled asset from another repository, first resolve the absolute path to this skill directory, then use that path. For example:

```bash
SKILL_DIR="<absolute path to the build-architecture-model skill directory>"
python "$SKILL_DIR/scripts/architecture_model.py" init <model-dir> --subject <name> --source <repo>
```

Keep generated `.architecture-model/` output in the target repository or user-selected workspace, not inside the skill directory.

## Required result

Create a model directory containing:

```text
.architecture-model/
  subject.json
  decisions.json
  scans/<source-id>.json
  canonical.json
```

- Agents author one bounded scan JSON document per repository.
- `decisions.json` preserves explicit identity, ownership, and boundary decisions.
- `canonical.json` is generated, never hand-edited.
- The generated canonical model is the durable working memory read before scanning the next repository.

Use the bundled standard-library tool:

```bash
python "$SKILL_DIR/scripts/architecture_model.py" init <model-dir> --subject <name> --source <repo> [--source <repo> ...]
python "$SKILL_DIR/scripts/architecture_model.py" validate-scan <model-dir>/scans/<source-id>.json
python "$SKILL_DIR/scripts/architecture_model.py" compile <model-dir>
python "$SKILL_DIR/scripts/architecture_model.py" validate <model-dir>
```

Use [assets/scan-template.json](assets/scan-template.json) as the agent-authoring template; replace its example values rather than inventing a different shape. A non-zero result is a hard failure. Never bypass validation or edit `canonical.json` to make it pass.

## Scope authority

The user's named subject selects the scope without determining its architecture type. Record its name, description, aliases, supplied roots, and exclusions in `subject.json`. Do not assume the subject is a DDD domain, bounded context, or C4 Software System. Do not search only for subject-name words; broadly inventory every supplied repository so wiring with unrelated terminology is not missed.

Repository structure is evidence, not architecture truth. One repository can contain several runtime units, and one runtime can be assembled from several repositories. A shared package is not a running service. A Docker image is deployment evidence, not a C4 classification.

## Per-repository transaction

For each source, complete this bounded cycle before opening the next source:

1. Read repository instructions.
2. Identify the exact repository, revision, branch, and scan coverage.
3. Read the current `subject.json`, `decisions.json`, and generated `canonical.json`.
4. Inventory solutions/workspaces, build outputs, executable entry points, deployment descriptors, configuration, generated code, tests, and documentation.
5. Discover all runtime units, stores, channels, shared libraries, inbound interfaces, outbound dependencies, and architecturally meaningful operations.
6. Write or replace only `scans/<source-id>.json`.
7. Validate that scan.
8. Compile and validate the canonical model.
9. Review newly resolved identities, contract conflicts, candidate external targets, and gaps.
10. Save the checkpoint before scanning another repository.

Do not defer reconciliation until every repository has been scanned. Do not copy findings from one scan into another. Re-scanning a source replaces its repository-local observations and then regenerates the canonical model.

## Record facts, not C4 guesses

Repository scan files use discovery kinds such as `runtime`, `store`, `channel`, `library`, `external`, and `person`. Runtime subtypes can include API, worker, MFE, scheduler, function, browser application, or another observed form. These are factual discovery classifications, not C4 types.

For each unit, capture:

- name, responsibility, discovery kind/subtype, and technology;
- deployment or logical identity signals;
- inbound interfaces;
- outbound dependencies;
- ownership only when evidenced;
- exact source anchors and observations.

For every inbound interface, capture what is observed and architecturally useful:

- HTTP/gRPC method, path/service, and API version;
- event/message channel, subscription or consumer group, and event version;
- scheduled-job trigger;
- request, response, event, or command contract identity;
- schema location or fingerprint and only key correlation/routing/security fields;
- authentication, routing rules, and filters when they affect callers or architectural paths.

For every outbound dependency, capture:

- source and intended target identity;
- dependency kind and explicit purpose;
- technology/protocol;
- API, event, or contract version;
- destination route, service, store/schema, queue/topic, package, or remote identity;
- rules that affect whether or where the dependency is invoked;
- evidence.

`from` and `to` in the generated relationship define runtime direction. Do not replace direction with a vague `dependsOn`. Keep compile/package dependencies distinct from runtime requests, message flow, data access, and UI composition.

## Right level of detail

Enumerate every public inbound interface and every outbound architectural dependency so relationship coverage can be evaluated. Do not copy full payloads or reproduce ordinary implementation detail.

Capture a payload schema reference, version, fingerprint, and key fields when useful for matching or architecture. Do not copy every DTO property.

Capture rules that change:

- authorization or accepted callers;
- routing, partitioning, or filtering;
- whether a downstream call/message occurs;
- ownership or state progression;
- retry, outbox, idempotency, or compensation behavior when architecturally significant.

Do not capture every field validator, object mapping, logging statement, MediatR pipeline behavior, helper method, or framework call.

MediatR, CQS, MassTransit, MobX, and design systems are mechanisms or shared artifacts unless evidence establishes a separately running boundary. Use framework-specific wiring to trace operations, not to manufacture nodes.

## Identity and reconciliation

Use strong identity signals before names:

1. explicit confirmed override in `decisions.json`;
2. deployment/runtime identity;
3. exact database/catalog/schema, bucket, index, queue, or topic identity;
4. exact configured service address and compatible interface;
5. compatible contract name, version, and fingerprint;
6. generated client/server origin or integration test evidence;
7. package identity;
8. names and textual similarity only as candidate evidence.

Never merge incompatible API or event versions silently. Never infer an inbound caller merely because an endpoint exists. The compiler derives callers from outbound findings and matching inbound interfaces. Leave unmatched targets as candidates or gaps.

A shared physical database host and a shared logical data store are different facts. Distinguish server/cluster, database/catalog, schema, index, and migration ownership. Several services using one logical store produce several directional relationships to one canonical store identity; they do not produce duplicate databases.

Use `decisions.json` for explicit identity/target overrides and candidate/confirmed/rejected system boundaries. Preserve confirmed decisions across rescans. Do not encode uncertain guesses as decisions.

## Operations and flows

Record one operation for a concrete inbound interface when it adds architectural value. Use a short ordered step list. A step either executes at a local unit or uses one of the owner's outbound dependencies. Add `next` only for an evidenced branch, parallel continuation, failure, or retry that materially changes the architectural story.

Do not build a detailed causal/event-sourcing model. Keep local implementation steps only when they explain a meaningful rule or boundary crossing. The compiler maps local dependency references to canonical relationships; downstream tools can turn selected flows into Dynamic diagrams.

## Fail-closed accuracy

Use certainty values only in the generated model: `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`. Repository scan documents contain observations and explicit gaps; deterministic reconciliation determines corroboration.

Record a gap when configuration is injected externally, a target cannot be resolved, a caller is absent from supplied roots, generated code hides an origin, reflection prevents tracing, or ownership cannot be established. Record concrete searches and architectural impact. Unknown is preferable to a polished guess.

## Completion gate

Do not report gathering complete until:

- [ ] Every supplied source has one validated scan with an exact revision and coverage status.
- [ ] Every detected executable/runtime and logical store is represented or explicitly excluded.
- [ ] Every discovered inbound interface is inventoried with version/contract details when observed.
- [ ] Every outbound architectural dependency has direction, purpose, technology, target identity, and evidence.
- [ ] Every operation selected for Dynamic/Component analysis maps to an inbound interface and evidenced steps; other public interfaces remain inventoried without forced flow detail.
- [ ] Shared packages, generated clients, contracts, migrations, and design systems are not mistaken for runtimes.
- [ ] API/event versions and incompatible contracts have not been silently merged.
- [ ] Database server, logical database/schema, and data access are distinguished.
- [ ] Candidate callers and targets remain gaps rather than fabricated relationships.
- [ ] Compilation and canonical validation pass after the final scan.
- [ ] Recompilation is deterministic and does not depend on repository scan order.

Run the executable evaluation suite before changing or completing this skill:

```bash
python -m unittest discover -s "$SKILL_DIR/tests" -p "test_*.py" -v
```

The tests are deterministic tooling checks. Apply [evals/reasoning-cases.md](evals/reasoning-cases.md) to agent behavior; matching a fail condition is a regression even when the executable tests pass.
