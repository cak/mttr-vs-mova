"""Simulate month-end vulnerability metrics under different work-ordering rules.

MTTR is computed from vulnerabilities resolved within each month. MOVA and open
count are month-end snapshots after that month's remediation work is applied
using a shared deterministic capacity schedule.
"""

from __future__ import annotations

import calendar
import random
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_PATH = DATA_DIR / "base_vulns.parquet"
METRICS_PATH = DATA_DIR / "metrics.parquet"

DEFAULT_START = date(2024, 1, 1)
DEFAULT_MONTHS = 24
DEFAULT_MONTHLY_CAPACITY = 60
DEFAULT_SEED = 20260426
DEFAULT_SEED_NAME = "talk_final_polish_v1"
DEFAULT_CAPACITY_VARIATION = 0.12
STRATEGIES: tuple[str, ...] = ("oldest_first", "newest_first")
CAPACITY_RHYTHM: tuple[float, ...] = (
    0.97,
    0.99,
    1.02,
    1.03,
    1.01,
    0.98,
    0.96,
    0.99,
    1.02,
    1.04,
    1.01,
    0.98,
)


@dataclass(frozen=True)
class MonthWindow:
    """A single simulation month."""

    index: int
    start: datetime
    end: datetime


@dataclass(frozen=True)
class SimulationConfig:
    """Parameters controlling the simulation horizon and remediation rate."""

    start_month: date = DEFAULT_START
    months: int = DEFAULT_MONTHS
    monthly_capacity: int = DEFAULT_MONTHLY_CAPACITY
    seed_name: str = DEFAULT_SEED_NAME
    seed: int = DEFAULT_SEED
    capacity_variation: float = DEFAULT_CAPACITY_VARIATION


def validate_config(config: SimulationConfig) -> None:
    """Fail fast on invalid simulation settings."""

    if config.months <= 0:
        raise ValueError("months must be positive")
    if config.monthly_capacity <= 0:
        raise ValueError("monthly_capacity must be positive")
    if not 0 < config.capacity_variation < 0.5:
        raise ValueError("capacity_variation must be between 0 and 0.5")


def add_months(value: date, delta: int) -> date:
    """Return the first day of the month shifted by `delta` months."""

    month_index = (value.year * 12 + value.month - 1) + delta
    year, month_offset = divmod(month_index, 12)
    return date(year, month_offset + 1, 1)


def month_window(start_month: date, month_index: int) -> MonthWindow:
    """Build a month window with inclusive start and end timestamps."""

    month_anchor = add_months(start_month, month_index - 1)
    start = datetime(month_anchor.year, month_anchor.month, 1)
    last_day = calendar.monthrange(month_anchor.year, month_anchor.month)[1]
    end = datetime(month_anchor.year, month_anchor.month, last_day, 23, 59, 59)
    return MonthWindow(index=month_index, start=start, end=end)


def simulation_windows(config: SimulationConfig) -> list[MonthWindow]:
    """Construct the sequence of month windows used for snapshots."""

    return [
        month_window(config.start_month, month_index)
        for month_index in range(1, config.months + 1)
    ]


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


def monthly_capacity_schedule(config: SimulationConfig) -> list[int]:
    """Build the explicit month-by-month capacity plan shared by both strategies."""

    rng = random.Random(config.seed)
    lower_bound = round(config.monthly_capacity * (1 - config.capacity_variation))
    upper_bound = round(config.monthly_capacity * (1 + config.capacity_variation))
    schedule: list[int] = []

    for month_index in range(config.months):
        rhythm = CAPACITY_RHYTHM[month_index % len(CAPACITY_RHYTHM)]
        schedule.append(
            bounded_normal_int(
                rng=rng,
                mean=config.monthly_capacity * rhythm,
                stddev=config.monthly_capacity * 0.03,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        )

    return schedule


def format_output_path(path: Path) -> str:
    """Return a stable display path for logs inside or outside the repo."""

    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_base_vulnerabilities(path: Path) -> pl.DataFrame:
    """Read the base dataset with the columns needed for the simulation."""

    return (
        pl.read_parquet(path)
        .select(
            "id",
            "created_at",
            "resolved_at",
            "severity",
            "created_month",
            "source_cohort",
            "is_initial_backlog",
        )
        .with_columns(
            pl.col("created_at").cast(pl.Datetime("us")),
            pl.col("resolved_at").cast(pl.Datetime("us")),
        )
        .sort(["created_at", "id"])
    )


def open_vulnerabilities(vulns: pl.DataFrame, as_of: datetime) -> pl.DataFrame:
    """Return findings created by `as_of` that are still open at that point."""

    return vulns.filter(
        (pl.col("created_at") <= pl.lit(as_of))
        & (pl.col("resolved_at").is_null() | (pl.col("resolved_at") > pl.lit(as_of)))
    )


def select_to_resolve(
    open_vulns: pl.DataFrame, strategy: str, monthly_capacity: int
) -> list[int]:
    """Choose which open findings to close this month.

    Only the ordering rule changes by strategy. Capacity and the candidate
    population are otherwise identical.
    """

    if open_vulns.is_empty():
        return []

    descending = strategy == "newest_first"
    return (
        open_vulns.sort(["created_at", "id"], descending=[descending, False])
        .head(monthly_capacity)
        .get_column("id")
        .to_list()
    )


def resolve_vulnerabilities(
    vulns: pl.DataFrame, vuln_ids: list[int], resolved_at: datetime
) -> pl.DataFrame:
    """Mark a set of vulnerabilities as resolved at the month-end timestamp."""

    if not vuln_ids:
        return vulns

    return vulns.with_columns(
        pl.when(pl.col("id").is_in(vuln_ids))
        .then(pl.lit(resolved_at))
        .otherwise(pl.col("resolved_at"))
        .alias("resolved_at")
    )


def compute_monthly_metrics(
    vulns: pl.DataFrame,
    strategy: str,
    window: MonthWindow,
) -> dict[str, object]:
    """Compute the flow and stock metrics for one month window."""

    closed_this_month = vulns.filter(
        pl.col("resolved_at").is_not_null()
        & (pl.col("resolved_at") >= pl.lit(window.start))
        & (pl.col("resolved_at") <= pl.lit(window.end))
    )
    open_as_of_month_end = open_vulnerabilities(vulns, window.end)

    # MTTR measures the age of closed work (flow); MOVA measures the age of the
    # open backlog at month end (stock).
    closed_with_age = closed_this_month.with_columns(
        (pl.col("resolved_at") - pl.col("created_at")).dt.total_days().alias("age_days")
    )
    open_with_age = open_as_of_month_end.with_columns(
        (pl.lit(window.end) - pl.col("created_at")).dt.total_days().alias("age_days")
    )

    mttr_days = (
        None
        if closed_with_age.is_empty()
        else closed_with_age.select(pl.col("age_days").mean()).item()
    )
    mova_days = (
        None
        if open_with_age.is_empty()
        else open_with_age.select(pl.col("age_days").mean()).item()
    )

    return {
        "strategy": strategy,
        "month_index": window.index,
        "month": window.end,
        "resolved_count": closed_this_month.height,
        "mttr_days": mttr_days,
        "mova_days": mova_days,
        "open_count": open_as_of_month_end.height,
    }


def simulate_strategy(
    base_vulns: pl.DataFrame,
    strategy: str,
    config: SimulationConfig,
    capacity_schedule: Sequence[int],
) -> pl.DataFrame:
    """Run the month-by-month simulation for a single prioritization strategy."""

    if strategy not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}")
    if len(capacity_schedule) != config.months:
        raise ValueError("capacity_schedule length must match config.months")

    working = base_vulns.clone()
    rows: list[dict[str, object]] = []

    for window, monthly_capacity in zip(
        simulation_windows(config), capacity_schedule, strict=True
    ):
        available_open = open_vulnerabilities(working, window.end)
        # The same capacity noise is shared across strategies so the only
        # strategic difference remains closure order.
        to_resolve = select_to_resolve(available_open, strategy, monthly_capacity)
        working = resolve_vulnerabilities(working, to_resolve, window.end)
        rows.append(compute_monthly_metrics(working, strategy, window))

    return pl.DataFrame(rows).sort(["strategy", "month_index"])


def print_validation_summary(
    capacity_schedule: Sequence[int], metrics: pl.DataFrame
) -> None:
    """Print a compact sanity summary for the shared capacity plan and end state."""

    average_capacity = sum(capacity_schedule) / len(capacity_schedule)
    print(
        "Capacity schedule: "
        f"avg={average_capacity:.1f}/month "
        f"min={min(capacity_schedule)} "
        f"max={max(capacity_schedule)}"
    )

    final_rows = (
        metrics.sort(["strategy", "month_index"])
        .group_by("strategy", maintain_order=True)
        .tail(1)
        .sort("strategy")
        .select("strategy", "mttr_days", "mova_days", "open_count")
    )

    for row in final_rows.iter_rows(named=True):
        print(
            f"{row['strategy']}: "
            f"MTTR={row['mttr_days']:.1f} "
            f"MOVA={row['mova_days']:.1f} "
            f"open={int(row['open_count'])}"
        )


def write_output(df: pl.DataFrame) -> None:
    """Write the default metrics dataset for the pipeline."""

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(METRICS_PATH)
    print(f"Wrote {format_output_path(METRICS_PATH)} ({df.height} rows)")


def main() -> None:
    """Run both strategy simulations and persist the monthly metrics."""

    config = SimulationConfig()
    validate_config(config)

    base_vulns = load_base_vulnerabilities(BASE_PATH)
    capacity_schedule = monthly_capacity_schedule(config)
    metrics = pl.concat(
        [
            simulate_strategy(base_vulns, strategy, config, capacity_schedule)
            for strategy in STRATEGIES
        ]
    ).sort(["strategy", "month_index"])
    print_validation_summary(capacity_schedule, metrics)
    write_output(metrics)


if __name__ == "__main__":
    main()
