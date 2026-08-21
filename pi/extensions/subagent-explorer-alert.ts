import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";

const ENTRY_TYPE = "subagent-explorer-error";

type Candidate = {
	location: string;
	task?: string;
	cwd?: string;
};

type AlertData = {
	timestamp: string;
	toolCallId: string;
	sessionFile?: string;
	cwd: string;
	matches: Candidate[];
};

function asOptionalString(value: unknown): string | undefined {
	return typeof value === "string" && value.length > 0 ? value : undefined;
}

function collectExplorerRequests(input: unknown): Candidate[] {
	if (!input || typeof input !== "object") return [];
	const params = input as Record<string, unknown>;
	const matches: Candidate[] = [];

	if (params.agent === "explorer") {
		matches.push({
			location: "agent",
			task: asOptionalString(params.task),
			cwd: asOptionalString(params.cwd),
		});
	}

	for (const [collectionName, collection] of [
		["tasks", params.tasks],
		["chain", params.chain],
	] as const) {
		if (!Array.isArray(collection)) continue;
		for (let index = 0; index < collection.length; index += 1) {
			const item = collection[index];
			if (!item || typeof item !== "object") continue;
			const candidate = item as Record<string, unknown>;
			if (candidate.agent !== "explorer") continue;
			matches.push({
				location: `${collectionName}[${index}].agent`,
				task: asOptionalString(candidate.task),
				cwd: asOptionalString(candidate.cwd),
			});
		}
	}

	return matches;
}

export default function (pi: ExtensionAPI) {
	pi.registerEntryRenderer(ENTRY_TYPE, (entry, _options, theme) => {
		const data = entry.data as AlertData;
		const lines = [
			theme.fg("error", theme.bold("Invalid subagent name: explorer")),
			theme.fg("muted", `${data.timestamp} · ${data.toolCallId}`),
			theme.fg("dim", `effective cwd: ${data.cwd}`),
		];
		if (data.sessionFile) lines.push(theme.fg("dim", `session: ${data.sessionFile}`));
		for (const match of data.matches) {
			lines.push(theme.fg("warning", match.location));
			if (match.task) lines.push(theme.fg("dim", `  task: ${match.task}`));
			if (match.cwd) lines.push(theme.fg("dim", `  cwd: ${match.cwd}`));
		}
		return new Text(lines.join("\n"), 0, 0);
	});

	pi.on("tool_call", (event, ctx) => {
		if (event.toolName !== "subagent") return;
		const matches = collectExplorerRequests(event.input);
		if (matches.length === 0) return;

		const timestamp = new Date().toISOString();
		const data: AlertData = {
			timestamp,
			toolCallId: event.toolCallId,
			sessionFile: ctx.sessionManager.getSessionFile() ?? undefined,
			cwd: ctx.cwd,
			matches,
		};
		pi.appendEntry(ENTRY_TYPE, data);
		const firstMatch = matches[0];
		const taskPreview = firstMatch.task
			? ` Task: ${firstMatch.task.length > 120 ? `${firstMatch.task.slice(0, 120)}…` : firstMatch.task}`
			: "";
		ctx.ui.notify(
			`ERROR: subagent requested nonexistent agent "explorer" at ${timestamp} (${firstMatch.location}, cwd: ${firstMatch.cwd ?? ctx.cwd}).${taskPreview} Logged in this session.`,
			"error",
		);
	});
}
