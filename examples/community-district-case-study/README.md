# Community District Case Study

This example loads a larger Brooklyn slice, reuses an example-local cache, and
turns the results into a publish-gated community-district case study focused on
volume, normalized residential-noise topics, and resolution gaps.

## Questions This Example Answers

- Which Brooklyn community districts carry the most complaint volume?
- Which districts show the strongest party-music intensity after normalization?
- Which complaint categories dominate the broader cached slice?
- Which districts have the weakest resolution rates?

## Local Repo Usage

```bash
cd examples/community-district-case-study
uv sync
uv run python main.py
```

To refetch the cache:

```bash
uv run python main.py --refresh
```

To refresh the tracked report assets:

```bash
uv run python main.py --publish-report
```

## Public Package Shape

```bash
pip install "nyc311[plotting]"
python main.py
```

Use `--refresh` to rebuild the cache and `--publish-report` only when you want
to intentionally update the tracked report assets.

## Output Layout

- `cache/`: ignored local live snapshot reused between runs
- `artifacts/`: ignored scratch CSV summaries for topic, volume, and resolution
  work
- `reports/`: tracked markdown tearsheet and tracked report figures

Running the example writes or reuses:

- `cache/brooklyn-case-study.csv`
- `artifacts/brooklyn-noise-community-districts.csv`
- `artifacts/brooklyn-noise-dominant-districts.csv`
- `artifacts/brooklyn-district-volume.csv`
- `artifacts/brooklyn-district-resolution.csv`
- `artifacts/brooklyn-complaint-type-resolution.csv`

When `--publish-report` is passed, it also writes:

- `reports/community-district-case-study-tearsheet.md`
- `reports/figures/brooklyn-district-volume.png`
- `reports/figures/brooklyn-party-music-intensity.png`
- `reports/figures/brooklyn-resolution-gap.png`

## Notes

- keeps its live slice local to this folder
- now defaults to a higher-row Brooklyn cache so district comparisons have more
  signal
- reuses the local cache by default instead of refetching
- gates tracked report regeneration behind `--publish-report`
