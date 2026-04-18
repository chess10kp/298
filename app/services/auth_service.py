"""Registration, password hashing, and JWT issuance."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import app.config as app_config
from jose import jwt
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthService:
    def hash_password(self, password: str) -> str:
        return _pwd.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return _pwd.verify(plain, hashed)

    def create_access_token(self, *, user_id: int, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=app_config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode: dict[str, Any] = {
            "sub": str(user_id),
            "role": role,
            "exp": expire,
        }
        return jwt.encode(
            to_encode,
            app_config.JWT_SECRET_KEY,
            algorithm=app_config.JWT_ALGORITHM,
        )
