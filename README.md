# AGENTS

Canonical, version-controlled resources shared by local coding agents.

## Repository layout

- `AGENTS.md` — harness-neutral global operating rules, including repository-local `.work/` continuity checkpoints.
- `skills/` — harness-neutral [Agent Skills](https://agentskills.io/) packages. Pi and other compatible agents can load these, including the `work-continuity` recovery workflow.
- `pi/extensions/` — Pi-specific TypeScript extensions, including best-effort early checkpoint and automatic post-compaction recovery reminders.
- `pi/agents/` — specialist profiles consumed by Pi's `subagent` extension.

The generic policy and skills stay at the repository root because they are useful across agent harnesses. Pi runtime code and Pi discovery formats stay under `pi/`.

## Pi source of truth

The canonical Pi resources are this repository. The local Pi paths should point back here (a file hard link plus directory junctions on Windows, symbolic links elsewhere):

```text
~/.pi/agent/AGENTS.md  -> <repo>/AGENTS.md
~/.pi/agent/skills     -> <repo>/skills
~/.pi/agent/extensions -> <repo>/pi/extensions
~/.pi/agent/agents     -> <repo>/pi/agents
```

These links are host provisioning maintained outside agent instructions. Agents must not create, replace, or repair them as part of normal repository work.

Pi's mutable and sensitive runtime data is intentionally not tracked here:

- `auth.json` and model credential/cache files
- `trust.json`
- `sessions/`
- locally installed binaries
- `settings.json`, which includes machine/UI preferences and Pi-managed changelog state

## Included Pi extensions

- `dependency-install-guard.ts` — enforces the local no-dependency-install policy.
- `herdr-agent-state.ts` — Herdr's Pi lifecycle integration. Herdr may regenerate this file; because Pi links to this repository, review and commit any generated update.
- `skill-toggle.ts` — toggles every discovered skill between agent-invocable and manual-only by updating its `disable-model-invocation` frontmatter through `/toggle-skills`.
- `subagent/` — adds the `subagent` tool, isolated single/parallel/chained Pi subprocesses, optional timestamped `.work/` artifact capture for terminal outputs, and `/context-viewer`.
- `subagent-explorer-alert.ts` — records a durable, visible session error whenever a model requests the nonexistent `explorer` agent; it does not alias or rewrite the request.
- `direct-web-tools.ts` — dependency-free `web_search` and `web_fetch` tools; search parses Bing's public HTML results directly, without search APIs, MCP search providers, or API keys.
- `work-continuity.ts` — keeps agents focused on a cumulative latest `.work/<task>/state.md` snapshot, with best-effort early checkpoint and automatic post-compaction recovery reminders.

This canonical agent-resource repository intentionally tracks `.work/` in `.gitignore` as part of the published continuity contract and to dogfood it safely. Product repositories should follow `AGENTS.md` and prefer their local Git exclude file when adopting agent scratch state.

The matching subagent profiles are in `pi/agents/`.
