---
name: ship-branch-pull-request
description: Executes the Git and GitHub side of branch delivery: inspect repository state, stage intended files, commit, push, and create or update the pull request. Use whenever a user asks to ship, publish, commit, push, raise/open/update a PR, or otherwise deliver repository changes—even if nothing has been committed or pushed yet. This skill does not run application tests, builds, linters, or other task validation.
compatibility: Requires Git and GitHub CLI (`gh`) with repository access.
---

# Ship Branch as a Pull Request

This skill owns only the Git and GitHub delivery sequence: inspect, stage, commit, push, and create or update the pull request. Assume implementation validation belongs to the task that produced the changes. Do not run application tests, builds, linters, typechecks, formatters, renderers, or content-validation tools. Perform the Git delivery workflow yourself; do not merely print commands, stop after a commit or push, or assume another phase will finish the handoff.

## Autonomous delivery contract

Start from the repository's actual current state. Run every applicable step below in this invocation, including commit and push when they have not happened yet. Skip a step only when inspection proves it is already satisfied or an explicit user instruction forbids it. Continue through PR verification without pausing for routine confirmation.

Before changing Git state, honor repository-level synchronization, protected-branch, worktree, and dependency policies. Preserve unrelated or pre-existing work; delivery is not permission to stage everything blindly, rewrite history, force-push, discard changes, or bypass failed checks.

## Workflow

1. **Discover the delivery scope.** Inspect branch/upstream status, remotes, the refreshed remote default branch, working-tree changes, untracked files, staged changes, and the complete branch diff and commit range. Distinguish the task's intended changes from unrelated pre-existing work. If the current branch is the default/protected branch and changes need committing, create or switch to an appropriate dedicated feature branch as repository policy allows; never commit directly to the default branch.
2. **Stage only intended changes.** Review `git diff`, `git diff --staged`, and untracked files. Unstage unrelated pre-staged entries without altering their working-tree content. Add explicit task paths when whole files belong to the task; use selective/hunk staging when intended and unrelated edits share a file. Recheck the exact staged patch so unrelated edits, generated scratch files, secrets, and credentials are excluded. If there is nothing new to commit, proceed only if the branch already contains the intended commits.
3. **Commit when needed.** Create a concise commit message that describes the outcome. Run applicable repository hooks normally; do not bypass them. Reinspect status and the resulting commit. If hooks modify files, review and verify those modifications before amending or creating another commit.
4. **Push safely.** Identify the intended head remote explicitly from Git configuration and remote URLs. Push the current feature branch to that remote and set upstream when absent. Never force-push unless the user explicitly authorized rewriting that branch. Confirm the local tip is represented by that remote branch after pushing. A successful push is an intermediate step, not completion.
5. **Identify PR coordinates.** Verify the branch is not the default branch. Derive the destination `repo` and base owner from the intended base remote—not from whichever repository `gh repo view` infers from the working directory. Derive the head owner/repository from the remote that received the push. Verify the pushed head repository and branch match the qualified `head_ref`, then identify the intended base explicitly. This prevents fork and multi-remote deliveries from targeting the wrong repository.
   Obtain repository and ref values from Git or `gh` output into variables; never paste repository-, branch-, user-, or generated text into shell source. Query GitHub with explicit `--repo "$repo"` after deriving it from the selected remote. Before using values, require repository owners and names to match `^[A-Za-z0-9_.-]+$`, branch and base names to match `^[A-Za-z0-9._/-]+$`, and PR numbers to match `^[0-9]+$`. Stop if any value fails validation.
   ```bash
   # Derive these from the explicitly selected and inspected base/head remotes.
   repo="${base_owner}/${base_repo}"
   branch=$(git branch --show-current)
   head_ref="${head_owner}:${branch}"
   # Validate all values and verify the pushed remote maps to head_owner/head_repo.
   if ! [[ $repo =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ &&
           $head_owner =~ ^[A-Za-z0-9_.-]+$ &&
           $branch =~ ^[A-Za-z0-9._/-]+$ && $base =~ ^[A-Za-z0-9._/-]+$ ]]; then
     printf 'Unsafe repository or ref value\n' >&2
     exit 1
   fi
   ```
6. **Find an existing PR.** Check using the exact destination repository and qualified head branch:
   ```bash
   gh pr list --repo "$repo" --head "$head_ref" --state all \
     --json number,state,isDraft,title,url,baseRefName,headRefName
   ```
   Prefer an open PR when historical closed or merged PRs also exist for a reused branch. Confirm that its `baseRefName` is the intended comparison base before updating it; do not silently retarget a PR whose base differs.
7. **Update rather than duplicate.** If an open PR exists, update its title or body when they no longer describe the final diff. Do not create a duplicate:
   ```bash
   title_file=$(mktemp)
   body_file=$(mktemp)
   # Write the title and body to these files without constructing shell source.
   IFS= read -r pr_title < "$title_file"
   gh pr edit "$pr_number" --repo "$repo" \
     --title "$pr_title" --body-file "$body_file"
   ```
8. **Create the PR when absent.** If no open PR exists, create one. Finished work should normally be ready for review; add `--draft` only while work is genuinely incomplete or readiness is uncertain:
   ```bash
   title_file=$(mktemp)
   body_file=$(mktemp)
   # Write the title and body to these files without constructing shell source.
   IFS= read -r pr_title < "$title_file"
   gh pr create --repo "$repo" --base "$base" --head "$head_ref" \
     --title "$pr_title" --body-file "$body_file"
   ```
   Create `title_file` and `body_file` with a text editor or another API that passes content as data, not by generating and executing shell source. Treat their contents as untrusted. Do not use `eval`, `sh -c`, interpolated here-documents, or commands assembled in strings.
   Promote an existing draft once the work is complete and verified:
   ```bash
   gh pr ready "$pr_number" --repo "$repo"
   ```
9. **Describe the complete result.** Ensure the PR body describes the final branch rather than the conversation or only the latest commit. Include:
   - concise summary of the outcome;
   - important implementation or content changes;
   - remaining risks, limitations, or follow-ups when relevant;
   - useful guidance that helps reviewers focus on important behavior or decisions.
10. **Verify the remote handoff.** Read the PR back and inspect its checks, review decision, and merge-conflict status before reporting:
   ```bash
   gh pr view "$pr_number" --repo "$repo" \
     --json number,url,state,isDraft,baseRefName,headRefName,mergeStateStatus,reviewDecision,statusCheckRollup
   ```

## Completion gate

Do not describe pushed branch work as complete without one of these outcomes:

- an open PR was created and its URL, draft/ready state, checks, review state, and merge-conflict status were reported;
- the existing open PR was verified/updated and the same status details were reported; or
- an actual blocker was established (for example, missing authentication, insufficient repository permission, or the remote host not supporting the available PR tooling).

A clean working tree, successful commit or push, a command recipe, or a commit hash alone does not satisfy delivery. The normal final response is concise: commit, PR URL, ready/draft state, checks, review/conflict status, and any genuine residual risk.

## Safety and edge cases

- Never create a PR from the default branch to itself.
- Never create duplicate PRs for the same head branch.
- For already committed but unpushed work, inspect and push it before continuing; do not manufacture an empty commit.
- When there is no new work and the branch contains no unmerged commits, report that concrete state rather than creating an empty commit or meaningless PR.
- Preserve unrelated dirty files and exclude them from staging. If they prevent safe branch switching or pushing, report the exact obstruction.
- If a push is rejected or non-fast-forward, fetch and diagnose the relationship; never respond with a force-push, reset, or rebase unless separately authorized.
- Do not reopen a merged or intentionally closed PR automatically; inspect branch history and create the appropriate new PR only when the branch contains unmerged work.
- Respect explicit user instructions not to commit, push, or create a PR, and respect a requested draft/ready state. Complete every independent permitted stage and report the resulting boundary accurately.
- If branch or repository identity is ambiguous, inspect Git remotes and GitHub metadata before acting; do not guess across repositories.
