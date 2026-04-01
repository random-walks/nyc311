# Point To Boundary Join

This example turns packaged sample records into points, joins them to packaged
sample community-district boundaries, and writes both a CSV preview and a PNG
map artifact.

## Local Repo Usage

```bash
cd examples/point-to-boundary-join
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Outputs

- writes `artifacts/point-boundary-join.csv`
- writes `artifacts/point-boundary-preview.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
