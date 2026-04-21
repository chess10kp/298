"""Driver / partner location updates."""

from __future__ import annotations

from typing import Annotated

import app.config as app_config
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import Conn, DriverUser, get_auth_service, get_db_session
from app.schemas.operational import DriverLocationIn
from app.services.auth_service import AuthService
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/v1/driver", tags=["driver"])


@router.post("/location")
def update_location(
    body: DriverLocationIn,
    conn: Conn,
    driver: DriverUser,
    db: Annotated[DBSession, Depends(get_db_session)],
) -> dict[str, bool]:
    db.upsert_driver_location(conn, driver.id, body.lat, body.lng)
    return {"ok": True}
