# Hyper Download Manager (HDM)

**Hyper Download Manager** is a high-performance, open-source download accelerator built with Python and PySide6. Designed for speed, privacy, and simplicity, it integrates seamlessly with modern browsers to manage your downloads efficiently.

![HDM Logo](icon.png)

## 🚀 Key Features

*   **Multi-Threaded Acceleration**: Splits files into chunks to maximize download speed.
*   **Modern UI**: Clean, native interface inspired by Windows 11 aesthetics.
*   **Deep Browser Integration**: Replaces the default download manager in Chrome, Edge, Brave, and Firefox via Native Messaging.
*   **Smart Persistence**: Automatically saves progress on status changes and restarts.
*   **Single Instance**: Smart link handling focuses the existing window effectively.
*   **Privacy Focused**: No data tracking or telemetry. Local storage only.

## 🛠️ Installation & Build

### Requirements
*   Python 3.10+
*   Windows 10/11

### Manual Setup (Development)
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

### Building the Executable
To create a standalone `.exe` installer:
1.  Run the build script:
    ```cmd
    build_exe.bat
    ```
2.  This will:
    *   Clean previous builds.
    *   Package the application using PyInstaller.
    *   Bundle the extension and Native Host.
    *   Generate an Installer (if Inno Setup is installed).

## 🧩 Browser Extensions

HDM uses a **Native Messaging Host** to communicate with browsers.
*   **Extension Source**: Located in `extension/` directory.
*   **Native Host**: Located in `nm_host.py` (compiled to `nm_host.exe`).

### Supported Browsers
*   **Google Chrome**
*   **Microsoft Edge**
*   **Brave Browser**
*   **Mozilla Firefox**

## 📂 Project Structure

*   `core/`: Backend logic (Downloader, Manager, Worker threads).
*   `ui/`: PySide6 User Interface (Windows, Dialogs, Widgets).
*   `extension/`: Browser extension source code (Manifest V3).
*   `utils/`: Helper functions and system monitors.
*   `Installers/`: Output directory for compiled setup files.

## 📄 License & Copyright

**Project Owner: Hussnain Ahmad**

> [!WARNING]
> **Strictly Prohibited:** Unauthorized modification, redistribution, or reverse engineering of this software is strictly prohibited without explicit permission. This project is the intellectual property of Hussnain Ahmad. All rights reserved.
