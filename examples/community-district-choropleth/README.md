# Community District Choropleth

This example builds a dominant-topic choropleth for the packaged sample's
community-district subset.

## Local Repo Usage

```bash
cd examples/community-district-choropleth
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output

- writes `artifacts/community-district-dominant-noise-topics.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
