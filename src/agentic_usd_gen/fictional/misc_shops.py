"""Fictional designs for fixtures and goods of various shops and rooms: living-room soft goods, pet-shop cases, liquor-store fixtures, store fixtures,
an electronics display table, garden-centre trays and benches, a whiteboard and a wheelchair.

No real product names, brands or logos; shapes and sizes are typical values. Front is -Y.
Products (cushion, remote, beer bottle, laptop, seedling tray) are rigid bodies; the rest are static.
"""

from __future__ import annotations

import math
import random

from ..spec import Colors, Dimensions, Part
from .backyard import RUBBER, _wheel
from .base import Product, label_canvas, revolve, top_canvas
from .conv_drinks import ALCOHOL_NOTE, _alcohol_mark
from .forms import RevolveForm, _arc
from .hc_garden import _p, _seg
from .paint import Canvas, finish, mix
from .products import INK, _bottle_back, _face

WHITE = "#FFFFFF"
BLACK = "#1E1E1E"
OAK, WALNUT = "#C8A57A", "#6B4A2E"
CHROME, STEEL, GALV = "#D4D7DB", "#9AA0A6", "#B9BEC4"
GLASS = "#E6F0F2"
LEAF = "#4F8A34"

HOME_TAGS = ["住宅", "リビング", "インテリア", "home", "living room", "interior"]
PET_TAGS = ["ペットショップ", "ペット", "生体", "pet shop", "pet store", "pet"]
LIQUOR_TAGS = ["酒屋", "酒販店", "liquor store", "wine shop", "liquor"]
STORE_TAGS = ["店舗", "店舗什器", "store fixture", "shop", "store"]
ELEC_TAGS = ["家電量販店", "携帯ショップ", "electronics store", "phone shop", "electronics"]
GARDEN_TAGS = ["園芸店", "ガーデンセンター", "園芸", "garden center", "garden centre", "nursery", "gardening"]
OFFICE_TAGS = ["オフィス", "事務所", "office"]
MEDICAL_TAGS = ["病院", "介護", "福祉", "hospital", "medical", "care"]


# ================================================================ living room

def _cushion_cover(seed: int, base: str, line: str) -> object:
    """A woven cushion cover: a fine cross-hatch with a lighter diamond in the middle and a piped edge."""
    c = Canvas(450, 450, 2, base, seed)
    c.gradient(0, 0, 450, 450, mix(base, WHITE, 0.06), mix(base, "#000000", 0.08))
    for k in range(0, 450, 6):
        c.line([(k, 0), (k, 450)], mix(base, "#000000", 0.10), 0.6)
        c.line([(0, k), (450, k)], mix(base, WHITE, 0.08), 0.6)
    c.polygon([(225, 95), (355, 225), (225, 355), (95, 225)], outline=line)
    c.polygon([(225, 125), (325, 225), (225, 325), (125, 225)], fill=mix(base, WHITE, 0.18), outline=line)
    c.rect(4, 4, 446, 446, outline=mix(base, "#000000", 0.25), width=5)
    return _face(c.array(), "paper", seed, 0.5, 10)


def throw_cushion() -> Product:
    """A square throw cushion (450 x 450 mm) standing on the sofa seat against the back."""
    W, T, H = 0.45, 0.16, 0.45
    base = "#7A8F8A"
    img = _cushion_cover(7901, base, "#E8E2D2")
    parts = [_p("Body", "box", (W, T, H), (0, 0, H / 2), base, "matte", faces={"front": 0, "back": 0},
                material="fabric", bevel=0.035)]
    for s in (-1, 1):  # the cover bulges in the middle, front and back
        parts.append(_p(f"Puff{'F' if s < 0 else 'B'}", "box", (W - 0.10, 0.02, H - 0.10), (0, s * (T / 2 + 0.004), H / 2),
                        base, "matte", faces={"front" if s < 0 else "back": 0}, collision=False, material="fabric",
                        bevel=0.009))
    return Product(slug="throw_cushion", name="クッション（45 cm 角）", shape_class="assembly", category="household",
                   dims=Dimensions(H, W, depth=T + 0.028), mass_kg=0.6, material="fabric",
                   description="形は一般的な 45 cm 角のソファのクッション（厚さ約 160 mm、くすんだ緑の織り地に菱形の柄）で、"
                               "寸法・質量は代表値。ソファの座面に立てて背もたれに寄せる。当たり判定は角を丸めた箱 1 つ。",
                   tags=["クッション", "ソファクッション", "インテリア小物", "throw pillow", "cushion", "sofa pillow",
                         "sofa cushion", "decorative pillow", *HOME_TAGS], photos=[], colors=Colors(label_base=base),
                   images=[img], parts=parts)


def _rug_top(seed: int) -> object:
    """A flat-woven rug seen from above: a border, a lighter field and a row of diamonds."""
    L, D = 1600, 1200
    c = Canvas(L, D, 1, "#B9A27E", seed)
    c.gradient(0, 0, L, D, "#C6B08A", "#AE9670")
    c.rect(40, 40, L - 40, D - 40, fill="#E7DCC4")
    c.rect(70, 70, L - 70, D - 70, outline="#7C4B32", width=10)
    c.rect(110, 110, L - 110, D - 110, outline="#3E5A6B", width=4)
    for k in range(5):
        cx = 300 + k * 250
        c.polygon([(cx, 380), (cx + 110, 600), (cx, 820), (cx - 110, 600)], fill="#C98A5A", outline="#7C4B32")
        c.polygon([(cx, 470), (cx + 60, 600), (cx, 730), (cx - 60, 600)], fill="#3E5A6B")
    for x in range(0, L, 8):  # the warp threads
        c.line([(x, 0), (x, D)], "#00000010", 0.8)
    return finish(c.array(), "paper", seed, 0.9)


def area_rug() -> Product:
    """A flat 1600 x 1200 mm area rug, lying on the floor (static: it does not slide under things)."""
    L, D, T = 1.60, 1.20, 0.010
    parts = [_p("Rug", "box", (L, D, T), (0, 0, T / 2), "#C6B08A", "matte", faces={"top": 0}, material="fabric",
                bevel=0.002)]
    return Product(slug="area_rug", name="ラグ（160 × 120 cm）", shape_class="assembly", category="household",
                   dims=Dimensions(T, L, depth=D), mass_kg=2.5, static=True, material="fabric",
                   description="形は一般的なリビングのラグ（1600 × 1200 mm・厚さ 10 mm、生成りの地に縁取りと菱形の柄）で、"
                               "寸法・質量は代表値。床に固定した薄い板として書き出す（剛体にすると机の脚に押されて滑る）。",
                   tags=["ラグ", "カーペット", "敷物", "マット", "rug", "area rug", "carpet", "living room rug", *HOME_TAGS],
                   photos=[], colors=Colors(label_base="#C6B08A"), images=[_rug_top(7902)], parts=parts)


def _remote_top(seed: int) -> object:
    c = Canvas(48, 180, 8, "#2B2D31", seed)
    c.gradient(0, 0, 48, 180, "#34363B", "#222428")
    c.ellipse(19, 10, 29, 20, fill="#C62828")  # power
    for r in range(4):  # number keys
        for k in range(3):
            x, y = 9 + k * 15, 32 + r * 12
            c.rect(x - 5, y - 4, x + 5, y + 4, fill="#4A4D53", radius=2)
            c.text(x, y, str(r * 3 + k + 1) if r < 3 else ("*0#"[k]), 3.6, "#E6E6E6", 700)
    c.ellipse(9, 86, 39, 116, fill="#4A4D53")  # cross key
    c.ellipse(18, 95, 30, 107, fill="#2B2D31", outline="#7A7E86", width=0.6)
    for k, col in enumerate(("#3E7BD8", "#D83E3E", "#3EAE5A", "#E0C030")):
        c.rect(6 + k * 10, 124, 12 + k * 10, 129, fill=col, radius=1.5)
    for r in range(2):
        for k in range(2):
            c.rect(8 + k * 22, 138 + r * 14, 18 + k * 22, 146 + r * 14, fill="#4A4D53", radius=3)
    c.text(24, 172, "TV", 4.0, "#9A9EA6", 800)
    return finish(c.array(), "paper", seed, 0.3)


def tv_remote() -> Product:
    """A TV remote control lying on its back."""
    W, L, H = 0.048, 0.180, 0.022
    parts = [_p("Body", "box", (W, L, H), (0, 0, H / 2), "#2B2D31", "plastic", faces={"top": 0}, material="plastic",
                bevel=0.006)]
    return Product(slug="tv_remote", name="テレビのリモコン", shape_class="assembly", category="household",
                   dims=Dimensions(H, L, depth=W), mass_kg=0.12, material="plastic",
                   description="形は一般的なテレビのリモコン（180 × 48 mm・厚さ 22 mm、黒い樹脂に数字・十字・色のボタン）で、"
                               "寸法・質量は代表値。ボタンは上面の絵。名前・メーカー名はすべて架空。",
                   tags=["リモコン", "テレビのリモコン", "remote control", "tv remote", "remote", "television remote",
                         *HOME_TAGS], photos=[], colors=Colors(label_base="#2B2D31"), images=[_remote_top(7903)],
                   parts=parts)


# ================================================================ pet shop

def _bars(prefix: str, x0, x1, y0, y1, z0, z1, step: float, d: float, color: str, ends: bool = True) -> list[Part]:
    """Vertical wire bars along the line (x0, y0) - (x1, y1), every `step`, from z0 to z1 (no collision).

    `ends=False` leaves out the two end bars, for a side whose corners another side already fills.
    """
    n = max(1, round(math.hypot(x1 - x0, y1 - y0) / step))
    return [_seg(f"{prefix}{k}", (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n, z0),
                 (x0 + (x1 - x0) * k / n + 1e-6, y0 + (y1 - y0) * k / n, z1), d, color, "metal", collision=False,
                 material="steel") for k in (range(n + 1) if ends else range(1, n))]


def pet_wire_cage() -> Product:
    """A wire dog cage (crate) with a plastic tray, as shown in a pet shop: bars on all sides and a wire top."""
    W, D, H = 0.78, 0.52, 0.62
    tray_h = 0.07
    wire = "#3A3D42"
    parts = [_p("Tray", "box", (W, D, tray_h), (0, 0, tray_h / 2), "#6E7378", "plastic", material="plastic", bevel=0.01),
             ]
    for nm, x, y, w, d in (("F", 0, -D / 2 + 0.006, W, 0.012), ("B", 0, D / 2 - 0.006, W, 0.012),
                           ("L", -W / 2 + 0.006, 0, 0.012, D), ("R", W / 2 - 0.006, 0, 0.012, D)):
        parts.append(_p(f"Top{nm}", "box", (w, d, 0.012), (x, y, H - 0.006), wire, "metal", material="steel", bevel=0.001))
    for k in range(1, 15):  # the wire top (look only)
        parts.append(_p(f"TopWire{k}", "box", (0.004, D - 0.02, 0.004), (-W / 2 + k * W / 15, 0, H - 0.004), wire, "metal",
                        collision=False, material="steel", bevel=0))
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):  # corner posts (collide)
        parts.append(_p(f"Post{n}", "box", (0.012, 0.012, H - tray_h), (sx * (W / 2 - 0.006), sy * (D / 2 - 0.006),
                        tray_h + (H - tray_h) / 2), wire, "metal", material="steel", bevel=0.001))
    z0, z1 = tray_h, H - 0.012
    parts += _bars("BarF", -W / 2, W / 2, -D / 2, -D / 2, z0, z1, 0.035, 0.004, wire)
    parts += _bars("BarB", -W / 2, W / 2, D / 2, D / 2, z0, z1, 0.035, 0.004, wire)
    # 角の棒は前後の面が持つ。左右の面にも置くと同じ位置に 2 本重なる（SimReady の VG.008）
    parts += _bars("BarL", -W / 2, -W / 2, -D / 2, D / 2, z0, z1, 0.035, 0.004, wire, ends=False)
    parts += _bars("BarR", W / 2, W / 2, -D / 2, D / 2, z0, z1, 0.035, 0.004, wire, ends=False)
    for k, z in enumerate((tray_h + 0.10, (z0 + z1) / 2, z1 - 0.08)):  # horizontal rails
        for nm, x, y, w, d in (("F", 0, -D / 2, W, 0.006), ("B", 0, D / 2, W, 0.006), ("L", -W / 2, 0, 0.006, D),
                               ("R", W / 2, 0, 0.006, D)):
            parts.append(_p(f"Rail{nm}{k}", "box", (w, d, 0.006), (x, y, z), wire, "metal", material="steel", bevel=0))
    parts.append(_p("Door", "box", (0.36, 0.008, 0.40), (0, -D / 2 - 0.006, tray_h + 0.24), wire, "metal",
                    collision=False, material="steel", bevel=0.001))
    parts.append(_p("Latch", "box", (0.05, 0.02, 0.03), (0.16, -D / 2 - 0.014, tray_h + 0.24), CHROME, "metal",
                    collision=False, material="steel"))
    parts.append(_p("Mat", "box", (W - 0.06, D - 0.06, 0.012), (0, 0, tray_h + 0.006), "#C9B79A", "matte",
                    collision=False, material="fabric"))
    return Product(slug="pet_wire_cage", name="ペットのワイヤーケージ（中型犬用）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.02), mass_kg=9.0, static=True, material="steel",
                   description="形は一般的な中型犬用のワイヤーケージ（780 × 520 mm・高さ 620 mm、黒い鋼線に樹脂の受け皿、正面に扉）で、"
                               "寸法・質量は代表値。売り場に置く見本として床に固定する。当たり判定は受け皿・四隅の柱・横桟・天面で、"
                               "細い鋼線は見た目だけ。",
                   tags=["ケージ", "犬のケージ", "ワイヤーケージ", "クレート", "pet cage", "dog cage", "wire cage",
                         "dog crate", "animal cage", *PET_TAGS], photos=[], colors=Colors(label_base=wire), images=[],
                   parts=parts)


def puppy_showcase() -> Product:
    """The glass-fronted showcase a pet shop keeps puppies and kittens in: 3 x 2 lit cubicles on a cabinet."""
    W, D, H = 1.80, 0.65, 1.80
    base_h, cols, rows = 0.40, 3, 2
    frame = "#F2F0EC"
    cw, ch = W / cols, (H - base_h) / rows
    parts = [_p("Cabinet", "box", (W, D, base_h), (0, 0, base_h / 2), WALNUT, "matte", material="wood"),
             _p("Back", "box", (W, 0.03, H - base_h), (0, D / 2 - 0.015, base_h + (H - base_h) / 2), frame, "matte",
                material="wood"),
             _p("Top", "box", (W, D, 0.04), (0, 0, H - 0.02), frame, "matte", material="wood")]
    for k in range(cols + 1):
        x = -W / 2 + 0.02 + k * (W - 0.04) / cols
        parts.append(_p(f"Side{k}", "box", (0.04, D, H - base_h), (x, 0, base_h + (H - base_h) / 2), frame, "matte",
                        material="wood"))
    for r in range(rows):
        z = base_h + r * ch
        parts.append(_p(f"Floor{r}", "box", (W, D - 0.03, 0.03), (0, -0.015, z + 0.015), frame, "matte",
                        material="wood"))
        for k in range(cols):
            x = -W / 2 + (k + 0.5) * cw
            parts += [_p(f"Glass{r}{k}", "box", (cw - 0.05, 0.006, ch - 0.06), (x, -D / 2 + 0.005, z + ch / 2),
                         GLASS, "glass", material="glass", thin_walled=True, bevel=0),
                      _p(f"Pad{r}{k}", "box", (cw - 0.08, D - 0.10, 0.012), (x, 0.0, z + 0.036),
                         "#D9CDB5" if (r + k) % 2 else "#BFD3C2", "matte", collision=False, material="fabric"),
                      _p(f"Lamp{r}{k}", "box", (cw - 0.12, 0.10, 0.008), (x, 0.0, z + ch - 0.008), "#FFF8EC", "light",
                         collision=False, material="plastic"),
                      _p(f"Vent{r}{k}", "box", (cw - 0.12, 0.006, 0.03), (x, -D / 2 + 0.002, z + ch - 0.035), "#9AA0A6",
                         "metal", collision=False, material="steel")]
    parts.append(_p("Kick", "box", (W - 0.04, 0.006, base_h - 0.06), (0, -D / 2 - 0.002, base_h / 2), mix(WALNUT, WHITE, 0.1),
                    "matte", collision=False, material="wood"))
    return Product(slug="puppy_showcase", name="子犬・子猫の展示ケース（3 × 2 室）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.004), mass_kg=160.0, static=True,
                   material="wood",
                   description="形はペットショップの壁際の一般的な生体の展示ケース（幅 1800 mm・奥行き 650 mm・高さ 1800 mm、"
                               "下は収納、上はガラス戸の照明付きの小部屋が 3 列 × 2 段、床にマット）で、寸法・質量は代表値。"
                               "中は空（動物は入れない）。",
                   tags=["生体ケース", "展示ケース", "ショーケース", "子犬", "子猫", "pet display case", "puppy showcase",
                         "animal display case", "pet showcase", "kennel", *PET_TAGS], photos=[],
                   colors=Colors(label_base=frame), images=[], parts=parts)


def aquarium_tank() -> Product:
    """A 900 mm aquarium on its cabinet stand: gravel, a few plants, water and a lit lid."""
    W, D = 0.90, 0.45
    stand_h, tank_h = 0.70, 0.45
    H = stand_h + tank_h + 0.04
    z0 = stand_h
    water = "#7FC4D6"
    parts = [_p("Stand", "box", (W, D, stand_h), (0, 0, stand_h / 2), BLACK, "matte", material="wood"),
             _p("StandDoors", "box", (W - 0.04, 0.004, stand_h - 0.08), (0, -D / 2 - 0.001, stand_h / 2), "#2E2E32",
                "glossy", collision=False, material="wood"),
             _p("Tank", "box", (W, D, tank_h), (0, 0, z0 + tank_h / 2), GLASS, "glass", material="glass",
                thin_walled=True, bevel=0.003),
             _p("Water", "box", (W - 0.02, D - 0.02, tank_h - 0.06), (0, 0, z0 + (tank_h - 0.06) / 2 + 0.005), water,
                "translucent", collision=False, material="water", bevel=0),
             _p("Gravel", "box", (W - 0.02, D - 0.02, 0.05), (0, 0, z0 + 0.03), "#B59F7E", "matte", collision=False,
                material="stone", bevel=0),
             _p("Lid", "box", (W + 0.01, D + 0.01, 0.04), (0, 0, z0 + tank_h + 0.02), BLACK, "plastic",
                material="plastic"),
             _p("Light", "box", (W - 0.10, 0.10, 0.006), (0, 0, z0 + tank_h - 0.004), "#F2FBFF", "light",
                collision=False, material="plastic"),
             _p("Rock", "dome", (0.20, 0.14, 0.10), (0.20, 0.08, z0 + 0.055 + 0.05), "#6F6A62", "matte",
                collision=False, material="stone")]
    rng = random.Random(7911)
    for k in range(9):  # tall plants at the back, a few short ones in front
        x = -0.38 + k * 0.095 + rng.uniform(-0.02, 0.02)
        back = k % 3 != 1
        h = rng.uniform(0.22, 0.32) if back else rng.uniform(0.08, 0.14)
        y = 0.12 if back else -0.08
        for j in range(3):
            parts.append(_p(f"Plant{k}_{j}", "leaf", (h, 0.025, 0.02), (x + (j - 1) * 0.012, y, z0 + 0.055 + h / 2),
                            mix(LEAF, "#2C5E22", rng.uniform(0, 0.6)), "matte", rot=(0, -90 + (j - 1) * 12, 90),
                            segments=0, collision=False, material="leaf_grass"))
    return Product(slug="aquarium_tank", name="水槽（90 cm）と水槽台", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W + 0.01, depth=D + 0.01), mass_kg=230.0, static=True, material="glass",
                   description="形は一般的な 90 cm 水槽（900 × 450 × 450 mm）を黒い水槽台（高さ 700 mm）に載せたもので、"
                               "寸法・質量（水込み）は代表値。中に砂利・石・水草と水、ふたに照明。魚は入れない。",
                   tags=["水槽", "アクアリウム", "熱帯魚", "水槽台", "aquarium", "fish tank", "aquarium tank",
                         "aquarium stand", *PET_TAGS], photos=[], colors=Colors(label_base=water), images=[], parts=parts)


def _treat_label(seed: int, name: str, color: str) -> object:
    c = Canvas(90, 40, 6, WHITE, seed)
    c.rect(0, 0, 90, 12, fill=color)
    c.text(45, 6.5, "量り売り", 6, WHITE, 900)
    c.text(45, 22, name, 8, INK, 900)
    c.text(45, 33, "100g ¥298", 6, "#C62828", 900)
    return _face(c.array(), "paper", seed, 0.4, 3)


def pet_treat_bulk_case() -> Product:
    """A bulk treat stand: 2 x 4 clear bins with flip lids, tilted forward, on a wooden stand, with a scoop."""
    W, D, H = 0.90, 0.50, 1.25
    goods = [("ささみ", "#C98A5A", "#D9A57A"), ("ジャーキー", "#7A3E22", "#8C4A2A"), ("ほね", "#E8DCC0", "#EADFC6"),
             ("クッキー", "#C99A55", "#D6AA66"), ("チーズ", "#E8C64A", "#EAD07A"), ("やさい", "#7FA34A", "#9AB85E"),
             ("にぼし", "#9AA0A6", "#B0B5BA"), ("ミックス", "#B07A4A", "#C08A5A")]
    imgs = [_treat_label(7920 + k, n, mix(col, "#000000", 0.2)) for k, (n, col, _) in enumerate(goods)]
    parts = [_p("Stand", "box", (W, D, 0.55), (0, 0.02, 0.275), OAK, "matte", material="wood"),
             _p("Back", "box", (W, 0.03, H - 0.55), (0, D / 2 - 0.015, 0.55 + (H - 0.55) / 2), OAK, "matte",
                material="wood"),
             _p("Header", "box", (W, 0.02, 0.12), (0, D / 2 - 0.04, H - 0.06), "#7A3E22", "matte", collision=False,
                material="wood")]
    bw, bd, bh = 0.205, 0.30, 0.25
    for r in range(2):
        z = 0.55 + r * 0.30
        parts.append(_p(f"Shelf{r}", "box", (W, D - 0.06, 0.02), (0, 0.0, z + 0.01), OAK, "matte", material="wood"))
        for k in range(4):
            i = r * 4 + k
            name, col, top = goods[i]
            x = -W / 2 + 0.02 + bw / 2 + k * (bw + 0.013)
            parts += [_p(f"Bin{i}", "box", (bw, bd, bh), (x, -0.03, z + 0.02 + bh / 2), GLASS, "glass",
                         material="plastic", thin_walled=True, bevel=0.004),
                      _p(f"Goods{i}", "box", (bw - 0.012, bd - 0.012, bh * 0.62), (x, -0.03, z + 0.026 + bh * 0.31), col,
                         "matte", collision=False, material="food", bevel=0.002),
                      _p(f"GoodsTop{i}", "dome", (bw - 0.014, bd - 0.014, 0.03), (x, -0.03, z + 0.026 + bh * 0.62 + 0.015),
                         top, "matte", collision=False, material="food"),
                      _p(f"Lid{i}", "box", (bw + 0.004, bd + 0.004, 0.012), (x, -0.03, z + 0.02 + bh + 0.006),
                         "#D8E4E8", "glass", collision=False, material="plastic", thin_walled=True, bevel=0.002),
                      _p(f"Label{i}", "box", (0.09, 0.002, 0.04), (x, -0.03 - bd / 2 - 0.002, z + 0.02 + bh - 0.04),
                         WHITE, "matte", faces={"front": i}, collision=False, material="paper", bevel=0)]
    parts.append(_p("Scoop", "box", (0.08, 0.16, 0.04), (0.30, -0.10, 0.55 + 0.30 * 2 + 0.04), "#D8E4E8", "plastic",
                    collision=False, material="plastic"))
    return Product(slug="pet_treat_bulk_case", name="ペットおやつの量り売りケース（8 種）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=45.0, static=True,
                   material="wood",
                   description="形はペットショップの一般的なおやつの量り売りの台（幅 900 mm・奥行き 500 mm・高さ 1250 mm、"
                               "木の台に透明なふた付きの容器 4 × 2 段、各容器に品名と 100 g の値段の札、スコップ）で、"
                               "寸法・質量は代表値。中身は見た目だけ。品名・値段は架空。",
                   tags=["量り売り", "おやつ", "ペットのおやつ", "ばら売り", "bulk treat case", "bulk bin", "treat bin",
                         "pet treats", "bulk treats", *PET_TAGS], photos=[], colors=Colors(label_base=OAK), images=imgs,
                   parts=parts)


# ================================================================ liquor store

def wine_step_rack() -> Product:
    """A wooden stepped wine rack: four flat steps rising toward the back, each with a low front lip."""
    W, D, H = 0.90, 0.60, 1.40
    steps = 4
    sd = D / steps
    parts = [_p("SideL", "box", (0.02, D, H), (-W / 2 + 0.01, 0, H / 2), WALNUT, "matte", material="wood"),
             _p("SideR", "box", (0.02, D, H), (W / 2 - 0.01, 0, H / 2), WALNUT, "matte", material="wood"),
             _p("Back", "box", (W, 0.02, H), (0, D / 2 - 0.01, H / 2), WALNUT, "matte", material="wood")]
    for k in range(steps):
        z = 0.30 + k * (H - 0.40) / (steps - 1)
        y = -D / 2 + (k + 0.5) * sd
        parts += [_p(f"Step{k}", "box", (W - 0.04, sd, 0.025), (0, y, z), OAK, "matte", material="wood"),
                  _p(f"Riser{k}", "box", (W - 0.04, 0.02, z), (0, y - sd / 2 + 0.01, z / 2), mix(OAK, "#000000", 0.08),
                     "matte", material="wood"),
                  _p(f"Lip{k}", "box", (W - 0.04, 0.012, 0.03), (0, y - sd / 2 + 0.006, z + 0.0275), WALNUT, "matte",
                     material="wood", bevel=0.002)]
        if k == steps - 1:
            parts.append(_p("Top", "box", (W, sd, 0.025), (0, y, H - 0.0125), WALNUT, "matte", material="wood"))
    return Product(slug="wine_step_rack", name="木のひな壇ワインラック", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=38.0, static=True, material="wood",
                   description="形は酒屋・ワイン売場の一般的な木のひな壇の陳列台（幅 900 mm・奥行き 600 mm・高さ 1400 mm、"
                               "奥ほど高い 4 段、各段の前に低い縁）で、寸法・質量は代表値。段は平らで、ボトルを立てて 並べる。",
                   tags=["ワインラック", "ひな壇", "ワイン棚", "陳列台", "wine rack", "wooden wine rack", "wine display",
                         "tiered display", "wine shelf", *LIQUOR_TAGS, *STORE_TAGS], photos=[],
                   colors=Colors(label_base=OAK), images=[], parts=parts)


def _crate_side(seed: int) -> object:
    c = Canvas(500, 300, 2, "#D9B98A", seed)
    c.gradient(0, 0, 500, 300, "#E0C496", "#C9A672")
    rng = random.Random(seed)
    for _ in range(60):  # wood grain
        y = rng.uniform(0, 300)
        c.line([(0, y), (500, y + rng.uniform(-6, 6))], "#B08A5A55", rng.uniform(0.5, 1.5))
    for y in (100, 200):
        c.line([(0, y), (500, y)], "#8C6A40", 2.0)
    c.text(250, 140, "VINO", 70, "#5A2A1A", 900, spacing=8)
    c.text(250, 210, "VIN DE TABLE · ROUGE", 20, "#5A2A1A", 800, spacing=3)
    c.rect(60, 40, 440, 260, outline="#5A2A1A", width=3)
    return finish(c.array(), "paper", seed, 0.8)


def wine_crate() -> Product:
    """An open wooden wine crate on the floor as a display; the bottom inside is a shelf for fill."""
    W, D, H = 0.50, 0.34, 0.30
    t = 0.015
    img = _crate_side(7931)
    # The bottom sits between the walls so the fill shelf it makes ends at the inner faces of the walls.
    parts = [_p("Bottom", "box", (W - 2 * t, D - 2 * t, 0.02), (0, 0, 0.01), "#D8C27A", "matte", material="wood",
                bevel=0),
             _p("Front", "box", (W, t, H), (0, -D / 2 + t / 2, H / 2), "#D9B98A", "matte", faces={"front": 0},
                material="wood", bevel=0.002),
             _p("Rear", "box", (W, t, H), (0, D / 2 - t / 2, H / 2), "#D9B98A", "matte", faces={"back": 0},
                material="wood", bevel=0.002),
             _p("Left", "box", (t, D - 2 * t, H), (-W / 2 + t / 2, 0, H / 2), "#D9B98A", "matte", material="wood",
                bevel=0.002),
             _p("Right", "box", (t, D - 2 * t, H), (W / 2 - t / 2, 0, H / 2), "#D9B98A", "matte", material="wood",
                bevel=0.002)]
    return Product(slug="wine_crate", name="木のワイン箱（陳列用）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=4.5, static=True, material="wood",
                   description="形は酒屋で床やひな壇に置く一般的な木のワイン箱（500 × 340 mm・高さ 300 mm、焼き印風の文字）で、寸法・質量は代表値。上は開いていて、底を 商品を並べる棚板にしてボトルを立てて並べる。",
                   tags=["ワイン箱", "木箱", "ワインケース", "陳列", "wine crate", "wooden wine crate", "wine box",
                         "wooden crate", *LIQUOR_TAGS, *STORE_TAGS], photos=[], colors=Colors(label_base="#D9B98A"),
                   images=[img], parts=parts)


def _beer_bottle(H: float, D: float, *, neck_r: float, cap_r: float, cap_h: float) -> RevolveForm:
    """A long-necked brown beer bottle with a crown cap, one solid body (the cap is not a separate part)."""
    R = D / 2
    cap_z = H - cap_h
    sh_z = 0.55 * H
    body = [(0.0, R * 0.88)] + _arc(0.0005, 0.006, R * 0.93, R, 8, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, sh_z + 0.055, R, neck_r * 1.15, 30, "cos")[1:]
    body += [(cap_z - 0.012, neck_r), (cap_z - 0.004, neck_r * 1.12), (cap_z, neck_r * 1.05)]
    cap = [(cap_z, cap_r), (H - 0.0008, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, (0.030, 0.110), None)


def beer_bottle_334ml() -> Product:
    """A 334 ml brown beer bottle with a crown cap, a single rigid body."""
    form = _beer_bottle(0.235, 0.062, neck_r=0.0125, cap_r=0.0145, cap_h=0.007)
    gold, red, cream = "#C9A23E", "#B3202A", "#F6EFD9"
    c = label_canvas(form, cream, seed=7941)
    W, Hc = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, Hc, "#FAF4E2", "#EADFC0")
    c.rect(fx - 34, 0, fx + 34, Hc, fill=cream)
    c.rect(fx - 32, 3, fx + 32, Hc - 3, outline=gold, width=0.8)
    c.rect(fx - 32, 26, fx + 32, 44, fill=red)
    c.text(fx, 15, "LAGER", 9, INK, 900, spacing=1.5)
    c.text(fx, 35, "生ビール", 9, cream, 900)
    c.text(fx, 54, "麦芽100%  334ml", 3.6, INK, 800)
    c.text(fx, 62, "アルコール分5%", 3.2, INK, 700)
    c.text(fx, 72, "架空の麦酒醸造所", 3.0, INK, 700)
    _alcohol_mark(c, fx + 26, 72, 6)
    _bottle_back(c, 0.25 * W, 6, 40, "ビール", "麦芽（外国製造）・ホップ", 1.7, color=INK, bg=cream,
                 extra=[("内容量", "334ml"), ("アルコール分", "5%"), ("製造者", "架空の麦酒 株式会社")])
    c.paragraph(0.25 * W - 22, 52, 0.25 * W + 22, ALCOHOL_NOTE, 1.5, INK, 600)
    c.barcode(0.25 * W - 11, 66, 22, 12)
    label = finish(c.array(), "paper", 7941, 0.5)
    t = top_canvas(form, gold, seed=7942)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D8B04A", "#A8822A")
    t.ellipse(d * 0.15, d * 0.15, d * 0.85, d * 0.85, outline=red, width=0.8)
    t.text(d / 2, d / 2, "L", 9, red, 900)
    top = finish(t.array(), "metal", 7942, 0.6)
    return Product(slug="beer_bottle_334ml", name="瓶ビール 334ml（王冠）", category="beverage", mass_kg=0.53,
                   capacity_ml=334, material="glass (opaque brown)",
                   description="形は一般的な 334ml の茶色いビール瓶（高さ 235 mm・胴径 62 mm、王冠）で、寸法・質量は代表値。"
                               "王冠は瓶と同じ 1 つの剛体（キャップが別の剛体だと棚の上で外れて落ちる）。濃い茶色のガラスで"
                               "中身はほとんど見えないため、不透明の瓶として作った。名前・メーカー名はすべて架空。",
                   tags=["ビール", "瓶ビール", "ビール瓶", "お酒", "酒類", "瓶", "beer bottle", "beer", "lager",
                         "bottled beer", "alcohol", *LIQUOR_TAGS], photos=[], colors=Colors(cap=gold, label_base="#5A3210"),
                   **revolve(form, label=label, top=top))


# ================================================================ store fixtures

def _wire_deck(seed: int, w_mm: float, d_mm: float) -> object:
    """A chrome wire deck seen from above: thin wires every 25 mm with three thicker supports."""
    c = Canvas(w_mm, d_mm, 2, "#3A3C40", seed)
    for x in range(0, int(w_mm) + 1, 25):
        c.line([(x, 0), (x, d_mm)], "#D4D7DB", 2.6)
    for y in (6, d_mm / 2, d_mm - 6):
        c.line([(0, y), (w_mm, y)], "#E4E6EA", 5.0)
    return finish(c.array(), "metal", seed, 0.5)


def chrome_wire_shelf() -> Product:
    """A chrome wire shelving unit on four casters (910 x 460 mm, four decks)."""
    W, D, H = 0.91, 0.46, 1.59
    cast = 0.10
    post = 0.025
    zs = [cast + 0.10, cast + 0.55, cast + 1.00, H - 0.02]
    parts = []
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x, y = sx * (W / 2 - post / 2), sy * (D / 2 - post / 2)
        parts += [_p(f"Post{n}", "cylinder", (post, post, H - cast), (x, y, cast + (H - cast) / 2), CHROME, "metal",
                     material="steel"),
                  _wheel(f"Caster{n}", 0.075, 0.025, (x, y, 0.0375)),
                  _p(f"Fork{n}", "box", (0.04, 0.05, 0.03), (x, y, cast - 0.015), CHROME, "metal", collision=False,
                     material="steel")]
    for k, z in enumerate(zs):
        parts += [_p(f"Deck{k}", "box", (W - 0.01, D - 0.01, 0.006), (0, 0, z), CHROME, "metal", faces={"top": 0},
                     material="steel", bevel=0),
                  _p(f"RimF{k}", "box", (W - 0.01, 0.008, 0.025), (0, -D / 2 + 0.004, z - 0.010), CHROME, "metal",
                     collision=False, material="steel", bevel=0),
                  _p(f"RimB{k}", "box", (W - 0.01, 0.008, 0.025), (0, D / 2 - 0.004, z - 0.010), CHROME, "metal",
                     collision=False, material="steel", bevel=0)]
    return Product(slug="chrome_wire_shelf", name="キャスター付きのスチールラック（4 段）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.05), mass_kg=16.0, static=True, material="steel",
                   description="形は一般的なクロムめっきのワイヤーシェルフ（幅 910 mm・奥行き 460 mm・高さ 1590 mm、棚 4 段、"
                               "直径 25 mm の支柱、75 mm のキャスター 4 個）で、寸法・質量は代表値。棚板は網の絵の薄い板で、"
                               "商品を並べる棚板に使える。転がらないよう床に固定して書き出す。",
                   tags=["スチールラック", "ワイヤーシェルフ", "メタルラック", "キャスター付き", "wire shelf",
                         "wire shelving", "chrome wire shelf", "metal rack", "chrome rack", "rolling shelf",
                         *STORE_TAGS, "kitchen", "backyard"], photos=[], colors=Colors(label_base=CHROME),
                   images=[_wire_deck(7951, 900, 450)], parts=parts)


def ceiling_fan() -> Product:
    """A four-blade ceiling fan with a light, hanging from a short downrod (top touches the ceiling)."""
    Dm, H = 1.20, 0.45
    body, wood = "#2E2E32", WALNUT
    parts = [_p("Canopy", "cylinder", (0.13, 0.13, 0.05), (0, 0, H - 0.025), body, "metal", material="metal"),
             _p("Rod", "cylinder", (0.025, 0.025, 0.20), (0, 0, H - 0.15), body, "metal", collision=False,
                material="metal"),
             _p("Motor", "cylinder", (0.20, 0.20, 0.10), (0, 0, 0.17), body, "metal", material="metal"),
             _p("Globe", "dome", (0.17, 0.17, 0.10), (0, 0, 0.10), "#F4F1E8", "frosted", rot=(180, 0, 0),
                collision=False, material="glass")]
    for k in range(4):
        a = math.radians(90 * k)
        r = 0.12 + (Dm / 2 - 0.12) / 2
        parts += [_p(f"Blade{k}", "box", (Dm / 2 - 0.12, 0.13, 0.008), (r * math.cos(a), r * math.sin(a), 0.16),
                     wood, "matte", rot=(8, 0, math.degrees(a)), material="wood", bevel=0.003),
                  _p(f"Arm{k}", "box", (0.10, 0.03, 0.01), (0.13 * math.cos(a), 0.13 * math.sin(a), 0.165), body, "metal",
                     rot=(0, 0, math.degrees(a)), collision=False, material="metal")]
    return Product(slug="ceiling_fan", name="シーリングファン（照明付き）", shape_class="assembly", category="environment",
                   dims=Dimensions(0.40, Dm, depth=Dm), mass_kg=7.0, static=True, mount="ceiling", material="metal",
                   description="形は一般的な 4 枚羽根のシーリングファン（羽根の直径 1200 mm、吊り下げ 450 mm、下に照明のグローブ）で、"
                               "寸法・質量は代表値。上面が天井に付く向き。羽根は回らない。",
                   tags=["シーリングファン", "天井扇", "ファン", "ceiling fan", "fan", "ceiling fan with light", "内装",
                         *HOME_TAGS, "cafe"], photos=[], colors=Colors(label_base=body), images=[], parts=parts)


def track_spotlights() -> Product:
    """A 2 m lighting track rail with four spotlights aimed down and forward (top touches the ceiling)."""
    L, H = 2.00, 0.22
    black = BLACK
    parts = [_p("Rail", "box", (L, 0.035, 0.035), (0, 0, H - 0.0175), black, "metal", material="aluminum", bevel=0.002),
             _p("EndL", "box", (0.02, 0.04, 0.04), (-L / 2 + 0.01, 0, H - 0.02), black, "metal", collision=False,
                material="aluminum"),
             _p("EndR", "box", (0.02, 0.04, 0.04), (L / 2 - 0.01, 0, H - 0.02), black, "metal", collision=False,
                material="aluminum")]
    for k in range(4):
        x = -0.75 + k * 0.5
        tilt = 25.0 if k % 2 == 0 else 35.0
        ty = -math.sin(math.radians(tilt)) * 0.06
        tz = math.cos(math.radians(tilt)) * 0.06
        zc = H - 0.035 - 0.05
        parts += [_p(f"Adapter{k}", "box", (0.05, 0.03, 0.03), (x, 0, H - 0.05), black, "metal", collision=False,
                     material="aluminum"),
                  _p(f"Arm{k}", "box", (0.012, 0.012, 0.04), (x, 0, H - 0.075), black, "metal", collision=False,
                     material="aluminum"),
                  _p(f"Head{k}", "cylinder", (0.065, 0.065, 0.12), (x, ty, zc - tz * 0.5), black, "metal",
                     rot=(-tilt, 0, 0), material="aluminum"),
                  _p(f"Lens{k}", "cylinder", (0.05, 0.05, 0.004), (x, ty * 2.1, zc - tz * 1.5), "#FFF6E0", "light",
                     rot=(-tilt, 0, 0), collision=False, material="glass")]
    return Product(slug="track_spotlights", name="ライティングレールとスポットライト 4 灯", shape_class="assembly",
                   category="environment", dims=Dimensions(0.1803, L, depth=0.1249), mass_kg=3.5, static=True,
                   mount="ceiling", material="aluminum",
                   description="形は店舗・カフェの天井に付ける一般的なライティングレール（長さ 2000 mm）に、黒い円筒のスポット"
                               "ライト 4 灯を手前へ 25〜35° 向けて付けたもので、寸法・質量は代表値。上面が天井に付く向き。"
                               "レンズは光る面の見た目だけ（光源は含まない）。",
                   tags=["ライティングレール", "スポットライト", "ダクトレール", "照明", "track light", "track lighting",
                         "spotlight", "spotlights", "lighting rail", "内装", *STORE_TAGS, "cafe"], photos=[],
                   colors=Colors(label_base=black), images=[], parts=parts)


# ================================================================ electronics

def _phone_screen(seed: int, accent: str) -> object:
    c = Canvas(70, 150, 6, "#0E1116", seed)
    c.gradient(0, 0, 70, 150, mix(accent, "#000000", 0.2), mix(accent, "#0E1116", 0.8))
    c.text(35, 24, "10:08", 13, WHITE, 800)
    c.text(35, 34, "11月8日 日曜日", 3.6, WHITE, 600)
    for r in range(4):
        for k in range(4):
            x, y = 11 + k * 16, 60 + r * 18
            c.rect(x - 5.5, y - 5.5, x + 5.5, y + 5.5, fill=mix(accent, WHITE, 0.15 + 0.12 * ((r + k) % 4)), radius=2.6)
    c.rect(25, 143, 45, 144.5, fill=WHITE, radius=0.7)
    return finish(c.array(), "screen", seed, 0.6)


def _laptop_screen(seed: int) -> object:
    c = Canvas(300, 190, 3, "#1B2A44", seed)
    c.gradient(0, 0, 300, 190, "#2C4A7A", "#14203A")
    c.ellipse(150, 30, 320, 200, fill="#3E66A0")
    c.rect(0, 180, 300, 190, fill="#20242C")
    for k in range(8):
        c.rect(110 + k * 10, 182, 117 + k * 10, 189, fill=mix("#6A8FD0", WHITE, 0.1 * k), radius=1.5)
    c.text(40, 20, "展示品", 9, WHITE, 900)
    return finish(c.array(), "screen", seed, 0.6)


def _keyboard(seed: int) -> object:
    c = Canvas(300, 200, 3, "#C9CCD1", seed)
    c.rect(0, 0, 300, 200, fill="#C9CCD1")
    for r in range(6):
        for k in range(14):
            x, y = 22 + k * 18.5, 18 + r * 17
            c.rect(x - 7.5, y - 6.5, x + 7.5, y + 6.5, fill="#2C2F35", radius=1.5)
    c.rect(100, 128, 200, 190, fill="#BABEC4", radius=4)
    return finish(c.array(), "metal", seed, 0.4)


def laptop_open() -> Product:
    """An open 13-inch laptop: the base collides, the screen is look only above it."""
    W, D = 0.300, 0.210
    base_h = 0.015
    tilt = 105.0
    sh = 0.200
    a = math.radians(tilt - 90)
    yc = D / 2 + math.sin(a) * sh / 2
    zc = base_h + math.cos(a) * sh / 2
    imgs = [_laptop_screen(7961), _keyboard(7962)]
    parts = [_p("Base", "box", (W, D, base_h), (0, 0, base_h / 2), "#BABEC4", "metal", faces={"top": 1},
                material="aluminum", bevel=0.003),
             _p("Lid", "box", (W, 0.006, sh), (0, yc + 0.003, zc), "#BABEC4", "metal", rot=(-(tilt - 90), 0, 0),
                material="aluminum", bevel=0.003),
             _p("Screen", "box", (W - 0.016, 0.001, sh - 0.016), (0, yc - 0.0005, zc), "#14203A", "screen",
                rot=(-(tilt - 90), 0, 0), faces={"front": 0}, collision=False, material="glass", bevel=0)]
    depth = D + math.sin(a) * sh + 0.006
    return Product(slug="laptop_open", name="ノートパソコン（13 インチ・開いた状態）", shape_class="assembly",
                   category="household", dims=Dimensions(base_h + math.cos(a) * sh + 0.003, W, depth=depth),
                   mass_kg=1.3, material="aluminum",
                   description="形は一般的な 13 インチのノートパソコン（300 × 210 mm・厚さ 15 mm）を 105° 開いたもので、"
                               "寸法・質量は代表値。画面は展示中の待ち受けの絵。名前・メーカー名はすべて架空。",
                   tags=["ノートパソコン", "ノート PC", "パソコン", "laptop", "notebook computer", "laptop computer",
                         "open laptop", *ELEC_TAGS, *OFFICE_TAGS], photos=[], colors=Colors(label_base="#BABEC4"),
                   images=imgs, parts=parts)


def device_display_table() -> Product:
    """A phone-shop display table: a white top with six phones on tilted stands and security cables, and two
    tablets; the middle is left free for laptops."""
    W, D, H = 1.60, 0.80, 0.90
    accents = ["#3E7BD8", "#D85A8A", "#3EAE8A", "#8A5AD8", "#D8A03E", "#5A6A7A"]
    imgs = [_phone_screen(7970 + k, a) for k, a in enumerate(accents)]
    parts = [_p("Top", "box", (W, D, 0.04), (0, 0, H - 0.02), WHITE, "matte", material="wood", bevel=0.006),
             _p("Base", "box", (W - 0.20, D - 0.20, H - 0.04), (0, 0, (H - 0.04) / 2), OAK, "matte", material="wood"),
             _p("Kick", "box", (W - 0.22, D - 0.22, 0.06), (0, 0, 0.03), BLACK, "matte", collision=False,
                material="wood")]
    tilt = 20.0
    for k in range(6):
        row, col = divmod(k, 3)
        x = -0.65 + col * 0.18 if row == 0 else 0.29 + col * 0.18
        y = -0.24
        z = H + 0.005
        parts += [_p(f"Stand{k}", "box", (0.08, 0.10, 0.01), (x, y, z), CHROME, "metal", collision=False,
                     material="aluminum", bevel=0.002),
                  _p(f"Phone{k}", "box", (0.072, 0.150, 0.008), (x, y + 0.01, z + 0.035), BLACK, "glossy",
                     rot=(tilt + 50, 0, 0), collision=False, material="glass", bevel=0.004),
                  _p(f"PhoneScreen{k}", "box", (0.066, 0.143, 0.001), (x, y + 0.01 - 0.0045 * math.cos(math.radians(70)),
                                                                      z + 0.035 + 0.0045 * math.sin(math.radians(70))),
                     "#0E1116", "screen", rot=(tilt + 50, 0, 0), faces={"top": k}, collision=False, material="glass",
                     bevel=0),
                  _p(f"Cable{k}", "cylinder", (0.006, 0.006, 0.12), (x, y + 0.10, z + 0.004), "#3A3D42", "plastic",
                     rot=(90, 0, 0), collision=False, material="plastic"),
                  _p(f"Tag{k}", "box", (0.07, 0.003, 0.045), (x, -D / 2 + 0.04, z + 0.02), WHITE, "matte",
                     rot=(-20, 0, 0), collision=False, material="paper", bevel=0)]
    for k, x in enumerate((-0.55, 0.55)):  # tablets lying in stands at the back
        parts += [_p(f"Tablet{k}", "box", (0.25, 0.17, 0.008), (x, 0.20, H + 0.07), BLACK, "glossy",
                     rot=(-60, 0, 0), collision=False, material="glass", bevel=0.005),
                  _p(f"TabletScreen{k}", "box", (0.24, 0.16, 0.001), (x, 0.20 - 0.0045 * math.sin(math.radians(60)),
                                                                     H + 0.07 + 0.0045 * math.cos(math.radians(60))),
                     "#0E1116", "screen", rot=(-60, 0, 0), faces={"top": k + 1}, collision=False, material="glass",
                     bevel=0),
                  _p(f"TabletStand{k}", "box", (0.12, 0.08, 0.05), (x, 0.24, H + 0.025), CHROME, "metal",
                     collision=False, material="aluminum")]
    return Product(slug="device_display_table", name="スマホ・タブレットの展示台", shape_class="assembly",
                   category="fixture", dims=Dimensions(H + 0.15, W, depth=D), mass_kg=70.0, static=True,
                   material="wood",
                   description="形は携帯ショップ・家電量販店の一般的な端末の展示台（1600 × 800 mm・高さ 900 mm、白い天板の手前に"
                               "盗難防止のケーブル付きのスマートフォン 6 台を斜めのスタンドに、奥にタブレット 2 台）で、寸法・質量は代表値。"
                               "中央はノートパソコンを載せる空き。端末は見た目だけで、当たるのは天板と台。名前・画面は架空。",
                   tags=["展示台", "スマホの展示台", "携帯ショップ", "スマートフォン", "タブレット", "device display table",
                         "phone display table", "smartphone display", "display table", "tablet display", *ELEC_TAGS,
                         *STORE_TAGS], photos=[], colors=Colors(label_base=WHITE), images=imgs, parts=parts)


# ================================================================ garden centre

def seedling_tray() -> Product:
    """A 4 x 8 plug tray of young seedlings (the tray collides, the leaves are look only)."""
    W, D, H = 0.54, 0.28, 0.06
    cols, rows = 8, 4
    soil = "#4A3626"
    parts = [_p("Tray", "box", (W, D, H), (0, 0, H / 2), BLACK, "plastic", material="plastic", bevel=0.004),
             _p("Soil", "box", (W - 0.02, D - 0.02, 0.004), (0, 0, H + 0.001), soil, "matte", collision=False,
                material="dirt", bevel=0)]
    rng = random.Random(7981)
    for r in range(rows):
        for k in range(cols):
            x = -W / 2 + (k + 0.5) * W / cols
            y = -D / 2 + (r + 0.5) * D / rows
            parts.append(_p(f"Rim{r}{k}", "box", (W / cols - 0.004, D / rows - 0.004, 0.002), (x, y, H + 0.004), "#2A2C30",
                            "plastic", collision=False, material="plastic", bevel=0))
            h = rng.uniform(0.035, 0.06)
            parts.append(_p(f"Sprout{r}{k}", "star", (h * 1.3, h * 1.3, h * 0.5), (x, y, H + 0.006 + h * 0.25),
                            mix(LEAF, "#9AC060", rng.uniform(0, 0.5)), "matte", rot=(0, 0, rng.uniform(0, 90)),
                            profile=[[4, 0.15, 1.3]], collision=False, material="leaf_grass"))
    return Product(slug="seedling_tray", name="野菜の苗のトレー（32 穴）", shape_class="assembly", category="household",
                   dims=Dimensions(H + 0.04, W, depth=D), mass_kg=1.8, material="plastic",
                   description="形は園芸店の一般的なセルトレー（540 × 280 mm・高さ 60 mm、4 × 8 の 32 穴）に双葉の苗を植えた"
                               "もので、寸法・質量は代表値。当たり判定はトレーだけで、苗は見た目だけ。",
                   tags=["苗", "苗トレー", "セルトレー", "野菜の苗", "seedling tray", "seedlings", "plug tray",
                         "vegetable seedlings", "plant tray", *GARDEN_TAGS], photos=[], colors=Colors(label_base=LEAF),
                   images=[], parts=parts)


def garden_bench_table() -> Product:
    """A galvanised nursery bench (平台) with a mesh top, for pots and seedling trays."""
    W, D, H = 1.80, 0.90, 0.75
    parts = [_p("Top", "box", (W, D, 0.02), (0, 0, H - 0.01), GALV, "metal", faces={"top": 0}, material="steel", bevel=0)]
    for nm, x, y, w, d in (("FrameF", 0, -D / 2 + 0.02, W, 0.04), ("FrameB", 0, D / 2 - 0.02, W, 0.04),
                           ("FrameL", -W / 2 + 0.02, 0, 0.04, D), ("FrameR", W / 2 - 0.02, 0, 0.04, D)):
        parts.append(_p(nm, "box", (w, d, 0.05), (x, y, H - 0.045), GALV, "metal", material="steel", bevel=0.002))
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1))):
        parts.append(_p(f"Leg{n}", "box", (0.04, 0.04, H - 0.07), (sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), (H - 0.07) / 2),
                        GALV, "metal", material="steel", bevel=0.002))
    parts.append(_p("Brace", "box", (W - 0.10, 0.03, 0.03), (0, 0, 0.15), GALV, "metal", collision=False,
                    material="steel"))
    return Product(slug="garden_bench_table", name="園芸店の平台（金網、1800 × 900）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=32.0, static=True, material="steel",
                   description="形は園芸店の一般的な苗・鉢を並べる平台（1800 × 900 mm・高さ 750 mm、亜鉛めっきの角パイプの枠に"
                               "金網の天板）で、寸法・質量は代表値。天板は網の絵の板で、商品を並べる棚板に使える。",
                   tags=["平台", "苗の台", "園芸台", "陳列台", "garden table", "nursery bench", "plant bench",
                         "display bench", "garden flat table", "potting bench", *GARDEN_TAGS, *STORE_TAGS], photos=[],
                   colors=Colors(label_base=GALV), images=[_wire_deck(7982, 1800, 900)], parts=parts)


# ================================================================ office and hospital

def _board_img(seed: int) -> object:
    c = Canvas(1200, 900, 1, WHITE, seed)
    c.gradient(0, 0, 1200, 900, "#FFFFFF", "#F1F3F5")
    c.text(240, 110, "週次ミーティング", 56, "#1E4FA0", 800)
    c.line([(120, 160), (560, 160)], "#1E4FA0", 4)
    for k, s in enumerate(("・進捗の確認", "・課題の洗い出し", "・次回までの宿題")):
        c.text(330, 240 + k * 80, s, 40, "#222222", 700)
    c.rect(700, 200, 1080, 560, outline="#C62828", width=4)
    c.line([(740, 520), (820, 420), (900, 460), (1000, 300), (1050, 330)], "#C62828", 5)
    c.text(890, 620, "売上の推移", 36, "#C62828", 700)
    return finish(c.array(), "paper", seed, 0.25)


def mobile_whiteboard() -> Product:
    """A 1200 x 900 mm whiteboard on a mobile stand with four casters and a marker tray."""
    BW, BH = 1.20, 0.90
    W, D, H = 1.30, 0.55, 1.80
    frame = "#C9CCD1"
    z_mid = 0.85 + BH / 2
    parts = [_p("Board", "box", (BW, 0.02, BH), (0, 0, z_mid), WHITE, "glossy", faces={"front": 0, "back": 0},
                material="metal", bevel=0.004),
             *[_p(f"Frame{nm}", "box", size, (x, 0.001, z), frame, "metal", collision=False, material="aluminum",
                  bevel=0.003)
               for nm, size, x, z in (("T", (BW + 0.03, 0.024, 0.015), 0, z_mid + BH / 2 + 0.0075),
                                      ("B", (BW + 0.03, 0.024, 0.015), 0, z_mid - BH / 2 - 0.0075),
                                      ("L", (0.015, 0.024, BH), -BW / 2 - 0.0075, z_mid),
                                      ("R", (0.015, 0.024, BH), BW / 2 + 0.0075, z_mid))],
             _p("Tray", "box", (BW * 0.8, 0.06, 0.02), (0, -0.04, 0.85), frame, "metal", material="aluminum")]
    for s in (-1, 1):
        x = s * (W / 2 - 0.02)
        parts += [_p(f"Upright{'LR'[s > 0]}", "box", (0.035, 0.035, H - 0.10), (x, 0, 0.10 + (H - 0.10) / 2), frame,
                     "metal", material="aluminum", bevel=0.002),
                  _p(f"Foot{'LR'[s > 0]}", "box", (0.05, D, 0.04), (x, 0, 0.10), frame, "metal", material="aluminum")]
        for t in (-1, 1):
            parts.append(_wheel(f"Caster{'LR'[s > 0]}{'FB'[t > 0]}", 0.07, 0.025, (x, t * (D / 2 - 0.03), 0.035)))
    parts += [_p(f"Marker{k}", "cylinder", (0.016, 0.016, 0.13), (-0.25 + k * 0.05, -0.04, 0.868), col, "plastic",
                 rot=(0, 90, 0), collision=False, material="plastic")
              for k, col in enumerate(("#222222", "#C62828", "#1E4FA0"))]
    parts.append(_p("Eraser", "box", (0.13, 0.05, 0.035), (0.20, -0.04, 0.877), "#2C2F35", "matte", collision=False,
                    material="fabric"))
    return Product(slug="mobile_whiteboard", name="ホワイトボード（脚付き・キャスター）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=22.0, static=True, material="aluminum",
                   description="形はオフィス・会議室の一般的な脚付きホワイトボード（板面 1200 × 900 mm、全高 1800 mm、"
                               "キャスター 4 個、マーカー受けにマーカー 3 本とイレーザー）で、寸法・質量は代表値。板面には"
                               "会議のメモの絵（文字は架空）。転がらないよう床に固定して書き出す。",
                   tags=["ホワイトボード", "白板", "会議", "whiteboard", "mobile whiteboard", "white board", "dry erase board",
                         "meeting room", *OFFICE_TAGS, "school"], photos=[], colors=Colors(label_base=WHITE),
                   images=[_board_img(7991)], parts=parts)


def wheelchair() -> Product:
    """A standard folding wheelchair: big rear wheels with hand rims, front casters, a sling seat and back."""
    W, D, H = 0.63, 1.00, 0.90
    frame, fabric = "#9AA0A6", "#2C3E5A"
    rw = 0.60
    ry = 0.20  # rear axle (back is +Y)
    seat_z = 0.47
    parts = [_p("Seat", "box", (0.42, 0.42, 0.03), (0, 0.02, seat_z), fabric, "matte", material="fabric", bevel=0.008),
             _p("Back", "box", (0.42, 0.03, 0.42), (0, 0.24, seat_z + 0.24), fabric, "matte", rot=(-8, 0, 0),
                material="fabric", bevel=0.008)]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        xw = s * (W / 2 - 0.03)
        xf = s * 0.23
        parts += [_p(f"Wheel{side}", "torus", (rw, rw, 0.03), (xw, ry, rw / 2), RUBBER, "matte", rot=(0, 90, 0),
                     material="rubber"),
                  _p(f"Hub{side}", "cylinder", (rw - 0.04, rw - 0.04, 0.006), (xw, ry, rw / 2), "#C9CCD1", "metal",
                     rot=(0, 90, 0), collision=False, material="aluminum"),
                  _p(f"HandRim{side}", "torus", (rw - 0.06, rw - 0.06, 0.016), (xw + s * 0.025, ry, rw / 2), CHROME,
                     "metal", rot=(0, 90, 0), collision=False, material="steel"),
                  _wheel(f"Caster{side}", 0.15, 0.03, (xf, -0.30, 0.075)),
                  _seg(f"CasterFork{side}", (xf, -0.30, 0.15), (xf, -0.28, seat_z - 0.02), 0.022, frame, "metal",
                       collision=False, material="steel"),
                  _seg(f"SideRail{side}", (xf, -0.28, seat_z - 0.02), (xf, 0.22, seat_z - 0.02), 0.022, frame, "metal",
                       collision=False, material="steel"),
                  _seg(f"BackPost{side}", (xf, 0.22, seat_z - 0.02), (xf, 0.30, H), 0.022, frame, "metal",
                       collision=False, material="steel"),
                  _p(f"Handle{side}", "cylinder", (0.03, 0.03, 0.11), (xf, 0.34, H - 0.01), BLACK, "matte",
                     rot=(90, 0, 0), collision=False, material="rubber"),
                  _p(f"Armrest{side}", "box", (0.05, 0.30, 0.03), (xf, 0.02, seat_z + 0.22), BLACK, "matte",
                     collision=False, material="plastic"),
                  _seg(f"ArmPost{side}", (xf, 0.10, seat_z), (xf, 0.10, seat_z + 0.20), 0.02, frame, "metal",
                       collision=False, material="steel"),
                  _seg(f"LegRest{side}", (xf, -0.26, seat_z - 0.02), (xf * 0.85, -0.42, 0.12), 0.02, frame, "metal",
                       collision=False, material="steel"),
                  _p(f"Footplate{side}", "box", (0.16, 0.12, 0.01), (xf * 0.55, -0.44, 0.11), "#3A3D42", "plastic",
                     collision=False, material="plastic")]
    return Product(slug="wheelchair", name="車椅子（自走式・標準形）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=15.0, static=True, material="aluminum",
                   description="形は一般的な自走式の折りたたみ車椅子（全幅 630 mm・全長 1000 mm・全高 900 mm、後輪 24 インチ・"
                               "前のキャスター 6 インチ、紺の布の座面と背もたれ）で、寸法・質量は代表値。正面（足の向き）が -Y。"
                               "転がらないよう床に固定して書き出す。当たり判定は座面・背もたれ・車輪。",
                   tags=["車椅子", "車いす", "介護用品", "wheelchair", "manual wheelchair", "folding wheelchair",
                         *MEDICAL_TAGS], photos=[], colors=Colors(label_base=fabric), images=[], parts=parts)


PRODUCTS = {f.__name__: f for f in (
    throw_cushion, area_rug, tv_remote,
    pet_wire_cage, puppy_showcase, aquarium_tank, pet_treat_bulk_case,
    wine_step_rack, wine_crate, beer_bottle_334ml,
    chrome_wire_shelf, ceiling_fan, track_spotlights,
    laptop_open, device_display_table,
    seedling_tray, garden_bench_table,
    mobile_whiteboard, wheelchair,
)}
