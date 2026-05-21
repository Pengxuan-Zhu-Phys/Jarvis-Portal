# Jarvis-Portal Documentation

This directory contains the developer documentation for Jarvis-Portal.

Jarvis-Portal is the IO adapter and registry package used by the Jarvis ecosystem. Its documentation is organized around the practical work needed to maintain the package: local development, adapter design, testing, architecture, and release preparation.

## Layout

- [Development](development/DEVELOPMENT.md): local setup, editable installs, optional extras, test commands, and build commands.
- [CLI](development/CLI.md): direct `jportal file`, `jportal man`, `-h`, and `-v` behavior and boundaries.
- [Architecture](design/ARCHITECTURE.md): package goals, ownership boundary with Jarvis-HEP, registry design, context objects, adapters, built-ins, and non-goals.
- [Adapter Authoring](development/ADAPTER_AUTHORING.md): how to implement and register new format adapters.
- [Format Catalog](development/FORMAT_CATALOG.md): per-format example directory structure and Jarvis-HEP YAML alignment rules.
- [JSON Format Usage](development/JSON_FORMAT.md): Jarvis-HEP-compatible JSON input/output file-spec usage.
- [Testing](development/TESTING.md): test layout, required adapter coverage, optional dependency handling, async test style, and CI expectations.
- [Release](release/RELEASE.md): version bump, build, GitHub release, PyPI Trusted Publishing, manual settings, and post-release checks.

For a short overview and install commands, start with the repository [README](../README.md).
