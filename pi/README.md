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

`extensions/direct-web-tools.ts` provides two dependency-free tools without search APIs, MCP search providers, or API keys:

- `web_search` — retrieves Bing's public HTML search-results page directly, parses result links and snippets, and returns normalized Markdown. Bing can block automation or change its undocumented markup, which will make search temporarily unavailable.
- `web_fetch` — fetches public HTTP(S) pages, JSON, text, and supported images; HTML is converted to readable Markdown or text. Private/local destinations and redirects are blocked.

Both tools use the same hardened public-HTTP path. Text output is capped at Pi's standard 2,000-line/50 KB limit. `web_fetch` rejects network responses over 5 MiB and images over 1 MiB.

## Skill invocation toggle

Run `/toggle-skills` to configure every skill currently discovered by Pi:

- `agent-invocable` — the skill description is available in agent context so Pi can select it automatically.
- `manual-only` — the skill is hidden from agent context and runs only through explicit `/skill:name` invocation.

`extensions/skill-toggle.ts` applies the selection directly to each discovered skill's source file, including package or external skills. Manual-only adds `disable-model-invocation: true`; agent-invocable removes that field. Press `Ctrl+S` to apply and reload Pi, or `Esc` to cancel. Manual invocation also requires Pi's `enableSkillCommands` setting.

## Context viewer

Run `/context-viewer open`, `/context-viewer close`, or `/context-viewer` to toggle a live widget below the editor. It displays primary context occupancy and nested subagent context occupancy as a tree. Completed subagent runs are reconstructed from the active session branch. `/context-tree` remains available as a legacy alias.

After changing a linked extension, profile, or prompt, use Pi's `/reload` command.
