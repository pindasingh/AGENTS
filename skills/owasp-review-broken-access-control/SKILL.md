---
name: owasp-review-broken-access-control
description: Finds and documents OWASP A01:2025 Broken Access Control vulnerabilities in application source, configuration, APIs, tests, and explicitly authorized running systems. Use whenever a user requests an OWASP access-control review, BAC assessment, authorization audit, IDOR/BOLA/BFLA/BOPLA or privilege-escalation analysis, tenant-isolation review, force-browsing check, or evidence-backed security findings—even if they only say "check permissions" or "can one user access another user's data?"
compatibility: Requires only harness-native read and output capabilities. Do not depend on Python, shell scripts, executable validators/renderers, package installation, or external scanners. Live requests require explicit user authorization and scope.
---

# Review OWASP Broken Access Control

Review OWASP A01:2025 only. Do not imply coverage of A02–A10. Treat authentication as identity evidence, not proof that the caller may perform an action on a resource.

## 1. Run eligibility triage before deep review

Do not load long references or recursively explore source yet. For each repository or deployable package, inspect only enough structure to identify its role:

1. repository instructions and root listing;
2. root README/architecture summary and workspace/service catalogue;
3. package/build manifests and deployment/runtime declarations;
4. top-level application directories and named entry points;
5. one small representative route, client, policy, or entry-point file only if still ambiguous.

Do not begin with repository-wide searches, tests, lockfiles, generated output, dependencies, assets, build artifacts, or an exhaustive file listing.

Classify each subject:

- **candidate** — contains/configures a reachable server, API, BFF, gateway, server action, resolver/RPC service, worker/consumer, policy engine, protected data/file access, identity delegation, or infrastructure permission boundary;
- **supporting** — exposes routes/contracts or calls a candidate but does not make the trusted decision, such as a client-only MFE, mobile client, generated SDK, or DTO package;
- **excluded** — has no credible protected resource, protected action, or trusted A01 enforcement surface;
- **undetermined** — inspect one additional targeted artifact or ask one precise question instead of scanning.

Usually exclude intentionally public static marketing/docs sites, presentational component libraries, client-only SPAs/MFEs without BFF/serverless/edge code, generated clients, undeployed samples, and unrelated tooling. A client route guard or hidden button is not trusted enforcement; retain only route/input handoff evidence for the owning backend.

Do not exclude merely because something is not an API: server-rendered actions, workers, gateways, policy libraries, object stores, and message consumers can be eligible. Do not activate API, GraphQL, browser, APIM, serverless, storage, or session checks without evidence that the surface exists.

For multiple repositories, output a compact selection table: subject, observed role, classification, evidence, applicable A01 surface, decision. Deep-review candidates only; consult supporting repositories only along selected paths. Excluded siblings are not evidence gaps. If all subjects are excluded, stop after triage and suggest the concrete backend/gateway/policy/worker/data repository needed next.

## 2. Choose the smallest review mode

Choose once after triage and state it.

### Triage

Use when the user asks what is eligible, no candidate remains, or scope is still undetermined. Output only the selection decision and next target. Do not build findings, a 19-branch matrix, assessment JSON, or full report.

### Focused — default

Use for ordinary requests to check permissions, review a repository, inspect an endpoint/feature, investigate IDOR/BOLA, or assess a bounded authorization concern. Review only selected sensitive operations and applicable concern areas. Do not create a 19-branch matrix or `assessment.json` unless the user explicitly asks for comprehensive coverage or structured assessment output.

Produce a concise Markdown report by default. HTML is generated only when explicitly requested.

### Comprehensive — explicit only

Use only when the user explicitly asks for a **full/comprehensive A01 assessment**, **all 19 branches**, **complete A01 coverage**, or the structured **assessment JSON/report contract**. Comprehensive mode produces `assessment.json` plus a Markdown report by default; produce standalone HTML only when explicitly requested.

Do not silently upgrade focused work to comprehensive because a candidate has many files or tiers.

## 3. Load references progressively

Before eligibility is decided, load none of the references below. In focused mode, load only concern files supported by selected-path evidence:

| Observed concern | Load |
|---|---|
| records, functions, fields, roles, tenants, methods, GraphQL/RPC | [coverage/object-function-tenant.md](references/coverage/object-function-tenant.md) |
| protected browser cookies/cross-origin behavior | [coverage/browser-cors-csrf.md](references/coverage/browser-cors-csrf.md) |
| sessions, tokens, logout, stale roles/ownership, signed links | [coverage/sessions-revocation.md](references/coverage/sessions-revocation.md) |
| deployed files, downloads, object stores, CDNs, caches, backups | [coverage/files-object-storage.md](references/coverage/files-object-storage.md) |
| gateways, APIM, BFFs, policy engines, services, delegation, events | [coverage/gateways-delegation.md](references/coverage/gateways-delegation.md) |
| approvals, state transitions, one-time limits, replay, races, quotas | [coverage/business-workflows.md](references/coverage/business-workflows.md) |

Load [end-to-end-authorization-tracing.md](references/end-to-end-authorization-tracing.md) only when a selected path crosses material tiers/identity transformations or needs an evidence checkpoint. Load [asvs-wstg-cheatsheet-crosswalk.md](references/asvs-wstg-cheatsheet-crosswalk.md) only when standards mappings are requested. Load [wstg-v42-a01-selection.md](references/wstg-v42-a01-selection.md) only for detailed applicable web test procedures. Load [owasp-a01-source-of-truth.md](references/owasp-a01-source-of-truth.md) only for comprehensive coverage or source/mapping verification.

In comprehensive mode, follow [coverage/comprehensive.md](references/coverage/comprehensive.md), then load [report-contract.md](references/report-contract.md) and the raw templates it names.

## 4. Review selected paths

For each selected operation:

1. State the policy as actor–resource–action–context and identify an actor outside it.
2. Trace reachable entry point → identity → policy decisions → selected resource/fields → protected action → side effects.
3. Record caller-controlled identifiers, tenant/role/state/field inputs and every material identity transition.
4. Search for controls that can close the apparent path: fallback/global policy, generated configuration, service/domain checks, scoped queries, deployment policy, and downstream enforcement.
5. Follow cross-repository references only when plausibly part of that selected path; do not fan out through every sibling or dependency.
6. Reuse the smallest exact evidence set: file/line/symbol, configuration key, test, or redacted supplied runtime artifact.

A finding requires an intended policy, an unauthorized actor, a reachable path, a missing/incorrect trusted decision, and impact. Use:

- `confirmed` — complete static proof, supplied reliable execution evidence, or authorized safe reproduction;
- `likely` — a credible path with one material runtime/configuration fact unresolved;
- `needs-validation` — a security-relevant signal without enough evidence for a vulnerability claim.

A search result or missing local annotation alone is not a finding. UI controls, valid tokens/keys, trusted networks, coarse roles/scopes, UUIDs, and CORS alone are not object/function authorization.

After targeted discovery, pause only for missing evidence that can materially change a selected-path conclusion. State what is missing, why it matters, what was searched, affected conclusions, and ways to continue. Await user direction rather than treating unknown behavior as permissive or protective.

## 5. Safety and authority

Static review is the default. Before network requests, data changes, test identities, bypass attempts, or live-system exercise, confirm authorization and record targets, identities, methods, time window, data constraints, and stop conditions.

Without confirmation, inspect supplied source/configuration/tests/evidence and propose safe verification steps only. Never imply unperformed execution, access another person's real data, or use destructive production checks. Stop on ambiguous ownership, availability/integrity risk, or unexpected sensitive data; retain minimal redacted evidence.

## 6. Output for the selected mode

### Focused report

Write concise Markdown unless HTML was explicitly requested:

1. mode and selected scope/exclusions;
2. actor–resource–action–context rule;
3. selected paths and trusted enforcement points;
4. findings grouped by category/component, each with status, exact evidence, unauthorized path, impact, focused mappings when requested, trusted-layer remediation, and allowed/denied regression tests;
5. needs-validation items and material gaps;
6. concise conclusion and next steps.

Do not duplicate full source or evidence narratives. Consolidate only instances sharing one root cause, policy, enforcement point, and fix.

### Comprehensive artifacts

Use [assets/assessment-template.json](assets/assessment-template.json), [assets/access-path-template.json](assets/access-path-template.json), and [assets/finding-template.json](assets/finding-template.json). Apply [report-contract.md](references/report-contract.md), self-check all IDs/statuses/cross-references, and author matching JSON and Markdown directly through the harness. HTML remains opt-in.

This skill is raw guidance and data. Do not run or create helper scripts, invoke Python/shell tooling, install packages, or expect an executable validator/renderer. Keep artifacts outside the installed skill directory. If the harness cannot create files, return equivalent content through its supported artifact/response channel and state the limitation.
