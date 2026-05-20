import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FORMAT_ROOT = ROOT / "examples" / "formats"
FORMAT_DIRS = ("json", "file", "slha", "xslha")


def test_format_example_directories_have_required_files():
    for name in FORMAT_DIRS:
        directory = FORMAT_ROOT / name
        assert directory.is_dir(), name
        assert (directory / "README.md").is_file(), name
        assert (directory / "jarvis-hep.yaml").is_file(), name
        assert (directory / "adapter-spec.yaml").is_file(), name


def test_format_yaml_examples_are_mappings():
    for name in FORMAT_DIRS:
        directory = FORMAT_ROOT / name
        for filename in ("jarvis-hep.yaml", "adapter-spec.yaml"):
            payload = yaml.safe_load((directory / filename).read_text(encoding="utf-8"))
            assert isinstance(payload, dict), f"{name}/{filename}"


def test_json_sample_files_are_valid_json():
    directory = FORMAT_ROOT / "json"
    for filename in ("input.json", "output.json"):
        payload = json.loads((directory / filename).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), filename


def test_jarvis_hep_examples_use_current_calculator_io_shape():
    for name in FORMAT_DIRS:
        payload = yaml.safe_load((FORMAT_ROOT / name / "jarvis-hep.yaml").read_text(encoding="utf-8"))
        modules = payload["Calculators"]["Modules"]
        assert isinstance(modules, list) and modules, name
        execution = modules[0]["execution"]
        assert "input" in execution, name
        assert "output" in execution, name
        for spec in [*execution["input"], *execution["output"]]:
            assert "name" in spec, name
            assert "path" in spec, name
            assert "type" in spec, name
