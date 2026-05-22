import json
import math

import pytest

from jarvis_portal import __version__
from jarvis_portal.cli import DIM, RESET, evaluate_runtime_expression, main, render_manual


def test_cli_prints_observables(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text("observables:\n  alpha: 1\n  beta: two\n", encoding="utf-8")

    assert main([str(path)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {"alpha": 1, "beta": "two"}


def test_cli_adapter_spec_prints_flat_observables(tmp_path, capsys):
    spec = tmp_path / "adapter-spec.yaml"
    input_json = tmp_path / "input.json"
    output_json = tmp_path / "output.json"
    input_json.write_text("{}", encoding="utf-8")
    output_json.write_text('{"z": 42, "fit": {"loglike": -1.25}}', encoding="utf-8")
    spec.write_text(
        """
observables:
  x: 1.0
  y: 2.0

input:
  - name: params
    path: input.json
    type: JSON
    actions:
      - type: Dump
        variables:
          - { name: "xx", expression: "x * Pi" }
          - { name: "cx", expression: "(x + y) * Pi", entry: "test.config.x" }
output:
  - name: observables
    path: output.json
    type: JSON
    variables:
      - { name: "z" }
      - { name: "likelihood", entry: "fit.loglike" }
""",
        encoding="utf-8",
    )

    assert main([str(spec)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload == {
        "xx": math.pi,
        "cx": 3.0 * math.pi,
        "z": 42,
        "likelihood": -1.25,
    }

    written = json.loads(input_json.read_text(encoding="utf-8"))
    assert written["xx"] == math.pi
    assert written["test"]["config"]["x"] == 3.0 * math.pi


def test_cli_accepts_full_jarvis_hep_io_shape(tmp_path, capsys):
    spec = tmp_path / "jarvis-hep.yaml"
    input_json = tmp_path / "input.json"
    input_json.write_text("{}", encoding="utf-8")
    spec.write_text(
        """
Calculators:
  Modules:
    - name: Demo
      execution:
        input:
          - name: params
            path: input.json
            type: JSON
            actions:
              - type: Dump
                variables:
                  - { name: "x" }
        output: []
""",
        encoding="utf-8",
    )

    assert main([str(spec)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {}


def test_cli_help(capsys):
    assert main(["--help"]) == 0

    captured = capsys.readouterr()
    assert "jportal file" in captured.out
    assert "jportal man" in captured.out
    assert "positional arguments:" in captured.out
    assert "  file  run a YAML file and print observables" in captured.out
    assert "  man   show the manual" in captured.out
    assert "json" not in captured.out


def test_cli_version(capsys):
    assert main(["--version"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == f"Jarvis-Portal {__version__}"


def test_cli_man_lists_formats(capsys):
    assert main(["man"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Supported formats:" in captured.out
    assert "input:" in captured.out
    assert "output:" in captured.out
    assert "json" in captured.out
    assert "csv" in captured.out
    assert "tsv" in captured.out
    assert "dat" in captured.out


def test_cli_man_json_prints_manual(capsys):
    assert main(["man", "json"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "JSON format manual" in captured.out
    assert "Observables contract:" in captured.out
    assert "┌─ YAML" in captured.out
    assert "│ input:" in captured.out
    assert "└" in captured.out
    assert "Note:\n  · means one indentation space" in captured.out
    assert "· means one indentation space" in captured.out
    assert '│ ··········- { name: "xx", expression: "x * Pi" }' in captured.out
    assert "cdot" not in captured.out
    assert "write_input" not in captured.out
    assert "read_output" not in captured.out
    assert "resolved absolute paths" in captured.out


def test_cli_man_json_can_dim_cdot_markers():
    rendered = render_manual("json", dim_markers=True)

    assert f'{DIM}··········{RESET}- {{ name: "xx", expression: "x * Pi" }}' in rendered
    assert "cdot" not in rendered


@pytest.mark.parametrize("topic", ["csv", "tsv", "dat"])
def test_cli_man_table_formats_print_manual(topic, capsys):
    assert main(["man", topic]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"{topic.upper()} format manual" in captured.out
    assert "column" in captured.out
    assert "Missing output columns or rows are omitted" in captured.out


def test_runtime_expression_evaluator_supports_pi():
    assert evaluate_runtime_expression("(x + y) * Pi", {"x": 1.0, "y": 2.0}) == 3.0 * math.pi


def test_cli_rejects_non_mapping_yaml(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")

    assert main([str(path)]) == 1

    captured = capsys.readouterr()
    assert "top-level document must be a mapping" in captured.err


def test_cli_rejects_unknown_options(capsys):
    assert main(["test.yaml", "--json"]) == 2

    captured = capsys.readouterr()
    assert "unexpected argument: --json" in captured.err


def test_cli_rejects_old_write_read_yaml_shape(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text(
        """
write_input:
  name: params
  path: input.json
  type: JSON
read_output:
  name: observables
  path: output.json
  type: JSON
""",
        encoding="utf-8",
    )

    assert main([str(path)]) == 1

    captured = capsys.readouterr()
    assert "YAML must contain observables, input, or output." in captured.err


def test_cli_rejects_unknown_manual_topic(capsys):
    assert main(["man", "root"]) == 1

    captured = capsys.readouterr()
    assert "Unknown manual topic: root" in captured.err
