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
            
            for _, row in df1.iterrows():
                c.execute('INSERT INTO vocabulary (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (row['NO'], row['TYPE'], row['FREQUENCY'], row['POS'], row['TERJEMAHAN'], row['DEFINISI'], row['KOLOKASI'], row['CONTOH KALIMAT'], row['GAMBAR']))
            print(f"Loaded {len(df1)} from EPS 1")
            
            df2 = pd.read_excel('DAFTAR TYPE.xlsx', sheet_name='EPS 2')
            max_no = df1['NO'].max()
            for _, row in df2.iterrows():
                c.execute('INSERT INTO vocabulary (no, type, frequency, pos, terjemahan, definisi, kolokasi, contoh_kalimat, gambar) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (int(row['NO']) + max_no, row['TYPE'], row['FREQUENCY'], row['POS'], row['TERJEMAHAN'], row['DEFINISI'], row['KOLOKASI'], row['CONTOH KALIMAT'], row['GAMBAR']))
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
    categories = [row['pos'] for row in cur.fetchall()]
    conn.close()
    return jsonify({'categories': categories})

@app.route('/api/search')
def search_vocabulary():
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    conn = get_db()
    cur = conn.cursor()
    
    sql = "SELECT * FROM vocabulary WHERE 1=1"
    params = []
    
    if category:
        sql += " AND pos = ?"
        params.append(category)
    
    cur.execute(sql, params)
    all_results = [dict(row) for row in cur.fetchall()]
    
    if query:
        results = []
        for row in all_results:
            # check korean
            if query in row.get('type', '').lower():
                results.append(row)
                continue
            # check indonesian
            translation = clean_translation(row.get('terjemahan', ''))
            if query in translation.lower():
                results.append(row)
        all_results = results
    
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
    
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

