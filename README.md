# Why Vulnerability MTTR Alone Misleads

This repository contains the [Quarto](https://quarto.org/) / Reveal.js deck and supporting analysis for the talk **Why Vulnerability MTTR Alone Misleads**.

The central claim is simple: **MTTR can rise while exposure falls**. When a team finally closes older backlog, the age of the work it closes goes up, so MTTR looks worse even while the open backlog is getting healthier. **MOVA** (Mean Open Vulnerability Age) complements MTTR by showing how old the backlog still open is right now.

The talk is grounded in a real operational pattern, but the repo stays vendor-neutral and reproducible: the examples use deterministic synthetic data, and the metric definitions, charts, and tables all live in code rather than in dashboard screenshots or hidden platform logic.

## What The Talk Argues

- **MTTR measures flow**: the age of work that got closed.
- **MOVA measures stock**: the age of work that is still open.
- MTTR alone can make leaders reward the wrong outcome: fast recent closures while older exposure stays stranded.
- Open count and `180+ days open` help show whether the aging tail is actually shrinking.
- The point is not to replace MTTR. It is to stop using MTTR alone.

## What This Repo Contains

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

## Practical Takeaways

- Report MTTR and MOVA side by side.
- Add open count and a backlog-age threshold such as `180+ days`.
- Define the metrics in code from exported vulnerability data; a CSV is usually enough.
- Use MTTR to understand flow, and MOVA to understand exposure.
- Do not reward teams for keeping MTTR low while backlog age worsens.

## Render The Deck

Prerequisites: [uv](https://docs.astral.sh/uv/) and [Quarto](https://quarto.org/).

```bash
uv sync
uv run quarto render
```

`uv run quarto render` runs the pre-render scripts in `_quarto.yml`, regenerates the synthetic data and comparison outputs, and writes the deck to `_output/index.html`.

For live preview while editing:

```bash
uv run quarto preview
```

## Tools & Approach

- [Quarto](https://quarto.org/) keeps the deck, narrative, and rendered outputs in one reproducible workflow.
- [Positron](https://positron.posit.co/) is a practical place to inspect the data and iterate on the analysis before rendering, though the workflow is not tied to any particular IDE.
- [Polars](https://pola.rs/) handles the metric logic, while [Plotnine](https://plotnine.org/) and [Great Tables](https://posit-dev.github.io/great-tables/) keep charts and tables in code so the analysis stays inspectable and rerunnable.

## Further Reading

For learning Polars, _[Python Polars: The Definitive Guide](https://polarsguide.com/)_ by Jeroen Janssens and Thijs Nieuwdorp is a practical reference.

## License

MIT License
