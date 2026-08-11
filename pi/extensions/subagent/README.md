# Subagent Example

Delegate tasks to specialized subagents with isolated context windows.

## Features

- **Isolated context**: Each subagent runs in a separate `pi` process
- **Streaming output**: See tool calls and progress as they happen
- **Parallel streaming**: All parallel tasks stream updates simultaneously
- **Markdown rendering**: Final output rendered with proper formatting (expanded view)
- **Usage tracking**: Shows turns, tokens, cost, and context occupancy per agent
- **Agent catalogue**: Advertises the currently available user-agent names and descriptions to the model before it calls the tool
- **Context viewer**: Toggle a live primary → subagent → nested-subagent context tree with `/context-viewer`
- **Invalid-name alert**: The companion `../subagent-explorer-alert.ts` extension records and displays any request for the nonexistent `explorer` agent without rewriting it
- **Abort support**: Ctrl+C propagates to kill subagent processes

## Structure

```
pi/
├── extensions/subagent/
│   ├── README.md            # This file
│   ├── index.ts             # Extension entry point and subagent tool
│   ├── agents.ts            # Agent discovery logic
│   └── context-viewer.ts    # Primary/subagent context widget
├── agents/
│   ├── scout.md             # Fast reconnaissance
│   ├── planner.md           # Implementation planning
│   ├── reviewer.md          # Code review
│   └── worker.md            # General-purpose work
└── prompts/
    ├── implement.md             # scout → planner → worker
    ├── scout-and-plan.md        # scout → planner
    └── implement-and-review.md  # worker → reviewer → worker
```

## Loading in Pi

This repository is the canonical source for the local Pi resources. Host provisioning maps `~/.pi/agent/extensions`, `agents`, and `prompts` to the corresponding `pi/` directories documented in the repository root [`README.md`](../../../README.md). The complete `subagent/` directory must remain available because `index.ts` imports both `agents.ts` and `context-viewer.ts`.

After changing a linked extension, profile, or prompt, run Pi's `/reload` command.

## Security Model

This tool executes a separate `pi` subprocess with a delegated system prompt and tool/model configuration.

**Project-local agents** (`.pi/agents/*.md`) are repo-controlled prompts that can instruct the model to read files, run bash commands, etc.

**Default behavior:** Only loads **user-level agents** from `~/.pi/agent/agents`.

To enable project-local agents, pass `agentScope: "both"` (or `"project"`). Only do this for repositories you trust.

When running interactively, the tool prompts for confirmation before running project-local agents. Set `confirmProjectAgents: false` to disable.

## Usage

### Single agent
```
Use scout to find all authentication code
```

### Parallel execution
```
Run 2 scouts in parallel: one to find models, one to find providers
```

### Chained workflow
```
Use a chain: first have scout find the read tool, then have planner suggest improvements
```

### Workflow prompts
```
/implement add Redis caching to the session store
/scout-and-plan refactor auth to support OAuth
/implement-and-review add input validation to API endpoints
```

## Tool Modes

| Mode | Parameter | Description |
|------|-----------|-------------|
| Single | `{ agent, task }` | One agent, one task |
| Parallel | `{ tasks: [...] }` | Multiple agents run concurrently (max 8, 4 concurrent) |
| Chain | `{ chain: [...] }` | Sequential with `{previous}` placeholder |

## Output Display

**Collapsed view** (default):
- Status icon (✓/✗/⏳) and agent name
- Last 5-10 items (tool calls and text)
- Usage stats: `3 turns ↑input ↓output RcacheRead WcacheWrite $cost ctx:contextTokens model`

**Expanded view** (Ctrl+O):
- Full task text
- All tool calls with formatted arguments
- Final output rendered as Markdown
- Per-task usage (for chain/parallel)

**Context viewer**:
- `/context-viewer` or `/context-viewer toggle` toggles the viewer; `/context-viewer open` and `/context-viewer close` set it explicitly
- `/context-tree` remains available as a legacy alias
- Renders below the editor without taking focus
- Shows current tokens, context-window size, percentage, model, and running/completed/failed state
- Discovers nested subagent calls from child Pi JSON lifecycle events
- Reconstructs completed runs from the active session branch after resume
- Primary occupancy uses Pi's live context estimate; child occupancy uses the latest child assistant response and may show `?` when the model's context window cannot be resolved

**Parallel mode streaming**:
- Shows all tasks with live status (⏳ running, ✓ done, ✗ failed)
- Updates as each task makes progress
- Shows "2/3 done, 1 running" status
- Returns each completed task's final output to the parent model, capped at 50 KB per task
- Returns failure diagnostics from stderr/error messages when a child exits before producing output

**Tool call formatting** (mimics built-in tools):
- `$ command` for bash
- `read ~/path:1-10` for read
- `grep /pattern/ in ~/path` for grep
- etc.

## Agent Definitions

Agents are markdown files with YAML frontmatter:

```markdown
---
name: my-agent
description: What this agent does
tools: read, grep, find, ls
model: claude-haiku-4-5
---

System prompt for the agent goes here.
```

**Locations:**
- `~/.pi/agent/agents/*.md` - User-level (always loaded)
- `.pi/agents/*.md` - Project-level (only with `agentScope: "project"` or `"both"`)

Project agents override user agents with the same name when `agentScope: "both"`.

## Sample Agents

| Agent | Purpose | Model | Tools |
|-------|---------|-------|-------|
| `scout` | Fast codebase recon | Pi default | read, grep, find, ls, bash |
| `planner` | Implementation plans | Pi default | read, grep, find, ls |
| `reviewer` | Code review | Pi default | read, grep, find, ls, bash |
| `worker` | General-purpose | Pi default | (all default) |

The bundled profiles intentionally omit a pinned model so child processes use the locally configured Pi default provider and model.

## Workflow Prompts

| Prompt | Flow |
|--------|------|
| `/implement <query>` | scout → planner → worker |
| `/scout-and-plan <query>` | scout → planner |
| `/implement-and-review <query>` | worker → reviewer → worker |

## Error Handling

- **Exit code != 0**: Tool returns error with stderr/output
- **stopReason "error"**: LLM error propagated with error message
- **stopReason "aborted"**: User abort (Ctrl+C) kills subprocess, throws error
- **Chain mode**: Stops at first failing step, reports which step failed

## Limitations

- Output truncated to last 10 items in collapsed view (expand to see all)
- Parallel model-visible output is capped at 50 KB per task; full results remain in tool details
- Agents discovered fresh on each invocation (allows editing mid-session)
- A child context percentage is unavailable when its provider/model cannot be resolved in the parent's model registry
- Primary context may temporarily be unknown immediately after compaction
- Parallel mode limited to 8 tasks, 4 concurrent
