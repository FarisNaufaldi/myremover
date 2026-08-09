---
title: MyRemover
emoji: ✂️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.12.0
app_file: app.py
pinned: false
license: mit
short_description: Free private AI background remover API for Vercel frontend
---

# MyRemover (Hugging Face free backend)

Gradio Space (free ZeroGPU / CPU basic — no Docker / no HF PRO).

### Limits

- Free Spaces **sleep** after long idle. First visit wakes them.
- Free always-on is not available; use paid hardware for that.

### Secrets

| Name | Example |
|------|---------|
| `ACCESS_PASSWORD` | strong password |
| `SESSION_SECRET` | long random string |
| `ACCESS_USERNAME` | `admin` (variable) |
| `REMBG_MODEL` | `u2netp` (variable) |

Frontend: Vercel with `VITE_BACKEND=gradio` and `VITE_HF_SPACE=https://….hf.space`
