buat#!/usr/bin/env bash
# run.sh - Menjalankan aplikasi camera tracking di Arch Linux Wayland
# Cara pakai: chmod +x run.sh && ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Camera Tracking Launcher ==="

# Deteksi desktop session
if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "Wayland terdeteksi. Menggunakan fallback XWayland untuk OpenCV GUI..."
    export QT_QPA_PLATFORM=xcb
    export SDL_VIDEODRIVER=x11
else
    echo "X11 terdeteksi. Menjalankan secara normal..."
fi

# Cek Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 tidak ditemukan. Install dengan: sudo pacman -S python"
    exit 1
fi

# Cek virtual environment
if [ -d "$SCRIPT_DIR/.venv" ]; then
    echo "Mengaktifkan virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Cek dependensi Python
if ! python3 -c "import cv2, mediapipe, numpy" 2>/dev/null; then
    echo "Dependensi Python belum lengkap. Menginstall dari requirements.txt..."
    if [ -d "$SCRIPT_DIR/.venv" ]; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt"
    fi
fi

# Cek model MediaPipe
if [ ! -f "$SCRIPT_DIR/hand_landmarker.task" ]; then
    echo "Peringatan: hand_landmarker.task tidak ditemukan di $SCRIPT_DIR"
    echo "Pastikan file model tersedia sebelum menjalankan aplikasi."
fi

echo "Menjalankan aplikasi..."
echo ""
python3 "$SCRIPT_DIR/main.py"
