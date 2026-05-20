from __future__ import annotations

from jarvis_portal.adapters.file import FileAdapter
from jarvis_portal.adapters.json import JsonAdapter
from jarvis_portal.adapters.slha import SLHAAdapter
from jarvis_portal.adapters.xslha import XSLHAAdapter
from jarvis_portal.registry import IORegistry


def register_builtins(registry: IORegistry) -> IORegistry:
    registry.register("JSON", JsonAdapter(), "both")
    registry.register("File", FileAdapter(), "both")
    registry.register("SLHA", SLHAAdapter(), "both")
    registry.register("xSLHA", XSLHAAdapter(), "output")
    return registry
