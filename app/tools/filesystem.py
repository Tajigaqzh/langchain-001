from __future__ import annotations

import json
import shutil
from datetime import datetime

from langchain_core.tools import tool

from app.tools.common import PROJECT_ROOT, resolve_path, run_command


@tool
def list_directory(path: str = ".", allow_outside_project: bool = False) -> str:
    """List files and subdirectories under a project-relative directory."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"Path does not exist: {path}"
    if not target.is_dir():
        return f"Path is not a directory: {path}"

    entries = sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    if not entries:
        return f"Directory is empty: {target.relative_to(PROJECT_ROOT)}"

    lines = []
    for entry in entries:
        prefix = "[D]" if entry.is_dir() else "[F]"
        lines.append(f"{prefix} {entry.relative_to(PROJECT_ROOT)}")
    return "\n".join(lines)


@tool
def read_text_file(path: str, allow_outside_project: bool = False) -> str:
    """Read a UTF-8 text file from inside the project root."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"File does not exist: {path}"
    if not target.is_file():
        return f"Path is not a file: {path}"

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"File is not valid UTF-8 text: {path}"


@tool
def read_json_file(path: str, allow_outside_project: bool = False) -> str:
    """Read a JSON file and return it as formatted UTF-8 text."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"File does not exist: {path}"
    if not target.is_file():
        return f"Path is not a file: {path}"

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return f"File is not valid UTF-8 text: {path}"
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in {path}: {exc}"
    return json.dumps(data, ensure_ascii=False, indent=2)


@tool
def read_csv_preview(
    path: str,
    rows: int = 10,
    allow_outside_project: bool = False,
) -> str:
    """Read the first few lines of a CSV-like text file."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"File does not exist: {path}"
    if not target.is_file():
        return f"Path is not a file: {path}"
    if rows <= 0:
        return "rows must be greater than 0."

    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"File is not valid UTF-8 text: {path}"
    preview = lines[:rows]
    return "\n".join(preview) if preview else f"File is empty: {path}"


@tool
def search_text(
    pattern: str,
    path: str = ".",
    allow_outside_project: bool = False,
) -> str:
    """Search text with ripgrep inside the project root."""
    if not pattern:
        return "Pattern must not be empty."

    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"Path does not exist: {path}"

    return run_command(["rg", "-n", "--color", "never", pattern, str(target)])


@tool
def write_text_file(
    path: str,
    content: str,
    allow_outside_project: bool = False,
) -> str:
    """Write UTF-8 text to a project file, creating parent directories if needed."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {target.relative_to(PROJECT_ROOT)}"


@tool
def append_text_file(
    path: str,
    content: str,
    allow_outside_project: bool = False,
) -> str:
    """Append UTF-8 text to a file, creating parent directories if needed."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(content)
    return f"Appended {len(content)} characters to {target.relative_to(PROJECT_ROOT)}"


@tool
def tail_text_file(
    path: str,
    lines: int = 20,
    allow_outside_project: bool = False,
) -> str:
    """Return the last few lines of a UTF-8 text file."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"File does not exist: {path}"
    if not target.is_file():
        return f"Path is not a file: {path}"
    if lines <= 0:
        return "lines must be greater than 0."

    try:
        content = target.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"File is not valid UTF-8 text: {path}"
    preview = content[-lines:]
    return "\n".join(preview) if preview else f"File is empty: {path}"


@tool
def write_json_file(
    path: str,
    content: str,
    allow_outside_project: bool = False,
) -> str:
    """Validate JSON text and write it to a file using UTF-8 encoding."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return f"Content is not valid JSON: {exc}"

    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
    target.write_text(f"{serialized}\n", encoding="utf-8")
    return f"Wrote JSON to {target.relative_to(PROJECT_ROOT)}"


@tool
def make_directory(path: str, allow_outside_project: bool = False) -> str:
    """Create a directory and any missing parent directories."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    target.mkdir(parents=True, exist_ok=True)
    return f"Created directory {target.relative_to(PROJECT_ROOT)}"


@tool
def copy_file(
    source_path: str,
    destination_path: str,
    allow_outside_project: bool = False,
) -> str:
    """Copy a file from one path to another."""
    try:
        source = resolve_path(source_path, allow_outside_project=allow_outside_project)
        destination = resolve_path(destination_path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not source.exists():
        return f"Source file does not exist: {source_path}"
    if not source.is_file():
        return f"Source path is not a file: {source_path}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return f"Copied {source} to {destination}"


@tool
def move_file(
    source_path: str,
    destination_path: str,
    allow_outside_project: bool = False,
) -> str:
    """Move or rename a file from one path to another."""
    try:
        source = resolve_path(source_path, allow_outside_project=allow_outside_project)
        destination = resolve_path(destination_path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not source.exists():
        return f"Source file does not exist: {source_path}"
    if not source.is_file():
        return f"Source path is not a file: {source_path}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return f"Moved {source} to {destination}"


@tool
def path_info(path: str, allow_outside_project: bool = False) -> str:
    """Return basic information about a file or directory path."""
    try:
        target = resolve_path(path, allow_outside_project=allow_outside_project)
    except ValueError as exc:
        return str(exc)

    if not target.exists():
        return f"Path does not exist: {path}"

    stat = target.stat()
    relative = (
        str(target.relative_to(PROJECT_ROOT))
        if PROJECT_ROOT in target.parents or target == PROJECT_ROOT
        else str(target)
    )
    kind = "directory" if target.is_dir() else "file"
    return "\n".join(
        [
            f"path: {relative}",
            f"type: {kind}",
            f"size_bytes: {stat.st_size}",
            f"modified_at: {datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec='seconds')}",
        ]
    )
