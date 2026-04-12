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

### 2. Create a `.env` file in the project folder

```
GEMINI_API_KEY=your-key-here
```

Get a free key at https://aistudio.google.com/app/apikey

### 3. Run whichever version you want

```bash
python main.py
```

---

## Version 1 — Clipboard

**File:** `v1_clipboard/main.py`

Takes the screenshot, sends it to Gemini, and copies the response directly to your clipboard. You then paste it manually wherever you need.

- No extra setup needed
- Works on Windows, macOS, Linux
- Best for: any situation where `Ctrl+V` is allowed

---

## Version 2 — Auto-Type

**File:** `v2_autotype/main.py`

After getting the response from Gemini, automatically types it into whatever field you have focused — character by character with random human-like delays so it looks like natural typing.

- Bypasses sites that block `Ctrl+V` paste
- 2 second window after Gemini responds to click into the target field
- Works on Windows, macOS, Linux
- Best for: paste-blocked coding platforms (HackerRank, etc.)

**Key settings at top of file:**
| Setting | Default | What it does |
|---------|---------|--------------|
| `STARTUP_DELAY` | `2` | Seconds before typing starts |
| `TYPE_DELAY_MIN` | `0.04` | Fastest keystroke gap (seconds) |
| `TYPE_DELAY_MAX` | `0.12` | Slowest keystroke gap (seconds) |

---

## Version 3 — General Purpose

**File:** `v3_general/main.py`

Same clipboard output as Version 1 but with a smarter prompt that adapts to any type of question on screen.

| Question type    | What Gemini returns              |
| ---------------- | -------------------------------- |
| Coding problem   | Working code only                |
| MCQ              | Correct option + one-line reason |
| Theory / concept | Clear concise answer             |
| Math             | Solution with steps              |
| Anything else    | Most helpful concise answer      |

- No extra setup needed
- Works on Windows, macOS, Linux
- Best for: general daily use across different question types

---

## Version 4 — Overlay

**Files:** `v4_overlay/main.py` + `v4_overlay/overlay.py`

Displays the AI response in a floating transparent window on your screen that is completely invisible to screenshots and screen sharing tools. Only visible on your physical monitor.

- Scrollable — handles long responses fine
- Draggable — click the header to reposition
- Press `Esc` or click `✕` to close
- Auto-hides after 60 seconds
- **Windows 10 v2004 (May 2020) or later required**
- Best for: when you are screen sharing or being proctored

**How the invisibility works:**
Uses the native Windows API `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` which tells the GPU compositor to exclude the window from all capture pipelines. Invisible to PrintScreen, Snipping Tool, Zoom, Google Meet, Microsoft Teams, and OBS.

---

## Quick Comparison

|                              | v1 Clipboard | v2 Auto-Type     | v3 General | v4 Overlay      |
| ---------------------------- | ------------ | ---------------- | ---------- | --------------- |
| Output method                | Clipboard    | Simulated typing | Clipboard  | Floating window |
| Works on paste-blocked sites | ❌           | ✅               | ❌         | ✅ (read only)  |
| Invisible to screen share    | ❌           | ✅               | ❌         | ✅              |
| Scrollable output            | ❌           | ❌               | ❌         | ✅              |
| Adaptive to question type    | ✅           | ✅               | ✅         | ✅              |
| Extra files needed           | None         | None             | None       | `overlay.py`    |
| OS support                   | Any          | Any              | Any        | Windows only    |
