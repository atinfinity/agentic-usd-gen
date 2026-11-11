"""架空の商品のデザイン: パン屋の什器と包装なしのパン。

products.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の物の一般的な値にする。
正面は −Y（お客さま側）。床置きの什器はキネマティック（static）、パン・トレーは動かせる。
パンを並べる面は薄い水平の板（トレーの底板）にする（商品を並べるツールが棚板として見つけられるように）。
トレーの縁・受けの桟は細く、棚板と見なされない。看板は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .paint import Canvas, mix
from .products import _box, _cyl, _face
from .super_fixtures import _grain

BAKERY_PLACES = ["bakery", "cafe", "supermarket"]  # パン売り場の看板が合う場所
WOOD, WOOD_DARK, WALNUT = "#C49A64", "#7A5533", "#5B3B26"
KRAFT, CREAM, STAINLESS = "#C9A577", "#F3EBDD", "#C4C8CC"
TRAY = "#B9BEC4"  # パンのトレー（アルミ・樹脂の銀色）
BLACK = "#2A2B2E"


def _wood(name, size, center, color=WOOD, faces=None, collision=True, rotation=None) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish="matte", faces=faces, collision=collision, material="wood")


def _kraft(w_mm: float, d_mm: float, seed: int) -> np.ndarray:
    """トレーに敷くクラフト紙（上から見た面）。"""
    c = Canvas(w_mm, d_mm, None, KRAFT, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(KRAFT, "#FFFFFF", 0.10), mix(KRAFT, "#000000", 0.05))
    c.pattern(0, 0, w_mm, d_mm, "dots", mix(KRAFT, "#8D6E4A", 0.25), 7, 0.6)
    for _ in range(6):  # しわ
        x = c.rng.uniform(0, w_mm)
        c.line([(x, 0), (x + c.rng.uniform(-30, 30), d_mm)], mix(KRAFT, "#FFFFFF", 0.18), 0.8)
    return _face(c.array(), "paper", seed, 0.6, 4)


def _tray(prefix: str, w: float, d: float, x: float, y: float, z: float, top_img: int | None,
          rim_h: float = 0.02, rim_t: float = 0.008, color: str = TRAY, rim_collision: bool = True) -> list[Part]:
    """底板（薄い板、z は底板の下の面）と、その外に立てた縁。縁は底板の外形の外に置き、底板の上に重ねない。"""
    plate = Part(f"{prefix}Plate", "box", [w, d, 0.004], [x, y, z + 0.002], color=color if top_img is None else KRAFT,
                 finish="metal" if top_img is None else "matte", faces=None if top_img is None else {"top": top_img},
                 material="aluminum" if top_img is None else "paper", bevel=0)
    rims = [
        _box(f"{prefix}RimF", (w + 2 * rim_t, rim_t, rim_h), (x, y - d / 2 - rim_t / 2, z + rim_h / 2), color, "metal",
             collision=rim_collision),
        _box(f"{prefix}RimB", (w + 2 * rim_t, rim_t, rim_h), (x, y + d / 2 + rim_t / 2, z + rim_h / 2), color, "metal",
             collision=rim_collision),
        _box(f"{prefix}RimL", (rim_t, d, rim_h), (x - w / 2 - rim_t / 2, y, z + rim_h / 2), color, "metal",
             collision=rim_collision),
        _box(f"{prefix}RimR", (rim_t, d, rim_h), (x + w / 2 + rim_t / 2, y, z + rim_h / 2), color, "metal",
             collision=rim_collision),
    ]
    return [plate, *rims]


def _header(w_mm: float, h_mm: float, seed: int, title: str, sub: str) -> tuple[np.ndarray, np.ndarray]:
    """パン売り場の看板（木の板に文字・小麦の絵）と、文字を抜いた木の板。"""
    blank = _grain(w_mm, h_mm, seed, WOOD)
    c = Canvas(w_mm, h_mm, None, WOOD, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(WOOD, "#FFFFFF", 0.10), mix(WOOD, "#000000", 0.06))
    c.rect(8, 8, w_mm - 8, h_mm - 8, fill=CREAM, radius=6)
    c.text(w_mm / 2, h_mm * 0.42, title, h_mm * 0.38, "#5D3A1A", 900, spacing=6)
    c.text(w_mm / 2, h_mm * 0.80, sub, h_mm * 0.17, "#8D5A2B", 700)
    for x in (w_mm * 0.12, w_mm * 0.88):  # 小麦の穂
        c.line([(x, h_mm * 0.85), (x, h_mm * 0.20)], "#B8862F", 2.4)
        for k in range(5):
            y = h_mm * (0.25 + 0.11 * k)
            c.ellipse(x - 12, y - 5, x - 1, y + 5, fill="#D6A646")
            c.ellipse(x + 1, y - 5, x + 12, y + 5, fill="#D6A646")
    return _face(c.array(), "paper", seed, 0.5, 6), blank


# ---------------------------------------------------------------- 陳列棚・トレー置き台・トレー


def bakery_display_shelf() -> Product:
    """パン屋の木の陳列棚（4 段、各段にクラフト紙を敷いたトレー 2 枚）。正面は −Y。

    参考: パン屋のセルフ式の平台・ひな壇の陳列棚（一般的な構成）
    """
    W, D, H = 1.30, 0.50, 1.45
    t = 0.03
    head, head_blank = _header(1240, 100, 5801, "焼きたてパン", "FRESH BAKED BREAD  毎朝お店で焼いています")
    images = [_kraft(580, 380, 5802), head, head_blank]
    inner = W - 2 * t
    parts: list[Part] = [
        _wood("SideL", (t, D, H - t), (-W / 2 + t / 2, 0, (H - t) / 2), WOOD_DARK),
        _wood("SideR", (t, D, H - t), (W / 2 - t / 2, 0, (H - t) / 2), WOOD_DARK),
        _wood("Back", (inner, 0.02, H - t - 0.10), (0, D / 2 - 0.01, 0.10 + (H - t - 0.10) / 2), WOOD),
        _wood("Plinth", (inner, D - 0.06, 0.10), (0, -0.01, 0.05), WALNUT),
        _wood("Top", (W, D, t), (0, 0, H - t / 2), WOOD_DARK),
        Part("Header", "box", [inner, 0.008, 0.10], [0, -D / 2 + 0.004, H - t - 0.05], color=WOOD, finish="matte",
             faces={"front": 1}, collision=False, material="wood", bevel=0, blank=2),
    ]
    tw, td = 0.58, 0.38
    for lv, z in enumerate((0.20, 0.50, 0.80, 1.08)):  # 段（受けの桟の上面）
        parts += [_wood(f"RailF{lv}", (inner, 0.03, 0.03), (0, -0.16, z - 0.015), WOOD_DARK),
                  _wood(f"RailB{lv}", (inner, 0.03, 0.03), (0, 0.16, z - 0.015), WOOD_DARK)]
        for k, x in enumerate((-0.305, 0.305)):
            parts += _tray(f"Tray{lv}{k}", tw, td, x, 0.0, z, 0, rim_h=0.018, rim_collision=False)
    return Product(slug="bakery_display_shelf", name="パン屋の木の陳列棚（トレー付き 4 段）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=55.0, static=True, material="wood",
                   description="形はパン屋のセルフ式の一般的な木の陳列棚（幅 1300 mm・奥行き 500 mm・高さ 1450 mm、4 段の受けの桟に"
                               "クラフト紙を敷いた 580 × 380 mm のトレーを 2 枚ずつ、上に売り場の看板）で、寸法・質量は代表値。看板の文面は架空。",
                   tags=["パン屋", "ベーカリー", "陳列棚", "パン棚", "店舗什器", "bakery shelf", "bread display",
                         "bakery rack"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts,
                   picture_places=BAKERY_PLACES)


def _tong_sign(w_mm: float, h_mm: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    c = Canvas(w_mm, h_mm, None, CREAM, seed)
    c.gradient(0, 0, w_mm, h_mm, "#FFF9EE", "#EFE3CC")
    c.text(w_mm / 2, h_mm * 0.22, "セルフサービス", h_mm * 0.13, "#8D5A2B", 800)
    c.text(w_mm / 2, h_mm * 0.45, "トレーとトングを", h_mm * 0.14, "#5D3A1A", 900)
    c.text(w_mm / 2, h_mm * 0.62, "お取りください", h_mm * 0.14, "#5D3A1A", 900)
    c.text(w_mm / 2, h_mm * 0.84, "TRAY & TONGS", h_mm * 0.11, "#B8862F", 900, spacing=3)
    blank = Canvas(w_mm, h_mm, None, CREAM, seed)
    blank.gradient(0, 0, w_mm, h_mm, "#FFF9EE", "#EFE3CC")
    return _face(c.array(), "paper", seed, 0.5, 6), _face(blank.array(), "paper", seed, 0.5, 6)


def tray_tong_station() -> Product:
    """パン屋の入口のトレー・トング置き台（重ねたトレー・トング立て・下段の棚）。正面は −Y。"""
    W, D, top_z = 0.60, 0.45, 0.85
    t = 0.02
    sign, blank = _tong_sign(200, 150, 5811)
    parts: list[Part] = [
        _wood("SideL", (t, D, top_z), (-W / 2 + t / 2, 0, top_z / 2), WOOD_DARK),
        _wood("SideR", (t, D, top_z), (W / 2 - t / 2, 0, top_z / 2), WOOD_DARK),
        _wood("Back", (W - 2 * t, t, top_z - 0.08), (0, D / 2 - t / 2, 0.08 + (top_z - 0.08) / 2), WOOD),
        _wood("Kick", (W - 2 * t, D - t, 0.08), (0, -t / 2, 0.04), WALNUT),
        _wood("Top", (W, D, 0.03), (0, 0, top_z - 0.015), WOOD_DARK),
        _wood("Shelf", (W - 2 * t, D - t - 0.01, t), (0, -t / 2 - 0.005, 0.45), WOOD),
        # 重ねたトレー（左寄り）
        _box("TrayStack", (0.34, 0.26, 0.06), (-0.10, -0.04, top_z + 0.03), TRAY, "metal"),
    ]
    # トング立て（右奥）とトング
    tx, ty = 0.19, 0.06
    parts.append(_cyl("TongHolder", (0.11, 0.11, 0.14), (tx, ty, top_z + 0.07), STAINLESS, "metal"))
    for k, a in enumerate((-12, 0, 12)):
        parts.append(Part(f"Tong{k}", "box", [0.025, 0.012, 0.23], [tx + math.sin(math.radians(a)) * 0.03, ty,
                          top_z + 0.11], [0, a, 0], color=STAINLESS, finish="metal", collision=False,
                          material="steel"))
    parts += [
        _box("SignStand", (0.012, 0.012, 0.10), (tx, -0.17, top_z + 0.05), WALNUT, "matte", collision=False),
        Part("Sign", "box", [0.20, 0.006, 0.15], [tx, -0.18, top_z + 0.10 + 0.075], [-8, 0, 0], color=CREAM,
             finish="plastic", faces={"front": 0}, collision=False, material="paper", bevel=0, blank=1),
    ]
    H = top_z + 0.10 + 0.15
    return Product(slug="tray_tong_station", name="パン屋のトレー・トング置き台", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=22.0, static=True, material="wood",
                   description="形はパン屋の入口に置く一般的なトレー・トング置き台（幅 600 mm・奥行き 450 mm・天板の高さ 850 mm、"
                               "天板に重ねたトレーとトング立て・案内の札、下に棚）で、寸法・質量は代表値。案内の文面は架空。",
                   tags=["パン屋", "ベーカリー", "トレー置き", "トング", "セルフサービス", "店舗什器", "tray stand",
                         "tong holder", "bakery"],
                   photos=[], colors=Colors(label_base=WOOD), images=[sign, blank], parts=parts,
                   picture_places=BAKERY_PLACES)


def bakery_display_table() -> Product:
    """パン屋の売り場の中央に置く木の平台（手前が低く奥が一段高い 2 段、各段にクラフト紙を敷いたトレー 2 枚）。正面は −Y。

    看板は付けない（島に置いて四方から見るため）。台の箱・奥の段は厚い箱で、棚板として見つかるのはトレーの底板 4 枚だけ。
    """
    W, D = 1.20, 0.90
    body_z, step = 0.70, 0.12  # 手前の段の高さ、奥の段の高さの差
    bh = body_z - 0.08
    images = [_kraft(560, 380, 5821), _grain(W * 1000, bh * 1000, 5822, WOOD), _grain(D * 1000, bh * 1000, 5823, WOOD),
              _grain(W * 1000, step * 1000, 5824, WOOD_DARK)]
    parts: list[Part] = [
        _wood("Plinth", (W - 0.06, D - 0.06, 0.08), (0, 0, 0.04), WALNUT),
        _wood("Body", (W, D, bh), (0, 0, 0.08 + bh / 2), WOOD,
              faces={"front": 1, "back": 1, "left": 2, "right": 2}),
        _wood("Step", (W, D / 2, step), (0, D / 4, body_z + step / 2), WOOD_DARK, faces={"front": 3, "back": 3}),
        # 手前の段の縁（細い見切り。棚板にはならない）
        _wood("EdgeF", (W, 0.025, 0.03), (0, -D / 2 + 0.0125, body_z + 0.015), WOOD_DARK),
        _wood("EdgeL", (0.025, D / 2 - 0.025, 0.03), (-W / 2 + 0.0125, -D / 4 + 0.0125, body_z + 0.015), WOOD_DARK),
        _wood("EdgeR", (0.025, D / 2 - 0.025, 0.03), (W / 2 - 0.0125, -D / 4 + 0.0125, body_z + 0.015), WOOD_DARK),
    ]
    tw, td = 0.56, 0.36
    for lv, (y, z) in enumerate(((-D / 4 + 0.005, body_z), (D / 4, body_z + step))):
        for k, x in enumerate((-0.29, 0.29)):
            parts += _tray(f"Tray{lv}{k}", tw, td, x, y, z, 0, rim_h=0.018, rim_collision=False)
    H = body_z + step + 0.018
    return Product(slug="bakery_display_table", name="パン屋の木の平台（2 段のトレー付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=45.0, static=True,
                   material="wood",
                   description="形はパン屋の売り場の中央に置く一般的な木の平台（幅 1200 mm・奥行き 900 mm、手前の段の高さ 700 mm・"
                               "奥の段 820 mm、各段にクラフト紙を敷いた 560 × 360 mm のトレーを 2 枚ずつ）で、寸法・質量は代表値。"
                               "看板なし。",
                   tags=["パン屋", "ベーカリー", "平台", "陳列台", "アイランド", "店舗什器", "bakery display table",
                         "bakery table", "bread table", "display table"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


def bread_tray_bakery() -> Product:
    """パン屋のセルフ式のトレー（340 × 260 mm）とトング。"""
    w, d, rim_t, rim_h = 0.33, 0.25, 0.005, 0.02
    parts = _tray("Tray", w, d, 0, 0, 0, None, rim_h=rim_h, rim_t=rim_t)
    # トング（2 本の腕と付け根）を斜めに載せる。コリジョンはトレーだけ
    a = 20.0
    for k, dy in enumerate((-0.006, 0.006)):
        parts.append(Part(f"TongArm{k}", "box", [0.23, 0.012, 0.003], [0.0, -0.03 + dy, 0.004 + 0.006 + 0.0015 * k],
                          [0, -2, a + (4 if k else -4)], color=STAINLESS, finish="metal", collision=False,
                          material="steel", bevel=0))
    parts.append(Part("TongHinge", "cylinder", [0.016, 0.016, 0.012], [0.105, 0.005, 0.004 + 0.008], color=BLACK,
                      finish="plastic", collision=False, material="plastic"))
    W = w + 2 * rim_t
    return Product(slug="bread_tray_bakery", name="パンのトレーとトング", shape_class="assembly", category="household",
                   dims=Dimensions(rim_h, W, depth=d + 2 * rim_t), mass_kg=0.35, static=False, material="aluminum",
                   description="形はパン屋のセルフ式の一般的なトレー（340 × 260 mm・縁の高さ 20 mm）と、ステンレスのトング（長さ 230 mm）"
                               "で、寸法・質量は代表値。",
                   tags=["パン屋", "ベーカリー", "トレー", "トング", "bread tray", "bakery tray", "tongs"],
                   photos=[], colors=Colors(label_base=TRAY), images=[], parts=parts)


# ---------------------------------------------------------------- 包装なしのパン


def _crust(w_mm: float, d_mm: float, seed: int, top: str, edge: str, gloss: float = 0.25,
           kind: str = "plain") -> np.ndarray:
    """パンの焼き色（bread 部品の山に、頂点からの道のりで貼る）。中央が濃く、裾が淡い。kind で模様（層・パン粉・クープ・へそ）。"""
    c = Canvas(w_mm, d_mm, 8, edge, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(edge, "#FFFFFF", 0.06), mix(edge, "#000000", 0.08))
    steps = 14
    for k in range(steps):  # 裾 → 中央へ濃くなる楕円
        f = k / steps
        mx, my = w_mm * 0.5 * f * 0.92, d_mm * 0.5 * f * 0.92
        c.ellipse(mx, my, w_mm - mx, d_mm - my, fill=mix(edge, top, min(1.0, f * 1.25)))
    if kind == "layers":  # クロワッサンの生地の層（節に沿った筋）
        for k in range(1, 3):
            y = d_mm * k / 3
            c.line([(w_mm * 0.1, y), (w_mm * 0.5, y + 1.5), (w_mm * 0.9, y)], mix(top, "#3A1E0A", 0.3), 0.8)
    elif kind == "panko":  # カレーパンのパン粉
        for _ in range(int(w_mm * d_mm / 6)):
            x, y = c.rng.uniform(0, w_mm), c.rng.uniform(0, d_mm)
            r = c.rng.uniform(0.6, 1.6)
            col = mix(top, "#F2C46A", c.rng.uniform(0.2, 0.7))
            c.ellipse(x - r, y - r, x + r, y + r, fill=col)
    elif kind == "coupe":  # バゲットのクープ 1 本（節の長さ方向に開いた明るい切れ目）
        c.ellipse(w_mm * 0.18, d_mm * 0.40, w_mm * 0.82, d_mm * 0.62, fill=mix(top, "#E9C27C", 0.65))
        c.line([(w_mm * 0.2, d_mm * 0.60), (w_mm * 0.8, d_mm * 0.60)], mix(top, "#3A1E0A", 0.45), 1.2)
    elif kind == "navel":  # あんパンのへそとけし
        cx, cy = w_mm / 2, d_mm / 2
        c.ellipse(cx - 7, cy - 7, cx + 7, cy + 7, fill=mix(top, "#2A1408", 0.35))
        for _ in range(70):
            a, r = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, 6.5)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            c.ellipse(x - 0.6, y - 0.4, x + 0.6, y + 0.4, fill="#F1EADB")
    if gloss:  # つや（左上の光）
        c.ellipse(w_mm * 0.25, d_mm * 0.18, w_mm * 0.55, d_mm * 0.40, fill=mix(top, "#FFFFFF", gloss * 0.5))
        c.ellipse(w_mm * 0.30, d_mm * 0.22, w_mm * 0.50, d_mm * 0.34, fill=mix(top, "#FFFFFF", gloss * 0.8))
    for _ in range(int(w_mm * d_mm / 25)):  # 焼きむら（小さく淡い）
        x, y = c.rng.uniform(0, w_mm), c.rng.uniform(0, d_mm)
        r = c.rng.uniform(0.3, 0.8)
        c.ellipse(x - r, y - r, x + r, y + r, fill=mix(top, "#3A1E0A", c.rng.uniform(0.04, 0.12)))
    for k in range(int(2 * (w_mm + d_mm) / 3)):  # 裾の焼きむら（縁が単色だと切り抜かれる）
        u = c.rng.uniform(0, 2 * (w_mm + d_mm))
        x, y = (u, 0) if u < w_mm else (w_mm, u - w_mm) if u < w_mm + d_mm else \
            (u - w_mm - d_mm, d_mm) if u < 2 * w_mm + d_mm else (0, u - 2 * w_mm - d_mm)
        r = c.rng.uniform(0.5, 1.2)
        c.ellipse(x - r, y - r, x + r, y + r, fill=mix(edge, "#5A3010", c.rng.uniform(0.06, 0.15)))
    return _face(c.array(), "paper", seed, 0.4, 2)


def _bread(name, size, center, color, faces=None, rotation=None) -> Part:
    """パンの山（bread）。パンは包装がないので部品そのものにコリジョンを付ける。"""
    return Part(name, "bread", list(size), list(center), list(rotation or [0, 0, 0]), color=color, finish="matte",
                collision=True, material="food", faces=faces)


def _footprint(parts: list[Part]) -> tuple[float, float, float, float]:
    """山・円柱の部品の足元（Z まわりに回した楕円）と箱の外接矩形 (x0, x1, y0, y1)。"""
    xs, ys = [], []
    for p in parts:
        a, b = p.size[0] / 2, p.size[1] / 2
        phi = math.radians(p.rotation[2])
        if p.shape == "box":
            hx = a * abs(math.cos(phi)) + b * abs(math.sin(phi))
            hy = a * abs(math.sin(phi)) + b * abs(math.cos(phi))
        else:
            hx = math.hypot(a * math.cos(phi), b * math.sin(phi))
            hy = math.hypot(a * math.sin(phi), b * math.cos(phi))
        xs += [p.center[0] - hx, p.center[0] + hx]
        ys += [p.center[1] - hy, p.center[1] + hy]
    return min(xs), max(xs), min(ys), max(ys)


def _centered(parts: list[Part]) -> tuple[float, float]:
    """足元の中心を原点に寄せ、(幅, 奥行き) を返す。"""
    x0, x1, y0, y1 = _footprint(parts)
    for p in parts:
        p.center[0] -= (x0 + x1) / 2
        p.center[1] -= (y0 + y1) / 2
    return x1 - x0, y1 - y0


def croissant() -> Product:
    """クロワッサン（三日月形）。節を弧に沿って重ねて並べ、両端を後ろ（+Y）へ曲げる。節が生地を巻いた層に見える。"""
    top, edge = "#A35A18", "#D9A050"
    R = 0.068  # 弧の半径
    # (弧の角度 [度], 弧に沿った幅, 弧に直交する長さ, 高さ, 画像)。隣どうし 3 割ほど重ねて 1 本の胴にする
    segs = [(0, 0.044, 0.064, 0.046, 0), (-22, 0.042, 0.056, 0.041, 1), (22, 0.042, 0.056, 0.041, 1),
            (-43, 0.038, 0.046, 0.033, 2), (43, 0.038, 0.046, 0.033, 2), (-62, 0.032, 0.034, 0.024, 3),
            (62, 0.032, 0.034, 0.024, 3)]
    images = [_crust(44, 64, 5821, top, edge, 0.3, "layers"), _crust(42, 56, 5822, top, edge, 0.25, "layers"),
              _crust(38, 46, 5823, "#B06A26", edge, 0.15, "layers"), _crust(32, 34, 5824, "#BC7A34", edge, 0.0)]
    parts = []
    for i, (a, w, d, h, img) in enumerate(segs):
        t = math.radians(a)
        parts.append(_bread(f"Seg{i}", (w, d, h), (R * math.sin(t), R * (1 - math.cos(t)), h / 2), top,
                            faces={"top": img}, rotation=[0, 0, a]))
    W, D = _centered(parts)
    H = max(p.size[2] for p in parts)
    return Product(slug="croissant", name="クロワッサン", shape_class="assembly", category="food",
                   dims=Dimensions(H, round(W, 4), depth=round(D, 4)), mass_kg=0.045, material="food",
                   description=f"形はパン屋の一般的なクロワッサン（三日月形、幅 {W * 1000:.0f} mm・奥行き {D * 1000:.0f} mm・"
                               f"高さ {H * 1000:.0f} mm、生地を巻いた節が 7 つ）で、寸法・質量は代表値。包装なし。",
                   tags=["パン", "クロワッサン", "ベーカリー", "包装なし", "croissant", "bread", "pastry"],
                   photos=[], colors=Colors(label_base=edge), images=images, parts=parts)


def anpan() -> Product:
    """あんパン（丸く平たい山、中央のへそにけしの実）。"""
    top, edge = "#7A3E12", "#B87430"
    D, H = 0.094, 0.036
    parts = [_bread("Bun", (D, D, H), (0, 0, H / 2), top, faces={"top": 0})]
    return Product(slug="anpan", name="あんパン", shape_class="assembly", category="food",
                   dims=Dimensions(H, D, depth=D), mass_kg=0.09, material="food",
                   description="形はパン屋の一般的なあんパン（直径 94 mm・高さ 36 mm、つやのある焼き色で中央のへそにけしの実）で、"
                               "寸法・質量は代表値。包装なし。",
                   tags=["パン", "あんパン", "菓子パン", "ベーカリー", "包装なし", "anpan", "sweet bun", "bread"],
                   photos=[], colors=Colors(label_base=top), images=[_crust(94, 94, 5831, top, edge, 0.35, "navel")],
                   parts=parts)


def curry_bread() -> Product:
    """カレーパン（楕円の揚げパン、パン粉の衣）。"""
    top, edge = "#A9661F", "#C98A3A"
    W, D, H = 0.13, 0.085, 0.045
    parts = [_bread("Bun", (W, D, H), (0, 0, H / 2), top, faces={"top": 0})]
    return Product(slug="curry_bread", name="カレーパン", shape_class="assembly", category="food",
                   dims=Dimensions(H, W, depth=D), mass_kg=0.11, material="food",
                   description="形はパン屋の一般的なカレーパン（楕円、長さ 130 mm・幅 85 mm・高さ 45 mm、パン粉の衣の揚げパン）で、"
                               "寸法・質量は代表値。包装なし。",
                   tags=["パン", "カレーパン", "総菜パン", "揚げパン", "ベーカリー", "包装なし", "curry bread", "bread"],
                   photos=[], colors=Colors(label_base=top), images=[_crust(130, 85, 5841, top, edge, 0.0, "panko")],
                   parts=parts)


def baguette() -> Product:
    """バゲット（クープごとの節を斜めに重ねてつなぐ。太さはほぼ一定で、両端だけ細い）。"""
    top, edge = "#94531A", "#C88A40"
    n, step = 9, 0.057  # 節（長さ 0.12 m）を半分ずつ重ね、つなぎ目の 1 割ほどのくぼみをクープの境目にする
    parts = []
    for i in range(n):
        x = (i - (n - 1) / 2) * step
        end = i in (0, n - 1)
        w, d, h = (0.110, 0.056, 0.048) if end else (0.120, 0.064, 0.056)
        parts.append(_bread(f"Seg{i}", (w, d, h), (x + (0.008 if i == 0 else -0.008 if end else 0), 0, h / 2), top,
                            faces={"top": 1 if end else 0}, rotation=[0, 0, 8]))
    W, D = _centered(parts)
    H = max(p.size[2] for p in parts)
    images = [_crust(120, 64, 5851, top, edge, 0.1, "coupe"), _crust(110, 56, 5852, "#9E5C20", edge, 0.0)]
    return Product(slug="baguette", name="バゲット", shape_class="assembly", category="food",
                   dims=Dimensions(H, round(W, 4), depth=round(D, 4)), mass_kg=0.25, material="food",
                   description=f"形はパン屋の一般的なバゲット（長さ {W * 1000:.0f} mm・幅 {D * 1000:.0f} mm・高さ {H * 1000:.0f} mm、"
                               "斜めのクープ 7 本）で、寸法・質量は代表値。包装なし。",
                   tags=["パン", "バゲット", "フランスパン", "ベーカリー", "包装なし", "baguette", "french bread",
                         "bread"],
                   photos=[], colors=Colors(label_base=top), images=images, parts=parts)


def _loaf_side(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    """食パンの側面（型に当たった焼き色、上の縁が淡い）。"""
    c = Canvas(w_mm, h_mm, 8, "#B87A38", seed)
    c.gradient(0, 0, w_mm, h_mm, "#C99050", "#8E5420")
    for _ in range(int(w_mm * h_mm / 30)):
        x, y = c.rng.uniform(0, w_mm), c.rng.uniform(0, h_mm)
        r = c.rng.uniform(0.5, 1.4)
        c.ellipse(x - r, y - r, x + r, y + r, fill=mix("#B87A38", "#5A3010", c.rng.uniform(0.1, 0.3)))
    return _face(c.array(), "paper", seed, 0.4, 10)


def shokupan_loaf() -> Product:
    """山型食パン 1.5 斤（イギリスパン）。型で焼いた胴の上に、ふくらんだ山が 2 つ。"""
    L, Wd, Hb = 0.18, 0.11, 0.09  # 胴（型の中）の長さ・幅・高さ
    mw, md, mh = 0.11, 0.118, 0.042  # 山の長さ・幅・高さ（型より少し張り出す）
    top, edge = "#7A4515", "#C08040"
    parts = [Part("Body", "box", [L, Wd, Hb], [0, 0, Hb / 2], color="#B87A38", finish="matte",
                  faces={"front": 0, "back": 0, "left": 1, "right": 1, "bottom": 2}, collision=True,
                  material="food", bevel=0.008)]
    for i, x in enumerate((-0.038, 0.038)):
        parts.append(_bread(f"Top{i}", (mw, md, mh), (x, 0, Hb - 0.006 + mh / 2), top, faces={"top": 3}))
    H = Hb - 0.006 + mh
    images = [_loaf_side(180, 90, 5861), _loaf_side(110, 90, 5862), _loaf_side(180, 110, 5864),
              _crust(110, 118, 5865, top, edge, 0.2)]
    return Product(slug="shokupan_loaf", name="山型食パン 1.5 斤", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), L, depth=md), mass_kg=0.55, material="food",
                   description=f"形はパン屋の一般的な山型食パン 1.5 斤（イギリスパン、長さ 180 mm・幅 118 mm・高さ {H * 1000:.0f} mm、"
                               "型の上に山が 2 つ）で、寸法・質量は代表値。包装なし。",
                   tags=["パン", "食パン", "山型食パン", "イギリスパン", "1.5 斤", "ベーカリー", "包装なし", "shokupan",
                         "bread loaf", "white bread"],
                   photos=[], colors=Colors(label_base="#B87A38"), images=images, parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    bakery_display_shelf, bakery_display_table, tray_tong_station, bread_tray_bakery, croissant, anpan, curry_bread, baguette,
    shokupan_loaf)}
