"""色テクスチャから、粗さ・金属度・法線のテクスチャを作る。

表面の種類（紙・フィルム・プラスチック・金属など）ごとに、
- 粗さ: 地の値と、インクの乗った部分の値を、色の濃さで混ぜる。細かいむらを足す
- 金属度（金属のみ）: 色の付いたインクは下の金属が透けるので金属、白や黒の不透明なインクは非金属
- 法線: 種類ごとの凹凸（紙の繊維、フィルムのしわ、金属のヘアライン）を高さとして描き、接空間の法線にする
を作る。色テクスチャから作るので、切り抜き・展開・アトラスの配置をやり直す必要がない。

同じ入力からはバイト単位で同じ画像になる（乱数の種は色テクスチャの中身から決める）。
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Surface:
    roughness: float  # 地（インクのない部分）の粗さ
    ink_roughness: float  # インクの乗った部分の粗さ
    jitter: float  # 粗さのむらの振れ幅
    bump: float  # 法線の凹凸の強さ（高さの勾配に掛ける倍率）。傾きの標準偏差が 0.02〜0.08 になるよう決めた
    metal: bool = False


SURFACES: dict[str, Surface] = {
    "paper": Surface(0.68, 0.48, 0.05, 0.3),  # コート紙の地はマット、インクは少しつやがある
    "film": Surface(0.20, 0.24, 0.04, 0.8),  # 光沢フィルム。しわでハイライトが揺れる
    "plastic": Surface(0.42, 0.40, 0.03, 0.3),
    "metal": Surface(0.26, 0.40, 0.03, 0.5, metal=True),  # 地は金属、白インクの部分は粗く非金属
    "wood": Surface(0.62, 0.62, 0.06, 0.32),
    "food": Surface(0.55, 0.50, 0.06, 0.34),
}

MAP_SCALE = 2  # 法線・粗さは色テクスチャの 1/MAP_SCALE の解像度で作る（細かい凹凸は見分けられず、容量だけ増えるため）


def surface_kind(role: str, labels: list[str] | None, metallic: float = 0.0) -> str:
    """マテリアルのロールと意味ラベルから、表面の種類を決める。"""
    labels = labels or []
    if metallic > 0 or "metal" in labels:
        return "metal"
    for kind in ("paper", "wood", "food"):
        if kind in labels:
            return kind
    # 容器・袋に巻いた印刷物はフィルム。部品の画像（画面など）は成形品のプラスチック
    return "film" if role == "label" else "plastic"


def _seed(img: np.ndarray, kind: str) -> int:
    return zlib.crc32(img.tobytes() + kind.encode())


def _smooth_noise(rng: np.random.Generator, shape: tuple[int, int], scale: float,
                  aspect: float = 1.0) -> np.ndarray:
    """平均 0・標準偏差 1 くらいのなめらかなノイズ。scale は模様の大きさ [px]、aspect は縦横の伸び（>1 で縦長）。"""
    h, w = shape
    sh = max(2, int(h / (scale * aspect)) + 2)
    sw = max(2, int(w / scale) + 2)
    small = Image.fromarray(rng.random((sh, sw), dtype=np.float32), mode="F")
    big = np.array(small.resize((w, h), Image.BICUBIC), np.float32)
    big -= big.mean()
    return big / (big.std() + 1e-6)


def _ink(rgb: np.ndarray) -> np.ndarray:
    """インクの量（0〜1）。白い地は 0、濃い色・鮮やかな色ほど 1。"""
    a = rgb.astype(np.float32) / 255
    v = a.max(axis=2)
    s = np.where(v > 0, (v - a.min(axis=2)) / np.maximum(v, 1e-6), 0)
    return np.clip(1 - v + s, 0, 1)


def _metallic(rgb: np.ndarray) -> np.ndarray:
    """金属に印刷したときの金属度（0〜1）。白や黒の不透明なインクは非金属、色の付いたインクは金属が透ける。"""
    a = rgb.astype(np.float32) / 255
    v = a.max(axis=2)
    s = np.where(v > 0, (v - a.min(axis=2)) / np.maximum(v, 1e-6), 0)
    white = np.clip((v - 0.72) / 0.2, 0, 1) * (1 - np.clip(s / 0.18, 0, 1))
    black = np.clip((0.22 - v) / 0.15, 0, 1)
    return np.clip(0.95 * (1 - np.maximum(white, 0.8 * black)), 0.05, 1)


def _height(kind: str, rng: np.random.Generator, shape: tuple[int, int]) -> np.ndarray:
    """種類ごとの凹凸の高さ（おおよそ -1〜1）。"""
    if kind == "paper":  # 繊維のざらつきと、すき むら
        fiber = cv2.GaussianBlur(rng.random(shape, dtype=np.float32), (0, 0), 0.8)
        fiber = (fiber - fiber.mean()) / (fiber.std() + 1e-6)
        return 0.35 * fiber + 0.5 * _smooth_noise(rng, shape, 24)
    if kind == "film":  # 縦に伸びたゆるいしわ
        return _smooth_noise(rng, shape, 40, aspect=3.0) + 0.3 * _smooth_noise(rng, shape, 10, aspect=2.0)
    if kind == "metal":  # 横方向のヘアライン（缶の胴の周方向）
        lines = np.repeat(rng.normal(0, 1, (shape[0], 1)).astype(np.float32), shape[1], axis=1)
        lines = cv2.GaussianBlur(lines, (0, 0), 0.6)
        return 0.25 * lines + 0.3 * _smooth_noise(rng, shape, 30)
    if kind in ("wood", "food"):
        return _smooth_noise(rng, shape, 6) + 0.5 * _smooth_noise(rng, shape, 20)
    return 0.6 * _smooth_noise(rng, shape, 16)


def normal_from_height(h: np.ndarray, strength: float) -> np.ndarray:
    """高さから接空間の法線（OpenGL 形式: 緑が +V＝画像の上向き）を 8 bit RGB で返す。"""
    dx = np.gradient(h, axis=1) * strength
    dy = -np.gradient(h, axis=0) * strength  # 画像の行は下向き、V は上向き
    n = np.stack([-dx, -dy, np.ones_like(h)], axis=2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return np.round((n * 0.5 + 0.5) * 255).astype(np.uint8)


def make_maps(rgb: np.ndarray, kind: str, roughness: float | None = None) -> dict[str, np.ndarray]:
    """色テクスチャ（H×W×3, uint8）から roughness / normal（と金属なら metallic）の画像を作る。

    roughness を渡すと、地の粗さをその値にする（インクの部分も同じだけずらす）。
    """
    sf = SURFACES.get(kind, SURFACES["plastic"])
    if roughness is not None:
        d = roughness - sf.roughness
        sf = Surface(roughness, sf.ink_roughness + d, sf.jitter, sf.bump, sf.metal)
    h, w = rgb.shape[:2]
    shape = (max(16, h // MAP_SCALE), max(16, w // MAP_SCALE))
    small = np.asarray(Image.fromarray(rgb[..., :3]).resize(shape[::-1], Image.BOX))
    rng = np.random.default_rng(_seed(small, kind))

    ink = _ink(small)
    if sf.metal:
        metallic = _metallic(small)
        # 非金属の部分（白インク）ほど、インクの粗さに近づける
        rough = sf.roughness + (sf.ink_roughness - sf.roughness) * (1 - metallic)
    else:
        metallic = None
        rough = sf.roughness + (sf.ink_roughness - sf.roughness) * ink
    rough = rough + sf.jitter * _smooth_noise(rng, shape, 48)
    out = {
        "roughness": np.round(np.clip(rough, 0.02, 1) * 255).astype(np.uint8),
        "normal": normal_from_height(_height(kind, rng, shape), sf.bump),
    }
    if metallic is not None:
        out["metallic"] = np.round(metallic * 255).astype(np.uint8)
    return out


def write_maps(texture: Path, kind: str, roughness: float | None = None) -> dict[str, Path]:
    """texture の隣に <名前>_roughness.png などを書き出し、{種類: パス} を返す。"""
    rgb = np.asarray(Image.open(texture).convert("RGB"))
    paths = {}
    for name, img in make_maps(rgb, kind, roughness).items():
        p = texture.with_name(f"{texture.stem}_{name}.png")
        Image.fromarray(img).save(p, optimize=True)
        paths[name] = p
    return paths
