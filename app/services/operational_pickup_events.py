"""Append ``pickups`` rows when riders request rides so analytics grow with app usage."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

from app.services.pickup_dataset_labels import nearest_seed_pickup_enrichment

logger = logging.getLogger(__name__)

PICKUPS_TABLE = "pickups"
FRUGER_APP_SOURCE = "fruger_app"
FRUGER_RIDE_DATA_SOURCE = "fruger_ride"


def _parse_ride_created_at(created_at: str) -> tuple[str, str, int]:
    """Return (pickup_datetime, pickup_date, pickup_hour UTC)."""
    s = created_at.strip()
    if "T" in s:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        try:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            dt = datetime.now(timezone.utc)
    dt = dt.astimezone(timezone.utc)
    pickup_date = dt.strftime("%Y-%m-%d")
    pickup_h = dt.hour
    disp = dt.strftime("%Y-%m-%d %H:%M:%S")
    return disp, pickup_date, pickup_h


def try_record_fruger_pickup_for_ride(
    conn: sqlite3.Connection,
    *,
    ride_id: int,
    pickup_lat: float,
    pickup_lng: float,
    created_at: str,
) -> None:
    """Insert one analytics pickup row for a new ride (no-op if ``pickups`` missing)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (PICKUPS_TABLE,),
    )
    if cur.fetchone() is None:
        return
    cur.execute("PRAGMA table_info(pickups)")
    if "source" not in {row[1] for row in cur.fetchall()}:
        return

    enrich = nearest_seed_pickup_enrichment(conn, pickup_lat, pickup_lng)
    zone = enrich["zone"] if enrich else None
    borough = enrich["borough"] if enrich else None
    base_code = "FRUGER"
    p_dt, p_date, p_hour = _parse_ride_created_at(created_at)

    try:
        cur.execute(
            f"""
            INSERT INTO {PICKUPS_TABLE} (
                pickup_datetime, pickup_date, pickup_hour, lat, lon,
                location_id, zone, borough, base_code, data_source, source
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                p_dt,
                p_date,
                p_hour,
                pickup_lat,
                pickup_lng,
                zone,
                borough,
                base_code,
                FRUGER_RIDE_DATA_SOURCE,
                FRUGER_APP_SOURCE,
            ),
        )
    except sqlite3.Error:
        logger.exception(
            "Failed to record Fruger pickup analytics for ride_id=%s", ride_id
        )
