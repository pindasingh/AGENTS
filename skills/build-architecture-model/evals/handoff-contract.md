# Evaluation: validated model handoff

## Prompt

The agent has scanned two repositories and wants to hand `.architecture-model/model.json` to a downstream C4 mapper. One progress revision differs from its scan, one relationship points to a missing node, a source finding is an ad-hoc string, and `model.systemBoundaries` omits a candidate boundary present in `decisions.json`.

## Required outcome

- Treat the complete `.architecture-model/` directory as the handoff, not `model.json` alone.
- Fail validation on the revision mismatch, missing endpoint, invalid source-finding shape, and boundary-mirror mismatch.
- Reset the affected progress gates before repairing authoritative artifacts.
- Reconcile and re-read the corrected model before declaring it ready.
- Require syntax, structural, referential, and semantic validation.
- Require every model flow to have a matching complete flow-review progress entry and JSON/Markdown/ASCII projection validation.

## Fail conditions

- Declares the model valid because every file parses as JSON.
- Ignores cross-file references or progress revisions.
- Lets the mapper guess a missing endpoint or boundary.
- Rewrites evidence to make an invalid relationship appear valid.
- Hands off sequenced flows whose numbered Markdown or ASCII review differs from `model.json`.
