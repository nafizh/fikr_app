import os
import time
import json
import shutil
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing 'src' modules if run directly
# This handles cases where we run 'python3 src/inbox_worker.py'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src import db

# Configuration
# We assume the 'inbox' folder is at the root of the project (workspace root)
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX_DIR = PROJECT_ROOT / "inbox"
PROCESSED_DIR = INBOX_DIR / "processed"
ERROR_DIR = INBOX_DIR / "error"

POLL_INTERVAL_SECONDS = 5

def ensure_dirs():
    """Ensure inbox and status directories exist."""
    for d in [INBOX_DIR, PROCESSED_DIR, ERROR_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def process_file(path: Path):
    print(f"[Inbox] Found file: {path.name}")
    try:
        # Read file
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            print(f"[Inbox] Skipping empty file: {path.name}")
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[Inbox] Invalid JSON in {path.name}")
            shutil.move(str(path), str(ERROR_DIR / path.name))
            return

        # Extract fields
        url = data.get("url")
        if not url:
            print(f"[Inbox] No URL found in {path.name}")
            shutil.move(str(path), str(ERROR_DIR / path.name))
            return

        title = data.get("title") or url
        tags_raw = data.get("tags")
        if isinstance(tags_raw, list):
            tags = " ".join(str(t) for t in tags_raw)
        else:
            tags = str(tags_raw) if tags_raw else ""
            
        description = data.get("description") or ""

        # Add to DB
        action = db.add_or_update_bookmark(
            url=url,
            title=title,
            tags=tags,
            description=description,
        )
        db.export_tags_to_json()
        print(f"[Inbox] {action.upper()}: {url}")

        # Move to processed
        dest = PROCESSED_DIR / path.name
        shutil.move(str(path), str(dest))

    except Exception as e:
        print(f"[Inbox] Error processing {path.name}: {e}")
        # Move to error folder
        dest = ERROR_DIR / path.name
        try:
            shutil.move(str(path), str(dest))
        except Exception as move_err:
            print(f"[Inbox] Failed to move {path.name} to error dir: {move_err}")

def run_worker():
    ensure_dirs()
    print(f"Starting Inbox Worker...")
    print(f"Watching: {INBOX_DIR}")
    print(f"Processed: {PROCESSED_DIR}")
    
    while True:
        try:
            # Check for .json files
            # We convert to list to avoid issues if files are moved during iteration
            files = sorted(list(INBOX_DIR.glob("*.json")))
            
            for f in files:
                # Skip if it's inside processed/error (glob shouldn't pick them up if they are subdirs, 
                # but let's be safe if structure changes)
                if PROCESSED_DIR in f.parents or ERROR_DIR in f.parents:
                    continue
                    
                process_file(f)
                
        except Exception as loop_err:
            print(f"[Inbox] Loop error: {loop_err}")
            
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_worker()
