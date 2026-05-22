import asyncio
import math
import shutil
from pathlib import Path

import pytest

from jarvis_portal import IOContext, create_default_registry
from jarvis_portal.cli import load_yaml_dict, payload_to_observables


def _evaluate_expression(expression, values):
    if expression == "x * Pi":
        return values["x"] * math.pi
    if expression == "y * Pi":
        return values["y"] * math.pi
    if expression == "(x+y)*Pi":
        return (values["x"] + values["y"]) * math.pi
    if expression == "(x + y) * Pi":
        return (values["x"] + values["y"]) * math.pi
    raise ValueError(expression)


@pytest.mark.parametrize(
    ("format_name", "filename", "separator"),
    [
        ("CSV", "input.csv", ","),
        ("TSV", "input.tsv", "\t"),
    ],
)
def test_delimited_adapter_writes_named_columns_and_reads_outputs(
    tmp_path,
    format_name,
    filename,
    separator,
):
    path = tmp_path / filename
    path.write_text(separator.join(["mass", "coupling", "config"]) + "\n0,0,0\n", encoding="utf-8")
    if separator == "\t":
        path.write_text("mass\tcoupling\tconfig\n0\t0\t0\n", encoding="utf-8")

    adapter = create_default_registry().get(format_name, "input")
    result = asyncio.run(
        adapter.write_input(
            IOContext(evaluate_expression=_evaluate_expression),
            {
                "name": "params",
                "path": str(path),
                "type": format_name,
                "header": True,
                "actions": [
                    {
                        "type": "Dump",
                        "variables": [
                            {"name": "var_mass", "expression": "x * Pi", "column": "mass"},
                            {"name": "plain", "column": "coupling"},
                        ],
                    }
                ],
            },
            {"x": 2.0, "plain": 7},
        )
    )

    assert result == {"var_mass": 2.0 * math.pi}
    assert str(2.0 * math.pi) in path.read_text(encoding="utf-8")

    output_path = tmp_path / f"output.{filename.split('.')[-1]}"
    output_path.write_text(
        separator.join(["chi2", "mass", "fit_loglike"])
        + "\n"
        + separator.join(["3.42", "125.1", "-1.25"])
        + "\n"
        + separator.join(["1.08", "125.3", "-0.87"])
        + "\n",
        encoding="utf-8",
    )
    result = asyncio.run(
        create_default_registry()
        .get(format_name, "output")
        .read_output(
            IOContext(),
            {
                "path": str(output_path),
                "type": format_name,
                "header": True,
                "variables": [
                    {"name": "chi2", "row": 0},
                    {"name": "best_mass", "column": "mass", "row": 0},
                    {"name": "loglike", "column": "fit_loglike"},
                    {"name": "missing", "column": "not_there"},
                ],
            },
        )
    )

    assert result == {"chi2": 3.42, "best_mass": 125.1, "loglike": [-1.25, -0.87]}


def test_dat_adapter_handles_comments_whitespace_and_headerless_columns(tmp_path):
    path = tmp_path / "input.dat"
    path.write_text("# mass coupling config\n0.0    0.0\t0.0\n", encoding="utf-8")

    adapter = create_default_registry().get("DAT", "input")
    result = asyncio.run(
        adapter.write_input(
            IOContext(evaluate_expression=_evaluate_expression),
            {
                "name": "params",
                "path": str(path),
                "type": "DAT",
                "header": False,
                "columns": ["mass", "coupling", "config"],
                "comment": "#",
                "actions": [
                    {
                        "type": "Dump",
                        "variables": [
                            {"name": "var_mass", "expression": "x * Pi", "column": "mass"},
                            {"name": "var_config", "expression": "(x+y)*Pi", "column": "config"},
                        ],
                    }
                ],
            },
            {"x": 1.5, "y": 10.0},
        )
    )

    assert result == {
        "var_mass": 1.5 * math.pi,
        "var_config": 11.5 * math.pi,
    }
    assert path.read_text(encoding="utf-8").split() == [
        str(1.5 * math.pi),
        "0.0",
        str(11.5 * math.pi),
    ]

    output_path = tmp_path / "output.dat"
    output_path.write_text(
        "# chi2  mass  fit_loglike\n3.42   125.1   -1.25\n1.08\t125.3\t-0.87\n",
        encoding="utf-8",
    )

    result = asyncio.run(
        adapter.read_output(
            IOContext(),
            {
                "path": str(output_path),
                "type": "DAT",
                "header": False,
                "columns": ["chi2", "mass", "fit_loglike"],
                "comment": "#",
                "variables": [
                    {"name": "chi2", "row": 0},
                    {"name": "best_mass", "column": "mass", "row": 0},
                    {"name": "loglike", "column": "fit_loglike"},
                    {"name": "missing", "column": "not_there"},
                ],
            },
        )
    )

    assert result == {"chi2": 3.42, "best_mass": 125.1, "loglike": [-1.25, -0.87]}


@pytest.mark.parametrize("name", ["csv", "tsv", "dat"])
def test_table_format_examples_run_through_cli_payload(tmp_path, name):
    source = Path(__file__).resolve().parents[1] / "examples" / "formats" / name
    target = tmp_path / name
    shutil.copytree(source, target)

    payload = load_yaml_dict(target / "adapter-spec.yaml")
    result = payload_to_observables(payload, project_root=target)

    assert result["chi2"] == 3.42
    assert result["best_mass"] == 125.1
    assert result["loglike"] == [-1.25, -0.87]
