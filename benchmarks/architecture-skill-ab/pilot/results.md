# Pilot results

Status: **directional calibration, not a final benchmark**. Each pair was run once on the same curated Microsoft eShopOnContainers evidence for one broad-architecture request and one sequence request. Both output sets were independently type/safety checked and opened offline in a browser. The paired skill specifications already contain eShop-specific expectations, so this fixture is benchmark-contaminated and cannot serve as hidden confirmatory evidence. Three-run variance testing and the unseen/renamed matrix in `blind-protocol.md` are required before treating these results as general.

## Directional result

| Request | Directional winner | Why |
|---|---|---|
| Broad architecture | `mermaid-diagrams` + `show-me` on semantic accuracy and first-pass readability; `build-signal-graph` + `render-signal-graph` on rendering and interaction | Mermaid avoided unsupported payment-failure details and produced a readable boundary/relationship review. Signal produced a real offline interactive graph and typed model, but introduced unsupported contracts/outcomes and its 50-edge overview was visually congested. |
| Sequence | `mermaid-diagrams` + `show-me` | Its authoritative source is a `sequenceDiagram` with ordered calls, returns, shared work, and outcome branches. Signal's final artifact remained an interactive topology canvas, not the requested sequence view. |

### Reversed-order reviewer check

Two independent model reviewers saw anonymous A/B outputs in opposite presentation orders. Both selected Mermaid/Show Me for the broad case and both selected it for the sequence case. Under the superseded pilot rubric, Mermaid/Show Me scored 79.8–87.2 on broad architecture versus Signal/render's 58.3–59.9, and 87.2–89.5 on sequence versus Signal/render's 58.4–67.2.

This reduces concern about simple A/B position bias, but it is not a final blind benchmark: only two model judges reviewed one generated artifact per pair, the fixture is contaminated, the old rubric did not separate projection fidelity, and several disputed fixture expectations affected reviewer reasoning. Raw results and coordinator notes are preserved in [`pilot/reviewer-results/`](pilot/reviewer-results/).

## Findings by pair

### `build-signal-graph` + `render-signal-graph`

Strengths:

- Both TypeScript models pass strict `tsc` checking.
- The renderer test suite passes.
- Both generated HTML artifacts are self-contained and work with browser offline mode.
- The broad artifact contains 13 stable component boxes, 50 directional interactions, and four selectable end-to-end paths.
- Keyboard selection exposes path choices and preserves unrelated architecture while highlighting a path.
- The browser accessibility audit found no definite violations in the Signal broad artifact, though color contrast on overlapped SVG labels was indeterminate.

Accuracy and usefulness problems:

- The broad model invents `OrderPaymentFailedIntegrationEvent`, `OrderStatusChangedToCancelledIntegrationEvent`, payment-failure cancellation persistence, and cancellation notifications. The fixture requires a payment-failure variant but explicitly supplies none of those details.
- Its validation record says `architecture.json` was serialized from the compiled root architecture. That conflicts with `render-signal-graph`'s explicit rule to type-check but not execute the compiled model; the sequence run instead used a data-only projector that did not import the model.
- It also gives exact names to Catalog stock-result contracts that the fixture does not supply.
- Its payment-failure flow `continuesFrom: [SuccessfulOrder]`; therefore the rendered path reads “asynchronous successful order → asynchronous payment failure” after the successful flow has already marked the order paid. This is a material causal error.
- It publishes `OrderStatusChangedToAwaitingValidationIntegrationEvent` from Ordering even though the selected fixture establishes consumption but does not expose that producer transition.
- The broad default view is difficult to read because many parallel labels converge around the event bus.
- Pointer clicking an SVG interaction failed in browser automation because the visible `<text>` overlapped the interaction target. Keyboard focus plus Enter worked, so keyboard behavior is better than pointer hit testing in this run.
- For the sequence request, the final artifact is still a component topology with selectable paths. It does not provide sequence lifelines or a directly legible top-to-bottom interaction order.
- The sequence model collapses Catalog's generic stock-confirmed result into `OrderStatusChangedToStockConfirmedIntegrationEvent` before Ordering changes state, reversing the evidenced distinction between Catalog's result and Ordering's later status publication.

### `mermaid-diagrams` + `show-me`

Strengths:

- The broad source correctly selects `flowchart LR`; the sequence source correctly selects `sequenceDiagram`.
- It preserves the exact evidenced `OrderPaymentSuccededIntegrationEvent` spelling.
- It keeps HTTP 202 before asynchronous order creation and completion.
- It leaves payment-failure contract/state details unresolved rather than inventing them.
- Broad source uses generic stock-confirmed/stock-rejected labels where exact Catalog result contracts are absent, then separately shows Ordering publishing `OrderStatusChangedToStockConfirmedIntegrationEvent`.
- Both HTML review artifacts are self-contained and work offline.
- The sequence source uses dashed delivery/return arrows and an `alt` block after shared processing.

Accuracy and usefulness problems:

- No installed Mermaid renderer was available, so neither `.mmd` source was renderer-validated. The HTML pages explicitly do **not** render Mermaid; they are hand-authored review summaries with embedded source.
- Consequently, the broad HTML is a set of ownership cards and a relationship table rather than the requested rendered topology, while the sequence HTML is a compact walkthrough rather than rendered lifelines.
- The sequence source invents Ordering as the producer of `OrderStatusChangedToAwaitingValidationIntegrationEvent`, even though the selected evidence only establishes its Catalog consumption.
- The broad Mermaid source models handlers/commands as separate nodes inside service ownership boundaries. This is readable, but a user seeking only runtime topology may consider it more detail than requested.
- The broad review HTML had one WCAG color-contrast violation affecting two explanatory paragraphs.

## Independent validation performed

- `node skills/render-signal-graph/tests/run-tests.js` — passed.
- Strict `tsc --noEmit` on both generated Signal models — passed.
- Static Mermaid safety scan — passed for both files.
- External HTTP(S) asset scan on Mermaid/Show Me HTML — passed.
- Offline browser reload, accessibility-tree capture, screenshots, error inspection, and accessibility audit — performed for all four HTML artifacts.
- No browser page errors were reported.

Exact commands are recorded in `pilot/independent-validation.txt`; browser evidence is under each output's `browser-review/` directory.

## What this pilot establishes

The pairs optimize for different outcomes:

- Signal/render is currently stronger when the user wants a type-checked reusable architecture model, offline interaction, and impact-path exploration.
- Mermaid/Show Me is currently stronger when the user asks for a specific conventional diagram type, especially a sequence diagram, and is more conservative with incomplete evidence in this pilot.

The final winner must be reported by requested view and use case, not only as one global score. Use `materials.md` for harness calibration, then run the unseen/renamed six-case confirmatory matrix in `blind-protocol.md` with three replicates, atomic fact sheets, and blinded task-based review.
