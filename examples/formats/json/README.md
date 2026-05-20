# JSON Format

JSON is a built-in Jarvis-Portal format with both input and output support.

Supported directions:

- `input`
- `output`

Dependencies: none beyond the Python standard library.

Behavior:

- `write_input` reads an existing JSON document or starts from `{}`.
- Write operations can set top-level names or dot-separated nested entries.
- `read_output` can read top-level names or dot-separated nested entries.
- Missing nested output entries return `None`.

Jarvis-HEP alignment:

- Jarvis-HEP currently represents JSON input writes under calculator `execution.input[*].actions`.
- Jarvis-HEP currently represents JSON output reads under calculator `execution.output[*].variables`.
- Jarvis-HEP remains responsible for expression evaluation before values are passed to Jarvis-Portal.
