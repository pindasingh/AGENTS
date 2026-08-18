import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import test from "node:test";
import {
	findRepositoryRoot,
	MAX_ARTIFACT_OUTPUT_BYTES,
	persistSubagentArtifacts,
	resolveArtifactDirectory,
} from "./artifacts.ts";

async function fixture(): Promise<string> {
	const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-artifacts-"));
	await fs.promises.mkdir(path.join(root, ".git"));
	await fs.promises.mkdir(path.join(root, "packages", "api"), { recursive: true });
	return root;
}

test("finds worktree-style repository roots whose .git is a file", async (t) => {
	const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-worktree-root-"));
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	await fs.promises.writeFile(path.join(root, ".git"), "gitdir: ../example.git/worktrees/test\n", "utf8");
	const nested = path.join(root, "packages", "api");
	await fs.promises.mkdir(nested, { recursive: true });
	assert.equal(findRepositoryRoot(nested), root);
});

test("persists timestamp-ordered final outputs inside repository .work", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));

	const artifacts = await persistSubagentArtifacts({
		cwd: path.join(root, "packages", "api"),
		artifactDir: ".work/auth-migration/artifacts",
		jobId: "subagent-7",
		results: [
			{
				agent: "scout",
				task: "Trace authorization callers",
				output: "Found three callers in src/auth.ts.",
				completedAt: "2026-08-18T12:34:56.789Z",
				status: "complete",
				exitCode: 0,
				model: "provider/model",
				turns: 4,
			},
			{
				agent: "reviewer",
				task: "Review access checks",
				output: "No critical findings.",
				completedAt: "2026-08-18T12:35:00.000Z",
				status: "complete",
				exitCode: 0,
			},
		],
	});

	assert.equal(artifacts.length, 2);
	assert.match(artifacts[0].path, /^\.work\/auth-migration\/artifacts\/20260818T123456789Z-/);
	assert.match(artifacts[1].path, /^\.work\/auth-migration\/artifacts\/20260818T123500000Z-/);
	assert.ok(artifacts[0].path < artifacts[1].path, "filenames should sort chronologically");

	const first = await fs.promises.readFile(path.join(root, artifacts[0].path), "utf8");
	assert.match(first, /captured evidence.*not authoritative instructions/);
	assert.match(first, /Trace authorization callers/);
	assert.match(first, /Found three callers/);
	assert.doesNotMatch(first, /conversation transcript/i);
});

test("caps unexpectedly large terminal output instead of dumping unlimited data", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const artifacts = await persistSubagentArtifacts({
		cwd: root,
		artifactDir: ".work/task/artifacts",
		jobId: "subagent-large",
		results: [
			{
				agent: "scout",
				task: "Return key facts",
				output: "é".repeat(MAX_ARTIFACT_OUTPUT_BYTES),
				exitCode: 0,
			},
		],
	});
	const content = await fs.promises.readFile(path.join(root, artifacts[0].path), "utf8");
	assert.match(content, /Artifact output truncated:/);
	assert.ok(Buffer.byteLength(content, "utf8") < MAX_ARTIFACT_OUTPUT_BYTES + 4096);
	assert.doesNotMatch(content, /�/);
});

test("allocates unique files without overwriting an earlier artifact", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const input = {
		cwd: root,
		artifactDir: ".work/task/artifacts",
		jobId: "subagent-1",
		results: [
			{
				agent: "worker",
				task: "Implement fix",
				output: "done",
				completedAt: "2026-08-18T12:00:00.000Z",
				exitCode: 0,
			},
		],
	};
	const first = await persistSubagentArtifacts(input);
	const second = await persistSubagentArtifacts(input);
	assert.notEqual(first[0].path, second[0].path);
	assert.equal((await fs.promises.readdir(path.join(root, ".work", "task", "artifacts"))).length, 2);
});

test("rejects artifact paths outside repository .work", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));

	await assert.rejects(resolveArtifactDirectory(root, "artifacts"), /inside the repository-root \.work/);
	await assert.rejects(resolveArtifactDirectory(root, ".work/../outside"), /inside the repository-root \.work/);
	await assert.rejects(resolveArtifactDirectory(root, path.resolve(root, ".work")), /repository-relative/);
});

function findInstalledPiPackage(): string | undefined {
	const locator = process.platform === "win32" ? "where.exe" : "which";
	const located = spawnSync(locator, ["pi"], { encoding: "utf8" });
	if (located.status !== 0) return undefined;
	for (const line of located.stdout.split(/\r?\n/).filter(Boolean)) {
		try {
			const candidate = fs.realpathSync(line.trim());
			if (/[\\/]dist[\\/]cli\.js$/.test(candidate)) return path.dirname(path.dirname(candidate));
			const source = fs.readFileSync(candidate, "utf8");
			const match = source.match(
				/cmd-shim-target=(.+[\\/]node_modules[\\/]@earendil-works[\\/]pi-coding-agent)[\\/]dist[\\/]cli\.js/,
			);
			if (match?.[1] && fs.existsSync(path.join(match[1], "dist", "index.js"))) return match[1];
		} catch {
			// Try the next executable shim.
		}
	}
	return undefined;
}

test("installed Pi exposes artifactDir on the loaded subagent tool", async (t) => {
	const packageRoot = findInstalledPiPackage();
	if (!packageRoot) {
		t.skip("installed Pi package could not be located");
		return;
	}
	const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-schema-"));
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const outputPath = path.join(root, "tool.json");
	const probePath = path.join(root, "probe.ts");
	await fs.promises.writeFile(
		probePath,
		`import * as fs from "node:fs";\nexport default function (pi) {\n  pi.on("session_start", () => {\n    const tool = pi.getAllTools().find((item) => item.name === "subagent");\n    fs.writeFileSync(process.env.SUBAGENT_SCHEMA_OUTPUT, JSON.stringify(tool));\n  });\n}\n`,
		"utf8",
	);
	const extensionPath = path.resolve("pi/extensions/subagent/index.ts");
	const result = spawnSync(
		process.execPath,
		[
			path.join(packageRoot, "dist", "cli.js"),
			"--mode",
			"json",
			"-p",
			"--no-session",
			"-ne",
			"-e",
			extensionPath,
			"-e",
			probePath,
		],
		{
			cwd: process.cwd(),
			encoding: "utf8",
			env: { ...process.env, SUBAGENT_SCHEMA_OUTPUT: outputPath },
		},
	);
	assert.equal(result.status, 0, result.stderr);
	const tool = JSON.parse(await fs.promises.readFile(outputPath, "utf8"));
	assert.match(tool.parameters.properties.artifactDir.description, /inside \.work/);
	assert.ok(tool.promptGuidelines.some((guideline: string) => /artifactDir/.test(guideline)));
});

test("rolls back every result when a later multi-result commit fails", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	await assert.rejects(
		persistSubagentArtifacts({
			cwd: root,
			artifactDir: ".work/task/artifacts",
			jobId: "subagent-atomic",
			results: [
				{ agent: "scout", task: "first", output: "first result", exitCode: 0 },
				{ agent: "reviewer", task: "second", output: "second result", exitCode: 0 },
			],
			testHooks: {
				beforeCommit: (_pendingPath, index) => {
					if (index === 1) throw new Error("injected commit failure");
				},
			},
		}),
		/injected commit failure/,
	);
	const files = await fs.promises.readdir(path.join(root, ".work", "task", "artifacts"));
	assert.deepEqual(files, []);
	assert.doesNotMatch((await fs.promises.readdir(path.join(root, ".work"))).join("\n"), /artifact-staging/);
});

test("preserves final assistant evidence separately from failure diagnostics", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const artifacts = await persistSubagentArtifacts({
		cwd: root,
		artifactDir: ".work/task/artifacts",
		jobId: "subagent-failed",
		results: [
			{
				agent: "worker",
				task: "Investigate flaky test",
				output: "Key finding: the retry counter is shared.",
				diagnostics: "Process exited after reporting the finding.",
				status: "failed",
				exitCode: 1,
			},
		],
	});
	const content = await fs.promises.readFile(path.join(root, artifacts[0].path), "utf8");
	assert.match(content, /## Key output[\s\S]*retry counter is shared/);
	assert.match(content, /## Failure diagnostics[\s\S]*Process exited/);
});

test("detects staging replacement between validation and content write", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const outside = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-staging-race-outside-"));
	t.after(() => fs.promises.rm(outside, { recursive: true, force: true }));
	const displaced = path.join(root, "displaced-staging");
	let unsupported: unknown;
	await assert.rejects(
		persistSubagentArtifacts({
			cwd: root,
			artifactDir: ".work/task/artifacts",
			jobId: "subagent-staging-race",
			results: [{ agent: "scout", task: "trace", output: "sensitive key fact", exitCode: 0 }],
			testHooks: {
				beforeContentWrite: async (pendingPath) => {
					const staging = path.dirname(pendingPath);
					try {
						await fs.promises.rename(staging, displaced);
						await fs.promises.symlink(outside, staging, process.platform === "win32" ? "junction" : "dir");
					} catch (error) {
						unsupported = error;
						throw error;
					}
				},
			},
		}),
	);
	if (unsupported instanceof Error && "code" in unsupported && (unsupported.code === "EPERM" || unsupported.code === "EACCES")) {
		t.skip("directory replacement is not permitted on this platform");
		return;
	}
	assert.deepEqual(await fs.promises.readdir(outside), []);
	for (const filename of await fs.promises.readdir(displaced)) {
		const content = await fs.promises.readFile(path.join(displaced, filename), "utf8");
		assert.equal(content, "", "a displaced pending file must be scrubbed before close");
	}
});

test("detects target replacement before commit without writing artifact data outside .work", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const outside = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-race-outside-"));
	t.after(() => fs.promises.rm(outside, { recursive: true, force: true }));
	const artifactDir = path.join(root, ".work", "task", "artifacts");
	const displaced = path.join(root, "displaced-artifacts");
	let unsupported: unknown;
	await assert.rejects(
		persistSubagentArtifacts({
			cwd: root,
			artifactDir: ".work/task/artifacts",
			jobId: "subagent-race",
			results: [{ agent: "scout", task: "trace", output: "sensitive key fact", exitCode: 0 }],
			testHooks: {
				beforeCommit: async () => {
					try {
						await fs.promises.rename(artifactDir, displaced);
						await fs.promises.symlink(outside, artifactDir, process.platform === "win32" ? "junction" : "dir");
					} catch (error) {
						unsupported = error;
						throw error;
					}
				},
			},
		}),
	);
	if (unsupported instanceof Error && "code" in unsupported && (unsupported.code === "EPERM" || unsupported.code === "EACCES")) {
		t.skip("directory replacement is not permitted on this platform");
		return;
	}
	assert.deepEqual(await fs.promises.readdir(outside), []);
	assert.deepEqual(await fs.promises.readdir(displaced), []);
	assert.doesNotMatch((await fs.promises.readdir(path.join(root, ".work"))).join("\n"), /artifact-staging/);
});

test("rejects symbolic-link components in artifact paths", async (t) => {
	const root = await fixture();
	t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
	const outside = await fs.promises.mkdtemp(path.join(os.tmpdir(), "subagent-artifacts-outside-"));
	t.after(() => fs.promises.rm(outside, { recursive: true, force: true }));
	await fs.promises.mkdir(path.join(root, ".work"));
	try {
		await fs.promises.symlink(outside, path.join(root, ".work", "linked"), process.platform === "win32" ? "junction" : "dir");
	} catch (error) {
		if (error instanceof Error && "code" in error && (error.code === "EPERM" || error.code === "EACCES")) {
			t.skip("creating symlinks is not permitted on this platform");
			return;
		}
		throw error;
	}
	await assert.rejects(
		persistSubagentArtifacts({
			cwd: root,
			artifactDir: ".work/linked/artifacts",
			jobId: "subagent-link",
			results: [{ agent: "scout", task: "trace", output: "result", exitCode: 0 }],
		}),
		/symbolic link/,
	);
	assert.deepEqual(await fs.promises.readdir(outside), []);
});
