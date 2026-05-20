# Jarvis-Portal

Jarvis-Portal is the IO adapter and registry layer for the Jarvis ecosystem.
It is designed to host format-specific read/write behavior for calculator IO
formats while leaving Jarvis-HEP in control of YAML semantics, path resolution,
expression evaluation, sample context, logging, and artifact policy.

## Scope

Jarvis-Portal owns:

- format adapter registration and lookup
- JSON nested entry reads/writes
- plain file adapter helpers
- optional SLHA/xSLHA record handling
- future adapters for ROOT, HepMC, LHE, YODA, SPheno, MadGraph cards, and related HEP formats

Jarvis-HEP should continue to own:

- YAML IO block parsing
- runtime path markers such as `&J`, `@PackID`, `@SampleID`, and `@Sdir`
- expression evaluation
- sample/runtime context
- save/copy/archive policy
- logger and IO manager integration
- deciding which variables are written or read

## Install

```bash
pip install Jarvis-Portal
```

Optional format extras:

```bash
pip install "Jarvis-Portal[slha]"
pip install "Jarvis-Portal[xslha]"
pip install "Jarvis-Portal[all]"
```

For development:

```bash
python -m pip install -e ".[dev,all]"
python -m pytest
ruff check .
```

## Basic Usage

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

## GitHub Setup

This repository includes GitHub Actions workflows for CI and PyPI publishing.
After creating the GitHub repository, set the remote:

```bash
git remote add origin git@github.com:Pengxuan-Zhu-Phys/Jarvis-Portal.git
git push -u origin main
```

## PyPI Setup

The publish workflow uses PyPI Trusted Publishing and runs on GitHub releases.
Manual setup needed:

1. Create the `Jarvis-Portal` project on PyPI, or publish the first release manually if PyPI requires it.
2. Add a trusted publisher for this GitHub repository.
3. Configure the workflow name as `publish.yml` and environment as `pypi` if you require protected publishing.
4. Create a GitHub release tag such as `v0.1.0` to publish.

No PyPI API token is committed or required when Trusted Publishing is configured.
