from __future__ import annotations

from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(path: str, allow_outside_project: bool = False) -> Path:
    """Resolve a user path and optionally allow access outside the project root."""
    candidate = (PROJECT_ROOT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        if not allow_outside_project:
            raise ValueError(
                "Path is outside the project root. Ask the user for approval first, "
                "then retry with allow_outside_project=True."
            ) from exc
    return candidate


def resolve_any_path(path: str, base_dir: Path | None = None) -> Path:
    """Resolve a path without restricting it to the project root."""
    if Path(path).is_absolute():
        return Path(path).resolve()
    return ((base_dir or PROJECT_ROOT) / path).resolve()


def run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout_seconds: int | None = None,
) -> str:
    """Run a subprocess command and return combined output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout_seconds} seconds."
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return output or f"{' '.join(command)} exited with code {result.returncode}"
