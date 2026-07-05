from __future__ import annotations

import subprocess

from langchain_core.tools import tool

from app.tools.common import PROJECT_ROOT, resolve_any_path


@tool
def run_shell_command(
    command: str,
    cwd: str = ".",
    timeout_seconds: int | None = None,
) -> str:
    """Run an arbitrary shell command from the given working directory."""
    if not command.strip():
        return "command must not be empty."
    if timeout_seconds is not None and timeout_seconds <= 0:
        return "timeout_seconds must be greater than 0."

    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    command_cwd.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            command,
            cwd=command_cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            shell=True,
            executable="/bin/bash",
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout_seconds} seconds."

    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return output or f"{command} exited with code {result.returncode}"
