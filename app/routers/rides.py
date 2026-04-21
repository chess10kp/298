"""Ride CRUD, bidding hooks, driver lifecycle."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import Conn, CurrentUser, DriverUser, RiderUser, get_db_session
from app.schemas.operational import (
    BidOut,
    BidPlaceRequest,
    BidderLocationOut,
    RideCreate,
    RideOut,
    UserRole,
)
from app.services.bidding_service import BiddingService
from app.services.db_session import DBSession
from fastapi import WebSocket, WebSocketDisconnect
from app.ws import register_driver, unregister_driver, broadcast_open_rides
from app.services.ride_service import RideService

router = APIRouter(prefix="/api/v1/rides", tags=["rides"])


def get_ride_service(db: Annotated[DBSession, Depends(get_db_session)]) -> RideService:
    return RideService(db)


def get_bidding_service(
    db: Annotated[DBSession, Depends(get_db_session)],
) -> BiddingService:
    return BiddingService(db)


Rs = Annotated[RideService, Depends(get_ride_service)]
Bs = Annotated[BiddingService, Depends(get_bidding_service)]


@router.post("", response_model=RideOut)
def create_ride(
    body: RideCreate,
    conn: Conn,
    rider: RiderUser,
    rides: Rs,
) -> RideOut:
    return rides.request_ride(conn, rider.id, body)


@router.get("/me", response_model=list[RideOut])
def my_rides(conn: Conn, rider: RiderUser, rides: Rs) -> list[RideOut]:
    return rides.list_my_rides(conn, rider.id)


@router.get("/open", response_model=list[RideOut])
def open_rides(
    conn: Conn,
    _: DriverUser,
    rides: Rs,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RideOut]:
    return rides.list_open_rides(conn, limit=limit)


@router.get("/driver/active", response_model=list[RideOut])
def driver_active_rides(conn: Conn, driver: DriverUser, rides: Rs) -> list[RideOut]:
    return rides.list_active_rides_for_driver(conn, driver.id)


@router.get("/{ride_id}", response_model=RideOut)
def get_ride(
    ride_id: int,
    conn: Conn,
    user: CurrentUser,
    rides: Rs,
    db: Annotated[DBSession, Depends(get_db_session)],
) -> RideOut:
    out = rides.get_ride(conn, ride_id)
    if user.role == UserRole.admin:
        return out
    if user.role == UserRole.rider and out.rider_id == user.id:
        return out
    if user.role == UserRole.driver:
        ride_row = db.get_ride(conn, ride_id)
        assert ride_row is not None
        ab = ride_row.get("accepted_bid_id")
        if ab is not None:
            bid = db.get_bid(conn, int(ab))
            if bid is not None and int(bid["driver_id"]) == user.id:
                return out
        # Driver who placed a bid can view
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM bids WHERE ride_id = ? AND driver_id = ? LIMIT 1",
            (ride_id, user.id),
        )
        if cur.fetchone() is not None:
            return out
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view this ride"
    )


@router.post("/{ride_id}/cancel", response_model=RideOut)
def cancel_ride(ride_id: int, conn: Conn, rider: RiderUser, rides: Rs) -> RideOut:
    return rides.cancel_ride(conn, ride_id, rider.id)


@router.post("/{ride_id}/bids", response_model=BidOut)
def place_bid(
    ride_id: int,
    body: BidPlaceRequest,
    conn: Conn,
    driver: DriverUser,
    bids: Bs,
) -> BidOut:
    return bids.place_bid(conn, ride_id, driver.id, body)


@router.get("/bids/{bid_id}/route")
def get_bid_route(
    bid_id: int, conn: Conn, db: Annotated[DBSession, Depends(get_db_session)]
) -> dict:
    bs = BiddingService(db)
    return bs.route_driver(conn, bid_id)


@router.websocket("/ws/drivers")
async def drivers_ws(ws: WebSocket, db: Annotated[DBSession, Depends(get_db_session)]):
    await ws.accept()
    await register_driver(ws)
    try:
        while True:
            # keep connection alive; we don't expect inbound messages for now
            await ws.receive_text()
    except WebSocketDisconnect:
        unregister_driver(ws)


@router.get("/{ride_id}/bidder-locations", response_model=list[BidderLocationOut])
def bidder_locations_for_ride(
    ride_id: int,
    conn: Conn,
    user: CurrentUser,
    db: Annotated[DBSession, Depends(get_db_session)],
) -> list[BidderLocationOut]:
    ride_row = db.get_ride(conn, ride_id)
    if ride_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found"
        )
    if user.role == UserRole.admin:
        pass
    elif user.role == UserRole.rider and int(ride_row["rider_id"]) == user.id:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view bidder pins"
        )
    rows = db.list_bidder_locations_for_ride(conn, ride_id)
    return [
        BidderLocationOut(
            driver_id=int(r["driver_id"]),
            lat=float(r["lat"]),
            lng=float(r["lng"]),
        )
        for r in rows
    ]


@router.get("/{ride_id}/bids", response_model=list[BidOut])
def list_bids(
    ride_id: int,
    conn: Conn,
    user: CurrentUser,
    bids: Bs,
    rides: Rs,
    db: Annotated[DBSession, Depends(get_db_session)],
) -> list[BidOut]:
    ride_row = db.get_ride(conn, ride_id)
    if ride_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found"
        )
    if user.role == UserRole.admin:
        return bids.list_bids_for_ride(conn, ride_id)
    if user.role == UserRole.rider and int(ride_row["rider_id"]) == user.id:
        return bids.list_bids_for_ride(conn, ride_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Cannot list bids"
    )


@router.post("/{ride_id}/bids/{bid_id}/accept", response_model=RideOut)
def accept_bid(
    ride_id: int,
    bid_id: int,
    conn: Conn,
    rider: RiderUser,
    bids: Bs,
    rides: Rs,
) -> RideOut:
    _, ride_row = bids.accept_bid(
        conn, ride_id=ride_id, bid_id=bid_id, rider_id=rider.id
    )
    # broadcast a short update to connected drivers that ride was assigned
    # schedule background broadcast without awaiting to keep request fast
    try:
        import asyncio

        asyncio_message = {"event": "ride_assigned", "ride_id": int(ride_row["id"])}
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in this thread; run the coroutine in a background thread
            import threading

            def _run():
                import asyncio as _asyncio

                _asyncio.run(broadcast_open_rides(asyncio_message))

            threading.Thread(target=_run, daemon=True).start()
        else:
            loop.create_task(broadcast_open_rides(asyncio_message))
    except Exception:
        # Intentionally swallow broadcast errors to avoid impacting API flow
        pass
    return RideService.ride_from_row(ride_row, conn)


@router.post("/{ride_id}/start", response_model=RideOut)
def start_ride(
    ride_id: int,
    conn: Conn,
    driver: DriverUser,
    rides: Rs,
) -> RideOut:
    return rides.start_ride(conn, ride_id, driver.id)


@router.post("/{ride_id}/rider-complete", response_model=RideOut)
def rider_complete_ride(
    ride_id: int,
    conn: Conn,
    rider: RiderUser,
    rides: Rs,
) -> RideOut:
    return rides.rider_complete_ride(conn, ride_id, rider.id)


@router.post("/{ride_id}/complete", response_model=RideOut)
def complete_ride(
    ride_id: int,
    conn: Conn,
    driver: DriverUser,
    rides: Rs,
) -> RideOut:
    return rides.complete_ride(conn, ride_id, driver.id)
