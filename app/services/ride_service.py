"""Ride lifecycle for riders and assigned drivers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.schemas.operational import BidStatus, RideCreate, RideOut, RideStatus
from app.services.db_session import DBSession
from app.services.operational_pickup_events import try_record_fruger_pickup_for_ride
from app.services.pickup_dataset_labels import nearest_pickup_location_label


class RideService:
    def __init__(self, db: DBSession):
        self._db = db

    @staticmethod
    def ride_from_row(row: dict, conn: sqlite3.Connection | None = None) -> RideOut:
        dma = row.get("driver_marked_complete_at")
        rma = row.get("rider_marked_complete_at")
        return RideOut(
            id=int(row["id"]),
            rider_id=int(row["rider_id"]),
            pickup_lat=float(row["pickup_lat"]),
            pickup_lng=float(row["pickup_lng"]),
            dropoff_lat=float(row["dropoff_lat"]),
            dropoff_lng=float(row["dropoff_lng"]),
            pickup_location=row.get("pickup_location"),
            dropoff_location=row.get("dropoff_location"),
            status=RideStatus(str(row["status"])),
            accepted_bid_id=int(row["accepted_bid_id"]) if row["accepted_bid_id"] is not None else None,
            final_fare_cents=int(row["final_fare_cents"]) if row["final_fare_cents"] is not None else None,
            created_at=str(row["created_at"]),
            cancelled_at=str(row["cancelled_at"]) if row["cancelled_at"] is not None else None,
            completed_at=str(row["completed_at"]) if row["completed_at"] is not None else None,
            driver_marked_complete_at=str(dma) if dma is not None else None,
            rider_marked_complete_at=str(rma) if rma is not None else None,
        )

    def _finalize_completed_ride(self, conn: sqlite3.Connection, ride_id: int, ride: dict) -> RideOut:
        aid = ride["accepted_bid_id"]
        if aid is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accepted bid",
            )
        bid = self._db.get_bid(conn, int(aid))
        if bid is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accepted bid",
            )
        now = datetime.now(timezone.utc).isoformat()
        fare = (
            int(ride["final_fare_cents"])
            if ride["final_fare_cents"] is not None
            else int(bid["fare_cents"])
        )
        self._db.update_ride(
            conn,
            ride_id,
            status=RideStatus.completed,
            final_fare_cents=fare,
            completed_at=now,
        )
        row = self._db.get_ride(conn, ride_id)
        assert row is not None
        return self.ride_from_row(row, conn)

    def request_ride(self, conn: sqlite3.Connection, rider_id: int, body: RideCreate) -> RideOut:
        pickup_label = nearest_pickup_location_label(conn, body.pickup_lat, body.pickup_lng)
        dropoff_label = nearest_pickup_location_label(conn, body.dropoff_lat, body.dropoff_lng)
        rid = self._db.insert_ride(
            conn,
            rider_id=rider_id,
            pickup_lat=body.pickup_lat,
            pickup_lng=body.pickup_lng,
            dropoff_lat=body.dropoff_lat,
            dropoff_lng=body.dropoff_lng,
            pickup_location=pickup_label,
            dropoff_location=dropoff_label,
            status=RideStatus.bidding_open,
        )
        row = self._db.get_ride(conn, rid)
        assert row is not None
        try_record_fruger_pickup_for_ride(
            conn,
            ride_id=rid,
            pickup_lat=body.pickup_lat,
            pickup_lng=body.pickup_lng,
            created_at=str(row["created_at"]),
        )
        return self.ride_from_row(row, conn)

    def cancel_ride(self, conn: sqlite3.Connection, ride_id: int, rider_id: int) -> RideOut:
        row = self._db.get_ride(conn, ride_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if int(row["rider_id"]) != rider_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ride")
        st = str(row["status"])
        if st not in (RideStatus.bidding_open.value, RideStatus.assigned.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride cannot be cancelled in this state",
            )
        now = datetime.now(timezone.utc).isoformat()
        self._db.update_ride(
            conn,
            ride_id,
            status=RideStatus.cancelled,
            cancelled_at=now,
        )
        # Reject pending bids if any
        conn.execute(
            "UPDATE bids SET status = ? WHERE ride_id = ? AND status = ?",
            (BidStatus.rejected.value, ride_id, BidStatus.pending.value),
        )
        row2 = self._db.get_ride(conn, ride_id)
        assert row2 is not None
        return self.ride_from_row(row2, conn)

    def list_my_rides(self, conn: sqlite3.Connection, rider_id: int) -> list[RideOut]:
        rows = self._db.list_rides_for_rider(conn, rider_id)
        return [self.ride_from_row(r, conn) for r in rows]

    def list_open_rides(self, conn: sqlite3.Connection, *, limit: int = 100) -> list[RideOut]:
        rows = self._db.list_rides_with_status(conn, RideStatus.bidding_open, limit=limit)
        return [self.ride_from_row(r, conn) for r in rows]

    def list_active_rides_for_driver(
        self, conn: sqlite3.Connection, driver_id: int
    ) -> list[RideOut]:
        rows = self._db.list_rides_for_assigned_driver(conn, driver_id)
        return [self.ride_from_row(r, conn) for r in rows]

    def get_ride(self, conn: sqlite3.Connection, ride_id: int) -> RideOut:
        row = self._db.get_ride(conn, ride_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        return self.ride_from_row(row, conn)

    def start_ride(self, conn: sqlite3.Connection, ride_id: int, driver_id: int) -> RideOut:
        ride = self._db.get_ride(conn, ride_id)
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if str(ride["status"]) != RideStatus.assigned.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride must be assigned before starting",
            )
        aid = ride["accepted_bid_id"]
        if aid is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accepted bid")
        bid = self._db.get_bid(conn, int(aid))
        if bid is None or int(bid["driver_id"]) != driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the assigned driver")
        self._db.update_ride(conn, ride_id, status=RideStatus.in_progress)
        self._db.clear_ride_completion_marks(conn, ride_id)
        row = self._db.get_ride(conn, ride_id)
        assert row is not None
        return self.ride_from_row(row, conn)

    def complete_ride(self, conn: sqlite3.Connection, ride_id: int, driver_id: int) -> RideOut:
        """Driver confirms trip finished; ride completes only after rider confirms too."""
        ride = self._db.get_ride(conn, ride_id)
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if str(ride["status"]) != RideStatus.in_progress.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride must be in progress to complete",
            )
        aid = ride["accepted_bid_id"]
        if aid is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accepted bid")
        bid = self._db.get_bid(conn, int(aid))
        if bid is None or int(bid["driver_id"]) != driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the assigned driver")
        if ride.get("driver_marked_complete_at"):
            row = self._db.get_ride(conn, ride_id)
            assert row is not None
            return self.ride_from_row(row, conn)
        now = datetime.now(timezone.utc).isoformat()
        self._db.update_ride(conn, ride_id, driver_marked_complete_at=now)
        row = self._db.get_ride(conn, ride_id)
        assert row is not None
        if row.get("rider_marked_complete_at"):
            return self._finalize_completed_ride(conn, ride_id, dict(row))
        return self.ride_from_row(row, conn)

    def rider_complete_ride(self, conn: sqlite3.Connection, ride_id: int, rider_id: int) -> RideOut:
        """Rider confirms trip finished; ride completes only after driver confirms too."""
        ride = self._db.get_ride(conn, ride_id)
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if int(ride["rider_id"]) != rider_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ride")
        if str(ride["status"]) != RideStatus.in_progress.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride must be in progress to confirm completion",
            )
        if ride.get("rider_marked_complete_at"):
            row = self._db.get_ride(conn, ride_id)
            assert row is not None
            return self.ride_from_row(row, conn)
        now = datetime.now(timezone.utc).isoformat()
        self._db.update_ride(conn, ride_id, rider_marked_complete_at=now)
        row = self._db.get_ride(conn, ride_id)
        assert row is not None
        if row.get("driver_marked_complete_at"):
            return self._finalize_completed_ride(conn, ride_id, dict(row))
        return self.ride_from_row(row, conn)
