"""FastUI rider JSON at ``/api/rider/dashboard`` (same tree as ``GET /api`` for rider sessions)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastui import AnyComponent
from pydantic import BaseModel

from app.deps import Conn, get_current_user_optional, get_db_session
from app.rider_dashboard import build_rider_dashboard
from app.schemas.operational import UserPublic, UserRole
from app.services.db_session import DBSession
from app.services.ride_service import RideService

router = APIRouter(prefix="/api/rider", tags=["rider-ui"])


def get_ride_service(db: Annotated[DBSession, Depends(get_db_session)]) -> RideService:
    return RideService(db)


def _serialize_val(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple)):
        return [_serialize_val(x) for x in v]
    if isinstance(v, dict):
        return {k: _serialize_val(val) for k, val in v.items()}
    if isinstance(v, BaseModel):
        return {f: _serialize_val(getattr(v, f, None)) for f in v.model_fields}
    if hasattr(v, "__str__"):
        return str(v)
    return v


def _fastui_json(components: list[AnyComponent]) -> JSONResponse:
    return JSONResponse(
        [
            _serialize_val(c.model_dump(exclude_none=True, by_alias=True))
            for c in components
        ]
    )


@router.get("/dashboard")
def rider_dashboard(
    request: Request,
    conn: Conn,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    rides_svc: Annotated[RideService, Depends(get_ride_service)],
) -> JSONResponse:
    rides = []
    if user is not None and user.role == UserRole.rider:
        rides = rides_svc.list_my_rides(conn, user.id)
    return _fastui_json(
        build_rider_dashboard(user, rides, request_base=str(request.base_url))
    )
