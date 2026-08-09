"""FastAPI entrypoint for the private AI Background Remover."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth.routes import router as auth_router
from background_removal.rembg_provider import load_model_on_startup
from background_removal.routes import router as bg_router
from background_removal.service import cleanup_old_files
from bootstrap import ensure_bootstrap_admin
from config import get_settings
from database import SessionLocal, init_db
from schemas import ApiResponse
from users.routes import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bgremover")

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
    finally:
        db.close()
    cleanup_old_files()
    load_model_on_startup()
    logger.info("Background Remover API ready")
    yield
    cleanup_old_files()


app = FastAPI(
    title="MyRemover API",
    description="Private AI-powered background removal for authorized users only.",
    version="1.0.0",
    lifespan=lifespan,
)

# Session cookie BEFORE CORS is fine; order: last added = outermost
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else [],
    allow_origin_regex=r"https://.*\.vercel\.app" if settings.is_production else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="myremover_session",
    max_age=settings.session_max_age,
    same_site=settings.cookie_samesite,
    https_only=settings.cookie_secure,
    path="/",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(bg_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail
    if not isinstance(detail, str):
        detail = "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, error=detail).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    # Flatten first error for human-readable message
    msg = "Invalid request."
    try:
        errs = exc.errors()
        if errs:
            e0 = errs[0]
            loc = ".".join(str(x) for x in e0.get("loc", []) if x != "body")
            msg = e0.get("msg", msg)
            if loc:
                msg = f"{loc}: {msg}"
    except Exception:
        pass
    return JSONResponse(
        status_code=422,
        content=ApiResponse(success=False, error=msg).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            success=False,
            error="Something went wrong. Please try again.",
        ).model_dump(),
    )


@app.get("/api/ping")
def ping():
    return ApiResponse(success=True, data={"pong": True})


# ── SPA (frontend build) for free single-host deploy (Render, etc.) ──
if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # Never swallow API — routers are registered above; this is only unmatched paths
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Not found.")
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend not built.")
else:

    @app.get("/")
    def root():
        return ApiResponse(
            success=True,
            data={
                "service": "MyRemover API",
                "docs": "/docs",
                "hint": "Frontend not built. Run: cd frontend && npm run build && cp -r dist/* ../backend/static/",
            },
        )
