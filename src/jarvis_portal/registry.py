from __future__ import annotations

from typing import Any, Literal, Protocol

from jarvis_portal.context import IOContext

Direction = Literal["input", "output", "both"]


class MissingAdapterError(ValueError):
    """Raised when no adapter is registered for a format and direction."""


class IOAdapter(Protocol):
    format_name: str
    direction: Direction

    async def write_input(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    async def read_output(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        ...


class IORegistry:
    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], IOAdapter] = {}

    def register(
        self,
        format_name: str,
        adapter: IOAdapter,
        direction: str | None = None,
        *,
        override: bool = False,
    ) -> None:
        fmt = normalize_format(format_name)
        adapter_direction = normalize_direction(direction or adapter.direction)
        key = (fmt, adapter_direction)
        if key in self._adapters and not override:
            raise ValueError(
                f"IO adapter for format '{format_name}' and direction "
                f"'{adapter_direction}' is already registered."
            )
        self._adapters[key] = adapter

    def get(self, format_name: str, direction: str) -> IOAdapter:
        fmt = normalize_format(format_name)
        wanted_direction = normalize_direction(direction)
        adapter = self._adapters.get((fmt, wanted_direction))
        if adapter is not None:
            return adapter
        adapter = self._adapters.get((fmt, "both"))
        if adapter is not None:
            return adapter

        available = self.available_formats(wanted_direction)
        available_text = ", ".join(available) if available else "none"
        raise MissingAdapterError(
            f"Unsupported IO format '{format_name}' for {wanted_direction}. "
            f"Available {wanted_direction} formats: {available_text}."
        )

    def available_formats(self, direction: str | None = None) -> list[str]:
        if direction is None:
            names = {adapter.format_name for adapter in self._adapters.values()}
        else:
            wanted_direction = normalize_direction(direction)
            names = {
                adapter.format_name
                for (_, adapter_direction), adapter in self._adapters.items()
                if adapter_direction in {wanted_direction, "both"}
            }
        return sorted(names, key=str.lower)


def normalize_format(format_name: str) -> str:
    text = str(format_name or "").strip()
    if not text:
        raise ValueError("IO format name must not be empty.")
    return text.casefold()


def normalize_direction(direction: str) -> str:
    text = str(direction or "").strip().casefold()
    if text not in {"input", "output", "both"}:
        raise ValueError(f"Unsupported IO direction '{direction}'.")
    return text


def create_default_registry() -> IORegistry:
    from jarvis_portal.builtins import register_builtins

    registry = IORegistry()
    register_builtins(registry)
    return registry


_DEFAULT_REGISTRY: IORegistry | None = None


def default_registry() -> IORegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = create_default_registry()
    return _DEFAULT_REGISTRY


def register(
    format_name: str,
    adapter: IOAdapter,
    direction: str | None = None,
    *,
    override: bool = False,
) -> None:
    default_registry().register(format_name, adapter, direction, override=override)


def get(format_name: str, direction: str) -> IOAdapter:
    return default_registry().get(format_name, direction)


def available_formats(direction: str | None = None) -> list[str]:
    return default_registry().available_formats(direction)
