"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env from backend/ then project root
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


class Settings:
    def __init__(self) -> None:
        self.session_secret: str = os.getenv(
            "SESSION_SECRET", "dev-only-insecure-secret-change-me"
        )
        self.database_url: str = os.getenv(
            "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"
        )
        # Resolve relative sqlite paths against backend/
        if self.database_url.startswith("sqlite:///./"):
            rel = self.database_url.removeprefix("sqlite:///./")
            self.database_url = f"sqlite:///{(BASE_DIR / rel).resolve()}"

        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.cors_origins: list[str] = [o.strip() for o in origins.split(",") if o.strip()]

        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.cookie_secure: bool = _bool(
            os.getenv("COOKIE_SECURE"),
            default=self.environment == "production",
        )
        # lax = same-site (works with Vercel /api proxy); none = cross-site (direct HF API)
        raw_samesite = (os.getenv("COOKIE_SAMESITE") or "lax").strip().lower()
        if raw_samesite not in {"lax", "strict", "none"}:
            raw_samesite = "lax"
        if raw_samesite == "none" and not self.cookie_secure:
            # Browsers reject SameSite=None without Secure
            self.cookie_secure = True
        self.cookie_samesite: str = raw_samesite
        self.session_max_age: int = _int(os.getenv("SESSION_MAX_AGE_SECONDS"), 86_400)

        self.max_upload_mb: int = _int(os.getenv("MAX_UPLOAD_MB"), 25)
        self.max_upload_bytes: int = self.max_upload_mb * 1024 * 1024

        upload = os.getenv("UPLOAD_DIR", "./data/uploads")
        result = os.getenv("RESULT_DIR", "./data/results")
        self.upload_dir: Path = (BASE_DIR / upload).resolve() if not Path(upload).is_absolute() else Path(upload)
        self.result_dir: Path = (BASE_DIR / result).resolve() if not Path(result).is_absolute() else Path(result)

        self.rembg_model: str = os.getenv("REMBG_MODEL", "u2net")
        self.inference_device: str = (os.getenv("INFERENCE_DEVICE") or "").strip().lower()
        self.alpha_matting: bool = _bool(os.getenv("ALPHA_MATTING"), True)
        # Alpha matting cost scales with pixel count — skip on large images by default
        self.alpha_matting_max_side: int = _int(
            os.getenv("ALPHA_MATTING_MAX_SIDE"), 1280
        )
        self.alpha_matting_foreground_threshold: int = _int(
            os.getenv("ALPHA_MATTING_FOREGROUND_THRESHOLD"), 240
        )
        self.alpha_matting_background_threshold: int = _int(
            os.getenv("ALPHA_MATTING_BACKGROUND_THRESHOLD"), 10
        )
        self.alpha_matting_erode_size: int = _int(
            os.getenv("ALPHA_MATTING_ERODE_SIZE"), 10
        )

        self.login_rate_limit: int = _int(os.getenv("LOGIN_RATE_LIMIT"), 8)
        self.login_rate_window_seconds: int = _int(
            os.getenv("LOGIN_RATE_WINDOW_SECONDS"), 300
        )
        # 3 wrong passwords → 3 hour lockout (per IP+username)
        self.login_max_failures: int = _int(os.getenv("LOGIN_MAX_FAILURES"), 3)
        self.login_lockout_seconds: int = _int(
            os.getenv("LOGIN_LOCKOUT_SECONDS"), 3 * 60 * 60
        )
        self.password_min_length: int = _int(os.getenv("PASSWORD_MIN_LENGTH"), 8)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
