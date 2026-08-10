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

## Web tools

`extensions/opencode-web-tools.ts` provides two dependency-free, OpenCode-inspired tools:

- `web_search` — searches through Exa by default or Parallel when `PI_WEB_SEARCH_PROVIDER=parallel`. `EXA_API_KEY` and `PARALLEL_API_KEY` are optional service credentials.
- `web_fetch` — fetches public HTTP(S) pages, JSON, text, and supported images; HTML is converted to readable Markdown or text. Private/local destinations and redirects are blocked.

Text output is capped at Pi's standard 2,000-line/50 KB limit. `web_fetch` rejects network responses over 5 MiB and images over 1 MiB.

## Context hierarchy

Run `/context-tree open`, `/context-tree close`, or `/context-tree` to toggle a live widget below the editor. It displays primary context occupancy and nested subagent context occupancy as a hierarchy. Completed subagent runs are reconstructed from the active session branch.

After changing a linked extension, profile, or prompt, use Pi's `/reload` command.
