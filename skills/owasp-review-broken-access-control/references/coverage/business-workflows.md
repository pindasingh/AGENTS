# Business workflows, state, limits, logging, and assurance

Load this file only when selected operations have state transitions, approvals, separation of duties, one-time actions, quotas, bulk/automated abuse risk, concurrency, compensating actions, or user-visible business limits. Load the logging subsection only for a comprehensive review or when detection is explicitly in scope.

## Trusted business policy

State prerequisites and permitted transitions in actor–resource–action–context form. Inspect:

- skipped, repeated, replayed, out-of-order, or rolled-back steps;
- caller-controlled status, approver, price, ownership, limit, or security fields;
- maker-checker and separation-of-duty rules;
- one-time operations, invitations, votes, coupons, purchases, exports, and approvals;
- edit-after-validation and transfer/reassignment behavior;
- races, concurrent requests, idempotency, atomicity, retries, queues, and compensating actions;
- aliases, batching, bulk endpoints, and automation that bypass per-operation limits;
- rate/volume controls by actor, tenant, resource, and operation when abuse creates unauthorized business impact.

A UI workflow is not trusted enforcement. Generic validation, throttling, or availability weakness is not A01 unless it connects to an unauthorized action/resource or a defined business authorization limit.

## Evidence and tests

Name the unauthorized actor, protected action/resource, required role/state/limit, bypassed trusted decision, and side effect. Separate findings when state authorization, field authorization, function authorization, and atomic one-time enforcement have different root causes or fixes.

Tests should cover lower role, forbidden field, skipped step, replay, duplicate submission, rollback, concurrent requests, bulk/batch behavior, and no-side-effect denial as applicable.

## Logging and assurance

When in scope, verify denials and suspicious repetitions produce structured, actionable records with actor, tenant, resource/action, decision, policy, reason, and correlation—without secrets. Logging absence is usually a control gap unless it enables concrete undetected abuse in the stated risk model.

Relevant coverage includes A01-CV-02/A01-CV-04/A01-CV-05, A01-PR-05/A01-PR-07/A01-PR-08/A01-PR-11, API3/API5/API6:2023 where applicable, and precise supported CWEs. Load `object-function-tenant.md` when fields, roles, objects, or functions are involved and `sessions-revocation.md` for delayed/stale authority.
