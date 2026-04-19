"""HTML pages: login and driver map (hybrid UI)."""

from __future__ import annotations

from typing import Annotated

import app.config as app_config
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_current_user_optional
from app.schemas.operational import UserPublic, UserRole

router = APIRouter(tags=["pages"])

_tpl = Jinja2Templates(directory=str(app_config.ROOT / "app" / "templates"))


@router.get("/")
def home_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    if user is None:
        return RedirectResponse(url="/login?next=/", status_code=status.HTTP_302_FOUND)
    return _tpl.TemplateResponse(
        request,
        "home.html",
        {"user": user, "nav_active": "home"},
    )


@router.get("/analytics")
def analytics_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    if user is None:
        return RedirectResponse(
            url="/login?next=/analytics",
            status_code=status.HTTP_302_FOUND,
        )
    overview = None
    analytics_error = None
    if app_config.DB_PATH.is_file():
        try:
            from app.analytics_queries import fetch_overview

            overview = fetch_overview(app_config.DB_PATH)
        except Exception as e:
            analytics_error = str(e)
    else:
        analytics_error = "Database file not found. Start the app once to create the SQLite file."
    return _tpl.TemplateResponse(
        request,
        "analytics.html",
        {
            "user": user,
            "nav_active": "analytics",
            "overview": overview,
            "analytics_error": analytics_error,
        },
    )

_DEFAULT_AFTER_LOGIN = "/"


def _safe_next_url(raw: str | None) -> str:
    """Allow only same-site relative paths (avoid open redirects)."""
    if not raw:
        return _DEFAULT_AFTER_LOGIN
    s = raw.strip()
    if s.startswith("/") and not s.startswith("//"):
        return s
    return _DEFAULT_AFTER_LOGIN


@router.get("/login")
def login_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    next_url = _safe_next_url(request.query_params.get("next"))
    cfg = app_config
    return _tpl.TemplateResponse(
        request,
        "login.html",
        {
            "user": user,
            "next_url": next_url,
            "show_default_hints": cfg.SHOW_DEFAULT_ACCOUNT_HINTS,
            "default_rider_email": cfg.DEFAULT_RIDER_EMAIL,
            "default_rider_password": cfg.DEFAULT_RIDER_PASSWORD,
            "default_admin_email": cfg.DEFAULT_ADMIN_EMAIL,
            "default_admin_password": cfg.DEFAULT_ADMIN_PASSWORD,
            "default_driver_email": cfg.DEFAULT_DRIVER_EMAIL,
            "default_driver_password": cfg.DEFAULT_DRIVER_PASSWORD,
        },
    )


@router.get("/driver")
def driver_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    if user is None:
        return RedirectResponse(url="/login?next=/driver", status_code=status.HTTP_302_FOUND)
    if user.role != UserRole.driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The driver map is only for ride-share partner (driver) accounts.",
        )
    return _tpl.TemplateResponse(
        request,
        "driver_map.html",
        {"maps_key": app_config.GOOGLE_MAPS_API_KEY},
    )


@router.get("/admin/map")
def admin_map_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    if user is None:
        return RedirectResponse(
            url="/login?next=/admin/map",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The fleet map is only for administrator accounts.",
        )
    return _tpl.TemplateResponse(
        request,
        "admin_map.html",
        {"maps_key": app_config.GOOGLE_MAPS_API_KEY},
    )


@router.get("/rider/bids")
def rider_bids_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    if user is None:
        return RedirectResponse(
            url="/login?next=/rider/bids",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.rider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This page is for rider accounts.",
        )
    return _tpl.TemplateResponse(
        request,
        "rider_bids.html",
        {"maps_key": app_config.GOOGLE_MAPS_API_KEY},
    )
