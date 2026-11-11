"""Fictional backyard and logistics fixtures and materials: roll cage carts
(empty and loaded), a bread / bento delivery tray and a stack of them on a dolly, a folding container and a stack,
plain taped cartons (S / M / L), a two-wheel hand truck, a hand pallet jack, a backyard steel rack and an
inspection table. They are for robot transport, restocking and inspection scenarios.

As in hc_fixtures.py: no real names or logos, typical sizes, front is -Y. Things that are moved by hand (carts,
trays, containers, cartons, the hand truck and the pallet jack) are dynamic rigid bodies; wheels and casters are
plain parts of the body (they do not turn, there are no joints). What a loaded cart or a stack carries is part of the
same rigid body (fixed contents). The steel rack, the inspection table and the container stack are kinematic
(static). Surfaces meant for goods are thin horizontal boards, so a tool that fills shelves with goods finds them as shelves; lips and
braces sit outside or below the boards. The thin wires of the cage panels are visual only (collision off); the
frame tubes and rails around them collide.
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .conv_goods import BOX_FACES, _faces
from .elec_goods import _kraft
from .hc_fixtures import GALV, KRAFT, STEEL, STEEL_DARK, WHITE, _carton, _holes, _mesh, _p, _steel
from .paint import Canvas, mix
from .products import INK, _face
from .store_more import _rod

RUBBER = "#2A2C30"
TRAY_BLUE = "#2F6DB5"
CONTAINER_GRAY = "#7F8A94"
RACK_IVORY = "#DCDBD3"
JACK_RED = "#C62828"
TAPE = "#D9B77E"  # kraft packing tape (a little lighter and yellower than the board)
LOGI_TAGS = ["バックヤード", "物流", "搬送", "倉庫", "backyard", "logistics", "warehouse"]


def _wheel(name: str, d: float, w: float, center, axis: str = "X") -> Part:
    """A wheel or caster (cylinder) rolling across its axis; axis X rolls along Y, axis Y rolls along X."""
    rot = [0, 90, 0] if axis == "X" else [90, 0, 0]
    return _p(name, "cylinder", (d, d, w), center, RUBBER, "matte", rot, material="rubber")


def _bbox(parts: list[Part]) -> tuple[np.ndarray, np.ndarray]:
    """The bounding box of the parts (boxes and cylinders as their oriented box)."""
    pts = []
    for p in parts:
        rx, ry, rz = (math.radians(a) for a in (p.rotation or [0, 0, 0]))
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx  # XYZ order
        h = np.array(p.size) / 2
        corners = np.array([[a, b, c] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]) * h
        pts.append(corners @ R.T + np.array(p.center))
    allp = np.vstack(pts)
    return allp.min(0), allp.max(0)


def _dims(parts: list[Part]) -> Dimensions:
    lo, hi = _bbox(parts)
    w, d, h = hi - lo
    return Dimensions(round(float(h), 4), round(float(w), 4), depth=round(float(d), 4))


def _shift(parts: list[Part], dx=0.0, dy=0.0, dz=0.0, prefix: str = "", k: int = 0) -> list[Part]:
    """Copies of the parts moved by (dx, dy, dz), renamed with prefix, face indices shifted by k."""
    out = []
    for p in parts:
        faces = {f: (None if i is None else i + k) for f, i in p.faces.items()} if p.faces else None
        out.append(Part(name=f"{prefix}{p.name}", shape=p.shape, size=list(p.size),
                        center=[p.center[0] + dx, p.center[1] + dy, p.center[2] + dz], rotation=list(p.rotation),
                        color=p.color, finish=p.finish, faces=faces, collision=p.collision, material=p.material,
                        bevel=p.bevel, thin_walled=p.thin_walled))
    return out


# ---------------------------------------------------------------- roll cage cart


def _cage_parts(W: float, D: float, H: float, k_deck: int) -> list[Part]:
    """A roll cage cart (roll box pallet): four casters, a steel deck, wire-mesh panels on the back and both sides,
    open at the front (-Y). Face index k_deck = the deck's mesh."""
    deck_top, tube = 0.17, 0.03
    parts = []
    cx, cy = W / 2 - 0.08, D / 2 - 0.08
    for n, (x, y) in enumerate(((-cx, -cy), (cx, -cy), (-cx, cy), (cx, cy))):
        parts += [_wheel(f"Caster{n}", 0.10, 0.035, (x, y, 0.05)),
                  _steel(f"CasterFork{n}", (0.05, 0.06, 0.04), (x, y, 0.12), GALV)]
    rz = deck_top - tube / 2
    for k, y in enumerate((-D / 2 + tube / 2, D / 2 - tube / 2)):  # base frame
        parts.append(_steel(f"BaseRailX{k}", (W, tube, tube), (0, y, rz), STEEL_DARK))
    for k, x in enumerate((-W / 2 + tube / 2, W / 2 - tube / 2)):
        parts.append(_steel(f"BaseRailY{k}", (tube, D - 2 * tube, tube), (x, 0, rz), STEEL_DARK))
    parts.append(_steel("Deck", (W - 2 * tube, D - 2 * tube, 0.02), (0, 0, deck_top - 0.01), GALV,
                        faces={"top": k_deck}))
    post_h = H - deck_top
    for n, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):  # corner posts
        parts.append(_steel(f"Post{n}", (tube, tube, post_h), (x * (W / 2 - tube / 2), y * (D / 2 - tube / 2),
                                                               deck_top + post_h / 2), GALV))
    xs, ys = W / 2 - tube / 2, D / 2 - tube / 2
    for k, z in enumerate((0.62, 1.12, H - 0.015)):  # rails on the three panels (collide)
        t = 0.03 if z > H - 0.02 else 0.02
        parts += [_steel(f"BackRail{k}", (W - 2 * tube, t, t), (0, ys, z), GALV),
                  _steel(f"LeftRail{k}", (t, D - 2 * tube, t), (-xs, 0, z), GALV),
                  _steel(f"RightRail{k}", (t, D - 2 * tube, t), (xs, 0, z), GALV)]
    wire, z0, z1 = 0.006, deck_top, H - 0.03
    wz = [z0 + 0.15 * i for i in range(1, int((z1 - z0) / 0.15) + 1) if z0 + 0.15 * i < z1 - 0.05]
    for i in range(1, 8):  # back panel wires
        x = -W / 2 + i * W / 8
        parts.append(_steel(f"BackWireV{i}", (wire, wire, z1 - z0), (x, ys, (z0 + z1) / 2), GALV, collision=False))
    for i in range(1, 6):  # side panel wires
        y = -D / 2 + i * D / 6
        for side, x in (("Left", -xs), ("Right", xs)):
            parts.append(_steel(f"{side}WireV{i}", (wire, wire, z1 - z0), (x, y, (z0 + z1) / 2), GALV,
                                collision=False))
    for j, z in enumerate(wz):
        parts += [_steel(f"BackWireH{j}", (W - 2 * tube, wire, wire), (0, ys, z), GALV, collision=False),
                  _steel(f"LeftWireH{j}", (wire, D - 2 * tube, wire), (-xs, 0, z), GALV, collision=False),
                  _steel(f"RightWireH{j}", (wire, D - 2 * tube, wire), (xs, 0, z), GALV, collision=False)]
    return parts


CAGE_W, CAGE_D, CAGE_H = 0.80, 0.60, 1.70
CAGE_TAGS = ["カゴ台車", "ロールボックスパレット", "ロールパレット", "かご車", "台車", "キャスター", *LOGI_TAGS,
             "roll cage", "roll container", "roll box pallet", "cage trolley", "cart"]


def roll_cage_cart() -> Product:
    parts = _cage_parts(CAGE_W, CAGE_D, CAGE_H, 0)
    return Product(slug="roll_cage_cart", name="カゴ台車 800×600×1700（空）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=30.0, material="steel",
                   description="形は物流センターから店へ商品を運ぶ一般的なカゴ台車（ロールボックスパレット。外寸 800 × 600 × 1700 mm、"
                               "床板の上面 170 mm、キャスター 4 個、背面と両側面が金網で前面は開いている）で、寸法・質量は代表値。"
                               "床板は 商品を並べる棚板として使える。金網の細い線は見た目だけ（当たり判定なし）で、枠と横桟は当たる。"
                               "押して動かす物なので動く剛体（キャスターは回らない）。",
                   tags=CAGE_TAGS, photos=[], colors=Colors(label_base=GALV), images=[_mesh(740, 540, 5601)],
                   parts=parts)


def _tape_top(w_mm: float, d_mm: float, seed: int, color: str = KRAFT) -> Canvas:
    """The top of a taped carton: the seam of the flaps along X with packing tape over it."""
    c = _kraft(w_mm, d_mm, seed) if color == KRAFT else Canvas(w_mm, d_mm, None, color, seed)
    c.line([(0, d_mm / 2), (w_mm, d_mm / 2)], mix(KRAFT, "#000000", 0.35), 0.8)
    tw = min(50.0, d_mm * 0.3)
    c.rect(0, d_mm / 2 - tw / 2, w_mm, d_mm / 2 + tw / 2, fill=TAPE)
    for x in (w_mm * 0.3, w_mm * 0.72):  # creases in the tape
        c.line([(x, d_mm / 2 - tw / 2), (x + 6, d_mm / 2 + tw / 2)], mix(TAPE, "#FFFFFF", 0.35), 0.6)
    return c


def roll_cage_cart_loaded() -> Product:
    """The roll cage cart with four layers of product cartons (2 x 2 per layer) as fixed parts."""
    cw, cd, ch = 0.36, 0.26, 0.29
    goods = [("緑茶 500ml", "24 本入  ケース", "#2E7D32"), ("カップめん しょうゆ味", "12 食入", "#C62828"),
             ("ティッシュペーパー", "5 箱 × 4 パック", "#1F5AA6"), ("ポテトチップス うすしお", "12 袋入", "#E39A14")]
    imgs = [_mesh(740, 540, 5611)]
    faces_by_layer = []
    for n, (title, sub, _) in enumerate(goods):
        k = len(imgs)
        imgs += [_carton(360, 290, 5612 + 4 * n, title, sub), _carton(260, 290, 5613 + 4 * n, title, sub),
                 _face(_tape_top(360, 260, 5614 + 4 * n).array(), "paper", 5614 + 4 * n, 0.7, 6)]
        faces_by_layer.append({"front": k, "back": k, "left": k + 1, "right": k + 1, "top": k + 2})
    parts = _cage_parts(CAGE_W, CAGE_D, CAGE_H, 0)
    for layer in range(4):
        z = 0.17 + ch * layer + ch / 2
        for i in range(2):
            for j in range(2):
                parts.append(_p(f"Carton{layer}{i}{j}", "box", (cw, cd, ch - 0.002),
                                ((i - 0.5) * (cw + 0.005), (j - 0.5) * (cd + 0.005) + 0.005, z), KRAFT, "matte",
                                faces=faces_by_layer[layer], material="cardboard"))
    return Product(slug="roll_cage_cart_loaded", name="カゴ台車（商品の段ボールを積んだもの）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=110.0, material="steel",
                   description="形は roll_cage_cart と同じカゴ台車に、商品の段ボールケース（360 × 260 × 290 mm）を 1 段 4 箱・4 段積んだ"
                               "もので、寸法・質量は代表値。段ボールは台車の固定の部品（当たり判定あり・台車と一体で動く）。"
                               "押して動かす物なので動く剛体。段ボールの印刷・商品名は架空。",
                   tags=[*CAGE_TAGS, "段ボール", "積載", "納品", "品出し", "loaded cart", "cartons"], photos=[],
                   colors=Colors(label_base=GALV), images=imgs, parts=parts)


# ---------------------------------------------------------------- bread tray (banju) and folding container


def _crate_wall(w_mm: float, h_mm: float, seed: int, color: str, handle: bool, hinge: bool = False) -> np.ndarray:
    """A moulded plastic crate wall: a rim band, vertical ribs, an optional hand hole and fold line."""
    c = Canvas(w_mm, h_mm, None, color, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(color, WHITE, 0.12), mix(color, "#000000", 0.10))
    rib = mix(color, "#000000", 0.22)
    rim = min(16.0, h_mm * 0.14)
    c.rect(0, 0, w_mm, rim, fill=mix(color, WHITE, 0.18))
    c.line([(0, rim), (w_mm, rim)], rib, 1.2)
    x = 30.0
    while x < w_mm - 10:
        c.line([(x, rim + 4), (x, h_mm - 6)], rib, 2.0)
        x += 40.0
    c.line([(0, h_mm - 5), (w_mm, h_mm - 5)], rib, 1.2)
    if hinge:
        c.rect(0, h_mm * 0.42, w_mm, h_mm * 0.42 + 6, fill=mix(color, "#000000", 0.3))
    if handle:
        hw, hh = min(110.0, w_mm * 0.3), min(32.0, h_mm * 0.22)
        y0 = rim + 8
        c.rect(w_mm / 2 - hw / 2, y0, w_mm / 2 + hw / 2, y0 + hh, fill="#1C1E21", radius=hh / 2)
    return _face(c.array(), "plastic", seed, 0.4, 4)


def _slotted_floor(w_mm: float, d_mm: float, seed: int, color: str) -> np.ndarray:
    """The floor of a tray seen from above: rows of drain slots between ribs."""
    c = Canvas(w_mm, d_mm, None, color, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(color, WHITE, 0.08), mix(color, "#000000", 0.08))
    dark = mix(color, "#000000", 0.45)
    y = 2.0  # rows run off the edges (an edge of one colour would be trimmed)
    while y < d_mm + 4:
        x = -20.0 if int(y / 30) % 2 else 3.0
        while x < w_mm:
            c.rect(x, y - 4, x + 34, y + 4, fill=dark, radius=4)
            x += 46.0
        y += 30.0
    return _face(c.array(), "plastic", seed, 0.4, 4)


def _crate_parts(W: float, D: float, H: float, t: float, color: str, k: int) -> list[Part]:
    """An open-top crate: a floor board inside the walls (fill finds it) and four walls outside it.
    Face indices: k = long wall, k + 1 = short wall (hand holes), k + 2 = floor."""
    ft = 0.012
    long_f = {"front": k, "back": k}
    short_f = {"left": k + 1, "right": k + 1}
    return [_p("Floor", "box", (W - 2 * t, D - 2 * t, ft), (0, 0, ft / 2), color, faces={"top": k + 2},
               material="plastic", bevel=0.002),
            _p("WallFront", "box", (W, t, H), (0, -D / 2 + t / 2, H / 2), color, faces=long_f, material="plastic",
               bevel=0.003),
            _p("WallBack", "box", (W, t, H), (0, D / 2 - t / 2, H / 2), color, faces=long_f, material="plastic",
               bevel=0.003),
            _p("WallLeft", "box", (t, D - 2 * t, H), (-W / 2 + t / 2, 0, H / 2), color, faces=short_f,
               material="plastic", bevel=0.003),
            _p("WallRight", "box", (t, D - 2 * t, H), (W / 2 - t / 2, 0, H / 2), color, faces=short_f,
               material="plastic", bevel=0.003)]


TRAY = (0.62, 0.42, 0.13, 0.012)  # W, D, H, wall thickness
TRAY_TAGS = ["番重", "ばんじゅう", "パン箱", "配送トレー", "コンテナ", "パン", "弁当", "コンビニ", *LOGI_TAGS,
             "bread tray", "bakery tray", "delivery tray", "food tray", "crate"]


def _tray_images(seed: int) -> list[np.ndarray]:
    W, D, H, t = (v * 1000 for v in TRAY)
    return [_crate_wall(W, H, seed, TRAY_BLUE, False), _crate_wall(D - 2 * t, H, seed + 1, TRAY_BLUE, True),
            _slotted_floor(W - 2 * t, D - 2 * t, seed + 2, TRAY_BLUE)]


def bread_tray() -> Product:
    W, D, H, t = TRAY
    parts = _crate_parts(W, D, H, t, TRAY_BLUE, 0)
    return Product(slug="bread_tray", name="番重（パン・弁当の配送用トレー）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=1.4, material="plastic",
                   description="形はパン・弁当・総菜を工場から店へ運ぶ一般的な樹脂の番重（外寸 620 × 420 × 130 mm、底は水抜きの穴、"
                               "短い側面に手掛け穴）で、寸法・質量は代表値。上の縁が平らで同じ番重をそのまま積み重ねられる。"
                               "底板は 商品を並べる棚板として使える。動く剛体。",
                   tags=TRAY_TAGS, photos=[], colors=Colors(label_base=TRAY_BLUE), images=_tray_images(5621),
                   parts=parts)


def bread_tray_stack() -> Product:
    """Eight bread trays stacked on a low four-caster dolly (the trays are fixed parts of the dolly)."""
    W, D, H, t = TRAY
    seat = 0.13  # top of the dolly frame
    DW, DD = W + 0.04, D + 0.04
    imgs = _tray_images(5631)
    parts = []
    cx, cy = DW / 2 - 0.06, DD / 2 - 0.06
    for n, (x, y) in enumerate(((-cx, -cy), (cx, -cy), (-cx, cy), (cx, cy))):
        parts += [_wheel(f"Caster{n}", 0.075, 0.025, (x, y, 0.0375)),
                  _steel(f"CasterFork{n}", (0.04, 0.05, 0.025), (x, y, 0.0875), GALV)]
    rt = 0.03
    for k, y in enumerate((-DD / 2 + rt / 2, DD / 2 - rt / 2)):
        parts.append(_steel(f"FrameX{k}", (DW, rt, rt), (0, y, seat - rt / 2), STEEL_DARK, finish_="plastic"))
    for k, x in enumerate((-DW / 2 + rt / 2, 0.0, DW / 2 - rt / 2)):
        parts.append(_steel(f"FrameY{k}", (rt, DD - 2 * rt, rt), (x, 0, seat - rt / 2), STEEL_DARK,
                            finish_="plastic"))
    for n, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):  # corner stops outside the trays
        parts.append(_steel(f"Stop{n}", (0.03, 0.03, 0.05), (x * (DW / 2 - 0.015), y * (DD / 2 - 0.015), seat + 0.025),
                            STEEL_DARK, finish_="plastic"))
    for level in range(8):
        parts += _shift(_crate_parts(W, D, H, t, TRAY_BLUE, 0), dz=seat + H * level, prefix=f"Tray{level}")
    return Product(slug="bread_tray_stack", name="番重の 8 段積み（ドーリー付き）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=16.0, material="plastic",
                   description="形は bread_tray と同じ番重（620 × 420 × 130 mm）を、番重用の低いドーリー（キャスター 4 個、上面 130 mm）"
                               "に 8 段積んだもので、寸法・質量は代表値。番重はドーリーの固定の部品（台車と一体で動く）。"
                               "いちばん上の番重の底板は 商品を並べる棚板として使える。押して動かす物なので動く剛体（キャスターは回らない）。",
                   tags=[*TRAY_TAGS, "ドーリー", "台車", "積み重ね", "dolly", "tray stack"], photos=[],
                   colors=Colors(label_base=TRAY_BLUE), images=imgs, parts=parts)


ORICON = (0.53, 0.366, 0.315, 0.015)  # W, D, H, wall thickness (50 L)
ORICON_TAGS = ["折りたたみコンテナ", "オリコン", "コンテナ", "通い箱", "50L", *LOGI_TAGS, "folding container",
               "collapsible crate", "foldable crate", "tote", "crate"]


def _oricon_images(seed: int) -> list[np.ndarray]:
    W, D, H, t = (v * 1000 for v in ORICON)
    return [_crate_wall(W, H, seed, CONTAINER_GRAY, False, hinge=True),
            _crate_wall(D - 2 * t, H, seed + 1, CONTAINER_GRAY, True),
            _slotted_floor(W - 2 * t, D - 2 * t, seed + 2, mix(CONTAINER_GRAY, "#000000", 0.05))]


def folding_container() -> Product:
    W, D, H, t = ORICON
    parts = _crate_parts(W, D, H, t, CONTAINER_GRAY, 0)
    return Product(slug="folding_container", name="折りたたみコンテナ（オリコン）50L", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=2.2, material="plastic",
                   description="形は通販・物流の通い箱に使う一般的な樹脂の折りたたみコンテナ（容量約 50 L、外寸 530 × 366 × 315 mm、"
                               "ふたなし、短い側面に手掛け穴、長い側面に折り目）で、寸法・質量は代表値。組み立てた形で、"
                               "折りたたみの関節はない。底板は 商品を並べる棚板として使える。動く剛体。",
                   tags=ORICON_TAGS, photos=[], colors=Colors(label_base=CONTAINER_GRAY),
                   images=_oricon_images(5641), parts=parts)


def folding_container_stack() -> Product:
    W, D, H, t = ORICON
    parts = []
    for level in range(5):
        parts += _shift(_crate_parts(W, D, H, t, CONTAINER_GRAY, 0), dz=H * level, prefix=f"Box{level}")
    return Product(slug="folding_container_stack", name="折りたたみコンテナの 5 段積み", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=11.0, static=True, material="plastic",
                   description="形は folding_container と同じ折りたたみコンテナ（50 L、530 × 366 × 315 mm）を床に 5 段積んだ山で、"
                               "寸法・質量は代表値。全体を 1 つの動かない物（static）にする。いちばん上のコンテナの底板は "
                               "商品を並べる棚板として使える。",
                   tags=[*ORICON_TAGS, "積み重ね", "container stack"], photos=[],
                   colors=Colors(label_base=CONTAINER_GRAY), images=_oricon_images(5651), parts=parts)


# ---------------------------------------------------------------- plain cartons


def _plain_carton(W: float, D: float, H: float, seed: int) -> list[np.ndarray]:
    """Six faces of a plain taped carton (mm): tape over the top and bottom seams, running down the ends."""
    tw = min(50.0, D * 0.3)
    flap = min(60.0, H * 0.3)
    canv = []
    for k in range(2):  # front, back: plain board with the flap creases
        c = _kraft(W, H, seed + k)
        for y in (6.0, H - 6.0):
            c.line([(0, y), (W, y)], mix(KRAFT, "#000000", 0.25), 0.6)
        if k == 1:  # the board maker's stamp (generic)
            c.ellipse(W * 0.06, H * 0.62, W * 0.06 + H * 0.26, H * 0.88, outline="#4A3A2A", width=1.2)
            c.text(W * 0.06 + H * 0.13, H * 0.75, "K5AF", H * 0.06, "#4A3A2A", 800)
        canv.append(c)
    for k in range(2):  # right, left: the tape comes down from the top and up from the bottom
        c = _kraft(D, H, seed + 2 + k)
        c.rect(D / 2 - tw / 2, 0, D / 2 + tw / 2, flap, fill=TAPE)
        c.rect(D / 2 - tw / 2, H - flap, D / 2 + tw / 2, H, fill=TAPE)
        c.line([(D / 2, flap), (D / 2, H - flap)], mix(KRAFT, "#000000", 0.25), 0.6)  # the glued joint
        canv.append(c)
    canv += [_tape_top(W, D, seed + 4), _tape_top(W, D, seed + 5)]
    return _faces(canv, "paper", seed, 0.6)


def _carton_box(slug: str, size_name: str, W: float, D: float, H: float, mass: float, seed: int) -> Product:
    return Product(slug=slug, name=f"無地の段ボール箱 {size_name}（{W:.0f}×{D:.0f}×{H:.0f}mm）", shape_class="box",
                   category="household", dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=mass,
                   material="paper",
                   description=f"形は印刷のない一般的な段ボール箱（A 式、外寸 {W:.0f} × {D:.0f} × {H:.0f} mm）で、上下の合わせ目を"
                               "クラフトテープで止めたもの。寸法は代表値、質量は中身の入った状態の代表値。動く剛体。",
                   tags=["段ボール", "段ボール箱", "ダンボール", "無地", "梱包", "荷物", "宅配", f"{size_name}サイズ",
                         *LOGI_TAGS, "cardboard box", "carton", "corrugated box", "shipping box", "parcel"],
                   photos=[], colors=Colors(label_base=KRAFT), images=_plain_carton(W, D, H, seed), faces=BOX_FACES)


def carton_box_s() -> Product:
    return _carton_box("carton_box_s", "S", 320.0, 240.0, 200.0, 3.0, 5661)


def carton_box_m() -> Product:
    return _carton_box("carton_box_m", "M", 400.0, 300.0, 300.0, 6.0, 5671)


def carton_box_l() -> Product:
    return _carton_box("carton_box_l", "L", 500.0, 400.0, 400.0, 10.0, 5681)


# ---------------------------------------------------------------- hand truck and pallet jack


def hand_truck() -> Product:
    """A two-wheel hand truck standing upright on its nose plate (-Y) and its wheels (+Y)."""
    frame, rail_x, top = "#2F3338", 0.20, 1.15
    parts = [_steel("NosePlate", (0.44, 0.22, 0.008), (0, -0.10, 0.004), GALV, faces=None),
             _steel("NoseLip", (0.44, 0.012, 0.03), (0, 0.004, 0.023), GALV)]
    for k, x in enumerate((-rail_x, rail_x)):
        parts += [_p(f"Rail{k}", "cylinder", (0.03, 0.03, top - 0.023), (x, 0.025, 0.008 + (top - 0.023) / 2), frame,
                     "metal", material="steel"),
                  _steel(f"AxleBracket{k}", (0.03, 0.10, 0.04), (x, 0.075, 0.15), frame)]
    for k, z in enumerate((0.40, 0.70, 1.00)):
        parts.append(_rod(f"CrossBar{k}", (-rail_x, 0.025, z), (rail_x, 0.025, z), 0.02, frame, collision=True))
    parts.append(_rod("Handle", (-rail_x - 0.015, 0.025, top - 0.015), (rail_x + 0.015, 0.025, top - 0.015), 0.032,
                      RUBBER, "matte", collision=True))
    parts.append(_rod("Axle", (-0.29, 0.125, 0.125), (0.29, 0.125, 0.125), 0.02, GALV, collision=True))
    for k, x in enumerate((-0.26, 0.26)):
        parts.append(_wheel(f"Wheel{k}", 0.25, 0.06, (x, 0.125, 0.125)))
    for p in parts:
        p.material = p.material or ("rubber" if p.color == RUBBER else "steel")
    return Product(slug="hand_truck", name="二輪台車", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=12.0, material="steel",
                   description="形は段ボールや飲料のケースを運ぶ一般的な二輪台車（高さ約 1150 mm、つめ板 440 × 220 mm、車輪 250 mm）で、"
                               "寸法・質量は代表値。つめ板と車輪で床に立てた向き（つめ板が前 -Y）。つめ板は 商品を並べる棚板として使える。"
                               "動かせる物なので動く剛体（車輪は回らない）。",
                   tags=["二輪台車", "台車", "ハンドトラック", "運搬", "品出し", *LOGI_TAGS, "hand truck",
                         "two-wheel dolly", "sack truck", "dolly"],
                   photos=[], colors=Colors(label_base=frame), images=[], parts=parts)


def pallet_jack() -> Product:
    """A manual pallet truck: two forks toward +Y, the pump and steering wheels at -Y, the tiller upright."""
    fork_w, fork_x, fork_l = 0.16, 0.19, 1.15
    fy0 = -0.10  # forks start here and run to fy0 + fork_l
    parts = []
    for k, x in enumerate((-fork_x, fork_x)):
        parts += [_steel(f"Fork{k}", (fork_w, fork_l, 0.06), (x, fy0 + fork_l / 2, 0.055), JACK_RED,
                         finish_="plastic"),
                  _steel(f"ForkTip{k}", (fork_w, 0.05, 0.03), (x, fy0 + fork_l + 0.025, 0.04), JACK_RED,
                         finish_="plastic"),
                  _wheel(f"LoadRoller{k}", 0.07, 0.08, (x, fy0 + fork_l - 0.12, 0.035)),
                  _wheel(f"EntryRoller{k}", 0.05, 0.06, (x, fy0 + fork_l - 0.03, 0.025))]
    parts += [_steel("Body", (2 * fork_x + fork_w, 0.20, 0.10), (0, -0.15, 0.13), JACK_RED, finish_="plastic"),
              _p("Pump", "cylinder", (0.09, 0.09, 0.22), (0, -0.22, 0.29), "#3A3D42", "metal", material="steel"),
              _steel("PumpHead", (0.14, 0.10, 0.06), (0, -0.23, 0.42), JACK_RED, finish_="plastic"),
              _steel("SteerFork", (0.17, 0.08, 0.05), (0, -0.22, 0.195), "#3A3D42")]
    for k, x in enumerate((-0.06, 0.06)):
        parts.append(_wheel(f"SteerWheel{k}", 0.18, 0.05, (x, -0.22, 0.09)))
    ty0, ty1, tz0, tz1 = -0.24, -0.31, 0.45, 1.18
    parts.append(_rod("Tiller", (0, ty0, tz0), (0, ty1, tz1), 0.035, JACK_RED, "plastic", collision=True))
    for k, x in enumerate((-0.13, 0.13)):  # the handle loop
        parts.append(_rod(f"HandleSide{k}", (x, ty1, tz1 - 0.02), (x, ty1, tz1 + 0.10), 0.025, JACK_RED, "plastic",
                          collision=True))
    parts += [_rod("HandleYoke", (-0.13, ty1, tz1 - 0.02), (0.13, ty1, tz1 - 0.02), 0.03, JACK_RED, "plastic",
                   collision=True),
              _rod("Grip", (-0.145, ty1, tz1 + 0.10), (0.145, ty1, tz1 + 0.10), 0.032, RUBBER, "matte",
                   collision=True)]
    for p in parts:
        p.material = p.material or ("rubber" if p.color == RUBBER else "steel")
    return Product(slug="pallet_jack", name="ハンドリフト（手動のパレットトラック）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=75.0, material="steel",
                   description="形は倉庫・バックヤードでパレットを運ぶ一般的な手動のハンドリフト（フォーク長さ 1150 mm・全幅 540 mm、"
                               "フォークを下げた高さ 85 mm、操作ハンドルを立てた状態）で、寸法・質量は代表値。油圧の上げ下げや"
                               "車輪・ハンドルの関節はなく、床に置く動く剛体（車輪は回らない）。フォークは +Y 側。",
                   tags=["ハンドリフト", "ハンドパレット", "パレットトラック", "パレット", "運搬", *LOGI_TAGS,
                         "pallet jack", "pallet truck", "hand pallet truck", "pump truck"],
                   photos=[], colors=Colors(label_base=JACK_RED), images=[], parts=parts)


# ---------------------------------------------------------------- steel rack and inspection table


def backyard_steel_rack() -> Product:
    """A light-duty boltless steel rack, 1800 x 600 x 1800, with four shelf plates."""
    W, D, H = 1.80, 0.60, 1.80
    post = 0.04
    plate_w, plate_d = W - 2 * post, D - 2 * post - 0.02  # the plates; their lips sit just outside them
    levels = (0.12, 0.66, 1.22, H - 0.02)
    parts = []
    for n, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts += [_steel(f"Post{n}", (post, post, H), (x * (W / 2 - post / 2), y * (D / 2 - post / 2), H / 2),
                         RACK_IVORY, finish_="plastic"),
                  _steel(f"Foot{n}", (post, post, 0.006), (x * (W / 2 - post / 2), y * (D / 2 - post / 2), 0.003),
                         STEEL_DARK)]
    yl = plate_d / 2 + 0.01  # lip centre (outside the plate)
    for k, z in enumerate(levels):
        parts += [_steel(f"Shelf{k}", (plate_w, plate_d, 0.02), (0, 0, z - 0.01), RACK_IVORY, finish_="plastic"),
                  _steel(f"LipFront{k}", (plate_w, 0.02, 0.045), (0, -yl, z - 0.0225), RACK_IVORY, finish_="plastic"),
                  _steel(f"LipBack{k}", (plate_w, 0.02, 0.045), (0, yl, z - 0.0225), RACK_IVORY, finish_="plastic")]
        for i, x in enumerate((-W / 2 + post / 2, W / 2 - post / 2)):  # side beams below each plate
            parts.append(_steel(f"SideBeam{k}{i}", (0.02, D - 2 * post, 0.03), (x, 0, z - 0.035), RACK_IVORY,
                                finish_="plastic"))
    xb = W / 2 - post / 2
    for i, x in enumerate((-xb, xb)):  # X braces on both sides (visual)
        for k in range(len(levels) - 1):
            z0, z1 = levels[k] - 0.05, levels[k + 1] - 0.05
            yy = D / 2 - post
            parts += [_rod(f"Brace{i}{k}a", (x, -yy, z0), (x, yy, z1), 0.008, STEEL_DARK),
                      _rod(f"Brace{i}{k}b", (x, yy, z0), (x, -yy, z1), 0.008, STEEL_DARK)]
    for p in parts:
        p.material = p.material or "steel"
    return Product(slug="backyard_steel_rack", name="バックヤードのスチールラック 1800×600×1800（4 段）",
                   shape_class="assembly", category="fixture", dims=_dims(parts), mass_kg=45.0, static=True,
                   material="steel",
                   description="形はバックヤード・倉庫で在庫を置く一般的なボルトレスの軽量スチールラック（幅 1800 × 奥行き 600 × 高さ "
                               "1800 mm、棚板 4 段：上面が床から 120・660・1220・1780 mm）で、寸法・質量は代表値。"
                               "棚板は奥行き 500 mm の水平の板で、前後の折り返しと側面の梁は板の外・下にある（商品を並べられる）。"
                               "側面の筋交いは見た目だけ。動かない物（static）。",
                   tags=["スチールラック", "ラック", "棚", "軽量棚", "ボルトレスラック", "在庫", "ストック", *LOGI_TAGS,
                         "steel rack", "steel shelving", "boltless shelving", "storage rack", "backroom shelving"],
                   photos=[], colors=Colors(label_base=RACK_IVORY), images=[], parts=parts)


def _work_top(w_mm: float, d_mm: float, seed: int) -> np.ndarray:
    """A pale green linoleum work top with a ruler printed along the front edge."""
    base = "#B9CBB8"
    c = Canvas(w_mm, d_mm, None, base, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(base, WHITE, 0.1), mix(base, "#000000", 0.05))
    grid = mix(base, "#000000", 0.12)
    x = 50.0
    while x < w_mm:
        c.line([(x, 40), (x, d_mm - 10)], grid, 0.6)
        x += 50.0
    y = 40.0
    while y < d_mm - 10:
        c.line([(10, y), (w_mm - 10, y)], grid, 0.6)
        y += 50.0
    y0 = d_mm - 30  # the ruler (front edge = bottom of the image)
    c.rect(0, y0, w_mm, d_mm, fill="#F2F2EC")
    for mm in range(0, int(w_mm) + 1, 10):
        L = 14 if mm % 100 == 0 else (9 if mm % 50 == 0 else 5)
        c.line([(mm, d_mm), (mm, d_mm - L)], INK, 0.6)
        if mm % 100 == 0 and 0 < mm < w_mm - 20:
            c.text(mm + 2, y0 + 8, str(mm // 10), 7, INK, 700, anchor="lm")
    return _face(c.array(), "plastic", seed, 0.3, 4)


def inspection_table() -> Product:
    """An inspection work table with a lower shelf and an upper shelf on a pegboard riser at the back."""
    W, D, H_top = 1.50, 0.75, 0.85
    leg = 0.04
    lx, ly = W / 2 - 0.03, D / 2 - 0.03
    imgs = [_work_top(1500, 750, 5691), _holes(1400, 380, 5692)]
    parts = [_p("Top", "box", (W, D, 0.03), (0, 0, H_top - 0.015), "#B9CBB8", "plastic", faces={"top": 0},
                material="plastic", bevel=0.004),
             _steel("LowerShelf", (2 * (lx - leg / 2), 2 * (ly - leg / 2), 0.02), (0, 0, 0.18), STEEL, finish_="plastic")]
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts += [_steel(f"Leg{n}", (leg, leg, H_top - 0.03), (sx * lx, sy * ly, (H_top - 0.03) / 2), STEEL_DARK,
                         finish_="plastic"),
                  _steel(f"Adjuster{n}", (0.05, 0.05, 0.01), (sx * lx, sy * ly, 0.005), RUBBER, finish_="matte")]
    for k, sy in enumerate((-1, 1)):  # apron rails under the top
        parts.append(_steel(f"Apron{k}", (2 * lx - leg, 0.02, 0.06), (0, sy * ly, H_top - 0.06), STEEL_DARK,
                            finish_="plastic"))
    riser_top, up_d = 1.30, 0.28
    yr = D / 2 - 0.02
    for k, x in enumerate((-lx, lx)):
        parts.append(_steel(f"RiserPost{k}", (leg, leg, riser_top - H_top), (x, yr, H_top + (riser_top - H_top) / 2),
                            STEEL_DARK, finish_="plastic"))
    parts += [_steel("UpperShelf", (2 * lx - leg, up_d, 0.02), (0, yr - leg / 2 - up_d / 2 + 0.02, riser_top - 0.01),
                     STEEL, finish_="plastic"),
              _p("Pegboard", "box", (2 * lx - leg, 0.01, 0.38), (0, yr + 0.005, H_top + 0.02 + 0.19), "#D8D4CC", "matte",
                 faces={"front": 1}, material="wood")]
    for p in parts:
        p.material = p.material or "steel"
    return Product(slug="inspection_table", name="検品台（棚付きの作業台）1500×750", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=55.0, static=True, material="steel",
                   description="形はバックヤードで納品物を検品・仕分けする一般的な作業台（天板 1500 × 750 mm・高さ 850 mm、下段の棚、"
                               "奥に有孔ボードと高さ 1300 mm の上棚）で、寸法・質量は代表値。天板（手前に目盛り）・下段・上棚は "
                               "商品を並べる棚板として使える。動かない物（static）。",
                   tags=["検品台", "作業台", "ワークテーブル", "検品", "仕分け", "棚付き", *LOGI_TAGS, "inspection table",
                         "work table", "workbench", "packing table"],
                   photos=[], colors=Colors(label_base="#B9CBB8"), images=imgs, parts=parts)


PRODUCTS = {f.__name__: f for f in (roll_cage_cart, roll_cage_cart_loaded, bread_tray, bread_tray_stack,
                                    folding_container, folding_container_stack, carton_box_s, carton_box_m,
                                    carton_box_l, hand_truck, pallet_jack, backyard_steel_rack, inspection_table)}
