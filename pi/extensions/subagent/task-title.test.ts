import assert from "node:assert/strict";
import test from "node:test";
import { conciseTaskTitle } from "./task-title.ts";

test("conciseTaskTitle normalizes delegated tasks and activities", () => {
	assert.equal(conciseTaskTitle("  Inspect\n\tthe   authorization flow  "), "Inspect the authorization flow");
	assert.equal(conciseTaskTitle("   \n\t  "), "");
});

test("conciseTaskTitle strips terminal and direction-control sequences", () => {
	assert.equal(conciseTaskTitle("\u001b[31mRunning tests\u001b[0m"), "Running tests");
	assert.equal(conciseTaskTitle("\u001b]8;;https://example.test\u0007linked\u001b]8;;\u0007"), "linked");
	assert.equal(conciseTaskTitle("safe\u202eevil\u2069\u200b"), "safeevil");
	assert.equal(conciseTaskTitle("\u001b[31m\u202e\u200b"), "");
});
