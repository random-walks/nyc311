# Releasing

This guide covers the first public PyPI launch path for `nyc311` and the
repeatable workflow after that.

## Release Shape

- Stable line: `0.2`
- First public stable target: `0.2.0`
- Version source: git tags via Hatch VCS
- Preferred publish trigger: GitHub Release publication

## Phase 1: Repo Polish

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

## Manual Setup Checklist

These steps must be done by a human account owner before the first public
release:

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
7. Decide when the repository will become public relative to the release tag and
   GitHub Release window.

Important: a pending trusted publisher does not reserve the PyPI name until it
is used successfully for the first publish.

## TestPyPI Dry Run

After manual setup is complete, do one dry run from the final release tag:

1. Create the release tag, for example `0.2.0`.
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

## Production Release

Once the TestPyPI dry run passes:

1. Make the repository public if it is still private.
2. Confirm the `pypi` environment and `PYPI_PUBLISH_ENABLED=true` are in place.
3. Publish a GitHub Release from the tag.

The `release.published` trigger will publish to real PyPI automatically. If you
prefer a manual path instead, run the `CD` workflow from the same tag with:

- `publish=true`
- `repository=pypi`

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
