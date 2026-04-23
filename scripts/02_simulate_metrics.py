"""Simulate month-end vulnerability metrics under different work-ordering rules.

MTTR is computed from vulnerabilities resolved within each month. MOVA, open
count, and 180+ tail are month-end snapshots after that month's remediation
work is applied.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_PATH = DATA_DIR / "base_vulns.parquet"
METRICS_PATH = DATA_DIR / "metrics.parquet"

DEFAULT_START = date(2024, 1, 1)
DEFAULT_MONTHS = 24
DEFAULT_MONTHLY_CAPACITY = 60
DEFAULT_TAIL_DAYS = 180
STRATEGIES: tuple[str, ...] = ("oldest_first", "newest_first")


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
    tail_days: int = DEFAULT_TAIL_DAYS


def validate_config(config: SimulationConfig) -> None:
    """Fail fast on invalid simulation settings."""

    if config.months <= 0:
        raise ValueError("months must be positive")
    if config.monthly_capacity <= 0:
        raise ValueError("monthly_capacity must be positive")
    if config.tail_days <= 0:
        raise ValueError("tail_days must be positive")


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
    tail_days: int,
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
    # The `aged_over_180` column name stays fixed even when the threshold moves.
    aged_over_tail = (
        0
        if open_with_age.is_empty()
        else open_with_age.filter(pl.col("age_days") >= tail_days).height
    )

    return {
        "strategy": strategy,
        "month_index": window.index,
        "month": window.end,
        "resolved_count": closed_this_month.height,
        "mttr_days": mttr_days,
        "mova_days": mova_days,
        "open_count": open_as_of_month_end.height,
        "aged_over_180": aged_over_tail,
    }


def simulate_strategy(
    base_vulns: pl.DataFrame, strategy: str, config: SimulationConfig
) -> pl.DataFrame:
    """Run the month-by-month simulation for a single prioritization strategy."""

    if strategy not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}")

    working = base_vulns.clone()
    rows: list[dict[str, object]] = []

    for window in simulation_windows(config):
        available_open = open_vulnerabilities(working, window.end)
        to_resolve = select_to_resolve(
            available_open, strategy, config.monthly_capacity
        )
        working = resolve_vulnerabilities(working, to_resolve, window.end)
        rows.append(
            compute_monthly_metrics(working, strategy, window, config.tail_days)
        )

    return pl.DataFrame(rows).sort(["strategy", "month_index"])


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
    metrics = pl.concat(
        [simulate_strategy(base_vulns, strategy, config) for strategy in STRATEGIES]
    ).sort(["strategy", "month_index"])
    write_output(metrics)


if __name__ == "__main__":
    main()
