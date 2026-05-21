#!/usr/bin/env bash
set -e

if [ ! -d "venv" ]; then
  echo "Run 'bash setup.sh' first."
  exit 1
fi

PYTHON="$(pwd)/venv/bin/python3"
PROJ="$(pwd)"

# Check PortAudio before starting
"$PYTHON" -c "import sounddevice" 2>/dev/null || {
  echo "ERROR: PortAudio missing. Run: sudo apt-get install -y portaudio19-dev libportaudio2"
  exit 1
}

AGENT=${1:-""}

if [ -z "$AGENT" ]; then
  echo ""
  echo "Usage:  bash start.sh <agent>"
  echo ""
  echo "  bash start.sh mcq          MCQ solver (answer shown in corner)"
  echo "  bash start.sh autotype     Types code into the editor"
  echo "  bash start.sh combo        MCQ + AutoType together (m+m to switch)"
  echo "  bash start.sh general      General Q&A, types the answer"
  echo "  bash start.sh clipboard    Copies answer to clipboard"
  echo "  bash start.sh full_control Chat overlay + mic"
  echo ""
  echo "Hotkeys (default):"
  echo "  k+,   Screenshot"
  echo "  k+.   Send to Gemini"
  echo "  k+/   Clear queue"
  echo "  a+s   Pause / resume typing"
  echo "  k+x   Stop typing"
  echo "  m+n   Toggle overlay"
  echo ""
  echo "Press Ctrl+C to stop."
  echo ""
  exit 0
fi

echo ""
echo "Starting '$AGENT' agent. Press Ctrl+C to stop."
echo ""

# Hotkeys use evdev (/dev/input) which needs the 'input' group.
# If the current session already has the group, run directly.
# Otherwise use 'sg input' to activate it without a logout.
if groups | grep -q '\binput\b'; then
  "$PYTHON" main.py --agent "$AGENT"
else
  sg input -c "cd '$PROJ' && '$PYTHON' main.py --agent '$AGENT'"
fi
