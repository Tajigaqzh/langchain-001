from __future__ import annotations

from app.cli import parse_args, run_cli


def main() -> None:
    """Start the interactive Agent CLI from command-line arguments."""
    args = parse_args()
    run_cli(
        thread_id=args.thread_id,
        memory_backend=args.memory_backend,
        memory_path=args.memory_path,
        stream=args.stream,
    )


if __name__ == "__main__":
    main()
