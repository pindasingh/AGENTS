import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";
import type { SubagentDetails, SingleResult } from "./index.ts";
import { conciseTaskTitle, MAX_TASK_TITLE_WIDTH } from "./task-title.ts";

const WIDGET_ID = "subagent-context-viewer";
export const SUBAGENT_JOB_ENTRY_TYPE = "subagent-job-state";

type Theme = ExtensionContext["ui"]["theme"];
type TuiHandle = { requestRender(): void };

interface PrimaryContext {
	tokens: number | null;
	contextWindow: number;
	percent: number | null;
	model?: string;
	working: boolean;
}

function formatTokens(count: number | null | undefined): string {
	if (count === null || count === undefined) return "?";
	if (count < 1000) return String(count);
	if (count < 10000) return `${(count / 1000).toFixed(1)}k`;
	if (count < 1000000) return `${Math.round(count / 1000)}k`;
	return `${(count / 1000000).toFixed(1)}M`;
}

function contextLabel(result: SingleResult): string {
	const tokens = result.usage.contextTokens || null;
	const window = result.usage.contextWindow || null;
	if (!tokens && !window) return "ctx:?";
	const percent = result.usage.contextPercent ?? (tokens && window ? (tokens / window) * 100 : null);
	return `ctx:${formatTokens(tokens)}/${formatTokens(window)}${percent === null ? "" : ` ${Math.round(percent)}%`}`;
}

function resultStatus(result: SingleResult): "running" | "queued" | "success" | "error" {
	if (result.status === "queued") return "queued";
	if (result.status === "running" || result.exitCode === -1) return "running";
	if (result.status === "aborted" || result.status === "failed") return "error";
	if (result.exitCode !== 0 || result.stopReason === "error" || result.stopReason === "aborted") return "error";
	return "success";
}

function statusGlyph(status: ReturnType<typeof resultStatus>): string {
	if (status === "running") return "●";
	if (status === "queued") return "○";
	if (status === "error") return "✗";
	return "✓";
}

function colorStatus(theme: Theme, status: ReturnType<typeof resultStatus>, text: string): string {
	if (status === "running") return theme.fg("success", text);
	if (status === "error") return theme.fg("error", text);
	if (status === "success") return theme.fg("success", text);
	return theme.fg("muted", text);
}

function invocationProgress(details: SubagentDetails): number {
	return details.results.reduce((score, result) => {
		const status = resultStatus(result);
		return score + (status === "queued" ? 0 : status === "running" ? 1 : 2);
	}, 0);
}

function invocationShouldDisplay(details: SubagentDetails): boolean {
	return details.results.some((result) => resultStatus(result) !== "success");
}

export function renderSubagentResultLines(result: SingleResult, prefix: string, last: boolean, theme: Theme, width: number): string[] {
	const status = resultStatus(result);
	const connector = last ? "└─" : "├─";
	const step = result.step ? ` step ${result.step}` : "";
	const agent = conciseTaskTitle(result.agent) || "subagent";
	const thinking = conciseTaskTitle(result.thinking ?? "");
	const safeModel = conciseTaskTitle(result.model ?? "");
	const thinkingLabel = thinking ? ` [${thinking}]` : "";
	const leading = `${prefix}${theme.fg("muted", connector)} ${colorStatus(theme, status, statusGlyph(status))} ${theme.fg("toolTitle", agent)}${theme.fg("muted", step)}${theme.fg("dim", thinkingLabel)}`;
	const model = safeModel ? ` ${theme.fg("dim", safeModel)}` : "";
	const telemetry = ` ${theme.fg("muted", contextLabel(result))}${model}`;
	const activity = conciseTaskTitle(result.activity || result.task);
	const separator = " — ";
	const hasActivity = activity && visibleWidth(activity) > 0;

	if (visibleWidth(leading + telemetry) > width) {
		const available = Math.min(MAX_TASK_TITLE_WIDTH, Math.max(0, width - visibleWidth(leading + separator)));
		const activityLabel = hasActivity && available > 0 ? separator + theme.fg("text", truncateToWidth(activity, available, "…")) : "";
		const telemetryPrefix = `${prefix}${last ? "  " : "│ "}  `;
		const context = theme.fg("muted", contextLabel(result));
		const telemetryModel = safeModel && visibleWidth(telemetryPrefix + context + model) <= width ? model : "";
		return [leading + activityLabel, telemetryPrefix + context + telemetryModel].map((line) => truncateToWidth(line, Math.max(1, width)));
	}

	const available = Math.min(MAX_TASK_TITLE_WIDTH, Math.max(0, width - visibleWidth(leading + separator + telemetry)));
	const activityLabel = hasActivity && available > 0 ? separator + theme.fg("text", truncateToWidth(activity, available, "…")) : "";
	return [truncateToWidth(leading + activityLabel + telemetry, Math.max(1, width))];
}

export class ContextViewer {
	private visible = false;
	private primary: PrimaryContext = { tokens: null, contextWindow: 0, percent: null, working: false };
	private readonly invocations = new Map<string, SubagentDetails>();
	private readonly latestInvocations = new Map<string, SubagentDetails>();
	private readonly activeInvocationIds = new Set<string>();
	private tui: TuiHandle | undefined;
	private widgetContext: ExtensionContext | undefined;
	private autoCloseWhenIdle = false;

	open(ctx: ExtensionContext, autoCloseWhenIdle = false): void {
		if (this.visible) {
			if (!autoCloseWhenIdle) this.autoCloseWhenIdle = false;
			return;
		}
		this.visible = true;
		this.widgetContext = ctx;
		this.autoCloseWhenIdle = autoCloseWhenIdle;
		ctx.ui.setWidget(
			WIDGET_ID,
			(tui, theme) => {
				this.tui = tui;
				return {
					render: (width: number) => this.render(width, theme),
					invalidate: () => {},
				};
			},
			{ placement: "belowEditor" },
		);
	}

	close(ctx: ExtensionContext): void {
		this.visible = false;
		this.tui = undefined;
		this.widgetContext = undefined;
		this.autoCloseWhenIdle = false;
		ctx.ui.setWidget(WIDGET_ID, undefined);
	}

	toggle(ctx: ExtensionContext): boolean {
		if (this.visible) this.close(ctx);
		else this.open(ctx);
		return this.visible;
	}

	isVisible(): boolean {
		return this.visible;
	}

	reset(): void {
		this.invocations.clear();
		this.latestInvocations.clear();
		this.activeInvocationIds.clear();
		this.requestRender();
	}

	updatePrimary(ctx: ExtensionContext, working = this.primary.working): void {
		const usage = ctx.getContextUsage();
		this.primary = {
			tokens: usage?.tokens ?? null,
			contextWindow: usage?.contextWindow ?? ctx.model?.contextWindow ?? 0,
			percent: usage?.percent ?? null,
			model: ctx.model ? `${ctx.model.provider}/${ctx.model.id}` : undefined,
			working,
		};
		this.requestRender();
	}

	startInvocation(toolCallId: string, details: SubagentDetails): void {
		this.activeInvocationIds.add(toolCallId);
		this.latestInvocations.set(toolCallId, details);
		this.invocations.set(toolCallId, details);
		this.requestRender();
	}

	updateInvocation(toolCallId: string, details: SubagentDetails): void {
		this.latestInvocations.set(toolCallId, details);
		if (this.activeInvocationIds.has(toolCallId) && invocationShouldDisplay(details)) {
			this.invocations.set(toolCallId, details);
		} else {
			this.invocations.delete(toolCallId);
		}
		this.requestRender();
		this.maybeAutoClose();
	}

	restoreFromBranch(ctx: ExtensionContext): void {
		this.invocations.clear();
		this.activeInvocationIds.clear();
		for (const entry of ctx.sessionManager.getBranch()) {
			if (entry.type !== "message" || entry.message.role !== "toolResult" || entry.message.toolName !== "subagent") continue;
			const details = entry.message.details as SubagentDetails | undefined;
			if (details?.results) {
				this.activeInvocationIds.add(entry.message.toolCallId);
				this.invocations.set(entry.message.toolCallId, details);
			}
		}

		// Completion may be appended while another branch is active. Search the whole
		// session, but only apply state for tool calls present on the active branch.
		for (const entry of ctx.sessionManager.getEntries()) {
			if (entry.type !== "custom" || entry.customType !== SUBAGENT_JOB_ENTRY_TYPE) continue;
			const data = entry.data as { toolCallId?: unknown; details?: SubagentDetails } | undefined;
			if (typeof data?.toolCallId !== "string" || !data.details?.results || !this.invocations.has(data.toolCallId)) continue;
			this.invocations.set(data.toolCallId, data.details);
			this.latestInvocations.set(data.toolCallId, data.details);
		}

		// Live state is retained even while viewing another branch, so returning to
		// the originating branch cannot regress from running/completed to queued.
		for (const [toolCallId, liveDetails] of this.latestInvocations) {
			const restoredDetails = this.invocations.get(toolCallId);
			if (
				restoredDetails &&
				liveDetails.jobId === restoredDetails.jobId &&
				invocationProgress(liveDetails) > invocationProgress(restoredDetails)
			) {
				this.invocations.set(toolCallId, liveDetails);
			}
		}
		for (const [toolCallId, details] of this.invocations) {
			if (!invocationShouldDisplay(details)) this.invocations.delete(toolCallId);
		}
		this.updatePrimary(ctx, false);
		this.maybeAutoClose();
	}

	private requestRender(): void {
		if (this.visible) this.tui?.requestRender();
	}

	private maybeAutoClose(): void {
		if (this.autoCloseWhenIdle && this.invocations.size === 0 && this.widgetContext) {
			this.close(this.widgetContext);
		}
	}

	private render(width: number, theme: Theme): string[] {
		const lines: string[] = [];
		const primaryContext = this.primary.contextWindow
			? `ctx:${formatTokens(this.primary.tokens)}/${formatTokens(this.primary.contextWindow)}${this.primary.percent === null ? "" : ` ${Math.round(this.primary.percent)}%`}`
			: `ctx:${formatTokens(this.primary.tokens)}`;
		const primaryStatus = this.primary.working ? theme.fg("success", "●") : theme.fg("muted", "●");
		const primaryModel = conciseTaskTitle(this.primary.model ?? "");
		lines.push(
			`${theme.fg("accent", theme.bold("Context viewer"))} ${theme.fg("dim", "(/context-viewer to close)")}`,
			`${primaryStatus} ${theme.fg("toolTitle", "primary")} ${theme.fg("muted", primaryContext)}${primaryModel ? ` ${theme.fg("dim", primaryModel)}` : ""}`,
		);

		const entries = Array.from(this.invocations.values());
		if (entries.length === 0) lines.push(theme.fg("dim", "  └─ no active subagent jobs"));
		for (let index = 0; index < entries.length; index += 1) {
			this.renderDetails(lines, entries[index], "  ", index === entries.length - 1, theme, width);
		}
		const bounded = lines.length > 200 ? [...lines.slice(0, 199), theme.fg("warning", "… context tree truncated at 200 lines")] : lines;
		return bounded.map((line) => truncateToWidth(line, Math.max(1, width)));
	}

	private renderDetails(lines: string[], details: SubagentDetails, prefix: string, last: boolean, theme: Theme, width: number): void {
		if (lines.length >= 200) return;
		const connector = last ? "└─" : "├─";
		const job = details.jobId ? ` ${theme.fg("toolTitle", details.jobId)}` : "";
		lines.push(`${prefix}${theme.fg("muted", connector)} ${theme.fg("accent", details.mode)}${job}`);
		const childPrefix = `${prefix}${last ? "  " : "│ "}`;
		for (let index = 0; index < details.results.length; index += 1) {
			this.renderResult(lines, details.results[index], childPrefix, index === details.results.length - 1, theme, width);
		}
	}

	private renderResult(lines: string[], result: SingleResult, prefix: string, last: boolean, theme: Theme, width: number): void {
		if (lines.length >= 200) return;
		lines.push(...renderSubagentResultLines(result, prefix, last, theme, width));
		const nestedPrefix = `${prefix}${last ? "  " : "│ "}`;
		for (let index = 0; index < (result.nested ?? []).length; index += 1) {
			const nested = result.nested![index];
			const nestedLast = index === result.nested!.length - 1;
			if (nested.details) this.renderDetails(lines, nested.details, nestedPrefix, nestedLast, theme, width);
			else {
				const nestedConnector = nestedLast ? "└─" : "├─";
				const glyph =
					nested.status === "running"
						? theme.fg("success", "●")
						: nested.status === "failed"
							? theme.fg("error", "✗")
							: theme.fg("success", "✓");
				lines.push(`${nestedPrefix}${theme.fg("muted", nestedConnector)} ${glyph} ${theme.fg("accent", "nested subagent")}`);
			}
		}
	}
}
