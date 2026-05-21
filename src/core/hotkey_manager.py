"""
src/core/hotkey_manager.py
Global hotkey registry — works on Linux (evdev, Wayland + X11) and Windows (pynput).

Linux: reads /dev/input directly so physical keys are captured even on Wayland.
       Requires the user to be in the 'input' group (setup.sh handles this).
Windows: uses pynput.keyboard.Listener.
"""
from __future__ import annotations

import sys
import threading
import time
from typing import Callable, Dict


CHORD_WINDOW = 0.4   # seconds — keys pressed within this window count as a chord


def _parse_combo(combo_str: str) -> frozenset:
    parts = combo_str.lower().split("+")
    return frozenset(p.strip() for p in parts if p.strip())


# ── Linux-only helpers ────────────────────────────────────────────────────────

if sys.platform != "win32":
    from evdev import InputDevice, categorize, ecodes, list_devices

    # evdev keycode → our combo string character
    _KEY_MAP = {
        "KEY_COMMA":      ",",
        "KEY_DOT":        ".",
        "KEY_SLASH":      "/",
        "KEY_LEFTALT":    "alt",  "KEY_RIGHTALT":   "alt",
        "KEY_LEFTCTRL":   "ctrl", "KEY_RIGHTCTRL":  "ctrl",
        "KEY_LEFTSHIFT":  "shift","KEY_RIGHTSHIFT":  "shift",
        "KEY_LEFTMETA":   "win",  "KEY_RIGHTMETA":   "win",
        "KEY_SPACE":      "space",
        "KEY_ENTER":      "enter",
        "KEY_ESC":        "esc",
    }

    def _key_name(keycode) -> str:
        if isinstance(keycode, list):
            keycode = keycode[0]
        if keycode in _KEY_MAP:
            return _KEY_MAP[keycode]
        # KEY_K → 'k',  KEY_1 → '1'
        if keycode.startswith("KEY_") and len(keycode) == 5:
            return keycode[4].lower()
        return keycode.lower().replace("key_", "")

    def _find_keyboards() -> list:
        devices = []
        for path in list_devices():
            try:
                dev  = InputDevice(path)
                caps = dev.capabilities()
                keys = caps.get(ecodes.EV_KEY, [])
                if ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys:
                    devices.append(dev)
            except Exception:
                pass
        return devices


# ── Windows-only helpers ──────────────────────────────────────────────────────

def _pynput_key_name(key) -> str:
    """Convert a pynput Key or KeyCode to our combo string."""
    try:
        # KeyCode with a printable character
        if key.char is not None and key.char.isprintable():
            return key.char.lower()
    except AttributeError:
        pass
    # Special key — use .name
    try:
        name = key.name.lower()
    except AttributeError:
        return str(key).lower()

    # Normalize modifier aliases
    if name in ("alt_l", "alt_r", "alt_gr"):
        return "alt"
    if name in ("ctrl_l", "ctrl_r"):
        return "ctrl"
    if name in ("shift", "shift_l", "shift_r"):
        return "shift"
    if name in ("cmd", "cmd_l", "cmd_r"):
        return "win"
    return name


# ── HotkeyManager ─────────────────────────────────────────────────────────────

class HotkeyManager:
    CHORD_WINDOW = CHORD_WINDOW

    def __init__(self):
        self._registry: Dict[frozenset, Callable] = {}
        self._pressed:  set  = set()
        self._recent:   dict = {}   # key → timestamp of last key-down
        self._lock      = threading.Lock()
        self._running   = False
        self._stop_evt  = threading.Event()
        self._devices:  list = []
        self._listener  = None   # pynput Listener (Windows only)

    def register(self, combo: str, callback: Callable) -> None:
        with self._lock:
            self._registry[_parse_combo(combo)] = callback

    def unregister(self, combo: str) -> None:
        with self._lock:
            self._registry.pop(_parse_combo(combo), None)

    def clear(self) -> None:
        with self._lock:
            self._registry.clear()
            self._pressed.clear()

    # ── start / stop / join ───────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        self._stop_evt.clear()

        if sys.platform == "win32":
            from pynput.keyboard import Listener
            self._listener = Listener(
                on_press=self._on_press_win,
                on_release=self._on_release_win,
            )
            self._listener.start()
            print("HotkeyManager started (Windows).", flush=True)
        else:
            self._devices = _find_keyboards()
            if not self._devices:
                print("WARNING: No keyboard found in /dev/input. "
                      "Make sure you're in the 'input' group and run setup.sh.", flush=True)
            else:
                print(f"logs: HotkeyManager started ({len(self._devices)} keyboard(s)).", flush=True)
            threading.Thread(target=self._loop, daemon=True).start()

    def stop(self) -> None:
        self._running = False
        self._stop_evt.set()

        if sys.platform == "win32":
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception:
                    pass
        else:
            for d in self._devices:
                try:
                    d.close()
                except Exception:
                    pass

    def join(self) -> None:
        self._stop_evt.wait()

    # ── Linux event loop ──────────────────────────────────────────────────────

    def _loop(self) -> None:
        import select
        fds = {d.fd: d for d in self._devices}
        while self._running:
            try:
                readable, _, _ = select.select(list(fds.keys()), [], [], 0.1)
            except (ValueError, OSError):
                break
            for fd in readable:
                try:
                    for event in fds[fd].read():
                        if event.type == ecodes.EV_KEY:
                            self._handle(categorize(event))
                except OSError:
                    pass

    def _handle(self, key_event) -> None:
        name  = _key_name(key_event.keycode)
        state = key_event.keystate   # 0=up  1=down  2=hold
        now   = time.monotonic()

        if state == 1:               # key pressed
            with self._lock:
                self._pressed.add(name)
                self._recent[name] = now
                snap   = frozenset(self._pressed)
                recent = frozenset(
                    k for k, t in self._recent.items()
                    if now - t <= self.CHORD_WINDOW
                )
                match = None
                for combo, cb in self._registry.items():
                    if combo.issubset(snap) or combo.issubset(recent):
                        match = cb
                        break
                if match:
                    self._pressed.clear()
                    self._recent.clear()
            if match:
                threading.Thread(target=match, daemon=True).start()

        elif state == 0:             # key released
            with self._lock:
                self._pressed.discard(name)

    # ── Windows pynput callbacks ──────────────────────────────────────────────

    def _on_press_win(self, key) -> None:
        name = _pynput_key_name(key)
        now  = time.monotonic()

        with self._lock:
            self._pressed.add(name)
            self._recent[name] = now
            snap   = frozenset(self._pressed)
            recent = frozenset(
                k for k, t in self._recent.items()
                if now - t <= self.CHORD_WINDOW
            )
            match = None
            for combo, cb in self._registry.items():
                if combo.issubset(snap) or combo.issubset(recent):
                    match = cb
                    break
            if match:
                self._pressed.clear()
                self._recent.clear()
        if match:
            threading.Thread(target=match, daemon=True).start()

    def _on_release_win(self, key) -> None:
        name = _pynput_key_name(key)
        with self._lock:
            self._pressed.discard(name)
