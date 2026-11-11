"""テスト用の合成ボトル画像（白背景・真横・既知の寸法）。"""

from __future__ import annotations

import numpy as np

# 画素単位の形状: 全高 820px、胴半径 130px → 縦横比は 高さ 0.205m / 直径 0.065m に一致
TOP, BOTTOM = 40, 860
CX = 300
R_BODY = 130
R_NECK = 56
R_CAP = 60
CAP_BOTTOM = 100  # キャップ: 行 40..100
SHOULDER_TOP, SHOULDER_BOTTOM = 160, 330
LABEL = (420, 600)
LIQUID_TOP = 200


def radius_at(y: int) -> float:
    if y < CAP_BOTTOM:
        return R_CAP
    if y < SHOULDER_TOP:
        return R_NECK
    if y < SHOULDER_BOTTOM:
        t = (y - SHOULDER_TOP) / (SHOULDER_BOTTOM - SHOULDER_TOP)
        return R_NECK + (R_BODY - R_NECK) * 0.5 * (1 - np.cos(np.pi * t))
    return R_BODY


def make_bottle(width: int = 600, height: int = 900) -> np.ndarray:
    img = np.full((height, width, 3), 255, np.uint8)
    for y in range(TOP, BOTTOM + 1):
        r = int(radius_at(y))
        x0, x1 = CX - r, CX + r
        if y < CAP_BOTTOM:
            img[y, x0:x1] = (200, 20, 30)  # 赤いキャップ
        elif y < LIQUID_TOP:
            img[y, x0 : x0 + 3] = (150, 160, 160)  # 透明 PET の縁だけ
            img[y, x1 - 3 : x1] = (150, 160, 160)
        elif LABEL[0] <= y < LABEL[1]:
            img[y, x0:x1] = (210, 25, 35)  # 赤いラベル
            img[y, CX - 40 : CX + 40] = (250, 250, 250) if (y // 10) % 2 else (210, 25, 35)
        else:
            img[y, x0:x1] = (45, 20, 15)  # 濃い茶色の液体
            img[y, x0 : x0 + 3] = (150, 160, 160)
            img[y, x1 - 3 : x1] = (150, 160, 160)
    return img
