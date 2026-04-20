"""Build presentation-friendly end-state outputs from the monthly metrics."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
METRICS_PATH = DATA_DIR / "metrics.parquet"
SUMMARY_PATH = DATA_DIR / "summary.parquet"


def format_output_path(path: Path) -> str:
    """Return a stable display path for logs inside or outside the repo."""

    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    """Parse lightweight CLI arguments for summary output generation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH, help="Input metrics dataset.")
    parser.add_argument("--out", type=Path, default=SUMMARY_PATH, help="Parquet output path.")
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional CSV export for inspection or demo workflows.",
    )
    return parser.parse_args()


def build_summary(metrics: pl.DataFrame) -> pl.DataFrame:
    """Take the final month for each strategy and keep a stable output schema."""

    return (
        metrics.sort(["strategy", "month_index"])
        .group_by("strategy", maintain_order=True)
        .tail(1)
        .with_columns(
            pl.when(pl.col("strategy") == "oldest_first")
            .then(pl.lit(0))
            .when(pl.col("strategy") == "newest_first")
            .then(pl.lit(1))
            .otherwise(pl.lit(99))
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


def write_outputs(df: pl.DataFrame, parquet_path: Path, csv_path: Path | None) -> None:
    """Write the primary summary dataset and optional CSV export."""

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(parquet_path)
    print(f"Wrote {format_output_path(parquet_path)} ({df.height} rows)")

    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(csv_path)
        print(f"Wrote {format_output_path(csv_path)}")


def main() -> None:
    """Build and persist the final comparison table input."""

    args = parse_args()
    metrics = pl.read_parquet(args.metrics)
    summary = build_summary(metrics)
    write_outputs(summary, args.out, args.csv_out)


if __name__ == "__main__":
    main()
