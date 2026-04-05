# Why MTTR Alone Misleads: MTTR vs. MOVA

This repository supports the BSides Charm 2026 talk **Why Vulnerability MTTR Alone Misleads: Add MOVA to Measure Real Risk**.

It uses a simple, vendor-neutral, reproducible simulation to show why MTTR alone can misread vulnerability program health. When teams work down older backlog, MTTR often rises even as exposure falls. **Mean Open Vulnerability Age (MOVA)** adds the missing view by measuring the age of what is still open.

- **MTTR = flow**
- **MOVA = stock**

Used together, they show both how work is closing and whether backlog risk is actually improving.

## Why This Repository Exists

The talk centers on a practical paradox:

> A team fixing older backlog can look worse on MTTR while reducing real exposure.

This repository makes that argument concrete with a constrained simulation:

- Same incoming volume
- Same remediation capacity
- Same time horizon
- Only prioritization changes

That keeps the question narrow and useful. What changes when a team picks different work first?

## What The Simulation Shows

Two strategies run under the same conditions:

- **Newest-first** keeps MTTR low and allows older exposure to age in the backlog
- **Oldest-first** raises MTTR and reduces the age of the remaining backlog

The point is not that MTTR is bad. The point is that MTTR measures completed work, not the health of what remains open. MOVA makes that backlog health visible.

## Why This Matters

If you report MTTR alone, you can reward behavior that hides aging risk.

If you report MTTR with MOVA, you can:

- See whether backlog exposure is improving
- Explain why MTTR sometimes rises during healthy cleanup work
- Give leaders a better read on operational progress versus residual risk
- Keep teams from optimizing for fast closures at the expense of older exposure

## What This Repository Is

This repo is both a conference deck and a reproducible analysis workflow.

The examples are intentionally simple. The data is synthetic, the assumptions are visible, and the outputs can be regenerated locally. That makes the argument easy to inspect, rerun, and adapt after the talk.

## Repository Layout

```text
.
|-- index.qmd                    # Presentation source
|-- index.html                   # Rendered deck
|-- styles.css                   # Presentation styling
|-- _quarto.yml                  # Quarto configuration
|-- scripts/
|   |-- 01_generate_data.py      # Synthetic vulnerability dataset
|   |-- 02_simulate_metrics.py   # MTTR / MOVA simulation
|   `-- 03_build_outputs.py      # Final outputs for slides
|-- data/
|   |-- base_vulns.parquet
|   |-- metrics.parquet
|   `-- summary.parquet
|-- rehearsal/
|   `-- speaker-notes.md
|-- pyproject.toml
|-- uv.lock
`-- LICENSE
```

## Simulation Design

The model is deliberately constrained:

- 24-month window
- 360-item starting backlog
- 60 new vulnerabilities per month
- 60 fixes per month
- Two strategies: `newest_first`, `oldest_first`

No changes in capacity. Only prioritization changes.

This isolates the question:

> What changes when you change how you choose what to fix?

## How To Run

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Quarto CLI](https://quarto.org/)

### Install

```bash
uv sync
```

### Generate Data

```bash
uv run python scripts/01_generate_data.py
uv run python scripts/02_simulate_metrics.py
uv run python scripts/03_build_outputs.py
```

### Render Presentation

```bash
uv run quarto render
```

Output:

- `index.html` as a standalone Reveal.js deck

## Why Quarto Fits This Project

Quarto is central to the workflow. The deck source, code execution, and final presentation stay close together in one project.

Python scripts generate the synthetic vulnerability data and simulation outputs. Those outputs are written to parquet, then read back into the Quarto presentation for charts and summary tables. That keeps the analysis path inspectable from raw inputs to rendered slides.

This is the kind of workflow that fits well with reproducible analytical work in the Posit ecosystem. Code, data artifacts, and presentation stay in the same repository without turning the project into a custom app.

## Practical Use

If you run vulnerability management or report security metrics upward:

- Keep MTTR for flow
- Add MOVA for backlog exposure
- Track aged backlog explicitly
- Read metric shifts in context instead of treating every MTTR increase as failure

This is not about replacing MTTR. It is about using it with the missing companion metric.

## Technology Stack

- **Quarto + Reveal.js** for the presentation
- **Python + Polars** for synthetic data generation and simulation
- **Plotnine + Great Tables** for charts and tables in the deck
- **Parquet** for portable, reproducible intermediate outputs

The result is a compact workflow for data, analysis, and presentation in one place.

## License

MIT License
