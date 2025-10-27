from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
import re
import os

app = Flask(__name__)
db_file = 'vocabulary.db'

KATEGORI_KEYWORD = {
    'makanan': ['kimchi', 'sup', 'sop', 'makanan', 'makan', 'rebusan', 'samgyetang', 'ayam', 'nasi', 'bakso', 'sate', 'rendang', 'gudeg'],
    'kendaraan': ['kereta', 'sepeda', 'motor', 'bus', 'pesawat', 'mobil', 'truk', 'kapal', 'helikopter', 'bemo', 'angkot'],
    'pekerjaan': ['pekerjaan', 'kerja', 'pekerja', 'buruh', 'karyawan', 'pegawai', 'tenaga kerja', 'dokter', 'guru', 'dosen'],
    'tempat': ['tempat', 'lokasi', 'gedung', 'rumah', 'sekolah', 'kantor', 'pasar', 'stasiun', 'bandara', 'gudang', 'perumahan'],
    'aktivitas': ['aktivitas', 'olahraga', 'belajar', 'kerja', 'libur', 'istirahat', 'permainan', 'bermain']
}

def clean_translation(text):
    if not text:
        return ""
    lines = [l for l in text.split('\n') if not l.strip().startswith('http')]
    text = ' '.join(lines)
    text = re.sub(r'\d+\.\s*', ' ', text)
    return text.strip()

def detect_kategori(text):
    if not text or pd.isna(text):
        return None
    try:
        text_lower = clean_translation(str(text)).lower()
        for kategori, keywords in KATEGORI_KEYWORD.items():
            for kw in keywords:
                if kw in text_lower:
                    return kategori
    except:
        pass
    return None

def init_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no INTEGER,
            type TEXT NOT NULL,
            frequency REAL,
            pos TEXT,
            terjemahan TEXT,
            definisi TEXT,
            kolokasi TEXT,
            contoh_kalimat TEXT,
            gambar TEXT,
            kategori TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        c.execute('ALTER TABLE vocabulary ADD COLUMN kategori TEXT')
    except:
        pass
    
    count = c.execute('SELECT COUNT(*) FROM vocabulary').fetchone()[0]
    
    if count == 0:
        try:
            df1 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 1')
            total = 0
            
            for _, r in df1.iterrows():
                kat = detect_kategori(r['TERJEMAHAN'])
                c.execute('''
                    INSERT INTO vocabulary 
                    (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar, kategori)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    r['NO'] if not pd.isna(r['NO']) else None,
                    r['TYPE'] if not pd.isna(r['TYPE']) else None,
                    r['FREQUENCY'] if not pd.isna(r['FREQUENCY']) else None,
                    r['POS'] if not pd.isna(r['POS']) else None,
                    r['TERJEMAHAN'] if not pd.isna(r['TERJEMAHAN']) else None,
                    r['DEFINISI'] if not pd.isna(r['DEFINISI']) else None,
                    r['KOLOKASI'] if not pd.isna(r['KOLOKASI']) else None,
                    r['CONTOH KALIMAT'] if not pd.isna(r['CONTOH KALIMAT']) else None,
                    r['GAMBAR'] if not pd.isna(r['GAMBAR']) else None,
                    kat
                ))
            print(f"Loaded {len(df1)} from EPS 1")
            total += len(df1)
            
            df2 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 2')
            max_no = df1['NO'].max()
            
            for _, r in df2.iterrows():
                kat = detect_kategori(r['TERJEMAHAN'])
                c.execute('''
                    INSERT INTO vocabulary 
                    (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar, kategori)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int(r['NO']) + max_no if not pd.isna(r['NO']) else None,
                    r['TYPE'] if not pd.isna(r['TYPE']) else None,
                    r['FREQUENCY'] if not pd.isna(r['FREQUENCY']) else None,
                    r['POS'] if not pd.isna(r['POS']) else None,
                    r['TERJEMAHAN'] if not pd.isna(r['TERJEMAHAN']) else None,
                    r['DEFINISI'] if not pd.isna(r['DEFINISI']) else None,
                    r['KOLOKASI'] if not pd.isna(r['KOLOKASI']) else None,
                    r['CONTOH KALIMAT'] if not pd.isna(r['CONTOH KALIMAT']) else None,
                    r['GAMBAR'] if not pd.isna(r['GAMBAR']) else None,
                    kat
                ))
            
            print(f"Loaded {len(df2)} from EPS 2")
            total += len(df2)
            
            conn.commit()
            print(f"Done. Total: {total} entries")
        except Exception as e:
            print(f"Excel error: {e}")
    
    conn.close()

def get_db():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def make_image(cat, korean, indonesian):
    cat = cat or 'Vocabulary'
    korean = korean or 'Word'
    indonesian = indonesian or ''
    
    img = Image.new('RGB', (400, 300), color=(102, 126, 234))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # korean word
    k_bbox = draw.textbbox((0, 0), korean, font=font_large)
    k_w = k_bbox[2] - k_bbox[0]
    
    draw.text(((400 - k_w) // 2, 100), korean, fill=(255, 255, 255), font=font_large)
    
    # indonesian
    if indonesian:
        ind_bbox = draw.textbbox((0, 0), indonesian, font=font_medium)
        ind_w = ind_bbox[2] - ind_bbox[0]
        
        draw.text(((400 - ind_w) // 2, 180), indonesian, fill=(255, 255, 255), font=font_medium)
    
    # category
    cat_bbox = draw.textbbox((0, 0), cat, font=font_medium)
    cat_w = cat_bbox[2] - cat_bbox[0]
    
    draw.text(((400 - cat_w) // 2, 220), cat, fill=(200, 200, 200), font=font_medium)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    img_b64 = base64.b64encode(img_data).decode()
    return f"data:image/png;base64,{img_b64}"

@app.route('/')
def index():
    return render_template('index_enhanced.html')

@app.route('/api/categories')
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT pos FROM vocabulary WHERE pos IS NOT NULL ORDER BY pos')
    cats = [r['pos'] for r in cur.fetchall()]
    conn.close()
    return jsonify({'categories': cats})

@app.route('/api/kategori')
def get_kategori():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT kategori FROM vocabulary WHERE kategori IS NOT NULL ORDER BY kategori')
    kats = [r['kategori'] for r in cur.fetchall()]
    conn.close()
    return jsonify({'kategori': kats})

@app.route('/api/search')
def search_vocabulary():
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('category', '').strip()
    kategori = request.args.get('kategori', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    show_images = request.args.get('include_images', 'true').lower() == 'true'
    
    conn = get_db()
    cur = conn.cursor()
    
    sql = "SELECT * FROM vocabulary WHERE 1=1"
    params = []
    
    if cat:
        sql += " AND pos = ?"
        params.append(cat)
    
    if kategori:
        sql += " AND kategori = ?"
        params.append(kategori)
    
    cur.execute(sql, params)
    all_results = [dict(r) for r in cur.fetchall()]
    
    if q:
        results = []
        for r in all_results:
            if q in r.get('type', '').lower():
                results.append(r)
                continue
            trans = clean_translation(r.get('terjemahan', ''))
            if q in trans.lower():
                results.append(r)
        all_results = results
    
    # generate images
    if show_images:
        for item in all_results:
            if not item.get('gambar'):
                trans = item.get('terjemahan', '')
                if trans:
                    cleaned = clean_translation(trans)
                    ind_word = cleaned.split()[0] if cleaned else item.get('type', '')
                else:
                    ind_word = item.get('type', '')
                
                item['gambar'] = make_image(
                    item.get('pos', 'Vocabulary'),
                    item.get('type', ''),
                    ind_word
                )
    
    total = len(all_results)
    start = (page - 1) * per_page
    end = start + per_page
    results = all_results[start:end]
    
    conn.close()
    
    return jsonify({
        'results': results,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/vocabulary/<int:vocab_id>')
def get_vocabulary(vocab_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vocabulary WHERE id = ?', (vocab_id,))
    r = cur.fetchone()
    conn.close()
    
    if r:
        data = dict(r)
        
        if not data.get('gambar'):
            trans = data.get('terjemahan', '')
            if trans:
                cleaned = clean_translation(trans)
                ind_word = cleaned.split()[0] if cleaned else data.get('type', '')
            else:
                ind_word = data.get('type', '')
            
            data['gambar'] = make_image(
                data.get('pos', 'Vocabulary'),
                data.get('type', ''),
                ind_word
            )
        
        return jsonify(data)
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
