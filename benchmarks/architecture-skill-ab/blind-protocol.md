# Blind architecture skill A/B protocol

This protocol compares two complete candidate configurations, A and B. Each candidate is one skill or an ordered set of cooperating skills declared in the run configuration. Score only the candidates' end-to-end outputs; do not infer independent scores for skills inside a multi-skill candidate.

## Controlled generation

For every case and replicate:

1. Use the same pinned model/version, system instructions, evidence package, outcome-focused prompt, repository access, and tool policy.
2. Start each run in a fresh session and expose only the assigned candidate's skills.
3. Apply equal token, wall-time, and tool-call ceilings. A candidate does not receive extra completion budget because its native workflow requires more operations.
4. Run the configured number of replicates per candidate and case, varying seed where supported.
5. Pair results by case and replicate. Record completion, failures, callback-captured duration/tokens, tool calls, artifact bytes, validation logs, and native-viewer evidence immediately, but hide them from quality judges.
6. Treat a run as completed only when declared sources/artifacts exist and its execution, timing, native-validation, and viewer evidence validate against the configuration.
7. Report quality under the equal user-cost budget and quality among successfully completed artifacts.
8. Preserve the exact prompt, externally committed evidence manifest, candidate skill revisions, authoritative sources, final artifacts, and execution transcript or summary.

Confirmatory runs require at least three replicates. Calibration and historical-pilot configurations may use fewer but cannot produce a final winner.

## Gold fact sheets

Before running either candidate, two independent architects create and reconcile an ontology-neutral fact sheet for each fixture. Every atomic item has:

- stable fact ID;
- required, forbidden, or unresolved status;
- evidence citation;
- weight;
- acceptable equivalent renderings.

Facts cover identities and ownership, directed operations, contracts, order and causality, synchronous/asynchronous boundaries, branches, terminal outcomes, forbidden inventions, unresolved relationships, and requested-view requirements. Do not require a candidate's native ontology; score facts such as “Basket publishes event X to the bus,” not whether a message is represented as a node.

## Submission preparation and blinding

An evaluation coordinator:

1. renames submissions to random IDs unrelated to A/B or skill identity;
2. removes skill names, generation logs, validation claims, and identifying filesystem paths;
3. derives each judge/case/replicate presentation order independently from an externally committed random seed and records only anonymous submission IDs in judge evidence;
4. preserves native formats because judges can be candidate-blind but not realistically format-blind;
5. recruits at least three judges with mixed experience across the declared artifact formats;
6. records each judge's prior format experience and preference before scoring;
7. seals all judge-visible submission bytes and judge evidence to an externally preserved commitment before revealing the candidate map;
8. keeps the candidate map inaccessible to judges until all judgments are locked and the review commitment is preserved.

## Three assessment layers

### 1. Authoritative semantics

Inspect each candidate's declared authoritative sources. Score architecture correctness without considering visual polish. If a candidate declares no authoritative source distinct from its artifact, score the inspectable artifact as source and record that limitation rather than inventing a hidden representation.

### 2. Projection fidelity

Trace every declared projection from authoritative source to delivered artifact. Compare the visual or navigable artifact with its own source using the candidate's declared projection stages and native validation.

A fact absent from source and artifact is one semantic omission, not a second projection failure. A fact present in source but absent, reversed, merged, duplicated, or distorted in the artifact is a projection failure. Do not reward one technology simply for having more projection stages.

### 3. Native user experience

Exercise each final artifact in its documented native viewer under the same offline/network policy. Test all applicable paths and controls, keyboard and pointer behavior, desktop and narrow widths, source readability, and static fallback behavior. For source-rendered formats, use one pinned renderer/version declared before generation. If no compatible renderer is available, report the missing rendered experience as a candidate capability limitation rather than silently substituting a coordinator-authored visualization.

Do not reward interactivity, portability, type checking, or compactness unless the capability serves the requested task.

## Judge tasks

Give judges case-specific questions rather than asking only for visual preference:

- When does the caller receive its response?
- Which stores can this endpoint modify?
- Which consumers observe the event?
- What differs between success and rejection?
- Which claims are unresolved?

Use answer correctness and answer time in the usefulness score defined by `rubric.json`.

## Confirmatory architecture matrix

The default design uses six cases × two candidates × three replicates: **36 executor runs**.

| Case | Fixture characteristic | Requested view | Primary stress |
|---|---|---|---|
| P1 | Unseen service system with HTTP, stores, and messaging | Structural topology, explicitly not a timeline | Boundaries, ownership, direction |
| P2 | One operation with acceptance followed by asynchronous work | Ordered interaction view | Response timing, event order, branches |
| P3 | Topic fan-out to multiple subscriptions and terminal effects | “Show everything this endpoint can touch” | Complete impact/path projection |
| P4 | Parallel reads/writes between the same components and a broker loop | Compact architecture view | Identity reuse and parallel-edge fidelity |
| P5 | Partial and conflicting evidence with tempting plausible dependencies | Evidence-backed current-state view | Hallucination resistance and uncertainty |
| P6 | Same architecture requested as portable source-only and as offline interactive exploration | Explicit format constraints | Capability and request fit |

P1–P5 are neutral cases. Report P6 as a separate format-fit stratum rather than folding it uncritically into an overall winner.

The public samples in `materials.md` are calibration and fixture-construction material. Build confirmatory fixtures from unseen systems or deterministic renamed/structurally modified evidence packs. Exclude any fixture whose expected architecture appears in either candidate's skill instructions or examples.

## Analysis and decision

For every score dimension report:

- mean and median by candidate;
- paired per-case and per-replicate differences;
- win/tie/loss counts;
- completion and critical-error rates;
- duration, token, tool-call, and artifact-size distributions;
- 95% bootstrap confidence interval over paired differences;
- inter-rater agreement, preferably Krippendorff's alpha.

Declare an overall winner only when it wins consistently on at least four of five neutral cases, the paired confidence interval excludes the ±5-point practical-equivalence margin, and it does not have a materially higher critical-error rate. Otherwise report a capability profile by requested view and use case.
