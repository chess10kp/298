"""FastUI JSON routes aligned with browser paths (``/api`` + pathname)."""

from __future__ import annotations

import json
from typing import Annotated, Any

import app.config as app_config
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastui import AnyComponent, components as c
from fastui.events import GoToEvent
from pydantic import BaseModel

from app.analytics_queries import fetch_overview
from app.components import build_navbar
from app.dashboard import build_dashboard
from app.deps import AdminUser, Conn, get_current_user_optional, get_db_session
from app.fruger_tailwind import BODY, H1, LINK, PAGE
from app.fruger_pages import (
    build_api_analytics,
    build_api_home,
    build_api_home_guest,
    build_driver_fastui,
)
from app.rider_dashboard import build_rider_dashboard
from app.routers.admin import admin_dashboard_fastui_json, get_admin_service
from app.schemas.operational import UserPublic, UserRole
from app.services.admin_service import AdminService
from app.services.db_session import DBSession
from app.services.ride_service import RideService

router = APIRouter(tags=["fruger-fastui"])


def _standalone_login_abs_url(request: Request) -> str:
    """Same document as ``GET /login`` (``login_html``). Full URL forces a real document load in FastUI."""
    base = str(request.base_url).rstrip("/")
    q = (request.url.query or "").strip()
    return f"{base}/login?{q}" if q else f"{base}/login"


@router.api_route("/api/auth/logout", methods=["GET", "POST"])
@router.api_route("/api/auth/logout/", methods=["GET", "POST"])
def api_auth_logout_fastui(request: Request) -> JSONResponse:
    """FastUI maps browser path ``/auth/logout`` → ``GET /api/auth/logout`` (sometimes with ``/``).

    Paths without a matching API route fall through to the SPA HTML catch-all (200 + HTML), so
    ``response.json()`` throws "Response not valid JSON". Trailing slash must be registered too.
    """
    target = _standalone_login_abs_url(request)
    payload = [
        c.FireEvent(event=GoToEvent(url=target)).model_dump(
            exclude_none=True, by_alias=True
        )
    ]
    resp = JSONResponse(payload)
    resp.delete_cookie("access_token", httponly=True, samesite="lax", path="/")
    return resp


@router.get("/api/login")
@router.get("/api/login/")
def api_login_fastui(request: Request) -> JSONResponse:
    """SPA navigates to ``/login`` by fetching JSON here; redirect to the real HTML login page."""
    target = _standalone_login_abs_url(request)
    payload = [
        c.FireEvent(event=GoToEvent(url=target)).model_dump(
            exclude_none=True, by_alias=True
        )
    ]
    return JSONResponse(payload)


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


@router.get("/api")
@router.get("/api/")
def api_root(
    request: Request,
    conn: Conn,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    rides_svc: Annotated[RideService, Depends(get_ride_service)],
) -> JSONResponse:
    """Browser ``/`` loads this JSON. Riders see the rider hub; drivers see driver redirect; others see the role dashboard."""
    if user is None:
        return _fastui_json(build_api_home_guest(user))
    if user.role == UserRole.rider:
        rides = rides_svc.list_my_rides(conn, user.id)
        return _fastui_json(
            build_rider_dashboard(user, rides, request_base=str(request.base_url))
        )
    if user.role == UserRole.driver:
        return _fastui_json(build_driver_fastui(str(request.base_url), user))
    return _fastui_json(build_api_home(user))


@router.get("/api/nyc")
@router.get("/api/nyc/")
def api_nyc_dataset(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    """Legacy NYC-only FastUI tree (formerly ``GET /api/``)."""
    return _fastui_json(build_dashboard(user))


@router.get("/api/analytics")
def api_analytics_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="NYC analytics", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="Sign in to view pickup analytics.", class_name=BODY
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/analytics"),
                        ),
                    ],
                )
            ]
        )
    overview = None
    err = None
    if app_config.DB_PATH.is_file():
        try:
            overview = fetch_overview(app_config.DB_PATH)
        except Exception as e:
            err = str(e)
    else:
        err = "Database file not found. Start the app once to create the SQLite file."
    base = str(request.base_url).rstrip("/")
    return _fastui_json(build_api_analytics(overview, err, user, request_base=base))


@router.get("/api/driver")
@router.get("/api/driver/")
@router.get("/api/drivers")
@router.get("/api/drivers/")
def api_driver_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Driver map", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="Sign in with a driver account to open the map.",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/driver"),
                        ),
                    ],
                )
            ]
        )
    if user.role != UserRole.driver:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Driver map", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="This surface is only for driver accounts.",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Fruger home")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/"),
                        ),
                    ],
                )
            ]
        )
    return _fastui_json(build_driver_fastui(str(request.base_url), user))


@router.get("/api/admin/dashboard")
@router.get("/api/admin/dashboard/")
def api_admin_dashboard_page(
    request: Request,
    conn: Conn,
    user: AdminUser,
    svc: Annotated[AdminService, Depends(get_admin_service)],
) -> JSONResponse:
    """FastUI requests ``/api`` + browser path; must not fall through to the HTML catch-all."""
    return admin_dashboard_fastui_json(conn, user, svc, request)


@router.get("/api/admin/map")
def api_admin_map_page(
    request: Request,
    conn: Conn,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    svc: Annotated[AdminService, Depends(get_admin_service)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Admin console", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="Sign in as an administrator to open the operations view.",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/admin/dashboard"),
                        ),
                    ],
                )
            ]
        )
    if user.role != UserRole.admin:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Admin console", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="The admin console is only for administrator accounts.",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Fruger home")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/"),
                        ),
                    ],
                )
            ]
        )
    return admin_dashboard_fastui_json(conn, user, svc, request)


@router.get("/api/rider/bids")
def api_rider_bids_page(
    request: Request,
    conn: Conn,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    rides_svc: Annotated[RideService, Depends(get_ride_service)],
) -> JSONResponse:
    """Same FastUI tree as the rider hub (``GET /api``): bids live on ``/``."""
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Rider hub", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="Sign in to open the rider hub (trips, bids, and requests).",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/"),
                        ),
                    ],
                )
            ]
        )
    if user.role != UserRole.rider:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Rider hub", level=1, class_name=H1),
                        build_navbar(user),
                        c.Paragraph(
                            text="The rider hub is only for rider accounts.", class_name=BODY
                        ),
                        c.Link(
                            components=[c.Text(text="Fruger home")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/"),
                        ),
                    ],
                )
            ]
        )
    rides = rides_svc.list_my_rides(conn, user.id)
    return _fastui_json(
        build_rider_dashboard(user, rides, request_base=str(request.base_url))
    )
