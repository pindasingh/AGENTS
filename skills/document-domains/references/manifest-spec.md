# Domain manifest specification

## Purpose

Use domain-manifest.json as the canonical, versionable record. Keep presentation out of the data. Prefer explicit empty arrays so agents can distinguish checked-and-empty from malformed output.

Use schema_version 2.1 and these top-level fields:

- document: id, title, domain, revision, generated_at, summary, and source_trust.

Use ISO 8601 timestamps. Use evidence paths relative to a source root.



## Source roots and evidence

A source root requires id, path, label, scan_status, and notes. For Git roots also record remote, branch, commit, fetch_status, and working_tree_divergence. Evaluate main or master and store the exact commit SHA. Use scan_status complete, partial, blocked, or not-started. Complete means the supplied root was inspected; it does not mean the system is complete.

Evidence requires id, root_id, path, and observation. Add line_start, line_end, symbol, and source_kind when available. Use source_kind such as implementation, configuration, contract, test, documentation, schema, or reconstructed-source.

Use evidence reliability direct, partial, ambiguous, or conflicting. Use freshness current, stale, or unknown. Reliability describes the artifact observation, not deployment or runtime truth.

Use claim certainty observed, corroborated, inferred, unknown, or contradictory. Evidence reliability and claim certainty are separate.



A connection requires id, from_ref, to_ref, mechanism, contract, certainty, rationale, and evidence_ids. The references normally identify components, operations, or interaction steps.

Each step requires id, sequence, kind, action, certainty, evidence_ids, and next_step_ids. Add component_id, state_changes, input, output, and notes when applicable. Preserve branches in next_step_ids; do not rely only on sequence. An inferred or unknown step must explain its reasoning or reference a gap.

Outcomes and failure paths require name, description, certainty, and evidence_ids. A failure may add from_step_id. State changes can be strings or objects containing entity, from, to, and description.



## Coverage, gaps, and conflicts

Coverage requires included_patterns, excluded_paths, limitations, and search_log. An exclusion records path and reason.

A gap requires id, scope_ref, kind, description, impact, searches, and status. Record the concrete searches behind a negative finding.

A conflict requires id, scope_ref, claim, observations, impact, and status. Each observation has value and evidence_ids. Never collapse disagreeing snapshots into one claim.

## Hydration

Rebuild findings from every supplied root before comparing with the prior manifest. Increment document.revision, preserve stable IDs, and update evidence freshness.

Record each material change with kind, ref, summary, and evidence_ids. Use kind added, changed, removed, stale, or resolved.

Do not delete an unresolved gap or conflict merely because refresh did not rediscover its evidence. Mark it stale or explain its evidence-backed resolution.
