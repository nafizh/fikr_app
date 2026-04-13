# Fikr iOS App

A native iOS app for bookmarking URLs with tag autocomplete, connecting to your FastAPI server via Tailscale.

## Architecture

```
iPhone (Fikr App) --[Tailscale VPN]--> Mac (FastAPI server at 100.x.x.x:8000)
```

## Prerequisites

1. **Mac**: FastAPI server running (`make run` or `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000`)
2. **Tailscale**: Installed on both Mac and iPhone, logged into same account
3. **Xcode 15+**: On your Mac for building the iOS app

## Setup Instructions

### 1. Get Your Mac's Tailscale IP

```bash
tailscale ip -4
```

This will show something like `100.64.0.1`. Note this down.

### 2. Start the FastAPI Server

```bash
cd ~/fikr_app
make run
# or: uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The server must bind to `0.0.0.0` (not `127.0.0.1`) to accept Tailscale connections.

### 3. Open in Xcode

```bash
open ios/Fikr/Fikr.xcodeproj
```

### 4. Configure Signing

1. Select the project in the navigator
2. Select the `Fikr` target
3. Go to "Signing & Capabilities"
4. Select your Team (Apple ID)
5. Repeat for the `FikrShare` target

### 5. Build and Run

1. Connect your iPhone via USB
2. Select your iPhone as the destination
3. Press Cmd+R to build and run

### 6. Configure the App

1. Open the Fikr app on your iPhone
2. Enter your Mac's Tailscale IP: `http://100.x.x.x:8000`
3. Tap "Save & Test Connection"
4. If successful, tags will be fetched

## Using the App

### From Share Sheet

1. In Safari, Twitter, or any app, tap the Share button
2. Scroll and tap "Fikr"
3. The bookmark form appears with the URL pre-filled
4. Type in the tag field for autocomplete suggestions
5. Tap "AI Suggest" for AI-powered tag suggestions
6. Tap Save

### Features

- **Tag Autocomplete**: Type to filter through 1000+ tags with prefix/substring matching
- **AI Tag Suggestions**: Uses Gemini to suggest relevant tags based on URL/title
- **New Tags**: Type any new tag and press + or Enter to add it
- **Tag Chips**: Visual tag chips with easy removal

## Troubleshooting

### "No server configured"

Open the main Fikr app and enter your server URL.

### Connection Failed

1. Verify Tailscale is running on both devices
2. Check that both devices show as "Connected" in Tailscale admin
3. Verify the FastAPI server is running with `--host 0.0.0.0`
4. Test from iPhone: try opening `http://100.x.x.x:8000/api/tags` in Safari

### Share Extension Not Appearing

1. Make sure both targets built successfully
2. Try restarting your iPhone
3. Check that the app is installed (not just running from Xcode)

## Files Structure

```
ios/Fikr/
├── Fikr.xcodeproj/
├── Fikr/
│   ├── FikrApp.swift          # App entry point
│   ├── ContentView.swift      # Main view (settings)
│   ├── SettingsView.swift     # Server config UI
│   ├── BookmarkView.swift     # Bookmark form with tag autocomplete
│   ├── APIClient.swift        # Network layer
│   ├── TagStore.swift         # Tag caching & filtering
│   ├── Models.swift           # Data models
│   └── Assets.xcassets/
└── FikrShare/
    ├── ShareViewController.swift  # Share extension entry
    ├── ShareView.swift            # Wraps BookmarkView
    └── Info.plist                 # Extension config
```

## API Endpoints Used

- `GET /api/tags` - Fetch all tags for autocomplete
- `POST /api/add` - Save a bookmark
- `POST /api/suggest-tags` - AI tag suggestions
