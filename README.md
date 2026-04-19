# Why Vulnerability MTTR Alone Misleads

This repository contains a Quarto presentation and supporting analysis that argues for pairing **MTTR** with **Mean Open Vulnerability Age (MOVA)** when communicating vulnerability risk.

- **MTTR = flow**: how fast closed work moved through the system
- **MOVA = stock**: how old the remaining open exposure is

The core point is simple: MTTR is useful, but it can mislead when reported alone. A team can close older vulnerabilities, improve its actual risk posture, and still watch MTTR get worse. MOVA makes that behavior visible.

The talk is built as a reproducible, vendor-neutral, analysis-as-code workflow for security leaders who need to explain real exposure, not just ticket movement.

## What This Repo Contains

- A Quarto / Reveal.js presentation in `index.qmd`
- Python and Polars scripts that generate the synthetic data and metrics
- Plotnine charts and Great Tables outputs used in the deck
- Parquet artifacts in `data/` for reproducible intermediate results

Everything is designed to be inspectable, rerunnable, and easy to adapt.

## Quick Start

Render the deck:

```bash
uv sync
uv run quarto render
open index.html
```

Regenerate the analysis artifacts and render from scratch:

```bash
uv run python scripts/01_generate_data.py
uv run python scripts/02_simulate_metrics.py
uv run python scripts/03_build_outputs.py
uv run quarto render
```

## What The Deck Shows

The simulation holds volume, capacity, and time horizon constant and changes only prioritization.

- **Newest-First** keeps MTTR lower by closing newer work first
- **Oldest-First** raises MTTR while reducing the age of the remaining backlog

That is the point of the talk:

> MTTR describes completed work. MOVA describes remaining exposure.

Used together, they help security leaders see whether operations are moving and whether the system is actually getting safer.

## Why It Matters

If you report MTTR alone, you can reward fast closure while older risk keeps aging in place. Pairing MTTR with MOVA makes it easier to:

- explain why MTTR can rise during meaningful cleanup work
- show whether backlog exposure is getting older or younger
- communicate risk to leadership in terms of current exposure, not dashboard optics

## Repository Layout

- `index.qmd`: the presentation and argument
- `scripts/`: synthetic data generation, simulation, and output builds
- `data/`: generated Parquet artifacts
- `_quarto.yml` and `pyproject.toml`: render and environment configuration
- `rehearsal/speaker-notes.md`: rehearsal notes

## Working Approach

The repo stays intentionally simple:

- synthetic data instead of production data
- explicit assumptions instead of hidden dashboard logic
- code-based analysis instead of ad hoc one-off interpretation

That makes the workflow auditable, repeatable, and cheaper to rerun when questions change.

## License

MIT License
