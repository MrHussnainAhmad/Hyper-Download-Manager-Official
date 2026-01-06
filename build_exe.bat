@echo off
echo Incrementing Version...
python increment_version.py

echo Converting Icon...
python convert_icon.py

echo Installing/Upgrading PyInstaller...
python -m pip install pypiwin32
python -m pip install --upgrade pyinstaller
python -m pip install Pillow

echo Building Hyper Download Manager (Windowed)...
python -m PyInstaller --noconfirm --onedir --windowed --name "HyperDownloadManager" --icon "icon.ico" --add-data "ui;ui" --add-data "core;core" --add-data "utils;utils" --add-data "extension;extension" --add-data "LICENSE.txt;." --add-data "icon.png;." --add-data "icon.ico;." --add-data "version.txt;." main.py

echo Building Native Messaging Host (Console)...
python -m PyInstaller --noconfirm --onefile --console --name "nm_host" --icon "icon.ico" nm_host.py

echo Copying Host to Main Distribution...
copy "dist\nm_host.exe" "dist\HyperDownloadManager\nm_host.exe"
copy "nm_manifest_prod.json" "dist\HyperDownloadManager\nm_manifest.json"

echo Compiling Installer...
:: Check if ISCC is in PATH, otherwise try standard path or warn
where ISCC >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    ) else (
        echo "ISCC.exe not found in PATH or standard location."
        echo "Please install Inno Setup or add it to PATH to build the installer automatically."
    )
) else (
    ISCC installer.iss
)

echo Build Cycle Complete.
pause
