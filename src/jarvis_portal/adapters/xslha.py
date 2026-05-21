from __future__ import annotations

from copy import deepcopy
from typing import Any

from jarvis_portal.context import IOContext


class XSLHAAdapter:
    format_name = "xSLHA"
    direction = "output"

    async def write_input(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError("xSLHA input writing is not currently supported.")

    async def read_output(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        return await context.run_blocking(self._read_sync, context, spec)

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        xslha = _import_xslha()
        path = context.path(spec["path"])
        document = xslha.read(str(path))
        observables: dict[str, Any] = {}
        for variable in spec.get("variables", []):
            name = variable["name"]
            block = str(variable.get("block", "")).upper()
            entry = variable.get("entry")
            value = _read_xslha_value(document, block, entry)
            if isinstance(value, list):
                observables[f"Re[{name}]"] = value[0]
                observables[f"Im[{name}]"] = value[1]
            else:
                observables[name] = value
        return observables


def _read_xslha_value(document: Any, block: str, entry: Any) -> Any:
    if block == "DECAY":
        if isinstance(entry, int):
            return document.widths[entry]
        decays = document.br[entry[0]]
        return decays.get(tuple(sorted(deepcopy(entry[1:]))), 0.0)
    if block == "DECAY1L":
        if isinstance(entry, int):
            return document.widths1L[entry]
        decays = document.br1L[entry[0]]
        return decays.get(tuple(sorted(deepcopy(entry[1:]))), 0.0)
    key = str(entry) if isinstance(entry, int) else ",".join(map(str, entry))
    return document.blocks[block][key]


def _import_xslha():
    try:
        import xslha
    except ImportError as exc:
        raise ImportError("xSLHA support requires `pip install Jarvis-HEP-Portal[xslha]`.") from exc
    return xslha
