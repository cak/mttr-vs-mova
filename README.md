# Why Vulnerability MTTR Alone Misleads

This repository contains the [Quarto](https://quarto.org/) / Reveal.js talk deck and reproducible analysis for the MOVA talk **Why Vulnerability MTTR Alone Misleads**.

The central claim is simple: **MTTR can rise while backlog age falls**. MTTR reflects the age of work that got closed. **MOVA** (Mean Open Vulnerability Age) measures backlog age: the age of the work still open today. When a team finally closes older backlog, the age of closed work goes up, so MTTR can look worse even while the remaining backlog gets healthier.

The talk is grounded in a real operational pattern, but the repo stays vendor-neutral and reproducible. The examples use deterministic synthetic data, and the metric definitions, charts, and tables all live in code rather than dashboard screenshots or hidden platform logic.

## Core Argument

- **MTTR reflects flow**: the age of work that got closed.
- **MOVA measures backlog age**: the age of work still open today.
- MTTR alone can reward recent closures while older backlog remains stranded.
- Open count and a threshold like `180+ days open` help show whether the aging tail is actually shrinking.
- The point is not to replace MTTR. It is to stop using MTTR alone.

## Repo Contents

- `index.qmd`: the talk deck source
- `scripts/01_generate_data.py`: builds the deterministic synthetic backlog and arrivals
- `scripts/02_simulate_metrics.py`: simulates monthly metrics for `oldest_first` and `newest_first`
- `scripts/03_build_outputs.py`: writes the end-state comparison used in the deck
- `_quarto.yml` and `styles.css`: deck configuration and presentation styling
- `pyproject.toml` and `uv.lock`: Python dependencies for the analysis pipeline

Generated artifacts are created during render under `data/` and `_output/`.

## The Simulation

The deck uses a small reproducible simulation to isolate prioritization:

- same starting backlog
- same incoming vulnerabilities each month
- same monthly remediation capacity
- same 24-month horizon
- only the work order changes: `newest_first` vs. `oldest_first`

That makes the tradeoff explicit:

- **Newest-First** keeps MTTR lower by closing newer findings first.
- **Oldest-First** raises MTTR while lowering MOVA and shrinking the `180+ days` tail.
- If you look only at MTTR, you pick the wrong winner.

## Published Links

The published materials use this structure:

- Landing page: <https://typeerror.com/mova>
- Talk deck: <https://typeerror.com/mova/slides/>
- BSides Charm listing: <https://pretalx.com/bsidescharm2026/talk/MMNUPD/>

In the published output, `docs/index.html` is the landing page and `docs/slides/index.html` is the talk.

## Render Locally

Prerequisites: [uv](https://docs.astral.sh/uv/) and [Quarto](https://quarto.org/).

```bash
uv sync
uv run quarto render
```

`uv run quarto render` runs the pre-render scripts in `_quarto.yml`, regenerates the synthetic data and comparison outputs, and writes the local deck to `_output/index.html`.

For live preview while editing:

```bash
uv run quarto preview
```

## Publish Slides

To render the published deck into `docs/slides` for GitHub Pages:

```bash
quarto render index.qmd --output-dir docs/slides
```

This keeps local development output in `_output/` and published output in `docs/slides/`.

## Tools & Approach

- [Quarto](https://quarto.org/) keeps the deck, narrative, and rendered outputs in one reproducible workflow.
- [Positron](https://positron.posit.co/) is a convenient place to inspect the data and iterate on the analysis before rendering, though the workflow does not depend on any particular IDE.
- [Shiny for Python](https://shiny.posit.co/py/) is useful for lightweight interactive checks when testing metric definitions and backlog slices.
- [Polars](https://pola.rs/) implements the metric logic.
- [Plotnine](https://plotnine.org/) and [Great Tables](https://posit-dev.github.io/great-tables/) keep charts and tables in code so the analysis stays inspectable and rerunnable.

## Further Reading

- _[Python Polars: The Definitive Guide](https://polarsguide.com/)_ by Jeroen Janssens and Thijs Nieuwdorp
- _[Effective Vulnerability Management: Managing Risk in the Vulnerable Digital Ecosystem](https://onlinelibrary.wiley.com/doi/book/10.1002/9781394277155)_ by Chris Hughes and Nikki Robinson

## License

MIT License
