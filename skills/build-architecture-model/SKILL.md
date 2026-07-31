---
name: build-architecture-model
description: Scans one or many code repositories incrementally and builds an evidence-backed reconciled architecture model of runtimes, stores, interfaces, contracts, dependencies, operations, conflicts, and gaps. Use for system discovery, cross-repository dependency analysis, architecture inventories, or architecture impact analysis.
---

# Build Architecture Model

Discover the architecture of a user-named subject one repository at a time. Produce repository-local findings first, then reconcile them into shared working memory after every repository.

Before scanning, read [references/model-spec.md](references/model-spec.md) completely. Read the applicable framework playbooks under `references/` after detecting the repository technologies.

## Working files

Use the bundled JSON templates as starting points and replace every example value. Author and reconcile the model artifacts directly; there is no separate generation step. Keep working output in the target repository or user-selected workspace, never in the installed skill directory.

## Required result

Create:

```text
.architecture-model/
  subject.json
  decisions.json
  scans/<source-id>.json
  model.json
```

Start from these reusable templates:

- [assets/subject-template.json](assets/subject-template.json)
- [assets/decisions-template.json](assets/decisions-template.json)
- [assets/scan-template.json](assets/scan-template.json)
- [assets/model-template.json](assets/model-template.json)

Agents author all four artifact types directly. The output is named `model.json` because the containing `.architecture-model/` directory already supplies its context and the file represents the current reconciled model, not a privileged or permanently final truth. Rebuild its affected entries from scans and confirmed decisions rather than inventing facts. Never use it as a second evidence ledger, and never alter a scan merely to make reconciliation look clean.

## Scope and per-repository transaction

The user's named subject selects scope without determining its architecture type. Record its name, description, aliases, supplied roots, and exclusions. Broadly inventory every supplied repository; do not search only for subject-name words.

For each source, finish this cycle before opening the next:

1. Read repository instructions and the current subject, decisions, scans, and reconciled model.
2. Record the exact repository, revision, branch, included paths, exclusions, and limitations.
3. Inventory workspaces, build outputs, executable entry points, deployments, configuration, generated code, tests, and documentation.
4. Discover runtimes, stores, channels, libraries, inbound interfaces, outbound dependencies, operations, and evidence gaps.
5. Write or replace only `scans/<source-id>.json` from the scan template.
6. Self-check the scan contract below.
7. Reconcile identities, interfaces, relationships, flows, conflicts, and gaps into `model.json` in stable ID order.
8. Self-check the whole model and save the checkpoint before scanning another repository.

Re-scanning replaces that source's observations and requires removing or updating model claims that no longer have support.

## Record facts, not presentation choices

Use discovery kinds `runtime`, `store`, `channel`, `library`, `external`, and `person`. Runtime subtypes such as API, worker, MFE, scheduler, function, or browser application describe observed behavior. A repository can contain several runtimes; a runtime can span repositories; a library is not a running service; a Docker image is deployment evidence, not an architecture boundary.

For every unit, interface, outbound dependency, and meaningful operation step, record the fields defined by the model specification and exact evidence anchors. Inventory every public inbound interface and architectural outbound dependency, but omit ordinary implementation noise. Preserve direction with `from` and `to`; distinguish requests, events, messages, data access, UI loading, and compile/package dependencies.

## Identity and reconciliation

Use identity signals in this order:

1. confirmed override in `decisions.json`;
2. deployment/runtime identity;
3. exact store or channel identity;
4. exact configured address plus compatible interface;
5. compatible contract name, version, and fingerprint;
6. generated client/server origin or integration evidence;
7. package identity;
8. names only as candidate evidence.

Never silently merge incompatible versions. Never infer a caller merely because an endpoint exists. Match an outbound observation to an inbound interface only when destination and contract evidence are compatible; otherwise preserve a candidate, conflict, or gap. Reuse one model node for one supported identity and attach every supporting source finding. Keep database server, logical database/schema, and access relationship distinct.

Certainty is one of `observed`, `corroborated`, `inferred`, `conflicting`, or `unknown`. Explain inferred matches and conflicts. Unknown is preferable to a polished guess. Use `decisions.json` only for explicit identity, target, ownership, or system-boundary decisions; preserve confirmed decisions across rescans.

## Operations

Record an operation only when a concrete inbound interface has architectural value. Keep steps short and ordered. A step executes at a local unit or uses an outbound dependency. Add branching only when evidenced and architecturally meaningful. Do not turn every handler or method into a flow.

## Completion check

Before reporting completion, review each JSON artifact and check all of the following:

- [ ] Every file is one parseable JSON object with `schemaVersion: 1`; every copied placeholder was replaced or intentionally removed.
- [ ] Subject sources and scan source IDs are unique; each supplied source has one scan at the intended revision and an honest `complete`, `partial`, or `blocked` status.
- [ ] Every unit, interface, dependency, and operation step has a repository-relative evidence path and concrete observation.
- [ ] Local `unitId`, operation owner/trigger/`uses`, decision override, model source-finding, and relationship endpoint references resolve.
- [ ] Every runtime and logical store is represented or explicitly excluded; shared packages and generated clients are not mistaken for runtimes.
- [ ] Every relationship has `from`, `to`, kind, purpose, technology, certainty, supporting findings, and evidence.
- [ ] Versions and incompatible contracts are not silently merged; unresolved callers, targets, ownership, and external configuration remain gaps or conflicts.
- [ ] Model IDs are stable and collections are ordered lexically by ID so a repeat review produces a reviewable diff independent of scan order.
- [ ] Every model claim is supported by a scan or confirmed decision, and stale claims from replaced scans were removed.
- [ ] `model.json` contains observed architecture facts rather than presentation-specific classifications.

Apply [evals/reasoning-cases.md](evals/reasoning-cases.md) as a behavior checklist. Matching a fail condition is a regression.
