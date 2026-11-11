"""架空の商品のデザイン: ファミレス・定食屋・居酒屋の客席の家具と卓上の小物。

cafe.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の家具・小物の一般的な値にする。
正面は −Y（座る人・お客さまの側）。ボックス席・ハイテーブルは床に固定（static）、テーブル・椅子・小物は動かせる。
テーブルの天板は薄い水平の板にする（商品を並べるツールが料理・食器を並べる面として見つけられるように）。
メニュー（店の料理の写真・値段の入った面）は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .cafe import _fabric, _wood
from .paint import Canvas, mix
from .products import INK, _box, _cyl, _face
from .super_fixtures import _grain

RESTAURANT_PLACES = ["restaurant"]  # メニューの絵柄が合う場所
WOOD, WOOD_DARK, WALNUT = "#B98A57", "#7A5533", "#5B3B26"
MELAMINE = "#C9A97E"  # メラミン化粧板（明るい木目）
BLACK, CHROME = "#2A2B2E", "#C9CDD1"
VINYL_RED, VINYL_BROWN = "#8E2A2A", "#5A3A2C"
CREAM = "#F3EBDD"


def _vinyl(name, size, center, color, rotation=None, bevel=0.02, collision=True) -> Part:
    """ビニールレザー張りのクッション。"""
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish="glossy", material="vinyl", bevel=bevel, collision=collision)


def _center_depth(parts: list[Part]) -> float:
    """部品の奥行き（Y）の中心を 0 にそろえ、奥行きを返す。"""
    ys = [p.center[1] - p.size[1] / 2 for p in parts] + [p.center[1] + p.size[1] / 2 for p in parts]
    mid = (min(ys) + max(ys)) / 2
    for p in parts:
        p.center[1] -= mid
    return round(max(ys) - min(ys), 3)


# ---------------------------------------------------------------- ボックス席


def booth_seat() -> Product:
    """ファミレスのボックス席の片側（2 人掛け、幅 1200 mm）。背面（+Y）を壁か、隣の席と背中合わせに付ける。"""
    W, D, H = 1.20, 0.65, 1.05
    seat_z = 0.43
    parts: list[Part] = [
        _wood("Base", (W, 0.52, 0.33), (0, -0.04, 0.165), WALNUT),
        _box("Kick", (W - 0.04, 0.01, 0.08), (0, -0.305, 0.04), BLACK, "plastic", collision=False),
        _vinyl("SeatCushion", (W - 0.04, 0.55, 0.10), (0, -0.04, 0.33 + 0.05), VINYL_RED),
        _wood("BackShell", (W, 0.08, H), (0, D / 2 - 0.04, H / 2), WALNUT),
        _wood("BackCap", (W + 0.02, 0.12, 0.03), (0, D / 2 - 0.06, H - 0.015), WOOD_DARK),
        _vinyl("BackCushion", (W - 0.06, 0.10, 0.52), (0, D / 2 - 0.08 - 0.05, seat_z + 0.29), VINYL_RED,
               rotation=[-8, 0, 0], bevel=0.025),
    ]
    for side, x in (("L", -W / 2 + 0.015), ("R", W / 2 - 0.015)):  # 両端の袖板
        parts.append(_wood(f"Side{side}", (0.03, 0.60, 0.62), (x, -0.025, 0.31), WALNUT, collision=False))
    for i, x in enumerate((-0.28, 0.0, 0.28)):  # 背もたれの縦のステッチ
        parts.append(Part(f"Seam{i}", "box", [0.006, 0.006, 0.48], [x, D / 2 - 0.181, seat_z + 0.29], [-8, 0, 0],
                          color=mix(VINYL_RED, "#000000", 0.35), finish="matte", collision=False, material="vinyl",
                          bevel=0))
    return Product(slug="booth_seat", name="ファミレスのボックス席のソファ（2 人掛け・片側）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=55.0, static=True, material="vinyl",
                   description="形はファミリーレストランのボックス席の片側の一般的なベンチソファ（2 人掛け、幅 1200 mm・奥行き 650 mm・"
                               "背もたれの高さ 1050 mm、座面の高さ 430 mm、木の台にビニールレザー張りの座面と背もたれ）で、寸法・質量は代表値。"
                               "背面（+Y）を壁に付けるか、隣のボックス席と背中合わせに置く。向かい合わせ 2 台の間に 4 人用テーブルを置く。",
                   tags=["ファミレス", "ボックス席", "ソファ", "ベンチシート", "客席", "家具", "booth seat", "booth",
                         "family restaurant", "banquette", "bench"],
                   photos=[], colors=Colors(label_base=VINYL_RED), images=[], parts=parts)


# ---------------------------------------------------------------- テーブル


def _table(slug: str, name: str, W: float, D: float, seed: int, people: int, two_legs: bool) -> Product:
    """メラミン化粧板の天板にスチールの脚（一本脚の円盤 or 2 本脚の T 字）のテーブル。"""
    H, t = 0.70, 0.03
    images = [_grain(W * 1000, D * 1000, seed, MELAMINE)]
    parts: list[Part] = [
        _wood("Top", (W, D, t), (0, 0, H - t / 2), MELAMINE, faces={"top": 0}),
    ]
    col_h = H - t - 0.012 - 0.02
    xs = (-W / 2 + 0.28, W / 2 - 0.28) if two_legs else (0.0,)
    for i, x in enumerate(xs):
        parts += [
            _box(f"Plate{i}", (0.18, 0.18, 0.012), (x, 0, H - t - 0.006), BLACK, "metal"),
            _cyl(f"Column{i}", (0.076, 0.076, col_h), (x, 0, 0.02 + col_h / 2), BLACK, "metal"),
        ]
        if two_legs:
            parts.append(_box(f"Foot{i}", (0.07, D - 0.10, 0.025), (x, 0, 0.0125), BLACK, "metal"))
        else:
            parts.append(_cyl(f"Foot{i}", (0.50, 0.50, 0.02), (x, 0, 0.01), BLACK, "metal"))
    if two_legs:
        parts.append(_box("Beam", (xs[1] - xs[0], 0.04, 0.04), (0, 0, H - t - 0.012 - 0.02), BLACK, "metal",
                          collision=False))
    base = "2 本脚の T 字の台座" if two_legs else "一本脚と円盤の台座"
    return Product(slug=slug, name=name, shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D),
                   mass_kg=round(10 + 18 * W * D, 1), static=False, material="wood",
                   description=f"形はファミリーレストラン・定食屋の {people} 人用の一般的な角テーブル（天板 {W * 1000:.0f} × "
                               f"{D * 1000:.0f} mm・高さ 700 mm、メラミン化粧板の天板にスチールの{base}）で、"
                               "寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["ファミレス", "テーブル", f"{people}人用テーブル", "角テーブル", "家具", "restaurant table",
                         "family restaurant", "dining table", "table"],
                   photos=[], colors=Colors(label_base=MELAMINE), images=images, parts=parts)


def family_table_4() -> Product:
    """4 人用の角テーブル（1200 × 750 mm、2 本脚の T 字の台座）。ボックス席 2 台の間に置く。"""
    return _table("family_table_4", "ファミレスの 4 人用テーブル（1200 × 750 mm）", 1.20, 0.75, 6801, 4, True)


def family_table_2() -> Product:
    """2 人用の角テーブル（750 × 750 mm、一本脚）。"""
    return _table("family_table_2", "ファミレスの 2 人用テーブル（750 × 750 mm）", 0.75, 0.75, 6802, 2, False)


def high_counter_table() -> Product:
    """立ち飲み・カウンター席のハイテーブル（1500 × 600 mm、天板の高さ 1000 mm）。足かけの横棒付き。"""
    W, D, H, t = 1.50, 0.60, 1.00, 0.04
    images = [_grain(W * 1000, D * 1000, 6803, WOOD)]
    parts: list[Part] = [_wood("Top", (W, D, t), (0, 0, H - t / 2), WOOD, faces={"top": 0})]
    for i, x in enumerate((-W / 2 + 0.10, W / 2 - 0.10)):
        parts += [_box(f"Leg{i}", (0.06, 0.06, H - t - 0.03), (x, 0, 0.03 + (H - t - 0.03) / 2), BLACK, "metal"),
                  _box(f"Foot{i}", (0.08, D - 0.06, 0.03), (x, 0, 0.015), BLACK, "metal")]
    parts += [_box("Apron", (W - 0.26, 0.03, 0.08), (0, 0, H - t - 0.04), BLACK, "metal", collision=False),
              Part("FootRest", "cylinder", [0.025, 0.025, W - 0.26], [0, -D / 2 + 0.08, 0.25], [0, 90, 0],
                   color=CHROME, finish="metal", collision=False),
              _box("FootRestArmL", (0.02, D / 2 - 0.08, 0.02), (-W / 2 + 0.13 - 0.01, -D / 4 - 0.04 + 0.04, 0.25),
                   CHROME, "metal", collision=False),
              _box("FootRestArmR", (0.02, D / 2 - 0.08, 0.02), (W / 2 - 0.13 + 0.01, -D / 4, 0.25),
                   CHROME, "metal", collision=False)]
    return Product(slug="high_counter_table", name="立ち飲み・カウンター席のハイテーブル（1500 × 600 mm）",
                   shape_class="assembly", category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=38.0,
                   static=True, material="wood",
                   description="形は居酒屋の立ち飲み・ハイカウンター席の一般的なハイテーブル（天板 1500 × 600 mm・高さ 1000 mm、"
                               "木の天板にスチールの 2 本脚、手前の高さ 250 mm に足かけの横棒）で、寸法・質量は代表値。床に固定（static）。"
                               "ハイスツール（座面の高さ 700〜750 mm）と組み合わせる。",
                   tags=["居酒屋", "ハイテーブル", "カウンター", "立ち飲み", "カウンター席", "家具", "high table",
                         "bar table", "counter table", "standing table"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


def zataku_table() -> Product:
    """和室・座敷の座卓（1200 × 750 mm、高さ 330 mm）。"""
    W, D, H, t = 1.20, 0.75, 0.33, 0.035
    top = "#8A5A34"
    images = [_grain(W * 1000, D * 1000, 6804, top)]
    parts: list[Part] = [_wood("Top", (W, D, t), (0, 0, H - t / 2), top, faces={"top": 0})]
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        parts.append(_wood(f"Leg{i}", (0.06, 0.06, H - t), (sx * (W / 2 - 0.07), sy * (D / 2 - 0.07), (H - t) / 2),
                           WALNUT))
    for name, size, c in (("ApronF", (W - 0.20, 0.02, 0.05), (0, -(D / 2 - 0.07), H - t - 0.025)),
                          ("ApronB", (W - 0.20, 0.02, 0.05), (0, D / 2 - 0.07, H - t - 0.025)),
                          ("ApronL", (0.02, D - 0.20, 0.05), (-(W / 2 - 0.07), 0, H - t - 0.025)),
                          ("ApronR", (0.02, D - 0.20, 0.05), (W / 2 - 0.07, 0, H - t - 0.025))):
        parts.append(_wood(name, size, c, WALNUT, collision=False))
    return Product(slug="zataku_table", name="座敷の座卓（1200 × 750 mm）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=16.0, static=False, material="wood",
                   description="形は和室・座敷の一般的な座卓（天板 1200 × 750 mm・高さ 330 mm、木の天板と 4 本脚・幕板）で、"
                               "寸法・質量は代表値。座布団と組み合わせる。動かせる（static ではない）。",
                   tags=["座卓", "和室", "座敷", "ローテーブル", "居酒屋", "和食", "家具", "low table", "zataku",
                         "japanese table", "tatami"],
                   photos=[], colors=Colors(label_base=top), images=images, parts=parts)


def zabuton() -> Product:
    """座布団（銘仙判 550 × 590 mm、厚さ 60 mm）。"""
    W, D, H = 0.55, 0.59, 0.06
    color = "#7C2F3B"
    parts = [_fabric("Cushion", (W, D, H), (0, 0, H / 2), color, bevel=0.025)]
    for i, (x, y) in enumerate([(0, 0), (-0.13, -0.14), (0.13, -0.14), (-0.13, 0.14), (0.13, 0.14)]):
        parts.append(Part(f"Tuft{i}", "cylinder", [0.018, 0.018, 0.004], [x, y, H + 0.001], color="#D9B44A",
                          finish="matte", collision=False, material="fabric"))
    return Product(slug="zabuton", name="座布団（銘仙判 550 × 590 mm）", shape_class="assembly", category="household",
                   dims=Dimensions(H + 0.003, W, depth=D), mass_kg=0.9, static=False, material="fabric",
                   description="形は和室・座敷の一般的な座布団（銘仙判 550 × 590 mm・厚さ 60 mm、中央と四隅に房（とじ糸））で、"
                               "寸法・質量は代表値。",
                   tags=["座布団", "和室", "座敷", "クッション", "居酒屋", "zabuton", "floor cushion", "cushion"],
                   photos=[], colors=Colors(label_base=color), images=[], parts=parts)


# ---------------------------------------------------------------- 椅子


def restaurant_chair() -> Product:
    """ファミレス・定食屋の椅子（木のフレームにビニールレザーの座面・背当て、座面の高さ 440 mm）。正面は −Y。"""
    W, H = 0.44, 0.84
    seat_z, leg = 0.44, 0.032
    parts: list[Part] = [
        _wood("SeatFrame", (W, 0.42, 0.03), (0, -0.02, seat_z - 0.05 - 0.015), WOOD_DARK),
        _vinyl("Seat", (W - 0.02, 0.42, 0.05), (0, -0.02, seat_z - 0.025), VINYL_BROWN, bevel=0.012),
    ]
    sz = seat_z - 0.08
    fy, by = -0.02 - 0.21 + 0.03, -0.02 + 0.21 - 0.02
    for i, x in enumerate((-W / 2 + 0.03, W / 2 - 0.03)):
        parts.append(_wood(f"FrontLeg{i}", (leg, leg, sz), (x, fy, sz / 2), WOOD_DARK))
    back_h = H - sz
    for i, x in enumerate((-W / 2 + 0.03, W / 2 - 0.03)):  # 後ろの脚は背もたれの柱まで通す
        parts += [_wood(f"BackLeg{i}", (leg, leg, sz), (x, by, sz / 2), WOOD_DARK),
                  _wood(f"BackPost{i}", (leg, leg, back_h), (x, by + 0.015, sz + back_h / 2), WOOD_DARK,
                        rotation=[-5, 0, 0])]
    parts += [_vinyl("BackPad", (W - 0.07, 0.04, 0.20), (0, by + 0.04, H - 0.14), VINYL_BROWN, rotation=[-5, 0, 0],
                     bevel=0.01),
              _wood("BackRail", (W - 0.06, 0.02, 0.04), (0, by + 0.022, seat_z + 0.10), WOOD_DARK,
                    rotation=[-5, 0, 0], collision=False)]
    for name, size, c in (("StretcherL", (0.02, 0.32, 0.02), (-W / 2 + 0.03, -0.01, 0.15)),
                          ("StretcherR", (0.02, 0.32, 0.02), (W / 2 - 0.03, -0.01, 0.15)),
                          ("StretcherB", (W - 0.08, 0.02, 0.02), (0, by, 0.20))):
        parts.append(_wood(name, size, c, WOOD_DARK, collision=False))
    D = _center_depth(parts)
    return Product(slug="restaurant_chair", name="ファミレス・定食屋の椅子（ビニールレザー張り）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=5.5, static=False, material="wood",
                   description="形はファミリーレストラン・定食屋の一般的な椅子（座面の高さ 440 mm・幅 440 mm・全高 840 mm、木のフレームに"
                               "ビニールレザー張りの座面と背当て）で、寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["ファミレス", "定食屋", "椅子", "レストランチェア", "ダイニングチェア", "家具", "restaurant chair",
                         "dining chair", "family restaurant", "chair"],
                   photos=[], colors=Colors(label_base=VINYL_BROWN), images=[], parts=parts)


def kids_high_chair() -> Product:
    """子ども用のハイチェア（木、座面の高さ 550 mm、足置き・前のガード付き）。正面は −Y。"""
    H, seat_z = 0.90, 0.55
    light = "#D2A877"
    parts: list[Part] = [_wood("Seat", (0.32, 0.30, 0.02), (0, -0.01, seat_z - 0.01), light)]
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):  # 4 本脚（まっすぐ、床で少し広い台）
        parts.append(_wood(f"Leg{i}", (0.035, 0.035, seat_z - 0.02), (sx * 0.175, sy * 0.155 - 0.01, (seat_z - 0.02) / 2),
                           light))
    parts += [
        _wood("FootRest", (0.38, 0.10, 0.018), (0, -0.155, 0.24), light),
        _wood("StretcherB", (0.32, 0.02, 0.02), (0, 0.145, 0.20), light, collision=False),
        _wood("StretcherL", (0.02, 0.28, 0.02), (-0.175, -0.01, 0.12), light, collision=False),
        _wood("StretcherR", (0.02, 0.28, 0.02), (0.175, -0.01, 0.12), light, collision=False),
    ]
    for side, x in (("L", -0.15), ("R", 0.15)):  # ひじ掛けと背もたれの柱
        parts += [_wood(f"ArmPost{side}", (0.025, 0.025, 0.17), (x, -0.13, seat_z + 0.085), light),
                  _wood(f"Arm{side}", (0.03, 0.30, 0.02), (x, -0.01, seat_z + 0.18), light),
                  _wood(f"BackPost{side}", (0.03, 0.03, H - seat_z), (x, 0.13, seat_z + (H - seat_z) / 2), light)]
    parts += [_wood("BackRest", (0.27, 0.02, 0.14), (0, 0.13, H - 0.09), light),
              _wood("Guard", (0.27, 0.025, 0.03), (0, -0.13, seat_z + 0.175), light),
              _wood("GuardPost", (0.04, 0.02, 0.16), (0, -0.13, seat_z + 0.08), light, collision=False)]
    D = _center_depth(parts)
    return Product(slug="kids_high_chair", name="子ども用ハイチェア（木）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, 0.38, depth=D), mass_kg=4.0, static=False, material="wood",
                   description="形はファミリーレストランに置く一般的な子ども用の木のハイチェア（座面の高さ 550 mm・全高 900 mm、"
                               "4 本脚、高さ 240 mm の足置き、ひじ掛けと前のガード）で、寸法・質量は代表値。動かせる。",
                   tags=["ファミレス", "子ども用椅子", "ハイチェア", "ベビーチェア", "キッズチェア", "家具", "high chair",
                         "kids chair", "baby chair", "family restaurant"],
                   photos=[], colors=Colors(label_base=light), images=[], parts=parts)


# ---------------------------------------------------------------- 卓上の小物


def _bell_top(seed: int) -> np.ndarray:
    """呼び出しボタンの上面（案内と卓番）。画像の下が正面。"""
    c = Canvas(70, 70, 10, "#F4F4F2", seed)
    c.gradient(0, 0, 70, 70, "#FFFFFF", "#E6E6E3")
    c.ellipse(13, 13, 57, 57, fill="#D7D7D3")
    c.text(35, 7, "ご用の方は", 4.6, INK, 800)
    c.text(35, 63, "押してください", 4.6, INK, 800)
    c.text(63, 52, "12", 4.0, "#C62828", 900)
    return _face(c.array(), "plastic", seed, 0.4, 4)


def call_bell() -> Product:
    """テーブルの呼び出しボタン（無線式、70 × 70 mm）。"""
    images = [_bell_top(6811)]
    parts = [_box("Body", (0.070, 0.070, 0.022), (0, 0, 0.011), "#F4F4F2", "plastic", {"top": 0}),
             _cyl("ButtonRing", (0.040, 0.040, 0.003), (0, 0, 0.0235), "#9E9E9E", "plastic"),
             _cyl("Button", (0.034, 0.034, 0.008), (0, 0, 0.029), "#D32F2F", "glossy")]
    return Product(slug="call_bell", name="テーブルの呼び出しボタン", shape_class="assembly", category="household",
                   dims=Dimensions(0.033, 0.070, depth=0.070), mass_kg=0.06, static=False, material="plastic",
                   description="形は飲食店のテーブルに置く一般的な無線式の呼び出しボタン（70 × 70 mm・高さ 33 mm、中央に赤い押しボタン、"
                               "上面に案内と卓番）で、寸法・質量は代表値。",
                   tags=["呼び出しボタン", "コールボタン", "呼び鈴", "ファミレス", "卓上", "call button", "call bell",
                         "table bell", "family restaurant"],
                   photos=[], colors=Colors(label_base="#F4F4F2"), images=images, parts=parts)


DISHES = [("curry", "カレーライス", 890), ("spaghetti", "ミートソース", 790), ("karaage", "唐揚げ定食", 950),
          ("ramen", "醤油ラーメン", 820), ("salad", "シーザーサラダ", 490), ("deli_gyoza", "焼き餃子", 390)]


def _menu(w_mm: float, h_mm: float, seed: int, page: int) -> tuple[np.ndarray, np.ndarray]:
    """卓上メニューの 1 面（料理の写真 3 枚と値段）と、文字・写真を抜いた無地の面。"""
    bg = "#FFF8EC"
    c = Canvas(w_mm, h_mm, None, bg, seed)
    c.gradient(0, 0, w_mm, h_mm, "#FFFDF7", "#F4E8D2")
    c.rect(0, 0, w_mm, 26, fill="#B23A2E")
    c.text(w_mm / 2, 13, ("GRAND MENU", "おすすめ")[page], 14, "#FFFFFF", 900, spacing=2)
    hh = (h_mm - 40) / 3 - 8
    for k, (pid, s, p) in enumerate(DISHES[page * 3:page * 3 + 3]):
        y0 = 34 + k * (h_mm - 40) / 3
        c.photo(pid, 8, y0, w_mm - 8, y0 + hh * 0.72, radius=4)
        c.text(10, y0 + hh * 0.88, s, 9, INK, 800, anchor="lm")
        c.text(w_mm - 10, y0 + hh * 0.88, f"¥{p}", 10, "#B23A2E", 900, anchor="rm")
    blank = Canvas(w_mm, h_mm, None, bg, seed)
    blank.gradient(0, 0, w_mm, h_mm, "#FFFDF7", "#F4E8D2")
    blank.rect(0, 0, w_mm, 26, fill="#B23A2E")
    return _face(c.array(), "paper", seed, 0.4, 4), _face(blank.array(), "paper", seed, 0.4, 4)


def menu_stand() -> Product:
    """卓上のメニュー立て（木の台）に、山形に開いた二つ折りのメニュー（A5 縦 2 面）。前後どちらからも読める。

    写真: curry・spaghetti・karaage・ramen・salad・deli_gyoza（CC0。メニューに合成）
    """
    pw, ph, tilt = 0.148, 0.21, 12.0
    f0, b0 = _menu(148, 210, 6821, 0)
    f1, b1 = _menu(148, 210, 6822, 1)
    images = [f0, b0, f1, b1]
    dy = ph / 2 * math.sin(math.radians(tilt))
    zc = 0.015 + ph / 2 * math.cos(math.radians(tilt))
    parts = [
        _wood("Base", (0.17, 0.10, 0.015), (0, 0, 0.0075), WALNUT),
        Part("PageFront", "box", [pw, 0.002, ph], [0, -dy, zc], [-tilt, 0, 0], color=CREAM, finish="matte",
             faces={"front": 0}, collision=True, material="paper", bevel=0, blank=1),
        Part("PageBack", "box", [pw, 0.002, ph], [0, dy, zc], [tilt, 0, 0], color=CREAM, finish="matte",
             faces={"back": 2}, collision=True, material="paper", bevel=0, blank=3),
    ]
    H = 0.015 + ph * math.cos(math.radians(tilt)) + 0.002
    return Product(slug="menu_stand", name="卓上のメニュー立て（二つ折りのメニュー付き）", shape_class="assembly",
                   category="household", dims=Dimensions(round(H, 3), 0.17, depth=0.10), mass_kg=0.25, static=False,
                   material="wood",
                   description="形は飲食店のテーブルに置く一般的な木のメニュー立て（台 170 × 100 mm）に、A5（148 × 210 mm）の二つ折りの"
                               "メニューを山形に開いて立てたもので、寸法・質量は代表値。メニューの料理・値段は架空。",
                   tags=["メニュー", "メニュー立て", "卓上メニュー", "ファミレス", "卓上", "menu", "menu stand",
                         "table menu", "family restaurant"],
                   photos=[d[0] for d in DISHES], colors=Colors(label_base=CREAM), images=images, parts=parts,
                   picture_places=RESTAURANT_PLACES)


def _bottle(prefix: str, x: float, y: float, d: float, h: float, body: str, cap: str, glass: bool = True) -> list[Part]:
    """卓上の調味料の容器（胴とキャップ）。トレーの上（z = 0.008）に立つ。"""
    return [Part(f"{prefix}Body", "cylinder", [d, d, h], [x, y, 0.008 + h / 2], color=body,
                 finish="glossy" if glass else "plastic", material="glass" if glass else "plastic"),
            _cyl(f"{prefix}Cap", (d * 0.8, d * 0.8, 0.018), (x, y, 0.008 + h + 0.009), cap, "plastic")]


def condiment_set() -> Product:
    """卓上の調味料セット（醤油差し・ソース・塩・こしょうの 4 本を小さなトレーに）。"""
    parts: list[Part] = [_box("Tray", (0.17, 0.08, 0.008), (0, 0, 0.004), "#3B2A20", "plastic")]
    parts += _bottle("Soy", -0.058, 0, 0.042, 0.075, "#3A1A10", "#C62828")
    parts += _bottle("Sauce", -0.010, 0, 0.042, 0.085, "#4A2412", "#2E2E2E")
    parts += _bottle("Salt", 0.034, 0.014, 0.028, 0.065, "#F4F4F2", CHROME, glass=False)
    parts += _bottle("Pepper", 0.066, -0.012, 0.028, 0.065, "#6D5A48", CHROME, glass=False)
    return Product(slug="condiment_set", name="卓上の調味料セット（醤油・ソース・塩・こしょう）", shape_class="assembly",
                   category="household", dims=Dimensions(0.111, 0.17, depth=0.08), mass_kg=0.6, static=False,
                   material="glass",
                   description="形は飲食店のテーブルに置く一般的な調味料のセット（170 × 80 mm のトレーに、ガラスの醤油差し・ソース差し"
                               "（直径 42 mm）と塩・こしょうの振り出し（直径 28 mm））で、寸法・質量は代表値。",
                   tags=["調味料", "醤油差し", "ソース", "塩", "こしょう", "卓上", "ファミレス", "定食屋",
                         "condiment set", "soy sauce", "salt and pepper", "cruet set"],
                   photos=[], colors=Colors(label_base="#3B2A20"), images=[], parts=parts)


def napkin_holder() -> Product:
    """紙ナプキン立て（ステンレス、紙ナプキンを立てて挟む）。"""
    W, D = 0.14, 0.07
    parts = [_box("Base", (W, D, 0.008), (0, 0, 0.004), CHROME, "metal"),
             Part("Napkins", "box", [0.125, 0.034, 0.11], [0, 0, 0.008 + 0.055], color="#FAFAF8", finish="matte",
                  material="paper"),
             _box("PlateF", (W, 0.003, 0.09), (0, -0.0185, 0.008 + 0.045), CHROME, "metal"),
             _box("PlateB", (W, 0.003, 0.09), (0, 0.0185, 0.008 + 0.045), CHROME, "metal")]
    return Product(slug="napkin_holder", name="紙ナプキン立て（ステンレス）", shape_class="assembly",
                   category="household", dims=Dimensions(0.118, W, depth=D), mass_kg=0.35, static=False,
                   material="steel",
                   description="形は飲食店のテーブルに置く一般的なステンレスの紙ナプキン立て（140 × 70 mm・高さ 100 mm、前後の板で"
                               "立てた紙ナプキンを挟む）で、寸法・質量は代表値。",
                   tags=["紙ナプキン", "ナプキン立て", "ナプキンホルダー", "卓上", "ファミレス", "napkin holder",
                         "napkin dispenser", "paper napkin"],
                   photos=[], colors=Colors(label_base=CHROME), images=[], parts=parts)


def toothpick_holder() -> Product:
    """つまようじ入れ（ガラスの筒にようじ、ふた付き）。"""
    parts = [Part("Body", "cylinder", [0.035, 0.035, 0.06], [0, 0, 0.03], color="#EAF2F5", finish="glass",
                  material="glass", thin_walled=True),
             Part("Picks", "cylinder", [0.026, 0.026, 0.054], [0, 0, 0.003 + 0.027], color="#E7D3A8",
                  finish="matte", collision=False, material="wood"),
             _cyl("Lid", (0.038, 0.038, 0.012), (0, 0, 0.066), "#2E2E2E", "plastic")]
    return Product(slug="toothpick_holder", name="つまようじ入れ", shape_class="assembly", category="household",
                   dims=Dimensions(0.072, 0.038, depth=0.038), mass_kg=0.08, static=False, material="glass",
                   description="形は飲食店のテーブルに置く一般的なつまようじ入れ（直径 35 mm・高さ 60 mm のガラスの筒にようじ、"
                               "樹脂のふた）で、寸法・質量は代表値。",
                   tags=["つまようじ", "ようじ入れ", "卓上", "定食屋", "ファミレス", "toothpick holder", "toothpicks"],
                   photos=[], colors=Colors(label_base="#EAF2F5"), images=[], parts=parts)


def _slip(seed: int) -> np.ndarray:
    """注文伝票（卓番・品名・数量）。"""
    c = Canvas(75, 180, 10, "#FFFFFF", seed)
    c.rect(0, 0, 75, 18, fill="#2E6FB8")
    c.text(37.5, 9, "御会計伝票", 7, "#FFFFFF", 900)
    c.text(8, 26, "卓番 12   2名", 5, INK, 700, anchor="lm")
    for k, (s, n) in enumerate((("ハンバーグ", "1"), ("オムライス", "1"), ("ドリンクバー", "2"), ("パフェ", "1"))):
        y = 40 + k * 14
        c.line([(4, y + 6), (71, y + 6)], "#9EC1E6", 0.4)
        c.text(8, y, s, 5.2, "#203A70", 700, anchor="lm")
        c.text(68, y, n, 5.2, "#203A70", 700, anchor="rm")
    c.text(37.5, 165, "レジでお支払いください", 4.4, INK, 700)
    return _face(c.array(), "paper", seed, 0.4, 3)


def order_slip_holder() -> Product:
    """伝票立て（樹脂の台に透明な筒、伝票を差す）。"""
    images = [_slip(6831)]
    parts = [_cyl("Base", (0.05, 0.05, 0.012), (0, 0, 0.006), BLACK, "plastic"),
             Part("Tube", "cylinder", [0.026, 0.026, 0.11], [0, 0.012, 0.012 + 0.055], color="#EAF2F5",
                  finish="glass", material="plastic", thin_walled=True),
             Part("Slip", "box", [0.075, 0.001, 0.18], [0, -0.0015, 0.012 + 0.09], color="#FFFFFF",
                  finish="matte", faces={"front": 0}, collision=False, material="paper", bevel=0)]
    return Product(slug="order_slip_holder", name="伝票立て（注文伝票付き）", shape_class="assembly",
                   category="household", dims=Dimensions(0.192, 0.075, depth=0.05), mass_kg=0.07, static=False,
                   material="plastic",
                   description="形は飲食店のテーブルに置く一般的な伝票立て（直径 50 mm の台に高さ 110 mm の透明な筒）に、"
                               "幅 75 mm の注文伝票を差したもので、寸法・質量は代表値。伝票の内容は架空。",
                   tags=["伝票", "伝票立て", "伝票差し", "卓上", "ファミレス", "居酒屋", "order slip holder",
                         "check holder", "bill holder"],
                   photos=[], colors=Colors(label_base="#FFFFFF"), images=images, parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    booth_seat, family_table_4, family_table_2, restaurant_chair, kids_high_chair, zataku_table, zabuton,
    high_counter_table, call_bell, menu_stand, condiment_set, napkin_holder, toothpick_holder, order_slip_holder)}
