from __future__ import annotations

from jarvis_portal.adapters.json import JsonAdapter
from jarvis_portal.registry import IORegistry


def register_builtins(registry: IORegistry) -> IORegistry:
    registry.register("JSON", JsonAdapter(), "both")
    return registry
