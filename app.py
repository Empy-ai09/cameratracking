"""MainApp - Hand Tracking + Blur + Panel Mode.

Kontrol:
- 2 peace signs -> blur ON
- Kedua jempol dekat -> panel ARMED
- Renggangkan jempol -> panel OPEN
- 'q' : quit
"""
from __future__ import annotations

import time
import cv2

from hand_tracker import HandTracker
from blur_manager import BlurManager
from ui_manager import UIManager
from halftone_panel import HalftonePanelManager


class MainApp:
    def __init__(self, cam_index=0, width=640, height=480):
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            raise RuntimeError("Kamera tidak bisa dibuka")

        self.tracker = HandTracker()
        self.blur = BlurManager()
        self.halftone = HalftonePanelManager()
        self.ui = UIManager()

        self.fps_ema = 0.0
        self._t_prev = time.time()

    def run(self):
        window_name = "Integrated Hand Tracking + Puzzle"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 960, 720)

        print("=== Integrated Hand Tracking + Puzzle ===")
        print("Camera Mode : 2 peace signs -> blur ON")
        print("Panel : Kedua jempol dekat -> ARMED | Renggangkan -> OPEN")
        print("'q' to quit\n")

        while True:
            ok, frame = self.cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            self._t_prev = time.time()

            hand = self.tracker.process(frame)
            self.blur.update(hand)
            self.halftone.update(hand)

            out = frame
            out = self.blur.apply(out, hand)
            out = self.halftone.draw(out)
            self.ui.draw_landmarks(out, hand)
            self.ui.draw_camera_hud(out, hand, self.blur.alpha, self._fps(),
                                    panel_state=self.halftone.state)

            cv2.imshow(window_name, out)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.cleanup()

    def _fps(self) -> float:
        now = time.time()
        dt = now - self._t_prev
        self._t_prev = now
        inst = 1.0 / dt if dt > 0 else 0.0
        self.fps_ema = inst if self.fps_ema == 0 else (0.9 * self.fps_ema + 0.1 * inst)
        return self.fps_ema

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.tracker.close()
        print("=== Program selesai ===")


if __name__ == "__main__":
    MainApp().run()
