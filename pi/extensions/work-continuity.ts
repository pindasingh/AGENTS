import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export const CHECKPOINT_THRESHOLD_PERCENT = 70;
export const REMINDER_TYPE = "work-continuity-reminder";

export class CheckpointReminderGate {
	private sent = false;

	shouldSend(percent: number | null | undefined): boolean {
		if (this.sent || percent === null || percent === undefined || !Number.isFinite(percent)) {
			return false;
		}
		if (percent < CHECKPOINT_THRESHOLD_PERCENT) {
			return false;
		}
		this.sent = true;
		return true;
	}

	reset(): void {
		this.sent = false;
	}
}

export function checkpointReminder(percent: number): string {
	return `Context usage is ${percent.toFixed(1)}% and is approaching compaction. Before more context-heavy work, create or update the active repository-root .work/ checkpoint with the task definition, constraints, completed and in-progress work, key findings and decisions, verification evidence, and exact next action. Keep it concise, then continue the task; do not stop merely to report this checkpoint.`;
}

export function recoveryReminder(reason: string): string {
	return `Context was compacted (${reason}). Re-establish working state before continuing: inspect the repository-root .work/ directory, read the checkpoint matching the active task, and reconcile it with the latest user request, repository instructions, git status and diff, actual files, and verification evidence. Repair stale notes and continue to completion. If no checkpoint exists and the task remains substantive, reconstruct and create one now. Compaction is not a blocker or a reason to return partial work. Read-only agents that cannot update .work/ should re-read source evidence and continue from the surviving summary.`;
}

export default function (pi: ExtensionAPI) {
	const gate = new CheckpointReminderGate();

	const sendReminder = (content: string, details: Record<string, unknown>) => {
		pi.sendMessage(
			{
				customType: REMINDER_TYPE,
				content,
				display: false,
				details,
			},
			{ deliverAs: "steer" },
		);
	};

	pi.on("session_start", (event) => {
		if (event.reason !== "reload") {
			gate.reset();
		}
	});

	pi.on("turn_end", (_event, ctx) => {
		const percent = ctx.getContextUsage()?.percent;
		if (!gate.shouldSend(percent) || percent === null || percent === undefined) {
			return;
		}
		sendReminder(checkpointReminder(percent), { phase: "before-compaction", percent });
	});

	pi.on("session_compact", (event) => {
		gate.reset();
		sendReminder(recoveryReminder(event.reason), {
			phase: "after-compaction",
			reason: event.reason,
			willRetry: event.willRetry,
		});
	});
}
