# Gateways, policy engines, delegation, services, and events

Load this file only when a selected path crosses a gateway, ingress/proxy, BFF, policy engine, service boundary, token exchange, workload identity, queue/event, or downstream API. Also load `../end-to-end-authorization-tracing.md` when the path has multiple material tiers or identity transformations.

## Cross-tier questions

At every material tier record entering/leaving identity, credential, policy, resource context, decision, evidence, and verification status. Ask:

1. What human, workload, application, subscription, gateway, delegated, or impersonated identity enters and leaves?
2. What does each token, key, certificate, role, scope, claim, network rule, or assertion actually prove?
3. Where are function, object, field, tenant, relationship, state, and business rules enforced?
4. Do policy and operation consume the same subject, method, route, host, resource, and duplicate input values?
5. Can direct, alternate, retry, failover, async, or old-version paths skip a decision?
6. Does identity transformation preserve originating authority without making an intermediary a confused deputy?

Transport/workload authentication is not originating-user or resource authorization unless explicitly designed and constrained.

## Framework policies and custom controls

Trace default, fallback, global, endpoint, inherited, and anonymous metadata through policy registration, providers, requirements, handlers, guards, filters, interceptors, directives, resource resolvers, and service/query checks. Inspect composition (`AND`, `OR`, first-match, deny override), ordering, failure behavior, resource context, and placement relative to routing, model binding, mutation, caching, and exceptions. A recognized annotation or passing handler test is not proof every endpoint invokes it correctly.

## API gateways and APIM

For any gateway inspect route/host/method matching, normalization, policy order/inheritance, authorizer caches, identity header transforms, JWT/key/mTLS/network semantics, backend selection, retries/failover, direct exposure, timeout/failure behavior, and environment/deployed differences.

When Azure APIM evidence exists, inspect service/workspace/global/product/API/version/revision/operation scopes; every relevant `<base />`; inbound/backend/outbound/on-error sections; `validate-jwt` or equivalent controls; `choose`, rewrites, backend selection, header/query transforms, caching, products/groups/subscriptions; named values/fragments; backend identity; direct reachability; and deployed revision. Missing inherited/effective policy is material only for a selected path.

A subscription/API key usually proves a calling subscription/application at configured scope—not an end user, tenant, role, object, or field permission.

## BFFs, service boundaries, and delegation

Inspect cookie/session establishment, anti-forgery where relevant, route authorization, mobile/partner bypasses, delegated/on-behalf-of/token-exchange/application-only/workload credentials, subject/tenant/role/scope preservation, fan-out, caching, direct backend paths, retries, sagas, internal/admin ports, mesh bypass, policy distribution, and version skew.

A backend authorizing only a BFF or service identity can become a confused deputy. Determine whether downstream policy intentionally authorizes the workload, originating subject, or both.

## Serverless and event-driven paths

Inspect gateway/event-source policy, function identity and cloud permissions, caller context in messages, producer integrity, consumer-side policy, tenant/resource binding, delayed role changes, replay, idempotency, direct function URLs, alternate triggers, dead-letter/admin replay, retries, and side effects. An authorized producer does not make every caller-controlled message resource authorized.

## Credential semantics

For sessions/JWT/OAuth/OIDC, API keys, mTLS/certificates, managed identities, roles/groups/scopes/claims, and contextual signals, determine issuer/controller, represented authority, integrity, audience, scope, tenant/resource/action binding, lifetime/revocation, transport, and downstream preservation. Treat forwarded headers and client claims as untrusted unless a verified intermediary establishes and protects them.

## Evidence and tests

Do not call a path complete while a material policy, identity transform, deployed overlay, consumer, or downstream decision is unknown. After targeted discovery, use the evidence checkpoint in `../end-to-end-authorization-tracing.md`.

Test intended access plus wrong user/application/subscription, peer, cross-tenant, lower scope/role, stale authority, direct backend, alternate route/method/version, missing context, policy timeout/failure, replay, and no downstream side effect as applicable. Map only the selected weakness; do not credit a valid gateway decision with authority it does not prove.
