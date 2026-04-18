"""Aggregates for admin dashboards."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app.schemas.operational import AdminStatsOut
from app.services.db_session import DBSession


class AdminService:
    def __init__(self, db: DBSession):
        self._db = db

    def overview_stats(self, conn: sqlite3.Connection) -> AdminStatsOut:
        by_status = self._db.count_rides_by_status(conn)
        return AdminStatsOut(
            total_rides=self._db.count_rides_total(conn),
            rides_by_status=by_status,
            completed_revenue_cents=self._db.sum_completed_revenue_cents(conn),
            total_bids=self._db.count_bids_total(conn),
        )

    def revenue_by_day(self, conn: sqlite3.Connection, days: int = 14) -> list[tuple[str, int]]:
        """Return (day_iso, revenue_cents) for completed rides in the last ``days`` days."""
        cur = conn.cursor()
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days - 1)
        cur.execute(
            """
            SELECT date(completed_at) AS d, COALESCE(SUM(final_fare_cents), 0)
            FROM rides
            WHERE status = 'completed' AND completed_at IS NOT NULL
              AND date(completed_at) >= date(?)
            GROUP BY date(completed_at)
            ORDER BY d
            """,
            (start.isoformat(),),
        )
        return [(str(row[0]), int(row[1])) for row in cur.fetchall()]
