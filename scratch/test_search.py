import sqlite3
import os
import urllib.request
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "database.db")

def populate_db():
    print("Populating database with test records...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing data to have a clean test run
    cursor.execute("DELETE FROM records")
    
    # Insert mock records
    # Record 1: Yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO records (audio_path, transcribed_text, created_at) VALUES (?, ?, ?)",
        ("uploads/test1.webm", "這是一個關於晴朗天空與海浪聲音的封存紀錄", yesterday)
    )
    
    # Record 2: Today (includes "雨聲")
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO records (audio_path, transcribed_text, created_at) VALUES (?, ?, ?)",
        ("uploads/test2.webm", "深夜在城市的咖啡廳，聽著窗外的雨聲，十分寧靜", today)
    )
    
    # Record 3: 5 days ago
    past = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO records (audio_path, transcribed_text, created_at) VALUES (?, ?, ?)",
        ("uploads/test3.webm", "森林深處的微風和鳥鳴，放鬆心靈的自然音律", past)
    )
    
    conn.commit()
    conn.close()
    print("Database populated successfully.")

import urllib.parse

def test_api(params_str):
    parts = urllib.parse.parse_qsl(params_str)
    query_str = urllib.parse.urlencode(parts)
    url = f"http://127.0.0.1:5000/api/search?{query_str}"
    print(f"GET {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("Status Code: 200")
            print(f"Found {len(res_data['records'])} records.")
            for r in res_data['records']:
                print(f" - [{r['created_at'][:10]}] ID={r['id']}: {r['transcribed_text']}")
            return res_data
    except Exception as e:
        print(f"Error calling API: {e}")
        return None


if __name__ == "__main__":
    populate_db()
    
    print("\n--- Test 1: Search keyword '雨聲' ---")
    test_api("q=雨聲")
    
    print("\n--- Test 2: Search date range starting 2 days ago ---")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    test_api(f"start_date={two_days_ago}")
    
    print("\n--- Test 3: Search keyword '微風' and date range 4-6 days ago ---")
    start = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    end = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
    test_api(f"q=微風&start_date={start}&end_date={end}")
    
    print("\n--- Test 4: Search dates with no results ---")
    test_api("start_date=2020-01-01&end_date=2020-12-31")
