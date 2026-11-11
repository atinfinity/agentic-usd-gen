"""Fictional product designs: home-center garden goods (a clay pot, potting soil, a watering can, a hose
reel and a potted house plant).

No real product names, brands or logos; shapes and sizes are typical values. Front is -Y. All are dynamic
rigid bodies.
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _cyl, _face, back_info, seal_crimp
from .store_more import _rod

WHITE = "#FFFFFF"
TERRACOTTA = "#B5653A"
SOIL = "#3B2A1E"
LEAF, LEAF_DARK = "#4C8F3A", "#2F6526"


def _p(name, shape, size, center, color, finish_="plastic", rot=None, faces=None, collision=True, material=None,
       **kw) -> Part:
    return Part(name=name, shape=shape, size=list(size), center=list(center), rotation=list(rot or [0, 0, 0]),
                color=color, finish=finish_, faces=faces, collision=collision, material=material, **kw)


def _seg(name, p0, p1, d, color, finish_="plastic", collision=True, material=None) -> Part:
    """A round bar from p0 to p1 in the XZ plane (rotation about Y) or the YZ plane (rotation about X)."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    if abs(y1 - y0) < 1e-9:
        rot = [0.0, math.degrees(math.atan2(x1 - x0, z1 - z0)), 0.0]
    else:
        rot = [math.degrees(math.atan2(-(y1 - y0), z1 - z0)), 0.0, 0.0]
    return _p(name, "cylinder", (d, d, math.dist(p0, p1)), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color,
              finish_, rot, collision=collision, material=material)


def _soil_top(d_mm: float, seed: int, color: str = SOIL) -> np.ndarray:
    c = Canvas(d_mm, d_mm, 6, color, seed)
    c.gradient(0, 0, d_mm, d_mm, mix(color, WHITE, 0.08), mix(color, "#000000", 0.15))
    for _ in range(int(d_mm * d_mm / 6)):
        x, y = c.rng.uniform(0, d_mm), c.rng.uniform(0, d_mm)
        r = c.rng.uniform(0.3, 1.4)
        c.ellipse(x - r, y - r, x + r, y + r, fill=c.rng.choice(["#5A4330", "#2A1D14", "#C9B48A", "#6B5038"]))
    return finish(c.array(), "paper", seed, 0.8)


def _leaves(w_mm: float, h_mm: float, seed: int, variegated: bool = True) -> np.ndarray:
    """Heart-shaped leaves seen from above (a pothos-like foliage texture)."""
    c = Canvas(w_mm, h_mm, 4, LEAF_DARK, seed)
    c.gradient(0, 0, w_mm, h_mm, "#3F7F33", "#24521E")
    rng = c.rng
    for _ in range(int(w_mm * h_mm / 900)):
        x, y = rng.uniform(0, w_mm), rng.uniform(0, h_mm)
        s = rng.uniform(26, 48)
        a = rng.uniform(0, 2 * math.pi)
        col = mix(LEAF, rng.choice(["#6FB04F", "#3E7E2E", "#5C9E40"]), rng.uniform(0.2, 0.8))
        pts = []
        for t in np.linspace(0, 2 * math.pi, 24):  # cardioid-like leaf outline
            r = s * 0.5 * (1 - math.sin(t)) * 0.8 + s * 0.1
            px, py = r * math.cos(t), r * math.sin(t)
            pts.append((x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)))
        c.polygon(pts, fill=col)
        c.line([(x, y), (x + s * 0.6 * math.cos(a - math.pi / 2), y + s * 0.6 * math.sin(a - math.pi / 2))],
               mix(col, WHITE, 0.25), 0.8)
        if variegated and rng.random() < 0.5:
            c.ellipse(x - s * 0.12, y - s * 0.3, x + s * 0.14, y - s * 0.06, fill=mix(col, "#E9E3A0", 0.6))
    return finish(c.array(), "paper", seed, 0.5)


# ---------------------------------------------------------------- clay pot


def flower_pot() -> Product:
    """An unglazed clay pot, size 6 (18 cm), hollow, with a price sticker on the rim."""
    D, H = 0.18, 0.16
    st = Canvas(30, 18, 12, WHITE, 9401)
    st.gradient(0, 0, 30, 18, "#FFFFFF", "#ECECEC")
    st.rect(0, 0, 30, 5, fill="#2E7D32")
    st.text(15, 2.6, "素焼き鉢", 2.8, WHITE, 900)
    st.text(15, 9.5, "6号 18cm", 3.2, INK, 900)
    st.text(15, 14.6, "398円", 3.6, "#C62828", 900)
    sticker = _face(st.array(), "paper", 9401, 0.4, 4)
    prof = [[0, 0], [0.74, 0], [0.80, 0.04], [0.97, 0.84], [1.0, 0.86], [1.0, 1.0], [0.90, 1.0], [0.88, 0.86],
            [0.72, 0.10], [0, 0.10]]
    parts = [_p("Pot", "revolve", (D, D, H), (0, 0, H / 2), TERRACOTTA, "matte", profile=prof, material="ceramic"),
             _p("Sticker", "box", (0.030, 0.0005, 0.018), (0, -D / 2 - 0.0003, H - 0.011), WHITE, "matte",
                faces={"front": 0}, collision=False, material="paper")]
    return Product(slug="flower_pot", name="素焼き鉢 6号（18cm）", shape_class="assembly", category="household",
                   dims=Dimensions(H, D, depth=D + 0.0006), mass_kg=0.95, material="ceramic",
                   description="形は一般的な素焼きの植木鉢 6 号（口径 180 mm・高さ 160 mm、縁の帯・底穴あり）で、"
                               "寸法・質量は代表値。中は空（当たり判定は外形の凸包）。",
                   tags=["植木鉢", "鉢", "素焼き鉢", "テラコッタ", "園芸", "ガーデニング", "ホームセンター",
                         "flower pot", "clay pot", "terracotta pot", "planter"],
                   photos=[], colors=Colors(label_base=TERRACOTTA), images=[sticker], parts=parts)


# ---------------------------------------------------------------- potting soil


def soil_bag() -> Product:
    """A 14 L bag of potting soil (pouch, gusseted bottom so it stands)."""
    W, H = 340.0, 520.0
    green, brown = "#2E6B2E", "#5A3B22"
    c = Canvas(W, H, 3, "#F4EFE2", 9411)
    c.gradient(0, 0, W, H, "#FAF6EC", "#E6DCC6")
    seal_crimp(c, 0, 0, W, 16, "#D9CFB6", 2.6)
    c.rect(0, 16, W, 120, fill=green)
    c.text(W / 2, 52, "花と野菜の", 24, WHITE, 900)
    c.text(W / 2, 96, "培養土", 46, WHITE, 900)
    c.rect(0, 120, W, 128, fill="#F2C230")
    soil = Canvas(W, 150, 3, SOIL, 9412)
    soil.gradient(0, 0, W, 150, "#4A3526", "#2A1D14")
    for _ in range(1600):
        x, y = soil.rng.uniform(0, W), soil.rng.uniform(0, 150)
        r = soil.rng.uniform(0.6, 2.4)
        soil.ellipse(x - r, y - r, x + r, y + r, fill=soil.rng.choice(["#6B5038", "#C9B48A", "#1E140E", "#7A5A3A"]))
    c.img.paste(soil.img.resize((round(W * c.s), round(150 * c.s))), (0, round(330 * c.s)))
    for k, (x, col) in enumerate(((80, "#E53935"), (170, "#FBC02D"), (260, "#8E24AA"))):  # flowers
        for a in range(5):
            t = a * 2 * math.pi / 5
            c.ellipse(x + 18 * math.cos(t) - 14, 250 + 18 * math.sin(t) - 14, x + 18 * math.cos(t) + 14,
                      250 + 18 * math.sin(t) + 14, fill=col)
        c.ellipse(x - 9, 241, x + 9, 259, fill="#FFE082")
        c.rect(x - 2, 270, x + 2, 330, fill=LEAF)
    c.rect(W / 2 - 100, 140, W / 2 + 100, 196, fill=WHITE, radius=10)
    c.text(W / 2, 160, "元肥入り  すぐ植えられる", 13, green, 900)
    c.text(W / 2, 182, "pH 調整済み", 11, brown, 800)
    c.ellipse(W - 100, 200, W - 14, 286, fill="#C62828", outline=WHITE, width=2.5)
    c.text(W - 57, 236, "14L", 24, WHITE, 900)
    c.text(W - 57, 262, "容量", 8, WHITE, 700)
    c.rect(0, H - 10, W, H, fill=green)
    front = trim_safe(edge_shade(finish(c.array(), "film", 9411, 1.0), 30, 0.15))
    b = Canvas(W, H, 3, "#F4EFE2", 9413)
    b.gradient(0, 0, W, H, "#FAF6EC", "#E6DCC6")
    seal_crimp(b, 0, 0, W, 16, "#D9CFB6", 2.6)
    b.rect(0, 16, W, 40, fill=green)
    b.text(W / 2, 28, "花と野菜の培養土 14L", 13, WHITE, 900)
    b.rect(16, 56, W - 16, 210, fill=WHITE, radius=5)
    back_info(b, 24, 64, W - 24, [("品名", "培養土"), ("容量", "14L"), ("原料", "赤玉土・腐葉土・ピートモス・バーミキュライト"),
                                  ("肥料", "元肥入り（N-P-K 0.5-0.6-0.4）"), ("pH", "6.0〜6.5")], 9.0)
    b.rect(16, 226, W - 16, 330, fill=WHITE, radius=5)
    b.text(W / 2, 244, "使い方", 11, green, 900)
    b.paragraph(28, 260, W - 28, "1. 鉢底石を入れ、培養土を鉢の 8 分目まで入れます。\n2. 苗を植えて、たっぷり水をやります。\n"
                "3. 2〜3 週間後から追肥をしてください。", 9.0, INK, 500)
    b.paragraph(28, 350, W - 28, "開封後は袋の口を閉じ、雨の当たらない所に保管してください。\n" + NOTICE, 8.0, INK, 400)
    b.rect(16, 420, 160, 500, fill=WHITE, radius=5)
    b.barcode(26, 428, 124, 64)
    b.recycle(210, 460, 28, "プラ", green, sub="袋")
    b.rect(0, H - 10, W, H, fill=green)
    back = trim_safe(edge_shade(finish(b.array(), "film", 9414, 1.0), 30, 0.15))
    return Product(slug="soil_bag", name="花と野菜の培養土 14L", shape_class="pouch", category="household",
                   dims=Dimensions(0.52, 0.34, depth=0.11, gusset=0.11, square=3), mass_kg=7.0, material="film",
                   description="形は一般的な 14 L 入りの培養土の袋（高さ 520 mm・幅 340 mm・厚さ約 110 mm、底マチで自立、"
                               "上端だけシール）で、寸法・質量は代表値。",
                   tags=["培養土", "土", "園芸用土", "花の土", "野菜の土", "園芸", "ガーデニング", "ホームセンター",
                         "potting soil", "soil bag", "potting mix"],
                   photos=[], colors=Colors(label_base="#F4EFE2"), images=[front, back],
                   faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- watering can


def watering_can() -> Product:
    """A 4 L plastic watering can: oval body, a long spout to the front (-Y) with a rose, a top handle."""
    green = "#3E9B4F"
    lab = Canvas(90, 60, 10, WHITE, 9421)
    lab.gradient(0, 0, 90, 60, "#FFFFFF", "#EDEDED")
    lab.rect(0, 0, 90, 14, fill=green)
    lab.text(45, 7, "じょうろ", 8, WHITE, 900)
    lab.text(45, 26, "4L  ハス口付き", 7, INK, 900)
    lab.text(45, 38, "ポリプロピレン", 5, INK, 700)
    lab.barcode(22, 43, 46, 14)
    label = _face(lab.array(), "paper", 9421, 0.4)
    bw, bd, bh = 0.15, 0.22, 0.20
    parts = [_p("Body", "cylinder", (bw, bd, bh), (0, 0.03, bh / 2), green),
             _p("Cap", "cylinder", (0.07, 0.07, 0.015), (0, 0.06, bh + 0.0075), mix(green, "#000000", 0.15)),
             _seg("Spout", (0, -0.06, 0.05), (0, -0.26, 0.24), 0.026, green),
             _p("Rose", "cylinder", (0.055, 0.055, 0.022), (0, -0.268, 0.252), "#F2F2EE", rot=(-45.0, 0, 0)),
             _seg("HandleFront", (0, -0.04, bh), (0, -0.01, bh + 0.08), 0.022, green),
             _seg("HandleTop", (0, -0.01, bh + 0.08), (0, 0.13, bh + 0.08), 0.022, green),
             _seg("HandleBack", (0, 0.13, bh + 0.08), (0, 0.13, bh - 0.02), 0.022, green),
             _p("Label", "box", (0.0005, 0.09, 0.06), (bw / 2 + 0.0003, 0.03, 0.10), WHITE, "matte",
                faces={"right": 0}, collision=False, material="paper")]
    return Product(slug="watering_can", name="じょうろ 4L ハス口付き", shape_class="assembly", category="household",
                   dims=Dimensions(0.29, 0.15, depth=0.43), mass_kg=0.45, material="plastic",
                   description="形は一般的な樹脂のじょうろ（容量 4 L、楕円の胴・前に長い注ぎ口とハス口・上の持ち手、"
                               "全長約 430 mm・高さ約 290 mm）で、寸法・質量は代表値。注ぎ口は −Y（正面）。",
                   tags=["じょうろ", "ジョウロ", "水やり", "園芸", "ガーデニング", "ホームセンター", "watering can",
                         "plastic watering can"],
                   photos=[], colors=Colors(label_base=green), images=[label], parts=parts)


# ---------------------------------------------------------------- hose reel


def _coil(w_mm: float, seed: int, color: str) -> np.ndarray:
    """The side of a wound hose: concentric turns."""
    c = Canvas(w_mm, w_mm, 4, color, seed)
    r = w_mm / 2
    c.gradient(0, 0, w_mm, w_mm, mix(color, WHITE, 0.1), mix(color, "#000000", 0.2))
    for k, rr in enumerate(np.arange(r, r * 0.42, -6.0)):
        c.ellipse(r - rr, r - rr, r + rr, r + rr, outline=mix(color, "#000000", 0.35 if k % 2 else 0.15), width=1.2)
    c.ellipse(r * 0.58, r * 0.58, r * 1.42, r * 1.42, fill="#E8E2D2")  # the drum's hub
    c.text(r, r, "20m", w_mm * 0.08, INK, 900)
    return finish(c.array(), "film", seed, 0.4)


def hose_reel() -> Product:
    """A 20 m garden hose on a hand-crank reel with a carrying handle (the drum axis is X)."""
    W, D, H = 0.40, 0.34, 0.50
    frame, hose = "#ECE7DA", "#3E9B4F"
    lab = Canvas(120, 70, 8, "#F7F3EA", 9431)
    lab.gradient(0, 0, 120, 70, "#FFFFFF", "#ECE7DA")
    lab.rect(0, 0, 120, 16, fill=hose)
    lab.text(60, 8, "ホースリール 20m", 8, WHITE, 900)
    lab.text(60, 30, "内径 15mm  ノズル 7パターン", 6.2, INK, 900, max_w=112)
    lab.text(60, 44, "ねじれにくいホース", 6.2, mix(hose, INK, 0.4), 800)
    lab.barcode(36, 50, 48, 17)
    label = _face(lab.array(), "paper", 9431, 0.4)
    coil = _coil(340, 9432, hose)
    dc = 0.34  # drum (coil) diameter
    zc = 0.04 + dc / 2
    parts = [_p("Coil", "cylinder", (dc, dc, 0.20), (0, 0, zc), hose, rot=(0, 90, 0), faces={"top": 1, "bottom": 1},
                material="rubber")]
    for k, s in enumerate((-1, 1)):
        x = s * 0.13
        parts += [_p(f"Side{k}", "box", (0.02, D, 0.44), (x + s * 0.01, 0, 0.26), frame, bevel=0.01),
                  _p(f"Foot{k}", "box", (0.04, D, 0.04), (x + s * 0.01, 0, 0.02), frame),
                  _p(f"Wheel{k}", "cylinder", (0.10, 0.10, 0.03), (s * (W / 2 - 0.015), 0.10, 0.05), "#2A2C30",
                     "matte", rot=(0, 90, 0), material="rubber")]
    parts += [_rod("HandleBar", (-0.14, 0, 0.49), (0.14, 0, 0.49), 0.026, frame, "plastic", collision=True),
              _p("Crank", "box", (0.02, 0.10, 0.02), (0.16, -0.04, zc), "#2A2C30", "matte"),
              _p("CrankKnob", "cylinder", (0.022, 0.022, 0.05), (0.185, -0.09, zc), "#2A2C30", "matte",
                 rot=(0, 90, 0)),
              # axles: the drum turns on one between the side plates, the wheels on one at the back
              _rod("DrumAxle", (-0.13, 0, zc), (0.13, 0, zc), 0.024, "#2A2C30", "matte"),
              _rod("WheelAxle", (-W / 2 + 0.015, 0.10, 0.05), (W / 2 - 0.015, 0.10, 0.05), 0.016, "#2A2C30", "matte"),
              # the nozzle hangs on the outside of the left side plate
              _p("Nozzle", "box", (0.04, 0.06, 0.12), (-0.17, -0.10, 0.36), "#F9B000", bevel=0.01),
              _p("Label", "box", (0.12, 0.0005, 0.07), (0, -dc / 2 - 0.0003, zc), WHITE, "matte",
                 faces={"front": 0}, collision=False, material="paper")]
    for p in parts:
        if p.material is None:
            p.material = "plastic"
    return Product(slug="hose_reel", name="ホースリール 20m", shape_class="assembly", category="household",
                   dims=Dimensions(H, W + 0.02, depth=D + 0.0006), mass_kg=3.6, material="plastic",
                   description="形は一般的な手回しの散水ホースリール（ホース 20 m・内径 15 mm、幅約 420 × 奥行き 340 × "
                               "高さ 500 mm、上に持ち手・下に車輪 2 個、ノズル付き）で、寸法・質量は代表値。"
                               "巻いたホースは円柱で表す。",
                   tags=["ホースリール", "ホース", "散水", "水やり", "園芸", "ガーデニング", "ホームセンター",
                         "hose reel", "garden hose", "garden hose reel"],
                   photos=[], colors=Colors(label_base=frame), images=[label, coil], parts=parts)


# ---------------------------------------------------------------- potted house plant


def _clump(name: str, center, w: float, h_up: float, h_down: float, tilt: float, toward: float, color: str,
           img: int, collision: bool = False) -> list[Part]:
    """A rounded leaf clump: an ellipsoid-like pair of domes (a taller top and a shallow underside) about `center`,
    its axis tilted `tilt` degrees outward toward the direction `toward` (degrees from +X)."""
    a = math.radians(toward)
    rx, ry = -tilt * math.sin(a), tilt * math.cos(a)
    cx_, sx_ = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    cy_, sy_ = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    u = np.array([sy_ * cx_, -sx_, cy_ * cx_])  # R = Ry @ Rx applied to +Z
    c = np.asarray(center, float)
    leaf = dict(finish_="matte", material="leaf_grass")
    return [_p(name, "dome", (w, w * 0.94, h_up), c + u * h_up / 2, color, rot=(rx, ry, 0), faces={"top": img},
               collision=collision, **leaf),
            _p(f"{name}Under", "dome", (w, w * 0.94, h_down), c - u * h_down / 2, color, rot=(180.0 + rx, ry, 0),
               faces={"top": img}, collision=False, **leaf)]


def potted_plant() -> Product:
    """A pothos-like foliage plant in a 6-size (18 cm) plastic pot with a plant tag.

    The pot is hollow and filled with soil, so most of the mass (split by volume) sits in the pot. The foliage is a
    bush of rounded leaf clumps tilted outward (a ring draping over the rim and a smaller ring and crown above), plus
    vines hanging down the pot, instead of one wide dome over a small pot.
    """
    Dp, Hp = 0.18, 0.165
    pot = "#F2F0EB"
    tag = Canvas(40, 70, 10, WHITE, 9441)
    tag.gradient(0, 0, 40, 70, "#FFFFFF", "#EEF3EA")
    tag.rect(0, 0, 40, 16, fill=LEAF_DARK)
    tag.text(20, 8, "観葉植物", 6, WHITE, 900)
    tag.text(20, 26, "ポトス", 7, INK, 900)
    tag.text(20, 36, "6号鉢", 5, INK, 800)
    tag.paragraph(4, 42, 36, "明るい日陰に置き、土が乾いたら水やり。", 3.2, INK, 500)
    tag.text(20, 64, "1,280円", 6, "#C62828", 900)
    tag_img = _face(tag.array(), "paper", 9441, 0.4, 4)
    soil = _soil_top(180, 9442)
    leaves = _leaves(300, 300, 9443)
    leaves_dark = _leaves(300, 300, 9444)
    prof = [[0, 0], [0.80, 0], [0.97, 0.90], [1.0, 0.92], [1.0, 1.0], [0.93, 1.0], [0.91, 0.92], [0.76, 0.06],
            [0, 0.06]]
    z_soil = Hp - 0.014
    hs = z_soil - 0.06 * Hp
    parts = [_p("Pot", "revolve", (Dp, Dp, Hp), (0, 0, Hp / 2), pot, "plastic", profile=prof),
             _p("SoilFill", "revolve", (Dp, Dp, hs), (0, 0, 0.06 * Hp + hs / 2), SOIL, "matte",
                profile=[[0, 0], [0.75, 0], [0.90, 1.0], [0, 1.0]], collision=False, material="dirt"),
             _p("Soil", "cylinder", (Dp * 0.90, Dp * 0.90, 0.002), (0, 0, z_soil + 0.001), SOIL, "matte",
                faces={"top": 1}, collision=False, material="dirt")]
    # the crown is the collider for the foliage
    parts += _clump("Foliage", (0.0, 0.01, Hp + 0.14), 0.12, 0.09, 0.03, 0.0, 0.0, LEAF, 2, collision=True)
    for k in range(6):  # lower ring, draping over the rim
        a = 60.0 * k
        t = math.radians(a)
        parts += _clump(f"Ring{k}", (0.075 * math.cos(t), 0.075 * math.sin(t), Hp + 0.025 + 0.006 * (k % 2)),
                        0.095, 0.06, 0.02, 40.0, a, LEAF_DARK if k % 2 else LEAF, 3 if k % 2 else 2)
    for k in range(4):  # upper ring
        a = 75.0 + 90.0 * k
        t = math.radians(a)
        parts += _clump(f"Mid{k}", (0.042 * math.cos(t), 0.042 * math.sin(t), Hp + 0.085), 0.09, 0.065, 0.02,
                        22.0, a, LEAF if k % 2 else LEAF_DARK, 2 if k % 2 else 3)
    # trailing vines down the outside of the pot
    for k, (a, ln) in enumerate(((205.0, 0.12), (262.0, 0.09), (322.0, 0.11))):
        t = math.radians(a)
        x, y, top = 0.102 * math.cos(t), 0.102 * math.sin(t), Hp + 0.01
        parts.append(_p(f"Vine{k}", "pointed_dome", (0.045, 0.045, ln), (x, y, top - ln / 2), LEAF,
                        rot=(180.0, 0, 0), faces={"top": 3}, collision=False, finish_="matte", material="leaf_grass"))
    parts.append(_p("Tag", "box", (0.040, 0.002, 0.070), (0.0, -0.092, Hp + 0.075), WHITE, "matte", (12.0, 0, 0),
                    faces={"front": 0}, collision=False, material="plastic"))
    return Product(slug="potted_plant", name="観葉植物 ポトス 6号鉢", shape_class="assembly", category="household",
                   dims=Dimensions(0.395, 0.256, depth=0.239), mass_kg=2.2, material="plastic",
                   description="形は一般的な 6 号（口径 180 mm）のプラスチック鉢に植えた観葉植物（ポトスのようなつる性の葉、"
                               "株の幅約 260 mm・高さ約 400 mm、鉢の外に垂れるつる・名札付き）で、寸法・質量は代表値。"
                               "葉の茂みは外へ傾けた丸い葉の塊（鉢の縁にかかる輪・その上の輪・頂部）に葉の絵を貼って表す。"
                               "鉢は中空で土を詰めてあり、質量の多くは鉢にある。当たり判定は鉢と頂部の茂み。",
                   tags=["観葉植物", "ポトス", "鉢植え", "グリーン", "植物", "園芸", "ホームセンター", "potted plant",
                         "house plant", "pothos", "indoor plant"],
                   photos=[], colors=Colors(label_base=LEAF), images=[tag_img, soil, leaves, leaves_dark], parts=parts)


PRODUCTS = {f.__name__: f for f in (flower_pot, soil_bag, watering_can, hose_reel, potted_plant)}
