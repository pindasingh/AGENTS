import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const POLICY = `Dependency and software installation is prohibited.

You must use only tools, runtimes, libraries, packages, and dependencies that are already available on this machine. Do not install, add, update, upgrade, restore, sync, fetch, bootstrap, or temporarily download packages or tooling. Do not bypass this rule with a different package manager, a remote install script, an ephemeral runner such as npx, or a hand-written downloader.

Before considering an installation, inspect the machine and look for an installed alternative. If the task genuinely cannot continue without something new, stop and ask the user to install it. The request must explain:
- the exact package/tool and version or constraint;
- why it is needed for the user's task;
- what cannot be completed without it;
- which already-installed alternatives you checked; and
- the command you propose the user run.

Do not run the proposed command yourself. Do not ask for an installation merely for convenience.`;

const BLOCK_REASON =
  "Dependency installation is disabled by the user's global policy. Do not retry, rephrase, or bypass this command. Use what is already installed. If a new package is essential, ask the user to install it and explain exactly what is needed, why it is needed, what is blocked, which installed alternatives were checked, and the proposed command.";

const OPTION_VALUE_FLAGS = new Set([
  "--cache",
  "--config",
  "--cwd",
  "--dir",
  "--directory",
  "--filter",
  "--global-dir",
  "--prefix",
  "--project",
  "--python",
  "--registry",
  "--userconfig",
  "--workspace",
  "-c",
  "-w",
]);

const SUDO_OPTION_VALUE_FLAGS = new Set([
  "--chdir",
  "--chroot",
  "--close-from",
  "--command-timeout",
  "--group",
  "--host",
  "--prompt",
  "--role",
  "--type",
  "--user",
  "-c",
  "-d",
  "-g",
  "-h",
  "-p",
  "-r",
  "-t",
  "-u",
]);

function commandAfterWrapperOptions(args: string[], valueFlags: ReadonlySet<string>): string[] | undefined {
  for (let index = 0; index < args.length; index += 1) {
    const token = args[index].toLowerCase();
    if (token === "--") return args.slice(index + 1);
    if (token.startsWith("-")) {
      if (!token.includes("=") && valueFlags.has(token)) index += 1;
      continue;
    }
    return args.slice(index);
  }
  return undefined;
}

function unquote(token: string): string {
  if (token.length >= 2) {
    const first = token[0];
    const last = token[token.length - 1];
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return token.slice(1, -1);
    }
  }
  return token;
}

function tokenize(segment: string): string[] {
  return (segment.match(/"(?:\\.|[^"\\])*"|'[^']*'|[^\s]+/g) ?? []).map(unquote);
}

function executableName(token: string): string {
  return token
    .replace(/^[({]+/, "")
    .replace(/[),]+$/, "")
    .replace(/\\/g, "/")
    .split("/")
    .pop()!
    .toLowerCase()
    .replace(/\.(?:exe|cmd|bat|ps1)$/, "");
}

function actionAfterOptions(args: string[], extraValueFlags: readonly string[] = []): string | undefined {
  const valueFlags = new Set([...OPTION_VALUE_FLAGS, ...extraValueFlags]);

  for (let index = 0; index < args.length; index += 1) {
    const token = args[index].toLowerCase();
    if (/^[a-z_][a-z0-9_]*=.*/i.test(token)) continue;
    if (token.startsWith("-")) {
      if (!token.includes("=") && valueFlags.has(token)) index += 1;
      continue;
    }
    return token.replace(/[;,)]*$/, "");
  }

  return undefined;
}

function hasAction(args: string[], actions: readonly string[], extraValueFlags: readonly string[] = []): boolean {
  return actions.includes(actionAfterOptions(args, extraValueFlags) ?? "");
}

function inspectDirectCommand(tokens: string[], depth: number): string | undefined {
  if (tokens.length === 0) return undefined;

  let executable = executableName(tokens[0]);
  let args = tokens.slice(1);

  if (["command", "nohup", "time"].includes(executable)) {
    const nested = commandAfterWrapperOptions(args, new Set());
    return nested ? inspectDirectCommand(nested, depth) : undefined;
  }

  if (["sudo", "doas"].includes(executable)) {
    const nested = commandAfterWrapperOptions(args, SUDO_OPTION_VALUE_FLAGS);
    return nested ? inspectDirectCommand(nested, depth) : undefined;
  }

  if (executable === "env") {
    let index = 0;
    while (index < args.length) {
      const token = args[index].toLowerCase();
      if (token === "--") {
        index += 1;
        break;
      }
      if (/^[a-z_][a-z0-9_]*=/i.test(token)) {
        index += 1;
        continue;
      }
      if (token === "-u" || token === "--unset" || token === "-c" || token === "--chdir") {
        index += 2;
        continue;
      }
      if (token.startsWith("-")) {
        index += 1;
        continue;
      }
      break;
    }
    return args[index] ? inspectDirectCommand(args.slice(index), depth) : undefined;
  }

  if (["bash", "sh", "zsh", "fish", "cmd", "powershell", "pwsh"].includes(executable)) {
    const commandFlagIndex = args.findIndex((token) => ["-c", "/c", "-command", "-encodedcommand"].includes(token.toLowerCase()));
    if (commandFlagIndex >= 0 && args[commandFlagIndex + 1] && depth < 4) {
      const nestedCommand = args.slice(commandFlagIndex + 1).join(" ");
      if (["powershell", "pwsh"].includes(executable) && /\b(?:install|update)-(?:module|package|script)\b/i.test(nestedCommand)) {
        return "PowerShell package/module installation/update";
      }
      return getBlockedDependencyCommandReason(nestedCommand, depth + 1);
    }
  }

  if (["npx", "pnpx", "bunx", "yarnpkg-dlx"].includes(executable)) return `${executable} can download and run packages`;
  if (executable === "pi" && hasAction(args, ["install", "update", "upgrade"])) return "pi package installation/update";

  if (executable === "npm" && hasAction(args, ["add", "ci", "exec", "i", "install", "up", "update", "upgrade"])) return "npm dependency acquisition";
  if (executable === "pnpm" && hasAction(args, ["add", "dlx", "fetch", "i", "install", "up", "update", "upgrade"])) return "pnpm dependency acquisition";
  if (["yarn", "yarnpkg"].includes(executable)) {
    let action = actionAfterOptions(args);
    if (action === "workspace") action = args[args.findIndex((token) => token.toLowerCase() === "workspace") + 2]?.toLowerCase();
    if (["add", "dlx", "install", "up", "update", "upgrade"].includes(action ?? "")) return "Yarn dependency acquisition";
  }
  if (executable === "bun" && hasAction(args, ["add", "i", "install", "update", "upgrade", "x"])) return "Bun dependency acquisition";
  if (executable === "corepack" && hasAction(args, ["install", "prepare", "up", "use"])) return "Corepack package-manager acquisition";

  if (/^pip\d*(?:\.\d+)?$/.test(executable) && hasAction(args, ["download", "install"])) return "Python package acquisition";
  if (/^(?:python|python\d+(?:\.\d+)?|py)$/.test(executable)) {
    const moduleIndex = args.findIndex((token) => token.toLowerCase() === "-m");
    if (moduleIndex >= 0 && /^pip\d*(?:\.\d+)?$/.test((args[moduleIndex + 1] ?? "").toLowerCase())) {
      if (hasAction(args.slice(moduleIndex + 2), ["download", "install"])) return "Python package acquisition";
    }
  }
  if (executable === "pipx" && hasAction(args, ["install", "inject", "upgrade", "upgrade-all"])) return "pipx package acquisition";
  if (executable === "uv") {
    const action = actionAfterOptions(args);
    if (["add", "sync"].includes(action ?? "")) return "uv dependency acquisition";
    if (["pip", "tool", "python"].includes(action ?? "")) {
      const actionIndex = args.findIndex((token) => token.toLowerCase() === action);
      if (hasAction(args.slice(actionIndex + 1), ["install", "sync", "upgrade"])) return "uv package/tool acquisition";
    }
  }
  if (["poetry", "pdm", "pipenv", "hatch"].includes(executable) && hasAction(args, ["add", "install", "sync", "update"])) return `${executable} dependency acquisition`;
  if (["conda", "mamba", "micromamba"].includes(executable) && hasAction(args, ["create", "install", "update", "upgrade"])) return `${executable} package/environment acquisition`;

  if (["apt", "apt-get"].includes(executable) && hasAction(args, ["build-dep", "dist-upgrade", "full-upgrade", "install", "upgrade"])) return "APT software installation/update";
  if (executable === "apk" && hasAction(args, ["add", "fix", "upgrade"])) return "Alpine package installation/update";
  if (["dnf", "yum", "zypper"].includes(executable) && hasAction(args, ["add", "dist-upgrade", "install", "update", "upgrade"])) return `${executable} software installation/update`;
  if (executable === "pacman" && args.some((token) => /^-s(?:y|u|yu|yyu)?$/i.test(token))) return "pacman software installation/update";
  if (["brew", "port", "pkg", "pkg_add", "mas"].includes(executable) && hasAction(args, ["add", "bundle", "install", "update", "upgrade"])) return `${executable} software installation/update`;
  if (["choco", "chocolatey", "winget", "scoop", "snap", "flatpak"].includes(executable) && hasAction(args, ["add", "install", "refresh", "update", "upgrade"])) return `${executable} software installation/update`;

  if (executable === "cargo" && hasAction(args, ["add", "fetch", "install", "update"])) return "Cargo package acquisition";
  if (executable === "rustup") {
    const action = actionAfterOptions(args);
    if (["default", "install", "update"].includes(action ?? "")) return "Rust toolchain installation/update";
    if (["component", "target", "toolchain"].includes(action ?? "") && args.some((token) => ["add", "install", "update"].includes(token.toLowerCase()))) return "Rust toolchain component acquisition";
  }
  if (executable === "go" && hasAction(args, ["get", "install"])) return "Go package/tool acquisition";
  if (executable === "go" && actionAfterOptions(args) === "mod" && args.some((token) => ["download", "tidy"].includes(token.toLowerCase()))) return "Go module acquisition";
  if (executable === "dotnet") {
    const action = actionAfterOptions(args);
    if (action === "restore") return ".NET dependency restore";
    if (["add", "package", "tool", "workload"].includes(action ?? "") && args.some((token) => ["add", "install", "restore", "update"].includes(token.toLowerCase()))) return ".NET package/tool acquisition";
  }
  if (executable === "nuget" && hasAction(args, ["install", "restore", "update"])) return "NuGet package acquisition";

  if (executable === "composer" && hasAction(args, ["create-project", "install", "require", "update", "upgrade"])) return "Composer dependency acquisition";
  if (executable === "gem" && hasAction(args, ["install", "update"])) return "Ruby gem installation/update";
  if (["bundle", "bundler"].includes(executable) && hasAction(args, ["add", "install", "update"])) return "Bundler dependency acquisition";
  if (executable === "mix" && args.some((token) => /^(?:archive\.install|deps\.(?:get|update)|local\.(?:hex|rebar))$/i.test(token))) return "Elixir dependency/tool acquisition";

  if (["cpan", "cpanm"].includes(executable)) return "Perl module acquisition";
  if (executable === "luarocks" && hasAction(args, ["install", "make"])) return "Lua package installation";
  if (executable === "raco" && actionAfterOptions(args) === "pkg" && args.some((token) => ["install", "update"].includes(token.toLowerCase()))) return "Racket package acquisition";
  if (["cabal", "stack", "opam", "vcpkg", "conan"].includes(executable) && hasAction(args, ["add", "install", "update", "upgrade"])) return `${executable} package acquisition`;
  if (executable === "sdk" && hasAction(args, ["install", "selfupdate", "upgrade"])) return "SDKMAN software installation/update";

  if (executable === "nix-env" && args.some((token) => /^-(?:i|ia|iA|if|u|uA|uf)$/i.test(token))) return "Nix package installation/update";
  if (executable === "nix") {
    const action = actionAfterOptions(args);
    if (["profile", "flake"].includes(action ?? "") && args.some((token) => ["install", "update", "upgrade"].includes(token.toLowerCase()))) return "Nix package/input acquisition";
  }

  if (/^(?:install|update)-(?:module|package|script)$/i.test(executable)) return "PowerShell package/module installation/update";

  return undefined;
}

export function getBlockedDependencyCommandReason(command: string, depth = 0): string | undefined {
  const normalized = command.replace(/\\\r?\n/g, " ").replace(/`\r?\n/g, " ");

  if (/(?:^|[;&|\r\n]\s*)(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b[^\r\n]{0,2000}\|\s*(?:(?:sudo|doas)\s+)?(?:sh|bash|zsh|fish|pwsh|powershell|iex|invoke-expression)\b/i.test(normalized)) {
    return "remote script download piped to an interpreter";
  }

  const segments = normalized.split(/\r?\n|&&|\|\||;|\|/);
  for (let segment of segments) {
    segment = segment.trim().replace(/^(?:(?:then|do|else)\s+)+/i, "");
    const reason = inspectDirectCommand(tokenize(segment), depth);
    if (reason) return reason;
  }

  return undefined;
}

export default function (pi: ExtensionAPI) {
  pi.on("session_start", (_event, ctx) => {
    if (ctx.hasUI) ctx.ui.setStatus("dependency-install-guard", "deps: install locked");
  });

  pi.on("before_agent_start", (event) => ({
    systemPrompt: `${event.systemPrompt}\n\n## Mandatory dependency-installation policy\n${POLICY}`,
  }));

  pi.on("tool_call", (event, ctx) => {
    if (event.toolName !== "bash") return undefined;

    const command = typeof event.input.command === "string" ? event.input.command : "";
    const detected = getBlockedDependencyCommandReason(command);
    if (!detected) return undefined;

    if (ctx.hasUI) ctx.ui.notify(`Blocked dependency install: ${detected}`, "warning");
    return { block: true, reason: `${BLOCK_REASON}\n\nDetected: ${detected}.` };
  });
}
