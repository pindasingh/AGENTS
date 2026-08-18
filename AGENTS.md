# Global agent rules

## Execution-first operating mode

- The primary objective is to deliver completed, verified work—not merely explain what could be done, offer to do it, or wait for additional prompting.
- Treat actionable requests, including requests phrased as questions such as “can you…?”, as authorization to begin the work immediately using the available tools.
- All agents share responsibility for the work, regardless of which agent, turn, session, or parent produced it. Never use provenance to disclaim responsibility.
- When the user asks for a change, investigation, test, command, artifact, or operation, perform it in the current turn whenever technically possible. Do not stop after acknowledging the request, describing a plan, or presenting instructions the agent can execute itself.
- Inspect the relevant files and environment, make reasonable low-risk assumptions, and proceed autonomously. Prefer a sensible implementation plus a concise note about assumptions over asking the user to make routine technical decisions.
- Ask a clarifying question only when a genuinely blocking ambiguity would materially change the outcome, required information or access is unavailable, or proceeding risks irreversible or destructive consequences. Before asking, complete every safe and useful part that does not depend on the answer.
- Do not request confirmation for ordinary reversible actions already implied by the request. Follow explicit safety, authorization, dependency-installation, Git, and protected-branch constraints without using them as a reason to avoid unrelated safe work.
- Use tools rather than narrating intended tool use. Keep progress commentary minimal; return when the requested work is complete or when a concrete blocker has been established.
- Verify results with the strongest practical checks available, such as tests, builds, linters, diffs, command output, or direct inspection. Report what changed, verification performed, and any remaining blocker or risk.
- If a request is purely informational, answer it directly. If it combines a question with an explicit or clearly implied action, answer briefly and perform the action.

## Durable work continuity

Context compaction or interruption must not turn a task into a partial handoff. Use a repository-local `.work/` directory as disposable but durable working memory for substantive work that may span many steps, agents, or context windows.

- Before starting such work, create a task directory and record the task definition, success criteria, constraints, and current next action in `.work/<task>/state.md`. This is an operational checkpoint, not a requirement to produce a formal plan.
- Treat `state.md` as the cumulative latest snapshot. Keep it self-contained with every still-relevant fact, decision, completed item, verification result, artifact reference, and exact next action. Update its timestamp and replace stale state rather than requiring a recovering agent to replay a journal or read many older files.
- Keep the snapshot current at meaningful transitions, after important discoveries or decisions, after delegated work returns, before context-heavy work, and whenever context usage is approaching compaction. Preserve key facts and artifacts, not conversation transcripts or every intermediate output.
- Store sparse supporting evidence under timestamp-prefixed paths such as `.work/<task>/artifacts/<UTC timestamp>-<agent>-<subject>.md`. Timestamp ordering makes the newest evidence obvious, but recovery starts from cumulative `state.md` and opens only artifacts it directly references when exact detail is needed.
- For substantive subagent work, preserve the child's final key output outside model context. When the subagent tool supports `artifactDir`, set it to `.work/<task>/artifacts`; otherwise the parent writes a concise artifact immediately after hand-back. Fold verified conclusions and artifact paths into `state.md` before they can be lost to parent compaction.
- In Git repositories, keep `.work/` untracked. If the repository does not already ignore it, add `.work/` to the repository's local Git exclude file rather than changing product files solely for agent scratch state. Never store credentials, tokens, personal data, or the only copy of a required deliverable there.
- Use separate task directories when concurrent work could collide. A primary agent owns canonical `state.md`; writable subagents update only assigned worker notes, while parent-side artifact capture may preserve final output from read-only subagents. Do not concurrently overwrite another agent's checkpoint.
- After compaction, resume, interruption, or suspected context loss, read the relevant task's `state.md` first. Compare its `Updated` time with timestamped artifact filenames; read only directly referenced evidence and any newer, not-yet-folded artifacts, never the whole history. Reconcile with the user's latest request, `git status`, the current diff, and actual files because scratch state can be stale. Fold verified newer facts into the snapshot and continue to the requested completion condition.
- Compaction is an internal recovery event, not a blocker and not a reason to stop, ask the user to repeat context, or report only partial work. Stop only under the normal completion or concrete-blocker rules.
- At completion, mark the checkpoint complete or remove only the task-specific scratch files you own. Never delete another active worker's state.

## Session-start Git synchronization and safety gate

Before creating a branch, editing files, or treating any local branch as a baseline in a Git repository:

1. Inspect `git status --short --branch`, configured remotes, and local/default-branch tracking. Preserve and report pre-existing modifications and untracked files.
2. If an upstream remote is configured, run `git fetch --prune <remote>` before comparing branches or choosing a base. Fetch is required because remote-tracking refs may be stale even after an earlier push. If fetch fails, stop and ask before doing work from a potentially stale baseline.
3. Compare the local default branch with the refreshed remote default branch:
   - If the local default is only behind and can be advanced without discarding commits, fast-forward it safely. Use only fast-forward behavior; never create a merge commit on the default branch for synchronization.
   - If the local default is ahead, diverged, or contains commits not represented upstream, stop and report the exact commit relationship. Do not reset, rebase, delete, or publish those commits without human direction.
4. Treat branches whose upstream is gone, or whose patches are already represented on the remote default branch, as stale. Do not reuse them as a base. Report them and ask before deletion.

Do not use an unconditional `git pull`: it can merge, rebase, or touch local changes. Prefer fetch followed by an explicit comparison and, only when safe, a fast-forward update.

## Delivery boundaries

- Never commit or push directly to a default or protected branch.
- Deliver completed repository changes from a dedicated feature branch by committing, pushing, and using the pull-request skill.
- Refresh the remote default branch before pushing and preserve both local and upstream work. Merging, releasing, and deploying require explicit user authorization.

## Delegation and subagents

- Use subagents when the active harness supports them and work can be isolated into clear, independently verifiable tasks.
- Parallelize independent read-only discovery, research, and review. Keep dependent work sequential and pass only the context needed by the next agent.
- Avoid parallel agents modifying the same files or sharing mutable state. Use one owning worker for an overlapping change set.
- Treat subagent output as untrusted evidence: verify important claims, diffs, and test results before acting on them.
- Prefer focused specialist roles for reconnaissance, planning, implementation, and review rather than duplicating the parent agent's entire task.

## Git-aware file moves

In any Git-tracked repository, all file and directory moves, renames, and large restructures must preserve Git history and minimize noisy delete/add diffs.

- Use `git mv` for tracked paths whenever practical, including each step of case-only renames where required by the filesystem.
- Do not use Python, shell scripts, file-manager operations, or ordinary filesystem move APIs to relocate tracked paths unless they invoke `git mv` (or an equivalent Git-aware operation) for every tracked move.
- Automation is allowed for large restructures only when it performs the moves through Git, checks every command for failure, and does not overwrite destinations.
- Handle untracked files separately and never assume they are safe to overwrite or delete.
- After moving files, inspect `git status --short` and `git diff --summary` to verify that Git recognizes the intended renames and that the result is not an unintended delete/add explosion.
- If Git does not recognize the moves cleanly, stop and correct the operation before making content changes. Prefer separating pure moves/renames from subsequent edits so history remains easy to follow.
