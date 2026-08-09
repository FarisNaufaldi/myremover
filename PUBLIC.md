# 🌐 Deploy MyRemover (FREE, public)

## Sudah siap di GitHub

**Repo publik:** https://github.com/FarisNaufaldi/myremover

---

## 1 langkah ke Render (gratis)

### Klik link ini (login GitHub di Render jika diminta):

### 👉 [Deploy ke Render Free](https://render.com/deploy?repo=https://github.com/FarisNaufaldi/myremover)

Atau manual:

1. Buka https://dashboard.render.com  
2. **New +** → **Blueprint**  
3. Connect repo **FarisNaufaldi/myremover**  
4. Apply `render.yaml`  
5. Pastikan `ADMIN_PASSWORD` = `MyRemoverChangeMe123` (atau ganti di Environment)  
6. **Apply** / Create

Build pertama: **10–20 menit**.

---

## Setelah live

URL akan mirip:

```text
https://myremover-xxxx.onrender.com
```

### Login admin (default)

| | |
|--|--|
| Username | `admin` |
| Password | `MyRemoverChangeMe123` |

**Segera ganti password** lewat Users → Reset password (atau ubah env `ADMIN_PASSWORD` + clear disk/redeploy jika bootstrap sudah lewat).

---

## Catatan free tier

- Service **tidur** setelah ~15 menit idle → request pertama bisa lambat.  
- Model AI ringan: `u2netp` (hemat RAM gratis).  
- Disk ephemeral: database bisa hilang saat rebuild — user admin bootstrap dibuat ulang dari env.

---

## Checklist

- [x] Code di GitHub (public)  
- [ ] Deploy Blueprint Render (klik link di atas)  
- [ ] Buka URL → login admin  
- [ ] Users → add teman  
- [ ] Ganti password admin  
