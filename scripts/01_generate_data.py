"""Generate deterministic synthetic vulnerability data for the talk deck.

The dataset seeds an existing backlog before the simulation starts, then adds a
steady stream of new vulnerabilities each month. The simulation scripts reuse
this same arrival pattern for every prioritization strategy.
"""

from __future__ import annotations

import argparse
import calendar
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_PATH = DATA_DIR / "base_vulns.parquet"

DEFAULT_START = date(2024, 1, 1)
DEFAULT_MONTHS = 24
DEFAULT_MONTHLY_ARRIVALS = 60
DEFAULT_INITIAL_BACKLOG = 180
DEFAULT_BACKLOG_HISTORY_MONTHS = 12
DEFAULT_SEED = 20260426

SEVERITY_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("low", 0.18),
    ("medium", 0.46),
    ("high", 0.28),
    ("critical", 0.08),
)


@dataclass(frozen=True)
class GenerationConfig:
    """Parameters for the synthetic input dataset."""

    start_month: date = DEFAULT_START
    months: int = DEFAULT_MONTHS
    monthly_arrivals: int = DEFAULT_MONTHLY_ARRIVALS
    initial_backlog: int = DEFAULT_INITIAL_BACKLOG
    backlog_history_months: int = DEFAULT_BACKLOG_HISTORY_MONTHS
    seed: int = DEFAULT_SEED


def parse_args() -> argparse.Namespace:
    """Parse lightweight CLI arguments for local reruns."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE_PATH, help="Parquet output path.")
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional CSV export for demo and inspection workflows.",
    )
    parser.add_argument("--months", type=int, default=DEFAULT_MONTHS)
    parser.add_argument("--monthly-arrivals", type=int, default=DEFAULT_MONTHLY_ARRIVALS)
    parser.add_argument("--initial-backlog", type=int, default=DEFAULT_INITIAL_BACKLOG)
    parser.add_argument(
        "--backlog-history-months",
        type=int,
        default=DEFAULT_BACKLOG_HISTORY_MONTHS,
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def add_months(value: date, delta: int) -> date:
    """Return the first day of the month shifted by `delta` months."""

    month_index = (value.year * 12 + value.month - 1) + delta
    year, month_offset = divmod(month_index, 12)
    return date(year, month_offset + 1, 1)


def month_end(value: date) -> datetime:
    """Return the final timestamp of the month for a date anchored to day 1."""

    last_day = calendar.monthrange(value.year, value.month)[1]
    return datetime(value.year, value.month, last_day, 23, 59, 59)


def random_timestamp_within_month(rng: random.Random, month_anchor: date) -> datetime:
    """Draw a deterministic timestamp within a given month."""

    start = datetime(month_anchor.year, month_anchor.month, 1)
    last_day = month_end(month_anchor).day
    return start + timedelta(
        days=rng.randrange(last_day),
        hours=rng.randrange(8, 18),
        minutes=rng.randrange(0, 60),
    )


def allocate_counts(total: int, weights: Sequence[int]) -> list[int]:
    """Allocate integer counts across weighted buckets while preserving totals."""

    weighted_total = sum(weights)
    raw = [total * weight / weighted_total for weight in weights]
    counts = [int(value) for value in raw]
    remainder = total - sum(counts)

    ranked_remainders = sorted(
        range(len(weights)),
        key=lambda index: raw[index] - counts[index],
        reverse=True,
    )
    for index in ranked_remainders[:remainder]:
        counts[index] += 1

    return counts


def validate_config(config: GenerationConfig) -> None:
    """Fail fast on invalid generation settings."""

    if config.months <= 0:
        raise ValueError("months must be positive")
    if config.monthly_arrivals <= 0:
        raise ValueError("monthly_arrivals must be positive")
    if config.initial_backlog < 0:
        raise ValueError("initial_backlog cannot be negative")
    if config.backlog_history_months <= 0:
        raise ValueError("backlog_history_months must be positive")


def generate_base_vulnerabilities(config: GenerationConfig) -> pl.DataFrame:
    """Build the synthetic vulnerability population used by the simulation.

    The initial backlog uses a simple ramp so recent months contribute more
    findings than very old months while still leaving a real long tail to work
    down. This keeps the data presentation-friendly without making the starting
    state perfectly flat.
    """

    validate_config(config)
    rng = random.Random(config.seed)
    severity_labels = [label for label, _ in SEVERITY_WEIGHTS]
    severity_weights = [weight for _, weight in SEVERITY_WEIGHTS]

    rows: list[dict[str, object]] = []
    next_id = 1

    backlog_weights = list(range(1, config.backlog_history_months + 1))
    backlog_counts = allocate_counts(config.initial_backlog, backlog_weights)

    for month_offset, count in zip(
        range(config.backlog_history_months, 0, -1),
        backlog_counts,
        strict=True,
    ):
        month_anchor = add_months(config.start_month, -month_offset)
        for _ in range(count):
            rows.append(
                {
                    "id": next_id,
                    "severity": rng.choices(severity_labels, weights=severity_weights, k=1)[0],
                    "created_at": random_timestamp_within_month(rng, month_anchor),
                    "resolved_at": None,
                    "created_month": month_anchor,
                    "source_cohort": "initial_backlog",
                    "is_initial_backlog": True,
                }
            )
            next_id += 1

    for month_offset in range(config.months):
        month_anchor = add_months(config.start_month, month_offset)
        for _ in range(config.monthly_arrivals):
            rows.append(
                {
                    "id": next_id,
                    "severity": rng.choices(severity_labels, weights=severity_weights, k=1)[0],
                    "created_at": random_timestamp_within_month(rng, month_anchor),
                    "resolved_at": None,
                    "created_month": month_anchor,
                    "source_cohort": "monthly_arrival",
                    "is_initial_backlog": False,
                }
            )
            next_id += 1

    return (
        pl.DataFrame(rows)
        .with_columns(
            pl.col("created_at").cast(pl.Datetime("us")),
            pl.col("resolved_at").cast(pl.Datetime("us")),
            pl.col("created_month").cast(pl.Date),
            pl.col("is_initial_backlog").cast(pl.Boolean),
        )
        .sort(["created_at", "id"])
    )


def write_outputs(df: pl.DataFrame, parquet_path: Path, csv_path: Path | None) -> None:
    """Write the primary Parquet artifact and optional CSV export."""

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(parquet_path)
    print(f"Wrote {parquet_path.relative_to(ROOT)} ({df.height} rows)")

    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(csv_path)
        print(f"Wrote {csv_path.relative_to(ROOT)}")


def main() -> None:
    """Generate the base dataset from CLI parameters."""

    args = parse_args()
    config = GenerationConfig(
        months=args.months,
        monthly_arrivals=args.monthly_arrivals,
        initial_backlog=args.initial_backlog,
        backlog_history_months=args.backlog_history_months,
        seed=args.seed,
    )
    base_vulns = generate_base_vulnerabilities(config)
    write_outputs(base_vulns, args.out, args.csv_out)


if __name__ == "__main__":
    main()
