import sqlite3
import os
from contextlib import contextmanager

# Use absolute path relative to this script
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bookmarks.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with tables and FTS5."""
    print(f"Initializing database at {DB_PATH}")
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Main Bookmarks Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            description TEXT,   -- User notes
            tags TEXT,          -- Space separated tags
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            unread BOOLEAN DEFAULT 0,
            shared BOOLEAN DEFAULT 0,
            archived BOOLEAN DEFAULT 0, -- Has it been processed by archiver?
            archive_content TEXT,       -- Full text of the page
            archive_html TEXT           -- Optional: clean HTML
        );
        """)
        
        # 2. FTS5 Virtual Table (External Content)
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts USING fts5(
            title,
            tags,
            description,
            archive_content,
            content='bookmarks',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );
        """)
        
        # 3. Triggers to keep FTS in sync
        # Insert Trigger
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS bookmarks_ai AFTER INSERT ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(rowid, title, tags, description, archive_content)
            VALUES (new.id, new.title, new.tags, new.description, new.archive_content);
        END;
        """)
        
        # Delete Trigger
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS bookmarks_ad AFTER DELETE ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(bookmarks_fts, rowid, title, tags, description, archive_content)
            VALUES ('delete', old.id, old.title, old.tags, old.description, old.archive_content);
        END;
        """)
        
        # Update Trigger
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS bookmarks_au AFTER UPDATE ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(bookmarks_fts, rowid, title, tags, description, archive_content)
            VALUES ('delete', old.id, old.title, old.tags, old.description, old.archive_content);
            INSERT INTO bookmarks_fts(rowid, title, tags, description, archive_content)
            VALUES (new.id, new.title, new.tags, new.description, new.archive_content);
        END;
        """)
        
        conn.commit()
        print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
