"""Build presentation-friendly end-state outputs from the monthly metrics."""

from __future__ import annotations

from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
METRICS_PATH = DATA_DIR / "metrics.parquet"
SUMMARY_PATH = DATA_DIR / "summary.parquet"
STRATEGY_ORDER = {"oldest_first": 0, "newest_first": 1}


def format_output_path(path: Path) -> str:
    """Return a stable display path for logs inside or outside the repo."""

    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_summary(metrics: pl.DataFrame) -> pl.DataFrame:
    """Take the final month for each strategy and keep a stable output schema."""

    return (
        metrics.sort(["strategy", "month_index"])
        .group_by("strategy", maintain_order=True)
        .tail(1)
        .with_columns(
            pl.col("strategy")
            .replace_strict(STRATEGY_ORDER, default=99)
            .alias("strategy_order")
        )
        .sort("strategy_order")
        .select(
            "strategy",
            "month_index",
            "month",
            "resolved_count",
            "mttr_days",
            "mova_days",
            "open_count",
            "aged_over_180",
        )
    )


def write_output(df: pl.DataFrame) -> None:
    """Write the default summary dataset for the pipeline."""

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(SUMMARY_PATH)
    print(f"Wrote {format_output_path(SUMMARY_PATH)} ({df.height} rows)")


def main() -> None:
    """Build and persist the final comparison table input."""

    metrics = pl.read_parquet(METRICS_PATH)
    summary = build_summary(metrics)
    write_output(summary)


if __name__ == "__main__":
    main()
