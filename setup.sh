#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║     B-POINT Setup Script — Linux / macOS (setup.sh)            ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

PROJ_DIR="$HOME/BPOINT_PRO"

echo ""
echo "  B-POINT — Virtual AI Mouse"
echo "  Developer: Babar  |  License: MIT  |  Stack: 100% Open Source"
echo "  ══════════════════════════════════════════════════════════════"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────
echo "[1/4] Checking Python 3.10+..."
if ! python3 -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null; then
    echo "ERROR: Python 3.10+ required. Install via your package manager."
    exit 1
fi
echo "       OK ($(python3 --version))"

# ── Step 2: Create directory & venv ──────────────────────────────
echo "[2/4] Creating project directory at $PROJ_DIR..."
mkdir -p "$PROJ_DIR"
python3 -m venv "$PROJ_DIR/venv"
echo "       OK"

# ── Step 3: Upgrade pip ───────────────────────────────────────────
echo "[3/4] Upgrading pip..."
"$PROJ_DIR/venv/bin/pip" install --upgrade pip --quiet
echo "       OK"

# ── Step 4: Install dependencies ─────────────────────────────────
echo "[4/4] Installing open-source dependencies..."
"$PROJ_DIR/venv/bin/pip" install \
    mediapipe \
    opencv-python \
    pyautogui \
    numpy

# Copy main.py
cp "$(dirname "$0")/main.py" "$PROJ_DIR/main.py"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅  Setup complete!"
echo ""
echo "  To run B-POINT:"
echo "    source $PROJ_DIR/venv/bin/activate"
echo "    python $PROJ_DIR/main.py"
echo "════════════════════════════════════════════════════════════"
