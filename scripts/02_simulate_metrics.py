from __future__ import annotations

import calendar
from datetime import datetime
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_PATH = DATA_DIR / "base_vulns.parquet"
METRICS_PATH = DATA_DIR / "metrics.parquet"
SIMULATION_START_YEAR = 2024
SIMULATION_START_MONTH = 1
SIMULATION_MONTHS = 24
MONTHLY_FIX = 60


def month_end(value: datetime) -> datetime:
    last_day = calendar.monthrange(value.year, value.month)[1]
    return datetime(value.year, value.month, last_day, 23, 59, 59)


def add_month(year: int, month: int, delta: int = 1) -> tuple[int, int]:
    month += delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def simulation_months() -> list[datetime]:
    year = SIMULATION_START_YEAR
    month = SIMULATION_START_MONTH
    months = []

    for _ in range(SIMULATION_MONTHS):
        months.append(month_end(datetime(year, month, 1)))
        year, month = add_month(year, month)

    return months


def active_vulns(vulns: pl.DataFrame, as_of: datetime) -> pl.DataFrame:
    return vulns.filter(pl.col("created_at") <= as_of)


def select_to_fix(vulns: pl.DataFrame, n: int, strategy: str) -> pl.DataFrame:
    if vulns.is_empty():
        return vulns

    desc = strategy == "newest_first"

    return vulns.filter(pl.col("resolved_at").is_null()).sort(
        "created_at", descending=desc
    ).head(n)


def resolve_vulns(vulns: pl.DataFrame, ids: list[int], as_of: datetime) -> pl.DataFrame:
    if not ids:
        return vulns

    return vulns.with_columns(
        pl.when(pl.col("id").is_in(ids))
        .then(pl.lit(as_of))
        .otherwise(pl.col("resolved_at"))
        .alias("resolved_at")
    )


def compute_mttr(vulns: pl.DataFrame, as_of: datetime) -> float | None:
    closed = vulns.filter(
        pl.col("resolved_at").is_not_null() & (pl.col("resolved_at") <= as_of)
    ).with_columns(
        (pl.col("resolved_at") - pl.col("created_at")).dt.total_days().alias("days")
    )
    return None if closed.is_empty() else closed.select(pl.col("days").mean()).item()


def compute_mova(vulns: pl.DataFrame, as_of: datetime) -> float | None:
    open_vulns = active_vulns(vulns, as_of).filter(pl.col("resolved_at").is_null())
    aged = open_vulns.with_columns(
        (pl.lit(as_of) - pl.col("created_at")).dt.total_days().alias("age")
    )
    return None if aged.is_empty() else aged.select(pl.col("age").mean()).item()


def aged_backlog_count(vulns: pl.DataFrame, as_of: datetime, days: int = 180) -> int:
    return (
        active_vulns(vulns, as_of)
        .filter(pl.col("resolved_at").is_null())
        .with_columns((pl.lit(as_of) - pl.col("created_at")).dt.total_days().alias("age"))
        .filter(pl.col("age") >= days)
        .height
    )


def simulate(strategy: str, monthly_fix: int = MONTHLY_FIX) -> pl.DataFrame:
    base = pl.read_parquet(BASE_PATH)
    backlog = base.clone()
    rows = []

    for month_index, as_of in enumerate(simulation_months(), start=1):
        current = active_vulns(backlog, as_of)
        to_fix = select_to_fix(current, monthly_fix, strategy)
        backlog = resolve_vulns(backlog, to_fix.get_column("id").to_list(), as_of)

        current = active_vulns(backlog, as_of)
        mttr = compute_mttr(backlog, as_of)
        mova = compute_mova(backlog, as_of)

        rows.append(
            {
                "strategy": strategy,
                "month_index": month_index,
                "month": as_of,
                "mttr_days": mttr,
                "mova_days": mova,
                "open_count": current.filter(pl.col("resolved_at").is_null()).height,
                "aged_over_180": aged_backlog_count(backlog, as_of),
            }
        )

    return pl.DataFrame(rows)


def main() -> None:
    newest = simulate("newest_first")
    oldest = simulate("oldest_first")
    metrics = pl.concat([oldest, newest]).sort(["strategy", "month_index"])
    metrics.write_parquet(METRICS_PATH)
    print(f"Wrote {METRICS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
