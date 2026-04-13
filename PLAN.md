# Project: Personal Pinboard Replacement

## 1. Data Rescue (Pinboard Migration)

Since the Pinboard API is unreliable, we will use one of the following methods to export your data:

### **Option A: Native HTML Export (Try this first)**
1.  Log in to Pinboard.
2.  Visit [https://pinboard.in/export/](https://pinboard.in/export/) (or go to Settings -> Backup).
3.  Download the **HTML** export (this includes tags and timestamps).
4.  If this works, we can simply import this file.

### **Option B: Local Scraper (Backup method)**
If the export page fails, we will use a custom Python script to "scrape" your bookmarks by simulating a web browser.
*   **How it works:** You run the script on your machine. It uses your session cookie to browse through your bookmarks page by page and saves them to a `pinboard_backup.json` file.
*   **Security:** You do not need to give me your password. You will run the script locally.
*   **Script:** I have prepared `pinboard_export.py` for this purpose.

---

## 2. System Architecture

We will build a simple, self-hosted application that mimics Pinboard's functionality while adding the specific features you requested.

### **Stack**
*   **Backend:** Python (FastAPI) - Lightweight, fast, and easy to modify.
*   **Database:** SQLite - Simple, file-based database (easy to back up, no server setup required).
*   **Frontend:** HTML/CSS (Jinja2 Templates) - To replicate the dense, text-heavy Pinboard UI.

### **Components**

#### **1. The Web UI (Pinboard Clone)**
*   A minimalist list view of bookmarks.
*   Tags displayed prominently next to/below titles.
*   "Unread" and "Starred" filters.
*   Search functionality.
*   **New Feature:** A "Preview" button/link to view the archived text of the bookmark.

#### **2. Desktop Integration (Custom Extension)**
*   **Mechanism:** A lightweight, custom Chrome/Brave extension.
*   **Workflow:**
    *   **Option A (One-Click):** Click the extension icon (or press a custom hotkey like `Alt+B`). The page is instantly saved.
    *   **Option B (Popup):** Press the hotkey, a small popup appears allowing you to edit the title or add tags before saving.
*   **Advantage:** 
    *   Faster than native bookmarking.
    *   Completely separate from Brave's internal bookmark system.
    *   Can capture the **current page text** immediately (speeding up the archiving process).

#### **3. Mobile Integration (iOS)**
*   **Replacement for "Pins for Pinboard":** We will use an **iOS Shortcut**.
*   **Workflow:**
    1.  You are on a page in Safari (or any app).
    2.  Tap "Share".
    3.  Select "Save to MyBookmarks".
    4.  The Shortcut sends the URL and Title to your server in the background.
*   **Why:** This is faster and more reliable than building a custom iOS app, and it integrates deeply with the system.

#### **4. Offline Archiving**
*   **Tool:** `trafilatura` (a powerful Python library for extracting text from web pages).
*   **Workflow:**
    1.  When a bookmark is added (via Brave or iOS), the system queues it.
    2.  A background worker fetches the webpage.
    3.  It extracts the main article text (removing ads/nav).
    4.  It saves the text to the database for offline reading.

---

## 3. Implementation Roadmap

1.  **Step 1: Data Export** - Run the `pinboard_export.py` script or get the HTML export.
2.  **Step 2: Core System Setup** - Initialize the FastAPI app and SQLite database.
3.  **Step 3: Import** - Write a script to import the Pinboard data into the new database.
4.  **Step 4: Web UI** - Build the basic list view to match Pinboard's look.
5.  **Step 5: Archiver** - Implement the background text fetcher.
6.  **Step 6: Desktop Extension** - Create a simple "Unpacked" Chrome extension for one-click bookmarking.
7.  **Step 7: iOS Shortcut** - Create and configure the iOS Shortcut.
