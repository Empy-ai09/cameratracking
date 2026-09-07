# RetroLens

RetroLens adalah modifikasi dari [syahdanfx/Retrolens](https://github.com/syahdanfx/Retrolens) untuk Linux desktop, termasuk KDE, GNOME, dan environment lain di Arch Linux.

Proyek ini memakai Python, OpenCV, dan MediaPipe untuk membuat portal filter real-time berbasis gerakan tangan.

---



## 🇬🇧 English

### Short description

This version was adapted to make the documentation and usage flow more comfortable on Linux desktop environments. The main features from the original project are preserved: portal filters, gesture-based filter switching, 2D/3D mode, and screenshots.

### System requirements

- OS: Arch Linux or an Arch-based distribution
- Desktop environment: KDE Plasma, GNOME, XFCE, Cinnamon, or others
- Python: 3.8–3.11
- Webcam: required
- Python packages: `opencv-python`, `mediapipe`, `numpy`

### Installation

1. Create and activate a virtual environment (recommended to prevent `externally-managed-environment` errors):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Run

```bash
python3 Retrolens.py
```

If `python3` is not available, use:

```bash
python Retrolens.py
```

### Controls

- Spread both hands → open the portal
- Pinch thumb + pinky → switch filter
- Fist both hands / press `C` → toggle 2D/3D mode
- `N` / `P` → next / previous filter
- `S` → save screenshot
- `Q` → quit

### License

This project uses the MIT License. See `LICENSE`.

### Credits

Based on the original project by Sy4hdan / syahdanfx.
-----
<br>

## 🇮🇩 Bahasa Indonesia

### Deskripsi singkat

Versi ini dibuat dengan menyesuaikan dokumentasi dan alur penggunaan agar lebih nyaman dijalankan di Linux desktop. Fitur utama dari proyek asli tetap dipertahankan: portal filter, pergantian filter dengan gesture, mode 2D/3D, dan screenshot.

### Spesifikasi sistem

- OS: Arch Linux atau distribusi berbasis Arch
- Desktop environment: KDE Plasma, GNOME, XFCE, Cinnamon, atau lainnya
- Python: 3.8–3.11
- Webcam: diperlukan
- Paket Python: `opencv-python`, `mediapipe`, `numpy`

### Instalasi

1. Buat dan aktifkan virtual environment (sangat disarankan, terutama pada Linux yang menggunakan PEP 668 seperti Arch Linux):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

### Cara menjalankan

```bash
python3 Retrolens.py
```

Jika `python3` tidak tersedia, gunakan:

```bash
python Retrolens.py
```

### Kontrol

- Bentangkan 2 tangan → buka portal
- Pinch ibu jari + kelingking → ganti filter
- Kepal 2 tangan / tekan `C` → toggle mode 2D/3D
- `N` / `P` → filter berikutnya / sebelumnya
- `S` → simpan screenshot
- `Q` → keluar

### Lisensi

Proyek ini menggunakan lisensi MIT. Lihat file `LICENSE`.

### Kredit

Berdasarkan proyek asli oleh Sy4hdan / syahdanfx.

---