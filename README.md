# MyRemover — Private AI Background Remover

Private, production-quality AI background removal for authorized users only.
No public registration.

Visual design follows the **anime-recommender-api** design system
(Instrument Serif + Inter, liquid-glass panels, floating nav pill, mesh gradient backdrop, dark/light theme).

**Public deploy GRATIS (tanpa HF PRO):**

- [**HF Gradio + Vercel**](./DEPLOY_HF_VERCEL.md) — backend gratis di Hugging Face, UI di Vercel (Space free bisa **sleep**, auto-wake saat dibuka)
- [Render Free all-in-one](./DEPLOY_FREE.md) — satu URL


---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, Tailwind CSS, React Router |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Auth | HTTP-only session cookies, Argon2 password hashing |
| AI | [rembg](https://github.com/danielgatis/rembg) (default **u2net**; optional **BiRefNet General**) with alpha matting + edge refinement |

### Model license

Default model: **u2net** via rembg (loads quickly, often already cached under `~/.u2net/`).

For higher cutout quality (hair, fine edges), set in `.env`:

```env
REMBG_MODEL=birefnet-general
```

Then restart the backend (first run downloads ~973MB ONNX to `~/.u2net/`).

- BiRefNet weights used by rembg’s `birefnet-general` session are **MIT**-licensed ([ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet)).
- Other options: `birefnet-portrait`, `isnet-general-use`, `u2net`.

---

## Project layout

```text
.
├── backend/
│   ├── auth/                  # login, logout, session
│   ├── users/                 # admin user management
│   ├── background_removal/    # AI pipeline
│   ├── scripts/create_admin.py
│   ├── main.py
│   └── requirements.txt
├── frontend/                  # React app (design system from anime-recommender)
├── .env.example
└── README.md
```

---

## Prerequisites

- **Python 3.11–3.13** recommended (3.13 works well on macOS)
- **Node.js 18+**
- ~200–500 MB disk free for the BiRefNet ONNX model (downloaded on first run)

---

## 1. Backend setup

```bash
cd backend

# Virtual environment
python3.13 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Environment
cp ../.env.example .env
# Edit SESSION_SECRET to a long random string before production use
```

### Create the first admin

There is no public signup. Bootstrap the first admin via CLI:

```bash
cd backend
source .venv/bin/activate
python scripts/create_admin.py --name "Admin" --username admin --password 'your-secure-password'
```

Interactive mode:

```bash
python scripts/create_admin.py
```

### Run the API

```bash
cd backend
source .venv/bin/activate
# Skip heavy model load when only testing auth:
# SKIP_MODEL_LOAD=1 uvicorn main:app --reload --port 8000

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

First start downloads the rembg model if missing. Subsequent starts load it once into memory.

GPU: set `INFERENCE_DEVICE=cuda` and install `onnxruntime-gpu` if you have CUDA.
On Apple Silicon, ONNX uses CPU (quality-first default).

Health:

```bash
curl http://localhost:8000/api/health
```

---

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

Vite proxies `/api/*` → `http://localhost:8000`.

Production build:

```bash
cd frontend
npm run build
npm run preview
```

---

## Environment variables

See `.env.example`. Important keys:

| Variable | Purpose |
|----------|---------|
| `SESSION_SECRET` | Signed session cookie secret |
| `DATABASE_URL` | Default SQLite path |
| `CORS_ORIGINS` | Allowed frontend origins |
| `COOKIE_SECURE` | `true` behind HTTPS |
| `MAX_UPLOAD_MB` | Upload size limit |
| `REMBG_MODEL` | rembg model name |
| `ALPHA_MATTING` | Soft-edge matting for hair/fur |
| `SKIP_MODEL_LOAD` | `1` for light CLI/admin tools |

Never commit a real `.env`.

---

## Workflow

```text
Create admin (CLI)
  → Login
  → (Admin) Users → Add User
  → New user login
  → Upload image (JPG / PNG / WEBP)
  → AI background removal + edge refinement
  → Before / after slider
  → Download transparent PNG
  → Logout
```

### Roles

- **ADMIN** — Background Remover + full user management
- **USER** — Background Remover only

Admin API routes enforce `requireAdmin()` server-side. Users cannot self-register.

---

## API overview

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/session

POST /api/remove-background   # multipart file, auth required

GET    /api/users
POST   /api/users
PATCH  /api/users/:id
DELETE /api/users/:id
POST   /api/users/:id/reset-password

GET  /api/health
```

Response envelope:

```json
{ "success": true, "data": {} }
```

```json
{ "success": false, "error": "Human readable message" }
```

---

## Processing pipeline

```text
Original image
  → EXIF normalize / RGB
  → BiRefNet segmentation (rembg)
  → Optional alpha matting
  → Edge / alpha refinement + soft decontamination
  → Full-resolution RGBA PNG
```

- Soft alpha is preserved (not crude 0.5 thresholds)
- Output dimensions match the input when possible
- Temporary uploads are deleted after processing

---

## Security notes

- Passwords hashed with **Argon2** (bcrypt available as install fallback)
- HTTP-only signed session cookies (`SameSite=Lax`, `Secure` in production)
- Login rate limiting
- Disabled users lose sessions (`session_version` bump)
- No public registration
- File type validated by content (Pillow), not extension alone
- Password hashes never returned to the client

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login works but processing fails | Check backend logs; first model download may still be running |
| `ModuleNotFoundError: rembg` | Activate venv and `pip install -r requirements.txt` |
| CORS errors | Add your frontend origin to `CORS_ORIGINS` |
| Session lost after restart | Expected if cookie domain/port changes; re-login |
| Slow inference | Use a smaller image, GPU (`cuda`), or `isnet-general-use` model |
| Cannot delete last admin | Intentional safeguard — keep one active admin |

---

## Production checklist

1. Set strong `SESSION_SECRET`
2. `ENVIRONMENT=production` and `COOKIE_SECURE=true` (HTTPS)
3. Restrict `CORS_ORIGINS`
4. Run behind reverse proxy (nginx / Caddy)
5. Back up `data/app.db`
6. Optionally switch SQLite → PostgreSQL via `DATABASE_URL`

---

## Design credit

UI/UX patterns ported from the local `anime-recommender-api` project so this app shares the same visual language (typography, glass surfaces, nav, theme system).
