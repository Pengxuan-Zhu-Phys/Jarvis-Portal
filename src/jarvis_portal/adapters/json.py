from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis_portal.context import IOContext


class JsonAdapter:
    format_name = "JSON"
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
        payload = _read_json_document(path)

        for operation in _iter_write_operations(spec, data):
            value = operation.get("value")
            entry = operation.get("entry")
            name = operation.get("name")
            if entry:
                _set_nested(payload, str(entry), value)
            elif name:
                payload[str(name)] = value

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
        return {}

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        path = context.path(spec["path"])
        payload = _read_json_document(path)
        observables: dict[str, Any] = {}
        for variable in spec.get("variables", []):
            name = variable["name"]
            entry = variable.get("entry")
            observables[name] = _get_nested(payload, str(entry)) if entry else payload.get(name)
        return observables


def _read_json_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def _iter_write_operations(spec: dict[str, Any], data: dict[str, Any]):
    operations = spec.get("operations")
    if operations is not None:
        yield from operations
        return

    for variable in spec.get("variables", []):
        name = variable["name"]
        value = variable.get("value", data.get(name))
        item = {"name": name, "value": value}
        if "entry" in variable:
            item["entry"] = variable["entry"]
        yield item


def _set_nested(payload: dict[str, Any], entry: str, value: Any) -> None:
    parts = [part for part in entry.split(".") if part]
    if not parts:
        raise ValueError("JSON entry path must not be empty.")
    current = payload
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise ValueError(f"JSON entry '{entry}' crosses non-object key '{part}'.")
        current = next_value
    current[parts[-1]] = value


def _get_nested(payload: dict[str, Any], entry: str) -> Any:
    current: Any = payload
    for part in [part for part in entry.split(".") if part]:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
