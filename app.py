"""MainApp - orkestrasi Camera Mode dan Puzzle Mode.

State machine:
    CAMERA  --[key 'p']-->  PUZZLE   (blur suspended)
    PUZZLE  --[solved | ESC]--> CAMERA  (blur resumed)

Aturan kunci:
- 1 webcam, 1 HandTracker - dipakai bersama.
- Saat mode == PUZZLE, BlurManager.suspend() dipanggil. Walaupun gesture
  peace masih terdeteksi, blur tetap OFF (alpha decay halus ke 0).
- Keluar Puzzle -> resume(); peace sign kembali bisa mengaktifkan blur.

Kontrol:
- 'p'   : Camera -> Puzzle setup
- ESC   : Puzzle -> Camera
- 'r'   : reset puzzle (di Puzzle Mode)
- metal : reset puzzle (gesture)
- 'q'   : quit
"""
from __future__ import annotations

import time
import cv2

from hand_tracker import HandTracker
from blur_manager import BlurManager
from puzzle_manager import PuzzleManager
from ui_manager import UIManager
from halftone_panel import HalftonePanelManager


CAMERA = "camera"
PUZZLE = "puzzle"


class MainApp:
    def __init__(self, cam_index=0, width=1280, height=720):
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError("Kamera tidak bisa dibuka")

        self.tracker = HandTracker()
        self.blur = BlurManager()
        self.puzzle = PuzzleManager(grid_size=3)
        self.halftone = HalftonePanelManager()
        self.ui = UIManager()

        self.mode = CAMERA
        self.fps_ema = 0.0
        self._t_prev = time.time()
        self._enter_cooldown = 0

    def _to_puzzle(self):
        if self.mode == PUZZLE:
            return
        self.mode = PUZZLE
        self.blur.suspend()
        self.halftone.suspend()
        self.puzzle.start_setup()

    def _to_camera(self):
        if self.mode == CAMERA:
            return
        self.mode = CAMERA
        self.puzzle.exit()
        self.blur.resume()
        self.halftone.resume()

    def run(self):
        print("=== Integrated Hand Tracking + Puzzle ===")
        print("Camera Mode : peace sign -> blur ON  |  'p' -> Puzzle Mode")
        print("Puzzle Mode : 2 hands + pinch to snap | metal -> reset | ESC -> Camera")
        print("'q' to quit\n")

        while True:
            ok, frame = self.cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)

            hand = self.tracker.process(frame)
            # update blur alpha tiap frame (decay otomatis saat suspended)
            self.blur.update(hand)
            self.halftone.update(hand)

            out = frame

            if self.mode == CAMERA:
                out = self.blur.apply(out, hand)
                out = self.halftone.draw(out)
                self.ui.draw_landmarks(out, hand)
                self.ui.draw_camera_hud(out, hand, self.blur.alpha, self._fps(),
                                        panel_state=self.halftone.state)
                if self._enter_cooldown > 0:
                    self._enter_cooldown -= 1
            else:
                solved_exit = self.puzzle.update(out, hand)
                self.ui.draw_landmarks(out, hand)
                self.ui.draw_puzzle_hud(
                    out, self.puzzle.state, self.puzzle.elapsed,
                    self.puzzle.is_solved, self._fps(), hand,
                )
                if solved_exit:
                    self._to_camera()

            cv2.imshow("Integrated Hand Tracking + Puzzle", out)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p') and self.mode == CAMERA and self._enter_cooldown == 0:
                self._to_puzzle()
            elif key == 27 and self.mode == PUZZLE:
                self._to_camera()
                self._enter_cooldown = 30
            elif key == ord('r') and self.mode == PUZZLE:
                self.puzzle.start_setup()

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
