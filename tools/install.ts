import { askForConfirmation } from "./lib/prompt";
import { buildPythonCommand, hasManagedEnvironment, run } from "./lib/python";

async function main(): Promise<void> {
  const python = buildPythonCommand();

  if (!hasManagedEnvironment()) {
    // 未检测到虚拟环境时要求显式确认，避免误装到系统 Python
    const confirmed = await askForConfirmation(
      "No active virtual environment detected. Install editable dependencies into the current Python environment? [y/N] ",
    );

    if (!confirmed) {
      process.exit(1);
    }
  }

  run(python, ["-m", "pip", "install", "-e", "."]);
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
