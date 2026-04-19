"""SQLite schema migrations using ``PRAGMA user_version``."""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


def _get_user_version(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _set_user_version(conn: sqlite3.Connection, v: int) -> None:
    conn.execute(f"PRAGMA user_version = {int(v)}")


def migrate(conn: sqlite3.Connection) -> None:
    """Apply pending migrations in order."""
    v = _get_user_version(conn)
    if v < 1:
        _migrate_1_operational(conn)
        _set_user_version(conn, 1)
        v = 1
    if v != CURRENT_SCHEMA_VERSION:
        logger.warning(
            "Schema version %s is behind code version %s; migrations may need updating.",
            v,
            CURRENT_SCHEMA_VERSION,
        )


def migrate_db_path(db_path: Path) -> None:
    """Open SQLite at ``db_path`` and run migrations."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        migrate(conn)
        conn.commit()
    finally:
        conn.close()


def operational_tables_present(conn: sqlite3.Connection) -> bool:
    """Return True if all operational ride-hailing tables exist."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('users', 'rides', 'bids', 'driver_locations')
        """
    )
    found = {row[0] for row in cur.fetchall()}
    return found == {"users", "rides", "bids", "driver_locations"}


def _migrate_1_operational(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('rider', 'driver', 'admin')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rider_id INTEGER NOT NULL REFERENCES users(id),
            pickup_lat REAL NOT NULL,
            pickup_lng REAL NOT NULL,
            dropoff_lat REAL NOT NULL,
            dropoff_lng REAL NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('bidding_open', 'assigned', 'in_progress', 'completed', 'cancelled')
            ),
            accepted_bid_id INTEGER,
            final_fare_cents INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            cancelled_at TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
            driver_id INTEGER NOT NULL REFERENCES users(id),
            fare_cents INTEGER NOT NULL,
            distance_to_pickup_m REAL NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (ride_id, driver_id)
        );

        CREATE TABLE IF NOT EXISTS driver_locations (
            driver_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
        CREATE INDEX IF NOT EXISTS idx_rides_rider ON rides(rider_id);
        CREATE INDEX IF NOT EXISTS idx_bids_ride ON bids(ride_id);
        CREATE INDEX IF NOT EXISTS idx_bids_driver ON bids(driver_id);
        CREATE INDEX IF NOT EXISTS idx_rides_created ON rides(created_at);
        """
    )
