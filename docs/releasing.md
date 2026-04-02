# Releasing

This guide covers the current PyPI release workflow for `nyc311`.

## Release discipline

- Current stable line: `0.2.x`
- Version source: git tags via Hatch VCS
- Preferred publish trigger: GitHub Release publication

Patch releases in the `0.2.x` line are the default path for docs polish,
workflow updates, packaging fixes, and backward-compatible behavior changes. Cut
a new minor release when the public workflow or package surface expands in a
meaningful way.

## Pre-release checks

Before cutting a release tag, make sure the repo passes:

```bash
make ci
make audit
make docs-build
make smoke-dist
```

That covers:

- lint, typing, and public API checks
- docs build validation
- source and wheel builds
- PyPI long-description validation
- installed-wheel smoke testing for the CLI and packaged resources

If the release touches `nyc311.geographies` or dependency ranges, also verify
the current `nyc-geo-toolkit` compatibility path before tagging.

## Release path

The standard production path is:

1. create the final release tag, for example `0.2.5`
2. push the tag
3. optionally run the `CD` workflow against TestPyPI first
4. publish the matching GitHub Release
5. let the `release.published` trigger publish to real PyPI

If you prefer the manual route, run the `CD` workflow from the same tag with:

- `publish=true`
- `repository=pypi`

## Trusted publishing setup

This repo uses trusted publishing through `.github/workflows/cd.yml` and the
`pypi` GitHub environment.

If you ever need to recreate that setup, verify:

- owner: `random-walks`
- repository: `nyc311`
- workflow: `.github/workflows/cd.yml`
- environment: `pypi`

## Bootstrap checklist

These one-time steps must be completed by a human account owner before the
trusted publishing flow can be used:

1. Create or verify the PyPI account that will own `nyc311`, and enable 2FA.
2. Create or verify a TestPyPI account if you want a dry run before production.
3. Add a pending trusted publisher for project `nyc311` on both TestPyPI and
   PyPI using:
   - Owner: `random-walks`
   - Repository: `nyc311`
   - Workflow: `.github/workflows/cd.yml`
   - Environment: `pypi`
4. In GitHub, create the `pypi` environment and add any desired deployment
   protection rules.
5. Set the repository variable `PYPI_PUBLISH_ENABLED=true` only when you are
   ready to allow publishing.
6. Prepare the public GitHub repository settings:
   - About description
   - Topics
   - Homepage / docs URL
   - Social preview

Important: a pending trusted publisher does not reserve the PyPI name until it
is used successfully for the first publish.

## TestPyPI Dry Run

For routine releases, do one dry run from the final release tag:

1. Create the release tag, for example `0.2.5`.
2. Push the tag.
3. Run the `CD` workflow manually from that tag with:
   - `publish=true`
   - `repository=testpypi`
4. Verify installation from TestPyPI in a clean environment.

Example validation commands:

```bash
python -m venv .venv-testpypi-check
.venv-testpypi-check/bin/python -m pip install --upgrade pip
.venv-testpypi-check/bin/python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nyc311
.venv-testpypi-check/bin/nyc311 --help
```

If you want the optional stacks too:

```bash
.venv-testpypi-check/bin/python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple "nyc311[all]"
```

## Post-Release Verification

After the release lands on PyPI:

1. Install `nyc311` from PyPI in a clean environment.
2. Run `nyc311 --help`.
3. Verify at least one packaged-resource path:
   - `nyc311.samples.load_sample_service_requests()`
   - `nyc311.geographies.load_nyc_boundaries("borough")`
4. Confirm the PyPI project page renders the README correctly.
5. Confirm the docs site, GitHub release notes, and README badges all reflect
   the public release.
