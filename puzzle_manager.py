"""Puzzle Camera: snapshot ROI, tiles, drag-drop via pinch, reset via metal.
Tidak punya kamera/detector sendiri - konsumsi HandData dari HandTracker.
"""
from __future__ import annotations

import random
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np

from hand_tracker import HandData


def _rr(img, pt1, pt2, color, thickness, radius=20):
    x1, y1 = pt1; x2, y2 = pt2
    if thickness == -1:
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        for (cx, cy) in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                         (x1+radius, y2-radius), (x2-radius, y2-radius)]:
            cv2.circle(img, (cx, cy), radius, color, -1)
    else:
        cv2.line(img, (x1+radius, y1), (x2-radius, y1), color, thickness)
        cv2.line(img, (x1+radius, y2), (x2-radius, y2), color, thickness)
        cv2.line(img, (x1, y1+radius), (x1, y2-radius), color, thickness)
        cv2.line(img, (x2, y1+radius), (x2, y2-radius), color, thickness)
        cv2.ellipse(img, (x1+radius, y1+radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2-radius, y1+radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x1+radius, y2-radius), (radius, radius), 90,  0, 90, color, thickness)
        cv2.ellipse(img, (x2-radius, y2-radius), (radius, radius), 0,   0, 90, color, thickness)


class PuzzleManager:
    PINCH_DIST = 45

    def __init__(self, grid_size: int = 3):
        self.grid_size = grid_size
        self.state = "idle"   # idle | setup | puzzle
        self.tiles: List[np.ndarray] = []
        self.tile_rects: List[List[int]] = []
        self.tile_order: List[int] = []
        self.selected_idx: Optional[int] = None
        self.last_cursor: Tuple[int, int] = (0, 0)
        self.reset_cooldown = 0
        self.start_time = 0.0
        self.elapsed = 0.0
        self.is_solved = False
        self._exit_solved_at: Optional[float] = None

    def start_setup(self):
        self.state = "setup"
        self.is_solved = False

    def exit(self):
        self.state = "idle"
        self.tiles.clear(); self.tile_rects.clear(); self.tile_order.clear()
        self.selected_idx = None
        self.is_solved = False
        self._exit_solved_at = None

    @property
    def active(self) -> bool:
        return self.state in ("setup", "puzzle")

    @staticmethod
    def _dist(p1, p2) -> float:
        return float(np.linalg.norm(np.array(p1) - np.array(p2)))

    def _pinch_cursor(self, hand: HandData):
        for hand_px in hand.hands_px:
            if len(hand_px) <= 8:
                continue
            idx_tip = hand_px[8]; thm_tip = hand_px[4]
            if self._dist(idx_tip, thm_tip) < self.PINCH_DIST:
                return True, idx_tip
        return False, None

    def _create_snapshot(self, frame, roi):
        x1, y1, x2, y2 = roi
        crop = frame[y1:y2, x1:x2].copy()
        if crop.size == 0:
            return False
        hc, wc, _ = crop.shape
        th, tw = hc // self.grid_size, wc // self.grid_size
        if th == 0 or tw == 0:
            return False
        self.tiles, self.tile_rects = [], []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.tiles.append(crop[i*th:(i+1)*th, j*tw:(j+1)*tw].copy())
                self.tile_rects.append([j*tw + x1, i*th + y1, tw, th])
        self.tile_order = list(range(len(self.tiles)))
        random.shuffle(self.tile_order)
        if all(self.tile_order[i] == i for i in range(len(self.tile_order))):
            random.shuffle(self.tile_order)
        self.start_time = time.time()
        self.is_solved = False
        return True

    def update(self, frame, hand: HandData) -> bool:
        if self.state == "idle":
            return False
        h, w = frame.shape[:2]
        is_pinch, cursor = self._pinch_cursor(hand)
        if cursor:
            self.last_cursor = cursor

        if hand.metal and self.state == "puzzle" and self.reset_cooldown == 0:
            self.start_setup()
            self.reset_cooldown = 45

        if self.state == "setup":
            if len(hand.hands_px) >= 2 and len(hand.hands_px[0]) > 8 and len(hand.hands_px[1]) > 8:
                p1 = hand.hands_px[0][8]; p2 = hand.hands_px[1][8]
                cx, cy = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
                side = max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]), 250)
                x1, y1 = max(0, cx - side // 2), max(0, cy - side // 2)
                x2, y2 = min(w, x1 + side), min(h, y1 + side)
                _rr(frame, (x1, y1), (x2, y2), (255, 255, 255), 1, radius=20)
                if is_pinch:
                    if self._create_snapshot(frame, (x1, y1, x2, y2)):
                        self.state = "puzzle"

        elif self.state == "puzzle":
            if not self.is_solved:
                self.elapsed = time.time() - self.start_time
                if self.tile_order and all(self.tile_order[i] == i for i in range(len(self.tile_order))):
                    self.is_solved = True
                    self._exit_solved_at = time.time()

            for i in range(len(self.tile_order)):
                tx, ty, tw, th = self.tile_rects[i]
                if self.selected_idx == i and cursor:
                    tx, ty = cursor[0] - tw // 2, cursor[1] - th // 2
                if 0 <= ty < h - th and 0 <= tx < w - tw:
                    frame[ty:ty + th, tx:tx + tw] = self.tiles[self.tile_order[i]]
                    _rr(frame, (tx, ty), (tx + tw, ty + th), (0, 0, 0), 2, radius=10)

            if is_pinch and cursor and not self.is_solved:
                if self.selected_idx is None:
                    for i, (rx, ry, rw, rh) in enumerate(self.tile_rects):
                        if rx < cursor[0] < rx + rw and ry < cursor[1] < ry + rh:
                            self.selected_idx = i
                            break
            else:
                if self.selected_idx is not None:
                    lx, ly = self.last_cursor
                    for i, (rx, ry, rw, rh) in enumerate(self.tile_rects):
                        if rx < lx < rx + rw and ry < ly < ry + rh:
                            self.tile_order[self.selected_idx], self.tile_order[i] = (
                                self.tile_order[i], self.tile_order[self.selected_idx])
                            break
                    self.selected_idx = None

            if is_pinch and cursor:
                cv2.circle(frame, cursor, 15, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.circle(frame, cursor, 5, (255, 255, 255), -1)

            if self.is_solved and self._exit_solved_at is not None:
                if (time.time() - self._exit_solved_at) > 2.5:
                    self.exit()
                    return True

        if self.reset_cooldown > 0:
            self.reset_cooldown -= 1
        return False
