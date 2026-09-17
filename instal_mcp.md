# Instal MCP Server Pixel Ruler (coord_mcp.py)

Panduan ini berisi instruksi untuk **agen AI** (atau manusia) agar memasang MCP server
`pixel-ruler-coords` dari repo ini ke opencode (atau klien MCP lain). Server ini
dipakai untuk mem-parse dan menginterpretasi koordinat yang disalin dari aplikasi
Pixel Ruler.

Ikuti **urutan instruksi di bawah secara berurutan**: unduh dulu `coord_mcp.py`,
lalu pasang konfigurasi, lalu verifikasi.

---

## 1. Unduh coord_mcp.py

Salin file `coord_mcp.py` dari repo ini ke mesin tujuan. Contoh menggunakan `curl`
dari GitHub raw (ganti `<owner>/<repo>` dengan pemilik dan nama repo Anda):

```bash
curl -o coord_mcp.py \
  "https://raw.githubusercontent.com/<owner>/<repo>/main/coord_mcp.py"
```

Pastikan file tersimpan dan boleh dieksekusi:

```bash
# Cek bahwa file terunduh dan berisi skrip Python
head -5 coord_mcp.py
python3 --version   # butuh Python 3.8+ (stdlib saja, tanpa dependensi eksternal)
```

Catatan:
- Gunakan path **absolut** ke file ini saat menulis konfigurasi pada langkah 2
  (contoh di bawah memakai `/path/ke/coord_mcp.py`).
- Server hanya berjalan lokal via stdio; file tidak perlu diinstal global, cukup
  ada di mesin yang menjalankan klien MCP.

## 2. Pasang entri konfigurasi

### 2a. opencode (proyek atau global)

Perlihatkan/masukkan entri berikut ke `opencode.json` klien opencode Anda.
**Proyek** (`opencode.json` di akar proyek) atau **global**
(`~/.config/opencode/opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "pixel-ruler-coords": {
      "type": "local",
      "command": ["python3", "/path/ke/coord_mcp.py"],
      "enabled": true
    }
  }
}
```

Ganti `/path/ke/coord_mcp.py` dengan path absolut hasil unduhan pada langkah 1.

### 2b. Klien MCP lain (adaptasi saja)

Untuk klien yang memakai `mcpServers` (mis. Claude Code, Cursor, dsb.):

```json
{
  "mcpServers": {
    "pixel-ruler-coords": {
      "command": "python3",
      "args": ["/path/ke/coord_mcp.py"]
    }
  }
}
```

## 3. Verifikasi

Setelah memasang entri, **restart opencode/klien MCP** agar config termuat.
Kemudian uji bahwa server merespons dengan benar:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"parse_coordinates","arguments":{"text":"(x1=10, y1=20) (x2=39, y2=49) ukuran=29x29px"}}}' \
| python3 /path/ke/coord_mcp.py
```

Output yang diharapkan pada panggilan ke-2 (ringkas):

```json
{"ok": true, "data": {"kind": "area", "x1": 10, "y1": 20, "x2": 39, "y2": 49,
  "width": 29, "height": 29, "span": [29, 29], "pixel_count": 900,
  "center": {"x": 24.5, "y": 34.5}}}
```

Atau di dalam percakapan opencode, minta agen memanggil:

> Gunakan tool `pixel-ruler-coords` untuk parse koordinat ini: `(120, 340)`

## Referensi format (ringkas)

- **Titik**: `(x, y)` → `(120, 340)`
- **Area**: `(x1=.., y1=..) (x2=.., y2=..) ukuran=<w>x<h>px`
  → `(x1=100, y1=50) (x2=250, y2=180) ukuran=150x130px`
- `w = x2 - x1`, `h = y2 - y1`; luas piksel tercakup = `(w+1) × (h+1)`.
- Origin (0,0) = kiri-atas gambar asli; x ke kanan, y ke bawah.

Dokumentasi lengkap interpretasi koordinat ada di `AGENTS.md` repo ini.