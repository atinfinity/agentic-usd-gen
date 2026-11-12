"""架空の商品のデザイン: コンビニの飲料。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .forms import RevolveForm, _arc
from .paint import Canvas, finish, mix
from .products import INK, steam, _bottle_back, _box, _can_top, _cyl, _face, back_info

ALCOHOL_NOTE = "お酒は20歳になってから。飲酒運転は法律で禁止されています。妊娠中・授乳期の飲酒は、胎児・乳児の発育に悪影響を与えるおそれがあります。"


def _alcohol_mark(c: Canvas, cx: float, cy: float, s: float, color: str = "#FFFFFF", bg: str = "#C62828"):
    """お酒の注意マーク（丸に「お酒」）。"""
    c.ellipse(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2, fill=bg, outline=color, width=s * 0.06)
    c.text(cx, cy, "お酒", s * 0.34, color, 900)


# ---------------------------------------------------------------- 缶


def energy_drink_can_250ml() -> Product:
    form = forms.aluminum_can(0.134, 0.053, top_d=0.050, label_margin=0.007)
    black, lime, silver, white = "#111417", "#B6F23A", "#C9CED3", "#FFFFFF"
    c = label_canvas(form, black, seed=2001)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#1C2126", "#07090B")
    for k in range(9):  # 斜めの帯
        x = fx - 40 + k * 10
        c.polygon([(x, H), (x + 4, H), (x + 22, 0), (x + 18, 0)], fill=mix(lime, black, 0.82))
    c.polygon([(fx - 4, 10), (fx + 8, 10), (fx + 1, 34), (fx + 9, 34), (fx - 7, 66), (fx - 2, 40), (fx - 10, 40)],
              fill=lime)
    c.vtext(fx - 15, 10, "エナジー", 7.2, white, 900, gap=0.02)
    c.vtext(fx + 16, 10, "ドリンク", 7.2, white, 900, gap=0.02)
    c.text(fx, 74, "ENERGY", 6.4, lime, 900, spacing=0.6)
    c.text(fx, 82, "アルギニン  カフェイン配合", 2.8, silver, 700)
    c.rect(fx - 16, 86, fx + 16, 92, fill=lime, radius=3)
    c.text(fx, 89, "炭酸飲料  250ml", 3.2, black, 900)
    c.rect(0, 0, W, 2, fill=lime)
    c.rect(0, H - 2, W, H, fill=lime)
    c.vtext(0.5 * W, 8, "GO FURTHER", 3.2, lime, 800)
    _bottle_back(c, 0.25 * W, 6, 34, "炭酸飲料", "果糖ぶどう糖液糖、砂糖／炭酸、酸味料、アルギニン、香料、カフェイン、ナイアシン、"
                 "着色料（カラメル）、ビタミンB6、ビタミンB2、ビタミンB12", 1.5, color=white, bg=black,
                 extra=[("内容量", "250ml"), ("賞味期限", "缶底に記載")],
                 nutrition=[("栄養成分表示 1本当たり", ""), ("エネルギー", "115kcal"), ("炭水化物", "28.5g"),
                            ("食塩相当量", "0.3g"), ("カフェイン", "80mg")], notice_color=white)
    c.text(0.25 * W, H - 6, "カフェインを多く含むため、", 1.6, lime, 700)
    c.text(0.25 * W, H - 3.6, "小児・妊婦の方はお控えください", 1.6, lime, 700)
    c.rect(0.5 * W - 13, 40, 0.5 * W + 13, 58, fill=white)
    c.barcode(0.5 * W - 11, 41.5, 22, 14)
    c.recycle(0.5 * W, 70, 7, "アルミ", white, kind="can")
    label = finish(c.array(), "metal", 2001, 0.7)
    return Product(slug="energy_drink_can_250ml", name="エナジードリンク 250ml 缶", category="beverage", mass_kg=0.27,
                   capacity_ml=250, material="aluminum",
                   description="形は一般的な 250ml のスリム缶（高さ 134 mm・胴径 53 mm）で、寸法・質量は代表値。",
                   tags=["エナジードリンク", "炭酸飲料", "スリム缶", "アルミ缶", "energy drink", "can"], photos=[],
                   colors=Colors(cap="#BFC2C5", label_base=black), **revolve(form, label=label, top=_can_top(form, 2002)))


def beer_can_350ml() -> Product:
    form = forms.aluminum_can(0.122, 0.066, top_d=0.054, label_margin=0.008)
    gold, navy, cream, white = "#D8A533", "#14284B", "#FFF6DC", "#FFFFFF"
    c = label_canvas(form, gold, seed=2011)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F0C14E", "#B9831F")
    c.pattern(0, 0, W, H, "dots", mix("#F0C14E", "#FFFFFF", 0.25), 4, 0.35)
    c.rect(0, 0, W, 10, fill=navy)
    c.rect(0, H - 8, W, H, fill=navy)
    c.text(fx, 5, "PREMIUM LAGER", 3.4, gold, 800, spacing=0.8)
    c.ellipse(fx - 22, 14, fx + 22, 58, fill=cream, outline=navy, width=1.0)
    c.ellipse(fx - 19, 17, fx + 19, 55, outline=gold, width=0.5)
    for k in range(-2, 3):  # 麦の穂
        x = fx + k * 5.5
        c.line([(x, 50), (x + k * 0.8, 30)], navy, 0.4)
        for j in range(5):
            y = 31 + j * 3.4
            c.ellipse(x - 1.6 + k * 0.6, y, x + 0.2 + k * 0.6, y + 2.6, fill=gold)
            c.ellipse(x - 0.2 + k * 0.6, y + 1.2, x + 1.6 + k * 0.6, y + 3.8, fill=gold)
    c.text(fx, 22, "麦芽100%", 3.6, navy, 900)
    c.text(fx, 68, "ビール", 13, navy, 900)
    c.text(fx, 80, "BEER", 6.0, navy, 900, spacing=1.6)
    c.text(fx, H - 4, "生  350ml  アルコール分5%", 3.2, white, 800)
    _alcohol_mark(c, fx + 26, 66, 8)
    c.vtext(0.5 * W, 14, "すっきりした飲みごたえ", 3.4, navy, 800)
    _bottle_back(c, 0.25 * W, 13, 42, "ビール", "麦芽（外国製造）、ホップ", 1.8, color=navy, bg=cream,
                 extra=[("内容量", "350ml"), ("アルコール分", "5%"), ("賞味期限", "缶底に記載"),
                        ("保存方法", "直射日光・高温を避けてください")], notice_color=navy)
    c.paragraph(0.25 * W - 21, 58, 0.25 * W + 21, ALCOHOL_NOTE, 1.7, navy, 700)
    c.rect(0.5 * W - 14, 54, 0.5 * W + 14, 72, fill=white)
    c.barcode(0.5 * W - 12, 55.5, 24, 14)
    c.recycle(0.5 * W + 10, 82, 7, "アルミ", navy, kind="can")
    _alcohol_mark(c, 0.5 * W - 10, 82, 7)
    label = finish(c.array(), "metal", 2011, 0.7)
    return Product(slug="beer_can_350ml", name="ビール 350ml 缶", category="beverage", mass_kg=0.368,
                   capacity_ml=350, material="aluminum",
                   description="形は一般的な 350ml のアルミ缶（高さ 122 mm・胴径 66 mm、上すぼまりのネック）で、寸法・質量は代表値。",
                   tags=["ビール", "お酒", "アルコール", "酒類", "アルミ缶", "beer", "alcohol", "can"], photos=[],
                   colors=Colors(cap="#BFC2C5", label_base=gold), **revolve(form, label=label, top=_can_top(form, 2012)))


def chuhai_can_500ml() -> Product:
    form = forms.aluminum_can(0.168, 0.066, top_d=0.054, label_margin=0.008)
    silver, yellow, blue, white = "#DDE3E8", "#FFE34D", "#1C5FB8", "#FFFFFF"
    c = label_canvas(form, silver, seed=2021)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F2F5F8", "#BAC3CB")
    c.pattern(0, 0, W, H, "stripes", mix("#F2F5F8", blue, 0.08), 6, 1.0)
    c.rect(0, 0, W, 8, fill=blue)
    c.text(fx, 4, "STRONG  LEMON", 3.4, white, 800, spacing=0.8)
    c.photo("lemon", fx - 26, 12, fx + 26, 64, shape="ellipse", shadow=1.0, crop=(0.08, 0.05, 0.92, 0.95))
    c.text(fx + 22, 63, "※写真はイメージです", 1.5, INK, 500, anchor="lm")
    c.rect(fx - 24, 70, fx + 24, 92, fill=blue, radius=3)
    c.text(fx, 77, "レモン", 7.6, white, 900)
    c.text(fx, 87, "チューハイ", 5.6, yellow, 900)
    c.text(fx, 99, "果汁3%  糖類ゼロ", 3.6, blue, 900)
    c.rect(fx - 20, 104, fx + 20, 112, fill=yellow, radius=4)
    c.text(fx, 108, "アルコール分 7%", 3.8, blue, 900)
    c.text(fx, H - 6, "500ml", 4.6, blue, 900)
    _alcohol_mark(c, fx + 28, 108, 9)
    c.vtext(0.5 * W, 14, "キリッと強炭酸", 4.4, blue, 900)
    _bottle_back(c, 0.25 * W, 13, 42, "リキュール（発泡性）①",
                 "レモン果汁、ウオッカ（国内製造）／炭酸、酸味料、香料、甘味料（アセスルファムK、スクラロース）",
                 1.8, color=blue, extra=[("内容量", "500ml"), ("アルコール分", "7%"), ("果汁", "3%"),
                                         ("賞味期限", "缶底に記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "40kcal"), ("炭水化物", "0.5g"),
                            ("糖類", "0g"), ("食塩相当量", "0.05g")])
    c.paragraph(0.25 * W - 21, 92, 0.25 * W + 21, ALCOHOL_NOTE, 1.7, blue, 700)
    c.rect(0.5 * W - 14, 58, 0.5 * W + 14, 76, fill=white)
    c.barcode(0.5 * W - 12, 59.5, 24, 14)
    c.recycle(0.5 * W + 10, 92, 7, "アルミ", blue, kind="can")
    _alcohol_mark(c, 0.5 * W - 10, 92, 8)
    c.text(0.5 * W, 104, "これはお酒です", 2.8, "#C62828", 900)
    label = finish(c.array(), "metal", 2021, 0.7)
    return Product(slug="chuhai_can_500ml", name="レモンチューハイ 500ml 缶", category="beverage", mass_kg=0.52,
                   capacity_ml=500, material="aluminum",
                   description="形は一般的な 500ml のロング缶（高さ 168 mm・胴径 66 mm、上すぼまりのネック）で、寸法・質量は代表値。",
                   tags=["チューハイ", "酎ハイ", "レモンサワー", "お酒", "アルコール", "酒類", "ロング缶", "chuhai", "lemon",
                         "alcohol", "can"], photos=["lemon"],
                   colors=Colors(cap="#BFC2C5", label_base=silver), **revolve(form, label=label, top=_can_top(form, 2022)))


def _bottle_can(H: float, D: float, *, cap_d: float, cap_h: float) -> RevolveForm:
    """アルミのボトル缶（広口のねじ蓋）。底の丸み → 直胴 → なだらかな肩 → 口のビード → アルミのキャップ。"""
    R, Rc = D / 2, cap_d / 2
    cap_z = H - cap_h
    neck_r = Rc - 0.0012
    sh_z = cap_z - 0.048
    body = [(0.0, R * 0.84)] + _arc(0.0005, 0.007, R * 0.88, R, 10, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, cap_z - 0.010, R, neck_r + 0.0005, 36, "cos")[1:]
    body += [(cap_z - 0.007, neck_r), (cap_z - 0.0065, neck_r + 0.0022), (cap_z - 0.0045, neck_r + 0.0022),
             (cap_z - 0.004, neck_r), (cap_z, neck_r)]
    cap = [(cap_z, Rc), (H - 0.001, Rc), (H, Rc - 0.001)]
    return RevolveForm(body, cap, (0.009, sh_z - 0.002))


def bottle_can_coffee_400ml() -> Product:
    form = _bottle_can(0.167, 0.066, cap_d=0.040, cap_h=0.017)
    black, gold, white = "#121212", "#C9A24D", "#FFFFFF"
    c = label_canvas(form, black, seed=2031)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#262626", "#0B0B0B")
    c.photo("coffee_beans", 0, H * 0.70, W, H, crop=(0, 0.25, 1, 0.7))
    c.gradient(0, H * 0.64, W, H * 0.74, "#141414", "#141414")
    c.rect(0, 3, W, 3.6, fill=gold)
    c.text(fx, 12, "ARTISAN ROAST", 3.6, gold, 800, spacing=0.8)
    c.vtext(fx + 8, 19, "ブラック", 11, white, 900, gap=0.03)
    c.vtext(fx - 9, 20, "無糖", 6.4, gold, 900)
    c.vtext(fx - 9, 40, "香り立つ深煎り", 3.4, white, 700)
    c.rect(fx - 18, 74, fx + 18, 81, fill=gold, radius=3.5)
    c.text(fx, 77.5, "コーヒー  400g", 3.6, black, 900)
    c.text(0.5 * W, 20, "リキャップできる", 3.0, gold, 800)
    c.text(0.5 * W, 25, "ボトル缶", 3.0, gold, 800)
    _bottle_back(c, 0.25 * W, 8, 42, "コーヒー", "コーヒー（コーヒー豆（ブラジル、エチオピア、その他））", 1.8,
                 color=white, bg=black,
                 extra=[("内容量", "400g"), ("賞味期限", "缶の肩に記載"), ("保存方法", "直射日光・高温を避けてください")],
                 nutrition=[("栄養成分表示 100g当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0.1g"), ("脂質", "0g"),
                            ("炭水化物", "0.5g"), ("食塩相当量", "0.03g")], notice_color=white)
    c.rect(0.5 * W - 14, 33, 0.5 * W + 14, 51, fill=white)
    c.barcode(0.5 * W - 12, 34.5, 24, 14)
    c.recycle(0.5 * W - 7, 62, 7, "アルミ", white, kind="can")
    c.recycle(0.5 * W + 7, 62, 7, "アルミ", white, kind="can")
    c.text(0.5 * W + 7, 68.5, "キャップ", 1.6, white, 600)
    c.text(0.5 * W, 74, "開栓後はお早めに", 2.2, gold, 700)
    label = finish(c.array(), "metal", 2031, 0.7)

    t = top_canvas(form, "#B6BBC0", seed=2032)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D3D7DB", "#9EA4A9")
    t.ellipse(0.8, 0.8, d - 0.8, d - 0.8, outline="#868B90", width=0.8)
    t.ellipse(4, 4, d - 4, d - 4, outline="#C5C9CD", width=0.4)
    t.text(d / 2, d * 0.42, "BLACK", 6.0, black, 900, spacing=0.6)
    t.text(d / 2, d * 0.60, "COFFEE", 3.4, "#4A4A4A", 800, spacing=0.6)
    top = finish(t.array(), "metal", 2032, 0.6)
    return Product(slug="bottle_can_coffee_400ml", name="ボトル缶コーヒー ブラック 400g", category="beverage", mass_kg=0.44,
                   capacity_ml=400, material="aluminum",
                   description="形は一般的な 400g のアルミのボトル缶（高さ 167 mm・胴径 66 mm、口径 38 mm のねじ蓋）で、寸法・質量は代表値。",
                   tags=["コーヒー", "缶コーヒー", "ブラック", "無糖", "ボトル缶", "coffee", "black coffee", "bottle can"],
                   photos=["coffee_beans"], colors=Colors(cap="#C3C7CB", label_base=black),
                   **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 瓶


def _drink_bottle(H: float, D: float, *, cap_h: float, cap_r: float, neck_r: float) -> RevolveForm:
    """栄養ドリンクの小びん（茶色のガラス）。底の丸み → 直胴 → 肩 → 細い首 → 口の玉縁 → 金属のキャップ。"""
    R = D / 2
    cap_z = H - cap_h
    sh_z = cap_z - 0.034
    body = [(0.0, R * 0.88)] + _arc(0.0005, 0.005, R * 0.93, R, 8, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, cap_z - 0.010, R, neck_r, 30, "cos")[1:]
    body += [(cap_z - 0.002, neck_r), (cap_z - 0.0015, neck_r + 0.0016), (cap_z, neck_r + 0.0016)]
    cap = [(cap_z, cap_r), (H - 0.0008, cap_r), (H, cap_r - 0.0008)]
    return RevolveForm(body, cap, (0.010, sh_z - 0.002), cap_z - 0.012)


def nutrition_drink_bottle_100ml() -> Product:
    form = _drink_bottle(0.118, 0.039, cap_h=0.013, cap_r=0.0140, neck_r=0.0110)
    white, red, navy, gold = "#FFFFFF", "#D3222A", "#1B2C6B", "#D9A93A"
    c = label_canvas(form, white, seed=2041)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.rect(0, 0, W, 9, fill=navy)
    c.rect(0, H - 9, W, H, fill=navy)
    c.rect(0, 9, W, 10, fill=gold)
    c.rect(0, H - 10, W, H - 9, fill=gold)
    c.text(fx, 4.5, "指定医薬部外品", 3.0, white, 800)
    c.text(fx, 18, "タウリン", 3.6, red, 900)
    c.text(fx, 23, "1000mg配合", 3.6, red, 900)
    c.rect(fx - 17, 26, fx + 17, 46, fill=red, radius=2)
    c.text(fx, 33, "滋養", 6.6, white, 900)
    c.text(fx, 41.5, "ドリンク", 5.2, white, 900)
    c.text(fx, 51, "Vitamin B群", 3.0, navy, 800)
    c.text(fx, H - 4.5, "100mL", 3.4, white, 900)
    c.vtext(0.5 * W, 13, "肉体疲労時の栄養補給", 2.6, navy, 800)
    bx = 0.25 * W
    y = c.table(bx - 18, 12, bx + 18, "1本（100mL）中", [
        ("タウリン", "1000mg"), ("ビタミンB1硝酸塩", "5mg"), ("ビタミンB2リン酸エステル", "5mg"),
        ("ビタミンB6", "5mg"), ("ニコチン酸アミド", "20mg"), ("無水カフェイン", "50mg")], 1.35, navy)
    c.paragraph(bx - 18, y + 0.8, bx + 18, "効能：肉体疲労・病中病後・食欲不振・栄養障害・発熱性消耗性疾患などの場合の栄養補給。"
                "用法：成人（15才以上）1日1回1本を服用してください。", 1.3, INK, 500)
    c.paragraph(bx - 18, H - 17, bx + 18, NOTICE, 1.3, INK, 500)
    c.barcode(0.5 * W - 8, 36, 16, 11)
    c.recycle(0.5 * W, 53, 5.5, "プラ", navy, sub="ラベル")
    label = finish(c.array(), "paper", 2041, 0.5)

    t = top_canvas(form, gold, seed=2042)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#F0C966", "#B8892A")
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline="#8F6A1E", width=0.6)
    t.ellipse(d * 0.18, d * 0.18, d * 0.82, d * 0.82, outline="#E8C46A", width=0.4)
    t.text(d / 2, d / 2, "滋養", 6.4, red, 900)
    top = finish(t.array(), "metal", 2042, 0.6)
    amber = "#5B2A08"
    return Product(slug="nutrition_drink_bottle_100ml", name="栄養ドリンク タウリン1000mg 100mL", category="beverage",
                   mass_kg=0.205, capacity_ml=100, material="glass",
                   description="形は一般的な 100mL の栄養ドリンクの茶色いガラス小びん（高さ 118 mm・胴径 39 mm、金属のキャップ）で、寸法・質量は代表値。",
                   tags=["栄養ドリンク", "ドリンク剤", "指定医薬部外品", "タウリン", "瓶", "energy drink", "nutrition drink"],
                   photos=[], colors=Colors(cap=gold, liquid=amber, label_base=white),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=amber))


# ---------------------------------------------------------------- PET ボトル


def milk_tea_pet_500ml() -> Product:
    form = forms.pet_bottle(0.212, 0.067, shoulder=0.24, cap_h=0.019, cap_r=0.0148, label=(0.040, 0.142),
                            liquid_top=0.176, ribs=(0.010, 0.036))
    cream, brown, red, white = "#F6ECDD", "#7A4A2A", "#B5272D", "#FFFFFF"
    liquid = "#C8A07A"
    c = label_canvas(form, cream, seed=2051)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FBF4EA", "#EFDFC8")
    c.pattern(0, 0, W, H, "dots", mix("#EFDFC8", brown, 0.12), 6, 0.6)
    c.rect(0, 0, W, 7, fill=red)
    c.rect(0, H - 7, W, H, fill=red)
    c.text(fx, 3.5, "ROYAL MILK TEA", 3.2, white, 800, spacing=0.8)
    # ティーカップの絵（受け皿・カップ・取っ手・湯気）
    cx, cy = fx - 14, 40
    c.ellipse(cx - 15, cy + 8, cx + 15, cy + 14, fill=white, outline=brown, width=0.5)
    c.polygon([(cx - 11, cy - 6), (cx + 11, cy - 6), (cx + 8, cy + 9), (cx - 8, cy + 9)], fill=white, outline=brown)
    c.ellipse(cx - 11, cy - 8.5, cx + 11, cy - 3.5, fill=liquid, outline=brown, width=0.5)
    c.ellipse(cx + 8.5, cy - 3, cx + 15, cy + 4, outline=brown, width=0.9)
    c.rect(cx - 9.5, cy + 1, cx + 9.5, cy + 2.2, fill=red)
    steam(c, cx, cy - 11, 10, 9, mix(brown, "#FFFFFF", 0.4), 0.6)
    c.vtext(fx + 16, 12, "ミルク", 8.6, brown, 900, gap=0.03)
    c.vtext(fx + 6, 22, "ティー", 8.6, brown, 900, gap=0.03)
    c.rect(fx - 28, 62, fx + 28, 72, fill=brown, radius=5)
    c.text(fx, 67, "紅茶葉 100%使用  まろやか", 3.6, white, 800)
    c.text(fx, 80, "紅茶飲料", 3.6, brown, 900)
    c.text(fx, 86, "500ml", 4.2, red, 900)
    c.text(fx, H - 3.5, "TEA & MILK", 3.0, white, 700, spacing=0.8)
    c.vtext(0.5 * W, 14, "芳醇なアッサム", 4.0, red, 900)
    _bottle_back(c, 0.25 * W, 11, 46, "紅茶飲料",
                 "牛乳（国内製造）、砂糖、紅茶、全粉乳、脱脂粉乳、デキストリン、食塩／香料、乳化剤、ビタミンC", 1.8,
                 extra=[("内容量", "500ml"), ("賞味期限", "キャップに記載"), ("保存方法", "高温・直射日光を避けてください")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "37kcal"), ("たんぱく質", "0.6g"), ("脂質", "0.6g"),
                            ("炭水化物", "7.3g"), ("食塩相当量", "0.1g")])
    c.barcode(0.5 * W - 13, 50, 26, 16)
    c.recycle(0.5 * W - 6, 78, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 78, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 2051, 0.8)
    return Product(slug="milk_tea_pet_500ml", name="ミルクティー 500ml", category="beverage", mass_kg=0.53,
                   capacity_ml=500, material="PET",
                   description="形は一般的な 500ml の紅茶飲料用 PET ボトル（高さ 212 mm・胴径 67 mm）で、寸法・質量は代表値。",
                   tags=["ミルクティー", "紅茶", "紅茶飲料", "ペットボトル", "milk tea", "tea", "PET bottle"], photos=[],
                   colors=Colors(cap=white, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def sports_drink_pet_500ml() -> Product:
    form = forms.pet_bottle(0.205, 0.069, shoulder=0.24, cap_h=0.019, cap_r=0.0148, label=(0.092, 0.150),
                            liquid_top=0.172, waist=(0.020, 0.085))
    blue, sky, white, navy = "#00897B", "#E0F5F1", "#FFFFFF", "#0B4A43"  # 青緑（名前は元のまま使う）
    lime = "#C6D930"
    liquid = "#EAF1F4"
    c = label_canvas(form, white, seed=2061)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", sky)
    c.rect(0, H - 14, W, H, fill=blue)
    c.rect(0, H - 16, W, H - 14, fill=lime)
    c.pattern(0, H - 13, W, H, "dots", mix(blue, white, 0.35), 3.0, 0.5)
    c.rect(0, 0, W, 6, fill=blue)
    c.text(fx, 3, "SPORTS DRINK", 3.0, white, 800, spacing=0.8)
    c.text(fx, 14, "ミネラル", 6.2, blue, 900)
    c.text(fx, 24, "チャージ", 8.4, navy, 900)
    c.text(fx, 32, "MINERAL CHARGE", 3.6, blue, 800, spacing=1.0)
    c.text(fx, 38, "汗で失われた水分・電解質を補給", 2.8, navy, 700)
    c.text(fx, H - 7, "清涼飲料水  500ml", 3.4, white, 900)
    c.vtext(0.5 * W + 20, 9, "すばやく補給", 4.2, blue, 900)  # バーコード（0.5 W ± 12 mm）の右に離す
    _bottle_back(c, 0.25 * W, 8, 44, "清涼飲料水",
                 "砂糖、果糖ぶどう糖液糖、果汁、食塩／酸味料、香料、塩化K、乳酸Ca、調味料（アミノ酸）、塩化Mg", 1.5,
                 extra=[("内容量", "500ml"), ("賞味期限", "キャップに記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "25kcal"), ("炭水化物", "6.2g"),
                            ("食塩相当量", "0.12g"), ("カリウム", "20mg")])
    # 識別表示が下の帯（H - 16 mm から）にかからないよう、バーコードごと上に寄せる
    c.barcode(0.5 * W - 12, 9, 24, 14)
    c.recycle(0.5 * W - 6, 32, 7, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 32, 7, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 2061, 0.8)
    return Product(slug="sports_drink_pet_500ml", name="スポーツドリンク 500ml", category="beverage", mass_kg=0.53,
                   capacity_ml=500, material="PET",
                   description="形は一般的な 500ml のスポーツドリンク用 PET ボトル（高さ 205 mm・胴径 69 mm、胴にくびれ）で、寸法・質量は代表値。",
                   tags=["スポーツドリンク", "イオン飲料", "清涼飲料水", "ペットボトル", "sports drink", "PET bottle"], photos=[],
                   colors=Colors(cap=blue, liquid=liquid, label_base=white),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


# ---------------------------------------------------------------- 紙パック・カップ


def vegetable_juice_pack_200ml() -> Product:
    W, D, H = 53.0, 40.0, 104.0
    green, red, orange, cream, white = "#2E7D32", "#D84315", "#F57C00", "#FFF8E8", "#FFFFFF"
    s = 12

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, cream, seed)
        f.gradient(0, 0, w, h, "#FFFDF5", "#FBEFD2")
        f.rect(0, 0, w, 6, fill=green)
        return f

    def tomato(f: Canvas, cx: float, cy: float, r: float):
        f.ellipse(cx - r, cy - r * 0.9, cx + r, cy + r * 0.9, fill="#E53935")
        f.ellipse(cx - r * 0.55, cy - r * 0.6, cx - r * 0.1, cy - r * 0.2, fill="#EF7B79")
        for k in range(5):
            a = k * 2 * np.pi / 5
            f.polygon([(cx, cy - r * 0.8), (cx + np.cos(a) * r * 0.5, cy - r * 0.8 + np.sin(a) * r * 0.25),
                       (cx + np.cos(a + 0.4) * r * 0.2, cy - r * 0.8 + np.sin(a + 0.4) * r * 0.1)], fill=green)

    def carrot(f: Canvas, x: float, y: float, L: float):
        f.polygon([(x, y), (x + L * 0.25, y - L * 0.12), (x + L, y + L * 0.02)], fill=orange)
        for k in (-1, 0, 1):
            f.polygon([(x + 0.5, y - 0.5), (x - L * 0.25, y - L * 0.18 + k * L * 0.12),
                       (x - L * 0.15, y - L * 0.02 + k * L * 0.1)], fill="#43A047")

    fr = face(W, H, 2071)
    fr.text(W / 2, 3, "1日分の緑黄色野菜", 2.8, white, 800)
    fr.text(W / 2, 15, "野菜", 10, green, 900)
    fr.text(W / 2, 27, "ジュース", 8.0, green, 900, max_w=W - 8)
    fr.text(W / 2, 35, "砂糖・食塩 不使用", 3.2, red, 900)
    fr.ellipse(4, 40, W - 4, 82, fill="#FFFFFF", outline=mix(green, white, 0.5), width=0.5)
    tomato(fr, W / 2 - 8, 64, 9)
    tomato(fr, W / 2 + 10, 70, 6.5)
    carrot(fr, W / 2 - 4, 52, 24)
    fr.text(W / 2, 80, "※イメージ図", 1.6, INK, 500)
    fr.rect(5, 86, W - 5, 94, fill=green, radius=4)
    fr.text(W / 2, 90, "30品目の野菜  200ml", 3.4, white, 900)
    fr.text(W / 2, 99.5, "VEGETABLE JUICE", 3.0, green, 800, spacing=0.4)

    bk = face(W, H, 2072)
    bk.text(W / 2, 3, "野菜汁 100%", 2.8, white, 800)
    back_info(bk, 3, 8, W - 3, [
        ("名称", "野菜汁（にんじん、トマト）"), ("原材料名", "野菜（にんじん、トマト、ケール、ほうれん草、セロリ、その他）、レモン果汁"),
        ("内容量", "200ml"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温を避けてください")], 2.0,
        [("栄養成分表示 1本当たり", ""), ("エネルギー", "70kcal"), ("たんぱく質", "1.6g"), ("脂質", "0g"),
         ("炭水化物", "16.5g"), ("食塩相当量", "0.0〜0.4g")], green)
    bk.barcode(W / 2 - 16, H - 24, 32, 17)
    rt = face(D, H, 2073)
    rt.vtext(D / 2, 12, "野菜ジュース", 7.2, green, 900, gap=0.04)
    rt.text(D / 2, 82, "よく振って", 3.2, red, 900)
    rt.text(D / 2, 87, "お飲みください", 3.2, red, 900)
    rt.recycle(D / 2, 97, 7, "紙パック", green)
    lf = face(D, H, 2074)
    lf.vtext(D / 2 + 7, 12, "砂糖・食塩不使用", 4.6, red, 900)
    lf.vtext(D / 2 - 6, 12, "緑黄色野菜たっぷり", 4.0, green, 800)
    lf.recycle(D / 2 - 8, 94, 6, "プラ", green, sub="ストロー袋")
    lf.recycle(D / 2 + 8, 94, 6, "紙", green, sub="パック")
    tp = Canvas(W, D, s, cream, 2075)
    tp.gradient(0, 0, W, D, "#FFFDF5", "#F3E6C4")
    tp.ellipse(W * 0.68, D * 0.32, W * 0.68 + 7, D * 0.32 + 7, fill="#E8E2D0", outline="#B8B09A", width=0.4)
    tp.text(W * 0.36, D * 0.42, "賞味期限", 2.6, INK, 700)
    tp.text(W * 0.36, D * 0.6, "2027.03.15", 2.8, INK, 700)
    tp.text(W * 0.74, D * 0.78, "ストロー", 2.0, green, 700)
    bt = Canvas(W, D, s, cream, 2076)
    bt.gradient(0, 0, W, D, "#FBEFD2", "#F1E2BE")
    bt.text(W / 2, D / 2, NOTICE, 1.6, INK, 500, max_w=W - 4)
    imgs = [_face(a.array(), "paper", 2077 + i) for i, a in enumerate((fr, bk, rt, lf, tp, bt))]
    # 裏面に貼り付けたストロー（透明の袋に入った伸縮ストロー）
    yb = D / 2000 + 0.0022
    parts = [_box("Straw", (0.0045, 0.0040, 0.090), (0.012, yb, 0.052), "#F4F4F0", "plastic", rotation=[0, 6, 0],
                  collision=False),
             _box("StrawBag", (0.0085, 0.0044, 0.098), (0.012, yb, 0.052), "#F2F6F8", "glass", thin_walled=True, rotation=[0, 6, 0],
                  collision=False)]
    return Product(slug="vegetable_juice_pack_200ml", name="野菜ジュース 200ml 紙パック", shape_class="box",
                   category="beverage", dims=Dimensions(0.104, 0.053, depth=0.040), mass_kg=0.215, capacity_ml=200,
                   material="paper",
                   description="形は一般的な 200ml のブリック型紙パック（高さ 104 mm・幅 53 mm・奥行き 40 mm、裏面にストロー付き）で、寸法・質量は代表値。",
                   tags=["野菜ジュース", "野菜汁", "紙パック", "トマト", "にんじん", "vegetable juice", "juice box"], photos=[],
                   colors=Colors(label_base=cream), images=imgs, parts=parts,
                   faces={"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5})


def chilled_cup_coffee_200ml() -> Product:
    form = forms.paper_cup(0.104, 0.070, 0.056, lid_h=0.003, lid_overhang=0.0012, rim_h=0.004)
    brown, cream, white, caramel = "#4B2C1A", "#F5EBDD", "#FFFFFF", "#C98A4B"
    c = label_canvas(form, cream, seed=2081)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FBF5EC", "#E9D7BF")
    c.photo("latte", fx - 26, 8, fx + 26, 56, shape="ellipse", shadow=1.2, crop=(0.12, 0.08, 0.88, 0.92))
    c.text(fx + 24, 55, "※写真はイメージです", 1.5, INK, 500, anchor="lm")
    c.text(fx, 64, "カフェラテ", 8.4, brown, 900)
    c.text(fx, 72, "CAFFE LATTE", 3.4, caramel, 800, spacing=1.0)
    c.rect(fx - 24, 76, fx + 24, 84, fill=brown, radius=4)
    c.text(fx, 80, "エスプレッソ×北海道産牛乳", 3.0, white, 800, max_w=46)
    c.text(fx, H - 5, "要冷蔵  200ml", 3.2, brown, 900)
    c.rect(0, 0, W, 3, fill=brown)
    c.vtext(0.5 * W, 10, "ストローを挿して", 3.2, brown, 800)
    _bottle_back(c, 0.25 * W, 7, 42, "乳飲料", "牛乳（国内製造）、砂糖、コーヒー、脱脂粉乳／乳化剤、香料", 1.7,
                 extra=[("内容量", "200ml"), ("無脂乳固形分", "6.0%"), ("乳脂肪分", "1.8%"), ("賞味期限", "ふたに記載"),
                        ("保存方法", "要冷蔵（10℃以下）")],
                 nutrition=[("栄養成分表示 1本当たり", ""), ("エネルギー", "128kcal"), ("たんぱく質", "5.4g"), ("脂質", "4.6g"),
                            ("炭水化物", "16.3g"), ("食塩相当量", "0.2g")], color=brown)
    c.barcode(0.5 * W - 11, 46, 22, 14)
    c.recycle(0.5 * W - 6, 72, 7, "プラ", brown, sub="容器")
    c.recycle(0.5 * W + 6, 72, 7, "プラ", brown, sub="ふた")
    label = finish(c.array(), "film", 2081, 0.7)

    t = top_canvas(form, cream, seed=2082)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FBF5EC", "#EADBC4")
    t.ellipse(0.8, 0.8, d - 0.8, d - 0.8, outline=brown, width=1.2)
    t.text(d / 2, d * 0.30, "CAFFE LATTE", 5.2, brown, 900, spacing=0.8)
    t.text(d / 2, d * 0.42, "カフェラテ", 6.8, brown, 900)
    t.ellipse(d * 0.62, d * 0.55, d * 0.62 + 9, d * 0.55 + 9, fill="#E8DCC8", outline=caramel, width=0.6)
    t.text(d * 0.62 + 4.5, d * 0.55 + 4.5, "ここ", 2.4, brown, 800)
    t.text(d * 0.36, d * 0.62, "ストロー差し口", 2.6, brown, 800)
    t.text(d / 2, d * 0.80, "賞味期限 2026.11.05", 3.0, INK, 600)
    top = finish(t.array(), "film", 2082, 0.5)
    return Product(slug="chilled_cup_coffee_200ml", name="カフェラテ チルドカップ 200ml", category="beverage", mass_kg=0.225,
                   capacity_ml=200, material="plastic",
                   description="形は一般的な 200ml のチルドカップ飲料（高さ 104 mm・口径 70 mm・底径 56 mm、ふたはシール）で、寸法・質量は代表値。",
                   tags=["カフェラテ", "コーヒー", "チルドカップ", "乳飲料", "要冷蔵", "caffe latte", "chilled cup", "coffee"],
                   photos=["latte"], colors=Colors(cap=cream, label_base=cream), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 乳酸菌飲料 5 本パック（部品の組み合わせ）


def lactic_drink_5pack() -> Product:
    n, bd, gap = 5, 0.037, 0.0006  # 本数、胴径、すき間
    red, white, pink, foil = "#1976D2", "#FFFFFF", "#E6F1FB", "#C7CDD2"  # 青（名前は元のまま使う）
    L = n * bd + (n - 1) * gap
    H = 0.092
    # ボトルの断面 (半径, 高さ) [m]。まっすぐな胴 → なで肩 → 口（くびれは付けない）
    keys = [(0.0, 0.0), (0.0172, 0.0), (0.0185, 0.003), (0.0185, 0.064), (0.0130, 0.0845), (0.0130, 0.0895),
            (0.0, 0.0895)]
    pts = [keys[0], keys[1]]
    for (r0, z0), (r1, z1) in zip(keys[1:-2], keys[2:-1]):
        steps = 1 if r0 == r1 else 8  # 太さの変わる区間は、なめらかな S 字（余弦）でつなぐ
        for t in np.linspace(0, 1, steps + 1)[1:]:
            e = (1 - np.cos(np.pi * t)) / 2
            pts.append((r0 + (r1 - r0) * e, z0 + (z1 - z0) * t))
    pts.append(keys[-1])
    bh = keys[-1][1]
    prof = [[round(float(r) / (bd / 2), 5), round(float(z) / bh, 5)] for r, z in pts]
    parts: list[Part] = []
    for k in range(n):
        x = -L / 2 + bd / 2 + k * (bd + gap)
        parts += [Part(f"Bottle{k}", "revolve", [bd, bd, bh], [x, 0, bh / 2], color=white, finish="plastic",
                       profile=prof),
                  _cyl(f"Bottle{k}Print", (0.0374, 0.0374, 0.010), (x, 0, 0.052), red, "plastic", collision=False),
                  _cyl(f"Bottle{k}Foil", (0.0275, 0.0275, 0.0016), (x, 0, 0.0902), foil, "metal", collision=False)]

    # 下の胴に巻いた印刷の帯（5 本を束ねる）
    BW, BD, BH = (L + 0.003) * 1000, (bd + 0.003) * 1000, 30.0
    s = 12

    def band(w: float, seed: int) -> Canvas:
        f = Canvas(w, BH, s, white, seed)
        f.gradient(0, 0, w, BH, "#FFFFFF", pink)
        f.rect(0, 0, w, 3, fill=red)
        f.rect(0, BH - 3, w, BH, fill=red)
        return f

    fr = band(BW, 2091)
    fr.text(BW * 0.30, 11, "乳酸菌飲料", 7.4, red, 900)
    fr.text(BW * 0.30, 21, "1本に乳酸菌 200億個", 3.4, INK, 800)
    fr.rect(BW * 0.58, 7, BW * 0.95, 23, fill=red, radius=3)
    fr.text(BW * 0.765, 12.5, "65ml × 5本", 4.6, white, 900)
    fr.text(BW * 0.765, 19, "要冷蔵（10℃以下）", 2.6, white, 700)
    bk = band(BW, 2092)
    back_info(bk, 4, 4, BW * 0.62, [("種類別名称", "乳酸菌飲料"), ("無脂乳固形分", "3.0%未満"),
                                     ("原材料名", "ぶどう糖果糖液糖、砂糖、脱脂粉乳／香料"), ("内容量", "65ml×5本"),
                                     ("賞味期限", "ふたに記載")], 1.5)
    bk.barcode(BW * 0.67, 6, 30, 15)
    bk.recycle(BW * 0.92, 11, 7, "プラ", red, sub="容器・帯")
    sides = []
    for k, seed in enumerate((2093, 2094)):
        sd = band(BD, seed)
        sd.text(BD / 2, 11, "乳酸菌", 5.4, red, 900)
        sd.text(BD / 2, 20, "65ml×5" if k == 0 else "要冷蔵", 3.6, INK, 800)
        sides.append(sd)
    imgs = [_face(a.array(), "film", 2095 + i, 0.6) for i, a in enumerate((fr, bk, *sides))]
    parts.append(_box("Band", (BW / 1000, BD / 1000, BH / 1000), (0, 0, 0.004 + BH / 2000), white, "plastic",
                      faces={"front": 0, "back": 1, "right": 2, "left": 3}, collision=False))
    # 全体を包む透明なフィルム（底はボトルの底と同じ面にならないよう 1 mm 下げる）
    fh = H + 0.003
    parts.append(_box("Film", (L + 0.006, bd + 0.006, fh), (0, 0, fh / 2 - 0.001), "#F2F6F8", "glass", thin_walled=True, collision=False))
    return Product(slug="lactic_drink_5pack", name="乳酸菌飲料 65ml×5本", shape_class="assembly", category="beverage",
                   dims=Dimensions(round(fh, 4), round(L + 0.006, 4), depth=round(bd + 0.006, 4)), mass_kg=0.36,
                   capacity_ml=325, material="plastic",
                   description="形はまっすぐな胴の 65ml の小びんの乳酸菌飲料（胴径 37 mm・高さ 92 mm、アルミのふた）を 5 本横に並べ、"
                               "印刷した帯と透明なフィルムで束ねたパックで、寸法・質量は代表値。",
                   tags=["乳酸菌飲料", "乳飲料", "要冷蔵", "5本パック", "lactic acid drink", "probiotic drink"], photos=[],
                   colors=Colors(label_base=white), images=imgs, parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    energy_drink_can_250ml, nutrition_drink_bottle_100ml, lactic_drink_5pack, milk_tea_pet_500ml,
    sports_drink_pet_500ml, vegetable_juice_pack_200ml, chilled_cup_coffee_200ml, beer_can_350ml,
    chuhai_can_500ml, bottle_can_coffee_400ml)}
