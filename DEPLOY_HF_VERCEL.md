# Deploy free: Hugging Face Gradio Space (backend) + Vercel (frontend)

## Reality check (read once)

| Claim | Truth |
|-------|--------|
| HF free + MyRemover Docker/FastAPI | **No** — Docker Spaces need **HF PRO** |
| HF free backend | **Yes** — Gradio Space (max 2, ZeroGPU ok) |
| Worker never sleeps | **No free option** on HF. Free Spaces **sleep** after long idle; **wake on visit** (~30–90s) |
| Continuous *use* while people open the site | **Yes** — Space auto-restarts when hit |

“Jalan terus” di free tier = **bisa dipakai kapan saja** (auto wake), **bukan** server 24/7 tanpa sleep.

---

## Architecture

```text
Browser  →  Vercel (React UI)  →  Hugging Face Gradio Space (rembg AI)
```

Auth: username/password → short-lived token in browser sessionStorage (no cross-site cookies).

---

## 1) Backend — Hugging Face (free)

1. Login https://huggingface.co (account: e.g. FeynmanProject)
2. **New Space**
   - Name: `myremover`
   - SDK: **Gradio**
   - Hardware: **ZeroGPU** if listed (free allowance for personal accounts), else any free Gradio option you still have
   - Visibility: **Public** (required for simplest free access) or Protected if your plan allows
3. Upload folder `hf-space/` contents into the Space root:
   - `app.py`
   - `requirements.txt`
   - `README.md` (YAML header)
4. **Settings → Variables and secrets**

| Type | Key | Value |
|------|-----|--------|
| Secret | `ACCESS_PASSWORD` | strong password |
| Secret | `SESSION_SECRET` | long random |
| Variable | `ACCESS_USERNAME` | `admin` |
| Variable | `REMBG_MODEL` | `u2netp` |

5. Wait until Space status is **Running**
6. Note URL:
   ```text
   https://huggingface.co/spaces/USERNAME/myremover
   App: https://USERNAME-myremover.hf.space
   ```
   (slug is lower-case, slash → hyphen)

### CLI alternative

```bash
# install: pip install -U "huggingface_hub[cli]"
hf auth login
cd hf-space
# Create Gradio space (UI recommended if CLI flags change)
# Then:
hf upload USERNAME/myremover . --repo-type=space
```

---

## 2) Frontend — Vercel (free)

1. Import GitHub repo https://github.com/FarisNaufaldi/myremover (or push this project)
2. **Root Directory:** `frontend`
3. **Environment variables** (Production):

| Name | Value |
|------|--------|
| `VITE_BACKEND` | `gradio` |
| `VITE_HF_SPACE` | `https://USERNAME-myremover.hf.space` |

4. Deploy
5. Open Vercel URL → login with `admin` + `ACCESS_PASSWORD`

`vercel.json` only serves the SPA (no cookie proxy needed).

---

## 3) Local test (optional)

```bash
# Terminal A — Gradio
cd hf-space
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ACCESS_PASSWORD=test1234
export SESSION_SECRET=dev-secret
python app.py

# Terminal B — frontend
cd frontend
echo 'VITE_BACKEND=gradio' > .env.local
echo 'VITE_HF_SPACE=http://127.0.0.1:7860' >> .env.local
npm install
npm run dev
```

---

## Limits & ops

- **First request after sleep**: slow (wake + maybe model load).
- **Model**: `u2netp` (light). Heavier models may OOM on free.
- **Users admin page**: disabled in Gradio mode (single shared admin account).
- **SQLite multi-user FastAPI**: still available on Render/Replit if you need full admin.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login fails | Check Space secrets; Space Running; open HF Space URL manually |
| “Space is waking up” | Wait and retry; keep Space open once while processing |
| CORS / client errors | Set exact `VITE_HF_SPACE` without trailing slash; rebuild Vercel |
| Build fail on HF (rembg) | Keep `u2netp`; check Space logs |
| 402 / PRO for Docker | Do **not** use Docker SDK — this stack is **Gradio only** |

---

## Files

| Path | Role |
|------|------|
| `hf-space/` | Free HF Gradio backend |
| `frontend/src/api/gradio.js` | Browser → Space client |
| `frontend/src/api/client.js` | Switches `fastapi` / `gradio` |
| `frontend/vercel.json` | SPA host on Vercel |
