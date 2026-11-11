"""架空の商品のデザイン: 店舗の設備（レジまわりのカウンター機器）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の製品の一般的な値にする。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .paint import Canvas, finish, trim_safe
from .products import INK, LAMP_TILT, WARM_WHITE, _box, _cyl, _lamp

STEEL, STEEL_DARK = "#C4C7CB", "#9EA2A8"
GLASS = "#F2F6F8"
STICK = "#E3C89A"


def _metal(c: Canvas, seed: int):
    return trim_safe(finish(c.array(), "metal", seed, 0.4))


FOOD = ("Karaage", "Korokke", "Frank", "Chicken", "CornDog", "SkewerMeat", "Bun", "Daikon", "Egg", "Chikuwa",
        "Konnyaku", "Ganmo", "Hanpen", "Kinchaku", "Suji")


def _mark_food(parts: list[Part]) -> list[Part]:
    """中に並べた食品（からあげ・中華まん・おでんの具など）の素材を food、おでんのつゆを liquid にする（意味ラベル用）。"""
    for p in parts:
        if p.name == "Broth":
            p.material = "liquid"
        elif p.name.startswith(FOOD) and "Stick" not in p.name:
            p.material = "food"
    return parts


def _lying(name, d, length, center, color, finish_="plastic", axis="x") -> Part:
    """寝かせた円柱（軸が X または Y）。"""
    rot = [0, 90, 0] if axis == "x" else [90, 0, 0]
    return Part(name, "cylinder", [d, d, length], list(center), rot, color=color, finish=finish_, collision=False)


def _dome(name, R, h, base_z, xy, color, finish_="plastic", shape="dome", collision=False) -> Part:
    """底が平らな山形（dome は半楕円体、bun は肩の張ったまんじゅう形）。base_z は底の高さ。"""
    return Part(name, shape, [2 * R, 2 * R, h], [xy[0], xy[1], base_z + h / 2], color=color, finish=finish_,
                collision=collision)


# ---------------------------------------------------------------- ホットスナックの保温ケース


def hot_snack_case() -> Product:
    W, D = 0.60, 0.45
    bh, top_z = 0.14, 0.54
    red = "#C8321E"
    w, h = W * 1000, bh * 1000
    c = Canvas(w, h, 1600 / w, STEEL, 2801)
    c.gradient(0, 0, w, h, "#D5D8DC", "#B4B8BD")
    c.rect(10, 8, 190, h - 8, fill=red, radius=6)
    c.text(100, 48, "ホット", 26, "#FFFFFF", 900)
    c.text(100, 84, "スナック", 26, "#FFFFFF", 900)
    c.text(100, 114, "できたて", 11, "#FFE7A0", 800)
    menu = [("からあげ 5個入", "238円"), ("コロッケ", "98円"), ("フランク", "150円"),
            ("フライドチキン", "220円"), ("アメリカンドッグ", "130円"), ("からあげ棒", "160円")]
    for i, (n, p) in enumerate(menu):
        x0 = 205 + (i % 2) * 195
        y0 = 14 + (i // 2) * 40
        c.rect(x0, y0, x0 + 185, y0 + 34, fill="#FFFFFF", outline="#9EA2A8", width=0.8, radius=4)
        c.text(x0 + 8, y0 + 17, n, 11, INK, 800, anchor="lm")
        c.text(x0 + 178, y0 + 17, p, 13, red, 900, anchor="rm")
    front = _metal(c, 2801)

    gh = top_z - bh
    slant = 0.065  # 前面ガラスの傾き（下端から上端までの奥行き方向のずれ）
    yf = -D / 2 + 0.01  # 前面ガラスの下端
    L = math.hypot(gh, slant)
    th = -math.degrees(math.atan2(slant, gh))  # 上を奥へ倒す（X 軸まわりに −）
    parts = [_box("Base", (W, D, bh), (0, 0, bh / 2), STEEL, "metal", {"front": 0}),
             _box("FrontGlass", (W - 0.03, 0.006, L), (0, yf + slant / 2, bh + gh / 2), GLASS, "glass", rotation=[th, 0, 0]),
             _box("SideGlassLeft", (0.006, D - 0.04, gh), (-W / 2 + 0.006, 0.01, bh + gh / 2), GLASS, "glass"),
             _box("SideGlassRight", (0.006, D - 0.04, gh), (W / 2 - 0.006, 0.01, bh + gh / 2), GLASS, "glass"),
             _box("BackDoorLeft", (0.29, 0.006, gh - 0.02), (-0.142, D / 2 - 0.012, bh + gh / 2), GLASS, "glass"),
             _box("BackDoorRight", (0.29, 0.006, gh - 0.02), (0.142, D / 2 - 0.022, bh + gh / 2), GLASS, "glass"),
             _box("BackDoorHandleLeft", (0.012, 0.012, 0.08), (-0.03, D / 2 - 0.008, bh + gh / 2), STEEL_DARK, "metal",
                  collision=False),
             _box("BackDoorHandleRight", (0.012, 0.012, 0.08), (0.03, D / 2 - 0.018, bh + gh / 2), STEEL_DARK,
                  "metal", collision=False),
             _box("Top", (W, D, 0.03), (0, 0, top_z + 0.015), STEEL, "metal"),
]
    # 照明：天板の裏のランプと、網棚の前寄りの下のランプ（下の段を照らす）
    lamp, lux = _lamp("LightBar", (0.50, 0.04, 0.012), (0, 0.0, top_z - 0.006), "#FFF4D6", 2500.0, WARM_WHITE)
    parts.append(lamp)
    lights = [lux]
    for k, sx in enumerate((-1, 1)):  # 奥の柱
        parts.append(_box(f"Post{k}", (0.02, 0.02, gh), (sx * (W / 2 - 0.01), D / 2 - 0.01, bh + gh / 2),
                          STEEL_DARK, "metal", collision=False))
    for k, sx in enumerate((-1, 1)):  # 前の柱（ガラスに沿って傾ける）
        parts.append(_box(f"FrontPost{k}", (0.02, 0.02, L), (sx * (W / 2 - 0.01), yf + slant / 2, bh + gh / 2), STEEL_DARK,
                          "metal", rotation=[th, 0, 0], collision=False))

    # 段（下の床 + 網棚 2 段）。各段に 2 枚のトレー
    levels = [bh, 0.27, 0.40]
    tray_z = []
    for i, z in enumerate(levels):
        if i > 0:
            parts.append(_box(f"WireShelf{i}", (W - 0.05, 0.34, 0.006), (0, 0.03, z), STEEL_DARK, "metal", collision=False))
            lamp, lux = _lamp(f"ShelfLight{i}", (W - 0.08, 0.02, 0.008), (0, -0.12, z - 0.007), "#FFF4D6", 6000.0,
                              WARM_WHITE, tilt=LAMP_TILT)
            parts.append(lamp)
            lights.append(lux)
        for j, x in enumerate((-0.135, 0.135)):
            parts.append(_box(f"Tray{i}{j}", (0.25, 0.30, 0.02), (x, 0.035, z + 0.013), "#D9DCDF", "metal",
                              collision=False))
        tray_z.append(z + 0.023)
    brown, beige, sausage, batter, chicken = "#9E5A22", "#D4A055", "#B4503A", "#D69A45", "#B0702E"
    z0 = tray_z[0]
    for k in range(8):  # からあげ
        x, y = -0.205 + (k % 4) * 0.045, 0.0 + (k // 4) * 0.06
        parts.append(_cyl(f"Karaage{k}", (0.04, 0.036, 0.03), (x, y, z0 + 0.015), brown, "plastic", collision=False))
        parts.append(_cyl(f"KaraageTop{k}", (0.028, 0.026, 0.008), (x + 0.003, y, z0 + 0.034), brown, "plastic",
                          collision=False))
    for k in range(4):  # コロッケ
        x, y = 0.09 + (k % 2) * 0.09, 0.0 + (k // 2) * 0.10
        parts.append(_cyl(f"Korokke{k}", (0.08, 0.055, 0.022), (x, y, z0 + 0.011), beige, "plastic", collision=False))
    z1 = tray_z[1]
    for k in range(5):  # フランク
        parts.append(_lying(f"Frank{k}", 0.022, 0.13, (-0.135, -0.05 + k * 0.045, z1 + 0.011), sausage))
    for k in range(4):  # フライドチキン
        x, y = 0.09 + (k % 2) * 0.09, -0.01 + (k // 2) * 0.10
        parts.append(_box(f"Chicken{k}", (0.075, 0.055, 0.04), (x, y, z1 + 0.02), chicken, "plastic",
                          rotation=[0, 0, 20 * (k % 2 * 2 - 1)], collision=False))
    z2 = tray_z[2]
    for k in range(4):  # アメリカンドッグ
        y = -0.03 + k * 0.05
        parts.append(_lying(f"CornDog{k}", 0.036, 0.10, (-0.16, y, z2 + 0.018), batter))
        parts.append(_lying(f"CornDogStick{k}", 0.006, 0.07, (-0.075, y, z2 + 0.018), STICK))
    for k in range(4):  # からあげ棒
        y = -0.03 + k * 0.05
        parts.append(_lying(f"SkewerStick{k}", 0.005, 0.20, (0.135, y, z2 + 0.016), STICK))
        for j in range(3):
            parts.append(_cyl(f"SkewerMeat{k}{j}", (0.032, 0.032, 0.028), (0.085 + j * 0.035, y, z2 + 0.016), brown,
                              "plastic", collision=False))
    return Product(slug="hot_snack_case", name="ホットスナック 保温ケース", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.57, W, depth=D), mass_kg=35.0, static=True, material="steel",
                   description="形はコンビニのレジ横に置く一般的なホットスナックの保温ケース（ステンレスの台、前が斜めのガラス、"
                               "店員側に引き戸、網棚 2 段）で、寸法・質量は代表値。中の揚げ物は簡単な形で表し、メニューと価格は架空。",
                   tags=["ホットスナック", "保温ケース", "ホットショーケース", "揚げ物", "レジ横", "店舗設備", "hot snack",
                         "food warmer", "hot showcase"], photos=[], colors=Colors(label_base=STEEL), images=[front],
                   parts=_mark_food(parts), lights=lights)


# ---------------------------------------------------------------- 中華まんスチーマー


def bun_steamer() -> Product:
    W, D = 0.50, 0.45
    bh, gh, th = 0.16, 0.42, 0.05
    red, orange = "#C8321E", "#E8742A"
    w, h = W * 1000, bh * 1000
    c = Canvas(w, h, 1600 / w, red, 2811)
    c.gradient(0, 0, w, h, "#D63A22", "#A82414")
    c.text(110, 56, "中華まん", 34, "#FFFFFF", 900)
    c.text(110, 94, "ふっくら蒸したて", 13, "#FFE7A0", 800)
    c.rect(20, 116, 200, 146, fill="#2A2C30", radius=4)  # 水位の窓
    c.rect(26, 126, 120, 138, fill="#6FB7E8", radius=2)
    c.text(160, 132, "水位", 10, "#FFFFFF", 700)
    menu = [("肉まん", "150円"), ("あんまん", "130円"), ("ピザまん", "150円"), ("カレーまん", "150円")]
    for i, (n, p) in enumerate(menu):
        y0 = 12 + i * 36
        c.rect(225, y0, w - 14, y0 + 31, fill="#FFF8E8", radius=5)
        c.text(238, y0 + 15.5, n, 13, INK, 900, anchor="lm")
        c.text(w - 24, y0 + 15.5, p, 14, red, 900, anchor="rm")
    front = _metal(c, 2811)
    sw, sh = W * 1000, th * 1000
    s = Canvas(sw, sh, 1600 / sw, orange, 2812)
    s.gradient(0, 0, sw, sh, "#F08A3A", "#D2601C")
    s.text(sw / 2, sh / 2, "ほかほか  中華まん  あります", 17, "#FFFFFF", 900)
    sign = _metal(s, 2812)

    z_top = bh + gh
    parts = [_box("Base", (W, D, bh), (0, 0, bh / 2), STEEL, "metal", {"front": 0}),
             _box("SideGlassLeft", (0.006, D - 0.04, gh), (-W / 2 + 0.006, 0, bh + gh / 2), GLASS, "glass"),
             _box("SideGlassRight", (0.006, D - 0.04, gh), (W / 2 - 0.006, 0, bh + gh / 2), GLASS, "glass"),
             _box("FrontDoorLeft", (0.235, 0.006, gh - 0.02), (-0.115, -D / 2 + 0.012, bh + gh / 2), GLASS, "glass"),
             _box("FrontDoorRight", (0.235, 0.006, gh - 0.02), (0.115, -D / 2 + 0.022, bh + gh / 2), GLASS, "glass"),
             _box("BackGlass", (W - 0.04, 0.006, gh - 0.02), (0, D / 2 - 0.012, bh + gh / 2), GLASS, "glass"),
             _box("FrontDoorHandleLeft", (0.010, 0.010, 0.07), (-0.02, -D / 2 + 0.006, bh + gh / 2), STEEL_DARK, "metal",
                  collision=False),
             _box("FrontDoorHandleRight", (0.010, 0.010, 0.07), (0.02, -D / 2 + 0.016, bh + gh / 2), STEEL_DARK, "metal",
                  collision=False),
             _box("Top", (W, D, th), (0, 0, z_top + th / 2), orange, "plastic", {"front": 1})]
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_box(f"Post{k}", (0.02, 0.02, gh), (sx * (W / 2 - 0.01), sy * (D / 2 - 0.01), bh + gh / 2), STEEL_DARK,
                          "metal", collision=False))
    tiers = [bh + 0.012, bh + 0.15, bh + 0.29]
    # 照明：天板の裏のランプと、上の 2 段の棚の前寄りの下のランプ（下の段を照らす）
    lamp, lux = _lamp("TopLight", (W - 0.08, 0.03, 0.008), (0, -0.12, z_top - 0.004), "#FFF4D6", 4000.0,
                      WARM_WHITE)
    parts.append(lamp)
    lights = [lux]
    for i, z in enumerate(tiers[1:], 1):
        lamp, lux = _lamp(f"ShelfLight{i}", (W - 0.08, 0.02, 0.008), (0, -0.14, z - 0.010), "#FFF4D6", 4000.0,
                          WARM_WHITE, tilt=LAMP_TILT)
        parts.append(lamp)
        lights.append(lux)
    pizza, curry = "#E8A15A", "#E6C05A"
    kinds = [  # 段ごと: (色, 半径, 高さ, 頂部の飾り)。中華まんは直径 9〜10cm・高さ 5〜6cm くらい
        [("#F0E9DD", 0.046, 0.050, "#7A3E2A")] * 6,  # あんまん（頂に印）
        [(pizza, 0.048, 0.044, None)] * 3 + [(curry, 0.046, 0.050, None)] * 3,  # ピザまん（平たい）・カレーまん
        [("#F5F1E8", 0.048, 0.054, "twist")] * 6,  # 肉まん（ひだを寄せてひねった頂）
    ]
    for i, z in enumerate(tiers):
        parts.append(_box(f"Shelf{i}", (W - 0.05, D - 0.07, 0.006), (0, 0, z - 0.003), "#C9CCD0", "metal",
                          collision=False))
        for k in range(6):
            x, y = -0.15 + (k % 3) * 0.15, -0.08 + (k // 3) * 0.16
            col, R, h, deco = kinds[i][k]
            f = 1 + 0.03 * math.sin(7 * i + 3 * k)  # 手作りらしく大きさを少しずつ変える
            R, h = R * f, h * f
            parts.append(_dome(f"Bun{i}{k}", R, h, z, (x, y), col, shape="bun"))
            if deco == "twist":  # 頂のひねり（とがった小山を少し埋める）と、そこへ寄るひだ
                parts.append(_dome(f"BunTwist{i}{k}", 0.013, 0.014, z + h - 0.006, (x, y), "#ECE5D8",
                                   shape="pointed_dome"))
                for j in range(8):
                    a = 2 * math.pi * j / 8 + 0.3 * k
                    rr = 0.36 * R  # ひだの中心の半径。bun の断面から、その高さと面の傾きを求める
                    zz = h * (1 - (rr / R) ** 2.6) ** (1 / 2.6)
                    tilt = math.degrees(math.atan(h / R * (rr / R) ** 1.6 * (1 - (rr / R) ** 2.6) ** (1 / 2.6 - 1)))
                    parts.append(_box(f"BunPleat{i}{k}{j}", (0.024, 0.004, 0.003),
                                      (x + rr * math.cos(a), y + rr * math.sin(a), z + zz - 0.0012), "#EAE3D6",
                                      "plastic", rotation=[0, tilt, math.degrees(a)], collision=False))
            elif deco:
                parts.append(_cyl(f"BunMark{i}{k}", (0.016, 0.016, 0.002), (x, y, z + h - 0.0002), deco, "plastic",
                                  collision=False))
    return Product(slug="bun_steamer", name="中華まんスチーマー 3段", shape_class="assembly", category="fixture",
                   dims=Dimensions(round(z_top + th, 4), W, depth=D), mass_kg=25.0, static=True, material="steel",
                   description="形はコンビニのレジ横に置く一般的な中華まんのスチーマー（水タンク付きの台、ガラスの 3 段、"
                               "前に引き戸）で、寸法・質量は代表値。中華まんはまんじゅう形の簡単な形で、メニューと価格は架空。",
                   tags=["中華まん", "スチーマー", "肉まん", "あんまん", "レジ横", "店舗設備", "steamer", "bun steamer",
                         "steamed bun"], photos=[], colors=Colors(label_base=STEEL), images=[front, sign],
                   parts=_mark_food(parts), lights=lights)


# ---------------------------------------------------------------- おでん什器


def oden_warmer() -> Product:
    W, D = 0.60, 0.40
    bh, ph = 0.10, 0.12
    w, h = W * 1000, bh * 1000
    c = Canvas(w, h, 1600 / w, "#2B3550", 2821)
    c.gradient(0, 0, w, h, "#33406A", "#1E2640")
    c.ellipse(20, 10, 160, 90, fill="#C8321E")  # ちょうちん風
    c.text(90, 50, "おでん", 30, "#FFFFFF", 900)
    menu = [("大根", "100円"), ("たまご", "100円"), ("ちくわ", "90円"), ("こんにゃく", "80円"),
            ("がんも", "120円"), ("はんぺん", "100円"), ("もち巾着", "130円"), ("牛すじ", "150円")]
    for i, (n, p) in enumerate(menu):
        x0 = 175 + (i % 4) * 104
        y0 = 12 + (i // 4) * 40
        c.rect(x0, y0, x0 + 98, y0 + 34, fill="#FFF8E8", radius=4)
        c.text(x0 + 49, y0 + 11, n, 10, INK, 900)
        c.text(x0 + 49, y0 + 25, p, 11, "#C8321E", 900)
    front = _metal(c, 2821)

    t = 0.01
    zw = bh + ph / 2
    b = bh + ph - 0.024  # 汁の面
    parts = [_box("Base", (W, D, bh), (0, 0, bh / 2), STEEL, "metal", {"front": 0}),
             _box("WallFront", (W, t, ph), (0, -D / 2 + t / 2, zw), STEEL, "metal"),
             _box("WallBack", (W, t, ph), (0, D / 2 - t / 2, zw), STEEL, "metal"),
             _box("WallLeft", (t, D - 2 * t, ph), (-W / 2 + t / 2, 0, zw), STEEL, "metal"),
             _box("WallRight", (t, D - 2 * t, ph), (W / 2 - t / 2, 0, zw), STEEL, "metal"),
             _box("Broth", (W - 2 * t, D - 2 * t, b - bh), (0, 0, (bh + b) / 2), "#A8722F", "glossy")]
    dz = bh + (ph - 0.012) / 2  # 仕切り（4 × 2 の 8 区画）
    parts.append(_box("DividerX", (W - 2 * t, 0.004, ph - 0.012), (0, 0, dz), STEEL_DARK, "metal", collision=False))
    for k, x in enumerate((-0.145, 0.0, 0.145)):
        parts.append(_box(f"DividerY{k}", (0.004, D - 2 * t, ph - 0.012), (x, 0, dz), STEEL_DARK, "metal",
                          collision=False))
    cx = [-0.2175, -0.0725, 0.0725, 0.2175]
    cy = [-0.095, 0.095]
    for k, (dx, dy) in enumerate(((-0.03, -0.035), (0.03, 0.0), (-0.025, 0.04))):  # 大根
        parts.append(_cyl(f"Daikon{k}", (0.06, 0.06, 0.03), (cx[0] + dx, cy[0] + dy, b), "#E2C48A", "plastic",
                          collision=False))
    for k, (dx, dy) in enumerate(((-0.035, -0.04), (0.03, -0.02), (-0.02, 0.035), (0.035, 0.045))):  # たまご
        x, y = cx[1] + dx, cy[0] + dy
        parts += [_cyl(f"Egg{k}", (0.042, 0.042, 0.014), (x, y, b + 0.002), "#C8954E", "glossy", collision=False),
                  _cyl(f"EggTop{k}", (0.03, 0.03, 0.008), (x, y, b + 0.012), "#C8954E", "glossy", collision=False)]
    for k in range(3):  # ちくわ
        parts.append(_lying(f"Chikuwa{k}", 0.026, 0.11, (cx[2], cy[0] - 0.05 + k * 0.05, b + 0.004), "#C98A45"))
    for k, (dx, dy, r) in enumerate(((-0.03, -0.04, 20), (0.03, -0.01, -15), (-0.02, 0.04, 40))):  # こんにゃく
        parts.append(_box(f"Konnyaku{k}", (0.05, 0.05, 0.014), (cx[3] + dx, cy[0] + dy, b + 0.003), "#6B6660",
                          "plastic", rotation=[0, 0, r], collision=False))
    for k, (dx, dy) in enumerate(((-0.03, -0.035), (0.03, 0.0), (-0.02, 0.045))):  # がんも
        parts.append(_cyl(f"Ganmo{k}", (0.056, 0.056, 0.026), (cx[0] + dx, cy[1] + dy, b), "#B07A38", "plastic",
                          collision=False))
    for k, (dx, dy, r) in enumerate(((-0.02, -0.035, 10), (0.02, 0.04, -12))):  # はんぺん
        parts.append(_box(f"Hanpen{k}", (0.07, 0.07, 0.016), (cx[1] + dx, cy[1] + dy, b + 0.006), "#F2EFE6", "plastic",
                          rotation=[0, 0, r], collision=False))
    for k, (dx, dy) in enumerate(((-0.03, -0.035), (0.03, 0.0), (-0.02, 0.045))):  # もち巾着
        x, y = cx[2] + dx, cy[1] + dy
        parts += [_cyl(f"Kinchaku{k}", (0.05, 0.05, 0.03), (x, y, b), "#D2A86E", "plastic", collision=False),
                  _cyl(f"KinchakuKnot{k}", (0.016, 0.016, 0.012), (x, y, b + 0.018), "#B88A50", "plastic",
                       collision=False)]
    for k in range(3):  # 牛すじ（串）
        y = cy[1] - 0.05 + k * 0.05
        parts.append(_lying(f"SujiStick{k}", 0.004, 0.13, (cx[3], y, b + 0.006), STICK))
        for j in range(3):
            parts.append(_box(f"Suji{k}{j}", (0.026, 0.024, 0.02), (cx[3] - 0.035 + j * 0.033, y, b + 0.006), "#7A4A2A",
                              "plastic", rotation=[0, 0, 15 * (j - 1)], collision=False))
    return Product(slug="oden_warmer", name="おでん什器 8区画", shape_class="assembly", category="fixture",
                   dims=Dimensions(bh + ph, W, depth=D), mass_kg=12.0, static=True, material="steel",
                   description="形はコンビニのレジ横に置く一般的なおでんの保温鍋（ヒーター付きの台にステンレスの角鍋、仕切りで 8 区画）で、"
                               "寸法・質量は代表値。具は簡単な形で表し、メニューと価格は架空。",
                   tags=["おでん", "おでん鍋", "保温鍋", "レジ横", "店舗設備", "oden", "food warmer"], photos=[],
                   colors=Colors(label_base=STEEL), images=[front], parts=_mark_food(parts))


# ---------------------------------------------------------------- 給湯台（電気ポット）


def hot_water_dispenser() -> Product:
    W, D, ch = 0.45, 0.45, 0.85
    blue, red = "#1F6F9C", "#C8321E"
    w, h = W * 1000, ch * 1000
    c = Canvas(w, h, 1600 / h, "#ECEDEE", 2831)
    c.gradient(0, 0, w, h, "#F2F3F4", "#D8DADD")
    c.rect(0, 0, w, 120, fill=blue)
    c.text(w / 2, 48, "お湯はこちら", 40, "#FFFFFF", 900)
    c.text(w / 2, 96, "（カップめん用）", 22, "#FFFFFF", 800)
    c.polygon([(155, 170), (295, 170), (280, 300), (170, 300)], fill="#F6D24A", outline="#8A6A10")  # カップめんの絵
    c.rect(150, 160, 300, 176, fill="#FFFFFF", outline="#8A6A10", width=1.2, radius=3)
    c.text(225, 240, "めん", 22, "#8A3A10", 900)
    for k in range(3):  # 湯気
        x = 195 + k * 30
        c.line([(x, 152), (x - 6, 142), (x, 132), (x - 6, 122)], "#9AA6B0", 2.5)
    c.text(w / 2, 335, "フタを半分あけて", 18, INK, 800)
    c.text(w / 2, 362, "線まで注いでください", 18, INK, 800)
    c.rect(30, 395, w - 30, 495, fill="#FFF1E8", outline=red, width=3, radius=8)
    c.text(w / 2, 428, "やけどに注意", 30, red, 900)
    c.text(w / 2, 470, "熱湯が出ます。お子さまだけで使わないでください", 11, INK, 700)
    c.rect(20, 520, w - 20, h - 40, outline="#B5B8BC", width=2, radius=6)  # 下の物入れの扉
    c.line([(w / 2, 520), (w / 2, h - 40)], "#B5B8BC", 2)
    c.rect(w / 2 - 30, 600, w / 2 - 14, 680, fill="#BFC2C6", radius=4)
    c.rect(w / 2 + 14, 600, w / 2 + 30, 680, fill="#BFC2C6", radius=4)
    c.text(w / 2, h - 18, NOTICE, 10, "#8A8E94", 500)
    sign = _metal(c, 2831)
    pw, ph = 120.0, 60.0
    p = Canvas(pw, ph, 1200 / pw, "#2A2C30", 2832)
    p.gradient(0, 0, pw, ph, "#34373C", "#202226")
    p.rect(8, 10, 54, 50, fill="#3C7DD0", radius=6)
    p.text(31, 30, "給湯", 12, "#FFFFFF", 900)
    p.rect(66, 10, 112, 50, fill="#5A5E64", radius=6)
    p.text(89, 24, "ロック", 8, "#FFFFFF", 800)
    p.text(89, 38, "解除", 8, "#FFFFFF", 800)
    panel = trim_safe(finish(p.array(), "screen", 2832, 0.4))

    pot_r, body_h = 0.11, 0.30
    py = 0.04  # ポットの中心（少し奥）
    z = ch + 0.02
    parts = [_box("Cabinet", (W, D, ch), (0, 0, ch / 2), "#E4E5E7", "plastic", {"front": 0}),
             _box("TopBoard", (W + 0.01, D + 0.01, 0.02), (0, 0, ch + 0.01), "#B9A27E", "plastic"),
             _cyl("PotBase", (2 * pot_r + 0.01, 2 * pot_r + 0.01, 0.02), (0, py, z + 0.01), "#3A3C40", "plastic"),
             _cyl("PotBody", (2 * pot_r, 2 * pot_r, body_h), (0, py, z + 0.02 + body_h / 2), STEEL, "metal")]
    zt = z + 0.02 + body_h
    parts.append(_dome("PotLid", pot_r, 0.05, zt, (0, py), "#F2F2F0", collision=True))
    parts += [_box("Handle", (0.03, 0.17, 0.016), (0, py, zt + 0.07), "#3A3C40", "plastic"),
              _box("HandlePostFront", (0.02, 0.016, 0.03), (0, py - 0.077, zt + 0.05), "#3A3C40", "plastic",
                   collision=False),
              _box("HandlePostBack", (0.02, 0.016, 0.03), (0, py + 0.077, zt + 0.05), "#3A3C40", "plastic",
                   collision=False),
              _box("ButtonPanel", (0.12, 0.03, 0.06), (0, py - pot_r - 0.005, zt - 0.02), "#2A2C30", "glossy",
                   {"front": 1}, [-20, 0, 0]),
              _box("Spout", (0.04, 0.06, 0.03), (0, py - pot_r - 0.02, zt - 0.075), "#3A3C40", "plastic"),
              _cyl("Nozzle", (0.016, 0.016, 0.03), (0, py - pot_r - 0.04, zt - 0.105), "#2A2C30", "plastic",
                   collision=False),
              _box("DripTray", (0.16, 0.14, 0.015), (0, py - pot_r - 0.04, z + 0.0075), "#5A5E64", "metal")]
    for k in range(5):  # 受け皿のすのこ
        parts.append(_box(f"DripSlat{k}", (0.15, 0.006, 0.003), (0, py - pot_r - 0.095 + k * 0.027, z + 0.0165),
                          "#2A2C30", "metal", collision=False))
    return Product(slug="hot_water_dispenser", name="給湯台 電気ポット付き（カップめん用）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(zt + 0.078, 4), W + 0.01, depth=D + 0.01), mass_kg=28.0,
                   static=True, material="steel",
                   description="形はコンビニの電子レンジの横に置く一般的な給湯台（物入れ付きの台に、5 L ほどの電気ポットと受け皿）で、"
                               "寸法・質量は代表値。表示は架空。",
                   tags=["給湯", "電気ポット", "お湯", "カップめん", "店舗設備", "hot water dispenser", "electric pot",
                         "air pot"], photos=[], colors=Colors(label_base="#E4E5E7"), images=[sign, panel], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (hot_snack_case, bun_steamer, oden_warmer, hot_water_dispenser)}
