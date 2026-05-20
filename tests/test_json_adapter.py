import asyncio
import json

from jarvis_portal import IOContext, create_default_registry


def test_json_adapter_writes_nested_entries_and_reads_variables(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps({"existing": 1}), encoding="utf-8")

    adapter = create_default_registry().get("json", "input")
    asyncio.run(
        adapter.write_input(
            IOContext(),
            {
                "path": str(path),
                "operations": [
                    {"name": "alpha", "value": 7},
                    {"name": "cx", "entry": "test.config.x", "value": 3.14},
                ],
            },
            {},
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["alpha"] == 7
    assert payload["test"]["config"]["x"] == 3.14

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
