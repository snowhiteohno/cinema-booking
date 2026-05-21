"""
src/core/screenshot.py
Screen capture — works on Windows (mss / PIL ImageGrab) and Linux (gnome-screenshot / grim / mss).

Linux GNOME Wayland note: mss/grim produce black images there; use gnome-screenshot:
  sudo apt install gnome-screenshot
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
from PIL import Image
import numpy as np


def _is_black(path: str) -> bool:
    try:
        img = Image.open(path).convert("RGB")
        return np.array(img).mean() < 5
    except Exception:
        return True


def _try_gnome_screenshot(path: str) -> bool:
    try:
        r = subprocess.run(["gnome-screenshot", "-f", path],
                           timeout=8, capture_output=True)
        return r.returncode == 0 and os.path.exists(path) and not _is_black(path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _try_grim(path: str) -> bool:
    try:
        r = subprocess.run(["grim", path], timeout=5, capture_output=True)
        return r.returncode == 0 and os.path.exists(path) and not _is_black(path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _try_mss(path: str) -> bool:
    try:
        import mss
        with mss.mss() as sct:
            raw = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            img.save(path, "PNG")
            return not _is_black(path)
    except Exception:
        return False


def _try_imagegrab(path: str) -> bool:
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(path, "PNG")
        return not _is_black(path)
    except Exception:
        return False


def take_screenshot(monitor: int = 0) -> Image.Image:
    """Capture the full screen. Returns a PIL Image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name

    try:
        if sys.platform == "win32":
            attempts = (_try_mss, _try_imagegrab)
        else:
            attempts = (_try_gnome_screenshot, _try_grim, _try_mss)

        for attempt in attempts:
            if attempt(path):
                img = Image.open(path).convert("RGB")
                img.load()
                return img

        raise RuntimeError(
            "Screenshot is black or all methods failed.\n"
            "Linux fix: sudo apt install gnome-screenshot\n"
            "Windows fix: ensure mss or Pillow is installed."
        )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    """Convert a PIL Image to raw bytes."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()
