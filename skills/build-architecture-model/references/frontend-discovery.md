# Front-end and MFE discovery playbook

Use this after detecting browser applications, React, or Module Federation. Libraries and build packages are not automatically runtime units.

## Runtime and delivery boundaries

Inspect package/workspace manifests, build targets, entry points, deployment descriptors, public paths, host/shell configuration, Module Federation configuration, route ownership, and runtime remote loading. Determine whether a browser application or MFE is independently built and delivered, loaded at runtime, or only linked into another bundle.

Record an independently delivered browser application/MFE as a runtime discovery unit. Record ordinary React packages, MobX stores, hooks, utilities, and design-system packages as libraries or internal evidence rather than runtimes.

## Inbound and composition interfaces

Capture user-facing responsibility and runtime composition interfaces when architecturally significant. For Module Federation, record host-to-remote direction, remote/module identity, public path, version policy when observed, and evidence from both host and remote when available.

Do not turn routes, pages, MobX stores, or design-system components into architecture nodes merely because they are named modules.

## Outbound dependencies

Find fetch/Axios clients, generated OpenAPI clients, GraphQL/gRPC-web clients, base URL and service-discovery configuration, browser messaging, storage, analytics, and runtime remote loading. Match clients to API interfaces using destination identity, method/path/version, and compatible contracts. An API route alone does not prove a browser caller.

## Contracts and rules

Retain API version, schema origin/fingerprint, authentication mechanism, and key routing/correlation fields. Capture guards, tenant routing, feature gates, or filters only when they change the caller, target, or architectural path. Do not copy full TypeScript types, component props, form validation, state trees, or ordinary UI behavior.

## Shared design systems

Record package identity and version as a library dependency. A design system becomes a runtime or external service only when separately running behavior is evidenced, such as a runtime asset service with architecturally meaningful communication. Package use can support impact analysis but does not by itself establish a runtime relationship.
