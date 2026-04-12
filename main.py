import os
import threading
import mss
from PIL import Image
from google import genai
from pynput import keyboard
from pynput.keyboard import KeyCode
import sys
from dotenv import load_dotenv
from overlay import OverlayWindow

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  CRITICAL: GEMINI_API_KEY not found. Please set it in your .env file.")
    sys.exit(1)

GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = (
    "Analyze this screenshot carefully and respond with the most useful answer possible. "
    "- If it contains a coding problem: provide the working code solution with brief explanation. "
    "- If it contains a theory or concept question: give a clear, structured answer. "
    "- If it contains an MCQ: state the correct option and explain why. "
    "- If it contains math: show the solution with steps. "
    "- For anything else: respond with the most helpful answer you can. "
    "Format your response in clean Markdown. Use ## headings to organize sections, "
    "**bold** for key terms, and ```language code blocks for any code. "
    "Be concise but complete."
)
# ────────────────────────────────────────────────────────────────────────────

client  = genai.Client(api_key=GEMINI_API_KEY)
overlay = OverlayWindow()

screenshot_queue: list[Image.Image] = []
queue_lock   = threading.Lock()
processing   = False
pressed_keys = set()

KEY_ANCHOR = 'k'
KEY_ADD    = ','
KEY_SEND   = '.'
KEY_CLEAR  = '/'



# ── Test mode ────────────────────────────────────────────────────────────────
# Press k + t to instantly show dummy content without calling Gemini
TEST_MD = """## Binary Search

**Concept:** Repeatedly halve the search space by comparing the target to the middle element.

**Time complexity:** `O(log n)` — far faster than linear search for sorted arrays.

### Solution

```java
public int search(int[] nums, int target) {
    int left = 0;
    int right = nums.length - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] == target) return mid;
        if (nums[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```

### Why `left + (right - left) / 2`?

Using `(left + right) / 2` can cause **integer overflow** when both values are large. The subtraction form avoids this safely.

- Works on any sorted array
- Returns `-1` if target not found
- Loop ends when `left > right`
"""


# ── Screenshot ───────────────────────────────────────────────────────────────
def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


# ── Gemini ───────────────────────────────────────────────────────────────────
def query_gemini(images: list[Image.Image]) -> str:
    contents = [PROMPT] + images
    print(f"logs: Sending {len(images)} screenshot(s) to Gemini...", flush=True)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=contents)
    print("logs: Response received.", flush=True)
    return response.text.strip()


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
            overlay.show(answer)
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
    lower_chars = {c.lower() for c in chars if c}

    # m + n → toggle overlay
    if 'm' in lower_chars and 'n' in lower_chars:
        pressed_keys.clear()
        overlay.toggle()
        print(f"👁️   Overlay {'hidden' if overlay.visible else 'shown'}", flush=True)
        return

    if KEY_ANCHOR in chars:
        if 't' in chars:                   # k + t → test mode
            pressed_keys.clear()
            print("🧪  Test mode — showing dummy content in overlay", flush=True)
            overlay.show(TEST_MD)
        elif KEY_ADD in chars:             # k + , → add screenshot
            pressed_keys.clear()
            add_to_queue()
        elif KEY_SEND in chars:            # k + . → send to Gemini
            pressed_keys.clear()
            send_queue()
        elif KEY_CLEAR in chars:           # k + / → clear queue
            pressed_keys.clear()
            clear_queue()


def on_release(key):
    try:
        pressed_keys.remove(key)
    except KeyError:
        pass


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    overlay.start()

    print("🚀  Screenshot-AI (Overlay) running.")
    print(f"    k + ,      →  Add screenshot to queue")
    print(f"    k + .      →  Send to Gemini → shows in overlay")
    print(f"    k + /      →  Clear the queue")
    print(f"    k + t      →  Test overlay with dummy content  ← use this for UI testing")
    print(f"    m + n      →  Toggle overlay (hide / show)\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()