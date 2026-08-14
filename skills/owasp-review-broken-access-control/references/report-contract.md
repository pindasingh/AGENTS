# Canonical A01 assessment JSON contract

## Assessment versus finding

An assessment records coverage whether or not vulnerabilities are found. A finding requires a supported unauthorized path.

Use this decision rule:

1. Name the intended access policy.
2. Name an actor outside that policy.
3. Trace how that actor reaches or influences the protected action/resource.
4. Identify the missing, incorrect, bypassable, or stale trusted decision.
5. Establish security impact.

If any element is unknown, use `likely`, `needs-validation`, or a coverage gap according to the remaining evidence. Do not convert checklist nonconformance directly into a vulnerability.

## Canonical output

Use `assets/assessment-template.json` for the assessment, `assets/access-path-template.json` for each end-to-end path, and `assets/finding-template.json` for each issue. Populate fragments before insertion because placeholder tiers, evidence, affected implementation, and cross-references are intentionally incomplete. The completed JSON is the skill's only output artifact; Markdown, HTML, SARIF, and other presentations are downstream concerns.

Required top-level sections are:

- `schemaVersion`
- `scopeSelection`
- `assessment`
- `authorizationModel`
- `coverage`
- `findings`
- `gaps`

`assessment.mode` is `triage`, `focused`, or `comprehensive`. Triage uses only scope selection and assessment metadata. Focused mode includes only selected paths and applicable coverage records. Comprehensive mode includes all 19 coverage records.

Schema version `1.4` adds mode and repository-selection data to the existing end-to-end authorization and evidence-gap contract. Every finding records its primary category and component, affected implementation, linked access paths, and concise supporting pseudocode. The harness must check structural and cross-reference invariants using the self-check in `SKILL.md`; no executable validator is required. Unknown extra fields are permitted so future A02–A10 profiles can extend the format, but existing meanings must not be changed.

## Access-path records

Each distinct protected entry/enforcement path records:

- stable `id` and exact `entryPoint`;
- `methodsOrOperations`, including protocol operation, message, job, or GraphQL operation type where HTTP verbs are insufficient;
- primary/mobile/partner/staging/support/service/async or other `channel`;
- expected `authentication` state and eligible `actors`;
- protected `resource` and `actions`;
- caller-controlled `inputVectors`, including headers, cookies, keys, claims, duplicate parameters, tenant/resource selectors, and method overrides;
- `traceStatus`: `complete`, `partial`, or `blocked`;
- reciprocal `gapIds` for partial or blocked paths;
- ordered `tiers` from entry and identity establishment through policy, protected operation, data, downstream, and asynchronous effects;
- exact path `evidence`.

Each tier records `name`, generic `type`, concrete `component`, `entryIdentity`, `exitIdentity`, `credentials`, `policies`, `resourceContext`, observed `decision`, `status`, and exact evidence. Tier types are architecture-neutral: identity, client, edge, gateway, BFF, application, policy, domain, data, cache, downstream, async, external, or other. Verified tiers require evidence. A complete path contains only verified tiers and no gap. A partial path records a user-accepted exclusion or confirmed unavailable artifact. A blocked path references an awaiting-user gap.

Once any coverage branch is assessed, at least one access path is required. Split paths when methods, versions, channels, identities, credentials, parsers, policy chains, direct backends, or downstream effects differ materially. Unavailable alternate channels and deployment tiers belong in gaps rather than being silently omitted.

## Evidence anchors

Evidence objects contain:

- `kind`: `source`, `config`, `test`, `request`, `response`, `runtime`, `documentation`, or `other`;
- `location`: repository-relative path and line/symbol, URL/route, configuration key, test name, or redacted artifact identifier;
- `observation`: what the evidence establishes;
- `revision`: commit, artifact version, environment build, or `unknown`.

Prefer exact anchors such as `src/Invoices/GetInvoice.cs:42-58 (Handle)` over broad locations such as `backend`. Never put credentials, complete tokens, personal data, or unnecessary record contents in evidence.

Keep evidence compact: normally one to three strongest anchors per access path, coverage branch, or finding. Reuse the exact location and a short observation instead of copying the whole source-to-impact narrative into every branch. Completeness comes from path and branch coverage, not repeated prose.

## Coverage statuses

In comprehensive mode every required branch appears exactly once. Focused mode includes each applicable selected branch once and does not add irrelevant branches merely to mark them unassessed. Triage has no coverage records.

Use:

- `finding` requires at least one referenced finding with status `confirmed` or `likely`;
- `reviewed-no-finding` requires evidence and a rationale describing what was inspected;
- `not-applicable` requires a concrete rationale;
- `not-assessed` requires a rationale and should normally correspond to a gap.

A branch can reference the same root-cause finding as another branch. This is coverage traceability, not duplicate reporting.

## Finding statuses and confidence

- `confirmed`: complete source proof, supplied reliable execution evidence, or authorized safe reproduction demonstrates the unauthorized path.
- `likely`: a credible unauthorized path is supported, but a material runtime/configuration fact remains unresolved.
- `needs-validation`: a signal warrants a named verification step but is not yet a vulnerability claim.

Use confidence `high`, `medium`, or `low` independently of severity. `needs-validation` cannot have `critical` or `high` severity because exploitability has not been established.

## Severity

Use `critical`, `high`, `medium`, `low`, or `informational`. Explain severity in terms of:

- privilege required and attacker reachability;
- cross-user, cross-tenant, administrative, or system-wide scope;
- confidentiality, integrity, availability, safety, financial, or business impact;
- interaction, prerequisites, repeatability, and automation;
- sensitivity and quantity of affected resources;
- compensating controls and detection/recovery.

A01's #1 ranking does not make each issue critical. Do not invent a CVSS vector; provide one only if the user asks and sufficient environmental inputs exist.

## Mapping rules

Every finding maps to `A01:2025` and at least one coverage branch. Add only supported mappings:

- current ASVS: `ASVS 5.0.0-8.2.2`
- legacy ASVS when requested: `ASVS 4.0.3-4.2.1`
- WSTG: `WSTG v4.2-ATHZ-04`
- API: `API1:2023`
- CWE: `CWE-639`

Prefer the most specific CWE. Broad CWE-284/285/862/863 can supplement but should not hide a specific weakness. Explain surprising mappings in finding notes.

A finding may identify an adjacent OWASP category, but this skill must state that A02–A10 were not comprehensively assessed.

## Finding organization and concise issue blocks

Assign every finding exactly one human-readable primary `category` and `component`. Use the authorization boundary as the category, for example object-level authorization, function-level authorization, property-level authorization, tenant isolation, workflow/business limits, route/method bypass, or browser trust boundaries. Use the service, API, deployable unit, or cohesive code module that owns the fix as the component. Record related components inside the affected implementation or evidence rather than duplicating the finding.

Each finding records:

- `classification`: the precise issue type, such as horizontal privilege escalation or missing function-level authorization;
- `affectedImplementation.controllers`, `classes`, `methods`, `endpoints`, and `filesOrArtifacts`; arrays may be empty when genuinely inapplicable, but at least one location must be identified overall;
- `expectedAccessRule`, `exercise`, `failureProof`, `impact`, and `remediation` objects, each containing a short plain-language `summary`, a presentation language, and `pseudocode`;
- one or more known `accessPathIds` containing the end-to-end identity, credential, policy, resource, and decision trace;
- structured allowed and denied `regressionTests`;
- exact evidence anchors, mappings, attack path, severity rationale, and limitations.

Populate structured fields directly from evidence. Do not invent pseudocode from source files or replace exact evidence anchors with generated prose.

Keep each pseudocode block focused: normally three to eight lines and never more than twelve non-blank lines or 1,600 characters. Distill only the policy, caller-controlled flow, safe request shape, impact, or trusted-layer fix needed for that section. Do not paste full methods, classes, payloads, responses, stack traces, or repeated source excerpts. Clearly treat these blocks as normalized pseudocode; exact source truth remains in the evidence anchors.

The `exercise` block is presented as **Unauthorized scenario**. Make it self-contained: name the unauthorized actor and starting privilege, protected resource, attempted action, decisive caller-controlled input or context, expected denial, and evidenced result. Prefer the actual interface shape when one exists. For libraries, policy engines, and synthetic corpora, express the business scenario and relevant field values before naming an internal method or fixture. Do not use opaque prose such as “exercise the denied probe” or rely on unexplained case IDs. Say `code result` or `static result` for source proof and reserve `observed` for supplied or authorized execution evidence.

## Attack path

Write ordered, reproducible, minimally harmful steps. Static paths can use code-flow steps, for example:

1. Authenticated user supplies `invoiceId` in `GET /invoices/{invoiceId}`.
2. Route requires authentication but no invoice permission.
3. Handler loads `Invoices.Find(invoiceId)` without owner or tenant scope.
4. Serializer returns the record to the caller.

State which step is inferred. Do not include weaponized automation, real victim identifiers, secrets, or destructive production actions.

## Remediation

Remediation must address policy and trusted enforcement:

- define the subject/resource/action/context rule;
- enforce it at a trusted service/domain/data boundary on every path;
- constrain data retrieval/mutation to authorized scope where possible;
- deny safely and prevent sensitive response/state changes;
- centralize reusable policy without assuming middleware alone solves object access;
- revoke stale authority when policy inputs change;
- add observability and tests.

Avoid vague advice such as “add authorization,” “sanitize the ID,” or “use UUIDs.”

## Regression tests

Each confirmed or likely finding needs at least two tests:

- one allowed case for the intended actor/context;
- one denied case for the unauthorized actor/context.

Add peer/non-owner, cross-tenant, lower-role, forbidden-field, alternate-method/path, stale-token, or business-limit cases as relevant. Assert response and side effects: no sensitive body, no mutation, no queued work, and no downstream action.

## Gaps

A gap records a fact needed for confidence or coverage, such as external gateway policy, inherited/generated/deployed configuration, unavailable identity-provider or downstream behavior, missing code/environment, or inability to test safely.

Before recording a material gap, search available repositories, references, deployment files, and tests. Each gap names:

- why it matters;
- non-empty `searched`, `requestedArtifacts`, and `blockedConclusions` lists;
- affected access-path and coverage IDs with reciprocal path references;
- `requestStatus`: `awaiting-user`, `excluded-by-user`, or `confirmed-unavailable`;
- exact `userDecision` and safe next step.

`awaiting-user` means the reviewer must ask and wait; affected paths remain blocked, so the assessment must not be marked final. An explicitly requested interim checkpoint remains visibly blocked. If the user supplies the artifact, inspect it and remove or update the gap. `excluded-by-user` or `confirmed-unavailable` permits a partial path but never complete trace status. Do not hide limitations while marking branches `reviewed-no-finding`, and do not treat silence as permission to exclude.

## Assessment outcome invariants

When the selected mode includes security conclusions, record deterministic `assessment.securityOutcome` and independent `assessment.traceCompleteness` values:

- security outcome is `FAIL` when any finding is `confirmed` or `likely`;
- security outcome is `REVIEW` when no supported finding exists but a finding needs validation or an assessed branch is `not-assessed`;
- security outcome is `PASS` when there is no supported finding, no finding needs validation, and no assessed branch is `not-assessed`;
- trace completeness is `BLOCKED` when any path is blocked or any gap awaits user direction;
- trace completeness is `PARTIAL` when no path is blocked but a path is partial or an assessed branch remains not assessed after explicit direction;
- trace completeness is `COMPLETE` when every recorded path is complete and no assessed branch is not assessed.

Triage uses `NOT_ASSESSED` for both values. A `FAIL` assessment can be partial or blocked; findings do not hide missing tiers. An unqualified `PASS` requires complete tracing. These values summarize A01 only and are not automatically a release gate, ASVS certification, or statement about A02–A10.
