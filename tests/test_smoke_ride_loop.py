"""End-to-end smoke test: ride request, bid, accept, start, complete, admin stats."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _import_app_with_db(db_path: str) -> Any:
    for name in list(sys.modules):
        if name == "main" or name.startswith("app."):
            del sys.modules[name]

    os.environ["DATABASE_PATH"] = db_path
    os.environ["SKIP_DATASET_SEED"] = "1"
    import main  # noqa: PLC0415

    return main


def test_full_ride_loop_and_admin(tmp_path, monkeypatch):
    db_file = tmp_path / "smoke.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("SKIP_DATASET_SEED", "1")
    main = _import_app_with_db(str(db_file))
    from fastapi.testclient import TestClient  # noqa: PLC0415

    with (
        TestClient(main.app) as rider_c,
        TestClient(main.app) as driver_c,
        TestClient(main.app) as admin_c,
    ):
        assert (
            rider_c.post(
                "/api/v1/auth/session",
                json={"email": "rider@local.dev", "password": "Riderpass123"},
            ).status_code
            == 200
        )
        assert (
            driver_c.post(
                "/api/v1/auth/session",
                json={"email": "driver@local.dev", "password": "Driverpass123"},
            ).status_code
            == 200
        )
        assert (
            admin_c.post(
                "/api/v1/auth/session",
                json={"email": "admin@local.dev", "password": "Adminpass123"},
            ).status_code
            == 200
        )

        r = rider_c.post(
            "/api/v1/rides",
            json={
                "pickup_lat": 40.75,
                "pickup_lng": -73.99,
                "dropoff_lat": 40.76,
                "dropoff_lng": -73.98,
            },
        )
        assert r.status_code == 200, r.text
        ride = r.json()
        rid = int(ride["id"])
        assert ride["status"] == "bidding_open"

        assert (
            driver_c.post(
                "/api/v1/driver/location",
                json={"lat": 40.751, "lng": -73.991},
            ).status_code
            == 200
        )
        r = driver_c.post(f"/api/v1/rides/{rid}/bids", json={"fare_cents": 1234})
        assert r.status_code == 200, r.text
        bid = r.json()
        bid_id = int(bid["id"])
        assert bid["distance_to_pickup_m"] > 0

        pins = rider_c.get(f"/api/v1/rides/{rid}/bidder-locations")
        assert pins.status_code == 200, pins.text
        assert len(pins.json()) == 1
        assert pins.json()[0]["driver_id"] == bid["driver_id"]

        r = rider_c.post(f"/api/v1/rides/{rid}/bids/{bid_id}/accept", json={})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "assigned"
        assert r.json()["final_fare_cents"] == 1234

        r = driver_c.post(f"/api/v1/rides/{rid}/start", json={})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "in_progress"

        r = driver_c.post(f"/api/v1/rides/{rid}/complete", json={})
        assert r.status_code == 200, r.text
        done = r.json()
        assert done["status"] == "completed"
        assert done["final_fare_cents"] == 1234

        stats = admin_c.get("/api/v1/admin/stats")
        assert stats.status_code == 200, stats.text
        body = stats.json()
        assert body["total_rides"] >= 1
        assert body["completed_revenue_cents"] >= 1234

        plot = admin_c.get("/api/v1/admin/plots/revenue.png")
        assert plot.status_code == 200
        assert plot.headers["content-type"] == "image/png"
        assert len(plot.content) > 100
