# Pi resources

These resources depend on Pi's extension and discovery APIs and are therefore Pi-specific rather than generic agent assets.

## Subagents

`extensions/subagent/` registers an LLM-callable `subagent` spawn tool. Each delegated task runs in a separate Pi process with an isolated context window.

Every invocation supplies a descriptive `name`, an explicit least-privilege `tools` allowlist, and a complete standalone `prompt`. Skills and recursive delegation are disabled for every child. The caller's prompt must directly include task-critical conversation context—such as proposed changes or user decisions—that is absent from referenced files.

The matching [`subagent` skill](../skills/subagent/SKILL.md) teaches the parent how to construct a complete handoff. Multiple independent calls provide visible parallel fanout without named role profiles or a hidden chain DSL.

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

Run `/context-viewer open`, `/context-viewer close`, or `/context-viewer` to toggle a live widget below the editor. It displays primary and child-subagent context occupancy as a tree. Completed subagent runs are reconstructed from the active session branch.

After changing a linked extension or profile, use Pi's `/reload` command.
