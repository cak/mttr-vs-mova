# mttr-vs-mova

Quarto Revealjs talk for BSides Charm 2026:
"Why MTTR Alone Misleads: Add MOVA to Measure Real Risk"

## Build

From the project root:

```bash
uv run python scripts/01_generate_data.py
uv run python scripts/02_simulate_metrics.py
uv run python scripts/03_build_outputs.py
uv run quarto render
```

## Structure

- `index.qmd`: presentation source
- `_quarto.yml`: project and Revealjs configuration
- `styles.css`: presentation styling
- `scripts/`: numbered data-generation pipeline
- `data/`: parquet outputs consumed by the slides
