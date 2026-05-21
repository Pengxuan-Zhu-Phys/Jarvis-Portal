import pytest

from jarvis_portal import MissingAdapterError, create_default_registry, create_entry_point_registry
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
    assert "SLHA" not in registry.available_formats("input")
    assert "xSLHA" not in registry.available_formats("output")
    assert "File" not in registry.available_formats("input")
    assert "File" not in registry.available_formats("output")


def test_registry_lists_adapters_once():
    registry = create_default_registry()

    names = [adapter.format_name for adapter in registry.adapters()]

    assert names == ["JSON"]


def test_entry_point_registry_loads_adapter_classes(monkeypatch):
    class FakeEntryPoint:
        name = "dummy"

        def load(self):
            return DummyAdapter

    monkeypatch.setattr("jarvis_portal.registry._entry_points", lambda group: [FakeEntryPoint()])

    registry = create_entry_point_registry(include_builtins=False, allowed_formats=None)

    assert registry.get("dummy", "input").format_name == "Dummy"
    assert registry.available_formats("output") == ["Dummy"]


def test_entry_point_registry_warns_and_skips_broken_entry_points(monkeypatch):
    class BrokenEntryPoint:
        name = "broken"

        def load(self):
            raise ModuleNotFoundError("missing adapter")

    monkeypatch.setattr("jarvis_portal.registry._entry_points", lambda group: [BrokenEntryPoint()])

    with pytest.warns(RuntimeWarning, match="Skipping IO adapter entry point 'broken'"):
        registry = create_entry_point_registry(include_builtins=False, allowed_formats=None)

    assert registry.available_formats() == []


def test_entry_point_registry_can_raise_broken_entry_points(monkeypatch):
    class BrokenEntryPoint:
        name = "broken"

        def load(self):
            raise ModuleNotFoundError("missing adapter")

    monkeypatch.setattr("jarvis_portal.registry._entry_points", lambda group: [BrokenEntryPoint()])

    with pytest.raises(ModuleNotFoundError, match="missing adapter"):
        create_entry_point_registry(include_builtins=False, on_error="raise", allowed_formats=None)


def test_entry_point_registry_filters_unexposed_formats(monkeypatch):
    class JsonEntryPoint:
        name = "json"

        def load(self):
            return DummyAdapter

    class SlhaEntryPoint:
        name = "slha"

        def load(self):
            raise AssertionError("unexposed entry point should not be loaded")

    monkeypatch.setattr(
        "jarvis_portal.registry._entry_points",
        lambda group: [JsonEntryPoint(), SlhaEntryPoint()],
    )

    registry = create_entry_point_registry(include_builtins=False, allowed_formats={"dummy"})

    assert registry.available_formats() == []
