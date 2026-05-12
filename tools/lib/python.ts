import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

export type Command = {
  command: string;
  args: string[];
};

export function pythonFromActiveEnvironment(): string | null {
  // 优先复用当前已激活的 conda 环境
  const condaPrefix = process.env.CONDA_PREFIX;
  if (condaPrefix) {
    const candidate =
      process.platform === "win32"
        ? path.join(condaPrefix, "python.exe")
        : path.join(condaPrefix, "bin", "python");
    if (existsSync(candidate)) {
      return candidate;
    }
  }

  // 若非 conda，尝试复用当前已激活的 venv
  const virtualEnv = process.env.VIRTUAL_ENV;
  if (virtualEnv) {
    const candidate =
      process.platform === "win32"
        ? path.join(virtualEnv, "Scripts", "python.exe")
        : path.join(virtualEnv, "bin", "python");
    if (existsSync(candidate)) {
      return candidate;
    }
  }

  return null;
}

export function fallbackPythonCommand(): Command {
  if (process.platform === "win32") {
    return { command: "py", args: ["-3"] };
  }

  return { command: "python3", args: [] };
}

export function buildPythonCommand(): Command {
  const activePython = pythonFromActiveEnvironment();
  if (activePython) {
    return { command: activePython, args: [] };
  }

  // 通用兜底执行指令
  return fallbackPythonCommand();
}

export function hasManagedEnvironment(): boolean {
  return Boolean(process.env.CONDA_PREFIX || process.env.VIRTUAL_ENV);
}

export function run(command: Command, extraArgs: string[]): never {
  const result = spawnSync(command.command, [...command.args, ...extraArgs], {
    stdio: "inherit",
    shell: false,
    env: process.env,
  });

  if (result.error) {
    throw result.error;
  }

  process.exit(result.status ?? 1);
}
