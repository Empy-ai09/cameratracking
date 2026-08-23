# ✋ Camera Tracking + Puzzle

> *Tangan kamu jadi remote control.*

Gesture-controlled real-time camera tracking pakai MediaPipe — **blur adaptif**, **puzzle 3×3**, dan **panel halftone perspektif** dari 4 ujung jari. Satu webcam, satu HandTracker, semua mode hidup bareng.

---

## 🎬 Gestur & Mode

| Mode | Trigger | Aksi |
|------|---------|------|
| 📷 Camera | ✌️ + ✌️ dua tangan | Blur area tangan aktif |
| 📷 Camera | ☝️🤏 2 tangan sentuh → buka | Panel halftone muncul |
| 🧩 Puzzle | `P` | Masuk puzzle mode |
| 🧩 Puzzle | 🤏 pinch 2 tangan | Geser tile |
| 🧩 Puzzle | 🤘 metal | Reset puzzle |
| 🌐 Semua | tangan terdeteksi | overlay landmark + HUD |

---

## ⌨️ Kontrol

| Key | Fungsi |
|-----|--------|
| `P` | Camera ↔ Puzzle |
| `ESC` | Puzzle → Camera |
| `R` | Reset puzzle |
| `Q` | Quit |

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Butuh `hand_landmarker.task` di direktori yang sama. Akses webcam diizinkan.

---

## 🧠 Arsitektur

```
MainApp
├── HandTracker     MediaPipe HandLandmarker + lowlight + smoothing
├── BlurManager     Gaussian blur + hull mask + downsample
├── PuzzleManager   3×3 tiles, drag-drop, solver detection
├── HalftonePanel   4-titik warp + dot-halftone dari video
└── UIManager       HUD, landmark, FPS, mode badge
```

---

## ⚡ Performa

Optimasi untuk 20–30 FPS di CPU-only:
- Input downscale `640×480`, detector di `320px`
- Low-light preprocessing jalan tiap 6 frame
- Blur pipeline di downsample `2×`
- Halftone skip ketika tidak aktif

Korban: tepi blur/halftone lebih kasar, deteksi low-light kurang agresif, gesture lebih gampang jitter di tangan cepat.

---

## 📁 Struktur

```
app.py               state machine + main loop
main.py              entry point
hand_tracker.py      MediaPipe wrapper
blur_manager.py      adaptive blur
puzzle_manager.py    3×3 puzzle + solver
halftone_panel.py    perspective halftone panel
ui_manager.py        HUD + overlay
requirements.txt
hand_landmarker.task
```

Bebas dipakai dan dimodifikasi.