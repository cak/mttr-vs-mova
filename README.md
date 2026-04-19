# Why Vulnerability MTTR Alone Misleads: Add MOVA to Measure Real Risk

MTTR is a useful operational metric, but a poor standalone measure of security risk. This talk argues for pairing it with **Mean Open Vulnerability Age (MOVA)** so you can see whether exposure is actually getting older or younger. The case is made with a small, reproducible Quarto deck backed by Python and Polars, not a hand-waved opinion.

- **MTTR = flow** (how fast work closes)
- **MOVA = stock** (how old the remaining risk is)

Used together, they show whether you are moving quickly and whether the system is getting safer.

The deck includes a live, in-slide Observable JS simulation with month-by-month playback, so the MTTR/MOVA divergence is visible instead of implied.

---

## Quick Start

If you want the rendered deck:

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

The talk centers on a simple paradox:

> Fixing older vulnerabilities can raise MTTR while reducing exposure.

Example:

- You close a 300-day-old vulnerability
- Average remediation time rises
- Your oldest risk disappears

MTTR records a regression.
The risk posture improved.

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

In the deck, the simulation appears two ways:

- Static Python-generated figures for the clean narrative beats
- A real Observable JS step-through with a month slider and play/pause controls
- A single Great Tables end-state comparison slide for leadership-style readout

---

## What You Should See

When you run the simulation:

- Newest-first lowers MTTR while older risk keeps aging
- Oldest-first raises MTTR while MOVA falls

That divergence is the point.

> MTTR describes completed work
> MOVA describes remaining exposure

---

## Why This Matters

If you report MTTR alone, you can reward fast closure while older vulnerabilities age in place. Pairing MTTR with MOVA changes the conversation:

- You can see whether backlog risk is improving
- You can explain MTTR increases during cleanup work
- You can define progress in terms of exposure, not ticket churn

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

Open `index.qmd` first. It is the deck and the argument.

- `scripts/` generates the synthetic data, runs the MTTR/MOVA simulation, and builds slide outputs
- `data/` holds the generated Parquet artifacts
- `rehearsal/speaker-notes.md` contains speaker notes
- `_quarto.yml` and `pyproject.toml` define the render and analysis environment

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

No changes in capacity.
No changes in volume.
Only prioritization changes.

This isolates the question:

> What happens when you change what you fix first?

---

## Why Quarto Fits This Project

Quarto keeps the full workflow in one place: Python and Polars generate the data and metrics, Parquet preserves the intermediate state, Observable JS re-simulates the same vulnerability records inside the deck, and Reveal.js handles presentation without a separate app.

That keeps the analysis reproducible, inspectable, and close to the argument.

---

## Adapting This To Your Environment

You do not need to copy this model exactly. The useful parts are:

- Track both time-to-close (MTTR) and age-of-open (MOVA)
- Segment by severity and system or business unit
- Track aged backlog explicitly (for example, `> 90` or `> 180` days)

The key shift is conceptual:

> Stop asking “how fast are we closing?”
> Also ask “how old is what we have not closed?”

---

## Technology Stack

- **Quarto + Reveal.js** for the presentation
- **Python + Polars** for reproducible data and simulation
- **Plotnine** for narrative charts used in the talk
- **Great Tables** for clean, presentation-ready summary tables
- **Parquet** for portable, reproducible intermediate data

---

## License

MIT License
