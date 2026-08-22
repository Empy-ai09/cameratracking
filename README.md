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
├── TwoHandPanel     → Panel gestur dua tangan
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
├── ui_manager.py       # Antarmuka visual
├── requirements.txt    # Dependensi Python
├── run.sh              # Script jalankan cepat
└── hand_landmarker.task # Model ML MediaPipe
```

---

## 💡 Ide Selanjutnya

- [ ] Mode multiplayer lokal (2 webcam)
- [ ] Puzzle ukuran dinamis (4x4, 5x5)
- [ ] Rekaman video otomatis saat solusi tercapai
- [ ] Integrasi suara (SFX saat potongan cocok)

---

## 📄 Lisensi

Dibuat untuk eksplorasi interaksi manusia-komputer. Bebas digunakan, dimodifikasi, dan dikembangkan.

---

> **"Tanganmu bukan hanya alat — ini remote control masa depan."** 👋
