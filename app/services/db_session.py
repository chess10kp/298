"""SQLite access layer for operational tables."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.schemas.operational import BidStatus, RideStatus, UserRole


class DBSession:
    """Thin repository over SQLite for users, rides, bids, driver locations."""

    def __init__(self, db_path: Path):
        self._path = db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- users ---
    def get_user_by_id(
        self, conn: sqlite3.Connection, user_id: int
    ) -> dict[str, Any] | None:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, role, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_user_by_email(
        self, conn: sqlite3.Connection, email: str
    ) -> dict[str, Any] | None:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, role, created_at FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip().lower(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def insert_user(
        self,
        conn: sqlite3.Connection,
        *,
        email: str,
        password_hash: str,
        role: UserRole,
    ) -> int:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email.strip().lower(), password_hash, role.value),
        )
        return int(cur.lastrowid)

    # --- rides ---
    def insert_ride(
        self,
        conn: sqlite3.Connection,
        *,
        rider_id: int,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float,
        status: RideStatus = RideStatus.bidding_open,
    ) -> int:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO rides (rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rider_id,
                pickup_lat,
                pickup_lng,
                dropoff_lat,
                dropoff_lng,
                status.value,
            ),
        )
        return int(cur.lastrowid)

    def get_ride(self, conn: sqlite3.Connection, ride_id: int) -> dict[str, Any] | None:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng,
                   status, accepted_bid_id, final_fare_cents, created_at, cancelled_at, completed_at
            FROM rides WHERE id = ?
            """,
            (ride_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def list_rides_for_rider(
        self, conn: sqlite3.Connection, rider_id: int
    ) -> list[dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng,
                   status, accepted_bid_id, final_fare_cents, created_at, cancelled_at, completed_at
            FROM rides WHERE rider_id = ? ORDER BY id DESC
            """,
            (rider_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def list_rides_with_status(
        self, conn: sqlite3.Connection, status: RideStatus
    ) -> list[dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng,
                   status, accepted_bid_id, final_fare_cents, created_at, cancelled_at, completed_at
            FROM rides WHERE status = ? ORDER BY id DESC
            """,
            (status.value,),
        )
        return [dict(r) for r in cur.fetchall()]

    def update_ride(
        self,
        conn: sqlite3.Connection,
        ride_id: int,
        *,
        status: RideStatus | None = None,
        accepted_bid_id: int | None = None,
        final_fare_cents: int | None = None,
        cancelled_at: str | None = None,
        completed_at: str | None = None,
    ) -> None:
        fields: list[str] = []
        vals: list[Any] = []
        if status is not None:
            fields.append("status = ?")
            vals.append(status.value)
        if accepted_bid_id is not None:
            fields.append("accepted_bid_id = ?")
            vals.append(accepted_bid_id)
        if final_fare_cents is not None:
            fields.append("final_fare_cents = ?")
            vals.append(final_fare_cents)
        if cancelled_at is not None:
            fields.append("cancelled_at = ?")
            vals.append(cancelled_at)
        if completed_at is not None:
            fields.append("completed_at = ?")
            vals.append(completed_at)
        if not fields:
            return
        vals.append(ride_id)
        conn.execute(f"UPDATE rides SET {', '.join(fields)} WHERE id = ?", vals)

    # --- bids ---
    def upsert_bid(
        self,
        conn: sqlite3.Connection,
        *,
        ride_id: int,
        driver_id: int,
        fare_cents: int,
        distance_to_pickup_m: float,
        status: BidStatus = BidStatus.pending,
    ) -> int:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bids (ride_id, driver_id, fare_cents, distance_to_pickup_m, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (ride_id, driver_id) DO UPDATE SET
                fare_cents = excluded.fare_cents,
                distance_to_pickup_m = excluded.distance_to_pickup_m,
                status = excluded.status,
                created_at = datetime('now')
            """,
            (
                ride_id,
                driver_id,
                fare_cents,
                distance_to_pickup_m,
                status.value,
            ),
        )
        cur.execute(
            "SELECT id FROM bids WHERE ride_id = ? AND driver_id = ?",
            (ride_id, driver_id),
        )
        row = cur.fetchone()
        return int(row[0]) if row else int(cur.lastrowid)

    def list_bids_for_ride(
        self, conn: sqlite3.Connection, ride_id: int
    ) -> list[dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, ride_id, driver_id, fare_cents, distance_to_pickup_m, status, created_at
            FROM bids WHERE ride_id = ? ORDER BY fare_cents ASC, id ASC
            """,
            (ride_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def list_bidder_locations_for_ride(
        self, conn: sqlite3.Connection, ride_id: int
    ) -> list[dict[str, Any]]:
        """Pending bidders on a ride with a known last GPS fix (for rider map pins)."""
        cur = conn.cursor()
        cur.execute(
            """
            SELECT b.driver_id AS driver_id, dl.lat AS lat, dl.lng AS lng
            FROM bids b
            INNER JOIN driver_locations dl ON dl.driver_id = b.driver_id
            WHERE b.ride_id = ? AND b.status = ?
            ORDER BY b.driver_id
            """,
            (ride_id, BidStatus.pending.value),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_bid(self, conn: sqlite3.Connection, bid_id: int) -> dict[str, Any] | None:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, ride_id, driver_id, fare_cents, distance_to_pickup_m, status, created_at
            FROM bids WHERE id = ?
            """,
            (bid_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def reject_other_bids(
        self, conn: sqlite3.Connection, ride_id: int, accepted_bid_id: int
    ) -> None:
        conn.execute(
            """
            UPDATE bids SET status = ? WHERE ride_id = ? AND id != ? AND status = ?
            """,
            (
                BidStatus.rejected.value,
                ride_id,
                accepted_bid_id,
                BidStatus.pending.value,
            ),
        )

    def accept_bid_row(self, conn: sqlite3.Connection, bid_id: int) -> None:
        conn.execute(
            "UPDATE bids SET status = ? WHERE id = ?",
            (BidStatus.accepted.value, bid_id),
        )

    def expire_stale_bids(
        self, conn: sqlite3.Connection, older_than_minutes: int = 10
    ) -> int:
        """Mark bids older than `older_than_minutes` as rejected/expired and return count."""
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM bids WHERE status = ? AND datetime(created_at) <= datetime('now', ?)",
            (BidStatus.pending.value, f"-{older_than_minutes} minutes"),
        )
        rows = cur.fetchall()
        ids = [int(r[0]) for r in rows]
        if not ids:
            return 0
        cur.execute(
            "UPDATE bids SET status = ? WHERE id IN (%s)" % ",".join(["?"] * len(ids)),
            [BidStatus.rejected.value] + ids,
        )
        return len(ids)

    # --- driver_locations ---
    def upsert_driver_location(
        self, conn: sqlite3.Connection, driver_id: int, lat: float, lng: float
    ) -> None:
        conn.execute(
            """
            INSERT INTO driver_locations (driver_id, lat, lng, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT (driver_id) DO UPDATE SET
                lat = excluded.lat,
                lng = excluded.lng,
                updated_at = datetime('now')
            """,
            (driver_id, lat, lng),
        )

    def get_driver_location(
        self, conn: sqlite3.Connection, driver_id: int
    ) -> dict[str, Any] | None:
        cur = conn.cursor()
        cur.execute(
            "SELECT driver_id, lat, lng, updated_at FROM driver_locations WHERE driver_id = ?",
            (driver_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def list_driver_locations_with_email(
        self, conn: sqlite3.Connection
    ) -> list[dict[str, Any]]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT dl.driver_id AS driver_id, u.email AS email,
                   dl.lat AS lat, dl.lng AS lng, dl.updated_at AS updated_at
            FROM driver_locations dl
            JOIN users u ON u.id = dl.driver_id
            ORDER BY dl.updated_at DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]

    # --- admin aggregates ---
    def count_rides_total(self, conn: sqlite3.Connection) -> int:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM rides")
        return int(cur.fetchone()[0])

    def count_rides_by_status(self, conn: sqlite3.Connection) -> dict[str, int]:
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM rides GROUP BY status")
        return {str(row[0]): int(row[1]) for row in cur.fetchall()}

    def sum_completed_revenue_cents(self, conn: sqlite3.Connection) -> int:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(SUM(final_fare_cents), 0) FROM rides
            WHERE status = ? AND final_fare_cents IS NOT NULL
            """,
            (RideStatus.completed.value,),
        )
        return int(cur.fetchone()[0])

    def count_bids_total(self, conn: sqlite3.Connection) -> int:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM bids")
        return int(cur.fetchone()[0])
