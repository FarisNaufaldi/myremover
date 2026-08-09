"""
MyRemover — free Hugging Face Gradio Space backend.

Free personal HF accounts: up to 2 Gradio Spaces on ZeroGPU (no Docker / no PRO).
Hardware "always on" is NOT free — free Spaces sleep after idle and wake on visit.

Vercel frontend talks to this Space via @gradio/client.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import os
import time
from functools import lru_cache

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


def login_fn(username: str, password: str):
    u = (username or "").strip().lower()
    p = password or ""
    if u != ACCESS_USERNAME or p != ACCESS_PASSWORD:
        raise gr.Error("Invalid username or password.")
    token = issue_token(u)
    return {
        "ok": True,
        "token": token,
        "user": {"username": u, "role": "ADMIN", "name": "Admin"},
    }


def session_fn(token: str):
    try:
        user = verify_token(token)
        return {
            "authenticated": True,
            "user": {"username": user, "role": "ADMIN", "name": "Admin"},
        }
    except gr.Error:
        return {"authenticated": False, "user": None}


def logout_fn(_token: str):
    return {"logged_out": True}


def _prepare_image(image: Image.Image) -> Image.Image:
    img = image.convert("RGBA")
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / float(longest)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    return img


def remove_bg_fn(image, token: str):
    verify_token(token)
    if image is None:
        raise gr.Error("Please upload an image.")
    if isinstance(image, dict):
        # Gradio FileData from API client
        src = image.get("url") or image.get("path") or ""
        if isinstance(src, str) and src.startswith("data:"):
            header, b64 = src.split(",", 1)
            raw = __import__("base64").b64decode(b64)
            image = Image.open(io.BytesIO(raw))
        elif isinstance(src, str) and src:
            import urllib.request

            with urllib.request.urlopen(src) as resp:  # nosec B310 — Space-controlled URL
                image = Image.open(io.BytesIO(resp.read()))
        else:
            raise gr.Error("Could not read uploaded image.")
    img = _prepare_image(image)
    session = get_session()
    out = remove(img, session=session)
    if not isinstance(out, Image.Image):
        out = Image.open(io.BytesIO(out)).convert("RGBA")
    else:
        out = out.convert("RGBA")
    return out


with gr.Blocks(title="MyRemover API") as demo:
    gr.Markdown(
        "# MyRemover (HF free backend)\n"
        "Backend for the Vercel frontend. Use the website UI — or test below."
    )
    with gr.Tab("Demo"):
        token_box = gr.Textbox(label="Session token (from login)", type="password")
        with gr.Row():
            inp = gr.Image(type="pil", label="Input")
            out = gr.Image(type="pil", label="Output (transparent PNG)")
        btn = gr.Button("Remove background", variant="primary")
        btn.click(remove_bg_fn, inputs=[inp, token_box], outputs=[out], api_name="remove_bg")

    with gr.Tab("Auth (API)"):
        u = gr.Textbox(label="Username")
        p = gr.Textbox(label="Password", type="password")
        login_out = gr.JSON(label="Login result")
        gr.Button("Login").click(login_fn, inputs=[u, p], outputs=[login_out], api_name="login")

        t = gr.Textbox(label="Token")
        sess_out = gr.JSON(label="Session")
        gr.Button("Session").click(session_fn, inputs=[t], outputs=[sess_out], api_name="session")
        gr.Button("Logout").click(logout_fn, inputs=[t], outputs=[sess_out], api_name="logout")


if __name__ == "__main__":
    # HF Spaces sets env; local default 7860
    demo.queue(default_concurrency_limit=1).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        show_error=True,
    )
