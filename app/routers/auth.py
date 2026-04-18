"""Registration and JWT / session login."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import Conn, get_auth_service, get_db_session
from app.schemas.operational import LoginRequest, RegisterRequest, TokenResponse, UserPublic, UserRole
from app.services.auth_service import AuthService
from app.services.db_session import DBSession

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic)
def register(
    body: RegisterRequest,
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
) -> UserPublic:
    if body.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot register as admin")
    if db.get_user_by_email(conn, body.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    uid = db.insert_user(
        conn,
        email=body.email,
        password_hash=auth.hash_password(body.password),
        role=body.role,
    )
    row = db.get_user_by_id(conn, uid)
    assert row is not None
    return UserPublic(id=int(row["id"]), email=str(row["email"]), role=UserRole(str(row["role"])))


@router.post("/token", response_model=TokenResponse)
def issue_token(
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """OAuth2 compatible: use ``username`` for email."""
    row = db.get_user_by_email(conn, form.username)
    if row is None or not auth.verify_password(form.password, str(row["password_hash"])):
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
) -> dict[str, bool]:
    """JSON login that sets ``access_token`` httpOnly cookie for browser flows."""
    import app.config as app_config

    row = db.get_user_by_email(conn, body.email)
    if row is None or not auth.verify_password(body.password, str(row["password_hash"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = auth.create_access_token(user_id=int(row["id"]), role=str(row["role"]))
    max_age = app_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax",
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie("access_token")
    return {"ok": True}
