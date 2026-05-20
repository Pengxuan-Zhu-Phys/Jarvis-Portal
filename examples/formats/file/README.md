# File Format

File is a built-in Jarvis-Portal format for plain text files.

Supported directions:

- `input`
- `output`

Dependencies: none beyond the Python standard library.

Behavior:

- `write_input` writes text content to a path.
- `read_output` returns file content only when `read_content: true` is set in the direct adapter spec.

Jarvis-HEP alignment:

- Current Jarvis-HEP has a `File` output handler for saving/copying output artifacts.
- Jarvis-Portal also has a direct plain text input writer so callers can generate simple text inputs without a format-specific parser.
