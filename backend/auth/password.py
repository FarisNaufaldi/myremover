"""Password hashing with Argon2 (preferred) or bcrypt fallback."""

from __future__ import annotations

_HAS_ARGON2 = False
_HAS_BCRYPT = False

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError

    _ph = PasswordHasher(
        time_cost=3,
        memory_cost=64 * 1024,
        parallelism=2,
        hash_len=32,
        salt_len=16,
    )
    _HAS_ARGON2 = True
except ImportError:  # pragma: no cover
    _ph = None

try:
    import bcrypt

    _HAS_BCRYPT = True
except ImportError:  # pragma: no cover
    bcrypt = None  # type: ignore


def hash_password(password: str) -> str:
    if _HAS_ARGON2 and _ph is not None:
        return _ph.hash(password)
    if _HAS_BCRYPT:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    raise RuntimeError("No password hasher available. Install argon2-cffi or bcrypt.")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    # Argon2 hashes start with $argon2
    if password_hash.startswith("$argon2"):
        if not _HAS_ARGON2 or _ph is None:
            return False
        try:
            return _ph.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError, VerificationError, Exception):
            return False

    # bcrypt hashes start with $2
    if password_hash.startswith("$2") and _HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    return False


def hasher_name() -> str:
    if _HAS_ARGON2:
        return "argon2"
    if _HAS_BCRYPT:
        return "bcrypt"
    return "none"
