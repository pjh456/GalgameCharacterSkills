import { buildPythonCommand, run } from "./lib/python";

const python = buildPythonCommand();
const extraArgs = process.argv.slice(2);
run(python, ["-m", "ruff", "check", "gal_chara_skill/", ...extraArgs]);
