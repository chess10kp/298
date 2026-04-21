"""Insert demo riders and open rides for driver-hub testing (same DB paths as production)."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.schemas.operational import UserRole
from app.services.auth_service import AuthService
from app.services.db_session import DBSession

# NYC-ish coordinates (decimal degrees).
_DEMO_RIDERS: tuple[tuple[str, str], ...] = (
    ("fruger-demo-rider-1@local.dev", "Demopass123"),
    ("fruger-demo-rider-2@local.dev", "Demopass123"),
)

# One open ride per rider each seed run: pickup → dropoff
_DEMO_LEGS: tuple[tuple[float, float, float, float], ...] = (
    (40.7580, -73.9855, 40.7484, -73.9857),  # Times Sq area → Midtown south
    (40.7614, -73.9776, 40.7282, -73.9942),  # Central Park S → downtown-ish
)


def run_driver_demo_seed(
    conn: sqlite3.Connection,
    db: DBSession,
    auth: AuthService,
    *,
    driver_id: int,
) -> dict[str, Any]:
    """Create or reuse demo riders, add ``bidding_open`` rides, park driver GPS near first pickup."""
    riders_out: list[dict[str, Any]] = []
    ride_ids: list[int] = []

    for i, (email, password) in enumerate(_DEMO_RIDERS):
        row = db.get_user_by_email(conn, email)
        if row is None:
            uid = db.insert_user(
                conn,
                email=email,
                password_hash=auth.hash_password(password),
                role=UserRole.rider,
            )
            riders_out.append(
                {"email": email, "user_id": uid, "user_created": True, "password": password}
            )
        else:
            uid = int(row["id"])
            riders_out.append(
                {"email": email, "user_id": uid, "user_created": False, "password": password}
            )

        plat, plng, dlat, dlng = _DEMO_LEGS[i % len(_DEMO_LEGS)]
        rid = db.insert_ride(
            conn,
            rider_id=uid,
            pickup_lat=plat,
            pickup_lng=plng,
            dropoff_lat=dlat,
            dropoff_lng=dlng,
        )
        ride_ids.append(rid)

    # So bidding works even without browser geolocation (tests / automation).
    p0_lat, p0_lng, _, _ = _DEMO_LEGS[0]
    db.upsert_driver_location(conn, driver_id, p0_lat, p0_lng)

    return {
        "ok": True,
        "riders": riders_out,
        "ride_ids": ride_ids,
        "driver_location_set": True,
        "message": (
            "Added open rides for demo riders; your GPS in the DB is set near the first pickup "
            "so you can bid immediately. Demo logins: fruger-demo-rider-1@local.dev / "
            "fruger-demo-rider-2@local.dev (password Demopass123)."
        ),
    }
