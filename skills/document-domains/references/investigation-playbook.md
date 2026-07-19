# Local investigation playbook

## Contents

- [Principle](#principle)
- [Inventory](#inventory)
- [Discover interfaces](#discover-interfaces)

## Principle

Build a traceable argument, not a polished guess. Use broad discovery first, focused tracing second, and contradiction searches last. Record what was searched when expected evidence is absent.

## Inventory



Do not begin with one business keyword. That biases discovery toward familiar names and misses wiring, indirect consumers, and alternate terminology.

## Canonical branch pass

For each Git root, inspect without changing the working tree. Resolve origin/main before origin/master, fetch when local instructions permit, and evaluate the resolved commit in an isolated temporary worktree or clone. Record the branch, commit SHA, remote, fetch result, and whether the supplied checkout diverges.

Never document a feature branch merely because it is checked out. If main or master is unavailable, stale, or fetch-blocked, preserve the best permitted local evidence and create a canonical-revision gap.

Build or test only the isolated canonical revision and only when it adds evidence. Use the repository's pinned toolchain and lockfiles; do not upgrade dependencies or deploy.

## Discover interfaces

Adapt searches to detected technologies. Find registration and wiring before handler bodies. Potential evidence includes:


## Trace operations

For each interface:

1. Capture trigger, input contract, authentication, authorization, and validation.

7. End at an observable result, local or external boundary, or named gap.
8. Reverse-search from each sink, event, or state change to reveal skipped hops.

Make one interaction step convey one meaningful decision, transformation, boundary crossing, or state change.

## Connect components

Rank evidence by convergence, not name similarity alone.

Strong signals include an exact configured address, topic, or queue plus compatible contracts; generated client and server code from one contract; composition or integration tests naming both sides; and matching correlation, identity, or idempotency conventions.



- Who or what initiates the behaviour and which outcome is sought.
- Which operations and asynchronous continuations participate.
- Which identities and data cross boundaries.
- Which state changes accumulate across subsystems.
- What initiators and downstream actors observe.


Check for:

- Error, retry, idempotency, rollback, or compensation paths omitted from happy-path descriptions.
