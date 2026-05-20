# Jarvis-Portal

Jarvis-Portal is the standalone IO adapter and registry package for the Jarvis ecosystem.

It provides format-specific read/write behavior for scientific file formats used by Jarvis-HEP and related tools, including JSON, plain files, SLHA, xSLHA, and future HEP calculator formats.

Jarvis-Portal is intended to serve YAML-driven Jarvis workflows through Jarvis-HEP. It does not own Jarvis-HEP YAML parsing or runtime workflow semantics.

## Scope

Jarvis-Portal owns:

- format adapter registration and lookup
- JSON nested entry reads/writes
- plain file adapter helpers
- optional SLHA/xSLHA record handling
- future adapters for ROOT, HepMC, LHE, YODA, SPheno, MadGraph cards, and related HEP formats

Jarvis-HEP owns:

- YAML IO block parsing
- runtime path markers such as `&J`, `@PackID`, `@SampleID`, and `@Sdir`
- expression evaluation
- sample/runtime context
- save/copy/archive policy
- logger and IO manager integration
- deciding which variables are written or read

## Quick Install

```bash
pip install Jarvis-Portal
```

Optional format extras:

```bash
pip install "Jarvis-Portal[slha]"
pip install "Jarvis-Portal[xslha]"
pip install "Jarvis-Portal[all]"
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
jportal input.yaml
jportal input.yaml --json
jportal --formats
jportal --version
```

By default, `jportal input.yaml` parses the YAML file and prints the resulting Python dictionary to the terminal. It does not execute Jarvis-HEP workflow semantics.

Python:

```python
from jarvis_portal import IOContext, create_default_registry

registry = create_default_registry()
adapter = registry.get("JSON", "input")

context = IOContext()
await adapter.write_input(
    context,
    {
        "path": "input.json",
        "operations": [
            {"name": "x", "value": 1.0},
            {"name": "nested", "entry": "config.value", "value": 2.0},
        ],
    },
    {},
)
```

## Documentation

- [Docs index](docs/README.md)
- [Development](docs/development/DEVELOPMENT.md)
- [CLI](docs/development/CLI.md)
- [Architecture](docs/design/ARCHITECTURE.md)
- [Adapter authoring](docs/development/ADAPTER_AUTHORING.md)
- [Format catalog](docs/development/FORMAT_CATALOG.md)
- [Testing](docs/development/TESTING.md)
- [Release](docs/release/RELEASE.md)
- [Contributing](CONTRIBUTING.md)

## Status

This package is in alpha development. Runtime behavior should stay small and adapter-focused so Jarvis-HEP can remain the owner of workflow semantics.
