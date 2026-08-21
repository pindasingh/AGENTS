import assert from "node:assert/strict";
import test from "node:test";
import { cancelAllOwnedJobs, cancelOwnedJob, terminalJobStatus } from "./control-contract.ts";

const job = () => ({ controller: new AbortController() });

test("cancellation targets only an exact job id owned by this session", () => {
	const first = job();
	const second = job();
	const jobs = new Map([["subagent-1", first], ["subagent-2", second]]);

	assert.equal(cancelOwnedJob(jobs, "subagent-9"), false);
	assert.equal(first.controller.signal.aborted, false);
	assert.equal(second.controller.signal.aborted, false);

	assert.equal(cancelOwnedJob(jobs, "subagent-2"), true);
	assert.equal(first.controller.signal.aborted, false);
	assert.equal(second.controller.signal.aborted, true);
});

test("cancelled jobs are reported as aborted rather than failed", () => {
	assert.equal(terminalJobStatus(true), "aborted");
	assert.equal(terminalJobStatus(false), "failed");
});

test("cancel-all returns and aborts only jobs in the owned map", () => {
	const first = job();
	const second = job();
	const jobs = new Map([["subagent-1", first], ["subagent-2", second]]);

	assert.deepEqual(cancelAllOwnedJobs(jobs), ["subagent-1", "subagent-2"]);
	assert.equal(first.controller.signal.aborted, true);
	assert.equal(second.controller.signal.aborted, true);
});
