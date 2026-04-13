# iOS App Plan for Fikr

This document outlines the steps to build a native iOS app to replace your Shortcuts workflow. This app will provide a superior UI with instant tag autocompletion.

## 1. Prerequisites
1.  **Mac with Xcode**: Install the latest Xcode from the Mac App Store.
2.  **Apple Developer Account**: You need an Apple ID. A free account works for installing on your own device (though you have to re-sign every 7 days). A paid account ($99/year) avoids this.
3.  **Dropbox App**: You need to register an app with Dropbox to get API access.

## 2. Dropbox Setup
1.  Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
2.  Click **Create app**.
3.  Choose **Scoped access**.
4.  Choose **App folder** access (safest, only gives access to one folder).
5.  Name it (e.g., `FikrBookmarkManager`).
6.  It will create a folder in your Dropbox at `/Apps/FikrBookmarkManager`.
    *   *Note*: You will need to move your `fikr_app` content into this new folder, or choose "Full Dropbox" access if you want to keep your current folder structure (`/fikr_app`).
    *   *Recommendation*: "Full Dropbox" is easier if you don't want to move files. Just be careful with the code.
7.  In the Settings tab:
    *   Note the **App key** and **App secret**.
    *   Add a **Redirect URI**: `fikrapp://oauth2redirect`

## 3. Xcode Project Setup
1.  Open Xcode -> **Create a new Xcode Project**.
2.  Choose **iOS** -> **App**.
3.  Product Name: `Fikr`
    *   Organization Identifier: `com.nafizh` (or similar)
    *   Interface: **SwiftUI**
    *   Language: **Swift**
4.  **Capabilities**:
    *   Click on the project root in the navigator.
    *   Select the Target `Fikr`.
    *   Go to **Signing & Capabilities**.
    *   Click **+ Capability** -> **App Groups**.
    *   Create a new group: `group.com.nafizh.fikr`. (This allows the Share Extension to share login tokens with the main app).

## 4. Add Share Extension
1.  File -> New -> **Target**.
2.  Choose **iOS** -> **Share Extension**.
3.  Name: `FikrShare`.
4.  In the prompt "Activate 'FikrShare' scheme?", click **Activate**.
5.  Go to **Signing & Capabilities** for the `FikrShare` target.
6.  Add **App Groups** and select the same group (`group.com.nafizh.fikr`).

## 5. Implementation Plan
I (Amp) can generate the Swift code for you. We will need:
1.  **DropboxClient.swift**: Handles OAuth and Upload/Download.
2.  **TagsStore.swift**: Handles loading `tags.json`, caching it, and filtering for autocomplete.
3.  **ShareView.swift**: The SwiftUI view that shows the URL, Title, and the Autocomplete Tag Input.

## 6. Next Steps
Once you have the "Hello World" empty project created:
1.  Tell me you are ready.
2.  I will provide the Swift code for the files mentioned above.
3.  You will copy-paste them into Xcode.
4.  We will wire up the `Info.plist` for the Dropbox OAuth redirect.
