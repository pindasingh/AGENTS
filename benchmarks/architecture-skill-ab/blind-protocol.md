# Blind head-to-head protocol

This protocol compares complete configurations, never individual skills:

- `build-signal-graph` → `render-signal-graph`
- `mermaid-diagrams` → `show-me`

## Controlled generation

For every case and replicate:

1. Use the same model/version, system instructions, evidence package, user prompt, and read-only repository/tool access.
2. Start each run in a fresh session and expose only the assigned pair.
3. Apply equal token, wall-time, and tool-call ceilings. Signal compilation and HTML generation do not receive an unlimited completion budget merely because they require more operations.
4. Run three replicates per pair and case, varying seed where supported.
5. Pair results by case and replicate. Record completion, failures, time, tokens, and tool calls, but hide those data from quality judges.
6. Report both quality under the equal user-cost budget and quality among successfully completed artifacts.

## Gold fact sheets

Before running either pair, two independent architects create and reconcile an ontology-neutral fact sheet for each fixture. Every atomic item has:

- stable fact ID;
- required, forbidden, or unresolved status;
- evidence citation;
- weight;
- acceptable equivalent renderings.

Facts cover identities and ownership, directed operations, contracts, order and causality, synchronous/asynchronous boundaries, branches, terminal outcomes, forbidden inventions, unresolved relationships, and requested-view requirements. Do not require either pair's native ontology; score facts such as “Basket publishes event X to the bus,” not whether a message is represented as a node.

## Submission preparation and blinding

An evaluation coordinator:

1. renames submissions to random IDs;
2. removes skill names, generation logs, validation claims, and identifying filesystem paths;
3. randomizes A/B presentation independently for every judge;
4. preserves native formats because judges can be configuration-blind but not realistically format-blind;
5. recruits at least three judges with mixed Mermaid and HTML experience;
6. records each judge's prior format experience and preference before scoring.

## Three assessment layers

### 1. Authoritative semantics

Inspect `architecture.ts` for Signal and Mermaid source for Mermaid/Show Me. Score architecture correctness without considering visual polish.

### 2. Projection fidelity

Compare each visual with its own authoritative source:

- Signal TypeScript → data-only JSON → interactive HTML;
- Mermaid source → one pinned already-available Mermaid renderer;
- direct Show Me HTML → its inspectable visual structure or embedded data.

A fact absent from source and visual is one semantic omission, not a second projection failure. A fact present in source but absent or distorted visually is a projection failure.

### 3. Native user experience

- Exercise HTML live in a browser, including every path, pointer and keyboard use, desktop width, and narrow width.
- Inspect Mermaid both as source and through the same pinned renderer.
- Show text/code-shape outputs in a standardized monospaced viewer.

Do not reward HTML merely for interactivity or Mermaid merely for portability unless that capability serves the request.

## Judge tasks

Give judges case-specific questions rather than asking only for visual preference:

- When does the caller receive its response?
- Which stores can this endpoint modify?
- Which consumers observe the event?
- What differs between success and rejection?
- Which claims are unresolved?

Use answer correctness and answer time in the usefulness score defined by `rubric.json`.

## Confirmatory pilot matrix

Use six cases × two pairs × three replicates: **36 executor runs**.

| Case | Fixture characteristic | Requested view | Primary stress |
|---|---|---|---|
| P1 | Unseen service system with HTTP, stores, and messaging | Structural topology, explicitly not a timeline | Boundaries, ownership, direction |
| P2 | One operation with acceptance followed by asynchronous work | Ordered interaction view | Response timing, event order, branches |
| P3 | Topic fan-out to multiple subscriptions and terminal effects | “Show everything this endpoint can touch” | Complete impact/path projection |
| P4 | Parallel reads/writes between the same components and a broker loop | Compact architecture view | Identity reuse and parallel-edge fidelity |
| P5 | Partial and conflicting evidence with tempting plausible dependencies | Evidence-backed current-state view | Hallucination resistance and uncertainty |
| P6 | Same architecture requested as portable source-only and as offline interactive exploration | Explicit format constraints | Capability and request fit |

P1–P5 are neutral cases. Report P6 as a separate format-fit stratum rather than folding it uncritically into an overall winner.

The public samples in `materials.md` are calibration and fixture-construction material. Existing eShop expectations are already embedded in both skill specifications, so eShop is not a hidden confirmatory case. Build confirmatory fixtures from unseen systems or deterministic renamed/structurally modified evidence packs.

## Analysis

For every score dimension report:

- mean and median by pair;
- paired per-case and per-replicate differences;
- win/tie/loss counts;
- completion and critical-error rates;
- time, token, and tool-call distributions;
- 95% bootstrap confidence interval over paired differences;
- inter-rater agreement, preferably Krippendorff's alpha.

Declare an overall winner only when it wins consistently on at least four of five neutral cases, the paired confidence interval excludes the ±5-point practical-equivalence margin, and it does not have a materially higher critical-error rate. Otherwise report a capability profile by requested view and use case.
