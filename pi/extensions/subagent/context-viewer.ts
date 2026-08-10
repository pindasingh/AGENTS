import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";
import type { SubagentDetails, SingleResult } from "./index.ts";

const WIDGET_ID = "subagent-context-viewer";

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
	if (result.status === "running" || result.exitCode === -1) return "running";
	if (result.status === "queued") return "queued";
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
	if (status === "running") return theme.fg("warning", text);
	if (status === "error") return theme.fg("error", text);
	if (status === "success") return theme.fg("success", text);
	return theme.fg("muted", text);
}

export class ContextViewer {
	private visible = false;
	private primary: PrimaryContext = { tokens: null, contextWindow: 0, percent: null, working: false };
	private readonly invocations = new Map<string, SubagentDetails>();
	private tui: TuiHandle | undefined;

	open(ctx: ExtensionContext): void {
		if (this.visible) return;
		this.visible = true;
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

	updateInvocation(toolCallId: string, details: SubagentDetails): void {
		this.invocations.set(toolCallId, details);
		this.requestRender();
	}

	restoreFromBranch(ctx: ExtensionContext): void {
		this.invocations.clear();
		for (const entry of ctx.sessionManager.getBranch()) {
			if (entry.type !== "message" || entry.message.role !== "toolResult" || entry.message.toolName !== "subagent") continue;
			const details = entry.message.details as SubagentDetails | undefined;
			if (details?.results) this.invocations.set(entry.message.toolCallId, details);
		}
		this.updatePrimary(ctx, false);
	}

	private requestRender(): void {
		if (this.visible) this.tui?.requestRender();
	}

	private render(width: number, theme: Theme): string[] {
		const lines: string[] = [];
		const primaryContext = this.primary.contextWindow
			? `ctx:${formatTokens(this.primary.tokens)}/${formatTokens(this.primary.contextWindow)}${this.primary.percent === null ? "" : ` ${Math.round(this.primary.percent)}%`}`
			: `ctx:${formatTokens(this.primary.tokens)}`;
		const primaryStatus = this.primary.working ? theme.fg("warning", "●") : theme.fg("success", "●");
		lines.push(
			`${theme.fg("accent", theme.bold("Context viewer"))} ${theme.fg("dim", "(/context-viewer to close)")}`,
			`${primaryStatus} ${theme.fg("toolTitle", "primary")} ${theme.fg("muted", primaryContext)}${this.primary.model ? ` ${theme.fg("dim", this.primary.model)}` : ""}`,
		);

		const entries = Array.from(this.invocations.values());
		if (entries.length === 0) lines.push(theme.fg("dim", "  └─ no subagent runs in this branch"));
		for (let index = 0; index < entries.length; index += 1) {
			this.renderDetails(lines, entries[index], "  ", index === entries.length - 1, theme);
		}
		const bounded = lines.length > 200 ? [...lines.slice(0, 199), theme.fg("warning", "… context tree truncated at 200 lines")] : lines;
		return bounded.map((line) => truncateToWidth(line, Math.max(1, width)));
	}

	private renderDetails(lines: string[], details: SubagentDetails, prefix: string, last: boolean, theme: Theme): void {
		if (lines.length >= 200) return;
		const connector = last ? "└─" : "├─";
		lines.push(`${prefix}${theme.fg("muted", connector)} ${theme.fg("accent", details.mode)}`);
		const childPrefix = `${prefix}${last ? "  " : "│ "}`;
		for (let index = 0; index < details.results.length; index += 1) {
			this.renderResult(lines, details.results[index], childPrefix, index === details.results.length - 1, theme);
		}
	}

	private renderResult(lines: string[], result: SingleResult, prefix: string, last: boolean, theme: Theme): void {
		if (lines.length >= 200) return;
		const status = resultStatus(result);
		const connector = last ? "└─" : "├─";
		const step = result.step ? ` step ${result.step}` : "";
		const model = result.model ? ` ${theme.fg("dim", result.model)}` : "";
		lines.push(
			`${prefix}${theme.fg("muted", connector)} ${colorStatus(theme, status, statusGlyph(status))} ${theme.fg("toolTitle", result.agent)}${theme.fg("muted", step)} ${theme.fg("muted", contextLabel(result))}${model}`,
		);
		const nestedPrefix = `${prefix}${last ? "  " : "│ "}`;
		for (let index = 0; index < (result.nested ?? []).length; index += 1) {
			const nested = result.nested![index];
			const nestedLast = index === result.nested!.length - 1;
			if (nested.details) this.renderDetails(lines, nested.details, nestedPrefix, nestedLast, theme);
			else {
				const nestedConnector = nestedLast ? "└─" : "├─";
				const glyph =
					nested.status === "running"
						? theme.fg("warning", "●")
						: nested.status === "failed"
							? theme.fg("error", "✗")
							: theme.fg("success", "✓");
				lines.push(`${nestedPrefix}${theme.fg("muted", nestedConnector)} ${glyph} ${theme.fg("accent", "nested subagent")}`);
			}
		}
	}
}
