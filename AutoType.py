import os
import threading
import time
import random
import re
import pyperclip
import mss
from PIL import Image
from google import genai
from pynput import keyboard
from pynput.keyboard import Controller, Key
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  CRITICAL: GEMINI_API_KEY not found. Please set it in your .env file.")
    sys.exit(1)

GEMINI_MODEL   = "gemini-2.5-flash"
AUTO_TYPE      = True
STARTUP_DELAY  = 2
TYPE_DELAY_MIN = 0.10
TYPE_DELAY_MAX = 0.25

PROMPT = (
    "You are a coding assistant. The screenshots contain a coding problem or question. "
    "Analyze all provided screenshots together as one combined context. "
    "Output ONLY the raw executable code. "
    "ABSOLUTE RULES — violation is not allowed: "
    "1. Zero comments of any kind — no #, no //, no /* */, no docstrings. "
    "2. No markdown, no backticks, no code fences. "
    "3. No explanations, no preamble, no trailing text. "
    "4. Use exactly 4 spaces per indent level — no tab characters ever. "
    "If you add anything other than raw code, you have failed the task."
)
# ────────────────────────────────────────────────────────────────────────────

client = genai.Client(api_key=GEMINI_API_KEY)
kb     = Controller()

screenshot_queue: list[Image.Image] = []
queue_lock   = threading.Lock()
processing   = False
pressed_keys = set()

KEY_ANCHOR = 'k'
KEY_ADD    = ','
KEY_SEND   = '.'
KEY_CLEAR  = '/'


# ── Screenshot ───────────────────────────────────────────────────────────────
def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


# ── Post-processing ──────────────────────────────────────────────────────────
def strip_code_fences(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def strip_comments(code: str) -> str:
    clean_lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('//'):
            continue
        if stripped.startswith('*') or stripped.startswith('/*') or stripped == '*/':
            continue
        line = re.sub(r'\s*//(?![\'"])[^\n]*', '', line)
        line = re.sub(r'(?<![\'"\w])#[^\n]*', '', line)
        clean_lines.append(line.rstrip())
    return "\n".join(line for line in clean_lines if line.strip() != '' or line == '')


def normalize_indentation(code: str) -> str:
    """Convert tabs to 4 spaces and fix any over-indented lines."""
    lines = []
    for line in code.splitlines():
        line = line.replace('\t', '    ')
        # Count leading spaces and round to nearest multiple of 4
        stripped   = line.lstrip(' ')
        raw_spaces = len(line) - len(stripped)
        indent_level = round(raw_spaces / 4)
        lines.append('    ' * indent_level + stripped)
    return "\n".join(lines)


def clean_response(raw: str) -> str:
    code = strip_code_fences(raw.strip())
    code = strip_comments(code)
    code = normalize_indentation(code)
    return code.strip()


# ── Gemini ───────────────────────────────────────────────────────────────────
def query_gemini(images: list[Image.Image]) -> str:
    contents = [PROMPT] + images
    print(f"logs: Sending {len(images)} screenshot(s) to Gemini...", flush=True)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=contents)
    print("logs: Response received.", flush=True)
    return clean_response(response.text)


# ── Typing ───────────────────────────────────────────────────────────────────
def human_delay():
    time.sleep(random.uniform(TYPE_DELAY_MIN, TYPE_DELAY_MAX))


def clear_auto_indent():
    """
    After pressing Enter the editor auto-indents the new line.
    This wipes whatever it inserted so we can type our own clean indentation.
    Home  → go to start of line
    Shift+End → select to end of line
    Delete → remove the selection
    """
    kb.press(Key.home);  kb.release(Key.home)
    time.sleep(0.03)
    kb.press(Key.shift)
    kb.press(Key.end);   kb.release(Key.end)
    kb.release(Key.shift)
    time.sleep(0.03)
    kb.press(Key.delete); kb.release(Key.delete)
    time.sleep(0.03)


def type_answer(answer: str):
    lines = answer.splitlines()

    for i, line in enumerate(lines):
        # Type every character on this line (including leading spaces)
        for char in line:
            kb.type(char)
            human_delay()

        if i < len(lines) - 1:
            # Press Enter to go to the next line
            kb.press(Key.enter)
            kb.release(Key.enter)
            time.sleep(0.05)

            # Wipe the editor's auto-indent so our spaces don't stack
            clear_auto_indent()


def deliver_answer(answer: str):
    if AUTO_TYPE:
        print(f"⌨️   Typing starts in {STARTUP_DELAY}s — click into the answer field now!", flush=True)
        time.sleep(STARTUP_DELAY)
        type_answer(answer)
        print("✅  Done typing!\n", flush=True)
    else:
        pyperclip.copy(answer)
        print("✅  Code copied to clipboard!\n", flush=True)


# ── Hotkey actions ───────────────────────────────────────────────────────────
def add_to_queue():
    img = take_screenshot()
    with queue_lock:
        screenshot_queue.append(img)
        count = len(screenshot_queue)
    print(f"📸  Screenshot #{count} added to queue.  (k+. to send | k+/ to clear)", flush=True)


def send_queue():
    global processing

    with queue_lock:
        if not screenshot_queue:
            print("⚠️   Queue is empty — nothing to send.", flush=True)
            return
        images_to_send = list(screenshot_queue)
        screenshot_queue.clear()

    if processing:
        print("⚠️   Already processing, please wait.", flush=True)
        return
    processing = True

    def run():
        global processing
        try:
            print(f"\n🤖  Sending {len(images_to_send)} screenshot(s) to Gemini...", flush=True)
            answer = query_gemini(images_to_send)
            print("─" * 60)
            print(answer)
            print("─" * 60, flush=True)
            deliver_answer(answer)
        except Exception as e:
            print(f"❌  Error: {e}", flush=True)
        finally:
            processing = False

    threading.Thread(target=run, daemon=True).start()


def clear_queue():
    with queue_lock:
        count = len(screenshot_queue)
        screenshot_queue.clear()
    print(f"🗑️   Queue cleared ({count} screenshot(s) removed).", flush=True)


# ── Keyboard listener ────────────────────────────────────────────────────────
def get_char(key) -> str | None:
    try:
        return key.char
    except AttributeError:
        return None


def on_press(key):
    pressed_keys.add(key)
    chars = {get_char(k) for k in pressed_keys}

    if KEY_ANCHOR in chars:
        if KEY_ADD in chars:
            pressed_keys.clear()
            add_to_queue()
        elif KEY_SEND in chars:
            pressed_keys.clear()
            send_queue()
        elif KEY_CLEAR in chars:
            pressed_keys.clear()
            clear_queue()


def on_release(key):
    try:
        pressed_keys.remove(key)
    except KeyError:
        pass


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = "AUTO-TYPE" if AUTO_TYPE else "Clipboard"
    print("🚀  Screenshot-AI running in background.")
    print(f"    Mode   : {mode}")
    print(f"    k + ,  →  Add screenshot to queue")
    print(f"    k + .  →  Send all screenshots to Gemini")
    print(f"    k + /  →  Clear the queue\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()