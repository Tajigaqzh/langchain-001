from __future__ import annotations

from langchain_core.tools import tool

from app.tools.common import PROJECT_ROOT, resolve_any_path, run_command


@tool
def git_status(cwd: str = ".") -> str:
    """Show git status in short form for the given working directory."""
    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    return run_command(["git", "status", "--short"], cwd=command_cwd)


@tool
def git_diff(target: str = "", cwd: str = ".") -> str:
    """Show git diff for the working directory or a specific target path."""
    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    command = ["git", "diff"]
    if target:
        resolved_target = resolve_any_path(target, base_dir=command_cwd)
        command.extend(["--", str(resolved_target)])
    return run_command(command, cwd=command_cwd)
