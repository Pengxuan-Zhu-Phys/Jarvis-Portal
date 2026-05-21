from __future__ import annotations

from typing import Any

from jarvis_portal.context import IOContext


class SLHAAdapter:
    format_name = "SLHA"
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
        pyslha = _import_pyslha()
        path = context.path(spec["path"])
        content = path.read_text(encoding=spec.get("encoding", "utf-8"))
        document = pyslha.readSLHA(content)

        for operation in spec.get("operations", []):
            value = operation.get("value", data.get(operation.get("name")))
            if operation.get("op") == "replace_text":
                content = content.replace(str(operation["placeholder"]), str(value))
                document = pyslha.readSLHA(content)
                continue
            block = operation.get("block")
            entry = operation.get("entry")
            if block is None or entry is None:
                continue
            key = tuple(entry) if isinstance(entry, list) else entry
            document.blocks[block][key] = value

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            pyslha.writeSLHA(document, ignorenobr=True),
            encoding=spec.get("encoding", "utf-8"),
        )
        return {}

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        pyslha = _import_pyslha()
        path = context.path(spec["path"])
        document = pyslha.readSLHA(path.read_text(encoding=spec.get("encoding", "utf-8")))
        observables: dict[str, Any] = {}
        for variable in spec.get("variables", []):
            name = variable["name"]
            block = variable.get("block")
            entry = variable.get("entry")
            if block == "DECAY":
                observables[name] = _read_decay(document, entry)
            else:
                key = tuple(entry) if isinstance(entry, list) else entry
                observables[name] = document.blocks[block][key]
        return observables


def _read_decay(document: Any, entry: Any) -> Any:
    if isinstance(entry, int):
        return float(document.decays[entry].__dict__["totalwidth"])
    decays = document.decays[entry[0]].__dict__["decays"]
    for decay in decays:
        if set(entry[1:]) == set(decay.ids):
            return decay.br
    return 0.0


def _import_pyslha():
    try:
        import pyslha
    except ImportError as exc:
        raise ImportError("SLHA support requires `pip install Jarvis-HEP-Portal[slha]`.") from exc
    return pyslha
