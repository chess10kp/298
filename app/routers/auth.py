"""Registration and JWT / session login."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastui import components as c
from fastui.events import GoToEvent

from app.deps import Conn, get_auth_service, get_db_session
from app.schemas.operational import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
    UserRole,
)
from app.services.auth_service import AuthService
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserPublic)
def register(
    body: RegisterRequest,
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
) -> UserPublic:
    if body.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot register as admin"
        )
    if db.get_user_by_email(conn, body.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    uid = db.insert_user(
        conn,
        email=body.email,
        password_hash=auth.hash_password(body.password),
        role=body.role,
    )
    row = db.get_user_by_id(conn, uid)
    assert row is not None
    return UserPublic(
        id=int(row["id"]), email=str(row["email"]), role=UserRole(str(row["role"]))
    )


@router.post("/token", response_model=TokenResponse)
def issue_token(
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """OAuth2 compatible: use ``username`` for email."""
    row = db.get_user_by_email(conn, form.username)
    if row is None or not auth.verify_password(
        form.password, str(row["password_hash"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(user_id=int(row["id"]), role=str(row["role"]))
    return TokenResponse(access_token=token)


@router.post("/session")
def create_session(
    body: LoginRequest,
    response: Response,
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """JSON login that sets ``access_token`` httpOnly cookie for browser flows."""
    import app.config as app_config

    logger.info(f"SESSION LOGIN: email={body.email}")
    row = db.get_user_by_email(conn, body.email)
    if row is None or not auth.verify_password(
        body.password, str(row["password_hash"])
    ):
        logger.error(f"SESSION LOGIN FAILED: email={body.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = auth.create_access_token(user_id=int(row["id"]), role=str(row["role"]))
    max_age = app_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    logger.info(f"SETTING COOKIE: key=access_token, max_age={max_age}, httponly=True")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax",
        path="/",
    )
    user_role = str(row["role"])
    logger.info(f"SESSION LOGIN SUCCESS: user_id={row['id']}, email={body.email}, role={user_role}")
    
    redirect_url = None
    if user_role == "admin":
        redirect_url = "/admin/dashboard"
    
    return {"ok": True, "redirect": redirect_url}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    logger.info(f"LOGOUT POST CALLED")
    logger.info(f"COOKIES BEFORE DELETE: {dict(request.cookies)}")
    response.delete_cookie("access_token", httponly=True, samesite="lax", path="/")
    logger.info(
        f"COOKIE DELETED: access_token with httponly=True, samesite=lax, path=/"
    )
    return {"ok": True}


@router.get("/logout")
def logout_get(request: Request, response: Response) -> JSONResponse:
    """GET logout — clears cookie and tells FastUI client to navigate to /."""
    logger.info(f"LOGOUT GET CALLED")
    logger.info(f"COOKIES BEFORE DELETE: {dict(request.cookies)}")
    logger.info(f"REQUEST HEADERS: {dict(request.headers)}")
    response.delete_cookie("access_token", httponly=True, samesite="lax", path="/")
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("access_token")
    logger.info("DELETED access_token WITH ALL POSSIBLE PARAMETER COMBINATIONS")
    base = str(request.base_url).rstrip("/")
    login_abs = f"{base}/login"
    fire_event = c.FireEvent(event=GoToEvent(url=login_abs))
    resp = JSONResponse([fire_event.model_dump(exclude_none=True, by_alias=True)])
    for key, value in response.headers.items():
        if key.lower() == "set-cookie":
            resp.headers[key] = value
    logger.info(f"RESPONSE HEADERS: {dict(resp.headers)}")
    return resp
