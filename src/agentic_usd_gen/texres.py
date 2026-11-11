"""テクスチャの解像度を、貼る表面の実寸から決める。

大きなボトル・箱でも近くから見たときの細かさがそろうよう、1 mm あたり PX_PER_MM 画素を目安にする。
一辺は 2 のべき乗に切り上げ（実際の密度は 8〜16 px/mm）、MAX_PX で頭打ちにする。
元の画像が小さいときは、それを大きく超えて引き伸ばさない（元の解像度にいちばん近い 2 のべき乗まで）。
"""

from __future__ import annotations

import math

PX_PER_MM = 8.0  # 目標の画素密度
MAX_PX = 4096  # テクスチャの一辺の上限
MIN_PX = 64


def _pow2(x: float, rounding) -> int:
    return 2 ** int(rounding(math.log2(max(x, 1.0))))


def texture_px(length_m: float, source_px: float | None = None, max_px: int = MAX_PX) -> int:
    """長さ length_m [m] の辺に割り当てる画素数（2 のべき乗）。source_px は元の画像のその辺の画素数。"""
    n = min(max(_pow2(length_m * 1000 * PX_PER_MM, math.ceil), MIN_PX), max_px)
    if source_px:
        n = min(n, max(_pow2(source_px, round), MIN_PX))
    return n


def draw_px_per_mm(length_m: float, max_px: int = MAX_PX) -> float:
    """長さ length_m [m] の辺の元の画像を描くときの画素密度 [px/mm]。

    texture_px は元の画像の画素数を 2 のべき乗に丸める（四捨五入）ので、目標の画素数の 1/√2 以上あれば
    目標のまま頭打ちにならない。PX_PER_MM を下回らず、それを満たす最小の値（少し余裕を持たせる）。
    上限 max_px で頭打ちになる大きな辺は、ちょうど max_px 画素になる値。
    """
    mm = length_m * 1000
    n = texture_px(length_m, max_px=max_px)
    return max(n / math.sqrt(2) / mm * 1.01, min(PX_PER_MM, n / mm))


def density(px: float, length_m: float) -> float:
    """画素密度 [px/mm]。"""
    return round(px / (length_m * 1000), 2)


def record(meta: dict, name: str, size: tuple[int, int], px: float, length_m: float) -> None:
    """meta["textures"][name] に画像の大きさ（幅, 高さ）と、長さ length_m に px 画素を割り当てたときの画素密度を残す。"""
    meta.setdefault("textures", {})[name] = {"size": [int(size[0]), int(size[1])], "px_per_mm": density(px, length_m)}
