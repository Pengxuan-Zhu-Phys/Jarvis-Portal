from io import StringIO
from pathlib import Path

import pytest

from jarvis_portal import wolframdict

ROOT = Path(__file__).resolve().parents[1]


def test_loads_parses_association_values_and_scientific_notation():
    payload = wolframdict.loads(
        """
        <|
          "name" -> "demo",
          "count" -> 3,
          "small" -> 2.5*^-6,
          "enabled" -> True,
          "missing" -> Null,
          "items" -> {1, 2.0, "three"},
          "nested" -> <|"x" -> -1.25|>
        |>
        """
    )

    assert payload == {
        "name": "demo",
        "count": 3,
        "small": 2.5e-6,
        "enabled": True,
        "missing": None,
        "items": [1, 2.0, "three"],
        "nested": {"x": -1.25},
    }


def test_loads_empty_input_returns_empty_dict():
    assert wolframdict.loads("") == {}
    assert wolframdict.loads("   \n\t") == {}


def test_loads_ignores_nested_wolfram_comments():
    payload = wolframdict.loads(
        """
        (* outer comment (* nested comment *) still comment *)
        <|
          "x" -> 1,
          (* association item comment *)
          "items" -> {1, (* list comment *) 2}
        |>
        """
    )

    assert payload == {"x": 1, "items": [1, 2]}


def test_loads_accepts_trailing_commas_and_unknown_identifiers():
    payload = wolframdict.loads(
        """
        <|
          "limit" -> Infinity,
          "items" -> {1, 2,},
        |>
        """
    )

    assert payload == {"limit": "Infinity", "items": [1, 2]}


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('<|"x" -> "unterminated|>', "Unterminated string"),
        ("<|@|>", "Unexpected character"),
        ("(* unterminated comment", "Unterminated comment"),
    ],
)
def test_loads_reports_parse_errors(source, message):
    with pytest.raises(ValueError, match=message):
        wolframdict.loads(source)


def test_dumps_roundtrips_nested_payload():
    payload = {
        "SMParameters": {"HiggsMass": 125.25, "alpha_s": 0.118},
        "Channels": [
            {"Name": "bb", "BR": 0.57538677},
            {"Name": "WW", "BR": 0.22041264},
        ],
        "SmallValue": 2.5e-6,
        "Converged": False,
        "NullValue": None,
    }

    assert wolframdict.loads(wolframdict.dumps(payload, indent=2)) == payload
    assert "*^-6" in wolframdict.dumps(payload, indent=2)


@pytest.mark.parametrize(
    "value",
    [
        3.141592653589793,
        0.3333333333333333,
        0.30000000000000004,
        1.0000000000000002,
        2.5e-6,
        1.2345678901234568e9,
    ],
)
def test_dumps_preserves_float_roundtrip_precision(value):
    payload = {"value": value}

    assert wolframdict.loads(wolframdict.dumps(payload, indent=2)) == payload


def test_load_and_dump_file_objects():
    stream = StringIO()
    wolframdict.dump({"x": 1, "values": [1, 2, 3]}, stream, indent=2)
    stream.seek(0)

    assert wolframdict.load(stream) == {"x": 1, "values": [1, 2, 3]}


def test_loads_rejects_non_association_top_level():
    with pytest.raises(TypeError, match="Association"):
        wolframdict.loads("{1, 2, 3}")


def test_project_example_output_roundtrips():
    reference = ROOT / "examples" / "formats" / "wolfram" / "output.wl"

    payload = wolframdict.loads(reference.read_text(encoding="utf-8"))
    assert payload["Channels"][0]["BR"] == 0.57538677
    assert payload["SmallValue"] == 2.5e-6
    assert payload["Converged"] is True
    assert wolframdict.loads(wolframdict.dumps(payload, indent=2)) == payload
