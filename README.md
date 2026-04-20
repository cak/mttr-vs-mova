# Why Vulnerability MTTR Alone Misleads

This repository contains a [Quarto](https://quarto.org/) / Reveal.js talk and the supporting analysis code behind it. The deck argues that vulnerability programs should read **MTTR** and **Mean Open Vulnerability Age (MOVA)** together:

- **MTTR = flow**: how long closed work took to remediate
- **MOVA = stock**: how old the open backlog is right now

The examples are vendor-neutral, built from synthetic data, and fully inspectable. Nothing depends on a platform screenshot or a hidden dashboard definition.

## Talk Summary

The talk centers on a simple operational paradox: MTTR can get worse while exposure is actually going down. If a team spends time clearing older findings, the age of the work it closes rises, so MTTR rises too. That can look like regression even when the backlog is getting healthier.

MOVA fills that gap by measuring the age of the vulnerabilities still open. This repo demonstrates the difference with a reproducible simulation that holds arrivals, capacity, and time horizon constant, then compares two strategies: **Newest-First** and **Oldest-First**. The point is not to replace MTTR, but to keep it in context.

## Core Idea

The deck makes four claims:

- MTTR tells you about completed work, not the backlog that remains.
- MOVA shows whether the exposure you still carry is getting older or younger.
- Open count and the `180+ days` tail help explain whether aging risk is actually being reduced.
- The metrics should be defined in code and reviewed together, not inherited blindly from a dashboard.

## What This Repo Contains

- `index.qmd`: the presentation source and narrative
- `scripts/`: synthetic data generation, strategy simulation, and summary build steps
- `data/`: generated Parquet files used by the deck
- `_quarto.yml` and `styles.css`: deck configuration and presentation styling
- `pyproject.toml` and `uv.lock`: Python environment and dependency lockfile

The analysis pipeline is small by design. It generates a synthetic backlog, simulates monthly remediation under two prioritization strategies, writes the metric outputs to Parquet, and renders the deck from those artifacts.

## Quick Start

Render the current deck:

```bash
uv sync
uv run quarto render
open index.html
```

Rebuild the synthetic data and metrics first:

```bash
uv run python scripts/01_generate_data.py
uv run python scripts/02_simulate_metrics.py
uv run python scripts/03_build_outputs.py
uv run quarto render
```

## What the Deck Shows

The simulation keeps the system constant and changes only prioritization.

- **Newest-First** closes recent findings first, which keeps MTTR lower.
- **Oldest-First** closes the aging backlog first, which lowers MOVA and reduces the `180+ days` tail.
- Both strategies run with the same arrivals, the same monthly remediation capacity, and the same time horizon.

That is the core read: the headline MTTR winner is not necessarily the exposure winner.

## Why It Matters

Read alone, MTTR can reward recent closure while older backlog remains stranded. Read with MOVA, open count, and the `180+ days` tail, it becomes easier to distinguish faster throughput from actual backlog cleanup.

This is also a practical argument for analysis-as-code. Most teams already have the underlying data. A CSV export is often enough. The harder problem is owning the metric definition instead of accepting whatever the dashboard happens to calculate.

## Repository Layout

- `index.qmd`: slide content, charts, tables, and embedded code examples
- `scripts/01_generate_data.py`: builds the synthetic vulnerability dataset
- `scripts/02_simulate_metrics.py`: runs the newest-first vs. oldest-first simulation
- `scripts/03_build_outputs.py`: writes the final comparison summary used in the deck
- `data/base_vulns.parquet`: synthetic starting dataset
- `data/metrics.parquet`: monthly MTTR, MOVA, open count, and `aged_over_180`
- `data/summary.parquet`: final-state comparison for the two strategies
- `rehearsal/speaker-notes.md`: talk notes used for delivery prep

## Tools & Approach

- [Quarto](https://quarto.org/) keeps the deck, narrative, and rendered outputs in one reproducible workflow.
- [Positron](https://positron.posit.co/) is a practical place to inspect the data and iterate on the analysis before rendering, though the workflow is not tied to any particular IDE.
- [Polars](https://pola.rs/) handles the metric logic, while [Plotnine](https://plotnine.org/) and [Great Tables](https://posit-dev.github.io/great-tables/) keep charts and tables in code so the analysis stays inspectable and rerunnable.

## Speaker

The talk and repository are by Caleb Kinney. More background and writing: [derail.net](https://derail.net).

## Further Reading

For learning Polars, *[Python Polars: The Definitive Guide](https://polarsguide.com/)* by Jeroen Janssens and Thijs Nieuwdorp is a practical reference.

## License

MIT License
