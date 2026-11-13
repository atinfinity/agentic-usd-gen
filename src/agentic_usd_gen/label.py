"""正面画像のラベル部分を円筒に逆投影して、全周のラベルテクスチャを作る。

テクスチャの u は円周方向（u=0.75 が正面 = Blender の -Y 側）、v は下端=0。
正面から見えている ±VISIBLE_DEG の範囲だけ画像から取る。写っていない側は、高さごとに、写っている範囲の代表色で塗る
（絵柄が空・山・草地のように上下で色が変わるラベルでも、境目が縦の切れ目にならない）。
"""

from __future__ import annotations

import numpy as np

from .profile import RevolveProfile, Silhouette
from .texres import texture_px

VISIBLE_DEG = 70.0
FEATHER_DEG = 20.0
FRONT_U = 0.75


def _hex_to_rgb(h: str) -> np.ndarray:
    return np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], np.float32)


def label_circumference(prof: RevolveProfile) -> float:
    """ラベル帯の中ほどの円周 [m]。"""
    assert prof.label_z is not None
    z0, z1 = prof.label_z
    return float(2 * np.pi * prof.radius_at((z0 + z1) / 2))


def label_size(prof: RevolveProfile, source_px: float | None = None) -> tuple[int, int]:
    """全周ラベルテクスチャの (幅, 高さ) [px]。幅は円周の実寸から決め（texres）、縦横比はラベル帯の高さ : 円周。

    source_px は元の画像に写っている円周ぶんの画素数（これを大きく超えて引き伸ばさない）。
    """
    z0, z1 = prof.label_z
    circumference = label_circumference(prof)
    width = texture_px(circumference, source_px)
    return width, max(16, int(width * (z1 - z0) / circumference))


def wrap_texture(img: np.ndarray, prof: RevolveProfile) -> np.ndarray:
    """展開済みの全周ラベル画像（横 = 円周、u=0.75 が正面）をラベル帯の大きさにそろえる。"""
    from PIL import Image

    return np.asarray(Image.fromarray(img).resize(label_size(prof, img.shape[1]), Image.LANCZOS))


def make_label_texture(rgb: np.ndarray, sil: Silhouette, prof: RevolveProfile) -> np.ndarray:
    z0, z1 = prof.label_z
    # 写真の縮尺（高さ方向の px/m）で円周を測ったときの画素数を、元の解像度とみなす
    tex_w, tex_h = label_size(prof, label_circumference(prof) * sil.height_px / prof.height)

    u = (np.arange(tex_w) + 0.5) / tex_w
    phi = 2 * np.pi * u  # 点 (r cosφ, r sinφ)。正面は φ = -90°（u = 0.75）
    delta = np.degrees(np.abs((phi - 2 * np.pi * FRONT_U + np.pi) % (2 * np.pi) - np.pi))
    weight = np.clip((VISIBLE_DEG - delta) / FEATHER_DEG, 0, 1)
    xs_unit = np.cos(phi)  # 画像上の横位置（中心からの比率、右が +X）

    v = (np.arange(tex_h) + 0.5) / tex_h
    z = z0 + v * (z1 - z0)
    rows = np.clip(np.round(sil.top + (1 - z / prof.height) * sil.height_px).astype(int), sil.top, sil.bottom)
    idx = rows - sil.top
    xs = sil.center[idx][:, None] + sil.radius[idx][:, None] * xs_unit[None, :]
    xs = np.clip(np.round(xs).astype(int), 0, rgb.shape[1] - 1)

    sampled = rgb[rows[:, None], xs].astype(np.float32)
    # 写っていない側の色: 高さごとに、写っている範囲の中央値（文字やマークに引かれない）。上下に少しならして筋を消す
    seen = sampled[:, weight >= 1] if (weight >= 1).any() else sampled
    fill = np.median(seen, axis=1)
    n = max(1, tex_h // 16) | 1
    padded = np.pad(fill, ((n // 2, n // 2), (0, 0)), mode="edge")
    fill = np.stack([np.convolve(padded[:, c], np.ones(n) / n, mode="valid") for c in range(3)], axis=1)
    tex = sampled * weight[None, :, None] + fill[:, None, :] * (1 - weight[None, :, None])
    # 行 0 が v=1（上端）になるよう上下反転して画像として返す
    return np.clip(tex[::-1], 0, 255).astype(np.uint8)
