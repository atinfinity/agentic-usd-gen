"""架空の商品のデザイン: 大きいペットボトルの飲料。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors
from .base import Product, label_canvas, revolve
from .forms import Profile, RevolveForm, _arc
from .paint import Canvas, finish, mix
from .products import INK, _bottle_back


def _big_pet(H: float, D: float, *, shoulder_h: float, label: tuple[float, float], liquid_top: float,
             grip: tuple[float, float] | None = None, ribs: list[tuple[float, float]] = (), petaloid: bool = False,
             neck_r: float = 0.0125, cap_h: float = 0.020, cap_r: float = 0.0150,
             square: float | None = None) -> RevolveForm:
    """大きい PET ボトル。底 → 直胴（任意でグリップのくびれ・横リブ）→ 肩（cos）→ 首 → キャップ。
    petaloid=True は炭酸用の花形の底（5 本の脚）。square は角形ボトルの断面（超楕円の指数）。"""
    R = D / 2
    cap_z = H - cap_h
    neck_z = cap_z - 0.016
    sh_z = neck_z - shoulder_h
    if petaloid:
        base_h = 0.034
        body: Profile = [(0.0, R * 0.50)] + _arc(0.0, 0.008, R * 0.50, R * 0.84, 8, "out")[1:] \
            + _arc(0.008, base_h, R * 0.84, R, 14, "out")[1:]
    else:
        base_h = 0.010
        body = [(0.0, R * 0.82)] + _arc(0.002, base_h, R * 0.92, R, 10, "out")[1:]
    for z in np.linspace(base_h + 0.001, sh_z, 220):
        r = R
        if grip and grip[0] < z < grip[1]:
            r -= 0.0065 * math.sin((z - grip[0]) / (grip[1] - grip[0]) * math.pi)
        for z0, z1 in ribs:
            if z0 < z < z1:
                r -= 0.0014 * (0.5 - 0.5 * math.cos((z - z0) / (z1 - z0) * 2 * math.pi))
        body.append((float(z), r))
    body += _arc(sh_z, neck_z, R, neck_r, 50, "cos")[1:]
    body += [(neck_z + 0.004, neck_r), (neck_z + 0.0045, neck_r + 0.0035), (neck_z + 0.0065, neck_r + 0.0035),
             (neck_z + 0.007, neck_r), (cap_z, neck_r)]
    cap: Profile = [(cap_z, cap_r), (H - 0.0015, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, label, liquid_top, square=square,
                       lobes=[5, base_h, 0.42] if petaloid else None)


def _ribs(z0: float, n: int, pitch: float = 0.010) -> list[tuple[float, float]]:
    return [(z0 + k * pitch, z0 + k * pitch + pitch * 0.7) for k in range(n)]


def _back(c: Canvas, W: float, H: float, name: str, materials: str, vol: str, nutrition, bg="#FFFFFF", extra=()):
    c.rect(0.25 * W - 36, 3, 0.25 * W + 36, H - 3, fill=bg, radius=2)
    _bottle_back(c, 0.25 * W, 6, 66, name, materials, 2.4,
                 extra=[("内容量", vol), ("賞味期限", "キャップに記載"), *extra], nutrition=nutrition)
    c.rect(0.5 * W - 18, 4, 0.5 * W + 18, H - 4, fill="#FFFFFF", radius=2)
    c.barcode(0.5 * W - 15, 8, 30, 18)
    # 識別表示はバーコード（数字の下端 30 mm）と下の注意書き（上端 H - 14 mm）の間に収める。低いラベルでは小さくする
    top, room = 30.0, H - 14 - 30.0
    s = min(10.0, room / 1.3)
    cy = top + (room - 1.3 * s) / 2 + 0.45 * s
    c.recycle(0.5 * W - 0.8 * s, cy, s, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 0.8 * s, cy, s, "プラ", INK, sub="ラベル")
    c.text(0.5 * W, H - 12, "開栓後は冷蔵し", 2.2, INK, 700)
    c.text(0.5 * W, H - 8, "お早めにお飲みください", 2.2, INK, 700)


def green_tea_pet_2l() -> Product:
    form = _big_pet(0.315, 0.105, shoulder_h=0.062, label=(0.140, 0.208), liquid_top=0.262,
                    grip=(0.040, 0.120), ribs=_ribs(0.012, 2) + _ribs(0.120, 2), square=5.0)
    cream, green, dark = "#F4F1E0", "#3E8E41", "#1F4D22"
    liquid = "#B9C46A"
    c = label_canvas(form, cream, seed=3001)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.photo("tea_field", 0, H * 0.6, W, H, crop=(0, 0.35, 1, 0.95))
    c.gradient(0, H * 0.55, W, H * 0.66, cream, mix(cream, green, 0.25))
    c.rect(0, 0, W, 7, fill=green)
    c.text(fx, 3.5, "JAPANESE GREEN TEA  2L", 3.6, "#FFFFFF", 800, spacing=1.0)
    c.rect(fx - 30, 10, fx + 30, 58, fill="#FFFFFF", radius=4)
    c.vtext(fx + 8, 13, "緑茶", 20, dark, 900, gap=0.1)
    c.vtext(fx - 14, 14, "国産茶葉100%", 5.0, green, 700)
    c.vtext(fx - 22, 14, "香り立つ", 4.2, dark, 700)
    c.rect(fx - 24, H - 10, fx + 24, H - 3, fill=green, radius=3)
    c.text(fx, H - 6.5, "お徳用  2L", 4.4, "#FFFFFF", 900)
    _back(c, W, H, "緑茶（清涼飲料水）", "緑茶（国産）／ビタミンC", "2L",
          [("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
           ("炭水化物", "0g"), ("食塩相当量", "0.02g")], bg=cream)
    label = finish(c.array(), "film", 3001, 0.8)
    return Product(slug="green_tea_pet_2l", name="緑茶 2L", category="beverage", mass_kg=2.06, capacity_ml=2000,
                   material="PET",
                   description="形は一般的な 2L の茶飲料用 PET ボトル（角形、高さ 315 mm・胴の幅 105 mm、下部にグリップのくびれ）で、"
                               "寸法・質量は代表値。",
                   tags=["緑茶", "お茶", "大容量", "2L", "ペットボトル", "green tea", "PET bottle"], photos=["tea_field"],
                   colors=Colors(cap=green, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def barley_tea_pet_2l() -> Product:
    form = _big_pet(0.315, 0.105, shoulder_h=0.062, label=(0.140, 0.208), liquid_top=0.262,
                    grip=(0.040, 0.120), ribs=_ribs(0.012, 2) + _ribs(0.120, 2), square=5.0)
    straw, brown, dark, sky = "#FFF6DC", "#B5651D", "#5A3210", "#CFE8F7"
    liquid = "#A8662A"
    c = label_canvas(form, straw, seed=3011)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H * 0.55, sky, "#FFFFFF")
    c.rect(0, H * 0.55, W, H, fill="#E9C46A")
    for k in range(int(W / 4)):  # 麦の穂
        x = k * 4 + (k % 3)
        c.line([(x, H), (x + 1.5, H * 0.62)], mix("#C9962E", dark, 0.2), 0.5)
        c.ellipse(x + 0.6, H * 0.58, x + 2.6, H * 0.66, fill="#D9A441")
    c.rect(0, 0, W, 7, fill=brown)
    c.text(fx, 3.5, "ROASTED BARLEY TEA  2L", 3.6, "#FFFFFF", 800, spacing=1.0)
    c.ellipse(fx - 30, 9, fx + 30, 52, fill="#FFFFFF")
    c.text(fx, 24, "麦茶", 17, dark, 900)
    c.text(fx, 38, "六条大麦  香ばし焙煎", 4.4, brown, 800)
    c.text(fx, 45, "カフェインゼロ", 4.0, "#C0392B", 900)
    c.rect(fx - 24, H - 10, fx + 24, H - 3, fill=brown, radius=3)
    c.text(fx, H - 6.5, "家族の  2L", 4.4, "#FFFFFF", 900)
    _back(c, W, H, "麦茶（清涼飲料水）", "大麦（国産）／ビタミンC", "2L",
          [("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
           ("炭水化物", "0g"), ("食塩相当量", "0.02g"), ("カフェイン", "0mg")], bg=straw)
    label = finish(c.array(), "film", 3011, 0.8)
    return Product(slug="barley_tea_pet_2l", name="麦茶 2L", category="beverage", mass_kg=2.06, capacity_ml=2000,
                   material="PET",
                   description="形は一般的な 2L の茶飲料用 PET ボトル（角形、高さ 315 mm・胴の幅 105 mm、下部にグリップのくびれ）で、"
                               "寸法・質量は代表値。",
                   tags=["麦茶", "お茶", "カフェインゼロ", "大容量", "2L", "ペットボトル", "barley tea", "PET bottle"],
                   photos=[], colors=Colors(cap=brown, liquid=liquid, label_base=straw),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def mineral_water_pet_2l() -> Product:
    form = _big_pet(0.315, 0.105, shoulder_h=0.065, label=(0.150, 0.205), liquid_top=0.258,
                    grip=(0.050, 0.130), ribs=_ribs(0.012, 3) + _ribs(0.132, 2), square=5.0)
    sky, blue = "#DDEFF8", "#1F6FA8"
    c = label_canvas(form, sky, seed=3021)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.photo("lake", 0, 0, W, H, crop=(0, 0.15, 1, 0.75))
    c.gradient(0, 0, W, 8, "#FFFFFF", mix("#FFFFFF", sky, 0.6))
    c.text(fx, 4, "NATURAL MINERAL WATER  2L", 3.4, blue, 800, spacing=0.6)
    c.rect(fx - 34, 10, fx + 34, 34, fill=(255, 255, 255), radius=4)
    c.text(fx, 19, "天然水", 11, blue, 900)
    c.text(fx, 29, "ナチュラルミネラルウォーター", 3.8, blue, 700)
    c.rect(fx - 26, H - 10, fx + 26, H - 3, fill=blue, radius=3)
    c.text(fx, H - 6.5, "軟水  硬度 約30mg/L", 3.6, "#FFFFFF", 800)
    _back(c, W, H, "ナチュラルミネラルウォーター", "水（鉱水）", "2L",
          [("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("ナトリウム", "0.6mg"), ("カルシウム", "0.9mg")],
          extra=[("採水地", "架空の山の湧水")])
    label = finish(c.array(), "film", 3021, 0.8)
    return Product(slug="mineral_water_pet_2l", name="天然水 2L", category="beverage", mass_kg=2.05, capacity_ml=2000,
                   material="PET",
                   description="形は一般的な 2L の水用 PET ボトル（角形、高さ 315 mm・胴の幅 105 mm、グリップのくびれと横リブ）で、"
                               "寸法・質量は代表値。",
                   tags=["水", "ミネラルウォーター", "天然水", "大容量", "2L", "ペットボトル", "mineral water", "PET bottle"],
                   photos=["lake"], colors=Colors(cap="#F4F6F8", label_base=sky),
                   **revolve(form, label=label, body_fill=None))


def cola_pet_1500ml() -> Product:
    form = _big_pet(0.310, 0.092, shoulder_h=0.095, label=(0.120, 0.180), liquid_top=0.252, petaloid=True,
                    cap_r=0.0148)
    red, dark, white = "#4E342E", "#2A1A16", "#FFF3DC"  # こげ茶とクリーム色（名前は元のまま使う）
    amber = "#F2A93B"
    liquid = "#3A1A0E"
    c = label_canvas(form, red, seed=3031)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#5D4037", dark)
    for k in range(9):  # 泡
        x = (k * 37.0) % W
        if abs(x + 2 - fx) < 24:  # 正面の文字（COLA・コーラ・ZESTY SPARK）に重ねない
            continue
        c.ellipse(x, H * 0.55 - k % 3 * 6, x + 4 + k % 3, H * 0.55 - k % 3 * 6 + 4 + k % 3, outline=mix(red, white, 0.5),
                  width=0.4)
    c.rect(0, 0, W, 2.5, fill=amber)
    c.rect(0, H - 2.5, W, H, fill=amber)
    c.rect(fx - 26, H - 21, fx + 26, H - 12, fill=amber, radius=4.5)
    c.text(fx, H - 16.5, "強炭酸", 4.4, dark, 900)
    c.text(fx, 13, "COLA", 13, white, 900, spacing=2.0)
    c.text(fx, 26, "コーラ", 8.0, white, 900)
    c.text(fx, 34, "ZESTY SPARK", 3.4, amber, 800, spacing=0.8)
    c.text(fx, H - 7, "炭酸飲料  1.5L", 3.6, white, 900)
    _back(c, W, H, "炭酸飲料", "糖類（果糖ぶどう糖液糖、砂糖）／炭酸、カラメル色素、酸味料、香料、カフェイン", "1.5L",
          [("栄養成分表示 100ml当たり", ""), ("エネルギー", "45kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
           ("炭水化物", "11.3g"), ("食塩相当量", "0g")])
    label = finish(c.array(), "film", 3031, 0.8)
    return Product(slug="cola_pet_1500ml", name="コーラ 1.5L", category="beverage", mass_kg=1.56, capacity_ml=1500,
                   material="PET",
                   description="形は一般的な 1.5L の炭酸飲料用 PET ボトル（高さ 310 mm・胴径 92 mm、底は 5 本脚の花形のペタロイド）で、"
                               "寸法・質量は代表値。",
                   tags=["コーラ", "炭酸飲料", "大容量", "1.5L", "ペットボトル", "cola", "PET bottle"], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base=red),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def orange_juice_pet_1l() -> Product:
    form = _big_pet(0.250, 0.085, shoulder_h=0.060, label=(0.060, 0.160), liquid_top=0.205,
                    ribs=_ribs(0.012, 3), neck_r=0.0135, cap_r=0.0165, cap_h=0.021)
    orange, leaf, cream, dark = "#F57C00", "#2E7D32", "#FFF5E1", "#8A3B00"
    liquid = "#F7A21B"
    c = label_canvas(form, cream, seed=3041)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFDF4", "#FFE7B8")
    c.rect(0, 0, W, 8, fill=orange)
    c.text(fx, 4, "100% ORANGE JUICE", 3.6, "#FFFFFF", 800, spacing=1.0)

    def orange_fruit(cx: float, cy: float, r: float, cut: bool = False):
        c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#F28C1A")
        if cut:
            c.ellipse(cx - r * 0.88, cy - r * 0.88, cx + r * 0.88, cy + r * 0.88, fill="#FFD27A")
            for k in range(10):
                a = k * 2 * math.pi / 10
                b = a + 2 * math.pi / 10 * 0.8
                c.polygon([(cx, cy), (cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8),
                           (cx + math.cos(b) * r * 0.8, cy + math.sin(b) * r * 0.8)], fill="#FBB040")
        else:
            c.ellipse(cx - r * 0.55, cy - r * 0.65, cx - r * 0.1, cy - r * 0.25, fill="#F8B04E")
            c.polygon([(cx, cy - r), (cx + r * 0.6, cy - r * 1.35), (cx + r * 0.2, cy - r * 0.95)], fill=leaf)

    orange_fruit(fx - 12, H * 0.68, 14)
    orange_fruit(fx + 13, H * 0.74, 11, cut=True)
    c.text(fx, H * 0.86 + 6, "※イメージ図", 1.8, INK, 500)
    c.text(fx, 20, "オレンジ", 10, orange, 900)
    c.text(fx, 33, "果汁100%", 7.0, dark, 900)
    c.text(fx, 41, "濃縮還元  ストレート感", 3.2, dark, 700)
    c.rect(fx - 20, H - 9, fx + 20, H - 2.5, fill=orange, radius=3)
    c.text(fx, H - 5.8, "要冷蔵  1L", 3.8, "#FFFFFF", 900)
    _back(c, W, H, "オレンジジュース（濃縮還元）", "オレンジ（ブラジル、アメリカ）／香料", "1L",
          [("栄養成分表示 200ml当たり", ""), ("エネルギー", "88kcal"), ("たんぱく質", "1.4g"), ("脂質", "0g"),
           ("炭水化物", "20.6g"), ("食塩相当量", "0g"), ("ビタミンC", "80mg")], bg="#FFFFFF",
          extra=[("保存方法", "要冷蔵（10℃以下）")])
    label = finish(c.array(), "film", 3041, 0.8)
    return Product(slug="orange_juice_pet_1l", name="オレンジ 100% 1L", category="beverage", mass_kg=1.08,
                   capacity_ml=1000, material="PET",
                   description="形は一般的な 1L の果汁飲料用 PET ボトル（高さ 250 mm・胴径 85 mm、広めの口）で、寸法・質量は代表値。",
                   tags=["オレンジジュース", "果汁100%", "ジュース", "1L", "ペットボトル", "orange juice", "PET bottle"],
                   photos=[], colors=Colors(cap=orange, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


PRODUCTS = {f.__name__: f for f in (green_tea_pet_2l, barley_tea_pet_2l, mineral_water_pet_2l, cola_pet_1500ml,
                                    orange_juice_pet_1l)}
