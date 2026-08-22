"""Hand tracking module.

Membungkus MediaPipe HandLandmarker (VIDEO mode) + low-light preprocessing
+ EMA smoothing + temporal hold + gesture detection (peace, metal).
Satu instance saja - dipakai bersama oleh Camera Mode dan Puzzle Mode.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

TIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIPS = {"thumb": 2, "index": 6, "middle": 10, "ring": 14, "pinky": 18}
MCPS = {"thumb": 1, "index": 5, "middle": 9,  "ring": 13, "pinky": 17}


class _P:
    __slots__ = ("x", "y")
    def __init__(self, x: float, y: float):
        self.x = x; self.y = y


@dataclass
class HandData:
    hands_norm: List[List[Tuple[float, float]]] = field(default_factory=list)
    hands_px:   List[List[Tuple[int, int]]]     = field(default_factory=list)
    hands_center: List[Tuple[int, int]]         = field(default_factory=list)
    hands_scale:  List[float]                   = field(default_factory=list)
    peace:      bool = False
    metal:      bool = False
    lowlight:   bool = False
    mean_lum:   float = 0.0
    width:      int = 0
    height:     int = 0


def _angle_deg(a, b, c) -> float:
    ba = np.array([a.x - b.x, a.y - b.y])
    bc = np.array([c.x - b.x, c.y - b.y])
    nba = np.linalg.norm(ba); nbc = np.linalg.norm(bc)
    if nba < 1e-6 or nbc < 1e-6:
        return 180.0
    cosang = np.clip(np.dot(ba, bc) / (nba * nbc), -1.0, 1.0)
    return math.degrees(math.acos(cosang))


def _finger_extended(lm, finger: str) -> bool:
    tip = lm[TIPS[finger]]; pip = lm[PIPS[finger]]; mcp = lm[MCPS[finger]]
    wrist = lm[0]
    ang = _angle_deg(mcp, pip, tip)
    dist_tip = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
    dist_pip = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
    return ang > 150 and dist_tip > dist_pip * 1.05


def _folded(lm, finger: str) -> bool:
    tip = lm[TIPS[finger]]; pip = lm[PIPS[finger]]; mcp = lm[MCPS[finger]]
    return _angle_deg(mcp, pip, tip) < 130


def is_peace_sign(lm) -> bool:
    idx_open  = _finger_extended(lm, "index")
    mid_open  = _finger_extended(lm, "middle")
    ring_open = _finger_extended(lm, "ring")
    pky_open  = _finger_extended(lm, "pinky")
    ring_closed = (not ring_open) and _folded(lm, "ring")
    pky_closed  = (not pky_open)  and _folded(lm, "pinky")
    return idx_open and mid_open and ring_closed and pky_closed


def is_metal_gesture(lm) -> bool:
    idx_open = _finger_extended(lm, "index")
    pky_open = _finger_extended(lm, "pinky")
    mid_closed = (not _finger_extended(lm, "middle")) and _folded(lm, "middle")
    rng_closed = (not _finger_extended(lm, "ring"))   and _folded(lm, "ring")
    return idx_open and pky_open and mid_closed and rng_closed


class HandTracker:
    def __init__(
        self,
        model_path: str = "hand_landmarker.task",
        num_hands: int = 2,
        min_det_conf: float = 0.35,
        min_trk_conf: float = 0.35,
        min_pres_conf: float = 0.35,
        smooth_alpha: float = 0.55,
        lost_hold_frames: int = 8,
        lowlight_thr: float = 95.0,
        clahe_clip: float = 2.5,
        clahe_tile: Tuple[int, int] = (8, 8),
    ):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_det_conf,
            min_hand_presence_confidence=min_pres_conf,
            min_tracking_confidence=min_trk_conf,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.smooth_alpha = smooth_alpha
        self.lost_hold_frames = lost_hold_frames
        self.lowlight_thr = lowlight_thr
        self.clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tile)
        self._prev_hands: List[List[Tuple[float, float]]] = []
        self._last_good: List[List[Tuple[float, float]]] = []
        self._lost = 0
        self._t0 = time.time()

    @staticmethod
    def _auto_gamma(mean_lum: float) -> float:
        return float(np.clip(mean_lum / 128.0, 0.5, 1.0))

    def _preprocess(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        mean_lum = float(gray.mean())
        if mean_lum >= self.lowlight_thr:
            return frame_bgr, mean_lum, False
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
        gamma = self._auto_gamma(mean_lum)
        inv = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv) * 255 for i in range(256)]).astype(np.uint8)
        enhanced = cv2.LUT(enhanced, table)
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.08, beta=8)
        enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=35, sigmaSpace=35)
        return enhanced, mean_lum, True

    def _smooth(self, raw_hands):
        if not raw_hands:
            return raw_hands
        out = []
        for i, hand in enumerate(raw_hands):
            if i < len(self._prev_hands) and len(self._prev_hands[i]) == len(hand):
                new_hand = []
                for (px, py), lm in zip(self._prev_hands[i], hand):
                    nx = self.smooth_alpha * px + (1 - self.smooth_alpha) * lm.x
                    ny = self.smooth_alpha * py + (1 - self.smooth_alpha) * lm.y
                    new_hand.append((nx, ny))
                out.append(new_hand)
            else:
                out.append([(lm.x, lm.y) for lm in hand])
        self._prev_hands = out
        return out

    def process(self, frame_bgr) -> HandData:
        h, w = frame_bgr.shape[:2]
        detect_frame, mean_lum, lowlight = self._preprocess(frame_bgr)
        rgb = cv2.cvtColor(detect_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int((time.time() - self._t0) * 1000)
        try:
            results = self.detector.detect_for_video(mp_image, ts_ms)
        except Exception:
            results = None
        raw = results.hand_landmarks if (results and results.hand_landmarks) else []

        if raw:
            self._lost = 0
            smoothed = self._smooth(raw)
            self._last_good = smoothed
        else:
            self._lost += 1
            if self._lost <= self.lost_hold_frames and self._last_good:
                smoothed = self._last_good
            else:
                smoothed = []
                self._prev_hands = []

        data = HandData(width=w, height=h, lowlight=lowlight, mean_lum=mean_lum)
        for hand_xy in smoothed:
            data.hands_norm.append(hand_xy)
            px = [(int(x * w), int(y * h)) for (x, y) in hand_xy]
            data.hands_px.append(px)
            # pusat telapak = rata-rata wrist + MCP semua jari
            anchors = [0, 5, 9, 13, 17]
            valid = [px[i] for i in anchors if i < len(px)]
            if valid:
                cx = int(sum(p[0] for p in valid) / len(valid))
                cy = int(sum(p[1] for p in valid) / len(valid))
                data.hands_center.append((cx, cy))
                # skala telapak = jarak wrist -> middle MCP (proxy ukuran tangan)
                if len(px) > 9:
                    scale = math.hypot(px[9][0] - px[0][0], px[9][1] - px[0][1])
                else:
                    scale = 1.0
                data.hands_scale.append(max(1.0, float(scale)))
            else:
                data.hands_center.append((0, 0))
                data.hands_scale.append(1.0)
            objs = [_P(x, y) for (x, y) in hand_xy]
            if is_peace_sign(objs):
                data.peace = True
            if is_metal_gesture(objs):
                data.metal = True
        return data

    def close(self):
        try:
            self.detector.close()
        except Exception:
            pass
