# Borough Choropleth

This example builds a borough-level dominant-topic choropleth from packaged
sample records and the packaged borough boundary layer.

## Local Repo Usage

```bash
cd examples/borough-choropleth
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output

- writes `artifacts/borough-dominant-noise-topics.png`

## Notes

- uses packaged sample records only
- does not create or depend on a cache
