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
    if not text or pd.isna(text):
        return ""
    # remove urls
    lines = [l for l in str(text).split('\n') if not l.strip().startswith('http')]
    text = ' '.join(lines)
    # remove numbers
    text = re.sub(r'\d+\.\s*', ' ', text)
    return text.strip()

def detect_kategori(text):
    if not text:
        return None
    text_clean = clean_translation(text)
    for kategori_name, keyword_list in KATEGORI_KEYWORD.items():
        for keyword in keyword_list:
            if keyword in text_clean.lower():
                return kategori_name
    return None

def init_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        no INTEGER, type TEXT NOT NULL, frequency REAL, pos TEXT,
        terjemahan TEXT, definisi TEXT, kolokasi TEXT, contoh_kalimat TEXT,
        gambar TEXT, kategori TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # add kategori column if missing
    try:
        c.execute('ALTER TABLE vocabulary ADD COLUMN kategori TEXT')
    except:
        pass
    
    if c.execute('SELECT COUNT(*) FROM vocabulary').fetchone()[0] == 0:
        try:
            # load eps 1
            df1 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 1')
            for _, row in df1.iterrows():
                kategori = detect_kategori(row.get('TERJEMAHAN'))
                c.execute('INSERT INTO vocabulary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (None, row['NO'], row['TYPE'], row['FREQUENCY'], row['POS'], row['TERJEMAHAN'],
                     row['DEFINISI'], row['KOLOKASI'], row['CONTOH KALIMAT'], row['GAMBAR'], kategori, None))
            print(f"Loaded {len(df1)} from EPS 1")
            
            # load eps 2
            df2 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 2')
            max_no = df1['NO'].max()
            for _, row in df2.iterrows():
                kategori = detect_kategori(row.get('TERJEMAHAN'))
                c.execute('INSERT INTO vocabulary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (None, int(row['NO']) + max_no, row['TYPE'], row['FREQUENCY'], row['POS'], row['TERJEMAHAN'],
                     row['DEFINISI'], row['KOLOKASI'], row['CONTOH KALIMAT'], row['GAMBAR'], kategori, None))
            print(f"Loaded {len(df2)} from EPS 2")
            
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
    
    conn.close()

def get_db():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def make_image(cat, korean, indonesian):
    # defaults
    cat = cat or 'Vocabulary'
    korean = korean or 'Word'
    indonesian = indonesian or ''
    
    # create image
    img = Image.new('RGB', (400, 300), color=(102, 126, 234))
    draw = ImageDraw.Draw(img)
    
    # fonts
    try:
        f1 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        f2 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        f1 = ImageFont.load_default()
        f2 = ImageFont.load_default()
    
    # draw korean
    bbox = draw.textbbox((0, 0), korean, font=f1)
    w = bbox[2] - bbox[0]
    draw.text(((400 - w) // 2, 100), korean, fill=(255, 255, 255), font=f1)
    
    # draw indonesian
    if indonesian:
        bbox = draw.textbbox((0, 0), indonesian, font=f2)
        w = bbox[2] - bbox[0]
        draw.text(((400 - w) // 2, 180), indonesian, fill=(255, 255, 255), font=f2)
    
    # draw category
    bbox = draw.textbbox((0, 0), cat, font=f2)
    w = bbox[2] - bbox[0]
    draw.text(((400 - w) // 2, 220), cat, fill=(200, 200, 200), font=f2)
    
    # encode
    buf = BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{img_b64}"

@app.route('/')
def index():
    return render_template('index_enhanced.html')

@app.route('/api/categories')
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT pos FROM vocabulary WHERE pos IS NOT NULL ORDER BY pos')
    categories = [row['pos'] for row in cur.fetchall()]
    conn.close()
    return jsonify({'categories': categories})

@app.route('/api/kategori')
def get_kategori():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT kategori FROM vocabulary WHERE kategori IS NOT NULL')
    kategori_list = [row['kategori'] for row in cur.fetchall()]
    conn.close()
    return jsonify({'kategori': kategori_list})

@app.route('/api/search')
def search_vocabulary():
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    kategori = request.args.get('kategori', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    show_images = request.args.get('include_images', 'true').lower() == 'true'
    
    conn = get_db()
    cur = conn.cursor()
    
    sql = "SELECT * FROM vocabulary WHERE 1=1"
    params = []
    
    if category:
        sql += " AND pos = ?"
        params.append(category)
    
    if kategori:
        sql += " AND kategori = ?"
        params.append(kategori)
    
    cur.execute(sql, params)
    all_results = [dict(row) for row in cur.fetchall()]
    
    if query:
        results = []
        for row in all_results:
            # check korean
            if query in str(row.get('type', '')).lower():
                results.append(row)
                continue
            # check indonesian
            translation = clean_translation(row.get('terjemahan', ''))
            if query in translation.lower():
                results.append(row)
        all_results = results
    
    # add images
    if show_images:
        for item in all_results:
            if not item.get('gambar'):
                translation = item.get('terjemahan', '')
                if translation:
                    indonesian_word = clean_translation(translation).split()[0]
                else:
                    indonesian_word = item.get('type', '')
                item['gambar'] = make_image(item.get('pos', 'Vocabulary'), item.get('type', ''), indonesian_word)
    
    total = len(all_results)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    results = all_results[start_idx:end_idx]
    
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
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Not found'}), 404
    
    data = dict(row)
    if not data.get('gambar'):
        translation = data.get('terjemahan', '')
        indonesian_word = clean_translation(translation).split()[0] if translation else data.get('type', '')
        data['gambar'] = make_image(data.get('pos', 'Vocabulary'), data.get('type', ''), indonesian_word)
    
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
