"""
MyRemover — HF Gradio backend (string-only API — avoids Gradio 5 schema crashes).
Endpoints:
  login(username, password) -> JSON string
  session(token) -> JSON string
  logout(token) -> JSON string
  remove_bg(image_b64, token) -> PNG base64 string (no data: prefix)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import time
from functools import lru_cache

# Must be set BEFORE importing gradio
os.environ["GRADIO_SSR_MODE"] = "false"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "false"

import gradio as gr
from PIL import Image
from rembg import new_session, remove

ACCESS_USERNAME = (os.getenv("ACCESS_USERNAME") or "admin").strip().lower()
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD") or "MyRemoverChangeMe123"
SESSION_SECRET = os.getenv("SESSION_SECRET") or "hf-free-change-me-please-32chars!!"
TOKEN_TTL = int(os.getenv("TOKEN_TTL_SECONDS") or "86400")
REMBG_MODEL = os.getenv("REMBG_MODEL") or "u2netp"
MAX_SIDE = int(os.getenv("MAX_IMAGE_SIDE") or "2048")


def _sign(payload: str) -> str:
    return hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]


def issue_token(username: str) -> str:
    exp = int(time.time()) + TOKEN_TTL
    payload = f"{username.strip().lower()}:{exp}"
    return f"{payload}:{_sign(payload)}"


def verify_token(token: str | None) -> str:
    if not token or not isinstance(token, str) or token.count(":") != 2:
        raise gr.Error("Not signed in. Please log in again.")
    user, exp_s, sig = token.split(":", 2)
    payload = f"{user}:{exp_s}"
    if not hmac.compare_digest(sig, _sign(payload)):
        raise gr.Error("Invalid session. Please log in again.")
    try:
        exp = int(exp_s)
    except ValueError as exc:
        raise gr.Error("Invalid session. Please log in again.") from exc
    if time.time() > exp:
        raise gr.Error("Session expired. Please log in again.")
    return user


@lru_cache(maxsize=1)
def get_session():
    return new_session(REMBG_MODEL)


def _decode_image_b64(image_b64: str) -> Image.Image:
    if not image_b64 or not isinstance(image_b64, str):
        raise gr.Error("Please upload an image.")
    raw = image_b64.strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    # strip whitespace/newlines
    raw = "".join(raw.split())
    try:
        data = base64.b64decode(raw, validate=False)
    except Exception as exc:
        raise gr.Error("Invalid image data.") from exc
    return Image.open(io.BytesIO(data)).convert("RGBA")


def _prepare_image(img: Image.Image) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / float(longest)
        img = img.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.Resampling.LANCZOS,
        )
    return img


def login_fn(username: str, password: str) -> str:
    u = (username or "").strip().lower()
    p = password or ""
    if u != ACCESS_USERNAME or p != ACCESS_PASSWORD:
        raise gr.Error("Invalid username or password.")
    token = issue_token(u)
    return json.dumps(
        {
            "ok": True,
            "token": token,
            "user": {"username": u, "role": "ADMIN", "name": "Admin"},
        }
    )


def session_fn(token: str) -> str:
    try:
        user = verify_token(token)
        return json.dumps(
            {
                "authenticated": True,
                "user": {"username": user, "role": "ADMIN", "name": "Admin"},
            }
        )
    except gr.Error:
        return json.dumps({"authenticated": False, "user": None})


def logout_fn(_token: str) -> str:
    return json.dumps({"logged_out": True})


def remove_bg_fn(image_b64: str, token: str) -> str:
    """Return raw base64 PNG (no data: prefix)."""
    verify_token(token)
    img = _prepare_image(_decode_image_b64(image_b64))
    session = get_session()
    out = remove(img, session=session)
    if not isinstance(out, Image.Image):
        out = Image.open(io.BytesIO(out)).convert("RGBA")
    else:
        out = out.convert("RGBA")
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=False)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# Text-only components → stable /info and /api schemas on Gradio 5
with gr.Blocks(title="MyRemover API") as demo:
    gr.Markdown(
        "# MyRemover API (HF)\n"
        "Use **Vercel frontend**. Demo fields below are for API testing only."
    )
    with gr.Tab("Login"):
        user_in = gr.Textbox(label="username")
        pass_in = gr.Textbox(label="password", type="password")
        login_out = gr.Textbox(label="result")
        gr.Button("login").click(
            login_fn, [user_in, pass_in], [login_out], api_name="login"
        )
    with gr.Tab("Session"):
        tok = gr.Textbox(label="token")
        sess_out = gr.Textbox(label="result")
        gr.Button("session").click(
            session_fn, [tok], [sess_out], api_name="session"
        )
        gr.Button("logout").click(
            logout_fn, [tok], [sess_out], api_name="logout"
        )
    with gr.Tab("Remove BG"):
        img_b64 = gr.Textbox(
            label="image base64 (raw or data-url)",
            lines=3,
            max_lines=5,
        )
        tok2 = gr.Textbox(label="token", type="password")
        out_b64 = gr.Textbox(label="png base64 result", lines=3)
        gr.Button("remove_bg").click(
            remove_bg_fn, [img_b64, tok2], [out_b64], api_name="remove_bg"
        )

demo.queue(default_concurrency_limit=1)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        show_error=True,
        ssr_mode=False,
        show_api=True,
    )
