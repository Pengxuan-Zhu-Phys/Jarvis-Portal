# Table Formats: CSV, TSV, DAT

## Context

Jarvis-Portal needs three tabular IO formats alongside the existing JSON adapter:

- **CSV** — comma-separated values
- **TSV** — tab-separated values
- **DAT** — whitespace-separated (one or more spaces/tabs), common in HEP Fortran-style output

All three share the same YAML spec structure; only the `type` field differs.

## Architecture Constraint: Format Isolation

Each IO format is implemented as an independent adapter class (`JsonAdapter`, `CsvAdapter`, `TsvAdapter`, `DatAdapter`). Adapters:

- Share no base class and have no cross-dependencies
- Are registered independently in the registry
- Can be added, modified, or removed without affecting other formats
- A bug or crash in one adapter does not propagate to others

This isolation ensures that modifying a single format never causes systemic failure.

## YAML Spec Design

### Mapping from JSON Concepts

| JSON concept | Table concept | Notes |
|---|---|---|
| `entry: "fit.loglike"` | `column: "loglike"` | Field addressing: JSON uses dot-path, tables use column name/index |
| (none) | `row: 0` | Tables have a row dimension; omitting `row` reads the whole column |
| (none) | `header: true` | Whether the first line contains column names |
| (none) | `columns: [...]` | Explicit column names when `header: false` |
| (none) | `comment: "#"` | Comment-line prefix (DAT default: `"#"`) |

### Spec-Level Fields (shared by all three formats)

```yaml
- name: params              # spec name
  path: "input.csv"         # file path
  type: CSV | TSV | DAT     # format type
  save: false               # whether to save a copy
  header: true              # first line is column names (default: true)
  columns: [col1, col2]     # explicit column names (when header: false)
  comment: "#"              # comment-line prefix (DAT only, default "#")
```

### DAT Whitespace Splitting

DAT format uses Python `str.split()` (no arguments) for column splitting:

- Handles any number of consecutive spaces and tabs
- Strips leading/trailing whitespace automatically
- Mixed spaces and tabs split correctly
- Skips lines starting with the `comment` prefix (default `#`) and blank lines
- On write, columns are separated by a single space

### Input (Writing)

Follows the JSON pattern: `actions` → `type: Dump` → `variables`.

**Key difference from JSON**: for table input variables, `name` is only an identifier — it does **not** fall back as a column name. `column` is mandatory.

```yaml
input:
  - name: params
    path: "input.csv"
    type: CSV
    header: true
    actions:
      - type: Dump
        variables:
          - { name: "var_mass",     expression: "x * Pi",   column: "mass" }
          - { name: "var_coupling", expression: "y * Pi",   column: "coupling" }
          - { name: "var_config",   expression: "(x+y)*Pi", column: "config" }
```

Variable fields:

| Field | Required | Description |
|---|---|---|
| `name` | yes | Variable identifier; used as the observable key when the variable has an expression |
| `expression` | yes | A literal number or expression; evaluated to produce the value; makes the variable an observable |
| `column` | **yes** | Target column (name or 0-based index) |
| `row` | no | Target row (default: 0, the first data row — not the header) |

**Single-cell write only**: each input variable writes exactly one value to one cell (`column` + `row`). Batch column operations are not supported — this keeps the write path simple and prevents cascading failures.

### Output (Reading)

```yaml
output:
  - name: observables
    path: "output.csv"
    type: CSV
    header: true
    variables:
      - { name: "chi2" }                              # reads column "chi2" → list or scalar
      - { name: "best_mass", column: "mass", row: 0 } # reads column "mass" row 0 → scalar
      - { name: "loglike", column: "fit_loglike" }     # reads column "fit_loglike" → list or scalar
```

Variable fields:

| Field | Required | Description |
|---|---|---|
| `name` | yes | Observable key; also used as default column name |
| `column` | no | Explicit column name (defaults to `name`) |
| `row` | no | Row index; omit to read the whole column |

Behavioral rules:

- **Auto-unpack**: when `row` is omitted and the column has exactly 1 element, the scalar is returned directly instead of a length-1 list.
- **Missing data**: if a variable cannot be read (column missing, row out of bounds, etc.), it is **omitted** from the returned observables dict entirely. Jarvis-HEP relies on key presence to decide whether all inputs are complete — a missing key triggers calculation abort. This is a hard constraint.

### Input vs Output `column` Semantics

| Direction | `column` | `name` role |
|---|---|---|
| Input | **mandatory** | identifier only |
| Output | optional (defaults to `name`) | observable key + default column name |

## Example Files

Each format directory under `examples/formats/` contains:

| File | Purpose |
|---|---|
| `README.md` | Format description |
| `adapter-spec.yaml` | jportal-runnable spec |
| `jarvis-hep.yaml` | Full Jarvis-HEP Calculators shape |
| `input.*` | Sample input template |
| `output.*` | Sample output data |

### CSV (`examples/formats/csv/`)

Standard comma-separated with header row.

### TSV (`examples/formats/tsv/`)

Tab-separated with header row.

### DAT (`examples/formats/dat/`)

Whitespace-separated with `comment: "#"`, demonstrates `header: false` + `columns: [...]`.
