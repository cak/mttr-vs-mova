# Why Vulnerability MTTR Alone Misleads: Add MOVA to Measure Real Risk

This repository supports the BSides Charm 2026 talk
**Why Vulnerability MTTR Alone Misleads: Add MOVA to Measure Real Risk**.

It demonstrates a simple but common failure mode in vulnerability programs:

> You can improve real risk while your MTTR gets worse.

This project uses a small, reproducible simulation to show why that happens and how **Mean Open Vulnerability Age (MOVA)** fills the gap.

- **MTTR = flow** (how fast work closes)
- **MOVA = stock** (how old the remaining risk is)

Used together, they show whether you are moving quickly and whether you are actually getting safer.

The rendered deck now includes a real in-slide Observable JS simulation with month-by-month playback, so the MTTR/MOVA paradox is visible live instead of being implied by static screenshots.

---

## Quick Start

If you just want to see the result:

```bash
uv sync
uv run quarto render
open index.html
```

Speaker notes for rehearsal live in `rehearsal/speaker-notes.md`.

If you want to regenerate everything from scratch:

```bash
uv run python scripts/01_generate_data.py
uv run python scripts/02_simulate_metrics.py
uv run python scripts/03_build_outputs.py
uv run quarto render
```

---

## The Core Idea

The talk centers on a practical paradox:

> Fixing older vulnerabilities can increase MTTR while reducing exposure.

Example:

- You close a 300-day-old vulnerability
- That raises your average remediation time
- Your MTTR goes up
- But your oldest risk just disappeared

MTTR reports that as a regression
Reality is that your risk posture improved

This repository makes that behavior visible and reproducible.

---

## What The Simulation Does

The model is intentionally constrained so the result is explainable:

- Same incoming volume
- Same remediation capacity
- Same time horizon
- Only prioritization changes

Two strategies run under identical conditions:

- **Newest-first**
  - Keeps MTTR low
  - Leaves older risk aging in the backlog

- **Oldest-first**
  - Raises MTTR
  - Reduces the age of remaining vulnerabilities

Nothing else changes. That isolates the effect of prioritization.

In the deck, the simulation is exposed two ways:

- Static Python-generated figures for the clean narrative beats
- A real Observable JS step-through with a month slider and play/pause controls

---

## What You Should See

When you run the simulation:

- MTTR looks better under newest-first
- MOVA looks worse under newest-first
- Oldest-first causes:
  - MTTR to rise
  - MOVA to fall

That divergence is the point

> MTTR describes completed work
> MOVA describes remaining exposure

---

## Why This Matters

If you report MTTR alone, you can reward the wrong behavior:

- Teams optimize for fast closures
- Older vulnerabilities linger
- Exposure quietly increases

If you report MTTR with MOVA, you can:

- See whether backlog risk is improving
- Explain MTTR increases during cleanup work
- Align leadership on what “progress” actually means
- Avoid optimizing for speed at the expense of exposure

This is not about replacing MTTR.
It is about making it interpretable.

---

## What This Repository Is

This repo is both:

1. A conference presentation (Quarto + Reveal.js)
2. A reproducible analysis workflow

The design is intentional:

- Synthetic data
- Explicit assumptions
- Deterministic outputs

You can inspect, rerun, and modify everything without needing production data.

---

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

---

## Simulation Design

The model is deliberately simple:

- 24-month window
- 360-item starting backlog
- 60 new vulnerabilities per month
- 60 fixes per month
- Strategies:
  - `newest_first`
  - `oldest_first`

No changes in capacity
No changes in volume
Only prioritization changes

This isolates the question:

> What happens when you change what you fix first?

---

## Why Quarto Fits This Project

Quarto keeps the full workflow in one place:

- Python generates the data and metrics
- Outputs are written to Parquet
- Observable JS re-simulates the same base vulnerability records inside the deck
- Reveal.js handles the presentation layer without a separate app

That gives you:

- Reproducibility
- Inspectable data flow
- No custom app or glue code

This is a good pattern for security analytics work where the story and the data should stay close together.

---

## Adapting This To Your Environment

You do not need to copy this model exactly. The useful parts are:

- Track both:
  - time-to-close (MTTR)
  - age-of-open (MOVA)

- Segment by:
  - severity
  - system or business unit

- Track “aged backlog” explicitly (for example, > 90 or > 180 days)

The key shift is conceptual:

> Stop asking “how fast are we closing?”
> Also ask “how old is what we have not closed?”

---

## Technology Stack

- **Quarto + Reveal.js** for presentation
- **Python + Polars** for reproducible data and static figures
- **Observable JS + Plot** for the live simulation
- **Plotnine** for speaker-friendly narrative charts
- **Parquet** for reproducible intermediate data

---

## License

MIT License
