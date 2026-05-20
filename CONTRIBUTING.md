# Contributing

Jarvis-Portal is the format adapter and registry package for Jarvis IO. Keep changes focused on adapter registration, format-specific reads/writes, and package integration points.

Jarvis-HEP remains responsible for YAML IO block parsing, runtime path markers, expression evaluation, sample context construction, artifact policy, logging integration, and deciding which variables are read or written.

## Workflow

1. Create a branch for the change.
2. Install development dependencies:

   ```bash
   python -m pip install -e ".[dev]"
   ```

3. Make the smallest practical change.
4. Add or update tests for behavior changes.
5. Run the checks that apply:

   ```bash
   ruff check .
   python -m pytest
   python -m build
   ```

## Coding Style

- Follow the existing small-module style.
- Keep adapters independent from Jarvis-HEP runtime classes.
- Use `IOContext` for paths, logging hooks, and blocking work.
- Keep optional format dependencies optional and imported lazily.
- Prefer clear exceptions with installation hints for missing optional dependencies.
- Avoid broad framework additions unless a concrete adapter or integration needs them.

## Testing Expectations

- Use `pytest`.
- Use `tmp_path` for file IO tests.
- Test async adapter methods with `asyncio.run` unless the suite adopts an async pytest plugin.
- Skip tests requiring optional HEP dependencies unless those dependencies are installed.
- Add adapter tests for registration, supported directions, successful reads/writes, and missing dependency behavior.

## Pull Request Checklist

- The change fits Jarvis-Portal ownership.
- README or docs are updated when public behavior changes.
- Tests cover new or changed adapter behavior.
- Optional dependencies remain optional.
- `ruff check .` passes or the PR explains why it was left to CI.
- `python -m pytest` passes.
- `python -m build` passes for release-facing changes.
