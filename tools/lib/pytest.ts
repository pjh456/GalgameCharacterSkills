import { existsSync, mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";

export type TestMode = "test" | "cov";

export type TestTarget = {
  path?: string;
  coverage?: string;
};

// 统一维护测试目标，避免为每个模块手写一套命令分支
export const TEST_TARGETS: Record<string, TestTarget> = {
  all: {
    coverage: "gal_chara_skill",
  },
  conf: {
    path: "tests/conf",
    coverage: "gal_chara_skill.conf",
  },
  log: {
    path: "tests/log",
    coverage: "gal_chara_skill.log",
  },
};

function isDirectoryWritable(directory: string): boolean {
  try {
    mkdirSync(directory, { recursive: true });
    const probePath = path.join(directory, ".bun-pytest-probe");
    writeFileSync(probePath, "probe");
    unlinkSync(probePath);
    return true;
  } catch {
    return false;
  }
}

export function resolvePytestCacheDir(cwd: string = process.cwd()): string {
  const primaryCacheDir = path.join(cwd, "tmp", "pytest-cache");
  if (isDirectoryWritable(primaryCacheDir)) {
    return primaryCacheDir;
  }

  // 主缓存目录不可写时，退回到仓库内独立隐藏目录，保持缓存能力
  const fallbackCacheDir = path.join(cwd, ".cache", "pytest");
  mkdirSync(fallbackCacheDir, { recursive: true });
  return fallbackCacheDir;
}

export function buildPytestArgs(target: TestTarget, mode: TestMode): string[] {
  const args = ["-m", "pytest", "-o", `cache_dir=${resolvePytestCacheDir()}`];

  if (target.path) {
    args.push(target.path);
  }

  if (mode === "cov" && target.coverage) {
    // 优先保留缓存能力，仅在默认目录不可写时自动切换到回退目录
    args.push(`--cov=${target.coverage}`, "--cov-report=term-missing");
  }

  return args;
}

export function parsePytestTask(rawTask: string | undefined): { mode: TestMode; targetKey: string } | null {
  if (!rawTask) {
    return null;
  }

  // 任务命名统一为 mode[:target]，例如 test:conf、cov:log
  const [mode, targetKey = "all"] = rawTask.split(":");
  if ((mode !== "test" && mode !== "cov") || !(targetKey in TEST_TARGETS)) {
    return null;
  }

  return { mode, targetKey };
}
