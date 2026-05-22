# CSV Format

CSV is a tabular Jarvis-Portal format with both input and output support.

Supported directions:

- `input`
- `output`

Dependencies: none beyond the Python standard library.

Behavior:

- `write_input` reads an existing CSV file or starts from an empty table.
- CSV input writes use Jarvis-HEP-compatible `actions` with `type: Dump`.
- Each input variable writes a single cell: `column` (mandatory) + `row` (default 0).
- `read_output` reads values by column name, optionally narrowed to a specific row.
- When `row` is omitted, the entire column is returned as a list.
- Auto-unpack: a single-element column list is returned as a scalar.
- Missing data (column not found, row out of bounds) causes the variable to be omitted from observables entirely.
- Input variables with `expression` return their evaluated observable `name: value` items.
- File spec names become observables only when `save: true`.

Spec-level options:

- `header: true` (default) — first row contains column names.
- `header: false` — no header; use `columns: [...]` to assign names.

See [Table Formats](../../../docs/development/TABLE_FORMATS.md) for the complete design.
