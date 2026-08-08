# AGENTS

Canonical, version-controlled resources shared by local coding agents.

## Repository layout

- `AGENTS.md` — harness-neutral global operating rules.
- `skills/` — harness-neutral [Agent Skills](https://agentskills.io/) packages. Pi and other compatible agents can load these.
- `evals/` — harness-neutral behavioral evaluation cases for global agent rules.
- `pi/extensions/` — Pi-specific TypeScript extensions.
- `pi/agents/` — specialist profiles consumed by Pi's `subagent` extension.
- `pi/prompts/` — Pi-specific prompt templates and workflow commands.

The generic policy and skills stay at the repository root because they are useful across agent harnesses. Pi runtime code and Pi discovery formats stay under `pi/`.

## Pi source of truth

The canonical Pi resources are this repository. The local Pi paths should point back here (a file hard link plus directory junctions on Windows, symbolic links elsewhere):

```text
~/.pi/agent/AGENTS.md  -> <repo>/AGENTS.md
~/.pi/agent/skills     -> <repo>/skills
~/.pi/agent/extensions -> <repo>/pi/extensions
~/.pi/agent/agents     -> <repo>/pi/agents
~/.pi/agent/prompts    -> <repo>/pi/prompts
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
- `subagent/` — adds the `subagent` tool, including isolated single, parallel, and chained Pi subprocesses.

The matching subagent profiles are in `pi/agents/`, and workflow templates are in `pi/prompts/`.
