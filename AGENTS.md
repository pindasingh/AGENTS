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
