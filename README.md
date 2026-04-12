# Screenshot-AI — All Versions

A background service that captures your screen, sends it to Gemini, and delivers the answer in different ways depending on the version.

---

## Hotkeys (same across all versions)

| Hotkey  | Action                                |
| ------- | ------------------------------------- |
| `k + ,` | Add current screenshot to queue       |
| `k + .` | Send all queued screenshots to Gemini |
| `k + /` | Clear the queue                       |

---

## Setup (same across all versions)

### 1. Install dependencies

```bash
pip install google-genai pynput mss Pillow pyperclip python-dotenv
```

### 2. Create a `.env` file

```
GEMINI_API_KEY=your-key-here
```

Get a free key at https://aistudio.google.com/app/apikey

### 3. Run whichever version you want

```bash
python main.py
```

---

---

## Version 1 — Clipboard

**What it does:** Sends the screenshot to Gemini and copies the response to your clipboard. You then manually paste it wherever you need.

**Best for:** Any situation where you can paste normally (`Ctrl+V`).

**`main.py`**

```python
import os
import threading
import pyperclip
import mss
from PIL import Image
from google import genai
from pynput import keyboard
import sys
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY not found.")
    sys.exit(1)

GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = (
    "Analyze this screenshot carefully and respond with the most useful answer possible. "
    "- If it contains a coding problem: respond with only the working code solution, no explanations. "
    "- If it contains a theory or concept question: respond with a clear, concise answer. "
    "- If it contains an MCQ: respond with just the correct option and a one-line reason. "
    "- If it contains math: respond with the solution and steps. "
    "- For anything else: respond with the most helpful, concise answer you can. "
    "No markdown formatting, no backticks, no unnecessary padding."
)

client       = genai.Client(api_key=GEMINI_API_KEY)
screenshot_queue: list[Image.Image] = []
queue_lock   = threading.Lock()
processing   = False
pressed_keys = set()

KEY_ANCHOR = 'k'
KEY_ADD    = ','
KEY_SEND   = '.'
KEY_CLEAR  = '/'

def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

def query_gemini(images: list[Image.Image]) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[PROMPT] + images
    )
    return response.text.strip()

def add_to_queue():
    img = take_screenshot()
    with queue_lock:
        screenshot_queue.append(img)
        count = len(screenshot_queue)
    print(f"📸  Screenshot #{count} added to queue.", flush=True)

def send_queue():
    global processing
    with queue_lock:
        if not screenshot_queue:
            print("⚠️  Queue is empty.", flush=True)
            return
        images_to_send = list(screenshot_queue)
        screenshot_queue.clear()
    if processing:
        return
    processing = True
    def run():
        global processing
        try:
            answer = query_gemini(images_to_send)
            pyperclip.copy(answer)
            print("✅  Copied to clipboard!", flush=True)
            print(answer, flush=True)
        except Exception as e:
            print(f"❌  {e}", flush=True)
        finally:
            processing = False
    threading.Thread(target=run, daemon=True).start()

def clear_queue():
    with queue_lock:
        screenshot_queue.clear()
    print("🗑️  Queue cleared.", flush=True)

def get_char(key):
    try:
        return key.char
    except AttributeError:
        return None

def on_press(key):
    pressed_keys.add(key)
    chars = {get_char(k) for k in pressed_keys}
    if KEY_ANCHOR in chars:
        if KEY_ADD in chars:
            pressed_keys.clear(); add_to_queue()
        elif KEY_SEND in chars:
            pressed_keys.clear(); send_queue()
        elif KEY_CLEAR in chars:
            pressed_keys.clear(); clear_queue()

def on_release(key):
    pressed_keys.discard(key)

if __name__ == "__main__":
    print("🚀  Screenshot-AI (Clipboard) running.")
    print("    k + ,  →  Add to queue")
    print("    k + .  →  Send to Gemini → copies to clipboard")
    print("    k + /  →  Clear queue\n")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
        l.join()
```

---

---

## Version 2 — Auto Type

**What it does:** After getting the response from Gemini, automatically types it into whatever field you have focused — character by character with random human-like delays.

**Best for:** Sites that block `Ctrl+V` paste.

**Extra config:**

```python
AUTO_TYPE      = True   # set False to fall back to clipboard
STARTUP_DELAY  = 2      # seconds before typing starts (time to click into the field)
TYPE_DELAY_MIN = 0.04   # min delay between keystrokes
TYPE_DELAY_MAX = 0.12   # max delay between keystrokes
```

**`main.py`**

```python
import os
import threading
import time
import random
import pyperclip
import mss
from PIL import Image
from google import genai
from pynput import keyboard
from pynput.keyboard import Controller, Key
import sys
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY not found.")
    sys.exit(1)

GEMINI_MODEL   = "gemini-2.5-flash"
AUTO_TYPE      = True
STARTUP_DELAY  = 2
TYPE_DELAY_MIN = 0.04
TYPE_DELAY_MAX = 0.12

PROMPT = (
    "Analyze this screenshot carefully and respond with the most useful answer possible. "
    "- If it contains a coding problem: respond with only the working code solution, no explanations. "
    "- If it contains a theory or concept question: respond with a clear, concise answer. "
    "- If it contains an MCQ: respond with just the correct option and a one-line reason. "
    "- If it contains math: respond with the solution and steps. "
    "- For anything else: respond with the most helpful, concise answer you can. "
    "No markdown formatting, no backticks, no unnecessary padding."
)

client       = genai.Client(api_key=GEMINI_API_KEY)
kb           = Controller()
screenshot_queue: list[Image.Image] = []
queue_lock   = threading.Lock()
processing   = False
pressed_keys = set()

KEY_ANCHOR = 'k'
KEY_ADD    = ','
KEY_SEND   = '.'
KEY_CLEAR  = '/'

def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

def query_gemini(images: list[Image.Image]) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[PROMPT] + images
    )
    return response.text.strip()

def human_delay():
    time.sleep(random.uniform(TYPE_DELAY_MIN, TYPE_DELAY_MAX))

def type_answer(answer: str):
    for char in answer:
        kb.type(char)
        human_delay()

def deliver_answer(answer: str):
    if AUTO_TYPE:
        print(f"⌨️  Typing in {STARTUP_DELAY}s — click into the field!", flush=True)
        time.sleep(STARTUP_DELAY)
        type_answer(answer)
        print("✅  Done typing!", flush=True)
    else:
        pyperclip.copy(answer)
        print("✅  Copied to clipboard!", flush=True)

def add_to_queue():
    img = take_screenshot()
    with queue_lock:
        screenshot_queue.append(img)
        count = len(screenshot_queue)
    print(f"📸  Screenshot #{count} added to queue.", flush=True)

def send_queue():
    global processing
    with queue_lock:
        if not screenshot_queue:
            print("⚠️  Queue is empty.", flush=True)
            return
        images_to_send = list(screenshot_queue)
        screenshot_queue.clear()
    if processing:
        return
    processing = True
    def run():
        global processing
        try:
            answer = query_gemini(images_to_send)
            print(answer, flush=True)
            deliver_answer(answer)
        except Exception as e:
            print(f"❌  {e}", flush=True)
        finally:
            processing = False
    threading.Thread(target=run, daemon=True).start()

def clear_queue():
    with queue_lock:
        screenshot_queue.clear()
    print("🗑️  Queue cleared.", flush=True)

def get_char(key):
    try:
        return key.char
    except AttributeError:
        return None

def on_press(key):
    pressed_keys.add(key)
    chars = {get_char(k) for k in pressed_keys}
    if KEY_ANCHOR in chars:
        if KEY_ADD in chars:
            pressed_keys.clear(); add_to_queue()
        elif KEY_SEND in chars:
            pressed_keys.clear(); send_queue()
        elif KEY_CLEAR in chars:
            pressed_keys.clear(); clear_queue()

def on_release(key):
    pressed_keys.discard(key)

if __name__ == "__main__":
    print("🚀  Screenshot-AI (Auto-Type) running.")
    print("    k + ,  →  Add to queue")
    print("    k + .  →  Send to Gemini → types answer")
    print("    k + /  →  Clear queue\n")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
        l.join()
```

---

---

## Version 3 — General Purpose

**What it does:** Same as Version 1 (clipboard) but with a smarter prompt that adapts to any type of question — coding, MCQ, theory, math, or anything else.

**Best for:** General use across different types of questions.

> This is identical to Version 1. The only difference is the prompt is more explicitly adaptive. Versions 1 and 3 have been merged — Version 1 already uses the general-purpose prompt.

---

---

## Version 4 — Overlay (Windows only)

**What it does:** Displays the AI response in a floating transparent overlay on your screen. The overlay is completely invisible to screenshots, screen sharing (Zoom, Meet, Teams), and OBS. Only visible on your physical monitor.

**Best for:** Situations where you are screen sharing or being monitored.

**Requires:** Windows 10 version 2004 (May 2020 update) or later.

**Extra dependency:**

```bash
# No extra pip install needed — uses built-in ctypes
```

**`overlay.py`** _(must be in the same folder as `main.py`)_

```python
import tkinter as tk
from tkinter import scrolledtext
import threading
import ctypes

WDA_EXCLUDEFROMCAPTURE = 0x00000011

class OverlayWindow:
    def __init__(self):
        self.root    = None
        self._ready  = threading.Event()
        self._drag_x = 0
        self._drag_y = 0

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        self._ready.wait()

    def _run(self):
        self.root = tk.Tk()
        self._build_window()
        self._ready.set()
        self.root.mainloop()

    def _build_window(self):
        self.root.title("ai-overlay")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#0d0d0d')
        self.root.withdraw()

        outer = tk.Frame(self.root, bg='#00ff88', padx=1, pady=1)
        outer.pack(fill='both', expand=True)

        inner = tk.Frame(outer, bg='#0d0d0d', padx=12, pady=10)
        inner.pack(fill='both', expand=True)

        header = tk.Frame(inner, bg='#0d0d0d')
        header.pack(fill='x', pady=(0, 6))

        title = tk.Label(header, text="⬤  AI Response",
            bg='#0d0d0d', fg='#00ff88', font=('Consolas', 10, 'bold'))
        title.pack(side='left')

        close_btn = tk.Label(header, text="  ✕  ",
            bg='#0d0d0d', fg='#666666', font=('Consolas', 10, 'bold'), cursor='hand2')
        close_btn.pack(side='right')
        close_btn.bind('<Button-1>', lambda e: self.hide())
        close_btn.bind('<Enter>',    lambda e: close_btn.config(fg='#ff4444'))
        close_btn.bind('<Leave>',    lambda e: close_btn.config(fg='#666666'))

        tk.Frame(inner, bg='#1e1e1e', height=1).pack(fill='x', pady=(0, 8))

        self.text_area = scrolledtext.ScrolledText(
            inner, bg='#0d0d0d', fg='#f0f0f0',
            font=('Consolas', 11), wrap=tk.WORD,
            relief='flat', bd=0, cursor='arrow',
            state='disabled', width=52, height=20
        )
        self.text_area.pack(fill='both', expand=True)
        self.text_area.vbar.configure(
            bg='#1e1e1e', troughcolor='#0d0d0d', activebackground='#00ff88'
        )

        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"560x420+{sw - 590}+24")

        for widget in (header, title):
            widget.bind('<Button-1>',  self._drag_start)
            widget.bind('<B1-Motion>', self._drag_move)

        self.root.bind('<Escape>', lambda e: self.hide())

        self.root.update()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            status = "✅ hidden from screen capture" if result else "⚠️ capture exclusion failed"
            print(f"logs: Overlay {status}", flush=True)
        except Exception as e:
            print(f"logs: Capture exclusion error: {e}", flush=True)

    def show(self, text: str):
        if not self.root:
            return
        def _update():
            self.text_area.configure(state='normal')
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert(tk.END, text)
            self.text_area.configure(state='disabled')
            self.text_area.see('1.0')
            self.root.deiconify()
            self.root.lift()
        self.root.after(0, _update)

    def hide(self):
        if self.root:
            self.root.after(0, self.root.withdraw)

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")
```

**`main.py`**

```python
import os
import threading
import mss
from PIL import Image
from google import genai
from pynput import keyboard
import sys
from dotenv import load_dotenv
from overlay import OverlayWindow

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY not found.")
    sys.exit(1)

GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = (
    "Analyze this screenshot carefully and respond with the most useful answer possible. "
    "- If it contains a coding problem: respond with only the working code solution, no explanations. "
    "- If it contains a theory or concept question: respond with a clear, concise answer. "
    "- If it contains an MCQ: respond with just the correct option and a one-line reason. "
    "- If it contains math: respond with the solution and steps. "
    "- For anything else: respond with the most helpful, concise answer you can. "
    "No markdown formatting, no backticks, no unnecessary padding."
)

client       = genai.Client(api_key=GEMINI_API_KEY)
overlay      = OverlayWindow()
screenshot_queue: list[Image.Image] = []
queue_lock   = threading.Lock()
processing   = False
pressed_keys = set()

KEY_ANCHOR = 'k'
KEY_ADD    = ','
KEY_SEND   = '.'
KEY_CLEAR  = '/'

def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

def query_gemini(images: list[Image.Image]) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[PROMPT] + images
    )
    return response.text.strip()

def add_to_queue():
    img = take_screenshot()
    with queue_lock:
        screenshot_queue.append(img)
        count = len(screenshot_queue)
    print(f"📸  Screenshot #{count} added to queue.", flush=True)

def send_queue():
    global processing
    with queue_lock:
        if not screenshot_queue:
            print("⚠️  Queue is empty.", flush=True)
            return
        images_to_send = list(screenshot_queue)
        screenshot_queue.clear()
    if processing:
        return
    processing = True
    def run():
        global processing
        try:
            answer = query_gemini(images_to_send)
            print(answer, flush=True)
            overlay.show(answer)
        except Exception as e:
            print(f"❌  {e}", flush=True)
        finally:
            processing = False
    threading.Thread(target=run, daemon=True).start()

def clear_queue():
    with queue_lock:
        screenshot_queue.clear()
    print("🗑️  Queue cleared.", flush=True)

def get_char(key):
    try:
        return key.char
    except AttributeError:
        return None

def on_press(key):
    pressed_keys.add(key)
    chars = {get_char(k) for k in pressed_keys}
    if KEY_ANCHOR in chars:
        if KEY_ADD in chars:
            pressed_keys.clear(); add_to_queue()
        elif KEY_SEND in chars:
            pressed_keys.clear(); send_queue()
        elif KEY_CLEAR in chars:
            pressed_keys.clear(); clear_queue()

def on_release(key):
    pressed_keys.discard(key)

if __name__ == "__main__":
    overlay.start()
    print("🚀  Screenshot-AI (Overlay) running.")
    print("    k + ,  →  Add to queue")
    print("    k + .  →  Send to Gemini → shows in overlay")
    print("    k + /  →  Clear queue")
    print("    Esc    →  Close overlay\n")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
        l.join()
```

---

## Quick Comparison

|                     | Clipboard | Auto-Type        | General Purpose | Overlay           |
| ------------------- | --------- | ---------------- | --------------- | ----------------- |
| Output method       | Clipboard | Simulated typing | Clipboard       | Floating window   |
| Paste blocked sites | ❌        | ✅               | ❌              | ✅ (read only)    |
| Screen share safe   | ❌        | ✅               | ❌              | ✅ (Windows only) |
| Scrollable output   | ❌        | ❌               | ❌              | ✅                |
| Extra files needed  | None      | None             | None            | `overlay.py`      |
| Windows required    | No        | No               | No              | Yes               |
