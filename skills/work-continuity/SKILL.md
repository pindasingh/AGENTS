---
name: work-continuity
description: Preserves and restores useful task state across context compaction, interruption, session resume, and multi-agent work by using a repository-local `.work/` checkpoint. Use proactively for substantive multi-step tasks likely to span a long context, whenever context usage nears compaction, after any compaction or suspected context loss, and when coordinating writable workers. Do not wait for the user to ask for a checkpoint, and never stop with partial work merely because context was compacted.
compatibility: Requires filesystem access; Git is optional.
---

# Work Continuity

Use `.work/` as the agent's repository-local working memory. It is a lightweight recovery aid, not a formal planning phase and not part of the product. Keep enough current state on disk that an agent with a compacted context can understand the assignment, verify reality, and continue.

## Start or adopt a checkpoint

For a substantive task that may span many steps or context windows:

1. Locate the repository root. Put `.work/` there rather than in a nested package.
2. Keep `.work/` untracked. Prefer the repository's local Git exclude file when `.work/` is not already ignored; do not change a product's shared `.gitignore` solely to accommodate agent scratch state.
3. Reuse the checkpoint that clearly matches the active task. Otherwise create `.work/<short-task-key>/state.md`. When only one task exists, `.work/state.md` is also acceptable.
4. Record the task definition, success criteria, constraints, current state, and exact next action before context-heavy work. Preserve important user wording where paraphrasing could lose a requirement.
5. Use the rest of that task directory freely for todos, findings, experiment output, review notes, and worker handoffs. Do not create ceremony that does not improve recovery.

Use [the state template](assets/state-template.md) as a prompt, not a rigid schema. Omit irrelevant sections and add useful ones.

## Keep it useful

Update the checkpoint when its absence would force meaningful rediscovery, especially:

- after a requirement, constraint, or success criterion changes;
- after an important discovery or decision;
- after a coherent implementation milestone;
- after tests, builds, reviews, or commands establish useful evidence;
- before broad exploration, large tool output, delegation, or another context-heavy operation;
- when context usage is approaching compaction;
- before an intentional session switch or handoff.

Capture present state, not a conversation transcript. Keep exact paths, symbols, commands, results, unresolved questions, and the next action. Replace stale statements rather than accumulating contradictory notes.

Do not put secrets, credentials, private personal data, large reproducible caches, dependencies, or the only copy of a required deliverable in `.work/`.

## Recover after context loss

After compaction, resume, interruption, or suspected loss of task context:

1. Do not stop or ask the user to repeat the assignment merely because context was compacted.
2. Inspect `.work/` and identify the active checkpoint whose task definition matches the current user request. Do not assume the newest directory belongs to this agent when concurrent tasks exist.
3. Read that checkpoint and any directly referenced notes.
4. Reconcile the notes with higher-authority and current evidence:
   - the user's latest request;
   - repository instructions;
   - `git status` and the current diff;
   - actual source files and test output.
5. Treat discrepancies as stale scratch state, repair the checkpoint, and continue from the first unverified action.
6. Continue until the normal completion condition or a concrete blocker is reached. Compaction itself is neither.

If no useful checkpoint exists, reconstruct the state from the surviving compaction summary, current files, Git evidence, and user request. Create a checkpoint before continuing a still-substantive task.

## Coordinate agents without collisions

The primary agent owns the canonical task checkpoint. Give each writable worker a separate path such as `.work/<task>/workers/<worker-key>.md` when its findings must survive compaction. Include that path in the delegated task rather than expecting workers to guess it.

Workers may read the canonical checkpoint but should update only their assigned note. If a writable worker was not assigned a path, it creates a uniquely named note under the matching task's `workers/` directory and never edits a candidate canonical checkpoint. The primary verifies worker output, folds durable conclusions into `state.md`, and remains responsible for integration.

Read-only workers cannot maintain repository checkpoints. They should continue from the compaction summary, re-read source evidence as needed, and return a concise evidence-backed handoff. The primary records anything that must persist.

## Finish

Before reporting completion:

1. Reconcile the checkpoint with the final diff and verification evidence.
2. Mark it `complete` or remove only the task-specific scratch files this agent owns.
3. Confirm `.work/` is not staged or included in the deliverable.
4. Report the completed result normally; do not expose internal scratch notes unless they are useful to the user.
