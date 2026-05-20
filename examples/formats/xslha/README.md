# xSLHA Format

xSLHA is an optional Jarvis-Portal output format.

Supported directions:

- `output`

Dependency:

```bash
pip install "Jarvis-Portal[xslha]"
```

Behavior:

- `read_output` reads xSLHA blocks, decay widths, decay branching ratios, and one-loop decay values where supported by the `xslha` package.
- Complex values represented by the parser as two-element lists are returned as `Re[name]` and `Im[name]`.
- `write_input` is intentionally unsupported.

Jarvis-HEP alignment:

- Jarvis-HEP currently uses xSLHA for output reads with `block` and `entry` variables.
- Jarvis-HEP owns path resolution, saving policy, and variable selection.
