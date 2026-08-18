# Architecture skill A/B runbook

Use this runbook only when an operator explicitly requests a benchmark. It is not an invocation contract and is not loaded as an Agent Skill.

## 1. Configure and preflight

1. Create a run configuration conforming to `benchmark-config.schema.json`.
2. Treat each candidate as an indivisible end-to-end configuration, even when it contains multiple skills.
3. Pin candidate skill revisions, model/version, system/tool-policy digests, evidence revisions, prompts, native viewer command/checks, renderers, validation commands, budgets, and seed policy. Every confirmatory candidate needs at least one native validation command.
4. Run `scripts/validate_config.py`. Confirmatory mode fails preflight unless it has at least three replicates, three judges, two gold adjudicators, all fairness controls enabled, equal non-null budgets, and only confirmation-eligible cases.
5. Run `scripts/prepare_runs.py` into a new empty directory. Never overwrite a prior run. Preserve the printed `PREPARATION_COMMITMENT` in an external record that cannot be rewritten with the run directory; it binds the configuration, candidate/evidence/gold/rubric manifest, run plan, random submission map, and review-seed commitment.

## 2. Build gold before generation

Two architects independently derive ontology-neutral atomic facts from each fixed evidence pack, then reconcile disagreements. Mark each fact required, forbidden, or unresolved and cite exact evidence. Freeze and hash the fact sheet before candidate execution.

Do not expose gold sheets or prior candidate outputs to executors.

## 3. Execute paired runs

For each case and replicate, launch candidate A and B together so scheduling conditions are comparable:

- fresh session for every run;
- only the assigned candidate's skills available;
- identical prompt, evidence, model, system instructions, repository access, and tool policy;
- output restricted to that run's `outputs/` directory;
- equal completion budgets.

Do not let one candidate inspect the other's outputs. Preserve authoritative sources and final artifacts matching the candidate's declared patterns. For every completed confirmatory run, also preserve `execution.json`, callback-captured `timing.json`, `validation.json`, command logs, and native-viewer/browser evidence conforming to `run-evidence.schema.json`. A score's completion flag is not accepted without those files and matching metrics.

## 4. Capture metrics immediately

Subagent completion callbacks may be the only source of token and duration data. On every completion, immediately write `timing.json` in the run directory with tokens, duration, start/end when available, completion state, and budget exhaustion. Record tool calls and output bytes separately. Missing metrics stay missing; never reconstruct or impute them.

## 5. Validate native outputs

Run every candidate's predeclared validation command with already-available tooling and preserve a hashed command log. Execute the predeclared viewer command over every delivered artifact, preserve its hashed log, and record exactly the predeclared checks (for example open, offline, interaction, accessibility, or narrow width). Confirmatory aggregation rejects empty validation lists, missing artifact paths/logs, budget overruns, or `budget_exhausted: true`. Record missing tooling as a candidate capability/delivery limitation, not a coordinator repair opportunity.

## 6. Grade three layers

1. **Semantics:** compare declared authoritative sources with atomic gold facts.
2. **Projection:** compare final artifacts with their own authoritative sources.
3. **Usefulness:** have judges answer case questions from the delivered artifact; capture correctness and answer time.

Apply `rubric.json`. Unsupported inventions cost more than omissions through precision, forbidden facts, and critical-error reporting. Never double-penalize a fact absent from both source and artifact.

## 7. Blind review

Preparation creates sealed random submission IDs in `coordinator/candidate-map.json`. The coordinator copies judge-visible artifacts into those submission directories, strips candidate identities and generation claims, and independently randomizes order per judge. Preserve native formats. Lock all judgments before revealing the candidate map.

Use at least three judges for confirmatory work and record format experience before review. Save raw judgments by anonymous submission ID, presentation position, answer correctness, answer time, and usefulness points in `coordinator/judge-evidence.json` conforming to `judge-evidence.schema.json`. Reveal the prepared randomization seed in that evidence; presentation order is reconstructed independently with HMAC-SHA256 for every judge/case/replicate.

Before revealing the candidate map, run:

```sh
python benchmarks/architecture-skill-ab/scripts/seal_review.py <run-directory>
```

Preserve the printed `REVIEW_COMMITMENT` externally. It binds locked judge evidence and every judge-visible submission byte. Only then reveal the map and write `coordinator/unblinding.json` with a timezone-qualified `candidate_map_revealed_at`. Aggregation verifies both external commitments, all content hashes, ordering, timestamps, submission/artifact equality, and each run's usefulness score against the judge mean.

## 8. Aggregate and decide

Write one `score.json` conforming to `run-score.schema.json` in every replicate directory, then run:

```sh
python benchmarks/architecture-skill-ab/scripts/aggregate_results.py \
  <config.json> <run-directory> \
  --preparation-commitment <externally-preserved-sha256> \
  --review-commitment <externally-preserved-sha256>
```

The dependency-free aggregator rejects missing/mismatched runs, changed input manifests, tampered plans/maps, malformed score totals, and incomplete judge evidence. It preserves candidate labels rather than identities, computes paired dimensions, per-family/view macro profiles, judge task statistics, interval agreement, and a deterministic bootstrap interval. It refuses to declare a winner unless every planned run completed and all confirmatory guards pass.

Pair candidate results by case and replicate. Report:

- all rubric dimensions, mean/median, and paired deltas;
- per-family and per-view win/tie/loss profiles;
- completion, critical errors, validation failures, duration, tokens, calls, and bytes;
- judge agreement and 95% paired bootstrap intervals;
- neutral cases separately from format-fit and breadth strata.

Apply the decision rule verbatim. If consistency, confidence, or critical-error guards fail, report no overall winner and give the capability profile instead.

## 9. Preserve the run

Keep configuration, config hash, run plan, evidence manifest, gold sheets, prompts, skill/model revisions, raw outputs, validation, metrics, judgments, aggregate JSON/Markdown, and static review artifact. Mark calibration, contaminated, incomplete, or historical runs prominently so they cannot be mistaken for confirmatory evidence.
