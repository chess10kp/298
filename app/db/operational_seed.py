"""Operational user seed: optional env admin, plus default admin + rider accounts."""

import logging
import os
import sqlite3

import app.config as app_config
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def seed_default_accounts(conn: sqlite3.Connection) -> None:
    """Ensure default admin, rider, and driver users exist (e.g. after DB reset)."""
    pairs = [
        (app_config.DEFAULT_ADMIN_EMAIL, app_config.DEFAULT_ADMIN_PASSWORD, "admin"),
        (app_config.DEFAULT_RIDER_EMAIL, app_config.DEFAULT_RIDER_PASSWORD, "rider"),
        (app_config.DEFAULT_DRIVER_EMAIL, app_config.DEFAULT_DRIVER_PASSWORD, "driver"),
    ]
    cur = conn.cursor()
    seen: set[str] = set()
    for email_raw, password, role in pairs:
        email = email_raw.strip().lower()
        if email in seen:
            logger.warning("Skipping duplicate default email %s", email)
            continue
        seen.add(email)
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone() is not None:
            continue
        h = _pwd.hash(password)
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, h, role),
        )
        logger.info("Seeded default %s user %s", role, email)


def seed_optional_admin(conn: sqlite3.Connection) -> None:
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    email = admin_email.strip().lower()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone() is not None:
        return
    h = _pwd.hash(admin_password)
    cur.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
        (email, h),
    )
    logger.info("Seeded admin user for email %s", email)
