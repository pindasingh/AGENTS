---
name: ship-branch-pull-request
description: Completes Git branch delivery by creating or updating a GitHub pull request after pushing commits. Use whenever work is committed or pushed to a non-default branch, a user asks to ship/publish/push changes, or a status report mentions a pushed branch without a PR. Treat the pull request—not the push—as the delivery artifact; use drafts only while work is incomplete or readiness is uncertain.
compatibility: Requires Git and GitHub CLI (`gh`) with repository access.
---

# Ship Branch as a Pull Request

A pushed branch is not a complete handoff: collaborators need a pull request to discover, review, discuss, test, and merge the work. Finish branch delivery by ensuring that the branch has a useful PR.

## Workflow

1. Inspect the complete branch diff and commit range against the refreshed remote default branch.
2. Verify the branch is not the default branch, has been pushed, and identify the destination repository, head repository owner, branch, and intended base explicitly. This matters for forks and similarly named repositories.
3. Check for an existing PR using the exact destination repository and qualified head branch:
   ```bash
   gh pr list --repo "<owner/repo>" --head "<head-owner>:<branch>" --state all \
     --json number,state,isDraft,title,url,baseRefName,headRefName
   ```
   Prefer an open PR when historical closed or merged PRs also exist for a reused branch. Confirm that its `baseRefName` is the intended comparison base before updating it; do not silently retarget a PR whose base differs.
4. If an open PR exists, update its title or body when they no longer describe the final diff. Do not create a duplicate:
   ```bash
   gh pr edit "<number>" --repo "<owner/repo>" \
     --title "<clear title>" --body "<final PR body>"
   ```
5. If no open PR exists, create one. Completed and verified work should be ready for review; add `--draft` only while work is genuinely incomplete or readiness is uncertain:
   ```bash
   gh pr create --repo "<owner/repo>" --base "<default-branch>" --head "<head-owner>:<branch>" \
     --title "<clear title>" --body "<final PR body>"
   ```
   Promote an existing draft once the work is complete and verified:
   ```bash
   gh pr ready "<number>" --repo "<owner/repo>"
   ```
6. Ensure the PR body describes the final branch rather than the conversation or only the latest commit. Include:
   - concise summary of the outcome;
   - important implementation or content changes;
   - verification performed and its result;
   - remaining risks, limitations, or follow-ups when relevant;
   - useful guidance that helps reviewers focus on important behavior or decisions.
7. Read the PR back and inspect its checks, review decision, and merge-conflict status before reporting:
   ```bash
   gh pr view "<number>" --repo "<owner/repo>" \
     --json number,url,state,isDraft,baseRefName,headRefName,mergeStateStatus,reviewDecision,statusCheckRollup
   ```

## Completion gate

Do not describe pushed branch work as complete without one of these outcomes:

- an open PR was created and its URL, draft/ready state, checks, review state, and merge-conflict status were reported;
- the existing open PR was verified/updated and the same status details were reported; or
- an actual blocker was established (for example, missing authentication, insufficient repository permission, or the remote host not supporting the available PR tooling).

A clean working tree, successful push, or commit hash alone does not satisfy delivery.

## Safety and edge cases

- Never create a PR from the default branch to itself.
- Never create duplicate PRs for the same head branch.
- Do not reopen a merged or intentionally closed PR automatically; inspect branch history and create the appropriate new PR only when the branch contains unmerged work.
- Respect explicit user instructions not to create a PR or to use a specific draft/ready state.
- If branch or repository identity is ambiguous, inspect Git remotes and GitHub metadata before acting; do not guess across repositories.
