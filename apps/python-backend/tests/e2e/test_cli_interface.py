"""E2E tests for CLI interface functionality."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIInterfaceE2E:
    """E2E tests for CLI interface."""

    @staticmethod
    def _env_with_src_path() -> dict[str, str]:
        env = os.environ.copy()
        src_path = Path(__file__).resolve().parents[2] / "src"
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else str(src_path)
        return env

    @staticmethod
    def strip_ansi_codes(text: str) -> str:
        """Remove ANSI escape codes from text."""
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_escape.sub("", text)

    def test_cli_welcome_message(self) -> None:
        """Test that CLI displays welcome message on startup."""
        # Run the CLI command
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "city_data_backend.main"],
            capture_output=True,
            text=True,
            check=False,
            env=self._env_with_src_path(),
        )

        assert result.returncode == 0
        assert "Welcome to City Data Backend!" in result.stdout
        assert "Type --help for more information" in result.stdout

    def test_cli_help_command(self) -> None:
        """Test that CLI displays help message with --help flag."""
        # Run the CLI command with --help
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "city_data_backend.main", "--help"],
            capture_output=True,
            text=True,
            check=False,
            env=self._env_with_src_path(),
        )

        assert result.returncode == 0
        # Strip ANSI codes for proper assertion
        clean_output = self.strip_ansi_codes(result.stdout)
        assert "Usage:" in clean_output
        assert "Options" in clean_output  # Typer uses "Options" without colon
        assert "help" in clean_output  # Check without dashes as they may vary

    def test_cli_with_interface_type_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that CLI respects INTERFACE_TYPE environment variable."""
        # Set environment variable
        monkeypatch.setenv("INTERFACE_TYPE", "cli")

        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "city_data_backend.main"],
            capture_output=True,
            text=True,
            check=False,
            env=self._env_with_src_path(),
        )

        assert result.returncode == 0
        assert "Welcome to City Data Backend!" in result.stdout
