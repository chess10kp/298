"""Rich demo data for empty databases: realistic users, GPS, bids, and rides in every lifecycle state."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

import app.config as app_config
from passlib.context import CryptContext

from app.schemas.operational import BidStatus, RideStatus, UserRole
from app.services.db_session import DBSession
from app.services.geo import haversine_m
from app.services.operational_pickup_events import try_record_fruger_pickup_for_ride

logger = logging.getLogger(__name__)

_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

_DEMO_PASSWORD = "FrugerDemo2024!"

# Realistic-looking accounts (all share _DEMO_PASSWORD for QA).
_RIDER_EMAILS: tuple[str, ...] = (
    "maria.garcia.work@outlook.com",
    "james.chen.nyc@gmail.com",
    "olivia.brown.design@proton.me",
    "damian.okonkwo@icloud.com",
    "sophia.rivera.events@me.com",
    "alex.kim.brooklyn@gmail.com",
)

_DRIVER_EMAILS: tuple[str, ...] = (
    "marcus.williams.partner@gmail.com",
    "elena.volkov.rides@outlook.com",
    "priya.shah.mobility@icloud.com",
    "kevin.murphy.fleet@gmail.com",
)

# Driver home bases (lat, lng) — Manhattan / Brooklyn mix.
_DRIVER_HOME: tuple[tuple[float, float], ...] = (
    (40.7589, -73.9851),
    (40.7484, -73.9857),
    (40.7282, -73.9942),
    (40.7061, -74.0087),
)

# (pickup_lat, pickup_lng, drop_lat, drop_lng) — short NYC hops.
_LEGS: tuple[tuple[float, float, float, float], ...] = (
    (40.7580, -73.9855, 40.7549, -73.9840),
    (40.7614, -73.9776, 40.7527, -73.9772),
    (40.7505, -73.9934, 40.7411, -73.9897),
    (40.7359, -73.9911, 40.7289, -73.9942),
    (40.7076, -74.0113, 40.7153, -74.0165),
    (40.7489, -73.9680, 40.7587, -73.9787),
    (40.7308, -73.9973, 40.7398, -73.9942),
)


def _ensure_user(
    db: DBSession,
    conn: sqlite3.Connection,
    email: str,
    role: UserRole,
) -> int:
    email_n = email.strip().lower()
    row = db.get_user_by_email(conn, email_n)
    if row is not None:
        return int(row["id"])
    try:
        uid = db.insert_user(
            conn,
            email=email_n,
            password_hash=_pwd.hash(_DEMO_PASSWORD),
            role=role,
        )
    except sqlite3.IntegrityError:
        # Another startup may have committed users after a failed demo seed (rides still empty).
        row = db.get_user_by_email(conn, email_n)
        if row is None:
            raise
        return int(row["id"])
    # Log creation but do not print the demo password to avoid accidental exposure
    logger.info("Created demo %s user: %s", role.value, email_n)
    return uid


def _insert_ride_with_pickup_analytics(
    db: DBSession,
    conn: sqlite3.Connection,
    *,
    rider_id: int,
    leg: tuple[float, float, float, float],
    status: RideStatus = RideStatus.bidding_open,
) -> int:
    plat, plng, dlat, dlng = leg
    rid = db.insert_ride(
        conn,
        rider_id=rider_id,
        pickup_lat=plat,
        pickup_lng=plng,
        dropoff_lat=dlat,
        dropoff_lng=dlng,
        status=status,
    )
    row = db.get_ride(conn, rid)
    assert row is not None
    try_record_fruger_pickup_for_ride(
        conn,
        ride_id=rid,
        pickup_lat=plat,
        pickup_lng=plng,
        created_at=str(row["created_at"]),
    )
    return rid


def _place_bid(
    db: DBSession,
    conn: sqlite3.Connection,
    *,
    ride_id: int,
    driver_id: int,
    fare_cents: int,
) -> int:
    ride = db.get_ride(conn, ride_id)
    assert ride is not None
    loc = db.get_driver_location(conn, driver_id)
    assert loc is not None
    dist = haversine_m(
        float(loc["lat"]),
        float(loc["lng"]),
        float(ride["pickup_lat"]),
        float(ride["pickup_lng"]),
    )
    return db.upsert_bid(
        conn,
        ride_id=ride_id,
        driver_id=driver_id,
        fare_cents=fare_cents,
        distance_to_pickup_m=dist,
        status=BidStatus.pending,
    )


def _accept_bid_core(
    db: DBSession,
    conn: sqlite3.Connection,
    *,
    ride_id: int,
    bid_id: int,
) -> None:
    bid = db.get_bid(conn, bid_id)
    assert bid is not None
    db.accept_bid_row(conn, bid_id)
    db.reject_other_bids(conn, ride_id, bid_id)
    db.update_ride(
        conn,
        ride_id,
        status=RideStatus.assigned,
        accepted_bid_id=bid_id,
        final_fare_cents=int(bid["fare_cents"]),
    )


def seed_operational_demo_if_empty(conn: sqlite3.Connection) -> None:
    """If ``rides`` is empty and config allows it, insert demo users, locations, bids, and rides."""
    if not app_config.AUTO_OPERATIONAL_DEMO_SEED:
        return
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM live_rides")
    if int(cur.fetchone()[0]) > 0:
        return

    db = DBSession(app_config.DB_PATH)
    rider_ids = [
        _ensure_user(db, conn, email, UserRole.rider) for email in _RIDER_EMAILS
    ]
    driver_ids = [
        _ensure_user(db, conn, email, UserRole.driver) for email in _DRIVER_EMAILS
    ]

    for did, (lat, lng) in zip(driver_ids, _DRIVER_HOME, strict=True):
        db.upsert_driver_location(conn, did, lat, lng)

    now = datetime.now(timezone.utc).isoformat()

    # 1) Open ride — two competing bids
    r_open = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[0], leg=_LEGS[0], status=RideStatus.bidding_open
    )
    _place_bid(db, conn, ride_id=r_open, driver_id=driver_ids[0], fare_cents=1895)
    _place_bid(db, conn, ride_id=r_open, driver_id=driver_ids[1], fare_cents=1750)

    # 2) Open ride — single bid
    r_open2 = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[1], leg=_LEGS[1], status=RideStatus.bidding_open
    )
    _place_bid(db, conn, ride_id=r_open2, driver_id=driver_ids[2], fare_cents=2125)

    # 3) Assigned (accepted bid)
    r_asg = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[2], leg=_LEGS[2], status=RideStatus.bidding_open
    )
    b_asg = _place_bid(
        db, conn, ride_id=r_asg, driver_id=driver_ids[0], fare_cents=1650
    )
    _place_bid(db, conn, ride_id=r_asg, driver_id=driver_ids[3], fare_cents=1599)
    _accept_bid_core(db, conn, ride_id=r_asg, bid_id=b_asg)

    # 4) In progress
    r_ip = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[3], leg=_LEGS[3], status=RideStatus.bidding_open
    )
    b_ip = _place_bid(db, conn, ride_id=r_ip, driver_id=driver_ids[1], fare_cents=2230)
    _accept_bid_core(db, conn, ride_id=r_ip, bid_id=b_ip)
    db.update_ride(conn, r_ip, status=RideStatus.in_progress)

    # 5) Completed
    r_done = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[4], leg=_LEGS[4], status=RideStatus.bidding_open
    )
    b_done = _place_bid(
        db, conn, ride_id=r_done, driver_id=driver_ids[2], fare_cents=1988
    )
    _accept_bid_core(db, conn, ride_id=r_done, bid_id=b_done)
    db.update_ride(conn, r_done, status=RideStatus.in_progress)
    db.update_ride(
        conn,
        r_done,
        status=RideStatus.completed,
        final_fare_cents=1988,
        completed_at=now,
        driver_marked_complete_at=now,
        rider_marked_complete_at=now,
    )

    # 6) Cancelled
    r_can = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[5], leg=_LEGS[5], status=RideStatus.bidding_open
    )
    _place_bid(db, conn, ride_id=r_can, driver_id=driver_ids[0], fare_cents=1450)
    db.update_ride(
        conn,
        r_can,
        status=RideStatus.cancelled,
        cancelled_at=now,
    )
    conn.execute(
        "UPDATE bids SET status = ? WHERE ride_id = ? AND status = ?",
        (BidStatus.rejected.value, r_can, BidStatus.pending.value),
    )

    # 7) Second completed (shows history for a repeat rider)
    r_done2 = _insert_ride_with_pickup_analytics(
        db, conn, rider_id=rider_ids[0], leg=_LEGS[6], status=RideStatus.bidding_open
    )
    b_done2 = _place_bid(
        db, conn, ride_id=r_done2, driver_id=driver_ids[3], fare_cents=1875
    )
    _accept_bid_core(db, conn, ride_id=r_done2, bid_id=b_done2)
    db.update_ride(conn, r_done2, status=RideStatus.in_progress)
    db.update_ride(
        conn,
        r_done2,
        status=RideStatus.completed,
        final_fare_cents=1875,
        completed_at=now,
        driver_marked_complete_at=now,
        rider_marked_complete_at=now,
    )

    logger.info(
        "Operational demo seed: %s riders, %s drivers, 7 rides (open/assigned/in_progress/"
        "completed/cancelled). Demo password for all new accounts: %s",
        len(_RIDER_EMAILS),
        len(_DRIVER_EMAILS),
        _DEMO_PASSWORD,
    )
