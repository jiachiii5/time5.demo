import os
import sqlite3
import math
import struct
import wave
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join("instance", "database.db")
UPLOAD_FOLDER = os.path.join("app", "static", "uploads")

def ensure_folders():
    os.makedirs("instance", exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print("Folders verified/created.")

def create_dummy_wav(filename, duration=3.0, sample_rate=22050, frequency=440.0):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    print(f"Generating dummy audio file: {filepath}")
    with wave.open(filepath, 'w') as w:
        w.setnchannels(1)  # Mono
        w.setsampwidth(2)   # 16-bit
        w.setframerate(sample_rate)
        
        num_frames = int(duration * sample_rate)
        for i in range(num_frames):
            # Simple sine wave
            val = int(16384.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            w.writeframesraw(struct.pack('<h', val))
    print(f"Audio file {filename} generated successfully.")

def init_schemas(conn):
    print("Initializing database tables...")
    # Load and execute Project Collaboration schema
    if os.path.exists("schema.sql"):
        with open("schema.sql", "r", encoding="utf8") as f:
            conn.executescript(f.read())
            print("- Applied schema.sql")
    
    # Load and execute Sensorial Archiving schema
    app_schema_path = os.path.join("app", "models", "schema.sql")
    if os.path.exists(app_schema_path):
        with open(app_schema_path, "r", encoding="utf8") as f:
            conn.executescript(f.read())
            print("- Applied app/models/schema.sql")

def clear_existing_data(conn):
    print("Cleaning up old data...")
    tables = ["project_members", "documents", "projects", "users", "records"]
    cursor = conn.cursor()
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError as e:
            # Table might not exist yet, which is fine
            print(f"Note: {table} skip clean ({e})")
    conn.commit()

def seed_project_collaboration(conn):
    print("Seeding Project Collaboration data...")
    cursor = conn.cursor()
    
    # 1. Users
    users_data = [
        ("admin", generate_password_hash("password123")),
        ("alice", generate_password_hash("password123")),
        ("bob", generate_password_hash("password123")),
        ("charlie", generate_password_hash("password123"))
    ]
    cursor.executemany("INSERT INTO users (username, password_hash) VALUES (?, ?)", users_data)
    
    # Fetch user IDs
    user_ids = {row[1]: row[0] for row in cursor.execute("SELECT id, username FROM users").fetchall()}
    
    # 2. Projects
    now = datetime.now()
    proj1_created = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    proj2_created = (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("INSERT INTO projects (name, created_at) VALUES (?, ?)", ("「極光」智慧家居系統開發", proj1_created))
    p1_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO projects (name, created_at) VALUES (?, ?)", ("「時光封存」APP 行銷計畫", proj2_created))
    p2_id = cursor.lastrowid
    
    # 3. Project Members
    members_data = [
        # Project 1: Alice is owner, Bob is editor, Charlie is viewer
        (p1_id, user_ids["alice"], "owner"),
        (p1_id, user_ids["bob"], "editor"),
        (p1_id, user_ids["charlie"], "viewer"),
        # Project 2: Bob is owner, Alice is editor, Charlie is viewer
        (p2_id, user_ids["bob"], "owner"),
        (p2_id, user_ids["alice"], "editor"),
        (p2_id, user_ids["charlie"], "viewer"),
    ]
    cursor.executemany("INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)", members_data)
    
    # 4. Documents
    doc1_content = """# 智慧家居系統架構設計規範

## 1. 核心元件
- **Gateway 控制中心**：負責處理終端感應器數據並上報至雲端。
- **邊緣運算節點**：進行本地即時決策控制，降低回應延遲。
- **Web 端與行動 App 介面**：提供終端使用者監控與操作的 Portal。

> [!NOTE]
> 為了提高隱私與安全性，所有感應器與閘道器之間的通訊必須進行 AES-256 加密。
"""
    
    doc2_content = """# 使用者體驗 (UX) 設計藍圖

- 主色系使用極光綠 (HSL 150, 80%, 40%) 與太空灰搭配。
- 提供深色模式與高對比模式，符合無障礙設計。
- 錄音控制鈕包含微幅脈衝 (pulse) 動態回饋，點擊時觸感更立體。
"""

    doc3_content = """# 媒體公關與發布排程計畫

## 預計里程碑
1. **06/01** - 發布首波媒體新聞稿。
2. **06/15** - 社群平台 (Instagram, Thread) 大規模 KOL 體驗短影音上線。
3. **07/01** - App Store & Google Play 正式開放下載。

> [!WARNING]
> 所有宣傳文案在未經 Bob 簽核前，嚴禁外流或在個人帳號發佈。
"""

    doc4_content = """# 競品分析與定位報告

我們將對比市面上主流的「語音筆記」與「AI 繪圖」軟體。
- **優勢**：整合度高、支援手動微調 prompt、提供精美封存清單。
- **劣勢**：目前為 Mock API，後續需規劃串接真實 AI 服務。
"""
    
    # Insert Documents
    # Doc 1: Locked by Alice, version 4
    cursor.execute(
        "INSERT INTO documents (project_id, title, content, version, locked_by_user_id, locked_at, last_modified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (p1_id, "系統架構設計規範.md", doc1_content, 4, user_ids["alice"], (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    # Doc 2: Unlocked, version 1
    cursor.execute(
        "INSERT INTO documents (project_id, title, content, version, locked_by_user_id, locked_at, last_modified_at) "
        "VALUES (?, ?, ?, ?, NULL, NULL, ?)",
        (p1_id, "使用者體驗設計藍圖.md", doc2_content, 1, (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    # Doc 3: Locked by Bob, version 2
    cursor.execute(
        "INSERT INTO documents (project_id, title, content, version, locked_by_user_id, locked_at, last_modified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (p2_id, "媒體公關與發布排程.md", doc3_content, 2, user_ids["bob"], (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    # Doc 4: Unlocked, version 1
    cursor.execute(
        "INSERT INTO documents (project_id, title, content, version, locked_by_user_id, locked_at, last_modified_at) "
        "VALUES (?, ?, ?, ?, NULL, NULL, ?)",
        (p2_id, "競品分析與定位報告.md", doc4_content, 1, (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    conn.commit()
    print("Project Collaboration data seeded successfully.")

def seed_sensorial_archiving(conn):
    print("Seeding Sensorial Archiving data...")
    cursor = conn.cursor()
    
    now = datetime.now()
    t_3_days_ago = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    t_1_day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    t_today = now.strftime("%Y-%m-%d %H:%M:%S")
    t_delivery = (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    records = [
        # Record 1: 3 days ago, unlocked
        (
            "uploads/forest.wav", 
            "在森林深處，鳥鳴和微風吹過樹葉的沙沙聲，彷彿時間靜止了。", 
            "https://picsum.photos/seed/forest/800/600",
            t_3_days_ago,
            'none',
            None,
            None,
            None,
            None,
            0,
            None,
            None,
            None
        ),
        # Record 2: 1 day ago, locked to Taipei 101 via Geofence
        (
            "uploads/cafe.wav", 
            "深夜在城市的咖啡廳，聽著窗外的雨聲，十分寧靜。", 
            "https://picsum.photos/seed/cafe/800/600",
            t_1_day_ago,
            'geofence',
            25.033976,
            121.564472,
            100.0,
            "台北 101 信義商圈",
            1,
            None,
            None,
            None
        ),
        # Record 3: Today, Random Delivery in progress (locked)
        (
            "uploads/ocean.wav", 
            "這是一段關於海洋與星空的聲音，感受到海風的吹拂，繁星點點灑落在大海上。", 
            None,
            t_today,
            'random',
            None,
            None,
            None,
            None,
            1,
            t_delivery,
            12,
            48
        )
    ]
    
    cursor.executemany(
        "INSERT INTO records (audio_path, transcribed_text, image_path, created_at, unlock_type, latitude, longitude, radius, location_name, is_locked, delivery_time, random_min_hours, random_max_hours) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records
    )
    conn.commit()
    print("Sensorial Archiving data seeded successfully.")

def main():
    ensure_folders()
    
    # Generate WAV files
    create_dummy_wav("forest.wav", duration=4.0, frequency=300.0)
    create_dummy_wav("cafe.wav", duration=3.0, frequency=400.0)
    create_dummy_wav("ocean.wav", duration=5.0, frequency=250.0)
    
    # Establish connection and seed
    conn = sqlite3.connect(DB_PATH)
    try:
        init_schemas(conn)
        clear_existing_data(conn)
        seed_project_collaboration(conn)
        seed_sensorial_archiving(conn)
        print("\nAll Done! Database seeded and audio resources prepared successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
