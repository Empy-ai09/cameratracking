# ✋ Camera Tracking + Puzzle — Gesture-Controlled Magic

> **track tangan sesukamu**

Aplikasi interaktif berbasis Python yang menggabungkan **pelacakan tangan real-time** (MediaPipe), **blur dinamis berbasis gestur**, dan **mode puzzle gesekan dua tangan** — semua dalam satu layar.

---

## 🎥 Demo Konsep

| Mode | Gestur | Aksi |
|------|--------|------|
| 📷 **Camera** | ✌️ Peace Sign | Blur area tangan aktif |
| 🧩 **Puzzle** | 🤏 Pinch 2 tangan | Geser potongan puzzle |
| 🧩 **Puzzle** | 🤘 Metal / Rock | Reset puzzle |
| 🌐 **Universal** | 👋 Hand Detected | Landmark tangan ditampilkan |

---

## ✨ Fitur Unggulan

- **✌️ Blur Cerdas** — Tunjukkan tanda *peace* dan area tangan langsung diburamkan secara halus.
- **🧩 Puzzle Mode** — Mode permainan geser potongan dengan dua tangan, lengkap dengan timer dan deteksi solusi otomatis.
- **🤘 Reset Instan** — Gestur *metal* langsung mereset puzzle tanpa menyentuh keyboard.
- **🎨 UI Real-Time** — Landmark tangan, HUD mode, FPS, dan status blur selalu terlihat.
- **⌨️ Kontrol Hybrid** — Bisa pakai gestur tangan **atau** keyboard (`p`, `ESC`, `r`, `q`).

---

## 🚀 Cara Menjalankan

```bash
# 1. Siapkan lingkungan
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 2. Install dependensi
pip install -r requirements.txt

# 3. Jalankan
python main.py
```

> Pastikan webcam terhubung dan file `hand_landmarker.task` ada di direktori yang sama.

---

## 🎮 Kontrol Lengkap

| Tombol | Fungsi |
|-------|--------|
| `P` | Masuk / keluar Puzzle Mode |
| `ESC` | Kembali ke Camera Mode |
| `R` | Reset puzzle (di Puzzle Mode) |
| `Q` | Keluar aplikasi |
| ✌️ | Aktifkan blur (Camera Mode) |
| 🤘 | Reset puzzle (gestur) |
| 🤏 | Pinch 2 tangan untuk menggeser puzzle |

---

## 🧠 Arsitektur Singkat

```
MainApp
├── HandTracker      → Deteksi landmark tangan (MediaPipe)
├── BlurManager      → Blur dinamis berbasis gestur
├── PuzzleManager    → Logika puzzle 3x3 + deteksi solusi
├── TwoHandPanel     → Panel gestur dua tangan (membuat persegi / panel dari dua tangan)
├── HalftonePanel    → Panel halftone presisi ke jari (perspektif + dot-pattern)
└── UIManager        → Rendering HUD & landmark
```

---

## 📁 Struktur Proyek

```
.
├── app.py              # Orkestrator utama (state machine)
├── main.py             # Entry point
├── hand_tracker.py     # MediaPipe Hand Landmarker
├── blur_manager.py     # Efek blur adaptif
├── puzzle_manager.py   # Puzzle 3x3 + timer + solusi
├── two_hand_panel.py   # Manajemen dua tangan
├── halftone_panel.py  # Panel halftone perspektif dari 4 landmark tangan
├── ui_manager.py       # Antarmuka visual
├── requirements.txt    # Dependensi Python
├── run.sh              # Script jalankan cepat
└── hand_landmarker.task # Model ML MediaPipe
```

---


## 🖐️ Modul `two_hand_panel.py`

Modul ini bisa **membuat persegi / panel dari posisi dua tangan**. Mekanismenya:
- **State machine**: `IDLE` → (`tangan bersentuhan`) → `ARMED` → (`tangan direntangkan`) → `OPEN` (panel tampil).
- Panel berbentuk persegi dengan sudut membulat, diisi **hatch / garis diagonal hitam-putih**.
- Transisi halus dengan `fade` dan `smooth` agar tampilan tidak berkedip.
- Murni OpenCV + NumPy, tanpa X11.

---

## 🖼️ Modul `halftone_panel.py`

Modul baru untuk **panel halftone yang menempel presisi ke jari** menggunakan 4 titik landmark (`INDEX_FINGER_TIP` 8 & `THUMB_TIP` 4) dari dua tangan pertama:
- **4 titik sudut** diambil langsung dari `HandData.hands_px`, bukan bounding box.
- **Warp perspektif** (`getPerspectiveTransform` + `warpPerspective`) membuat panel miring sesuai sudut tangan asli.
- **Efek halftone**: grayscale → CLAHE/equalizeHist → grid dot (radius proporsional kegelapan) dengan background putih solid; area paling gelap mendapat tint biru gelap.
- **EMA smoothing** pada quad + state machine `IDLE → ARMED → OPEN` + fallback `last-good-hold` saat landmark hilang.
- Terintegrasi di `app.py` sebagai layer tambahan di Camera Mode.

---

## 📄 Lisensi

Dibuat untuk eksplorasi interaksi manusia-komputer. Bebas digunakan, dimodifikasi, dan dikembangkan.

---


