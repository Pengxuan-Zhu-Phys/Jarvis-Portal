# Architecture

Jarvis-Portal is the standalone IO adapter and registry package for the Jarvis ecosystem.

Its main purpose is to provide a small, stable layer that Jarvis-HEP can call when it needs format-specific file reads and writes. Jarvis-Portal is not a full workflow runtime.

## Package Goals

- Provide a lightweight IO adapter registry.
- Define a small adapter interface for input writing and output reading.
- Provide runtime context objects that let callers pass path resolution, logging, and blocking-work execution behavior into adapters.
- Ship built-in adapters only after their behavior is tested.
- Keep untested optional adapters hidden from the registry until they are ready for Jarvis-HEP.
- Leave room for future adapters for ROOT, HepMC, LHE, YODA, SPheno, MadGraph cards, and other HEP calculator formats.
- Serve YAML-driven Jarvis workflows through Jarvis-HEP without taking ownership of YAML parsing or runtime semantics.

## Ownership Boundary With Jarvis-HEP

Jarvis-HEP owns runtime and workflow semantics:

- YAML IO block parsing
- runtime path markers such as `&J`, `@PackID`, `@SampleID`, and `@Sdir`
- expression evaluation such as `x * Pi`
- sample and runtime context construction
- save, copy, and archive policy
- logger and IO manager integration
- deciding which variables are written or read

Jarvis-Portal owns format behavior:

- adapter registration and lookup
- adapter interface definitions
- format-specific read and write behavior
- JSON nested entry assignment and lookup
- tested format-specific parsing/writing
- future format-specific HEP IO logic

Jarvis-HEP should prepare concrete adapter specs and data values, then call Jarvis-Portal. Jarvis-Portal should not parse Jarvis-HEP YAML blocks or infer workflow policy.

## Registry Architecture

The registry is implemented by `jarvis_portal.registry.IORegistry`.

Adapters are registered by format name and direction:

```python
registry.register("JSON", JsonAdapter(), "both")
```

Format lookup is case-insensitive. Direction lookup accepts:

- `input`
- `output`
- `both`

When a direction-specific adapter is not found, the registry falls back to a `both` adapter for the same format. If no adapter is found, `MissingAdapterError` reports the requested format and the available formats for that direction.

`create_default_registry()` returns a fresh registry populated by `register_builtins()`. `create_entry_point_registry()` returns a fresh registry populated by built-ins plus installed `jarvishep.io` entry points that are allowed by `EXPOSED_FORMATS`. Broken entry points are skipped with a warning by default, and strict callers can pass `on_error="raise"`. Jarvis-HEP should use the entry point registry when it wants new Portal IO formats to become available after only upgrading `Jarvis-HEP-Portal`; newly developed formats must be added to `EXPOSED_FORMATS` before Jarvis-HEP can see them. Module-level helpers such as `get()`, `register()`, and `available_formats()` use a process-local default registry.

## IOContext Role

`IOContext` is the runtime-owned object passed into every adapter call.

It currently carries:

- optional logger
- optional IO manager
- sample and package identifiers
- sample save directory
- project root
- module name
- optional path resolver
- optional expression evaluator
- runtime values

Adapters should use `context.path(value)` for file paths. If Jarvis-HEP supplies a resolver, `IOContext` delegates path handling to it. Otherwise, relative paths can be resolved against `project_root`.

Adapters should use `context.run_blocking(...)` around synchronous file or parser work. If a caller provides an IO manager with `run_blocking`, that manager is used. Otherwise, work is dispatched through the active event loop executor.

`IOContext` can carry an expression evaluator for runtime integration, but current adapters should not use it to interpret Jarvis-HEP expressions unless that behavior has been explicitly assigned to Jarvis-Portal.

## Adapter Interface Role

The adapter protocol is `jarvis_portal.registry.IOAdapter`.

Adapters expose:

- `format_name`: human-readable format name, such as `JSON`
- `direction`: `input`, `output`, or `both`
- `async write_input(context, spec, data) -> dict`
- `async read_output(context, spec) -> dict`

`write_input` writes input files for external tools. `read_output` reads output files and returns observable values.

The registry does not enforce inheritance. Any object with the expected attributes and methods can be registered.

## Built-In Adapters

Current built-ins are registered in `jarvis_portal.builtins.register_builtins`.

- `JSON`: reads and writes JSON documents. Supports nested entries using dot-separated paths such as `settings.model.mass`.

SLHA/xSLHA code may exist in the repository during development, but it must not be registered or exposed through `jarvishep.io` until it has dedicated tests and examples.

## CLI Role

The `jportal` command is a lightweight utility entry point.

Current behavior:

- `jportal file` is the only supported CLI shape.
- `jportal man`, `jportal man <format>`, `jportal -h`, and `jportal -v` are the only utility exceptions.
- stdout is the observable dictionary itself encoded as JSON.
- the observable dictionary is flat and contains `name: value` items.

The CLI should stay separate from Jarvis-HEP workflow execution. Do not add options or alternate modes casually; any CLI expansion needs an explicit design decision.

## Non-Goals

Jarvis-Portal should not own:

- Jarvis-HEP YAML IO block parsing
- runtime path marker expansion
- expression evaluation
- sample construction
- workflow scheduling
- calculator execution
- save/copy/archive decisions
- logging policy
- variable selection policy
- a broad application framework around adapters

Keep the package focused on adapter lookup and format-specific IO behavior.
