from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import re
import os

app = Flask(__name__)
db_file = 'vocabulary.db'

def init_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT, no INTEGER, type TEXT NOT NULL, 
        frequency REAL, pos TEXT, terjemahan TEXT, definisi TEXT, kolokasi TEXT, 
        contoh_kalimat TEXT, gambar TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    count = c.execute('SELECT COUNT(*) FROM vocabulary').fetchone()[0]
    
    if count == 0:
        try:
            # load both sheets
            df1 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 1')
            
            for _, r in df1.iterrows():
                c.execute('INSERT INTO vocabulary (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (r['NO'], r['TYPE'], r['FREQUENCY'], r['POS'], r['TERJEMAHAN'], r['DEFINISI'], r['KOLOKASI'], r['CONTOH KALIMAT'], r['GAMBAR']))
            print(f"Loaded {len(df1)} from EPS 1")
            
            df2 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 2')
            max_no = df1['NO'].max()
            for _, r in df2.iterrows():
                c.execute('INSERT INTO vocabulary (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (int(r['NO']) + max_no, r['TYPE'], r['FREQUENCY'], r['POS'], r['TERJEMAHAN'], r['DEFINISI'], r['KOLOKASI'], r['CONTOH KALIMAT'], r['GAMBAR']))
            print(f"Loaded {len(df2)} from EPS 2")
            
            conn.commit()
            print(f"Total entries: {len(df1) + len(df2)}")
        except Exception as e:
            print(f"Excel error: {e}")
    
    conn.close()

def get_db():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def clean_translation(text):
    if not text:
        return ""
    lines = [l for l in text.split('\n') if not l.strip().startswith('http')]
    text = ' '.join(lines)
    text = re.sub(r'\d+\.\s*', ' ', text)
    return text.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT pos FROM vocabulary WHERE pos IS NOT NULL ORDER BY pos')
    cats = [r['pos'] for r in cur.fetchall()]
    conn.close()
    return jsonify({'categories': cats})

@app.route('/api/search')
def search_vocabulary():
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('category', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    conn = get_db()
    cur = conn.cursor()
    
    sql = "SELECT * FROM vocabulary WHERE 1=1"
    params = []
    
    if cat:
        sql += " AND pos = ?"
        params.append(cat)
    
    cur.execute(sql, params)
    all_results = [dict(r) for r in cur.fetchall()]
    
    if q:
        results = []
        for r in all_results:
            # check korean
            if q in r.get('type', '').lower():
                results.append(r)
                continue
            # check indonesian
            trans = clean_translation(r.get('terjemahan', ''))
            if q in trans.lower():
                results.append(r)
        all_results = results
    
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
        return jsonify(dict(r))
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

