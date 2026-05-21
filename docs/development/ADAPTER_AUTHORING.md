# Adapter Authoring

Adapters are small objects that implement format-specific reads and writes. They should be easy to test in isolation and should not depend on Jarvis-HEP internals.

## Adapter Shape

An adapter should provide these attributes:

- `format_name`: the public format name, for example `JSON`, `SLHA`, or `ROOT`
- `direction`: one of `input`, `output`, or `both`

It should provide these async methods:

```python
async def write_input(
    self,
    context: IOContext,
    spec: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    ...

async def read_output(
    self,
    context: IOContext,
    spec: dict[str, Any],
) -> dict[str, Any]:
    ...
```

`write_input` should create or update files needed by an external program. `read_output` should return a dictionary of values read from files.

Each adapter should also have an independent example directory under `examples/formats/<format>/`. That directory documents the Jarvis-HEP-facing YAML shape and the compact `input` / `output` IO shape accepted by `jportal file`. See the [format catalog](FORMAT_CATALOG.md).

## What Adapters May Do

Adapters may:

- use `context.path(...)` to resolve file paths supplied in the spec
- use `context.run_blocking(...)` for synchronous parser and filesystem work
- parse and serialize their own file format
- create parent directories for files they write
- return format-derived values from `read_output`
- raise clear installation errors for missing optional dependencies
- accept format-specific fields in `spec`, such as `block`, `entry`, `encoding`, or `operations`

## What Adapters May Not Do

Adapters should not:

- parse Jarvis-HEP YAML IO blocks
- expand Jarvis-HEP path markers such as `&J`, `@PackID`, `@SampleID`, or `@Sdir`
- evaluate expressions such as `x * Pi`
- decide which variables a workflow should read or write
- construct Jarvis-HEP sample contexts
- decide save, copy, or archive policy
- call Jarvis-HEP loggers or IO managers directly instead of using `IOContext`
- make optional HEP dependencies required for importing `jarvis_portal`

## Registering Adapters

Register an adapter on a registry instance:

```python
from jarvis_portal import IORegistry

registry = IORegistry()
registry.register("Example", ExampleAdapter(), "both")
```

Use `override=True` only when intentionally replacing an existing adapter:

```python
registry.register("Example", NewExampleAdapter(), "both", override=True)
```

For the package default registry:

```python
from jarvis_portal import register

register("Example", ExampleAdapter(), "both")
```

Built-in adapters are registered by `jarvis_portal.builtins.register_builtins`.

## Entry Point Discovery

`pyproject.toml` declares the Python entry point group used by Jarvis-HEP and third-party packages:

```toml
[project.entry-points."jarvishep.io"]
json = "jarvis_portal.adapters.json:JsonAdapter"
```

Only tested formats should be listed here. Adapter code may exist in the repository before it is exposed, but Jarvis-HEP will discover anything listed under this group.

Jarvis-Portal exposes discovery helpers:

```python
from jarvis_portal import create_entry_point_registry, discover_entry_points

registry = create_entry_point_registry()
```

`create_entry_point_registry()` returns a fresh registry with built-ins plus installed adapter entry points from `jarvishep.io` whose entry point names are listed in `EXPOSED_FORMATS`. `discover_entry_points(registry)` loads entry points into an existing registry.

`EXPOSED_FORMATS` is the public allow-list Jarvis-HEP should see. It is currently `{"json"}`. Add a format there only after its adapter behavior is tested.

Discovery defaults to `on_error="warn"`: broken or stale entry points are skipped with a `RuntimeWarning` instead of preventing Jarvis-HEP from starting. Use `on_error="raise"` in strict tests.

Development tools can pass `allowed_formats=None` to load every installed entry point, including hidden or experimental ones. Jarvis-HEP should use the default.

Jarvis-HEP should use `create_entry_point_registry()` when it wants all IO formats provided by the installed `Jarvis-HEP-Portal` package without hard-coding format names. Keep Jarvis-HEP-owned formats such as `File` registered on the Jarvis-HEP side.

Third-party packages should use the same entry point group.

## Example Adapter

This adapter writes and reads a simple `key=value` text format:

```python
from __future__ import annotations

from typing import Any

from jarvis_portal import IOContext


class KeyValueAdapter:
    format_name = "KeyValue"
    direction = "both"

    async def write_input(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await context.run_blocking(self._write_sync, context, spec, data)

    async def read_output(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        return await context.run_blocking(self._read_sync, context, spec)

    def _write_sync(
        self,
        context: IOContext,
        spec: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        path = context.path(spec["path"])
        keys = spec.get("keys", data.keys())
        lines = [f"{key}={data[key]}" for key in keys if key in data]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding=spec.get("encoding", "utf-8"))
        return {}

    def _read_sync(self, context: IOContext, spec: dict[str, Any]) -> dict[str, Any]:
        path = context.path(spec["path"])
        raw = path.read_text(encoding=spec.get("encoding", "utf-8"))
        values = {}
        for line in raw.splitlines():
            if not line.strip() or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return {item["name"]: values.get(item["name"]) for item in spec.get("variables", [])}
```

Register it:

```python
registry.register("KeyValue", KeyValueAdapter(), "both")
```
