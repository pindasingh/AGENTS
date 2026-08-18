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

const CHECKPOINT_OWNERSHIP = `Primary agents own the canonical task checkpoint. Writable workers must update only their parent-assigned worker note; without an assigned path, create a uniquely named note under .work/<task>/workers/ and never modify a candidate canonical checkpoint. Read-only agents must not write checkpoint files.`;

export function checkpointReminder(percent: number): string {
	return `Best-effort early warning: context usage is ${percent.toFixed(1)}%. Before the next context-heavy tool step, update the active task's cumulative .work/<task>/state.md with every still-relevant fact, decision, completed and in-progress item, verification result, key artifact path, and exact next action. Preserve key evidence, not transcripts. ${CHECKPOINT_OWNERSHIP} Keep the snapshot self-contained so recovery reads it first instead of replaying older files, then continue the task.`;
}

export function recoveryReminder(reason: string): string {
	return `Context was compacted (${reason}). Re-establish working state before continuing. A primary agent should read the matching task's cumulative .work/<task>/state.md first, compare its Updated time with timestamped artifact filenames, and open only directly referenced evidence plus any newer artifacts not yet folded into state; never replay historical notes. Reconcile with the latest user request, repository instructions, git status and diff, actual files, and verification evidence, then repair canonical state. ${CHECKPOINT_OWNERSHIP} Writable workers should reconcile and repair only their own note. Read-only agents should re-read source evidence and continue from the surviving summary. If no suitable state exists and the task remains substantive, create it only within the ownership rules. Compaction is not a blocker or a reason to return partial work.`;
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

	pi.on("turn_end", (event, ctx) => {
		// Tool results mean Pi already has another model call to make. Steering here
		// adds checkpoint guidance to that continuation without creating a new turn
		// after a text-only response that may have completed the task.
		if (event.toolResults.length === 0) {
			return;
		}
		const percent = ctx.getContextUsage()?.percent;
		if (!gate.shouldSend(percent) || percent === null || percent === undefined) {
			return;
		}
		sendReminder(checkpointReminder(percent), { phase: "early-checkpoint", percent });
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
