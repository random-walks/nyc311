# Example Template

This folder is the canonical bootstrap template for new `nyc311` examples.

Copy it to a new semantic slug, then replace the placeholders in `main.py`,
`pyproject.toml`, and this README with the story for your new example.

## Copy Workflow

1. Copy `examples/example-template/` to `examples/<your-semantic-slug>/`.
2. Update `pyproject.toml` with the new project name, description, and required
   `nyc311` extras.
3. Replace the placeholder metadata and TODOs in `main.py`.
4. Decide which data mode the example uses:
   - packaged sample data only
   - cache-backed live slice
5. Decide which output classes the example needs:
   - `cache/` for ignored local snapshots
   - `artifacts/` for ignored scratch CSVs and intermediate outputs
   - `reports/` for tracked markdown and tracked report figures
6. Generate the first report and figures, then tighten the README so it reads as
   a user-facing example instead of a template.

## Folder Contract

Every well-formed example should include:

- `pyproject.toml`
- `.gitignore`
- `README.md`
- `main.py`
- optional tracked `reports/`
- optional ignored `cache/`
- optional ignored `artifacts/`

## Report Pattern

Use a tracked `reports/` folder when the example produces stable, useful assets
that should ship with the repo.

Recommended report conventions:

- name the markdown file `<example-slug>-tearsheet.md`
- store report images in `reports/figures/`
- reference figures with explicit relative paths like
  `./figures/example-chart.png`
- keep markdown narrative auto-generated from computed values
- keep README narrative focused on how to run and understand the example

## Output Split

- `cache/`: ignored local data snapshots and expensive refreshable inputs
- `artifacts/`: ignored scratch CSVs, intermediate joins, staging files, and
  anything too heavy or too unstable for git
- `reports/`: tracked tearsheets and the exact figures those tearsheets need

## Question-Driven Story

A good example should answer a small number of clear questions.

Examples:

- Which geography has the strongest party-music intensity?
- Which complaint type dominates after spatial enrichment?
- Which records fall outside the boundary layer?
- Which areas show the weakest dominant-topic signal?

Prefer charts and report sections that answer those questions directly instead
of a generic dump of every available output.

## Shipping Checklist

- the example imports only `nyc311.*`
- `uv sync` and `uv run python main.py` work from the example folder
- README lists the right extras for public consumers
- ignored outputs stay in `cache/` or `artifacts/`
- tracked outputs stay under `reports/`
- markdown image links use relative paths that render on GitHub
