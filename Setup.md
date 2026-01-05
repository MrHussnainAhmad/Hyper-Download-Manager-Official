# Hyper Download Manager - Setup & User Guide

Welcome to **Hyper Download Manager (HDM)**. This comprehensive guide will assist you in installing, configuring, and mastering your new download manager. Designed for speed, privacy, and seamless browser integration, HDM is the ultimate tool for managing your downloads on Windows.

---

## 📋 Table of Contents
1.  [System Requirements](#1-system-requirements)
2.  [Installation Guide](#2-installation-guide)
3.  [Browser Integration](#3-browser-integration)
4.  [How to Download Files](#4-how-to-download-files)
5.  [Managing Downloads](#5-managing-downloads)
6.  [Updating the Application](#6-updating-the-application)
7.  [Uninstallation](#7-uninstallation)
8.  [Troubleshooting & FAQ](#8-troubleshooting--faq)

---

## 1. System Requirements
Before proceeding, please ensure your system meets the following prerequisites to guarantee optimal performance.

*   **Operating System**: Windows 10 (Version 2004 or later) or Windows 11.
*   **Processor**: 1 GHz or faster 64-bit (x64) processor.
*   **Memory (RAM)**: 4 GB minimum (8 GB recommended for heavy multitasking).
*   **Disk Space**: Approximately 200 MB of free check space for installation.
*   **Internet Connection**: Required for downloading files and receiving application updates.
*   **Supported Browsers**:
    *   Google Chrome (Latest Stable)
    *   Microsoft Edge (Chromium)
    *   Mozilla Firefox
    *   Brave Browser
    *   Opera / Vivaldi (via Chrome Extension store methods)

---

## 2. Installation Guide

### Step 1: Obtain the Installer
If you have not already, download the latest version of the installer (`HyperDownloadManager_Setup.exe`) from the official release channel or build it from source using `build_exe.bat`.

### Step 2: Run the Installation Wizard
1.  Locate the downloaded file, typically in your `Downloads` folder.
2.  Double-click `HyperDownloadManager_Setup.exe` to launch the wizard.
3.  **User Account Control (UAC)** may ask for permission. Click **Yes** to proceed.
4.  Follow the on-screen prompts:
    *   Review and accept the License Agreement.
    *   Choose the installation directory (Default: `C:\Program Files\HyperDownloadManager`).
    *   Select whether to create a desktop shortcut.
5.  Click **Install**. The process typically takes less than a minute.
6.  Once complete, click **Finish** to launch Hyper Download Manager.

> **Note**: The application will automatically start in the system tray area to be ready for your downloads immediately.

---

## 3. Browser Integration
To enable automatic download interception, you must install the helper extension in your preferred web browser.

### A. Google Chrome, Microsoft Edge, Brave, & Opera
Since the extension interacts directly with the desktop app, it is often side-loaded or installed via "Developer Mode" if not yet on the public store.

1.  **Open Extension Management**:
    *   **Chrome**: Type `chrome://extensions` in the address bar.
    *   **Edge**: Type `edge://extensions`.
    *   **Brave**: Type `brave://extensions`.
2.  **Enable Developer Mode**:
    *   Look for a toggle switch named **"Developer mode"** (usually top-right corner) and turn it **ON**.
3.  **Load the Extension**:
    *   Click the **"Load unpacked"** button that appears.
    *   Navigate to your installation folder (e.g., `C:\Program Files\HyperDownloadManager`).
    *   Select the folder named `extension`.
4.  **Confirm Installation**:
    *   You should now see "Hyper Download Manager" in your list of extensions.
    *   Ensure the toggle is set to **On/Enabled**.

### B. Mozilla Firefox
1.  Open Firefox and type `about:debugging` in the address bar.
2.  In the sidebar, click **"This Firefox"**.
3.  Click the **"Load Temporary Add-on..."** button.
4.  Navigate to the `extension` folder inside your HDM installation directory.
5.  Select the `manifest.json` file and click **Open**.
6.  The extension is now active for this session.

---

## 4. How to Download Files
HDM offers flexible ways to start your downloads.

### Method 1: Automatic Interception (Recommended)
Once the browser extension is active, HDM works silently in the background.
1.  Navigate to a website and click a download link.
2.  Instead of the browser's default download bar, the **HDM Add Download** dialog will appear.
3.  You can rename the file or change the destination folder if desired.
4.  Click **Download** to begin immediately.

### Method 2: Manual Addition
Ideal for downloads from non-browser sources or if the extension is disabled.
1.  Copy the direct download link (URL) of the file to your clipboard.
2.  Open the HDM main dashboard.
3.  Click the large **(+) Add** button in the toolbar.
4.  The application usually auto-detects the link in your clipboard. If not, paste it into the URL field.
5.  Click **Download**.

---

## 5. Managing Downloads
The main dashboard gives you full control over your files.

*   **Pause & Resume**: Right-click any active download to pause it (if supported by the server) and resume it later without losing progress.
*   **Prioritize**: If multiple files are downloading, HDM automatically manages bandwidth. (Future versions may allow manual reordering).
*   **Open Location**: Double-click a finished download (or use the folder icon) to open the directory containing your file.
*   **Remove**: Select a file and press `Delete` (or click the trash icon) to remove it from the list. You will be asked if you also want to delete the file from the disk.

---

## 6. Updating the Application
We frequently release updates to improve speed, fix bugs, and enhance compatibility.

1.  **Check for Updates**: Visit the official repository or check the "About" section in the app settings for new version notifications.
2.  **Download & Install**: Download the new installer. You do **not** need to uninstall the old version first.
3.  **Overwrite**: Run the installer; it will safely update all core files while keeping your download history and preferences intact.
4.  **Update Extension**:
    *   After an app update, go back to your browser's extension page (`chrome://extensions`, etc.).
    *   Find Hyper Download Manager.
    *   Click the **Reload** (circular arrow) icon to ensure the browser loads the latest scripts.

---

## 7. Uninstallation
If you wish to remove the software:

1.  **Close the App**: Right-click the HDM icon in the system tray and select **Exit/Quit**.
2.  **Windows Settings**: Go to **Settings > Apps > Installed apps**.
3.  **Find & Remove**: Search for "Hyper Download Manager", click the three dots menu, and select **Uninstall**.
4.  **Remove Extension**: Go to your browser's extension page and click **Remove** on the HDM extension.

---

## 8. Troubleshooting & FAQ

**Q: The download dialog doesn't appear when I click a link.**
*   **A**: Ensure the browser extension is installed and enabled. Also, check that HDM is running in the background (look for the icon in the system tray). Some websites use complex JavaScript blobs that might bypass automatic detection; in these cases, use **Method 2 (Manual Addition)**.

**Q: My download speed is slow.**
*   **A**: Speeds depend heavily on your internet connection and the server you are downloading from. HDM uses multi-threading to maximize speed, but we cannot exceed the physical limits of your bandwidth or server caps.

**Q: Does it support YouTube videos?**
*   **A**: Currently, HDM is designed for direct file downloads. Specialized video extraction is planned for a future release.

**Q: I get a "Network Error" repeatedly.**
*   **A**: Check your internet connection. If the file is very large or the server is unstable, try pausing and resuming after a few seconds.

---

*Thank you for choosing Hyper Download Manager. We are committed to providing the fastest and most reliable download experience.*
