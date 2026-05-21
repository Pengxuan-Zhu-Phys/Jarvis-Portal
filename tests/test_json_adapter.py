import asyncio
import json

from jarvis_portal import IOContext, create_default_registry


def test_json_adapter_writes_nested_entries_and_reads_variables(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps({"existing": 1}), encoding="utf-8")

    adapter = create_default_registry().get("json", "input")
    result = asyncio.run(
        adapter.write_input(
            IOContext(),
            {
                "path": str(path),
                "actions": [
                    {
                        "type": "Dump",
                        "variables": [
                            {"name": "alpha"},
                            {"name": "cx", "entry": "test.config.x"},
                        ],
                    },
                ],
            },
            {"alpha": 7, "cx": 3.14},
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["alpha"] == 7
    assert payload["test"]["config"]["x"] == 3.14
    assert result == {}

    output_adapter = create_default_registry().get("JSON", "output")
    result = asyncio.run(
        output_adapter.read_output(
            IOContext(),
            {
                "path": str(path),
                "variables": [
                    {"name": "alpha"},
                    {"name": "cx", "entry": "test.config.x"},
                    {"name": "missing", "entry": "test.config.nope"},
                ],
            },
        )
    )

    assert result == {"alpha": 7, "cx": 3.14, "missing": None}


def test_json_adapter_accepts_jarvis_hep_dump_actions(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps({"existing": 1}), encoding="utf-8")
    save_dir = tmp_path / "samples"

    def evaluate_expression(expression, values):
        if expression == "x * 2":
            return values["x"] * 2
        return None

    adapter = create_default_registry().get("JSON", "input")
    result = asyncio.run(
        adapter.write_input(
            IOContext(
                sample_save_dir=str(save_dir),
                module="DemoCalc",
                evaluate_expression=evaluate_expression,
            ),
            {
                "name": "params",
                "path": str(path),
                "type": "JSON",
                "save": True,
                "actions": [
                    {
                        "type": "Dump",
                        "variables": [
                            {"name": "x"},
                            {"name": "missing"},
                            {"name": "mass", "entry": "model.mass", "expression": "x * 2"},
                        ],
                    },
                    {
                        "type": "Ignored",
                        "variables": [{"name": "ignored"}],
                    },
                ],
            },
            {"x": 1.5},
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["x"] == 1.5
    assert payload["missing"] == "MISSING_VALUE"
    assert payload["model"]["mass"] == 3.0

    saved_path = save_dir / "input.json@DemoCalc"
    assert json.loads(saved_path.read_text(encoding="utf-8")) == payload
    assert result == {"mass": 3.0, "params": str(path.resolve())}


def test_json_adapter_reads_jarvis_hep_output_variables_and_temp_copy(tmp_path):
    path = tmp_path / "output.json"
    path.write_text(json.dumps({"fit": {"loglike": -12.5}, "z": 4}), encoding="utf-8")
    save_dir = tmp_path / "samples"

    adapter = create_default_registry().get("JSON", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(sample_save_dir=str(save_dir), module="DemoCalc"),
            {
                "name": "observables",
                "path": str(path),
                "type": "JSON",
                "save": False,
                "variables": [
                    {"name": "z"},
                    {"name": "likelihood", "entry": "fit.loglike"},
                ],
            },
        )
    )

    copied_path = save_dir / ".temp" / "output.json@DemoCalc"
    assert copied_path.is_file()
    assert result == {"z": 4, "likelihood": -12.5}


def test_json_adapter_returns_saved_file_observable_only_when_save_true(tmp_path):
    path = tmp_path / "output.json"
    path.write_text(json.dumps({"z": 4}), encoding="utf-8")
    save_dir = tmp_path / "samples"

    adapter = create_default_registry().get("JSON", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(sample_save_dir=str(save_dir), module="DemoCalc"),
            {
                "name": "observables",
                "path": str(path),
                "type": "JSON",
                "save": True,
                "variables": [{"name": "z"}],
            },
        )
    )

    saved_path = save_dir / "output.json@DemoCalc"
    assert saved_path.is_file()
    assert result == {"z": 4, "observables": str(path.resolve())}
