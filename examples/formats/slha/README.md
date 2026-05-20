# SLHA Format

SLHA is an optional Jarvis-Portal format with input and output support.

Supported directions:

- `input`
- `output`

Dependency:

```bash
pip install "Jarvis-Portal[slha]"
```

Behavior:

- `write_input` can replace placeholders or update SLHA block entries.
- `read_output` can read block entries and decay widths/branching ratios.

Jarvis-HEP alignment:

- Jarvis-HEP currently supports SLHA input actions with `type: Replace`, `type: SLHA`, and `type: File`.
- Jarvis-HEP currently supports SLHA output variables with `block` and `entry`.
- Jarvis-HEP owns expression evaluation and placeholder value selection before Portal writes the file.
