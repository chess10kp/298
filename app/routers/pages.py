"""Browser routes: FastUI shells (``fruger_prebuilt_html``) and standalone login HTML."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.deps import get_current_user_optional
from app.fastui_html import fruger_prebuilt_html
from app.login_html import render_login_page
from app.schemas.operational import UserPublic, UserRole

router = APIRouter(tags=["pages"])


def _shell(title: str) -> HTMLResponse:
    return HTMLResponse(fruger_prebuilt_html(title=title))


_DEFAULT_AFTER_LOGIN = "/"


def _safe_next_url(raw: str | None) -> str:
    """Allow only same-site relative paths (avoid open redirects)."""
    if not raw:
        return _DEFAULT_AFTER_LOGIN
    s = raw.strip()
    if s.startswith("/") and not s.startswith("//"):
        return s
    return _DEFAULT_AFTER_LOGIN


@router.get("/")
def home_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(url="/login?next=/", status_code=status.HTTP_302_FOUND)
    if user.role == UserRole.rider:
        return _shell("Rider hub — Fruger")
    return _shell("Dashboard — Fruger")


@router.get("/analytics")
def analytics_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(
            url="/login?next=/analytics",
            status_code=status.HTTP_302_FOUND,
        )
    return _shell("NYC analytics — Fruger")


@router.get("/login")
def login_page(
    request: Request,
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
):
    next_url = _safe_next_url(request.query_params.get("next"))
    return HTMLResponse(render_login_page(user=user, next_url=next_url))


@router.get("/driver")
def driver_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(url="/login?next=/driver", status_code=status.HTTP_302_FOUND)
    if user.role != UserRole.driver:
        _forbidden_driver()
    return _shell("Driver — Fruger")


@router.get("/admin/map")
def admin_map_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(
            url="/login?next=/admin/map",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.admin:
        _forbidden_admin()
    return _shell("Fleet map — Fruger")


@router.get("/rider/dashboard")
def rider_dashboard_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    """Legacy URL; rider hub lives at ``/``."""
    if user is None:
        return RedirectResponse(
            url="/login?next=/",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.rider:
        _forbidden_rider()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_shell(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(
            url="/login?next=/admin/dashboard",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.admin:
        _forbidden_admin()
    return _shell("Fruger · Admin")


@router.get("/rider/bids")
def rider_bids_page(user: Annotated[UserPublic | None, Depends(get_current_user_optional)]):
    if user is None:
        return RedirectResponse(
            url="/login?next=/rider/bids",
            status_code=status.HTTP_302_FOUND,
        )
    if user.role != UserRole.rider:
        _forbidden_rider()
    return _shell("Bids — Fruger")


def _forbidden_driver() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The driver map is only for ride-share partner (driver) accounts.",
    )


def _forbidden_admin() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The fleet map is only for administrator accounts.",
    )


def _forbidden_rider() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This page is for rider accounts.",
    )
