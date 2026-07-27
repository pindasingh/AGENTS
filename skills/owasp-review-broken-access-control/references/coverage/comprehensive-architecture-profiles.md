# Comprehensive architecture and credential profiles

## How to use these profiles

Load this file only during comprehensive mode when architecture-specific detail is material. Focused reviews use the smaller concern files selected by `SKILL.md`.

Apply the architecture-neutral trace in `../end-to-end-authorization-tracing.md` first. Activate only profiles supported by discovered evidence. These profiles improve product-specific discovery; they do not replace end-to-end policy reasoning or authorize live control-plane access.

For an unknown product, identify its equivalents for route scope, policy inheritance, identity validation, transformation, backend selection, direct exposure, failure behavior, deployment overlays, and negative tests.

## Custom attributes, annotations, and policy engines

Inspect:

- authentication versus authorization attributes and schemes;
- default, fallback, global, endpoint, inherited, and anonymous/permit-all metadata;
- custom policy providers, requirements, handlers, voters, guards, filters, interceptors, directives, and resource resolvers;
- policy composition (`AND`, `OR`, first-match, deny override), handler ordering, and multiple-scheme behavior;
- whether the selected resource, tenant, fields, action, and state are supplied to the decision;
- middleware/filter placement relative to routing, authentication, model binding, mutation, caching, and exception handling;
- endpoint conventions, generated routes, minimal/function endpoints, versioned controllers, and alternate protocols;
- service/domain/query enforcement and tests beneath coarse route roles.

Trace named policy registration to implementation. A recognized attribute or passing handler unit test is not proof that every endpoint invokes it with authoritative context.

## Azure API Management profile

When Azure APIM evidence exists, inventory:

- service, workspace, global, product, API, version/revision, and operation scopes;
- inherited policy behavior and every relevant `<base />` placement or omission;
- inbound, backend, outbound, and on-error policy sections;
- `validate-jwt`, `validate-azure-ad-token`, certificate, IP/network, header, subscription, and custom policy-expression decisions;
- `choose`/`when` branching, `return-response`, `rewrite-uri`, `set-backend-service`, header/query transforms, caching, and error paths;
- products, groups, subscriptions, subscription scope, `subscriptionRequired`, and whether a key is required alone or with user/workload identity;
- named values, Key Vault references, environment parameters, fragments, workspaces, self-hosted gateways, and generated/deployed policy;
- backend credentials and identities, originating-subject propagation, user/application token exchange, and direct backend reachability;
- versions, revisions, operations, wildcard templates, unmatched routes, WebSocket/GraphQL surfaces, and policy differences by environment;
- IaC/pipeline source versus the policy revision actually deployed.

Treat a subscription key as evidence of a subscription or calling application at its configured scope, not automatically as end-user, tenant, role, object, or field authorization. Determine whether APIM policy intentionally maps the subscription to additional trusted authority and whether the backend independently enforces resource policy.

If repository policy uses `<base />`, fragments, named values, product membership, or external deployment configuration that is absent and material, request the effective policy/export or authorized evidence before completing the path.

## Generic API gateways, ingress, proxies, and service meshes

For AWS API Gateway and Lambda authorizers, Kong, NGINX, Envoy, ingress controllers, YARP, Ocelot, service meshes, and comparable products, inspect their equivalents for:

- route/host/method matching and normalization;
- global/service/route/plugin/filter policy order and inheritance;
- authorizer identity and decision caches;
- forwarded, rewritten, signed, or stripped identity/context headers;
- JWT/API-key/mTLS/network validation and claim mapping;
- backend routing, retries, failover, shadow routes, and direct exposure;
- external authorization service failure and timeout behavior;
- environment, cluster, listener, virtual-host, route, and workload differences.

Compare the exact method, path, host, duplicate parameter, and decoded value consumed by policy with the value consumed by the protected operation.

## BFF and API-composition profile

Inspect:

- browser cookie/session establishment, origin and anti-forgery controls, logout, and session revocation;
- mobile/partner/server channels that bypass browser-specific BFF assumptions;
- BFF route authorization and resource context;
- user-delegated, on-behalf-of, token-exchange, application-only, and managed/workload downstream credentials;
- preservation or replacement of originating subject, tenant, roles, scopes, actor/delegation chain, and correlation context;
- header/cookie/token transforms and whether the backend trusts them only from an authenticated intermediary;
- aggregation where one request fans out to resources with different policies;
- caching and response composition across users/tenants;
- BFF-only versus directly reachable backend routes and alternate versions.

A backend that authorizes only the BFF service identity may become a confused deputy. A BFF function check does not prove backend object, field, tenant, or business-state authorization.

## Microservices, service-to-service, and service mesh

Inspect:

- workload identity and transport authentication separately from user/resource authorization;
- delegated subject and actor chains, token audience, scopes, tenant, and downstream resource binding;
- per-hop authorization versus a trusted centralized decision and the integrity of decision context;
- retries, fan-out, sagas, compensating actions, internal/admin ports, mesh bypass, and direct pod/service routes;
- policy distribution, cache invalidation, control-plane failure, and version skew;
- whether downstream services authorize the originating user, the calling workload, or both according to policy.

## GraphQL, gRPC, WebSockets, and API composition

Inspect operation, resolver/method, object, field, subscription/stream, batch, alias, and nested-resource authorization. Verify identity propagation to underlying APIs and each fan-out resource. Include introspection or reflection only when it exposes or enables a protected path; schema visibility alone is not object authorization failure.

## Serverless and event-driven systems

Inspect:

- gateway/event-source authorization before function invocation;
- function/workload identity and per-resource cloud permissions;
- caller identity/context preserved in events, queues, topics, schedules, callbacks, and dead-letter/replay paths;
- consumer-side policy, idempotency, stale/replayed authority, delayed role/tenant changes, and side effects;
- direct function URLs, alternate triggers, administrative replay, and poison/error handling.

Do not assume an authorized producer makes every event payload or requested resource authorized for every consumer action.

## Files, object stores, CDNs, signed links, and caches

Inspect origin and edge policy, direct object URLs, cache keys and principal/tenant variance, signed URL resource/audience/expiry binding, path normalization, listing, metadata/backups, purge behavior, and origin bypass. Separate public publication from protected objects.

## Credential and authority profiles

### API and subscription keys

Determine issuer, owner, product/API/environment scope, transport location, rotation/revocation, source restrictions, quotas, and whether the key is combined with human/workload identity. Test missing, invalid, revoked, wrong-product, wrong-environment, wrong-tenant/application, and direct-backend cases.

Key exposure or storage may be adjacent to A01. Report A01 only when key possession creates a supported unauthorized path or incorrect authority decision.

### Sessions, cookies, JWT, OAuth/OIDC, and delegated tokens

Verify issuer, signature/key trust, audience, exact scope/role/group parsing, tenant, subject, actor/delegation, lifetime, revocation, session binding, token exchange, and resource policy. A valid token authenticates represented authority; it does not automatically authorize every object or function.

### mTLS, certificates, managed identities, and workload identities

Verify trust chain/issuer, subject or workload mapping, audience, environment, rotation, allowed caller workload, and intended downstream operation. Transport or workload identity does not substitute for originating-user/resource policy unless explicitly designed and constrained.

### Roles, groups, scopes, claims, attributes, and relationships

Trace source of truth, mapping/synchronization, namespace and case semantics, inheritance, deny/allow composition, tenant binding, stale changes, and resource context. Coarse role or scope checks commonly need ownership, relationship, field, state, and business constraints.

### Network, device, origin, and contextual signals

Treat IP, network, origin, device, time, risk, and location as contextual policy inputs only when obtained and validated through a trusted path. Forwarded headers and client claims are not authoritative merely because an intermediary normally sets them.

## Cross-profile questions

For every discovered architecture ask:

1. What identity and credential reaches each tier?
2. What does that credential actually prove?
3. Which tier decides function permission?
4. Which tier decides object, field, tenant, relationship, and state permission?
5. Do policy and operation consume the same route, method, subject, and resource?
6. Can any alternate channel or direct path skip a decision?
7. Does identity transformation preserve the authority needed downstream without granting excess authority?
8. Do failures, timeouts, stale caches, new routes, and unknown operations deny safely?
9. Are positive and negative tests present at unit, integration, and architecture boundaries?
10. Which material artifacts remain unavailable, and has the user directed how to proceed?
