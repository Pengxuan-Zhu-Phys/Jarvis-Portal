from __future__ import annotations

from typing import Any

from jarvis_portal.context import IOContext


class FileAdapter:
    format_name = "File"
    direction = "both"

    async def write_input(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await context.run_blocking(self._write_sync, context, spec, data)

    async def read_output(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        return await context.run_blocking(self._read_sync, context, spec)

    def _write_sync(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        path = context.path(spec["path"])
        content = spec.get("content", data.get(spec.get("name", "content"), ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding=spec.get("encoding", "utf-8"))
        return {}

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        if not spec.get("read_content", False):
            return {}
        path = context.path(spec["path"])
        name = spec.get("name", "content")
        return {name: path.read_text(encoding=spec.get("encoding", "utf-8"))}
