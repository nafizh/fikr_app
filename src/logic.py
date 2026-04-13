# Pure calculations for search and pagination
import math
from typing import Optional
from .model import SearchParams, SearchResult, Bookmark

def sanitize_fts_query(q: str) -> str:
    """
    Transform user query into FTS5 query string.
    Calculation: str -> str
    """
    search_term = q.strip()
    # Naive check for advanced syntax
    if not any(char in search_term for char in [':', '"', 'OR', 'AND']):
        words = search_term.split()
        if words:
            # Prefix search on the last word
            words[-1] += "*"
            search_term = " ".join(words)
    return search_term

def calculate_pagination(total_count: int, limit: int, current_page: int) -> int:
    """Calculation: Calculate total pages."""
    if limit <= 0: return 1
    return math.ceil(total_count / limit)

def get_pagination_range(current_page: int, total_pages: int, delta: int = 2) -> list[int]:
    """
    Calculation: Get a range of pages to display around current page.
    """
    start = max(1, current_page - delta)
    end = min(total_pages, current_page + delta)
    
    # Adjust if we're near the beginning
    if current_page - delta < 1:
        end = min(total_pages, end + (delta - (current_page - 1)))
        
    # Adjust if we're near the end
    if current_page + delta > total_pages:
        start = max(1, start - (current_page + delta - total_pages))
        
    return list(range(start, end + 1))

def calculate_offset(page: int, limit: int) -> int:
    """Calculation: Calculate SQL offset."""
    return (page - 1) * limit

def row_to_bookmark(row: dict) -> Bookmark:
    """
    Transform a DB row (dict-like) into a Bookmark domain object.
    Calculation: dict -> Bookmark
    """
    tags_raw = row["tags"] or ""
    return Bookmark(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        description=row["description"],
        tags=tuple(tags_raw.split()) if tags_raw else (),
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        unread=False, 
        shared=False,
        archive_content=row.get("archive_content"),
        title_highlight=row.get("title_highlight"),
        desc_highlight=row.get("desc_highlight"),
        body_highlight=row.get("body_highlight")
    )
