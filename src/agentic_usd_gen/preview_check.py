"""プレビューの透明な部品の見え方を、画素の色で検査する（API は使わない）。

透明な物体はプレビューで破綻しても（液体が白く濁る・真っ黒・見えないなど）気づきにくい。
render_preview.py が描くマスク（debug/masks/）で液体と透明な容器の画素を取り出し、次を確かめる。

- 液体: 見えている液体の色（中央値）と、液体の色（colors.liquid）を透かした背景に表面の映り込みを足した色との差（ΔE）
- 透明な容器: 中身も不透明な部品もない所（液面より上など）の明るさ（中央値）と、背景の明るさとの差（ΔL*）
- 液体があるはずなのに（生成時に液面を決めた）、液体のメッシュがない・ほとんど見えない

半透明（translucent）の容器の奥の液体は、もともと白っぽく見えるので測らない。
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

VIEWS = ("front", "34")  # 真上からは液面とキャップしか見えないので使わない
MIN_PIXELS = 400  # これより少なければ測らない（ラベルでほとんど隠れているなど）
ERODE = 3  # 縁（輪郭の反射・アンチエイリアス）を除く幅 [px]
LIQUID_DE = 18.0  # 液体の色の差の許容（正常なら 13 以下）
# 液体の見え方 = 背景 × 液体の色^PATH × TRANSMIT + 背景 × REFLECT（線形）。液体のある架空の商品 20 点の
# プレビューに当てはめた。表面で返る光のぶん透過は弱まり（TRANSMIT）、周りの映り込みのぶん明るくなる（REFLECT）。
# 屈折で胴の中心より長く液体を通る光があるので、液体の色は少し濃く効く（PATH）
TRANSMIT = 0.85
REFLECT = 0.095
PATH = 1.14
CLEAR_DARK = 20.0  # 透明な容器が背景よりこれ以上暗ければ警告（L*。正常なら ±5 ほど）
CLEAR_BRIGHT = 20.0  # 背景よりこれ以上明るければ警告（L*）


def srgb_to_lab(rgb) -> np.ndarray:
    """sRGB（0〜255）→ CIE L*a*b*（D65）。"""
    c = np.asarray(rgb, float) / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def to_linear(rgb) -> np.ndarray:
    c = np.asarray(rgb, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(lin) -> np.ndarray:
    lin = np.clip(np.asarray(lin, float), 0, 1)
    return 255 * np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def rgb_hex(rgb) -> str:
    return "#" + "".join(f"{round(float(v)):02X}" for v in np.clip(rgb, 0, 255))


def _mask(path: Path) -> np.ndarray:
    a = np.asarray(Image.open(path).convert("RGBA"))
    return (a[..., 3] > 127) & (a[..., :3].min(-1) > 127)


def gather(debug_dir: Path) -> dict | None:
    """液体・中身のない透明な容器の画素（RGB）を、使う向きのぶんまとめて返す。マスクがなければ None。"""
    masks = debug_dir / "masks"
    if not (masks / "background.png").exists():
        return None
    out: dict = {"liquid": [], "clear": []}
    for view in VIEWS:
        prev = debug_dir / f"preview_{view}.png"
        if not prev.exists() or not (masks / f"{view}_liquid.png").exists():
            continue
        img = np.asarray(Image.open(prev).convert("RGBA"))
        solid = img[..., 3] > 250  # 背景の抜けた縁は除く
        liquid, clear, opaque = (_mask(masks / f"{view}_{k}.png") for k in ("liquid", "clear", "opaque"))
        regions = {"liquid": liquid, "clear": clear & ~liquid & ~opaque}
        for k, m in regions.items():
            m = cv2.erode((m & solid).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=ERODE).astype(bool)
            out[k].append(img[..., :3][m])
    bg = np.asarray(Image.open(masks / "background.png").convert("RGB")).reshape(-1, 3).mean(0)
    return {"background": bg, **{k: np.concatenate(v) if v else np.zeros((0, 3)) for k, v in out.items()}}


def expected_liquid(color: str | None, background) -> np.ndarray:
    """液体の色を透かした背景に、表面の映り込みを足した色。色がなければ（水など）背景の色を透かす。

    コーラ・醤油のような濃い液体は、映り込みだけが見えて黒に近い灰色になる。真っ黒に描かれても見た目は正しいので、
    この差（ΔE 3 ほど）は警告しない。
    """
    bg = to_linear(background)
    tint = to_linear(hex_rgb(color)) ** PATH if color else 1.0
    return to_srgb(bg * tint * TRANSMIT + bg * REFLECT)


def check(debug_dir: Path, liquid_color: str | None, liquid_expected: bool = False) -> dict | None:
    """透明な部品の見え方を測り、{liquid, clear, warnings} を返す。マスクがなければ None。

    liquid_expected: 液体があるはず（生成時に液面を決めた）か。液体が消えた・見えないときに警告する。
    """
    px = gather(debug_dir)
    if px is None:
        return None
    bg = px["background"]
    res: dict = {"background": rgb_hex(bg), "warnings": []}
    liq = px["liquid"]
    info_path = debug_dir / "masks" / "info.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else {}
    if liquid_expected and info.get("liquid") == 0:
        res["warnings"].append("液体があるはずなのに、USD に液体のメッシュがない")
    elif liquid_expected and info and len(liq) < MIN_PIXELS and not info.get("translucent"):
        # 半透明の容器の奥なら見えないのが正しい。透明な容器なのに見えなければ、消えたか隠れている。
        # info.json のない古い描画では半透明の部品があるかわからないので、警告しない
        res["warnings"].append(f"液体がプレビューでほとんど見えない（{len(liq)} px。ラベルで覆われていないか確かめる）")
    if len(liq) >= MIN_PIXELS:
        mean = np.median(liq, 0)  # 映り込みのハイライトに引っ張られないよう中央値
        exp = expected_liquid(liquid_color, bg)
        de = float(np.linalg.norm(srgb_to_lab(mean) - srgb_to_lab(exp)))
        res["liquid"] = {"expected": rgb_hex(exp), "measured": rgb_hex(mean), "delta_e": round(de, 1),
                         "pixels": len(liq)}
        if de > LIQUID_DE:
            res["warnings"].append(f"液体の色がプレビューで {rgb_hex(mean)} に見え、期待（{rgb_hex(exp)}）と違う"
                                   f"（ΔE {de:.0f}）")
    clr = px["clear"]
    if len(clr) >= MIN_PIXELS:
        mean = np.median(clr, 0)
        dl = float(srgb_to_lab(mean)[0] - srgb_to_lab(bg)[0])
        res["clear"] = {"measured": rgb_hex(mean), "delta_l": round(dl, 1), "pixels": len(clr)}
        if dl < -CLEAR_DARK or dl > CLEAR_BRIGHT:
            res["warnings"].append(f"透明な容器が背景より{'暗' if dl < 0 else '明る'}すぎる"
                                   f"（{rgb_hex(mean)}、背景 {rgb_hex(bg)}、ΔL* {dl:+.0f}）")
    return res
