# Database Adapter (Actions)
import sqlite3
import os
import json
from typing import Optional, List, Tuple, Any
from contextlib import contextmanager
from .model import Bookmark

# Use absolute path to ensure we hit the same DB regardless of CWD
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bookmarks.db"))
TAGS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tags.json"))

def get_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def fetch_bookmarks_by_query(query: str, limit: int, offset: int) -> Tuple[List[sqlite3.Row], int]:
    """
    Action: Search using FTS5.
    Returns (rows, total_count)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Count
        cursor.execute("SELECT count(*) FROM bookmarks_fts WHERE bookmarks_fts MATCH ?", (query,))
        total = cursor.fetchone()[0]

        # Fetch
        sql = """
            SELECT 
                b.id, b.url, b.title, b.tags, b.description, b.created_at, b.updated_at, b.archive_content,
                snippet(bookmarks_fts, 0, '<mark>', '</mark>', '...', 15) as title_highlight,
                snippet(bookmarks_fts, 2, '<mark>', '</mark>', '...', 25) as desc_highlight,
                snippet(bookmarks_fts, 3, '<mark>', '</mark>', '...', 40) as body_highlight
            FROM bookmarks_fts 
            JOIN bookmarks b ON b.id = bookmarks_fts.rowid
            WHERE bookmarks_fts MATCH ?
            ORDER BY bm25(bookmarks_fts, 10.0, 8.0, 3.0, 1.0) ASC
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (query, limit, offset))
        rows = cursor.fetchall()
        return rows, total

def fetch_bookmarks_by_tag(tag: str, limit: int, offset: int) -> Tuple[List[sqlite3.Row], int]:
    """Action: Filter by tag."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM bookmarks WHERE tags LIKE ?", (f"%{tag}%",))
        total = cursor.fetchone()[0]
        
        sql = """
            SELECT id, url, title, tags, description, created_at, updated_at,
            NULL as title_highlight, NULL as desc_highlight, NULL as body_highlight,
            NULL as archive_content
            FROM bookmarks 
            WHERE tags LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (f"%{tag}%", limit, offset))
        rows = cursor.fetchall()
        return rows, total

def fetch_all_bookmarks(limit: int, offset: int) -> Tuple[List[sqlite3.Row], int]:
    """Action: List all."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM bookmarks")
        total = cursor.fetchone()[0]
        
        sql = """
            SELECT id, url, title, tags, description, created_at, updated_at, archive_content,
            NULL as title_highlight, NULL as desc_highlight, NULL as body_highlight
            FROM bookmarks 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (limit, offset))
        rows = cursor.fetchall()
        return rows, total

def fetch_bookmark_by_id(id: int) -> Optional[sqlite3.Row]:
    """Action: Get single bookmark by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, url, title, tags, description, created_at, updated_at, archive_content
            FROM bookmarks 
            WHERE id = ?
        """, (id,))
        return cursor.fetchone()

def fetch_bookmark_by_url(url: str) -> Optional[sqlite3.Row]:
    """Action: Get single bookmark by URL."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, url, title, tags, description 
            FROM bookmarks 
            WHERE url = ?
        """, (url,))
        return cursor.fetchone()

def fetch_all_tags() -> List[str]:
    """Action: Get all unique tags."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tags FROM bookmarks WHERE tags IS NOT NULL AND tags != ''")
        rows = cursor.fetchall()
        
        all_tags = set()
        for row in rows:
            tags_str = row['tags']
            if tags_str:
                for t in tags_str.split():
                    all_tags.add(t.strip())
        
        return sorted(list(all_tags))

def export_tags_to_json():
    """Action: Export all tags to a JSON file for external apps (iOS Shortcuts)."""
    tags = fetch_all_tags()
    try:
        with open(TAGS_JSON_PATH, 'w') as f:
            json.dump({"tags": tags}, f, indent=2)
    except Exception as e:
        print(f"Failed to export tags: {e}")

def add_or_update_bookmark(url: str, title: str, tags: str, description: str) -> str:
    """Action: Insert or Update bookmark."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM bookmarks WHERE url = ?", (url,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE bookmarks 
                SET title = coalesce(?, title), 
                    tags = coalesce(?, tags), 
                    description = coalesce(?, description),
                    updated_at = CURRENT_TIMESTAMP,
                    archived = 0
                WHERE url = ?
            """, (title, tags, description, url))
            conn.commit()
            return "updated"
        else:
            cursor.execute("""
                INSERT INTO bookmarks (url, title, tags, description, unread, archived)
                VALUES (?, ?, ?, ?, 0, 0)
            """, (url, title or url, tags or "", description or ""))
            conn.commit()
            return "created"

def delete_bookmark(bookmark_id: int):
    """Action: Delete a bookmark by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        conn.commit()

def update_bookmark_details(id: int, url: str, title: str, tags: str, description: str):
    """Action: Update bookmark details by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookmarks 
            SET url = ?,
                title = ?, 
                tags = ?, 
                description = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (url, title, tags, description, id))
        conn.commit()

def fetch_unarchived_bookmarks(limit: int = 10) -> List[sqlite3.Row]:
    """Action: Get bookmarks that need archiving."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, url, title 
            FROM bookmarks 
            WHERE archived = 0 
            ORDER BY updated_at DESC, created_at DESC 
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def update_bookmark_archive(bookmark_id: int, content: str, html: Optional[str] = None, new_title: Optional[str] = None):
    """Action: Save archived content and optionally update title."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if new_title:
            cursor.execute("""
                UPDATE bookmarks 
                SET archive_content = ?, 
                    archive_html = ?,
                    archived = 1,
                    title = ?
                WHERE id = ?
            """, (content, html, new_title, bookmark_id))
        else:
            cursor.execute("""
                UPDATE bookmarks 
                SET archive_content = ?, 
                    archive_html = ?,
                    archived = 1
                WHERE id = ?
            """, (content, html, bookmark_id))
            
        conn.commit()
