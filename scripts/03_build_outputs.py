"""Build summary outputs for the presentation.

Run after 02_simulate_metrics.py. Reads data/metrics.parquet and writes
data/summary.parquet with the final-month state for each strategy.
"""
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
METRICS_PATH = DATA_DIR / "metrics.parquet"
SUMMARY_PATH = DATA_DIR / "summary.parquet"


def main() -> None:
    metrics = pl.read_parquet(METRICS_PATH)
    last_month = metrics.get_column("month_index").max()

    summary = (
        metrics.filter(pl.col("month_index") == last_month)
        .with_columns(
            pl.when(pl.col("strategy") == "oldest_first")
            .then(pl.lit(0))
            .otherwise(pl.lit(1))
            .alias("strategy_order")
        )
        .sort("strategy_order")
        .select(
            "strategy",
            "mttr_days",
            "mova_days",
            "open_count",
            "aged_over_180",
        )
    )

    summary.write_parquet(SUMMARY_PATH)
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)} ({summary.height} rows)")


if __name__ == "__main__":
    main()
