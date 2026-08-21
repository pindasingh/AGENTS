export const RUN_NAME_PATTERN = /^[a-z0-9](?:[a-z0-9-]{0,62})$/;
const TOOL_NAME_PATTERN = /^[a-zA-Z0-9_.-]+$/;

export interface ChildLaunchConfig {
	tools: string[];
	model?: string;
	thinking: "off" | "minimal" | "low" | "medium";
}

export function buildChildArgs(config: ChildLaunchConfig): string[] {
	const args = [
		"--mode",
		"json",
		"-p",
		"--no-session",
		"--thinking",
		config.thinking,
		"--exclude-tools",
		"subagent",
		"--no-skills",
	];
	if (config.model) args.push("--model", config.model);
	args.push("--tools", config.tools.join(","));
	return args;
}

export function validateSpawnContract(name: string, tools: string[], prompt: string): string | undefined {
	if (!RUN_NAME_PATTERN.test(name)) return "Invalid name. Use 1-63 lowercase letters, digits, or hyphens.";
	if (
		tools.length === 0 ||
		tools.includes("subagent") ||
		new Set(tools).size !== tools.length ||
		tools.some((tool) => !TOOL_NAME_PATTERN.test(tool))
	) {
		return "Invalid tools. Provide unique tool names in a non-empty allowlist that excludes subagent.";
	}
	if (!prompt.trim()) return "Invalid prompt. Provide a complete standalone task prompt.";
	return undefined;
}
