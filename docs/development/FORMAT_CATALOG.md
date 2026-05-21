# Format Catalog

Jarvis-Portal is expected to grow many independent IO format adapters. Each format must be developed, documented, tested, and exampled as its own unit.

This catalog defines the repository layout and minimum contract for each format.

## Directory Layout

Each format gets one directory under `examples/formats/`:

```text
examples/formats/<format>/
  README.md
  jarvis-hep.yaml
  adapter-spec.yaml
  input-or-template-file
  output-or-sample-file
```

Use lowercase directory names, for example:

```text
examples/formats/json/
examples/formats/slha/
examples/formats/xslha/
examples/formats/root/
examples/formats/hepmc/
examples/formats/lhe/
examples/formats/yoda/
```

## Required Files

`README.md` explains the format-specific adapter behavior, supported directions, optional dependencies, and known limitations.

`jarvis-hep.yaml` shows the Jarvis-HEP-facing YAML shape. This file must stay aligned with Jarvis-HEP's current calculator IO configuration style.

`adapter-spec.yaml` shows a compact Jarvis-HEP IO shape that `jportal file` can run directly. It must use `input` and `output` lists, not a second public YAML design.

Sample files should be small, deterministic, and readable. They should exercise the fields shown in the YAML examples without requiring a full external HEP calculator.

## Independence Rule

Every format should be independent:

- adapter implementation in its own module or package area
- built-in registration in `register_builtins()` or an entry point under `jarvishep.io`
- tests in a dedicated test file or test class
- example directory under `examples/formats/<format>/`
- optional dependencies isolated to extras
- no import-time dependency on optional HEP packages
- no hidden coupling to another format adapter

Shared helpers are allowed only when they remove real duplication and do not make one format depend on another format's parser.

## Jarvis-HEP Alignment

Current Jarvis-HEP calculator IO YAML uses file specs under:

```yaml
Calculators:
  Modules:
    - execution:
        input:
          - name: params
            path: input.json
            type: JSON
            save: true
            actions: []
        output:
          - name: observables
            path: output.json
            type: JSON
            save: false
            variables: []
```

Jarvis-Portal examples should preserve this shape in `jarvis-hep.yaml`.

Do not move these Jarvis-HEP responsibilities into Jarvis-Portal:

- parsing the full Jarvis-HEP card
- resolving `&J`, `@PackID`, `@SampleID`, or `@Sdir`
- evaluating expressions
- selecting variables for a workflow
- sample save/copy/archive policy
- module execution

Jarvis-Portal examples may include those fields only to document compatibility with Jarvis-HEP.

## Adapter Spec Alignment

`adapter-spec.yaml` should document the compact Jarvis-HEP IO contract that can be used in unit tests. For JSON, it intentionally keeps the Jarvis-HEP `input` and `output` field names:

```yaml
input:
  - name: params
    path: input.json
    type: JSON
    save: false
    actions:
      - type: Dump
        variables:
          - { name: "x" }
          - { name: "nested", entry: "settings.value" }

output:
  - name: observables
    path: output.json
    type: JSON
    save: false
    variables:
      - { name: "result", entry: "observables.result" }
```

This is not a replacement for full Jarvis-HEP task YAML. It is the selected file-spec shape after Jarvis-HEP or another caller has resolved workflow semantics.

## Adding A New Format

For every new format:

1. Add or update the adapter implementation.
2. Add the format to the registry only for supported directions.
3. Add optional dependencies to a dedicated extra when needed.
4. Add tests for registration, success cases, error cases, and missing optional dependencies.
5. Add `examples/formats/<format>/README.md`.
6. Add `examples/formats/<format>/jarvis-hep.yaml`.
7. Add `examples/formats/<format>/adapter-spec.yaml`.
8. Add small input/output sample files.
9. Add the format to `register_builtins()` or `jarvishep.io` entry points only after tests pass.
10. Update docs and README links if the format becomes user-facing.

## Current Format Directories

- [JSON](../../examples/formats/json/README.md)
- [JSON usage](JSON_FORMAT.md)

SLHA/xSLHA example directories may exist during development, but they are not currently exposed through the registry.
