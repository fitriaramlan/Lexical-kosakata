# 🇰🇷 Kamus Kosakata Korea - Indonesia

Website bilingual untuk belajar kosakata Korea dan Indonesia.

## Fitur

- Pencarian Korea & Indonesia (5,828 kosakata)
- Filter kategori (POS & kategori tematik)
- Image generation otomatis
- Tampilan responsif
- Siap untuk deployment online

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run aplikasi
python app_image_generator.py
```

Buka: http://localhost:5000

## Deploy Online (Railway/Render)

### 1. Upload ke GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/kamus-korea-indonesia.git
git push -u origin main
```

### 2. Deploy ke Railway.app
1. Login: https://railway.app
2. New Project → Deploy from GitHub
3. Pilih repository Anda
4. Done! Dapatkan link gratis

Lihat **GITHUB_DEPLOY_STEPS.md** untuk panduan lengkap.

## Struktur Project

```
├── app_image_generator.py    # Main app
├── templates/
│   ├── index.html           # Basic UI
│   └── index_enhanced.html  # Enhanced UI
├── requirements.txt          # Dependencies
├── Procfile                 # For deployment
├── DAFTAR TYPE.xlsx        # Data source (EPS 1 & EPS 2)
└── vocabulary.db            # Database (auto-generated)
```

## Cara Pakai

### Pencarian
- Ketik kata Korea atau Indonesia di search box
- Hasil muncul real-time
- Contoh: "makanan", "pekerja", "manusia"

### Filter Kategori
- Filter berdasarkan POS (NNG, VV, dll)
- Filter berdasarkan kategori tematik (makanan, pekerjaan, dll)

### Navigasi
- Pagination untuk browse semua kosakata
- Setiap card menampilkan:
  - Kata Korea
  - Terjemahan Indonesia
  - Definisi & contoh kalimat
  - Gambar (jika ada)

## Data

- **Total**: 5,828 kosakata
  - EPS 1: 2,389 entries
  - EPS 2: 3,439 entries
- **Terjemahan Indonesia**: 38 entries
- **Kategori**: makanan (3), pekerjaan (6), tempat (4), kendaraan (1)

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Image**: PIL/Pillow

## API

- `GET /` - Main page
- `GET /api/categories` - List kategori POS
- `GET /api/kategori` - List kategori tematik  
- `GET /api/search?q={query}&kategori={cat}&page={p}` - Search kosakata
- `GET /api/vocabulary/{id}` - Detail kosakata

## Development

```bash
# Run basic version
python app.py

# Run enhanced version (with images)
python app_image_generator.py
```

## License

MIT License
