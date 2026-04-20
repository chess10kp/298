"""FastAPI dependencies: database connection, auth, service instances."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from typing import Annotated

import app.config as app_config
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from app.schemas.operational import UserPublic, UserRole
from app.services.auth_service import AuthService
from app.services.db_session import DBSession

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def get_db_session() -> DBSession:
    return DBSession(app_config.DB_PATH)


def get_auth_service() -> AuthService:
    return AuthService()


def db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(app_config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(db_connection)]


def get_token_optional(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> str | None:
    if credentials is not None and credentials.credentials:
        logger.info(f"Token from Bearer header: {credentials.credentials[:20]}...")
        return credentials.credentials
    cookie_token = request.cookies.get("access_token")
    logger.info(f"Token from cookie: {cookie_token[:20] if cookie_token else None}...")
    logger.info(f"All cookies: {dict(request.cookies)}")
    return cookie_token


def get_current_user_optional(
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
    token: Annotated[str | None, Depends(get_token_optional)],
) -> UserPublic | None:
    if not token:
        logger.info("No token found, returning None user")
        return None
    try:
        payload = jwt.decode(
            token, app_config.JWT_SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        if sub is None:
            logger.info("No 'sub' in token payload, returning None user")
            return None
        uid = int(sub)
        logger.info(f"Decoded token for user_id: {uid}")
    except (JWTError, ValueError, TypeError) as e:
        logger.info(f"Token decode error: {e}, returning None user")
        return None
    row = db.get_user_by_id(conn, uid)
    if row is None:
        logger.info(f"User not found in DB for id: {uid}, returning None user")
        return None
    user = UserPublic(
        id=int(row["id"]),
        email=str(row["email"]),
        role=UserRole(str(row["role"])),
    )
    logger.info(f"Found user: {user.email} (role: {user.role})")
    return user


def get_current_user(
    user: Annotated[UserPublic | None, Depends(get_current_user_optional)],
) -> UserPublic:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: UserRole):
    def _inner(user: Annotated[UserPublic, Depends(get_current_user)]) -> UserPublic:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return _inner


CurrentUser = Annotated[UserPublic, Depends(get_current_user)]
RiderUser = Annotated[UserPublic, Depends(require_roles(UserRole.rider))]
DriverUser = Annotated[UserPublic, Depends(require_roles(UserRole.driver))]
AdminUser = Annotated[UserPublic, Depends(require_roles(UserRole.admin))]
