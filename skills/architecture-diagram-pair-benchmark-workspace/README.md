# Architecture diagram pair benchmark

This workspace compares only these paired configurations:

1. `build-signal-graph` + `render-signal-graph` (`signal-render`)
2. `mermaid-diagrams` + `show-me` (`mermaid-show-me`)

It does not score any skill independently.

## Comparison rule

Each configuration receives the same fixed evidence snapshot and exact outcome-focused user prompt. The prompt does not prescribe TypeScript, HTML, or Mermaid unless requested-view compliance is itself under test. The authoritative source and the final artifact are graded separately so a correct source cannot hide an inaccurate or unusable projection.

See [`rubric.json`](rubric.json) for weights, hard failures, and fairness controls.

## Pilot

The pilot uses the repository's curated Microsoft eShopOnContainers checkout fixture for two requests:

- `pilot/eshop-broad`: a broad structural architecture view;
- `pilot/eshop-sequence`: an ordered checkout sequence with HTTP acceptance and asynchronous outcomes.

Each case contains shared `eval_metadata.json` plus isolated outputs for both configurations. Results are provisional until objective grading, reversed-order blind comparison, and browser inspection are complete.

## Full benchmark design

A defensible full benchmark should add fixed, licensed evidence packs for:

- a single-repository monolith;
- a modular monolith;
- a microservices monorepo;
- multi-repository or event-driven microservices;
- incomplete or contradictory evidence;
- a lifecycle/state request and an ER/class request, reported as diagram-breadth rather than core architecture scores.

Run each case at least three times per configuration. Macro-average by architecture family and requested view so the largest microservice fixture does not determine the winner. Report duration, tokens, and artifact size separately from quality.
