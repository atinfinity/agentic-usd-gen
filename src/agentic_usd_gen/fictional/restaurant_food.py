"""架空の商品のデザイン: ファミレス・食堂の皿に盛った料理。

形と寸法は同じ種類の料理・器の一般的な値にし、実在の店名・ブランド名は使わない。
器（皿・丼・トレー・グラス）はコリジョンのある部品で 1 品が 1 つの剛体になり、料理はコリジョンのない見た目だけの部品
（products._food）を器の内側に載せる。料理の上面には CC0 の写真（photos.json）か Canvas で描いた模様を貼る。
正面は −Y（お客さまの側）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .paint import Canvas, finish
from .products import _food, _food_photo

WHITE_WARE = "#F7F5F0"

# 器の断面（[半径の割合, 高さの割合]、外側を上って縁で折り返し、内側を下りて底の中心で閉じる）。
# 料理は内側の底（最後の点の高さ）か、内側の壁の半径（_inner）に合わせて載せる。
PLATE = [[0, 0], [0.58, 0], [0.62, 0.18], [0.70, 0.30], [0.97, 0.82], [1.0, 1.0], [0.95, 1.0], [0.70, 0.45],
         [0, 0.45]]
DEEP = [[0, 0], [0.52, 0], [0.56, 0.12], [0.62, 0.18], [0.90, 0.72], [1.0, 1.0], [0.95, 1.0], [0.84, 0.72],
        [0.58, 0.30], [0, 0.28]]
BOWL = [[0, 0], [0.42, 0], [0.45, 0.08], [0.52, 0.12], [0.82, 0.48], [0.97, 0.90], [1.0, 1.0], [0.95, 1.0],
        [0.92, 0.90], [0.74, 0.48], [0.40, 0.16], [0, 0.14]]
SKILLET = [[0, 0], [0.90, 0], [0.96, 0.25], [1.0, 1.0], [0.92, 1.0], [0.88, 0.32], [0, 0.30]]


def _inner(prof: list[list[float]], zf: float) -> float:
    """器の内側の壁の半径の割合（高さの割合 zf で）。縁（最初の最も高い点）より後の点を補間する。"""
    top = max(z for _, z in prof)
    rim = next(i for i, (_, z) in enumerate(prof) if z == top) + 1  # 縁の内側の点
    pts = prof[rim:]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z1 <= zf <= z0:
            t = (zf - z0) / (z1 - z0) if z1 != z0 else 0.0
            return r0 + (r1 - r0) * t
    return pts[-1][0] if zf < pts[-1][1] else pts[0][0]


def _seat(prof: list[list[float]], frac: float) -> float:
    """内側の壁の半径の割合が frac になる高さの割合（底の広い山をその高さに置けば器の外へ突き抜けない）。"""
    zf = prof[-1][1]
    while zf < 1.0 and _inner(prof, zf) < frac:
        zf += 0.005
    return zf


def _ware(name: str, prof, size, at=(0.0, 0.0, 0.0), color: str = WHITE_WARE, finish_: str = "glossy",
          material: str = "ceramic", **kw) -> tuple[Part, float]:
    """器の部品と、内側の底の高さ（at の z からの絶対値）。"""
    x, y, z = at
    p = Part(name, "revolve", list(size), [x, y, z + size[2] / 2], color=color, finish=finish_, material=material,
             profile=prof, **kw)
    return p, z + prof[-1][1] * size[2]


def _tex(c: Canvas, seed: int, strength: float = 0.3) -> np.ndarray:
    return finish(c.array(), "paper", seed, strength)


def _speckle(c: Canvas, n: int, colors: list[str], r: tuple[float, float], area=None) -> None:
    x0, y0, x1, y1 = area or (0, 0, c.w_mm, c.h_mm)
    for _ in range(n):
        x, y = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        rr = c.rng.uniform(*r)
        col = colors[c.rng.randrange(len(colors))]
        c.ellipse(x - rr, y - rr * c.rng.uniform(0.6, 1.0), x + rr, y + rr * c.rng.uniform(0.6, 1.0), fill=col)


# ---------------------------------------------------------------- ハンバーグ


def _patty_top(seed: int) -> np.ndarray:
    """デミグラスソースのかかったハンバーグの上面。"""
    W, D = 115.0, 82.0
    c = Canvas(W, D, 8, "#6B3A1E", seed)
    c.gradient(0, 0, W, D, "#7A4424", "#5A2E16")
    _speckle(c, 160, ["#4E2610", "#8A5230", "#3E1E0C"], (0.6, 2.0))
    c.ellipse(12, 10, W - 12, D - 10, fill="#4A1E0C")  # ソース
    c.ellipse(22, 18, W - 26, D - 20, fill="#5A2610")
    for _ in range(6):  # つやの筋
        x, y = c.rng.uniform(25, W - 35), c.rng.uniform(20, D - 25)
        c.line([(x, y), (x + c.rng.uniform(8, 18), y + c.rng.uniform(-3, 3))], "#9C5A3A", c.rng.uniform(0.8, 1.6))
    _speckle(c, 18, ["#F4EBD0"], (0.6, 1.2), (30, 22, W - 30, D - 22))  # 生クリームの点
    return _tex(c, seed, 0.25)


def hamburg_steak_set() -> Product:
    """木の台に載せた楕円の鉄板のハンバーグ（デミグラスソース）と付け合わせ（コーン・にんじん・ブロッコリー・ポテト）。"""
    board = (0.30, 0.21, 0.018)
    sk = (0.25, 0.18, 0.024)
    images = [_patty_top(7001)]
    parts: list[Part] = [Part("Board", "box", list(board), [0, 0, board[2] / 2], color="#9A6A3E", finish="matte",
                              material="wood", bevel=0.004)]
    pan, floor = _ware("Skillet", SKILLET, sk, (0, 0, board[2]), color="#2A2A2C", finish_="metal", material="iron")
    parts.append(pan)
    parts += [
        _food("Sauce", "cylinder", (0.14, 0.11, 0.003), (-0.03, 0.0, floor + 0.0015), "#4A1E0C", "glossy"),
        _food("Patty", "bun", (0.115, 0.082, 0.030), (-0.03, 0.0, floor + 0.002 + 0.015), "#6B3A1E",
              faces={"top": 0}),
    ]
    # 付け合わせ（右側）: コーン・にんじんのグラッセ・ブロッコリー・フライドポテト
    for k in range(9):
        a = k * 0.7
        parts.append(_food(f"Corn{k}", "dome", (0.009, 0.008, 0.006),
                           (0.065 + 0.012 * math.cos(a), 0.040 + 0.010 * math.sin(a), floor + 0.003), "#F2C230",
                           "glossy"))
    for k, (x, y, rz) in enumerate(((0.068, -0.005, 20), (0.090, 0.012, -30))):
        parts.append(_food(f"Carrot{k}", "prism", (0.026, 0.016, 0.014), (x, y, floor + 0.007), "#E2721E", "glossy",
                           rotation=(0, 0, rz), profile=[[-0.5, 0.0], [0.5, 0.0], [0.15, 1.0], [-0.15, 1.0]]))
    parts += [_food("Broccoli", "bun", (0.032, 0.030, 0.026), (0.082, -0.040, floor + 0.013), "#3F7A2A"),
              _food("BroccoliStem", "cylinder", (0.012, 0.012, 0.012), (0.080, -0.036, floor + 0.004), "#8DB560")]
    for k, (x, y, rz) in enumerate(((0.040, -0.052, 10), (0.050, -0.060, 35), (0.035, -0.064, -25))):
        parts.append(_food(f"Fry{k}", "box", (0.050, 0.009, 0.009), (x, y, floor + 0.0045 + 0.004 * (k % 2)),
                           "#E9C46A", rotation=(0, 0, rz)))
    H = max(floor + 0.002 + 0.030, board[2] + sk[2])
    return Product(slug="hamburg_steak_set", name="ハンバーグ（鉄板・デミグラスソース）", shape_class="assembly",
                   category="food", dims=Dimensions(round(H, 4), board[0], depth=board[1]),
                   mass_kg=1.6, material="iron",
                   description="形はファミリーレストランの一般的な鉄板のハンバーグ（木の台 300×210 mm に楕円の鉄板 250×180 mm、"
                               "200 g ほどのハンバーグにデミグラスソース、付け合わせはコーン・にんじん・ブロッコリー・ポテト）で、"
                               "寸法・質量（鉄板込み）は代表値。ハンバーグの上面は描いた模様。",
                   tags=["ハンバーグ", "鉄板", "洋食", "ファミレス", "料理", "hamburg steak", "hamburger steak",
                         "sizzling plate", "plated dish"],
                   photos=[], colors=Colors(label_base="#6B3A1E"), images=images, parts=parts)


# ---------------------------------------------------------------- オムライス


def _omelet_top(seed: int) -> np.ndarray:
    W, D = 170.0, 90.0
    c = Canvas(W, D, 8, "#F2C230", seed)
    c.gradient(0, 0, W, D, "#F6CF45", "#E9B526")
    _speckle(c, 40, ["#E0A52A", "#F8D865"], (1.0, 3.5))
    _speckle(c, 10, ["#C98A2A"], (0.8, 1.8))  # 焼き色
    pts = [(28 + i * 12.5, D / 2 + (9 if i % 2 else -9)) for i in range(10)]  # ケチャップのジグザグ
    c.line(pts, "#B3121C", 5.5)
    c.line(pts, "#D02A2A", 3.0)
    return _tex(c, seed, 0.25)


def omurice() -> Product:
    """楕円の皿にオムライス（ケチャップのジグザグ）とパセリ。"""
    pl = (0.28, 0.20, 0.022)
    plate, floor = _ware("Plate", PLATE, pl)
    images = [_omelet_top(7011)]
    parts: list[Part] = [plate,
                         _food("Omelet", "bun", (0.170, 0.090, 0.048), (-0.005, 0, floor - 0.001 + 0.024),
                               "#F2C230", faces={"top": 0}),
                         _food("Parsley", "bun", (0.022, 0.020, 0.014), (0.098, -0.020, floor + 0.007), "#3E7B27"),
                         _food("Ketchup", "dome", (0.020, 0.016, 0.005), (0.095, 0.025, floor + 0.0015), "#B3121C",
                               "glossy")]
    H = floor - 0.001 + 0.048
    return Product(slug="omurice", name="オムライス", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), pl[0], depth=pl[1]), mass_kg=0.85, material="ceramic",
                   description="形は洋食店・ファミリーレストランの一般的なオムライス（楕円の皿 280×200 mm に、"
                               "長さ 170 mm・幅 90 mm・高さ 48 mm の卵で包んだチキンライス、上にケチャップ）で、寸法・質量（皿込み）は代表値。"
                               "卵の上面は描いた模様。",
                   tags=["オムライス", "洋食", "卵", "ケチャップ", "ファミレス", "料理", "omurice", "omelette rice",
                         "omelet", "plated dish"],
                   photos=[], colors=Colors(label_base="#F2C230"), images=images, parts=parts)


# ---------------------------------------------------------------- ミートソース


def _meat_sauce_top(seed: int) -> np.ndarray:
    W = 105.0
    c = Canvas(W, W * 0.9, 8, "#8B3A1A", seed)
    c.gradient(0, 0, W, W * 0.9, "#9A4420", "#7A3014")
    _speckle(c, 260, ["#6A2810", "#A54A22", "#5A200C", "#B85A2C"], (0.8, 2.6))
    _speckle(c, 25, ["#D9822B"], (0.6, 1.4))  # 油
    _speckle(c, 30, ["#F3E9C8"], (0.4, 0.9))  # 粉チーズ
    _speckle(c, 14, ["#3E7B27"], (0.4, 0.8))  # パセリ
    return _tex(c, seed, 0.25)


def meat_sauce_pasta() -> Product:
    """深皿のスパゲッティ ミートソース（パスタの山の上にひき肉のソースと粉チーズ）。

    写真: spaghetti（CC0。パスタの山に合成）
    """
    pl = (0.26, 0.26, 0.042)
    plate, floor = _ware("Plate", DEEP, pl)
    images = [_food_photo("spaghetti", 175, 175, (0.22, 0.20, 0.70, 0.92), 7021), _meat_sauce_top(7022)]
    zb = _seat(DEEP, 0.175 / pl[0] * 1.02) * pl[2]  # パスタの山の裾が内側の壁に触れる高さ
    parts: list[Part] = [
        plate,
        _food("Pasta", "bun", (0.175, 0.175, 0.036), (0, 0, zb + 0.018), "#E2A34E", faces={"top": 0}),
        _food("Sauce", "bun", (0.105, 0.095, 0.020), (0.004, -0.004, zb + 0.026 + 0.010), "#8B3A1A",
              faces={"top": 1}),
    ]
    H = max(pl[2], zb + 0.026 + 0.020)
    return Product(slug="meat_sauce_pasta", name="スパゲッティ ミートソース", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), pl[0], depth=pl[1]), mass_kg=0.95, material="ceramic",
                   description="形はファミリーレストランの一般的なミートソースのスパゲッティ（直径 260 mm・高さ 42 mm の深皿に、"
                               "パスタの山とひき肉のソース、粉チーズとパセリ）で、寸法・質量（皿込み）は代表値。パスタの山は写真、"
                               "ソースは描いた模様。",
                   tags=["ミートソース", "スパゲッティ", "パスタ", "洋食", "ファミレス", "料理", "meat sauce pasta",
                         "spaghetti bolognese", "pasta", "plated dish"],
                   photos=["spaghetti"], colors=Colors(label_base="#E2A34E"), images=images, parts=parts)


# ---------------------------------------------------------------- カレーライス


def _curry_top(seed: int) -> np.ndarray:
    c = Canvas(205, 165, 8, "#8A4E1E", seed)
    c.photo("curry", 0, 0, 205, 165, shape="ellipse", feather=6, crop=(0.22, 0.13, 0.80, 0.88))
    return finish(c.array(), "paper", seed, 0.3)


def curry_rice() -> Product:
    """カレー皿（楕円の浅い深皿）のカレーライスとスプーン。

    写真: curry（CC0。ご飯とカレーの山に合成）
    """
    pl = (0.28, 0.22, 0.036)
    plate, floor = _ware("Plate", DEEP, pl)
    images = [_curry_top(7031)]
    zb = _seat(DEEP, max(0.205 / pl[0], 0.165 / pl[1]) * 1.02) * pl[2]
    parts: list[Part] = [plate,
                         _food("Curry", "bun", (0.205, 0.165, 0.032), (0, 0, zb + 0.016), "#8A4E1E",
                               faces={"top": 0}),
                         Part("Spoon", "box", [0.16, 0.022, 0.004], [0.07, -0.082, pl[2] - 0.004], [0, -6, -10],
                              color="#C9CDD1", finish="metal", collision=False, material="steel", bevel=0.0015)]
    t = math.radians(6)  # スプーンの傾き（Y 軸まわり）
    H = max(pl[2] - 0.004 + 0.08 * math.sin(t) + 0.002 * math.cos(t), zb + 0.032)
    return Product(slug="curry_rice", name="カレーライス", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), pl[0], depth=pl[1]), mass_kg=0.9, material="ceramic",
                   description="形は食堂・ファミリーレストランの一般的なカレーライス（楕円のカレー皿 280×220 mm・高さ 36 mm に、"
                               "ご飯とカレー、縁にスプーン）で、寸法・質量（皿込み）は代表値。ご飯とカレーは写真を貼った低い山。",
                   tags=["カレー", "カレーライス", "洋食", "ファミレス", "料理", "curry rice", "japanese curry",
                         "curry", "plated dish"],
                   photos=["curry"], colors=Colors(label_base="#8A4E1E"), images=images, parts=parts)


# ---------------------------------------------------------------- ラーメン


def _negi_top(seed: int) -> np.ndarray:
    c = Canvas(40, 36, 8, "#6FAE3A", seed)
    _speckle(c, 70, ["#A6D46A", "#4E8E26", "#E8F2D0"], (0.8, 2.0))
    return _tex(c, seed, 0.2)


def ramen_bowl() -> Product:
    """黒い丼のラーメン（みそ）。スープの面に写真、のり・チャーシュー・ねぎを部品で足す。

    写真: ramen（CC0。スープの面に合成）
    """
    D, h = 0.21, 0.088
    bowl, _ = _ware("Bowl", BOWL, (D, D, h), color="#1E1E20")
    zs = 0.80
    soup_d = 2 * _inner(BOWL, zs) * D / 2 * 0.98
    zt = zs * h
    images = [_food_photo("ramen", 170, 170, (0.17, 0.06, 0.78, 0.88), 7041), _negi_top(7042)]
    parts: list[Part] = [
        bowl,
        _food("Soup", "cylinder", (soup_d, soup_d, 0.004), (0, 0, zt - 0.002), "#C9853A", "glossy",
              faces={"top": 0}),
        _food("Nori", "box", (0.070, 0.002, 0.065), (0.010, 0.058, zt + 0.022), "#1C2416", rotation=(-22, 0, 4)),
        _food("Negi", "bun", (0.042, 0.038, 0.007), (-0.035, -0.030, zt + 0.0025), "#6FAE3A", faces={"top": 1}),
    ]
    for k, (x, y, rx) in enumerate(((0.040, 0.000, 12), (0.050, -0.032, 18))):
        parts.append(_food(f"Chashu{k}", "cylinder", (0.060, 0.055, 0.006), (x, y, zt + 0.004), "#C48A64",
                           rotation=(rx, -10, 0)))
        parts.append(_food(f"ChashuRim{k}", "torus", (0.061, 0.056, 0.004), (x, y, zt + 0.004), "#7A4A2A",
                           rotation=(rx, -10, 0)))
    H = max(h, zt + 0.022 + 0.033)
    return Product(slug="ramen_bowl", name="ラーメン（みそ）", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), D), mass_kg=1.4, material="ceramic",
                   description="形はラーメン店・食堂の一般的なラーメン（口径 210 mm・高さ 88 mm の丼に、スープと麺・チャーシュー・"
                               "のり・ねぎ）で、寸法・質量（丼とスープ込み）は代表値。スープの面は写真、のり・チャーシュー・ねぎは簡単な形。",
                   tags=["ラーメン", "みそラーメン", "丼", "麺類", "料理", "ramen", "miso ramen", "noodle soup",
                         "bowl of ramen"],
                   photos=["ramen"], colors=Colors(label_base="#C9853A"), images=images, parts=parts)


# ---------------------------------------------------------------- 唐揚げ定食


def _cabbage_top(seed: int) -> np.ndarray:
    c = Canvas(75, 70, 8, "#DCEBC0", seed)
    for _ in range(140):
        x, y = c.rng.uniform(0, 75), c.rng.uniform(0, 70)
        a = c.rng.uniform(0, math.pi)
        L = c.rng.uniform(6, 16)
        c.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))],
               ["#B8D490", "#F4F8E8", "#9CC46C"][c.rng.randrange(3)], c.rng.uniform(0.5, 1.1))
    return _tex(c, seed, 0.2)


def karaage_set() -> Product:
    """唐揚げ定食（塗りのトレーに唐揚げとキャベツの皿・ご飯・みそ汁・箸）。

    写真: karaage・cooked_rice・miso_soup（CC0。唐揚げ・ご飯・みそ汁の面に合成）
    """
    TW, TD, TH = 0.42, 0.30, 0.012
    images = [_food_photo("karaage", 46, 40, (0.40, 0.18, 0.62, 0.48), 7051, 0.25),
              _food_photo("karaage", 46, 40, (0.55, 0.40, 0.78, 0.72), 7052, 0.25),
              _food_photo("cooked_rice", 100, 100, (0.26, 0.16, 0.74, 0.72), 7053),
              _food_photo("miso_soup", 95, 95, (0.25, 0.29, 0.74, 0.62), 7054),
              _cabbage_top(7055)]
    lacquer = "#3A2016"
    parts: list[Part] = [Part("Tray", "box", [TW, TD, TH], [0, 0, TH / 2], color=lacquer, finish="glossy",
                              material="wood", bevel=0.003)]
    for name, size, c in (("RimF", (TW, 0.008, 0.010), (0, -TD / 2 + 0.004, TH + 0.005)),
                          ("RimB", (TW, 0.008, 0.010), (0, TD / 2 - 0.004, TH + 0.005)),
                          ("RimL", (0.008, TD - 0.016, 0.010), (-TW / 2 + 0.004, 0, TH + 0.005)),
                          ("RimR", (0.008, TD - 0.016, 0.010), (TW / 2 - 0.004, 0, TH + 0.005))):
        parts.append(Part(name, "box", list(size), list(c), color=lacquer, finish="glossy", collision=False,
                          material="wood", bevel=0.002))
    # 主菜の皿（奥）: キャベツの千切りの山・唐揚げ 5 個・レモン
    plate, pf = _ware("Plate", PLATE, (0.20, 0.20, 0.022), (0.0, 0.050, TH))
    parts += [plate, _food("Cabbage", "bun", (0.075, 0.070, 0.030), (0.040, 0.080, pf + 0.015), "#DCEBC0",
                           faces={"top": 4})]
    for k, (x, y, s) in enumerate(((-0.040, 0.035, 1.0), (-0.005, 0.025, 0.95), (-0.030, 0.072, 1.05),
                                   (0.005, 0.062, 0.9), (-0.062, 0.062, 0.92))):
        parts.append(_food(f"Karaage{k}", "bread", (0.046 * s, 0.040 * s, 0.032 * s), (x, y, pf + 0.016 * s),
                           "#B5702C", faces={"top": k % 2}))
    parts.append(_food("Lemon", "prism", (0.034, 0.014, 0.016), (0.042, 0.022, pf + 0.008), "#F2D03A", "glossy",
                       rotation=(0, 0, -25), profile=[[-0.5, 0.0], [0.5, 0.0], [0.0, 1.0]]))
    # ご飯（手前の左）・みそ汁（手前の右）
    rice_bowl, _ = _ware("RiceBowl", BOWL, (0.120, 0.120, 0.062), (-0.120, -0.080, TH), color="#F3F1EA")
    zr = TH + 0.72 * 0.062
    rr = 2 * _inner(BOWL, 0.72) * 0.060
    soup_bowl, _ = _ware("SoupBowl", BOWL, (0.115, 0.115, 0.068), (0.120, -0.080, TH), color="#6E1A12")
    zm = TH + 0.80 * 0.068
    mr = 2 * _inner(BOWL, 0.80) * 0.0575 * 0.98
    parts += [rice_bowl,
              _food("Rice", "dome", (rr, rr, 0.026), (-0.120, -0.080, zr + 0.013 - 0.002), "#F4F1E8",
                    faces={"top": 2}),
              soup_bowl,
              _food("MisoSoup", "cylinder", (mr, mr, 0.004), (0.120, -0.080, zm - 0.002), "#C9A46A", "glossy",
                    faces={"top": 3})]
    for k, dx in enumerate((-0.004, 0.004)):  # 箸（右端に縦に置く）
        parts.append(Part(f"Chopstick{k}", "box", [0.007, 0.215, 0.006], [0.192 + dx, -0.005, TH + 0.003],
                          color="#5A3A22", finish="matte", collision=False, material="wood", bevel=0.001))
    H = max(TH + 0.068, zr + 0.024, pf + 0.034)
    return Product(slug="karaage_set", name="唐揚げ定食", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), TW, depth=TD), mass_kg=1.9, material="wood",
                   description="形は食堂・ファミリーレストランの一般的な唐揚げ定食（塗りのトレー 420×300 mm に、"
                               "唐揚げ 5 個とキャベツの千切り・レモンの皿（直径 200 mm）、ご飯の茶碗、みそ汁の汁椀、箸）で、"
                               "寸法・質量（器込み）は代表値。唐揚げ・ご飯・みそ汁の面は写真、キャベツは描いた模様。",
                   tags=["唐揚げ", "唐揚げ定食", "定食", "和食", "ご飯", "みそ汁", "料理", "karaage", "karaage set meal",
                         "fried chicken", "set meal", "teishoku"],
                   photos=["karaage", "cooked_rice", "miso_soup"], colors=Colors(label_base="#B5702C"), images=images,
                   parts=parts)


# ---------------------------------------------------------------- 焼き餃子


def _gyoza_top(seed: int) -> np.ndarray:
    """焼き目を上にした餃子（縁は白い皮、中央がきつね色）。"""
    W, D = 72.0, 34.0
    c = Canvas(W, D, 8, "#EFE0BE", seed)
    c.gradient(0, 0, W, D, "#F4E8CC", "#E6D3A6")
    c.ellipse(8, 6, W - 8, D - 6, fill="#D9A55A")
    c.ellipse(14, 9, W - 14, D - 9, fill="#C2803A")
    c.ellipse(22, 12, W - 22, D - 12, fill="#A9652A")
    _speckle(c, 40, ["#8A4E1E", "#D39A50"], (0.5, 1.4), (14, 9, W - 14, D - 9))
    return _tex(c, seed, 0.25)


def gyoza_plate() -> Product:
    """焼き餃子 6 個（焼き目を上に並べる）の楕円の皿と、たれの小皿。"""
    pl = (0.26, 0.15, 0.020)
    py = 0.025
    plate, floor = _ware("Plate", PLATE, pl, (0, py, 0))
    images = [_gyoza_top(7061)]
    parts: list[Part] = [plate]
    for k in range(6):  # 1 列に 6 個、横に寄せて少しずつ傾けて並べる（焼いたフライパンの形のまま）
        x = (k - 2.5) * 0.031
        parts.append(_food(f"Gyoza{k}", "bun", (0.072, 0.033, 0.022), (x, py + 0.002 * (k % 2), floor + 0.011),
                           "#E6D3A6", rotation=(0, 0, 90 + (k - 2.5) * 2.5), faces={"top": 0}))
    sx, sy = 0.085, -0.090
    sauce, sf = _ware("SauceDish", PLATE, (0.085, 0.085, 0.016), (sx, sy, 0))
    parts += [sauce, _food("Sauce", "cylinder", (0.050, 0.050, 0.002), (sx, sy, sf + 0.001), "#5A2A12", "glossy"),
              _food("ChiliOil", "cylinder", (0.020, 0.016, 0.0005), (sx + 0.005, sy + 0.005, sf + 0.0023), "#C2401A",
                    "glossy")]
    H = max(floor + 0.022, pl[2])
    depth = (py + pl[1] / 2) - (sy - 0.0425)
    return Product(slug="gyoza_plate", name="焼き餃子（6 個）", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), pl[0], depth=round(depth, 4)), mass_kg=0.6, material="ceramic",
                   description="形は中華料理店・ファミリーレストランの一般的な焼き餃子（楕円の皿 260×150 mm に、"
                               "焼き目を上にした長さ 72 mm の餃子 6 個、手前にたれの小皿）で、寸法・質量（皿込み）は代表値。焼き目は描いた模様。",
                   tags=["餃子", "焼き餃子", "中華", "ファミレス", "料理", "gyoza", "pan-fried dumplings", "dumplings",
                         "plated dish"],
                   photos=[], colors=Colors(label_base="#E6D3A6"), images=images, parts=parts)


# ---------------------------------------------------------------- ピザ


def _pizza_top(seed: int) -> np.ndarray:
    """マルゲリータの上面（円。縁の焼けた生地・トマトソース・溶けたチーズ・バジル）。"""
    W = 250.0
    c = Canvas(W, W, 8, "#C98A45", seed)
    c.ellipse(0, 0, W, W, fill="#D39A55")
    c.ellipse(14, 14, W - 14, W - 14, fill="#B8321E")
    _speckle(c, 60, ["#A02818", "#C8462A"], (2, 6), (30, 30, W - 30, W - 30))
    rng = c.rng
    for _ in range(14):  # 溶けたチーズ
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 85)
        x, y = W / 2 + r * math.cos(a), W / 2 + r * math.sin(a)
        s = rng.uniform(14, 26)
        c.ellipse(x - s, y - s * 0.8, x + s, y + s * 0.8, fill="#F3E2B0")
        c.ellipse(x - s * 0.6, y - s * 0.5, x + s * 0.4, y + s * 0.3, fill="#FAF0CE")
        if rng.random() < 0.4:
            c.ellipse(x - 3, y - 2, x + 3, y + 2, fill="#C98A3A")  # 焼き色
    for k in range(6):  # バジル
        a = k * math.pi / 3 + 0.3
        x, y = W / 2 + 60 * math.cos(a), W / 2 + 60 * math.sin(a)
        c.polygon([(x - 10, y), (x, y - 5), (x + 10, y), (x, y + 5)], fill="#2E6B1E")
        c.line([(x - 8, y), (x + 8, y)], "#4E8E2E", 0.8)
    return _tex(c, seed, 0.25)


def pizza_plate() -> Product:
    """丸い平皿のマルゲリータ（直径 250 mm、8 等分）。"""
    pl = (0.29, 0.29, 0.018)
    plate, floor = _ware("Plate", PLATE, pl)
    images = [_pizza_top(7071)]
    pd = 0.25
    parts: list[Part] = [plate,
                         _food("Pizza", "cylinder", (pd, pd, 0.008), (0, 0, floor + 0.004), "#B8321E",
                               faces={"top": 0}),
                         _food("Crust", "torus", (pd + 0.004, pd + 0.004, 0.016), (0, 0, floor + 0.008), "#C98A45")]
    for k in range(4):  # 切れ目（8 等分）
        parts.append(_food(f"Cut{k}", "box", (pd - 0.02, 0.0015, 0.0008), (0, 0, floor + 0.0084), "#7A2A14",
                           rotation=(0, 0, 45 * k)))
    H = max(pl[2], floor + 0.016)
    return Product(slug="pizza_plate", name="マルゲリータ ピザ", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), pl[0]), mass_kg=0.95, material="ceramic",
                   description="形はイタリアン・ファミリーレストランの一般的なピザ（直径 290 mm の平皿に、直径 250 mm の"
                               "マルゲリータを 8 等分）で、寸法・質量（皿込み）は代表値。ピザの上面は描いた模様。",
                   tags=["ピザ", "マルゲリータ", "イタリアン", "ファミレス", "料理", "pizza", "margherita pizza",
                         "plated dish"],
                   photos=[], colors=Colors(label_base="#B8321E"), images=images, parts=parts)


# ---------------------------------------------------------------- サラダ


def salad_bowl() -> Product:
    """白いボウルのグリーンサラダ（ミニトマト）。

    写真: salad（CC0。盛った野菜の山に合成）
    """
    D, h = 0.20, 0.075
    bowl, _ = _ware("Bowl", BOWL, (D, D, h))
    zb = 0.50
    sd = 2 * _inner(BOWL, zb) * D / 2 * 0.97
    images = [_food_photo("salad", 150, 150, (0.12, 0.08, 0.88, 0.92), 7081)]
    z0 = zb * h
    parts: list[Part] = [bowl, _food("Salad", "bun", (sd, sd, 0.060), (0, 0, z0 + 0.030), "#7CB342",
                                     faces={"top": 0})]
    for k, (x, y) in enumerate(((0.035, 0.022), (-0.030, 0.034), (0.020, -0.038), (-0.042, -0.018))):
        r2 = x * x + y * y
        zt = z0 + 0.060 * math.sqrt(max(0.0, 1 - r2 / (sd / 2) ** 2)) - 0.004
        parts.append(_food(f"Tomato{k}", "dome", (0.026, 0.026, 0.013), (x, y, zt + 0.0065), "#D84315", "glossy"))
    H = z0 + 0.060
    return Product(slug="salad_bowl", name="グリーンサラダ（ボウル）", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), D), mass_kg=0.6, material="ceramic",
                   description="形はファミリーレストランの一般的なサラダ（口径 200 mm・高さ 75 mm の白いボウルに、葉物・ミニトマトを"
                               "山に盛る）で、寸法・質量（器込み）は代表値。野菜の山は写真、ミニトマトは簡単な形。",
                   tags=["サラダ", "グリーンサラダ", "野菜", "ファミレス", "料理", "salad", "green salad", "salad bowl",
                         "plated dish"],
                   photos=["salad"], colors=Colors(label_base="#7CB342"), images=images, parts=parts)


# ---------------------------------------------------------------- パフェ

# 脚付きのグラス（台・脚・器）。内側は 0.335h の底から縁まで
PARFAIT_GLASS = [[0, 0], [0.80, 0], [0.82, 0.02], [0.30, 0.05], [0.16, 0.10], [0.16, 0.26], [0.48, 0.32],
                 [0.84, 0.60], [1.0, 1.0], [0.96, 1.0], [0.80, 0.61], [0.45, 0.345], [0, 0.335]]


def _layer(z0: float, z1: float, shrink: float = 0.96) -> tuple[list[list[float]], float]:
    """グラスの内側の z0〜z1（高さの割合）を満たす層の断面（revolve の profile）と、その最大の半径の割合。"""
    zs = sorted({z0, z1, *[z for _, z in PARFAIT_GLASS[10:12] if z0 < z < z1]})
    rs = [_inner(PARFAIT_GLASS, z) * shrink for z in zs]
    rmax = max(rs)
    prof = [[0, 0]] + [[r / rmax, (z - z0) / (z1 - z0)] for r, z in zip(rs, zs)] + [[0, 1]]
    return prof, rmax


def parfait_glass() -> Product:
    """背の高いパフェ（脚付きのグラスにコーンフレーク・アイス・いちごのソース・生クリームの層、上にいちごとウエハース）。"""
    D, h = 0.090, 0.200
    glass = Part("Glass", "revolve", [D, D, h], [0, 0, h / 2], color="#EAF2F5", finish="glass", material="glass",
                 profile=PARFAIT_GLASS, thin_walled=True)
    parts: list[Part] = [glass]
    for name, z0, z1, color in (("Flakes", 0.345, 0.48, "#D9A54A"), ("Vanilla", 0.48, 0.62, "#F6EEDC"),
                                ("Berry", 0.62, 0.72, "#C0283A"), ("Cream", 0.72, 0.985, "#FBF7EE")):
        prof, rmax = _layer(z0, z1)
        d = 2 * rmax * D / 2
        parts.append(Part(name, "revolve", [d, d, (z1 - z0) * h], [0, 0, (z0 + z1) / 2 * h], color=color,
                          finish="matte", collision=False, material="food", profile=prof))
    top = 0.985 * h
    parts += [_food("Whip", "pointed_dome", (0.070, 0.070, 0.045), (0, 0, top + 0.0225), "#FFFDF6"),
              _food("Scoop", "dome", (0.040, 0.040, 0.028), (-0.018, 0.012, top + 0.012), "#F3E6C8")]
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = 0.024 * math.cos(a), 0.024 * math.sin(a)
        parts.append(_food(f"Strawberry{k}", "fruit", (0.026, 0.026, 0.032), (x, y, top + 0.026), "#C8102E",
                           "glossy", rotation=(180 + 20 * math.sin(a), 20 * math.cos(a), 0)))
    parts += [_food("Wafer", "box", (0.014, 0.004, 0.060), (0.014, 0.020, top + 0.045), "#E2B66A",
                    rotation=(-15, 15, 0)),
              _food("Mint", "leaf", (0.020, 0.012, 0.004), (-0.004, -0.010, top + 0.046), "#3C8C3A")]
    H = top + 0.045 + 0.032
    return Product(slug="parfait_glass", name="いちごのパフェ", shape_class="assembly", category="food",
                   dims=Dimensions(round(H, 4), D), mass_kg=0.55, material="glass",
                   description="形はファミリーレストラン・喫茶店の一般的なパフェ（口径 90 mm・高さ 200 mm の脚付きのグラスに、"
                               "コーンフレーク・バニラアイス・いちごのソース・生クリームの層、上にホイップ・いちご・ウエハース・ミント）で、"
                               "寸法・質量（グラス込み）は代表値。",
                   tags=["パフェ", "いちごパフェ", "デザート", "スイーツ", "ファミレス", "parfait", "strawberry parfait",
                         "dessert", "sundae"],
                   photos=[], colors=Colors(label_base="#FBF7EE"), images=[], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    hamburg_steak_set, omurice, meat_sauce_pasta, curry_rice, ramen_bowl, karaage_set, gyoza_plate, pizza_plate,
    salad_bowl, parfait_glass)}
