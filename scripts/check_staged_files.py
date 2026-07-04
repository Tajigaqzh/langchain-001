#!/usr/bin/env python3
"""Check staged files before commit for this Python Agent project."""

import ast
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

MAX_RECOMMENDED_FILE_LINES = 1000
MAX_RECOMMENDED_FUNCTION_LINES = 80
COMMENTED_CODE_RULE = "commented-code"
YELLOW = "\033[33m"
RESET = "\033[0m"

TEXT_EXTENSIONS = {".md", ".py", ".txt", ".yaml", ".yml", ".json", ".toml"}
PYTHON_EXTENSIONS = {".py"}
BLOCKED_PATH_PARTS = {
    ".codegraph",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
BLOCKED_FILE_NAMES = {".env", ".DS_Store"}
BLOCKED_SUFFIXES = {".pyc", ".pyo"}


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and return captured output for staged checks."""
    return subprocess.run(
        command,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )


def get_staged_files() -> list[Path]:
    """Return existing files currently staged for add, copy, modify, or rename."""
    result = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to read staged files.")

    return [
        Path(file_path)
        for file_path in result.stdout.split("\0")
        if file_path and Path(file_path).exists()
    ]


def is_blocked_local_file(path: Path) -> bool:
    """Detect local-only files that must never be committed."""
    parts = set(path.parts)
    return (
        bool(parts & BLOCKED_PATH_PARTS)
        or path.name in BLOCKED_FILE_NAMES
        or path.suffix in BLOCKED_SUFFIXES
    )


def read_text(path: Path) -> str:
    """Read a text file as UTF-8 for lightweight staged checks."""
    return path.read_text(encoding="utf-8")


def is_code_like_comment(line: str) -> bool:
    """Decide whether a comment line looks like disabled Python code."""
    text = re.sub(r"^\s*#\s?", "", line).strip()
    if not text:
        return False

    return bool(
        re.search(
            r"(:$|=|\.invoke\(|\.append\(|\b(def|class|return|import|from|if|for|while|try|except|with|raise)\b)",
            text,
        )
    )


def parse_bypass(line: str) -> tuple[bool, str] | None:
    """Parse commented-code bypass markers and return scope plus reason."""
    match = re.search(
        r"staged-check-disable(-next-line)?\s+commented-code\s+--\s+(.+)$",
        line,
    )
    if not match:
        return None

    reason = match.group(2).strip()
    if not reason:
        return None

    return bool(match.group(1)), reason


def find_commented_code_blocks(path: Path, content: str) -> tuple[list[str], list[str]]:
    """Find large commented code blocks while honoring explicit bypass markers."""
    findings: list[str] = []
    bypasses: list[str] = []
    lines = content.splitlines()
    active_bypass_reason: str | None = None
    next_line_bypasses: dict[int, str] = {}
    block_start = 0
    block_lines: list[tuple[int, str]] = []

    def flush_block() -> None:
        """Evaluate and record the current contiguous comment block."""
        nonlocal block_start, block_lines
        if len(block_lines) < 3:
            block_lines = []
            return

        code_like_count = sum(1 for _, text in block_lines if is_code_like_comment(text))
        if code_like_count < 2:
            block_lines = []
            return

        start_line = block_start
        end_line = block_lines[-1][0]
        reason = next_line_bypasses.get(start_line) or active_bypass_reason
        if reason:
            bypasses.append(
                f"{path}:{start_line}-{end_line} bypassed {COMMENTED_CODE_RULE}: {reason}"
            )
        else:
            findings.append(
                f"{path}:{start_line}-{end_line} contains a large commented code block"
            )

        block_lines = []

    for index, line in enumerate(lines, start=1):
        bypass = parse_bypass(line)
        if bypass:
            is_next_line, reason = bypass
            if is_next_line:
                next_line_bypasses[index + 1] = reason
            else:
                active_bypass_reason = reason
            continue

        if f"staged-check-enable {COMMENTED_CODE_RULE}" in line:
            active_bypass_reason = None
            continue

        if line.lstrip().startswith("#"):
            if not block_lines:
                block_start = index
            block_lines.append((index, line))
            continue

        flush_block()

    flush_block()
    return findings, bypasses


def check_python_compile(path: Path) -> str | None:
    """Compile a staged Python file and return an error message on failure."""
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        return f"{path}: Python compile failed: {exc.msg}"
    return None


def find_python_warnings(path: Path, content: str) -> list[str]:
    """Find non-blocking Python maintainability warnings."""
    warnings: list[str] = []
    lines = content.splitlines()

    if len(lines) > MAX_RECOMMENDED_FILE_LINES:
        warnings.append(
            f"{path}: file has {len(lines)} lines; consider splitting files over {MAX_RECOMMENDED_FILE_LINES} lines."
        )

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return warnings

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        end_lineno = getattr(node, "end_lineno", node.lineno)
        function_lines = end_lineno - node.lineno + 1
        if function_lines > MAX_RECOMMENDED_FUNCTION_LINES:
            warnings.append(
                f"{path}:{node.lineno} function '{node.name}' has {function_lines} lines; consider splitting it."
            )

        if ast.get_docstring(node) is None:
            warnings.append(
                f"{path}:{node.lineno} function '{node.name}' is missing a docstring comment."
            )

    return warnings


def main() -> int:
    """Run all staged checks and print blocking findings plus warnings."""
    staged_files = get_staged_files()
    if not staged_files:
        print("No staged files to check.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    bypasses: list[str] = []

    for path in staged_files:
        if is_blocked_local_file(path):
            errors.append(f"{path}: local-only file must not be committed.")
            continue

        if path.suffix in PYTHON_EXTENSIONS:
            compile_error = check_python_compile(path)
            if compile_error:
                errors.append(compile_error)

        if path.suffix not in TEXT_EXTENSIONS:
            continue

        try:
            content = read_text(path)
        except UnicodeDecodeError:
            continue

        comment_errors, comment_bypasses = find_commented_code_blocks(path, content)
        errors.extend(comment_errors)
        bypasses.extend(comment_bypasses)

        if path.suffix in PYTHON_EXTENSIONS:
            warnings.extend(find_python_warnings(path, content))

    if bypasses:
        print(f"{YELLOW}Commented-code bypasses:{RESET}")
        for bypass in bypasses:
            print(f"{YELLOW}- {bypass}{RESET}")

    if warnings:
        print(f"{YELLOW}Warnings:{RESET}")
        for warning in warnings:
            print(f"{YELLOW}- {warning}{RESET}")

    if errors:
        print("Staged check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Staged check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
