"""回転体の細部: キャップのローレット（縦の溝）と、缶の巻き締め（上面のくぼみ）・底のドーム。

ローレットのような細かい凹凸は形状にせず法線マップにして、頂点数を増やさない。
缶の上面のくぼみと底のドームは外形（凸包）の内側に入る形なので、コリジョンと質量・重心の計算は変わらない
（質量・重心は輪郭のプロファイルから求めていて、ここで足す輪は使わない）。
"""

from __future__ import annotations

import math

import numpy as np

from ..surface import normal_from_height

# ねじキャップ: 胴よりはっきり細く（直径の比）、ある程度の高さがあるもの
SCREW_CAP_MAX_RATIO = 0.65
SCREW_CAP_H = (0.008, 0.035)  # [m]
KNURL_PITCH = 0.0008  # 溝の間隔 [m]
KNURL_DEPTH = 0.00012  # 溝の深さ [m]
KNURL_PX = 8  # 溝 1 本あたりの画素数（の目安）
KNURL_BAND = (0.08, 0.84)  # 溝のある高さ（キャップの側面の v の範囲）。上の面取りと下端には付けない

# 缶: 金属で、上に低く太い巻き締めの縁（キャップ扱い）があるもの
CAN_RIM_MAX_H = 0.006  # [m]
CAN_RIM_MIN_RATIO = 0.7  # 縁の直径 ÷ 胴の直径
SEAM_WIDTH = 0.0013  # 巻き締めの縁の上面の幅 [m]
TOP_RECESS = 0.0063  # 縁の上端から蓋の平らな面までの深さ [m]
DOME_RATIO = 0.15  # 底のドームの高さ ÷ 胴の直径
STAND_WIDTH = 0.0010  # 底の接地する輪の幅 [m]


def _max_r(pts) -> float:
    return max(r for _, r in pts)


def is_screw_cap(cap_pts, body_pts, metal: bool) -> bool:
    """ボトルのねじキャップか（側面に縦の溝を付けるか）。"""
    cap_h = cap_pts[-1][0] - cap_pts[0][0]
    return (not metal and _max_r(cap_pts) <= SCREW_CAP_MAX_RATIO * _max_r(body_pts)
            and SCREW_CAP_H[0] <= cap_h <= SCREW_CAP_H[1])


def is_can(cap_pts, body_pts, metal: bool) -> bool:
    """飲料缶か（キャップが低く太い巻き締めの縁）。"""
    cap_h = cap_pts[-1][0] - cap_pts[0][0]
    return metal and cap_h <= CAN_RIM_MAX_H and _max_r(cap_pts) >= CAN_RIM_MIN_RATIO * _max_r(body_pts)


def knurl_normal_map(cap_pts) -> tuple[np.ndarray, float]:
    """キャップの側面の縦の溝の法線マップ（H×W×3, uint8）と、周方向の画素密度 [px/m] を返す。

    側面の UV は u = 角度、v = 高さの比率（build_revolve.py）。溝は u 方向にだけ変わる。
    """
    circ = 2 * math.pi * _max_r(cap_pts)
    n = max(round(circ / KNURL_PITCH), 8)
    w = min(2 ** math.ceil(math.log2(n * KNURL_PX)), 4096)
    h = 64
    u = (np.arange(w) + 0.5) / w
    v = 1 - (np.arange(h) + 0.5) / h  # 画像の上が v = 1
    ridge = 0.5 * KNURL_DEPTH * np.cos(2 * math.pi * n * u)  # [m]
    lo, hi = KNURL_BAND
    edge = 0.04
    env = np.clip((v - lo) / edge, 0, 1) * np.clip((hi - v) / edge, 0, 1)
    env = env * env * (3 - 2 * env)
    px_per_m = w / circ
    height = env[:, None] * ridge[None, :] * px_per_m  # 高さを画素単位にすると、勾配がそのまま傾きになる
    return normal_from_height(height.astype(np.float32), 1.0), px_per_m


def can_top_recess(cap_pts) -> list[list[float]]:
    """缶の上面: 巻き締めの縁の上端から内側へ、蓋の壁（チャックウォール）→ 溝 → 平らな面 と続く (z, r) の輪。"""
    H = cap_pts[-1][0]
    r = _max_r(cap_pts) - SEAM_WIDTH
    d = TOP_RECESS
    return [[H, r], [H - 0.0007, r - 0.0004], [H - d + 0.0009, r - 0.0013], [H - d, r - 0.0018],
            [H - d + 0.0007, r - 0.0027]]


def can_cap_bottom(cap_pts, recess) -> list[list[float]]:
    """縁の下面の内側の輪。くぼみの壁より少し外で止める（底を円で閉じると、くぼみを横切ってしまう）。"""
    z0 = cap_pts[0][0]
    zs = [z for z, _ in recess]
    rs = [r for _, r in recess]
    # くぼみの壁が縁の下端の高さを通るところの半径（z は上から下へ並ぶので逆順にして補間）
    r_wall = float(np.interp(z0, zs[::-1][1:], rs[::-1][1:]))
    return [[z0, min(r_wall + 0.0003, cap_pts[0][1] - 0.0002)]]


def can_bottom_dome(body_pts, diameter: float) -> list[list[float]]:
    """缶の底: 接地する輪から内側へ立ち上がり、中央が持ち上がったドームになる (z, r) の輪（外 → 中央）。"""
    r0 = body_pts[0][1]
    r1 = r0 - STAND_WIDTH
    r2 = r1 - 0.0018
    z2 = 0.0025
    dome = DOME_RATIO * diameter
    out = [[0.0, r1], [z2, r2]]
    # (0, dome) を頂点にして (z2, r2) を通る球の一部
    rad = (r2**2 + (dome - z2) ** 2) / (2 * (dome - z2))
    for t in np.linspace(0, 1, 7)[1:]:
        rr = r2 * (1 - t) + r2 * 0.12 * t
        out.append([float(dome - rad + math.sqrt(rad**2 - rr**2)), float(rr)])
    return out
