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
from app.dashboard import build_dashboard
from app.deps import Conn, get_current_user_optional, get_db_session
from app.fruger_tailwind import BODY, H1, LINK, PAGE
from app.fruger_pages import (
    build_admin_map_fastui,
    build_api_analytics,
    build_api_home,
    build_api_home_guest,
    build_driver_fastui,
    build_rider_bids_fastui,
)
from app.rider_dashboard import build_rider_dashboard
from app.schemas.operational import UserPublic, UserRole
from app.services.db_session import DBSession
from app.services.ride_service import RideService

router = APIRouter(tags=["fruger-fastui"])


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
    """Browser ``/`` loads this JSON. Riders see the rider hub; others see the role dashboard."""
    if user is None:
        return _fastui_json(build_api_home_guest())
    if user.role == UserRole.rider:
        rides = rides_svc.list_my_rides(conn, user.id)
        return _fastui_json(
            build_rider_dashboard(user, rides, request_base=str(request.base_url))
        )
    return _fastui_json(build_api_home(user))


@router.get("/api/nyc")
@router.get("/api/nyc/")
def api_nyc_dataset() -> JSONResponse:
    """Legacy NYC-only FastUI tree (formerly ``GET /api/``)."""
    return _fastui_json(build_dashboard())


@router.get("/api/analytics")
def api_analytics_page(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="NYC analytics", level=1, class_name=H1),
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
    return _fastui_json(build_api_analytics(overview, err))


@router.get("/api/driver")
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
    return _fastui_json(build_driver_fastui(str(request.base_url)))


@router.get("/api/admin/map")
def api_admin_map_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Fleet map", level=1, class_name=H1),
                        c.Paragraph(
                            text="Sign in as an administrator to view the fleet map.",
                            class_name=BODY,
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/admin/map"),
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
                        c.Heading(text="Fleet map", level=1, class_name=H1),
                        c.Paragraph(
                            text="The fleet map is only for administrator accounts.",
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
    return _fastui_json(build_admin_map_fastui(str(request.base_url)))


@router.get("/api/rider/bids")
def api_rider_bids_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> JSONResponse:
    if user is None:
        return _fastui_json(
            [
                c.Page(
                    class_name=PAGE,
                    components=[
                        c.Heading(text="Bids", level=1, class_name=H1),
                        c.Paragraph(
                            text="Sign in to view bids on your rides.", class_name=BODY
                        ),
                        c.Link(
                            components=[c.Text(text="Sign in")],
                            class_name=LINK,
                            on_click=GoToEvent(url="/login?next=/rider/bids"),
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
                        c.Heading(text="Bids", level=1, class_name=H1),
                        c.Paragraph(
                            text="This view is for rider accounts.", class_name=BODY
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
    return _fastui_json(build_rider_bids_fastui(str(request.base_url)))
