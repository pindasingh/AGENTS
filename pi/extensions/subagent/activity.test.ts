import assert from "node:assert/strict";
import test from "node:test";
import { ChildActivityTracker, describeStreamingActivity, describeToolActivity } from "./activity.ts";

test("describeToolActivity summarizes common active operations", () => {
	assert.equal(describeToolActivity("read", { path: "src/auth.ts" }), "Reading src/auth.ts");
	assert.equal(describeToolActivity("edit", { path: "src/auth.ts" }), "Editing src/auth.ts");
	assert.equal(describeToolActivity("bash", { command: "pnpm   test\n --filter auth" }), "Running pnpm test --filter auth");
	assert.equal(describeToolActivity("grep", { pattern: "authorize" }), "Searching code for authorize");
	assert.equal(describeToolActivity("web_search", { query: "Pi extensions" }), "Searching the web for Pi extensions");
	assert.equal(describeToolActivity("custom_tool", {}), "Using custom tool");
});

test("describeStreamingActivity tracks high-level model activity", () => {
	assert.equal(describeStreamingActivity("thinking_delta"), "Thinking");
	assert.equal(describeStreamingActivity("text_start"), "Writing response");
	assert.equal(describeStreamingActivity("toolcall_delta"), "Preparing next action");
	assert.equal(describeStreamingActivity("unknown"), undefined);
});

test("ChildActivityTracker follows a complete child event sequence", () => {
	const tracker = new ChildActivityTracker("review authorization");
	assert.equal(tracker.update({ type: "turn_start" }), "Thinking about review authorization");
	assert.equal(
		tracker.update({ type: "tool_execution_start", toolCallId: "read-1", toolName: "read", args: { path: "src/auth.ts" } }),
		"Reading src/auth.ts",
	);
	assert.equal(
		tracker.update({ type: "tool_execution_end", toolCallId: "read-1", toolName: "read", isError: false }),
		"Reviewing read results",
	);
	assert.equal(
		tracker.update({ type: "message_update", assistantMessageEvent: { type: "text_delta" } }),
		"Writing response",
	);
});

test("ChildActivityTracker preserves interleaved concurrent tool activity", () => {
	const tracker = new ChildActivityTracker("run checks");
	assert.equal(
		tracker.update({ type: "tool_execution_start", toolCallId: "test", toolName: "bash", args: { command: "pnpm test" } }),
		"Running pnpm test",
	);
	assert.equal(
		tracker.update({ type: "tool_execution_start", toolCallId: "lint", toolName: "bash", args: { command: "pnpm lint" } }),
		"Running 2 actions: Running pnpm test; Running pnpm lint",
	);
	assert.equal(
		tracker.update({ type: "tool_execution_end", toolCallId: "test", toolName: "bash", isError: false }),
		"Running pnpm lint",
	);
	assert.equal(
		tracker.update({ type: "tool_execution_end", toolCallId: "lint", toolName: "bash", isError: true }),
		"Recovering from failed bash",
	);
});
