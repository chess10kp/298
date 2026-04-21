"""Resolve ride coordinates to labels from the NYC TLC ``pickups`` dataset table."""

from __future__ import annotations

import sqlite3

from app.schemas.operational import RideOut
from app.services.reverse_geocode import nominatim_cached_label

_PICKUPS = "pickups"
# TLC CSV seed rows (``fruger_app`` rows are synthetic and must not anchor lookups).
_SEED_FILTER = " AND (source IS NULL OR source = 'nyc_dataset') "

_seed_filter_cache: dict[str, str] = {}


def _seed_filter_sql(conn: sqlite3.Connection) -> str:
    db_path = conn.execute("PRAGMA database_list").fetchone()[2] or ""
    cached = _seed_filter_cache.get(db_path)
    if cached is not None:
        return cached
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(pickups)")
        if "source" not in {r[1] for r in cur.fetchall()}:
            _seed_filter_cache[db_path] = ""
            return ""
    except sqlite3.Error:
        _seed_filter_cache[db_path] = ""
        return ""
    _seed_filter_cache[db_path] = _SEED_FILTER
    return _SEED_FILTER


def _pickups_table_ready(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (_PICKUPS,),
    )
    return cur.fetchone() is not None


def _format_row_label(zone: object, borough: object, base_code: object) -> str | None:
    z = str(zone).strip() if zone is not None else ""
    b = str(borough).strip() if borough is not None else ""
    bc = str(base_code).strip() if base_code is not None else ""
    if z and b and b.lower() not in z.lower():
        return f"{z} ({b})"
    if z:
        return z
    if b:
        return b
    return None


def nearest_pickup_location_label(conn: sqlite3.Connection, lat: float, lng: float) -> str | None:
    """Pick the closest **seed** ``pickups`` row by Euclidean distance on lat/lon."""
    if not _pickups_table_ready(conn):
        return None
    cur = conn.cursor()
    # Widen the search box so we avoid a full-table scan on large seeds.
    filt = _seed_filter_sql(conn)
    for delta in (0.02, 0.06, 0.15, 0.4):
        lo_lat, hi_lat = lat - delta, lat + delta
        lo_lng, hi_lng = lng - delta, lng + delta
        try:
            cur.execute(
                f"""
                SELECT zone, borough, base_code,
                       ((lat - ?) * (lat - ?) + (lon - ?) * (lon - ?)) AS d2
                FROM {_PICKUPS}
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                  {filt}
                  AND lat BETWEEN ? AND ?
                  AND lon BETWEEN ? AND ?
                ORDER BY d2
                LIMIT 1
                """,
                (lat, lat, lng, lng, lo_lat, hi_lat, lo_lng, hi_lng),
            )
        except sqlite3.Error:
            return None
        row = cur.fetchone()
        if row is not None:
            return _format_row_label(row["zone"], row["borough"], row["base_code"])
    return None


def nearest_seed_pickup_enrichment(
    conn: sqlite3.Connection, lat: float, lng: float
) -> dict[str, str | None] | None:
    """Nearest TLC seed row for zone/borough hints on Fruger pickup events."""
    if not _pickups_table_ready(conn):
        return None
    cur = conn.cursor()
    filt = _seed_filter_sql(conn)
    for delta in (0.02, 0.06, 0.15, 0.4):
        lo_lat, hi_lat = lat - delta, lat + delta
        lo_lng, hi_lng = lng - delta, lng + delta
        try:
            cur.execute(
                f"""
                SELECT zone, borough
                FROM {_PICKUPS}
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                  {filt}
                  AND lat BETWEEN ? AND ?
                  AND lon BETWEEN ? AND ?
                ORDER BY ((lat - ?) * (lat - ?) + (lon - ?) * (lon - ?))
                LIMIT 1
                """,
                (lo_lat, hi_lat, lo_lng, hi_lng, lat, lat, lng, lng),
            )
        except sqlite3.Error:
            return None
        row = cur.fetchone()
        if row is not None:
            z = row["zone"]
            b = row["borough"]
            return {
                "zone": str(z).strip() if z is not None else None,
                "borough": str(b).strip() if b is not None else None,
            }
    return None


def _resolve_label(conn: sqlite3.Connection, lat: float, lng: float) -> str | None:
    """Try the pickups dataset first, then check the Nominatim cache.

    Does NOT make a network call — the client-side ``enrichRidePlaceLabels``
    triggers ``/api/v1/geocode/reverse-batch`` which populates the cache for
    subsequent requests.
    """
    label = nearest_pickup_location_label(conn, lat, lng)
    if label is not None:
        return label
    return nominatim_cached_label(lat, lng)


def attach_pickup_dataset_labels(conn: sqlite3.Connection, ride: RideOut) -> RideOut:
    pl = _resolve_label(conn, ride.pickup_lat, ride.pickup_lng)
    dl = _resolve_label(conn, ride.dropoff_lat, ride.dropoff_lng)
    return ride.model_copy(update={"pickup_location": pl, "dropoff_location": dl})
