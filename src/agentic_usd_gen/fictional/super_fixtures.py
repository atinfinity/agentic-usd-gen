"""架空の商品のデザイン: スーパーの売場の什器（青果・精肉鮮魚・惣菜・冷凍・特売）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
正面は −Y（お客さま側）。床置きの什器はキネマティック（static）。
商品を並べる面は薄い水平の板にする（商品を並べるツールが棚板として見つけられるように。傾けると板の外形の
高さが 5 cm を超えて棚板と見なされない）。青果の台の「傾き」は段（ひな壇）で表す。
売場の POP・看板（店の売り文句の入った面）は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .paint import Canvas, mix
from .products import COOL_WHITE, INK, LAMP_TILT, WARM_WHITE, _box, _cyl, _face, _lamp, _price_strip

SUPER_PLACES = ["supermarket", "shop"]  # 生鮮・特売の POP が合う場所
WOOD, WOOD_DARK, GRASS = "#B98A57", "#7A5533", "#4E8B3A"
STAINLESS, WHITE, GLASS = "#C4C8CC", "#F4F5F7", "#EAF2F5"


def _wood(name, size, center, color=WOOD, faces=None, collision=True) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), color=color, finish="matte",
                faces=faces, collision=collision, material="wood")


def _sign(name, size, center, color, faces, blank, rotation=None, collision=False, material="paper") -> Part:
    """POP・看板の板（Picture バリアントで無地にできる）。"""
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish="plastic", faces=faces, collision=collision, material=material, bevel=0,
                blank=blank)


def _grain(w_mm: float, h_mm: float, seed: int, base: str = WOOD) -> np.ndarray:
    """木目の板（台の側板など）。"""
    c = Canvas(w_mm, h_mm, None, base, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(base, "#FFFFFF", 0.08), mix(base, "#000000", 0.06))
    y = 6.0
    while y < h_mm:
        c.line([(0, y), (w_mm * 0.4, y + c.rng.uniform(-3, 3)), (w_mm, y + c.rng.uniform(-4, 4))],
               mix(base, WOOD_DARK, c.rng.uniform(0.15, 0.35)), c.rng.uniform(0.6, 1.6))
        y += c.rng.uniform(8, 22)
    return _face(c.array(), "paper", seed, 0.5, 6)


def _mat(w_mm: float, d_mm: float, seed: int, color: str = GRASS) -> np.ndarray:
    """青果の台に敷く人工芝のマット（上から見た面）。"""
    c = Canvas(w_mm, d_mm, None, color, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(color, "#FFFFFF", 0.06), mix(color, "#000000", 0.08))
    c.pattern(0, 0, w_mm, d_mm, "dots", mix(color, "#B5D99C", 0.35), 9, 1.2)
    return _face(c.array(), "paper", seed, 0.6, 4)


def _pop(w_mm: float, h_mm: float, title: str, sub: str, seed: int, bg: str = "#C62828", fg: str = "#FFFFFF",
         band: str = "#FFD54F", kind: str = "paper") -> np.ndarray:
    """売場の POP（色地に大きな文字・下に帯と小さな文字）。"""
    c = Canvas(w_mm, h_mm, None, bg, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(bg, "#FFFFFF", 0.1), mix(bg, "#000000", 0.12))
    bh = h_mm * 0.26
    c.rect(0, h_mm - bh, w_mm, h_mm, fill=band)
    c.text(w_mm / 2, (h_mm - bh) * 0.52, title, (h_mm - bh) * 0.55, fg, 900, max_w=w_mm * 0.92)
    c.text(w_mm / 2, h_mm - bh / 2, sub, bh * 0.5, INK, 800, max_w=w_mm * 0.92)
    return _face(c.array(), kind, seed, 0.4, 6)


def _rim(parts: list[Part], w: float, d: float, z_top: float, h: float = 0.06, t: float = 0.02) -> None:
    """台の縁（前・左右・奥）。幅が細いので棚板には数えられない。"""
    zc = z_top + h / 2
    parts += [_wood("RimFront", (w, t, h), (0, -d / 2 + t / 2, zc), WOOD_DARK),
              _wood("RimBack", (w, t, h), (0, d / 2 - t / 2, zc), WOOD_DARK),
              _wood("RimL", (t, d - 2 * t, h), (-w / 2 + t / 2, 0, zc), WOOD_DARK),
              _wood("RimR", (t, d - 2 * t, h), (w / 2 - t / 2, 0, zc), WOOD_DARK)]


# ---------------------------------------------------------------- 青果の平台


def produce_flat_table() -> Product:
    W, D = 1.20, 0.90
    top_z, rim_h = 0.72, 0.07
    H = top_z + rim_h
    imgs = [_mat(W * 1000, D * 1000, 4101), _grain(W * 1000, 640, 4102), _grain(D * 1000, 640, 4103),
            _pop(1100, 120, "産地直送 新鮮野菜", "朝どれ・その日のうちに店頭へ", 4104, "#2E7D32")]
    parts = [
        _wood("Skirt", (W, D, 0.64), (0, 0, 0.36), faces={"front": 1, "back": 1, "left": 2, "right": 2}),
        _wood("Plinth", (W - 0.04, D - 0.04, 0.04), (0, 0, 0.02), WOOD_DARK),
        _wood("TopBoard", (W, D, 0.04), (0, 0, top_z - 0.02), GRASS, faces={"top": 0}),
        _sign("PopStrip", (1.10, 0.004, 0.12), (0, -D / 2 - 0.002, 0.58), "#2E7D32", {"front": 3}, "#F7F5F0"),
    ]
    _rim(parts, W, D, top_z, rim_h)
    return Product(slug="produce_flat_table", name="青果の平台 1200mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D + 0.004), mass_kg=38.0, static=True, material="wood",
                   description="形はスーパーの青果売場の島に置く一般的な木製の平台（天板の高さ約 720 mm・人工芝のマット・"
                               "縁の高さ 70 mm・前面に POP）で、寸法・質量は代表値。天板は水平（傾けた台は 棚板と"
                               "見なされないため）。POP の文字は架空。",
                   tags=["青果", "平台", "野菜", "果物", "陳列台", "店舗什器", "スーパー", "produce table",
                         "produce display", "supermarket"], photos=[], colors=Colors(label_base=WOOD),
                   images=imgs, parts=parts, picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- 青果のひな壇


def produce_tiered_stand() -> Product:
    W, D = 1.20, 0.96
    steps = [(0.56, 0.32), (0.76, 0.32), (0.96, 0.32)]  # (板の上面, 奥行き)
    sign_h = 0.28
    top = steps[-1][0]
    H = top + 0.10 + sign_h + 0.06
    imgs = [_mat(W * 1000, 320, 4111), _grain(W * 1000, 560, 4112), _grain(D * 1000, 1020, 4113),
            _pop(1150, 260, "旬の野菜・くだもの", "本日のおすすめ", 4114, "#2E7D32")]
    parts: list[Part] = []
    y = -D / 2
    for k, (z, d) in enumerate(steps):
        yc = y + d / 2
        parts += [_wood(f"Riser{k}", (W, d, z - 0.04), (0, yc, (z - 0.04) / 2), faces={"front": 1}),
                  _wood(f"Step{k}", (W, d, 0.04), (0, yc, z - 0.02), GRASS, faces={"top": 0}),
                  _wood(f"Lip{k}", (W, 0.02, 0.06), (0, y + 0.01, z + 0.03), WOOD_DARK)]
        y += d
    side_h = top + 0.06
    parts += [_wood("SideL", (0.02, D, side_h), (-W / 2 - 0.01, 0, side_h / 2), faces={"left": 2}),
              _wood("SideR", (0.02, D, side_h), (W / 2 + 0.01, 0, side_h / 2), faces={"right": 2}),
              _wood("BackStop", (W, 0.02, 0.10), (0, D / 2 - 0.01, top + 0.05), WOOD_DARK)]
    zs = top + 0.10
    for k, x in enumerate((-W / 2 + 0.05, W / 2 - 0.05)):  # 看板の支柱
        parts.append(_cyl(f"SignPost{k}", (0.025, 0.025, H - zs), (x, D / 2 - 0.03, zs + (H - zs) / 2), WOOD_DARK,
                          "matte"))
    parts.append(_sign("SignBoard", (W - 0.04, 0.012, sign_h), (0, D / 2 - 0.05, H - 0.03 - sign_h / 2), "#2E7D32",
                       {"front": 3}, "#F7F5F0", collision=True))
    return Product(slug="produce_tiered_stand", name="青果のひな壇 3段", shape_class="assembly", category="fixture",
                   dims=Dimensions(round(H, 3), W + 0.04, depth=D), mass_kg=55.0, static=True, material="wood",
                   description="形はスーパーの青果売場の壁際・島に置く一般的な木製のひな壇（奥ほど高い 3 段、段の高さ"
                               "560・760・960 mm、奥行き各 320 mm、人工芝のマット、奥に看板）で、寸法・質量は代表値。"
                               "傾斜は段で表し、各段の天板は水平。看板の文字は架空。",
                   tags=["青果", "ひな壇", "段台", "野菜", "果物", "陳列台", "店舗什器", "スーパー", "tiered display",
                         "produce stand", "supermarket"], photos=[], colors=Colors(label_base=WOOD),
                   images=imgs, parts=parts, picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- バナナ用ハンガー


def banana_hanger() -> Product:
    H, R = 1.60, 0.30  # 高さ・台の半径
    chrome = "#C9CDD1"
    imgs = [_pop(300, 120, "バナナ", "1房 198円〜", 4121, "#F9A825", INK, "#FFFFFF", "plastic")]
    arm_z = H - 0.08
    parts = [_cyl("Base", (2 * R, 2 * R, 0.03), (0, 0, 0.015), "#3A3D42"),
             _cyl("Pole", (0.032, 0.032, H - 0.05), (0, 0, 0.03 + (H - 0.05) / 2), chrome),
             _cyl("Tray", (0.50, 0.50, 0.015), (0, 0, 0.72), "#E6E8EA", "plastic"),
             _box("ArmX", (0.62, 0.02, 0.02), (0, 0, arm_z), chrome, "metal"),
             _box("ArmY", (0.02, 0.62, 0.02), (0, 0, arm_z), chrome, "metal"),
             _cyl("Cap", (0.05, 0.05, 0.02), (0, 0, H - 0.01), chrome)]
    for k, (x, y) in enumerate(((-0.29, 0), (0.29, 0), (0, -0.29), (0, 0.29))):  # 房を掛けるフック
        parts += [_cyl(f"Hook{k}", (0.008, 0.008, 0.10), (x, y, arm_z - 0.06), chrome, collision=False),
                  _box(f"HookTip{k}", (0.03, 0.03, 0.008), (x, y, arm_z - 0.11), chrome, "metal", collision=False)]
    parts.append(_sign("PopCard", (0.30, 0.004, 0.12), (0, -0.02, H - 0.24), "#F9A825", {"front": 0}, "#FFFFFF"))
    return Product(slug="banana_hanger", name="バナナハンガー スタンド", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, 2 * R, depth=2 * R), mass_kg=9.0, static=True, material="steel",
                   description="形はスーパーの青果売場の一般的なバナナ用のスタンド（丸い台・支柱・高さ約 720 mm の受け皿・"
                               "上の十字の腕にフック 4 本・POP）で、寸法・質量は代表値。房はフックに掛けるか受け皿に置く。"
                               "POP の文字と値段は架空。",
                   tags=["バナナ", "バナナハンガー", "青果", "スタンド", "店舗什器", "スーパー", "banana hanger",
                         "banana stand", "produce"], photos=[], colors=Colors(label_base=chrome),
                   images=imgs, parts=parts, picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- 精肉・鮮魚の対面ケース


def serve_over_counter() -> Product:
    W, D = 1.80, 1.10
    deck_z, glass_top = 0.84, 1.22
    H = glass_top + 0.04
    fr = Canvas(1720, 600, None, "#1D3F6E", 4131)  # お客さま側の前板
    fr.gradient(0, 0, 1720, 600, "#24508A", "#132D52")
    fr.rect(0, 470, 1720, 482, fill="#F2C230")
    fr.text(860, 200, "鮮魚・精肉 対面コーナー", 120, "#FFFFFF", 900, max_w=1600)
    fr.text(860, 350, "お刺身・切り身・量り売り  ご希望の量でお切りします", 52, "#CFE3FF", 700, max_w=1600)
    fr.text(860, 540, "FRESH FISH & MEAT", 44, "#F2C230", 800)
    front = _face(fr.array(), "metal", 4131, 0.35, 8)
    strip = _price_strip(["398円", "298円", "198円", "698円", "258円", "498円", "128円"], 1720, 4132, 240)
    imgs = [front, strip]
    dy, dd = -0.06, 0.78  # 陳列面の中心と奥行き
    parts = [
        _box("Plinth", (W - 0.04, D - 0.10, 0.10), (0, 0.03, 0.05), "#2B2E31", "matte"),
        _box("Cabinet", (W, D - 0.06, deck_z - 0.12), (0, 0.03, 0.10 + (deck_z - 0.12) / 2), WHITE),
        _sign("FrontPanel", (W - 0.08, 0.01, 0.60), (0, -D / 2 + 0.025, 0.42), "#1D3F6E", {"front": 0}, "#C4C8CC",
              material="steel"),
        _box("Bumper", (W, 0.04, 0.05), (0, -D / 2 + 0.02, 0.76), "#9AA0A6", "metal"),
        _box("Deck", (W - 0.08, dd, 0.015), (0, dy, deck_z - 0.0075), "#E9ECEF", "metal"),
        _box("PriceRail", (W - 0.08, 0.012, 0.035), (0, dy - dd / 2 - 0.006, deck_z + 0.012), "#FFFFFF", "plastic",
             {"front": 1}, collision=False),
        _box("EndL", (0.04, dd, glass_top - deck_z), (-W / 2 + 0.02, dy, (deck_z + glass_top) / 2), GLASS, "glass"),
        _box("EndR", (0.04, dd, glass_top - deck_z), (W / 2 - 0.02, dy, (deck_z + glass_top) / 2), GLASS, "glass"),
        # 前のガラス（上ほど奥へ倒れる）と上の棚ガラス
        Part("FrontGlass", "box", [W - 0.08, 0.012, 0.40], [0, dy - dd / 2 + 0.07, deck_z + 0.19], [-20.0, 0, 0],
             color=GLASS, finish="glass", thin_walled=True),
        _box("TopRail", (W - 0.08, 0.06, 0.04), (0, -0.33, glass_top + 0.02), STAINLESS, "metal"),
        _box("TopGlass", (W - 0.08, 0.36, 0.01), (0, -0.12, glass_top + 0.035), GLASS, "glass"),
        _box("CanopyBar", (W - 0.08, 0.08, 0.04), (0, 0.10, glass_top + 0.02), STAINLESS, "metal"),
        # 店員側：奥の作業台（まな板を置く台）と腰板
        _box("WorkTop", (W, 0.20, 0.03), (0, D / 2 - 0.10, 0.92), STAINLESS, "metal"),
        _box("BackPanel", (W - 0.04, 0.02, 0.80), (0, D / 2 - 0.03, 0.50), "#DADDE0", "metal"),
    ]
    lights = []
    for k, (y, tilt) in enumerate(((-0.33, LAMP_TILT), (0.10, 0.0))):
        lamp, lux = _lamp(f"CanopyLight{k}", (W - 0.14, 0.03, 0.008), (0, y, glass_top - 0.0045), "#FFF6F0", 9000.0,
                          4000.0, tilt=tilt)
        parts.append(lamp)
        lights.append(lux)
    return Product(slug="serve_over_counter", name="対面ケース 精肉・鮮魚 1800mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=220.0, static=True, material="steel",
                   description="形はスーパーの精肉・鮮魚売場の一般的な対面式の冷蔵ショーケース（陳列面の高さ約 840 mm・"
                               "前の傾いたガラス・上の棚ガラス・内部の照明・店員側の作業台）で、寸法・質量は代表値。"
                               "陳列面は水平の板。前板の文字と値段は架空。",
                   tags=["対面ケース", "精肉", "鮮魚", "ショーケース", "冷蔵ケース", "店舗什器", "スーパー",
                         "serve-over counter", "deli case", "meat case", "fish counter", "supermarket"],
                   photos=[], colors=Colors(label_base=WHITE), images=imgs, parts=parts, lights=lights,
                   picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- 惣菜の平台ケース（保温・冷蔵）


def deli_flat_case() -> Product:
    W, D = 1.50, 0.90
    deck_z, wall_h = 0.78, 0.14
    canopy_z = 1.38
    H = canopy_z + 0.03
    fr = Canvas(1440, 480, None, "#8D3B12", 4141)
    fr.gradient(0, 0, 1440, 480, "#B5531D", "#7A300C")
    fr.rect(0, 380, 1440, 392, fill="#FFD54F")
    fr.text(720, 170, "できたて お惣菜", 120, "#FFFFFF", 900, max_w=1300)
    fr.text(360, 300, "あたたかい", 56, "#FFE0B2", 800)
    fr.text(1080, 300, "つめたい", 56, "#B3E5FC", 800)
    fr.text(720, 438, "お好きな量をパックにどうぞ", 40, "#FFFFFF", 700)
    imgs = [_face(fr.array(), "metal", 4141, 0.35, 8)]
    half = (W - 0.08) / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.10), (0, 0, 0.05), "#2B2E31", "matte"),
        _box("Cabinet", (W, D, deck_z - 0.12), (0, 0, 0.10 + (deck_z - 0.12) / 2), "#E8E2D6"),
        _sign("FrontPanel", (W - 0.06, 0.01, 0.48), (0, -D / 2 - 0.005, 0.40), "#8D3B12", {"front": 0}, "#C4C8CC",
              material="steel"),
        _box("Divider", (0.02, D - 0.08, wall_h), (0, 0, deck_z + wall_h / 2), STAINLESS, "metal"),
    ]
    for side, x, col in (("Warm", -half / 2 - 0.005, "#D9CBB4"), ("Cold", half / 2 + 0.005, "#DCE6EC")):
        parts.append(_box(f"Deck{side}", (half - 0.02, D - 0.08, 0.015), (x, 0, deck_z - 0.0075), col, "metal"))
    for name, size, center in (("WallFront", (W, 0.02, wall_h), (0, -D / 2 + 0.01, deck_z + wall_h / 2)),
                               ("WallBack", (W, 0.02, wall_h), (0, D / 2 - 0.01, deck_z + wall_h / 2)),
                               ("WallL", (0.02, D - 0.04, wall_h), (-W / 2 + 0.01, 0, deck_z + wall_h / 2)),
                               ("WallR", (0.02, D - 0.04, wall_h), (W / 2 - 0.01, 0, deck_z + wall_h / 2))):
        parts.append(_box(name, size, center, GLASS, "glass"))
    parts += [_box("RimFront", (W, 0.03, 0.02), (0, -D / 2 + 0.015, deck_z + wall_h + 0.01), STAINLESS, "metal"),
              _box("RimBack", (W, 0.03, 0.02), (0, D / 2 - 0.015, deck_z + wall_h + 0.01), STAINLESS, "metal")]
    # 奥の 2 本の支柱で上の照明の梁を支える（くしゃみ除けのガラス付き）
    post_h = canopy_z - 0.03 - (deck_z + wall_h + 0.02)
    for k, x in enumerate((-W / 2 + 0.04, W / 2 - 0.04)):
        parts.append(_box(f"Post{k}", (0.03, 0.03, post_h), (x, D / 2 - 0.05, deck_z + wall_h + 0.02 + post_h / 2),
                          STAINLESS, "metal"))
    parts += [_box("Canopy", (W, 0.30, 0.06), (0, D / 2 - 0.17, canopy_z), STAINLESS, "metal"),
              Part("SneezeGuard", "box", [W - 0.10, 0.008, 0.26], [0, D / 2 - 0.36, canopy_z - 0.16], [-25.0, 0, 0],
                   color=GLASS, finish="glass", collision=False, thin_walled=True)]
    lights = []
    for side, x, kel, col in (("Warm", -half / 2, WARM_WHITE, "#FFF3E0"), ("Cold", half / 2, COOL_WHITE, "#F4F8FF")):
        lamp, lux = _lamp(f"Lamp{side}", (half - 0.10, 0.08, 0.01), (x, D / 2 - 0.17, canopy_z - 0.035), col, 7000.0,
                          kel, tilt=-20.0)
        parts.append(lamp)
        lights.append(lux)
    return Product(slug="deli_flat_case", name="惣菜の平台ケース 保温・冷蔵 1500mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.01), mass_kg=150.0, static=True,
                   material="steel",
                   description="形はスーパーの惣菜売場の一般的な平型ケース（陳列面の高さ約 780 mm・左が保温・右が冷蔵・"
                               "低いガラスの囲い・奥の支柱で上の照明とくしゃみ除けのガラス）で、寸法・質量は代表値。"
                               "保温側は電球色、冷蔵側は昼白色の照明。前板の文字は架空。",
                   tags=["惣菜", "平台", "ショーケース", "保温ケース", "冷蔵ケース", "デリ", "店舗什器", "スーパー",
                         "deli case", "hot food case", "supermarket"], photos=[],
                   colors=Colors(label_base="#E8E2D6"), images=imgs, parts=parts, lights=lights,
                   picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- 平型冷凍ケース（両面・アイランド）


def island_freezer_double() -> Product:
    W, D = 2.00, 1.60
    deck_z, rim_z = 0.42, 0.86  # 陳列面・縁の上面
    ridge_z = 0.94  # 中央の峰の上面（ふたが峰へ向かって上がる）
    H = ridge_z
    sign = Canvas(1900, 220, None, "#1C5FA8", 4151)
    sign.gradient(0, 0, 1900, 220, "#2A78C8", "#0E3D73")
    sign.pattern(0, 0, 1900, 220, "dots", "#3B82C9", 16, 2.0)
    sign.rect(380, 30, 1520, 190, fill="#FFFFFF", radius=18)
    sign.text(950, 95, "冷凍食品 よりどり", 84, "#174C8A", 900)
    sign.text(950, 160, "FROZEN FOODS  −18℃以下で保存", 30, "#2C6FB7", 700)
    imgs = [_face(sign.array(), "plastic", 4151, 0.4, 6)]
    wall = 0.05
    wall_h = rim_z - 0.02 - deck_z
    deck_d = D / 2 - wall - 0.02  # 壁の内側から仕切り（厚さ 40 mm）まで
    parts = [
        _box("Plinth", (W - 0.06, D - 0.06, 0.10), (0, 0, 0.05), "#2B2E31", "matte"),
        _box("CabinetLower", (W, D, deck_z - 0.12), (0, 0, 0.10 + (deck_z - 0.12) / 2), WHITE),
        # 陳列面は仕切りの前後に 1 枚ずつ（1 枚だと商品を並べるツールが仕切りの上にも商品を並べ、物理で押し出される）
        _box("DeckF", (W - 2 * wall, deck_d, 0.02), (0, -0.02 - deck_d / 2, deck_z - 0.01), "#DCE3E8", "matte"),
        _box("DeckB", (W - 2 * wall, deck_d, 0.02), (0, 0.02 + deck_d / 2, deck_z - 0.01), "#DCE3E8", "matte"),
        _box("Divider", (W - 2 * wall, 0.04, 0.24), (0, 0, deck_z + 0.10), "#C9D3DA", "plastic"),  # 陳列面の間を埋める
        _box("BumperF", (W, 0.02, 0.06), (0, -D / 2 - 0.01, 0.30), "#9AA0A6", "metal", collision=False),
        _box("BumperB", (W, 0.02, 0.06), (0, D / 2 + 0.01, 0.30), "#9AA0A6", "metal", collision=False),
    ]
    for name, size, center in (("WallFront", (W, wall, wall_h), (0, -D / 2 + wall / 2, deck_z + wall_h / 2)),
                               ("WallBack", (W, wall, wall_h), (0, D / 2 - wall / 2, deck_z + wall_h / 2)),
                               ("WallL", (wall, D - 2 * wall, wall_h), (-W / 2 + wall / 2, 0, deck_z + wall_h / 2)),
                               ("WallR", (wall, D - 2 * wall, wall_h), (W / 2 - wall / 2, 0, deck_z + wall_h / 2))):
        parts.append(_box(name, size, center, WHITE))
    for side, y, face in (("Front", -D / 2 - 0.003, "front"), ("Back", D / 2 + 0.003, "back")):
        parts.append(_sign(f"Sign{side}", (W - 0.10, 0.006, 0.22), (0, y, rim_z - 0.16), "#1C5FA8", {face: 0},
                           "#F4F5F7", material="plastic"))
    parts += [_box("TopRimFront", (W, 0.04, 0.02), (0, -D / 2 + 0.02, rim_z - 0.01), "#B9BCBE", "metal"),
              _box("TopRimBack", (W, 0.04, 0.02), (0, D / 2 - 0.02, rim_z - 0.01), "#B9BCBE", "metal"),
              _box("TopRimL", (0.04, D - 0.08, 0.02), (-W / 2 + 0.02, 0, rim_z - 0.01), "#B9BCBE", "metal"),
              _box("TopRimR", (0.04, D - 0.08, 0.02), (W / 2 - 0.02, 0, rim_z - 0.01), "#B9BCBE", "metal"),
              _box("Ridge", (W, 0.06, ridge_z - deck_z - 0.22), (0, 0, deck_z + 0.22 + (ridge_z - deck_z - 0.22) / 2),
                   "#B9BCBE", "metal")]
    # ガラスの引き戸：片側 2 枚ずつ、縁から中央の峰へ上がる（水平だと棚板と見なされる）
    y_in, y_out = 0.03, D / 2 - 0.04  # 峰の脇・縁の内側
    lid_d = math.hypot(y_out - y_in, ridge_z - rim_z)
    tilt = math.degrees(math.atan2(ridge_z - rim_z, y_out - y_in))
    joints: list[Joint] = []
    lw = (W - 0.08) / 2
    for side, sy in (("F", -1), ("B", 1)):
        yc = sy * (y_in + y_out) / 2
        zc = (rim_z + ridge_z) / 2 + 0.004
        for k, x in enumerate((-lw / 2, lw / 2)):
            name = f"Lid{side}{k}"
            dz = 0.007 * k  # 右の戸を少し上に重ねる
            p = Part(name, "box", [lw - 0.01, lid_d, 0.006], [x, yc, zc + dz], [-sy * tilt, 0.0, 0.0], color=GLASS,
                     finish="glass", thin_walled=True)
            p.link = f"{name}Link"
            parts.append(p)
            lim = [0.0, 0.45] if k == 0 else [-0.45, 0.0]
            joints.append(Joint(link=p.link, anchor=[x, yc, zc + dz], limits=lim, type="prismatic", axis="X"))
    return Product(slug="island_freezer_double", name="平型冷凍ケース 両面アイランド 2000mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.02), mass_kg=260.0, static=True,
                   material="steel",
                   description="形はスーパーの冷凍食品売場の島に置く一般的な両面の平型冷凍ケース（陳列面の高さ約 420 mm・"
                               "中央の仕切りと峰・両側から開けるガラスの引き戸 4 枚・側面の案内表示）で、寸法・質量は代表値。"
                               "引き戸（Lid*Link）は X 方向に 450 mm まで動く。案内表示の文字は架空。",
                   tags=["冷凍ケース", "平型", "アイランド", "両面", "冷凍食品", "ショーケース", "店舗什器", "スーパー",
                         "island freezer", "chest freezer", "supermarket"], photos=[],
                   colors=Colors(label_base=WHITE), images=imgs, parts=parts, joints=joints,
                   picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- リーチイン冷凍庫（ガラス扉 5 枚）


def reach_in_freezer_5door() -> Product:
    n = 5
    W, D, H = 3.12, 0.86, 2.06
    frame, dark, lining, shelf_c = "#3A3D42", "#24262A", "#EEF2F5", "#C9CCD0"
    base_h, head_h = 0.12, 0.28
    inner_w = W - 0.08
    pitch = inner_w / n
    open_h = H - base_h - head_h
    zc_open = base_h + open_h / 2
    hw, hh = inner_w * 1000, 220.0
    c = Canvas(hw, hh, 3600 / hw, "#0E3D73", 4161)
    c.gradient(0, 0, hw, hh, "#2A78C8", "#0E3D73")
    for k in range(9):  # 雪の結晶の飾り
        cx = 120 + k * (hw - 240) / 8
        for a in range(3):
            ang = math.radians(a * 60)
            c.line([(cx - 24 * math.cos(ang), 40 - 24 * math.sin(ang)),
                    (cx + 24 * math.cos(ang), 40 + 24 * math.sin(ang))], "#BFE0FF", 3)
    c.text(hw / 2, 120, "冷凍食品・アイスクリーム", 84, "#FFFFFF", 900)
    c.text(hw / 2, 185, "FROZEN FOODS & ICE CREAM  −18℃以下で保存", 30, "#D6E8FA", 700)
    header = _face(c.array(), "plastic", 4161, 0.4, 6)
    fr = Canvas(560, 160, None, "#FFFFFF", 4162)  # 扉の下の霜（白いぼかし）
    fr.gradient(0, 0, 560, 160, "#F4F8FB", "#DCE7EE")
    for _ in range(120):
        x, y, r = fr.rng.uniform(0, 560), fr.rng.uniform(0, 160), fr.rng.uniform(3, 16)
        fr.ellipse(x - r, y - r, x + r, y + r, fill=mix("#FFFFFF", "#CFE0EA", fr.rng.uniform(0, 0.5)))
    frost = _face(fr.array(), "paper", 4162, 0.3, 2)
    imgs = [header, frost]
    parts: list[Part] = [
        _box("Base", (W, D - 0.06, base_h), (0, 0.03, base_h / 2), dark, "metal"),
        _box("SideLeft", (0.04, D, H), (-W / 2 + 0.02, 0, H / 2), frame, "metal"),
        _box("SideRight", (0.04, D, H), (W / 2 - 0.02, 0, H / 2), frame, "metal"),
        _box("Back", (inner_w, 0.04, H - base_h), (0, D / 2 - 0.02, base_h + (H - base_h) / 2), lining, "plastic"),
        _box("Top", (inner_w, D, head_h), (0, 0, H - head_h / 2), dark, "metal"),
        _sign("Header", (inner_w, 0.012, 0.22), (0, -D / 2 - 0.006, H - head_h / 2), "#0E3D73", {"front": 0},
              "#24262A", material="plastic"),
        _box("Floor", (inner_w, D - 0.10, 0.02), (0, 0.01, base_h + 0.01), lining, "plastic"),
    ]
    for k in range(n - 1):
        x = -inner_w / 2 + pitch * (k + 1)
        parts.append(_box(f"Mullion{k}", (0.04, 0.06, open_h), (x, -D / 2 + 0.05, zc_open), frame, "metal"))
    lights = []
    for k, x in enumerate([-inner_w / 2 + 0.012, *(-inner_w / 2 + pitch * (j + 1) for j in range(n - 1)),
                           inner_w / 2 - 0.012]):
        lamp, lux = _lamp(f"LedBar{k}", (0.02, 0.008, open_h - 0.08), (x, -D / 2 + 0.084, zc_open), "#F4F8FF",
                          20000.0, COOL_WHITE, facing="back")
        parts.append(lamp)
        lights.append(lux)
    joints: list[Joint] = []
    for d in range(n):
        x = -inner_w / 2 + pitch * (d + 0.5)
        for i in range(5):
            z = base_h + 0.28 + i * 0.27
            parts += [_box(f"Shelf{d}_{i}", (pitch - 0.03, 0.58, 0.012), (x, 0.06, z), shelf_c, "metal"),
                      _box(f"PriceRail{d}_{i}", (pitch - 0.03, 0.008, 0.035), (x, 0.06 - 0.294, z + 0.006),
                           "#FFFFFF", "plastic", collision=False)]
        dw, dh, y = pitch - 0.012, open_h - 0.02, -D / 2
        parts += [_box(f"Door{d}", (dw, 0.02, dh), (x, y, zc_open), "#EEF4F7", "glass"),
                  Part(f"Door{d}Frost", "box", [dw - 0.08, 0.002, 0.14], [x, y - 0.011, zc_open - dh / 2 + 0.14],
                       color="#F2F6F9", finish="frosted", faces={"front": 1}, collision=False, bevel=0),
                  _box(f"Door{d}StileL", (0.035, 0.026, dh), (x - dw / 2 + 0.0175, y, zc_open), dark, "metal",
                       collision=False),
                  _box(f"Door{d}StileR", (0.035, 0.026, dh), (x + dw / 2 - 0.0175, y, zc_open), dark, "metal",
                       collision=False),
                  _box(f"Door{d}RailT", (dw, 0.026, 0.05), (x, y, zc_open + dh / 2 - 0.025), dark, "metal",
                       collision=False),
                  _box(f"Door{d}RailB", (dw, 0.026, 0.07), (x, y, zc_open - dh / 2 + 0.035), dark, "metal",
                       collision=False)]
        hx = x + dw / 2 - 0.06
        parts += [_box(f"Door{d}Handle", (0.022, 0.026, 0.70), (hx, y - 0.043, zc_open), "#B8BCC0", "metal"),
                  _box(f"Door{d}HandlePostT", (0.016, 0.03, 0.016), (hx, y - 0.028, zc_open + 0.30), "#B8BCC0",
                       "metal", collision=False),
                  _box(f"Door{d}HandlePostB", (0.016, 0.03, 0.016), (hx, y - 0.028, zc_open - 0.30), "#B8BCC0",
                       "metal", collision=False)]
        link = f"Door{d}Link"
        for p in parts:
            if p.name.startswith(f"Door{d}"):
                p.link = link
        joints.append(Joint(link=link, anchor=[x - dw / 2, y - 0.01, zc_open], limits=[-100.0, 0.0]))
    return Product(slug="reach_in_freezer_5door", name="リーチイン冷凍庫 ガラス扉 5枚", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=0.916), mass_kg=520.0, static=True,
                   material="steel",
                   description="形はスーパーの冷凍食品・アイスの壁面に並ぶ一般的なガラス扉のリーチイン冷凍庫（扉 5 枚・"
                               "棚 5 段・扉の下に霜・上の看板）で、寸法・質量は代表値。扉 5 枚（Door0Link〜Door4Link）は"
                               "左端の蝶番で手前に 100° まで開く。看板の文字は架空。",
                   tags=["リーチイン", "冷凍庫", "冷凍ケース", "ガラス扉", "冷凍食品", "アイス", "店舗什器", "スーパー",
                         "reach-in freezer", "glass door freezer", "supermarket"], photos=[],
                   colors=Colors(label_base=frame), images=imgs, parts=parts, joints=joints, lights=lights,
                   picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- ゴンドラのエンドの特売の山積み台


def endcap_promo_table() -> Product:
    W, D = 0.90, 0.60
    H = 1.50
    imgs = [_pop(880, 300, "本日の特売", "お一人様 2 点まで", 4171, "#C62828", "#FFFFFF", "#FFEB3B", "plastic"),
            _pop(880, 130, "お買い得", "数量限定", 4172, "#F9A825", INK, "#FFFFFF")]
    parts = [
        _box("Base", (W, D, 0.14), (0, 0, 0.07), "#3A3D42", "matte"),
        _box("Deck", (W, D, 0.02), (0, 0, 0.15), "#D8DADC", "metal"),
        _box("UpperBase", (W, 0.28, 0.20), (0, D / 2 - 0.14, 0.26), "#3A3D42", "matte"),
        _box("UpperDeck", (W, 0.28, 0.02), (0, D / 2 - 0.14, 0.37), "#D8DADC", "metal"),
        _sign("Skirt", (W - 0.02, 0.004, 0.13), (0, -D / 2 - 0.002, 0.075), "#F9A825", {"front": 1}, "#F7F5F0"),
    ]
    for k, x in enumerate((-W / 2 + 0.03, W / 2 - 0.03)):
        parts.append(_cyl(f"Post{k}", (0.025, 0.025, H - 0.38), (x, D / 2 - 0.03, 0.38 + (H - 0.38) / 2), "#B9BEC4"))
    parts.append(_sign("PopBoard", (W - 0.02, 0.01, 0.30), (0, D / 2 - 0.06, H - 0.16), "#C62828", {"front": 0},
                       "#F7F5F0", collision=True, material="plastic"))
    return Product(slug="endcap_promo_table", name="エンドの特売の山積み台 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.004), mass_kg=28.0, static=True,
                   material="steel",
                   description="形はゴンドラ棚の端（エンド）の前に置く一般的な特売用の低い山積み台（幅 900 mm・2 段の台・"
                               "奥の支柱に POP の看板）で、寸法・質量は代表値。台は箱やケースを積む水平の板。POP の文字は架空。",
                   tags=["エンド", "特売", "山積み", "平台", "POP", "店舗什器", "スーパー", "endcap", "promo display",
                         "supermarket"], photos=[], colors=Colors(label_base="#3A3D42"), images=imgs, parts=parts,
                   picture_places=SUPER_PLACES)


# ---------------------------------------------------------------- 特売ワゴン


def promo_wagon() -> Product:
    W, D = 0.90, 0.60
    deck_z, wall_h = 0.58, 0.22
    H = 1.20
    chrome = "#C9CDD1"
    imgs = [_pop(400, 150, "特価", "よりどり 3 点 500円", 4181, "#C62828", "#FFFFFF", "#FFEB3B", "plastic")]
    parts = []
    for tag, x, y in (("FL", -W / 2 + 0.06, -D / 2 + 0.06), ("FR", W / 2 - 0.06, -D / 2 + 0.06),
                      ("BL", -W / 2 + 0.06, D / 2 - 0.06), ("BR", W / 2 - 0.06, D / 2 - 0.06)):
        parts += [_cyl(f"Caster{tag}", (0.075, 0.075, 0.075), (x, y, 0.0375), "#3A3D42", "plastic"),
                  _box(f"Leg{tag}", (0.025, 0.025, deck_z - 0.09), (x, y, 0.075 + (deck_z - 0.09) / 2), chrome,
                       "metal")]
    parts += [_box("LowerShelf", (W - 0.06, D - 0.06, 0.012), (0, 0, 0.22), "#9EA3A8", "metal"),
              _box("Deck", (W, D, 0.015), (0, 0, deck_z - 0.0075), "#B8BDC2", "metal")]
    zr = deck_z + wall_h - 0.006
    for name, size, center in (("RailFront", (W, 0.012, 0.012), (0, -D / 2 + 0.006, zr)),
                               ("RailBack", (W, 0.012, 0.012), (0, D / 2 - 0.006, zr)),
                               ("RailL", (0.012, D - 0.024, 0.012), (-W / 2 + 0.006, 0, zr)),
                               ("RailR", (0.012, D - 0.024, 0.012), (W / 2 - 0.006, 0, zr))):
        parts.append(_box(name, size, center, chrome, "metal"))
    wz = deck_z + (wall_h - 0.012) / 2
    for k in range(9):  # 網の縦の線（前後）
        x = -W / 2 + 0.006 + k * (W - 0.012) / 8
        for side, y in (("F", -D / 2 + 0.006), ("B", D / 2 - 0.006)):
            parts.append(_box(f"Wire{side}{k}", (0.005, 0.005, wall_h - 0.012), (x, y, wz), chrome, "metal",
                              collision=False))
    for k in range(1, 6):  # 網の縦の線（左右）
        y = -D / 2 + 0.006 + k * (D - 0.012) / 6
        for side, x in (("L", -W / 2 + 0.006), ("R", W / 2 - 0.006)):
            parts.append(_box(f"Wire{side}{k}", (0.005, 0.005, wall_h - 0.012), (x, y, wz), chrome, "metal",
                              collision=False))
    # 網の当たり判定：透明な薄い板（見た目はほぼ見えない）
    for name, size, center in (("GuardF", (W - 0.02, 0.004, wall_h - 0.012), (0, -D / 2 + 0.006, wz)),
                               ("GuardB", (W - 0.02, 0.004, wall_h - 0.012), (0, D / 2 - 0.006, wz)),
                               ("GuardL", (0.004, D - 0.02, wall_h - 0.012), (-W / 2 + 0.006, 0, wz)),
                               ("GuardR", (0.004, D - 0.02, wall_h - 0.012), (W / 2 - 0.006, 0, wz))):
        parts.append(Part(name, "box", list(size), list(center), color="#F4F6F8", finish="glass", thin_walled=True,
                          bevel=0))
    pole_h = H - 0.15 - deck_z - wall_h
    parts += [_cyl("PopPole", (0.016, 0.016, pole_h), (W / 2 - 0.03, D / 2 - 0.03, deck_z + wall_h + pole_h / 2),
                   chrome),
              _sign("PopCard", (0.40, 0.004, 0.15), (W / 2 - 0.23, D / 2 - 0.03, H - 0.075), "#C62828",
                    {"front": 0, "back": 0}, "#F7F5F0")]
    return Product(slug="promo_wagon", name="特売ワゴン キャスター付き", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=18.0, static=True, material="steel",
                   description="形はスーパーの通路やエンドに置く一般的な網かごの特売ワゴン（幅 900 mm・かごの底の高さ約 "
                               "580 mm・深さ 220 mm・下に棚・キャスター 4 個・POP）で、寸法・質量は代表値。シミュレーション"
                               "では動かない（static）。網は細い棒と透明な薄い板（当たり判定）で表す。POP の文字は架空。",
                   tags=["ワゴン", "特売", "網かご", "POP", "店舗什器", "スーパー", "promo wagon", "bargain bin",
                         "supermarket"], photos=[], colors=Colors(label_base=chrome), images=imgs, parts=parts,
                   picture_places=SUPER_PLACES)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    produce_flat_table, produce_tiered_stand, banana_hanger, serve_over_counter, deli_flat_case,
    island_freezer_double, reach_in_freezer_5door, endcap_promo_table, promo_wagon)}
