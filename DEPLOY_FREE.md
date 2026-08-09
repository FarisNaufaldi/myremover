# Deploy GRATIS — MyRemover

Tidak butuh Hugging Face PRO. **Satu service gratis di Render** melayani frontend + backend.

```text
Browser  →  https://myremover-xxxx.onrender.com  →  React + FastAPI + AI
```

Cookie session jalan di domain yang sama (paling sederhana & gratis).

---

## Yang gratis

| Layanan | Role | Biaya |
|---------|------|--------|
| **[Render](https://render.com)** Free Web Service | App lengkap | $0 |
| GitHub (opsional) | Source code | $0 |

> Render free instance **tidur** setelah ~15 menit idle. Request pertama setelah itu bisa 30–90 detik (wake up). Setelah hidup, normal lagi.

---

## Langkah cepat (UI — paling mudah)

### 1. Push project ke GitHub (gratis)

Di folder project:

```bash
cd "/Users/a/WEB REMOVE BG"
git init
git add .
git commit -m "MyRemover free deploy"
# Buat repo kosong di github.com, lalu:
git remote add origin https://github.com/USERNAME/myremover.git
git branch -M main
git push -u origin main
```

### 2. Deploy di Render

1. Daftar: https://render.com (bisa login GitHub)
2. **New +** → **Blueprint**
3. Connect repo `myremover`
4. Render membaca `render.yaml` → create service **myremover** (Free)
5. Wait build (pertama ~10–20 menit: install node + python + model ringan)

### Atau tanpa Blueprint (manual)

1. **New +** → **Web Service**
2. Connect repo
3. Settings:
   - **Runtime:** Docker  
   - **Dockerfile path:** `./Dockerfile`  
   - **Docker context:** `.`  
   - **Plan:** Free  
   - **Health check path:** `/api/ping`
4. Environment:

| Key | Value |
|-----|--------|
| `ENVIRONMENT` | `production` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `lax` |
| `REMBG_MODEL` | `u2netp` |
| `ALPHA_MATTING` | `false` |
| `SKIP_MODEL_LOAD` | `1` |
| `SESSION_SECRET` | generate random (Render “Generate”) |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | password kuatmu (min 8) |
| `ADMIN_NAME` | `Admin` |

5. **Create Web Service**

### 3. Buka website

Render memberi URL:

```text
https://myremover-xxxx.onrender.com
```

Login:

- Username: `admin`  
- Password: nilai `ADMIN_PASSWORD` (atau yang di-generate Render di dashboard → Environment)

Lalu di app: **Users** → add temanmu.

---

## Model AI di free tier

Default free: **`u2netp`** (ringan, hemat RAM ~512MB).

Kualitas bagus untuk banyak kasus; kalau butuh lebih bagus (setelah upgrade RAM / paid):

```env
REMBG_MODEL=u2net
# atau birefnet-general (lebih berat)
```

---

## Vercel (opsional, juga gratis)

Tidak wajib. Kalau mau UI di Vercel + API di Render:

1. Deploy backend Render dulu (API only juga bisa — gunakan `backend/Dockerfile` lama, atau monorepo URL).
2. Edit `frontend/vercel.json`:

```json
"destination": "https://YOUR-SERVICE.onrender.com/api/:path*"
```

3. `npx vercel --prod` di folder `frontend`

**Rekomendasi gratis:** pakai **Render all-in-one** saja (satu URL).

---

## File terkait

| File | Fungsi |
|------|--------|
| `Dockerfile` | Build frontend + backend dalam 1 image |
| `render.yaml` | Blueprint Render Free |
| `scripts/docker-entrypoint.sh` | Start di `$PORT` |
| `backend/main.py` | Serve SPA + API |

---

## Troubleshooting gratis

| Gejala | Solusi |
|--------|--------|
| Build gagal / OOM | Pastikan `REMBG_MODEL=u2netp`, `ALPHA_MATTING=false` |
| Request pertama 1 menit | Free spin-down; tunggu wake |
| Tidak bisa login | Cek `ADMIN_PASSWORD` di Render Environment; pastikan HTTPS |
| 502 setelah deploy | Tunggu health check hijau; cek Logs di Render |
| Database kosong setelah redeploy | Disk free ephemeral — set ulang `ADMIN_*` secrets (bootstrap recreate) |

Persistent DB gratis terbatas di free plan. Bisa tolerate: bootstrap admin tiap cold empty, atau re-create users via UI setelah first boot (jika disk masih ada antar restart—disk free tidak guarantee).
