# Object, function, field, and tenant authorization

Load this file only when selected paths operate on records, fields, tenant data, privileged functions, methods, routes, RPC operations, GraphQL fields, or caller-supplied resource context.

## Model the rule

For each selected path state:

```text
actor may perform action on resource/fields when context is true
actor must be denied when ownership, tenant, role, relationship, field, or state differs
```

Contrast only boundaries that exist: anonymous/authenticated, owner/peer, same/cross-tenant, ordinary/privileged/admin, permitted/forbidden fields, and valid/invalid resource state. Authentication, a UI guard, a coarse role, an API key, CORS, or identifier unpredictability is not object or function authorization.

## Trace the selected operation

Record the entry point, method/operation, channel, identity, caller-controlled identifiers/fields/tenant values, route and policy checks, service/domain decisions, query constraints, serialization, downstream effects, and exact evidence. Compare policy and operation parsing for alternate methods, overrides, duplicate parameters, rewrites, versions, aliases, batches, and direct backend routes only when those surfaces exist.

Inspect:

- public/anonymous exceptions and fallback/default policy;
- route/controller/resolver/function authorization and policy composition;
- object retrieval, list/search, bulk/export, nested resources, attachments, and history;
- owner, tenant, relationship, delegated authority, and platform-operator rules;
- writable and returned fields, mass assignment, immutable/security fields, and serializer behavior;
- privileged/admin/support/impersonation/approval operations;
- old versions, alternate protocols, arbitrary methods, and routes hidden only by clients;
- query scoping versus fetch-then-check and post-filtering;
- negative tests that assert no body, mutation, queue item, cache entry, or downstream effect.

For GraphQL inspect queries, mutations, subscriptions, fields, aliases, batching, nested resources, resolver checks, and identity propagation. For gRPC/WebSockets inspect method, message, stream/subscription, and resource authorization. Schema visibility alone is not an authorization failure.

## Evidence threshold

A finding needs an intended policy, an actor outside it, a reachable selected path, the missing/incorrect trusted decision, and impact. Search for global middleware, generated policy, service checks, and data-layer constraints before concluding that a local annotation gap is exploitable.

Use:

- `confirmed` for complete static proof, supplied reliable execution evidence, or authorized reproduction;
- `likely` when evidence supports the path but one material runtime/configuration fact remains;
- `needs-validation` for a signal without enough evidence to claim a vulnerability.

Do not describe generic input validation, readable JWTs, UUIDs, missing UI controls, or policy names as findings without connecting them to an unauthorized protected operation.

## Focused mappings

Use only mappings supported by the weakness:

- object/tenant access: A01-CV-03, A01-PR-04, API1:2023, CWE-639 or CWE-566;
- field/property access: A01-CV-02/A01-CV-04, API3:2023, a precise supported CWE;
- function/method access: A01-CV-04/A01-CV-05, API5:2023, CWE-862/863 or more specific CWE;
- trusted enforcement/defaults: A01-CV-01, A01-PR-01/A01-PR-02/A01-PR-03/A01-PR-10;
- negative authorization tests: A01-PR-11.

Load `../asvs-wstg-cheatsheet-crosswalk.md` only when standards mappings are requested. Load `../wstg-v42-a01-selection.md` only when detailed web test procedures are needed.

## Finding output

Name the unauthorized actor and starting privilege, protected resource/fields/action/context, expected denial, evidenced result, exact implementation/evidence anchors, impact, focused mappings, trusted-layer remediation, and at least one allowed and one denied regression case. Consolidate only instances sharing one root cause, enforcement point, policy, and fix.
