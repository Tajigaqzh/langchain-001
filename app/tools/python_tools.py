from __future__ import annotations

import os
import tempfile

from langchain_core.tools import tool

from app.tools.common import PROJECT_ROOT, resolve_any_path, run_command


@tool
def run_pytest(target: str = "", cwd: str = ".") -> str:
    """Run pytest for the whole project or a specific target path."""
    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    command = ["pytest"]
    if target:
        resolved_target = resolve_any_path(target, base_dir=command_cwd)
        command.append(str(resolved_target))
    return run_command(command, cwd=command_cwd)


@tool
def run_python_module(module: str, cwd: str = ".") -> str:
    """Run a Python module with `python -m` from the given working directory."""
    if not module:
        return "Module name must not be empty."
    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    return run_command(["python", "-m", module], cwd=command_cwd)


@tool
def compile_project(cwd: str = ".") -> str:
    """Run a Python compile check from the given working directory."""
    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    return run_command(
        ["python", "-m", "compileall", "app", "tests", "main.py"],
        cwd=command_cwd,
    )


@tool
def run_python_script(
    script: str,
    cwd: str = ".",
    timeout_seconds: int | None = None,
) -> str:
    """Write a temporary Python script and execute it from the given working directory."""
    if not script.strip():
        return "script must not be empty."
    if timeout_seconds is not None and timeout_seconds <= 0:
        return "timeout_seconds must be greater than 0."

    command_cwd = resolve_any_path(cwd, base_dir=PROJECT_ROOT)
    command_cwd.mkdir(parents=True, exist_ok=True)

    script_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".py",
            prefix="agent_script_",
            dir=command_cwd,
            delete=False,
        ) as handle:
            handle.write(script)
            script_path = handle.name
        return run_command(
            ["python", script_path],
            cwd=command_cwd,
            timeout_seconds=timeout_seconds,
        )
    finally:
        if script_path and os.path.exists(script_path):
            os.remove(script_path)
