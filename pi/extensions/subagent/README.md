# Subagent Example

Delegate tasks to specialized subagents with isolated context windows.

## Features

- **Isolated context**: Each subagent runs in a separate `pi` process
- **Non-blocking delegation**: The parent tool call returns immediately while subagents continue in the background
- **Automatic hand-back**: Completion queues a custom follow-up message and starts a parent turn to pick the result back up
- **Live context view**: Delegation automatically opens a background-progress widget below the editor
- **Result hand-back**: Final output is preserved in model context through a custom completion message
- **Durable artifact capture**: Optional `artifactDir` stores timestamped terminal outputs under repository-root `.work/` before hand-back
- **Usage tracking**: The live context viewer shows thinking level, turns, tokens, cost, and context occupancy per agent
- **Agent catalogue**: Advertises the currently available user-agent names and descriptions to the model before it calls the tool
- **Context viewer**: Shows a live primary → job → subagent context tree with changing activity titles; toggle it with `/context-viewer`
- **Invalid-name alert**: The companion `../subagent-explorer-alert.ts` extension records and displays any request for the nonexistent `explorer` agent without rewriting it
- **Job control**: `/subagents` lists running work; `/subagents cancel <id>` and `/subagents cancel-all` stop it

## Structure

```
pi/
├── extensions/subagent/
│   ├── README.md            # This file
│   ├── index.ts             # Extension entry point and subagent tool
│   ├── agents.ts            # Agent discovery logic
│   ├── artifacts.ts         # Safe timestamped `.work/` final-output persistence
│   └── context-viewer.ts    # Primary/subagent context widget
└── agents/
    ├── scout.md             # Focused read-only reconnaissance
    ├── reviewer.md          # Read-only review
    └── worker.md            # Primary-like bounded implementation
```

## Loading in Pi

This repository is the canonical source for the local Pi resources. Host provisioning maps `~/.pi/agent/extensions` and `agents` to the corresponding `pi/` directories documented in the repository root [`README.md`](../../../README.md). The complete `subagent/` directory must remain available because `index.ts` imports both `agents.ts` and `context-viewer.ts`.

After changing a linked extension or profile, run Pi's `/reload` command.

## Security Model

This tool executes a separate `pi` subprocess with a delegated system prompt and tool/model configuration. The tool returns a background job id immediately, leaving the parent responsive. When the child finishes, the extension injects its result as a custom follow-up message with `triggerTurn: true`; if the parent is busy, Pi queues that hand-back, otherwise it starts the next parent turn immediately. Child processes always start with `--exclude-tools subagent`, so a subagent cannot recursively delegate to another subagent. The worker profile also uses an explicit tool allowlist that omits `subagent`, providing the same boundary when an older already-running parent extension reads the profile before spawning a new worker.

**Project-local agents** (`.pi/agents/*.md`) are repo-controlled prompts that can instruct the model to read files, run bash commands, etc.

**Default behavior:** Only loads **user-level agents** from `~/.pi/agent/agents`.

To enable project-local agents, pass `agentScope: "both"` (or `"project"`). Only do this for repositories you trust.

When running interactively, the tool prompts for confirmation before running project-local agents. Set `confirmProjectAgents: false` to disable.

## Usage

### Single agent
```
Use scout to find all authentication code
```

For durable final-output capture:
```json
{
  "agent": "scout",
  "task": "Find authentication entry points and return exact paths and symbols",
  "artifactDir": ".work/auth-refactor/artifacts"
}
```

### Parallel execution
```
Run 2 scouts in parallel: one to find models, one to find providers
```

### Chained workflow
```
Use a chain: first have worker implement the bounded task, then have reviewer review it
```

## Tool Modes

| Mode | Parameter | Description |
|------|-----------|-------------|
| Single | `{ agent, task }` | One agent, one task |
| Parallel | `{ tasks: [...] }` | Multiple agents run concurrently (max 8, 4 concurrent) |
| Chain | `{ chain: [...] }` | Sequential with `{previous}` placeholder |

All modes accept an optional repository-relative `artifactDir` inside `.work/`, for example `.work/auth-refactor/artifacts`. Use it for substantive delegated work whose final facts must survive parent compaction. The extension stores terminal final output—not the complete child transcript—in UTC timestamp-prefixed Markdown files and returns their paths in both result details and the completion hand-back. An individual artifact output is capped at 1 MiB with an explicit truncation marker to prevent unbounded scratch writes.

## Output Display

**Delegation receipt**:
- Returns immediately with a background job id
- Tells the parent not to wait or duplicate the delegated scope
- Final output and failure diagnostics arrive in a custom completion message

**Context viewer**:
- Automatically opens as soon as a valid background delegation starts, so queued and running work is visible without a command
- `/context-viewer` or `/context-viewer toggle` toggles the viewer; `/context-viewer open` and `/context-viewer close` set it explicitly
- Renders below the editor without taking focus; an automatically opened viewer closes when all jobs succeed, while a manually opened viewer remains until closed
- Uses green for running work and red for failures; successful jobs are removed immediately instead of accumulating as history
- Shows each agent's configured thinking level and changing high-level activity (for example thinking, reading a file, running a command, or writing its response) ahead of context usage, model, and queued/running/failed state; process IDs are not displayed
- Persists compact final job state session-wide for restoration and hand-back without displaying successful history
- Prevents recursive child delegation by excluding the `subagent` tool from every child process
- Primary occupancy uses Pi's live context estimate; child occupancy uses the latest child assistant response and may show `?` when the model's context window cannot be resolved

**Background completion**:
- The tool result immediately returns a job id instead of blocking the parent turn
- `/context-viewer` shows live child state while work continues
- The completion follow-up returns each task's final output to the parent model, capped at 50 KB per parallel task
- When `artifactDir` is set, terminal final outputs and relevant failure diagnostics are written before hand-back; filenames sort by completion time
- Artifact capture is opt-in so routine delegation does not dump every result to disk, and each artifact is marked as evidence rather than authoritative instructions
- The parent should verify key facts and fold them plus relevant artifact paths into cumulative `.work/<task>/state.md`; recovery reads that snapshot first rather than scanning every artifact
- Failure diagnostics from stderr/error messages are handed back when a child exits before producing output
- Session shutdown or extension reload records active jobs as aborted, then stops all jobs owned by that session

## Agent Definitions

Agents are markdown files with YAML frontmatter:

```markdown
---
name: my-agent
description: What this agent does
tools: read, grep, find, ls
model: claude-haiku-4-5
thinking: low
---

System prompt for the agent goes here.
```

**Locations:**
- `~/.pi/agent/agents/*.md` - User-level (always loaded)
- `.pi/agents/*.md` - Project-level (only with `agentScope: "project"` or `"both"`)

Project agents override user agents with the same name when `agentScope: "both"`.

`thinking` is mandatory. Profiles without one of `off`, `minimal`, `low`, or `medium` are not loaded. The calling agent cannot supply or override thinking; the selected profile determines it statically. A `model` value must not include Pi's `:<thinking>` suffix because thinking is configured separately; profiles that use such a suffix are not loaded.

## Sample Agents

| Agent | Purpose | Model | Thinking | Tools |
|-------|---------|-------|----------|-------|
| `scout` | Focused read-only codebase discovery | Pi default | low | read, grep, find, ls |
| `reviewer` | Read-only quality and security review | Pi default | medium | read, grep, find, ls, bash |
| `worker` | Primary-like bounded implementation without delegation | Pi default | low | read, bash, edit, write, grep, find, ls, web_search, web_fetch |

The bundled profiles intentionally omit a pinned model so child processes use the locally configured Pi default provider and model. Each profile must set an explicit thinking level; the extension accepts only `off`, `minimal`, `low`, or `medium` and refuses to load profiles with missing or invalid values.

## Error Handling

- **Exit code != 0**: Tool returns error with stderr/output
- **stopReason "error"**: LLM error propagated with error message
- **stopReason "aborted"**: User abort (Ctrl+C) kills subprocess, throws error
- **Chain mode**: Stops at first failing step, reports which step failed

## Limitations

- The completed tool card remains a delegation receipt; live progress moves to `/context-viewer`, and final output arrives in the follow-up message
- Parallel model-visible output is capped at 50 KB per task; full results remain in tool details and, when requested, timestamped artifacts
- Agents discovered fresh on each invocation (allows editing mid-session)
- A child context percentage is unavailable when its provider/model cannot be resolved in the parent's model registry
- Primary context may temporarily be unknown immediately after compaction
- Artifact output is capped at 1 MiB per terminal result and marked when truncated
- Parallel mode limited to 8 tasks, 4 concurrent
