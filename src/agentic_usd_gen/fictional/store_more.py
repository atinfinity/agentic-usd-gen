"""架空の商品のデザイン: 店舗の什器（売場・レジまわりの設備の追加分）。

products.py・store_floor.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
形・部品構成は Wikimedia Commons の CC0 / パブリックドメインの写真を参考にした（各関数の docstring）。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Joint, Part
from .base import NOTICE, Product
from .conv_snacks import atarime_hang, beef_jerky_hang, dried_squid_hang, hung_bag_parts
from .paint import Canvas, finish, trim_safe
from .products import COOL_WHITE, INK, WARM_WHITE, _box, _lamp

STEEL, STEEL_DARK = "#C4C7CB", "#9EA2A8"
CHROME = "#D4D7DB"
GLASS = "#F2F6F8"
TEAL = "#1E8C8C"


def _metal(c: Canvas, seed: int):
    return trim_safe(finish(c.array(), "metal", seed, 0.4))


def _link(parts: list[Part], prefix: str, link: str) -> None:
    """名前が prefix で始まる部品を 1 つの可動部（link）にまとめる。"""
    for p in parts:
        if p.name.startswith(prefix):
            p.link = link


def _rod(name, p0, p1, d, color, finish_="metal", collision=False) -> Part:
    """p0 から p1 への丸棒（X 方向か、YZ 面内）。"""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    if abs(x1 - x0) > 1e-9:  # X 方向（Y 軸まわりに 90°）
        rot = [0.0, 90.0, 0.0]
    else:  # YZ 面内：Z 軸を -Y へ倒す向きが正（X 軸まわり）
        rot = [math.degrees(math.atan2(-(y1 - y0), z1 - z0)), 0.0, 0.0]
    return Part(name=name, shape="cylinder", size=[d, d, math.dist(p0, p1)],
                center=[(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], rotation=rot, color=color, finish=finish_,
                collision=collision)


# ---------------------------------------------------------------- ホットドリンク保温ケース


def hot_drink_warmer() -> Product:
    """レジ横の卓上の温蔵庫（棚 3 段・前面ガラス扉 1 枚）。中は空。

    参考: https://commons.wikimedia.org/wiki/File:2020-03-27_10.15.39_세븐일레븐_원주은행점_온장고_음료수.jpg（CC0）
    """
    W, D, H = 0.48, 0.40, 0.60
    body, dark = "#8E9398", "#3A3D42"
    base_h, head_h = 0.09, 0.07
    open_h = H - base_h - head_h
    zc = base_h + open_h / 2
    # 下の操作部（温度表示・スイッチ・吸気口）
    c = Canvas(W * 1000, base_h * 1000, None, body, 3101)
    c.gradient(0, 0, W * 1000, base_h * 1000, "#9AA0A5", "#7E8388")
    c.rect(20, 18, 150, 72, fill="#202226", radius=4)
    c.text(85, 45, "55℃", 30, "#FF6A3A", 800)
    c.text(205, 34, "温度", 13, "#FFFFFF", 700)
    c.rect(185, 48, 225, 66, fill="#5A5E64", radius=3)
    c.ellipse(255, 30, 285, 60, fill="#2A2C30")
    c.ellipse(262, 37, 278, 53, fill="#E05A2A")
    c.text(270, 72, "電源", 10, "#FFFFFF", 700)
    for k in range(10):
        c.rect(320 + k * 14, 22, 328 + k * 14, 70, fill="#5E6268", radius=2)
    ctrl = _metal(c, 3101)
    # 上の看板
    c = Canvas(W * 1000, head_h * 1000, None, "#C2361F", 3102)
    c.gradient(0, 0, W * 1000, head_h * 1000, "#D9472C", "#A82A16")
    c.rect(14, 12, 104, 58, fill="#FFFFFF", radius=8)
    c.text(59, 36, "HOT", 26, "#C2361F", 900)
    c.text(290, 28, "あたたかい飲み物", 26, "#FFFFFF", 900)
    c.text(290, 54, "HOT DRINKS  ・  やけどにご注意ください", 11, "#FFE2D6", 700)
    header = trim_safe(finish(c.array(), "screen", 3102, 0.3))
    parts: list[Part] = [
        _box("Base", (W, D, base_h), (0, 0, base_h / 2), body, "metal", {"front": 0}),
        _box("Top", (W, D, head_h), (0, 0, H - head_h / 2), body, "metal", {"front": 1}),
        _box("Back", (W - 0.02, 0.02, open_h), (0, D / 2 - 0.01, zc), "#D7D9DC", "metal"),
        _box("Floor", (W - 0.04, D - 0.06, 0.006), (0, 0.0, base_h + 0.003), "#B9BDC2", "metal", collision=False),
    ]
    for sx in (-1, 1):
        s = "L" if sx < 0 else "R"
        for sy in (-1, 1):
            parts.append(_box(f"Post{s}{'F' if sy < 0 else 'B'}", (0.02, 0.02, open_h),
                              (sx * (W / 2 - 0.01), sy * (D / 2 - 0.01), zc), body, "metal"))
        parts.append(_box(f"SideGlass{s}", (0.006, D - 0.04, open_h - 0.01), (sx * (W / 2 - 0.006), 0, zc), GLASS,
                          "glass"))
    for i in range(2):  # 網棚 2 枚（床と合わせて 3 段）
        z = base_h + open_h * (i + 1) / 3
        parts += [_box(f"Shelf{i}", (W - 0.04, D - 0.08, 0.008), (0, 0.01, z), "#C9CCD0", "metal"),
                  _box(f"ShelfLip{i}", (W - 0.04, 0.006, 0.02), (0, 0.01 - (D - 0.08) / 2, z + 0.006), "#B8BCC0",
                       "metal", collision=False)]
    lights = []
    for i, z in enumerate((base_h + open_h / 3, base_h + open_h * 2 / 3, H - head_h)):  # 棚の裏と天井の前寄りの照明
        lamp, lux = _lamp(f"Lamp{i}", (W - 0.08, 0.02, 0.006), (0, -0.06, z - 0.008), "#FFF1D8", 6000.0, WARM_WHITE)
        parts.append(lamp)
        lights.append(lux)
    # 扉（右端の蝶番で手前に開く。取っ手は左）
    dw, dh, y = W - 0.01, open_h - 0.006, -D / 2 - 0.006
    hx = -dw / 2 + 0.03
    parts += [
        _box("DoorGlass", (dw - 0.03, 0.006, dh - 0.03), (0, y, zc), GLASS, "glass"),
        _box("DoorFrameL", (0.016, 0.012, dh), (-dw / 2 + 0.008, y, zc), dark, "metal"),
        _box("DoorFrameR", (0.016, 0.012, dh), (dw / 2 - 0.008, y, zc), dark, "metal", collision=False),
        _box("DoorFrameT", (dw, 0.012, 0.016), (0, y, zc + dh / 2 - 0.008), dark, "metal", collision=False),
        _box("DoorFrameB", (dw, 0.012, 0.016), (0, y, zc - dh / 2 + 0.008), dark, "metal", collision=False),
        _box("DoorHandle", (0.014, 0.018, 0.18), (hx, y - 0.022, zc), "#B8BCC0", "metal"),
        _box("DoorHandlePostT", (0.01, 0.02, 0.01), (hx, y - 0.012, zc + 0.075), "#B8BCC0", "metal",
             collision=False),
        _box("DoorHandlePostB", (0.01, 0.02, 0.01), (hx, y - 0.012, zc - 0.075), "#B8BCC0", "metal",
             collision=False),
    ]
    _link(parts, "Door", "DoorLink")
    joints = [Joint(link="DoorLink", anchor=[dw / 2, y, zc], limits=[0.0, 100.0])]
    return Product(slug="hot_drink_warmer", name="ホットドリンク保温ケース（卓上・3段）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D / 2 + 0.037 + D / 2), mass_kg=22.0, static=True,
                   material="steel",
                   description="形はレジ横に置く一般的な卓上の温蔵庫（ガラス扉 1 枚・棚 3 段・中は空）で、寸法・質量は代表値。"
                               "扉（DoorLink）は右端の蝶番で手前に 100° まで開く。上の看板は架空。",
                   tags=["ホットドリンク", "温蔵庫", "保温ケース", "ガラス扉", "店舗什器", "hot drink warmer",
                         "heated beverage cabinet", "glass door"], photos=[], colors=Colors(label_base=body),
                   images=[ctrl, header], parts=parts, joints=joints, lights=lights)


# ---------------------------------------------------------------- たばこ陳列棚


_PACK_WORDS = ("BLEND", "MENTHOL", "FRESH", "ORIGINAL", "SMOOTH", "ROAST", "CLEAR", "AROMA", "SELECT", "NATURAL")
_PACK_COLORS = ("#1F3E7A", "#2E6FB8", "#C9D6E6", "#B0242A", "#E8E4D8", "#1F6E4A", "#5BB8A0", "#3A3A3E",
                "#D9A52E", "#7A2C5E", "#F2F2F2", "#8BA6C4")
_PACK_W = 55.0  # 箱の幅 [mm]


def _pack_row(seed: int, n: int, w_mm: float, h_mm: float):
    """箱入りのたばこを正面から並べた絵（架空のデザイン。銘柄名の代わりに一般的な語と数字）。"""
    c = Canvas(w_mm, h_mm, None, "#F4F6F8", seed)
    c.gradient(0, 0, w_mm, h_mm, "#FAFBFC", "#E2E5E8")
    rng = c.rng
    pw, ph = _PACK_W, h_mm - 2
    gap = (w_mm - n * pw) / n
    for i in range(n):
        x0, y0 = gap / 2 + i * (pw + gap), h_mm - ph
        col, acc = rng.choice(_PACK_COLORS), rng.choice(_PACK_COLORS)
        fg = INK if col in ("#C9D6E6", "#E8E4D8", "#F2F2F2") else "#FFFFFF"
        c.rect(x0, y0, x0 + pw, y0 + ph, fill=col)
        c.rect(x0, y0, x0 + pw, y0 + 12, fill=acc)  # ふたの帯
        c.line([(x0, y0 + 12), (x0 + pw, y0 + 12)], "#333333", 0.5)
        kind = rng.randint(0, 2)
        if kind == 0:
            c.ellipse(x0 + pw / 2 - 11, y0 + 17, x0 + pw / 2 + 11, y0 + 39, fill=acc)
        elif kind == 1:
            c.rect(x0 + 6, y0 + 22, x0 + pw - 6, y0 + 27, fill=acc)
        else:
            c.polygon([(x0 + pw / 2, y0 + 17), (x0 + pw / 2 + 12, y0 + 38), (x0 + pw / 2 - 12, y0 + 38)], fill=acc)
        c.text(x0 + pw / 2, y0 + 47, rng.choice(_PACK_WORDS), 8, fg, 900, max_w=pw - 6)
        c.text(x0 + pw / 2, y0 + 57, f"{rng.choice((1, 3, 5, 6, 8, 10, 12))} mg", 6, fg, 700)
        c.rect(x0 + 3, y0 + 63, x0 + pw - 3, y0 + ph - 3, fill="#FFFFFF")  # 注意文の白い帯
        for k in range(3):
            c.line([(x0 + 7, y0 + 69 + k * 4.5), (x0 + pw - 7, y0 + 69 + k * 4.5)], "#555555", 1.2)
    return trim_safe(c.array())


def _tag_row(seed: int, n: int, w_mm: float, h_mm: float, first: int):
    """箱の下の番号札の列（左から first, first+1, ...）。"""
    c = Canvas(w_mm, h_mm, None, "#FFFFFF", seed)
    c.gradient(0, 0, w_mm, h_mm, "#FFFFFF", "#D6D9DC")
    gap = (w_mm - n * _PACK_W) / n
    for i in range(n):
        xc = gap / 2 + i * (_PACK_W + gap) + _PACK_W / 2
        c.rect(xc - 14, 1.5, xc + 14, h_mm - 1.5, fill="#1E2A3A", radius=2)
        c.text(xc, h_mm / 2, str(first + i), h_mm * 0.62, "#FFFFFF", 900)
    return trim_safe(c.array())


def cigarette_display_wall() -> Product:
    """レジの後ろ（背面カウンターの上）に置くたばこの陳列棚。箱は架空のデザインで、下に番号札が並ぶ。

    参考: https://commons.wikimedia.org/wiki/File:JP_日本_Japan_沖繩_OKINAWA_浦添市_Urasoe-city_AEON_Department_cigarette_on_sale_February_2026_N13P.jpg（CC0）
    参考: https://commons.wikimedia.org/wiki/File:JP_日本_Japan_沖繩_OKINAWA_那霸_Naha_Omoromachi_Shintoshin_新都心_Naha_Main_Place_商場_Shopping_Mall_shop_Aeon_Supermarket_cigarettes_January_2025_R12S_01.jpg（CC0）
    """
    W, D, H = 1.80, 0.30, 1.10
    frame = "#2A2E36"
    base_h, head_h = 0.06, 0.14
    iw = W - 0.06
    rows, n = 8, 24
    row_h = (H - base_h - head_h) / rows
    c = Canvas(iw * 1000, head_h * 1000, None, "#1E2A3A", 3201)
    c.gradient(0, 0, iw * 1000, head_h * 1000, "#2A3A52", "#141C28")
    c.text(170, 70, "たばこ", 64, "#FFFFFF", 900)
    c.text(iw * 500, 55, "番号でお申し付けください", 46, "#FFFFFF", 900)
    c.text(iw * 500, 104, "TOBACCO  ・  PLEASE ORDER BY NUMBER", 22, "#B9C6D8", 700)
    c.rect(iw * 1000 - 470, 28, iw * 1000 - 30, 112, fill="#C8102E", radius=10)
    c.text(iw * 1000 - 250, 54, "20歳未満の方には", 26, "#FFFFFF", 900)
    c.text(iw * 1000 - 250, 88, "販売できません", 26, "#FFFFFF", 900)
    c.text(iw * 500, 128, NOTICE, 10, "#8090A8", 600)
    images = [trim_safe(finish(c.array(), "screen", 3201, 0.3))]
    parts: list[Part] = [
        _box("SideLeft", (0.03, D, H), (-W / 2 + 0.015, 0, H / 2), frame, "metal"),
        _box("SideRight", (0.03, D, H), (W / 2 - 0.015, 0, H / 2), frame, "metal"),
        _box("Base", (iw, D, base_h), (0, 0, base_h / 2), frame, "metal"),
        _box("Header", (iw, D, head_h), (0, 0, H - head_h / 2), frame, "metal", {"front": 0}),
        _box("Back", (iw, 0.02, H - base_h - head_h), (0, D / 2 - 0.01, (H + base_h - head_h) / 2), "#F4F6F8",
             "glossy"),
    ]
    pack_h = 0.088
    lights = []
    for r in range(rows):
        z = base_h + r * row_h  # 棚板の下面
        k = len(images)
        images.append(_pack_row(3210 + r, n, iw * 1000, pack_h * 1000))
        images.append(_tag_row(3230 + r, n, iw * 1000, 16.0, 1 + (rows - 1 - r) * n))
        parts += [
            _box(f"Shelf{r}", (iw, D - 0.02, 0.01), (0, 0.01, z + 0.005), "#E8EAEC", "plastic"),
            _box(f"Packs{r}", (iw, 0.09, pack_h), (0, -D / 2 + 0.02 + 0.045, z + 0.01 + pack_h / 2), "#F4F6F8",
                 "plastic", {"front": k}),
            _box(f"NumberRail{r}", (iw, 0.006, 0.016), (0, -D / 2 + 0.003, z + 0.006), "#FFFFFF", "plastic",
                 {"front": k + 1}, collision=False),
        ]
        # 段ごとの LED（上の棚板・看板の下の手前の縁、番号札のすぐ後ろ）。奥へ傾けて箱の正面を照らす
        lamp, lux = _lamp(f"ShelfLight{r}", (iw - 0.02, 0.008, 0.004), (0, -D / 2 + 0.009, z + row_h - 0.0025),
                          "#FBFBF6", 14000.0, COOL_WHITE, tilt=20.0)
        parts.append(lamp)
        lights.append(lux)
    return Product(slug="cigarette_display_wall", name="たばこ陳列棚（レジ後ろ・番号札付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=60.0, static=True, material="steel",
                   description="形はレジの後ろの背面カウンターの上に置く一般的なたばこの陳列棚（8 段・番号札付き）で、"
                               "寸法・質量は代表値。箱の絵柄・看板は架空で、実在の銘柄に似せていない。",
                   tags=["たばこ", "陳列棚", "番号札", "レジ後ろ", "店舗什器", "cigarette display shelf",
                         "tobacco wall", "numbered tags"], photos=[], colors=Colors(label_base=frame),
                   images=images, parts=parts, lights=lights)


# ---------------------------------------------------------------- 吊り下げフック什器


HOOK_RACK = (0.60, 0.45, 1.60)  # 吊り下げフック什器の幅・奥行き・高さ
HOOK_X = (-0.18, 0.0, 0.18)
HOOK_LEN = 0.20


def _hook_rack(rows: list[float]) -> tuple[list[Part], list]:
    """自立式の網パネルの吊り下げ什器の部品と画像（看板・値札）。フックは rows の高さに 3 列（見た目だけ・当たり判定なし）。"""
    W, D, H = HOOK_RACK
    frame, wire = "#3A3D42", "#5A5E64"
    c = Canvas(W * 1000, 120, None, "#E8A21C", 3301)
    c.gradient(0, 0, W * 1000, 120, "#F2B232", "#D88E10")
    c.text(300, 52, "おつまみ・珍味", 46, INK, 900)
    c.text(300, 96, "SNACKS FOR DRINKS", 18, "#5A3A00", 800)
    header = trim_safe(c.array())
    c = Canvas(40, 26, None, "#FFFFFF", 3302)
    c.gradient(0, 0, 40, 26, "#FFFFFF", "#E6E6E6")
    c.rect(0, 0, 40, 7, fill="#E8A21C")
    c.text(20, 17, "¥198", 9, INK, 900)
    tag = trim_safe(c.array())
    hp = H - 0.16  # 柱の高さ
    parts: list[Part] = [
        _box("FootLeft", (0.05, D, 0.04), (-W / 2 + 0.025, 0, 0.02), frame, "metal"),
        _box("FootRight", (0.05, D, 0.04), (W / 2 - 0.025, 0, 0.02), frame, "metal"),
        _box("FootBar", (W - 0.10, 0.04, 0.04), (0, 0, 0.02), frame, "metal"),
        _box("PostLeft", (0.03, 0.03, hp), (-W / 2 + 0.015, 0, 0.04 + hp / 2), frame, "metal"),
        _box("PostRight", (0.03, 0.03, hp), (W / 2 - 0.015, 0, 0.04 + hp / 2), frame, "metal"),
        _box("Header", (W, 0.02, 0.12), (0, 0, H - 0.06), "#E8A21C", "plastic", {"front": 0}),
    ]
    z0, z1 = 0.25, 1.48
    mw = W - 0.06
    parts += [_box("MeshFrameB", (mw, 0.012, 0.012), (0, 0, z0), wire, "metal"),
              _box("MeshFrameT", (mw, 0.012, 0.012), (0, 0, z1), wire, "metal")]
    for i in range(11):
        parts.append(_box(f"MeshV{i}", (0.005, 0.005, z1 - z0), (-mw / 2 + mw * i / 10, 0, (z0 + z1) / 2), wire,
                          "metal", collision=False))
    nh = round((z1 - z0) / 0.05)
    for i in range(1, nh):
        parts.append(_box(f"MeshH{i}", (mw, 0.005, 0.005), (0, 0, z0 + (z1 - z0) * i / nh), wire, "metal",
                          collision=False))
    hl = HOOK_LEN
    for r, z in enumerate(rows):
        for k, x in enumerate(HOOK_X):
            parts += [_rod(f"Hook{r}_{k}", (x, -0.003, z), (x, -hl, z), 0.005, CHROME),
                      _box(f"HookTag{r}_{k}", (0.04, 0.003, 0.026), (x, -hl - 0.002, z + 0.012), "#FFFFFF",
                           "plastic", {"front": 1}, collision=False)]
    return parts, [header, tag]


def hook_display_rack() -> Product:
    """自立式の網（メッシュ）パネルにフックを並べた吊り下げ什器（おつまみ・珍味などの袋を掛ける）。商品は掛けていない。

    参考: https://commons.wikimedia.org/wiki/File:Grocery-store-december-2015-ramat-gan.jpg（CC0）
    """
    W, D, H = HOOK_RACK
    frame = "#3A3D42"
    parts, images = _hook_rack([1.38 - r * 0.18 for r in range(6)])
    return Product(slug="hook_display_rack", name="吊り下げフック什器（自立式・網パネル）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=15.0, static=True, material="steel",
                   description="形は売場に置く一般的な自立式の網パネルの吊り下げ什器（フック 3 列 × 6 段）で、"
                               "寸法・質量は代表値。商品は掛けていない。看板・値札は架空。",
                   tags=["吊り下げ什器", "フック", "網パネル", "メッシュ", "店舗什器", "hook display rack",
                         "wire mesh panel", "peg hooks"], photos=[], colors=Colors(label_base=frame),
                   images=images, parts=parts)


def hook_display_rack_snacks() -> Product:
    """hook_display_rack と同じ什器に、さきいか・あたりめ・ビーフジャーキーの袋を掛けたもの（掛けた袋は固定の見た目だけ）。

    袋の丈（ヘッダー込み 185〜195 mm）がフックの段の間隔 180 mm より長いので、段を 5 段・間隔 225 mm にしている。
    袋は dried_squid_bag・atarime_bag・beef_jerky_bag と同じ画像で、1 種類につき 1 組だけ持つ（部品で共用）。
    PhysX で細い棒に袋を掛けると接触が不安定なので、hc_fixtures.pegboard_wall_tools と同じく什器の部品にする。
    """
    W, D, H = HOOK_RACK
    frame = "#3A3D42"
    rows = [1.38 - r * 0.225 for r in range(5)]
    parts, imgs = _hook_rack(rows)
    bags = {}
    for key, f, color in (("sq", dried_squid_hang, "#FFF8E8"), ("at", atarime_hang, "#FBF6EC"),
                          ("jk", beef_jerky_hang, "#3B2416")):
        b = f()
        bags[key] = (b, len(imgs), color)
        imgs += b.images
    plan = (("sq", "sq", "at"), ("jk", "jk", "sq"), ("at", "at", "jk"), ("sq", "jk", "at"), ("at", "sq", "jk"))
    for r, z in enumerate(rows):
        for c, x in enumerate(HOOK_X):
            key = plan[r][c]
            b, k, color = bags[key]
            t = b.depth * 0.8
            step = t + 0.004
            n = 0
            while 0.03 + t + n * step <= HOOK_LEN - 0.03:  # 袋は奥から手前へ。先の値札の前は空ける
                parts += hung_bag_parts(b, f"{key}{r}_{c}_{n}_", x, -(0.03 + t / 2 + n * step), z, k, color)
                n += 1
    return Product(slug="hook_display_rack_snacks", name="吊り下げフック什器（おつまみ・珍味の袋付き）",
                   shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=18.0,
                   static=True, material="steel",
                   description="形は hook_display_rack と同じ自立式の網パネルの吊り下げ什器（フック 3 列 × 5 段）に、"
                               "さきいか・あたりめ・ビーフジャーキーの袋（dried_squid_bag・atarime_bag・beef_jerky_bag と同じ絵）を"
                               "フック 1 本に 6〜7 袋ずつ掛けたもので、寸法・質量は代表値。掛けた袋は什器の一部"
                               "（見た目だけ・当たり判定なし・動かない）。看板・値札は架空。",
                   tags=["吊り下げ什器", "フック", "網パネル", "おつまみ", "珍味", "さきいか", "あたりめ", "ビーフジャーキー",
                         "店舗什器", "コンビニ", "hook display rack", "snack display", "hanging snack bags",
                         "peg hooks"], photos=["snk_dried_squid"], colors=Colors(label_base=frame),
                   images=imgs, parts=parts)


# ---------------------------------------------------------------- 新聞ラック


def _newspaper(seed: int, title: str, color: str):
    """二つ折りの新聞の一面（架空の見本紙）。"""
    w, h = 270.0, 400.0
    c = Canvas(w, h, None, "#EDEBE4", seed)
    c.gradient(0, 0, w, h, "#F2F0EA", "#E2DFD6")
    c.rect(8, 8, w - 8, 62, fill="#FFFFFF")
    c.text(w / 2, 32, title, 30, color, 900, max_w=w - 30)
    c.text(w / 2, 54, "見本  ・  架空の新聞です", 9, "#555555", 700)
    c.rect(8, 66, w - 8, 68, fill=color)
    c.vtext(w - 32, 92, "見出しの見本", 20, INK, 900)
    c.rect(14, 80, w - 62, 190, fill="#B9B6AE")  # 写真の代わりの灰色の面
    c.rect(20, 86, w - 68, 184, fill=c.rng.choice(("#8E8A80", "#A3A9AE", "#9C9484")))
    for k in range(18):  # 本文の行
        y = 204 + k * 10.5
        if y > h - 14:
            break
        c.line([(14, y), (w - 14 if k % 6 else w * 0.5, y)], "#77746E", 2.2)
    return trim_safe(finish(c.array(), "paper", seed, 0.6))


def newspaper_stand() -> Product:
    """白い針金の段々の新聞ラック（3 段・新聞 6 部）。新聞は架空の見本紙。

    参考: https://commons.wikimedia.org/wiki/File:JP_日本_Japan_沖繩_OKINAWA_便利商店_Lawson_stores_商品_January_2025_R12S_01.jpg（CC0）
    """
    W, D, H = 0.60, 0.44, 1.12
    wire = "#F2F2F0"
    t = 15.0  # 新聞を奥へ倒す角度 [度]
    up = (math.sin(math.radians(t)), math.cos(math.radians(t)))
    c = Canvas(400, 100, None, "#1E4F9A", 3401)
    c.gradient(0, 0, 400, 100, "#2A64B8", "#173E7A")
    c.text(200, 46, "新聞", 52, "#FFFFFF", 900)
    c.text(200, 84, "NEWSPAPERS", 16, "#D6E2F4", 800)
    images = [trim_safe(c.array()), _newspaper(3402, "日刊 見本新聞", "#1E2A6E"),
              _newspaper(3403, "スポーツ見本", "#C8102E"), _newspaper(3404, "見本経済", "#1F6E4A")]
    yb, yf = D / 2 - 0.01, -D / 2 + 0.01
    parts: list[Part] = []
    for s, x in (("L", -W / 2 + 0.006), ("R", W / 2 - 0.006)):
        parts += [
            _rod(f"Skid{s}", (x, yf, 0.006), (x, yb, 0.006), 0.012, wire, collision=True),
            _rod(f"PostBack{s}", (x, yb, 0.0), (x, yb, H - 0.02), 0.012, wire, collision=True),
            _rod(f"PostFront{s}", (x, yf, 0.0), (x, yf, 0.20), 0.012, wire, collision=True),
            _rod(f"Diagonal{s}", (x, yf, 0.20), (x, yb, 1.0), 0.010, wire, collision=True),
        ]
    parts += [_rod("TopBar", (-W / 2 + 0.006, yb, H - 0.02), (W / 2 - 0.006, yb, H - 0.02), 0.010, wire),
              _box("Sign", (0.40, 0.006, 0.10), (0, yb - 0.008, H - 0.05), "#1E4F9A", "plastic", {"front": 0})]
    papers = [1, 2, 3, 1, 3, 2]
    ph = 0.40
    for i, (zb, y_f) in enumerate(((0.08, -0.18), (0.34, -0.07), (0.60, 0.04))):
        parts += [
            _box(f"Tray{i}", (W - 0.02, 0.10, 0.006), (0, y_f + 0.05, zb + 0.003), wire, "metal"),
            _rod(f"Lip{i}", (-W / 2 + 0.006, y_f, zb + 0.05), (W / 2 - 0.006, y_f, zb + 0.05), 0.008, wire),
            _rod(f"BackBar{i}", (-W / 2 + 0.006, y_f + 0.13, zb + 0.22), (W / 2 - 0.006, y_f + 0.13, zb + 0.22),
                 0.008, wire),
        ]
        for k, x in enumerate((-0.145, 0.145)):
            p = _box(f"Paper{i}_{k}", (0.27, 0.012, ph), (x, y_f + 0.03 + up[0] * ph / 2, zb + 0.006 + up[1] * ph / 2),
                     "#EDEBE4", "matte", {"front": papers[i * 2 + k]}, rotation=[-t, 0, 0])
            p.material = "paper"
            parts.append(p)
    return Product(slug="newspaper_stand", name="新聞ラック（3段・ワイヤー）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=9.0, static=True, material="steel",
                   description="形は店の入口付近に置く一般的な白いワイヤーの段々の新聞ラック（3 段・新聞 6 部）で、"
                               "寸法・質量は代表値。新聞は架空の見本紙。",
                   tags=["新聞ラック", "新聞", "ワイヤーラック", "店舗什器", "newspaper rack", "newspaper stand",
                         "wire rack"], photos=[], colors=Colors(label_base=wire), images=images, parts=parts)


# ---------------------------------------------------------------- 傘立て


def umbrella_stand() -> Product:
    """店の入口に置くステンレスの傘立て（2 列 × 8 本・鍵なし・下に水受け）。

    参考: https://commons.wikimedia.org/wiki/File:Commercial_umbrella_stand.jpg（CC0）
    """
    W, D, H = 0.86, 0.30, 0.62
    c = Canvas(220, 60, None, "#FFFFFF", 3501)
    c.gradient(0, 0, 220, 60, "#2A64B8", "#173E7A")
    c.rect(3, 3, 217, 57, fill="#FFFFFF", radius=3)
    c.text(110, 22, "傘立て", 20, "#1E4F9A", 900)
    c.text(110, 45, "お忘れ物にご注意ください", 11, INK, 700)
    sign = trim_safe(c.array())
    parts: list[Part] = []
    lx, ly = W / 2 - 0.0125, D / 2 - 0.0125
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(_box(f"Leg{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", (0.025, 0.025, H - 0.01),
                              (sx * lx, sy * ly, (H - 0.01) / 2), STEEL, "metal"))
    for z, nm in ((H - 0.02, "Top"), (0.30, "Mid")):
        for y, s in ((-ly, "F"), (0.0, "C"), (ly, "B")):
            parts.append(_box(f"{nm}Rail{s}", (W - 0.05, 0.015, 0.015), (0, y, z), STEEL, "metal"))
        for sx in (-1, 1):
            parts.append(_box(f"{nm}End{'L' if sx < 0 else 'R'}", (0.015, D - 0.05, 0.015), (sx * lx, 0, z), STEEL,
                              "metal"))
    pitch = (W - 0.06) / 8
    for r, y in enumerate((-0.0625, 0.0625)):
        for k in range(8):
            parts.append(Part(name=f"Ring{r}_{k}", shape="torus", size=[0.085, 0.085, 0.008],
                              center=[-W / 2 + 0.03 + pitch * (k + 0.5), y, H - 0.02], color=STEEL, finish="metal",
                              collision=False))
    tz, tw, td = 0.03, W - 0.05, D - 0.05  # 水受け（底の皿）
    parts += [
        _box("TrayFloor", (tw, td, 0.004), (0, 0, tz), STEEL_DARK, "metal"),
        _box("TrayWallF", (tw, 0.004, 0.035), (0, -td / 2, tz + 0.0175), STEEL, "metal"),
        _box("TrayWallB", (tw, 0.004, 0.035), (0, td / 2, tz + 0.0175), STEEL, "metal"),
        _box("TrayWallL", (0.004, td, 0.035), (-tw / 2, 0, tz + 0.0175), STEEL, "metal"),
        _box("TrayWallR", (0.004, td, 0.035), (tw / 2, 0, tz + 0.0175), STEEL, "metal"),
        _box("Sign", (0.22, 0.003, 0.06), (0, -ly - 0.009, 0.44), "#FFFFFF", "plastic", {"front": 0},
             collision=False),
        _box("SignBracket", (0.01, 0.006, 0.16), (0, -ly - 0.0045, 0.38), STEEL, "metal", collision=False),
    ]
    return Product(slug="umbrella_stand", name="傘立て（ステンレス・16本・鍵なし）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=9.0, static=True, material="steel",
                   description="形は店の入口に置く一般的なステンレスの傘立て（2 列 × 8 本・鍵なし・下に水受け）で、"
                               "寸法・質量は代表値。表示板は架空。",
                   tags=["傘立て", "ステンレス", "入口", "店舗什器", "umbrella stand", "stainless umbrella rack"],
                   photos=[], colors=Colors(label_base=STEEL), images=[sign], parts=parts)


# ---------------------------------------------------------------- 縦型冷凍リーチインケース


def upright_freezer_1door() -> Product:
    """ガラス扉 1 枚の縦型の冷凍ケース（アイス・冷凍食品用、棚 5 段・中は空）。作りは reach_in_cooler_3door と同じ。

    参考: https://commons.wikimedia.org/wiki/File:JP_日本_Japan_沖繩_OKINAWA_便利商店_Lawson_stores_商品_January_2025_R12S_04.jpg（CC0）
    参考: https://commons.wikimedia.org/wiki/File:Seven_eleven_yokohama_hammerhead06.jpg（CC0）
    """
    W, D, H = 0.60, 0.70, 1.95
    frame, dark, lining, shelf_c = "#3A3D42", "#24262A", "#F2F4F6", "#C9CCD0"
    base_h, head_h = 0.12, 0.22
    iw = W - 0.08
    open_h = H - base_h - head_h
    zc = base_h + open_h / 2
    hw, hh = iw * 1000, 180.0
    c = Canvas(hw, hh, None, "#1E5FA8", 3601)
    c.gradient(0, 0, hw, hh, "#3A8AD8", "#123E78")
    c.text(hw / 2, 62, "アイス・冷凍食品", 50, "#FFFFFF", 900, max_w=hw - 40)
    c.text(hw / 2, 112, "FROZEN FOODS", 26, "#D6E8FA", 800)
    c.text(hw / 2, 150, "−20℃ 以下  ・  扉はすぐにお閉めください", 16, "#BFD8F2", 700, max_w=hw - 30)
    header = trim_safe(finish(c.array(), "screen", 3601, 0.4))
    parts: list[Part] = [
        _box("Base", (W, D - 0.06, base_h), (0, 0.03, base_h / 2), dark, "metal"),
        _box("BaseGrille", (iw, 0.01, 0.09), (0, -D / 2 + 0.035, base_h / 2), "#141518", "matte", collision=False),
        _box("SideLeft", (0.04, D, H), (-W / 2 + 0.02, 0, H / 2), frame, "metal"),
        _box("SideRight", (0.04, D, H), (W / 2 - 0.02, 0, H / 2), frame, "metal"),
        _box("Back", (iw, 0.04, H - base_h), (0, D / 2 - 0.02, base_h + (H - base_h) / 2), lining, "plastic"),
        _box("Top", (iw, D, head_h), (0, 0, H - head_h / 2), dark, "metal"),
        _box("Header", (iw, 0.012, 0.18), (0, -D / 2 - 0.006, H - head_h / 2), "#1E5FA8", "screen", {"front": 0},
             collision=False),
        _box("Floor", (iw, D - 0.10, 0.02), (0, 0.01, base_h + 0.01), lining, "plastic"),
    ]
    # 照明：左右の内壁の前寄りに縦の LED（扉の内側から奥へ照らす）
    lights = []
    for k, x in enumerate((-iw / 2 + 0.012, iw / 2 - 0.012)):
        lamp, lux = _lamp(f"LedBar{k}", (0.02, 0.008, open_h - 0.08), (x, -D / 2 + 0.084, zc), "#F4F8FF", 20000.0,
                          COOL_WHITE, facing="back")
        parts.append(lamp)
        lights.append(lux)
    for i in range(5):  # 棚とプライスレール
        z = base_h + 0.28 + i * 0.27
        parts += [_box(f"Shelf{i}", (iw - 0.01, 0.50, 0.012), (0, 0.06, z), shelf_c, "metal"),
                  _box(f"PriceRail{i}", (iw - 0.01, 0.008, 0.035), (0, 0.06 - 0.254, z + 0.006), "#FFFFFF",
                       "plastic", collision=False)]
    dw, dh, y = iw - 0.006, open_h - 0.02, -D / 2
    hx = dw / 2 - 0.06  # 取っ手（扉の右寄り）
    parts += [_box("DoorGlass", (dw, 0.02, dh), (0, y, zc), GLASS, "glass"),
              _box("DoorStileL", (0.04, 0.028, dh), (-dw / 2 + 0.02, y, zc), dark, "metal", collision=False),
              _box("DoorStileR", (0.04, 0.028, dh), (dw / 2 - 0.02, y, zc), dark, "metal", collision=False),
              _box("DoorRailT", (dw, 0.028, 0.06), (0, y, zc + dh / 2 - 0.03), dark, "metal", collision=False),
              _box("DoorRailB", (dw, 0.028, 0.08), (0, y, zc - dh / 2 + 0.04), dark, "metal", collision=False),
              _box("DoorHandle", (0.022, 0.026, 0.60), (hx, y - 0.043, zc), "#B8BCC0", "metal"),
              _box("DoorHandlePostT", (0.016, 0.03, 0.016), (hx, y - 0.028, zc + 0.26), "#B8BCC0", "metal",
                   collision=False),
              _box("DoorHandlePostB", (0.016, 0.03, 0.016), (hx, y - 0.028, zc - 0.26), "#B8BCC0", "metal",
                   collision=False)]
    # 扉は左端の蝶番で手前に開く（上から見て時計回り = Z 軸の負の向き）
    _link(parts, "Door", "DoorLink")
    joints = [Joint(link="DoorLink", anchor=[-dw / 2, y - 0.01, zc], limits=[-100.0, 0.0])]
    return Product(slug="upright_freezer_1door", name="縦型冷凍リーチインケース ガラス扉1枚", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.056), mass_kg=130.0, static=True,
                   material="steel",
                   description="形はコンビニの壁際に置く一般的なガラス扉 1 枚の縦型の冷凍ケース（棚 5 段・中は空）で、"
                               "寸法・質量は代表値。扉（DoorLink）は左端の蝶番で手前に 100° まで開く。上の看板は架空。",
                   tags=["冷凍ケース", "リーチイン", "ガラス扉", "アイス", "冷凍食品", "店舗什器", "upright freezer",
                         "reach-in freezer", "glass door"], photos=[], colors=Colors(label_base=frame),
                   images=[header], parts=parts, joints=joints, lights=lights)


# ---------------------------------------------------------------- 宅配便受け取りロッカー


def _locker_column(seed: int, w_mm: float, h_mm: float, doors: list[float], first: int, panel: tuple | None):
    """扉の並んだロッカーの列の正面。doors は扉の高さ [mm]（上から）。panel は操作部の (上端, 下端) [mm]。"""
    c = Canvas(w_mm, h_mm, None, "#E4E7EA", seed)
    c.gradient(0, 0, w_mm, h_mm, "#ECEEF0", "#D6D9DD")
    y, no = 0.0, first
    for dh in doors:
        if panel and abs(y - panel[0]) < 1:  # 操作部（画面・読み取り機は部品で重ねる）
            c.rect(6, y + 6, w_mm - 6, panel[1] - 6, fill="#2A2E34", radius=6)
            c.rect(6, y + 6, w_mm - 6, y + 40, fill=TEAL, radius=6)
            c.text(w_mm / 2, y + 23, "操作パネル  画面にタッチ", 18, "#FFFFFF", 900)
            c.text(w_mm / 2, panel[1] - 60, "受け取り番号・バーコードで開きます", 15, "#E6E6E6", 700)
            c.text(w_mm / 2, panel[1] - 32, "PICK UP / DROP OFF", 14, "#9FD6D6", 800)
            y = panel[1]
            continue
        c.rect(6, y + 4, w_mm - 6, y + dh - 4, fill="#F2F4F6", outline="#B5BAC0", width=1.5, radius=3)
        c.rect(w_mm - 70, y + dh / 2 - 22, w_mm - 54, y + dh / 2 + 22, fill="#9EA4AA", radius=3)  # 取っ手のくぼみ
        c.rect(18, y + 16, 66, y + 46, fill=TEAL, radius=4)
        c.text(42, y + 31, f"{no:02d}", 20, "#FFFFFF", 900)
        y += dh
        no += 1
    return _metal(c, seed)


def parcel_locker() -> Product:
    """店内に置く宅配便の受け取りロッカー（3 列・中央に操作パネルと画面）。扉は開かない。

    参考: https://commons.wikimedia.org/wiki/File:PUDO_Kintetsu_Imazato_Station.jpg（CC0）
    参考: https://commons.wikimedia.org/wiki/File:郵便_and_Smari_and_Amazon_delivery_lockers_inside_convenience_store.jpg（CC0）
    """
    cw, D, H = 0.42, 0.55, 1.90
    W = cw * 3 + 0.04
    plinth, sign_h = 0.08, 0.20
    bh = H - plinth - sign_h
    hmm = bh * 1000
    pz0, pz1 = 540.0, 990.0  # 中央の列の操作部（上から [mm]）
    # 列ごとの扉の高さ [mm]（合計 = 1620）
    left = [180, 180, 180, 270, 270, 270, 270]
    mid = [180, 180, 180, pz1 - pz0, 270, 360]
    right = [270, 270, 360, 360, 360]
    images = [_locker_column(3701, cw * 1000, hmm, left, 1, None),
              _locker_column(3702, cw * 1000, hmm, mid, 8, (pz0, pz1)),
              _locker_column(3703, cw * 1000, hmm, right, 13, None)]
    c = Canvas((W - 0.04) * 1000, sign_h * 1000, None, TEAL, 3704)
    sw = (W - 0.04) * 1000
    c.gradient(0, 0, sw, sign_h * 1000, "#28A2A2", "#16706F")
    c.text(sw / 2, 70, "宅配便 受け取りロッカー", 64, "#FFFFFF", 900)
    c.text(sw / 2, 138, "PARCEL LOCKER  ・  24時間 受け取りできます", 28, "#D8F2F2", 800)
    c.text(sw / 2, 182, NOTICE, 12, "#BFE6E6", 600)
    images.append(trim_safe(finish(c.array(), "screen", 3704, 0.3)))
    c = Canvas(220, 150, None, "#0E2A3A", 3705)
    c.gradient(0, 0, 220, 150, "#16465E", "#0B2232")
    c.rect(10, 10, 210, 36, fill=TEAL, radius=4)
    c.text(110, 23, "ようこそ", 15, "#FFFFFF", 900)
    for k, lab in enumerate(("受け取る", "発送する", "ヘルプ")):
        c.rect(20, 46 + k * 33, 200, 72 + k * 33, fill="#FFFFFF", radius=6)
        c.text(110, 59 + k * 33, lab, 14, "#16465E", 900)
    images.append(trim_safe(finish(c.array(), "screen", 3705, 0.6)))
    parts: list[Part] = [
        _box("Plinth", (W - 0.02, D - 0.04, plinth), (0, 0.02, plinth / 2), "#2A2E34", "matte"),
        _box("SideLeft", (0.02, D, H - plinth), (-W / 2 + 0.01, 0, (H + plinth) / 2), "#D6D9DD", "metal"),
        _box("SideRight", (0.02, D, H - plinth), (W / 2 - 0.01, 0, (H + plinth) / 2), "#D6D9DD", "metal"),
        _box("Sign", (W - 0.04, D, sign_h), (0, 0, H - sign_h / 2), TEAL, "plastic", {"front": 3}),
    ]
    for k in range(3):
        parts.append(_box(f"Column{k}", (cw, D, bh), (-cw + k * cw, 0, plinth + bh / 2), "#E4E7EA", "metal",
                          {"front": k}))
    zp = plinth + bh - pz0 / 1000  # 操作部の上端の高さ
    parts += [
        _box("ScreenBezel", (0.25, 0.008, 0.18), (0, -D / 2 - 0.004, zp - 0.17), "#1A1C20", "plastic"),
        _box("Screen", (0.22, 0.004, 0.15), (0, -D / 2 - 0.010, zp - 0.17), "#0E2A3A", "screen", {"front": 4},
             collision=False),
        _box("Reader", (0.09, 0.03, 0.06), (-0.08, -D / 2 - 0.015, zp - 0.33), "#1A1C20", "plastic"),
        _box("ReaderWindow", (0.06, 0.002, 0.035), (-0.08, -D / 2 - 0.031, zp - 0.33), "#B02A2A", "glossy",
             collision=False),
        _box("Slot", (0.09, 0.02, 0.012), (0.08, -D / 2 - 0.01, zp - 0.33), "#1A1C20", "plastic"),
    ]
    return Product(slug="parcel_locker", name="宅配便受け取りロッカー（3列・操作パネル付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.032), mass_kg=220.0, static=True,
                   material="steel",
                   description="形はコンビニ・駅に置く一般的な宅配便の受け取りロッカー（3 列 17 扉・中央に画面と読み取り機）で、"
                               "寸法・質量は代表値。扉は開かない。看板・画面は架空。",
                   tags=["宅配便ロッカー", "受け取りロッカー", "宅配ボックス", "店舗什器", "parcel locker",
                         "package pickup locker", "delivery locker"], photos=[], colors=Colors(label_base="#E4E7EA"),
                   images=images, parts=parts)


# ---------------------------------------------------------------- モバイルバッテリーレンタルスタンド


def battery_rental_stand() -> Product:
    """レジ横・入口に置くモバイルバッテリーのレンタルスタンド（画面付き・8 本）。卓上の小型のもので、持ち運べるので static にしない。

    参考: https://commons.wikimedia.org/wiki/File:JP_日本_Japan_沖繩_OKINAWA_那霸_Naha_Airport_arrival_January_2025_R12S_122_electricity_chargers_rental.jpg（CC0）
    """
    W, D, Hb = 0.36, 0.14, 0.20
    body = "#F4F5F6"
    c = Canvas(W * 1000, Hb * 1000, None, body, 3801)
    c.gradient(0, 0, W * 1000, Hb * 1000, "#FAFBFC", "#E2E4E7")
    c.rect(0, 0, W * 1000, 14, fill=TEAL)
    c.rect(18, 26, 198, 140, fill="#1A1C20", radius=6)  # 画面（部品で重ねる）の枠
    c.text(278, 44, "モバイル", 22, INK, 900)
    c.text(278, 70, "バッテリー", 22, INK, 900)
    c.text(278, 96, "レンタル", 22, TEAL, 900)
    c.rect(238, 110, 318, 190, fill="#FFFFFF", outline="#555555", width=1)
    rng = c.rng
    for i in range(9):  # QR コード風の模様（読み取れない）
        for j in range(9):
            if rng.random() < 0.5 or (i < 3 and j < 3) or (i < 3 and j > 5) or (i > 5 and j < 3):
                c.rect(242 + i * 8, 114 + j * 8, 250 + i * 8, 122 + j * 8, fill="#111111")
    c.text(108, 160, "USB-C ・ Lightning ・ micro USB", 10, "#555555", 700)
    c.text(108, 182, "どこでも返せます", 13, INK, 800)
    front = trim_safe(c.array())
    c = Canvas(170, 105, None, "#0E2A3A", 3802)
    c.gradient(0, 0, 170, 105, "#16465E", "#0B2232")
    c.text(85, 22, "借りる", 18, "#FFFFFF", 900)
    c.rect(18, 40, 152, 70, fill=TEAL, radius=8)
    c.text(85, 55, "QR を読み取ってください", 10, "#FFFFFF", 800)
    c.text(85, 88, "1時間 ¥200（見本）", 11, "#BFE6E6", 700)
    screen = trim_safe(finish(c.array(), "screen", 3802, 0.6))
    parts: list[Part] = [
        _box("Body", (W, D, Hb), (0, 0, Hb / 2), body, "plastic", {"front": 0}),
        _box("Screen", (0.17, 0.004, 0.105), (-W / 2 + 0.108, -D / 2 - 0.002, Hb - 0.083), "#0E2A3A", "screen",
             {"front": 1}, collision=False),
        _box("TopTrim", (W - 0.02, D - 0.02, 0.004), (0, 0, Hb + 0.002), "#2A2E34", "plastic"),
    ]
    pitch = (W - 0.04) / 8
    for k in range(8):  # 上に差したバッテリー（上 4 cm が出ている）
        x = -W / 2 + 0.02 + pitch * (k + 0.5)
        parts += [_box(f"Battery{k}", (0.026, 0.072, 0.04), (x, 0.0, Hb + 0.004 + 0.02), "#FFFFFF", "plastic"),
                  _box(f"BatteryCap{k}", (0.026, 0.072, 0.006), (x, 0.0, Hb + 0.044 + 0.003), TEAL, "plastic",
                       collision=False),
                  _box(f"BatteryLed{k}", (0.006, 0.003, 0.004), (x, -0.0375, Hb + 0.034), "#3ACF6A", "light",
                       collision=False)]
    return Product(slug="battery_rental_stand", name="モバイルバッテリー レンタルスタンド（卓上・8本）",
                   shape_class="assembly", category="fixture", dims=Dimensions(Hb + 0.05, W, depth=D + 0.004),
                   mass_kg=4.0, material="plastic",
                   description="形はレジ横・入口に置く一般的な卓上のモバイルバッテリーのレンタルスタンド（画面付き・"
                               "バッテリー 8 本を上に差す）で、寸法・質量は代表値。画面・表示・QR 模様は架空。",
                   tags=["モバイルバッテリー", "レンタル", "充電スタンド", "店舗什器", "power bank rental stand",
                         "battery sharing station"], photos=[], colors=Colors(label_base=body),
                   images=[front, screen], parts=parts)


# ---------------------------------------------------------------- 買い物かご置き台


def basket_stand() -> Product:
    """入口に置く買い物かごの置き台（クロームの針金の枠・キャスター付き）。台だけで、かごは別（shopping_basket）。

    参考: https://commons.wikimedia.org/wiki/File:People_waiting_to_get_Quintuple_Stimulus_Vouchers_at_FamilyMart_Futai_Store_FamiPort_20211008.jpg（CC0）
    """
    W, D, H = 0.54, 0.40, 0.45
    c = Canvas(300, 80, None, "#C8102E", 3901)
    c.gradient(0, 0, 300, 80, "#D8283A", "#B00C22")
    c.text(150, 32, "お買い物かご", 30, "#FFFFFF", 900)
    c.text(150, 62, "SHOPPING BASKETS", 14, "#FFE0E4", 800)
    sign = trim_safe(c.array())
    x, y = W / 2 - 0.015, D / 2 - 0.015
    parts: list[Part] = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            nm = f"{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}"
            parts += [
                Part(name=f"Wheel{nm}", shape="cylinder", size=[0.05, 0.05, 0.02], center=[sx * x, sy * y, 0.025],
                     rotation=[0, 90, 0], color="#2A2C30", finish="plastic"),
                _box(f"CasterFork{nm}", (0.03, 0.03, 0.03), (sx * x, sy * y, 0.06), CHROME, "metal",
                     collision=False),
                _rod(f"Post{nm}", (sx * x, sy * y, 0.075), (sx * x, sy * y, H - 0.006), 0.012, CHROME,
                     collision=True),
            ]
    for z, nm in ((0.08, "Bottom"), (0.22, "Floor"), (H - 0.006, "Rim")):
        for sy in (-1, 1):
            parts.append(_rod(f"{nm}Rail{'F' if sy < 0 else 'B'}", (-x, sy * y, z), (x, sy * y, z), 0.012, CHROME,
                              collision=True))
        for sx in (-1, 1):
            parts.append(_rod(f"{nm}End{'L' if sx < 0 else 'R'}", (sx * x, -y, z), (sx * x, y, z), 0.012, CHROME,
                              collision=True))
    for i in range(1, 9):  # かごを載せる網の床
        xx = -x + 2 * x * i / 9
        parts.append(_rod(f"FloorWire{i}", (xx, -y, 0.224), (xx, y, 0.224), 0.005, CHROME))
    parts += [_box("FloorBoard", (2 * x - 0.01, 2 * y - 0.01, 0.003), (0, 0, 0.2195), "#9EA2A8", "metal"),
              _box("Sign", (0.30, 0.004, 0.08), (0, -y - 0.008, H - 0.06), "#C8102E", "plastic", {"front": 0},
                   collision=False)]
    return Product(slug="basket_stand", name="買い物かご置き台（キャスター付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=6.0, static=True, material="steel",
                   description="形は店の入口に置く一般的なクロームの針金の買い物かご置き台（キャスター付き・かごは別）で、"
                               "寸法・質量は代表値。表示板は架空。",
                   tags=["買い物かご置き台", "かご置き", "キャスター", "店舗什器", "shopping basket stand",
                         "basket dolly"], photos=[], colors=Colors(label_base=CHROME), images=[sign], parts=parts)


# ---------------------------------------------------------------- 卓上フライヤー


def counter_fryer() -> Product:
    """カウンターの奥に置く卓上の電気フライヤー（油槽 2 つ・かご 2 つ・奥にかご掛け）。

    参考: https://commons.wikimedia.org/wiki/File:Deepfryer.jpg（PD）
    参考: https://commons.wikimedia.org/wiki/File:Freidora.jpg（PD）
    """
    W, D = 0.58, 0.46
    feet, zt = 0.04, 0.32  # 脚の高さ・天板の上面
    oil_top, tank_floor = 0.25, 0.10
    tw, td, ty = 0.24, 0.30, -0.03  # 油槽の開口の幅・奥行き・中心の Y
    tx = (-0.135, 0.135)
    # 正面の操作部
    fw, fh = W * 1000, (zt - feet - 0.01) * 1000
    c = Canvas(fw, fh, None, STEEL, 3001)
    c.gradient(0, 0, fw, fh, "#D2D5D9", "#B4B8BD")
    for x in tx:
        xc = fw / 2 + x * 1000
        c.rect(xc - 105, 20, xc + 105, 150, fill="#2A2C30", radius=8)
        c.ellipse(xc - 45, 40, xc + 45, 130, fill="#E4E6E8")
        for a in range(0, 271, 30):
            r = math.radians(135 + a)
            c.line([(xc + 50 * math.cos(r), 85 + 50 * math.sin(r)), (xc + 58 * math.cos(r), 85 + 58 * math.sin(r))],
                   "#FFFFFF", 2)
        c.text(xc - 72, 140, "120", 9, "#FFFFFF", 700)
        c.text(xc + 72, 140, "190℃", 9, "#FFFFFF", 700)
        c.text(xc + 72, 36, "電源", 9, "#FFFFFF", 700)
    c.text(fw / 2, 196, "高温注意  油に水を入れないでください", 16, "#B0242A", 900)
    c.text(fw / 2, 228, "100V ・ 1.5kW × 2", 11, "#4A4E54", 700)
    front = _metal(c, 3001)
    # かごの網
    c = Canvas(200, 130, None, "#8A8E94", 3002)
    c.gradient(0, 0, 200, 130, "#A4A8AE", "#7A7E84")
    for k in range(0, 201, 6):
        c.line([(k, 0), (k, 130)], "#3A3C40", 0.9)
    for k in range(0, 131, 6):
        c.line([(0, k), (200, k)], "#3A3C40", 0.9)
    mesh = trim_safe(c.array())
    c = Canvas(260, 130, None, "#8A8E94", 3003)
    c.gradient(0, 0, 260, 130, "#A4A8AE", "#7A7E84")
    for k in range(0, 261, 6):
        c.line([(k, 0), (k, 130)], "#3A3C40", 0.9)
    for k in range(0, 131, 6):
        c.line([(0, k), (260, k)], "#3A3C40", 0.9)
    mesh_side = trim_safe(c.array())
    bz, ph = feet + (zt - feet) / 2, zt - feet
    parts: list[Part] = [
        _box(f"Foot{i}", (0.04, 0.04, feet), (sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), feet / 2), "#2A2C30",
             "plastic") for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))
    ]
    parts += [
        _box("Bottom", (W, D, 0.01), (0, 0, feet + 0.005), STEEL, "metal"),
        _box("FrontPanel", (W, 0.01, ph - 0.01), (0, -D / 2 + 0.005, bz - 0.005), STEEL, "metal", {"front": 0}),
        _box("BackPanel", (W, 0.01, ph), (0, D / 2 - 0.005, bz), STEEL, "metal"),
        _box("SideLeft", (0.01, D - 0.02, ph), (-W / 2 + 0.005, 0, bz), STEEL, "metal"),
        _box("SideRight", (0.01, D - 0.02, ph), (W / 2 - 0.005, 0, bz), STEEL, "metal"),
    ]
    # 天板（油槽の開口のまわり）
    y0, y1 = ty - td / 2, ty + td / 2
    dz, xe = zt - 0.005, 0.255  # 開口の外の端の X
    parts += [
        _box("DeckFront", (W, y0 + D / 2, 0.01), (0, (-D / 2 + y0) / 2, dz), STEEL, "metal"),
        _box("DeckBack", (W, D / 2 - y1, 0.01), (0, (y1 + D / 2) / 2, dz), STEEL, "metal"),
        _box("DeckLeft", (W / 2 - xe, td, 0.01), (-(W / 2 + xe) / 2, ty, dz), STEEL, "metal"),
        _box("DeckMid", (0.03, td, 0.01), (0, ty, dz), STEEL, "metal"),
        _box("DeckRight", (W / 2 - xe, td, 0.01), ((W / 2 + xe) / 2, ty, dz), STEEL, "metal"),
    ]
    wh = zt - 0.01 - tank_floor
    wz = tank_floor + wh / 2
    bw, bd, bh = 0.20, 0.26, 0.13  # かご
    bz0 = 0.17
    bzc = bz0 + bh / 2
    a = math.radians(30)  # 取っ手の上がり角
    L, Lg = 0.17, 0.10  # 取っ手の長さ・握りの長さ
    for i, x in enumerate(tx):
        oil = _box(f"Oil{i}", (tw - 0.01, td - 0.01, oil_top - tank_floor - 0.003),
                   (x, ty, (tank_floor + 0.003 + oil_top) / 2), "#C99A2E", "glossy", collision=False)
        oil.material = "liquid"
        parts += [
            _box(f"Tank{i}Floor", (tw, td, 0.006), (x, ty, tank_floor), STEEL_DARK, "metal"),
            _box(f"Tank{i}WallF", (tw, 0.004, wh), (x, y0 + 0.002, wz), "#B4B8BD", "metal"),
            _box(f"Tank{i}WallB", (tw, 0.004, wh), (x, y1 - 0.002, wz), "#B4B8BD", "metal"),
            _box(f"Tank{i}WallL", (0.004, td, wh), (x - tw / 2 + 0.002, ty, wz), "#B4B8BD", "metal"),
            _box(f"Tank{i}WallR", (0.004, td, wh), (x + tw / 2 - 0.002, ty, wz), "#B4B8BD", "metal"),
            oil,
            # かご（下半分が油につかる）
            _box(f"Basket{i}Floor", (bw, bd, 0.004), (x, ty, bz0), "#8A8E94", "metal", collision=False),
            _box(f"Basket{i}WallF", (bw, 0.003, bh), (x, ty - bd / 2, bzc), "#8A8E94", "metal", {"front": 1},
                 collision=False),
            _box(f"Basket{i}WallB", (bw, 0.003, bh), (x, ty + bd / 2, bzc), "#8A8E94", "metal", {"front": 1},
                 collision=False),
            _box(f"Basket{i}WallL", (0.003, bd, bh), (x - bw / 2, ty, bzc), "#8A8E94", "metal",
                 {"left": 2, "right": 2}, collision=False),
            _box(f"Basket{i}WallR", (0.003, bd, bh), (x + bw / 2, ty, bzc), "#8A8E94", "metal",
                 {"left": 2, "right": 2}, collision=False),
            _box(f"Basket{i}RimF", (bw + 0.006, 0.006, 0.006), (x, ty - bd / 2, bz0 + bh), "#B8BCC0", "metal",
                 collision=False),
            _box(f"Basket{i}RimB", (bw + 0.006, 0.006, 0.006), (x, ty + bd / 2, bz0 + bh), "#B8BCC0", "metal",
                 collision=False),
            _box(f"Basket{i}RimL", (0.006, bd, 0.006), (x - bw / 2, ty, bz0 + bh), "#B8BCC0", "metal",
                 collision=False),
            _box(f"Basket{i}RimR", (0.006, bd, 0.006), (x + bw / 2, ty, bz0 + bh), "#B8BCC0", "metal",
                 collision=False),
        ]
        # 取っ手：かごの前の縁から手前・上へ
        p0 = (x, ty - bd / 2, bz0 + bh)
        pg = (x, p0[1] - (L - Lg) * math.cos(a), p0[2] + (L - Lg) * math.sin(a))
        p1 = (x, p0[1] - L * math.cos(a), p0[2] + L * math.sin(a))
        parts += [_rod(f"Basket{i}Handle", p0, pg, 0.008, CHROME),
                  _rod(f"Basket{i}Grip", pg, p1, 0.022, "#1A1A1C", "plastic", collision=True),
                  # 操作部のつまみ・ランプ
                  Part(name=f"Knob{i}", shape="cylinder", size=[0.04, 0.04, 0.02], center=[x, -D / 2 - 0.01, 0.211],
                       rotation=[90, 0, 0], color="#1A1A1C", finish="plastic"),
                  Part(name=f"Pilot{i}", shape="cylinder", size=[0.012, 0.012, 0.006],
                       center=[x + 0.072, -D / 2 - 0.003, 0.254], rotation=[90, 0, 0], color="#FF7A2A",
                       finish="light", collision=False)]
    hz, hy = zt + 0.13, D / 2 - 0.02  # 奥のかご掛け
    parts += [_rod("HangerPostL", (-0.24, hy, zt), (-0.24, hy, hz), 0.012, STEEL, collision=True),
              _rod("HangerPostR", (0.24, hy, zt), (0.24, hy, hz), 0.012, STEEL, collision=True),
              _rod("HangerBar", (-0.24, hy, hz), (0.24, hy, hz), 0.014, STEEL, collision=True)]
    y_front = ty - bd / 2 - L * math.cos(a) - 0.011  # 取っ手の先
    return Product(slug="counter_fryer", name="卓上フライヤー（2槽・電気式）", shape_class="assembly",
                   category="fixture", dims=Dimensions(hz + 0.007, W, depth=D / 2 - y_front), mass_kg=25.0,
                   static=True, material="steel",
                   description="形はカウンターの奥に置く一般的な卓上の電気フライヤー（油槽 2 つ・かご 2 つ・奥にかご掛け）で、"
                               "寸法・質量は代表値。油は液体（liquid）の部品。表示は架空。",
                   tags=["フライヤー", "揚げ物", "油槽", "店舗厨房", "店舗什器", "counter fryer",
                         "electric deep fryer", "fryer baskets"], photos=[], colors=Colors(label_base=STEEL),
                   images=[front, mesh, mesh_side], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    hot_drink_warmer, cigarette_display_wall, hook_display_rack, hook_display_rack_snacks, newspaper_stand, umbrella_stand,
    upright_freezer_1door, parcel_locker, battery_rental_stand, basket_stand, counter_fryer,
)}
