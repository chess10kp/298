"""SQLite schema migrations using ``PRAGMA user_version``."""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 5


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
    if v < 2:
        _migrate_2_pickups_source(conn)
        _set_user_version(conn, 2)
        v = 2
    if v < 3:
        _migrate_3_dual_completion(conn)
        _set_user_version(conn, 3)
        v = 3
    if v < 4:
        _migrate_4_pickups_lat_lon_index(conn)
        _set_user_version(conn, 4)
        v = 4
    if v < 5:
        _migrate_5_ride_location_labels(conn)
        _set_user_version(conn, 5)
        v = 5
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
    """Return True if all Fruger operational tables exist."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('users', 'live_rides', 'bids', 'driver_locations')
        """
    )
    found = {row[0] for row in cur.fetchall()}
    return found == {"users", "live_rides", "bids", "driver_locations"}


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

        CREATE TABLE IF NOT EXISTS live_rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rider_id INTEGER NOT NULL REFERENCES users(id),
            pickup_lat REAL NOT NULL,
            pickup_lng REAL NOT NULL,
            dropoff_lat REAL NOT NULL,
            dropoff_lng REAL NOT NULL,
            pickup_location TEXT,
            dropoff_location TEXT,
            status TEXT NOT NULL CHECK (
                status IN ('bidding_open', 'assigned', 'in_progress', 'completed', 'cancelled')
            ),
            accepted_bid_id INTEGER,
            final_fare_cents INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            cancelled_at TEXT,
            completed_at TEXT
        );

        -- Admin-only seeded/archival rides (kept separate from live rider/driver flow).
        CREATE TABLE IF NOT EXISTS seed_rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rider_id INTEGER,
            pickup_lat REAL NOT NULL,
            pickup_lng REAL NOT NULL,
            dropoff_lat REAL NOT NULL,
            dropoff_lng REAL NOT NULL,
            status TEXT,
            accepted_bid_id INTEGER,
            final_fare_cents INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            cancelled_at TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL REFERENCES live_rides(id) ON DELETE CASCADE,
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

        CREATE INDEX IF NOT EXISTS idx_live_rides_status ON live_rides(status);
        CREATE INDEX IF NOT EXISTS idx_live_rides_rider ON live_rides(rider_id);
        CREATE INDEX IF NOT EXISTS idx_live_rides_created ON live_rides(created_at);
        CREATE INDEX IF NOT EXISTS idx_live_rides_status_id ON live_rides(status, id DESC);
        CREATE INDEX IF NOT EXISTS idx_bids_ride ON bids(ride_id);
        CREATE INDEX IF NOT EXISTS idx_bids_driver ON bids(driver_id);
        CREATE INDEX IF NOT EXISTS idx_seed_rides_status ON seed_rides(status);
        CREATE INDEX IF NOT EXISTS idx_seed_rides_created ON seed_rides(created_at);
        """
    )


def _migrate_2_pickups_source(conn: sqlite3.Connection) -> None:
    """Tag TLC seed rows vs Fruger app pickup events (``pickups.source``)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pickups' LIMIT 1"
    )
    if cur.fetchone() is None:
        return
    cur.execute("PRAGMA table_info(pickups)")
    cols = {row[1] for row in cur.fetchall()}
    if "source" not in cols:
        conn.execute(
            "ALTER TABLE pickups ADD COLUMN source TEXT DEFAULT 'nyc_dataset'"
        )


def _migrate_3_dual_completion(conn: sqlite3.Connection) -> None:
    """Driver and rider must both confirm before status becomes completed."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(live_rides)")
    cols = {row[1] for row in cur.fetchall()}
    if "driver_marked_complete_at" not in cols:
        conn.execute(
            "ALTER TABLE live_rides ADD COLUMN driver_marked_complete_at TEXT"
        )
    if "rider_marked_complete_at" not in cols:
        conn.execute(
            "ALTER TABLE live_rides ADD COLUMN rider_marked_complete_at TEXT"
        )
    conn.execute(
        """
        UPDATE live_rides
        SET driver_marked_complete_at = completed_at,
            rider_marked_complete_at = completed_at
        WHERE status = 'completed'
          AND completed_at IS NOT NULL
          AND driver_marked_complete_at IS NULL
        """
    )


def _migrate_4_pickups_lat_lon_index(conn: sqlite3.Connection) -> None:
    """Add spatial index on pickups(lat, lon) to speed up nearest-neighbor queries."""
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pickups' LIMIT 1"
    )
    if cur.fetchone() is None:
        return
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pickups_lat_lon ON pickups(lat, lon)")


def _migrate_5_ride_location_labels(conn: sqlite3.Connection) -> None:
    """Store pickup/dropoff location labels directly on live_rides."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(live_rides)")
    cols = {row[1] for row in cur.fetchall()}
    if "pickup_location" not in cols:
        conn.execute("ALTER TABLE live_rides ADD COLUMN pickup_location TEXT")
    if "dropoff_location" not in cols:
        conn.execute("ALTER TABLE live_rides ADD COLUMN dropoff_location TEXT")
