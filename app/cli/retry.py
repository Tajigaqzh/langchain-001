from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from app.cli.errors import describe_model_error
from app.cli.runtime import CliRuntime
from app.ui import CliConsole

T = TypeVar("T")


def retry_model_call(
    operation: Callable[[], T],
    runtime: CliRuntime,
    cli_console: CliConsole,
) -> T:
    """Retry a model operation after transient failures."""
    for retry_index in range(runtime.retry_attempts + 1):
        try:
            return operation()
        except Exception as exc:
            if retry_index >= runtime.retry_attempts:
                cli_console.print_model_error(describe_model_error(exc))
                raise
            cli_console.print_retry_notice(
                error=Exception(describe_model_error(exc)),
                retry_number=retry_index + 1,
                max_retries=runtime.retry_attempts,
                delay=runtime.retry_delay,
            )
            if runtime.retry_delay > 0:
                time.sleep(runtime.retry_delay)
    raise RuntimeError("Model retry loop exited unexpectedly.")
