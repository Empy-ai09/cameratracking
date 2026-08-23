"""Panel halftone presisi ke jari (4 titik sudut dari landmark tangan).

State machine: IDLE -> ARMED -> OPEN (dengan debounce, mirip TwoHandPanel).
Sumber 4 titik: INDEX_FINGER_TIP (8) dan THUMB_TIP (4) dari dua tangan pertama.
Warp perspektif + efek dot-halftone (CLAHE, grid dot, tint biru gelap).
EMA smoothing pada 4 titik quad + fallback last-good-hold.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple, List

import cv2
import numpy as np

from hand_tracker import HandData

IDLE = "idle"
ARMED = "armed"
OPEN = "open"

INDEX_ID = 8
THUMB_ID = 4


class HalftonePanelManager:
    TOUCH_RATIO = 1.4
    OPEN_RATIO = 3.2
    TOUCH_FRAMES = 6
    OPEN_FRAMES = 4
    LOST_FRAMES = 10

    def __init__(
        self,
        video_path: str = "glich.mp4",
        smooth: float = 0.35,
        fade_speed: float = 0.18,
        cell_size: int = 12,
        max_radius_ratio: float = 0.6,
        dark_blue: Tuple[int, int, int] = (30, 40, 100),
        black: Tuple[int, int, int] = (10, 10, 10),
        skip_frames: int = 1,
    ):
        self.state = IDLE
        self.alpha = 0.0
        self.smooth = smooth
        self.fade_speed = fade_speed
        self.cell_size = cell_size
        self.max_radius = max_radius_ratio * cell_size
        self.dark_blue = dark_blue
        self.black = black
        self.skip_frames = skip_frames
        self._suspended = False
        self._touch_count = 0
        self._open_count = 0
        self._lost_count = 0
        self._quad_smooth: Optional[List[Tuple[float, float]]] = None
        self._last_good_quad: Optional[List[Tuple[float, float]]] = None

        # Buka video glich sebagai sumber animasi loop
        self.cap_vid = cv2.VideoCapture(video_path)
        if not self.cap_vid.isOpened():
            raise RuntimeError(f"Tidak bisa membuka video: {video_path}")
        self._frame_idx = 0

    def suspend(self):
        self._suspended = True

    def resume(self):
        self._suspended = False

    def reset(self):
        self.state = IDLE
        self._touch_count = self._open_count = self._lost_count = 0
        self._quad_smooth = None
        self._last_good_quad = None
        self.alpha = 0.0

    @property
    def active(self) -> bool:
        return not self._suspended

    @property
    def visible(self) -> bool:
        return self.alpha > 0.01

    def _extract_quad_points(self, hand: HandData) -> Optional[List[Tuple[int, int]]]:
        # butuh minimal 2 tangan
        if len(hand.hands_px) < 2:
            return None
        # pastikan setiap tangan punya cukup landmark
        pts = []
        for hand_px in hand.hands_px[:2]:
            if len(hand_px) <= max(INDEX_ID, THUMB_ID):
                return None
            pts.extend([
                (int(hand_px[INDEX_ID][0]), int(hand_px[INDEX_ID][1])),
                (int(hand_px[THUMB_ID][0]), int(hand_px[THUMB_ID][1])),
            ])
        # pts = [left_index, left_thumb, right_index, right_thumb]
        # Urutkan sehingga index menjadi sudut luar berlawanan, thumb sudut dalam berlawanan
        # Kita urutkan: index pertama, index kedua, thumb kedua, thumb pertama (clockwise)
        # Ini memastikan index dan thumb berlawanan secara diagonal.
        left_idx = pts[0]
        left_thumb = pts[1]
        right_idx = pts[2]
        right_thumb = pts[3]
        # Tentukan urutan clockwise mulai dari kiri atas (atau kanan atas) berdasarkan y
        # Untuk stabilitas, urutkan berdasarkan y rata-rata
        # Kita akan pakai urutan tetap: left_index, right_index, right_thumb, left_thumb
        # (index luar atas, index luar bawah, thumb dalam bawah, thumb dalam atas)
        # Ini membentuk quad yang menyerupai kartu dipegang dua tangan.
        quad = [left_idx, right_idx, right_thumb, left_thumb]
        return quad

    def _smooth_quad(self, quad: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
        if self._quad_smooth is None:
            self._quad_smooth = [(float(x), float(y)) for x, y in quad]
            return self._quad_smooth
        s = self.smooth
        smoothed = []
        for (cx, cy), (tx, ty) in zip(self._quad_smooth, quad):
            nx = cx + (tx - cx) * s
            ny = cy + (ty - cy) * s
            smoothed.append((nx, ny))
        self._quad_smooth = smoothed
        return smoothed

    def update(self, hand: HandData):
        if self._suspended:
            self.state = IDLE
            self._touch_count = self._open_count = 0
            self.alpha += (0.0 - self.alpha) * self.fade_speed
            return

        # Cek apakah ada 2 tangan dan quad valid
        raw_quad = self._extract_quad_points(hand)
        two_hands = len(hand.hands_px) >= 2

        if raw_quad is None or not two_hands:
            self._lost_count += 1
            if self._lost_count > self.LOST_FRAMES:
                self.reset()
            else:
                # tahan last good
                pass
        else:
            self._lost_count = 0
            smoothed = self._smooth_quad(raw_quad)
            self._last_good_quad = smoothed

            # Hitung jarak antara tangan (gunakan index tips)
            # Kita pakai jarak antara titik tengah index dan thumb untuk menentukan touch/open
            # Atau gunakan jarak antara pusat tangan seperti two_hand_panel
            # Untuk konsistensi, gunakan jarak antara titik tengah dari 2 index tips
            p1 = np.array(smoothed[0], dtype=float)  # left index
            p2 = np.array(smoothed[2], dtype=float)  # right index
            # Skala tangan: rata-rata skala dari hand.hands_scale
            scale = 1.0
            if len(hand.hands_scale) >= 2:
                scale = max(1.0, (hand.hands_scale[0] + hand.hands_scale[1]) / 2.0)
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / scale

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

        target_alpha = 1.0 if self.state == OPEN else 0.0
        self.alpha += (target_alpha - self.alpha) * self.fade_speed
        self.alpha = max(0.0, min(1.0, self.alpha))
        if self.alpha <= 0.01 and self.state != OPEN:
            # Tidak reset quad, tetap tahan untuk fallback
            pass

    def _build_halftone(self, src_gray: np.ndarray) -> np.ndarray:
        h_img, w_img = src_gray.shape
        cell = self.cell_size
        max_r = self.max_radius
        # downsampled grid: block-reduce via cv2.resize average
        gh = h_img // cell
        gw = w_img // cell
        if gh == 0 or gw == 0:
            return np.ones((h_img, w_img, 3), dtype=np.uint8) * 255
        small = cv2.resize(src_gray, (gw, gh), interpolation=cv2.INTER_AREA)
        darkness = 1.0 - (small.astype(np.float32) / 255.0)
        ys, xs = np.indices((gh, gw))
        cx = (xs * cell + cell // 2).astype(np.int32)
        cy = (ys * cell + cell // 2).astype(np.int32)
        r = np.clip((darkness * max_r), 0, max_r).astype(np.int32)
        out = np.ones((h_img, w_img, 3), dtype=np.uint8) * 255
        # color mask: <60 mean -> dark_blue, else black
        mean_v = small
        blue_mask = mean_v < 60
        b_ch = np.where(blue_mask, self.dark_blue[0], self.black[0]).astype(np.uint8)
        g_ch = np.where(blue_mask, self.dark_blue[1], self.black[1]).astype(np.uint8)
        r_ch = np.where(blue_mask, self.dark_blue[2], self.black[2]).astype(np.uint8)
        # paint dots (radius 0 -> skip)
        for yy in range(gh):
            for xx in range(gw):
                radius = int(r[yy, xx])
                if radius > 0:
                    cv2.circle(out, (int(cx[yy, xx]), int(cy[yy, xx])), radius,
                               (int(b_ch[yy, xx]), int(g_ch[yy, xx]), int(r_ch[yy, xx])), -1)
        return out

    def draw(self, frame: np.ndarray) -> np.ndarray:
        if self.alpha <= 0.01:
            return frame

        # Gunakan quad terakhir yang valid (baik smooth saat ini atau last good)
        quad_pts = None
        if self._last_good_quad is not None:
            quad_pts = [(int(round(x)), int(round(y))) for x, y in self._last_good_quad]

        if quad_pts is None or len(quad_pts) != 4:
            return frame

        # Pastikan semua titik dalam frame
        h, w = frame.shape[:2]
        quad_pts = [
            (max(0, min(x, w - 1)), max(0, min(y, h - 1))) for x, y in quad_pts
        ]

        # Baca frame video berikutnya (loop)
        ret, vid_frame = self.cap_vid.read()
        if not ret:
            # Loop kembali ke awal
            self.cap_vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, vid_frame = self.cap_vid.read()
        if not ret or vid_frame is None:
            # Fallback jika video gagal dibaca
            return frame

        # Proses frame video menjadi grayscale kontras tinggi
        gray_vid = cv2.cvtColor(vid_frame, cv2.COLOR_BGR2GRAY)
        eq_vid = cv2.equalizeHist(gray_vid)
        clahe_vid = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_base = clahe_vid.apply(eq_vid)

        # Membuat gambar halftone dari frame video
        halftone_img = self._build_halftone(gray_base)

        # Sumber rectangle (ukuran source image)
        sh, sw = halftone_img.shape[:2]
        src_pts = np.array([[0, 0], [sw, 0], [sw, sh], [0, sh]], dtype=np.float32)
        dst_pts = np.array(quad_pts, dtype=np.float32)

        # Perspektif warp
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(
            halftone_img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255)
        )

        # Mask polygon untuk blending halus (supaya tepi sesuai quad)
        mask = np.zeros((h, w), dtype=np.uint8)
        poly_pts = np.array(quad_pts, dtype=np.int32)
        cv2.fillConvexPoly(mask, poly_pts, 255)

        # Blend dengan alpha
        alpha_mask = (mask.astype(np.float32) / 255.0 * self.alpha)[..., None]
        # Di luar polygon, biarkan frame asli (warped mungkin ada warna putih di luar karena borderValue)
        # Jadi blend hanya di area mask
        out = frame.astype(np.float32)
        warped_float = warped.astype(np.float32)
        out = warped_float * alpha_mask + out * (1.0 - alpha_mask)
        # Untuk area di luar mask tapi di dalam bounding box warp (seharusnya sudah putih karena borderValue)
        # Kita bisa memastikan bahwa di luar mask, gunakan frame asli
        # Sudah tercapai karena alpha_mask = 0 di luar mask.
        return out.astype(np.uint8)
