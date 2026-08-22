"""Entry point - jalankan `python main.py`.

Semua fitur (hand tracking, gesture blur, puzzle mode, HUD) ada di
MainApp pada app.py. File ini hanya wrapper agar `python main.py`
langsung menjalankan aplikasi terintegrasi.
"""
from app import MainApp


if __name__ == "__main__":
    MainApp().run()