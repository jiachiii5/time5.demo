import sqlite3
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('models/schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def create_record(audio_path, transcribed_text, image_path=None):
    db = get_db()
    cursor = db.execute(
        'INSERT INTO records (audio_path, transcribed_text, image_path) '
        'VALUES (?, ?, ?)',
        (audio_path, transcribed_text, image_path)
    )
    db.commit()
    return cursor.lastrowid

def get_record(id):
    db = get_db()
    return db.execute(
        'SELECT * FROM records WHERE id = ?', (id,)
    ).fetchone()

def update_record_image(id, image_path):
    db = get_db()
    db.execute(
        'UPDATE records SET image_path = ? WHERE id = ?',
        (image_path, id)
    )
    db.commit()

def get_all_records():
    db = get_db()
    return db.execute(
        'SELECT * FROM records ORDER BY created_at DESC'
    ).fetchall()

def search_records(query=None, start_date=None, end_date=None):
    db = get_db()
    sql = 'SELECT * FROM records WHERE 1=1'
    params = []
    
    if query:
        sql += ' AND transcribed_text LIKE ?'
        params.append(f'%{query}%')
        
    if start_date:
        sql += ' AND date(created_at) >= ?'
        params.append(start_date)
        
    if end_date:
        sql += ' AND date(created_at) <= ?'
        params.append(end_date)
        
    sql += ' ORDER BY created_at DESC'
    
    return db.execute(sql, params).fetchall()

