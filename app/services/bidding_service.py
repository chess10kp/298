"""Driver bids and rider acceptance."""

from __future__ import annotations

import sqlite3

from fastapi import HTTPException, status

from app.schemas.operational import BidOut, BidPlaceRequest, BidStatus, RideStatus
from app.services.db_session import DBSession
from app.services.geo import haversine_m


class BiddingService:
    def __init__(self, db: DBSession):
        self._db = db

    @staticmethod
    def _bid_out(row: dict) -> BidOut:
        return BidOut(
            id=int(row["id"]),
            ride_id=int(row["ride_id"]),
            driver_id=int(row["driver_id"]),
            fare_cents=int(row["fare_cents"]),
            distance_to_pickup_m=float(row["distance_to_pickup_m"]),
            status=BidStatus(str(row["status"])),
            created_at=str(row["created_at"]),
        )

    def place_bid(
        self,
        conn: sqlite3.Connection,
        ride_id: int,
        driver_id: int,
        body: BidPlaceRequest,
    ) -> BidOut:
        ride = self._db.get_ride(conn, ride_id)
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if str(ride["status"]) != RideStatus.bidding_open.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bidding is closed")
        loc = self._db.get_driver_location(conn, driver_id)
        if loc is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set your location before bidding",
            )
        dist = haversine_m(
            float(loc["lat"]),
            float(loc["lng"]),
            float(ride["pickup_lat"]),
            float(ride["pickup_lng"]),
        )
        bid_id = self._db.upsert_bid(
            conn,
            ride_id=ride_id,
            driver_id=driver_id,
            fare_cents=body.fare_cents,
            distance_to_pickup_m=dist,
            status=BidStatus.pending,
        )
        row = self._db.get_bid(conn, bid_id)
        assert row is not None
        return self._bid_out(row)

    def list_bids_for_ride(self, conn: sqlite3.Connection, ride_id: int) -> list[BidOut]:
        rows = self._db.list_bids_for_ride(conn, ride_id)
        return [self._bid_out(r) for r in rows]

    def accept_bid(
        self,
        conn: sqlite3.Connection,
        *,
        ride_id: int,
        bid_id: int,
        rider_id: int,
    ) -> tuple[BidOut, dict]:
        ride = self._db.get_ride(conn, ride_id)
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if int(ride["rider_id"]) != rider_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ride")
        if str(ride["status"]) != RideStatus.bidding_open.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride is not accepting bids",
            )
        bid = self._db.get_bid(conn, bid_id)
        if bid is None or int(bid["ride_id"]) != ride_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bid not found")
        if str(bid["status"]) != BidStatus.pending.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bid is not pending")

        self._db.accept_bid_row(conn, bid_id)
        self._db.reject_other_bids(conn, ride_id, bid_id)
        self._db.update_ride(
            conn,
            ride_id,
            status=RideStatus.assigned,
            accepted_bid_id=bid_id,
            final_fare_cents=int(bid["fare_cents"]),
        )
        row = self._db.get_bid(conn, bid_id)
        ride_row = self._db.get_ride(conn, ride_id)
        assert row is not None and ride_row is not None
        return self._bid_out(row), ride_row
