# Architecture diagram pair benchmark

This workspace compares only these paired configurations:

1. `build-signal-graph` + `render-signal-graph` (`signal-render`)
2. `mermaid-diagrams` + `show-me` (`mermaid-show-me`)

It does not score any skill independently.

## Comparison rule

Each configuration receives the same fixed evidence snapshot and exact outcome-focused user prompt. The prompt does not prescribe TypeScript, HTML, or Mermaid unless requested-view compliance is itself under test. The authoritative source and the final artifact are graded separately so a correct source cannot hide an inaccurate or unusable projection.

See [`rubric.json`](rubric.json) for the 100-point score and critical-error rules. [`blind-protocol.md`](blind-protocol.md) defines controlled generation, blinding, the six-case confirmatory matrix, and the winner decision rule. [`coverage-audit.md`](coverage-audit.md) records reusable repository assets and comparative gaps.

## Pilot

The pilot uses the repository's curated Microsoft eShopOnContainers checkout fixture for two requests:

- `pilot/eshop-broad`: a broad structural architecture view;
- `pilot/eshop-sequence`: an ordered checkout sequence with HTTP acceptance and asynchronous outcomes.

Each case contains shared `eval_metadata.json` plus isolated outputs for both configurations. Browser inspection and native validation are preserved. [`pilot-results.md`](pilot-results.md) records the directional one-run result; it is not a statistically final or blind preference benchmark.

## Full benchmark design

[`materials.md`](materials.md) pins licensed public evidence packs and exact oracle files for single-repository clean architecture, monoliths, microservices, event-driven flows, and explicit AsyncAPI contracts. It also defines anonymized and evidence-ablation controls.

Use those public materials first for a 24-run calibration: four cases × two pairs × three runs. Because the skills already encode eShop-specific expectations and public samples may be familiar to the model, do not use calibration alone to declare a winner. The confirmatory benchmark in `blind-protocol.md` uses six unseen/renamed cases × two pairs × three runs: 36 executor runs. Keep explicit format-fit and state/ER/class breadth results separate from the five neutral architecture cases.
