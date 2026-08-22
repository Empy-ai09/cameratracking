"""Background blur dengan mask tangan + transisi halus.

Dipakai HANYA di Camera Mode. Saat masuk Puzzle Mode, panggil suspend()
agar walaupun gesture peace masih terdeteksi, blur tetap OFF.
"""
from __future__ import annotations

import cv2
import numpy as np

from hand_tracker import HandData


class BlurManager:
    def __init__(self, blur_strength=35, mask_padding=70, transition_speed=0.18):
        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength
        self.mask_padding = mask_padding
        self.transition_speed = transition_speed
        self.enabled = True
        self._suspended = False
        self.alpha = 0.0

    def suspend(self):
        self._suspended = True

    def resume(self):
        self._suspended = False

    @property
    def active(self) -> bool:
        return self.enabled and not self._suspended

    def update(self, hand: HandData):
        target = 1.0 if (self.active and hand.peace) else 0.0
        self.alpha += (target - self.alpha) * self.transition_speed
        self.alpha = max(0.0, min(1.0, self.alpha))

    def apply(self, frame, hand: HandData):
        if self.alpha <= 0.01:
            return frame
        h, w = frame.shape[:2]
        blurred = cv2.GaussianBlur(frame, (self.blur_strength, self.blur_strength), 0)
        mask = np.zeros((h, w), dtype=np.uint8)
        for points in hand.hands_px:
            if len(points) >= 3:
                hull = cv2.convexHull(np.array(points, dtype=np.int32))
                cv2.fillConvexPoly(mask, hull, 255)
                cv2.drawContours(mask, [hull], -1, 255, thickness=self.mask_padding)
        mask = cv2.GaussianBlur(mask, (61, 61), 0)
        mask_f = (mask.astype(np.float32) / 255.0) * self.alpha
        mask_f = mask_f[..., None]
        out = (frame.astype(np.float32) * mask_f +
               blurred.astype(np.float32) * (1.0 - mask_f)).astype(np.uint8)
        return out
