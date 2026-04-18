"""FastAPI dependencies: database connection, auth, service instances."""

from __future__ import annotations

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

security = HTTPBearer(auto_error=False)


def get_db_session() -> DBSession:
    return DBSession(app_config.DB_PATH)


def get_auth_service() -> AuthService:
    return AuthService()


def db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(app_config.DB_PATH)
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
        return credentials.credentials
    return request.cookies.get("access_token")


def get_current_user_optional(
    conn: Conn,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    db: Annotated[DBSession, Depends(get_db_session)],
    token: Annotated[str | None, Depends(get_token_optional)],
) -> UserPublic | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, app_config.JWT_SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        if sub is None:
            return None
        uid = int(sub)
    except (JWTError, ValueError, TypeError):
        return None
    row = db.get_user_by_id(conn, uid)
    if row is None:
        return None
    return UserPublic(
        id=int(row["id"]),
        email=str(row["email"]),
        role=UserRole(str(row["role"])),
    )


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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _inner


CurrentUser = Annotated[UserPublic, Depends(get_current_user)]
RiderUser = Annotated[UserPublic, Depends(require_roles(UserRole.rider))]
DriverUser = Annotated[UserPublic, Depends(require_roles(UserRole.driver))]
AdminUser = Annotated[UserPublic, Depends(require_roles(UserRole.admin))]
