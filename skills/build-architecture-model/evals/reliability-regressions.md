# Evaluation: determinism and architecture-change reliability

These cases distinguish agent/output nondeterminism from genuine architecture changes. Run them against fixed fixture revisions and compare generated indexes rather than prose claims.

## Repeatability matrix

| Case | Mutation | Expected semantic result | Expected provenance/projection result |
|---|---|---|---|
| Same input | None; repeat at least three times | Identical `modelSemanticHash` | Byte-identical projections |
| Source order | Reverse repository scan order | Identical IDs, hierarchy, and semantic hash | No projection changes |
| JSON order | Reorder object keys and set-like arrays | Identical canonical bytes after `format` | No diff |
| Checkout relocation | Move identical repositories to another root | Identical graph semantic hash | Source location can be provenance-only |
| Revision only | Change recorded revision with no architecture observation change | No graph semantic change | Source/evidence-only change |
| Evidence lines | Shift line anchors after code movement | No graph semantic change | Evidence-only change |
| Implementation refactor | Rename a private helper without changing stable component responsibility or path | No graph semantic change | Evidence-only or no change |
| Caller added | Add compatible mobile caller evidence | Caller relationship/path semantic change | Regenerated path projections |
| Contract changed | Change outbound v2 to incompatible v3 | Separate interface/relationship/conflict/gap changes | Affected path becomes partial/blocked |
| Dependency inserted | Add a real feature-flag or downstream call | Focused relationship and path semantic changes | Sequence/projections change at exact position |
| Call reordered | Swap two evidenced dependency calls | Path semantic hash changes | Numbered and ASCII order changes |
| Return removed | Remove the actual caller response | Validation failure or partial path with explicit gap | Cannot retain complete coverage |
| Projection tampered | Edit Markdown/ASCII only | No canonical graph change | Validation fails projection drift |

## Assertions

- Stable graph IDs never depend on scan order, temporary checkout path, JSON object order, or participant aliases.
- A no-op rescan does not rewrite unrelated shards.
- Semantic hashing excludes evidence and source-finding records but retains operation behavior, identities, references, rules, contracts, and path order.
- Content hashing uses canonical full JSON so evidence-only changes remain inspectable.
- `diff` reports `semanticChanges`, `evidenceOnlyChanges`, `projectionChanges`, `controlChanges`, `added`, and `removed` separately.
- A projection change without a canonical path change is drift, not accepted architecture evolution.
- A changed source revision does not automatically imply changed architecture.
- A real dependency, direction, caller, contract, component responsibility, operation, or sequence change cannot be classified as evidence-only.

## Variance protocol for agent evaluations

For each machine-readable discovery eval in `evals.json`:

1. Run at least three independent with-skill executions against the same fixed fixture.
2. Run the prior skill snapshot as baseline when evaluating an improvement.
3. Validate every artifact set with the bundled helper.
4. Compare normalized hierarchy, stable IDs, relationships, path participants, sequence labels/order/endpoints, outcomes, coverage, and semantic hash.
5. Grade exact assertions; do not award success for a plausible prose explanation.
6. Investigate any field that varies across valid runs. Either make it deterministic, classify it as provenance-only, or document why it is genuinely underdetermined by evidence.

A model is not reliable merely because each independent run looks reasonable. Equivalent evidence must converge on equivalent graph meaning.
