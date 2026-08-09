"""
MyRemover — free Hugging Face Gradio Space backend.
API returns plain strings (JSON text) to avoid Gradio 5 api_info bugs with dict schemas.
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

import gradio as gr
from PIL import Image
from rembg import new_session, remove

ACCESS_USERNAME = (os.getenv("ACCESS_USERNAME") or "admin").strip().lower()
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD") or "MyRemoverChangeMe123"
SESSION_SECRET = os.getenv("SESSION_SECRET") or "hf-free-change-me-please-32chars!!"
TOKEN_TTL = int(os.getenv("TOKEN_TTL_SECONDS") or "86400")
REMBG_MODEL = os.getenv("REMBG_MODEL") or "u2netp"
MAX_SIDE = int(os.getenv("MAX_IMAGE_SIDE") or "2048")

# Disable Gradio 5 SSR on Spaces (avoids Node path + crashes for API clients)
os.environ["GRADIO_SSR_MODE"] = "false"


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


def _prepare_image(image: Image.Image) -> Image.Image:
    img = image.convert("RGBA")
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / float(longest)
        img = img.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.Resampling.LANCZOS,
        )
    return img


def _to_pil(image) -> Image.Image:
    if image is None:
        raise gr.Error("Please upload an image.")
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, dict):
        src = image.get("url") or image.get("path") or ""
        if isinstance(src, str) and src.startswith("data:"):
            _header, b64 = src.split(",", 1)
            raw = base64.b64decode(b64)
            return Image.open(io.BytesIO(raw))
        if isinstance(src, str) and src:
            import urllib.request

            with urllib.request.urlopen(src) as resp:  # nosec B310
                return Image.open(io.BytesIO(resp.read()))
        raise gr.Error("Could not read uploaded image.")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(image))
    raise gr.Error("Unsupported image type.")


def remove_bg_fn(image, token: str):
    verify_token(token)
    img = _prepare_image(_to_pil(image))
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
        btn.click(
            remove_bg_fn,
            inputs=[inp, token_box],
            outputs=[out],
            api_name="remove_bg",
        )

    with gr.Tab("Auth (API)"):
        u = gr.Textbox(label="Username")
        p = gr.Textbox(label="Password", type="password")
        login_out = gr.Textbox(label="Login result (JSON text)")
        gr.Button("Login").click(
            login_fn, inputs=[u, p], outputs=[login_out], api_name="login"
        )

        t = gr.Textbox(label="Token")
        sess_out = gr.Textbox(label="Session / logout (JSON text)")
        gr.Button("Session").click(
            session_fn, inputs=[t], outputs=[sess_out], api_name="session"
        )
        gr.Button("Logout").click(
            logout_fn, inputs=[t], outputs=[sess_out], api_name="logout"
        )


# Queue once; HF Spaces auto-launches `demo` if present.
demo.queue(default_concurrency_limit=1)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
        ssr_mode=False,
    )
