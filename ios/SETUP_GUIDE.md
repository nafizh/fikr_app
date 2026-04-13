# Fikr iOS App Setup Guide (Beginner-Friendly)

This guide assumes you've never done iOS development or used Tailscale before.

---

## Part 1: Install Tailscale (5 minutes)

Tailscale creates a private network between your devices, so your iPhone can reach your Mac from anywhere (home, coffee shop, etc.)

### Step 1.1: Install Tailscale on Mac

1. Go to https://tailscale.com/download/mac
2. Click "Download Tailscale for Mac"
3. Open the downloaded file and drag Tailscale to Applications
4. Open Tailscale from Applications
5. Click the Tailscale icon in your menu bar (top right, looks like a network icon)
6. Click "Log in" and create an account (use Google/GitHub/etc.)

### Step 1.2: Install Tailscale on iPhone

1. Open App Store on your iPhone
2. Search for "Tailscale"
3. Install it (free)
4. Open the app and log in with the SAME account you used on Mac

### Step 1.3: Get Your Mac's Tailscale IP

Once both devices are logged in:

1. Open Terminal on your Mac
2. Run this command:
   ```bash
   tailscale ip -4
   ```
3. You'll see something like: `100.64.0.1`
4. **Write this down!** You'll need it later.

To verify both devices are connected:
- Click the Tailscale icon in Mac menu bar
- You should see both your Mac and iPhone listed as "Connected"

---

## Part 2: Install Xcode (30-60 minutes)

Xcode is Apple's tool for building iOS apps.

### Step 2.1: Download Xcode

1. Open the App Store on your Mac
2. Search for "Xcode"
3. Click "Get" / "Install" (it's free but large ~12GB)
4. Wait for download and installation (this takes a while!)

### Step 2.2: First-Time Xcode Setup

1. Open Xcode from Applications
2. Accept the license agreement
3. It will install additional components (wait for this to finish)
4. You may need to enter your Mac password

---

## Part 3: Prepare Your iPhone (5 minutes)

### Step 3.1: Enable Developer Mode on iPhone

For iOS 16+, you need to enable Developer Mode:

1. On your iPhone, go to **Settings > Privacy & Security**
2. Scroll down to find **Developer Mode**
3. Turn it ON
4. Your iPhone will restart
5. After restart, confirm you want to enable Developer Mode

### Step 3.2: Trust Your Mac

1. Connect your iPhone to your Mac with a USB cable
2. On your iPhone, tap "Trust" when asked "Trust This Computer?"
3. Enter your iPhone passcode

---

## Part 4: Configure the Xcode Project (10 minutes)

### Step 4.1: Open the Project

1. Open Terminal
2. Run:
   ```bash
   open ~/fikr_app/ios/Fikr/Fikr.xcodeproj
   ```

Xcode will open with the Fikr project.

### Step 4.2: Sign In to Your Apple ID

1. In Xcode menu bar: **Xcode > Settings** (or press Cmd+,)
2. Click the **Accounts** tab
3. Click the **+** button at bottom left
4. Choose **Apple ID**
5. Sign in with your Apple ID (same one you use for App Store)
6. Close the Settings window

### Step 4.3: Configure Signing for Main App

1. In the left sidebar, click on **Fikr** (the blue icon at the very top - this is the project)
2. In the middle panel, under **TARGETS**, click **Fikr**
3. Click the **Signing & Capabilities** tab
4. Check ✓ **Automatically manage signing**
5. For **Team**, select your Apple ID from the dropdown
   - It will show as "Your Name (Personal Team)"
6. If you see any red errors, they should resolve after selecting your team

### Step 4.4: Configure Signing for Share Extension

1. In the middle panel, under **TARGETS**, click **FikrShare**
2. Click the **Signing & Capabilities** tab
3. Check ✓ **Automatically manage signing**
4. For **Team**, select the same Apple ID

You should now see NO red error messages.

---

## Part 5: Start the Server (2 minutes)

The FastAPI server must be running on your Mac for the app to work.

### Step 5.1: Start the Server

1. Open a NEW Terminal window (don't close the Xcode one)
2. Run:
   ```bash
   cd ~/fikr_app
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

3. You should see output like:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

4. **Keep this terminal open!** The server needs to stay running.

The `--host 0.0.0.0` is important - it allows connections from other devices (your iPhone via Tailscale).

---

## Part 6: Build and Run the App (5 minutes)

### Step 6.1: Select Your iPhone

1. In Xcode, look at the top toolbar
2. You'll see something like "Fikr > iPhone 15 Pro" 
3. Click on "iPhone 15 Pro" (or whatever simulator is shown)
4. A dropdown appears - select your physical iPhone
   - It will show as "Your iPhone Name"
   - If you don't see it, make sure it's connected via USB

### Step 6.2: Build and Install

1. Press **Cmd+R** (or click the ▶ Play button)
2. Xcode will build the app (first time takes 1-2 minutes)
3. You may see a popup: "codesign wants to access key..." - click **Always Allow**
4. The app will install on your iPhone

### Step 6.3: Trust the Developer on iPhone

The FIRST time you install, iPhone will block the app:

1. On your iPhone, go to **Settings > General > VPN & Device Management**
2. Under "Developer App", tap your Apple ID email
3. Tap **Trust "[your email]"**
4. Tap **Trust** to confirm

### Step 6.4: Run the App Again

1. Back in Xcode, press **Cmd+R** again
2. The Fikr app should now open on your iPhone!

---

## Part 7: Configure the App (2 minutes)

### Step 7.1: Enter Server URL

1. The app opens to a Settings screen
2. In the **Server URL** field, enter:
   ```
   http://100.64.0.1:8000
   ```
   (Replace `100.64.0.1` with YOUR Tailscale IP from Part 1)

3. Tap **Save & Test Connection**
4. If successful, you'll see a green checkmark ✓
5. The app will automatically fetch your tags

### Step 7.2: Troubleshooting Connection Issues

If connection fails:

1. **Is the server running?** Check the terminal from Part 5
2. **Is Tailscale connected?** Check both devices show "Connected"
3. **Correct IP?** Run `tailscale ip -4` again to verify
4. **Try from Safari first:** On iPhone, open Safari and go to `http://100.64.0.1:8000/api/tags` - you should see JSON

---

## Part 8: Using the App

### Bookmarking from Safari

1. Open Safari on iPhone
2. Go to any webpage
3. Tap the Share button (square with arrow)
4. Scroll down and tap **Fikr**
5. The bookmark form appears with URL pre-filled
6. Type in the tag field - autocomplete suggestions appear!
7. Tap **AI Suggest** to get AI-powered tag suggestions
8. Tap **Save**

### Bookmarking from Twitter/X

Same process - share any tweet and select Fikr.

---

## Common Issues & Solutions

### "Untrusted Developer" error on iPhone
→ See Step 6.3 above

### "Could not launch Fikr" in Xcode
→ Make sure Developer Mode is enabled (Step 3.1)

### App can't connect to server
→ Check that:
- Server is running (Part 5)
- Both devices on Tailscale
- Using correct Tailscale IP (not your regular local IP)

### "No provisioning profile" error in Xcode
→ Make sure you selected your Team in Signing settings (Step 4.3)

### Share Extension doesn't appear
→ Try restarting your iPhone after first install

### Server shows "connection refused"
→ Make sure you started with `--host 0.0.0.0`, not `--host 127.0.0.1`

---

## Quick Reference

**Start Server:**
```bash
cd ~/fikr_app
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Get Tailscale IP:**
```bash
tailscale ip -4
```

**Open Project:**
```bash
open ~/fikr_app/ios/Fikr/Fikr.xcodeproj
```

---

## After Initial Setup

Once everything is set up, your daily workflow is:

1. Make sure Tailscale is running on Mac (it usually auto-starts)
2. Start the server: `cd ~/fikr_app && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000`
3. Use the Share Sheet on iPhone to bookmark!

The app stays installed - you only need Xcode again if you want to update the app code.
