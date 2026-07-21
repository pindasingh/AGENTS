# .NET discovery playbook

Use this only after detecting .NET. Framework names are search aids, not architecture classifications.

## Inventory

Inspect solution/project files, target frameworks, `OutputType`, project/package references, executable projects, test projects, generated clients, migration projects, Dockerfiles, deployment manifests, CI artifacts, and configuration sources. Distinguish one solution from its independently executing outputs.

## Composition roots and inbound work

Trace `Program.cs`, host builders, startup modules, and transitive `Add*` registration extensions. Find:

- ASP.NET controllers, minimal API maps, route groups, API versioning, OpenAPI documents, gRPC services, and authentication/authorization policies;
- `IHostedService`, `BackgroundService`, Functions triggers, Quartz/Hangfire jobs, and scheduled commands;
- MassTransit/NServiceBus/Azure Service Bus/Kafka consumers, endpoints, queue/topic/subscription names, consumer definitions, filters, retries, outbox, and dead-letter behavior.

Do not stop at an extension method call. Follow the registration implementation until the runtime, interface, or explicit gap is established.

## Outbound work

Find typed/named `HttpClient`, Refit, generated OpenAPI clients, gRPC clients, service-discovery keys, base-address configuration, message publish/send calls, producer registrations, `DbContext`/database clients, Elasticsearch clients, blob/file clients, and package/project references.

Trace configuration keys through `appsettings*.json`, options binding, environment variables, Helm/Kubernetes values, Compose, infrastructure code, and integration tests. A common key such as `DefaultConnection` does not prove a shared database.

## Contracts and versions

Record API version from observed route/versioning/OpenAPI evidence. Record event identity from the actual type/schema/discriminator and its explicit version. Package or assembly version is not automatically an event version. Retain schema paths or deterministic fingerprints and only fields needed for correlation, routing, partitioning, ownership, or security.

Match generated clients to servers using generator metadata, OpenAPI/protobuf origin, routes, and compatible contracts. Match publishers to consumers using channel identity plus compatible contract identity/version/fingerprint. Preserve mismatches.

## Clean Architecture and mediator patterns

Project names such as Domain, Application, Infrastructure, and API do not establish C4 Components. Use MediatR/CQS handlers, ports, adapters, public interfaces, and dependency direction to trace an operation. Record internal steps only for significant decisions or boundary crossings. Do not inventory every handler, validator, mapper, behavior, repository class, or utility.

## Stores

Record the logical database/catalog/schema, index, bucket, or file-store identity, not merely the database server. Find `DbContext`, mappings, connection configuration, migrations, index aliases, and read/write sites. Record migration ownership separately from read/write access. Several runtimes accessing one exact logical identity map to one candidate store with several directional dependencies.
