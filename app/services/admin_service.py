"""Aggregates for admin dashboards."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from statistics import median

from app.schemas.admin_metrics import (
    AdminMetricsOut,
    BidMarketMetrics,
    CohortMetrics,
    DemandMetrics,
    DriverSnapshotMetrics,
    FunnelMetrics,
    LabeledCount,
    RevenueFareMetrics,
)
from app.schemas.operational import AdminStatsOut
from app.services.db_session import DBSession


class AdminService:
    def __init__(self, db: DBSession):
        self._db = db

    def overview_stats(self, conn: sqlite3.Connection) -> AdminStatsOut:
        by_status = self._db.count_rides_by_status(conn)
        rev_cents, rev_rides = self._db.completed_revenue_totals(conn)
        return AdminStatsOut(
            total_rides=self._db.count_rides_total(conn),
            rides_by_status=by_status,
            completed_revenue_cents=rev_cents,
            revenue_ride_count=rev_rides,
            total_bids=self._db.count_bids_total(conn),
            nyc_pickup_records=self._db.count_pickups_rows(conn),
        )

    def revenue_by_day(self, conn: sqlite3.Connection, days: int = 14) -> list[tuple[str, int]]:
        """Return (day_iso, revenue_cents) for completed rides in the last ``days`` days."""
        cur = conn.cursor()
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days - 1)
        cur.execute(
            """
            SELECT date(completed_at) AS d, COALESCE(SUM(final_fare_cents), 0)
            FROM live_rides
            WHERE status = 'completed' AND completed_at IS NOT NULL
              AND date(completed_at) >= date(?)
            GROUP BY date(completed_at)
            ORDER BY d
            """,
            (start.isoformat(),),
        )
        return [(str(row[0]), int(row[1])) for row in cur.fetchall()]

    @staticmethod
    def _rate(num: int, den: int) -> float:
        if den <= 0:
            return 0.0
        return float(num) / float(den)

    @staticmethod
    def _median_int(values: list[int]) -> int:
        if not values:
            return 0
        return int(round(float(median(values))))

    @staticmethod
    def _median_float(values: list[int]) -> float:
        if not values:
            return 0.0
        return float(median(values))

    def operational_metrics(self, conn: sqlite3.Connection) -> AdminMetricsOut:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pickups' LIMIT 1")
        has_pickups = cur.fetchone() is not None

        by_pickup_source: list[LabeledCount] = []
        by_pickup_hour: list[LabeledCount] = []
        by_pickup_date_last_30d: list[LabeledCount] = []
        top_bases: list[LabeledCount] = []
        top_geo_cells: list[LabeledCount] = []
        fruger_pickups_total = 0

        if has_pickups:
            cur.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(source), ''), '(unknown)') AS label, COUNT(*) AS c
                FROM pickups
                GROUP BY COALESCE(NULLIF(TRIM(source), ''), '(unknown)')
                ORDER BY c DESC
                """
            )
            by_pickup_source = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT printf('Hour %02d', pickup_hour) AS label, COUNT(*) AS c
                FROM pickups
                WHERE pickup_hour IS NOT NULL
                GROUP BY pickup_hour
                ORDER BY pickup_hour
                """
            )
            by_pickup_hour = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT pickup_date AS label, COUNT(*) AS c
                FROM pickups
                WHERE pickup_date IS NOT NULL
                  AND TRIM(pickup_date) != ''
                  AND date(pickup_date) >= date('now', '-30 day')
                GROUP BY pickup_date
                ORDER BY pickup_date
                """
            )
            by_pickup_date_last_30d = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(base_code), ''), '(unknown)') AS label, COUNT(*) AS c
                FROM pickups
                GROUP BY COALESCE(NULLIF(TRIM(base_code), ''), '(unknown)')
                ORDER BY c DESC
                LIMIT 10
                """
            )
            top_bases = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT printf('%.2f, %.2f', ROUND(lat, 2), ROUND(lon, 2)) AS label, COUNT(*) AS c
                FROM pickups
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                GROUP BY ROUND(lat, 2), ROUND(lon, 2)
                ORDER BY c DESC
                LIMIT 12
                """
            )
            top_geo_cells = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) FROM pickups WHERE source = 'fruger_app'")
            fruger_pickups_total = int(cur.fetchone()[0])

        demand = DemandMetrics(
            fruger_pickups_total=fruger_pickups_total,
            by_pickup_source=by_pickup_source,
            by_pickup_hour=by_pickup_hour,
            by_pickup_date_last_30d=by_pickup_date_last_30d,
            top_bases=top_bases,
            top_geo_cells=top_geo_cells,
        )

        cur.execute("SELECT status, COUNT(*) FROM live_rides GROUP BY status")
        status_counts = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        total_rides = sum(status_counts.values())
        completed = status_counts.get("completed", 0)
        cancelled = status_counts.get("cancelled", 0)
        assigned = status_counts.get("assigned", 0)
        in_progress = status_counts.get("in_progress", 0)
        bidding_open = status_counts.get("bidding_open", 0)
        funnel = FunnelMetrics(
            total_rides=total_rides,
            bidding_open=bidding_open,
            assigned=assigned,
            in_progress=in_progress,
            completed=completed,
            cancelled=cancelled,
            assign_rate=self._rate(assigned + in_progress + completed, total_rides),
            completion_rate=self._rate(completed, total_rides),
            cancellation_rate=self._rate(cancelled, total_rides),
        )

        cur.execute(
            """
            SELECT final_fare_cents
            FROM live_rides
            WHERE status = 'completed' AND final_fare_cents IS NOT NULL
            ORDER BY final_fare_cents
            """
        )
        completed_fares = [int(r[0]) for r in cur.fetchall()]
        completed_revenue_cents = int(sum(completed_fares))
        completed_rides_with_fare = len(completed_fares)
        avg_completed_fare_cents = (
            int(round(completed_revenue_cents / completed_rides_with_fare))
            if completed_rides_with_fare
            else 0
        )
        median_completed_fare_cents = self._median_int(completed_fares)

        cur.execute("SELECT fare_cents FROM bids WHERE status = 'accepted' ORDER BY fare_cents")
        accepted_bid_fares = [int(r[0]) for r in cur.fetchall()]
        accepted_bid_count = len(accepted_bid_fares)
        avg_accepted_bid_cents = (
            int(round(sum(accepted_bid_fares) / accepted_bid_count)) if accepted_bid_count else 0
        )
        median_accepted_bid_cents = self._median_int(accepted_bid_fares)

        cur.execute(
            """
            SELECT r.final_fare_cents - b.fare_cents AS delta
            FROM live_rides r
            JOIN bids b ON b.id = r.accepted_bid_id
            WHERE r.status = 'completed'
              AND r.final_fare_cents IS NOT NULL
              AND b.fare_cents IS NOT NULL
            """
        )
        deltas = [int(r[0]) for r in cur.fetchall()]
        paired_completed_with_accepted_bid = len(deltas)
        avg_final_minus_accepted_cents = (
            int(round(sum(deltas) / paired_completed_with_accepted_bid))
            if paired_completed_with_accepted_bid
            else 0
        )

        revenue_fares = RevenueFareMetrics(
            completed_revenue_cents=completed_revenue_cents,
            completed_rides_with_fare=completed_rides_with_fare,
            avg_completed_fare_cents=avg_completed_fare_cents,
            median_completed_fare_cents=median_completed_fare_cents,
            accepted_bid_count=accepted_bid_count,
            avg_accepted_bid_cents=avg_accepted_bid_cents,
            median_accepted_bid_cents=median_accepted_bid_cents,
            paired_completed_with_accepted_bid=paired_completed_with_accepted_bid,
            avg_final_minus_accepted_cents=avg_final_minus_accepted_cents,
        )

        cur.execute("SELECT COUNT(*) FROM bids")
        total_bids = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(DISTINCT ride_id) FROM bids")
        rides_with_bids = int(cur.fetchone()[0])
        rides_with_zero_bids = max(0, total_rides - rides_with_bids)
        cur.execute(
            """
            SELECT ride_id, COUNT(*) AS c
            FROM bids
            GROUP BY ride_id
            ORDER BY ride_id
            """
        )
        bids_per_ride = [int(r[1]) for r in cur.fetchall()]
        avg_bids_per_ride = float(total_bids) / float(total_rides) if total_rides else 0.0
        median_bids_per_ride = self._median_float(bids_per_ride)

        cur.execute(
            """
            SELECT status, COUNT(*) AS c
            FROM bids
            GROUP BY status
            """
        )
        bid_status_counts = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        accepted_bids = bid_status_counts.get("accepted", 0)
        rejected_bids = bid_status_counts.get("rejected", 0)
        pending_bids = bid_status_counts.get("pending", 0)
        cur.execute("SELECT COUNT(DISTINCT driver_id) FROM bids")
        distinct_bidding_drivers = int(cur.fetchone()[0])

        bid_market = BidMarketMetrics(
            total_bids=total_bids,
            rides_with_bids=rides_with_bids,
            rides_with_zero_bids=rides_with_zero_bids,
            avg_bids_per_ride=avg_bids_per_ride,
            median_bids_per_ride=median_bids_per_ride,
            accepted_bids=accepted_bids,
            rejected_bids=rejected_bids,
            pending_bids=pending_bids,
            bid_acceptance_rate=self._rate(accepted_bids, total_bids),
            distinct_bidding_drivers=distinct_bidding_drivers,
        )

        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'driver'")
        total_driver_accounts = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM driver_locations")
        drivers_with_location = int(cur.fetchone()[0])
        cur.execute(
            """
            SELECT COUNT(*) FROM driver_locations
            WHERE datetime(updated_at) >= datetime('now', '-15 minutes')
            """
        )
        drivers_active_last_15m = int(cur.fetchone()[0])
        cur.execute(
            """
            SELECT COUNT(*) FROM driver_locations
            WHERE datetime(updated_at) >= datetime('now', '-60 minutes')
            """
        )
        drivers_active_last_60m = int(cur.fetchone()[0])

        driver_snapshot = DriverSnapshotMetrics(
            total_driver_accounts=total_driver_accounts,
            drivers_with_location=drivers_with_location,
            drivers_active_last_15m=drivers_active_last_15m,
            drivers_active_last_60m=drivers_active_last_60m,
        )

        cur.execute(
            """
            SELECT role AS label, COUNT(*) AS c
            FROM users
            GROUP BY role
            ORDER BY c DESC, role
            """
        )
        users_by_role = [LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(u.email, printf('rider#%d', r.rider_id)) AS label, COUNT(*) AS c
            FROM live_rides r
            LEFT JOIN users u ON u.id = r.rider_id
            GROUP BY r.rider_id
            ORDER BY c DESC, label
            LIMIT 10
            """
        )
        top_riders_by_ride_count = [
            LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT COALESCE(u.email, printf('driver#%d', b.driver_id)) AS label, COUNT(*) AS c
            FROM bids b
            LEFT JOIN users u ON u.id = b.driver_id
            GROUP BY b.driver_id
            ORDER BY c DESC, label
            LIMIT 10
            """
        )
        top_drivers_by_bid_count = [
            LabeledCount(label=str(r[0]), count=int(r[1])) for r in cur.fetchall()
        ]

        cohorts = CohortMetrics(
            users_by_role=users_by_role,
            top_riders_by_ride_count=top_riders_by_ride_count,
            top_drivers_by_bid_count=top_drivers_by_bid_count,
        )

        return AdminMetricsOut(
            demand=demand,
            funnel=funnel,
            revenue_fares=revenue_fares,
            bid_market=bid_market,
            driver_snapshot=driver_snapshot,
            cohorts=cohorts,
        )
