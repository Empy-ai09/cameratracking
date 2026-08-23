"""HUD modern + landmark overlay + status mode."""
from __future__ import annotations

import cv2
import numpy as np

from hand_tracker import HAND_CONNECTIONS, HandData

FONT = cv2.FONT_HERSHEY_DUPLEX


def _pill(img, x1, y1, x2, y2, color, radius=12, alpha=0.55):
    overlay = img.copy()
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    for cx, cy in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                   (x1+radius, y2-radius), (x2-radius, y2-radius)]:
        cv2.circle(overlay, (cx, cy), radius, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


class UIManager:
    def draw_landmarks(self, frame, hand: HandData):
        for points in hand.hands_px:
            for s, e in HAND_CONNECTIONS:
                if s < len(points) and e < len(points):
                    cv2.line(frame, points[s], points[e], (255, 255, 255), 1, cv2.LINE_AA)
            for _id, (cx, cy) in enumerate(points):
                cv2.circle(frame, (cx, cy), 4, (255, 255, 255), -1, cv2.LINE_AA)

    def draw_camera_hud(self, frame, hand: HandData, blur_alpha: float, fps: float,
                        panel_state: str = "idle"):
        h, w = frame.shape[:2]
        label = "FOCUS MODE  ON" if hand.two_hand_peace else "FOCUS MODE  OFF"
        accent = (180, 255, 120) if hand.two_hand_peace else (180, 180, 180)
        (tw, th), _ = cv2.getTextSize(label, FONT, 0.62, 1)
        x1, y1 = 16, 16
        x2, y2 = x1 + tw + 64, y1 + th + 24
        _pill(frame, x1, y1, x2, y2, (30, 30, 30), radius=14, alpha=0.55)
        cx, cy = x1 + 26, (y1 + y2) // 2
        cv2.circle(frame, (cx, cy), 7, accent, -1)
        cv2.circle(frame, (cx, cy), 3, (30, 30, 30), -1)
        cv2.putText(frame, label, (cx + 18, y2 - 14), FONT, 0.62, accent, 1, cv2.LINE_AA)

        if blur_alpha > 0.05:
            sub = f"BLUR ACTIVE  {int(blur_alpha*100):3d}%"
            (sw, sh), _ = cv2.getTextSize(sub, FONT, 0.5, 1)
            sx1, sy1 = 16, y2 + 8
            sx2, sy2 = sx1 + sw + 56, sy1 + sh + 18
            _pill(frame, sx1, sy1, sx2, sy2, (40, 30, 50), radius=12, alpha=0.5)
            ix, iy = sx1 + 18, (sy1 + sy2) // 2
            pts = np.array([[ix, iy-6], [ix+6, iy], [ix, iy+6], [ix-6, iy]], np.int32)
            cv2.fillPoly(frame, [pts], (140, 220, 255))
            cv2.putText(frame, sub, (sx1 + 36, sy2 - 9), FONT, 0.5,
                        (220, 230, 240), 1, cv2.LINE_AA)
            y2 = sy2

        if panel_state in ("armed", "open"):
            ptxt = "PANEL  READY" if panel_state == "armed" else "PANEL  OPEN"
            pcol = (150, 210, 255) if panel_state == "armed" else (180, 255, 180)
            (pw_, ph_), _ = cv2.getTextSize(ptxt, FONT, 0.5, 1)
            px1, py1 = 16, y2 + 8
            px2, py2 = px1 + pw_ + 56, py1 + ph_ + 18
            _pill(frame, px1, py1, px2, py2, (28, 34, 40), radius=12, alpha=0.5)
            gx, gy = px1 + 20, (py1 + py2) // 2
            cv2.rectangle(frame, (gx - 7, gy - 5), (gx + 7, gy + 5), pcol, 1, cv2.LINE_AA)
            cv2.putText(frame, ptxt, (px1 + 36, py2 - 9), FONT, 0.5,
                        (225, 230, 235), 1, cv2.LINE_AA)

        self._draw_fps_lowlight(frame, fps, hand.lowlight)

    def draw_puzzle_hud(self, frame, state, elapsed, solved, fps, hand):
        h, w = frame.shape[:2]
        if state == "setup":
            label = "PUZZLE SETUP - use 2 hands, pinch to snap"
            color = (255, 220, 120)
        else:
            label = f"PUZZLE MODE - {int(elapsed)}s"
            color = (140, 220, 255)
        (tw, th), _ = cv2.getTextSize(label, FONT, 0.6, 1)
        x1, y1 = 16, 16
        x2, y2 = x1 + tw + 36, y1 + th + 24
        _pill(frame, x1, y1, x2, y2, (30, 30, 30), radius=14, alpha=0.6)
        cv2.putText(frame, label, (x1 + 18, y2 - 14), FONT, 0.6, color, 1, cv2.LINE_AA)

        hint = "Show metal gesture to reset  |  ESC -> camera  |  q -> quit"
        cv2.putText(frame, hint, (16, h - 18), FONT, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        if solved:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            msg = "SYSTEM STABILIZED"
            (mw, mh), _ = cv2.getTextSize(msg, FONT, 1.4, 2)
            cv2.putText(frame, msg, (w//2 - mw//2, h//2), FONT, 1.4,
                        (255, 255, 255), 2, cv2.LINE_AA)
            sub = "returning to camera..."
            (sw, sh), _ = cv2.getTextSize(sub, FONT, 0.7, 1)
            cv2.putText(frame, sub, (w//2 - sw//2, h//2 + 40), FONT, 0.7,
                        (200, 200, 200), 1, cv2.LINE_AA)

        self._draw_fps_lowlight(frame, fps, hand.lowlight)

    def _draw_fps_lowlight(self, frame, fps, lowlight):
        h, w = frame.shape[:2]
        info = f"{fps:5.1f} FPS"
        (iw, ih), _ = cv2.getTextSize(info, FONT, 0.5, 1)
        ix1 = w - iw - 28 - 16; iy1 = 16
        ix2 = w - 16;            iy2 = iy1 + ih + 18
        _pill(frame, ix1, iy1, ix2, iy2, (25, 25, 25), radius=12, alpha=0.5)
        cv2.putText(frame, info, (ix1 + 14, iy2 - 9), FONT, 0.5,
                    (220, 220, 220), 1, cv2.LINE_AA)
        if lowlight:
            ll = "LOW LIGHT BOOST"
            (lw, lh), _ = cv2.getTextSize(ll, FONT, 0.45, 1)
            lx2 = ix2; ly1 = iy2 + 8
            lx1 = lx2 - lw - 24; ly2 = ly1 + lh + 14
            _pill(frame, lx1, ly1, lx2, ly2, (40, 35, 20), radius=10, alpha=0.55)
            cv2.putText(frame, ll, (lx1 + 12, ly2 - 7), FONT, 0.45,
                        (120, 200, 255), 1, cv2.LINE_AA)
