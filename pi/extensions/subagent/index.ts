/**
 * Subagent Tool - Delegate tasks to specialized agents
 *
 * Spawns a separate `pi` process for each subagent invocation,
 * giving it an isolated context window.
 *
 * Supports three modes:
 *   - Single: { agent: "name", task: "..." }
 *   - Parallel: { tasks: [{ agent: "name", task: "..." }, ...] }
 *   - Chain: { chain: [{ agent: "name", task: "... {previous} ..." }, ...] }
 *   - Optional artifactDir: persist timestamped terminal outputs under repository .work/
 *
 * Uses JSON mode to capture structured output from subagents.
 */

import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { AgentToolResult } from "@earendil-works/pi-agent-core";
import type { Message } from "@earendil-works/pi-ai";
import { StringEnum } from "@earendil-works/pi-ai";
import {
	CONFIG_DIR_NAME,
	type ExtensionAPI,
	type ExtensionCommandContext,
	getAgentDir,
	getMarkdownTheme,
	withFileMutationQueue,
} from "@earendil-works/pi-coding-agent";
import { Container, Markdown, Spacer, Text } from "@earendil-works/pi-tui";
import { Type } from "typebox";
import { type AgentConfig, type AgentScope, discoverAgents, type SubagentThinkingLevel } from "./agents.ts";
import {
	persistSubagentArtifacts,
	resolveArtifactDirectory,
	type SubagentArtifactInput,
} from "./artifacts.ts";
import { ChildActivityTracker } from "./activity.ts";
import { ContextViewer, SUBAGENT_JOB_ENTRY_TYPE } from "./context-viewer.ts";

const MAX_PARALLEL_TASKS = 8;
const MAX_CONCURRENCY = 4;
const COLLAPSED_ITEM_COUNT = 10;
const PER_TASK_OUTPUT_CAP = 50 * 1024;

interface BackgroundJob {
	controller: AbortController;
	description: string;
	toolCallId: string;
	details?: SubagentDetails;
}

function formatTokens(count: number): string {
	if (count < 1000) return count.toString();
	if (count < 10000) return `${(count / 1000).toFixed(1)}k`;
	if (count < 1000000) return `${Math.round(count / 1000)}k`;
	return `${(count / 1000000).toFixed(1)}M`;
}

function formatUsageStats(
	usage: {
		input: number;
		output: number;
		cacheRead: number;
		cacheWrite: number;
		cost: number;
		contextTokens?: number;
		turns?: number;
	},
	model?: string,
): string {
	const parts: string[] = [];
	if (usage.turns) parts.push(`${usage.turns} turn${usage.turns > 1 ? "s" : ""}`);
	if (usage.input) parts.push(`↑${formatTokens(usage.input)}`);
	if (usage.output) parts.push(`↓${formatTokens(usage.output)}`);
	if (usage.cacheRead) parts.push(`R${formatTokens(usage.cacheRead)}`);
	if (usage.cacheWrite) parts.push(`W${formatTokens(usage.cacheWrite)}`);
	if (usage.cost) parts.push(`$${usage.cost.toFixed(4)}`);
	if (usage.contextTokens && usage.contextTokens > 0) {
		parts.push(`ctx:${formatTokens(usage.contextTokens)}`);
	}
	if (model) parts.push(model);
	return parts.join(" ");
}

function formatToolCall(
	toolName: string,
	args: Record<string, unknown>,
	themeFg: (color: any, text: string) => string,
): string {
	const shortenPath = (p: string) => {
		const home = os.homedir();
		return p.startsWith(home) ? `~${p.slice(home.length)}` : p;
	};

	switch (toolName) {
		case "bash": {
			const command = (args.command as string) || "...";
			const preview = command.length > 60 ? `${command.slice(0, 60)}...` : command;
			return themeFg("muted", "$ ") + themeFg("toolOutput", preview);
		}
		case "read": {
			const rawPath = (args.file_path || args.path || "...") as string;
			const filePath = shortenPath(rawPath);
			const offset = args.offset as number | undefined;
			const limit = args.limit as number | undefined;
			let text = themeFg("accent", filePath);
			if (offset !== undefined || limit !== undefined) {
				const startLine = offset ?? 1;
				const endLine = limit !== undefined ? startLine + limit - 1 : "";
				text += themeFg("warning", `:${startLine}${endLine ? `-${endLine}` : ""}`);
			}
			return themeFg("muted", "read ") + text;
		}
		case "write": {
			const rawPath = (args.file_path || args.path || "...") as string;
			const filePath = shortenPath(rawPath);
			const content = (args.content || "") as string;
			const lines = content.split("\n").length;
			let text = themeFg("muted", "write ") + themeFg("accent", filePath);
			if (lines > 1) text += themeFg("dim", ` (${lines} lines)`);
			return text;
		}
		case "edit": {
			const rawPath = (args.file_path || args.path || "...") as string;
			return themeFg("muted", "edit ") + themeFg("accent", shortenPath(rawPath));
		}
		case "ls": {
			const rawPath = (args.path || ".") as string;
			return themeFg("muted", "ls ") + themeFg("accent", shortenPath(rawPath));
		}
		case "find": {
			const pattern = (args.pattern || "*") as string;
			const rawPath = (args.path || ".") as string;
			return themeFg("muted", "find ") + themeFg("accent", pattern) + themeFg("dim", ` in ${shortenPath(rawPath)}`);
		}
		case "grep": {
			const pattern = (args.pattern || "") as string;
			const rawPath = (args.path || ".") as string;
			return (
				themeFg("muted", "grep ") +
				themeFg("accent", `/${pattern}/`) +
				themeFg("dim", ` in ${shortenPath(rawPath)}`)
			);
		}
		default: {
			const argsStr = JSON.stringify(args);
			const preview = argsStr.length > 50 ? `${argsStr.slice(0, 50)}...` : argsStr;
			return themeFg("accent", toolName) + themeFg("dim", ` ${preview}`);
		}
	}
}

export interface UsageStats {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	cost: number;
	contextTokens: number;
	contextWindow: number;
	contextPercent: number | null;
	turns: number;
}

export interface NestedInvocation {
	toolCallId: string;
	status: "running" | "complete" | "failed";
	details?: SubagentDetails;
}

export interface SingleResult {
	agent: string;
	agentSource: "user" | "project" | "unknown";
	task: string;
	activity?: string;
	thinking?: SubagentThinkingLevel;
	exitCode: number;
	pid?: number;
	status?: "queued" | "running" | "complete" | "failed" | "aborted";
	messages: Message[];
	stderr: string;
	usage: UsageStats;
	nested?: NestedInvocation[];
	model?: string;
	stopReason?: string;
	errorMessage?: string;
	step?: number;
	completedAt?: string;
	artifactPath?: string;
}

export interface SubagentDetails {
	mode: "single" | "parallel" | "chain";
	agentScope: AgentScope;
	projectAgentsDir: string | null;
	jobId?: string;
	artifactDir?: string;
	artifactError?: string;
	results: SingleResult[];
}

function emptyUsage(): UsageStats {
	return {
		input: 0,
		output: 0,
		cacheRead: 0,
		cacheWrite: 0,
		cost: 0,
		contextTokens: 0,
		contextWindow: 0,
		contextPercent: null,
		turns: 0,
	};
}

function summarizeNestedDetails(details: SubagentDetails, depth = 0, budget = { nodes: 100 }): SubagentDetails {
	return {
		mode: details.mode,
		agentScope: details.agentScope,
		projectAgentsDir: details.projectAgentsDir,
		jobId: details.jobId,
		artifactDir: details.artifactDir,
		artifactError: details.artifactError,
		results: details.results.flatMap((result) => {
			if (budget.nodes <= 0) return [];
			budget.nodes -= 1;
			return [{
				...result,
				messages: [],
				nested:
					depth >= 7 || budget.nodes <= 0
						? []
						: (result.nested ?? []).slice(0, budget.nodes).map((nested) => ({
								toolCallId: nested.toolCallId,
								status: nested.status,
								details: nested.details ? summarizeNestedDetails(nested.details, depth + 1, budget) : undefined,
							})),
			}];
		}),
	};
}

export function terminalizePendingDetails(details: SubagentDetails, error: unknown, aborted: boolean): SubagentDetails {
	const message = error instanceof Error ? error.message : String(error);
	return {
		...details,
		results: details.results.map((result) => {
			if (result.status !== "queued" && result.status !== "running" && result.exitCode !== -1) return result;
			return {
				...result,
				exitCode: 1,
				status: aborted ? "aborted" : "failed",
				activity: aborted ? "Aborted" : "Failed",
				stopReason: aborted ? "aborted" : "error",
				errorMessage: result.errorMessage ?? message,
				stderr: result.stderr || message,
				completedAt: result.completedAt ?? new Date().toISOString(),
			};
		}),
	};
}

function getFinalOutput(messages: Message[]): string {
	for (let i = messages.length - 1; i >= 0; i--) {
		const msg = messages[i];
		if (msg.role === "assistant") {
			for (const part of msg.content) {
				if (part.type === "text") return part.text;
			}
		}
	}
	return "";
}

function isFailedResult(result: SingleResult): boolean {
	return result.exitCode !== 0 || result.stopReason === "error" || result.stopReason === "aborted";
}

function getResultOutput(result: SingleResult): string {
	if (isFailedResult(result)) {
		return result.errorMessage || result.stderr || getFinalOutput(result.messages) || "(no output)";
	}
	return getFinalOutput(result.messages) || "(no output)";
}

function truncateParallelOutput(output: string): string {
	const byteLength = Buffer.byteLength(output, "utf8");
	if (byteLength <= PER_TASK_OUTPUT_CAP) return output;

	let truncated = output.slice(0, PER_TASK_OUTPUT_CAP);
	while (Buffer.byteLength(truncated, "utf8") > PER_TASK_OUTPUT_CAP) {
		truncated = truncated.slice(0, -1);
	}
	return `${truncated}\n\n[Output truncated: ${byteLength - Buffer.byteLength(truncated, "utf8")} bytes omitted. Full output preserved in tool details.]`;
}

type DisplayItem = { type: "text"; text: string } | { type: "toolCall"; name: string; args: Record<string, any> };

function getDisplayItems(messages: Message[]): DisplayItem[] {
	const items: DisplayItem[] = [];
	for (const msg of messages) {
		if (msg.role === "assistant") {
			for (const part of msg.content) {
				if (part.type === "text") items.push({ type: "text", text: part.text });
				else if (part.type === "toolCall") items.push({ type: "toolCall", name: part.name, args: part.arguments });
			}
		}
	}
	return items;
}

async function mapWithConcurrencyLimit<TIn, TOut>(
	items: TIn[],
	concurrency: number,
	fn: (item: TIn, index: number) => Promise<TOut>,
): Promise<TOut[]> {
	if (items.length === 0) return [];
	const limit = Math.max(1, Math.min(concurrency, items.length));
	const results: TOut[] = new Array(items.length);
	let nextIndex = 0;
	const workers = new Array(limit).fill(null).map(async () => {
		while (true) {
			const current = nextIndex++;
			if (current >= items.length) return;
			results[current] = await fn(items[current], current);
		}
	});
	await Promise.all(workers);
	return results;
}

async function writePromptToTempFile(agentName: string, prompt: string): Promise<{ dir: string; filePath: string }> {
	const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "pi-subagent-"));
	const safeName = agentName.replace(/[^\w.-]+/g, "_");
	const filePath = path.join(tmpDir, `prompt-${safeName}.md`);
	await withFileMutationQueue(filePath, async () => {
		await fs.promises.writeFile(filePath, prompt, { encoding: "utf-8", mode: 0o600 });
	});
	return { dir: tmpDir, filePath };
}

function getPiInvocation(args: string[]): { command: string; args: string[] } {
	const currentScript = process.argv[1];
	const isBunVirtualScript = currentScript?.startsWith("/$bunfs/root/");
	if (currentScript && !isBunVirtualScript && fs.existsSync(currentScript)) {
		return { command: process.execPath, args: [currentScript, ...args] };
	}

	const execName = path.basename(process.execPath).toLowerCase();
	const isGenericRuntime = /^(node|bun)(\.exe)?$/.test(execName);
	if (!isGenericRuntime) {
		return { command: process.execPath, args };
	}

	return { command: "pi", args };
}

type OnUpdateCallback = (partial: AgentToolResult<SubagentDetails>) => void;

async function runSingleAgent(
	defaultCwd: string,
	agents: AgentConfig[],
	agentName: string,
	task: string,
	cwd: string | undefined,
	step: number | undefined,
	signal: AbortSignal | undefined,
	onUpdate: OnUpdateCallback | undefined,
	makeDetails: (results: SingleResult[]) => SubagentDetails,
	resolveContextWindow: (provider: string | undefined, model: string | undefined) => number,
): Promise<SingleResult> {
	const agent = agents.find((a) => a.name === agentName);

	if (!agent) {
		const available = agents.map((a) => `"${a.name}"`).join(", ") || "none";
		return {
			agent: agentName,
			agentSource: "unknown",
			task,
			exitCode: 1,
			messages: [],
			stderr: `Unknown agent: "${agentName}". Available agents: ${available}.`,
			usage: emptyUsage(),
			status: "failed",
			activity: "Failed",
			step,
		};
	}

	const args: string[] = [
		"--mode",
		"json",
		"-p",
		"--no-session",
		"--thinking",
		agent.thinking,
		"--exclude-tools",
		"subagent",
	];
	if (agent.model) args.push("--model", agent.model);
	if (agent.tools && agent.tools.length > 0) args.push("--tools", agent.tools.join(","));

	let tmpPromptDir: string | null = null;
	let tmpPromptPath: string | null = null;

	const currentResult: SingleResult = {
		agent: agentName,
		agentSource: agent.source,
		task,
		exitCode: 0,
		messages: [],
		stderr: "",
		usage: emptyUsage(),
		status: "running",
		activity: `Starting ${task}`,
		thinking: agent.thinking,
		nested: [],
		model: agent.model,
		step,
	};

	const emitUpdate = () => {
		const details = makeDetails([currentResult]);
		onUpdate?.({
			content: [{ type: "text", text: getFinalOutput(currentResult.messages) || "(running...)" }],
			details,
		});
	};

	emitUpdate();

	try {
		if (agent.systemPrompt.trim()) {
			const tmp = await writePromptToTempFile(agent.name, agent.systemPrompt);
			tmpPromptDir = tmp.dir;
			tmpPromptPath = tmp.filePath;
			args.push("--append-system-prompt", tmpPromptPath);
		}

		args.push(`Task: ${task}`);
		let wasAborted = false;

		const exitCode = await new Promise<number>((resolve) => {
			const invocation = getPiInvocation(args);
			const proc = spawn(invocation.command, invocation.args, {
				cwd: cwd ?? defaultCwd,
				shell: false,
				stdio: ["ignore", "pipe", "pipe"],
			});
			currentResult.pid = proc.pid;
			emitUpdate();
			let buffer = "";
			let processClosed = false;
			let killTimer: ReturnType<typeof setTimeout> | undefined;
			const activityTracker = new ChildActivityTracker(task);

			const setActivity = (activity: string) => {
				if (currentResult.activity === activity) return;
				currentResult.activity = activity;
				emitUpdate();
			};

			const processLine = (line: string) => {
				if (!line.trim()) return;
				let event: any;
				try {
					event = JSON.parse(line);
				} catch {
					return;
				}

				const nextActivity = activityTracker.update(event);
				if (nextActivity) setActivity(nextActivity);

				if (event.type === "message_end" && event.message) {
					const msg = event.message as Message;
					currentResult.messages.push(msg);

					if (msg.role === "assistant") {
						currentResult.usage.turns++;
						const usage = msg.usage;
						if (usage) {
							currentResult.usage.input += usage.input || 0;
							currentResult.usage.output += usage.output || 0;
							currentResult.usage.cacheRead += usage.cacheRead || 0;
							currentResult.usage.cacheWrite += usage.cacheWrite || 0;
							currentResult.usage.cost += usage.cost?.total || 0;
							currentResult.usage.contextTokens =
								usage.totalTokens || usage.input + usage.output + usage.cacheRead + usage.cacheWrite;
						}
						const assistant = msg as Message & { provider?: string; model?: string };
						if (!currentResult.model && assistant.model) currentResult.model = assistant.model;
						currentResult.usage.contextWindow = resolveContextWindow(assistant.provider, assistant.model ?? currentResult.model);
						currentResult.usage.contextPercent =
							currentResult.usage.contextWindow > 0
								? (currentResult.usage.contextTokens / currentResult.usage.contextWindow) * 100
								: null;
						if (msg.stopReason) currentResult.stopReason = msg.stopReason;
						if (msg.errorMessage) currentResult.errorMessage = msg.errorMessage;
					}
					emitUpdate();
				}

				if (event.toolName === "subagent" && event.toolCallId) {
					const nested = currentResult.nested ?? (currentResult.nested = []);
					let invocation = nested.find((item) => item.toolCallId === event.toolCallId);
					if (!invocation) {
						invocation = { toolCallId: event.toolCallId, status: "running" };
						nested.push(invocation);
					}
					if (event.type === "tool_execution_update") {
						const details = event.partialResult?.details as SubagentDetails | undefined;
						if (details?.results) invocation.details = summarizeNestedDetails(details);
					}
					if (event.type === "tool_execution_end") {
						const details = event.result?.details as SubagentDetails | undefined;
						if (details?.results) invocation.details = summarizeNestedDetails(details);
						invocation.status = event.isError ? "failed" : "complete";
					}
					emitUpdate();
				}
			};

			proc.stdout.on("data", (data) => {
				buffer += data.toString();
				const lines = buffer.split("\n");
				buffer = lines.pop() || "";
				for (const line of lines) processLine(line);
			});

			proc.stderr.on("data", (data) => {
				currentResult.stderr += data.toString();
			});

			proc.on("close", (code) => {
				processClosed = true;
				if (killTimer) clearTimeout(killTimer);
				if (buffer.trim()) processLine(buffer);
				resolve(code ?? 0);
			});

			proc.on("error", () => {
				processClosed = true;
				if (killTimer) clearTimeout(killTimer);
				resolve(1);
			});

			if (signal) {
				const killProc = () => {
					wasAborted = true;
					if (processClosed) return;
					proc.kill("SIGTERM");
					killTimer = setTimeout(() => {
						if (!processClosed) proc.kill("SIGKILL");
					}, 5000);
				};
				if (signal.aborted) killProc();
				else signal.addEventListener("abort", killProc, { once: true });
			}
		});

		currentResult.exitCode = exitCode;
		currentResult.status = wasAborted ? "aborted" : exitCode === 0 && currentResult.stopReason !== "error" ? "complete" : "failed";
		currentResult.activity = wasAborted ? "Aborted" : currentResult.status === "complete" ? "Completed" : "Failed";
		currentResult.completedAt = new Date().toISOString();
		emitUpdate();
		if (wasAborted) throw new Error("Subagent was aborted");
		return currentResult;
	} finally {
		if (tmpPromptPath)
			try {
				fs.unlinkSync(tmpPromptPath);
			} catch {
				/* ignore */
			}
		if (tmpPromptDir)
			try {
				fs.rmdirSync(tmpPromptDir);
			} catch {
				/* ignore */
			}
	}
}

const TaskItem = Type.Object({
	agent: Type.String({ description: "Name of the agent to invoke" }),
	task: Type.String({ description: "Task to delegate to the agent" }),
	cwd: Type.Optional(Type.String({ description: "Working directory for the agent process" })),
});

const ChainItem = Type.Object({
	agent: Type.String({ description: "Name of the agent to invoke" }),
	task: Type.String({ description: "Task with optional {previous} placeholder for prior output" }),
	cwd: Type.Optional(Type.String({ description: "Working directory for the agent process" })),
});

const AgentScopeSchema = StringEnum(["user", "project", "both"] as const, {
	description: 'Which agent directories to use. Default: "user". Use "both" to include project-local agents.',
	default: "user",
});

const SubagentParams = Type.Object({
	agent: Type.Optional(Type.String({ description: "Name of the agent to invoke (for single mode)" })),
	task: Type.Optional(Type.String({ description: "Task to delegate (for single mode)" })),
	tasks: Type.Optional(Type.Array(TaskItem, { description: "Array of {agent, task} for parallel execution" })),
	chain: Type.Optional(Type.Array(ChainItem, { description: "Array of {agent, task} for sequential execution" })),
	agentScope: Type.Optional(AgentScopeSchema),
	confirmProjectAgents: Type.Optional(
		Type.Boolean({ description: "Prompt before running project-local agents. Default: true.", default: true }),
	),
	cwd: Type.Optional(Type.String({ description: "Working directory for the agent process (single mode)" })),
	artifactDir: Type.Optional(
		Type.String({
			description:
				"Repository-relative directory inside .work/ where timestamped final subagent outputs should be preserved",
		}),
	),
});

export default function (pi: ExtensionAPI) {
	const contextViewer = new ContextViewer();
	const backgroundJobs = new Map<string, BackgroundJob>();
	let nextJobNumber = 1;
	let runtimeActive = true;
	const availableUserAgents = discoverAgents(process.cwd(), "user").agents;
	const availableUserAgentNames = availableUserAgents.map((agent) => agent.name).join(", ") || "none";
	const availableUserAgentCatalog =
		availableUserAgents.map((agent) => `${agent.name} (${agent.description})`).join("; ") || "none";
	const handleContextViewerCommand = async (args: string, ctx: ExtensionCommandContext): Promise<void> => {
		const action = args.trim().toLowerCase() || "toggle";
		if (action === "open") contextViewer.open(ctx);
		else if (action === "close") contextViewer.close(ctx);
		else if (action === "toggle") contextViewer.toggle(ctx);
		else {
			ctx.ui.notify("Usage: /context-viewer [open|close|toggle]", "warning");
			return;
		}
		contextViewer.updatePrimary(ctx);
		ctx.ui.notify(`Context viewer ${contextViewer.isVisible() ? "opened" : "closed"}.`, "info");
	};

	pi.registerCommand("context-viewer", {
		description: "Open or close the primary/subagent context viewer (open|close|toggle)",
		handler: handleContextViewerCommand,
	});

	pi.registerCommand("subagents", {
		description: "List or cancel background subagent jobs: /subagents [cancel <id>|cancel-all]",
		handler: async (args, ctx) => {
			const [action, jobId] = args.trim().split(/\s+/, 2);
			if (action === "cancel-all") {
				for (const job of backgroundJobs.values()) job.controller.abort();
				ctx.ui.notify(`Cancelling ${backgroundJobs.size} subagent job(s).`, "info");
				return;
			}
			if (action === "cancel") {
				const job = jobId ? backgroundJobs.get(jobId) : undefined;
				if (!job) {
					ctx.ui.notify(`Unknown subagent job: ${jobId || "(missing id)"}`, "warning");
					return;
				}
				job.controller.abort();
				ctx.ui.notify(`Cancelling ${jobId}.`, "info");
				return;
			}
			if (backgroundJobs.size === 0) {
				ctx.ui.notify("No subagent jobs are running.", "info");
				return;
			}
			ctx.ui.notify(
				Array.from(backgroundJobs, ([id, job]) => `${id}: ${job.description}`).join("\n"),
				"info",
			);
		},
	});

	pi.on("session_start", (_event, ctx) => contextViewer.restoreFromBranch(ctx));
	pi.on("agent_start", (_event, ctx) => contextViewer.updatePrimary(ctx, true));
	pi.on("message_end", (_event, ctx) => contextViewer.updatePrimary(ctx));
	pi.on("agent_settled", (_event, ctx) => contextViewer.updatePrimary(ctx, false));
	pi.on("model_select", (_event, ctx) => contextViewer.updatePrimary(ctx));
	pi.on("session_tree", (_event, ctx) => contextViewer.restoreFromBranch(ctx));
	pi.on("session_shutdown", (_event, ctx) => {
		for (const job of backgroundJobs.values()) {
			if (job.details) {
				const terminalDetails = terminalizePendingDetails(job.details, new Error("Session shutdown"), true);
				pi.appendEntry(SUBAGENT_JOB_ENTRY_TYPE, {
					toolCallId: job.toolCallId,
					details: summarizeNestedDetails(terminalDetails),
				});
			}
			job.controller.abort();
		}
		runtimeActive = false;
		backgroundJobs.clear();
		contextViewer.close(ctx);
	});

	pi.registerTool({
		name: "subagent",
		label: "Subagent",
		description: [
			`Available user agents: ${availableUserAgentCatalog}. Use these exact names; scout is the reconnaissance/exploration agent.`,
			"Delegate tasks to specialized subagents with isolated context. Delegation runs in the background and completion automatically resumes the parent in a follow-up turn.",
			"For substantive long-running work, set artifactDir to a repository-relative .work/<task>/artifacts directory to preserve timestamped final outputs outside model context.",
			"Modes: single (agent + task), parallel (tasks array), chain (sequential with {previous} placeholder).",
			`Default agent scope is "user" (from ${path.join(getAgentDir(), "agents")}).`,
			`To enable project-local agents in ${CONFIG_DIR_NAME}/agents, set agentScope: "both" (or "project").`,
		].join(" "),
		promptSnippet: `Delegate work to available agents: ${availableUserAgentNames}`,
		promptGuidelines: [
			`For subagent calls using the default user scope, use only these advertised agent names: ${availableUserAgentNames}. Use scout for reconnaissance or exploration.`,
			"The subagent tool runs asynchronously. After delegation, continue only independent work; do not duplicate or overlap the delegated scope. A completion message will automatically start a follow-up turn so you can pick the result back up.",
			"For substantive delegated work whose findings must survive parent compaction, set subagent artifactDir to the active task's .work/<task>/artifacts directory; preserve final key output, then fold verified facts into the latest cumulative task checkpoint.",
		],
		parameters: SubagentParams,

		async execute(toolCallId, params, _signal, _onUpdate, ctx) {
			const agentScope: AgentScope = params.agentScope ?? "user";
			const discovery = discoverAgents(ctx.cwd, agentScope);
			const agents = discovery.agents;
			const confirmProjectAgents = params.confirmProjectAgents ?? true;

			const hasChain = (params.chain?.length ?? 0) > 0;
			const hasTasks = (params.tasks?.length ?? 0) > 0;
			const hasSingle = Boolean(params.agent && params.task);
			const modeCount = Number(hasChain) + Number(hasTasks) + Number(hasSingle);
			let detailsJobId: string | undefined;
			let latestDetails: SubagentDetails | undefined;
			let latestArtifactError: string | undefined;

			const buildDetails =
				(mode: "single" | "parallel" | "chain") =>
				(results: SingleResult[]): SubagentDetails => ({
					mode,
					agentScope,
					projectAgentsDir: discovery.projectAgentsDir,
					jobId: detailsJobId,
					artifactDir: params.artifactDir,
					artifactError: latestArtifactError,
					results,
				});
			const makeDetails =
				(mode: "single" | "parallel" | "chain") =>
				(results: SingleResult[]): SubagentDetails => {
					const details = buildDetails(mode)(results);
					latestDetails = details;
					if (detailsJobId) {
						const job = backgroundJobs.get(detailsJobId);
						if (job) job.details = details;
					}
					contextViewer.updateInvocation(toolCallId, details);
					return details;
				};

			const resolveContextWindow = (provider: string | undefined, model: string | undefined): number => {
				if (!model) return 0;
				if (provider) return ctx.modelRegistry.find(provider, model)?.contextWindow ?? 0;
				const slash = model.indexOf("/");
				if (slash > 0) return ctx.modelRegistry.find(model.slice(0, slash), model.slice(slash + 1))?.contextWindow ?? 0;
				return ctx.model?.id === model ? ctx.model.contextWindow : 0;
			};

			const preserveArtifacts = async (details: SubagentDetails): Promise<string[]> => {
				if (!params.artifactDir) return [];
				const completedResults = details.results.filter((result) => result.completedAt !== undefined);
				const artifactInputs: SubagentArtifactInput[] = completedResults.map((result) => ({
					agent: result.agent,
					// Chain execution expands {previous} in result.task. Preserve the
					// authored task instead of duplicating prior agent output here.
					task: result.step ? (params.chain?.[result.step - 1]?.task ?? result.task) : result.task,
					output: getResultOutput(result),
					completedAt: result.completedAt,
					status: result.status,
					exitCode: result.exitCode,
					stopReason: result.stopReason,
					errorMessage: result.errorMessage,
					model: result.model,
					turns: result.usage.turns,
				}));
				const artifacts = await persistSubagentArtifacts({
					cwd: ctx.cwd,
					artifactDir: params.artifactDir,
					jobId: details.jobId ?? "subagent",
					results: artifactInputs,
				});
				for (let index = 0; index < artifacts.length; index += 1) {
					completedResults[index].artifactPath = artifacts[index].path;
				}
				return artifacts.map((artifact) => artifact.path);
			};

			if (modeCount !== 1) {
				const available = agents.map((a) => `${a.name} (${a.source})`).join(", ") || "none";
				return {
					content: [
						{
							type: "text",
							text: `Invalid parameters. Provide exactly one mode.\nAvailable agents: ${available}`,
						},
					],
					details: makeDetails("single")([]),
				};
			}
			if (hasTasks && params.tasks!.length > MAX_PARALLEL_TASKS) {
				return {
					content: [
						{
							type: "text",
							text: `Too many parallel tasks (${params.tasks!.length}). Max is ${MAX_PARALLEL_TASKS}.`,
						},
					],
					details: makeDetails("parallel")([]),
				};
			}
			if (params.artifactDir) {
				try {
					await resolveArtifactDirectory(ctx.cwd, params.artifactDir);
				} catch (error) {
					const message = error instanceof Error ? error.message : String(error);
					return {
						content: [{ type: "text", text: `Invalid artifactDir: ${message}` }],
						details: makeDetails(hasChain ? "chain" : hasTasks ? "parallel" : "single")([]),
					};
				}
			}

			if ((agentScope === "project" || agentScope === "both") && confirmProjectAgents && ctx.hasUI) {
				const requestedAgentNames = new Set<string>();
				if (params.chain) for (const step of params.chain) requestedAgentNames.add(step.agent);
				if (params.tasks) for (const t of params.tasks) requestedAgentNames.add(t.agent);
				if (params.agent) requestedAgentNames.add(params.agent);

				const projectAgentsRequested = Array.from(requestedAgentNames)
					.map((name) => agents.find((a) => a.name === name))
					.filter((a): a is AgentConfig => a?.source === "project");

				if (projectAgentsRequested.length > 0) {
					const names = projectAgentsRequested.map((a) => a.name).join(", ");
					const dir = discovery.projectAgentsDir ?? "(unknown)";
					const ok = await ctx.ui.confirm(
						"Run project-local agents?",
						`Agents: ${names}\nSource: ${dir}\n\nProject agents are repo-controlled. Only continue for trusted repositories.`,
					);
					if (!ok)
						return {
							content: [{ type: "text", text: "Canceled: project-local agents not approved." }],
							details: makeDetails(hasChain ? "chain" : hasTasks ? "parallel" : "single")([]),
						};
				}
			}

			const jobId = `subagent-${nextJobNumber++}`;
			detailsJobId = jobId;
			const controller = new AbortController();
			const taskPreview = params.task && params.task.length > 120 ? `${params.task.slice(0, 120)}...` : params.task;
			const invocationDescription = params.chain?.length
				? `chain (${params.chain.length} steps)`
				: params.tasks?.length
					? `parallel (${params.tasks.length} tasks)`
					: `${params.agent}: ${taskPreview}`;
			backgroundJobs.set(jobId, { controller, description: invocationDescription, toolCallId });

			const queuedResult = (agentName: string, task: string, step?: number): SingleResult => {
				const agent = agents.find((candidate) => candidate.name === agentName);
				return {
					agent: agentName,
					agentSource: agent?.source ?? "unknown",
					task,
					exitCode: -1,
					messages: [],
					stderr: "",
					usage: emptyUsage(),
					status: "queued",
					activity: `Queued: ${task}`,
					thinking: agent?.thinking,
					step,
				};
			};
			const initialMode = hasChain ? "chain" : hasTasks ? "parallel" : "single";
			const initialResults = params.chain?.length
				? params.chain.map((item, index) => queuedResult(item.agent, item.task, index + 1))
				: params.tasks?.length
					? params.tasks.map((item) => queuedResult(item.agent, item.task))
					: [queuedResult(params.agent!, params.task!)];
			const initialDetails = makeDetails(initialMode)(initialResults);
			contextViewer.startInvocation(toolCallId, initialDetails);
			if (ctx.mode === "tui") contextViewer.open(ctx, true);
			contextViewer.updatePrimary(ctx);

			const executeInvocation = async (): Promise<AgentToolResult<SubagentDetails>> => {
			if (params.chain && params.chain.length > 0) {
				const results: SingleResult[] = [];
				let previousOutput = "";

				for (let i = 0; i < params.chain.length; i++) {
					const step = params.chain[i];
					const taskWithContext = step.task.replace(/\{previous\}/g, previousOutput);

					// Create update callback that includes all previous results
					const chainUpdate: OnUpdateCallback = (partial) => {
						// Combine completed results with the current result and queued future steps.
						const currentResult = partial.details?.results[0];
						if (currentResult) makeDetails("chain")([...results, currentResult, ...initialResults.slice(i + 1)]);
					};

					const result = await runSingleAgent(
						ctx.cwd,
						agents,
						step.agent,
						taskWithContext,
						step.cwd,
						i + 1,
						controller.signal,
						chainUpdate,
						buildDetails("chain"),
						resolveContextWindow,
					);
					results.push(result);

					const isError = isFailedResult(result);
					if (isError) {
						const errorMsg = getResultOutput(result);
						const skippedReason = `Skipped because chain step ${i + 1} (${step.agent}) failed`;
						const skippedResults = initialResults.slice(i + 1).map((queued) => ({
							...queued,
							exitCode: 1,
							status: "aborted" as const,
							activity: "Skipped after earlier chain failure",
							stopReason: "aborted" as const,
							errorMessage: skippedReason,
							stderr: skippedReason,
							completedAt: new Date().toISOString(),
						}));
						return {
							content: [{ type: "text", text: `Chain stopped at step ${i + 1} (${step.agent}): ${errorMsg}` }],
							details: makeDetails("chain")([...results, ...skippedResults]),
						};
					}
					previousOutput = getFinalOutput(result.messages);
				}
				return {
					content: [{ type: "text", text: getFinalOutput(results[results.length - 1].messages) || "(no output)" }],
					details: makeDetails("chain")(results),
				};
			}

			if (params.tasks && params.tasks.length > 0) {
				// Track all results for streaming updates, preserving queued tasks.
				const allResults = initialResults.map((result) => ({ ...result }));

				const emitParallelUpdate = () => {
					makeDetails("parallel")([...allResults]);
				};

				const results = await mapWithConcurrencyLimit(params.tasks, MAX_CONCURRENCY, async (t, index) => {
					try {
						if (controller.signal.aborted) throw new Error("Subagent was aborted");
						const result = await runSingleAgent(
							ctx.cwd,
							agents,
							t.agent,
							t.task,
							t.cwd,
							undefined,
							controller.signal,
							// Per-task update callback
							(partial) => {
								if (partial.details?.results[0]) {
									allResults[index] = partial.details.results[0];
									emitParallelUpdate();
								}
							},
							buildDetails("parallel"),
							resolveContextWindow,
						);
						allResults[index] = result;
						emitParallelUpdate();
						return result;
					} catch (error) {
						const message = error instanceof Error ? error.message : String(error);
						const failedResult: SingleResult = {
							...allResults[index],
							exitCode: 1,
							status: controller.signal.aborted ? "aborted" : "failed",
							activity: controller.signal.aborted ? "Aborted" : "Failed",
							stopReason: controller.signal.aborted ? "aborted" : "error",
							errorMessage: allResults[index].errorMessage ?? message,
							stderr: allResults[index].stderr || message,
							completedAt: new Date().toISOString(),
						};
						allResults[index] = failedResult;
						emitParallelUpdate();
						return failedResult;
					}
				});

				const successCount = results.filter((r) => !isFailedResult(r)).length;
				const summaries = results.map((r) => {
					const output = truncateParallelOutput(getResultOutput(r));
					const status = isFailedResult(r)
						? `failed${r.stopReason && r.stopReason !== "end" ? ` (${r.stopReason})` : ""}`
						: "completed";
					return `### [${r.agent}] ${status}\n\n${output}`;
				});
				return {
					content: [
						{
							type: "text",
							text: `Parallel: ${successCount}/${results.length} succeeded\n\n${summaries.join("\n\n---\n\n")}`,
						},
					],
					details: makeDetails("parallel")(results),
				};
			}

			if (params.agent && params.task) {
				const result = await runSingleAgent(
					ctx.cwd,
					agents,
					params.agent,
					params.task,
					params.cwd,
					undefined,
					controller.signal,
					(partial) => {
						const currentResult = partial.details?.results[0];
						if (currentResult) makeDetails("single")([currentResult]);
					},
					buildDetails("single"),
					resolveContextWindow,
				);
				const isError = isFailedResult(result);
				if (isError) {
					const errorMsg = getResultOutput(result);
					return {
						content: [{ type: "text", text: `Agent ${result.stopReason || "failed"}: ${errorMsg}` }],
						details: makeDetails("single")([result]),
					};
				}
				return {
					content: [{ type: "text", text: getFinalOutput(result.messages) || "(no output)" }],
					details: makeDetails("single")([result]),
				};
			}

			const available = agents.map((a) => `${a.name} (${a.source})`).join(", ") || "none";
			return {
				content: [{ type: "text", text: `Invalid parameters. Available agents: ${available}` }],
				details: makeDetails("single")([]),
			};
			};

			void Promise.resolve()
				.then(executeInvocation)
				.then(async (result) => {
					backgroundJobs.delete(jobId);
					if (!runtimeActive) return;
					let artifactNotice = "";
					if (result.details && params.artifactDir) {
						try {
							const artifactPaths = await preserveArtifacts(result.details);
							artifactNotice = artifactPaths.length
								? `\n\nDurable subagent artifacts:\n${artifactPaths.map((artifactPath) => `- ${artifactPath}`).join("\n")}\n\nFold verified key facts and these paths into the latest cumulative .work task checkpoint; recovery should read that checkpoint first, not every artifact.`
								: "";
						} catch (error) {
							latestArtifactError = error instanceof Error ? error.message : String(error);
							result.details.artifactError = latestArtifactError;
							artifactNotice = `\n\nArtifact persistence failed: ${latestArtifactError}. Preserve the key result in the latest cumulative .work task checkpoint now.`;
						}
					}
					if (result.details) {
						pi.appendEntry(SUBAGENT_JOB_ENTRY_TYPE, {
							toolCallId,
							details: summarizeNestedDetails(result.details),
						});
					}
					const output = result.content
						.filter((part): part is { type: "text"; text: string } => part.type === "text")
						.map((part) => part.text)
						.join("\n") || "(no output)";
					const failed = result.details?.results.some(isFailedResult) ?? false;
					const status = failed ? "failed" : "completed";
					pi.sendMessage(
						{
							customType: "subagent-completion",
							content: `Background subagent job ${jobId} ${status}.\n\n${output}${artifactNotice}\n\nPick up this delegated result now.`,
							display: true,
							details: { jobId, result: result.details },
						},
						{ triggerTurn: true, deliverAs: "followUp" },
					);
				})
				.catch(async (error: unknown) => {
					backgroundJobs.delete(jobId);
					if (!runtimeActive) return;
					let artifactNotice = "";
					if (latestDetails) {
						const terminalDetails = terminalizePendingDetails(latestDetails, error, controller.signal.aborted);
						latestDetails = terminalDetails;
						contextViewer.updateInvocation(toolCallId, terminalDetails);
						if (params.artifactDir) {
							try {
								const artifactPaths = await preserveArtifacts(terminalDetails);
								artifactNotice = artifactPaths.length
									? `\nDurable partial artifacts:\n${artifactPaths.map((artifactPath) => `- ${artifactPath}`).join("\n")}`
									: "";
							} catch (artifactError) {
								latestArtifactError = artifactError instanceof Error ? artifactError.message : String(artifactError);
								terminalDetails.artifactError = latestArtifactError;
								artifactNotice = `\nArtifact persistence also failed: ${latestArtifactError}`;
							}
						}
						pi.appendEntry(SUBAGENT_JOB_ENTRY_TYPE, {
							toolCallId,
							details: summarizeNestedDetails(terminalDetails),
						});
					}
					const message = error instanceof Error ? error.message : String(error);
					pi.sendMessage(
						{
							customType: "subagent-completion",
							content: `Background subagent job ${jobId} failed: ${message}${artifactNotice}`,
							display: true,
							details: { jobId, result: latestDetails },
						},
						{ triggerTurn: true, deliverAs: "followUp" },
					);
				});

			return {
				content: [
					{
						type: "text",
						text: `Delegated as background job ${jobId}. Do not wait or duplicate its scope; continue independent work. Its completion will automatically resume you in a follow-up turn.${params.artifactDir ? ` Final outputs will be preserved under ${params.artifactDir}.` : ""}`,
					},
				],
				details: makeDetails(initialMode)(initialResults),
			};
		},

		renderCall(args, theme, _context) {
			const scope: AgentScope = args.agentScope ?? "user";
			if (args.chain && args.chain.length > 0) {
				let text =
					theme.fg("toolTitle", theme.bold("subagent ")) +
					theme.fg("accent", `chain (${args.chain.length} steps)`) +
					theme.fg("muted", ` [${scope}]`);
				for (let i = 0; i < Math.min(args.chain.length, 3); i++) {
					const step = args.chain[i];
					// Clean up {previous} placeholder for display
					const cleanTask = step.task.replace(/\{previous\}/g, "").trim();
					const preview = cleanTask.length > 40 ? `${cleanTask.slice(0, 40)}...` : cleanTask;
					text +=
						"\n  " +
						theme.fg("muted", `${i + 1}.`) +
						" " +
						theme.fg("accent", step.agent) +
						theme.fg("dim", ` ${preview}`);
				}
				if (args.chain.length > 3) text += `\n  ${theme.fg("muted", `... +${args.chain.length - 3} more`)}`;
				return new Text(text, 0, 0);
			}
			if (args.tasks && args.tasks.length > 0) {
				let text =
					theme.fg("toolTitle", theme.bold("subagent ")) +
					theme.fg("accent", `parallel (${args.tasks.length} tasks)`) +
					theme.fg("muted", ` [${scope}]`);
				for (const t of args.tasks.slice(0, 3)) {
					const preview = t.task.length > 40 ? `${t.task.slice(0, 40)}...` : t.task;
					text += `\n  ${theme.fg("accent", t.agent)}${theme.fg("dim", ` ${preview}`)}`;
				}
				if (args.tasks.length > 3) text += `\n  ${theme.fg("muted", `... +${args.tasks.length - 3} more`)}`;
				return new Text(text, 0, 0);
			}
			const agentName = args.agent || "...";
			const preview = args.task ? (args.task.length > 60 ? `${args.task.slice(0, 60)}...` : args.task) : "...";
			let text =
				theme.fg("toolTitle", theme.bold("subagent ")) +
				theme.fg("accent", agentName) +
				theme.fg("muted", ` [${scope}]`);
			text += `\n  ${theme.fg("dim", preview)}`;
			return new Text(text, 0, 0);
		},

		renderResult(result, { expanded }, theme, _context) {
			const details = result.details as SubagentDetails | undefined;
			if (!details || details.results.length === 0) {
				const text = result.content[0];
				return new Text(text?.type === "text" ? text.text : "(no output)", 0, 0);
			}

			const mdTheme = getMarkdownTheme();

			const renderDisplayItems = (items: DisplayItem[], limit?: number) => {
				const toShow = limit ? items.slice(-limit) : items;
				const skipped = limit && items.length > limit ? items.length - limit : 0;
				let text = "";
				if (skipped > 0) text += theme.fg("muted", `... ${skipped} earlier items\n`);
				for (const item of toShow) {
					if (item.type === "text") {
						const preview = expanded ? item.text : item.text.split("\n").slice(0, 3).join("\n");
						text += `${theme.fg("toolOutput", preview)}\n`;
					} else {
						text += `${theme.fg("muted", "→ ") + formatToolCall(item.name, item.args, theme.fg.bind(theme))}\n`;
					}
				}
				return text.trimEnd();
			};

			if (details.mode === "single" && details.results.length === 1) {
				const r = details.results[0];
				const isQueued = r.status === "queued";
				if (isQueued) {
					const job = details.jobId ? ` ${theme.fg("accent", details.jobId)}` : "";
					return new Text(
						`${theme.fg("warning", "○")} ${theme.fg("toolTitle", theme.bold(r.agent))}${job}\n${theme.fg("muted", "Running in background · live progress shown below the editor")}`,
						0,
						0,
					);
				}
				const isError = isFailedResult(r);
				const icon = isError ? theme.fg("error", "✗") : theme.fg("success", "✓");
				const displayItems = getDisplayItems(r.messages);
				const finalOutput = getFinalOutput(r.messages);

				if (expanded) {
					const container = new Container();
					let header = `${icon} ${theme.fg("toolTitle", theme.bold(r.agent))}${theme.fg("muted", ` (${r.agentSource})`)}`;
					if (isError && r.stopReason) header += ` ${theme.fg("error", `[${r.stopReason}]`)}`;
					container.addChild(new Text(header, 0, 0));
					if (isError && r.errorMessage)
						container.addChild(new Text(theme.fg("error", `Error: ${r.errorMessage}`), 0, 0));
					container.addChild(new Spacer(1));
					container.addChild(new Text(theme.fg("muted", "─── Task ───"), 0, 0));
					container.addChild(new Text(theme.fg("dim", r.task), 0, 0));
					container.addChild(new Spacer(1));
					container.addChild(new Text(theme.fg("muted", "─── Output ───"), 0, 0));
					if (displayItems.length === 0 && !finalOutput) {
						container.addChild(new Text(theme.fg("muted", "(no output)"), 0, 0));
					} else {
						for (const item of displayItems) {
							if (item.type === "toolCall")
								container.addChild(
									new Text(
										theme.fg("muted", "→ ") + formatToolCall(item.name, item.args, theme.fg.bind(theme)),
										0,
										0,
									),
								);
						}
						if (finalOutput) {
							container.addChild(new Spacer(1));
							container.addChild(new Markdown(finalOutput.trim(), 0, 0, mdTheme));
						}
					}
					const usageStr = formatUsageStats(r.usage, r.model);
					if (usageStr) {
						container.addChild(new Spacer(1));
						container.addChild(new Text(theme.fg("dim", usageStr), 0, 0));
					}
					return container;
				}

				let text = `${icon} ${theme.fg("toolTitle", theme.bold(r.agent))}${theme.fg("muted", ` (${r.agentSource})`)}`;
				if (isError && r.stopReason) text += ` ${theme.fg("error", `[${r.stopReason}]`)}`;
				if (isError && r.errorMessage) text += `\n${theme.fg("error", `Error: ${r.errorMessage}`)}`;
				else if (displayItems.length === 0) text += `\n${theme.fg("muted", "(no output)")}`;
				else {
					text += `\n${renderDisplayItems(displayItems, COLLAPSED_ITEM_COUNT)}`;
					if (displayItems.length > COLLAPSED_ITEM_COUNT) text += `\n${theme.fg("muted", "(Ctrl+O to expand)")}`;
				}
				const usageStr = formatUsageStats(r.usage, r.model);
				if (usageStr) text += `\n${theme.fg("dim", usageStr)}`;
				return new Text(text, 0, 0);
			}

			const aggregateUsage = (results: SingleResult[]) => {
				const total = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: 0, turns: 0 };
				for (const r of results) {
					total.input += r.usage.input;
					total.output += r.usage.output;
					total.cacheRead += r.usage.cacheRead;
					total.cacheWrite += r.usage.cacheWrite;
					total.cost += r.usage.cost;
					total.turns += r.usage.turns;
				}
				return total;
			};

			if (details.mode === "chain") {
				const pendingCount = details.results.filter(
					(r) => r.status === "queued" || r.status === "running" || r.exitCode === -1,
				).length;
				const successCount = details.results.filter(
					(r) => r.exitCode !== -1 && !isFailedResult(r),
				).length;
				const failCount = details.results.length - pendingCount - successCount;
				const icon = pendingCount > 0
					? theme.fg("warning", "⏳")
					: failCount > 0
						? theme.fg("error", "✗")
						: theme.fg("success", "✓");
				const chainStatus = pendingCount > 0
					? `${successCount + failCount}/${details.results.length} done, ${pendingCount} pending`
					: `${successCount}/${details.results.length} steps`;
				const chainResultIcon = (result: SingleResult): string => {
					if (result.status === "queued") return theme.fg("muted", "○");
					if (result.status === "running" || result.exitCode === -1) return theme.fg("warning", "●");
					return isFailedResult(result) ? theme.fg("error", "✗") : theme.fg("success", "✓");
				};

				if (expanded) {
					const container = new Container();
					container.addChild(
						new Text(
							icon +
								" " +
								theme.fg("toolTitle", theme.bold("chain ")) +
								theme.fg("accent", chainStatus),
							0,
							0,
						),
					);

					for (const r of details.results) {
						const rIcon = chainResultIcon(r);
						const displayItems = getDisplayItems(r.messages);
						const finalOutput = getFinalOutput(r.messages);

						container.addChild(new Spacer(1));
						container.addChild(
							new Text(
								`${theme.fg("muted", `─── Step ${r.step}: `) + theme.fg("accent", r.agent)} ${rIcon}`,
								0,
								0,
							),
						);
						container.addChild(new Text(theme.fg("muted", "Task: ") + theme.fg("dim", r.task), 0, 0));

						// Show tool calls
						for (const item of displayItems) {
							if (item.type === "toolCall") {
								container.addChild(
									new Text(
										theme.fg("muted", "→ ") + formatToolCall(item.name, item.args, theme.fg.bind(theme)),
										0,
										0,
									),
								);
							}
						}

						// Show final output as markdown
						if (finalOutput) {
							container.addChild(new Spacer(1));
							container.addChild(new Markdown(finalOutput.trim(), 0, 0, mdTheme));
						}

						const stepUsage = formatUsageStats(r.usage, r.model);
						if (stepUsage) container.addChild(new Text(theme.fg("dim", stepUsage), 0, 0));
					}

					const usageStr = formatUsageStats(aggregateUsage(details.results));
					if (usageStr) {
						container.addChild(new Spacer(1));
						container.addChild(new Text(theme.fg("dim", `Total: ${usageStr}`), 0, 0));
					}
					return container;
				}

				// Collapsed view
				let text =
					icon +
					" " +
					theme.fg("toolTitle", theme.bold("chain ")) +
					theme.fg("accent", chainStatus);
				for (const r of details.results) {
					const rIcon = chainResultIcon(r);
					const displayItems = getDisplayItems(r.messages);
					text += `\n\n${theme.fg("muted", `─── Step ${r.step}: `)}${theme.fg("accent", r.agent)} ${rIcon}`;
					if (displayItems.length === 0) {
						const emptyLabel = r.status === "queued" ? "(queued...)" : r.status === "running" ? "(running...)" : "(no output)";
						text += `\n${theme.fg("muted", emptyLabel)}`;
					} else text += `\n${renderDisplayItems(displayItems, 5)}`;
				}
				const usageStr = formatUsageStats(aggregateUsage(details.results));
				if (usageStr) text += `\n\n${theme.fg("dim", `Total: ${usageStr}`)}`;
				text += `\n${theme.fg("muted", "(Ctrl+O to expand)")}`;
				return new Text(text, 0, 0);
			}

			if (details.mode === "parallel") {
				const running = details.results.filter((r) => r.exitCode === -1).length;
				const successCount = details.results.filter((r) => r.exitCode !== -1 && !isFailedResult(r)).length;
				const failCount = details.results.filter((r) => r.exitCode !== -1 && isFailedResult(r)).length;
				const isRunning = running > 0;
				const icon = isRunning
					? theme.fg("warning", "⏳")
					: failCount > 0
						? theme.fg("warning", "◐")
						: theme.fg("success", "✓");
				const status = isRunning
					? `${successCount + failCount}/${details.results.length} done, ${running} running`
					: `${successCount}/${details.results.length} tasks`;

				if (expanded && !isRunning) {
					const container = new Container();
					container.addChild(
						new Text(
							`${icon} ${theme.fg("toolTitle", theme.bold("parallel "))}${theme.fg("accent", status)}`,
							0,
							0,
						),
					);

					for (const r of details.results) {
						const rIcon = isFailedResult(r) ? theme.fg("error", "✗") : theme.fg("success", "✓");
						const displayItems = getDisplayItems(r.messages);
						const finalOutput = getFinalOutput(r.messages);

						container.addChild(new Spacer(1));
						container.addChild(
							new Text(`${theme.fg("muted", "─── ") + theme.fg("accent", r.agent)} ${rIcon}`, 0, 0),
						);
						container.addChild(new Text(theme.fg("muted", "Task: ") + theme.fg("dim", r.task), 0, 0));

						// Show tool calls
						for (const item of displayItems) {
							if (item.type === "toolCall") {
								container.addChild(
									new Text(
										theme.fg("muted", "→ ") + formatToolCall(item.name, item.args, theme.fg.bind(theme)),
										0,
										0,
									),
								);
							}
						}

						// Show final output as markdown
						if (finalOutput) {
							container.addChild(new Spacer(1));
							container.addChild(new Markdown(finalOutput.trim(), 0, 0, mdTheme));
						}

						const taskUsage = formatUsageStats(r.usage, r.model);
						if (taskUsage) container.addChild(new Text(theme.fg("dim", taskUsage), 0, 0));
					}

					const usageStr = formatUsageStats(aggregateUsage(details.results));
					if (usageStr) {
						container.addChild(new Spacer(1));
						container.addChild(new Text(theme.fg("dim", `Total: ${usageStr}`), 0, 0));
					}
					return container;
				}

				// Collapsed view (or still running)
				let text = `${icon} ${theme.fg("toolTitle", theme.bold("parallel "))}${theme.fg("accent", status)}`;
				for (const r of details.results) {
					const rIcon =
						r.exitCode === -1
							? theme.fg("warning", "⏳")
							: isFailedResult(r)
								? theme.fg("error", "✗")
								: theme.fg("success", "✓");
					const displayItems = getDisplayItems(r.messages);
					text += `\n\n${theme.fg("muted", "─── ")}${theme.fg("accent", r.agent)} ${rIcon}`;
					if (displayItems.length === 0)
						text += `\n${theme.fg("muted", r.exitCode === -1 ? "(running...)" : "(no output)")}`;
					else text += `\n${renderDisplayItems(displayItems, 5)}`;
				}
				if (!isRunning) {
					const usageStr = formatUsageStats(aggregateUsage(details.results));
					if (usageStr) text += `\n\n${theme.fg("dim", `Total: ${usageStr}`)}`;
				}
				if (!expanded) text += `\n${theme.fg("muted", "(Ctrl+O to expand)")}`;
				return new Text(text, 0, 0);
			}

			const text = result.content[0];
			return new Text(text?.type === "text" ? text.text : "(no output)", 0, 0);
		},
	});
}
