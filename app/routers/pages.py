"""HTML pages: login and driver map (hybrid UI)."""

from __future__ import annotations

from typing import Annotated

import app.config as app_config
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.deps import get_current_user_optional
from app.schemas.operational import UserPublic

router = APIRouter(tags=["pages"])

_tpl = Jinja2Templates(directory=str(app_config.ROOT / "app" / "templates"))

_DEFAULT_AFTER_LOGIN = "/api/rider/dashboard"


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
        },
    )


@router.get("/driver")
def driver_page(request: Request):
    return _tpl.TemplateResponse(
        request,
        "driver_map.html",
        {"maps_key": app_config.GOOGLE_MAPS_API_KEY},
    )
