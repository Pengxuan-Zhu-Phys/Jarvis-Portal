from __future__ import annotations

from jarvis_portal.adapters.csv import CsvAdapter
from jarvis_portal.adapters.dat import DatAdapter
from jarvis_portal.adapters.json import JsonAdapter
from jarvis_portal.adapters.tsv import TsvAdapter
from jarvis_portal.registry import IORegistry


def register_builtins(registry: IORegistry) -> IORegistry:
    registry.register("JSON", JsonAdapter(), "both")
    registry.register("CSV", CsvAdapter(), "both")
    registry.register("TSV", TsvAdapter(), "both")
    registry.register("DAT", DatAdapter(), "both")
    return registry
