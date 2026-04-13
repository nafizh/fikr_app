from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Bookmark:
    url: str
    title: str
    description: str
    tags: tuple[str, ...]
    created_at: str
    unread: bool
    shared: bool
    updated_at: Optional[str] = None
    archive_content: Optional[str] = None
    id: Optional[int] = None
    # Highlights from FTS
    title_highlight: Optional[str] = None
    desc_highlight: Optional[str] = None
    body_highlight: Optional[str] = None

@dataclass(frozen=True)
class SearchParams:
    query: Optional[str] = None
    tag: Optional[str] = None
    page: int = 1
    limit: int = 50

@dataclass(frozen=True)
class SearchResult:
    bookmarks: list[Bookmark]
    total_count: int
    page: int
    total_pages: int
