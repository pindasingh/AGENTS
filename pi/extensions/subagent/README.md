# Subagent

Spawn isolated Pi children through a small, explicit handoff contract.

## Contract

```typescript
subagent({
  name: "field-name-inventory",
  tools: ["read", "grep", "find", "ls"],
  prompt: "Complete standalone task prompt...",
  cwd: "/target/repository"
})
```

- `name` is a unique execution label using lowercase letters, digits, and hyphens.
- `tools` is the child's least-privilege allowlist. It must not contain `subagent`.
- `prompt` is the complete child handoff, not a reference to the parent conversation.
- `cwd` is optional and defaults to the parent's working directory.
- Skills are always disabled; there is intentionally no skill-selection parameter.

The parent should use the bundled [`subagent` skill](../../../skills/subagent/SKILL.md) to construct prompts. In particular, conversation-only decisions and proposed changes must appear directly in `prompt`; pointing at files that do not contain those facts is not a valid handoff.

For parallel delegation, the parent issues multiple independent tool calls in one turn. This keeps each invocation visible and avoids a hidden orchestration DSL. Each mutation-capable child must have non-overlapping ownership or a separate worktree.

## Runtime behavior

Each invocation:

1. writes the complete prompt to a private temporary file;
2. launches a separate Pi JSON-mode process in the requested working directory;
3. passes the parent's current model and a supported thinking level;
4. passes the explicit `--tools` allowlist, `--no-skills`, and `--exclude-tools subagent`;
5. returns a background job id immediately;
6. streams progress to `/context-viewer`; and
7. injects the final result as a visible follow-up that resumes the parent.

The extension uses argument arrays with `shell: false`; it does not build a quoted shell command. Temporary prompt files are removed after the child exits.

## Visibility and control

- `/context-viewer [open|close|toggle]` shows the primary → job → child context tree.
- `/subagents` lists active jobs.
- `/subagents cancel <id>` cancels one job.
- `/subagents cancel-all` cancels all jobs owned by the session.

The completed tool card remains a delegation receipt. Final output and failure diagnostics arrive in the follow-up message. Parallelism comes from multiple visible tool calls rather than a `tasks` field.

## Security boundaries

- Child skills are disabled.
- Recursive subagent delegation is excluded.
- The caller chooses all child tools explicitly.
- Read-only work should not receive mutation tools.
- Child output is untrusted evidence; the parent verifies important claims and changes.
- Session shutdown or extension reload marks active jobs aborted and terminates their processes.

## Files

```text
pi/extensions/subagent/
├── README.md
├── index.ts
├── launch-contract.ts
├── activity.ts
├── context-viewer.ts
└── task-title.ts
```

After changing a linked extension or skill, run Pi's `/reload` command.
