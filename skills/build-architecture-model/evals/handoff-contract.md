# Evaluation: validated sharded model handoff

## Prompt

The agent has scanned two repositories and wants to hand only `index.json` to a downstream mapper. One progress revision differs from its scan, one relationship points to a missing node, a component-operation reference is not reciprocal, a source finding is an ad-hoc string, one path has an extra participant, and its ASCII arrow differs from deterministic rendering.

## Required outcome

- Treat the complete `.architecture-model/` directory as the handoff; `index.json` is a navigation manifest, not the architecture payload.
- Fail validation on revision mismatch, missing endpoint, non-reciprocal hierarchy, invalid source finding, incorrect participant set, and projection drift.
- Reset affected progress/path-review gates before repairing canonical artifacts.
- Repair source observations or graph/path shards, never generated projections as architecture authority.
- Run format, render, index, and final validation before handoff.
- Give the human direct links to the domain, affected components, operation/path, numbered view, ASCII view, and classified change report.

## Fail conditions

- Declares the model valid because JSON parses or `index.json` exists.
- Copies detailed architecture records into the index.
- Ignores cross-file references, reciprocal links, progress revisions, or relationship direction.
- Lets a downstream mapper guess missing endpoints or path order.
- Changes the canonical path merely to agree with a tampered projection.
- Hands off without a complete deterministic projection pair for every path.
