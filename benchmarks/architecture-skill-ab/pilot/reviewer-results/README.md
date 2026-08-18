# Legacy pilot reviewer results

Two independent model reviewers compared the same generated artifacts in reversed A/B orders for each eShop case. Native formats were preserved, but skill/configuration names, logs, and validation claims were hidden from the comparison prompt.

## Order mapping

| Case/order | A | B |
|---|---|---|
| broad/order 1 | Mermaid/Show Me | Signal/render |
| broad/order 2 | Signal/render | Mermaid/Show Me |
| sequence/order 1 | Mermaid/Show Me | Signal/render |
| sequence/order 2 | Signal/render | Mermaid/Show Me |

Both reviewers selected Mermaid/Show Me in both cases despite the reversed presentation order:

| Case | Mermaid/Show Me totals | Signal/render totals |
|---|---:|---:|
| Broad architecture | 87.2, 79.8 | 58.3, 59.9 |
| Sequence | 87.2, 89.5 | 67.2, 58.4 |

This corroborates the directional result in `../../pilot-results.md`: Mermaid/Show Me was more evidence-conservative and matched the requested sequence form, while Signal/render supplied stronger native interactivity but introduced unsupported details and did not deliver a temporal sequence view.

## Why these are not final benchmark scores

- The reviewers used the superseded pilot rubric: semantic accuracy 50%, requested-view compliance 20%, usefulness 20%, and technical integrity 10%. Two reported totals contain 0.4-point arithmetic discrepancies; the JSON preserves each reported value and adds the recomputed total.
- The current rubric separately scores semantic accuracy, projection fidelity, requested-view compliance, and task-based usefulness.
- eShop is benchmark-contaminated because both skill specifications already encode its expected architecture.
- There was one generated artifact per pair, not three replicates.
- There were two model judges per case, not the required three mixed-experience judges.
- No human answer-time study, prior format preference, paired confidence interval, or inter-rater statistic was captured.
- The pilot fixture and eval metadata disagree about some unsupported/required details. Reviewer claims about Submitted status, rejected-status propagation, and paid-status SignalR delivery are preserved with coordinator notes rather than silently accepted.

The individual grading callbacks were incomplete: broad Signal received 65.6/100; sequence Signal received 63.4/100; sequence Mermaid received 87.45/100 with 7/10 assertions. Broad Mermaid's individual reviewer returned no numerical score. Do not impute the missing score or aggregate these partial grades.

Use these JSON files as historical reviewer evidence only. The winner decision must follow `../../blind-protocol.md` and `../../rubric.json`.
