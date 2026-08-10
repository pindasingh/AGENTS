import { chmod, lstat, readFile, realpath, rename, stat, unlink, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { isDeepStrictEqual } from "node:util";
import {
  getSettingsListTheme,
  parseFrontmatter,
  type ExtensionAPI,
  withFileMutationQueue,
} from "@earendil-works/pi-coding-agent";
import { Container, matchesKey, type SettingItem, SettingsList, Text } from "@earendil-works/pi-tui";

type InvocationMode = "agent-invocable" | "manual-only";
type DialogResult = "apply" | "cancel";

interface SkillRecord {
  commandName: string;
  name: string;
  description: string;
  filePath: string;
  raw: string;
  mode: InvocationMode;
}

const DISABLE_KEY = "disable-model-invocation";
const DISABLE_LINE = /^(?:disable-model-invocation|"disable-model-invocation"|'disable-model-invocation')[ \t]*:[ \t]*(.*?)(?:\r?\n)?$/;

function skillName(commandName: string): string {
  return commandName.startsWith("skill:") ? commandName.slice("skill:".length) : commandName;
}

function lineEnding(text: string): "\n" | "\r\n" {
  return text.includes("\r\n") ? "\r\n" : "\n";
}

function frontmatterBounds(raw: string): { start: number; end: number } | undefined {
  if (!raw.startsWith("---")) return undefined;
  const openingEnd = raw.indexOf("\n");
  if (openingEnd === -1) return undefined;

  // Match Pi's parser: the first newline followed by `---` ends frontmatter.
  const closing = /\r?\n---/.exec(raw.slice(openingEnd + 1));
  if (!closing || closing.index === undefined) return undefined;
  const closingStart = openingEnd + 1 + closing.index + closing[0].length - 3;
  return { start: openingEnd + 1, end: closingStart };
}

function splitLinesPreservingEndings(text: string): string[] {
  return text.match(/.*(?:\r\n|\n|$)/g)?.filter((line) => line.length > 0) ?? [];
}

function invocationMode(raw: string): InvocationMode {
  const { frontmatter } = parseFrontmatter(raw);
  return frontmatter[DISABLE_KEY] === true ? "manual-only" : "agent-invocable";
}

function withoutDisableKey(frontmatter: Record<string, unknown>): Record<string, unknown> {
  const { [DISABLE_KEY]: _disabled, ...rest } = frontmatter;
  return rest;
}

function validatePatch(beforeRaw: string, afterRaw: string, desiredMode: InvocationMode): void {
  const before = parseFrontmatter(beforeRaw).frontmatter;
  const after = parseFrontmatter(afterRaw).frontmatter;
  if (!isDeepStrictEqual(withoutDisableKey(before), withoutDisableKey(after))) {
    throw new Error("frontmatter layout is not safe to patch without changing other fields");
  }
  if (desiredMode === "manual-only" && after[DISABLE_KEY] !== true) {
    throw new Error("could not set disable-model-invocation safely");
  }
  if (desiredMode === "agent-invocable" && Object.hasOwn(after, DISABLE_KEY)) {
    throw new Error("could not remove disable-model-invocation safely");
  }
}

function patchInvocationMode(raw: string, desiredMode: InvocationMode): string {
  const eol = lineEnding(raw);
  const bounds = frontmatterBounds(raw);
  if (!bounds) {
    if (desiredMode === "agent-invocable") return raw;
    return `---${eol}${DISABLE_KEY}: true${eol}---${eol}${raw}`;
  }

  const lines = splitLinesPreservingEndings(raw.slice(bounds.start, bounds.end));
  const next: string[] = [];
  let wroteDisableKey = false;

  for (const line of lines) {
    const match = DISABLE_LINE.exec(line);
    if (!match) {
      next.push(line);
      continue;
    }
    if (desiredMode === "manual-only" && !wroteDisableKey) {
      const existingEol = line.endsWith("\r\n") ? "\r\n" : line.endsWith("\n") ? "\n" : eol;
      next.push(`${DISABLE_KEY}: true${existingEol}`);
      wroteDisableKey = true;
    }
  }

  if (desiredMode === "manual-only" && !wroteDisableKey) {
    if (next.length > 0 && !next[next.length - 1]!.endsWith("\n")) {
      next[next.length - 1] += eol;
    }
    next.push(`${DISABLE_KEY}: true${eol}`);
  }

  const patched = raw.slice(0, bounds.start) + next.join("") + raw.slice(bounds.end);
  validatePatch(raw, patched, desiredMode);
  return patched;
}

async function writeSafely(filePath: string, content: string): Promise<void> {
  const symbolicPath = await lstat(filePath);
  const targetPath = await realpath(filePath);
  const targetStats = await stat(targetPath);

  // Preserve the directory entry for direct symlinks and hard-linked files.
  if (symbolicPath.isSymbolicLink() || targetStats.nlink > 1) {
    await writeFile(targetPath, content, "utf8");
    return;
  }

  const temporaryPath = join(
    dirname(targetPath),
    `.pi-skill-toggle-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}.tmp`,
  );
  await writeFile(temporaryPath, content, "utf8");
  try {
    await chmod(temporaryPath, targetStats.mode);
    await rename(temporaryPath, targetPath);
  } catch (error) {
    await unlink(temporaryPath).catch(() => undefined);
    throw error;
  }
}

export default function skillToggleExtension(pi: ExtensionAPI) {
  async function discoverSkills(): Promise<{ skills: SkillRecord[]; errors: string[] }> {
    const commands = pi.getCommands().filter((command) => command.source === "skill");
    const results = await Promise.allSettled(
      commands.map(async (command): Promise<SkillRecord> => {
        const raw = await readFile(command.sourceInfo.path, "utf8");
        return {
          commandName: command.name,
          name: skillName(command.name),
          description: command.description ?? "",
          filePath: command.sourceInfo.path,
          raw,
          mode: invocationMode(raw),
        };
      }),
    );

    const skills: SkillRecord[] = [];
    const errors: string[] = [];
    for (let index = 0; index < results.length; index += 1) {
      const result = results[index]!;
      if (result.status === "fulfilled") skills.push(result.value);
      else errors.push(`${commands[index]!.name}: ${result.reason instanceof Error ? result.reason.message : String(result.reason)}`);
    }
    skills.sort((left, right) => left.commandName.localeCompare(right.commandName));
    return { skills, errors };
  }

  pi.registerCommand("toggle-skills", {
    description: "Toggle whether skills are agent-invocable or manual-only",
    handler: async (_args, ctx) => {
      if (ctx.mode !== "tui") {
        ctx.ui.notify("/toggle-skills requires TUI mode", "error");
        return;
      }

      const { skills, errors: discoveryErrors } = await discoverSkills();
      if (skills.length === 0) {
        ctx.ui.notify(discoveryErrors.length > 0 ? `No readable skills:\n${discoveryErrors.join("\n")}` : "No discovered skills", "error");
        return;
      }
      if (discoveryErrors.length > 0) {
        ctx.ui.notify(`Some skills could not be read:\n${discoveryErrors.join("\n")}`, "warning");
      }

      const desiredModes = new Map(skills.map((skill) => [skill.filePath, skill.mode]));
      const result = await ctx.ui.custom<DialogResult>((tui, theme, _keybindings, done) => {
        const container = new Container();
        container.addChild(new Text(theme.fg("accent", theme.bold("Skill invocation")), 1, 1));

        const items: SettingItem[] = skills.map((skill) => ({
          id: skill.filePath,
          label: skill.name,
          description: skill.description,
          currentValue: skill.mode,
          values: ["agent-invocable", "manual-only"],
        }));
        const list = new SettingsList(
          items,
          Math.min(items.length + 2, 15),
          getSettingsListTheme(),
          (id, newValue) => desiredModes.set(id, newValue as InvocationMode),
          () => done("cancel"),
          { enableSearch: true },
        );
        container.addChild(list);
        container.addChild(new Text(theme.fg("dim", "ctrl+s apply and reload • esc cancel"), 1, 1));

        return {
          render: (width: number) => container.render(width),
          invalidate: () => container.invalidate(),
          handleInput: (data: string) => {
            if (matchesKey(data, "ctrl+s")) done("apply");
            else list.handleInput?.(data);
            tui.requestRender();
          },
        };
      });
      if (result !== "apply") return;

      const changes = skills
        .map((skill) => ({ skill, desiredMode: desiredModes.get(skill.filePath) ?? skill.mode }))
        .filter(({ skill, desiredMode }) => desiredMode !== skill.mode);
      if (changes.length === 0) {
        ctx.ui.notify("No skill changes", "info");
        return;
      }

      const applied: string[] = [];
      const writeErrors: string[] = [];
      for (const { skill, desiredMode } of changes) {
        try {
          const targetPath = await realpath(skill.filePath);
          await withFileMutationQueue(targetPath, async () => {
            const current = await readFile(skill.filePath, "utf8");
            if (current !== skill.raw) {
              throw new Error("changed while the selector was open");
            }
            await writeSafely(skill.filePath, patchInvocationMode(current, desiredMode));
          });
          applied.push(`${skill.name}: ${skill.mode} → ${desiredMode}`);
        } catch (error) {
          writeErrors.push(`${skill.name}: ${error instanceof Error ? error.message : String(error)}`);
        }
      }

      const summary = [
        `Applied ${applied.length} skill change${applied.length === 1 ? "" : "s"}.`,
        ...applied.map((change) => `- ${change}`),
        ...writeErrors.map((error) => `- Skipped ${error}`),
      ].join("\n");
      ctx.ui.notify(summary, writeErrors.length > 0 ? "warning" : "info");

      if (applied.length > 0) {
        await ctx.reload();
        return;
      }
    },
  });
}
