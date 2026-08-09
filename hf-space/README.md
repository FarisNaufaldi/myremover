---
title: MyRemover
emoji: ✂️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: Free private AI background remover API for Vercel frontend
---

# MyRemover (Hugging Face free backend)

Gradio Space (works on free accounts via **ZeroGPU Gradio**, no Docker / no HF PRO).

### Limits (platform, not optional)

- Free Spaces **sleep** after long idle (~48h). First visit **wakes** them (cold start).
- Free **always-on / no sleep** is not offered by Hugging Face — only paid hardware stays warm forever.
- For free accounts you can host up to **2 Gradio ZeroGPU** Spaces.

### Secrets (Space → Settings → Variables and secrets)

| Name | Example |
|------|---------|
| `ACCESS_USERNAME` | `admin` |
| `ACCESS_PASSWORD` | strong password |
| `SESSION_SECRET` | long random string |
| `REMBG_MODEL` | `u2netp` (recommended free) |

Public variables optional: `MAX_IMAGE_SIDE=2048`.

### Frontend

Deploy `frontend/` to Vercel with:

```text
VITE_BACKEND=gradio
VITE_HF_SPACE=https://YOUR_USER-myremover.hf.space
```

See root `DEPLOY_HF_VERCEL.md`.
