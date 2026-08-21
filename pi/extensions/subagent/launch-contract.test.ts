import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { buildChildArgs, validateSpawnContract } from "./launch-contract.ts";

test("child launch disables skills and recursive delegation while preserving requested tools", () => {
	assert.deepEqual(
		buildChildArgs({
			tools: ["read", "grep", "find", "ls"],
			model: "openai-codex/gpt-5.6-sol",
			thinking: "medium",
		}),
		[
			"--mode",
			"json",
			"-p",
			"--no-session",
			"--thinking",
			"medium",
			"--exclude-tools",
			"subagent",
			"--no-skills",
			"--model",
			"openai-codex/gpt-5.6-sol",
			"--tools",
			"read,grep,find,ls",
		],
	);
});

test("spawn contract requires a safe name, tools without subagent, and a non-empty prompt", () => {
	assert.equal(validateSpawnContract("field-name-inventory", ["read", "grep"], "Inspect the target."), undefined);
	assert.match(validateSpawnContract("Field Name", ["read"], "Inspect")!, /Invalid name/);
	assert.match(validateSpawnContract("field-name", ["read", "subagent"], "Inspect")!, /Invalid tools/);
	assert.match(validateSpawnContract("field-name", ["read", "read"], "Inspect")!, /Invalid tools/);
	assert.match(validateSpawnContract("field-name", ["read,bash"], "Inspect")!, /Invalid tools/);
	assert.match(validateSpawnContract("field-name", ["read"], "   ")!, /Invalid prompt/);
});

test("skill requires conversation-only proposals and decisions to be copied into the child prompt", () => {
	const skill = readFileSync(new URL("../../../skills/subagent/SKILL.md", import.meta.url), "utf8");
	assert.match(skill, /proposed changes, decisions, rejected approaches/);
	assert.match(skill, /Include these directly even when they are absent from referenced files/);
	assert.match(skill, /References supplement context; they do not replace it/);
});
