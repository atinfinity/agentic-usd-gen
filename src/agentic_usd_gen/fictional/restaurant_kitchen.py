"""架空の商品のデザイン: 飲食店の業務用厨房機器。

products.py と同じく、実在のメーカー名・ロゴは使わず、形と寸法は同じ種類の機器の一般的な値にする。
正面は −Y（調理する人の側）。すべてステンレスの据え置き（static）。扉・フードは関節（Joint）で動く。
作業台・棚板は薄い水平の板にする（商品を並べるツールが棚板として見つけられるように）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .paint import Canvas
from .products import _face
from .store_more import _link, _rod

STEEL, STEEL_DARK, STEEL_LIGHT = "#C4C7CB", "#9EA2A8", "#D6D9DC"
CAST_IRON, BLACK, OIL = "#2B2B2D", "#1A1A1C", "#C99A2E"
KITCHEN_TAGS = ["厨房機器", "業務用", "ステンレス", "厨房", "飲食店", "kitchen", "restaurant kitchen",
                "commercial kitchen", "stainless steel"]


def _s(name, size, center, color=STEEL, faces=None, collision=True, rotation=None, finish="metal") -> Part:
    """ステンレスの板・箱。"""
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish=finish, faces=faces, collision=collision, material="steel")


def _c(name, size, center, color=STEEL, collision=True, rotation=None, finish="metal") -> Part:
    return Part(name=name, shape="cylinder", size=list(size), center=list(center),
                rotation=list(rotation or [0, 0, 0]), color=color, finish=finish, collision=collision,
                material="steel" if finish == "metal" else None)


def _legs(W: float, D: float, h: float, inset: float = 0.03, d: float = 0.04, n_x: int = 2) -> list[Part]:
    """丸パイプの脚とアジャスター（四隅、n_x=3 で前後の中央にも）。"""
    out = []
    xs = [-W / 2 + inset + d / 2 + k * (W - 2 * inset - d) / (n_x - 1) for k in range(n_x)]
    for i, x in enumerate(xs):
        for j, y in enumerate((-D / 2 + inset + d / 2, D / 2 - inset - d / 2)):
            out += [_c(f"Leg{i}{j}", (d, d, h - 0.02), (x, y, 0.02 + (h - 0.02) / 2)),
                    _c(f"Foot{i}{j}", (d + 0.01, d + 0.01, 0.02), (x, y, 0.01), STEEL_DARK)]
    return out


def _corners(p: Part) -> np.ndarray:
    """部品の外接箱の 8 隅（回転込み）。"""
    sx, sy, sz = (s / 2 for s in p.size)
    pts = np.array([[x, y, z] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)])
    rx, ry, rz = (math.radians(a) for a in (p.rotation or [0, 0, 0]))
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return pts @ (Rz @ Ry @ Rx).T + np.array(p.center)


def _fit(parts: list[Part], joints: list[Joint] = ()) -> Dimensions:
    """足元の中心を原点に寄せ（部品と関節を平行移動）、外寸の Dimensions を返す。"""
    pts = np.vstack([_corners(p) for p in parts])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for p in parts:
        p.center = [p.center[0] - cx, p.center[1] - cy, p.center[2]]
    for j in joints:
        j.anchor = [j.anchor[0] - cx, j.anchor[1] - cy, j.anchor[2]]
    return Dimensions(round(float(hi[2]), 4), round(float(hi[0] - lo[0]), 4), depth=round(float(hi[1] - lo[1]), 4))


def _panel(w_mm: float, h_mm: float, seed: int) -> Canvas:
    """ヘアラインのステンレスの地。"""
    c = Canvas(w_mm, h_mm, None, STEEL, seed)
    c.gradient(0, 0, w_mm, h_mm, "#D3D6D9", "#B4B8BD", horizontal=True)
    y = 2.0
    while y < h_mm:
        c.line([(0, y), (w_mm, y + c.rng.uniform(-0.6, 0.6))], "#C9CCD0" if c.rng.random() < 0.5 else "#BDC1C5",
               0.5)
        y += c.rng.uniform(2.0, 6.0)
    return c


def _louver(c: Canvas, x0: float, y0: float, x1: float, y1: float, step: float = 14.0) -> None:
    """機械室の吸気口（横長のスリット）。"""
    y = y0
    while y + step * 0.5 < y1:
        c.rect(x0, y, x1, y + step * 0.45, fill="#2A2C30", radius=step * 0.2)
        y += step


def _display(c: Canvas, x: float, y: float, value: str, label: str = "庫内温度") -> None:
    """デジタルの温度表示と操作ボタン（中心 x, y）。"""
    c.rect(x - 95, y - 32, x + 95, y + 32, fill="#202226", radius=6)
    c.rect(x - 85, y - 24, x + 15, y + 24, fill="#0B1A10")
    c.text(x - 35, y + 1, value, 30, "#5CFF8A", 900)
    c.text(x + 55, y - 14, label, 10, "#E0E3E6", 700)
    for k in range(3):
        c.ellipse(x + 24 + k * 22, y + 4, x + 40 + k * 22, y + 20, fill="#9EA4AA")


# ---------------------------------------------------------------- 縦型冷蔵庫


def kitchen_fridge_2door() -> Product:
    """業務用の縦型冷蔵庫（2 ドア、幅 750 mm）。上に機械室（吸気口・温度表示）、扉は上下 2 枚で右の蝶番で手前に開く。"""
    W, D, H = 0.75, 0.80, 1.95
    t, wall, base = 0.06, 0.05, 0.10  # 扉の厚さ・断熱の壁・脚の高さ
    mach = 0.15  # 機械室の高さ
    y0, y1 = -D / 2 + t, D / 2  # 箱の前・後ろ
    z_top = H - mach  # 庫内の上の板の上面
    hdr = _panel(W * 1000, mach * 1000, 7201)
    _louver(hdr, 30, 25, 430, 130)
    _display(hdr, 600, 75, "3.0℃")
    images = [_face(hdr.array(), "metal", 7201, 0.5, 4)]
    zc = base + (z_top - base) / 2
    parts: list[Part] = _legs(W, D - t, base, inset=0.02)
    for p in parts:
        p.center[1] += t / 2
    parts += [
        _s("Kick", (W - 0.02, 0.01, base), (0, y0 + 0.03, base / 2), STEEL_DARK, collision=False),
        _s("SideL", (wall, y1 - y0, z_top - base), (-W / 2 + wall / 2, (y0 + y1) / 2, zc)),
        _s("SideR", (wall, y1 - y0, z_top - base), (W / 2 - wall / 2, (y0 + y1) / 2, zc)),
        _s("Back", (W - 2 * wall, wall, z_top - base), (0, y1 - wall / 2, zc)),
        _s("Bottom", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, base + wall / 2)),
        _s("Ceiling", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, z_top - wall / 2)),
        _s("Machine", (W, D, mach), (0, 0, z_top + mach / 2)),
        _s("MachineFront", (W, 0.004, mach - 0.004), (0, -D / 2 - 0.002, z_top + mach / 2), faces={"front": 0},
           collision=False),
    ]
    zm = base + (z_top - base) / 2  # 上下の庫内の仕切り
    parts.append(_s("Divider", (W - 2 * wall, y1 - y0 - wall, 0.04), (0, (y0 + y1 - wall) / 2, zm)))
    for k, (za, zb) in enumerate(((base + wall, zm - 0.02), (zm + 0.02, z_top - wall))):  # 庫内の網棚（各室 1 枚）
        parts.append(_s(f"Shelf{k}", (W - 2 * wall - 0.01, y1 - y0 - wall - 0.04, 0.012),
                        (0, (y0 + y1 - wall) / 2, (za + zb) / 2), STEEL_LIGHT))
    joints = []
    dw, yd = W - 0.006, -D / 2 + t / 2
    for name, za, zb in (("LowerDoor", base + 0.003, zm - 0.002), ("UpperDoor", zm + 0.002, z_top - 0.003)):
        dh, dz = zb - za, (za + zb) / 2
        hx = -dw / 2 + 0.05
        parts += [
            _s(f"{name}Panel", (dw, t, dh), (0, yd, dz)),
            _s(f"{name}Gasket", (dw - 0.04, 0.006, dh - 0.04), (0, -D / 2 + t + 0.003, dz), "#3A3C40",
               collision=False, finish="plastic"),
            _c(f"{name}Grip", (0.026, 0.026, 0.36), (hx, -D / 2 - 0.04, dz)),
            _s(f"{name}GripPostT", (0.02, 0.04, 0.02), (hx, -D / 2 - 0.02, dz + 0.15), collision=False),
            _s(f"{name}GripPostB", (0.02, 0.04, 0.02), (hx, -D / 2 - 0.02, dz - 0.15), collision=False),
        ]
        _link(parts, name, f"{name}Link")
        joints.append(Joint(link=f"{name}Link", anchor=[dw / 2, -D / 2, dz], limits=[0.0, 100.0]))
    dims = _fit(parts, joints)
    return Product(slug="kitchen_fridge_2door", name="業務用縦型冷蔵庫（2ドア・幅 750 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=110.0, static=True, material="steel",
                   description="形は飲食店の厨房に置く一般的な業務用の縦型冷蔵庫（幅 750 mm・奥行き 800 mm・高さ 1950 mm、"
                               "上に高さ 150 mm の機械室と温度表示、庫内は上下 2 室で各 1 枚の網棚、扉は上下 2 枚）で、寸法・質量は代表値。"
                               "扉（UpperDoorLink・LowerDoorLink）は右端の蝶番で手前に 100° まで開く。",
                   tags=["業務用冷蔵庫", "縦型冷蔵庫", "冷蔵庫", "2ドア", *KITCHEN_TAGS, "commercial refrigerator",
                         "reach-in refrigerator", "upright fridge", "fridge"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts, joints=joints)


# ---------------------------------------------------------------- コールドテーブル


def cold_table() -> Product:
    """コールドテーブル（台下冷蔵庫、幅 1500 mm）。天板は作業台、左に機械室、右に両開きの扉 2 枚。"""
    W, D, H = 1.50, 0.60, 0.80
    t, wall, base, top_t = 0.04, 0.04, 0.12, 0.04
    y0, y1 = -D / 2 + t, D / 2
    zb, zt = base, H - top_t  # 箱の下・上
    zc = (zb + zt) / 2
    xm = -W / 2 + 0.40  # 機械室と庫内の境
    mw = xm + W / 2
    front = _panel(mw * 1000 - 10, (zt - zb) * 1000 - 10, 7211)
    _louver(front, 40, 260, mw * 1000 - 50, 600)
    _display(front, (mw * 1000 - 10) / 2, 140, "5.0℃")
    images = [_face(front.array(), "metal", 7211, 0.5, 4)]
    parts: list[Part] = _legs(W, D - t, base, inset=0.03, n_x=3)
    for p in parts:
        p.center[1] += t / 2
    parts += [
        _s("Top", (W, D, top_t), (0, 0, H - top_t / 2)),
        _s("TopLip", (W, 0.004, top_t + 0.01), (0, -D / 2 - 0.002, H - (top_t + 0.01) / 2), collision=False),
        _s("SideL", (wall, y1 - y0, zt - zb), (-W / 2 + wall / 2, (y0 + y1) / 2, zc)),
        _s("SideR", (wall, y1 - y0, zt - zb), (W / 2 - wall / 2, (y0 + y1) / 2, zc)),
        _s("Back", (W - 2 * wall, wall, zt - zb), (0, y1 - wall / 2, zc)),
        _s("Bottom", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, zb + wall / 2)),
        _s("Partition", (wall, y1 - y0 - wall, zt - zb - wall), (xm + wall / 2, (y0 + y1 - wall) / 2,
                                                                 zc + wall / 2)),
        _s("MachineFront", (mw - 0.004, t, zt - zb - 0.004), (-W / 2 + mw / 2, -D / 2 + t / 2, zc),
           faces={"front": 0}),
    ]
    xa, xb = xm + wall, W / 2 - wall  # 庫内
    parts.append(_s("Shelf", (xb - xa - 0.01, y1 - y0 - wall - 0.04, 0.012),
                    ((xa + xb) / 2, (y0 + y1 - wall) / 2, zb + (zt - zb) * 0.55), STEEL_LIGHT))
    joints = []
    span = W / 2 - xm
    dw = span / 2 - 0.004
    yd = -D / 2 + t / 2
    for k, name in enumerate(("DoorL", "DoorR")):
        x = xm + span / 4 + k * span / 2
        hx = x + (dw / 2 - 0.05) * (1 if k == 0 else -1)  # 取っ手は扉の合わせ目の側
        dh = zt - zb - 0.006
        parts += [
            _s(f"{name}Panel", (dw, t, dh), (x, yd, zc)),
            _s(f"{name}Grip", (0.02, 0.03, 0.18), (hx, -D / 2 - 0.015, zc + 0.12)),
        ]
        _link(parts, name, f"{name}Link")
        if k == 0:  # 左の扉は左端の蝶番、右の扉は右端の蝶番で手前に開く
            joints.append(Joint(link="DoorLLink", anchor=[x - dw / 2, -D / 2, zc], limits=[-100.0, 0.0]))
        else:
            joints.append(Joint(link="DoorRLink", anchor=[x + dw / 2, -D / 2, zc], limits=[0.0, 100.0]))
    dims = _fit(parts, joints)
    return Product(slug="cold_table", name="コールドテーブル（台下冷蔵庫・幅 1500 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=85.0, static=True, material="steel",
                   description="形は飲食店の厨房の一般的なコールドテーブル（台下冷蔵庫、幅 1500 mm・奥行き 600 mm・高さ 800 mm、"
                               "天板は厚さ 40 mm のステンレスの作業台、左に幅 400 mm の機械室と温度表示、庫内に網棚 1 枚）で、"
                               "寸法・質量は代表値。扉（DoorLLink・DoorRLink）は外側の蝶番で手前に 100° まで開く。",
                   tags=["コールドテーブル", "台下冷蔵庫", "冷蔵庫", "作業台", *KITCHEN_TAGS,
                         "refrigerated work table", "undercounter refrigerator", "cold table", "prep table"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts, joints=joints)


# ---------------------------------------------------------------- ガスレンジ


def _range_rail(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    c = _panel(w_mm, h_mm, seed)
    for k in range(5):
        x = w_mm * (0.1 + 0.2 * k)
        c.text(x, 14, ("左奥", "左前", "オーブン", "右前", "右奥")[k], 9, "#33373C", 800)
        for a in range(0, 181, 45):
            r = math.radians(180 + a)
            c.line([(x + 30 * math.cos(r), 62 + 30 * math.sin(r)), (x + 36 * math.cos(r), 62 + 36 * math.sin(r))],
                   "#B0242A" if a == 180 else "#33373C", 1.4)
    c.text(w_mm - 70, h_mm - 12, "都市ガス 13A", 8, "#55595F", 700)
    return _face(c.array(), "metal", seed, 0.5, 4)


def gas_range() -> Product:
    """業務用ガスレンジ（4 口・オーブン付き、幅 900 mm）。鋳物の五徳、下のオーブンの扉は下の蝶番で手前に倒れる。"""
    W, D, H = 0.90, 0.75, 0.80
    base, deck_t, rail_h = 0.15, 0.02, 0.10
    bg_h, bg_t = 0.10, 0.03  # 奥のバックガード
    zt = H  # 天板の上面
    wall = 0.02
    zb = base
    zc = (zb + zt - deck_t) / 2
    images = [_range_rail(W * 1000, rail_h * 1000, 7221)]
    parts: list[Part] = _legs(W, D, base, inset=0.03)
    parts += [
        _s("Deck", (W, D, deck_t), (0, 0, zt - deck_t / 2), STEEL_DARK),
        _s("SideL", (wall, D, zt - deck_t - zb), (-W / 2 + wall / 2, 0, zc)),
        _s("SideR", (wall, D, zt - deck_t - zb), (W / 2 - wall / 2, 0, zc)),
        _s("Back", (W - 2 * wall, wall, zt - deck_t - zb), (0, D / 2 - wall / 2, zc)),
        _s("Bottom", (W - 2 * wall, D - wall, wall), (0, -wall / 2, zb + wall / 2)),
        _s("Rail", (W, 0.03, rail_h), (0, -D / 2 + 0.015, zt - deck_t - rail_h / 2), faces={"front": 0}),
        _s("OvenTop", (W - 2 * wall, D - wall - 0.03, wall), (0, 0.0, zt - deck_t - rail_h - wall / 2)),
        _s("OvenRack", (W - 2 * wall - 0.02, D - wall - 0.08, 0.01), (0, 0.01, zb + 0.24), STEEL_LIGHT),
        _s("Backguard", (W, bg_t, bg_h), (0, D / 2 - bg_t / 2, zt + bg_h / 2)),
    ]
    for k in range(5):  # 操作つまみ
        x = -W / 2 + W * (0.1 + 0.2 * k)
        parts.append(_c(f"Knob{k}", (0.05, 0.05, 0.03), (x, -D / 2 - 0.015, zt - deck_t - rail_h * 0.38), BLACK,
                        rotation=[90, 0, 0], finish="plastic"))
    # バーナーと五徳（鋳物の四角い枠に 4 本の爪）
    ty = 0.30
    for i, (x, y) in enumerate(((-0.22, -0.16), (-0.22, 0.17), (0.22, -0.16), (0.22, 0.17))):
        parts += [
            _c(f"Burner{i}Ring", (0.22, 0.22, 0.008), (x, y, zt + 0.004), "#3A3C40"),
            _c(f"Burner{i}Head", (0.12, 0.12, 0.035), (x, y, zt + 0.0175), CAST_IRON),
            _c(f"Burner{i}Cap", (0.075, 0.075, 0.012), (x, y, zt + 0.041), "#4A4A4C"),
        ]
        bar, gz = 0.022, zt + 0.06
        h = ty / 2
        parts += [
            _s(f"Trivet{i}F", (ty, bar, bar), (x, y - h + bar / 2, gz - bar / 2), CAST_IRON, finish="matte"),
            _s(f"Trivet{i}B", (ty, bar, bar), (x, y + h - bar / 2, gz - bar / 2), CAST_IRON, finish="matte"),
            _s(f"Trivet{i}L", (bar, ty - 2 * bar, bar), (x - h + bar / 2, y, gz - bar / 2), CAST_IRON, finish="matte"),
            _s(f"Trivet{i}R", (bar, ty - 2 * bar, bar), (x + h - bar / 2, y, gz - bar / 2), CAST_IRON, finish="matte"),
        ]
        for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            parts.append(_s(f"Trivet{i}Leg{k}", (bar, bar, gz - bar - zt),
                            (x + sx * (h - bar / 2), y + sy * (h - bar / 2), zt + (gz - bar - zt) / 2), CAST_IRON,
                            collision=False, finish="matte"))
        fl = 0.075  # 爪（鍋を載せる）
        for k, (dx, dy, sx, sy) in enumerate(((0, -1, bar, fl), (0, 1, bar, fl), (-1, 0, fl, bar), (1, 0, fl, bar))):
            parts.append(_s(f"Trivet{i}Finger{k}", (sx, sy, bar * 0.8),
                            (x + dx * (h - bar - fl / 2), y + dy * (h - bar - fl / 2), gz - bar * 0.4), CAST_IRON,
                            finish="matte"))
    # オーブンの扉（下端の蝶番で手前に倒れる）
    dz0, dz1 = zb + 0.01, zt - deck_t - rail_h - 0.005
    dzc, dh = (dz0 + dz1) / 2, dz1 - dz0
    yd = -D / 2 - 0.012
    parts += [
        _s("OvenDoorPanel", (W - 0.04, 0.024, dh), (0, yd, dzc)),
        Part("OvenDoorWindow", "box", [0.40, 0.006, 0.16], [0, yd - 0.013, dzc + 0.03], color="#1C2226",
             finish="glass", collision=False, material="glass", bevel=0),
        _rod("OvenDoorGrip", (-0.30, yd - 0.05, dz1 - 0.05), (0.30, yd - 0.05, dz1 - 0.05), 0.024, STEEL_LIGHT),
        _s("OvenDoorGripPostL", (0.02, 0.04, 0.02), (-0.28, yd - 0.03, dz1 - 0.05), collision=False),
        _s("OvenDoorGripPostR", (0.02, 0.04, 0.02), (0.28, yd - 0.03, dz1 - 0.05), collision=False),
    ]
    _link(parts, "OvenDoor", "OvenDoorLink")
    joints = [Joint(link="OvenDoorLink", anchor=[0, -D / 2 - 0.024, dz0], limits=[0.0, 85.0], axis="X")]
    dims = _fit(parts, joints)
    return Product(slug="gas_range", name="業務用ガスレンジ（4口・オーブン付き 900 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=130.0, static=True, material="steel",
                   description="形は飲食店の厨房の一般的な業務用ガスレンジ（幅 900 mm・奥行き 750 mm・天板の高さ 800 mm、"
                               "バーナー 4 口に鋳物の五徳、奥に高さ 100 mm のバックガード、下にオーブン）で、寸法・質量は代表値。"
                               "オーブンの扉（OvenDoorLink）は下端の蝶番で手前に 85° まで倒れる。",
                   tags=["ガスレンジ", "ガスコンロ", "コンロ", "オーブン", "五徳", *KITCHEN_TAGS, "gas range",
                         "commercial range", "stove", "oven", "burner"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts, joints=joints)


# ---------------------------------------------------------------- フライヤー


def floor_fryer() -> Product:
    """床置きのガスフライヤー（1 槽・かご 2 つ、幅 450 mm）。奥に排気筒、下は扉付きの収納。"""
    W, D, H = 0.45, 0.60, 0.80
    base, wall = 0.12, 0.015
    zt = H
    ow, od, oy = 0.34, 0.38, -0.02  # 油槽の開口
    tank_floor, oil_top = 0.50, 0.70
    flue_h, flue_d = 0.15, 0.10
    c = _panel(W * 1000 - 10, (zt - 0.02 - base) * 1000 - 20, 7231)
    c.rect(40, 30, c.w_mm - 40, 130, fill="#2A2C30", radius=6)
    c.ellipse(c.w_mm / 2 - 40, 40, c.w_mm / 2 + 40, 120, fill="#E4E6E8")
    c.text(c.w_mm / 2, 145, "160 — 200℃", 12, "#33373C", 800)
    c.text(c.w_mm / 2, 200, "高温注意", 26, "#B0242A", 900)
    c.text(c.w_mm / 2, 236, "油に水を入れないでください", 12, "#B0242A", 800)
    c.rect(c.w_mm - 60, 300, c.w_mm - 40, 420, fill="#9EA4AA", radius=4)  # 扉の取っ手
    images = [_face(c.array(), "metal", 7231, 0.5, 4)]
    zc = (base + zt - 0.02) / 2
    parts: list[Part] = _legs(W, D, base, inset=0.02)
    parts += [
        _s("SideL", (wall, D, zt - base), (-W / 2 + wall / 2, 0, base + (zt - base) / 2)),
        _s("SideR", (wall, D, zt - base), (W / 2 - wall / 2, 0, base + (zt - base) / 2)),
        _s("Back", (W - 2 * wall, wall, zt - base), (0, D / 2 - wall / 2, base + (zt - base) / 2)),
        _s("Bottom", (W - 2 * wall, D - wall, wall), (0, -wall / 2, base + wall / 2)),
        _s("Front", (W, 0.01, zt - 0.02 - base - 0.02), (0, -D / 2 + 0.005, zc), faces={"front": 0}),
    ]
    y0, y1 = oy - od / 2, oy + od / 2
    dz = zt - 0.01
    xe = ow / 2
    parts += [
        _s("DeckFront", (W, y0 + D / 2, 0.02), (0, (-D / 2 + y0) / 2, dz)),
        _s("DeckBack", (W, D / 2 - flue_d - y1, 0.02), (0, (y1 + D / 2 - flue_d) / 2, dz)),
        _s("DeckLeft", (W / 2 - xe, od, 0.02), (-(W / 2 + xe) / 2, oy, dz)),
        _s("DeckRight", (W / 2 - xe, od, 0.02), ((W / 2 + xe) / 2, oy, dz)),
        _s("Flue", (W, flue_d, flue_h), (0, D / 2 - flue_d / 2, zt + flue_h / 2 - 0.02)),
        _s("FlueGrille", (W - 0.04, flue_d - 0.03, 0.004), (0, D / 2 - flue_d / 2, zt + flue_h - 0.018), "#3A3C40",
           collision=False),
    ]
    wh = zt - 0.02 - tank_floor
    wz = tank_floor + wh / 2
    parts += [
        _s("TankFloor", (ow, od, 0.006), (0, oy, tank_floor), STEEL_DARK),
        _s("TankWallF", (ow, 0.004, wh), (0, y0 + 0.002, wz), STEEL_DARK),
        _s("TankWallB", (ow, 0.004, wh), (0, y1 - 0.002, wz), STEEL_DARK),
        _s("TankWallL", (0.004, od, wh), (-ow / 2 + 0.002, oy, wz), STEEL_DARK),
        _s("TankWallR", (0.004, od, wh), (ow / 2 - 0.002, oy, wz), STEEL_DARK),
    ]
    oil = _s("Oil", (ow - 0.01, od - 0.01, oil_top - tank_floor - 0.003), (0, oy, (tank_floor + 0.003 + oil_top) / 2),
             OIL, collision=False, finish="glossy")
    oil.material = "liquid"
    parts.append(oil)
    bw, bd, bh, bz0 = 0.155, 0.30, 0.13, oil_top - 0.07  # かご（下半分が油につかる）
    a, L, Lg = math.radians(30), 0.20, 0.11
    for i, x in enumerate((-0.083, 0.083)):
        bzc = bz0 + bh / 2
        for nm, size, cen in (("Floor", (bw, bd, 0.004), (x, oy, bz0)),
                              ("WallF", (bw, 0.003, bh), (x, oy - bd / 2, bzc)),
                              ("WallB", (bw, 0.003, bh), (x, oy + bd / 2, bzc)),
                              ("WallL", (0.003, bd, bh), (x - bw / 2, oy, bzc)),
                              ("WallR", (0.003, bd, bh), (x + bw / 2, oy, bzc))):
            parts.append(_s(f"Basket{i}{nm}", size, cen, "#8A8E94", collision=False))
        p0 = (x, oy - bd / 2, bz0 + bh)
        pg = (x, p0[1] - (L - Lg) * math.cos(a), p0[2] + (L - Lg) * math.sin(a))
        p1 = (x, p0[1] - L * math.cos(a), p0[2] + L * math.sin(a))
        parts += [_rod(f"Basket{i}Handle", p0, pg, 0.008, STEEL_LIGHT),
                  _rod(f"Basket{i}Grip", pg, p1, 0.024, BLACK, "plastic", collision=True)]
    parts += [_c("Knob", (0.045, 0.045, 0.025), (0, -D / 2 - 0.012, base + (zt - base) * 0.86), BLACK,
                 rotation=[90, 0, 0], finish="plastic"),
              _c("Pilot", (0.012, 0.012, 0.006), (0.08, -D / 2 - 0.003, base + (zt - base) * 0.86), "#FF7A2A",
                 collision=False, rotation=[90, 0, 0], finish="light")]
    dims = _fit(parts)
    return Product(slug="floor_fryer", name="業務用フライヤー（床置き・1槽 450 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=70.0, static=True, material="steel",
                   description="形は飲食店の厨房の一般的な床置きのガスフライヤー（幅 450 mm・奥行き 600 mm・天板の高さ 800 mm、"
                               "油槽 1 つにかご 2 つ、奥に高さ 150 mm の排気筒、下は収納）で、寸法・質量は代表値。卓上の counter_fryer と別物。",
                   tags=["フライヤー", "揚げ物", "床置きフライヤー", *KITCHEN_TAGS, "deep fryer", "floor fryer",
                         "commercial fryer", "fryer"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts)


# ---------------------------------------------------------------- 2 槽シンク


def sink_2bowl() -> Product:
    """業務用の 2 槽シンク（幅 1200 mm）。バックガード付き、槽ごとに台付きの水栓。脚は丸パイプ。"""
    W, D, H = 1.20, 0.60, 0.80
    bg_h, bg_t = 0.15, 0.04
    deck_t = 0.02
    bw, bd, depth = 0.50, 0.45, 0.30
    by = -0.025  # 槽の中心の Y
    bxs = (-0.285, 0.285)
    zt = H
    zf = zt - depth  # 槽の底
    parts: list[Part] = _legs(W, D, zt - deck_t, inset=0.03)
    for i in range(2):  # 脚の横の桟
        x = -W / 2 + 0.05 + i * (W - 0.10)
        parts.append(_s(f"StretcherY{i}", (0.03, D - 0.10, 0.03), (x, 0, 0.15), collision=False))
    parts.append(_s("StretcherX", (W - 0.10, 0.03, 0.03), (0, D / 2 - 0.05, 0.15), collision=False))
    y0, y1 = by - bd / 2, by + bd / 2
    dz = zt - deck_t / 2
    xe = bxs[1] + bw / 2
    xi = bxs[1] - bw / 2
    parts += [
        _s("DeckFront", (W, y0 + D / 2, deck_t), (0, (-D / 2 + y0) / 2, dz)),
        _s("DeckBack", (W, D / 2 - bg_t - y1, deck_t), (0, (y1 + D / 2 - bg_t) / 2, dz)),
        _s("DeckLeft", (W / 2 - xe, bd, deck_t), (-(W / 2 + xe) / 2, by, dz)),
        _s("DeckMid", (2 * xi, bd, deck_t), (0, by, dz)),
        _s("DeckRight", (W / 2 - xe, bd, deck_t), ((W / 2 + xe) / 2, by, dz)),
        _s("FrontLip", (W, 0.01, 0.05), (0, -D / 2 + 0.005, zt - 0.025), collision=False),
        _s("Backguard", (W, bg_t, bg_h), (0, D / 2 - bg_t / 2, zt + bg_h / 2)),
    ]
    wh = depth - deck_t
    wz = zf + wh / 2
    for i, x in enumerate(bxs):
        parts += [
            _s(f"Bowl{i}Floor", (bw, bd, 0.01), (x, by, zf), STEEL_LIGHT),
            _s(f"Bowl{i}WallF", (bw, 0.01, wh), (x, y0 + 0.005, wz)),
            _s(f"Bowl{i}WallB", (bw, 0.01, wh), (x, y1 - 0.005, wz)),
            _s(f"Bowl{i}WallL", (0.01, bd, wh), (x - bw / 2 + 0.005, by, wz)),
            _s(f"Bowl{i}WallR", (0.01, bd, wh), (x + bw / 2 - 0.005, by, wz)),
            _c(f"Bowl{i}Drain", (0.08, 0.08, 0.004), (x, by + 0.12, zf + 0.007), "#5A5E64", collision=False),
        ]
        # 台付きの水栓（首が立ち上がり、吐水口が槽の中央へ）
        fy, fz = (y1 + D / 2 - bg_t) / 2, zt + 0.28
        sy = by + 0.02
        parts += [
            _c(f"Faucet{i}Base", (0.05, 0.05, 0.03), (x, fy, zt + 0.015)),
            _rod(f"Faucet{i}Riser", (x, fy, zt + 0.03), (x, fy, fz), 0.022, STEEL_LIGHT),
            _rod(f"Faucet{i}Spout", (x, fy, fz), (x, sy, fz), 0.02, STEEL_LIGHT),
            _rod(f"Faucet{i}Tip", (x, sy, fz), (x, sy, fz - 0.05), 0.018, STEEL_LIGHT),
            _rod(f"Faucet{i}Lever", (x - 0.12, fy, zt + 0.08), (x + 0.12, fy, zt + 0.08), 0.014, STEEL_LIGHT),
            _c(f"Faucet{i}Body", (0.04, 0.04, 0.06), (x, fy, zt + 0.08), STEEL_LIGHT),
        ]
    dims = _fit(parts)
    return Product(slug="sink_2bowl", name="業務用 2 槽シンク（バックガード付き 1200 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=28.0, static=True, material="steel",
                   description="形は飲食店の厨房の一般的なステンレスの 2 槽シンク（幅 1200 mm・奥行き 600 mm・高さ 800 mm、"
                               "槽は 500 × 450 mm・深さ 300 mm が 2 つ、奥に高さ 150 mm のバックガード、槽ごとに台付きの水栓、"
                               "丸パイプの脚に桟）で、寸法・質量は代表値。",
                   tags=["シンク", "2槽シンク", "流し台", "洗い場", "水栓", *KITCHEN_TAGS, "commercial sink",
                         "two compartment sink", "kitchen sink", "sink"],
                   photos=[], colors=Colors(label_base=STEEL), images=[], parts=parts)


# ---------------------------------------------------------------- 作業台


def work_table_steel() -> Product:
    """ステンレスの作業台（幅 1200 mm、バックガード・下棚付き）。"""
    W, D, H = 1.20, 0.60, 0.80
    top_t, bg_h, bg_t = 0.04, 0.10, 0.025
    parts: list[Part] = []
    leg = 0.04
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, y = sx * (W / 2 - 0.03 - leg / 2), sy * (D / 2 - 0.03 - leg / 2)
        parts += [_s(f"Leg{i}", (leg, leg, H - top_t - 0.02), (x, y, 0.02 + (H - top_t - 0.02) / 2)),
                  _c(f"Foot{i}", (leg + 0.01, leg + 0.01, 0.02), (x, y, 0.01), STEEL_DARK)]
    parts += [
        _s("Top", (W, D, top_t), (0, 0, H - top_t / 2)),
        _s("Backguard", (W, bg_t, bg_h), (0, D / 2 - bg_t / 2, H + bg_h / 2)),
        _s("UnderShelf", (W - 0.06, D - 0.06, 0.025), (0, 0, 0.20)),
    ]
    dims = _fit(parts)
    return Product(slug="work_table_steel", name="ステンレス作業台（バックガード・下棚付き 1200 mm）",
                   shape_class="assembly", category="fixture", dims=dims, mass_kg=22.0, static=True, material="steel",
                   description="形は飲食店の厨房の一般的なステンレスの作業台（幅 1200 mm・奥行き 600 mm・天板の高さ 800 mm、"
                               "奥に高さ 100 mm のバックガード、高さ 200 mm に下棚、角パイプの 4 本脚）で、寸法・質量は代表値。",
                   tags=["作業台", "調理台", "ステンレス台", *KITCHEN_TAGS, "work table", "prep table",
                         "stainless steel table", "kitchen table"],
                   photos=[], colors=Colors(label_base=STEEL), images=[], parts=parts)


# ---------------------------------------------------------------- 食器洗浄機


def _dishwasher_panel(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    c = _panel(w_mm, h_mm, seed)
    c.rect(60, 40, w_mm - 60, 170, fill="#2A2C30", radius=8)
    for k, (lab, val) in enumerate((("洗浄", "60℃"), ("すすぎ", "85℃"))):
        x = 150 + k * 220
        c.rect(x - 80, 60, x + 80, 120, fill="#0B1A10")
        c.text(x, 91, val, 26, "#FFB74D", 900)
        c.text(x, 145, lab, 14, "#E0E3E6", 800)
    for k, col in enumerate(("#4CAF50", "#2196F3", "#B0242A")):
        c.ellipse(w_mm - 170 + k * 40 - 14, 90, w_mm - 170 + k * 40 + 14, 118, fill=col)
    c.text(w_mm / 2, 230, "フードを下ろすと洗浄が始まります", 16, "#33373C", 800)
    c.text(w_mm / 2, h_mm - 40, "DISHWASHER", 22, "#7A7E84", 900, spacing=6)
    return _face(c.array(), "metal", seed, 0.5, 4)


def dishwasher_door() -> Product:
    """ドアタイプの業務用食器洗浄機（本体のみ）。洗浄室を覆うフードが上下にスライドする。"""
    W, D, H = 0.64, 0.65, 1.45
    base, zb = 0.10, 0.85  # 脚・洗浄室の床（ラックを載せる高さ）
    hood_h, lift = 0.45, 0.40
    tower_d = 0.05
    images = [_dishwasher_panel(W * 1000, (zb - base) * 1000 - 20, 7261)]
    parts: list[Part] = _legs(W, D, base, inset=0.03)
    parts += [
        _s("Body", (W, D, zb - base), (0, 0, base + (zb - base) / 2)),
        _s("BodyFront", (W, 0.004, zb - base - 0.02), (0, -D / 2 - 0.002, base + (zb - base) / 2),
           faces={"front": 0}, collision=False),
        _s("Tower", (W, tower_d, H - zb), (0, D / 2 - tower_d / 2, zb + (H - zb) / 2)),
        _s("TowerCap", (W, tower_d + 0.02, 0.02), (0, D / 2 - (tower_d + 0.02) / 2, H - 0.01), STEEL_DARK,
           collision=False),
    ]
    for k, x in enumerate((-0.26, 0.26)):  # ラックのレール
        parts.append(_s(f"RackRail{k}", (0.02, D - tower_d - 0.04, 0.02), (x, -tower_d / 2, zb + 0.01), STEEL_DARK))
    parts += [_s("WashArm", (0.50, 0.04, 0.012), (0, -tower_d / 2, zb + 0.008), STEEL_DARK, collision=False),
              _c("WashArmHub", (0.05, 0.05, 0.015), (0, -tower_d / 2, zb + 0.008), STEEL_DARK, collision=False),
              _s("RinseBar", (0.50, 0.03, 0.02), (0, D / 2 - tower_d - 0.02, zb + hood_h - 0.06), STEEL_DARK,
                 collision=False)]
    # フード（前・左右・天井の 4 面、前に取っ手）。上へ 400 mm スライドする
    hz0 = zb + 0.01
    hy0, hy1 = -D / 2, D / 2 - tower_d - 0.005
    hzc = hz0 + hood_h / 2
    hyc = (hy0 + hy1) / 2
    tw = 0.015
    parts += [
        _s("HoodFront", (W, tw, hood_h), (0, hy0 + tw / 2, hzc)),
        _s("HoodLeft", (tw, hy1 - hy0, hood_h), (-W / 2 + tw / 2, hyc, hzc)),
        _s("HoodRight", (tw, hy1 - hy0, hood_h), (W / 2 - tw / 2, hyc, hzc)),
        _s("HoodTop", (W, hy1 - hy0, tw), (0, hyc, hz0 + hood_h - tw / 2)),
        _rod("HoodGrip", (-0.24, hy0 - 0.04, hz0 + hood_h * 0.7), (0.24, hy0 - 0.04, hz0 + hood_h * 0.7), 0.025,
             STEEL_LIGHT, collision=True),
        _s("HoodGripPostL", (0.02, 0.04, 0.02), (-0.22, hy0 - 0.02, hz0 + hood_h * 0.7), collision=False),
        _s("HoodGripPostR", (0.02, 0.04, 0.02), (0.22, hy0 - 0.02, hz0 + hood_h * 0.7), collision=False),
    ]
    _link(parts, "Hood", "HoodLink")
    joints = [Joint(link="HoodLink", anchor=[0, hyc, hzc], limits=[0.0, lift], type="prismatic", axis="Z")]
    dims = _fit(parts, joints)
    return Product(slug="dishwasher_door", name="業務用食器洗浄機（ドアタイプ）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=85.0, static=True, material="steel",
                   description="形は飲食店の洗い場の一般的なドアタイプの食器洗浄機の本体（幅 640 mm・奥行き 650 mm・高さ 1450 mm、"
                               "ラックを載せる洗浄室の床の高さ 850 mm、洗浄室を前・左右・上から覆う高さ 450 mm のフード、"
                               "下の正面に操作盤）で、寸法・質量は代表値。両側の作業台・ラックは含まない。"
                               "フード（HoodLink）は 400 mm まで上にスライドして開く。",
                   tags=["食器洗浄機", "食洗機", "洗い場", "ドアタイプ", *KITCHEN_TAGS, "commercial dishwasher",
                         "door type dishwasher", "hood type dishwasher", "dishwasher"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts, joints=joints)


# ---------------------------------------------------------------- ワイヤーシェルフ


def _wire(w_mm: float, d_mm: float, seed: int) -> np.ndarray:
    """ワイヤーの網棚（隙間は濃い灰色）。"""
    c = Canvas(w_mm, d_mm, None, "#4A4D52", seed)
    c.gradient(0, 0, w_mm, d_mm, "#55585D", "#3E4146")
    x = 0.0
    while x <= w_mm:
        c.line([(x, 0), (x, d_mm)], STEEL_LIGHT, 4.0)
        x += 25.0
    for y in (6, d_mm / 3, 2 * d_mm / 3, d_mm - 6):
        c.line([(0, y), (w_mm, y)], STEEL, 6.0)
    return _face(c.array(), "metal", seed, 0.4, 2)


def kitchen_rack() -> Product:
    """ステンレスのワイヤーシェルフ（4 段、幅 1200 mm・奥行き 450 mm・高さ 1800 mm）。"""
    W, D, H = 1.20, 0.45, 1.80
    post = 0.025
    images = [_wire(1170, 420, 7271)]
    parts: list[Part] = []
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        parts.append(_c(f"Post{i}", (post, post, H), (sx * (W / 2 - post / 2), sy * (D / 2 - post / 2), H / 2),
                        STEEL_LIGHT))
    for k, z in enumerate((0.15, 0.68, 1.21, 1.74)):
        parts += [
            _s(f"Shelf{k}", (W - 0.03, D - 0.03, 0.02), (0, 0, z), STEEL_LIGHT, faces={"top": 0, "bottom": 0}),
            _rod(f"Shelf{k}RimF", (-W / 2 + 0.02, -D / 2 + 0.015, z + 0.012), (W / 2 - 0.02, -D / 2 + 0.015, z + 0.012),
                 0.008, STEEL_LIGHT),
            _rod(f"Shelf{k}RimB", (-W / 2 + 0.02, D / 2 - 0.015, z + 0.012), (W / 2 - 0.02, D / 2 - 0.015, z + 0.012),
                 0.008, STEEL_LIGHT),
        ]
    dims = _fit(parts)
    return Product(slug="kitchen_rack", name="ステンレスのワイヤーシェルフ（4段 1200 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=20.0, static=True, material="steel",
                   description="形は飲食店の厨房・倉庫の一般的なステンレスのワイヤーシェルフ（幅 1200 mm・奥行き 450 mm・高さ 1800 mm、"
                               "4 本の支柱に網棚 4 段）で、寸法・質量は代表値。網棚は 1 枚の薄い板で表す。",
                   tags=["ワイヤーシェルフ", "ラック", "棚", "厨房ラック", *KITCHEN_TAGS, "wire shelving",
                         "kitchen rack", "storage rack", "shelf"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts)


# ---------------------------------------------------------------- 排気フード


def exhaust_hood() -> Product:
    """壁付けの排気フード（幅 1800 mm・奥行き 900 mm・高さ 600 mm）。上面を天井、背面（+Y）を壁に付ける。

    下は開いていて、奥にグリスフィルター、前の下端に油受けの樋。
    """
    W, D, H = 1.80, 0.90, 0.60
    t = 0.012
    skirt = 0.30  # 前の垂直な面の高さ
    ys = -0.20  # 前の斜めの面の上端の Y
    rise = H - t - skirt  # 斜めの面は天板の下で止める（板の厚さで外寸の上に出ないように）
    slant = math.hypot(ys + D / 2, rise)
    tilt = -math.degrees(math.atan2(ys + D / 2, rise))
    side_profile = [[-0.5, 0.0], [0.5, 0.0], [0.5, 1.0], [ys / D, 1.0], [-0.5, skirt / H]]
    parts: list[Part] = [
        _s("Skirt", (W, t, skirt), (0, -D / 2 + t / 2, skirt / 2)),
        _s("Slant", (W, t, slant), (0, (-D / 2 + ys) / 2 + t / 2, skirt + rise / 2), rotation=[tilt, 0, 0]),
        _s("Top", (W, D / 2 - ys, t), (0, (ys + D / 2) / 2, H - t / 2)),
        _s("Back", (W, t, H), (0, D / 2 - t / 2, H / 2)),
        _s("Gutter", (W - 2 * t, 0.06, 0.03), (0, -D / 2 + t + 0.03, 0.015), STEEL_DARK, collision=False),
        _s("FilterTrough", (W - 2 * t, 0.06, 0.04), (0, D / 2 - t - 0.03 - 0.20, 0.17), STEEL_DARK, collision=False),
    ]
    for k, x in enumerate((-W / 2 + t / 2, W / 2 - t / 2)):
        parts.append(Part(f"Side{k}", "prism", [D, t, H], [x, 0, H / 2], [0, 0, 90], color=STEEL, finish="metal",
                          material="steel", profile=side_profile))
    # グリスフィルター（奥の壁へ寄りかかる網の板）
    fz0, fz1, fy0, fy1 = 0.19, 0.55, D / 2 - t - 0.20, D / 2 - t - 0.02
    flen = math.hypot(fy1 - fy0, fz1 - fz0)
    ftilt = -math.degrees(math.atan2(fy1 - fy0, fz1 - fz0))
    c = Canvas(500, 360, None, "#8A8E94", 7281)
    c.gradient(0, 0, 500, 360, "#A4A8AE", "#7A7E84")
    for y in range(0, 361, 8):
        c.line([(0, y), (500, y)], "#5A5E64", 2.0)
    c.rect(8, 8, 492, 352, outline=STEEL_LIGHT, width=10)
    images = [_face(c.array(), "metal", 7281, 0.4, 2)]
    n = 3
    fw = (W - 2 * t - 0.04) / n
    for k in range(n):
        x = -W / 2 + t + 0.02 + fw * (k + 0.5)
        parts.append(_s(f"Filter{k}", (fw - 0.01, 0.02, flen), (x, (fy0 + fy1) / 2, (fz0 + fz1) / 2),
                        "#8A8E94", faces={"front": 0}, collision=False, rotation=[ftilt, 0, 0]))
    dims = _fit(parts)
    return Product(slug="exhaust_hood", name="厨房の排気フード（壁付け 1800 mm）", shape_class="assembly",
                   category="fixture", dims=dims, mass_kg=45.0, static=True, mount="ceiling", material="steel",
                   description="形は飲食店の厨房のコンロ・フライヤーの上に付ける一般的な壁付けのステンレスの排気フード"
                               "（幅 1800 mm・奥行き 900 mm・高さ 600 mm、前は高さ 300 mm の垂直な面から奥へ傾く面、下は開いていて"
                               "奥にグリスフィルター 3 枚、前の下端に油受けの樋）で、寸法・質量は代表値。上面が天井、背面（+Y）が壁に付く。"
                               "排気ダクトは含まない。",
                   tags=["排気フード", "レンジフード", "換気フード", "フード", *KITCHEN_TAGS, "exhaust hood",
                         "range hood", "kitchen hood", "ventilation hood", "canopy hood"],
                   photos=[], colors=Colors(label_base=STEEL), images=images, parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    kitchen_fridge_2door, cold_table, gas_range, floor_fryer, sink_2bowl, work_table_steel, dishwasher_door,
    kitchen_rack, exhaust_hood)}
