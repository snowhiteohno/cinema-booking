import os
import threading
import mss
from PIL import Image
from google import genai
from google.genai import types
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

SYSTEM_PROMPT = (
    "You are a helpful AI assistant embedded in a floating overlay. "
    "The user will send you screenshots of problems they are looking at. "
    "Analyze the screenshot carefully and respond with the most useful answer. "
    "- Coding problem → working solution with brief explanation. "
    "- Theory / concept → clear structured answer. "
    "- MCQ → correct option and why. "
    "- Math → solution with steps. "
    "- Anything else → most helpful concise answer. "
    "Format responses in clean Markdown. Use ## headings, **bold** for key terms, "
    "and ```language code blocks for code. Be concise but complete. "
    "For follow-up questions, remember the full context of the conversation."
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

VK_SLASH = KeyCode.from_vk(0xBF)

# ── Conversation memory ───────────────────────────────────────────────────────
# Stores the full multi-turn conversation for Gemini context.
# Each entry: {"role": "user" | "model", "parts": [...]}
conversation_history: list[dict] = []
history_lock = threading.Lock()


def clear_memory():
    """Wipe conversation history and the overlay display."""
    with history_lock:
        conversation_history.clear()
    overlay.clear_chat()
    print("🗑️   Memory & chat cleared.", flush=True)


# ── Screenshot ───────────────────────────────────────────────────────────────
def take_screenshot() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def image_to_part(img: Image.Image) -> types.Part:
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return types.Part(
        inline_data=types.Blob(mime_type="image/png", data=buf.getvalue())
    )


# ── Gemini — initial screenshot query ────────────────────────────────────────
def query_gemini_screenshot(images: list[Image.Image]) -> str:
    parts = [types.Part(text=SYSTEM_PROMPT)]
    for img in images:
        parts.append(image_to_part(img))

    user_turn = types.Content(role="user", parts=parts)

    with history_lock:
        conversation_history.clear()
        conversation_history.append({"role": "user", "parts": parts})

    print(f"logs: Sending {len(images)} screenshot(s) to Gemini...", flush=True)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[user_turn]
    )
    answer = response.text.strip()

    with history_lock:
        conversation_history.append({
            "role": "model",
            "parts": [types.Part(text=answer)]
        })

    print("logs: Response received.", flush=True)
    return answer


# ── Gemini — follow-up with memory ───────────────────────────────────────────
def query_gemini_followup(text: str) -> str:
    follow_up_part = types.Part(text=text)

    with history_lock:
        conversation_history.append({
            "role": "user",
            "parts": [follow_up_part]
        })
        # Build full contents list from history
        contents = [
            types.Content(role=turn["role"], parts=turn["parts"])
            for turn in conversation_history
        ]

    print(f"logs: Sending follow-up to Gemini (history: {len(contents)} turns)...", flush=True)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents
    )
    answer = response.text.strip()

    with history_lock:
        conversation_history.append({
            "role": "model",
            "parts": [types.Part(text=answer)]
        })

    print("logs: Follow-up response received.", flush=True)
    return answer


# ── Follow-up handler (called from overlay input) ─────────────────────────────
def handle_followup(text: str):
    if not conversation_history:
        # No prior context — treat it as a plain question
        with history_lock:
            conversation_history.append({
                "role": "user",
                "parts": [types.Part(text=SYSTEM_PROMPT + "\n\n" + text)]
            })

    overlay.add_user_message(text)
    overlay.set_thinking(True)

    try:
        answer = query_gemini_followup(text)
        overlay.add_ai_message(answer)
    except Exception as e:
        overlay.add_ai_message(f"**Error:** {e}")
        print(f"❌  Follow-up error: {e}", flush=True)


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
            overlay.set_thinking(True)
            overlay.show()
            answer = query_gemini_screenshot(images_to_send)
            overlay.add_ai_message(answer)
            print("─" * 60)
            print(answer)
            print("─" * 60, flush=True)
        except Exception as e:
            overlay.add_ai_message(f"**Error:** {e}")
            print(f"❌  Error: {e}", flush=True)
        finally:
            processing = False

    threading.Thread(target=run, daemon=True).start()


def clear_queue():
    with queue_lock:
        count = len(screenshot_queue)
        screenshot_queue.clear()
    print(f"🗑️   Queue cleared ({count} screenshot(s) removed).", flush=True)


# ── Test mode ────────────────────────────────────────────────────────────────
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

Using `(left + right) / 2` can cause **integer overflow** when both values are large.

- Works on any sorted array
- Returns `-1` if target not found
- Loop ends when `left > right`
"""


# ── Keyboard listener ─────────────────────────────────────────────────────────
def get_char(key) -> str | None:
    try:
        return key.char
    except AttributeError:
        return None


def on_press(key):
    pressed_keys.add(key)

    chars      = {get_char(k) for k in pressed_keys}
    lower      = {c.lower() for c in chars if c}
    ctrl_held  = keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys
    is_slash   = (key == VK_SLASH) or (get_char(key) == '/')

    # m + n → toggle overlay
    if 'm' in lower and 'n' in lower:
        pressed_keys.clear()
        overlay.toggle()
        print(f"👁️   Overlay {'hidden' if overlay.visible else 'shown'}", flush=True)
        return

    if KEY_ANCHOR in lower:
        if 't' in lower:                   # k + t → test
            pressed_keys.clear()
            print("🧪  Test mode", flush=True)
            overlay.show()
            overlay.add_ai_message(TEST_MD)
        elif 'c' in lower:                 # k + c → clear memory
            pressed_keys.clear()
            clear_memory()
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
    overlay.on_send  = handle_followup
    overlay.on_clear = clear_memory

    print("🚀  Screenshot-AI (Overlay) running.")
    print(f"    k + ,   →  Add screenshot to queue")
    print(f"    k + .   →  Send to Gemini → shows in overlay")
    print(f"    k + /   →  Clear the screenshot queue")
    print(f"    k + c   →  Clear memory + overlay chat")
    print(f"    k + t   →  Test overlay with dummy content")
    print(f"    m + n   →  Toggle overlay (hide / show)")
    print(f"    ↵ Enter →  Send follow-up in overlay input field\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()