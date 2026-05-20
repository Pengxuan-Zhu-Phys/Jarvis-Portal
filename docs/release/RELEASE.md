# Release

Do not publish from a local development session unless that is the explicit release task. Normal development should stop after local build verification.

## Version Bump Checklist

Jarvis-Portal currently stores the version in two places:

- `pyproject.toml`
- `src/jarvis_portal/_version.py`

For a release:

- choose the next version
- update both files to the same value
- update release notes or changelog material if available
- run tests
- run lint
- run build
- commit the version bump
- tag the release as `vX.Y.Z`

Do not change the package version for documentation-only or ordinary feature work unless preparing a release.

## Build Checklist

From a clean working tree:

```bash
python -m pip install -e ".[dev]"
ruff check .
python -m pytest
python -m build
twine check dist/*
```

Inspect `dist/` and confirm both a source distribution and wheel were produced.

For the local PyPI release helper, source `jptrel` from the repository root and pass the target version:

```bash
source ./jptrel
jptrel 0.1.1
```

This helper updates `pyproject.toml` and `src/jarvis_portal/_version.py`, cleans build artifacts, builds distributions, uploads them with `twine upload -r pypi`, reinstalls the package locally in editable mode, and verifies the installed package metadata and built-in adapters.

## GitHub Release Process

The publish workflow runs when a GitHub release is published.

Expected process:

1. Confirm CI is passing on the release commit.
2. Create and push a tag such as `v0.1.0`.
3. Draft a GitHub release for that tag.
4. Include concise release notes: changed behavior, new adapters, compatibility notes, and known limitations.
5. Publish the GitHub release.
6. Let `.github/workflows/publish.yml` build and publish to PyPI.

Do not create GitHub releases from routine development tasks.

## PyPI Trusted Publishing Setup

The publish workflow uses PyPI Trusted Publishing through `pypa/gh-action-pypi-publish`.

Required GitHub workflow properties are already present:

- `permissions: id-token: write`
- release trigger
- PyPI publish action
- `environment: pypi`

Manual PyPI setup is still required before the workflow can publish.

## Manual PyPI And GitHub Settings

On PyPI:

- create or claim the `Jarvis-Portal` project
- configure a trusted publisher for the GitHub repository
- match the workflow filename: `publish.yml`
- match the environment name: `pypi`
- confirm the package name uses the same normalized project name expected by PyPI

On GitHub:

- confirm the repository URL in `pyproject.toml`
- keep the `pypi` environment if protected publishing is desired
- configure any required environment reviewers or branch/tag protections
- ensure releases are created from the intended tag

No PyPI API token should be committed. Trusted Publishing should use GitHub OIDC instead.

## Post-Release Verification

After the publish workflow succeeds:

```bash
python -m pip install --upgrade Jarvis-Portal
python -c "import jarvis_portal; print(jarvis_portal.__version__)"
```

Optionally verify extras in a fresh environment:

```bash
python -m pip install "Jarvis-Portal[slha]"
python -m pip install "Jarvis-Portal[xslha]"
```

Check:

- the PyPI project page shows the expected version
- the wheel and source distribution are present
- the package imports on a clean Python version supported by CI
- GitHub release notes point to the correct tag
- no unintended files were included in the distribution
