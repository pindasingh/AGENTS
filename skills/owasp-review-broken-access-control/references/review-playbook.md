# A01 review playbook

## How to use this playbook

Complete all 19 coverage branches. Start from the authorization model and trace real operations; do not replace semantic review with keyword searches. Searches locate candidate enforcement points and sinks, while code/configuration flow establishes whether an unauthorized path exists.

For each branch record one status:

- `finding` — one or more confirmed or likely findings reference the branch;
- `reviewed-no-finding` — applicable paths were reviewed and no supported issue was found;
- `not-applicable` — the subject lacks the relevant surface, with evidence or a scoped rationale;
- `not-assessed` — evidence, access, time, environment, or authorization was insufficient.

Evidence can be reused across branches, but each branch needs its own conclusion. A hardening opportunity without a concrete unauthorized path belongs in branch notes or gaps, not as a fabricated vulnerability.

## Actor–resource–action–context matrix

Model at least these boundaries where they exist:

| Dimension | Cases to contrast |
|---|---|
| Authentication | anonymous, authenticated, expired/revoked session |
| Horizontal | owner versus peer/non-owner with the same role |
| Vertical | ordinary, privileged, administrator, support/operator |
| Tenant | same tenant, different tenant, platform operator |
| Function | read/list, create, update, delete, approve/execute/export |
| Field | public, owner-only, privileged, immutable/security-sensitive |
| Resource state | draft/published, active/disabled, pending/approved, owned/transferred |
| Delegation | originating user, gateway/service identity, background worker |
| Context | normal versus restricted location/device/time/network/risk state |
| Business limits | ordinary use, bulk/automated use, quota or workflow boundary |

Use precise expected-policy statements, for example: “A tenant member may read invoices belonging to the same tenant but may not read another tenant's invoice, even if its identifier is known.”

## Access-path inventory

Build one inventory entry per distinct policy/enforcement path, not merely per visible page. Record:

- route, method/protocol, API version, GraphQL operation, message, job, file/object URL, or other entry point;
- primary/mobile/partner/staging/support or other channel and whether accounts/resources are shared;
- anonymous/authenticated/post-logout state and eligible roles/tenants;
- protected resource, fields, function, action, and business state;
- query/body/path parameters, duplicate parameters, hidden fields, cookies, claims, custom/rewrite/forward headers, and method overrides;
- gateway/proxy, middleware, controller/resolver, service/domain, repository/store, and downstream enforcement chain;
- exact source/config/test/runtime evidence and any unverified deployment dependency.

Compare route registrations with OpenAPI/GraphQL schemas, clients, tests, gateway rules, static/web roots, cloud object configuration, and generated code. A route list is incomplete if alternate channels, old versions, direct backends, load-balanced variants, consumers, or background operations remain unaccounted for.

## Official common-vulnerability branches

### A01-CV-01 — Least privilege and deny-by-default failure

Inspect public/anonymous declarations, default/fallback policy, wildcard grants, broad roles/scopes, inherited permissions, infrastructure permissions, default file/object ACLs, and error/fallback behavior. Trace unmatched or newly added routes. Distinguish intentionally public resources from accidental allow-by-default behavior.

Strong evidence includes a sensitive operation reachable under a subject lacking its intended permission. A permissive-looking policy without a reachable protected operation is a hypothesis or gap.

### A01-CV-02 — URL, parameter, state, HTML, or API-request bypass

Inventory caller-controlled resource IDs, role/tenant/account selectors, ownership flags, workflow state, headers, content types, alternate verbs, route aliases, API versions, GraphQL fields, RPC methods, and hidden fields. Trace each to the trusted decision and resource query.

Look for checks performed only in clients, stale middleware attached to one route version, method-specific policy gaps, arbitrary verbs, method-override headers, duplicate-parameter parsing differences, rewrite/forward headers, trusted proxy headers, mass assignment into security fields, or server code that accepts caller-supplied identity/context instead of deriving it from the authenticated subject.

### A01-CV-03 — IDOR and object-level authorization

For every direct and indirect object reference, compare owner with peer/non-owner and same-tenant with cross-tenant access. Inspect single-record, list/search, bulk, export, attachment, history, and nested-resource paths. Prefer queries constrained by authorized scope over fetch-then-check patterns; verify that failure behavior does not leak the object.

Common sinks include primary-key lookups, storage keys, filenames, sequential IDs, slugs, foreign keys, and GraphQL/node identifiers. UUID unpredictability is not authorization.

### A01-CV-04 — Missing API operation controls

Compare policy across GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS, arbitrary methods, method overrides, custom actions, bulk endpoints, import/export, websocket subscriptions, GraphQL queries/mutations/subscriptions/aliases/batches, RPC methods, background jobs, and old API versions. Confirm function, object, and field permission, and verify response bodies and side effects rather than trusting status codes.

Do not infer safety because the UI never emits a method. Direct clients can send any reachable request.

### A01-CV-05 — Anonymous, horizontal, or vertical privilege escalation

Trace sensitive functions, administration, support tooling, impersonation, role management, account provisioning/deprovisioning, approvals, exports, and dangerous operations. Test the intended role hierarchy in both directions. Inspect whether a subject can provision greater privilege, how owned resources transfer, maker-checker/segregation rules, role/scope parsing, case/namespace collisions, default roles, group synchronization, privilege changes, and stale sessions.

An authentication bypass can enable A01, but map it to A01 only when it produces a demonstrated authorization boundary failure; note A07 as an adjacent category outside this skill's full scope.

### A01-CV-06 — Authorization metadata manipulation or replay

Identify every authorization input: server session, JWT claims, OAuth scopes, cookies, hidden fields, headers, cache entries, policy data, signed URLs, and resource attributes. Determine who issues it, integrity protection, audience, lifetime, revocation, refresh, and how quickly role/ownership changes take effect.

Do not recommend custom token cryptography. Verify established library behavior and server-side policy. A readable JWT is not a vulnerability; untrusted or stale claims affecting authorization can be.

### A01-CV-07 — CORS trust-policy failure

Review exact allowed origins, credential use, origin reflection, `null` origins, subdomain matching, preflight handling, caching and `Vary: Origin`, and environment-specific overrides. Determine whether a malicious origin can read or modify protected data with victim credentials or tokens.

CORS is a browser response-sharing control, not server-side user authorization. Inventory fixed/validated origins, reflection, wildcard behavior, credentials, allowed methods/headers, preflight handling, and sensitive response content. A broad CORS policy is a finding only when combined with a concrete protected browser interaction and attacker capability; otherwise document hardening or a gap. Evaluate CSRF separately: determine whether a third-party site can cause the victim browser to perform a protected state-changing action; POST alone is not protection.

### A01-CV-08 — Force browsing

Build a route/resource inventory independent of visible navigation. Include admin/support endpoints across ports and hostnames, debug/status pages, old versions, source comments, backups/editor variants/snapshots, generated documentation, static assets, direct download URLs, cloud objects, case/extension variants, alternate channels, and internal/direct-backend routes exposed by gateway rules. Verify access as anonymous and lower-privilege actors.

Do not treat a redirect to login as sufficient without checking the terminal response, alternate methods, API behavior, and direct backend route where applicable.

## Official prevention and assurance branches

### A01-PR-01 — Trusted server-side enforcement

Map every sensitive operation to a server/service/domain/repository enforcement point. Flag client-only checks, manipulable policy metadata, or downstream calls that authorize the intermediary rather than the originating subject. Record ASVS 5.0.0-8.3.1 and, where applicable, 8.3.3.

### A01-PR-02 — Deny by default

Verify framework fallback/default policy, route registration, policy evaluation failures, new endpoint behavior, static resources, and infrastructure defaults. Explicitly identify public resources. Exceptions should be narrow and reviewable.

### A01-PR-03 — Consistent reusable mechanisms and minimal CORS

Inventory authorization frameworks, middleware, policy services, annotations/decorators, query scoping, and custom one-off checks. Compare enforcement across stacks and versions. Reuse reduces policy drift but does not prove policy correctness. Review CORS centrally and per endpoint.

### A01-PR-04 — Record ownership

Verify data-specific authorization for create, read, update, delete, list, bulk, and nested operations. Ownership can mean tenant, relationship, delegated authority, or policy attributes rather than a literal `owner_id`; document the actual rule. Check ownership transfer and reassignment.

### A01-PR-05 — Domain business limits

Identify limits such as one-time transitions, approval separation, transaction caps, inventory reservations, voting, invitations, coupon use, purchases, exports, or rate/volume constraints. Model prerequisites, repeated/skipped/out-of-order steps, edit-after-validation, rollback/compensation, back navigation, aliases/batching, and resource transfer. Ensure the trusted domain layer—not only UI state—enforces them under replay, concurrency, and automation.

### A01-PR-06 — Directory listing and exposed metadata/backups

Inspect web roots, static-file handlers, object-store publication, directory indexes, build/deployment copy rules, source maps, `.git`, archives, editor backups, environment files, logs, temporary files, generated reports, and sensitive source/comments. Confirm deployment relevance before reporting repository-only files as exposed.

### A01-PR-07 — Failure logging and alerting

Trace authorization denials and suspicious repetitions to structured logs and actionable alerts without leaking secrets. Check actor, resource/action, decision, policy, correlation, tenant, and reason-code capture. Logging absence is generally a control gap unless it enables a concrete undetected abuse impact described by the user’s risk model.

### A01-PR-08 — Rate limits against automated abuse

Review limits by actor, tenant, resource, operation, and business flow; distributed bypasses; trusted client headers; GraphQL aliases/batches; batch endpoints; reset windows; races; and fail-open dependencies. Separate availability throttling from authorization, and connect an A01 finding to automated unauthorized access or business-limit harm.

### A01-PR-09 — Session and token invalidation

Check logout, password/role/tenant/ownership changes, user disablement, incident revocation, token lifetime, refresh rotation/reuse, signing-key rollover, caches, and long-running connections. Verify that authorization changes take effect at the level required by ASVS 5.0.0-8.3.2.

### A01-PR-10 — Established declarative controls

Verify framework/toolkit configuration, version-appropriate semantics, policy composition, annotation inheritance, proxy behavior, and centralized tests. Custom checks require deeper path and failure review. The mere presence of a recognized framework is not a pass.

### A01-PR-11 — Functional authorization tests

Review unit and integration tests for positive and negative cases. Require anonymous, lower-role, peer/non-owner, cross-tenant, forbidden field, alternate method/path, revoked privilege, and relevant business-limit cases. Tests should assert no state change and no sensitive response, not only an HTTP status.

## Coverage of all 40 A01 CWEs

Use these groups to ensure each official mapped CWE is considered. Groups guide coverage; findings still receive only the most precise supported mappings.

| Review group | CWEs | Primary branches |
|---|---|---|
| Paths, links, temporary files | CWE-22, CWE-23, CWE-36, CWE-59, CWE-61, CWE-65, CWE-377, CWE-379 | CV-02, CV-08, PR-06 |
| Unauthorized information/resource exposure | CWE-200, CWE-201, CWE-359, CWE-402, CWE-497, CWE-668, CWE-922 | CV-01, CV-03, PR-01, PR-04 |
| Web-root, source, backup, and directory exposure | CWE-219, CWE-538, CWE-540, CWE-548, CWE-552, CWE-615 | CV-08, PR-06 |
| Defaults, permissions, and ownership | CWE-276, CWE-281, CWE-282, CWE-283, CWE-732 | CV-01, CV-03, PR-02, PR-04 |
| General missing/incorrect authorization | CWE-284, CWE-285, CWE-862, CWE-863 | CV-01, CV-04, CV-05, PR-01 through PR-04 |
| Cross-origin request/response boundaries | CWE-352, CWE-1275 | CV-06, CV-07, PR-03, PR-09 |
| Alternate/direct/dangerous paths and functions | CWE-424, CWE-425, CWE-749 | CV-02, CV-04, CV-08 |
| User-controlled object keys | CWE-566, CWE-639 | CV-03, PR-04 |
| Delegation, redirects, and server-side destinations | CWE-441, CWE-601, CWE-918 | CV-02, PR-01 |

The table's union must remain exactly the official 40-CWE list. `evals/run_evals.py` verifies this invariant.

## Static-review heuristics

Adapt searches to the detected languages and frameworks. Useful candidate categories include:

- route/endpoint declarations and anonymous/public exceptions;
- authorization annotations, policies, guards, middleware, filters, interceptors, resolvers, and directives;
- object lookups by request IDs and unscoped list queries;
- tenant/account/user IDs accepted from request data;
- role, scope, group, permission, ownership, and policy comparisons;
- administrative, support, impersonation, export, bulk, approval, and delete operations;
- serializers/mappers selecting response fields and binders accepting writable fields;
- file/static handlers, web roots, object stores, archives, source maps, and temporary files;
- CORS, cookie, session, JWT, OAuth/OIDC, gateway, proxy, and cache configuration;
- authorization denial logs, metrics, alerts, throttles, and negative tests.

Search both for controls and for sensitive operations. Also compare parsers across proxy/gateway, framework, controller, and data layers: method overrides, duplicate parameters, rewritten URLs, forwarded client/network identity, and decoded/normalized paths can cause policy and operation to evaluate different values. A repository with no authorization keywords may use generated/global controls or may lack them; either conclusion requires architectural and call-path evidence.

## Safe dynamic verification, only when authorized

Prefer a controlled matrix using synthetic identities and records:

1. Establish an allowed baseline for the owner/intended role.
2. Repeat with anonymous, peer/non-owner, lower-role, cross-tenant, and revoked identities as applicable.
3. Change one variable at a time: identifier, method, path, field, role/scope, tenant, state, origin, or token age.
4. Verify status, response body, side effects, audit record, and downstream state.
5. Stop on unexpected sensitive data; retain a redacted minimal proof.

Never use destructive methods against production merely because they appear in A01 examples. Source review and proposed test cases are valid outcomes when safe execution is unavailable.
