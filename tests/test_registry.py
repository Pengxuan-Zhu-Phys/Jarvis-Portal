import pytest

from jarvis_portal import MissingAdapterError, create_default_registry
from jarvis_portal.registry import IORegistry


class DummyAdapter:
    format_name = "Dummy"
    direction = "both"

    async def write_input(self, context, spec, data):
        return {}

    async def read_output(self, context, spec):
        return {}


def test_registry_lookup_is_case_insensitive():
    registry = IORegistry()
    adapter = DummyAdapter()
    registry.register("Dummy", adapter, "both")

    assert registry.get("dummy", "input") is adapter
    assert registry.get("DUMMY", "output") is adapter


def test_duplicate_registration_requires_override():
    registry = IORegistry()
    registry.register("Dummy", DummyAdapter(), "input")

    with pytest.raises(ValueError, match="already registered"):
        registry.register("dummy", DummyAdapter(), "input")


def test_missing_adapter_error_lists_available_formats():
    registry = create_default_registry()

    with pytest.raises(MissingAdapterError, match="Available output formats:.*JSON"):
        registry.get("ROOT", "output")


def test_default_registry_contains_builtin_formats():
    registry = create_default_registry()

    assert "JSON" in registry.available_formats("input")
    assert "File" in registry.available_formats("output")
    assert "SLHA" in registry.available_formats("input")
    assert "xSLHA" in registry.available_formats("output")
