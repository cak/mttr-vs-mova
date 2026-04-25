# Why Vulnerability MTTR Alone Misleads

This repository contains the [Quarto](https://quarto.org/) / Reveal.js talk deck and reproducible analysis for the MOVA talk **Why Vulnerability MTTR Alone Misleads**.

The talk's thesis is practical: **MTTR and MOVA are complementary signals**. Mean Time to Remediate (MTTR) shows closure flow. Mean Open Vulnerability Age (MOVA) shows the age of the open backlog right now. Neither is sufficient alone.

The simulation is not meant to prove that oldest-first is best. It shows that prioritization choices have measurable consequences, and teams should read MTTR and MOVA together before judging progress.

Older vulnerabilities often persist because they are harder to fix, require coordination, or carry higher risk. If older risk is not being addressed, it will show up in MOVA even when MTTR looks healthy.

## How to Prioritize

Prioritize remediation based on risk, not newest-first or oldest-first. Use MTTR and MOVA to observe the consequences of those choices; in this repo, newest-first and oldest-first are simplified simulation patterns used to make metric behavior visible. Examples include CVSS, CISA Known Exploited Vulnerabilities (KEV), and the Exploit Prediction Scoring System (EPSS).

- Severity, such as CVSS
- Exploitability, such as CISA KEV, EPSS, or weaponized proof-of-concept
- Exposure, such as internet reachability
- Asset criticality, such as production or sensitive systems
- Threat intelligence, such as active targeting
- Business context, such as customer or compliance impact

The talk is grounded in a real operational pattern, but the repo stays vendor-neutral and reproducible. The examples use deterministic synthetic data, and the metric definitions, charts, and tables all live in code rather than dashboard screenshots or hidden platform logic.

## Core Argument

- **MTTR reflects closure flow**: how old the remediated work was in a reporting window.
- **MOVA reflects open backlog age**: how old the unresolved work is right now.
- MTTR is windowed. Label the window before calling a regression.
- MOVA is not windowed. It reflects open backlog age right now.
- Lower MTTR can hide an aging backlog. Lower MOVA can still hide slow response to new risk.
- Prioritization choices have measurable consequences. Read MTTR and MOVA together before judging progress.

## Repo Contents

- `index.qmd`: the talk deck source
- `scripts/01_generate_data.py`: builds the deterministic synthetic backlog and arrivals
- `scripts/02_simulate_metrics.py`: simulates monthly metrics for `oldest_first` and `newest_first`
- `scripts/03_build_outputs.py`: writes the end-state comparison used in the deck
- `_quarto.yml` and `styles.css`: deck configuration and presentation styling
- `pyproject.toml` and `uv.lock`: Python dependencies for the analysis pipeline

Generated artifacts are created during render under `data/` and `_output/`.

## The Simulation

The deck uses a small reproducible simulation to isolate how closure order changes metric behavior:

- same starting backlog
- same deterministic arrival pattern (with realistic variability)
- same deterministic capacity pattern (shared across strategies)
- same 24-month horizon
- only the simplified closure pattern changes: `newest_first` vs. `oldest_first`

This is an intentionally simplified comparison. `newest_first` and `oldest_first` are not recommended remediation strategies. They are controlled simulation patterns used to reveal how MTTR and MOVA respond when the same team closes work in a different order.

In the simulation, `oldest_first` changes MOVA by working older backlog first, but it ignores risk and is not a real-world remediation strategy.

`newest_first` can improve MTTR while leaving high-risk older findings open.

Both patterns operate on the exact same arrivals and capacity each month. Small deterministic variability is introduced to avoid perfectly smooth charts while keeping the comparison fair.

That makes the tradeoff explicit:

- **Newest-First** keeps MTTR lower by closing newer findings first.
- **Oldest-First** changes MOVA in the simulation because it reaches older backlog work first.
- If you read only MTTR, recent closures can look like full-program progress.

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
