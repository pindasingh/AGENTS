import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, realpathSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
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

test("reminders preserve ownership while requiring recovery and continued work", () => {
	const before = checkpointReminder(72.5);
	assert.match(before, /Best-effort early warning/);
	assert.match(before, /parent-assigned worker note/);
	assert.match(before, /never modify a candidate canonical checkpoint/);
	assert.match(before, /continue the task/);

	const after = recoveryReminder("threshold");
	assert.match(after, /Updated time/);
	assert.match(after, /newer artifacts/);
	assert.match(after, /git status and diff/);
	assert.match(after, /repair only their own note/);
	assert.match(after, /Compaction is not a blocker/);
	assert.match(after, /Read-only agents/);
});

test("extension steers only an existing tool continuation before compaction", () => {
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

	let percent: number | null = 75;
	const ctx = { getContextUsage: () => ({ percent }) };
	const turnEnd = handlers.get("turn_end");
	const compact = handlers.get("session_compact");
	assert.ok(turnEnd);
	assert.ok(compact);

	turnEnd({ toolResults: [] }, ctx);
	assert.equal(sent.length, 0, "a completed text-only turn must not cause another model turn");
	turnEnd({ toolResults: [{}] }, ctx);
	turnEnd({ toolResults: [{}] }, ctx);
	assert.equal(sent.length, 1);
	assert.equal(sent[0].message.customType, REMINDER_TYPE);
	assert.equal(sent[0].message.details.phase, "early-checkpoint");
	assert.deepEqual(sent[0].options, { deliverAs: "steer" });

	compact({ reason: "overflow", willRetry: true }, ctx);
	assert.equal(sent.length, 2);
	assert.equal(sent[1].message.details.phase, "after-compaction");
	assert.equal(sent[1].message.details.willRetry, true);

	turnEnd({ toolResults: [{}] }, ctx);
	assert.equal(sent.length, 3);
});

function findInstalledPiPackage(): string | undefined {
	const locator = process.platform === "win32" ? "where.exe" : "which";
	const located = spawnSync(locator, ["pi"], { encoding: "utf8" });
	if (located.status !== 0) return undefined;

	for (const line of located.stdout.split(/\r?\n/).filter(Boolean)) {
		try {
			const candidate = realpathSync(line.trim());
			if (/[\\/]dist[\\/]cli\.js$/.test(candidate)) {
				return dirname(dirname(candidate));
			}
			const source = readFileSync(candidate, "utf8");
			const match = source.match(
				/cmd-shim-target=(.+[\\/]node_modules[\\/]@earendil-works[\\/]pi-coding-agent)[\\/]dist[\\/]cli\.js/,
			);
			if (match?.[1] && existsSync(join(match[1], "dist", "index.js"))) {
				return match[1];
			}
		} catch {
			// Try the next executable shim returned by the platform locator.
		}
	}
	return undefined;
}

test("actual Pi queueing carries recovery through threshold, overflow, and manual compaction", async (t) => {
	const packageRoot = findInstalledPiPackage();
	if (!packageRoot) {
		t.skip("installed Pi package could not be located");
		return;
	}
	const piModule = await import(pathToFileURL(join(packageRoot, "dist", "index.js")).href);
	const sendCustomMessage = piModule.AgentSession.prototype.sendCustomMessage as Function;

	for (const [reason, willRetry, sessionFile] of [
		["threshold", false, "primary-session.jsonl"],
		["overflow", true, undefined],
		["manual", false, "primary-session.jsonl"],
	] as const) {
		const handlers = new Map<string, (event: any, ctx: any) => void>();
		const pending: Promise<void>[] = [];
		const steered: any[] = [];
		const session = {
			isStreaming: true,
			sessionFile,
			agent: {
				steer(message: any) {
					steered.push(message);
				},
			},
		};
		const pi = {
			on(name: string, handler: (event: any, ctx: any) => void) {
				handlers.set(name, handler);
			},
			sendMessage(message: any, options: any) {
				pending.push(sendCustomMessage.call(session, message, options));
			},
		};
		workContinuity(pi as never);

		const compact = handlers.get("session_compact");
		assert.ok(compact);
		compact({ reason, willRetry }, {});
		await Promise.all(pending);

		assert.equal(steered.length, 1, `${reason} compaction should queue one continuation message`);
		assert.equal(steered[0].customType, REMINDER_TYPE);
		assert.equal(steered[0].details.reason, reason);
		assert.equal(steered[0].details.willRetry, willRetry);
		assert.match(steered[0].content, /Context was compacted/);
	}
});

test("extension loads in Pi's headless no-session subagent mode", (t) => {
	const packageRoot = findInstalledPiPackage();
	if (!packageRoot) {
		t.skip("installed Pi package could not be located");
		return;
	}
	const extensionPath = resolve("pi/extensions/work-continuity.ts");
	const result = spawnSync(
		process.execPath,
		[join(packageRoot, "dist", "cli.js"), "--mode", "json", "-p", "--no-session", "-e", extensionPath],
		{ cwd: process.cwd(), encoding: "utf8" },
	);
	assert.equal(result.status, 0, result.stderr);
	const events = result.stdout
		.split(/\r?\n/)
		.filter(Boolean)
		.map((line) => JSON.parse(line));
	assert.ok(events.some((event) => event.type === "session"));
});
