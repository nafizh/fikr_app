import argparse
import json
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../bookmarks.db"))

def parse_time(time_str):
    """Convert Pinboard time (ISO 8601) to SQLite compatible format."""
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def import_data(json_path: str):
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        return
    run_import(json_path)

def run_import(json_file):
    print(f"Reading {json_file}...")
    with open(json_file, "r") as f:
        data = json.load(f)
    
    print(f"Found {len(data)} bookmarks. Importing into {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    success_count = 0
    skip_count = 0
    
    for item in data:
        url = item.get("href")
        if not url:
            continue
            
        title = item.get("description", "")
        notes = item.get("extended", "")
        tags = item.get("tags", "")
        created_at = parse_time(item.get("time", ""))
        
        is_unread = 1 if item.get("toread") == "yes" else 0
        is_shared = 1 if item.get("shared") == "yes" else 0
        
        try:
            cursor.execute("""
            INSERT INTO bookmarks (url, title, description, tags, created_at, unread, shared)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                tags=excluded.tags,
                updated_at=CURRENT_TIMESTAMP
            """, (url, title, notes, tags, created_at, is_unread, is_shared))
            
            success_count += 1
        except sqlite3.Error as e:
            print(f"Error inserting {url}: {e}")
            skip_count += 1
            
    conn.commit()
    conn.close()
    print(f"Import complete.")
    print(f"Successfully imported/updated: {success_count}")
    print(f"Skipped/Errors: {skip_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import a Pinboard JSON export into the Fikr SQLite database.")
    parser.add_argument("json_path", help="Path to the Pinboard JSON export file.")
    args = parser.parse_args()
    import_data(args.json_path)
