---
name: ship-branch-pull-request
description: Runs the standard Git/GitHub commands that finish repository work: confirm the branch is current, stage and commit the intended changes, push, and create or update the pull request. Use for commit, push, ship, publish, or PR requests. Do not run tests, builds, linters, renderers, or other implementation checks.
compatibility: Requires Git and GitHub CLI (`gh`) with repository access.
---

# Ship Branch Pull Request

Run this workflow automatically. Do not explain the commands instead of running them, and do not pause between routine steps.

## Commands

1. Inspect the repository and refresh remote state:
   ```bash
   git status --short --branch
   git remote -v
   git fetch --prune origin
   git branch --show-current
   git rev-list --left-right --count origin/HEAD...HEAD
   ```
2. Stop if the current branch is the default branch, is behind/diverged from its base, or if unrelated changes make the intended commit ambiguous. Never reset, stash, rebase, clean, force-push, or discard work.
3. Review and commit only the intended changes. Use explicit paths; never use `git add .` or `git add -A`:
   ```bash
   git diff
   git diff --staged
   git add -- <intended-paths>
   git diff --staged
   git commit -m "<message>"
   ```
   Skip `git add` and `git commit` when the intended work is already committed.
4. Push the current feature branch:
   ```bash
   git push -u origin HEAD
   ```
5. Find the pull request for the current branch. If one exists, update it; otherwise create it:
   ```bash
   branch=$(git branch --show-current)
   gh pr list --head "$branch" --state open --json number,url,title
   gh pr create --base "$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)" --head "$branch" --title "<title>" --body-file "<body-file>"
   # Or, for an existing PR:
   gh pr edit <number> --title "<title>" --body-file "<body-file>"
   ```
6. Read back the result and report it:
   ```bash
   gh pr view --json number,url,state,isDraft,mergeStateStatus,statusCheckRollup
   git status --short --branch
   ```

The job is complete only after the branch is pushed and an open pull request is confirmed. Report a concrete blocker only when one of these commands establishes it.
