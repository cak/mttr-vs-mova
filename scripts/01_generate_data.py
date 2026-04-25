"""Generate deterministic synthetic vulnerability data for the talk deck.

The dataset seeds an existing backlog before the simulation starts, then adds a
deterministic month-by-month arrival pattern. The simulation scripts reuse this
same arrival pattern for every prioritization strategy.
"""

from __future__ import annotations

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
DEFAULT_INITIAL_BACKLOG = 120
DEFAULT_BACKLOG_HISTORY_MONTHS = 9
DEFAULT_SEED = 20260426
DEFAULT_SEED_NAME = "talk_final_polish_v1"
DEFAULT_ARRIVAL_VARIATION = 0.15

SEVERITY_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("low", 0.18),
    ("medium", 0.46),
    ("high", 0.28),
    ("critical", 0.08),
)


def format_output_path(path: Path) -> str:
    """Return a stable display path for logs inside or outside the repo."""

    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class GenerationConfig:
    """Parameters for the synthetic input dataset."""

    start_month: date = DEFAULT_START
    months: int = DEFAULT_MONTHS
    monthly_arrivals: int = DEFAULT_MONTHLY_ARRIVALS
    initial_backlog: int = DEFAULT_INITIAL_BACKLOG
    backlog_history_months: int = DEFAULT_BACKLOG_HISTORY_MONTHS
    seed_name: str = DEFAULT_SEED_NAME
    seed: int = DEFAULT_SEED
    arrival_variation: float = DEFAULT_ARRIVAL_VARIATION


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


def bounded_normal_int(
    rng: random.Random,
    mean: float,
    stddev: float,
    lower_bound: int,
    upper_bound: int,
) -> int:
    """Return a rounded bounded normal draw using a local RNG."""

    if lower_bound > upper_bound:
        raise ValueError("lower_bound cannot exceed upper_bound")

    sampled = round(rng.gauss(mean, stddev))
    return max(lower_bound, min(upper_bound, sampled))


def consume_vulnerability_draws(
    rng: random.Random,
    month_anchor: date,
    count: int,
    severity_labels: Sequence[str],
    severity_weights: Sequence[float],
) -> None:
    """Advance the RNG exactly as vulnerability row generation would."""

    for _ in range(count):
        rng.choices(severity_labels, weights=severity_weights, k=1)
        random_timestamp_within_month(rng, month_anchor)


def monthly_arrival_schedule(config: GenerationConfig) -> list[int]:
    """Build the explicit month-by-month arrival plan used by the base dataset."""

    validate_config(config)
    rng = random.Random(config.seed)
    severity_labels = [label for label, _ in SEVERITY_WEIGHTS]
    severity_weights = [weight for _, weight in SEVERITY_WEIGHTS]
    backlog_weights = list(range(1, config.backlog_history_months + 1))
    backlog_counts = allocate_counts(config.initial_backlog, backlog_weights)

    for month_offset, count in zip(
        range(config.backlog_history_months, 0, -1),
        backlog_counts,
        strict=True,
    ):
        month_anchor = add_months(config.start_month, -month_offset)
        consume_vulnerability_draws(
            rng, month_anchor, count, severity_labels, severity_weights
        )

    lower_bound = round(config.monthly_arrivals * (1 - config.arrival_variation))
    upper_bound = round(config.monthly_arrivals * (1 + config.arrival_variation))
    schedule: list[int] = []

    for month_offset in range(config.months):
        arrival_count = bounded_normal_int(
            rng=rng,
            mean=config.monthly_arrivals,
            stddev=config.monthly_arrivals * 0.07,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        schedule.append(arrival_count)
        month_anchor = add_months(config.start_month, month_offset)
        consume_vulnerability_draws(
            rng,
            month_anchor,
            arrival_count,
            severity_labels,
            severity_weights,
        )

    return schedule


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
    if not 0 < config.arrival_variation < 0.5:
        raise ValueError("arrival_variation must be between 0 and 0.5")


def generate_base_vulnerabilities(
    config: GenerationConfig, arrival_schedule: Sequence[int] | None = None
) -> pl.DataFrame:
    """Build the synthetic vulnerability population used by the simulation.

    The initial backlog uses a simple ramp so recent months contribute more
    findings than very old months while still leaving meaningful older work to
    address. New arrivals follow one explicit deterministic schedule so the
    charts feel less synthetic without changing the comparison.
    """

    validate_config(config)
    rng = random.Random(config.seed)
    schedule = (
        monthly_arrival_schedule(config)
        if arrival_schedule is None
        else list(arrival_schedule)
    )
    if len(schedule) != config.months:
        raise ValueError("arrival_schedule length must match config.months")
    severity_labels = [label for label, _ in SEVERITY_WEIGHTS]
    severity_weights = [weight for _, weight in SEVERITY_WEIGHTS]

    rows: list[dict[str, object]] = []
    next_id = 1

    backlog_weights = list(range(1, config.backlog_history_months + 1))
    backlog_counts = allocate_counts(config.initial_backlog, backlog_weights)
    arrival_lower_bound = round(
        config.monthly_arrivals * (1 - config.arrival_variation)
    )
    arrival_upper_bound = round(
        config.monthly_arrivals * (1 + config.arrival_variation)
    )

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
                    "severity": rng.choices(
                        severity_labels, weights=severity_weights, k=1
                    )[0],
                    "created_at": random_timestamp_within_month(rng, month_anchor),
                    "resolved_at": None,
                    "created_month": month_anchor,
                    "source_cohort": "initial_backlog",
                    "is_initial_backlog": True,
                }
            )
            next_id += 1

    for month_offset, arrival_count in zip(range(config.months), schedule, strict=True):
        drawn_arrival_count = bounded_normal_int(
            rng=rng,
            mean=config.monthly_arrivals,
            stddev=config.monthly_arrivals * 0.07,
            lower_bound=arrival_lower_bound,
            upper_bound=arrival_upper_bound,
        )
        if drawn_arrival_count != arrival_count:
            raise ValueError("arrival_schedule does not match the deterministic RNG")
        month_anchor = add_months(config.start_month, month_offset)
        for _ in range(arrival_count):
            rows.append(
                {
                    "id": next_id,
                    "severity": rng.choices(
                        severity_labels, weights=severity_weights, k=1
                    )[0],
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


def write_output(df: pl.DataFrame) -> None:
    """Write the default Parquet artifact for the pipeline."""

    BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(BASE_PATH)
    print(f"Wrote {format_output_path(BASE_PATH)} ({df.height} rows)")


def print_arrival_summary(arrival_schedule: Sequence[int]) -> None:
    """Print a compact sanity summary for the shared arrival plan."""

    average_arrivals = sum(arrival_schedule) / len(arrival_schedule)
    print(
        "Arrival schedule: "
        f"avg={average_arrivals:.1f}/month "
        f"min={min(arrival_schedule)} "
        f"max={max(arrival_schedule)}"
    )


def main() -> None:
    """Generate the base dataset at the default pipeline path."""

    config = GenerationConfig()
    validate_config(config)
    arrival_schedule = monthly_arrival_schedule(config)
    print_arrival_summary(arrival_schedule)
    base_vulns = generate_base_vulnerabilities(config, arrival_schedule)
    write_output(base_vulns)


if __name__ == "__main__":
    main()
