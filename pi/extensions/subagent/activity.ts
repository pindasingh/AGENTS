function normalizedText(value: unknown): string {
	return typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "";
}

function pathArgument(args: unknown): string {
	if (!args || typeof args !== "object") return "";
	const values = args as Record<string, unknown>;
	return normalizedText(values.path ?? values.url);
}

export function describeToolActivity(toolName: string, args: unknown): string {
	const values = args && typeof args === "object" ? (args as Record<string, unknown>) : {};
	const path = pathArgument(args);

	switch (toolName) {
		case "read":
			return path ? `Reading ${path}` : "Reading files";
		case "edit":
			return path ? `Editing ${path}` : "Editing files";
		case "write":
			return path ? `Writing ${path}` : "Writing a file";
		case "bash": {
			const command = normalizedText(values.command);
			return command ? `Running ${command}` : "Running a command";
		}
		case "grep": {
			const pattern = normalizedText(values.pattern);
			return pattern ? `Searching code for ${pattern}` : "Searching code";
		}
		case "find": {
			const pattern = normalizedText(values.pattern);
			return pattern ? `Finding ${pattern}` : "Finding files";
		}
		case "web_search": {
			const query = normalizedText(values.query);
			return query ? `Searching the web for ${query}` : "Searching the web";
		}
		case "web_fetch":
			return path ? `Fetching ${path}` : "Fetching a web page";
		case "subagent":
			return "Delegating a subtask";
		default:
			return `Using ${toolName.replaceAll("_", " ")}`;
	}
}

export function describeStreamingActivity(eventType: string): string | undefined {
	if (eventType.startsWith("thinking_")) return "Thinking";
	if (eventType.startsWith("text_")) return "Writing response";
	if (eventType.startsWith("toolcall_")) return "Preparing next action";
	return undefined;
}

interface ChildActivityEvent {
	type: string;
	toolCallId?: string;
	toolName?: string;
	args?: unknown;
	isError?: boolean;
	message?: { role?: string };
	assistantMessageEvent?: { type?: string };
}

export class ChildActivityTracker {
	private readonly activeTools = new Map<string, string>();
	private readonly task: string;

	constructor(task: string) {
		this.task = task;
	}

	update(event: ChildActivityEvent): string | undefined {
		if (event.type === "turn_start" || (event.type === "message_start" && event.message?.role === "assistant")) {
			return `Thinking about ${this.task}`;
		}
		if (event.type === "message_update") {
			return describeStreamingActivity(event.assistantMessageEvent?.type ?? "");
		}
		if (event.type === "tool_execution_start" && event.toolName && event.toolCallId) {
			this.activeTools.set(event.toolCallId, describeToolActivity(event.toolName, event.args));
			return this.activeToolSummary();
		}
		if (event.type === "tool_execution_end" && event.toolName) {
			if (event.toolCallId) this.activeTools.delete(event.toolCallId);
			return (
				this.activeToolSummary() ??
				(event.isError
					? `Recovering from failed ${event.toolName.replaceAll("_", " ")}`
					: `Reviewing ${event.toolName.replaceAll("_", " ")} results`)
			);
		}
		return undefined;
	}

	private activeToolSummary(): string | undefined {
		const activities = Array.from(this.activeTools.values());
		if (activities.length === 0) return undefined;
		return activities.length === 1 ? activities[0] : `Running ${activities.length} actions: ${activities.join("; ")}`;
	}
}
