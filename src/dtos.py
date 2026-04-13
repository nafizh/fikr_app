from pydantic import BaseModel
from typing import List, Optional

class BookmarkCreateDTO(BaseModel):
    url: str
    title: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None

class SuggestTagsRequest(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    page_content: Optional[str] = None
    existing_tags: Optional[List[str]] = None
    max_tags: int = 8

class SuggestTagsResponse(BaseModel):
    tags: List[str]

class TagsResponse(BaseModel):
    tags: List[str]

class BookmarkResponseDTO(BaseModel):
    id: int
    url: str
    title: Optional[str]
    tags: Optional[str]
    description: Optional[str]
