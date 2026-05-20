import json

import pytest

from jarvis_portal import __version__
from jarvis_portal.cli import main


def test_cli_prints_python_dict_by_default(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text("alpha: 1\nnested:\n  beta: two\n", encoding="utf-8")

    assert main([str(path)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.strip() == "{'alpha': 1, 'nested': {'beta': 'two'}}"


def test_cli_can_emit_json(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text("alpha: 1\nnested:\n  beta: two\n", encoding="utf-8")

    assert main([str(path), "--json"]) == 0

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"alpha": 1, "nested": {"beta": "two"}}


def test_cli_can_write_output_file(tmp_path, capsys):
    input_path = tmp_path / "input.yaml"
    output_path = tmp_path / "out" / "payload.json"
    input_path.write_text("alpha: 1\n", encoding="utf-8")

    assert main([str(input_path), "--json", "-o", str(output_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"alpha": 1}


def test_cli_version(capsys):
    assert main(["--version"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == f"Jarvis-Portal {__version__}"


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: jportal" in captured.out


def test_cli_rejects_non_mapping_yaml(tmp_path, capsys):
    path = tmp_path / "input.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")

    assert main([str(path)]) == 1

    captured = capsys.readouterr()
    assert "top-level document must be a mapping" in captured.err
