# CLI

Jarvis-Portal installs one command:

```bash
jportal test.yaml
jportal man
jportal man json
jportal -h
jportal -v
```

`jportal file` is the only supported business CLI shape. The allowed utility exceptions are `jportal man`, `jportal man <format>`, `-h/--help`, and `-v/--version`. Do not add ad hoc CLI options or extra modes without an explicit design decision. Jarvis-Portal is primarily an adapter library for Jarvis-HEP; the CLI is a narrow inspection/execution helper and must stay predictable.

## Output Contract

The screen output is always the observable dictionary itself:

```json
{
  "z": 42.0,
  "likelihood": -1.25
}
```

The observable dictionary is flat. It must not contain nested direction groups such as `input` or `output`, and the CLI must not print auxiliary `details`, logs, wrapper keys, or adapter metadata to stdout.

For Jarvis-HEP IO specs, output variables contribute `name: value` items. Plain input variables are written to files and do not become observables. Input variables with `expression` contribute their evaluated `name: value` items when an evaluator is available. An input or output file spec itself contributes its YAML `name` only when `save: true`; that file observable maps to the resolved absolute file path.

## Accepted YAML

`jportal test.yaml` accepts either:

- a Jarvis-HEP IO spec with top-level `input` and/or `output` lists
- a full Jarvis-HEP card with `Calculators.Modules[*].execution.input` and `Calculators.Modules[*].execution.output`
- a mapping that already contains an `observables` dictionary

When `observables` appears together with `input` or `output`, it supplies runtime values for input expressions. It is not printed by itself; stdout remains the adapter-returned observable dictionary.

JSON example:

```yaml
observables:
  x: 1.0
  y: 2.0

input:
  - name: params
    path: input.json
    type: JSON
    actions:
      - type: Dump
        variables:
          - { name: "xx", expression: "x * Pi" }
          - { name: "yy", expression: "y * Pi" }
          - { name: "cx", expression: "(x + y) * Pi", entry: "test.config.x" }

output:
  - name: observables
    path: output.json
    type: JSON
    variables:
      - { name: "z" }
      - { name: "likelihood", entry: "fit.loglike" }
```

## Manual

`jportal man` prints a quick manual with supported input/output format lists and available format manual topics.

```bash
jportal man
```

`jportal man json` prints the JSON format manual, including the YAML shape and flat observable dictionary return contract.

```bash
jportal man json
```

Use `jportal man` for quick format discovery. Do not add `--formats`; manual output is the supported discovery path.

## Boundary

The CLI should not grow general workflow features. Do not add options for:

- alternate output shapes
- compact output
- separate format listing flags
- output redirection
- Jarvis-HEP workflow execution
- runtime path marker expansion beyond the adapter context
- expression evaluation
- save/copy/archive policy selection

Those responsibilities stay in Jarvis-HEP or in library-level APIs.
