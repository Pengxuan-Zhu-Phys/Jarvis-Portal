# DAT Format

DAT is a whitespace-delimited tabular Jarvis-Portal format with both input and output support. Common in HEP for Fortran-style output files.

Supported directions:

- `input`
- `output`

Dependencies: none beyond the Python standard library.

Behavior:

- Columns are split by whitespace (`str.split()` — handles multiple spaces, tabs, mixed).
- Lines starting with the `comment` prefix (default `#`) and blank lines are skipped.
- `write_input` reads an existing DAT file or starts from an empty table.
- DAT input writes use Jarvis-HEP-compatible `actions` with `type: Dump`.
- Each input variable writes a single cell: `column` (mandatory) + `row` (default 0).
- `read_output` reads values by column name, optionally narrowed to a specific row.
- When `row` is omitted, the entire column is returned as a list.
- Auto-unpack: a single-element column list is returned as a scalar.
- Missing data causes the variable to be omitted from observables entirely.
- Input variables with `expression` return their evaluated observable `name: value` items.
- File spec names become observables only when `save: true`.
- On write, columns are separated by a single space.

Spec-level options:

- `header: false` (typical for DAT) — use `columns: [...]` to assign column names.
- `header: true` — first data row contains column names.
- `comment: "#"` (default) — prefix for comment lines to skip.

See [Table Formats](../../../docs/development/TABLE_FORMATS.md) for the complete design.
