import assert from "node:assert/strict";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { visibleWidth } from "@earendil-works/pi-tui";
import { renderSubagentResultLines } from "./context-viewer.ts";
import { terminalizePendingDetails, type SingleResult } from "./index.ts";

const theme = {
	fg: (_color: string, text: string) => text,
} as never;

function result(task: string, activity?: string, pid?: number): SingleResult {
	return {
		agent: "worker",
		agentSource: "user",
		task,
		activity,
		thinking: "low",
		exitCode: -1,
		pid,
		status: "running",
		messages: [],
		stderr: "",
		model: "provider/model",
		usage: {
			input: 0,
			output: 0,
			cacheRead: 0,
			cacheWrite: 0,
			cost: 0,
			contextTokens: 1200,
			contextWindow: 10000,
			contextPercent: 12,
			turns: 1,
		},
	};
}

const active = renderSubagentResultLines(
	result("Review the implementation", "Running node --test", 4321),
	"    ",
	true,
	theme,
	80,
);
assert.equal(active.length, 1);
assert.match(active[0]!, /worker \[low\] — Running node --test/);
assert.match(active[0]!, /ctx:1\.2k\/10k 12% provider\/model/);
assert.doesNotMatch(active[0]!, /pid:/);
assert.ok(visibleWidth(active[0]!) <= 80);

const taskFallback = renderSubagentResultLines(result("Review the implementation", undefined, 4321), "    ", true, theme, 100);
assert.match(taskFallback[0]!, /worker \[low\] — Review the implementation/);
assert.doesNotMatch(taskFallback[0]!, /pid:/);

const unicode = renderSubagentResultLines(
	result("检查授权流程", "正在检查授权流程并验证所有回归测试 👩‍💻👨‍👩‍👧‍👦", 4321),
	"    ",
	true,
	theme,
	64,
);
assert.match(unicode[0]!, /worker \[low\] — /);
assert.match(unicode[0]!, /ctx:1\.2k\/10k 12% provider\/model/);
assert.doesNotMatch(unicode[0]!, /pid:/);
assert.ok(unicode.every((line) => visibleWidth(line) <= 64));

const sanitized = renderSubagentResultLines(
	result("fallback task", "\u001b[31mReading auth.ts\u001b[0m\u202e", 4321),
	"    ",
	true,
	theme,
	80,
);
assert.match(sanitized[0]!, /worker \[low\] — Reading auth\.ts/);
assert.doesNotMatch(sanitized.join("\n"), /\u001b|\u202e|pid:/);

const unsafeMetadataResult = result("review", "Thinking", 4321);
unsafeMetadataResult.agent = "\u001b[31mworker\u001b[0m\u202e";
unsafeMetadataResult.model = "\u001b]8;;https://example.test\u0007provider/model\u001b]8;;\u0007";
const safeMetadata = renderSubagentResultLines(unsafeMetadataResult, "    ", true, theme, 80);
assert.match(safeMetadata[0]!, /worker \[low\] — Thinking/);
assert.match(safeMetadata.join("\n"), /provider\/model/);
assert.doesNotMatch(safeMetadata.join("\n"), /\u001b|\u202e|pid:/);

const narrow = renderSubagentResultLines(result("", "Thinking", 4321), "    ", true, theme, 32);
assert.equal(narrow.length, 2);
assert.match(narrow[0]!, /worker \[low\]/);
assert.equal(narrow[1]!.trim(), "ctx:1.2k/10k 12%");
assert.ok(narrow.every((line) => visibleWidth(line) <= 32));
assert.doesNotMatch(narrow.join("\n"), /pid:/);

const longMetadataResult = result("", "Thinking", 4321);
longMetadataResult.agent = "a-very-long-project-agent-name";
const longMetadata = renderSubagentResultLines(longMetadataResult, "    ", true, theme, 32);
assert.equal(longMetadata.length, 2);
assert.equal(longMetadata[1]!.trim(), "ctx:1.2k/10k 12%");
assert.ok(longMetadata.every((line) => visibleWidth(line) <= 32));

const noActivity = renderSubagentResultLines(result("", undefined, 4321), "    ", true, theme, 80);
assert.match(noActivity[0]!, /worker \[low\] ctx:/);
assert.doesNotMatch(noActivity[0]!, /pid:/);

const pendingResult = result("review", "Queued: review");
pendingResult.status = "queued";
const failedDetails = terminalizePendingDetails(
	{ mode: "single", agentScope: "user", projectAgentsDir: null, results: [pendingResult] },
	new Error("spawn failed"),
	false,
);
assert.equal(failedDetails.results[0]?.status, "failed");
assert.equal(failedDetails.results[0]?.activity, "Failed");
const abortedResult = result("review", "Starting review");
abortedResult.status = "running";
const abortedDetails = terminalizePendingDetails(
	{ mode: "single", agentScope: "user", projectAgentsDir: null, results: [abortedResult] },
	new Error("aborted"),
	true,
);
assert.equal(abortedDetails.results[0]?.activity, "Aborted");

export default function (_pi: ExtensionAPI): void {}
