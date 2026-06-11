import sqlite3
from flask import current_app, g

from datetime import datetime

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('models/schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def check_all_random_locks():
    db = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "UPDATE records SET is_locked = 0 "
        "WHERE is_locked = 1 AND unlock_type = 'random' AND datetime(delivery_time) <= datetime(?)",
        (now_str,)
    )
    db.commit()

def create_record(audio_path, transcribed_text, image_path=None, unlock_type='none', latitude=None, longitude=None, radius=None, location_name=None, is_locked=0, delivery_time=None, random_min_hours=None, random_max_hours=None):
    db = get_db()
    cursor = db.execute(
        'INSERT INTO records (audio_path, transcribed_text, image_path, unlock_type, latitude, longitude, radius, location_name, is_locked, delivery_time, random_min_hours, random_max_hours) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (audio_path, transcribed_text, image_path, unlock_type, latitude, longitude, radius, location_name, is_locked, delivery_time, random_min_hours, random_max_hours)
    )
    db.commit()
    return cursor.lastrowid

def get_record(id):
    check_all_random_locks()
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
    check_all_random_locks()
    db = get_db()
    return db.execute(
        'SELECT * FROM records ORDER BY created_at DESC'
    ).fetchall()

def search_records(query=None, start_date=None, end_date=None):
    check_all_random_locks()
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

