# WSTG 4.2 selection for A01 reviews

## Selection basis

This reference records the WSTG 4.2 material that materially improves an OWASP A01:2025 Broken Access Control review. It is intentionally not a claim that every WSTG test belongs to A01.

- Release: [OWASP WSTG v4.2](https://owasp.org/www-project-web-security-testing-guide/v42/)
- Git tag: [`v4.2`](https://github.com/OWASP/wstg/tree/v4.2)
- Tag commit: `dd33419e10edb22b78d89325a6c2aad9f184e3a2`
- Core authorization chapter: [4.5 Authorization Testing](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/05-Authorization_Testing/)

Selection criteria:

- **direct** — the procedure can establish an A01 unauthorized-access path or tests an A01-listed weakness/prevention control;
- **supporting** — the procedure improves attack-surface completeness, expected-policy modelling, evidence quality, or reporting;
- **conditional** — use only when the named technology/surface exists or when the weakness changes an authorization decision;
- **excluded** — the topic is primarily another category and adds no distinct A01 review step.

The skill design reviewed 39 candidate WSTG 4.2 documents selected from the complete v4.2 table of contents. The material below is what was retained. Tool-specific exploitation recipes and unrelated authentication, injection, cryptography, client-side, and infrastructure tests were not engraved into the A01 workflow.

## Retained methodology

| WSTG source | Relevance | Material retained in this skill |
|---|---|---|
| Web Security Testing Framework | supporting | Review requirements, architecture, threat models, source, deployment configuration, and post-change behavior rather than relying on one black-box pass. |
| 4.0 Introduction and Objectives | supporting | Separate passive surface discovery from explicitly authorized active verification; document controls tested and evidence observed. |
| `WSTG-INFO-06` Identify Application Entry Points | direct support | Inventory every method, parameter, hidden field, cookie, custom header, authentication state, multi-step operation, websocket/API path, and external message entry point. |
| `WSTG-INFO-07` Map Execution Paths | direct support | Record discovered and tested paths; inspect decision branches, data flow, and race/concurrency paths rather than claiming complete coverage from route enumeration. |
| `WSTG-INFO-10` Map Application Architecture | supporting | Include gateways, reverse proxies, caches, load balancers, application servers, identity systems, stores, and downstream services because enforcement may differ across tiers or nodes. |
| WSTG Reporting | supporting | State version, scope, limitations, evidence mode, finding likelihood/impact, masked proof, remediation, methodology, and tested coverage. |

## Direct and conditional A01 procedures

### Resource, route, and deployment exposure

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-CONF-03` | conditional/direct | Check whether sensitive source/config/archive extensions are served, whether extension handling differs by directory/node, and whether old variants bypass normal execution or access rules. |
| `WSTG-CONF-04` | direct | Find old, backup, snapshot, unreferenced, log, source, and hidden-function files; distinguish repository presence from actual web exposure. |
| `WSTG-CONF-05` | direct | Enumerate administration/support interfaces across paths, ports, hostnames, source comments, defaults, and hidden parameters; then apply function authorization. |
| `WSTG-CONF-06` and merged `WSTG-INPV-03` | direct | Compare policy across methods, arbitrary/unknown verbs, `HEAD`, method-override headers, and gateway/framework method interpretation. Verify body and side effects, not status alone. |
| `WSTG-CONF-09` | direct | Review OS/container/deployment permissions for web, config, secret, log, executable, database, temporary, and upload resources. |
| `WSTG-CONF-11` | direct | Review cloud-object list/read/create/update/delete permissions at bucket/container and object level; do not perform writes/deletes without explicit safe authorization. |

### Identity, role, and channel model

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-IDNT-01` | direct support | Identify roles and actual permissions, then compare same-role peers and vertical roles. A role name or signed role value is not itself a vulnerability. Include support/operator and maker-checker/segregation rules. |
| `WSTG-IDNT-03` | conditional/direct | Test who may provision/deprovision each account type, whether a subject can create greater privilege, and how owned resources/authority transfer after deprovisioning. |
| `WSTG-ATHN-04` | conditional | Include direct protected-page access and caller-controlled authenticated flags only when they produce anonymous access to an A01-protected function/resource. Classify authentication-only root causes as adjacent A07. |
| `WSTG-ATHN-10` | supporting | Inventory mobile, partner, accessibility, regional, staging, call-centre, and other shared-account channels; compare authorization, not only authentication, and record inaccessible channels as scope gaps. |

### Core authorization

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-ATHZ-01` | direct | Enumerate every user-controlled file/path input, normalization layer, encoding, OS path form, archive/link/include operation, and effective service-account file permission. Use safe synthetic files for authorized dynamic checks. |
| `WSTG-ATHZ-02` | direct | Build an access matrix for every role and function, including anonymous, post-logout, same-role peer, lower-role, special rewrite/forward headers, direct backend paths, and administrative functions. |
| `WSTG-ATHZ-03` | direct | Test caller-controlled group, role, profile, tenant, condition, IP/network, hidden field, and URL values; distinguish horizontal and vertical escalation and inspect partial URL policy matches. |
| `WSTG-ATHZ-04` | direct | Find all caller-controlled references to records, operations, files, and functions, including references split across multiple parameters; compare at least two owners and, where relevant, roles and tenants. |

### Session and browser-carried authority

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-SESS-01` | conditional/direct | Inspect session/JWT/cookie/hidden-field values used as authorization metadata for tamper resistance, replay, subject/role/tenant content, and server verification. General token entropy belongs primarily to authentication/session review unless it enables unauthorized access. |
| `WSTG-SESS-02` | conditional/direct | Inspect cookie `Domain`, `Path`, `SameSite`, `Secure`, `HttpOnly`, expiry, and prefixes where cookie scope/injection/replay changes authority or cross-site request behavior. A missing flag without an A01 path is adjacent hardening. |
| `WSTG-SESS-05` | direct | Check whether a third-party origin can cause a victim browser to perform a protected state-changing action. POST alone is not CSRF protection. Keep CSRF distinct from CORS response-reading policy. |
| `WSTG-SESS-06` | direct | Verify server-side invalidation after logout, old-token replay, critical paths after logout, SSO/application session termination, response data, and side effects. |
| `WSTG-SESS-07` | conditional/direct | Verify server-enforced inactivity/absolute lifetime where stale authority matters; client-controlled expiry and cookie deletion alone do not revoke server authority. |
| `WSTG-CLNT-12` | conditional | Inspect browser storage and global client state only for sensitive authorization metadata or client-only decisions; general sensitive-data storage is outside this A01 profile. |

### Parser, trust-boundary, and failure-path bypass

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-INPV-04` | conditional/direct | Compare duplicate-parameter interpretation at gateway, middleware, framework, controller, and data layer. A finding requires policy validation and protected operation/resource selection to consume different occurrences. |
| `WSTG-INPV-19` | conditional/direct | Trace attacker-controlled destinations to server-side fetches and determine whether server/network/service identity grants access to internal files, metadata, services, or administrative actions. This is A01 when it crosses an authorization/resource sphere; otherwise note adjacent classification. |
| `WSTG-ERRH-01` | conditional/direct | Exercise malformed, missing, unavailable-policy, timeout, and exception paths to verify authorization fails closed and does not return sensitive data or perform side effects. Different error text alone is not an A01 finding. |

### Business policy and abuse resistance

| WSTG ID | Relevance | A01 use |
|---|---|---|
| Business Logic Introduction | direct support | Obtain intended limits and workflows from owners/docs; create manual abuse/misuse cases because generic scanners cannot infer application-specific policy. Include race/concurrency paths. |
| `WSTG-BUSL-02` | direct | Identify guessable, hidden, debug, and workflow parameters accepted outside the normal UI; require trusted server-side policy rather than expected client flow. |
| `WSTG-BUSL-03` | direct | Check hidden/non-editable fields, relational edits, field-level permissions, state-dependent writes, and unauthorized log/data modification. |
| `WSTG-BUSL-05` | direct | Identify per-subject/resource/tenant limits and verify repetition, replay, back-navigation, batching, and concurrency cannot exceed them. |
| `WSTG-BUSL-06` | direct | Model state transitions, prerequisites, rollback/compensation, repeated/skipped/out-of-order steps, and edit-after-validation paths. |
| `WSTG-BUSL-07` | supporting | Assess denial logging, alerting, throttling, and application-wide misuse signals. Lack of active defense alone is a gap/hardening item unless it materially enables documented A01 impact. |

### CORS and APIs

| WSTG ID | Relevance | A01 use |
|---|---|---|
| `WSTG-CLNT-07` | direct | Inventory CORS endpoints; inspect fixed/validated origins, reflection, wildcard, credentials, methods, headers, and preflight behavior. Prove a malicious origin can read or influence protected data before reporting an A01 finding; public APIs may intentionally allow `*`. |
| `WSTG-APIT-01` | conditional/direct | Inventory GraphQL queries, mutations, subscriptions, arguments, IDs, fields, aliases, batching, introspection, and underlying API calls. Enforce function/object/field authorization in resolvers/services and preserve the originating subject downstream. |

## Material deliberately not engraved

- Generic tool installation and command recipes: the skill must work without requiring a scanner or package installation.
- Broad session randomness, transport, XSS, injection, cryptography, and generic sensitive-browser-storage guidance unless it changes an authorization decision or enables the A01 path being documented.
- Destructive examples such as arbitrary object upload/delete, account changes, or production file access: live testing requires explicit authorization and synthetic/non-destructive proofs.
- Appendix F browser-tool keystrokes: useful operationally, but they add no durable BAC reasoning beyond request, cookie, storage, and JavaScript manipulation already represented in the playbook.
- A WSTG status code alone as proof: compare response content, protected state, queued work, downstream effects, audit evidence, and actor/resource policy.

## Reliability consequences

A reliable A01 assessment must now produce or explicitly gap:

1. an access-path inventory spanning all entry points, methods, parameters, headers, cookies, channels, versions, tiers, and downstream calls;
2. an actor/role/peer/tenant matrix including post-logout and changed-authority states;
3. protected resource/function/field/business-state rules;
4. trusted enforcement chains and parser behavior at every tier;
5. negative tests that assert response **and** absence of side effects;
6. coverage evidence tied to exact source revision or authorized runtime artifact;
7. a report that separates findings, control gaps, adjacent-category signals, and unassessed scope.
