"""FastUI rider home."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastui import AnyComponent, FastUI

from app.deps import Conn, get_current_user_optional, get_db_session
from app.rider_dashboard import build_rider_dashboard
from app.schemas.operational import UserPublic, UserRole
from app.services.db_session import DBSession
from app.services.ride_service import RideService

router = APIRouter(prefix="/api/rider", tags=["rider-ui"])


def get_ride_service(db: Annotated[DBSession, Depends(get_db_session)]) -> RideService:
    return RideService(db)


@router.get("/dashboard", response_model=FastUI, response_model_exclude_none=True)
def rider_dashboard(
    conn: Conn,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    rides_svc: Annotated[RideService, Depends(get_ride_service)],
) -> list[AnyComponent]:
    rides = []
    if user is not None and user.role == UserRole.rider:
        rides = rides_svc.list_my_rides(conn, user.id)
    return build_rider_dashboard(user, rides)
