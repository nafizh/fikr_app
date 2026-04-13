from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os

from . import logic, db, ai_client, inbox_worker, archiver
from .model import SearchParams, SearchResult
from .dtos import BookmarkCreateDTO, SuggestTagsRequest, SuggestTagsResponse, TagsResponse
from fastapi import HTTPException, status
from google.genai.types import GenerateContentConfig
import json
import threading

# Configuration - Relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import dateutil.parser

# ... existing code ...

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (including chrome-extension://...)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Background Worker Handling
def start_inbox_worker():
    """Run the inbox worker in a daemon thread."""
    try:
        inbox_worker.run_worker()
    except Exception as e:
        print(f"Inbox worker failed: {e}")

def start_archiver_worker():
    """Run the archiver worker in a daemon thread."""
    try:
        archiver.run_worker()
    except Exception as e:
        print(f"Archiver worker failed: {e}")

@app.on_event("startup")
async def startup_event():
    # Start the inbox worker in a background thread
    t1 = threading.Thread(target=start_inbox_worker, daemon=True)
    t1.start()
    
    # Start the archiver worker in a background thread
    t2 = threading.Thread(target=start_archiver_worker, daemon=True)
    t2.start()
    
    # Ensure tags.json is fresh on startup
    db.export_tags_to_json()

def format_timestamp(value):
    if not value:
        return ""
    try:
        # Parse UTC string from SQLite
        # SQLite returns "YYYY-MM-DD HH:MM:SS" (naive, but effectively UTC)
        # Note: dateutil handles the parsing robustly
        dt = dateutil.parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        # Convert to local system time
        local_dt = dt.astimezone()
        
        # Format nice string
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)

templates.env.filters["timestamp"] = format_timestamp

from .dtos import BookmarkCreateDTO, SuggestTagsRequest, SuggestTagsResponse, TagsResponse, BookmarkResponseDTO

# ... existing code ...

@app.get("/api/tags", response_model=TagsResponse)
async def get_tags():
    tags = db.fetch_all_tags()
    return {"tags": tags}

@app.get("/api/check", response_model=Optional[BookmarkResponseDTO])
async def check_bookmark(url: str):
    row = db.fetch_bookmark_by_url(url)
    if row:
        return dict(row)
    return None

@app.post("/api/suggest-tags", response_model=SuggestTagsResponse)
async def suggest_tags(req: SuggestTagsRequest):
    client, model = ai_client.get_gemini_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured (missing API key)"
        )

    existing_tags_str = ", ".join(req.existing_tags or [])
    current_tags_extra = f"Current tags on this bookmark: {existing_tags_str}\n" if existing_tags_str else ""

    # Fetch all system tags to encourage consistency
    all_db_tags = db.fetch_all_tags()
    system_vocab_str = ", ".join(all_db_tags)

    prompt = f"""
You are a tagging assistant for browser bookmarks.

Your task: Suggest concise, relevant tags for organizing this bookmark.
Rules:
- Return ONLY a JSON object of the form: {{"tags": ["tag1", "tag2", ...]}}
- Tags must be:
  - lowercase
  - 1–3 words each
  - multi-word tags MUST be joined by underscores (e.g. "machine_learning", "full_stack")
  - no punctuation except underscore
  - no duplicates
- PRIORITIZE using tags from the "System Vocabulary" below if they are relevant, to maintain consistency with the user's existing library.
- Also generate new, specific tags based on the content.
- Generate exactly {req.max_tags} tags.

System Vocabulary (comma-separated):
{system_vocab_str}

Bookmark data:
URL: {req.url}
Title: {req.title or "(none)"}
User Description: {req.description or "(none)"}
Page Content Snippet: {req.page_content or "(none)"}
{current_tags_extra}

Now respond with JSON only.
""".strip()

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=128,
                response_mime_type="application/json",
            ),
        )
        
        data = json.loads(response.text or "{}")
        tags = data.get("tags") or []
        
        # Cleanup
        clean_tags = []
        seen = set()
        for t in tags:
            if isinstance(t, str):
                tag = t.strip().lower()
                if tag and tag not in seen:
                    seen.add(tag)
                    clean_tags.append(tag)
                    
        return {"tags": clean_tags}
        
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/bookmark/{id}", response_class=HTMLResponse)
async def read_bookmark(request: Request, id: int):
    row = db.fetch_bookmark_by_id(id)
    if not row:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    bookmark = logic.row_to_bookmark(dict(row))
    return templates.TemplateResponse("detail.html", {"request": request, "bookmark": bookmark})

@app.get("/bookmark/{id}/edit", response_class=HTMLResponse)
async def edit_bookmark(request: Request, id: int):
    row = db.fetch_bookmark_by_id(id)
    if not row:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    bookmark = logic.row_to_bookmark(dict(row))
    all_tags = db.fetch_all_tags()
    return templates.TemplateResponse("edit.html", {
        "request": request, 
        "bookmark": bookmark,
        "all_tags": all_tags
    })

@app.post("/bookmark/{id}/edit")
async def update_bookmark_handler(
    id: int, 
    url: str = Form(...),
    title: str = Form(None),
    description: str = Form(None),
    tags: str = Form(None)
):
    try:
        db.update_bookmark_details(id, url, title or "", tags or "", description or "")
        db.export_tags_to_json()
        return RedirectResponse(url=f"/bookmark/{id}", status_code=303)
    except Exception as e:
        print(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    q: Optional[str] = None, 
    tag: Optional[str] = None, 
    page: int = 1
):
    # Orchestration (App Layer)
    limit = 50
    offset = logic.calculate_offset(page, limit)
    
    rows = []
    total_count = 0
    
    if q:
        fts_query = logic.sanitize_fts_query(q)
        rows, total_count = db.fetch_bookmarks_by_query(fts_query, limit, offset)
    elif tag:
        rows, total_count = db.fetch_bookmarks_by_tag(tag, limit, offset)
    else:
        rows, total_count = db.fetch_all_bookmarks(limit, offset)
    
    # Transform rows to domain models (Data)
    bookmarks = [logic.row_to_bookmark(dict(row)) for row in rows]
    
    total_pages = logic.calculate_pagination(total_count, limit, page)
    page_range = logic.get_pagination_range(page, total_pages)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "bookmarks": bookmarks,
        "q": q,
        "tag": tag,
        "page": page,
        "total_pages": total_pages,
        "page_range": page_range,
        "total_count": total_count
    })

@app.post("/api/refresh/{id}")
def refresh_bookmark(id: int):
    # Fetch fresh row
    row = db.fetch_bookmark_by_id(id)
    if not row:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    # Run archive process synchronously in threadpool
    try:
        archiver.process_bookmark(row)
        return {"status": "success", "id": id}
    except Exception as e:
        print(f"Manual refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete")
async def delete_bookmark(id: int):
    db.delete_bookmark(id)
    db.export_tags_to_json()
    return {"status": "success", "id": id}

@app.post("/api/add")
async def add_bookmark(item: BookmarkCreateDTO):
    action = db.add_or_update_bookmark(
        url=item.url, 
        title=item.title, 
        tags=item.tags, 
        description=item.description
    )
    db.export_tags_to_json()
    return {"status": "success", "action": action, "url": item.url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
