"""Fictional product designs: home-center and 100-yen-shop fixtures (a tall sales rack with top stock, pallets
and palletized goods, pegboard hook displays, a long-goods rack, garden stands, a platform cart, a low
100-yen gondola with bins, and hanging section signs).

As in super_fixtures.py: no real names or logos, typical sizes, front is -Y (the customer side), floor
fixtures are kinematic (static) and every surface meant for goods is a thin horizontal board so a shelf-filling tool
finds it. Stops and lips sit in front of the boards (not on them), so the fill margins stay free.
The pallets and the platform cart are movable things, so they are dynamic rigid bodies.

Pegboard hooks: hanging goods from a hook is not something fill can do (it stocks horizontal boards), and a
blister card resting on a thin rod is an unstable contact in PhysX. So the hooks are visual only
(collision off). `pegboard_gondola` keeps the hooks empty and gives a fillable base deck and low shelf;
`pegboard_wall_tools` comes with the tool packs from hc_tools already hanging on its hooks, as static visual
parts of the fixture. The same packs exist as separate dynamic products (screwdriver_blister etc.) for shelves.
POP and header signs carry shop slogans, so they can be switched to plain boards (Picture=Blank).
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .hc_tools import pliers_pack, place, screw_pack, screwdriver_pack, tape_measure_pack
from .paint import Canvas, mix, trim_safe, finish
from .products import INK, _box, _cyl, _face
from .store_more import _rod
from .super_fixtures import _pop, _sign

HC_PLACES = ["home_center", "shop"]  # where the home-center POP fits (Picture variant)
HUNDRED_PLACES = ["hundred_yen_shop", "shop"]
WHITE = "#FFFFFF"
HC_ORANGE, HC_NAVY, HC_GREEN = "#E8701A", "#1F3A5F", "#2E7D32"
STEEL, STEEL_DARK, GALV = "#8E949B", "#4A4F55", "#B9BEC4"
PALLET_WOOD, PALLET_BLUE = "#C9A877", "#1E5AA8"
KRAFT = "#C49A6C"
ENV = "environment"


def _p(name, shape, size, center, color, finish_="plastic", rot=None, faces=None, collision=True, material=None,
       **kw) -> Part:
    return Part(name=name, shape=shape, size=list(size), center=list(center), rotation=list(rot or [0, 0, 0]),
                color=color, finish=finish_, faces=faces, collision=collision, material=material, **kw)


def _steel(name, size, center, color=STEEL, faces=None, collision=True, finish_="metal") -> Part:
    return _p(name, "box", size, center, color, finish_, faces=faces, collision=collision, material="steel")


def _mesh(w_mm: float, d_mm: float, seed: int, color: str = GALV, step: float = 50.0) -> np.ndarray:
    """A wire-mesh deck seen from above (a grid of bars on a darker gap)."""
    c = Canvas(w_mm, d_mm, None, mix(color, "#000000", 0.45), seed)
    c.gradient(0, 0, w_mm, d_mm, mix(color, "#000000", 0.35), mix(color, "#000000", 0.55))
    x = step / 2
    while x < w_mm:
        c.rect(x - 2.5, 0, x + 2.5, d_mm, fill=color)
        x += step
    y = step / 2
    while y < d_mm:
        c.rect(0, y - 2.5, w_mm, y + 2.5, fill=mix(color, WHITE, 0.15))
        y += step
    return _face(c.array(), "plastic", seed, 0.5, 4)


def _holes(w_mm: float, h_mm: float, seed: int, color: str = "#D8D4CC", pitch: float = 25.0) -> np.ndarray:
    """A pegboard: holes on a 25 mm grid."""
    c = Canvas(w_mm, h_mm, None, color, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(color, WHITE, 0.08), mix(color, "#000000", 0.06))
    y = 0.0  # holes on the edges are cut in half (so the border is not one colour)
    while y < h_mm + 3:
        x = 0.0
        while x < w_mm + 3:
            c.ellipse(x - 3, y - 3, x + 3, y + 3, fill=mix(color, "#000000", 0.6))
            x += pitch
        y += pitch
    return _face(c.array(), "paper", seed, 0.4, 4)


def _slats(w_mm: float, d_mm: float, seed: int, color: str = PALLET_WOOD, n: int = 7) -> np.ndarray:
    """The top deck of a wooden pallet: n boards along X with gaps between them."""
    c = Canvas(w_mm, d_mm, None, mix(color, "#000000", 0.55), seed)
    gap = 30.0
    bw = (d_mm - gap * (n - 1)) / n
    for k in range(n):
        y0 = k * (bw + gap)
        base = mix(color, c.rng.choice(["#E2C79C", "#B08A58", "#D2B080"]), c.rng.uniform(0.2, 0.6))
        c.gradient(0, y0, w_mm, y0 + bw, mix(base, WHITE, 0.08), mix(base, "#000000", 0.08))
        for _ in range(10):
            y = c.rng.uniform(y0 + 3, y0 + bw - 3)
            c.line([(0, y), (w_mm * 0.5, y + c.rng.uniform(-2, 2)), (w_mm, y + c.rng.uniform(-3, 3))],
                   mix(base, "#6B4A2A", c.rng.uniform(0.15, 0.35)), c.rng.uniform(0.5, 1.4))
        for x in (40.0, w_mm / 2, w_mm - 40.0):  # nail heads over the stringers
            for dy in (bw * 0.3, bw * 0.7):
                c.ellipse(x - 3, y0 + dy - 3, x + 3, y0 + dy + 3, fill="#5A5F66")
    return _face(c.array(), "paper", seed, 0.6, 6)


def _wood_side(w_mm: float, h_mm: float, seed: int, color: str = PALLET_WOOD) -> np.ndarray:
    c = Canvas(w_mm, h_mm, None, color, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(color, WHITE, 0.08), mix(color, "#000000", 0.12))
    for _ in range(int(h_mm / 6) + 2):
        y = c.rng.uniform(0, h_mm)
        c.line([(0, y), (w_mm, y + c.rng.uniform(-3, 3))], mix(color, "#6B4A2A", c.rng.uniform(0.15, 0.4)),
               c.rng.uniform(0.4, 1.2))
    return _face(c.array(), "paper", seed, 0.6, 6)


# ---------------------------------------------------------------- pallets


def _wood_pallet_parts(k: int) -> list[Part]:
    """A JIS T11 (1100 x 1100 x 144 mm) wooden pallet: bottom boards along Y, three stringers along X, a top
    deck drawn as slats. Face indices: k = deck top, k + 1 = stringer side."""
    parts = []
    for i, x in enumerate((-0.50, 0.0, 0.50)):
        parts.append(_p(f"Bottom{i}", "box", (0.10, 1.10, 0.022), (x, 0, 0.011), PALLET_WOOD, "matte",
                        material="wood"))
    for i, y in enumerate((-0.50, 0.0, 0.50)):
        parts.append(_p(f"Stringer{i}", "box", (1.10, 0.10, 0.10), (0, y, 0.072), PALLET_WOOD, "matte",
                        faces={"front": k + 1, "back": k + 1}, material="wood"))
    parts.append(_p("Deck", "box", (1.10, 1.10, 0.022), (0, 0, 0.133), PALLET_WOOD, "matte", faces={"top": k},
                    material="wood"))
    return parts


def _wood_pallet_images(seed: int) -> list[np.ndarray]:
    return [_slats(1100, 1100, seed), _wood_side(1100, 100, seed + 1)]


def wood_pallet() -> Product:
    return Product(slug="wood_pallet", name="木製パレット 1100×1100（T11 型）", shape_class="assembly",
                   category="fixture", dims=Dimensions(0.144, 1.10, depth=1.10), mass_kg=25.0, material="wood",
                   description="形は一般的な木製の平パレット（JIS の T11 型 1100 × 1100 × 144 mm、桁 3 本・下板 3 枚）で、"
                               "寸法・質量は代表値。上面の板（すのこ）は 1 枚の板に絵で描く（商品を並べる棚板として使える）。"
                               "床に置いて動かせる物なので動く剛体。",
                   tags=["パレット", "木製パレット", "T11", "平パレット", "物流", "倉庫", "ホームセンター", "pallet",
                         "wooden pallet", "wood pallet"],
                   photos=[], colors=Colors(label_base=PALLET_WOOD), images=_wood_pallet_images(4401),
                   parts=_wood_pallet_parts(0))


def _grid_top(w_mm: float, d_mm: float, seed: int, color: str = PALLET_BLUE) -> np.ndarray:
    c = Canvas(w_mm, d_mm, None, color, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(color, WHITE, 0.1), mix(color, "#000000", 0.12))
    for x in np.arange(0, w_mm, 40.0):  # ribs along the moulded rim
        for y0, y1 in ((0, 12), (d_mm - 12, d_mm)):
            c.rect(x, y0, x + 20, y1, fill=mix(color, "#000000", 0.35))
    for y in np.arange(0, d_mm, 40.0):
        for x0, x1 in ((0, 12), (w_mm - 12, w_mm)):
            c.rect(x0, y, x1, y + 20, fill=mix(color, "#000000", 0.35))
    step = 55.0
    x = step
    while x < w_mm - 20:
        y = step
        while y < d_mm - 20:
            c.rect(x - 18, y - 18, x + 18, y + 18, fill=mix(color, "#000000", 0.35), radius=4)
            y += step
        x += step
    return _face(c.array(), "plastic", seed, 0.4, 6)


def plastic_pallet() -> Product:
    """A 1100 x 1100 plastic pallet on nine feet (the deck's grid of holes is drawn)."""
    blue = PALLET_BLUE
    parts = [_p("Deck", "box", (1.10, 1.10, 0.035), (0, 0, 0.1325), blue, "plastic", faces={"top": 0}, bevel=0.01,
                material="plastic")]
    for i, x in enumerate((-0.47, 0.0, 0.47)):
        for j, y in enumerate((-0.47, 0.0, 0.47)):
            parts.append(_p(f"Foot{i}{j}", "box", (0.14, 0.14, 0.095), (x, y, 0.0675), blue, "plastic", bevel=0.01,
                            material="plastic"))
    for i, x in enumerate((-0.47, 0.0, 0.47)):
        parts.append(_p(f"Runner{i}", "box", (0.10, 1.08, 0.02), (x, 0, 0.01), mix(blue, "#000000", 0.1), "plastic",
                        material="plastic"))
    return Product(slug="plastic_pallet", name="プラスチックパレット 1100×1100", shape_class="assembly",
                   category="fixture", dims=Dimensions(0.15, 1.10, depth=1.10), mass_kg=18.0, material="plastic",
                   description="形は一般的な樹脂の平パレット（1100 × 1100 × 150 mm、脚 9 本・下に滑り材 3 本）で、寸法・質量は代表値。"
                               "上面の格子の穴は絵で描く（商品を並べる棚板として使える）。床に置いて動かせる物なので動く剛体。",
                   tags=["パレット", "プラスチックパレット", "樹脂パレット", "物流", "倉庫", "ホームセンター", "pallet",
                         "plastic pallet"],
                   photos=[], colors=Colors(label_base=blue), images=[_grid_top(1100, 1100, 4411)], parts=parts)


def _bag_top(w_mm: float, d_mm: float, seed: int) -> np.ndarray:
    """A bag of potting soil lying flat, seen from above (the same print as soil_bag, simplified)."""
    green = "#2E6B2E"
    c = Canvas(w_mm, d_mm, None, "#F4EFE2", seed)
    c.gradient(0, 0, w_mm, d_mm, "#FAF6EC", "#E2D7BF")
    long_x = w_mm >= d_mm
    if long_x:
        c.rect(0, 0, w_mm * 0.30, d_mm, fill=green)
        c.text(w_mm * 0.15, d_mm / 2, "培養土", w_mm * 0.07, WHITE, 900, max_w=w_mm * 0.28)
        c.text(w_mm * 0.64, d_mm * 0.36, "花と野菜の培養土", d_mm * 0.11, green, 900, max_w=w_mm * 0.62)
        c.rect(w_mm * 0.38, d_mm * 0.52, w_mm * 0.90, d_mm * 0.78, fill="#C62828", radius=8)
        c.text(w_mm * 0.64, d_mm * 0.65, "14L  元肥入り", d_mm * 0.10, WHITE, 900, max_w=w_mm * 0.5)
    else:
        c.rect(0, 0, w_mm, d_mm * 0.30, fill=green)
        c.text(w_mm / 2, d_mm * 0.15, "培養土", d_mm * 0.12, WHITE, 900, max_w=w_mm * 0.9)
        c.text(w_mm / 2, d_mm * 0.45, "花と野菜の培養土", w_mm * 0.08, green, 900, max_w=w_mm * 0.9)
        c.rect(w_mm * 0.12, d_mm * 0.58, w_mm * 0.88, d_mm * 0.78, fill="#C62828", radius=8)
        c.text(w_mm / 2, d_mm * 0.68, "14L  元肥入り", w_mm * 0.08, WHITE, 900, max_w=w_mm * 0.7)
    return finish(trim_safe(c.array()), "film", seed, 0.8)


def _bag_side(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    c = Canvas(w_mm, h_mm, None, "#EFE8D6", seed)
    c.gradient(0, 0, w_mm, h_mm, "#F6F0E2", "#D9CDB2")
    c.rect(0, h_mm * 0.35, w_mm, h_mm * 0.65, fill="#2E6B2E")
    c.text(w_mm / 2, h_mm / 2, "培養土 14L", h_mm * 0.22, WHITE, 900, max_w=w_mm * 0.9)
    return _face(c.array(), "film", seed, 0.6, 6)


def pallet_soil_stack() -> Product:
    """Bags of potting soil stacked six high on a wooden pallet, with a price POP on the front."""
    bl, bw, bh, layers = 0.55, 0.36, 0.10, 6
    imgs = [*_wood_pallet_images(4421), _bag_top(550, 360, 4423), _bag_top(360, 550, 4424),
            _bag_side(550, 100, 4425), _bag_side(360, 100, 4426),
            _pop(600, 220, "培養土 14L", "よりどり 3 袋 1,280円", 4427, HC_GREEN, WHITE, "#FFD54F")]
    parts = _wood_pallet_parts(0)
    for layer in range(layers):
        z = 0.144 + bh * layer + bh / 2
        if layer % 2 == 0:  # 2 along X x 3 along Y
            cells = [((i - 0.5) * bl, (j - 1) * bw) for i in range(2) for j in range(3)]
            size, top, side, end = (bl - 0.004, bw - 0.004, bh), 2, 4, 5
        else:  # 3 along X x 2 along Y
            cells = [((i - 1) * bw, (j - 0.5) * bl) for i in range(3) for j in range(2)]
            size, top, side, end = (bw - 0.004, bl - 0.004, bh), 3, 5, 4
        for n, (x, y) in enumerate(cells):
            parts.append(_p(f"Bag{layer}_{n}", "box", size, (x, y, z), "#EFE8D6", "plastic",
                            faces={"top": top, "front": side, "back": side, "left": end, "right": end},
                            bevel=0.03, material="plastic"))
    H = 0.144 + bh * layers
    parts.append(_sign("Pop", (0.60, 0.004, 0.22), (0, -0.552, 0.40), HC_GREEN, {"front": 6}, "#F7F5F0"))
    return Product(slug="pallet_soil_stack", name="培養土の袋のパレット積み（6 段）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), 1.10, depth=1.104), mass_kg=280.0, static=True,
                   material="plastic",
                   description="形はホームセンターの園芸売場や入口に置く一般的な、木製パレット（T11）に培養土の袋（約 550 × 360 × "
                               "100 mm）を 1 段 6 袋・6 段の煉瓦積みにした山で、寸法・質量は代表値。袋は角の丸い箱で表し、"
                               "全体を 1 つの動かない物（static）にする。前面に POP（文字は架空）。",
                   tags=["パレット", "培養土", "土", "山積み", "園芸", "ガーデニング", "店舗什器", "ホームセンター",
                         "palletized goods", "soil bags", "pallet stack", "home center"],
                   photos=[], colors=Colors(label_base="#EFE8D6"), images=imgs, parts=parts,
                   picture_places=HC_PLACES)


def _carton(w_mm: float, h_mm: float, seed: int, title: str, sub: str) -> np.ndarray:
    c = Canvas(w_mm, h_mm, None, KRAFT, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(KRAFT, WHITE, 0.08), mix(KRAFT, "#000000", 0.1))
    c.rect(0, h_mm * 0.46, w_mm, h_mm * 0.54, fill="#B88B5C")  # tape band
    c.text(w_mm / 2, h_mm * 0.22, title, h_mm * 0.13, HC_NAVY, 900, max_w=w_mm * 0.86)
    c.text(w_mm / 2, h_mm * 0.72, sub, h_mm * 0.08, HC_NAVY, 800, max_w=w_mm * 0.86)
    for k, x in enumerate((w_mm * 0.12, w_mm * 0.88)):  # handling marks
        c.rect(x - 14, h_mm * 0.84, x + 14, h_mm * 0.94, outline=HC_NAVY, width=2)
        c.line([(x, h_mm * 0.92), (x, h_mm * 0.86)], HC_NAVY, 2)
    return _face(c.array(), "paper", seed, 0.7, 6)


def pallet_carton_stack() -> Product:
    """Cartons of storage cases stacked three high on a plastic pallet, with a POP."""
    cw, ch, layers = 0.54, 0.35, 3
    imgs = [_grid_top(1100, 1100, 4431), _carton(540, 350, 4432, "収納ケース", "深型 45L × 4 個入"),
            _carton(540, 540, 4433, "天地無用", "この面を上に"),
            _pop(600, 220, "まとめ買い", "収納ケース 4 個 4,980円", 4434, HC_NAVY, WHITE, "#FFD54F")]
    parts = [_p("Deck", "box", (1.10, 1.10, 0.035), (0, 0, 0.1325), PALLET_BLUE, "plastic", faces={"top": 0},
                material="plastic")]
    for i, x in enumerate((-0.47, 0.0, 0.47)):
        for j, y in enumerate((-0.47, 0.0, 0.47)):
            parts.append(_p(f"Foot{i}{j}", "box", (0.14, 0.14, 0.115), (x, y, 0.0575), PALLET_BLUE, "plastic",
                            material="plastic"))
    for layer in range(layers):
        z = 0.15 + ch * layer + ch / 2
        for i in range(2):
            for j in range(2):
                parts.append(_p(f"Carton{layer}{i}{j}", "box", (cw, cw, ch - 0.002),
                                ((i - 0.5) * (cw + 0.01), (j - 0.5) * (cw + 0.01), z), KRAFT, "matte",
                                faces={"front": 1, "back": 1, "left": 1, "right": 1, "top": 2},
                                material="cardboard"))
    H = 0.15 + ch * layers
    parts.append(_sign("Pop", (0.60, 0.004, 0.22), (0, -0.552, 0.50), HC_NAVY, {"front": 3}, "#F7F5F0"))
    return Product(slug="pallet_carton_stack", name="段ボールケースのパレット積み（3 段）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), 1.10, depth=1.104), mass_kg=95.0, static=True,
                   material="cardboard",
                   description="形はホームセンターの通路やエンドに置く一般的な、樹脂パレットに段ボールケース（540 × 540 × 350 mm）を"
                               "1 段 4 箱・3 段に積んだ山で、寸法・質量は代表値。全体を 1 つの動かない物（static）にする。"
                               "前面に POP（文字は架空）。",
                   tags=["パレット", "段ボール", "ケース", "山積み", "まとめ買い", "店舗什器", "ホームセンター",
                         "palletized goods", "carton stack", "pallet stack", "home center"],
                   photos=[], colors=Colors(label_base=KRAFT), images=imgs, parts=parts, picture_places=HC_PLACES)


# ---------------------------------------------------------------- tall sales rack


def hc_tall_rack() -> Product:
    """A 2.4 m steel sales rack: four fillable decks for the customer and boxed stock on top."""
    W, D, H_top = 1.80, 0.60, 2.02
    post, deck_w = 0.06, 1.68
    deck_d, y_front = 0.55, -0.26  # decks span y -0.26 .. 0.29; the beam is in front of them
    decks = [0.12, 0.62, 1.12, 1.62, H_top]
    carton_h = 0.36
    H = H_top + carton_h
    imgs = [_carton(580, 360, 4441, "在庫", "収納用品  ケース入"),
            _pop(1600, 100, "大型商品・まとめ買い", "お持ち帰りはレジ横のカートをご利用ください", 4442, HC_ORANGE, WHITE,
                 "#FFFFFF")]
    parts = []
    for i, x in enumerate((-W / 2 + post / 2, W / 2 - post / 2)):  # uprights (front and back post + braces)
        for j, y in enumerate((-D / 2 + 0.02 + post / 2, D / 2 - post / 2)):
            parts.append(_steel(f"Post{i}{j}", (post, post, H_top), (x, y, H_top / 2), HC_NAVY, finish_="plastic"))
        for k, z in enumerate((0.30, 1.00, 1.70)):
            parts.append(_steel(f"Brace{i}{k}", (0.03, D - 0.14, 0.03), (x, 0.01, z), HC_NAVY, finish_="plastic"))
    for k, z in enumerate(decks):
        parts.append(_steel(f"Deck{k}", (deck_w, deck_d, 0.02), (0, y_front + deck_d / 2, z - 0.01), GALV))
        parts.append(_steel(f"Beam{k}", (deck_w, 0.04, 0.10), (0, -D / 2 + 0.02, z - 0.05), HC_ORANGE,
                            finish_="plastic"))
        parts.append(_steel(f"BeamBack{k}", (deck_w, 0.04, 0.08), (0, D / 2 - 0.03, z - 0.06), HC_ORANGE,
                            finish_="plastic"))
    parts.append(_p("BackMesh", "box", (deck_w, 0.004, H_top - 0.12), (0, D / 2 - 0.008, 0.12 + (H_top - 0.12) / 2),
                    GALV, "metal", faces=None, material="steel", thin_walled=True))
    for i in range(3):  # boxed stock on the top deck (buries it, so fill skips the top)
        parts.append(_p(f"Stock{i}", "box", (0.56, 0.54, carton_h), ((i - 1) * 0.57, y_front + deck_d / 2,
                                                                       H_top + carton_h / 2), KRAFT, "matte",
                        faces={"front": 0, "back": 0}, material="cardboard", show={"TopStock": ["Boxes"]}))
    parts.append(_sign("Pop", (1.60, 0.004, 0.10), (0, -D / 2 - 0.002, decks[-1] - 0.05), HC_ORANGE, {"front": 1},
                       "#F7F5F0"))
    return Product(slug="hc_tall_rack", name="ホームセンターの高層ラック 1800mm（上段ストック）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D + 0.004), mass_kg=120.0, static=True,
                   material="steel",
                   description="形はホームセンターの売場の一般的な高いスチールラック（幅 1800 × 奥行き 600、高さ約 2.4 m。床から "
                               "120・620・1120・1620 mm の 4 段が売場、2020 mm の最上段に段ボールの在庫）で、寸法・質量は代表値。"
                               "棚板は奥行き 550 mm の水平の板で、前のオレンジの梁は板の手前（商品を並べる邪魔をしない）。"
                               "最上段は在庫の箱で埋まっているので 商品を並べる面にならない。TopStock バリアントで在庫の箱を"
                               "消せる（Boxes＝既定 / None＝空の最上段。売場の見通しを良くするとき）。POP の文字は架空。",
                   tags=["ラック", "高層ラック", "スチールラック", "重量棚", "在庫", "店舗什器", "ホームセンター",
                         "tall rack", "warehouse shelving", "store rack", "home center"],
                   photos=[], colors=Colors(label_base=HC_NAVY), images=imgs, parts=parts, picture_places=HC_PLACES,
                   variant_sets={"TopStock": ["Boxes", "None"]})


# ---------------------------------------------------------------- pegboard


def _pegboard_parts(W: float, D: float, H: float, k_holes: int, k_header: int, hooks: list[tuple[float, float]],
                    ) -> tuple[list[Part], float]:
    """A single-sided pegboard gondola. Returns the parts and the y of the pegboard's front face."""
    base_h, board_t = 0.10, 0.018
    yb = D / 2 - 0.03 - board_t  # pegboard front face
    parts = [_steel("Plinth", (W, D - 0.04, base_h), (0, 0.02, base_h / 2), STEEL_DARK, finish_="plastic"),
             _steel("Kick", (W, 0.02, base_h), (0, -D / 2 + 0.01, base_h / 2), STEEL_DARK, finish_="plastic"),
             _steel("BaseDeck", (W - 0.04, yb + D / 2 - 0.02, 0.02), (0, (yb - D / 2 + 0.02) / 2, base_h + 0.01),
                    GALV),
             _steel("BackFrame", (W, 0.03, H - base_h), (0, D / 2 - 0.015, base_h + (H - base_h) / 2), STEEL_DARK,
                    finish_="plastic"),
             _p("Pegboard", "box", (W - 0.04, board_t, H - base_h - 0.22), (0, yb + board_t / 2,
                                                                          base_h + (H - base_h - 0.22) / 2 + 0.02),
                "#D8D4CC", "matte", faces={"front": k_holes}, material="wood")]
    # a low shelf (0.36 deep) on brackets; the hooks start above the space its goods need
    sd = 0.36
    parts += [_steel("LowShelf", (W - 0.04, sd, 0.02), (0, yb - sd / 2, 0.41), GALV),
              _steel("LowLip", (W - 0.04, 0.012, 0.05), (0, yb - sd - 0.006, 0.415), GALV)]
    for i, x in enumerate((-W / 2 + 0.05, W / 2 - 0.05)):
        parts.append(_steel(f"Bracket{i}", (0.012, sd, 0.04), (x, yb - sd / 2, 0.38), STEEL_DARK))
    for n, (x, z) in enumerate(hooks):  # visual hooks (collision off, see the module docstring)
        parts += [_rod(f"Hook{n}", (x, yb, z), (x, yb - 0.25, z), 0.005, "#C9CDD1"),
                  _rod(f"HookTip{n}", (x, yb - 0.25, z), (x, yb - 0.25, z + 0.025), 0.005, "#C9CDD1")]
    parts.append(_sign("Header", (W - 0.04, 0.012, 0.18), (0, yb - 0.006, H - 0.10), HC_ORANGE, {"front": k_header},
                       "#F7F5F0", collision=True, material="plastic"))
    return parts, yb


def _hook_grid(W: float, rows: tuple[float, ...], cols: int) -> list[tuple[float, float]]:
    xs = [-W / 2 + (W / cols) * (i + 0.5) for i in range(cols)]
    return [(x, z) for z in rows for x in xs]


def pegboard_gondola() -> Product:
    W, D, H = 0.90, 0.60, 1.80
    rows = (1.00, 1.25, 1.50)
    imgs = [_holes(860, 1480, 4451), _pop(860, 180, "金物・工具", "必要な分だけ選べます", 4452, HC_ORANGE, WHITE, "#FFFFFF")]
    parts, _ = _pegboard_parts(W, D, H, 0, 1, _hook_grid(W, rows, 3))
    return Product(slug="pegboard_gondola", name="有孔ボードのフック陳列ゴンドラ 900mm（片面）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=45.0, static=True, material="steel",
                   description="形はホームセンター・100 円ショップの一般的な片面の有孔ボード（穴のピッチ 25 mm）のゴンドラ（幅 900 × "
                               "奥行き 600 × 高さ 1800 mm、下に台と低い棚、上の 3 段 × 3 列にフック、頭に POP）で、寸法・質量は代表値。"
                               "フックは見た目だけ（当たり判定なし）で、吊った商品は 商品を並べる面にならない。商品は下の台（床から 120 mm）"
                               "と低い棚（420 mm）に 並べる。フックに商品を吊った版は pegboard_wall_tools。POP の文字は架空。",
                   tags=["有孔ボード", "ペグボード", "フック", "ゴンドラ", "金物", "工具", "店舗什器", "ホームセンター",
                         "100円ショップ", "pegboard", "pegboard display", "hook display", "home center"],
                   photos=[], colors=Colors(label_base=STEEL_DARK), images=imgs, parts=parts,
                   picture_places=HC_PLACES)


def pegboard_wall_tools() -> Product:
    """The pegboard gondola with hand-tool packs hanging on its hooks (static, visual)."""
    W, D, H = 0.90, 0.60, 1.80
    rows = (1.00, 1.25, 1.50)
    hooks = _hook_grid(W, rows, 3)
    imgs = [_holes(860, 1480, 4461), _pop(860, 180, "手道具", "ドライバー・ペンチ・メジャー", 4462, HC_NAVY, WHITE, "#FFD54F")]
    parts, yb = _pegboard_parts(W, D, H, 0, 1, hooks)
    packs = {}
    for name, f in (("sd", screwdriver_pack), ("pl", pliers_pack), ("tm", tape_measure_pack), ("sc", screw_pack)):
        p = f()
        packs[name] = (p, len(imgs))
        imgs += p.images
    plan = {1.50: ("sd", "sd", "sd"), 1.25: ("pl", "pl", "pl"), 1.00: ("tm", "sc", "sc")}
    for n, (x, z) in enumerate(hooks):
        key = plan[z][n % 3]
        pack, k = packs[key]
        for m, dy in enumerate((0.045, 0.11, 0.175)):  # three packs on each hook, front to back
            parts += place(pack, f"{key}{n}_{m}_", x, yb - dy, z + 0.012 - pack.size[2], k, collision=False)
    return Product(slug="pegboard_wall_tools", name="有孔ボードの工具売場 900mm（フックに商品付き）",
                   shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=52.0,
                   static=True, material="steel",
                   description="形は pegboard_gondola と同じ有孔ボードのゴンドラに、ドライバー・ペンチ・コンベックス・木ねじの"
                               "ブリスターパック（hc_tools と同じ絵）をフック 1 本に 3 個ずつ吊ったもので、寸法・質量は代表値。"
                               "吊った商品は什器の一部（見た目だけ・当たり判定なし・動かない）。下の台と低い棚は 商品を並べられる。"
                               "POP の文字は架空。",
                   tags=["有孔ボード", "ペグボード", "フック", "工具", "手道具", "ドライバー", "ペンチ", "店舗什器",
                         "ホームセンター", "pegboard", "tool display", "hook display", "home center"],
                   photos=[], colors=Colors(label_base=STEEL_DARK), images=imgs, parts=parts,
                   picture_places=HC_PLACES)


# ---------------------------------------------------------------- long goods


def long_goods_rack() -> Product:
    """A cantilever rack for lumber and pipes: columns at the back, four decks on arms, stops in front."""
    W, D, H = 2.00, 0.60, 1.62
    deck_w, deck_d = 1.96, 0.50
    y0 = -D / 2 + 0.02  # deck front edge (the stop is in front of it)
    decks = (0.15, 0.55, 0.95, 1.35)
    imgs = [_pop(1900, 120, "木材・パイプ", "カットサービス承ります（1 カット 50円）", 4471, HC_GREEN, WHITE, "#FFFFFF")]
    parts = []
    for i, x in enumerate((-0.85, 0.0, 0.85)):
        parts += [_steel(f"Column{i}", (0.08, 0.06, H - 0.12), (x, D / 2 - 0.03, (H - 0.12) / 2), HC_NAVY,
                         finish_="plastic"),
                  _steel(f"Foot{i}", (0.08, D - 0.06, 0.04), (x, 0.0, 0.02), HC_NAVY, finish_="plastic")]
        for k, z in enumerate(decks):
            # the arm runs from the deck front back to the column face (y = D / 2 - 0.06)
            arm_d = D / 2 - 0.06 - y0
            parts.append(_steel(f"Arm{i}{k}", (0.05, arm_d, 0.05), (x, y0 + arm_d / 2, z - 0.045), HC_NAVY,
                                finish_="plastic"))
    for k, z in enumerate(decks):
        parts += [_steel(f"Deck{k}", (deck_w, deck_d, 0.02), (0, y0 + deck_d / 2, z - 0.01), GALV),
                  _steel(f"Stop{k}", (deck_w, 0.02, 0.07), (0, y0 - 0.01, z + 0.015), HC_ORANGE, finish_="plastic")]
    parts.append(_sign("Header", (1.90, 0.01, 0.12), (0, D / 2 - 0.065, H - 0.06), HC_GREEN, {"front": 0}, "#F7F5F0",
                       collision=True, material="plastic"))
    return Product(slug="long_goods_rack", name="長尺物ラック 2000mm（木材・パイプ）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=85.0, static=True, material="steel",
                   description="形はホームセンターの資材売場の一般的な片持ちの長尺物ラック（幅 2000 × 奥行き 600、腕に載る 4 段の"
                               "棚板 150・550・950・1350 mm、前にオレンジの止め）で、寸法・質量は代表値。木材・塩ビ管を長さ方向（X）に"
                               "寝かせて 並べる。止めは棚板の手前にある。看板の文字は架空。",
                   tags=["長尺物", "木材", "角材", "パイプ", "片持ちラック", "資材", "店舗什器", "ホームセンター",
                         "lumber rack", "cantilever rack", "long goods rack", "home center"],
                   photos=[], colors=Colors(label_base=HC_NAVY), images=imgs, parts=parts, picture_places=HC_PLACES)


# ---------------------------------------------------------------- garden


def garden_tiered_stand() -> Product:
    """A three-step steel stand for plant pots (each step a mesh deck)."""
    W, D = 1.50, 0.90
    steps = [(0.30, 0.30), (0.55, 0.30), (0.80, 0.28)]  # the sign stands behind the last step
    sign_h = 0.26
    H = steps[-1][0] + 0.06 + sign_h + 0.04
    imgs = [_mesh(1500, 300, 4481), _pop(1400, 260, "季節の花苗", "よりどり 5 ポット 498円", 4482, HC_GREEN, WHITE,
                                        "#FFD54F")]
    parts = []
    y = -D / 2
    for k, (z, d) in enumerate(steps):
        yc = y + d / 2
        parts += [_steel(f"Step{k}", (W, d, 0.02), (0, yc, z - 0.01), GALV, faces={"top": 0}),
                  _steel(f"Riser{k}", (W, 0.03, z - 0.02), (0, y + d - 0.015, (z - 0.02) / 2), HC_GREEN,
                         finish_="plastic")]
        for i, x in enumerate((-W / 2 + 0.02, 0.0, W / 2 - 0.02)):
            parts.append(_steel(f"Leg{k}{i}", (0.03, 0.03, z - 0.02), (x, y + 0.015, (z - 0.02) / 2), HC_GREEN,
                                finish_="plastic"))
        y += d
    top = steps[-1][0]
    for k, x in enumerate((-W / 2 + 0.05, W / 2 - 0.05)):
        parts.append(_cyl(f"SignPost{k}", (0.025, 0.025, H - top), (x, D / 2 - 0.013, top + (H - top) / 2), HC_GREEN,
                          "plastic"))
    parts.append(_sign("SignBoard", (W - 0.14, 0.01, sign_h), (0, D / 2 - 0.013, H - 0.02 - sign_h / 2), HC_GREEN,
                       {"front": 1}, "#F7F5F0", collision=True, material="plastic"))
    for p in parts:
        p.material = p.material or "steel"
    return Product(slug="garden_tiered_stand", name="園芸のひな壇 3段 1500mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=40.0, static=True,
                   material="steel",
                   description="形はホームセンターの園芸売場の一般的なスチールのひな壇（幅 1500 × 奥行き 900、奥ほど高い 3 段 300・550・"
                               "800 mm、各段は網の水平の板、奥に看板）で、寸法・質量は代表値。花苗・鉢を 並べる。看板の文字は架空。",
                   tags=["ひな壇", "段台", "園芸", "花苗", "鉢", "ガーデニング", "店舗什器", "ホームセンター",
                         "tiered plant stand", "garden display", "plant stand", "home center"],
                   photos=[], colors=Colors(label_base=HC_GREEN), images=imgs, parts=parts, picture_places=HC_PLACES)


def garden_outdoor_shelf() -> Product:
    """A galvanized outdoor shelf with four mesh levels (the top one is open)."""
    W, D, H = 1.80, 0.60, 1.47
    levels = (0.25, 0.65, 1.05, 1.45)
    post = 0.04
    bw = W - 2 * post
    imgs = [_mesh(1720, 580, 4491), _pop(1600, 100, "園芸用品", "屋外でも錆びにくい溶融亜鉛めっき棚", 4492, HC_GREEN, WHITE,
                                        "#FFFFFF")]
    parts = []
    for i, x in enumerate((-W / 2 + post / 2, W / 2 - post / 2)):
        for j, y in enumerate((-D / 2 + post / 2 + 0.004, D / 2 - post / 2)):
            parts.append(_steel(f"Post{i}{j}", (post, post, H), (x, y, H / 2), GALV))
    for k, z in enumerate(levels):
        parts += [_steel(f"Level{k}", (bw, D - 0.024, 0.02), (0, 0.006, z - 0.01), GALV, faces={"top": 0}),
                  _steel(f"Rail{k}", (bw, 0.01, 0.04), (0, -D / 2 + 0.007, z - 0.03), GALV)]  # just in front
    parts.append(_sign("Pop", (1.60, 0.004, 0.10), (0, -D / 2 + 0.002, levels[0] - 0.08), HC_GREEN, {"front": 1},
                       "#F7F5F0"))
    return Product(slug="garden_outdoor_shelf", name="屋外用の園芸棚 1800mm 4段", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=48.0, static=True, material="steel",
                   description="形はホームセンターの屋外の園芸売場の一般的な亜鉛めっきの網棚（幅 1800 × 奥行き 600 × 高さ約 1470 mm、"
                               "網の段 250・650・1050・1450 mm）で、寸法・質量は代表値。各段は水平の板（網は絵）で 鉢・土・"
                               "じょうろ等を並べる。POP の文字は架空。",
                   tags=["園芸棚", "網棚", "屋外", "園芸", "ガーデニング", "店舗什器", "ホームセンター", "garden shelf",
                         "outdoor shelf", "wire shelf", "home center"],
                   photos=[], colors=Colors(label_base=GALV), images=imgs, parts=parts, picture_places=HC_PLACES)


# ---------------------------------------------------------------- platform cart


def platform_cart() -> Product:
    """A flat platform hand cart (deck 900 x 600) with a fixed handle at +X and four casters."""
    W, D = 0.90, 0.60
    deck_z = 0.17
    handle_h = 0.86
    deck_w = W - 0.03
    c = Canvas(870, 600, None, "#2F3236", 4501)
    c.gradient(0, 0, 870, 600, "#3A3D42", "#26282C")
    c.pattern(0, 0, 870, 600, "stripes", "#4A4E54", 24, 3)
    c.text(435, 300, "店内用  最大積載 150kg", 34, "#6A6E74", 800)
    imgs = [_face(c.array(), "plastic", 4501, 0.5, 6)]
    parts = [_steel("Deck", (deck_w, D, 0.03), (-0.015, 0, deck_z - 0.015), "#2F3236", faces={"top": 0},
                    finish_="plastic"),
             _steel("FrameL", (deck_w, 0.04, 0.03), (-0.015, -D / 2 + 0.06, deck_z - 0.045), STEEL_DARK),
             _steel("FrameR", (deck_w, 0.04, 0.03), (-0.015, D / 2 - 0.06, deck_z - 0.045), STEEL_DARK)]
    hx = W / 2 - 0.015
    for k, y in enumerate((-D / 2 + 0.04, D / 2 - 0.04)):
        parts.append(_cyl(f"HandlePost{k}", (0.025, 0.025, handle_h - deck_z), (hx, y, deck_z + (handle_h - deck_z) / 2),
                          HC_ORANGE, "plastic"))
    parts.append(_p("HandleBar", "cylinder", (0.03, 0.03, D - 0.05), (hx, 0, handle_h - 0.015), "#2A2C30", "matte",
                    (90, 0, 0), material="rubber"))
    for k, (x, y) in enumerate(((-W / 2 + 0.08, -D / 2 + 0.08), (-W / 2 + 0.08, D / 2 - 0.08),
                                (W / 2 - 0.10, -D / 2 + 0.08), (W / 2 - 0.10, D / 2 - 0.08))):
        parts += [_p(f"Fork{k}", "box", (0.05, 0.04, 0.04), (x, y, 0.105), GALV, "metal", material="steel"),
                  _p(f"Wheel{k}", "cylinder", (0.10, 0.10, 0.03), (x, y, 0.05), "#2A2C30", "matte", (90, 0, 0),
                     material="rubber")]
    for p in parts:
        p.material = p.material or "steel"
    return Product(slug="platform_cart", name="平台車 900×600（店内用）", shape_class="assembly", category="fixture",
                   dims=Dimensions(handle_h, W, depth=D), mass_kg=12.0, material="steel",
                   description="形はホームセンターで重い物・長尺物を運ぶ一般的な平台車（荷台 900 × 600 mm・高さ 170 mm、+X 側に固定の"
                               "ハンドル、キャスター 4 個）で、寸法・質量は代表値。荷台は 商品を並べる棚板として使える。"
                               "動かせる物なので動く剛体（車輪は回らない）。",
                   tags=["台車", "平台車", "運搬", "カート", "ホームセンター", "platform cart", "hand truck",
                         "flatbed cart", "trolley"],
                   photos=[], colors=Colors(label_base="#2F3236"), images=imgs, parts=parts)


# ---------------------------------------------------------------- 100-yen gondola


def hundred_yen_gondola() -> Product:
    """A low 100-yen-shop gondola: base deck, two levels of small bins (their floors are the boards), open top."""
    W, D, H = 0.90, 0.45, 1.35
    side_t, back_t = 0.02, 0.02
    inner = W - 2 * side_t
    yb = D / 2 - back_t  # back panel front face
    pink, white = "#E84A7F", "#F6F6F4"
    head = Canvas(860, 160, None, pink, 4511)
    head.gradient(0, 0, 860, 160, mix(pink, WHITE, 0.1), mix(pink, "#000000", 0.12))
    head.ellipse(20, 10, 160, 150, fill=WHITE)
    head.text(90, 80, "100", 60, pink, 900)
    head.text(520, 62, "100円", 70, WHITE, 900)
    head.text(520, 126, "税込 110円  ほとんどの商品", 24, "#FFE082", 800)
    rail = Canvas(860, 30, None, "#F2F2EE", 4512)
    rail.gradient(0, 0, 860, 30, "#FFFFFF", "#E2E2DC")
    for k in range(6):
        x = 30 + k * 140
        rail.rect(x, 4, x + 90, 26, fill=WHITE, outline="#C9C9C2", width=1)
        rail.text(x + 45, 15, "¥100", 13, pink, 900)
    imgs = [_face(head.array(), "plastic", 4511, 0.3, 4), _face(rail.array(), "plastic", 4512, 0.3, 2)]
    parts = [_p("Plinth", "box", (inner, D - 0.02, 0.08), (0, 0.0, 0.04), "#7A7E84", "plastic", material="steel"),
             _p("BaseDeck", "box", (inner, yb + D / 2 - 0.02, 0.02), (0, (yb - D / 2 + 0.02) / 2, 0.09), white,
                "plastic", material="steel"),
             _p("Back", "box", (inner, back_t, H - 0.08), (0, D / 2 - back_t / 2, 0.08 + (H - 0.08) / 2), white,
                "plastic", material="steel")]
    for i, x in enumerate((-W / 2 + side_t / 2, W / 2 - side_t / 2)):
        parts.append(_p(f"Side{i}", "box", (side_t, D, H - 0.18), (x, 0, (H - 0.18) / 2), white, "plastic",
                        material="steel"))
    # bins: floor (the board) + thin walls just outside the floor's footprint
    bin_w, bin_d, wall, bin_h = 0.27, 0.38, 0.004, 0.10
    nb = 3
    pitch = inner / nb
    y_c = yb - 0.01 - bin_d / 2
    for lv, z in enumerate((0.43, 0.77)):
        parts += [_p(f"Rail{lv}", "box", (inner, 0.02, 0.03), (0, y_c - bin_d / 2 - wall - 0.01, z - 0.02), "#F2F2EE",
                     "plastic", faces={"front": 1}, material="plastic"),
                  _p(f"RailBack{lv}", "box", (inner, 0.02, 0.02), (0, yb - 0.01, z - 0.015), "#7A7E84", "plastic",
                     material="steel")]
        for b in range(nb):
            x = -inner / 2 + pitch * (b + 0.5)
            col = ("#4FC3F7", "#FFB74D", "#AED581")[(b + lv) % 3]
            zf = z - 0.004
            parts += [_p(f"Bin{lv}{b}Floor", "box", (bin_w, bin_d, 0.008), (x, y_c, zf), col, "plastic",
                         material="plastic"),
                      _p(f"Bin{lv}{b}Front", "box", (bin_w + 2 * wall, wall, 0.06), (x, y_c - bin_d / 2 - wall / 2,
                                                                                     z + 0.03 - 0.008), col,
                         "translucent", material="plastic"),
                      _p(f"Bin{lv}{b}Rear", "box", (bin_w + 2 * wall, wall, bin_h), (x, y_c + bin_d / 2 + wall / 2,
                                                                                    z + bin_h / 2 - 0.008), col,
                         "plastic", material="plastic")]
            for s in (-1, 1):
                parts.append(_p(f"Bin{lv}{b}Side{'L' if s < 0 else 'R'}", "box", (wall, bin_d, bin_h),
                                (x + s * (bin_w / 2 + wall / 2), y_c, z + bin_h / 2 - 0.008), col, "plastic",
                                material="plastic"))
    top_z = 1.12
    parts += [_p("Top", "box", (inner, yb + D / 2 - 0.02, 0.02), (0, (yb - D / 2 + 0.02) / 2, top_z - 0.01), white,
                 "plastic", material="steel"),
              _p("TopRail", "box", (inner, 0.02, 0.03), (0, -D / 2 + 0.01, top_z - 0.025), "#F2F2EE", "plastic",
                 faces={"front": 1}, material="plastic"),
              _sign("Header", (inner, 0.012, 0.16), (0, yb - 0.006, H - 0.09), pink, {"front": 0}, "#F7F5F0",
                    collision=True, material="plastic")]
    return Product(slug="hundred_yen_gondola", name="100 円ショップの低いゴンドラ 900mm（小分けのかご付き）",
                   shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=32.0,
                   static=True, material="steel",
                   description="形は 100 円ショップの一般的な低い片面のゴンドラ（幅 900 × 奥行き 450 × 高さ 1350 mm、下の台・"
                               "小分けのかご 3 個 × 2 段・天板、頭に「100円」の看板）で、寸法・質量は代表値。かごの底（270 × 380 mm）が"
                               "棚板で、壁は底の外側にあるので かごごとに小物を並べられる。下の台（床から 100 mm）と天板（1120 mm）"
                               "にも並べられる。看板の文字は架空。",
                   tags=["ゴンドラ", "低いゴンドラ", "かご", "小分け", "100円", "100均", "店舗什器", "100円ショップ",
                         "gondola", "bin shelf", "dollar store", "hundred yen shop"],
                   photos=[], colors=Colors(label_base=white), images=imgs, parts=parts,
                   picture_places=HUNDRED_PLACES)


# ---------------------------------------------------------------- hanging section signs


def _icon_tools(c: Canvas, cx: float, cy: float, r: float, col: str):
    c.polygon([(cx - r * 0.65, cy + r * 0.55), (cx - r * 0.5, cy + r * 0.7), (cx + r * 0.35, cy - r * 0.15),
               (cx + r * 0.2, cy - r * 0.3)], fill="#8D6E63")  # handle
    c.polygon([(cx + r * 0.0, cy - r * 0.45), (cx + r * 0.25, cy - r * 0.7), (cx + r * 0.7, cy - r * 0.25),
               (cx + r * 0.45, cy + r * 0.0)], fill="#546E7A")  # head
    # screwdriver: a red handle and a thin grey shaft, so it does not read as a "no" slash
    c.line([(cx - r * 0.1, cy - r * 0.05), (cx + r * 0.55, cy + r * 0.6)], "#90A4AE", r * 0.07)
    c.line([(cx - r * 0.62, cy - r * 0.57), (cx - r * 0.1, cy - r * 0.05)], "#E53935", r * 0.22)


def _icon_garden(c: Canvas, cx: float, cy: float, r: float, col: str):
    c.polygon([(cx - r * 0.45, cy + r * 0.15), (cx + r * 0.45, cy + r * 0.15), (cx + r * 0.32, cy + r * 0.75),
               (cx - r * 0.32, cy + r * 0.75)], fill="#B5653A")
    c.rect(cx - r * 0.04, cy - r * 0.45, cx + r * 0.04, cy + r * 0.15, fill="#4C8F3A")
    for a in (-1, 1):
        c.ellipse(cx + a * r * 0.32 - r * 0.22, cy - r * 0.25 - r * 0.12, cx + a * r * 0.32 + r * 0.22,
                  cy - r * 0.25 + r * 0.12, fill="#4C8F3A")
    for k in range(6):
        t = k * math.pi / 3
        c.ellipse(cx + r * 0.2 * math.cos(t) - r * 0.13, cy - r * 0.6 + r * 0.2 * math.sin(t) - r * 0.13,
                  cx + r * 0.2 * math.cos(t) + r * 0.13, cy - r * 0.6 + r * 0.2 * math.sin(t) + r * 0.13, fill=col)
    c.ellipse(cx - r * 0.1, cy - r * 0.7, cx + r * 0.1, cy - r * 0.5, fill="#FFE082")


def _icon_hardware(c: Canvas, cx: float, cy: float, r: float, col: str):
    c.polygon([(cx - r * 0.45 + r * 0.9 * (0.5 + 0.5 * math.cos(t)) - r * 0.45, cy - r * 0.45 + r * 0.25 * math.sin(t))
               for t in np.linspace(0, 2 * math.pi, 7)[:-1]], fill="#78909C")  # bolt head (hexagon)
    c.rect(cx - r * 0.16, cy - r * 0.3, cx + r * 0.16, cy + r * 0.75, fill="#90A4AE")
    for k in range(7):
        y = cy - r * 0.2 + k * r * 0.13
        c.line([(cx - r * 0.2, y), (cx + r * 0.2, y + r * 0.06)], "#546E7A", r * 0.04)
    c.ellipse(cx + r * 0.35, cy + r * 0.1, cx + r * 0.75, cy + r * 0.5, outline=col, width=r * 0.1)


def _icon_storage(c: Canvas, cx: float, cy: float, r: float, col: str):
    c.rect(cx - r * 0.65, cy - r * 0.2, cx + r * 0.65, cy + r * 0.65, fill="#E3E7EA", outline="#90A4AE",
           width=r * 0.05, radius=r * 0.08)
    c.rect(cx - r * 0.72, cy - r * 0.38, cx + r * 0.72, cy - r * 0.18, fill=col, radius=r * 0.06)
    c.rect(cx - r * 0.2, cy + r * 0.05, cx + r * 0.2, cy + r * 0.18, fill="#90A4AE", radius=r * 0.04)


def _hc_section_sign(slug: str, name: str, ja: str, en: str, accent: str, icon, seed: int,
                     tags: list[str]) -> Product:
    """A section sign hung from the ceiling by two wires (the same picture on both sides)."""
    W, bh, t, drop = 1.20, 0.40, 0.012, 0.80
    H = bh + drop
    cw, ch = W * 1000, bh * 1000
    c = Canvas(cw, ch, None, accent, seed)
    c.gradient(0, 0, cw, ch, mix(accent, WHITE, 0.12), mix(accent, "#000000", 0.18))
    c.rect(0, ch - 30, cw, ch - 20, fill=WHITE)
    r, cx, cy = 140.0, 190.0, ch / 2 - 12
    c.ellipse(cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8, fill=WHITE)
    icon(c, cx, cy, r, accent)
    size, spacing = (180, 20) if len(ja) <= 2 else (150, 20) if len(ja) <= 4 else (118, 6)  # 6 chars fit 780 px
    c.text(cw / 2 + 170, 160, ja, size, WHITE, 900, spacing=spacing, max_w=cw - 420)
    c.text(cw / 2 + 170, 300, en, 44, mix(accent, WHITE, 0.8), 800, spacing=6, max_w=cw - 420)
    img = trim_safe(finish(c.array(), "plastic", seed, 0.3))
    parts = [_p("Board", "box", (W, t, bh), (0, 0, bh / 2), accent, "plastic", faces={"front": 0, "back": 0},
                bevel=0.004, blank=mix(accent, WHITE, 0.05)),
             _p("Rail", "box", (W, t + 0.008, 0.016), (0, 0, bh + 0.008), GALV, "metal", collision=False,
                material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.12, W / 2 - 0.12)):
        parts += [_p(f"Wire{k}", "cylinder", (0.0015, 0.0015, drop - 0.016), (x, 0, bh + 0.016 + (drop - 0.016) / 2),
                     "#C9CDD1", "metal", collision=False, material="steel"),
                  _p(f"CeilingPlate{k}", "cylinder", (0.040, 0.040, 0.006), (x, 0, H - 0.003), WHITE, "plastic",
                     collision=False)]
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=0.040), mass_kg=3.2, static=True, mount="ceiling", material="plastic",
                   description="形はホームセンターの売場の上に天井からワイヤーで吊る一般的な売場名の看板（1200 × 400 mm・厚さ 12 mm、"
                               "吊り下げ 800 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。"
                               f"表と裏に同じ「{ja}」を表示する。デザインは架空。",
                   tags=[*tags, "売場看板", "吊り看板", "売り場サイン", "ホームセンター", "内装", "section sign",
                         "hanging sign", "store signage", "home center"],
                   photos=[], colors=Colors(label_base=accent), images=[img], parts=parts, picture_places=HC_PLACES)


def section_sign_tools() -> Product:
    return _hc_section_sign("section_sign_tools", "売場の吊り看板「工具」", "工具", "TOOLS", HC_NAVY, _icon_tools, 4521,
                            ["工具", "電動工具", "tools"])


def section_sign_garden() -> Product:
    return _hc_section_sign("section_sign_garden", "売場の吊り看板「園芸」", "園芸", "GARDEN", HC_GREEN, _icon_garden,
                            4522, ["園芸", "ガーデニング", "garden"])


def section_sign_hardware() -> Product:
    return _hc_section_sign("section_sign_hardware", "売場の吊り看板「金物・DIY」", "金物・DIY", "HARDWARE & DIY",
                            "#6D4C41", _icon_hardware, 4523, ["金物", "DIY", "hardware"])


def section_sign_storage() -> Product:
    return _hc_section_sign("section_sign_storage", "売場の吊り看板「収納・日用品」", "収納・日用品", "STORAGE & HOUSEHOLD",
                            HC_ORANGE, _icon_storage, 4524, ["収納", "日用品", "storage"])


PRODUCTS = {f.__name__: f for f in (
    hc_tall_rack, wood_pallet, plastic_pallet, pallet_soil_stack, pallet_carton_stack, pegboard_gondola,
    pegboard_wall_tools, long_goods_rack, garden_tiered_stand, garden_outdoor_shelf, platform_cart,
    hundred_yen_gondola, section_sign_tools, section_sign_garden, section_sign_hardware, section_sign_storage)}
