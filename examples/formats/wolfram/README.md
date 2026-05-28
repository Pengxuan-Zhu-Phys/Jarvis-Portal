# Wolfram Format

Wolfram is a built-in Jarvis-Portal format with both input and output support.

Supported directions:

- `input`
- `output`

Dependencies: none beyond the Python standard library.

Behavior:

- `write_input` reads an existing Wolfram Language Association document or starts from `<||>`.
- Wolfram input writes use Jarvis-HEP-compatible `actions` with `type: Dump`.
- Dumped variables can set top-level names or dot-separated nested entries.
- `read_output` can read top-level names, dot-separated nested entries, and list indexes.
- Missing nested output entries return `None`.
- Missing input data values are written as `"MISSING_VALUE"`.
- Adapter calls return the observable dictionary itself.
- Output variables contribute observable `name: value` items.
- Plain input variables are written to files and do not become observables.
- Input variables with `expression` return their evaluated observable `name: value` items.
- File spec names become observables only when `save: true`.

Jarvis-HEP alignment:

- Jarvis-HEP currently represents Wolfram input writes under calculator `execution.input[*].actions`.
- Jarvis-HEP currently represents Wolfram output reads under calculator `execution.output[*].variables`.
- Jarvis-Portal accepts the same Wolfram file-spec shape for adapter calls.
- Jarvis-HEP remains responsible for expression evaluation during full workflow runs. Direct Portal calls that include `expression` must provide `IOContext.evaluate_expression`.

See [Wolfram Format Usage](../../../docs/development/WOLFRAM_FORMAT.md) for the complete design.
