---
name: subagent
description: Spawn an isolated Pi child with an explicit name, least-privilege tools, disabled skills, and a complete standalone prompt. Use for independent review, reconnaissance, or bounded delegated work when the child must receive task-critical context directly rather than infer it from the parent conversation.
compatibility: Requires Pi with the repository's subagent extension and its name/tools/prompt spawn contract.
---

# Subagent

Use the `subagent` tool to spawn one isolated child. The child does not inherit this skill or any other skill, and it cannot spawn subagents.

```typescript
subagent({
  name: "field-name-inventory",
  tools: ["read", "grep", "find", "ls"],
  prompt: "Complete standalone task prompt...",
  cwd: "/absolute/or/appropriate/working/directory"
})
```

## Build the handoff before spawning

The child sees the `prompt` and the target repository context. It does not see facts merely because the parent read or discussed them. Write a compact but self-contained prompt containing:

1. **Goal** — the concrete result to produce.
2. **Target** — repository, cwd, branch or diff, and relevant source seams.
3. **Authority** — whether it may only inspect or may also edit, test, commit, or publish.
4. **Known context** — task-critical user statements, proposed changes, decisions, rejected approaches, and constraints. Include these directly even when they are absent from referenced files.
5. **Evidence anchors** — useful files, symbols, URLs, or commands. References supplement context; they do not replace it.
6. **Success and validation** — what must be true and which checks or evidence are expected.
7. **Output contract** — the concise report or implementation handoff the parent needs.

Before calling the tool, ask: **Could a fresh agent understand every material requirement from this prompt and the named evidence alone?** If not, complete the prompt first.

## Choose capabilities explicitly

- Give the run a short descriptive lowercase-hyphenated `name`; it is an execution label, not a reusable role profile.
- Pass the smallest sufficient `tools` allowlist.
- Omit mutation tools for review and reconnaissance.
- Do not include `subagent`; recursion is blocked.
- Skills are always disabled by the extension. Put required procedures and constraints in the prompt instead of relying on skill inheritance.
- Set `cwd` whenever the target is not unambiguously the parent's current working directory.

For independent parallel work, issue several separate `subagent` calls in the same turn with distinct names, prompts, and non-overlapping authority. Use one writer per working directory.

## Control running jobs

Keep every job id returned by `subagent`. The parent can safely inspect and cancel only jobs owned by its session:

```typescript
subagent_control({ action: "list" })
subagent_control({ action: "cancel", id: "subagent-2" })
subagent_control({ action: "cancel-all" })
```

Use the exact returned id. If a job cannot be identified in `list`, do not kill shared processes through the shell.

## Parent responsibilities

The parent owns task decomposition, complete context handoff, synthesis, and verification. After spawning, continue only independent work and do not duplicate the child's scope. Treat the returned result as evidence rather than authority; inspect important claims and validate changes before completion.

See [`UPSTREAM.md`](UPSTREAM.md) for the transparent-harness design provenance and intentional differences from the referenced gist.
