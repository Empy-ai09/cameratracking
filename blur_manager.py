"""Background blur dengan mask tangan + transisi halus.

Dipakai HANYA di Camera Mode. Saat masuk Puzzle Mode, panggil suspend()
agar walaupun gesture peace masih terdeteksi, blur tetap OFF.
"""
from __future__ import annotations

import cv2
import numpy as np

from hand_tracker import HandData


class BlurManager:
    def __init__(self, blur_strength=21, mask_padding=40, transition_speed=0.28, downsample=2):
        if blur_strength % 2 == 0:
            blur_strength += 1
        self.blur_strength = blur_strength
        self.mask_padding = mask_padding
        self.transition_speed = transition_speed
        self.downsample = downsample
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
        target = 1.0 if (self.active and hand.two_hand_peace) else 0.0
        self.alpha += (target - self.alpha) * self.transition_speed
        self.alpha = max(0.0, min(1.0, self.alpha))

    def apply(self, frame, hand: HandData):
        if self.alpha <= 0.01:
            return frame
        ds = self.downsample
        small = cv2.resize(frame, (frame.shape[1] // ds, frame.shape[0] // ds),
                           interpolation=cv2.INTER_AREA)
        h_s, w_s = small.shape[:2]
        blurred_s = cv2.GaussianBlur(small, (self.blur_strength, self.blur_strength), 0)
        mask_s = np.zeros((h_s, w_s), dtype=np.uint8)
        scale_x = w_s / frame.shape[1]
        scale_y = h_s / frame.shape[0]
        for points in hand.hands_px:
            if len(points) >= 3:
                pts_s = np.array([(int(p[0] * scale_x), int(p[1] * scale_y)) for p in points],
                                 dtype=np.int32)
                hull = cv2.convexHull(pts_s)
                cv2.fillConvexPoly(mask_s, hull, 255)
                cv2.drawContours(mask_s, [hull], -1, 255,
                                 thickness=max(1, self.mask_padding // ds))
        mask_s = cv2.GaussianBlur(mask_s, (31, 31), 0)
        mask_f = (mask_s.astype(np.float32) / 255.0) * self.alpha
        mask_f = cv2.resize(mask_f, (frame.shape[1], frame.shape[0]),
                            interpolation=cv2.INTER_LINEAR)[..., None]
        blurred = cv2.resize(blurred_s, (frame.shape[1], frame.shape[0]),
                             interpolation=cv2.INTER_LINEAR)
        out = (frame.astype(np.float32) * mask_f +
               blurred.astype(np.float32) * (1.0 - mask_f)).astype(np.uint8)
        return out
