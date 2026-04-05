from __future__ import annotations

import calendar
import random
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_PATH = DATA_DIR / "base_vulns.parquet"
SIMULATION_START_YEAR = 2024
SIMULATION_START_MONTH = 1
SIMULATION_MONTHS = 24
MONTHLY_NEW = 60
INITIAL_BACKLOG = 360
HISTORICAL_MONTHS = 12


def month_start(year: int, month: int) -> datetime:
    return datetime(year, month, 1)


def month_end(year: int, month: int) -> datetime:
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, last_day, 23, 59, 59)


def add_month(year: int, month: int, delta: int = 1) -> tuple[int, int]:
    month += delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def random_timestamp(rng: random.Random, year: int, month: int) -> datetime:
    start = month_start(year, month)
    last_day = month_end(year, month).day
    return start + timedelta(
        days=rng.randrange(last_day),
        hours=rng.randrange(8, 19),
        minutes=rng.randrange(0, 60),
    )


def generate_vulns(
    months: int = SIMULATION_MONTHS,
    monthly_new: int = MONTHLY_NEW,
    initial_backlog: int = INITIAL_BACKLOG,
    historical_months: int = HISTORICAL_MONTHS,
    seed: int = 42,
) -> pl.DataFrame:
    rng = random.Random(seed)

    severities = ["low", "medium", "high", "critical"]
    weights = [0.35, 0.35, 0.22, 0.08]

    rows = []
    vuln_id = 1

    year = SIMULATION_START_YEAR
    month = SIMULATION_START_MONTH

    per_month = initial_backlog // historical_months
    remainder = initial_backlog % historical_months

    for offset in range(historical_months, 0, -1):
        hist_year, hist_month = add_month(year, month, -offset)
        count = per_month + (1 if historical_months - offset < remainder else 0)

        for _ in range(count):
            rows.append(
                {
                    "id": vuln_id,
                    "severity": rng.choices(severities, weights=weights, k=1)[0],
                    "created_at": random_timestamp(rng, hist_year, hist_month),
                    "resolved_at": None,
                }
            )
            vuln_id += 1

    for _ in range(months):
        for _ in range(monthly_new):
            rows.append(
                {
                    "id": vuln_id,
                    "severity": rng.choices(severities, weights=weights, k=1)[0],
                    "created_at": random_timestamp(rng, year, month),
                    "resolved_at": None,
                }
            )
            vuln_id += 1

        year, month = add_month(year, month)

    return pl.DataFrame(rows)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df = generate_vulns()
    df.write_parquet(BASE_PATH)
    print(f"Wrote {BASE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
