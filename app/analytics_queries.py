"""SQLite aggregations for NYC TLC Uber pickup rows (``pickups`` table)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.schemas.analytics import CountByLabel, NycOverviewResponse, PickupTotals


def _friendly_pickup_source(raw: str) -> str:
    """Map ``pickups.source`` values to short UI labels."""
    key = (raw or "").strip()
    return {
        "nyc_dataset": "TLC seed (Kaggle / FiveThirtyEight)",
        "fruger_app": "Fruger ride requests (live)",
    }.get(key, key or "(Unknown source)")


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_overview(db_path: Path, top_n: int = 8) -> NycOverviewResponse:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM pickups")
        total = int(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COUNT(*) FROM pickups
            WHERE lat IS NOT NULL AND lon IS NOT NULL
              AND lat BETWEEN 35 AND 45 AND lon BETWEEN -80 AND -70
            """
        )
        with_latlon = int(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COUNT(*) FROM pickups
            WHERE zone IS NOT NULL AND TRIM(zone) != ''
            """
        )
        with_zone = int(cur.fetchone()[0])

        cur.execute("SELECT COUNT(DISTINCT TRIM(base_code)) FROM pickups WHERE TRIM(base_code) != ''")
        distinct_bases = int(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(source), ''), '(Unknown source)') AS label,
                   COUNT(*) AS c
            FROM pickups
            GROUP BY COALESCE(NULLIF(TRIM(source), ''), '(Unknown source)')
            ORDER BY c DESC
            """
        )
        by_pickup_source = [
            CountByLabel(label=_friendly_pickup_source(str(r["label"])), count=int(r["c"]))
            for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(borough), ''), '(Unknown borough)') AS label,
                   COUNT(*) AS c
            FROM pickups
            GROUP BY COALESCE(NULLIF(TRIM(borough), ''), '(Unknown borough)')
            ORDER BY c DESC
            LIMIT ?
            """,
            (top_n + 20,),
        )
        by_borough = [CountByLabel(label=r["label"], count=int(r["c"])) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(base_code), ''), '(Unknown base)') AS label,
                   COUNT(*) AS c
            FROM pickups
            GROUP BY TRIM(base_code)
            ORDER BY c DESC
            LIMIT ?
            """,
            (top_n + 20,),
        )
        by_base = [CountByLabel(label=r["label"], count=int(r["c"])) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT printf('Hour %02d', pickup_hour) AS label,
                   COUNT(*) AS c
            FROM pickups
            WHERE pickup_hour IS NOT NULL
            GROUP BY pickup_hour
            ORDER BY pickup_hour
            """
        )
        by_hour = [CountByLabel(label=r["label"], count=int(r["c"])) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(zone), ''), '(No zone)') AS label,
                   COUNT(*) AS c
            FROM pickups
            WHERE zone IS NOT NULL AND TRIM(zone) != ''
            GROUP BY TRIM(zone)
            ORDER BY c DESC
            LIMIT ?
            """,
            (top_n,),
        )
        top_zones = [CountByLabel(label=r["label"], count=int(r["c"])) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT data_source AS label, COUNT(*) AS c
            FROM pickups
            GROUP BY data_source
            ORDER BY label
            """
        )
        by_data_source = [
            CountByLabel(label=r["label"] or "(unknown)", count=int(r["c"])) for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT pickup_date AS label, COUNT(*) AS c
            FROM pickups
            WHERE pickup_date IS NOT NULL AND TRIM(pickup_date) != ''
            GROUP BY pickup_date
            ORDER BY pickup_date
            LIMIT 120
            """
        )
        pickups_by_date = [CountByLabel(label=r["label"], count=int(r["c"])) for r in cur.fetchall()]

        totals = PickupTotals(
            total_pickups=total,
            pickups_with_latlon=with_latlon,
            pickups_with_zone=with_zone,
            distinct_bases=distinct_bases,
        )

        return NycOverviewResponse(
            totals=totals,
            by_pickup_source=by_pickup_source,
            by_borough=by_borough,
            by_base=by_base,
            by_hour=by_hour,
            top_zones=top_zones,
            by_data_source=by_data_source,
            pickups_by_date=pickups_by_date,
        )
    finally:
        conn.close()
