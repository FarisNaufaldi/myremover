# 🌐 Publikkan MyRemover — GRATIS

Repo: https://github.com/FarisNaufaldi/myremover

---

## Apa yang terjadi di Render?

Bukan "bayar langganan". Render menampilkan **Payment Information Required** supaya:

1. Ada **kartu di akun** (anti-abuse), dan  
2. Autorisasi sementara **$1** (lalu dilepas) — **tidak memotong biaya** jika plan Free.

Banyak “hosting gratis” 2025–2026 begini (Render, Fly, Railway).  
Kalau **tidak mau isi kartu sama sekali**, pakai opsi **B (Replit)** di bawah.

Blueprint juga diganti dari **Docker → Python free** (lebih cocok free tier).

---

## Opsi A — Render Free (isi kartu, $0 / bulan)

1. Push latest (repo sudah ada).  
2. **New + → Web Service** (lebih baik daripada Blueprint jika error berlanjut):
   - Repo: `FarisNaufaldi/myremover`
   - **Runtime: Python 3**
   - **Instance type: Free**
   - **Build command:**

```bash
pip install -r backend/requirements.txt && cd frontend && npm install && npm run build && mkdir -p ../backend/static && cp -r dist/* ../backend/static/
```

   - **Start command:**

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

   - Health check: `/api/ping`  
3. Environment (sama seperti `render.yaml`):  
   `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=MyRemoverChangeMe123`, `REMBG_MODEL=u2netp`, dll.  
4. Deploy.

Jika tetap diminta kartu: itu kebijakan Render. Pilih **isi kartunya** (tetap Free) atau opsi B.

---

## Opsi B — Replit Free (biasanya **tanpa** kartu)

1. Buka https://replit.com → login GitHub  
2. **Create Repl** → **Import from GitHub** → `FarisNaufaldi/myremover`  
3. Run (tombol Run) — script `replit-run.sh` yang jalan  
4. **Deploy** / Webview → dapat URL publik  
5. Login: `admin` / `MyRemoverChangeMe123`

File terkait: `.replit`, `replit-run.sh`

---

## Opsi C — Vercel (frontend) saja

Vercel gratis bagus untuk frontend, **tapi AI rembg butuh server Python** (tidak muat di serverless).  
Jadi backend tetap di Render/Replit; Vercel opsional.

---

## Login setelah live

| | |
|--|--|
| User | `admin` |
| Pass | `MyRemoverChangeMe123` |

Ganti setelah login.

---

## Ringkas

| Opsi | Kartu? | Biaya | Catatan |
|------|--------|-------|---------|
| Render Free | Biasanya **ya** (verifikasi) | $0 | Service tidur saat idle |
| Replit Free | Biasanya **tidak** | $0 | Lebih cocok “tanpa kartu” |
| HF Docker | PRO / bayar | tidak gratis | Ditolak sebelumnya |
