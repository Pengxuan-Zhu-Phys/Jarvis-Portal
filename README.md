# Jarvis-Portal

Jarvis-Portal is the standalone IO adapter and registry package for the Jarvis ecosystem.

It provides format-specific read/write behavior for scientific file formats used by Jarvis-HEP and related tools. The currently exposed format is JSON; SLHA, xSLHA, and future HEP calculator formats can be developed behind the registry until they are tested.

Jarvis-Portal is intended to serve YAML-driven Jarvis workflows through Jarvis-HEP. It does not own Jarvis-HEP YAML parsing or runtime workflow semantics.

## Scope

Jarvis-Portal owns:

- format adapter registration and lookup
- JSON nested entry reads/writes
- future adapters for ROOT, HepMC, LHE, YODA, SPheno, MadGraph cards, and related HEP formats

Jarvis-HEP owns:

- YAML IO block parsing
- runtime path markers such as `&J`, `@PackID`, `@SampleID`, and `@Sdir`
- expression evaluation
- sample/runtime context
- save/copy/archive policy
- logger and IO manager integration
- deciding which variables are written or read
- plain file copy/save helpers that do not require format parsing

## Quick Install

```bash
pip install Jarvis-HEP-Portal
```

Optional format extras:

```bash
pip install "Jarvis-HEP-Portal[slha]"
pip install "Jarvis-HEP-Portal[xslha]"
pip install "Jarvis-HEP-Portal[all]"
```

## Development

```bash
python -m pip install -e ".[dev,all]"
python -m pytest
ruff check .
python -m build
```

## Basic Usage

CLI:

```bash
jportal file
jportal man
jportal man json
jportal -h
jportal -v
```

`jportal file` is the only supported business CLI shape. It prints the observable dictionary itself as JSON. Utility exceptions are `jportal man`, `jportal man <format>`, `-h/--help`, and `-v/--version`.

Python:

```python
from jarvis_portal import IOContext, create_default_registry

registry = create_default_registry()
adapter = registry.get("JSON", "input")

def evaluate_expression(expression, values):
    if expression == "x * 2":
        return values["x"] * 2
    raise ValueError(expression)

context = IOContext(evaluate_expression=evaluate_expression)
observables = await adapter.write_input(
    context,
    {
        "name": "params",
        "path": "input.json",
        "type": "JSON",
        "actions": [
            {
                "type": "Dump",
                "variables": [
                    {"name": "nested", "entry": "config.value", "expression": "x * 2"},
                ],
            },
        ],
    },
    {"x": 1.0},
)
```

JSON adapter calls return the observable dictionary itself. For JSON input, plain dumped variables are written to the file; expression variables and saved file specs may contribute observables, matching Jarvis-HEP.

## Documentation

- [Docs index](docs/README.md)
- [Development](docs/development/DEVELOPMENT.md)
- [CLI](docs/development/CLI.md)
- [Architecture](docs/design/ARCHITECTURE.md)
- [Adapter authoring](docs/development/ADAPTER_AUTHORING.md)
- [Format catalog](docs/development/FORMAT_CATALOG.md)
- [JSON format usage](docs/development/JSON_FORMAT.md)
- [Testing](docs/development/TESTING.md)
- [Release](docs/release/RELEASE.md)
- [Contributing](CONTRIBUTING.md)

## Status

This package is in alpha development. Runtime behavior should stay small and adapter-focused so Jarvis-HEP can remain the owner of workflow semantics.
