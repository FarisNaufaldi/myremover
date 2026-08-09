"""Bootstrap first admin from environment (for HF Spaces deploy)."""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from auth.password import hash_password
from models import User, UserRole

logger = logging.getLogger(__name__)


def ensure_bootstrap_admin(db: Session) -> None:
    """
    Create an admin if ADMIN_USERNAME + ADMIN_PASSWORD are set and
    no user with that username exists yet.

    Safe to call on every startup (idempotent by username).
    """
    username = (os.getenv("ADMIN_USERNAME") or "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD") or ""
    name = (os.getenv("ADMIN_NAME") or "Admin").strip() or "Admin"

    if not username or not password:
        # Only warn if the database is empty (first deploy without bootstrap)
        count = db.query(User).count()
        if count == 0:
            logger.warning(
                "No users in database and ADMIN_USERNAME/ADMIN_PASSWORD not set. "
                "Create an admin via: python scripts/create_admin.py"
            )
        return

    if len(password) < 8:
        logger.error("ADMIN_PASSWORD must be at least 8 characters — bootstrap skipped.")
        return

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        logger.info("Bootstrap admin '%s' already exists — skipping create.", username)
        return

    user = User(
        name=name,
        username=username,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    logger.info("Bootstrap admin created: %s", username)
