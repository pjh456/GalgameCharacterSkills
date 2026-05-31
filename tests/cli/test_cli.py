from __future__ import annotations

from click.testing import CliRunner
from gal_chara_skill.cli import main


class TestCliMain:
    def test_main_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "GalgameCharacterSkills" in result.output

    def test_run_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.output

    def test_resume_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["resume", "--help"])
        assert result.exit_code == 0
        assert "--task-id" in result.output

    def test_check_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["check", "--help"])
        assert result.exit_code == 0
        assert "--task-id" in result.output

    def test_ping_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["ping", "--help"])
        assert result.exit_code == 0
        assert "--api-key" in result.output

    def test_run_missing_required_args(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["run"])
        assert result.exit_code != 0

    def test_resume_missing_task_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["resume"])
        assert result.exit_code != 0

    def test_version_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_run_with_args_fails_no_input(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "run",
            "--role-name", "TestChar",
            "--api-key", "sk-test",
            "--input", "/nonexistent/input.txt",
        ])
        assert result.exit_code != 0

    def test_check_command_runs(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "check",
            "--task-id", "test-task-999",
            "--output-dir", "/tmp",
        ])
        assert result.exit_code == 0
        assert "任务 ID" in result.output
