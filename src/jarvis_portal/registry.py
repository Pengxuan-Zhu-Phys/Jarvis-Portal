from __future__ import annotations

from importlib import metadata
import warnings
from typing import Any, Iterable, Literal, Protocol

from jarvis_portal.context import IOContext

Direction = Literal["input", "output", "both"]
ENTRY_POINT_GROUP = "jarvishep.io"
EXPOSED_FORMATS = frozenset({"json"})


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

    def adapters(self, direction: str | None = None) -> list[IOAdapter]:
        wanted_direction = normalize_direction(direction) if direction is not None else None
        seen: set[int] = set()
        adapters: list[IOAdapter] = []
        for (_, adapter_direction), adapter in self._adapters.items():
            if wanted_direction is not None and adapter_direction not in {wanted_direction, "both"}:
                continue
            identity = id(adapter)
            if identity in seen:
                continue
            adapters.append(adapter)
            seen.add(identity)
        return sorted(adapters, key=lambda item: item.format_name.lower())


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


def create_entry_point_registry(
    *,
    group: str = ENTRY_POINT_GROUP,
    include_builtins: bool = True,
    on_error: str = "warn",
    allowed_formats: Iterable[str] | None = EXPOSED_FORMATS,
) -> IORegistry:
    registry = create_default_registry() if include_builtins else IORegistry()
    discover_entry_points(
        registry,
        group=group,
        override=True,
        on_error=on_error,
        allowed_formats=allowed_formats,
    )
    return registry


def discover_entry_points(
    registry: IORegistry,
    *,
    group: str = ENTRY_POINT_GROUP,
    override: bool = False,
    on_error: str = "warn",
    allowed_formats: Iterable[str] | None = EXPOSED_FORMATS,
) -> IORegistry:
    allowed = _normalize_allowed_formats(allowed_formats)
    for entry_point in _entry_points(group):
        if allowed is not None and normalize_format(entry_point.name) not in allowed:
            continue
        try:
            adapter = _load_adapter_entry_point(entry_point)
        except Exception as exc:
            _handle_entry_point_error(entry_point, exc, on_error=on_error)
            continue
        if allowed is not None and normalize_format(adapter.format_name) not in allowed:
            continue
        registry.register(adapter.format_name, adapter, adapter.direction, override=override)
    return registry


def _entry_points(group: str):
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return entry_points.select(group=group)
    return entry_points.get(group, [])


def _normalize_allowed_formats(allowed_formats: Iterable[str] | None) -> set[str] | None:
    if allowed_formats is None:
        return None
    return {normalize_format(format_name) for format_name in allowed_formats}


def _load_adapter_entry_point(entry_point: metadata.EntryPoint) -> IOAdapter:
    loaded = entry_point.load()
    adapter = loaded() if isinstance(loaded, type) else loaded
    _validate_adapter(adapter, source=entry_point.name)
    return adapter


def _handle_entry_point_error(
    entry_point: metadata.EntryPoint,
    exc: Exception,
    *,
    on_error: str,
) -> None:
    mode = str(on_error).strip().casefold()
    if mode == "raise":
        raise exc
    if mode == "ignore":
        return
    if mode != "warn":
        raise ValueError("entry point error mode must be 'warn', 'ignore', or 'raise'.")
    warnings.warn(
        f"Skipping IO adapter entry point '{entry_point.name}': {exc}",
        RuntimeWarning,
        stacklevel=2,
    )


def _validate_adapter(adapter: Any, *, source: str) -> IOAdapter:
    missing = [
        name
        for name in ("format_name", "direction", "write_input", "read_output")
        if not hasattr(adapter, name)
    ]
    if missing:
        missing_text = ", ".join(missing)
        raise TypeError(f"IO adapter entry point '{source}' is missing: {missing_text}.")
    normalize_format(adapter.format_name)
    normalize_direction(adapter.direction)
    return adapter


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
