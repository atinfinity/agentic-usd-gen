"""Fictional product designs: restaurant tableware (family restaurant, teishoku, izakaya).

As in products.py, no real shop or brand names; shapes and sizes are typical values for the kind of tableware.
Plates, bowls and glasses are hollow revolves (the profile goes up the outside, folds at the rim and comes down the
inside); the hollow is visual only and the collision is the convex hull of the outer shape. Plates have a flat foot so
they rest on tables and shelves. Nothing is static.
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .paint import Canvas, mix
from .products import _box, _face
from .super_fixtures import _grain

PORCELAIN, IVORY, INDIGO = "#F6F5F1", "#EFE9DC", "#2B3F6B"
LACQUER, LACQUER_RED = "#2A1410", "#9E2A1E"
GLASS, WATER, BEER, FOAM = "#F2F6F8", "#E6F2F6", "#D99A2B", "#F7F1E1"
STAINLESS, WOOD = "#C9CDD1", "#B98A57"


def _profile(outer, inner, D: float, H: float) -> list[list[float]]:
    """Outer wall (bottom to rim) and inner wall (rim to bottom) as [radius, height] in m -> revolve fractions.
    Starts at the bottom center (radius 0) and closes at the inner bottom center."""
    pts = [(0.0, 0.0), *outer, *inner, (0.0, inner[-1][1])]
    return [[round(r / (D / 2), 4), round(z / H, 4)] for r, z in pts]


def _r_at(wall, z: float) -> float:
    """Radius of a wall ([radius, height] points) at height z."""
    pts = sorted(wall, key=lambda p: p[1])
    return float(np.interp(z, [p[1] for p in pts], [p[0] for p in pts]))


def _vessel(name: str, D: float, H: float, outer, inner, color: str, finish_: str, material: str, **kw) -> Part:
    return Part(name, "revolve", [D, D, H], [0, 0, H / 2], color=color, finish=finish_, material=material,
                profile=_profile(outer, inner, D, H), **kw)


def _liquid(name: str, inner, z0: float, z1: float, color: str, material: str = "water", finish_: str = "glass",
            gap: float = 0.0006) -> Part:
    """Contents filling the inside from z0 to z1 (gap away from the wall, no collision)."""
    r0, r1 = _r_at(inner, z0) - gap, _r_at(inner, z1) - gap
    mid = _r_at(inner, (z0 + z1) / 2) - gap
    D, h = 2 * r1, z1 - z0
    prof = [[0, 0], [r0 / r1, 0], [mid / r1, 0.5], [1.0, 1.0], [0, 1.0]]
    return Part(name, "revolve", [D, D, h], [0, 0, z0 + h / 2], color=color, finish=finish_, material=material,
                profile=[[round(a, 4), b] for a, b in prof], collision=False)


def _band(name: str, r: float, z: float, t: float, color: str) -> Part:
    """A painted line around the outside (thin torus, no collision); r is the outer radius of the wall at z."""
    d = 2 * r + t
    return Part(name, "torus", [d, d, t], [0, 0, z], color=color, finish="glossy", material="ceramic",
                collision=False)


# ---------------------------------------------------------------- plates


def dinner_plate() -> Product:
    """White dinner plate, 260 mm, flat foot and wide rim."""
    D, H = 0.260, 0.025
    outer = [(0.075, 0.0), (0.077, 0.004), (0.090, 0.006), (0.105, 0.012), (0.122, 0.020), (0.130, 0.024),
             (0.130, H)]
    inner = [(0.126, H), (0.116, 0.019), (0.098, 0.011), (0.085, 0.009)]
    parts = [_vessel("Plate", D, H, outer, inner, PORCELAIN, "glossy", "ceramic")]
    return Product(slug="dinner_plate", name="白い洋皿（ディナー皿 26 cm）", shape_class="assembly", category="household",
                   dims=Dimensions(H, D, depth=D), mass_kg=0.62, material="ceramic",
                   description="形は飲食店で使う一般的な白磁の洋皿（直径 260 mm・高さ 25 mm、直径 150 mm の平らな高台と広いリム）で、"
                               "寸法・質量は代表値。中は見た目だけのくぼみ（当たり判定は外形の凸包）。",
                   tags=["食器", "皿", "洋皿", "ディナー皿", "大皿", "白い皿", "飲食店", "ファミレス", "dinner plate",
                         "plate", "white plate", "dish", "tableware"],
                   photos=[], colors=Colors(label_base=PORCELAIN), images=[], parts=parts)


def deep_plate() -> Product:
    """Deep plate for curry or pasta, 240 mm."""
    D, H = 0.240, 0.045
    outer = [(0.068, 0.0), (0.070, 0.004), (0.085, 0.008), (0.100, 0.018), (0.110, 0.032), (0.119, 0.042),
             (0.120, H)]
    inner = [(0.116, H), (0.106, 0.034), (0.095, 0.020), (0.078, 0.011), (0.060, 0.009)]
    t = 0.0014
    parts = [_vessel("Plate", D, H, outer, inner, PORCELAIN, "glossy", "ceramic"),
             _band("RimLine", _r_at(outer, 0.040) - t / 2, 0.040, t, INDIGO)]
    return Product(slug="deep_plate", name="カレー・パスタの深皿（24 cm）", shape_class="assembly",
                   category="household", dims=Dimensions(H, D, depth=D), mass_kg=0.58, material="ceramic",
                   description="形はカレー・パスタに使う一般的な白磁の深皿（直径 240 mm・高さ 45 mm、平らな高台、縁に藍の線）で、"
                               "寸法・質量は代表値。中は見た目だけのくぼみ（当たり判定は外形の凸包）。",
                   tags=["食器", "皿", "深皿", "カレー皿", "パスタ皿", "スープ皿", "飲食店", "ファミレス", "deep plate",
                         "pasta plate", "curry plate", "soup plate", "tableware"],
                   photos=[], colors=Colors(label_base=PORCELAIN), images=[], parts=parts)


# ---------------------------------------------------------------- bowls


def _bowl_shape(D: float, H: float, foot_r: float, foot_h: float, wall: float = 0.004):
    """Outer and inner walls ([radius, height]) of a bowl on a foot ring."""
    R = D / 2
    outer = [(foot_r, 0.0), (foot_r, foot_h), (foot_r + 0.004, foot_h + 0.002), (R * 0.70, H * 0.32),
             (R * 0.90, H * 0.66), (R, H * 0.97), (R - 0.001, H)]
    inner = [(R - 0.0025, H), (R - wall, H * 0.95), (R * 0.88 - wall, H * 0.64), (R * 0.66 - wall, H * 0.36),
             (foot_r * 0.9, foot_h + 0.008)]
    return outer, inner


def donburi_bowl() -> Product:
    """Donburi bowl, 165 mm, white porcelain with indigo lines."""
    D, H = 0.165, 0.085
    outer, inner = _bowl_shape(D, H, 0.032, 0.008)
    parts = [_vessel("Bowl", D, H, outer, inner, IVORY, "glossy", "ceramic"),
             _band("BandTop", _r_at(outer, H * 0.86) - 0.001, H * 0.86, 0.0022, INDIGO),
             _band("BandLow", _r_at(outer, H * 0.50) - 0.0009, H * 0.50, 0.0018, INDIGO)]
    return Product(slug="donburi_bowl", name="丼（どんぶり 5.5 寸）", shape_class="assembly", category="household",
                   dims=Dimensions(H, D, depth=D), mass_kg=0.48, material="ceramic",
                   description="形は丼もの・麺に使う一般的な磁器の丼（直径 165 mm・高さ 85 mm、直径 64 mm の高台、外側に藍の線 2 本）で、"
                               "寸法・質量は代表値。中は見た目だけのくぼみ（当たり判定は外形の凸包）。",
                   tags=["食器", "丼", "どんぶり", "丼鉢", "和食器", "飲食店", "定食屋", "donburi bowl", "rice bowl",
                         "noodle bowl", "bowl", "tableware"],
                   photos=[], colors=Colors(label_base=IVORY), images=[], parts=parts)


def rice_bowl() -> Product:
    """Rice bowl (chawan), 120 mm."""
    D, H = 0.120, 0.062
    outer, inner = _bowl_shape(D, H, 0.024, 0.007, wall=0.0035)
    parts = [_vessel("Bowl", D, H, outer, inner, "#E9E1D2", "glossy", "ceramic"),
             _band("Band", _r_at(outer, H * 0.80) - 0.0009, H * 0.80, 0.0018, "#7A4A2A")]
    return Product(slug="rice_bowl", name="茶碗（ご飯茶碗）", shape_class="assembly", category="household",
                   dims=Dimensions(H, D, depth=D), mass_kg=0.16, material="ceramic",
                   description="形は定食に使う一般的な陶器の茶碗（直径 120 mm・高さ 62 mm、直径 48 mm の高台、外側に茶の線）で、"
                               "寸法・質量は代表値。中は見た目だけのくぼみ（当たり判定は外形の凸包）。",
                   tags=["食器", "茶碗", "ご飯茶碗", "飯碗", "和食器", "定食屋", "飲食店", "rice bowl", "chawan",
                         "bowl", "tableware"],
                   photos=[], colors=Colors(label_base="#E9E1D2"), images=[], parts=parts)


def soup_bowl() -> Product:
    """Soup bowl for miso soup, 120 mm; black outside and vermilion inside, lacquer-look resin."""
    D, H = 0.120, 0.072
    outer, inner = _bowl_shape(D, H, 0.030, 0.012, wall=0.003)
    # the vermilion inside: a thin shell 0.5 mm inside the inner wall, up to just below the rim
    top = H - 0.003
    up = [(r - 0.0005, z) for r, z in inner[::-1] if z < top] + [(_r_at(inner, top) - 0.0005, top)]
    down = [(r - 0.0012, z) for r, z in up[::-1]]
    down[-1] = (down[-1][0], down[-1][1] + 0.0007)
    z0, R = up[0][1], up[-1][0]
    lh = top - z0
    prof = [[0, 0]] + [[round(r / R, 4), round((z - z0) / lh, 4)] for r, z in up + down] + \
        [[0, round((down[-1][1] - z0) / lh, 4)]]
    parts = [_vessel("Bowl", D, H, outer, inner, LACQUER, "glossy", "plastic"),
             Part("Lining", "revolve", [2 * R, 2 * R, lh], [0, 0, z0 + lh / 2], color=LACQUER_RED, finish="glossy",
                  material="plastic", profile=prof, collision=False)]
    return Product(slug="soup_bowl", name="汁椀（味噌汁の椀・黒と朱）", shape_class="assembly", category="household",
                   dims=Dimensions(H, D, depth=D), mass_kg=0.09, material="plastic",
                   description="形は定食の味噌汁に使う一般的な汁椀（直径 120 mm・高さ 72 mm、高い高台、外は黒・内は朱の漆塗り風の"
                               "樹脂）で、寸法・質量は代表値。中は見た目だけのくぼみ（当たり判定は外形の凸包）。",
                   tags=["食器", "汁椀", "お椀", "味噌汁椀", "漆器", "和食器", "定食屋", "飲食店", "soup bowl",
                         "miso soup bowl", "lacquer bowl", "wooden bowl", "bowl", "tableware"],
                   photos=[], colors=Colors(label_base=LACQUER), images=[], parts=parts)


# ---------------------------------------------------------------- glass, mug, pitcher


def water_glass() -> Product:
    """Tumbler of iced water (o-hiya), about 280 ml."""
    D, H = 0.072, 0.100
    outer = [(0.030, 0.0), (0.031, 0.002), (0.036, H - 0.001), (0.0358, H)]
    inner = [(0.0338, H), (0.0288, 0.009)]
    parts = [_vessel("Glass", D, H, outer, inner, GLASS, "glass", "glass"),
             _liquid("Water", inner, 0.0095, 0.075, WATER)]
    for k, (x, y, z, r) in enumerate(((-0.009, 0.006, 0.068, (12, 20, 30)), (0.010, -0.007, 0.062, (-18, 8, -25)))):
        parts.append(Part(f"Ice{k}", "box", [0.020, 0.020, 0.018], [x, y, z], list(r), color="#FAFCFD",
                          finish="glass", material="ice", collision=False, bevel=0.003))
    return Product(slug="water_glass", name="お冷やのグラス（タンブラー 280 ml・氷入り）", shape_class="assembly",
                   category="household", dims=Dimensions(H, D, depth=D), mass_kg=0.42, material="glass",
                   capacity_ml=280,
                   description="形は飲食店でお冷やを出す一般的なガラスのタンブラー（口径 72 mm・底径 60 mm・高さ 100 mm、"
                               "満水 280 ml、厚い底）に水 約 200 ml と角氷 2 個を入れたもので、寸法・質量（水込み）は代表値。",
                   tags=["食器", "グラス", "コップ", "タンブラー", "お冷や", "水", "飲食店", "ファミレス", "water glass",
                         "tumbler", "glass of water", "drinking glass", "tableware"],
                   photos=[], colors=Colors(label_base=GLASS), images=[], parts=parts)


def beer_mug() -> Product:
    """Medium beer mug (chu-jokki), about 435 ml, handle on +X, filled with beer and foam."""
    D, H = 0.085, 0.150
    R = D / 2
    outer = [(0.040, 0.0), (0.0415, 0.003), (R, 0.012), (R, H - 0.001), (R - 0.0005, H)]
    inner = [(R - 0.004, H), (R - 0.004, 0.020), (R - 0.008, 0.016)]
    t, ring = 0.015, 0.075  # handle tube thickness and ring outer diameter
    hx = R - 0.004 + ring / 2 - t / 2  # the ring's inner edge sinks into the wall
    parts = [_vessel("Mug", D, H, outer, inner, GLASS, "glass", "glass"),
             Part("Handle", "torus", [ring, ring, t], [hx, 0, 0.078], [90, 0, 0], color=GLASS, finish="glass",
                  material="glass"),
             _liquid("Beer", inner, 0.0165, 0.118, BEER),
             _liquid("Foam", inner, 0.118, 0.140, FOAM, material="food", finish_="matte")]
    W = hx + ring / 2 + R
    return Product(slug="beer_mug", name="生ビールの中ジョッキ（435 ml）", shape_class="assembly", category="household",
                   dims=Dimensions(H, round(W, 4), depth=D), mass_kg=1.05, material="glass", capacity_ml=435,
                   description="形は居酒屋・ファミレスで使う一般的なガラスの中ジョッキ（口径 85 mm・高さ 150 mm、厚い底、"
                               "+X 側に輪の取っ手、中ジョッキの目安 435 ml）に生ビールと泡を注いだもので、寸法・質量（中身込み）は代表値。",
                   tags=["食器", "ジョッキ", "ビールジョッキ", "中ジョッキ", "生ビール", "居酒屋", "飲食店", "beer mug",
                         "beer stein", "glass of beer", "mug", "tableware"],
                   photos=[], colors=Colors(label_base=GLASS, liquid=BEER), images=[], parts=parts)


def water_pitcher() -> Product:
    """Water pitcher, 1.3 L, clear resin; spout on -X, handle on +X, with water."""
    D, H = 0.110, 0.210
    R = D / 2
    outer = [(0.048, 0.0), (0.050, 0.003), (R, 0.020), (R, H - 0.004), (R + 0.002, H - 0.001), (R + 0.002, H)]
    inner = [(R - 0.0015, H), (R - 0.0025, H - 0.006), (R - 0.0025, 0.022), (0.046, 0.006)]
    parts = [_vessel("Pitcher", D + 0.004, H, outer, inner, GLASS, "glass", "plastic"),
             _liquid("Water", inner, 0.0065, 0.135, WATER),
             Part("Spout", "box", [0.030, 0.034, 0.003], [-R - 0.010, 0, H - 0.006], [0, -18, 0], color=GLASS,
                  finish="glass", material="plastic", thin_walled=True, bevel=0.001)]
    hx = R + 0.032
    handle = [
        _box("HandleTop", (0.036, 0.016, 0.012), (R + 0.016, 0, H - 0.030), GLASS, "glass"),
        _box("HandleBottom", (0.036, 0.016, 0.012), (R + 0.016, 0, 0.050), GLASS, "glass"),
        _box("HandleGrip", (0.012, 0.018, H - 0.068), (hx, 0, (H - 0.030 + 0.050) / 2), GLASS, "glass"),
    ]
    for p in handle:
        p.material = "plastic"
    parts += handle
    W = (hx + 0.006) + (R + 0.010 + 0.015)
    return Product(slug="water_pitcher", name="水差し（ピッチャー 1.3 L）", shape_class="assembly", category="household",
                   dims=Dimensions(H, round(W, 4), depth=D + 0.004), mass_kg=1.35, material="plastic",
                   capacity_ml=1300,
                   description="形は飲食店のお冷や用の一般的な透明の樹脂のピッチャー（胴の直径 110 mm・高さ 210 mm、容量 1.3 L、"
                               "−X に注ぎ口・+X に取っ手）に水 約 1 L を入れたもので、寸法・質量（水込み）は代表値。",
                   tags=["食器", "ピッチャー", "水差し", "お冷や", "水", "飲食店", "ファミレス", "water pitcher",
                         "pitcher", "jug", "water jug", "tableware"],
                   photos=[], colors=Colors(label_base=GLASS), images=[], parts=parts)


# ---------------------------------------------------------------- oshibori, cutlery


def oshibori() -> Product:
    """Rolled white hand towel (oshibori) on its bamboo-look resin tray."""
    TW, TD, th = 0.140, 0.055, 0.010
    base = "#A87B45"
    tray = Canvas(TW * 1000, TD * 1000, None, base, 6921)
    tray.gradient(0, 0, TW * 1000, TD * 1000, mix(base, "#FFFFFF", 0.10), mix(base, "#000000", 0.08))
    for k in range(1, 7):  # bamboo-like slats
        x = TW * 1000 * k / 7
        tray.line([(x, 0), (x, TD * 1000)], mix(base, "#3A2614", 0.45), 0.9)
    for y in (6, TD * 1000 - 6):
        tray.line([(0, y), (TW * 1000, y)], mix(base, "#3A2614", 0.35), 0.7)
    towel_r, towel_l = 0.016, 0.105
    rim = mix(base, "#000000", 0.1)
    tray_parts = [
        _box("Tray", (TW, TD, th * 0.4), (0, 0, th * 0.2), base, "plastic", {"top": 0}),
        _box("RimF", (TW, 0.005, th), (0, -TD / 2 + 0.0025, th / 2), rim, "plastic"),
        _box("RimB", (TW, 0.005, th), (0, TD / 2 - 0.0025, th / 2), rim, "plastic"),
    ]
    for p in tray_parts:
        p.material = "plastic"
    parts = tray_parts + [
        Part("Towel", "cylinder", [2 * towel_r, 2 * towel_r, towel_l], [0, 0, th * 0.4 + towel_r], [0, 90, 0],
             color="#FBFBF8", finish="matte", material="fabric"),
        Part("TowelEdge", "box", [towel_l - 0.004, 0.002, 0.012], [0, -towel_r * 0.55, th * 0.4 + towel_r * 1.70],
             [-30, 0, 0], color="#F1F1EC", finish="matte", material="fabric", collision=False, bevel=0),
    ]
    images = [_face(tray.array(), "plastic", 6921, 0.4, 4)]
    return Product(slug="oshibori", name="おしぼりとおしぼり受け", shape_class="assembly", category="household",
                   dims=Dimensions(th * 0.4 + 2 * towel_r, TW, depth=TD), mass_kg=0.07, material="fabric",
                   description="形は飲食店で出す一般的な巻いた布のおしぼり（直径 32 mm・長さ 105 mm）と、樹脂の竹風のおしぼり受け"
                               "（140 × 55 mm・縁の高さ 10 mm）で、寸法・質量は代表値。",
                   tags=["おしぼり", "おしぼり受け", "おしぼりトレー", "タオル", "居酒屋", "飲食店", "ファミレス",
                         "oshibori", "wet towel", "hand towel", "towel tray"],
                   photos=[], colors=Colors(label_base="#FBFBF8"), images=images, parts=parts)


def cutlery_set() -> Product:
    """Table cutlery case (wood, 4 cells) with forks, knives, spoons and paper-wrapped chopsticks."""
    W, D, H = 0.200, 0.100, 0.090
    t = 0.008
    images = [_grain(W * 1000, H * 1000, 6931, WOOD), _grain((D - 2 * t) * 1000, H * 1000, 6932, WOOD),
              _grain(W * 1000, D * 1000, 6933, mix(WOOD, "#FFFFFF", 0.1))]
    dark = mix(WOOD, "#000000", 0.25)

    def wood(name, size, center, faces=None, collision=True):
        return Part(name, "box", list(size), list(center), color=WOOD, finish="matte", material="wood", faces=faces,
                    collision=collision)

    parts: list[Part] = [
        wood("Base", (W, D, t), (0, 0, t / 2), {"top": 2}),
        wood("WallF", (W, t, H), (0, -D / 2 + t / 2, H / 2), {"front": 0}),
        wood("WallB", (W, t, H), (0, D / 2 - t / 2, H / 2), {"back": 0}),
        wood("WallL", (t, D - 2 * t, H), (-W / 2 + t / 2, 0, H / 2), {"left": 1}),
        wood("WallR", (t, D - 2 * t, H), (W / 2 - t / 2, 0, H / 2), {"right": 1}),
    ]
    cell = (W - 2 * t) / 4
    for i in range(1, 4):
        parts.append(Part(f"Divider{i}", "box", [0.005, D - 2 * t, H - 0.015],
                          [-W / 2 + t + cell * i, 0, t + (H - 0.015 - t) / 2], color=dark, finish="matte",
                          material="wood", collision=False))
        parts[-1].size[2] = H - 0.015 - t
    rng = np.random.default_rng(6934)

    def cx(i: int) -> float:
        return -W / 2 + t + cell * (i + 0.5)

    z0 = t
    # cells 0-2: forks, knives, spoons (handles up)
    for i, (kind, L) in enumerate((("Fork", 0.190), ("Knife", 0.205), ("Spoon", 0.180))):
        for k in range(5):
            x = cx(i) + (k - 2) * 0.006 + rng.uniform(-0.001, 0.001)
            y = (k - 2) * 0.014
            tilt = [rng.uniform(-8, 8), rng.uniform(-5, 5), 0]
            w = 0.011 if kind == "Knife" else 0.013
            parts.append(Part(f"{kind}{k}", "box", [w, 0.003, L], [x, y, z0 + L / 2], tilt, color=STAINLESS,
                              finish="metal", material="steel", collision=False, bevel=0.0012))
    # cell 3: paper-wrapped chopsticks (white sleeve, red band)
    L = 0.215
    for k in range(6):
        x = cx(3) + (k % 3 - 1) * 0.011
        y = (k // 3 - 0.5) * 0.034
        tilt = [rng.uniform(-6, 6), rng.uniform(-5, 5), 0]
        c = np.array([x, y, z0 + L / 2])
        up = np.array([np.sin(np.radians(tilt[1])), -np.sin(np.radians(tilt[0])), 1.0])
        b = c + up * (L * 0.32)
        parts += [Part(f"Chopsticks{k}", "box", [0.014, 0.006, L], c.tolist(), tilt, color="#F7F4EC",
                       finish="matte", material="paper", collision=False, bevel=0.001),
                  Part(f"ChopBand{k}", "box", [0.0146, 0.0066, 0.012], b.tolist(), tilt, color="#B3262B",
                       finish="matte", material="paper", collision=False, bevel=0.0005)]
    return Product(slug="cutlery_set", name="卓上のカトラリーケース（フォーク・ナイフ・スプーン・割り箸）",
                   shape_class="assembly", category="household", dims=Dimensions(z0 + L, W, depth=D),
                   mass_kg=0.95, material="wood",
                   description="形はファミレスのテーブルに置く一般的な木のカトラリーケース（200 × 100 mm・高さ 90 mm、4 つの仕切り）に、"
                               "ステンレスのフォーク・ナイフ・スプーン各 5 本（柄が上）と袋入りの割り箸 6 膳を立てたもので、寸法・質量は代表値。"
                               "当たり判定はケースだけ。",
                   tags=["カトラリー", "カトラリーケース", "フォーク", "ナイフ", "スプーン", "割り箸", "箸", "卓上",
                         "飲食店", "ファミレス", "cutlery", "cutlery holder", "silverware", "fork", "knife", "spoon",
                         "chopsticks", "tableware"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    dinner_plate, deep_plate, donburi_bowl, rice_bowl, soup_bowl, water_glass, beer_mug, water_pitcher, oshibori,
    cutlery_set)}
