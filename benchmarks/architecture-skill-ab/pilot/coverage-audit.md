# Pair-benchmark coverage audit

This audit considers only the two paired configurations:

1. `build-signal-graph` + `render-signal-graph` (`signal-render`)
2. `mermaid-diagrams` + `show-me` (`mermaid-show-me`)

Individual skill quality is relevant only where it affects a pair's end-to-end result.

## Reusable assets already present

| Asset | What it contributes to the pair benchmark | Limitation |
|---|---|---|
| `skills/build-signal-graph/evals/fixtures/eshop-checkout/` | One shared evidence oracle already referenced by Signal build/render and Mermaid evals | One famous microservice domain creates overfitting and memorization risk |
| `skills/build-signal-graph/tests/type-safety.ts` and `runtime.ts` | Programmatic gate for typed wiring, object identity, and operation preservation | Tests the Signal pair's model mechanics, not comparative artifact usefulness |
| `skills/render-signal-graph/tests/run-tests.js` | Programmatic gate for deterministic output, safe escaping, invalid references, identity uniqueness, and renderer CLI behavior | Does not establish that a generated diagram matches a particular repository |
| `skills/render-signal-graph-workspace/` | Two preserved Signal renderer iterations, HTML, screenshot, accessibility result, grading, and review page | Compares renderer versions, not the two skill pairs; one run per version, no timing or variance |
| `skills/mermaid-diagrams/evals/evals.json` | Topology, sequence, state, ER, and hostile-input prompts with expected semantics | Definitions only: no saved pair outputs, grading, screenshots, timing, or benchmark history |
| `skills/skill-creator/` grader, comparator, analyzer, aggregation, and viewer | Existing benchmark and human-review machinery | Standard aggregate schema assumes with/without configurations; pair labels need explicit mapping or a small pair-aware adapter |

`show-me` has no standalone eval corpus. For this benchmark that is not a reason to test it individually; it means the `mermaid-show-me` pair must be judged on whether Show Me improves selection, concision, and artifact presentation rather than bypassing or weakening Mermaid semantics.

## What the pilot now covers

| Capability | Signal/render | Mermaid/Show Me |
|---|:---:|:---:|
| Same eShop evidence and exact broad-view prompt | ✓ | ✓ |
| Same eShop evidence and exact sequence prompt | ✓ | ✓ |
| Authoritative source preserved | ✓ | ✓ |
| Offline review artifact preserved | ✓ | ✓ |
| Browser screenshot and accessibility tree | ✓ | ✓ |
| Browser offline reload and page-error inspection | ✓ | ✓ |
| Gold manifest and shared assertions | ✓ | ✓ |
| Strict/native mechanical validation | ✓ | Static safety only |
| Repeated trials and variance | — | — |
| Timing and token capture | — | — |
| Reversed-order anonymous model-judge comparison | ✓ (legacy rubric) | ✓ (legacy rubric) |
| Human feedback, task answer time, and format preference | — | — |
| Non-eShop architecture families | — | — |

The existing pilot therefore supports directional findings, not a universal winner.

## Comparative gaps to close

1. **Variance and equal budgets:** run each case three times per pair under equal token, wall-time, and tool-call ceilings. Save `timing.json` immediately from executor completion metadata and report both budgeted completion quality and quality among successful artifacts.
2. **Rendered-artifact parity:** the current machine has no installed Mermaid renderer. The Mermaid source is authoritative and the Show Me HTML is reviewable, but it is not a rendered Mermaid diagram. Report this as delivered-artifact capability rather than silently treating source and rendering as equivalent. A final rendered comparison requires one pinned renderer that is already available in the execution environment.
3. **Blind usefulness review:** randomize A/B order independently for at least three judges with mixed format experience, ask the case's architecture questions, and save preference, answer accuracy, and answer time. File type can reveal the approach, so blindness means hiding skill identity—not pretending the formats are identical.
4. **Machine scoring:** derive required identities, edges, directions, order constraints, and forbidden inventions from each gold manifest. Use programmatic checks for syntax, exact names, and contract/cardinality facts; reserve readability and utility for human review.
5. **Corpus balance:** use the pinned evidence packs in `materials.md`, including a monolith/project-reference oracle, a large microservice monorepo, an event-driven sequence, and a machine-readable AsyncAPI case.
6. **Evidence uncertainty:** include anonymized and evidence-ablation controls so famous-sample recall and unsupported inference are measurable.
7. **Fixture consistency:** resolve the eShop fixture's requirement for a payment-failure variant despite the absence of a payment-failure contract or terminal behavior. The gold rule should require an explicit unresolved branch and forbid invented details.
8. **Requested-view breadth:** report topology, sequence, impact, and explicit event-topology results separately. State/ER/class requests should be a capability-breadth track, not allowed to distort core architecture-discovery scores.

## Staged next execution

### Phase 1: public-material calibration

Use these four cases from `materials.md`:

1. eShopOnWeb — broad logical/deployment architecture;
2. Google microservices-demo — broad microservice architecture;
3. eShopOnContainers — checkout acceptance and asynchronous outcome sequence;
4. AsyncAPI Streetlights — event topology and directionality.

At two pairs and three runs, this is **24 executor runs**. These cases validate the harness and gold-scoring mechanics, but eShop expectations are already present in the skills and the public samples may be familiar to the model. Calibration cannot establish a final winner.

### Phase 2: blind confirmatory comparison

Run the six-case matrix in `blind-protocol.md`: five neutral unseen/renamed architecture cases plus one separately reported format-fit case. At two pairs and three runs, this is **36 executor runs**. Use two-architect adjudicated atomic fact sheets, anonymized submissions, at least three judges, and the decision rule in `rubric.json`.

For both phases, run all configurations for a case from the same evidence snapshot and exact user prompt. Apply native gates after each run:

```sh
tsc -p skills/build-signal-graph/tests/tsconfig.json
node skills/render-signal-graph/tests/run-tests.js
```

Then grade against atomic gold manifests, randomize A/B order per judge, aggregate by pair and requested view, and generate the static review artifact with:

```sh
python skills/skill-creator/eval-viewer/generate_review.py \
  <workspace> \
  --skill-name "Architecture diagram pair benchmark" \
  --benchmark <workspace>/benchmark.json \
  --static <workspace>/review.html
```

Do not add a no-skill baseline to this comparison. The configurations under test are the two pairs.
