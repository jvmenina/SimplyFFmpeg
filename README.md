# SimplyFFmpeg

SimplyFFmpeg is an easy-to-use GUI for FFmpeg, perfect for quick and simple multimedia processing.

## Prerequisites

- You must have [FFmpeg](https://www.ffmpeg.org/download.html) installed to use this application
    - Windows: 
        - Powershell - `winget install ffmpeg`
        - Manual Install - [Download Link](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z)
    - Linux:
        - Arch - `sudo pacman -S ffmpeg`
        - Debian - `sudo apt install ffmpeg`
        - Fedora - `sudo dnf install ffmpeg`

## Build Instructions

For Windows users, replace `python3` with `python`.

1. Create a virtual environment
    - `python3 -m venv .venv`
2. Activate virtual environment (Can be skipped, see below)
    - Windows: `.venv\Scripts\activate`
    - Linux: `source .venv/bin/activate`
3. Install dependencies
    - `python3 -m pip install -r requirements.txt`
4. Either...
    - Compile as executable: `python3 -m PyInstaller --onefile -n "SimplyFFmpeg" "./main.py"`
    - Or, run it directly: `python3 "./main.py"`

Alternatively, virtual environment activation may be skipped:
```powershell
# NOTE: This is in Powershell
python -m venv .venv
& "./.venv/Scripts/python.exe" -m pip install -r requirements.txt
& "./.venv/Scripts/python.exe" -m PyInstaller --onefile -n "SimplyFFmpeg" "./main.py"
& "./.venv/Scripts/python.exe" "./main.py"
```
