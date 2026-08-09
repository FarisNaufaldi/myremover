---
title: MyRemover API
emoji: ✂️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# MyRemover API

Private AI background remover backend (FastAPI + rembg/u2net).

Deployed for the MyRemover frontend on Vercel.

## Secrets (Space Settings → Secrets)

| Name | Required | Description |
|------|----------|-------------|
| `SESSION_SECRET` | yes | Long random string for signed cookies |
| `ADMIN_USERNAME` | yes (first boot) | Bootstrap admin username |
| `ADMIN_PASSWORD` | yes (first boot) | Bootstrap admin password (min 8 chars) |
| `ADMIN_NAME` | no | Default `Admin` |

## Variables (optional)

| Name | Default |
|------|---------|
| `CORS_ORIGINS` | (allows `*.vercel.app` in production) |
| `REMBG_MODEL` | `u2net` |
| `MAX_UPLOAD_MB` | `15` |
| `ALPHA_MATTING_MAX_SIDE` | `1280` |

## Notes

- SQLite is **ephemeral** on free HF Spaces (resets on rebuild/restart unless you add storage).
- After bootstrap, manage users from the admin UI.
- Cold starts on free CPU can take a minute while the container wakes up.
