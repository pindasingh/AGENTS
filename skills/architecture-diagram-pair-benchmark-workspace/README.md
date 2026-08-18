# Architecture diagram pair benchmark

This workspace compares only these paired configurations:

1. `build-signal-graph` + `render-signal-graph` (`signal-render`)
2. `mermaid-diagrams` + `show-me` (`mermaid-show-me`)

It does not score any skill independently.

## Comparison rule

Each configuration receives the same fixed evidence snapshot and exact outcome-focused user prompt. The prompt does not prescribe TypeScript, HTML, or Mermaid unless requested-view compliance is itself under test. The authoritative source and the final artifact are graded separately so a correct source cannot hide an inaccurate or unusable projection.

See [`rubric.json`](rubric.json) for weights, hard failures, and fairness controls. [`coverage-audit.md`](coverage-audit.md) records the reusable repository assets, comparative gaps, and compact next execution.

## Pilot

The pilot uses the repository's curated Microsoft eShopOnContainers checkout fixture for two requests:

- `pilot/eshop-broad`: a broad structural architecture view;
- `pilot/eshop-sequence`: an ordered checkout sequence with HTTP acceptance and asynchronous outcomes.

Each case contains shared `eval_metadata.json` plus isolated outputs for both configurations. Browser inspection and native validation are preserved. [`pilot-results.md`](pilot-results.md) records the directional one-run result; it is not a statistically final or blind preference benchmark.

## Full benchmark design

[`materials.md`](materials.md) pins licensed evidence packs and exact oracle files for single-repository clean architecture, monoliths, microservices, event-driven flows, and explicit AsyncAPI contracts. It also defines anonymized and evidence-ablation controls.

The compact next iteration is four cases × two pairs × three runs: 24 executor runs. Macro-average by architecture family and requested view so the largest microservice fixture does not determine the winner. Report duration, tokens, and artifact size separately from quality. Keep lifecycle/state and ER/class requests in a separate diagram-breadth track rather than allowing them to distort core architecture-discovery scores.
