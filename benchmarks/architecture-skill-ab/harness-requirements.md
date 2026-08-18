# Harness completion requirements

A run is complete only when every applicable item is preserved or explicitly marked unavailable.

## Configuration

- [ ] Exactly two candidates, A and B, each with one or more existing skill paths
- [ ] Fixed model/version, system-instruction digest, tool-policy digest, evidence revisions, prompt, and budgets
- [ ] Candidate-native authoritative sources, artifacts, viewer command/checks, and at least one confirmatory validation command declared before execution
- [ ] Architecture family, requested view, and confirmation eligibility recorded per case
- [ ] Printed preparation commitment is preserved outside the mutable run directory

## Evidence and gold

- [ ] Compact immutable evidence packs with attribution
- [ ] Atomic required, forbidden, and unresolved facts with citations and weights
- [ ] Two independent gold authors and reconciled sheet for confirmatory cases
- [ ] Famous-sample contamination and candidate-instruction overlap checked

## Execution

- [ ] Fresh isolated session per run with only assigned candidate skills
- [ ] A/B launched under equivalent scheduling conditions
- [ ] Three replicates per candidate/case for confirmatory work
- [ ] Tokens, duration, tool calls, completion, errors, and artifact bytes captured and within configured budgets
- [ ] Declared sources/artifacts plus execution, callback timing, validation logs, native-viewer evidence, and uncertainties preserved

## Assessment

- [ ] Native validation and viewer/browser checks completed
- [ ] Semantics, projection fidelity, view compliance, and usefulness scored separately
- [ ] Sealed random submission IDs and HMAC-reconstructable per-judge order
- [ ] At least three judges and prior format experience captured for confirmatory work
- [ ] Blinded submissions and `judge-evidence.json` are sealed before unblinding; the external review commitment is preserved
- [ ] `judge-evidence.json` validates, including lock/unblinding timestamps, task answer correctness, answer time, and judge usefulness points
- [ ] Critical errors and disputed facts adjudicated separately

## Reporting

- [ ] Paired per-case/replicate results and macro-averages by family/view
- [ ] Completion/cost distributions and successful-artifact quality both reported
- [ ] Inter-rater agreement and paired bootstrap confidence interval
- [ ] Format-fit and state/ER/class breadth excluded from neutral overall score
- [ ] Winner rule applied without relaxing thresholds after seeing results
- [ ] `score.json` exists for every planned run and pair-aware aggregation passes
- [ ] Static review artifact and machine-readable aggregate preserved
