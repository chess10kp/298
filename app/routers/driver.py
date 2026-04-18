"""Driver / partner location updates."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import Conn, DriverUser, get_db_session
from app.schemas.operational import DriverLocationIn
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/driver", tags=["driver"])


@router.post("/location")
def update_location(
    body: DriverLocationIn,
    conn: Conn,
    driver: DriverUser,
    db: Annotated[DBSession, Depends(get_db_session)],
) -> dict[str, bool]:
    db.upsert_driver_location(conn, driver.id, body.lat, body.lng)
    return {"ok": True}
