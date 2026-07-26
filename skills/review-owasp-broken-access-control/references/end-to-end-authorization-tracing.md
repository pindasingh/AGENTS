# End-to-end authorization tracing and evidence acquisition

## Purpose

Trace the authoritative subject, policy, resource, action, and context through every material tier that can admit, transform, authorize, select, mutate, or delegate a protected operation. Apply this model regardless of product, language, protocol, deployment style, or repository layout.

Do the discovery work before asking the user for architecture details. An absent local controller annotation is not proof of exposure, and a gateway allow decision is not proof of object or tenant authorization.

## Architecture-neutral trace

Model each operation as:

```text
entry point
  -> identity establishment
  -> credential validation
  -> identity transformation or delegation
  -> function authorization
  -> object, field, tenant, relationship, and state authorization
  -> protected operation and data selection
  -> downstream and asynchronous effects
```

Common tiers include identity providers, clients, CDNs/WAFs, gateways, ingress or service meshes, BFFs, API composition layers, middleware, controllers, resolvers, functions, policy engines, domain services, repositories, files/object stores, downstream services, queues, workers, caches, and external integrations. Include only tiers supported by evidence; do not force this list onto simpler architectures.

## Heavy-lifting discovery pass

Before asking the user, inspect all available scope for:

1. repository instructions, solution/workspace manifests, service catalogues, architecture documents, threat models, and ownership metadata;
2. deployment pipelines, environment overlays, IaC, API specifications, route manifests, gateway/proxy policies, container/orchestration files, and generated configuration;
3. authentication schemes, credential validators, token exchange, session state, custom attributes/decorators, policy registration/providers/handlers, filters, middleware, guards, interceptors, and anonymous exceptions;
4. controller/resolver/function/message entry points and alternate versions, methods, hosts, channels, direct backends, jobs, and static/file paths;
5. domain checks, query scoping, row/tenant policy, downstream calls, queues, caches, and side-effect boundaries;
6. positive and negative authorization tests, deployment tests, policy tests, and supplied runtime evidence;
7. references to external repositories, generated policies, control-plane configuration, named values, secrets, identity-provider setup, or deployed state that are not present.

Search for both controls and protected operations. Follow references and call paths; keyword matches alone neither prove nor disprove enforcement.

## Tier record

Record every material tier in order with:

- generic tier type and concrete component;
- identity entering and leaving the tier as `entryIdentity` and `exitIdentity`;
- credentials or authority inputs considered there;
- policies, attributes, roles, scopes, keys, relationships, tenant, state, or resource rules evaluated;
- resource context available to the decision;
- the observed decision or delegation behavior;
- exact source, configuration, test, or runtime evidence;
- `verified`, `partial`, or `unverified` status.

Identity transitions are security decisions. Distinguish:

```text
originating human or workload
service or gateway identity
subscription/client/application identity
delegated user identity
impersonated/effective identity
resource owner and tenant context
```

A service identity may authorize transport to a downstream service without carrying the originating user's authority. A role, scope, key, certificate, network location, or valid token proves only the authority it was designed to represent.

## Authorization-input semantics

For every credential or policy input determine:

```text
what identity or authority it proves
who issues or controls it
where it is accepted
integrity and transport protection
scope, audience, tenant, product, resource, and action binding
lifetime, rotation, and revocation
whether it survives delegation or identity transformation
whether it is sufficient for this specific function and resource
```

Evaluate combinations, not just individual validity. Examples include application key plus user token, managed identity plus originating-user context, gateway assertion plus backend policy, role plus ownership, scope plus tenant, and signed URL plus resource binding.

## Trace statuses

Use these statuses per access path:

- `complete`: every material tier from reachable entry point through protected operation and downstream effect is verified with evidence;
- `partial`: the user explicitly accepted an exclusion or confirmed that evidence is unavailable, and the available tiers were traced as far as possible;
- `blocked`: a material artifact or decision is unavailable and user direction is required before continuing that path.

A complete path contains only verified tiers and no unresolved gap reference. Partial and blocked paths identify the exact gaps that prevent completeness.

Report assessment completeness separately from the security outcome:

- `COMPLETE`: all recorded paths are complete and no coverage branch is not assessed;
- `PARTIAL`: no path is blocked, but at least one path is partial or coverage remains not assessed after user direction;
- `BLOCKED`: at least one path is awaiting user direction.

A confirmed finding can coexist with PARTIAL or BLOCKED completeness. Do not let `FAIL` hide incomplete tracing. An unqualified `PASS` requires COMPLETE trace coverage for the stated scope.

## Material evidence gate

A missing artifact is material when it can change a conclusion about:

- route, method, host, channel, version, or direct-backend reachability;
- the authoritative identity, tenant, role, scope, key, relationship, or policy data;
- gateway/policy inheritance, deployment overlays, generated configuration, or policy ordering;
- delegated versus application-only authority;
- object, field, tenant, business-state, query, file, or downstream enforcement;
- fail-open behavior, revocation, side effects, or negative tests.

Do not classify a path as complete by assuming that a missing tier is permissive or protective. Use `likely`, `needs-validation`, or no finding according to the evidence that remains.

## Required user checkpoint

After exhausting available evidence, batch related missing artifacts into a precise request. State:

```text
Missing artifact or access
Why it is material
What was searched or inspected
Affected access paths and coverage branches
Which findings or no-finding conclusions are blocked
Acceptable ways to continue
```

Offer relevant options:

1. provide the repository path, configuration, policy export, generated artifact, or code;
2. provide explicitly authorized read-only access;
3. provide reliable deployment or runtime evidence;
4. explicitly exclude the layer and accept a partial assessment;
5. stop the affected review path.

Then wait for user direction. Do not render or describe an assessment as final while a material gap is `awaiting-user`.

If evidence is supplied, inspect it and remove or update the gap. If the user excludes it or confirms it cannot be obtained, record the exact decision, mark affected paths partial, and preserve blocked conclusions in the report. Silence is not consent to exclude.

## Finding confidence across incomplete chains

A missing upstream or downstream tier may close or worsen an apparent path. Use:

- `confirmed` only when available evidence itself proves a reachable unauthorized path or complete static flow;
- `likely` when one material deployment/runtime fact remains but evidence supports the probable path;
- `needs-validation` when the missing tier could materially change whether unauthorized access is possible.

A gateway authentication rule does not close object authorization. Conversely, missing local endpoint metadata is not a finding when an available trusted policy or data constraint demonstrably closes the operation.

## Regression design

Build tests across tier boundaries, not just within one method:

```text
allowed intended actor and resource
anonymous or missing credential
wrong application/subscription/key
same-role peer or non-owner
cross-tenant actor/resource
lower role or missing scope
alternate route/method/version/channel
revoked or stale authority
direct backend and delegated downstream path
policy failure, timeout, or missing context
no sensitive response, mutation, queue item, cache entry, or downstream effect
```

Use synthetic data and authorized environments. A unit test of a custom handler and an integration test through the actual gateway/BFF/backend chain answer different questions; record both where applicable.
