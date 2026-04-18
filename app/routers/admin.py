"""Admin JSON, plots, and FastUI dashboard."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fastui import AnyComponent, FastUI

from app.admin_dashboard import build_admin_dashboard
from app.admin_plots import revenue_by_day_png
from app.deps import AdminUser, Conn, get_db_session
from app.schemas.operational import AdminStatsOut
from app.services.admin_service import AdminService
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_service(db: Annotated[DBSession, Depends(get_db_session)]) -> AdminService:
    return AdminService(db)


Asvc = Annotated[AdminService, Depends(get_admin_service)]


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(conn: Conn, _: AdminUser, svc: Asvc) -> AdminStatsOut:
    return svc.overview_stats(conn)


@router.get("/plots/revenue.png")
def revenue_plot(conn: Conn, _: AdminUser, svc: Asvc) -> Response:
    points = svc.revenue_by_day(conn)
    png = revenue_by_day_png(points)
    return Response(content=png, media_type="image/png")


@router.get("/dashboard", response_model=FastUI, response_model_exclude_none=True)
def admin_dashboard_ui(conn: Conn, _: AdminUser, svc: Asvc) -> list[AnyComponent]:
    stats = svc.overview_stats(conn)
    return build_admin_dashboard(stats)
