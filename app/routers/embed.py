"""Iframe-friendly tool pages (HTML built in Python)."""

from __future__ import annotations

from typing import Annotated

import app.config as app_config
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.deps import get_current_user_optional
from app.embed_html import (
    admin_map_embed,
    admin_map_embed_no_key,
    driver_hub_document_html,
    rider_hub_actions_embed,
    rider_hub_actions_embed_no_key,
    rider_bids_embed,
    rider_bids_embed_no_key,
)
from app.schemas.operational import UserPublic, UserRole

router = APIRouter(tags=["embed"])


def _maps_key() -> str:
    return (app_config.GOOGLE_MAPS_API_KEY or "").strip()


@router.get("/embed/driver", response_class=HTMLResponse)
def embed_driver(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> HTMLResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required"
        )
    if user.role != UserRole.driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver map is only for driver accounts.",
        )
    return HTMLResponse(driver_hub_document_html())


@router.get("/embed/admin/map", response_class=HTMLResponse)
def embed_admin_map(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> HTMLResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required"
        )
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fleet map is only for administrators.",
        )
    key = _maps_key()
    body = admin_map_embed(key) if key else admin_map_embed_no_key()
    return HTMLResponse(
        body,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/embed/rider/actions", response_class=HTMLResponse)
def embed_rider_actions(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
    coords: Annotated[
        bool,
        Query(
            description=(
                "If true, use latitude/longitude fields instead of Places search "
                "(useful when Maps Places Autocomplete is unavailable for your API key)."
            ),
        ),
    ] = False,
) -> HTMLResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required"
        )
    if user.role != UserRole.rider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This view is for rider accounts.",
        )
    if coords:
        body = rider_hub_actions_embed_no_key()
    else:
        key = _maps_key()
        body = rider_hub_actions_embed(key) if key else rider_hub_actions_embed_no_key()
    return HTMLResponse(body)


@router.get("/embed/rider/bids", response_class=HTMLResponse)
def embed_rider_bids(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> HTMLResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required"
        )
    if user.role != UserRole.rider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This view is for rider accounts.",
        )
    key = _maps_key()
    body = rider_bids_embed(key) if key else rider_bids_embed_no_key()
    return HTMLResponse(body)
