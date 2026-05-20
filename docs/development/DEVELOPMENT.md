# Development

Jarvis-Portal is a small Python package with source code under `src/jarvis_portal` and tests under `tests`.

## Python Versions

`pyproject.toml` requires Python `>=3.10`.

The CI matrix currently runs:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

Use one of those versions for local development.

## Local Setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the package in editable mode with development tools:

```bash
python -m pip install -e ".[dev]"
```

This installs the package plus the current development tools declared in `pyproject.toml`: `pytest`, `ruff`, `build`, and `twine`.

## Optional Extras

Jarvis-Portal keeps HEP format dependencies optional so the JSON, File, and registry layers can be used without heavier format packages.

Available extras:

```bash
python -m pip install -e ".[slha]"
python -m pip install -e ".[xslha]"
python -m pip install -e ".[all]"
```

For full local development:

```bash
python -m pip install -e ".[dev,all]"
```

## Working Without Optional HEP Dependencies

Optional adapters import their dependencies only when used:

- `SLHAAdapter` requires `pyslha` and raises an installation hint if it is missing.
- `XSLHAAdapter` requires `xslha` and raises an installation hint if it is missing.

You can still run the core registry, JSON adapter, and File adapter tests with only:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Do not make optional HEP packages required for importing `jarvis_portal` or constructing the default registry.

## Running Tests

Run all tests:

```bash
python -m pytest
```

Run one test file:

```bash
python -m pytest tests/test_json_adapter.py
```

Run one test:

```bash
python -m pytest tests/test_registry.py::test_default_registry_contains_builtin_formats
```

## Linting

Run Ruff if installed:

```bash
ruff check .
```

CI installs the `dev` extra and runs Ruff. If Ruff is not installed locally, install `.[dev]` or leave linting to CI.

## Building

Build source and wheel distributions:

```bash
python -m build
```

The build output is written to `dist/`.

Check built distributions before release:

```bash
twine check dist/*
```

## Common Commands

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[dev,all]"
jportal --version
jportal input.yaml
python -m pytest
ruff check .
python -m build
twine check dist/*
```

## CLI

The package installs a small command line tool:

```bash
jportal input.yaml
```

By default it parses the YAML file and prints the resulting Python dictionary to stdout. Use `--json` for JSON output, `-o/--output` to write to a file, `--formats` to list built-in adapter formats, and `-v/--version` to print the installed version.

The CLI is intentionally an inspection and utility entry point. It does not parse Jarvis-HEP YAML IO semantics, expand runtime markers, evaluate expressions, or run adapters.

## Jarvis-HEP Integration Boundary

Jarvis-Portal is intended to be called by Jarvis-HEP and other Jarvis runtime components, but it should not grow Jarvis-HEP runtime responsibilities.

Jarvis-HEP owns YAML IO block parsing, runtime path markers, expression evaluation, sample context construction, save/copy/archive policy, logging integration, IO manager integration, and deciding which variables are read or written.

Jarvis-Portal owns format-specific behavior, adapter registration and lookup, JSON nested entry behavior, SLHA/xSLHA structured record handling, and future format-specific HEP IO logic.
