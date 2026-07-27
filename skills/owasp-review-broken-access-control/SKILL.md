---
name: owasp-review-broken-access-control
description: Finds and documents OWASP A01:2025 Broken Access Control vulnerabilities in application source, configuration, APIs, tests, and explicitly authorized running systems. Use whenever a user requests an OWASP access-control review, BAC assessment, authorization audit, IDOR/BOLA/BFLA/BOPLA or privilege-escalation analysis, tenant-isolation review, force-browsing check, or evidence-backed security findings—even if they only say "check permissions" or "can one user access another user's data?"
compatibility: Requires read access to the assessment subject and Python 3 for the bundled dependency-free validator and Markdown/standalone-HTML report renderer. Live requests require explicit user authorization and scope; no package installation or external scanner is required.
---

# Review OWASP Broken Access Control

Find and document evidence-backed access-control weaknesses using OWASP A01:2025 as the risk taxonomy. Use ASVS 5.0.0 V8 for current verifiable requirements, ASVS 4.0.3 V4 when a legacy cross-reference is requested, WSTG 4.2 authorization tests for reproducible test design, the Authorization Cheat Sheet for implementation guidance, and the API Security Top 10:2023 when APIs are present.

This version covers A01 only. Do not imply that it assesses OWASP A02–A10.

## Scope eligibility gate

Run this gate **before loading the long references or recursively exploring source**. A01 can apply to many architectures, but that does not make every repository an authorization enforcement target. The purpose of triage is to spend review effort only where the repository can expose a protected resource, perform a protected action, or make/mediate a trusted authorization decision.

### Bounded structure-first pass

For each supplied repository or workspace member, inspect only enough structure to identify its role:

1. repository instructions and the root directory listing;
2. root README/architecture summary and workspace, solution, or service catalogue;
3. package/build manifests and deployment/runtime declarations;
4. top-level application directories and named entry points;
5. at most a small representative route, client, policy, or entry-point file when the role remains ambiguous.

Do not start with recursive source reads, repository-wide content searches, tests, lockfiles, generated output, vendored dependencies, assets, or build artifacts. Do not enumerate every file merely because it is available. Expand discovery only inside a selected candidate and only along evidence-backed authorization paths.

Classify every repository or independently deployable package:

- **candidate** — contains or configures a reachable server, API, BFF, gateway/ingress policy, server-side web action, resolver/RPC service, worker/consumer, authorization library/policy engine, protected file/object/data access, identity delegation, or infrastructure permission boundary;
- **supporting evidence** — exposes routes/contracts or calls a candidate but does not itself make the trusted decision, such as a client-only MFE, mobile client, generated SDK, or shared DTO package; inspect only the files needed to identify candidate targets and caller-controlled inputs;
- **excluded** — has no credible protected resource, protected action, or trusted enforcement surface for A01 in the requested scope;
- **undetermined** — structure gives conflicting signals; inspect one additional targeted artifact or ask one precise question rather than scanning the repository.

Common exclusions from deep A01 review include an intentionally public static marketing/docs site with no accounts or private state, a presentational component/design-token library, a client-only SPA/MFE with no BFF/serverless/edge runtime, generated clients, sample/demo content outside deployment, and unrelated tooling. These repositories may have other security concerns, but that does not make them eligible for this A01 skill. A client route guard or hidden admin button is not trusted enforcement: record the referenced backend as a candidate handoff when known, but do not deep-scan the MFE or report the client check alone as a BAC vulnerability.

Do not exclude a repository merely because it is “not an API.” Server-rendered actions, gateways, workers, policy libraries, object stores, deployment permissions, and message consumers can enforce or bypass authorization. Conversely, do not activate API, GraphQL, browser, APIM, serverless, or other profile-specific checks without structural evidence that the profile exists.

For a multi-repository request, return a short selection table with repository/package, observed role, classification, evidence, applicable A01 surfaces, and decision. Deep-review candidates only. Consult supporting repositories only when a selected path requires them. Do not follow every sibling or dependency, and do not turn excluded repositories into material-evidence gaps. If every subject is excluded, stop after the triage result and suggest the concrete backend, gateway, policy, worker, or data repository that would be useful next; do not generate a full assessment, 19-branch matrix, or vulnerability report.

### Reference loading after selection

Once at least one candidate is selected, read these core files completely:

1. [references/owasp-a01-source-of-truth.md](references/owasp-a01-source-of-truth.md) — normative A01 source and mapped CWEs.
2. [references/end-to-end-authorization-tracing.md](references/end-to-end-authorization-tracing.md) — tier tracing and evidence acquisition for selected paths.
3. [references/review-playbook.md](references/review-playbook.md) — required coverage branches and evidence heuristics.
4. [references/report-contract.md](references/report-contract.md) — finding threshold, statuses, severity, and output contract.

Load the remaining guidance only when the selected surface needs it:

- [references/asvs-wstg-cheatsheet-crosswalk.md](references/asvs-wstg-cheatsheet-crosswalk.md) when assigning standards mappings;
- [references/wstg-v42-a01-selection.md](references/wstg-v42-a01-selection.md) for applicable web/API/browser procedures, not for a non-web policy library or worker by default;
- only the relevant sections of [references/architecture-profiles.md](references/architecture-profiles.md) for architectures actually discovered (for example APIM, BFF, GraphQL, microservices, serverless/event-driven, or object storage).

## Harness portability

Resolve the absolute path to this skill directory before reading assets or running scripts; do not assume the shell starts here.

```bash
SKILL_DIR="<absolute path to owasp-review-broken-access-control>"
python "$SKILL_DIR/scripts/bac_assessment.py" validate <assessment.json>
python "$SKILL_DIR/scripts/bac_assessment.py" render <assessment.json> --format html --output <report.html>
python "$SKILL_DIR/scripts/bac_assessment.py" render <assessment.json> --format markdown --output <report.md>
```

Use [assets/assessment-template.json](assets/assessment-template.json) as the assessment starting point, [assets/access-path-template.json](assets/access-path-template.json) for each end-to-end path, and [assets/finding-template.json](assets/finding-template.json) for each issue record. The fragments are intentionally incomplete until their tiers, affected implementation, evidence, and cross-references are replaced. The CLI delegates presentation to the dependency-free [scripts/report_renderers.py](scripts/report_renderers.py); do not call that internal module directly. Keep generated assessments and reports in the reviewed project or a user-selected workspace, never in the installed skill directory.

## Safety and authority

Static review of user-provided repositories is the default. Before making network requests, changing data, creating test identities, bypassing controls, or exercising a running system, obtain explicit confirmation that the user is authorized and record the allowed targets, identities, methods, time window, data constraints, and stop conditions.

Without that confirmation:

- inspect source, configuration, infrastructure definitions, tests, and supplied request/response samples only;
- propose safe verification steps rather than executing them;
- do not claim a source hypothesis was dynamically confirmed;
- do not access another person's or tenant's real data;
- prefer synthetic fixtures and non-destructive read checks in authorized test environments.

Stop active verification when scope or ownership is ambiguous, a check could affect availability or integrity, or unexpected sensitive data appears. Preserve only the minimum evidence needed to document the issue and redact secrets and personal data.

## Required result

This section applies after the eligibility gate selects at least one candidate. A triage-only result where all subjects are excluded uses the concise selection table described above and stops.

For a full review, produce both:

1. `assessment.json`, conforming to the bundled template and validator.
2. A human report rendered from that validated JSON as standalone HTML or Markdown.

Honor the user's requested format. If they do not specify one, prefer standalone HTML because its fixed navigation, visual decision status, and internal links make a long security assessment easier to use. Produce both formats only when requested. The renderer can infer format from an `.html` or `.md` output extension, but use `--format` explicitly in automation.

The report must contain:

- a table of contents with internal links to summaries, each finding, coverage, and gaps;
- a high-level `PASS`, `FAIL`, or `REVIEW` security outcome plus separate `COMPLETE`, `PARTIAL`, or `BLOCKED` end-to-end trace completeness and visible decision rules;
- a concise dashboard showing finding, path-completeness, and coverage counts without expanding the full branch matrix;
- an executive summary written for a non-security reader: what was reviewed, what failed, what passed, and what the real-world context means;
- a compact linked findings register with one short table per category, followed by detailed findings grouped as category → component → issue;
- concise issue code panels for `Classification`, `Affected implementation`, `End-to-end authorization path`, `Expected access rule`, `Unauthorized scenario`, `Why the check fails`, `What could happen`, `Recommended resolution`, and `How to verify the fix`;
- short normalized pseudocode instead of full source dumps, paired with exact evidence anchors;
- collapsed HTML technical detail for evidence metadata, standards mappings, access paths, and branch evidence so the first reading layer stays understandable;
- scope, revision/environment, authorization mode, exclusions, and limitations;
- an actor–resource–action–context authorization model;
- an evidence-backed access-path inventory covering methods, inputs, channels, tiers, and enforcement chains;
- all 19 A01 coverage branches with explicit status;
- findings with concrete attack paths and exact evidence anchors;
- precise OWASP, ASVS, WSTG, API Top 10, and CWE mappings where applicable;
- remediation at the policy and enforcement point;
- negative authorization regression tests;
- coverage gaps and safe next steps.

A focused review of the selected candidate scope is still required to account for every coverage branch. Use `not-applicable` or `not-assessed` with a concrete rationale instead of silently omitting a branch. Do not create branch matrices for repositories excluded by the eligibility gate.

Keep the assessment usable and finishable. Reference the same access-path or evidence anchor instead of repeating its full explanation, use the smallest evidence set that proves each conclusion, and consolidate only true shared root causes. For a small application, the JSON and report should be concise enough for an engineer to review in one sitting.

## Workflow

### 1. Establish the selected assessment subject

Carry forward the eligibility selection table. Identify revisions, selected services, applicable clients/infrastructure, identity systems, policy/control planes, data/downstream systems, and environments in candidate scope. Record supporting and excluded repositories explicitly so they are not repeatedly rediscovered.

Perform the heavy-lifting discovery pass in `references/end-to-end-authorization-tracing.md` **within selected candidates and material supporting paths only**: inspect architecture documents, manifests, deployment pipelines, IaC, gateway/proxy policies, routes, application policies, data controls, downstream references, and tests before asking the user to explain or locate missing material. Follow a cross-repository reference only when it is plausibly part of a selected authorization path; do not fan out through every repository, workspace package, or dependency. Record exclusions and whether evidence is static, supplied dynamic evidence, or explicitly authorized live testing.

Use conditional profiles from `references/architecture-profiles.md` only when evidence supports them. APIM, BFF, custom attributes, subscription keys, and other products or credentials are first-class profiles when present, not assumptions or universal checklists.

Do not equate authentication with authorization. A valid identity proves who the caller is; it does not prove that the caller may perform this action on this resource or field in this context.

### 2. Build the authorization model

Inventory:

- **actors:** anonymous, ordinary user, resource owner, peer/non-owner, privileged user, administrator, service identity, support/operator, and tenant identities;
- **resources:** records, fields, files, routes, functions, jobs, queues, administrative surfaces, exports, and downstream resources;
- **actions:** create, read, list, update, delete, approve, execute, impersonate, export, and bulk operations;
- **context:** tenant, ownership, relationship, role/scope, resource state, time, device, network, delegation, and business limits;
- **enforcement points:** gateway, middleware, route/controller, resolver, service/domain layer, repository/query, file boundary, message consumer, and downstream service.

Create an actor–resource–action–context matrix before judging individual checks. Repository structure and policy names are evidence, not proof that enforcement is complete.

Create the template's `accessPaths` inventory. For each entry point record method/protocol, channel/version, authentication state, eligible actors, protected resource/actions, caller-controlled inputs, and exact evidence. Record every material tier in order with its concrete component, generic tier type, entering and leaving identity, credentials, policies, resource context, observed decision, exact evidence, and verification status. Assign each path `complete`, `partial`, or `blocked` using the end-to-end contract. Include mobile/partner/staging, direct backend, asynchronous, downstream, or other materially different channels as paths or explicit gaps.

### 3. Trace every access path end to end

For each sensitive operation, trace attacker-controlled input from every reachable entry point to the protected action and resource. Check alternate routes, HTTP methods, arbitrary/unknown verbs, method-override headers, duplicate parameters, rewrite/forward headers, API versions, content types, GraphQL aliases/batches, background consumers, exports, static/files/cloud objects, caches, gateways, and direct backend paths.

At each path answer:

1. Which human, workload, subscription/application, gateway, service, delegated, or impersonated subject enters and leaves each tier?
2. What does each session, token, key, certificate, role, scope, claim, relationship, network, or contextual input actually prove?
3. Which resource and fields are selected?
4. Which function, object, field, tenant, relationship, state, and business policy should apply?
5. Where is each policy enforced in trusted code or configuration?
6. Can caller-controlled identifiers, roles, claims, headers, cookies, keys, tenant values, or state alter the decision?
7. Does the data query itself constrain ownership/tenant, or is filtering performed too late?
8. Does identity transformation preserve the originating authority without turning an intermediary into a confused deputy?
9. Are denial, revocation, logging, and tests fail-closed?
10. Do gateway, framework, controller, data, and downstream tiers parse the same subject, method, path, resource, and duplicate input values?
11. Do logout, role/tenant/ownership changes, workflow rollback, batching, replay, queues, or concurrent requests preserve the intended decision?

A UI-hidden button, route guard, valid subscription/API key, trusted network, valid token, coarse role/scope, guessed identifier difficulty, CORS policy, or authentication check alone is not object/function authorization. State exactly what each authority input proves. CORS controls browser response sharing; CSRF controls unwanted victim-authorized actions. Evaluate and report them separately.

### 3a. Stop for material missing evidence

After exhausting the selected candidates and material supporting configuration, apply the material evidence gate in `references/end-to-end-authorization-tracing.md`. Batch related missing code, policy exports, inherited/generated configuration, deployed revisions, identity setup, downstream implementations, or runtime evidence into a precise request that states why it matters, what was searched, affected paths/coverage, blocked conclusions, and ways to continue. Mark affected paths `blocked`, create reciprocal gaps with `requestStatus: awaiting-user`, ask the user, and wait. A repository excluded during triage is not missing evidence unless a selected path demonstrably depends on its trusted behavior.

If the user supplies evidence, resume and update the tiers. If the user explicitly excludes it or confirms it unavailable, record that decision and continue with `partial` paths. Silence does not authorize exclusion. Do not call a report final or claim end-to-end completion while a material gap awaits user direction.

### 4. Execute complete A01 coverage

Apply every branch in `references/review-playbook.md`:

- eight official common-vulnerability branches (`A01-CV-01` through `A01-CV-08`);
- eleven official prevention/assurance branches (`A01-PR-01` through `A01-PR-11`).

The branches collectively cover all 40 CWEs mapped by the official A01:2025 page. Do not attach all 40 CWEs to every finding. Select only the most specific identifiers supported by the actual weakness; record broader coverage through the branch matrix.

For APIs, deepen object-, property-, function-, and sensitive-business-flow authorization using API1, API3, API5, and API6:2023. For GraphQL, inventory queries, mutations, subscriptions, arguments, fields, aliases, batching, resolver checks, and underlying API identity propagation. These mappings supplement A01; they do not replace the A01 coverage branches.

Apply the direct and conditional WSTG procedures selected in `references/wstg-v42-a01-selection.md`. Do not turn adjacent authentication, session, injection, or client findings into A01 unless they enable the documented unauthorized path.

### 5. Separate evidence from hypotheses

Use these finding statuses:

- `confirmed`: the unauthorized path is demonstrated by complete static proof, supplied reliable execution evidence, or authorized safe reproduction;
- `likely`: evidence shows a credible path but one material runtime/configuration fact remains unresolved;
- `needs-validation`: a security-relevant signal warrants a specific check but does not yet support a vulnerability claim.

Do not report a code pattern alone as a confirmed vulnerability. Framework defaults, global middleware, generated policy, data-layer scoping, or deployment controls may close an apparent gap. Search for them and record unresolved controls as gaps.

`reviewed-no-finding` means relevant paths and controls were actually inspected. It never means “a search returned no matches.”

### 6. Document actionable findings

Each confirmed or likely finding must identify:

- one or more evidence-backed access-path IDs and show their end-to-end identity, credential, policy, decision, resource, and trace status in the human report;
- one primary human-readable category based on the authorization boundary and one owning component based on where the fix belongs;
- a precise classification, such as horizontal privilege escalation, IDOR/BOLA, missing function authorization, or property-level authorization failure;
- affected controllers, classes, methods, endpoints, files, or artifacts; use empty location arrays only when a location type genuinely does not apply, and identify at least one implementation or endpoint location overall;
- unauthorized actor and required starting privilege;
- protected resource, fields, action, and context;
- intended policy and observed enforcement failure;
- reproducible source-to-sink or request-to-impact path;
- exact file/line/symbol, configuration, test, or redacted request/response evidence;
- impact to confidentiality, integrity, availability, or business constraints;
- focused mappings and severity rationale;
- remediation at the trusted enforcement layer;
- at least one positive and one negative regression test, including a peer/non-owner or lower-privilege case where relevant.

For the issue's first reading layer, write a short summary and normalized pseudocode for the expected rule, unauthorized scenario, failure proof, impact, and remedy. Keep each block normally three to eight lines and within the validator's twelve-line/1,600-character cap. The renderer derives classification, affected-implementation, and verification panels from their structured fields. Do not paste full methods or responses; pair distilled pseudocode with exact evidence anchors and never imply pseudocode is verbatim source.

Make the `exercise` block understandable to someone who has not read the source. Describe the concrete unauthorized actor, starting privilege, resource, action, and decisive input or context, then state the expected denial and the evidenced result. Prefer a representative HTTP/GraphQL/CLI request when the subject exposes one; for a library or in-memory policy, use named business facts rather than opaque fixture IDs or phrases such as “synthetic denied probe.” Mention internal classes or test harnesses only after the scenario is clear. Distinguish static proof (`code result: allow`) from an actually executed observation (`observed: allow`), and never imply live execution occurred when it did not.

Consolidate instances only when they share one root cause, policy, enforcement point, and remediation. Assign the consolidated issue one primary category and component, then list related surfaces within it. Otherwise report separately so ownership and fixes remain clear.

### 7. Validate and render

Populate the bundled template, then run:

```bash
python "$SKILL_DIR/scripts/bac_assessment.py" validate <assessment.json>
python "$SKILL_DIR/scripts/bac_assessment.py" render <assessment.json> --format html --output <report.html>
# Or, when Markdown is requested:
python "$SKILL_DIR/scripts/bac_assessment.py" render <assessment.json> --format markdown --output <report.md>
```

Validation errors are hard failures; fix the assessment rather than weakening the validator or hand-editing rendered output. Rendering returns exit code `3` when a material gap is `awaiting-user`: present the precise evidence request and wait instead of rendering a final report. Use `--allow-blocked` only when the user explicitly requests an interim checkpoint report, which remains visibly BLOCKED. Once validation succeeds and no direction is pending, render immediately and preserve the JSON and requested report artifact before optional commentary or further exploration. Do not spend completion time re-running repository housekeeping or expanding already-supported prose.

## Completion gate

Apply this gate to the selected candidate scope, not to repositories excluded during triage. Do not call the A01 review complete until:

- [ ] Scope, revision/environment, authorization mode, exclusions, and limitations are explicit.
- [ ] Actors, resources, actions, context, and trusted enforcement points are modelled.
- [ ] The access-path inventory covers all discovered entry points, methods, inputs, channels, identity transformations, credentials, policies, resource context, tiers, and downstream effects or records explicit gaps.
- [ ] Same-role peers, vertical roles, tenants, post-logout/stale authority, alternate methods/channels, and business states were represented where applicable.
- [ ] All 8 official vulnerability patterns and all 11 prevention/assurance branches have statuses and rationales.
- [ ] The branch mapping accounts for all 40 official A01 CWEs without indiscriminate CWE assignment.
- [ ] Every finding links known access paths and has one primary category and component, a precise classification, affected implementation/endpoints, a concrete unauthorized path, and exact evidence.
- [ ] Every material tier has entering/leaving identity, credential/policy semantics, resource context, decision, status, and exact evidence; no role, key, token, network, gateway, or intermediary is credited with authority it does not prove.
- [ ] Missing material evidence was searched for before a precise user checkpoint; awaiting decisions remain blocked, accepted exclusions remain partial, and no incomplete trace is called end-to-end complete.
- [ ] Each issue has concise pseudocode for expected rule, exercise, proof, impact, remedy, and derived allowed/denied verification without full source dumps.
- [ ] Authentication-only checks, UI controls, identifier unpredictability, and CORS are not mistaken for authorization.
- [ ] Horizontal, vertical, anonymous, object, function/method, field/property, tenant, and business-limit boundaries were considered where applicable.
- [ ] Alternate paths, methods/overrides, duplicate parameters, rewrite/forward headers, versions, static/file/cloud resources, and downstream delegation were considered.
- [ ] CSRF and CORS were evaluated as distinct browser trust boundaries.
- [ ] GraphQL aliases/batching/resolvers and parser differences across tiers were considered when present.
- [ ] Confidence and severity reflect evidence and impact rather than the A01 ranking.
- [ ] Remediation and negative authorization tests address the root enforcement failure.
- [ ] Unverified runtime or deployment assumptions appear as gaps, not facts.
- [ ] The assessment validator passes and the requested HTML or Markdown report is generated from the validated JSON.
- [ ] The report has a linked table of contents, separate PASS/FAIL/REVIEW security outcome and COMPLETE/PARTIAL/BLOCKED trace status, a concise dashboard, a compact per-category findings register, category → component → issue detail grouping, end-to-end issue paths, and links from summary rows to technical detail.

## Skill evaluations

Run the deterministic checks after changing this skill:

```bash
python "$SKILL_DIR/evals/run_evals.py"
python -m unittest discover -s "$SKILL_DIR/tests" -p "test_*.py" -v
```

Use [evals/evals.json](evals/evals.json) for behavioral evaluation. A response fails if it recursively explores repositories before eligibility triage, deep-scans excluded static/client/component repositories, applies API or architecture profiles without evidence, turns excluded siblings into gaps, omits required A01 coverage for selected candidates, reports a pattern without an unauthorized path as confirmed, performs unapproved live testing, credits a role/key/token/gateway with authority it does not prove, calls an unverified path complete, fails to stop for material missing evidence, or produces findings without linked tiered paths, category/component organization, concise supporting pseudocode, actionable evidence, and allowed/denied regression tests.
