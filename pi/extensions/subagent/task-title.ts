export const MAX_TASK_TITLE_WIDTH = 72;

const BIDI_AND_INVISIBLE_CONTROLS = /[\u061c\u200b\u200e\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]/g;
const NON_PRINTING_CONTROLS = /[\u0000-\u0008\u000b\u000c\u000e-\u001a\u001c-\u001f\u007f-\u009f]/g;

function stripTerminalSequences(value: string): string {
	let output = "";
	for (let index = 0; index < value.length; index += 1) {
		if (value.charCodeAt(index) !== 0x1b) {
			output += value[index];
			continue;
		}

		const introducer = value[index + 1];
		if (introducer === "]") {
			index += 2;
			while (index < value.length && value.charCodeAt(index) !== 0x07) {
				if (value.charCodeAt(index) === 0x1b && value[index + 1] === "\\") {
					index += 1;
					break;
				}
				index += 1;
			}
			continue;
		}
		if (introducer === "P" || introducer === "X" || introducer === "^" || introducer === "_") {
			index += 2;
			while (index < value.length) {
				if (value.charCodeAt(index) === 0x1b && value[index + 1] === "\\") {
					index += 1;
					break;
				}
				index += 1;
			}
			continue;
		}
		if (introducer === "[") {
			index += 2;
			while (index < value.length) {
				const code = value.charCodeAt(index);
				if (code >= 0x40 && code <= 0x7e) break;
				index += 1;
			}
			continue;
		}

		if (introducer) index += 1;
	}
	return output;
}

export function conciseTaskTitle(task: string): string {
	return stripTerminalSequences(task)
		.replace(BIDI_AND_INVISIBLE_CONTROLS, "")
		.replace(NON_PRINTING_CONTROLS, "")
		.replace(/\s+/g, " ")
		.trim();
}
