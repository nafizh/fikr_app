import time
import trafilatura
import re
import sqlite3
from playwright.sync_api import sync_playwright
from . import db
from .ai_client import ocr_tweet_from_screenshot

# Get DB Path from db module or define it here
DB_PATH = db.DB_PATH

def extract_title(html_content):
    """
    Extract title from HTML content using trafilatura or regex.
    """
    if not html_content:
        return None
        
    match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        raw_title = match.group(1).strip()
        
        # Special handling for X/Twitter to keep it clean
        # Format usually: "Name (@handle) on X: \"Tweet content\" / X"
        if " on X:" in raw_title:
            # Keep only the part before the colon
            clean_title = raw_title.split(" on X:")[0] + " on X"
            return clean_title
            
        # Format variation: "Name on X: \"Tweet\""
        if " on X" in raw_title and ": \"" in raw_title:
             clean_title = raw_title.split(": \"")[0]
             return clean_title

        return raw_title
    return None

def update_x_titles():
    """Special utility to fix X titles in DB retrospectively."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find X bookmarks with long titles
    cursor.execute("SELECT id, title FROM bookmarks WHERE (url LIKE '%x.com%' OR url LIKE '%twitter.com%') AND title LIKE '% on X:%'")
    rows = cursor.fetchall()
    
    count = 0
    for r in rows:
        bid, old_title = r
        if " on X:" in old_title:
            new_title = old_title.split(" on X:")[0] + " on X"
            cursor.execute("UPDATE bookmarks SET title = ? WHERE id = ?", (new_title, bid))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Fixed {count} X.com titles.")

def fetch_with_playwright(url: str):
    """
    Fetch URL using Playwright (for SPAs like X.com, YouTube, etc.)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars"
                ]
            )
            # Use a consistent context to reuse cookies/cache if we were persisting it,
            # but here we just want a fresh page with a real User-Agent.
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
                locale="en-US",
            )
            page = context.new_page()
            
            # Mask webdriver
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Go to URL
            print(f"  [Playwright] Navigating to {url}...")
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Specific waiting logic for SPAs
            if "x.com" in url or "twitter.com" in url:
                try:
                    # Wait for the actual tweet content
                    page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
                except Exception:
                    print("  [Playwright] Timeout waiting for X tweet, dumping whatever we have...")
            else:
                # Generic wait for other SPAs
                time.sleep(3)
            
            content = page.content()
            
            # Take screenshot for X/Twitter
            screenshot_b64 = None
            if "x.com" in url or "twitter.com" in url:
                try:
                    import base64
                    screenshot_bytes = page.screenshot(full_page=False)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception as e:
                    print(f"  [Playwright] Screenshot failed: {e}")

            browser.close()
            return content, screenshot_b64
    except Exception as e:
        print(f"  [Playwright] Error fetching {url}: {e}")
        return None, None

def archive_url(url: str):
    """
    Fetch and extract content from a URL.
    Returns (text_content, html_content, extracted_title, screenshot_b64)
    """
    # Heuristic: If it's a known SPA or 'difficult' site, skip straight to Playwright
    # Or if trafilatura fails, fallback to Playwright.
    
    is_spa = any(domain in url.lower() for domain in ["x.com", "twitter.com", "youtube.com", "instagram.com"])
    
    html_content = None
    screenshot_b64 = None
    
    if is_spa:
        html_content, screenshot_b64 = fetch_with_playwright(url)
    else:
        # Try standard fetch
        try:
            html_content = trafilatura.fetch_url(url)
        except Exception:
            pass
            
    # Fallback: If trafilatura failed (returned None) but it wasn't flagged as SPA, try Playwright now
    if not html_content and not is_spa:
        print("  Standard fetch failed, retrying with Playwright...")
        html_content, screenshot_b64 = fetch_with_playwright(url)
    
    # Fallback 2: If we got HTML but extraction is suspicious (very short), try Playwright
    # (Only if we haven't used Playwright yet)
    if html_content and not is_spa:
        text_check = trafilatura.extract(html_content)
        if not text_check or len(text_check) < 200:
            print(f"  Extracted text is too short ({len(text_check) if text_check else 0} chars). Retrying with Playwright...")
            html_content, screenshot_b64 = fetch_with_playwright(url)
        
    if html_content:
        # Extract text and title
        text = trafilatura.extract(html_content)
        title = extract_title(html_content)
        return text, html_content, title, screenshot_b64
            
    return None, None, None, None

def process_bookmark(row: sqlite3.Row):
    """Archive a single bookmark row and update DB."""
    print(f"Archiving: {row['url']}")
    text, html, extracted_title, screenshot_b64 = archive_url(row['url'])
    
    # Determine if it's X.com
    is_x = "x.com" in row['url'] or "twitter.com" in row['url']

    # If this is an X link and the extracted text looks wrong, try Gemini OCR on the screenshot.
    if is_x and screenshot_b64:
        bad_or_missing_text = (
            not text
            or "JavaScript is disabled" in text
            or "Something went wrong" in text
            or "Sign up now" in text
            or "New to X?" in text
            or "Don’t miss what’s happening" in text
            or "Trending now" in text
            or "What’s happening" in text
            or "Terms of Service" in text
            or "Who can reply?" in text
            or len(text.strip()) < 40  # very short is suspicious for a tweet
        )
        if bad_or_missing_text:
            print("  -> Using Gemini OCR to extract tweet text from screenshot...")
            ocr_text = ocr_tweet_from_screenshot(screenshot_b64)
            if ocr_text:
                text = ocr_text
            else:
                print("  [Gemini OCR] Failed or returned empty text; keeping original text (if any).")
    
    # Determine if we should update the title
    current_title = row['title'] or ""
    new_title = None
    
    should_update = False
    if extracted_title:
        if not current_title.strip(): should_update = True
        elif current_title.strip().lower() in ["[no title]", "no title", "untitled"]: should_update = True
        elif current_title.strip() == row['url']: should_update = True
        elif is_x and len(current_title) > 50 and " on X" in extracted_title: should_update = True
    
    if should_update:
        print(f"  -> Updating title to: {extracted_title}")
        new_title = extracted_title
    
    # Update DB with screenshot (we need to add a column for it first)
    # For now, let's just append it to archive_html or text if we can't alter schema easily
    # Actually, let's add a column. But for this immediate step, let's embed it in the archive_content as an image tag
    
    final_content = text or ""
    if screenshot_b64:
        img_tag = f'\n\n<img src="data:image/png;base64,{screenshot_b64}" style="max-width:100%; border:1px solid #ccc; margin-top:20px;">'
        if html:
            html += img_tag
        # We append it to archive_content so it shows up in the reader view
        # The reader view uses | safe, so this HTML will render.
        final_content += img_tag

    db.update_bookmark_archive(row['id'], final_content, html, new_title)

def run_worker():
    print("Starting Archiver Worker...")
    while True:
        bookmarks = db.fetch_unarchived_bookmarks(limit=5)
        if not bookmarks:
            print("No bookmarks to archive. Sleeping...")
            time.sleep(60)
            continue
            
        for row in bookmarks:
            process_bookmark(row)
            
            # Be polite to servers
            time.sleep(2)

if __name__ == "__main__":
    run_worker()
