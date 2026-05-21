#!/usr/bin/env bash
set -e

echo "=== Helfi Setup ==="

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install it first."
  exit 1
fi

echo "Installing system dependencies (requires sudo)..."
sudo apt-get install -y python3-tk portaudio19-dev libportaudio2 gnome-screenshot

# Add user to input group for /dev/input access (Wayland hotkey support)
if groups | grep -q '\binput\b'; then
  echo "input group: already active"
else
  echo "Adding $USER to 'input' group for hotkey support..."
  sudo usermod -aG input "$USER"
  echo ">>> input group added. No logout needed — start.sh handles it automatically."
fi

# Allow input group to write to /dev/uinput (needed for Wayland keystroke injection)
UINPUT_RULE="/etc/udev/rules.d/99-uinput.rules"
if [ ! -f "$UINPUT_RULE" ]; then
  echo "Setting up /dev/uinput permissions for Wayland typing..."
  echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee "$UINPUT_RULE" > /dev/null
  sudo udevadm control --reload-rules
  sudo udevadm trigger --name-match=uinput
  echo ">>> uinput permissions set."
else
  echo "uinput rule: already exists"
fi

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo ">>> Created .env — open it and paste your Gemini API key."
  echo ">>> Then run: bash start.sh mcq"
else
  echo ">>> .env already exists."
  echo ">>> Run: bash start.sh mcq"
fi

echo ""
echo "=== Setup complete ==="
