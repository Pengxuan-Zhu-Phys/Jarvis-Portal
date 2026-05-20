# CLI

Jarvis-Portal installs one command:

```bash
jportal
```

The CLI is intentionally small. It is for inspecting Portal-facing YAML data and package adapter availability. It does not run Jarvis-HEP workflows.

## Usage

```bash
jportal input.yaml
jportal input.yaml --json
jportal input.yaml --json --compact
jportal input.yaml --json -o output.json
jportal --formats
jportal -v
jportal -h
```

## Default Behavior

`jportal input.yaml` loads the YAML file with `yaml.safe_load`, requires the top-level document to be a mapping, and prints the resulting Python dictionary to stdout:

```text
{'alpha': 1, 'nested': {'beta': 'two'}}
```

An empty YAML file is treated as an empty dictionary.

## Options

- `-h`, `--help`: print help and exit.
- `-v`, `--version`: print the installed Jarvis-Portal version and exit.
- `-o`, `--output`: write output to a file instead of stdout.
- `--json`: emit JSON instead of Python dictionary syntax.
- `--compact`: emit compact JSON; valid only with `--json`.
- `--formats`: list built-in adapter formats and exit.

## Boundary

The CLI may parse a YAML file into a dictionary. It should not:

- parse Jarvis-HEP IO block semantics
- expand `&J`, `@PackID`, `@SampleID`, or `@Sdir`
- evaluate expressions
- construct runtime/sample context
- run calculators or adapters
- decide save/copy/archive policy

Those responsibilities stay in Jarvis-HEP.
