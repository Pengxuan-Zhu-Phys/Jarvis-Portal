# Examples

Examples are organized by IO format.

Each format directory is independent and contains:

- `README.md`: format-specific notes
- `jarvis-hep.yaml`: Jarvis-HEP-facing calculator IO YAML shape
- `adapter-spec.yaml`: compact Jarvis-HEP IO YAML shape accepted by `jportal file`
- small sample files for tests, documentation, and manual inspection

Jarvis-HEP owns the full workflow card semantics. Jarvis-Portal owns only the format-specific file behavior shown in `adapter-spec.yaml`; public YAML still uses Jarvis-HEP `input` / `output` field names.
