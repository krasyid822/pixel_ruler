# AGENTS.md

## Tentang proyek ini

**Pixel Ruler** adalah aplikasi web (PWA) file-tunggal untuk membaca koordinat pixel
pada gambar. Pengguna membuka gambar, mengarahkan kursor untuk membaca koordinat
titik, atau klik-tarik untuk mengukur area (rectangle) dengan koordinat dan ukuran.

### File utama

| File | Peran |
|------|-------|
| `index.html` | Aplikasi utama (HTML+CSS+JS, tanpa build step) |
| `sw.js` | Service worker; cache-first untuk aset statis, network-first untuk navigasi |
| `manifest.webmanifest` | Manifest PWA (standalone, ikon 192/512, maskable) |
| `icons/` | `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` |

### Cara menjalankan

PWA hanya berfungsi melalui HTTP/HTTPS (service worker tidak berjalan via `file://`):

```bash
python3 -m http.server 8000   # lalu buka http://localhost:8000
```

## Format data koordinat yang disalin (paling penting)

Aplikasi ini menyalin informasi koordinat ke clipboard dalam dua format teks
terstruktur. **Saat menerima data ini sebagai konteks/MCP, interpretasikan persis
seperti di bawah.**

### 1. Koordinat titik (cursor)

```
(x, y)
```

Contoh: `(120, 340)`

### 2. Seleksi area (klik-tarik)

```
(x1=<x>, y1=<y>) (x2=<x>, y2=<y>) ukuran=<w>x<h>px
```

Contoh: `(x1=100, y1=50) (x2=250, y2=180) ukuran=150x130px`

### Sistem koordinat

- **Origin (0,0)** = piksel kiri-atas gambar asli. Berlaku juga saat zoom (koordinat
  selalu dikembalikan ke piksel gambar asli, bukan piksel layar).
- **Satuan** = piksel gambar asli; nilai **integer** (hasil `floor`, indeks piksel ke-0).
- **Arah** = x ke kanan, y ke bawah (sistem koordinat layar/gambar standar).
- **Tanpa unit** lain — tidak pernah menyertakan DPI/inch; hanya piksel.

### Interpretasi semantik

- `(x1, y1)` = sudut kiri-atas area; `(x2, y2)` = sudut kanan-bawah (indeks piksel
  yang terseleksi). Nilai `x2 ≥ x1`, `y2 ≥ y1` (di-normalisasi saat drag terbalik).
- `w = x2 - x1`, `h = y2 - y1` → **jarak span dalam piksel** (bukan jumlah piksel).
  Untuk menghitung jumlah piksel yang tercakup: kolom = `w + 1`, baris = `h + 1`,
  total piksel = `(w + 1) × (h + 1)`.
- Titik yang disalin selalu di dalam batas gambar: `0 ≤ x < lebar`, `0 ≤ y < tinggi`.

### Contoh konversi

Input: `(x1=10, y1=20) (x2=39, y2=49) ukuran=29x29px`

- Luas piksel yang dipilih: `30 × 30 = 900` px
- Ukuran span: `29 × 29` px
- Koordinat tengah: `x = (10+39)/2 = 24,5`; `y = (20+49)/2 = 34,5`

## Perilaku aplikasi (untuk konteks)

- **Hover** memperbarui koordinat cursor secara real-time; crosshair biru ditampilkan.
- **Klik-tarik** membuat persegi seleksi; dilepas kecil (<1px) = membatalkan seleksi,
  dilepas normal = seleksi tertahan (tetap bisa disalin walau cursor pindah).
- **Tombol "Salin Koordinat" / Ctrl+C** menyalin seleksi aktif jika ada, selain itu
  menyalin posisi cursor terakhir.
- **Escape** = hapus seleksi; **scroll** = zoom (koordinat tetap akurat);
  **Ctrl`+`** tidak mengubah seleksi.

## Pedoman untuk agen / MCP

1. Data koordinat tiba sebagai teks polos — **parse, bukan tebak**. Cocokkan regex
   ketat: `^\((\d+), (\d+)\)$` untuk titik, atau
   `^\(x1=(\d+), y1=(\d+)\) \(x2=(\d+), y2=(\d+)\) ukuran=(\d+)x(\d+)px$` untuk area.
2. Validasi konsistensi: `ukuran` harus sama dengan `x2-x1` dan `y2-y1`.
3. Saat memberi saran/edit CSS atau desain, gunakan koordinat piksel gambar asli
   tersebut; jangan menambah/mengurangi offset tanpa alasan.
4. Jika hanya ada titik tanpa ukuran, itu posisi kursor terakhir — bukan seleksi.
5. Jangan pernah menukar sumbu: `x` horizontal, `y` vertikal (sistem top-down).