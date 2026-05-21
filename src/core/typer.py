"""
src/core/typer.py
Keystroke injection — works on Linux (evdev UInput) and Windows (pynput Controller).

Linux: kernel-level injection via /dev/uinput; works on Wayland-native apps,
       X11 apps, browsers — everything.
       Requires /dev/uinput to be writable by the current user.
       Run once: sudo bash -c 'echo KERNEL==\"uinput\",GROUP=\"input\",MODE=\"0660\" >
         /etc/udev/rules.d/99-uinput.rules && udevadm control --reload-rules &&
         udevadm trigger --name-match=uinput'
       Then start a new terminal (or re-login) so sg input picks up the permission.
"""
from __future__ import annotations

import sys
import time


if sys.platform == "win32":
    # ── Windows: pynput Controller ────────────────────────────────────────────

    class UInputTyper:
        """Types characters and presses special keys via pynput on Windows."""

        def __init__(self):
            from pynput.keyboard import Controller, Key
            self._kb  = Controller()
            self._Key = Key

        def type_char(self, ch: str, delay: float = 0.05) -> None:
            self._kb.type(ch)
            time.sleep(delay)

        _KEY_MAP = {
            'enter':     'enter',
            'home':      'home',
            'end':       'end',
            'delete':    'delete',
            'tab':       'tab',
            'backspace': 'backspace',
            'space':     'space',
            'esc':       'esc',
        }

        def press_key(self, key_name: str, shift: bool = False, delay: float = 0.02) -> None:
            from pynput.keyboard import Key
            attr = self._KEY_MAP.get(str(key_name), str(key_name))
            key  = getattr(Key, attr, None)
            if key is None:
                return
            if shift:
                self._kb.press(Key.shift)
            self._kb.press(key)
            self._kb.release(key)
            if shift:
                self._kb.release(Key.shift)
            time.sleep(delay)

        def close(self) -> None:
            pass

else:
    # ── Linux: evdev UInput ───────────────────────────────────────────────────

    from evdev import UInput, ecodes as e

    # US QWERTY: char → (keycode, need_shift)
    _CHAR_MAP: dict[str, tuple[int, bool]] = {}

    def _build_map() -> None:
        for ch in "abcdefghijklmnopqrstuvwxyz":
            _CHAR_MAP[ch] = (getattr(e, f"KEY_{ch.upper()}"), False)
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            _CHAR_MAP[ch] = (getattr(e, f"KEY_{ch}"), True)
        for digit, key in zip("1234567890", [e.KEY_1,e.KEY_2,e.KEY_3,e.KEY_4,e.KEY_5,
                                              e.KEY_6,e.KEY_7,e.KEY_8,e.KEY_9,e.KEY_0]):
            _CHAR_MAP[digit] = (key, False)
        for shifted, key in zip("!@#$%^&*()", [e.KEY_1,e.KEY_2,e.KEY_3,e.KEY_4,e.KEY_5,
                                                e.KEY_6,e.KEY_7,e.KEY_8,e.KEY_9,e.KEY_0]):
            _CHAR_MAP[shifted] = (key, True)
        _CHAR_MAP.update({
            ' ':  (e.KEY_SPACE,      False),
            '\t': (e.KEY_TAB,        False),
            '\n': (e.KEY_ENTER,      False),
            '-':  (e.KEY_MINUS,      False),
            '_':  (e.KEY_MINUS,      True),
            '=':  (e.KEY_EQUAL,      False),
            '+':  (e.KEY_EQUAL,      True),
            '[':  (e.KEY_LEFTBRACE,  False),
            '{':  (e.KEY_LEFTBRACE,  True),
            ']':  (e.KEY_RIGHTBRACE, False),
            '}':  (e.KEY_RIGHTBRACE, True),
            '\\': (e.KEY_BACKSLASH,  False),
            '|':  (e.KEY_BACKSLASH,  True),
            ';':  (e.KEY_SEMICOLON,  False),
            ':':  (e.KEY_SEMICOLON,  True),
            "'":  (e.KEY_APOSTROPHE, False),
            '"':  (e.KEY_APOSTROPHE, True),
            ',':  (e.KEY_COMMA,      False),
            '<':  (e.KEY_COMMA,      True),
            '.':  (e.KEY_DOT,        False),
            '>':  (e.KEY_DOT,        True),
            '/':  (e.KEY_SLASH,      False),
            '?':  (e.KEY_SLASH,      True),
            '`':  (e.KEY_GRAVE,      False),
            '~':  (e.KEY_GRAVE,      True),
        })

    _build_map()

    _STR_TO_EVDEV = {
        'enter':     28,
        'home':      102,
        'end':       107,
        'delete':    111,
        'tab':       15,
        'backspace': 14,
        'space':     57,
        'esc':       1,
    }

    class UInputTyper:
        """Injects keystrokes via /dev/uinput — works on Wayland and X11."""

        def __init__(self) -> None:
            self._ui = UInput()

        def type_char(self, ch: str, delay: float = 0.05) -> None:
            mapping = _CHAR_MAP.get(ch)
            if mapping is None:
                return
            keycode, shift = mapping
            if shift:
                self._ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1); self._ui.syn()
            self._ui.write(e.EV_KEY, keycode, 1); self._ui.syn()
            time.sleep(delay)
            self._ui.write(e.EV_KEY, keycode, 0); self._ui.syn()
            if shift:
                self._ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0); self._ui.syn()

        def press_key(self, key_name: str, shift: bool = False, delay: float = 0.02) -> None:
            keycode = _STR_TO_EVDEV.get(str(key_name))
            if keycode is None:
                return
            if shift:
                self._ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1); self._ui.syn()
            self._ui.write(e.EV_KEY, keycode, 1); self._ui.syn()
            time.sleep(delay)
            self._ui.write(e.EV_KEY, keycode, 0); self._ui.syn()
            if shift:
                self._ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0); self._ui.syn()

        def close(self) -> None:
            try:
                self._ui.close()
            except Exception:
                pass
