"""Windows helpers: tray icon, Start with Windows, and silent launch."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STARTUP_NAME = "AVA Assistant.vbs"


def project_python() -> Path:
    venv_pythonw = ROOT / ".venv" / "Scripts" / "pythonw.exe"
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_pythonw.exists():
        return venv_pythonw
    if venv_python.exists():
        return venv_python
    return Path(sys.executable)


def entry_script() -> Path:
    return ROOT / "start_ava.py"


def startup_folder() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_shortcut_path() -> Path:
    return startup_folder() / STARTUP_NAME


def is_start_with_windows() -> bool:
    return startup_shortcut_path().exists()


def set_start_with_windows(enabled: bool) -> str:
    shortcut = startup_shortcut_path()
    if not enabled:
        if shortcut.exists():
            shortcut.unlink()
        return "AVA will no longer start with Windows."

    python = project_python()
    script = entry_script()
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    contents = (
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        f'WshShell.CurrentDirectory = "{ROOT}"\r\n'
        f'WshShell.Run """{python}"" ""{script}""", 0, False\r\n'
    )
    shortcut.write_text(contents, encoding="utf-8")
    return "AVA will start with Windows and listen for Hey AVA."


def make_tray_image():
    from PIL import Image, ImageDraw, ImageFont

    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((2, 2, size - 3, size - 3), fill=(14, 22, 34, 255), outline=(46, 230, 199, 255), width=3)
    draw.ellipse((18, 18, 46, 46), fill=(46, 230, 199, 255))
    try:
        font = ImageFont.truetype("segoeui.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 21), "A", fill=(7, 11, 18, 255), font=font)
    return image
