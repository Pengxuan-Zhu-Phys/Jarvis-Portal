from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IOContext:
    """Runtime-owned context passed into format adapters.

    Jarvis-Portal adapters should use this context instead of inheriting from
    Jarvis-HEP runtime classes or guessing project paths.
    """

    logger: Any = None
    io_manager: Any | None = None
    sample_uuid: str | None = None
    pack_id: str | None = None
    sample_save_dir: str | None = None
    project_root: str | None = None
    module: str | None = None
    resolve_path: Callable[[str], str] | None = None
    evaluate_expression: Callable[[str, Mapping[str, Any]], Any] | None = None
    runtime_values: Mapping[str, Any] = field(default_factory=dict)

    def path(self, value: str | Path) -> Path:
        raw = str(value)
        if self.resolve_path is not None:
            return Path(self.resolve_path(raw))
        path = Path(raw).expanduser()
        if not path.is_absolute() and self.project_root:
            path = Path(self.project_root) / path
        return path

    async def run_blocking(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self.io_manager is not None and hasattr(self.io_manager, "run_blocking"):
            return await self.io_manager.run_blocking(fn, *args, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    def log_debug(self, message: str) -> None:
        if self.logger is not None and hasattr(self.logger, "debug"):
            self.logger.debug(message)

    def log_info(self, message: str) -> None:
        if self.logger is not None and hasattr(self.logger, "info"):
            self.logger.info(message)

    def log_warning(self, message: str) -> None:
        if self.logger is not None and hasattr(self.logger, "warning"):
            self.logger.warning(message)
