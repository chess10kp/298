from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response

from app.analytics_plots import (
    base_chart_png,
    borough_chart_png,
    hour_chart_png,
    pickups_by_date_chart_png,
)
from app.analytics_queries import fetch_overview
from app.config import DB_PATH
from app.schemas.analytics import NycOverviewResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _db_path() -> Path:
    return DB_PATH


@router.get("/overview", response_model=NycOverviewResponse)
def get_overview() -> NycOverviewResponse:
    path = _db_path()
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Database not initialized. Start the app once to create it.",
        )
    try:
        return fetch_overview(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/plots/borough.png")
def plot_borough() -> Response:
    path = _db_path()
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Database not available.")
    overview = fetch_overview(path)
    data = borough_chart_png(overview.by_borough)
    return Response(content=data, media_type="image/png")


@router.get("/plots/base.png")
def plot_base() -> Response:
    path = _db_path()
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Database not available.")
    overview = fetch_overview(path)
    data = base_chart_png(overview.by_base)
    return Response(content=data, media_type="image/png")


@router.get("/plots/hour.png")
def plot_hour() -> Response:
    path = _db_path()
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Database not available.")
    overview = fetch_overview(path)
    data = hour_chart_png(overview.by_hour)
    return Response(content=data, media_type="image/png")


@router.get("/plots/pickups-by-date.png")
def plot_pickups_by_date() -> Response:
    path = _db_path()
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Database not available.")
    overview = fetch_overview(path)
    data = pickups_by_date_chart_png(overview.pickups_by_date)
    return Response(content=data, media_type="image/png")


# Backwards-friendly aliases (older relative URLs)
@router.get("/plots/status.png")
def plot_status_alias() -> RedirectResponse:
    return RedirectResponse(url="/api/v1/analytics/plots/borough.png", status_code=307)


@router.get("/plots/vehicle.png")
def plot_vehicle_alias() -> RedirectResponse:
    return RedirectResponse(url="/api/v1/analytics/plots/base.png", status_code=307)


@router.get("/plots/payment.png")
def plot_payment_alias() -> RedirectResponse:
    return RedirectResponse(url="/api/v1/analytics/plots/hour.png", status_code=307)


@router.get("/plots/timeline.png")
def plot_timeline_alias() -> RedirectResponse:
    return RedirectResponse(
        url="/api/v1/analytics/plots/pickups-by-date.png", status_code=307
    )
