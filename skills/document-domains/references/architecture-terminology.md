# Architecture terminology

Use these terms consistently in the manifest, report, instructions, and tests.



## Component

An evidenced software boundary such as a service, application, worker, gateway, transformer, or meaningful subsystem.

Call a component a microservice, bounded context, aggregate, or deployable only when evidence establishes that classification.

## Inbound endpoint

The concrete architectural path by which a component receives work. It is a first-class record containing:


- subscription or consumer group;
- authentication and authorization;
- handler symbol;
- relevant payload shape and identities;
- ordered infrastructure ingress path, such as Front Door → APIM → service;
- evidence and explicit gaps for unknown fields.



## Operation

One component handling one concrete inbound endpoint. The entry point is one of:

- an HTTP method and route;
- a named command or query;
- a named event or message;
- a scheduled job;
- a domain-language actor action when the exact technical contract is unavailable.

An operation owns one canonical interaction sequence.





A rule constraining identity, ownership, state, routing, or valid behaviour. Attach it to the relevant domain, component, operation, or interaction step.

## Evidence gap

A point where the available source cannot establish implementation, wiring, runtime behaviour, or outcome. Record what was searched and where the evidence trail ends.

## Report hierarchy

The report hierarchy is fixed:

```text
Domain
├── Table of contents

    ├── Component overview
    └── Operations
        └── Interaction sequence
```



- `flow breakdown`
- `available content`
- `domain journey`
- `operation flow`
- `technical trace`

Use the defined terms instead. Generic `flow` may appear only when it is part of established domain language or quoted source terminology.
