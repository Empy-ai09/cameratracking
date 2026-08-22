"""Gesture dua tangan -> panel hatching (garis diagonal hitam-putih).

State machine:
    IDLE  --(2 tangan saling menempel, debounce)--> ARMED
    ARMED --(tangan direntangkan, debounce)-------> OPEN   (panel tampil)
    OPEN  --(tangan didekatkan lagi)--------------> ARMED  (panel tertutup)
    * --(salah satu tangan hilang beberapa frame)-> IDLE

Tidak punya kamera/detector sendiri - konsumsi HandData dari HandTracker.
Murni OpenCV + NumPy (aman di Wayland, tanpa X11/xdotool/Xlib).
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import cv2
import numpy as np

from hand_tracker import HandData

IDLE = "idle"
ARMED = "armed"
OPEN = "open"


def _rounded_mask(h: int, w: int, radius: int) -> np.ndarray:
    """Mask putih dengan sudut membulat, ukuran h x w."""
    mask = np.zeros((h, w), dtype=np.uint8)
    r = max(0, min(radius, h // 2, w // 2))
    if r == 0:
        mask[:] = 255
        return mask
    cv2.rectangle(mask, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(mask, (0, r), (w, h - r), 255, -1)
    for cx, cy in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]:
        cv2.circle(mask, (cx, cy), r, 255, -1)
    return mask


def _hatch_tile(h: int, w: int, spacing: int = 6, thickness: int = 2) -> np.ndarray:
    """Panel bergaris diagonal hitam-putih rapat."""
    tile = np.zeros((h, w, 3), dtype=np.uint8)
    step = max(2, spacing)
    for offset in range(-h, w + h, step):
        cv2.line(tile, (offset, 0), (offset + h, h), (255, 255, 255),
                 max(1, thickness), cv2.LINE_AA)
    return tile


class TwoHandPanelManager:
    # ambang jarak (dinormalisasi terhadap skala telapak) - histeresis
    TOUCH_RATIO = 1.4     # < ini dianggap "bersentuhan"
    OPEN_RATIO = 3.2      # > ini dianggap "direntangkan"
    TOUCH_FRAMES = 6
    OPEN_FRAMES = 4
    LOST_FRAMES = 10

    def __init__(self, smooth: float = 0.35, fade_speed: float = 0.18,
                 hatch_spacing: int = 6, hatch_thickness: int = 2):
        self.state = IDLE
        self.alpha = 0.0
        self.smooth = smooth
        self.fade_speed = fade_speed
        self.hatch_spacing = hatch_spacing
        self.hatch_thickness = hatch_thickness
        self._suspended = False
        self._touch_count = 0
        self._open_count = 0
        self._lost_count = 0
        self._rect: Optional[Tuple[float, float, float, float]] = None  # x1,y1,x2,y2 (smoothed)

    # ---- kontrol mode (dipakai app.py saat masuk/keluar Puzzle Mode) ----
    def suspend(self):
        self._suspended = True

    def resume(self):
        self._suspended = False

    def reset(self):
        self.state = IDLE
        self._touch_count = self._open_count = self._lost_count = 0
        self._rect = None

    @property
    def active(self) -> bool:
        return not self._suspended

    @property
    def visible(self) -> bool:
        return self.alpha > 0.01

    # ---------------------------------------------------------------
    def _target_rect(self, c1, c2, scale, w, h):
        cx, cy = (c1[0] + c2[0]) / 2.0, (c1[1] + c2[1]) / 2.0
        span = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
        pw = max(120.0, span * 0.92)
        ph = max(90.0, pw * 0.62)
        x1 = max(0.0, cx - pw / 2.0)
        y1 = max(0.0, cy - ph / 2.0)
        x2 = min(float(w), x1 + pw)
        y2 = min(float(h), y1 + ph)
        return (x1, y1, x2, y2)

    def update(self, hand: HandData):
        if self._suspended:
            self.state = IDLE
            self._touch_count = self._open_count = 0
            self.alpha += (0.0 - self.alpha) * self.fade_speed
            return

        two_hands = len(hand.hands_center) >= 2 and len(hand.hands_scale) >= 2

        if not two_hands:
            self._lost_count += 1
            if self._lost_count > self.LOST_FRAMES:
                self.reset()
        else:
            self._lost_count = 0
            c1, c2 = hand.hands_center[0], hand.hands_center[1]
            scale = max(1.0, (hand.hands_scale[0] + hand.hands_scale[1]) / 2.0)
            dist = math.hypot(c2[0] - c1[0], c2[1] - c1[1]) / scale

            touching = dist < self.TOUCH_RATIO
            spread = dist > self.OPEN_RATIO

            self._touch_count = self._touch_count + 1 if touching else 0
            self._open_count = self._open_count + 1 if spread else 0

            if self.state == IDLE:
                if self._touch_count >= self.TOUCH_FRAMES:
                    self.state = ARMED
                    self._open_count = 0
            elif self.state == ARMED:
                if self._open_count >= self.OPEN_FRAMES:
                    self.state = OPEN
            elif self.state == OPEN:
                if self._touch_count >= self.TOUCH_FRAMES:
                    self.state = ARMED
                    self._open_count = 0

            if self.state == OPEN:
                target = self._target_rect(c1, c2, scale, hand.width, hand.height)
                if self._rect is None:
                    self._rect = target
                else:
                    s = self.smooth
                    self._rect = tuple(
                        cur + (tgt - cur) * s for cur, tgt in zip(self._rect, target)
                    )  # type: ignore[assignment]

        target_alpha = 1.0 if self.state == OPEN else 0.0
        self.alpha += (target_alpha - self.alpha) * self.fade_speed
        self.alpha = max(0.0, min(1.0, self.alpha))
        if self.alpha <= 0.01 and self.state != OPEN:
            self._rect = None

    def draw(self, frame):
        if self.alpha <= 0.01 or self._rect is None:
            return frame
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = [int(round(v)) for v in self._rect]
        x1 = max(0, min(x1, w - 2)); y1 = max(0, min(y1, h - 2))
        x2 = max(x1 + 2, min(x2, w)); y2 = max(y1 + 2, min(y2, h))
        ph, pw = y2 - y1, x2 - x1
        if ph < 4 or pw < 4:
            return frame

        hatch = _hatch_tile(ph, pw, self.hatch_spacing, self.hatch_thickness)
        radius = max(8, min(28, min(ph, pw) // 6))
        mask = _rounded_mask(ph, pw, radius)
        mask_f = (mask.astype(np.float32) / 255.0 * self.alpha)[..., None]

        roi = frame[y1:y2, x1:x2].astype(np.float32)
        frame[y1:y2, x1:x2] = (hatch.astype(np.float32) * mask_f +
                               roi * (1.0 - mask_f)).astype(np.uint8)

        border = np.zeros((ph, pw, 3), dtype=np.uint8)
        edges = cv2.Canny(mask, 50, 150)
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8))
        border[edges > 0] = (200, 200, 200)
        e_f = (edges.astype(np.float32) / 255.0 * self.alpha)[..., None]
        roi2 = frame[y1:y2, x1:x2].astype(np.float32)
        frame[y1:y2, x1:x2] = (border.astype(np.float32) * e_f +
                               roi2 * (1.0 - e_f)).astype(np.uint8)
        return frame