# Architecture skill A/B benchmark harness

> **Operator-run benchmark infrastructure—not an Agent Skill.** This directory intentionally lives under `benchmarks/`, contains no `SKILL.md`, is not discovered by Pi's skill loader, and cannot trigger or be invoked as a skill.

This harness compares two architecture-output **candidates**, A and B. A candidate may contain one skill or an ordered set of cooperating skills. The harness does not assume Signal, Mermaid, TypeScript, HTML, or any other representation; those are candidate-declared capabilities.

The preserved eShop run under [`pilot/`](pilot/) compares:

- A: `build-signal-graph` + `render-signal-graph`
- B: `mermaid-diagrams` + `show-me`

That is an example benchmark instance, not a hard-coded harness restriction.

## Run a new A/B benchmark

1. Copy [`pilot/benchmark-config.json`](pilot/benchmark-config.json) to a new run workspace.
2. Replace candidate A and B's `id`, pinned `revision`, `skill_paths`, source/artifact declarations, native viewer command/checks, and native validation commands. Confirmatory candidates require at least one validation command.
3. Replace the cases with fixed evidence paths and identical outcome-focused prompts.
4. Validate the configuration:

   ```sh
   python benchmarks/architecture-skill-ab/scripts/validate_config.py <config.json>
   ```

5. Prepare an isolated run plan:

   ```sh
   python benchmarks/architecture-skill-ab/scripts/prepare_runs.py \
     <config.json> <new-run-directory>
   ```

6. Preserve the printed `PREPARATION_COMMITMENT` outside the run directory.
7. Follow [`runbook.md`](runbook.md) continuously through generation, callback metric capture, native validation evidence, semantic grading, projection review, blinded task review, pre-unblinding review sealing, aggregation, and the winner rule.

A normal comparison is `cases × 2 candidates × replicates`. Candidate labels remain A/B throughout generation and scoring; skill identities are retained only in the coordinator map and removed from judge submissions.

For reproducibility and input hashing, `skill_paths` must be repository-relative directories containing `SKILL.md`. Snapshot or vendor a globally installed/external skill into the benchmark repository before comparing it; absolute paths are intentionally rejected.

## Fairness model

Each candidate receives the same fixed evidence snapshot, exact user prompt, model/version, fresh-session policy, repository access, and completion budget. Prompts remain outcome-focused and format-neutral except in a separately reported format-fit stratum. Grade authoritative semantics, projection fidelity, requested-view compliance, and task usefulness separately.

- [`benchmark-config.schema.json`](benchmark-config.schema.json) defines the reusable candidate/case contract.
- [`run-score.schema.json`](run-score.schema.json) defines candidate-neutral per-run grading and metrics.
- [`run-evidence.schema.json`](run-evidence.schema.json) defines execution, callback timing, validation-log, native-viewer, and artifact evidence required from completed confirmatory runs.
- [`judge-evidence.schema.json`](judge-evidence.schema.json) defines the sealed, coordinator-side proof required for blind task review.
- [`rubric.json`](rubric.json) defines the architecture-specific 100-point score and critical errors.
- [`blind-protocol.md`](blind-protocol.md) defines candidate-neutral generation and judging controls.
- [`harness-requirements.md`](harness-requirements.md) is the operational completion checklist.
- [`materials.md`](materials.md) lists architecture calibration and fixture-construction sources.
- [`scripts/`](scripts/) validates configurations, prepares isolated run plans, and aggregates A/B scores without third-party dependencies.
- [`STATUS.md`](STATUS.md) states what is complete and what remains blocked.

## Preserved pilot

[`pilot/results.md`](pilot/results.md) records the directional one-generation eShop result and reversed-order reviewer check. [`pilot/coverage-audit.md`](pilot/coverage-audit.md) records its exact validation coverage and shortcomings. The pilot is benchmark-contaminated and does not satisfy the confirmatory decision protocol.
