CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audio_path TEXT NOT NULL,
  transcribed_text TEXT NOT NULL,
  image_path TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  unlock_type TEXT DEFAULT 'none',
  latitude REAL,
  longitude REAL,
  radius REAL,
  location_name TEXT,
  is_locked INTEGER DEFAULT 0,
  delivery_time TIMESTAMP,
  random_min_hours INTEGER,
  random_max_hours INTEGER
);

