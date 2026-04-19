"""Admin JSON, plots, and FastUI dashboard."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from fastui import AnyComponent
from pydantic import BaseModel

from app.admin_dashboard import build_admin_dashboard
from app.admin_plots import revenue_by_day_png
from app.deps import AdminUser, Conn, get_db_session
from app.schemas.operational import AdminStatsOut, DriverLocationOut
from app.services.admin_service import AdminService
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_service(
    db: Annotated[DBSession, Depends(get_db_session)],
) -> AdminService:
    return AdminService(db)


Asvc = Annotated[AdminService, Depends(get_admin_service)]


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


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(conn: Conn, _: AdminUser, svc: Asvc) -> AdminStatsOut:
    return svc.overview_stats(conn)


@router.get("/driver-locations", response_model=list[DriverLocationOut])
def admin_driver_locations(
    conn: Conn, _: AdminUser, db: Annotated[DBSession, Depends(get_db_session)]
) -> list[DriverLocationOut]:
    rows = db.list_driver_locations_with_email(conn)
    return [
        DriverLocationOut(
            driver_id=int(r["driver_id"]),
            email=str(r["email"]),
            lat=float(r["lat"]),
            lng=float(r["lng"]),
            updated_at=str(r["updated_at"]),
        )
        for r in rows
    ]


@router.get("/plots/revenue.png")
def revenue_plot(conn: Conn, _: AdminUser, svc: Asvc) -> Response:
    points = svc.revenue_by_day(conn)
    png = revenue_by_day_png(points)
    return Response(content=png, media_type="image/png")


@router.get("/dashboard")
def admin_dashboard_ui(conn: Conn, _: AdminUser, svc: Asvc) -> JSONResponse:
    stats = svc.overview_stats(conn)
    return _fastui_json(build_admin_dashboard(stats))
