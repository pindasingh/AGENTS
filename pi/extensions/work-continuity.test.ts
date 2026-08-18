import assert from "node:assert/strict";
import test from "node:test";
import workContinuity, {
	CHECKPOINT_THRESHOLD_PERCENT,
	CheckpointReminderGate,
	REMINDER_TYPE,
	checkpointReminder,
	recoveryReminder,
} from "./work-continuity.ts";

test("CheckpointReminderGate sends once per compaction cycle", () => {
	const gate = new CheckpointReminderGate();
	assert.equal(gate.shouldSend(CHECKPOINT_THRESHOLD_PERCENT - 0.1), false);
	assert.equal(gate.shouldSend(CHECKPOINT_THRESHOLD_PERCENT), true);
	assert.equal(gate.shouldSend(95), false);
	gate.reset();
	assert.equal(gate.shouldSend(95), true);
});

test("CheckpointReminderGate ignores unavailable usage", () => {
	const gate = new CheckpointReminderGate();
	assert.equal(gate.shouldSend(undefined), false);
	assert.equal(gate.shouldSend(null), false);
	assert.equal(gate.shouldSend(Number.NaN), false);
});

test("reminders require checkpointing, reconciliation, and continued work", () => {
	const before = checkpointReminder(72.5);
	assert.match(before, /repository-root \.work\/ checkpoint/);
	assert.match(before, /continue the task/);

	const after = recoveryReminder("threshold");
	assert.match(after, /git status and diff/);
	assert.match(after, /Compaction is not a blocker/);
	assert.match(after, /Read-only agents/);
});

test("extension injects one warning before compaction and recovery after it", () => {
	const handlers = new Map<string, (event: any, ctx: any) => void>();
	const sent: Array<{ message: any; options: any }> = [];
	const pi = {
		on(name: string, handler: (event: any, ctx: any) => void) {
			handlers.set(name, handler);
		},
		sendMessage(message: any, options: any) {
			sent.push({ message, options });
		},
	};
	workContinuity(pi as never);

	let percent: number | null = 69;
	const ctx = { getContextUsage: () => ({ percent }) };
	const turnEnd = handlers.get("turn_end");
	const compact = handlers.get("session_compact");
	assert.ok(turnEnd);
	assert.ok(compact);

	turnEnd({}, ctx);
	assert.equal(sent.length, 0);
	percent = 75;
	turnEnd({}, ctx);
	turnEnd({}, ctx);
	assert.equal(sent.length, 1);
	assert.equal(sent[0].message.customType, REMINDER_TYPE);
	assert.equal(sent[0].message.details.phase, "before-compaction");
	assert.deepEqual(sent[0].options, { deliverAs: "steer" });

	compact({ reason: "overflow", willRetry: true }, ctx);
	assert.equal(sent.length, 2);
	assert.equal(sent[1].message.details.phase, "after-compaction");
	assert.equal(sent[1].message.details.willRetry, true);

	turnEnd({}, ctx);
	assert.equal(sent.length, 3);
});
