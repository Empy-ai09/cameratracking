# ✋ Camera Tracking

> *Tangan kamu jadi remote control.*

Gesture-controlled real-time camera tracking pakai MediaPipe — **blur adaptif** dan **panel halftone perspektif** dari 4 ujung jari. Satu webcam, satu HandTracker, satu mode: Camera.

---

## 🎬 Gestur

| Mode | Trigger | Aksi |
|------|---------|------|
| 📷 Camera | ✌️ + ✌️ dua tangan | Blur area tangan aktif |
| 📷 Camera | 🤏🤏 kedua jempol sangat dekat | Panel halftone ARMED |
| 📷 Camera | kedua jempol direnggangkan | Panel halftone OPEN (langsung aktif) |
| 🌐 Semua | tangan terdeteksi | overlay landmark + HUD |

---

## ⌨️ Kontrol

| Key | Fungsi |
|-----|--------|
| `Q` | Quit |

> Jendela aplikasi bisa di-resize bebas.

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
├── HalftonePanel   4-titik warp + dot-halftone dari video, trigger jempol
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
app.py               main loop + state
main.py              entry point
hand_tracker.py      MediaPipe wrapper
blur_manager.py      adaptive blur
halftone_panel.py    perspective halftone panel (trigger jempol)
ui_manager.py        HUD + overlay
requirements.txt
hand_landmarker.task
```

Bebas dipakai dan dimodifikasi.
