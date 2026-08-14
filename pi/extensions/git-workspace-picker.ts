import { isAbsolute, resolve } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { createLocalBashOperations, isToolCallEventType } from "@earendil-works/pi-coding-agent";

type Worktree = {
	path: string;
	branch?: string;
	detached: boolean;
};

type WorkspaceOption = {
	label: string;
	root: string;
	branch?: string;
	kind: "worktree" | "branch";
};

type SavedSelection = {
	root: string;
	branch?: string;
	kind: WorkspaceOption["kind"];
};

const ACTION_INTENT =
	/\b(add|analy[sz]e|audit|build|change|check|commit|continue|create|debug|delete|deploy|document|edit|fix|implement|inspect|investigate|lint|make|merge|move|push|refactor|remove|rename|resolve|restore|revert|review|run|test|update|work on|write)\b/i;

function samePath(left: string, right: string): boolean {
	const normalize = (value: string) => resolve(value).replaceAll("\\", "/").replace(/\/$/, "");
	const [normalizedLeft, normalizedRight] = [normalize(left), normalize(right)];
	return process.platform === "win32"
		? normalizedLeft.toLowerCase() === normalizedRight.toLowerCase()
		: normalizedLeft === normalizedRight;
}

function shortenBranch(ref: string): string {
	return ref.startsWith("refs/heads/") ? ref.slice("refs/heads/".length) : ref;
}

function parseWorktrees(output: string): Worktree[] {
	const worktrees: Worktree[] = [];
	let current: Worktree | undefined;

	for (const field of output.split("\0")) {
		if (field.startsWith("worktree ")) {
			if (current) worktrees.push(current);
			current = { path: field.slice("worktree ".length), detached: false };
		} else if (current && field.startsWith("branch ")) {
			current.branch = shortenBranch(field.slice("branch ".length));
		} else if (current && field === "detached") {
			current.detached = true;
		}
	}
	if (current) worktrees.push(current);

	return worktrees;
}

function parseBranches(output: string): string[] {
	return output
		.split("\0")
		.map((line) => line.trim())
		.filter(Boolean)
		.sort((a, b) => a.localeCompare(b));
}

function shellQuote(value: string): string {
	return `'${value.replaceAll("'", `'"'"'`)}'`;
}

function isGitPreparationCommand(command: string): boolean {
	const segments = command
		.split(/(?:&&|\|\||[;\n])/)
		.map((part) => part.trim().replace(/^\(+|\)+$/g, "").trim())
		.filter(Boolean);
	return segments.length > 0 && segments.every((part) => /^(?:git\b|pwd\b|printf\b|echo\b)/i.test(part));
}

export default function gitWorkspacePicker(pi: ExtensionAPI) {
	let selectionArmed = false;
	let selectedRoot: string | undefined;
	let selectedBranch: string | undefined;
	let selectedKind: WorkspaceOption["kind"] | undefined;

	async function git(cwd: string, args: string[]) {
		return pi.exec("git", args, { cwd, timeout: 10_000 });
	}

	async function discoverOptions(ctx: ExtensionContext): Promise<WorkspaceOption[]> {
		const rootResult = await git(ctx.cwd, ["rev-parse", "--show-toplevel"]);
		if (rootResult.code !== 0) return [];

		const currentRoot = rootResult.stdout.trim();
		const [worktreeResult, branchResult] = await Promise.all([
			git(currentRoot, ["worktree", "list", "--porcelain", "-z"]),
			git(currentRoot, ["for-each-ref", "--format=%(refname)", "-z", "refs/heads"]),
		]);
		if (worktreeResult.code !== 0 || branchResult.code !== 0) return [];

		const worktrees = parseWorktrees(worktreeResult.stdout);
		const checkedOutBranches = new Set(worktrees.map((item) => item.branch).filter((item): item is string => !!item));
		const current = worktrees.find((item) => samePath(item.path, currentRoot));
		const orderedWorktrees = [
			...(current ? [current] : []),
			...worktrees.filter((item) => item !== current).sort((a, b) => a.path.localeCompare(b.path)),
		];

		const options: WorkspaceOption[] = orderedWorktrees.map((item) => {
			const marker = samePath(item.path, currentRoot) ? "current" : "worktree";
			const branch = item.branch ?? (item.detached ? "detached HEAD" : "unknown branch");
			return {
				label: `${marker}  •  ${branch}  •  ${item.path}`,
				root: item.path,
				branch: item.branch,
				kind: "worktree",
			};
		});

		for (const ref of parseBranches(branchResult.stdout)) {
			const branch = shortenBranch(ref);
			if (checkedOutBranches.has(branch)) continue;
			options.push({
				label: `branch   •  ${branch}  •  safely switch ${currentRoot}`,
				root: currentRoot,
				branch,
				kind: "branch",
			});
		}

		return options;
	}

	function updateStatus(ctx: ExtensionContext): void {
		if (!selectedRoot) {
			ctx.ui.setStatus("git-workspace", undefined);
			return;
		}
		const branch = selectedBranch ? ` (${selectedBranch})` : "";
		ctx.ui.setStatus("git-workspace", ctx.ui.theme.fg("accent", `workspace: ${selectedRoot}${branch}`));
	}

	async function chooseWorkspace(
		ctx: ExtensionContext,
	): Promise<"selected" | "cancelled" | "not-git"> {
		const options = await discoverOptions(ctx);
		if (options.length === 0) return "not-git";

		const choice = await ctx.ui.select(
			"Choose the branch or worktree for this task:",
			options.map((option) => option.label),
		);
		if (!choice) return "cancelled";

		const selected = options.find((option) => option.label === choice);
		if (!selected) return "cancelled";

		selectedRoot = selected.root;
		selectedBranch = selected.branch;
		selectedKind = selected.kind;
		selectionArmed = false;
		pi.appendEntry("git-workspace-selection", {
			root: selected.root,
			branch: selected.branch,
			kind: selected.kind,
		} satisfies SavedSelection);
		updateStatus(ctx);
		ctx.ui.notify(`Task workspace: ${selected.branch ?? "detached HEAD"} at ${selected.root}`, "info");
		return "selected";
	}

	async function selectedBranchIsReady(): Promise<boolean> {
		if (!selectedRoot || selectedKind !== "branch" || !selectedBranch) return true;
		const result = await git(selectedRoot, ["branch", "--show-current"]);
		return result.code === 0 && result.stdout.trim() === selectedBranch;
	}

	pi.registerCommand("workspace", {
		description: "Choose the Git branch or worktree for subsequent agent work",
		handler: async (_args, ctx) => {
			await ctx.waitForIdle();
			const result = await chooseWorkspace(ctx);
			if (result === "not-git") {
				ctx.ui.notify("The current directory is not inside a Git repository.", "warning");
			}
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		selectedRoot = undefined;
		selectedBranch = undefined;
		selectedKind = undefined;

		const saved = ctx.sessionManager
			.getEntries()
			.filter((entry) => entry.type === "custom" && entry.customType === "git-workspace-selection")
			.pop()?.data as SavedSelection | undefined;
		if (saved?.root && (saved.kind === "branch" || saved.kind === "worktree")) {
			selectedRoot = saved.root;
			selectedBranch = saved.branch;
			selectedKind = saved.kind;
		}

		const repositoryCheck = await git(ctx.cwd, ["rev-parse", "--is-inside-work-tree"]);
		const isGitRepository = repositoryCheck.code === 0 && repositoryCheck.stdout.trim() === "true";
		selectionArmed =
			isGitRepository &&
			!selectedRoot &&
			!ctx.sessionManager.getEntries().some((entry) => entry.type === "message" && entry.message.role === "user");
		updateStatus(ctx);
	});

	pi.on("input", async (event, ctx) => {
		if (
			!selectionArmed ||
			event.source !== "interactive" ||
			event.streamingBehavior !== undefined ||
			!ACTION_INTENT.test(event.text)
		) {
			return { action: "continue" as const };
		}

		if (!ctx.hasUI) return { action: "continue" as const };
		const result = await chooseWorkspace(ctx);
		if (result === "selected" || result === "not-git") {
			return { action: "continue" as const };
		}

		ctx.ui.setEditorText(event.text);
		ctx.ui.notify("Workspace selection cancelled; the task was returned to the editor.", "info");
		return { action: "handled" as const };
	});

	pi.on("before_agent_start", (event) => {
		if (!selectedRoot) return;

		const branchInstruction =
			selectedKind === "branch" && selectedBranch
				? `The user selected local branch ${JSON.stringify(selectedBranch)}, which was not checked out when selected. Before task work, perform the required session-start Git synchronization and safety gate, then switch the selected worktree to that branch only if safe. File and search tools remain blocked until that branch is checked out.`
				: `The user selected the existing worktree at ${JSON.stringify(selectedRoot)}${selectedBranch ? ` on branch ${JSON.stringify(selectedBranch)}` : ""}.`;

		return {
			systemPrompt: `${event.systemPrompt}\n\n## Selected Git workspace\n${branchInstruction}\nTreat ${JSON.stringify(selectedRoot)} as the authoritative task root. Relative file/search paths and shell commands are routed there, even if another cwd appears elsewhere in session metadata. Re-run Git status/remotes/tracking and follow the configured Git synchronization safety gate before editing or choosing a baseline. Discover and obey any AGENTS.md files applicable within the selected root.`,
		};
	});

	pi.on("tool_call", async (event) => {
		if (!selectedRoot) return;
		const branchReady = await selectedBranchIsReady();

		if (isToolCallEventType("bash", event)) {
			if (!branchReady && !isGitPreparationCommand(event.input.command)) {
				return {
					block: true,
					reason: `Workspace branch ${selectedBranch} is not checked out yet. Only Git inspection, synchronization, and switching commands are allowed until it is ready.`,
				};
			}
			event.input.command = `cd -- ${shellQuote(selectedRoot)} && (${event.input.command})`;
			return;
		}

		if (!branchReady) {
			return {
				block: true,
				reason: `Workspace branch ${selectedBranch} is not checked out yet. Complete the Git safety gate and switch branches using bash first.`,
			};
		}

		if (
			isToolCallEventType("read", event) ||
			isToolCallEventType("edit", event) ||
			isToolCallEventType("write", event)
		) {
			if (!isAbsolute(event.input.path)) event.input.path = resolve(selectedRoot, event.input.path);
			return;
		}

		if (
			isToolCallEventType("find", event) ||
			isToolCallEventType("grep", event) ||
			isToolCallEventType("ls", event)
		) {
			const input = event.input as { path?: string };
			input.path = input.path ? (isAbsolute(input.path) ? input.path : resolve(selectedRoot, input.path)) : selectedRoot;
		}
	});

	pi.on("user_bash", (_event, ctx) => {
		if (!selectedRoot) return;
		const local = createLocalBashOperations();
		return {
			operations: {
				exec(command, _cwd, options) {
					return local.exec(command, selectedRoot ?? ctx.cwd, options);
				},
			},
		};
	});
}
