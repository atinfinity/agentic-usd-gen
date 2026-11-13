"""側面画像から回転体の半径プロファイルを抽出する。

前提: 単色背景、商品 1 本が直立した真横からの画像。各行で前景の左端と右端を取り、
その幅の半分を半径とする（透明な PET でも縁の映り込みが前景として拾えれば幅が取れる）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

from .spec import Dimensions
from .vision import Landmarks

log = logging.getLogger(__name__)

N_SAMPLES = 256
DEFAULT_CAP_RATIO = 0.075  # 全高に対するキャップ高さ（取得できなかったときの既定値）


@dataclass
class Silhouette:
    top: int
    bottom: int
    left: np.ndarray  # 行 top..bottom の左端 x
    right: np.ndarray
    bg_lab: np.ndarray
    bg_noise: float
    touches_border: bool
    tilt: float  # 中心線の傾き（px/px）
    asymmetry: float  # 中心のばらつき / 最大半径

    @property
    def center(self) -> np.ndarray:
        return (self.left + self.right) / 2

    @property
    def radius(self) -> np.ndarray:
        return (self.right - self.left) / 2

    @property
    def height_px(self) -> int:
        return self.bottom - self.top

    def row(self, ratio: float) -> int:
        """上端=0、下端=1 の比率を画像の行に変換する。"""
        return int(round(self.top + ratio * self.height_px))

    def quality(self, image_shape: tuple[int, ...]) -> float:
        """輪郭抽出に向いているほど大きいスコア（0 は使えない）。"""
        if self.touches_border or self.bg_noise > 20 or self.height_px < 0.3 * image_shape[0]:
            return 0.0
        return (self.height_px / image_shape[0]) * max(0.0, 1 - 5 * self.asymmetry) * max(0.0, 1 - 10 * abs(self.tilt))


@dataclass
class RevolveProfile:
    """回転体のプロファイル（メートル、z は底面=0 から上向き）。"""

    z: np.ndarray
    r: np.ndarray
    height: float
    cap_z: float
    liquid_top_z: float | None
    label_z: tuple[float, float] | None
    colors: dict[str, str | None] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def radius_at(self, z: float) -> float:
        return float(np.interp(z, self.z, self.r))


def _median_filter(a: np.ndarray, k: int) -> np.ndarray:
    pad = k // 2
    padded = np.pad(a, pad, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(padded, k), axis=1)


def _to_hex(rgb: np.ndarray) -> str:
    r, g, b = (int(np.clip(v, 0, 255)) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


# 輪郭の線の切れ目をふさぐ幅（画像の長辺に対する比）
FILL_GAP = 0.02


def extract_silhouette(rgb: np.ndarray) -> Silhouette:
    """輪郭を抽出する。返す座標は元画像のもの。"""
    h0, w0 = rgb.shape[:2]
    lab0 = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    b = max(2, int(0.02 * min(h0, w0)))
    border0 = np.concatenate(
        [lab0[:b].reshape(-1, 3), lab0[-b:].reshape(-1, 3), lab0[:, :b].reshape(-1, 3), lab0[:, -b:].reshape(-1, 3)]
    )
    bg = np.median(border0, axis=0)
    # 商品が画像の端に接している写真（パックショットに多い）でも輪郭が閉じるよう、背景色で余白を足す
    pad = b * 2
    bg_rgb = cv2.cvtColor(bg.reshape(1, 1, 3).astype(np.uint8), cv2.COLOR_LAB2RGB).reshape(3)
    rgb = cv2.copyMakeBorder(rgb, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=[int(c) for c in bg_rgb])
    h, w = rgb.shape[:2]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    # 背景のばらつきは元画像の縁から測る。縁に接した商品の画素（背景から大きく離れた色）は除く
    border_dist = np.linalg.norm(border0 - bg, axis=1)
    inliers = border_dist[border_dist < 40]
    border_dist = inliers if inliers.size > 0.5 * border_dist.size else border_dist
    bg_noise = float(np.percentile(border_dist, 95))

    dist = np.linalg.norm(lab - bg, axis=2)
    thr = max(10.0, float(np.percentile(border_dist, 99)) + 4.0)
    fg = dist > thr
    # 透明部分は背景との色差が小さいので、エッジも前景に足す
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    fg |= cv2.Canny(gray, 30, 90) > 0

    k = max(3, int(0.006 * max(h, w)) | 1)
    fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    # 透明な容器は輪郭が細い線にしか写らず、線はところどころ途切れる。線で囲まれた内側も前景にする。
    # 線を太らせて切れ目をふさぎ、外周から届かない領域（内側）を同じ幅だけ広げて線まで戻す
    kf = max(k, int(FILL_GAP * max(h, w)) | 1)
    thick = cv2.dilate(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kf, kf)))
    cv2.floodFill(thick, None, (0, 0), 2)
    inside = (thick == 0).astype(np.uint8)
    if inside.any():
        fg |= cv2.dilate(inside, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kf + 2, kf + 2)))
        # 内側に凹凸の線が多いと、広げた内側が輪郭の線まで届かない。同じ行の中で近い線とはつなぐ。
        # 横方向だけなので各行の左右の端は変わらない。内側とつながった部分だけを足す（商品の下の注記の文字などは足さない）
        joined = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((1, kf), np.uint8))
        _, lab_j = cv2.connectedComponents(joined, connectivity=8)
        fg |= np.isin(lab_j, np.unique(lab_j[inside > 0])).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if n <= 1:
        raise ValueError("前景が見つかりません")
    areas = stats[1:, cv2.CC_STAT_AREA]
    main = 1 + int(np.argmax(areas))
    mx0, mw = stats[main, cv2.CC_STAT_LEFT], stats[main, cv2.CC_STAT_WIDTH]
    cx = mx0 + mw / 2
    keep = np.zeros(n, bool)
    for i in range(1, n):
        x0, ww, area = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_AREA]
        # 主成分の中心線と重なり、ある程度大きい成分（キャップが分離した場合など）も残す
        if i == main or (x0 <= cx <= x0 + ww and area > 0.002 * h * w):
            keep[i] = True
    mask = keep[labels]

    rows = np.where(mask.any(axis=1))[0]
    top, bottom = int(rows.min()), int(rows.max())
    left = np.full(bottom - top + 1, np.nan)
    right = np.full_like(left, np.nan)
    for i, y in enumerate(range(top, bottom + 1)):
        xs = np.where(mask[y])[0]
        if xs.size:
            left[i], right[i] = xs.min(), xs.max() + 1
    idx = np.arange(left.size)
    ok = ~np.isnan(left)
    left = np.interp(idx, idx[ok], left[ok])
    right = np.interp(idx, idx[ok], right[ok])

    # 余白を除いて元画像の座標に戻す
    top, bottom, left, right = top - pad, bottom - pad, left - pad, right - pad
    center = (left + right) / 2
    radius = (right - left) / 2
    # 見切れの判定: 左右の端に接している、または上下の端に幅広く接している（キャップの丸い頂部が触れる程度は許す）
    wide = 0.6 * radius.max()
    touches = bool(
        left.min() <= 1 or right.max() >= w0 - 2
        or (top <= 1 and radius[0] > wide) or (bottom >= h0 - 2 and radius[-1] > wide)
    )
    tilt = float(np.polyfit(idx, center, 1)[0])
    asym = float(np.std(center) / max(radius.max(), 1))
    return Silhouette(top, bottom, left, right, bg, bg_noise, touches, tilt, asym)


# ---------------------------------------------------------------- 目印の推定（画像認識が使えないとき）


def _center_strip(rgb: np.ndarray, sil: Silhouette, y0: int, y1: int, frac: float) -> np.ndarray:
    """行 y0..y1 の中心付近 frac 幅の画素（N×3）。"""
    px = []
    for y in range(max(y0, sil.top), min(y1, sil.bottom)):
        i = y - sil.top
        c, r = sil.center[i], sil.radius[i] * frac
        px.append(rgb[y, int(c - r) : int(c + r) + 1])
    return np.concatenate(px) if px else np.empty((0, 3))


def guess_label_band(rgb: np.ndarray, sil: Silhouette, cap_row: int) -> tuple[int, int] | None:
    """彩度が高く不透明な行が連続する最長区間をラベルとみなす。"""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    score = []
    for y in range(cap_row, sil.bottom):
        i = y - sil.top
        c, r = sil.center[i], sil.radius[i] * 0.6
        seg = hsv[y, int(c - r) : int(c + r) + 1]
        score.append(np.mean((seg[:, 1] > 90) & (seg[:, 2] > 70)) if seg.size else 0.0)
    on = np.array(score) > 0.3
    # ロゴや文字で途切れた短い区間を埋める
    gap = max(1, int(0.02 * sil.height_px))
    off_run = 0
    for i in range(on.size):
        if on[i]:
            if 0 < off_run <= gap and i - off_run > 0 and on[i - off_run - 1]:
                on[i - off_run : i] = True
            off_run = 0
        else:
            off_run += 1
    best, start = (0, 0), None
    for i, v in enumerate(np.append(on, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    if best[1] - best[0] < 0.05 * sil.height_px:
        return None
    return cap_row + best[0], cap_row + best[1]


def guess_liquid_top(rgb: np.ndarray, sil: Silhouette, cap_row: int) -> int | None:
    """キャップ下から下向きに見て、中心部が背景と大きく違う行が続き始める位置。"""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    start = cap_row + int(0.03 * sil.height_px)  # 口部のリングを飛ばす
    run, need = 0, max(3, int(0.02 * sil.height_px))
    for y in range(start, sil.bottom):
        i = y - sil.top
        c, r = sil.center[i], max(1.0, sil.radius[i] * 0.2)
        seg = lab[y, int(c - r) : int(c + r) + 1]
        dark = np.median(np.linalg.norm(seg - sil.bg_lab, axis=1)) > 30
        run = run + 1 if dark else 0
        if run >= need:
            return y - need + 1
    return None


# ---------------------------------------------------------------- プロファイル生成


def build_profile(
    rgb: np.ndarray,
    sil: Silhouette,
    dims: Dimensions,
    landmarks: Landmarks,
    spec_colors: dict[str, str | None],
) -> RevolveProfile:
    warnings: list[str] = []
    H, R = dims.height, dims.diameter / 2

    # 半径（px → m）。縦は全高、横は最大径で別々に合わせる（透視や撮影の歪みを吸収）
    radius_px = _median_filter(sil.radius, 5)
    sz = H / sil.height_px
    sr = R / radius_px.max()
    if abs(sr / sz - 1) > 0.15:
        warnings.append(f"画像の縦横比が寸法と {abs(sr / sz - 1):.0%} ずれています（斜め撮影や寸法誤りの可能性）")
    if abs(sil.tilt) > 0.02:
        warnings.append(f"画像の中心線が傾いています（{sil.tilt:+.3f}）")

    rows = np.arange(sil.top, sil.bottom + 1)
    z_rows = (sil.bottom - rows) * sz  # 上端 = H、下端 = 0
    z = np.linspace(0, H, N_SAMPLES)
    r = np.interp(z, z_rows[::-1], (radius_px * sr)[::-1])

    def ratio_to_z(ratio: float) -> float:
        return H * (1 - ratio)

    def row_to_z(y: int) -> float:
        return float((sil.bottom - y) * sz)

    # キャップ: 画像認識 > 検索した寸法 > 既定値
    if landmarks.cap_bottom is not None:
        cap_z = ratio_to_z(landmarks.cap_bottom)
    elif dims.cap_height:
        cap_z = H - dims.cap_height
    else:
        cap_z = H * (1 - DEFAULT_CAP_RATIO)
        warnings.append("キャップ高さが不明のため既定値を使いました")
    cap_row = sil.row(1 - cap_z / H)

    # ラベル
    if landmarks.label_top is not None and landmarks.label_bottom is not None:
        label_z = (ratio_to_z(landmarks.label_bottom), ratio_to_z(landmarks.label_top))
    else:
        band = guess_label_band(rgb, sil, cap_row)
        label_z = (row_to_z(band[1]), row_to_z(band[0])) if band else None

    # 液面
    if landmarks.liquid_top is not None:
        liquid_z = ratio_to_z(landmarks.liquid_top)
    else:
        y = guess_liquid_top(rgb, sil, cap_row)
        liquid_z = row_to_z(y) if y is not None else None
    if liquid_z is None:
        # 肩（半径が最大径の 6 割を超える位置）まで入っているとみなす
        above = z[(r > 0.6 * R) & (z < cap_z)]
        liquid_z = float(above.max()) if above.size else 0.8 * cap_z
        warnings.append("液面が判別できないため肩の位置にしました")
    liquid_z = min(liquid_z, cap_z - 0.002)

    # キャップとラベル地の色は検索結果を優先し、無いときだけ画像から推定する（印刷や反射で色がずれやすい）
    colors = dict(spec_colors)
    cap_px = _center_strip(rgb, sil, sil.top, cap_row, 0.5)
    if cap_px.size and not colors.get("cap"):
        colors["cap"] = _to_hex(np.median(cap_px, axis=0))
    if label_z and not colors.get("label_base"):
        lab_px = _center_strip(rgb, sil, sil.row(1 - label_z[1] / H), sil.row(1 - label_z[0] / H), 0.6)
        if lab_px.size:
            colors["label_base"] = _to_hex(np.median(lab_px, axis=0))
    liq_rows = (sil.row(1 - label_z[0] / H) + 3, sil.bottom - int(0.04 * sil.height_px)) if label_z else None
    if not liq_rows or liq_rows[1] - liq_rows[0] < 5:
        liq_rows = (sil.row(1 - liquid_z / H) + 3, sil.row(1 - (label_z[1] if label_z else liquid_z * 0.5) / H))
    liq_px = _center_strip(rgb, sil, *liq_rows, 0.3)
    if liq_px.size:
        med = np.median(liq_px, axis=0)
        med_lab = cv2.cvtColor(med.astype(np.uint8).reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        colors["liquid"] = None if np.linalg.norm(med_lab - sil.bg_lab) < 20 else _to_hex(med)

    return RevolveProfile(z, r, H, cap_z, liquid_z, label_z, colors, warnings)


def parametric_profile(dims: Dimensions, spec_colors: dict[str, str | None]) -> RevolveProfile:
    """画像が使えないときの簡易ボトル形状（胴・肩・首・キャップ）。"""
    H, R = dims.height, dims.diameter / 2
    cap_h = dims.cap_height or H * DEFAULT_CAP_RATIO
    rc = (dims.cap_diameter or dims.diameter * 0.46) / 2
    rn = rc * 0.92
    cap_z = H - cap_h
    neck_z = cap_z - 0.06 * H
    body_top = 0.55 * H

    z = np.linspace(0, H, N_SAMPLES)
    r = np.empty_like(z)
    for i, zi in enumerate(z):
        if zi < 0.02 * H:
            r[i] = R * (0.9 + 0.1 * zi / (0.02 * H))
        elif zi < body_top:
            r[i] = R
        elif zi < neck_z:
            t = (zi - body_top) / (neck_z - body_top)
            r[i] = rn + (R - rn) * 0.5 * (1 + np.cos(np.pi * t))
        elif zi < cap_z:
            r[i] = rn
        else:
            r[i] = rc
    return RevolveProfile(
        z, r, H, cap_z, liquid_top_z=body_top + 0.3 * (neck_z - body_top), label_z=None,
        colors=dict(spec_colors), warnings=["画像が使えないため寸法だけの簡易形状で作成しました"],
    )


def draw_debug(rgb: np.ndarray, sil: Silhouette, prof: RevolveProfile) -> np.ndarray:
    out = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR).copy()
    ys = np.arange(sil.top, sil.bottom + 1)
    pts_l = np.stack([sil.left, ys], 1).astype(np.int32)
    pts_r = np.stack([sil.right, ys], 1).astype(np.int32)
    cv2.polylines(out, [pts_l, pts_r], False, (0, 255, 0), 2)
    cv2.polylines(out, [np.stack([sil.center, ys], 1).astype(np.int32)], False, (255, 0, 0), 1)

    def hline(zv: float, color: tuple[int, int, int], text: str) -> None:
        y = sil.row(1 - zv / prof.height)
        cv2.line(out, (0, y), (out.shape[1], y), color, 1)
        cv2.putText(out, text, (5, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    hline(prof.cap_z, (0, 0, 255), "cap")
    if prof.liquid_top_z is not None:
        hline(prof.liquid_top_z, (255, 0, 255), "liquid")
    if prof.label_z:
        hline(prof.label_z[0], (0, 200, 255), "label bottom")
        hline(prof.label_z[1], (0, 200, 255), "label top")
    return out
