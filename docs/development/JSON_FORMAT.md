# JSON Format Usage

Jarvis-Portal's JSON adapter follows Jarvis-HEP's calculator IO JSON shape. A JSON input file spec can be copied from a Jarvis-HEP calculator `execution.input` item and passed to `JsonAdapter.write_input`; a JSON output file spec can be copied from `execution.output` and passed to `JsonAdapter.read_output`.

Both methods return the observable dictionary itself. Its structure is deliberately simple and flat: JSON output variables contribute one `name: value` item where `name` is the variable's YAML `name` and `value` is the concrete value read from JSON. Plain JSON input variables are written to the input file and do not become observables. JSON input variables with `expression` return their evaluated `name: value` items, matching Jarvis-HEP `JsonInputFile`. An input or output file spec itself contributes its YAML `name` only when `save: true`; that file observable maps to the resolved absolute file path.

Jarvis-HEP still owns full task YAML parsing, workflow execution, runtime path expansion, parameter sampling, and expression evaluation. Portal owns the file-format behavior after a caller has selected a JSON file spec and supplied concrete runtime values.

## Jarvis-HEP YAML Shape

For `jportal file`, use the same `input` / `output` file-spec field names as Jarvis-HEP. Do not use a second public YAML shape such as `write_input` or `read_output`.

In the compact `jportal` example, top-level `observables` supplies runtime values used by input expressions. The final stdout is still the adapter-returned observable dictionary.

```yaml
observables:
  x: 1.0
  y: 2.0

input:
  - name: params
    path: "input.json"
    type: JSON
    save: false
    actions:
      - type: Dump
        variables:
          - { name: "xx", expression: "x * Pi" }
          - { name: "yy", expression: "y * Pi" }
          - { name: "cx", expression: "(x + y) * Pi", entry: "test.config.x" }
output:
  - name: observables
    path: "output.json"
    type: JSON
    save: false
    variables:
      - { name: "z" }
      - { name: "likelihood", entry: "fit.loglike" }
```

Inside a full Jarvis-HEP calculator card, the same file specs live under `execution.input` and `execution.output`:

```yaml
Calculators:
  Modules:
    - name: JsonExample
      execution:
        path: "&J/calculators/json_example"
        commands:
          - "python run_json_example.py"
        input:
          - name: params
            path: "input.json"
            type: JSON
            save: true
            actions:
              - type: Dump
                variables:
                  - { name: "xx", expression: "x * Pi" }
                  - { name: "yy", expression: "y * Pi" }
                  - { name: "cx", expression: "(x + y) * Pi", entry: "test.config.x" }
        output:
          - name: observables
            path: "output.json"
            type: JSON
            save: false
            variables:
              - { name: "z" }
              - { name: "likelihood", entry: "fit.loglike" }
```

## Input Writes

Only `actions` with `type: Dump` are applied, matching Jarvis-HEP's `JsonInputFile` behavior.

Each dumped variable supports:

- `name`: the parameter name and default top-level JSON key.
- `entry`: optional dot-separated nested path, such as `model.mass`.
- `expression`: optional expression. Portal requires `IOContext.evaluate_expression` when this field is used.

If `expression` is not provided, Portal reads the value from the `data` mapping by `name`. Missing values are written as the string `"MISSING_VALUE"`, matching Jarvis-HEP.

```python
from jarvis_portal import IOContext, create_default_registry

adapter = create_default_registry().get("JSON", "input")

spec = {
    "name": "params",
    "path": "input.json",
    "type": "JSON",
    "save": False,
    "actions": [
        {
            "type": "Dump",
            "variables": [
                {"name": "x"},
                {"name": "mass", "entry": "model.mass"},
            ],
        }
    ],
}

observables = await adapter.write_input(IOContext(), spec, {"x": 1.0, "mass": 2.0})
```

The resulting JSON is:

```json
{
    "x": 1.0,
    "model": {
        "mass": 2.0
    }
}
```

With `save: false`, the returned observable dictionary is empty because plain input variables do not become observables:

```python
{}
```

If a dumped variable uses `expression`, its evaluated result is returned as an observable, matching Jarvis-HEP:

```yaml
actions:
  - type: Dump
    variables:
      - { name: "mass", entry: "model.mass", expression: "x * 2" }
```

## Output Reads

Output variables support top-level reads by `name` and nested reads by `entry`.

```python
adapter = create_default_registry().get("JSON", "output")

observables = await adapter.read_output(
    IOContext(),
    {
        "name": "observables",
        "path": "output.json",
        "type": "JSON",
        "save": False,
        "variables": [
            {"name": "z"},
            {"name": "likelihood", "entry": "fit.loglike"},
        ],
    },
)
```

Missing nested entries return `None`.

## Screen Output

Use the CLI to print the JSON adapter result as structured stdout:

```bash
jportal examples/formats/json/adapter-spec.yaml
```

The screen output is the observable dictionary itself:

```json
{
  "z": 42.0,
  "likelihood": -1.25
}
```

## Save Copies

When `save: true` and `IOContext.sample_save_dir` is set, Portal writes a copy named `<basename>@<module>` and returns the file spec `name` as an observable. For output reads with `save: false`, Portal mirrors Jarvis-HEP by writing a temporary copy under `<sample_save_dir>/.temp` when a sample save directory is available, but it does not return the file spec `name` as an observable. Returned file observable values are always resolved absolute primary file paths.

## Compatibility Notes

JSON input is aligned to Jarvis-HEP's `actions` / `variables` shape. Public YAML examples, CLI inputs, and direct adapter specs should use `actions` with `type: Dump`.
