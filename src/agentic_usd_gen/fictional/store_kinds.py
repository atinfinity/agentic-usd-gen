"""Fictional product designs for more store kinds (florist, toy store, pet shop,
shoe store, optician).

No real product names, brands or logos; shapes and sizes are typical values. Front is -Y.
"""

from __future__ import annotations

import math

import numpy as np

from ..shapes.assembly import rotation_matrix
from ..spec import Colors, Dimensions, Part
from .apparel_fixtures import _mirror_img
from .base import NOTICE, Product, label_canvas, revolve
from .conv_goods import BOX_FACES, _faces, _hang_hole
from .conv_snacks import HangBag, _bag_header, _cat, _hang_header
from .farm import _aim, _bez, _tube
from .food_fresh_snack import _pouch
from .food_pantry import _eo_lid, _food_can
from .goods_more import FILM, _card_edges
from .hc_garden import _p
from .paint import Canvas, finish, mix
from .products import INK, _box, _face, back_info, seal_crimp
from .shelf_more import _dog

WHITE = "#FFFFFF"
STEM, LEAF = "#4F7F34", "#3E7230"
LEAF_KW = dict(finish_="matte", material="leaf_grass", collision=False)

# ---------------------------------------------------------------- cut flowers in a florist's bucket

FLOWERS = ["Rose", "Carnation", "Gerbera", "Bouquet"]


def _rose_top(seed: int, color: str) -> np.ndarray:
    """A rose seen from above: petals wrapped in a spiral, darker toward the centre."""
    c = Canvas(60, 60, 8, color, seed)
    c.gradient(0, 0, 60, 60, mix(color, WHITE, 0.10), mix(color, "#000000", 0.25))
    for k in range(9):  # overlapping petal edges spiralling in
        r = 29 - k * 3.1
        a0 = k * 47.0
        pts = [(30 + r * math.cos(math.radians(a0 + t)), 30 + r * math.sin(math.radians(a0 + t))) for t in range(0, 230, 10)]
        c.line(pts, mix(color, "#000000", 0.35 + 0.03 * k), 1.6)
        c.line([(x + 0.8, y + 0.8) for x, y in pts], mix(color, WHITE, 0.25), 0.7)
    c.ellipse(26, 26, 34, 34, fill=mix(color, "#000000", 0.45))
    return finish(c.array(), "paper", seed, 0.35)


def _frill_top(seed: int, color: str) -> np.ndarray:
    """A carnation seen from above: a frilly ball of thin, serrated petals."""
    c = Canvas(60, 60, 8, color, seed)
    c.gradient(0, 0, 60, 60, mix(color, WHITE, 0.25), mix(color, "#000000", 0.12))
    rng = c.rng
    for _ in range(420):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(2, 28)
        ln = rng.uniform(2, 5)
        x0, y0 = 30 + r0 * math.cos(a), 30 + r0 * math.sin(a)
        b = a + rng.uniform(-1.2, 1.2)
        tone = rng.choice([mix(color, WHITE, 0.45), mix(color, "#000000", 0.25), mix(color, WHITE, 0.15)])
        c.line([(x0, y0), (x0 + ln * math.cos(b), y0 + ln * math.sin(b))], tone, 0.8)
    return finish(c.array(), "paper", seed, 0.35)


def _daisy_top(seed: int, color: str) -> np.ndarray:
    """A gerbera seen from above: long rays with a faint stripe around a dark disc ringed with yellow."""
    c = Canvas(80, 80, 6, color, seed)
    c.gradient(0, 0, 80, 80, mix(color, WHITE, 0.15), mix(color, "#000000", 0.10))
    for k in range(48):
        a = math.radians(k * 7.5)
        c.line([(40 + 13 * math.cos(a), 40 + 13 * math.sin(a)), (40 + 39 * math.cos(a), 40 + 39 * math.sin(a))],
               mix(color, "#000000", 0.18), 0.6)
    c.ellipse(26, 26, 54, 54, fill="#E0B422")
    c.ellipse(30, 30, 50, 50, fill="#3B2412")
    c.ellipse(35, 35, 45, 45, fill="#5A3A1C")
    return finish(c.array(), "paper", seed, 0.35)


def _leaf_img(seed: int) -> np.ndarray:
    c = Canvas(60, 40, 6, LEAF, seed)
    c.gradient(0, 0, 60, 40, "#4C8A3A", "#2C5E22")
    c.line([(0, 20), (60, 20)], "#7FB060", 1.0)
    for k in range(6):
        x = 6 + k * 9
        c.line([(x, 20), (x + 7, 6)], "#5E9A48", 0.6)
        c.line([(x, 20), (x + 7, 34)], "#5E9A48", 0.6)
    return finish(c.array(), "paper", seed, 0.4)


def _card(seed: int, title: str, sub: str, price: str, band: str) -> np.ndarray:
    c = Canvas(80, 50, 8, WHITE, seed)
    c.gradient(0, 0, 80, 50, "#FFFFFF", "#F1EEE6")
    c.rect(0, 0, 80, 12, fill=band)
    c.text(40, 6.5, sub, 6, WHITE, 900)
    c.text(40, 24, title, 11, INK, 900)
    c.text(40, 40, price, 10, "#C62828", 900)
    return _face(c.array(), "paper", seed, 0.4, 4)


def _head_spots(n: int, rng, r_max: float, z0: float, z1: float) -> list[np.ndarray]:
    """n head positions on a low dome over the bucket (more toward the front, -Y)."""
    out = []
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(n):
        r = r_max * math.sqrt((k + 0.5) / n)
        a = k * golden + rng.uniform(-0.2, 0.2)
        z = z1 - (z1 - z0) * (r / r_max) ** 2 + rng.uniform(-0.012, 0.012)
        out.append(np.array([r * math.cos(a), r * math.sin(a) - 0.01, z]))
    return out


def _stem_to(name: str, head, base_r: float, z_base: float, rng, show) -> tuple[Part, np.ndarray]:
    """A stem from inside the bucket (below the water line) to `head`; returns the part and the head's facing."""
    head = np.asarray(head, float)
    xy = head[:2] / max(np.linalg.norm(head[:2]), 1e-6) * min(base_r, np.linalg.norm(head[:2]) * 0.35)
    base = np.array([xy[0], xy[1], z_base])
    ctrl = base + (head - base) * 0.55 + [0, 0, 0.04]
    facing = head - base
    facing = facing / np.linalg.norm(facing) + [0, 0, 0.6]
    return _tube(name, _bez(base, ctrl, head, 7), 0.0055, 0.0045, STEM, 5, show), facing / np.linalg.norm(facing)


def _stem_leaves(prefix: str, head, z_rim: float, rng, img: int, show) -> list[Part]:
    """Two leaves on the stem a little above the rim, pointing out and up."""
    head = np.asarray(head, float)
    parts = []
    for k in range(2):
        t = rng.uniform(0.30, 0.55)
        at = np.array([head[0] * t, head[1] * t, z_rim + (head[2] - z_rim) * (t - 0.15)])
        heading = math.degrees(math.atan2(head[1], head[0])) + (k * 2 - 1) * rng.uniform(35, 70)
        pitch = rng.uniform(20, 40)
        ln = rng.uniform(0.050, 0.065)
        th, ph = math.radians(heading), math.radians(pitch)
        c = at + ln / 2 * np.array([math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)])
        parts.append(_p(f"{prefix}Leaf{k}", "leaf", (ln, ln * 0.45, ln * 0.10), tuple(c), LEAF, rot=(0.0, -pitch, heading),
                        faces={"top": img}, segments=5, show=show, **LEAF_KW))
    return parts


def cut_flower_bucket() -> Product:
    """A florist's black plastic bucket of water with a bunch of cut flowers standing in it, as one rigid body.

    The flowers have no collision: the bucket (a solid frustum, most of the mass with the water) is the only
    collider, so the bunch cannot roll away. The Flower variant set picks roses, carnations, gerberas or three
    wrapped bouquets.
    """
    D, Db, H = 0.30, 0.23, 0.38
    z_base, z_rim = 0.06, H
    rng = np.random.default_rng(7201)
    images = [_rose_top(7202, "#B3122A"), _frill_top(7203, "#E8708E"), _daisy_top(7204, "#F07A1E"),
              _daisy_top(7205, "#F2C230"), _daisy_top(7206, "#E8508A"), _leaf_img(7207),
              _card(7208, "バラ", "切り花", "1本 300円", "#B3122A"),
              _card(7209, "カーネーション", "切り花", "1本 250円", "#D0567A"),
              _card(7210, "ガーベラ", "切り花", "1本 200円", "#E06A1A"),
              _card(7211, "花束", "ブーケ", "1,650円", "#2E7D32")]
    LEAF_IMG = 5
    # no bevel at the foot: PhysX trims a hull to 64 vertices, and a bevel ring just above the floor let the
    # trimmed hull rest 3.7 degrees off upright. With every low vertex at z=0 the hull's base stays flat.
    prof = [[0, 0], [Db / D, 0], [0.98, 0.95], [1.0, 0.96], [1.0, 1.0], [0.955, 1.0],
            [0.95, 0.96], [Db / D - 0.03, 0.05], [0, 0.05]]
    # the water disc sits just inside the inner wall at 62 % of the height
    parts = [_p("Bucket", "revolve", (D, D, H), (0, 0, H / 2), "#1E1F22", "plastic", profile=prof),
             _p("Water", "cylinder", (D * 0.85, D * 0.85, 0.002), (0, 0, H * 0.62), "#2E3F4A", "glossy",
                collision=False, material="water")]
    for i, (name, img_card) in enumerate(zip(FLOWERS, (6, 7, 8, 9))):
        show = {"Flower": [name]}
        # a price pick: a card on a clear stick pushed in at the front, inside the rim
        parts.append(_p(f"{name}Card", "box", (0.080, 0.002, 0.050), (0.0, -D / 2 + 0.030, H + 0.055), WHITE, "matte",
                        (-8.0, 0, 0), faces={"front": img_card}, collision=False, material="paper", show=show))
        parts.append(_p(f"{name}Pick", "cylinder", (0.004, 0.004, 0.16), (0.0, -D / 2 + 0.032, H - 0.045), "#D8E4E8",
                        "glossy", collision=False, show=show))
    # roses: 15 closed blooms
    for k, head in enumerate(_head_spots(15, rng, 0.10, 0.58, 0.70)):
        stem, v = _stem_to(f"RoseStem{k}", head, 0.07, z_base, rng, {"Flower": ["Rose"]})
        rot = _aim(v)
        show = {"Flower": ["Rose"]}
        parts += [stem,
                  _p(f"RoseHead{k}", "dome", (0.050, 0.050, 0.040), tuple(head + v * 0.012), "#B3122A", "matte", rot=rot,
                     faces={"top": 0}, collision=False, material="leaf_grass", segments=16, show=show),
                  _p(f"RoseBase{k}", "pointed_dome", (0.040, 0.040, 0.022), tuple(head - v * 0.004), "#8E0E22",
                     "matte", rot=(rot[0] + 180.0, rot[1], 0), collision=False, material="leaf_grass", segments=12,
                     show=show)]
        if k % 2 == 0:
            parts += _stem_leaves(f"Rose{k}", head, z_rim, rng, LEAF_IMG, show)
    # carnations: 18 frilly blooms with a green calyx
    for k, head in enumerate(_head_spots(18, rng, 0.10, 0.56, 0.68)):
        show = {"Flower": ["Carnation"]}
        stem, v = _stem_to(f"CarnationStem{k}", head, 0.07, z_base, rng, show)
        rot = _aim(v)
        parts += [stem,
                  _p(f"CarnationHead{k}", "dome", (0.055, 0.055, 0.026), tuple(head + v * 0.010), "#E8708E", "matte",
                     rot=rot, faces={"top": 1}, collision=False, material="leaf_grass", segments=16, show=show),
                  _p(f"CarnationFrill{k}", "star", (0.062, 0.062, 0.006), tuple(head + v * 0.008), "#E8708E",
                     rot=rot, profile=[[20, 0.82, 0.8]], faces={"top": 1}, segments=16, show=show,
                     **{**LEAF_KW, "material": "leaf_grass"}),
                  _p(f"CarnationCalyx{k}", "pointed_dome", (0.016, 0.016, 0.026), tuple(head - v * 0.010), STEM,
                     "matte", rot=(rot[0] + 180.0, rot[1], 0), collision=False, material="leaf_grass", segments=10,
                     show=show)]
        if k % 3 == 0:
            parts += _stem_leaves(f"Carnation{k}", head, z_rim, rng, LEAF_IMG, show)
    # gerberas: 12 flat daisies in three colours, facing up and out
    for k, head in enumerate(_head_spots(12, rng, 0.085, 0.58, 0.68)):
        show = {"Flower": ["Gerbera"]}
        stem, v = _stem_to(f"GerberaStem{k}", head, 0.06, z_base, rng, show)
        rot = _aim(v + [0, 0, 0.8])
        img = 2 + k % 3
        parts += [stem,
                  _p(f"GerberaHead{k}", "star", (0.095, 0.095, 0.008), tuple(head + v * 0.004), WHITE, rot=rot,
                     profile=[[26, 0.72, 0.6]], faces={"top": img}, segments=24, show=show, **LEAF_KW),
                  _p(f"GerberaDisc{k}", "dome", (0.030, 0.030, 0.008), tuple(head + v * 0.007), "#3B2412", "matte",
                     rot=rot, collision=False, material="leaf_grass", segments=16, show=show),
                  _p(f"GerberaBack{k}", "pointed_dome", (0.030, 0.030, 0.012), tuple(head - v * 0.003), STEM, "matte",
                     rot=(rot[0] + 180.0, rot[1], 0), collision=False, material="leaf_grass", segments=10, show=show)]
    # bouquets: three paper cones of mixed blooms, leaning out
    mixed = ((0, "#B3122A"), (1, "#F2D0DA"), (3, "#F2C230"), (1, "#FFFFFF"), (0, "#E86A8A"))
    for b, (heading, wrap) in enumerate(((270.0, "#C9A27A"), (30.0, "#F4F1EA"), (150.0, "#9FB7C9"))):
        show = {"Flower": ["Bouquet"]}
        th = math.radians(heading)
        lean = np.array([0.07 * math.cos(th), 0.07 * math.sin(th), 1.0])
        lean /= np.linalg.norm(lean)
        rot = _aim(lean)
        R = rotation_matrix(list(rot))
        foot = np.array([0.040 * math.cos(th), 0.040 * math.sin(th), 0.12])
        Hc, Dc = 0.44, 0.15
        cone = [[0, 0], [0.16, 0], [1.0, 1.0], [0.95, 1.0], [0.13, 0.03], [0, 0.03]]
        parts.append(_p(f"Bouquet{b}Wrap", "revolve", (Dc, Dc, Hc), tuple(foot + R @ [0, 0, Hc / 2]), wrap, "matte",
                        rot=rot, profile=cone, collision=False, material="paper", show=show))
        parts.append(_p(f"Bouquet{b}Ribbon", "cylinder", (0.050, 0.050, 0.018), tuple(foot + R @ [0, 0, 0.16]),
                        "#C62828", "glossy", rot=rot, collision=False, material="fabric", show=show))
        for k in range(9):
            a = k * 2.4 + b
            r = 0.015 + 0.040 * math.sqrt((k + 0.5) / 9)
            local = np.array([r * math.cos(a), r * math.sin(a), Hc - 0.02 - 0.05 * (r / 0.06) ** 2 + 0.03])
            img, col = mixed[(k + b) % len(mixed)]
            parts.append(_p(f"Bouquet{b}Bloom{k}", "dome", (0.042, 0.042, 0.030), tuple(foot + R @ local), col,
                            "matte", rot=rot, faces={"top": img} if col in ("#B3122A", "#E86A8A") else None,
                            collision=False, material="leaf_grass", segments=14, show=show))
        for k in range(4):
            a = math.radians(k * 90 + 45)
            local = np.array([0.055 * math.cos(a), 0.055 * math.sin(a), Hc - 0.03])
            parts.append(_p(f"Bouquet{b}Leaf{k}", "leaf", (0.07, 0.03, 0.006), tuple(foot + R @ local), LEAF,
                            rot=(rot[0], rot[1] - 40.0, k * 90 + 45 + heading), faces={"top": LEAF_IMG}, segments=5,
                            show=show, **LEAF_KW))
    return Product(slug="cut_flower_bucket", name="花桶の切り花（バラ・カーネーション・ガーベラ・花束）", shape_class="assembly",
                   category="household", dims=Dimensions(0.72, 0.30, depth=0.30), mass_kg=4.8, material="plastic",
                   variant_sets={"Flower": FLOWERS},
                   description="形は花屋の店先に並ぶ黒いプラスチックの花桶（口径 300 mm・高さ 380 mm、水入り）に切り花を立てたもので、"
                               "寸法・質量は代表値。花の種類は Flower バリアント（Rose＝赤いバラ 15 本 / Carnation＝ピンクの"
                               "カーネーション 18 本 / Gerbera＝3 色のガーベラ 12 本 / Bouquet＝紙で包んだ花束 3 つ）、"
                               "それぞれ桶に挿した値札付き。花は桶の口の内側にまとめてある。花と茎には当たり判定が無く、当たり判定は桶（外形の凸包）だけなので、"
                               "1 つの剛体として桶ごと立ち、花が転がり出ない。質量の多くは桶と水にある。",
                   tags=["切り花", "花", "花束", "ブーケ", "花桶", "バケツ", "バラ", "カーネーション", "ガーベラ", "花屋",
                         "cut flowers", "flower bouquet", "bouquet", "flower bucket", "flowers", "roses", "carnations",
                         "gerberas", "florist"],
                   photos=[], colors=Colors(label_base="#B3122A"), images=images, parts=parts)


# ---------------------------------------------------------------- toys

TOY_TAGS = ["おもちゃ", "玩具", "おもちゃ屋", "toy", "toys", "toy store"]
TOY_MAKER = "架空のおもちゃ"


def _age_mark(c: Canvas, cx: float, cy: float, s: float, color: str):
    """対象年齢のマーク（丸の中に「3才以上」）。"""
    c.ellipse(cx - s, cy - s, cx + s, cy + s, fill=WHITE, outline=color, width=s * 0.12)
    c.text(cx, cy - s * 0.18, "3才", s * 0.62, color, 900)
    c.text(cx, cy + s * 0.45, "以上", s * 0.38, color, 800)


def _draw_car(c: Canvas, x0, y0, x1, y1, body: str, accent: str = "#FFD23F"):
    """横から見た丸っこい車（箱・台紙の絵）。"""
    w, h = x1 - x0, y1 - y0
    base = y0 + h * 0.72
    c.rect(x0, y0 + h * 0.38, x1, base, fill=body, radius=h * 0.16)
    c.rect(x0 + w * 0.22, y0 + h * 0.06, x0 + w * 0.72, y0 + h * 0.46, fill=body, radius=h * 0.14)
    for a, b in ((0.27, 0.46), (0.50, 0.67)):
        c.rect(x0 + w * a, y0 + h * 0.13, x0 + w * b, y0 + h * 0.38, fill="#BFE6F5", radius=h * 0.05)
    c.rect(x0 + w * 0.02, y0 + h * 0.48, x0 + w * 0.08, y0 + h * 0.56, fill=accent, radius=1)
    c.rect(x1 - w * 0.06, y0 + h * 0.48, x1, y0 + h * 0.56, fill="#E8E8E8", radius=1)
    c.rect(x0 + w * 0.05, y0 + h * 0.60, x1 - w * 0.05, y0 + h * 0.63, fill=accent)
    for f in (0.24, 0.76):
        cx, r = x0 + w * f, h * 0.17
        c.ellipse(cx - r, base - r, cx + r, base + r, fill="#22252A")
        c.ellipse(cx - r * 0.45, base - r * 0.45, cx + r * 0.45, base + r * 0.45, fill="#C9CED6")


def _toy_box(W, D, H, seed, bg, accent, title, en, sub, draw, rows, note) -> list:
    """Six faces of a printed toy box (mm). draw(c, x0, y0, x1, y1) draws the toy on the front."""
    s = min(W, H)
    fr = Canvas(W, H, None, bg, seed)
    fr.gradient(0, 0, W, H, mix(bg, WHITE, 0.25), mix(bg, "#000000", 0.15))
    for k in range(9):  # sunburst behind the toy
        a = math.radians(k * 40)
        cx, cy = W * 0.5, H * 0.42
        fr.polygon([(cx, cy), (cx + W * math.cos(a), cy + W * math.sin(a)),
                    (cx + W * math.cos(a + 0.35), cy + W * math.sin(a + 0.35))], fill=mix(bg, WHITE, 0.18))
    draw(fr, W * 0.08, H * 0.16, W * 0.92, H * 0.70)
    fr.rect(0, H * 0.72, W, H, fill=accent)
    fr.text(W / 2, H * 0.80, title, s * 0.10, WHITE, 900, max_w=W * 0.9)
    fr.text(W / 2, H * 0.88, en, s * 0.05, bg, 900, spacing=s * 0.004, max_w=W * 0.9)
    fr.text(W / 2, H * 0.94, sub, s * 0.045, WHITE, 700, max_w=W * 0.9)
    fr.text(W * 0.05, H * 0.06, TOY_MAKER, s * 0.05, WHITE, 900, anchor="lm")
    _age_mark(fr, W - s * 0.11, s * 0.11, s * 0.075, accent)
    bk = Canvas(W, H, None, WHITE, seed + 1)
    bk.gradient(0, 0, W, H, "#FFFFFF", "#F1F3F6")
    bk.rect(0, 0, W, H * 0.08, fill=accent)
    bk.text(W / 2, H * 0.04, en, s * 0.045, WHITE, 900, max_w=W * 0.9)
    y = bk.table(W * 0.06, H * 0.12, W * 0.94, "セット内容", rows, s * 0.045)
    bk.paragraph(W * 0.06, y + s * 0.03, W * 0.94,
                 note + "\n小さな部品があります。3 才未満のお子さまには与えないでください。\n" + NOTICE, s * 0.034, INK, 500)
    bk.barcode(W * 0.06, H * 0.80, W * 0.36, H * 0.14)
    _age_mark(bk, W * 0.62, H * 0.87, s * 0.07, accent)
    bk.recycle(W * 0.84, H * 0.87, s * 0.07, "紙", accent, sub="箱")
    sides = []
    for k in range(2):
        sd = Canvas(D, H, None, accent, seed + 2 + k)
        sd.gradient(0, 0, D, H, mix(accent, WHITE, 0.1), mix(accent, "#000000", 0.15))
        sd.vtext(D / 2, H * 0.10, title[:9], min(D * 0.32, H * 0.07), WHITE, 900)
        sd.rect(0, H * 0.88, D, H * 0.92, fill=bg)
        sides.append(sd)
    tops = []
    for k in range(2):
        t = Canvas(W, D, None, bg, seed + 4 + k)
        t.gradient(0, 0, W, D, mix(bg, WHITE, 0.15), bg, horizontal=True)
        t.text(W / 2, D / 2, title, min(D * 0.28, W * 0.08), WHITE, 900, max_w=W * 0.9)
        tops.append(t)
    return _faces((fr, bk, *sides, *tops), "film", seed, 0.5)


def toy_car_box() -> Product:
    """A boxed radio-controlled car, the classic big box on a toy-store shelf."""
    W, D, H = 340.0, 170.0, 150.0
    bg, accent = "#1565C0", "#E53935"

    def draw(c, x0, y0, x1, y1):
        _draw_car(c, x0 + (x1 - x0) * 0.05, y0 + (y1 - y0) * 0.1, x1 - (x1 - x0) * 0.05, y1, "#E53935")
        c.text(x1 - (x1 - x0) * 0.04, y0 + (y1 - y0) * 0.04, "2.4GHz", (y1 - y0) * 0.12, "#FFD23F", 900,
               anchor="rm")

    imgs = _toy_box(W, D, H, 7301, bg, accent, "ラジコンカー", "RC RACING CAR", "充電式  2.4GHz  最高 10 km/h", draw,
                    [("本体", "約 260 × 130 × 95 mm"), ("送信機", "単 3 形 × 2（別売）"), ("充電", "USB 約 90 分")],
                    "室内の平らな床で遊んでください。")
    return Product(slug="toy_car_box", name="ラジコンカーの箱", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.9, material="paper",
                   description="形は一般的な子ども向けラジコンカーの化粧箱（340 × 170 × 150 mm）で、寸法・質量は本体と"
                               "送信機を含む代表値。正面に車の絵と対象年齢のマーク。印刷・型番・メーカー名はすべて架空。",
                   tags=["ラジコン", "ラジコンカー", "箱入りのおもちゃ", "おもちゃの車", "toy car", "toy vehicle",
                         "rc car", "toy box", "boxed toy", *TOY_TAGS], photos=[], colors=Colors(label_base=bg),
                   images=imgs, faces=BOX_FACES)


BRICK_COLORS = ("#D32F2F", "#1976D2", "#FBC02D", "#388E3C", "#FFFFFF", "#F57C00")


def building_blocks_tub() -> Product:
    """A clear tub of toy bricks with a coloured lid: the bricks show through the sides."""
    W, D, H = 0.30, 0.20, 0.22
    T, LID = 0.19, 0.03
    rng = np.random.default_rng(7311)
    lab = Canvas(180.0, 70.0, 8, WHITE, 7312)
    lab.rect(0, 0, 180, 70, fill="#FBC02D", radius=6)
    lab.rect(3, 3, 177, 67, fill=WHITE, radius=5)
    for k, col in enumerate(BRICK_COLORS[:4]):  # a little brick stack logo
        lab.rect(8 + k * 9, 44 - k * 9, 30 + k * 9, 56 - k * 9, fill=col, outline="#555555", width=0.3, radius=1)
    lab.text(110, 24, "つみあげブロック", 15, "#D32F2F", 900, max_w=120)
    lab.text(110, 42, "BUILDING BLOCKS  120 pcs", 7, "#1976D2", 900, max_w=120)
    lab.text(110, 56, TOY_MAKER + "  対象年齢 3才以上", 6, INK, 700, max_w=120)
    label = _face(lab.array(), "film", 7312, 0.4)
    parts = [_box("Tub", (W, D, T), (0, 0, T / 2), FILM, "glass", thin_walled=True),
             _box("Lid", (W + 0.008, D + 0.008, LID), (0, 0, T + LID / 2), "#D32F2F", "plastic"),
             _box("Handle", (0.12, 0.03, 0.012), (0, 0, T + LID + 0.006), "#B71C1C", "plastic", collision=False),
             _box("Label", (0.18, 0.001, 0.07), (0, -D / 2 - 0.0006, T * 0.62), WHITE, "matte", {"front": 0},
                  collision=False)]
    # loose bricks: three uneven layers, each brick a little rotated, all inside the tub walls
    bw, bd, bh = 0.032, 0.016, 0.0192
    k = 0
    for layer, rows in enumerate((5, 5, 4)):
        z = 0.004 + bh / 2 + layer * (bh + 0.004)
        for i in range(rows):
            for j in range(7):
                if layer == 2 and rng.random() < 0.35:
                    continue
                x = -W / 2 + 0.028 + j * (W - 0.056) / 6 + rng.uniform(-0.006, 0.006)
                y = -D / 2 + 0.022 + i * (D - 0.044) / max(rows - 1, 1) + rng.uniform(-0.004, 0.004)
                yaw = float(rng.choice([0.0, 90.0])) + rng.uniform(-12, 12)
                col = BRICK_COLORS[int(rng.integers(len(BRICK_COLORS)))]
                parts.append(_box(f"Brick{k}", (bw, bd, bh), (x, y, z), col, "glossy", rotation=[0, 0, yaw],
                                  collision=False))
                k += 1
    for p in parts:
        p.material = "paper" if p.name == "Label" else "plastic"
    return Product(slug="building_blocks_tub", name="ブロックのケース（120 ピース）", shape_class="assembly",
                   category="household", dims=Dimensions(T + LID + 0.012, W + 0.008, depth=D + 0.008), mass_kg=1.1,
                   material="plastic",
                   description="形は一般的な子ども向けの組み立てブロックを入れた透明の収納ケース（300 × 200 mm、高さ 220 mm、"
                               "赤いふたと取っ手）で、寸法・質量は代表値。側面から 6 色のブロックが見える。当たり判定は"
                               "ケースとふただけで、ブロックは見た目だけ。印刷・メーカー名はすべて架空。",
                   tags=["ブロック", "積み木", "組み立てブロック", "知育玩具", "building blocks", "toy blocks",
                         "toy bricks", "construction toy", *TOY_TAGS], photos=[], colors=Colors(label_base="#D32F2F"),
                   images=[label], parts=parts)


def plush_bear() -> Product:
    """A sitting teddy bear: a flat-bottomed body carries it, the rest is soft shapes without collision."""
    fur, light, dark = "#B07A4A", "#E8CBA4", "#2A1A12"
    egg = [[0, 0], [0.62, 0], [0.88, 0.14], [1.0, 0.42], [0.92, 0.72], [0.64, 0.94], [0, 1.0]]
    ball = [[0, 0], [0.55, 0.05], [0.88, 0.25], [1.0, 0.5], [0.88, 0.75], [0.55, 0.95], [0, 1.0]]
    kw = dict(collision=False, material="fabric")
    parts = [_p("Body", "revolve", (0.15, 0.13, 0.16), (0, 0.005, 0.08), fur, "matte", profile=egg, material="fabric"),
             _p("Head", "revolve", (0.13, 0.12, 0.12), (0, 0.0, 0.205), fur, "matte", profile=ball, material="fabric"),
             _p("Muzzle", "revolve", (0.055, 0.05, 0.04), (0, -0.058, 0.192), light, "matte", rot=(90, 0, 0),
                profile=ball, **kw),
             _p("Nose", "dome", (0.020, 0.014, 0.010), (0, -0.082, 0.200), dark, "glossy", rot=(90, 0, 0), **kw)]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        parts += [
            _p(f"Ear{side}", "cylinder", (0.045, 0.045, 0.018), (s * 0.045, 0.004, 0.258), fur, "matte",
               rot=(90, 0, s * 8), **kw),
            _p(f"EarIn{side}", "cylinder", (0.026, 0.026, 0.004), (s * 0.045, -0.006, 0.256), light, "matte",
               rot=(90, 0, s * 8), **kw),
            _p(f"Eye{side}", "dome", (0.013, 0.013, 0.006), (s * 0.026, -0.054, 0.222), dark, "glossy",
               rot=(80, 0, 0), **kw),
            _p(f"Arm{side}", "revolve", (0.045, 0.045, 0.10), (s * 0.072, -0.022, 0.095), fur, "matte",
               rot=(-25, s * -30, 0), profile=ball, **kw),
            _p(f"Leg{side}", "revolve", (0.055, 0.055, 0.10), (s * 0.040, -0.060, 0.028), fur, "matte",
               rot=(85, 0, s * -10), profile=ball, **kw),
            _p(f"Sole{side}", "cylinder", (0.040, 0.040, 0.004), (s * 0.048, -0.108, 0.030), light, "matte",
               rot=(85, 0, s * -10), **kw)]
    parts.append(_p("Ribbon", "torus", (0.085, 0.080, 0.012), (0, 0.0, 0.153), "#C62828", "glossy", **kw))
    return Product(slug="plush_bear", name="クマのぬいぐるみ（座り）", shape_class="assembly", category="household",
                   dims=Dimensions(0.281, 0.184, depth=0.207), mass_kg=0.25, material="fabric",
                   description="形は一般的な座った姿勢のクマのぬいぐるみ（高さ約 270 mm）で、寸法・質量は代表値。首に赤い"
                               "リボン。当たり判定は底の平らな胴と頭だけで、手足・耳は見た目だけ（棚に座らせても転がらない）。"
                               "名前・メーカー名はすべて架空。",
                   tags=["ぬいぐるみ", "クマ", "テディベア", "stuffed animal", "plush toy", "teddy bear", "plush",
                         *TOY_TAGS], photos=[], colors=Colors(label_base=fur), images=[], parts=parts)


def toy_car_blister() -> Product:
    """A die-cast mini car on a blister card, for the hooks of a toy store."""
    CW, CH = 110.0, 160.0
    bg, accent = "#0D47A1", "#FFD23F"
    c = Canvas(CW, CH, 10, bg, 7321)
    c.gradient(0, 0, CW, CH, mix(bg, WHITE, 0.15), mix(bg, "#000000", 0.25))
    _hang_hole(c, CW / 2, 5, mix(bg, "#000000", 0.5))
    for k in range(7):  # speed lines behind the car
        y = 52 + k * 9
        c.rect(4, y, CW - 4, y + 2.5, fill=mix(bg, WHITE, 0.10 + 0.03 * (k % 3)), radius=1)
    c.rect(0, 14, CW, 34, fill=accent)
    c.text(CW / 2, 22, "ミニカー", 9.0, "#D32F2F", 900)
    c.text(CW / 2, 30, "DIE-CAST MINI CAR", 4.2, bg, 900, spacing=0.3)
    c.rect(6, CH - 24, CW - 6, CH - 11, fill="#D32F2F", radius=3)
    c.text(CW / 2, CH - 17.5, "1/64 スケール  ダイキャスト", 4.2, WHITE, 900, max_w=CW - 16)
    c.text(CW / 2, CH - 5, TOY_MAKER, 3.6, WHITE, 700)
    _age_mark(c, CW - 12, 44, 6, "#D32F2F")
    _card_edges(c, accent)
    front = _face(c.array(), "film", 7321, 0.6)
    b = Canvas(CW, CH, 10, WHITE, 7322)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF1F6")
    _card_edges(b, bg)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 15, CW, 25, fill=bg)
    b.text(CW / 2, 20, "DIE-CAST MINI CAR", 3.8, WHITE, 800)
    yb = b.table(6, 30, CW - 6, "", [("大きさ", "約 70 × 30 × 26 mm"), ("素材", "亜鉛合金・ABS"),
                                      ("対象年齢", "3 才以上")], 3.4)
    b.paragraph(6, yb + 3, CW - 6, "小さな部品があります。口に入れないでください。\n" + NOTICE, 2.8, INK, 400)
    b.barcode(8, CH - 34, 40, 20)
    b.recycle(CW - 28, CH - 20, 7, "紙", bg, sub="台紙")
    b.recycle(CW - 13, CH - 20, 7, "プラ", bg, sub="ケース")
    back = _face(b.array(), "paper", 7322, 0.6)
    body = "#E53935"
    yc = -0.0006 - 0.016  # the car's centre line, in front of the card
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.090, 0.034, 0.064), (0, -0.0176, 0.080), FILM, "glass", thin_walled=True,
                  collision=False),
             _box("CarBody", (0.070, 0.028, 0.014), (0, yc, 0.072), body, "glossy", collision=False),
             _box("CarCabin", (0.036, 0.024, 0.012), (-0.004, yc, 0.085), body, "glossy", collision=False),
             _box("CarGlass", (0.030, 0.0245, 0.008), (-0.004, yc, 0.086), "#7FB8D6", "glossy", collision=False)]
    for s, x in (("F", 0.022), ("R", -0.022)):
        parts.append(_p(f"Wheels{s}", "cylinder", (0.017, 0.017, 0.030), (x, yc, 0.064), "#22252A", "matte",
                        rot=(90, 0, 0), collision=False))
    for p in parts:
        p.material = "paper" if p.name == "Card" else ("metal" if p.name.startswith("Car") else "plastic")
    return Product(slug="toy_car_blister", name="ミニカー（ブリスター）", shape_class="assembly", category="household",
                   dims=Dimensions(CH / 1000, CW / 1000, depth=0.0352), mass_kg=0.06, material="plastic",
                   description="形は一般的な台紙とブリスターに入った 1/64 のダイキャストのミニカー（台紙 110 × 160 mm、車 "
                               "70 × 28 × 26 mm）で、寸法・質量は代表値。フックに掛ける吊り下げ穴は穴を開けず印刷で表す。"
                               "当たり判定は台紙だけ。印刷・車種・メーカー名はすべて架空。",
                   tags=["ミニカー", "おもちゃの車", "ブリスター", "toy blister pack", "toy car blister", "toy car",
                         "mini car", "die-cast car", "blister pack", *TOY_TAGS], photos=[],
                   colors=Colors(label_base=bg), images=[front, back], parts=parts)

# ---------------------------------------------------------------- pet goods

PET_TAGS = ["ペット用品", "ペットショップ", "pet supplies", "pet shop"]
PET_MAKER = "架空のペット用品"
BALL = [[0, 0], [0.55, 0.05], [0.88, 0.25], [1.0, 0.5], [0.88, 0.75], [0.55, 0.95], [0, 1.0]]


def cat_food_can() -> Product:
    """A small can of wet cat food with an easy-open lid, the stacked cans on a pet-shop shelf."""
    form = _food_can(0.037, 0.066)
    orange, navy, cream = "#F28C28", "#203A6B", "#FFF4DE"
    c = label_canvas(form, orange, seed=7401)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F7A04A", "#E0761A")
    c.pattern(0, 0, W, H - 4, "dots", mix(orange, WHITE, 0.15), 5, 0.4)
    c.rect(0, H - 4, W, H, fill=navy)
    c.ellipse(fx - 38, 2, fx - 8, H - 6, fill=cream)
    _cat(c, fx - 23, H * 0.47, 9.5, "#F2F2F0", "#555555")
    c.text(fx + 16, 7.0, "ねこのごちそう", 5.6, WHITE, 900, stroke=0.3, stroke_fill=navy)
    c.text(fx + 16, 14.0, "まぐろ＆かつお", 4.2, navy, 900)
    c.text(fx + 16, 19.5, "パテタイプ  成猫用  80g", 2.8, WHITE, 800)
    c.text(fx, H - 2, "一般食  ※絵はイメージです", 1.9, WHITE, 700)
    c.text(0.5 * W + 6, H - 2, "CAT FOOD", 2.0, WHITE, 800, spacing=0.4)
    bx = 0.25 * W
    c.rect(bx - 31, 1, bx + 36, 19, fill=WHITE, radius=1)
    back_info(c, bx - 30, 1.6, bx + 6, [
        ("名称", "キャットフード（一般食）"), ("原材料名", "まぐろ、かつお、鶏肉、増粘安定剤、ビタミン E"),
        ("内容量", "80g"), ("賞味期限", "缶ふたに記載"), ("原産国", "日本")], 1.2)
    c.table(bx + 8, 1.6, bx + 35, "成分（保証値）", [
        ("たんぱく質", "11.0%以上"), ("脂質", "0.5%以上"), ("粗繊維", "0.1%以下"), ("灰分", "2.5%以下"),
        ("水分", "86.0%以下")], 1.15)
    c.barcode(0.5 * W - 8, 2, 18, 11)
    c.recycle(0.5 * W + 1, 18.5, 5, "スチール", WHITE, kind="can")
    label = finish(c.array(), "paper", 7401, 0.7)
    top = _eo_lid(form, 7402, "賞味期限 2029.08")
    return Product(slug="cat_food_can", name="キャットフード 缶 まぐろ＆かつお 80g", category="household", mass_kg=0.1,
                   material="steel",
                   description="形は一般的な 80g のキャットフードの缶（高さ 37 mm・胴径 66 mm、イージーオープン）で、"
                               "寸法・質量は代表値。ねこの絵と印刷・メーカー名はすべて架空。",
                   tags=["キャットフード", "猫缶", "ペットフード", "缶詰", "ねこ", "cat food can", "pet food can",
                         "canned cat food", "pet food", *PET_TAGS], photos=[],
                   colors=Colors(cap="#C3C6C9", label_base=orange), **revolve(form, label=label, top=top))


def _bone(prefix: str, L: float, knob: float, shaft: float, z: float, color: str, collision: bool) -> list[Part]:
    """A bone shape along X: a round shaft with two balls at each end (centre height z)."""
    parts = [_p(f"{prefix}Shaft", "cylinder", (shaft, shaft, L - knob), (0, 0, z), color, "matte", rot=(0, 90, 0),
                collision=False, material="plastic")]
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        parts.append(_p(f"{prefix}Knob{i}", "revolve", (knob, knob, knob),
                        (sx * (L - knob) / 2, sy * knob * 0.36, z), color, "matte", profile=BALL,
                        collision=collision, material="plastic"))
    return parts


def dog_toy() -> Product:
    """A rubber chew bone for dogs, lying on its four end knobs."""
    L, knob = 0.165, 0.038
    parts = _bone("", L, knob, 0.024, knob / 2, "#2E86DE", True)
    for k, x in enumerate((-0.03, 0.0, 0.03)):  # raised grip rings on the shaft
        parts.append(_p(f"Ring{k}", "cylinder", (0.027, 0.027, 0.005), (x, 0, knob / 2), "#1B6FC0", "matte",
                        rot=(0, 90, 0), collision=False, material="plastic"))
    return Product(slug="dog_toy", name="犬のおもちゃ（ラバーのほね）", shape_class="assembly", category="household",
                   dims=Dimensions(knob, L, depth=knob * 1.72), mass_kg=0.12, material="plastic",
                   description="形は一般的な犬用のラバー製のほね型のおもちゃ（長さ 165 mm・端の玉の径 38 mm）で、寸法・質量は"
                               "代表値。当たり判定は両端の 4 つの玉で、寝かせて置くと転がらない。メーカー名は架空。",
                   tags=["犬のおもちゃ", "ペットのおもちゃ", "ほね", "ラバー", "pet toy", "dog toy", "chew toy",
                         "dog bone toy", *PET_TAGS], photos=[], colors=Colors(label_base="#2E86DE"), images=[],
                   parts=parts)


def pet_toy_blister() -> Product:
    """A small rubber ball and a mini bone for dogs on a blister card, for the hooks of a pet shop."""
    CW, CH = 120.0, 170.0
    bg, accent = "#00897B", "#FFB300"
    c = Canvas(CW, CH, 10, bg, 7411)
    c.gradient(0, 0, CW, CH, mix(bg, WHITE, 0.15), mix(bg, "#000000", 0.2))
    _hang_hole(c, CW / 2, 5, mix(bg, "#000000", 0.5))
    for k in range(10):  # paw prints behind the toys
        x, y = 12 + (k % 4) * 30 + (k // 4 % 2) * 15, 48 + (k // 4) * 32
        col = mix(bg, WHITE, 0.12)
        c.ellipse(x - 4, y - 3, x + 4, y + 4, fill=col)
        for dx, dy in ((-5, -6), (-1.7, -8.5), (1.7, -8.5), (5, -6)):
            c.ellipse(x + dx - 1.6, y + dy - 1.6, x + dx + 1.6, y + dy + 1.6, fill=col)
    c.rect(0, 14, CW, 36, fill=accent)
    c.text(CW / 2, 22, "わんちゃんのおもちゃ", 8.0, "#5D2E00", 900, max_w=CW - 10)
    c.text(CW / 2, 31, "BALL & BONE  ボール＆ほね", 4.2, bg, 900, spacing=0.3)
    _dog(c, CW - 18, 50, 18)
    c.rect(6, CH - 24, CW - 6, CH - 11, fill="#5D2E00", radius=3)
    c.text(CW / 2, CH - 17.5, "やわらかラバー  小型犬用  2 個入り", 4.0, WHITE, 900, max_w=CW - 16)
    c.text(CW / 2, CH - 5, PET_MAKER, 3.6, WHITE, 700)
    _card_edges(c, accent)
    front = _face(c.array(), "film", 7411, 0.6)
    b = Canvas(CW, CH, 10, WHITE, 7412)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF4F3")
    _card_edges(b, bg)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 15, CW, 25, fill=bg)
    b.text(CW / 2, 20, "BALL & BONE  2 個入り", 3.8, WHITE, 800)
    yb = b.table(6, 30, CW - 6, "", [("大きさ", "ボール 径 45 mm・ほね 長さ 75 mm"), ("素材", "天然ゴム"),
                                      ("対象", "小型犬")], 3.4)
    b.paragraph(6, yb + 3, CW - 6, "かじって壊れたら取り上げてください。飼い主のいる所で遊ばせてください。\n" + NOTICE,
                2.8, INK, 400)
    b.barcode(8, CH - 34, 40, 20)
    b.recycle(CW - 28, CH - 20, 7, "紙", bg, sub="台紙")
    b.recycle(CW - 13, CH - 20, 7, "プラ", bg, sub="ケース")
    back = _face(b.array(), "paper", 7412, 0.6)
    yc = -0.0006 - 0.0235  # the toys' centre line, in front of the card
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.100, 0.050, 0.080), (0, -0.0256, 0.090), FILM, "glass", thin_walled=True,
                  collision=False),
             _p("Ball", "revolve", (0.045, 0.045, 0.045), (-0.022, yc, 0.0565), "#E53935", "matte", profile=BALL,
                collision=False)]
    bx, bz, bl, bk = 0.030, 0.090, 0.075, 0.020  # a mini bone standing up, to the right of the ball
    parts.append(_p("BoneShaft", "cylinder", (0.012, 0.012, bl - bk), (bx, yc, bz), "#FFB300", "matte",
                    collision=False))
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_p(f"BoneKnob{i}", "revolve", (bk, bk, bk), (bx + sx * bk * 0.36, yc, bz + sz * (bl - bk) / 2),
                        "#FFB300", "matte", profile=BALL, collision=False))
    for p in parts:
        p.material = "paper" if p.name == "Card" else "plastic"
    return Product(slug="pet_toy_blister", name="犬のおもちゃ ボール＆ほね（ブリスター）", shape_class="assembly",
                   category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0512), mass_kg=0.09,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入った小型犬用のおもちゃ（台紙 120 × 170 mm、ボール径 45 mm と"
                               "長さ 75 mm のほね）で、寸法・質量は代表値。フックに掛ける吊り下げ穴は穴を開けず印刷で表す。"
                               "当たり判定は台紙だけ。印刷・メーカー名はすべて架空。",
                   tags=["犬のおもちゃ", "ペットのおもちゃ", "ブリスター", "pet toy blister pack", "dog toy blister",
                         "blister pack", *PET_TAGS], photos=[], colors=Colors(label_base=bg), images=[front, back],
                   parts=parts)


def _jerky(c: Canvas, x0: float, y0: float, x1: float, y1: float, n: int):
    """Strips of chicken jerky seen through the window."""
    rng = c.rng
    for k in range(n):
        x = x0 + (k + 0.5) * (x1 - x0) / n + rng.uniform(-2, 2)
        w = (x1 - x0) / n * 0.75
        a = rng.uniform(-0.25, 0.25)
        top, bot = y0 + rng.uniform(1, 5), y1 - rng.uniform(1, 5)
        dx = (bot - top) * a / 2
        col = mix("#A0522D", "#6B3416", rng.random())
        c.polygon([(x - w / 2 - dx, top), (x + w / 2 - dx, top), (x + w / 2 + dx, bot), (x - w / 2 + dx, bot)], fill=col)
        for j in range(4):
            yy = top + (bot - top) * (0.2 + 0.2 * j)
            c.line([(x - w * 0.4, yy), (x + w * 0.4, yy + rng.uniform(-1.5, 1.5))], mix(col, "#000000", 0.25), 0.5)


def dog_treat_hang() -> HangBag:
    """The pictures of a hanging bag of chicken jerky treats for dogs."""
    W, H, depth = 130.0, 180.0, 0.024
    HH = 30.0
    red, brown, cream, yellow = "#C62828", "#5D2E0C", "#FFF8E8", "#FFC107"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, red, seed=seed)
        c.gradient(0, 0, W, H, "#D84343", "#A51D1D")
        seal_crimp(c, 0, 0, W, 10, "#D84343", 1.2)
        seal_crimp(c, 0, H - 10, W, H, "#A51D1D", 1.2)
        return c

    c = base(7421)
    c.rect(0, 10, W, 24, fill=yellow)
    c.text(W / 2, 17, "犬用おやつ  無着色", 5.4, brown, 900)
    c.text(W / 2, 38, "ささみジャーキー", 14, WHITE, 900, max_w=W - 14, stroke=0.6, stroke_fill=brown)
    c.text(W / 2, 50, "国産ささみ使用  やわらか細切り", 4.6, yellow, 800)
    c.rect(12, 58, W - 12, 136, fill=cream, radius=8)
    _jerky(c, 16, 62, W - 16, 132, 7)
    c.rect(12, 58, W - 12, 136, outline=brown, width=0.6, radius=8)
    _dog(c, 30, 150, 30)
    c.ellipse(W - 44, 138, W - 8, 172, fill=yellow)
    c.text(W - 26, 151, "100g", 8.0, brown, 900)
    c.text(W - 26, 162, "内容量", 3.4, brown, 700)
    c.text(52, 152, "全犬種用", 5.0, WHITE, 900, anchor="lm")
    c.text(52, 160, "※中身の絵はイメージです", 2.8, WHITE, 500, anchor="lm")
    front = _pouch(c, 7421, 0.9, 16)

    b = base(7422)
    b.text(W / 2, 17, "ささみジャーキー 100g", 5.4, WHITE, 900)
    b.rect(7, 26, W - 7, H - 13, fill=WHITE, radius=2)
    y = b.paragraph(11, 30, W - 11, "【名称】ペットフード（間食）\n【原材料名】鶏ささみ、グリセリン、ソルビトール、"
                    "酸化防止剤（ビタミン E）\n【内容量】100g\n【賞味期限】上部に記載\n【原産国】日本", 3.4, INK, 400)
    y = b.table(11, y + 3, W - 11, "成分（保証値）", [("たんぱく質", "50.0%以上"), ("脂質", "1.0%以上"),
                                                  ("粗繊維", "0.5%以下"), ("灰分", "6.0%以下"), ("水分", "25.0%以下")], 3.2)
    b.table(11, y + 3, W - 11, "1 日の目安", [("体重 5kg まで", "約 5 本"), ("体重 10kg まで", "約 10 本")], 3.2)
    b.paragraph(11, H - 52, W - 11, "おやつは 1 日の食事の 2 割までにしてください。\n" + NOTICE, 2.6, INK, 400)
    b.barcode(11, H - 38, 32, 20)
    b.recycle(W - 22, H - 28, 9, "プラ", brown, sub="袋")
    back = _pouch(b, 7422, 0.9, 16)
    imgs = [front, back, _bag_header(W, HH, 7423, "犬用おやつ  ささみ", cream, red),
            _bag_header(W, HH, 7424, PET_MAKER + "  100g", cream, red)]
    return HangBag(imgs, W, H, depth, HH, 0.11)


def dog_treat_bag() -> Product:
    """A bag of chicken jerky dog treats with a flat header to hang it on a hook."""
    b = dog_treat_hang()
    return Product(slug="dog_treat_bag", name="犬用おやつ ささみジャーキー 100g", shape_class="pouch",
                   category="household", dims=Dimensions(b.H / 1000, b.W / 1000, depth=b.depth), mass_kg=b.mass,
                   material="film",
                   description="形は一般的な吊り下げのフックに掛ける犬用おやつの袋（袋 高さ 180 mm・幅 130 mm に、吊り下げ穴の"
                               "ある高さ 30 mm のヘッダーを足した全高 約 210 mm）で、寸法・質量は代表値。穴は開けず印刷で"
                               "表す。中身の絵・印刷・メーカー名はすべて架空。",
                   tags=["犬のおやつ", "ジャーキー", "ペットフード", "おやつ", "吊り下げ", "pet treat bag", "dog treat bag",
                         "dog treats", "jerky", *PET_TAGS], photos=[], colors=Colors(label_base="#C62828"), images=b.images,
                   faces={"front": 0, "back": 1}, parts=[_hang_header(b)])


# ---------------------------------------------------------------- shoes

SHOE_TAGS = ["靴", "シューズ", "靴屋", "shoes", "footwear", "shoe store"]
SHOE_MAKER = "架空のシューズ"


def _shoe(prefix: str, x: float, L: float, w: float, upper: str, sole: str) -> list[Part]:
    """One lace-up leather shoe with the toe toward -Y, standing on its sole (collision: the sole only)."""
    so = 0.010
    parts = [_p(f"{prefix}Sole", "cylinder", (w, L, so), (x, 0, so / 2), sole, "matte", material="plastic"),
             _p(f"{prefix}Heel", "box", (w * 0.70, L * 0.24, 0.022), (x, L * 0.36, 0.011), sole, "matte",
                collision=False, material="plastic")]
    z = so + 0.004
    hv, hb = 0.055, 0.072  # heights of the vamp over the forefoot and of the back over the heel
    kw = dict(collision=False, material="plastic")
    parts += [
        _p(f"{prefix}Vamp", "bun", (w * 0.94, L * 0.78, hv), (x, -L * 0.10, z + hv / 2), upper, "glossy", **kw),
        _p(f"{prefix}Quarter", "bun", (w * 0.96, L * 0.56, hb), (x, L * 0.20, z + hb / 2), upper, "glossy", **kw),
        _p(f"{prefix}Opening", "cylinder", (w * 0.62, L * 0.30, 0.004), (x, L * 0.24, z + hb - 0.004), "#3A2A20",
           "matte", collision=False, material="fabric"),
        _p(f"{prefix}Collar", "torus", (w * 0.68, L * 0.34, 0.008), (x, L * 0.24, z + hb - 0.002),
           mix(upper, WHITE, 0.08), "glossy", **kw),
        _p(f"{prefix}Tongue", "box", (w * 0.38, L * 0.14, 0.005), (x, L * 0.02, z + hv + 0.004), upper, "glossy",
           rot=(-24, 0, 0), **kw)]
    for k in range(3):
        t = k / 2
        parts.append(_p(f"{prefix}Lace{k}", "box", (w * 0.48, 0.005, 0.003),
                        (x, -L * 0.17 + t * L * 0.15, z + hv * (0.82 + 0.18 * t) + 0.002), "#1B1B1B", "matte",
                        rot=(-22, 0, 0), collision=False, material="fabric"))
    return parts


def leather_shoe() -> Product:
    """One black leather lace-up dress shoe, the display sample on a shoe-store shelf (toe toward -Y)."""
    L, w = 0.27, 0.092
    parts = _shoe("", 0.0, L, w, "#16110E", "#3B2A20")
    return Product(slug="leather_shoe", name="革靴（黒・片足）", shape_class="assembly", category="household",
                   dims=Dimensions(0.088, w, depth=L), mass_kg=0.45, material="plastic",
                   description="形は一般的な黒い革の紐靴（ビジネスシューズ、25 cm、長さ 270 mm。靴の壁棚の奥行きに入る）の片足（売場の見本）で、"
                               "寸法・質量は代表値。かかとの下にヒール。当たり判定は靴底だけ。メーカー名は架空。",
                   tags=["革靴", "ビジネスシューズ", "紳士靴", "leather shoe", "leather shoes", "dress shoe",
                         "dress shoes", "shoe", "片足", "見本", *SHOE_TAGS], photos=[], colors=Colors(label_base="#16110E"), images=[],
                   parts=parts)


def _insole(prefix: str, x: float, yc: float, z: float, L: float, w: float, color: str) -> list[Part]:
    """A flat insole standing upright on the card (toe up): a wide toe oval, a narrow waist and a heel oval.
    The waist sits a little behind the ovals so that the overlapping faces do not flicker."""
    kw = dict(rot=(90, 0, 0), collision=False, material="fabric")
    return [_p(f"{prefix}Toe", "cylinder", (w, L * 0.50, 0.004), (x, yc - 0.001, z + L * 0.24), color, "matte", **kw),
            _p(f"{prefix}Waist", "cylinder", (w * 0.72, L * 0.50, 0.004), (x, yc + 0.0005, z - L * 0.04), color, "matte", **kw),
            _p(f"{prefix}Heel", "cylinder", (w * 0.84, L * 0.40, 0.004), (x, yc - 0.001, z - L * 0.28), color, "matte", **kw)]


def _hang_card(CW, CH, seed, bg, accent, title, en, band, back_title, rows, note, maker=SHOE_MAKER) -> list:
    """Front and back of a hanging blister card (mm) for the shoe store and the optician."""
    c = Canvas(CW, CH, 10, bg, seed)
    c.gradient(0, 0, CW, CH, mix(bg, WHITE, 0.15), mix(bg, "#000000", 0.2))
    _hang_hole(c, CW / 2, 5, mix(bg, "#000000", 0.5))
    c.rect(0, 14, CW, 36, fill=accent)
    c.text(CW / 2, 22, title, 8.0, bg, 900, max_w=CW - 10)
    c.text(CW / 2, 31, en, 4.2, mix(bg, "#000000", 0.3), 900, spacing=0.3, max_w=CW - 10)
    c.rect(6, CH - 24, CW - 6, CH - 11, fill=mix(bg, "#000000", 0.45), radius=3)
    c.text(CW / 2, CH - 17.5, band, 4.0, WHITE, 900, max_w=CW - 16)
    c.text(CW / 2, CH - 5, maker, 3.6, WHITE, 700)
    _card_edges(c, accent)
    front = _face(c.array(), "film", seed, 0.6)
    b = Canvas(CW, CH, 10, WHITE, seed + 1)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF1F6")
    _card_edges(b, bg)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 15, CW, 25, fill=bg)
    b.text(CW / 2, 20, back_title, 3.8, WHITE, 800, max_w=CW - 8)
    yb = b.table(6, 30, CW - 6, "", rows, 3.4)
    b.paragraph(6, yb + 3, CW - 6, note + "\n" + NOTICE, 2.8, INK, 400)
    b.barcode(8, CH - 34, 40, 20)
    b.recycle(CW - 28, CH - 20, 7, "紙", bg, sub="台紙")
    b.recycle(CW - 13, CH - 20, 7, "プラ", bg, sub="ケース")
    return [front, _face(b.array(), "paper", seed + 1, 0.6)]


def shoe_insole_pack() -> Product:
    """A pair of cushion insoles on a tall hanging card."""
    CW, CH = 110.0, 300.0
    bg = "#263238"
    imgs = _hang_card(CW, CH, 7511, bg, "#4FC3F7", "クッションインソール", "CUSHION INSOLE  1 足分",
                      "つま先でカット  23.0〜27.0 cm", "CUSHION INSOLE",
                      [("サイズ", "23.0〜27.0 cm（カットして調整）"), ("素材", "ポリウレタン・ポリエステル"), ("入数", "1 足分")],
                      "靴の中敷きを外してから入れてください。")
    yc = -0.0006 - 0.006
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.096, 0.012, 0.250), (0, -0.0066, 0.165), FILM, "glass", thin_walled=True,
                  collision=False)]
    for s, x in (("L", -0.022), ("R", 0.022)):
        parts += _insole(f"Insole{s}", x, yc - (0.002 if s == "L" else 0.0), 0.165, 0.240, 0.040, "#4FC3F7")
    for p in parts:
        p.material = "paper" if p.name == "Card" else ("fabric" if p.name.startswith("Insole") else "plastic")
    return Product(slug="shoe_insole_pack", name="クッションインソール（吊り下げ）", shape_class="assembly",
                   category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0132), mass_kg=0.08,
                   material="plastic",
                   description="形は一般的な縦長の台紙と透明ケースに入った靴の中敷き 1 足分（台紙 110 × 300 mm、中敷きは"
                               "縮めて長さ 240 mm）で、寸法・質量は代表値。フックに掛ける吊り下げ穴は穴を開けず印刷で表す。"
                               "当たり判定は台紙だけ。印刷・メーカー名はすべて架空。",
                   tags=["インソール", "中敷き", "靴のケア用品", "shoe insole pack", "insole", "insoles",
                         "blister pack", *SHOE_TAGS], photos=[], colors=Colors(label_base=bg), images=imgs, parts=parts)


def shoelace_blister() -> Product:
    """Two coiled shoelaces on a small hanging blister card."""
    CW, CH = 90.0, 150.0
    bg = "#E65100"
    imgs = _hang_card(CW, CH, 7521, bg, WHITE, "くつひも", "SHOELACES  120 cm  2 本",
                      "平ひも  スニーカー用", "SHOELACES 120 cm",
                      [("長さ", "120 cm"), ("太さ", "幅 8 mm（平ひも）"), ("入数", "2 本（1 足分）")],
                      "穴の数が 6〜7 対の靴に合います。")
    yc = -0.0006 - 0.008
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.074, 0.016, 0.084), (0, -0.0086, 0.078), FILM, "glass", thin_walled=True,
                  collision=False)]
    for k, z in enumerate((0.098, 0.058)):  # two coils, one above the other
        for j in range(3):
            parts.append(_p(f"Coil{k}{j}", "torus", (0.060 - j * 0.012, 0.034 - j * 0.006, 0.006), (0, yc, z),
                            WHITE if k == 0 else "#212121", "matte", rot=(90, 0, 0), collision=False,
                            material="fabric"))
    for p in parts:
        if p.name in ("Card", "Blister"):
            p.material = "paper" if p.name == "Card" else "plastic"
    return Product(slug="shoelace_blister", name="くつひも 2 本入り（ブリスター）", shape_class="assembly",
                   category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0172), mass_kg=0.03,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入ったスニーカー用の平ひも 120 cm 2 本（白と黒を巻いたもの、"
                               "台紙 90 × 150 mm）で、寸法・質量は代表値。フックに掛ける吊り下げ穴は穴を開けず印刷で表す。"
                               "当たり判定は台紙だけ。印刷・メーカー名はすべて架空。",
                   tags=["くつひも", "靴ひも", "シューレース", "ブリスター", "shoelace blister pack", "shoelaces",
                         "shoelace", "blister pack", *SHOE_TAGS], photos=[], colors=Colors(label_base=bg), images=imgs,
                   parts=parts)


# ---------------------------------------------------------------- optician

EYE_TAGS = ["眼鏡", "メガネ", "眼鏡店", "eyewear", "optician", "optical shop"]
EYE_MAKER = "架空のメガネ"


def eyeglasses() -> Product:
    """A pair of black-rimmed glasses with the temples open, standing on the rims and the temple tips (front -Y)."""
    rw, rh = 0.050, 0.038  # rim width and height
    fw = 2 * (rw + 0.009 + 0.010)  # frame width over the hinges
    frame, lens = "#1C1C1E", "#DCE8F0"
    z = rh / 2
    parts = []
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        x = s * (rw / 2 + 0.009)
        parts += [_p(f"Rim{side}", "torus", (rw, rh, 0.005), (x, 0, z), frame, "glossy", rot=(90, 0, 0),
                     material="plastic"),
                  _p(f"Lens{side}", "cylinder", (rw - 0.004, rh - 0.004, 0.002), (x, 0, z), lens, "glass",
                     rot=(90, 0, 0), collision=False, material="glass"),
                  # the end piece runs from the rim to the hinge so the temple is joined to the front
                  _p(f"End{side}", "box", (0.010, 0.005, 0.006), (s * (rw + 0.009 + 0.003), 0, z + rh * 0.25), frame,
                     "glossy", collision=False, material="plastic"),
                  _p(f"Hinge{side}", "box", (0.004, 0.006, 0.007), (s * (rw + 0.009 + 0.008), 0.004, z + rh * 0.25),
                     frame, "glossy", collision=False, material="plastic")]
        # the temple runs back from the hinge and drops to the table at its tip
        L, z0, z1 = 0.140, z + rh * 0.25, 0.002
        tilt = math.degrees(math.atan2(z0 - z1, L))
        parts.append(_p(f"Temple{side}", "box", (0.003, L, 0.004), (s * (rw + 0.009 + 0.008), 0.007 + L / 2,
                                                                    (z0 + z1) / 2),
                        frame, "glossy", rot=(-tilt, 0, 0), material="plastic"))
    parts.append(_p("Bridge", "box", (0.020, 0.004, 0.004), (0, 0, z + rh * 0.28), frame, "glossy", collision=False,
                    material="plastic"))
    for s in (-1, 1):  # nose pads
        parts.append(_p(f"Pad{'L' if s < 0 else 'R'}", "dome", (0.006, 0.010, 0.003), (s * 0.010, 0.006, z - rh * 0.05),
                        "#F2F2F2", "glass", rot=(0, s * 70, 0), collision=False, material="plastic"))
    return Product(slug="eyeglasses", name="眼鏡（黒ぶち）", shape_class="assembly", category="household",
                   dims=Dimensions(rh, fw, depth=0.149), mass_kg=0.025, material="plastic",
                   description="形は一般的な黒いプラスチックの枠の眼鏡（幅 138 mm、レンズ 50 × 38 mm、つる 140 mm）で、寸法・"
                               "質量は代表値。つるを開いて、枠の下とつるの先で机・棚に立つ（当たり判定は枠とつる）。"
                               "レンズは度の入っていない見本。メーカー名は架空。",
                   tags=["眼鏡", "メガネ", "めがね", "フレーム", "eyeglasses", "glasses", "spectacles",
                         "eyeglass frame", *EYE_TAGS], photos=[], colors=Colors(label_base=frame), images=[],
                   parts=parts)


def glasses_case() -> Product:
    """A hard clamshell glasses case, closed, lying flat."""
    W, D = 0.158, 0.060
    shell, inner = "#1F3A5F", "#C9B07A"
    parts = [_p("Base", "cylinder", (W, D, 0.018), (0, 0, 0.009), shell, "matte", material="plastic"),
             _p("Seam", "cylinder", (W * 0.995, D * 0.98, 0.002), (0, 0, 0.019), inner, "matte", collision=False,
                material="fabric"),
             _p("Lid", "bun", (W, D, 0.022), (0, 0, 0.031), shell, "matte", material="plastic"),
             _p("Hinge", "cylinder", (0.004, 0.004, 0.040), (0, D / 2 - 0.001, 0.020), "#9AA3B2", "metal",
                rot=(0, 90, 0), collision=False, material="metal"),
             _p("Badge", "box", (0.022, 0.0015, 0.006), (0, -D / 2 + 0.0004, 0.012), "#C9A227", "metal",
                collision=False, material="metal")]
    return Product(slug="glasses_case", name="眼鏡ケース（ハード）", shape_class="assembly", category="household",
                   dims=Dimensions(0.042, W, depth=D), mass_kg=0.07, material="plastic",
                   description="形は一般的な貝の形に開く硬い眼鏡ケース（158 × 60 × 42 mm、閉じた状態）で、寸法・質量は代表値。"
                               "紺の外側に、合わせ目から内張りの布がのぞく。当たり判定は下のケースとふた。メーカー名は架空。",
                   tags=["眼鏡ケース", "メガネケース", "glasses case", "eyeglass case", "spectacle case",
                         *EYE_TAGS], photos=[], colors=Colors(label_base=shell), images=[], parts=parts)


def glasses_cleaner_blister() -> Product:
    """A small lens-cleaner spray and a microfibre cloth on a hanging blister card."""
    CW, CH = 90.0, 150.0
    bg = "#0277BD"
    imgs = _hang_card(CW, CH, 7611, bg, WHITE, "メガネクリーナー", "LENS CLEANER & CLOTH",
                      "スプレー 30 ml ＋ クロス", "LENS CLEANER SET",
                      [("液", "30 ml（界面活性剤・アルコール）"), ("クロス", "15 × 15 cm マイクロファイバー"),
                       ("使える物", "眼鏡・サングラスのレンズ")],
                      "コーティングを傷めないよう、乾いたまま強くこすらないでください。", EYE_MAKER)
    yc = -0.0006 - 0.013
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.074, 0.026, 0.086), (0, -0.0136, 0.081), FILM, "glass", thin_walled=True,
                  collision=False),
             _p("Bottle", "cylinder", (0.024, 0.024, 0.060), (-0.018, yc, 0.071), "#E3F2FD", "glass",
                collision=False, material="plastic"),
             _p("Sprayer", "cylinder", (0.016, 0.016, 0.014), (-0.018, yc, 0.108), WHITE, "glossy", collision=False,
                material="plastic"),
             _p("Nozzle", "box", (0.004, 0.008, 0.004), (-0.018, yc - 0.008, 0.111), WHITE, "glossy",
                collision=False, material="plastic"),
             _p("Cloth", "box", (0.036, 0.008, 0.060), (0.018, yc, 0.078), "#B39DDB", "matte", collision=False,
                material="fabric")]
    for p in parts[:2]:
        p.material = "paper" if p.name == "Card" else "plastic"
    return Product(slug="glasses_cleaner_blister", name="メガネクリーナー スプレー＋クロス（ブリスター）",
                   shape_class="assembly", category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0272),
                   mass_kg=0.06, material="plastic",
                   description="形は一般的な台紙とブリスターに入ったレンズ用のクリーナー（スプレー 30 ml とたたんだクロス、"
                               "台紙 90 × 150 mm）で、寸法・質量は代表値。フックに掛ける吊り下げ穴は穴を開けず印刷で表す。"
                               "当たり判定は台紙だけ。印刷・メーカー名はすべて架空。",
                   tags=["メガネクリーナー", "メガネ拭き", "クロス", "ブリスター", "glasses cleaner blister pack",
                         "glasses cleaner", "lens cloth", "lens cleaner", "blister pack", *EYE_TAGS], photos=[],
                   colors=Colors(label_base=bg), images=imgs, parts=parts)


# ---------------------------------------------------------------- shoe-store and optician fixtures (static)

BLACK = "#1E1E1E"
OAK = "#C8A57A"
FELT = "#5B5F66"


def shoe_display_riser() -> Product:
    """A two-step riser for shoes on the shop floor: a low front step and a higher back step."""
    W, D = 1.20, 0.60
    t = 0.012
    parts = []
    for k, (h, y) in enumerate(((0.15, -D / 4), (0.30, D / 4))):
        parts += [_box(f"Step{k + 1}", (W, D / 2, h - t), (0, y, (h - t) / 2), WHITE, "plastic"),
                  _box(f"Top{k + 1}", (W + 0.01, D / 2, t), (0, y, h - t / 2), OAK, "plastic")]
    for p in parts:
        p.material = "wood"
    return Product(slug="shoe_display_riser", name="靴の陳列台（2 段）", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.30, W + 0.01, depth=D), mass_kg=28.0, static=True, material="wood",
                   description="形は靴売場の床に置く一般的な 2 段の陳列台（幅 1200 mm・奥行き 600 mm、手前の段 150 mm・"
                               "奥の段 300 mm、白い箱に木の天板）で、寸法・質量は代表値。天板に靴を並べる。",
                   tags=["靴の陳列台", "ひな壇", "陳列台", "靴", "shoe display", "shoe display riser", "display riser",
                         "display platform", "shoe stand", *SHOE_TAGS], photos=[], colors=Colors(label_base=WHITE),
                   images=[], parts=parts)


def shoe_fitting_bench() -> Product:
    """A low upholstered bench for trying shoes on."""
    W, D, H = 1.20, 0.40, 0.42
    parts = [_p("Base", "box", (W - 0.06, D - 0.06, 0.34), (0, 0, 0.17), BLACK, "matte", material="wood"),
             _p("Seat", "box", (W, D, H - 0.34), (0, 0, 0.34 + (H - 0.34) / 2), FELT, "matte", material="fabric",
                bevel=0.012)]
    return Product(slug="shoe_fitting_bench", name="試し履きのベンチ", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=18.0, static=True, material="wood",
                   description="形は靴売場の一般的な試し履き用の低いベンチ（幅 1200 mm・奥行き 400 mm・座面 420 mm、"
                               "黒い台に灰色の布張りの座面）で、寸法・質量は代表値。",
                   tags=["試し履き", "ベンチ", "腰掛け", "靴", "shoe fitting bench", "fitting bench", "shoe bench",
                         "bench", "seat", *SHOE_TAGS], photos=[], colors=Colors(label_base=FELT), images=[],
                   parts=parts)


def shoe_floor_mirror() -> Product:
    """A small floor mirror leaning back, for looking at shoes on your feet."""
    W, H, lean = 0.36, 0.48, 15.0
    t = math.radians(lean)
    h = H / math.cos(t) - 0.02
    yc = math.tan(t) * H / 2
    parts = [_p("Frame", "box", (W, 0.018, h), (0, yc + 0.004, H / 2), BLACK, "glossy", rot=(-lean, 0, 0),
                material="plastic"),
             _p("Mirror", "box", (W - 0.03, 0.004, h - 0.03), (0, yc - 0.006, H / 2), "#DDE3E8", "glossy",
                rot=(-lean, 0, 0), faces={"front": 0}, collision=False, material="glass", bevel=0),
             _p("Foot", "box", (W, 0.20, 0.02), (0, 0.06, 0.01), BLACK, "matte", material="metal")]
    return Product(slug="shoe_floor_mirror", name="靴売場の足元ミラー", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=0.20), mass_kg=4.5, static=True, material="glass",
                   description="形は靴売場の床に置く一般的な足元を映す小さな鏡（幅 360 mm・高さ 480 mm、後ろへ 15° 傾ける）で、"
                               "寸法・質量は代表値。",
                   tags=["足元ミラー", "床置きミラー", "鏡", "靴", "floor mirror", "shoe mirror", "foot mirror",
                         "mirror", *SHOE_TAGS], photos=[], colors=Colors(label_base=BLACK), images=[_mirror_img(330, 450, 7701)],
                   parts=parts)


def eyewear_wall_case() -> Product:
    """A wall case for spectacle frames: a closed cabinet below and glass shelves on a lit back panel above."""
    W, D, H = 0.90, 0.25, 2.00
    base_h = 0.80
    zs = [0.95 + 0.135 * k for k in range(7)]
    parts = [_p("Cabinet", "box", (W, D, base_h), (0, 0, base_h / 2), WHITE, "matte", material="wood"),
             _p("Drawers", "box", (W - 0.04, 0.004, base_h - 0.12), (0, -D / 2 - 0.001, base_h / 2 + 0.02), OAK, "matte",
                collision=False, material="wood"),
             _p("Back", "box", (W, 0.02, H - base_h), (0, D / 2 - 0.01, base_h + (H - base_h) / 2), WHITE, "matte",
                material="wood"),
             _p("Light", "box", (W - 0.06, 0.004, H - base_h - 0.18), (0, D / 2 - 0.022, base_h + (H - base_h - 0.18) / 2 + 0.06),
                "#F7F5EE", "glossy", collision=False, material="plastic"),
             _p("SideL", "box", (0.02, D, H - base_h), (-W / 2 + 0.01, 0, base_h + (H - base_h) / 2), WHITE, "matte",
                material="wood"),
             _p("SideR", "box", (0.02, D, H - base_h), (W / 2 - 0.01, 0, base_h + (H - base_h) / 2), WHITE, "matte",
                material="wood"),
             _p("Top", "box", (W, D, 0.03), (0, 0, H - 0.015), WHITE, "matte", material="wood")]
    for k, z in enumerate(zs):
        parts.append(_p(f"Shelf{k + 1}", "box", (W - 0.04, D - 0.04, 0.008), (0, -0.01, z), "#E6F0F2", "glass",
                        material="glass"))
    return Product(slug="eyewear_wall_case", name="眼鏡フレームの壁面ケース", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=55.0, static=True, material="wood",
                   description="形は眼鏡店の壁際の一般的なフレームの見本棚（幅 900 mm・奥行き 250 mm・高さ 2000 mm、下は引き出しの"
                               "収納、上は光る背板の前にガラスの棚 7 段）で、寸法・質量は代表値。棚に眼鏡を並べる。",
                   tags=["眼鏡の棚", "フレーム棚", "眼鏡店", "壁面ケース", "eyewear display", "eyeglass display",
                         "frame display", "eyewear wall case", "glasses shelf", "display case", *EYE_TAGS], photos=[],
                   colors=Colors(label_base=WHITE), images=[], parts=parts)


def phoropter_stand() -> Product:
    """A refraction stand with a phoropter on its arm, the eye-test instrument of an optician (patient side -Y)."""
    parts = [_p("Base", "cylinder", (0.50, 0.50, 0.05), (0, 0, 0.025), "#E9ECEF", "matte", material="metal"),
             _p("Column", "cylinder", (0.07, 0.07, 1.30), (0, 0, 0.05 + 0.65), "#D5D9DE", "metal", material="metal"),
             _p("Arm", "box", (0.06, 0.42, 0.06), (0, -0.21, 1.32), "#D5D9DE", "metal", material="metal"),
             _p("Hanger", "box", (0.04, 0.04, 0.08), (0, -0.40, 1.25), "#3A3F45", "matte", material="metal"),
             _p("Head", "box", (0.32, 0.10, 0.18), (0, -0.40, 1.12), "#2F3338", "matte", material="metal",
                bevel=0.02)]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        parts += [_p(f"Dial{side}", "cylinder", (0.13, 0.13, 0.03), (s * 0.08, -0.465, 1.11), "#4A5058", "metal",
                     rot=(90, 0, 0), collision=False, material="metal"),
                  _p(f"Eyepiece{side}", "cylinder", (0.035, 0.035, 0.03), (s * 0.08, -0.495, 1.11), "#101215", "glossy",
                     rot=(90, 0, 0), collision=False, material="plastic")]
    parts.append(_p("ForeheadRest", "box", (0.10, 0.03, 0.03), (0, -0.465, 1.19), "#101215", "matte", collision=False,
                    material="plastic"))
    return Product(slug="phoropter_stand", name="検眼器（フォロプター）のスタンド", shape_class="assembly",
                   category="fixture", dims=Dimensions(1.35, 0.50, depth=0.76), mass_kg=60.0, static=True,
                   material="metal",
                   description="形は眼鏡店の検眼室の一般的な検眼器（フォロプター）とスタンド（台の直径 500 mm・高さ 1350 mm、"
                               "腕の先に左右のレンズを切り替えるダイヤルと接眼部）で、寸法・質量は代表値。正面（-Y）が"
                               "検眼を受ける人の側。",
                   tags=["検眼器", "フォロプター", "視力検査", "検眼", "phoropter", "refractor", "eye test",
                         "refraction stand", "optometry", *EYE_TAGS], photos=[], colors=Colors(label_base="#2F3338"),
                   images=[], parts=parts)


PRODUCTS = {f.__name__: f for f in (cut_flower_bucket, toy_car_box, building_blocks_tub, plush_bear,
                                        toy_car_blister, cat_food_can, dog_toy, pet_toy_blister, dog_treat_bag,
                                        leather_shoe, shoe_insole_pack, shoelace_blister, eyeglasses, glasses_case,
                                        glasses_cleaner_blister, shoe_display_riser, shoe_fitting_bench,
                                        shoe_floor_mirror, eyewear_wall_case, phoropter_stand)}
