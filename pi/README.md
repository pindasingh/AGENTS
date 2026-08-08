# Pi resources

These resources depend on Pi's extension and discovery APIs and are therefore Pi-specific rather than generic agent assets.

## Subagents

`extensions/subagent/` registers an LLM-callable `subagent` tool. Each delegated task runs in a separate Pi process with an isolated context window.

Available profiles:

- `scout` — codebase reconnaissance
- `planner` — implementation planning
- `reviewer` — code review
- `worker` — general-purpose work with the default tools

Available workflow templates:

- `/implement <task>` — scout → planner → worker
- `/scout-and-plan <task>` — scout → planner
- `/implement-and-review <task>` — worker → reviewer → worker

Project-local profiles in `.pi/agents/` are not enabled by default. Calling the tool with `agentScope: "project"` or `"both"` enables them and may require interactive confirmation.

After changing a linked extension, profile, or prompt, use Pi's `/reload` command.
