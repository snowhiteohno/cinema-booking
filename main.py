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

# ── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  CRITICAL: Target GEMINI_API_KEY environment variable not found. Please set it in your .env file.")
    sys.exit(1)

GEMINI_MODEL   = "gemini-2.5-flash-lite"

PROMPT = (
    "You are a coding assistant. The screenshots contain a coding problem or question. "
    "Analyze all the provided screenshots together as one combined context. "
    "Respond with ONLY the code solution — no explanations, no markdown fences (no ```), "
    "no comments unless they are absolutely essential, and no preamble. "
    "Just raw, clean, working code that can be pasted directly into an editor."
)
# ────────────────────────────────────────────────────────────────────────────

client       = genai.Client(api_key=GEMINI_API_KEY)

screenshot_queue: list[Image.Image] = []   # holds queued screenshots
queue_lock   = threading.Lock()            # thread-safe queue access
processing   = False                       # debounce flag
pressed_keys = set()


# ── Screenshot helpers ───────────────────────────────────────────────────────
def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    return img


def strip_code_fences(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


# ── Gemini call ──────────────────────────────────────────────────────────────
def query_gemini(images: list[Image.Image]) -> str:
    # Build contents: prompt first, then every image
    contents = [PROMPT] + images

    print(f"logs: Sending {len(images)} screenshot(s) to Gemini...", flush=True)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
    )
    print("logs: Response received.", flush=True)
    return strip_code_fences(response.text.strip())


# ── Hotkey actions ───────────────────────────────────────────────────────────
def add_to_queue():
    """Ctrl + Space — capture and queue a screenshot."""
    img = take_screenshot()
    with queue_lock:
        screenshot_queue.append(img)
        count = len(screenshot_queue)
    print(f"📸  Screenshot #{count} added to queue. (Press Ctrl+Shift+Space to send all)", flush=True)


def send_queue():
    """Ctrl + Shift + Space — send all queued screenshots to Gemini."""
    global processing

    with queue_lock:
        if not screenshot_queue:
            print("⚠️   Queue is empty — nothing to send.", flush=True)
            return
        images_to_send = list(screenshot_queue)
        screenshot_queue.clear()

    if processing:
        print("⚠️   Already processing a request, please wait.", flush=True)
        return
    processing = True

    def run():
        global processing
        try:
            print(f"\n🤖  Sending {len(images_to_send)} screenshot(s) to Gemini...", flush=True)
            answer = query_gemini(images_to_send)

            pyperclip.copy(answer)
            print("✅  Code copied to clipboard!\n", flush=True)
            print("─" * 60)
            print(answer)
            print("─" * 60, flush=True)

        except Exception as e:
            print(f"❌  Error: {e}", flush=True)
        finally:
            processing = False

    threading.Thread(target=run, daemon=True).start()


def clear_queue():
    """Ctrl + Shift + X — discard all queued screenshots."""
    with queue_lock:
        count = len(screenshot_queue)
        screenshot_queue.clear()
    print(f"🗑️   Queue cleared ({count} screenshot(s) removed).", flush=True)


# ── Keyboard listener ────────────────────────────────────────────────────────
def on_press(key):
    pressed_keys.add(key)

    ctrl_held  = keyboard.Key.ctrl_l  in pressed_keys or keyboard.Key.ctrl_r  in pressed_keys
    shift_held = keyboard.Key.shift_l in pressed_keys or keyboard.Key.shift_r in pressed_keys
    space      = keyboard.Key.space   in pressed_keys

    try:
        x_held = keyboard.KeyCode.from_char('x') in pressed_keys or \
                 keyboard.KeyCode.from_char('X') in pressed_keys
    except Exception:
        x_held = False

    if ctrl_held and shift_held and x_held:
        pressed_keys.clear()
        clear_queue()

    elif ctrl_held and shift_held and space:
        pressed_keys.clear()
        send_queue()

    elif ctrl_held and not shift_held and space:
        pressed_keys.clear()
        add_to_queue()


def on_release(key):
    try:
        pressed_keys.remove(key)
    except KeyError:
        pass


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀  Screenshot-AI running in background.")
    print("    Ctrl + Space            →  Add screenshot to queue")
    print("    Ctrl + Shift + Space    →  Send all queued screenshots to Gemini")
    print("    Ctrl + Shift + X        →  Clear the queue\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()