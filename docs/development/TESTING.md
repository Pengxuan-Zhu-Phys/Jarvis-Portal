# Testing

Tests live under `tests/` and use `pytest`.

Current test files cover:

- registry registration, lookup, duplicate handling, and missing adapter errors
- JSON nested write/read behavior
- plain File adapter write/read behavior
- CLI YAML parsing, output rendering, version output, and error handling

## Running Tests

Run all tests:

```bash
python -m pytest
```

Run a single file:

```bash
python -m pytest tests/test_json_adapter.py
```

Run a single test:

```bash
python -m pytest tests/test_file_adapter.py::test_file_adapter_can_write_and_read_text
```

## Unit Test Structure

Prefer one focused test file per adapter:

```text
tests/test_registry.py
tests/test_json_adapter.py
tests/test_file_adapter.py
tests/test_cli.py
tests/test_slha_adapter.py
tests/test_xslha_adapter.py
```

Keep tests close to observable behavior:

- registry input and output lookup
- written file content
- returned output dictionaries
- missing dependency errors
- invalid spec errors where the adapter owns validation

## Required Tests For Every Adapter

Every adapter should have tests for:

- registration and lookup through `IORegistry` or `create_default_registry`
- a format example directory under `examples/formats/<format>/`
- valid `jarvis-hep.yaml` and `adapter-spec.yaml` example files
- at least one successful `write_input` case when the adapter supports input
- at least one successful `read_output` case when the adapter supports output
- path handling through `IOContext`
- clear behavior for missing or unsupported fields that the adapter owns
- missing optional dependency behavior, if the adapter requires an optional package

For output-only adapters, test that `write_input` raises the documented error if the method is intentionally unsupported.

## Optional Dependency Strategy

Optional HEP dependencies must not be required for the base test suite.

Recommended pattern:

```python
pytest.importorskip("pyslha")
```

Use this when the test needs the real optional package.

Also include lightweight tests that monkeypatch the import path or call the adapter in an environment without the dependency when practical, so the installation hint remains covered.

Base CI currently installs `.[dev]`, not `.[dev,all]`, so tests requiring optional packages should be skipped unless CI is explicitly changed to install those extras.

## Temporary Files

Use the `tmp_path` fixture for adapter file IO:

```python
def test_adapter_writes_file(tmp_path):
    path = tmp_path / "input.dat"
```

Do not write test artifacts into the repository root. Keep generated files in `tmp_path` unless a test specifically needs packaged fixture data.

## Async Adapter Testing

Adapter methods are async. Current tests call them with `asyncio.run`:

```python
import asyncio

result = asyncio.run(adapter.read_output(context, spec))
```

Keep using `asyncio.run` for simple unit tests. Add an async pytest plugin only if the test suite grows enough to justify the dependency.

## CI Expectations

The GitHub Actions CI workflow runs on pushes to `main` and on pull requests.

It currently:

- tests Python 3.10, 3.11, 3.12, and 3.13
- installs `.[dev]`
- runs `ruff check .`
- runs `python -m pytest`
- runs `python -m build`

Changes should pass the same commands locally when possible:

```bash
ruff check .
python -m pytest
python -m build
```
