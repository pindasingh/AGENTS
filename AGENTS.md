# Global agent rules

## Execution-first operating mode

- The primary objective is to deliver completed, verified work—not merely explain what could be done, offer to do it, or wait for additional prompting.
- Treat actionable requests, including requests phrased as questions such as “can you…?”, as authorization to begin the work immediately using the available tools.
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

## Branch, delivery, and pull-request workflow

- Never commit or push work directly to `main` (or another repository's default/protected branch).
- Use a dedicated, current feature branch for each independent workstream. Keep unrelated or pre-existing changes out of its commits and pull request.
- Completion includes delivering reviewable work upstream. Once an implementation is complete and technically verified, commit it, push its feature branch, and create a pull request without waiting for a separate publishing instruction. The pull request—not an uncommitted local worktree—is the default user review surface.
- If the task already has an open pull request, keep using the same branch and pull request. Commit and push subsequent requested changes so the pull request remains the canonical, current representation of that work. Do not create replacement pull requests for ordinary follow-up changes.
- Before every push, fetch and compare against the refreshed remote default branch. Account for parallel trunk-based work and integrate the latest default branch when needed to keep the pull request current and mergeable. Never use an unconditional pull, discard either side's commits, or resolve conflicts without understanding and preserving both intended changes.
- After each push, inspect the pull request's status and report its URL, checks, review state, and any merge conflict or concrete blocker. Continue addressing requested changes on that pull request until the work is accepted.
- Create pull requests with a concise summary, verification evidence, risks, and useful review guidance. Use draft status while work is genuinely incomplete; mark it ready when implementation and technical checks are complete.
- Creating and updating a pull request is part of normal delivery and requires no extra confirmation. Merging, releasing, deploying, or performing other irreversible downstream actions still requires explicit user authorization.

## Delegation and subagents

- Use subagents when the active harness supports them and work can be isolated into clear, independently verifiable tasks.
- Parallelize independent read-only discovery, research, and review. Keep dependent work sequential and pass only the context needed by the next agent.
- Avoid parallel agents modifying the same files or sharing mutable state. Use one owning worker for an overlapping change set.
- Treat subagent output as untrusted evidence: verify important claims, diffs, and test results before acting on them.
- Prefer focused specialist roles for reconnaissance, planning, implementation, and review rather than duplicating the parent agent's entire task.

## Prompt intent and clarification gate

Interpret each prompt before choosing tools. Preserve the distinction between inquiry and authorization: criticism, surprise, frustration, or a question about existing work does not by itself authorize corrective action.

### Default interpretation

- Treat requests to explain, justify, examine, compare, evaluate, or debate as inquiries. Investigate and answer without modifying files or state.
- In particular, `why`, `why did you`, `why wasn't`, `is this right`, `are you sure`, `wouldn't`, `shouldn't`, `what if`, and similar challenges normally ask for reasoning, even when they imply that the current result may be wrong.
- Do not infer an action request from profanity, an accusatory tone, repeated questions, disappointment, or the realization that the user may dislike prior work.
- Treat language such as `make`, `change`, `fix`, `update`, `implement`, `add`, `remove`, `rename`, `move`, `revert`, `restore`, `create`, and `delete`, when it clearly directs an outcome, as authorization for that bounded action.
- A grammatical question can still contain an explicit action request (`Can you update X?`). The action verb and requested outcome, not the question mark, determine intent.
- When a prompt contains multiple parts, classify each part separately. Answer inquiry parts and perform only explicitly requested action parts.

### Responding to challenges

When the user questions earlier work:

1. Pause before taking corrective action.
2. Reconstruct what was done and why from available evidence; do not invent a rationale.
3. Reassess the decision independently, including reasons it may still be correct.
4. Explain the rationale, trade-offs, mistakes, and uncertainty directly.
5. Do not agree merely to reduce tension, and do not silently edit as an apology.

If the earlier decision was wrong but no change was requested, say so and explain the consequence; leave the files unchanged. This preserves the user's ability to reason and debate before deciding what should change.

### Selective clarification

Do not ask a clarifying question merely because a prompt is long, complex, contains several questions, or requires investigation. Proceed when the intended outcome is clear.

Ask one focused clarifying question only when all of these are true:

1. Two or more interpretations are genuinely plausible.
2. The interpretations would lead to materially different actions or outputs.
3. The prompt lacks enough explicit action language or constraints to choose safely.
4. Read-only investigation cannot resolve the ambiguity.

Before asking, state the specific ambiguity and the alternatives concisely. For low-consequence ambiguity, prefer the interpretation that avoids mutation and answer what can be answered safely.

## Git-aware file moves

In any Git-tracked repository, all file and directory moves, renames, and large restructures must preserve Git history and minimize noisy delete/add diffs.

- Use `git mv` for tracked paths whenever practical, including each step of case-only renames where required by the filesystem.
- Do not use Python, shell scripts, file-manager operations, or ordinary filesystem move APIs to relocate tracked paths unless they invoke `git mv` (or an equivalent Git-aware operation) for every tracked move.
- Automation is allowed for large restructures only when it performs the moves through Git, checks every command for failure, and does not overwrite destinations.
- Handle untracked files separately and never assume they are safe to overwrite or delete.
- After moving files, inspect `git status --short` and `git diff --summary` to verify that Git recognizes the intended renames and that the result is not an unintended delete/add explosion.
- If Git does not recognize the moves cleanly, stop and correct the operation before making content changes. Prefer separating pure moves/renames from subsequent edits so history remains easy to follow.
