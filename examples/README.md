# Examples

Examples are organized by IO format.

Each format directory is independent and contains:

- `README.md`: format-specific notes
- `jarvis-hep.yaml`: Jarvis-HEP-facing calculator IO YAML shape
- `adapter-spec.yaml`: direct Jarvis-Portal adapter spec shape
- small sample files for tests, documentation, and manual inspection

Jarvis-HEP owns the full workflow card semantics. Jarvis-Portal owns only the format-specific adapter behavior shown in `adapter-spec.yaml`.
