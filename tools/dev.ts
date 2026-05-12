import { buildPythonCommand, run } from "./lib/python";
import { buildPytestArgs, parsePytestTask, TEST_TARGETS } from "./lib/pytest";

const parsedTask = parsePytestTask(process.argv[2]);
if (!parsedTask) {
  console.error("Unknown task. Use one of: test, test:conf, test:log, test:fs, cov, cov:conf, cov:log, cov:fs");
  process.exit(1);
}

const python = buildPythonCommand();
const target = TEST_TARGETS[parsedTask.targetKey];
run(python, buildPytestArgs(target, parsedTask.mode));
