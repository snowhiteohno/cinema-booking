# Helfi AI Toolkit v2.0 🚀

A premium, modular AI-powered desktop toolkit for productivity, coding, and educational assistance. **Helfi** leverages Google’s Gemini AI to interpret your screen, transcribe meetings in real-time, and automate tedious tasks through human-like typing or subtle overlays.

---

## ✨ Key Features

- **Unified Launcher**: A sleek, dark-mode dashboard to manage all AI agents and settings.
- **Global Mode Switching**: Instantly switch between agents from anywhere using `Alt + 1-5`.
- **7 specialized Agents**: From MCQ solving to multi-file coding architectures.
- **Human-Like Simulation**: Typing engine with randomized delays and smart indentation clearing.
- **Stealth Overlays**: Transparent, borderless windows that deliver answers without interrupting your workflow (invisible to most recording software).
- **Audio Intelligence**: Real-time transcription of both Microphone and System Audio (Speakers) for meeting assistance.
- **Model Fallbacks**: Automatically switches from `Gemini Flash` → `Gemini Pro` if rate limits or errors occur.

---

## 🛠️ Getting Started

### 1. Installation
Ensure you have Python 3.9+ installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory with your API key:
```text
GEMINI_API_KEY=your_google_ai_studio_key
```
*(Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 3. Launching
Start the **Launcher GUI** to pick your agent:
```bash
python main.py
```
*Note: You can also run agents headlessly using `python main.py --agent mcq`.*

### 4. Build Executable
To create a standalone `Helfi.exe` for Windows:
```bash
python build.py
```

---

## 🤖 The Helfi Agents

| Agent | Purpose | Primary Hotkeys | Quick Switch |
| :--- | :--- | :--- | :--- |
| **Auto-Type** | Human-like typing for coding. Includes **Multi-File LLD mode**. | `k+,` (Add) / `k+.` (Send) | `Alt + 2` |
| **Full Control** | **Unified Assistant**: Screenshots + Text Chat + Real-time Audio Transcript. | `k+,` (Add) / `m+n` (Overlay) | `Alt + 5` |
| **MCQ AI** | Stealth overlay for multiple choice questions. | `k+,` (Add) / `k+.` (Send) | `Alt + 4` |
| **General AI** | Detects question type; types code or theory solutions. | `k+,` (Add) / `k+.` (Send) | `Alt + 3` |
| **Clipboard** | Fast code generation directly to your clipboard. | `k+,` (Add) / `k+.` (Send) | `Alt + 1` |

---

### Featured Workflows

#### 1. Full Control (The Unified Assistant)
The most advanced mode. It combines a floating markdown chat with real-time audio detection.
- **Manual Mode**: Capture screenshots (`k+,`) and get solutions in the chat box.
- **Auto Mode**: Click the 🔊 icon to enable the **Debounce Listener**. It automatically transcribes speakers (Interviewer) and your Mic, then sends concise answers to the overlay.

#### 2. Auto-Type & Multi-File
Designed for sites that block pasting.
- **Standard**: Types a single block of code character-by-character.
- **Multi-File Toggle**: Enable this in the Launcher to handle Low-Level Design (LLD) questions. Gemini will generate folder structures and multiple files; use the `Next File` hotkey (`k+n`) to cycle through them.

#### 3. Stealth MCQ
Uses a tiny, borderless, transparent overlay that is nearly invisible to screen sharing. Ideal for quick answer verification.

---

## 🏗️ Architecture

Helfi v2.0 follows a modular, plugin-based architecture for easy expansion:

```text
/src
 ├── agents/     # Independent AI features (plugins)
 ├── audio/      # Microphone & System Audio capture
 ├── core/       # Gemini Client, Hotkey Manager, Screenshot logic
 ├── ui/         # Modern Launcher and Overlay windows
 └── utils/      # Text cleaners and formatting logic
```

### For Developers: Adding an Agent
1. Create a new file in `src/agents/my_agent.py`.
2. Inherit from `BaseAgent`.
3. Register your hotkeys and implement the `_run()` method.
4. Add your agent key to the registry in `main.py`.

---

## ⚙️ Customization (`settings.json`)
Manage all preferences via the **Settings** panel in the UI:
- **Hotkeys**: Rebind any shortcut to avoid conflicts with your IDE.
- **Typing Engine**: Adjust Min/Max delays and startup wait time.
- **Appearance**: Customize overlay colors, transparency (Alpha), and font sizes.
- **Models**: Prioritize which Gemini versions to use.

---

## ⚠️ Disclaimer
Helfi is designed for **accessibility and educational purposes**. Using this toolkit to violate academic integrity policies or professional codes of conduct is strictly discouraged. The developers are not responsible for any misuse.

---

*Built with ❤️ for power users.*

