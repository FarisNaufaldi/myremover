#!/usr/bin/env python3
"""Create the first admin user (or additional admin via CLI).

Usage (from backend/ directory):

    python scripts/create_admin.py --name "Admin" --username admin --password 'your-secure-password'

Or interactive:

    python scripts/create_admin.py
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

# Ensure backend/ is on path when executed as a script
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Skip heavy model load when only creating admin
import os

os.environ.setdefault("SKIP_MODEL_LOAD", "1")

from auth.password import hash_password  # noqa: E402
from config import get_settings  # noqa: E402
from database import SessionLocal, init_db  # noqa: E402
from models import User, UserRole  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--name", default=None)
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    settings = get_settings()
    min_len = settings.password_min_length

    name = args.name or input("Name: ").strip()
    username = (args.username or input("Username: ")).strip().lower()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.", file=sys.stderr)
            return 1

    if not name or not username or not password:
        print("Name, username, and password are required.", file=sys.stderr)
        return 1
    if len(password) < min_len:
        print(f"Password must be at least {min_len} characters.", file=sys.stderr)
        return 1

    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Username '{username}' already exists.", file=sys.stderr)
            return 1
        user = User(
            name=name,
            username=username,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin created: {username} (id={user.id})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
