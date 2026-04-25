# Why Vulnerability MTTR Alone Misleads

This repository contains the [Quarto](https://quarto.org/) / Reveal.js talk deck and reproducible analysis for the MOVA talk **Why Vulnerability MTTR Alone Misleads**.

The central pattern is simple: **MTTR can rise while backlog age falls**. MTTR reflects the age of work that got closed. **MOVA** (Mean Open Vulnerability Age) measures backlog age: the age of the work still open today. When a team finally closes older backlog, the age of closed work goes up, so MTTR can look worse even while the remaining backlog changes in a useful way. Older vulnerabilities often persist because they are harder to fix, require coordination, or carry higher risk.

Metrics are not the goal. They are how we observe the consequences of risk-based decisions.

MTTR and MOVA are partial signals. Each answers a different question, and neither is sufficient alone.

## How to Prioritize

Prioritize remediation based on risk. Not newest-first or oldest-first.

- Severity (CVSS)
- Exploitability (KEV, weaponized PoC)
- Exposure (reachability)
- Asset criticality
- Threat intelligence

The talk is grounded in a real operational pattern, but the repo stays vendor-neutral and reproducible. The examples use deterministic synthetic data, and the metric definitions, charts, and tables all live in code rather than dashboard screenshots or hidden platform logic.

## Core Argument

- **MTTR reflects flow**: the age of work that got closed.
- **MOVA measures backlog age**: the age of work still open today.
- Each answers a different question.
- Neither metric is sufficient alone.
- MOVA without MTTR can also mislead. A healthier backlog can still hide slow response to new risk.
- Open count and an aging-tail diagnostic help show whether older backlog is actually shrinking.
- Use MTTR and MOVA together to understand whether your risk-based prioritization is improving the system.

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
- same deterministic arrival pattern (with realistic variability)
- same deterministic capacity pattern (shared across strategies)
- same 24-month horizon
- only the work order changes: `newest_first` vs. `oldest_first`

This is an intentionally simplified comparison. It is not a recommendation to use `oldest_first` as a remediation strategy. We do not prioritize by age. We prioritize by risk. Metrics show the consequences of those decisions.

In the simulation, `oldest_first` produces lower backlog age, but it ignores risk and is not a real-world strategy.

Newest-first can improve MTTR while leaving high-risk older findings open.

The simulation isolates closure order so the metric behavior is easy to see.

Both strategies operate on the exact same arrivals and capacity each month. Only prioritization changes.

Small deterministic variability is introduced to avoid perfectly smooth charts while keeping the comparison fair.

That makes the tradeoff explicit:

- **Newest-First** keeps MTTR lower by closing newer findings first.
- **Oldest-First** produces lower MOVA and a smaller aging tail in the simulation because it reaches older backlog work first.
- If you look only at MTTR, recent closures can look like full-program progress.

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
