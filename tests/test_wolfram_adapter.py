import asyncio

import pytest

from jarvis_portal import IOContext, create_default_registry, wolframdict


class CapturingLogger:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


def test_wolfram_adapter_writes_nested_entries_and_reads_variables(tmp_path):
    path = tmp_path / "input.wl"
    path.write_text('<|"existing" -> 1|>', encoding="utf-8")

    adapter = create_default_registry().get("wolfram", "input")
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
                            {"name": "mass", "entry": "SMParameters.HiggsMass"},
                        ],
                    },
                ],
            },
            {"alpha": 7, "mass": 125.25},
        )
    )

    payload = wolframdict.loads(path.read_text(encoding="utf-8"))
    assert payload["alpha"] == 7
    assert payload["SMParameters"]["HiggsMass"] == 125.25
    assert result == {}

    output_adapter = create_default_registry().get("Wolfram", "output")
    result = asyncio.run(
        output_adapter.read_output(
            IOContext(),
            {
                "path": str(path),
                "variables": [
                    {"name": "alpha"},
                    {"name": "mass", "entry": "SMParameters.HiggsMass"},
                    {"name": "missing", "entry": "SMParameters.nope"},
                ],
            },
        )
    )

    assert result == {"alpha": 7, "mass": 125.25, "missing": None}


def test_wolfram_adapter_accepts_jarvis_hep_dump_actions(tmp_path):
    path = tmp_path / "input.wl"
    path.write_text('<|"existing" -> 1|>', encoding="utf-8")
    save_dir = tmp_path / "samples"

    def evaluate_expression(expression, values):
        if expression == "x * 2":
            return values["x"] * 2
        return None

    adapter = create_default_registry().get("Wolfram", "input")
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
                "type": "Wolfram",
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

    payload = wolframdict.loads(path.read_text(encoding="utf-8"))
    assert payload["x"] == 1.5
    assert payload["missing"] == "MISSING_VALUE"
    assert payload["model"]["mass"] == 3.0

    saved_path = save_dir / "input.wl@DemoCalc"
    assert wolframdict.loads(saved_path.read_text(encoding="utf-8")) == payload
    assert result == {"mass": 3.0, "params": str(path.resolve())}


def test_wolfram_adapter_reads_output_variables_list_indexes_and_temp_copy(tmp_path):
    path = tmp_path / "output.wl"
    path.write_text(
        """
        <|
          "LinearEntropy" -> 0.6725,
          "BranchingFractionSum" -> 1.0,
          "Channels" -> {
            <|"Name" -> "bb", "BR" -> 0.57538677|>,
            <|"Name" -> "WW", "BR" -> 0.22041264|>
          }
        |>
        """,
        encoding="utf-8",
    )
    save_dir = tmp_path / "samples"

    adapter = create_default_registry().get("Wolfram", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(sample_save_dir=str(save_dir), module="DemoCalc"),
            {
                "name": "observables",
                "path": str(path),
                "type": "Wolfram",
                "save": False,
                "variables": [
                    {"name": "LinearEntropy"},
                    {"name": "BRSum", "entry": "BranchingFractionSum"},
                    {"name": "BR_bb", "entry": "Channels.0.BR"},
                    {"name": "negative", "entry": "Channels.-1.BR"},
                    {"name": "missing", "entry": "Channels.2.BR"},
                    {"name": "non_index", "entry": "Channels.bb.BR"},
                ],
            },
        )
    )

    copied_path = save_dir / ".temp" / "output.wl@DemoCalc"
    assert copied_path.is_file()
    assert result == {
        "LinearEntropy": 0.6725,
        "BRSum": 1.0,
        "BR_bb": 0.57538677,
        "negative": None,
        "missing": None,
        "non_index": None,
    }


def test_wolfram_adapter_rejects_negative_list_index_on_write(tmp_path):
    path = tmp_path / "input.wl"
    path.write_text('<|"Channels" -> {<|"BR" -> 1.0|>}|>', encoding="utf-8")

    adapter = create_default_registry().get("Wolfram", "input")
    with pytest.raises(ValueError, match="negative list index"):
        asyncio.run(
            adapter.write_input(
                IOContext(),
                {
                    "path": str(path),
                    "actions": [
                        {
                            "type": "Dump",
                            "variables": [{"name": "BR", "entry": "Channels.-1.BR"}],
                        },
                    ],
                },
                {"BR": 0.5},
            )
        )


def test_wolfram_adapter_missing_file_returns_none_and_logs_error(tmp_path):
    path = tmp_path / "missing.wl"
    logger = CapturingLogger()

    adapter = create_default_registry().get("Wolfram", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(logger=logger),
            {
                "path": str(path),
                "type": "Wolfram",
                "variables": [{"name": "z"}],
            },
        )
    )

    assert result == {"z": None}
    assert logger.errors == [f"File not found: {path}"]


def test_wolfram_adapter_malformed_file_returns_none_and_logs_error(tmp_path):
    path = tmp_path / "bad.wl"
    path.write_text("<|@", encoding="utf-8")
    logger = CapturingLogger()

    adapter = create_default_registry().get("Wolfram", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(logger=logger),
            {
                "path": str(path),
                "type": "Wolfram",
                "variables": [{"name": "z"}],
            },
        )
    )

    assert result == {"z": None}
    assert logger.errors == [f"Error decoding Wolfram Association from file: {path}"]


def test_wolfram_adapter_returns_saved_file_observable_only_when_save_true(tmp_path):
    path = tmp_path / "output.wl"
    path.write_text('<|"z" -> 4|>', encoding="utf-8")
    save_dir = tmp_path / "samples"

    adapter = create_default_registry().get("Wolfram", "output")
    result = asyncio.run(
        adapter.read_output(
            IOContext(sample_save_dir=str(save_dir), module="DemoCalc"),
            {
                "name": "observables",
                "path": str(path),
                "type": "Wolfram",
                "save": True,
                "variables": [{"name": "z"}],
            },
        )
    )

    saved_path = save_dir / "output.wl@DemoCalc"
    assert saved_path.is_file()
    assert result == {"z": 4, "observables": str(path.resolve())}
