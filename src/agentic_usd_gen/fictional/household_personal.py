"""架空の商品のデザイン: 日用品（衛生・身だしなみ）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _cyl, _face, _pump_bottle, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _faces(canvases, kind: str, seed: int, strength: float = 0.8) -> list[np.ndarray]:
    """箱の 6 面（正面・裏・右・左・上・底の順）を仕上げる。"""
    return [_face(c.array(), kind, seed + i, strength) for i, c in enumerate(canvases)]


def _caution(c: Canvas, x0: float, y0: float, x1: float, text: str, size: float, bg: str = "#FFFFFF",
             color: str = INK) -> float:
    """注意書きを白地の枠に書く。下端 y を返す。"""
    n = sum(len(c.wrap(p, size, x0 + 1.5, x1 - 1.5)) for p in text.split("\n"))
    y1 = y0 + 3 + n * size * 1.45
    c.rect(x0, y0, x1, y1, fill=bg, radius=1)
    c.paragraph(x0 + 1.5, y0 + 1.5, x1 - 1.5, text, size, color, 400)
    return y1


# ---------------------------------------------------------------- シャンプー


def shampoo_pump() -> Product:
    cream, green, dark = "#F4F1E6", "#5E8C6A", "#2F4A37"
    form, pump = _pump_bottle(0.075, 0.170, (0.014, 0.138), green)
    c = label_canvas(form, cream, seed=1901)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FAF8F0", "#E6E9DA")
    c.photo("mint", fx - 30, 70, fx + 30, 112, shape="ellipse", feather=3, crop=(0.15, 0.1, 0.85, 0.9))
    c.rect(fx - 32, 8, fx + 32, 9, fill=green)
    c.text(fx, 15, "BOTANICAL", 3.4, green, 700, spacing=1.2)
    c.text(fx, 30, "シャンプー", 11, dark, 900, max_w=62)
    c.text(fx, 44, "ノンシリコン  アミノ酸系洗浄成分", 3.4, green, 700, max_w=62)
    c.text(fx, 52, "髪と頭皮をやさしく洗う", 3.4, INK, 600)
    c.rect(fx - 22, 58, fx + 22, 66, fill=green, radius=4)
    c.text(fx, 62, "ハーブミントの香り", 3.8, "#FFFFFF", 800)
    c.text(fx, H - 6, "480ml", 4.6, dark, 900)
    c.text(0.5 * W, 10, "SHAMPOO", 3.4, green, 800, spacing=0.8)
    c.vtext(0.5 * W, 22, "シャンプー", 5.0, dark, 900)
    caution = ("【使用方法】髪をぬらしてから適量を手にとり、よく泡立てて洗い、十分にすすいでください。\n"
               "【使用上の注意】頭皮に傷・はれもの・湿疹など異常のあるときは使わないでください。"
               "目に入ったときは、こすらずにすぐ洗い流してください。\n"
               "【成分】水、ココイルグルタミン酸TEA、コカミドプロピルベタイン、グリセリン、ハッカ油、香料\n" + NOTICE)
    _caution(c, 0.25 * W - 28, 8, 0.25 * W + 28, caution, 2.3, "#FFFFFF")
    c.barcode(0.5 * W - 12, 80, 24, 15)
    c.recycle(0.5 * W - 8, 106, 7, "プラ", dark, sub="容器")
    c.recycle(0.5 * W + 8, 106, 7, "プラ", dark, sub="ポンプ")
    label = finish(c.array(), "film", 1901, 0.6)
    return Product(slug="shampoo_pump", name="シャンプー ハーブミントの香り 480ml", category="household", mass_kg=0.55,
                   capacity_ml=480, material="plastic",
                   description="形は一般的なポンプ式のシャンプーボトル（ポンプ込みの高さ 226 mm・胴径 75 mm）で、寸法・質量は代表値。ポンプの軸・押し頭・ノズルは部品で表す。", parts=pump,
                   tags=["シャンプー", "ヘアケア", "ポンプ", "ミント", "shampoo", "hair care", "pump bottle"],
                   photos=["mint"], colors=Colors(cap=green, label_base=cream), **revolve(form, label=label))


# ---------------------------------------------------------------- ボディソープ 詰め替え


def body_soap_refill() -> Product:
    W, H = 150.0, 230.0
    lilac, purple, white = "#E6DDF2", "#5B3F8C", "#FFFFFF"
    c = Canvas(W, H, 8, white, seed=1911)
    c.gradient(0, 0, W, H, "#F6F1FB", "#D9CBEB")
    c.photo("lavender", 0, 120, W, H, crop=(0.0, 0.25, 1.0, 0.95))
    c.gradient(0, 112, W, 132, "#E9E0F3", mix("#E9E0F3", "#D9CBEB", 0.3))
    seal_crimp(c, 0, 0, W, 12, "#CDBCE3", 1.4)
    seal_crimp(c, 0, H - 12, W, H, "#7D61A8", 1.4)
    c.rect(0, 12, W, 22, fill=purple)
    c.text(W / 2, 17, "つめかえ用  REFILL", 5.0, white, 800, spacing=0.6)
    c.ellipse(W - 30, 26, W - 6, 50, fill="#F2C230")
    c.text(W - 18, 34, "約1.0回", 3.6, purple, 900)
    c.text(W - 18, 42, "分", 3.6, purple, 900)
    c.text(W / 2, 62, "ボディソープ", 17, purple, 900, max_w=W - 24)
    c.text(W / 2, 80, "うるおい保湿  弱酸性", 6.0, INK, 700)
    c.rect(W / 2 - 38, 88, W / 2 + 38, 100, fill=purple, radius=6)
    c.text(W / 2, 94, "ラベンダーの香り", 6.0, white, 800)
    c.rect(10, H - 40, 70, H - 18, fill=white, radius=3)
    c.text(40, H - 32, "400ml", 8.0, purple, 900)
    c.text(40, H - 23, "詰め替え用", 3.6, INK, 700)
    img = trim_safe(edge_shade(finish(c.array(), "film", 1911, 1.0), 25, 0.16))
    # 裏面: 使用方法・成分・注意・NOTICE・バーコード
    b = Canvas(W, H, 8, white, seed=1912)
    b.gradient(0, 0, W, H, "#F6F1FB", "#E3D8F0")
    seal_crimp(b, 0, 0, W, 12, "#CDBCE3", 1.4)
    seal_crimp(b, 0, H - 12, W, H, "#7D61A8", 1.4)
    b.rect(0, 12, W, 22, fill=purple)
    b.text(W / 2, 17, "ボディソープ  ラベンダーの香り  つめかえ用 400ml", 4.4, white, 800)
    b.rect(10, 28, W - 10, 52, fill=white, radius=3)
    b.text(W / 2, 34, "つめかえ方", 4.4, purple, 900)
    for i, t in enumerate(("① 容器を空にして洗い、よく乾かす", "② 上部をハサミで切る", "③ こぼさないようにゆっくり注ぐ")):
        b.text(W / 2, 40 + i * 4.6, t, 3.2, INK, 600)
    b.rect(10, 56, W - 10, 168, fill=white, radius=3)
    yb = b.paragraph(14, 60, W - 14,
                     "【使用方法】適量をタオルやスポンジにとり、よく泡立ててからだを洗い、十分に洗い流してください。\n"
                     "【使用上の注意】お肌に合わないとき、傷・はれもの・湿疹など異常のあるときは使わないでください。"
                     "目に入ったときは、こすらずにすぐ洗い流してください。乳幼児の手の届かない所に置いてください。"
                     "使用後は袋の口を閉じ、直射日光を避けて保管してください。\n"
                     "【成分】水、ラウレス硫酸Na、コカミドプロピルベタイン、グリセリン、ラウリン酸、"
                     "水酸化K、ラベンダー油、香料、EDTA-2Na、安息香酸Na", 3.9, INK, 400)
    b.table(14, yb + 4, W - 14, "", [("品名", "ボディソープ"), ("内容量", "400ml"), ("販売者", "架空の会社")], 3.6)
    b.rect(10, 172, W - 10, H - 16, fill=white, radius=3)
    b.barcode(16, 178, 46, 26)
    b.recycle(84, 190, 12, "プラ", purple, sub="袋")
    b.paragraph(98, 180, W - 14, NOTICE, 3.0, INK, 500)
    back = trim_safe(edge_shade(finish(b.array(), "film", 1912, 1.0), 25, 0.16))
    return Product(slug="body_soap_refill", name="ボディソープ ラベンダーの香り 詰め替え 400ml", shape_class="pouch",
                   category="household", dims=Dimensions(0.23, 0.15, depth=0.045), mass_kg=0.42, capacity_ml=400,
                   material="film",
                   description="形は一般的な詰め替え用のボディソープの袋（高さ 230 mm・幅 150 mm）をピロー包装で近似したもので、寸法・質量は代表値。注ぎ口は省略。",
                   tags=["ボディソープ", "詰め替え", "つめかえ用", "ラベンダー", "body soap", "refill pouch"],
                   photos=["lavender"], colors=Colors(label_base=lilac), images=[img, back],
                   faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- 歯みがき


def toothpaste_box() -> Product:
    W, D, H = 195.0, 42.0, 42.0  # 横長の箱を寝かせて置く
    white, blue, red = "#FFFFFF", "#1E5AA8", "#D93A3A"
    s = 9

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFFFFF", "#E3EEF8")
        f.rect(0, h - 4, w, h, fill=blue)
        f.rect(0, 0, w, 1.5, fill=red)
        return f

    fr = face(W, H, 1921)
    fr.pattern(120, 4, W, H - 4, "waves", mix("#E3EEF8", blue, 0.15), 6, 0.4)
    fr.text(12, 9, "医薬部外品", 3.0, INK, 700, anchor="lm")
    fr.text(12, 20, "薬用歯みがき", 11, blue, 900, anchor="lm")
    fr.text(12, 31, "むし歯予防・口臭予防  フッ素配合", 4.0, INK, 700, anchor="lm")
    fr.photo("mint", 128, 6, 158, 34, shape="ellipse", feather=1.0)
    fr.rect(162, 10, 188, 30, fill=red, radius=3)
    fr.text(175, 17, "120g", 6.0, white, 900)
    fr.text(175, 25, "クールミント", 3.0, white, 700)
    fr.text(W / 2, H - 2, "TOOTHPASTE", 2.4, white, 700, spacing=1.0)
    bk = face(W, H, 1922)
    bk.paragraph(8, 5, 140, "【効能】むし歯の発生及び進行の予防、口臭の防止、歯石の沈着を防ぐ。\n"
                 "【使用方法】適量を歯ブラシにとり、歯をみがきます。\n"
                 "【成分】湿潤剤：ソルビット液　清掃剤：無水ケイ酸　薬用成分：フッ化ナトリウム（フッ素 1450ppm）　"
                 "香味剤：香料（クールミントタイプ）\n6歳未満の子どもへの使用は控えてください。\n" + NOTICE, 2.4, INK, 400)
    bk.barcode(148, 6, 38, 22)
    bk.recycle(158, 33, 6, "紙", blue)
    bk.recycle(176, 33, 6, "プラ", blue, sub="チューブ")
    sides = []
    for k, seed in enumerate((1923, 1924)):
        sd = face(D, H, seed)
        sd.text(D / 2, 12, "薬用", 5.0, blue, 900)
        sd.text(D / 2, 21, "歯みがき", 5.0, blue, 900)
        sd.text(D / 2, 31, "120g" if k == 0 else "フッ素", 4.0, red, 900)
        sides.append(sd)
    tp = face(W, D, 1925)
    tp.text(W / 2, 14, "薬用歯みがき  クールミント  120g", 6.0, blue, 900)
    tp.text(W / 2, 26, "高濃度フッ素 1450ppm 配合", 4.0, INK, 700)
    bt = face(W, D, 1926)
    bt.text(W / 2, 14, "使用期限 2029.09", 4.0, INK, 600)
    bt.text(W / 2, 24, NOTICE, 3.0, INK, 400, max_w=W - 10)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 1930)
    return Product(slug="toothpaste_box", name="薬用歯みがき クールミント 120g", shape_class="box", category="household",
                   dims=Dimensions(0.042, 0.195, depth=0.042), mass_kg=0.145, material="paper",
                   description="形は一般的なチューブ入り歯みがきの外箱（長さ 195 mm・断面 42 × 42 mm、寝かせて置く）で、寸法・質量は代表値。",
                   tags=["歯みがき", "歯磨き粉", "オーラルケア", "医薬部外品", "toothpaste", "oral care"],
                   photos=["mint"], colors=Colors(label_base="#F1F6FB"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 歯ブラシ（台紙とブリスター）


def toothbrush_blister() -> Product:
    CW, CH = 70.0, 230.0
    sky, blue, white = "#D8ECF8", "#1E5AA8", "#FFFFFF"
    c = Canvas(CW, CH, 10, sky, seed=1941)
    c.gradient(0, 0, CW, CH, "#EAF5FC", "#B9DCF2")
    c.rect(0, 0, CW, 30, fill=blue)
    c.rect(CW / 2 - 9, 7, CW / 2 + 9, 13, fill="#0E3360", radius=3)  # 吊り下げ穴（印刷で表す）
    c.text(CW / 2, 22, "歯ブラシ", 8.0, white, 900)
    c.rect(0, 30, CW, 32, fill="#F2C230")
    c.pattern(0, 32, CW, CH, "dots", mix("#B9DCF2", white, 0.5), 5, 0.5)
    # 右側（ブリスターの外）に説明を書く
    x = 53.5
    c.rect(x - 7, 42, x + 7, 58, fill=blue, radius=3)
    c.text(x, 50, "ふつう", 4.4, white, 900)
    c.vtext(x, 66, "コンパクトヘッド", 4.2, blue, 900)
    c.vtext(x, 142, "奥歯まで届く", 3.4, INK, 700)
    c.rect(x - 7, 190, x + 7, 214, fill=white, radius=2)
    c.text(x, 196, "毛の", 3.0, INK, 700)
    c.text(x, 202, "かたさ", 3.0, INK, 700)
    c.text(x, 209, "ふつう", 3.4, blue, 900)
    c.rect(0, CH - 10, CW, CH, fill=blue)
    c.text(CW / 2, CH - 5, "TOOTHBRUSH", 3.0, white, 800, spacing=0.8)
    front = _face(c.array(), "paper", 1941)
    b = Canvas(CW, CH, 10, white, seed=1942)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EAF2F8")
    b.rect(0, 0, CW, 30, fill=blue)
    b.rect(CW / 2 - 9, 7, CW / 2 + 9, 13, fill="#0E3360", radius=3)
    b.text(CW / 2, 22, "TOOTHBRUSH", 5.0, white, 800, spacing=0.6)
    yb = b.table(6, 38, CW - 6, "", [("品名", "歯ブラシ"), ("毛のかたさ", "ふつう"), ("柄の材質", "ポリプロピレン"),
                                    ("毛の材質", "ナイロン"), ("耐熱温度", "80度")], 3.0)
    b.paragraph(6, yb + 5, CW - 6, "【使用上の注意】歯ぐきを傷つけないよう、強くこすらないでください。毛先が開いたら"
                "取り替えてください。使用後はよく洗い、乾燥させてください。\n" + NOTICE, 2.8, INK, 400)
    b.barcode(14, 168, 42, 22)
    b.recycle(22, 206, 8, "紙", blue, sub="台紙")
    b.recycle(48, 206, 8, "プラ", blue, sub="ケース")
    b.rect(0, CH - 3, CW, CH, fill=blue)
    back = _face(b.array(), "paper", 1942)

    bx = -0.012  # ブリスターと歯ブラシの中心 x（台紙の左寄り）
    navy, handle = "#0E3360", "#2F7FC8"
    parts = [_box("Card", (0.07, 0.001, 0.23), (0, 0, 0.115), white, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.030, 0.016, 0.188), (bx, -0.0092, 0.106), "#F2F6F8", "glass", thin_walled=True, collision=False),
             _box("Handle", (0.011, 0.006, 0.13), (bx, -0.0055, 0.08), handle, "glossy"),
             _box("Grip", (0.0115, 0.0065, 0.05), (bx, -0.0055, 0.05), navy, "matte"),
             _box("Neck", (0.006, 0.005, 0.031), (bx, -0.005, 0.1595), handle, "glossy"),
             _box("Head", (0.011, 0.005, 0.023), (bx, -0.005, 0.186), handle, "glossy"),
             _box("Bristles", (0.009, 0.008, 0.019), (bx, -0.0115, 0.186), "#F4F7FA", "matte")]
    return Product(slug="toothbrush_blister", name="歯ブラシ コンパクトヘッド ふつう", shape_class="assembly",
                   category="household", dims=Dimensions(0.23, 0.07, depth=0.017), mass_kg=0.025, material="plastic",
                   description="形は一般的な台紙とブリスターに入った歯ブラシ（台紙 70 × 230 mm）で、寸法・質量は代表値。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["歯ブラシ", "オーラルケア", "ブリスター", "toothbrush", "oral care", "blister pack"],
                   photos=[], colors=Colors(label_base=sky), images=[front, back], parts=parts)


# ---------------------------------------------------------------- 洗口液


def mouthwash_bottle() -> Product:
    form = forms.pet_bottle(0.205, 0.072, shoulder=0.13, neck_r=0.016, cap_h=0.030, cap_r=0.0195,
                            label=(0.030, 0.125), liquid_top=0.165)
    white, blue, aqua = "#FFFFFF", "#1554A0", "#4FB6E0"
    c = label_canvas(form, white, seed=1951)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#DDF0FA")
    c.rect(0, 0, W, 4, fill=blue)
    c.rect(0, H - 4, W, H, fill=blue)
    c.photo("mint", fx - 13, 60, fx + 13, 82, shape="ellipse", feather=1.0)
    c.text(fx, 10, "医薬部外品", 3.0, INK, 700)
    c.text(fx, 23, "洗口液", 12, blue, 900)
    c.text(fx, 35, "マウスウォッシュ", 4.6, aqua, 800)
    c.rect(fx - 26, 42, fx + 26, 52, fill=blue, radius=5)
    c.text(fx, 47, "ノンアルコール  低刺激", 4.0, white, 800, max_w=50)
    c.text(fx, H - 9, "口臭予防・歯肉炎予防  500ml", 3.4, blue, 900)
    c.text(0.5 * W, 12, "MOUTHWASH", 3.0, blue, 800, spacing=0.6)
    caution = ("【使用方法】適量（約20ml）を口に含み、20秒ほどすすいでから吐き出してください。\n"
               "【使用上の注意】口の中に異常があるときは使わないでください。飲み込まないこと。\n"
               "【成分】塩化セチルピリジニウム、グリセリン、ソルビット液、香料（ミント）、青色1号\n" + NOTICE)
    yb = _caution(c, 0.25 * W - 26, 7, 0.25 * W + 26, caution, 2.2, "#FFFFFF")
    c.rect(0.25 * W - 26, yb + 2, 0.25 * W + 26, yb + 20, fill="#FFFFFF", radius=1)
    c.barcode(0.25 * W - 24, yb + 3, 26, 16)
    c.recycle(0.25 * W + 10, yb + 11, 6, "PET", INK, kind="triangle")
    c.recycle(0.25 * W + 21, yb + 11, 6, "プラ", INK, sub="キャップ")
    label = finish(c.array(), "film", 1951, 0.6)
    return Product(slug="mouthwash_bottle", name="洗口液 ノンアルコール 500ml", category="household", mass_kg=0.56,
                   capacity_ml=500, material="PET",
                   description="形は一般的な洗口液の平たいボトル（高さ 205 mm・幅 72 mm・奥行き 48 mm、計量カップを兼ねた大きなキャップ）を楕円断面の回転体で近似したもので、寸法・質量は代表値。",
                   tags=["洗口液", "マウスウォッシュ", "オーラルケア", "医薬部外品", "mouthwash", "oral care"],
                   photos=["mint"], colors=Colors(cap="#F4F8FB", liquid="#3FA9E0", label_base="#EAF6FC"),
                   **revolve(form, label=label, body_fill=None, liquid="#3FA9E0", depth=0.048))


# ---------------------------------------------------------------- 綿棒


def cotton_swab_case() -> Product:
    form = forms.jar(0.082, 0.068, cap_h=0.020, cap_d=0.070, label=(0.005, 0.055))
    white, teal, pale = "#FFFFFF", "#138A86", "#E3F4F2"
    c = label_canvas(form, white, seed=1961)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", pale)
    for k in range(int(W / 4)):  # 中の綿棒の柄（縦の線）
        x = 2 + k * 4
        c.line([(x, 6), (x, H - 6)], mix(pale, teal, 0.12), 0.6)
    c.rect(0, 0, W, 2, fill=teal)
    c.rect(0, H - 2, W, H, fill=teal)
    c.rect(fx - 26, 4, fx + 26, 40, fill=white, radius=4)
    c.rect(fx - 26, 4, fx + 26, 10, fill=teal, radius=2)
    c.text(fx, 7, "抗菌加工", 3.2, white, 800)
    c.text(fx, 20, "綿棒", 10, teal, 900)
    c.text(fx, 31, "やわらか 純綿 100%", 3.6, INK, 700)
    c.text(fx, 37, "200本入", 3.6, teal, 900)
    c.text(fx, H - 5, "COTTON SWABS", 2.6, teal, 700, spacing=0.6)
    c.text(0.5 * W, 9, "200本", 4.0, teal, 900)
    c.rect(0.25 * W - 25, 3, 0.25 * W + 25, H - 3, fill=white, radius=2)
    c.paragraph(0.25 * W - 23, 5, 0.25 * W + 23,
                "品名：綿棒  綿の材質：綿 100%  軸の材質：紙  本数：200本\n【注意】耳や鼻の奥まで入れないでください。"
                "乳幼児の手の届かない所に保管してください。\n" + NOTICE, 2.0, INK, 400)
    c.barcode(0.5 * W - 11, 16, 22, 13)
    c.recycle(0.5 * W, 40, 6, "プラ", teal, sub="容器")
    label = finish(c.array(), "film", 1961, 0.5)
    t = top_canvas(form, teal, seed=1962)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#1BA39E", "#0E6E6B")
    t.ellipse(2, 2, d - 2, d - 2, outline=white, width=0.8)
    t.text(d / 2, d * 0.40, "綿棒", 10, white, 900)
    t.text(d / 2, d * 0.56, "200本入", 4.4, white, 800)
    t.text(d / 2, d * 0.70, "フタを回してあけてください", 2.6, white, 600)
    top = finish(t.array(), "film", 1962, 0.5)
    return Product(slug="cotton_swab_case", name="綿棒 200本入", category="household", mass_kg=0.07, material="plastic",
                   description="形は一般的な丸いケース入りの綿棒（高さ 82 mm・径 68 mm、ねじ蓋）で、寸法・質量は代表値。",
                   tags=["綿棒", "衛生用品", "コットン", "cotton swabs", "cotton buds"], photos=[],
                   colors=Colors(cap=teal, label_base=pale), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- マスク


def face_mask_box() -> Product:
    W, D, H = 195.0, 100.0, 80.0
    white, blue, navy = "#FFFFFF", "#3B8ED0", "#1B3E66"
    s = 7

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFFFFF", "#E5F0F9")
        f.rect(0, 0, w, 4, fill=blue)
        f.rect(0, h - 4, w, h, fill=navy)
        return f

    fr = face(W, H, 1971)
    fr.text(14, 18, "不織布マスク", 13, navy, 900, anchor="lm")
    fr.text(14, 32, "3層構造  ふつうサイズ", 5.4, blue, 800, anchor="lm")
    # マスクの絵（プリーツ）
    mx, my = 152.0, 26.0
    fr.rect(mx - 26, my - 13, mx + 26, my + 13, fill=white, outline=blue, width=0.7, radius=5)
    for k in range(3):
        y = my - 7 + k * 7
        fr.line([(mx - 25, y), (mx + 25, y)], mix(blue, white, 0.3), 0.6)
    fr.line([(mx - 26, my - 9), (mx - 34, my - 4), (mx - 34, my + 4), (mx - 26, my + 9)], blue, 0.7)
    fr.line([(mx + 26, my - 9), (mx + 34, my - 4), (mx + 34, my + 4), (mx + 26, my + 9)], blue, 0.7)
    for i, t in enumerate(("花粉", "ほこり", "飛沫")):
        cx = 26 + i * 30
        fr.ellipse(cx - 12, 44, cx + 12, 68, fill=blue)
        fr.text(cx, 52, t, 4.0, white, 900, max_w=20)
        fr.text(cx, 60, "対策", 3.4, white, 700)
    fr.rect(124, 48, 186, 70, fill=navy, radius=4)
    fr.text(155, 56, "30枚入", 7.0, white, 900)
    fr.text(155, 65, "ふつうサイズ", 3.4, white, 600)
    fr.text(W / 2, H - 2, "NON-WOVEN FACE MASK", 2.2, white, 700, spacing=1.0)
    bk = face(W, H, 1972)
    bk.table(8, 8, 110, "", [("品名", "不織布マスク"), ("サイズ", "ふつう（約 175 × 95 mm）"), ("入数", "30枚"),
                            ("材質", "本体・フィルター：ポリプロピレン　耳ひも：ポリウレタン、ナイロン")], 2.8)
    bk.paragraph(116, 8, 186, "【使用上の注意】このマスクはすべての感染を防ぐものではありません。肌に異常を感じたときは"
                 "使用を中止してください。1回使い切りです。\n" + NOTICE, 2.6, INK, 400)
    bk.barcode(132, 44, 36, 20)
    bk.recycle(122, 70, 6, "紙", navy)
    sides = []
    for k, seed in enumerate((1973, 1974)):
        sd = face(D, H, seed)
        sd.text(D / 2, 26, "不織布マスク", 9, navy, 900)
        sd.text(D / 2, 42, "ふつうサイズ" if k == 0 else "3層構造", 6, blue, 800)
        sd.text(D / 2, 58, "30枚入", 7, navy, 900)
        sides.append(sd)
    tp = face(W, D, 1975)
    # 取り出し口のミシン目
    x = 40.0
    while x < W - 40:
        tp.rect(x, D / 2 - 18, x + 2.4, D / 2 - 17.4, fill=navy)
        tp.rect(x, D / 2 + 17.4, x + 2.4, D / 2 + 18, fill=navy)
        x += 4
    tp.text(W / 2, D / 2 - 4, "ここを押してあけてください", 6.0, navy, 800)
    tp.text(W / 2, D / 2 + 7, "不織布マスク  ふつうサイズ  30枚入", 4.4, blue, 700)
    bt = face(W, D, 1976)
    bt.text(W / 2, D / 2 - 5, "不織布マスク  30枚入", 7, navy, 800)
    bt.text(W / 2, D / 2 + 8, NOTICE, 4.0, INK, 500)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 1980)
    return Product(slug="face_mask_box", name="不織布マスク ふつうサイズ 30枚入", shape_class="box", category="household",
                   dims=Dimensions(0.08, 0.195, depth=0.10), mass_kg=0.17, material="paper",
                   description="形は一般的な箱入りの不織布マスク 30 枚（幅 195 mm・奥行き 100 mm・高さ 80 mm）で、寸法・質量は代表値。",
                   tags=["マスク", "不織布マスク", "衛生用品", "face mask", "disposable mask"], photos=[],
                   colors=Colors(label_base="#EEF5FB"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 手指消毒ジェル


def hand_sanitizer_pump() -> Product:
    white, green, lime = "#FFFFFF", "#1F8A4C", "#9BD770"
    form, pump = _pump_bottle(0.065, 0.135, (0.012, 0.104), green)
    c = label_canvas(form, white, seed=1991)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#EAF7E2")
    c.rect(0, 0, W, 5, fill=green)
    c.rect(0, H - 5, W, H, fill=green)
    c.text(fx, 11, "指定医薬部外品", 3.0, INK, 700)
    c.text(fx, 24, "手指消毒", 9.0, green, 900)
    c.text(fx, 36, "ジェル", 9.0, green, 900)
    c.rect(fx - 24, 43, fx + 24, 51, fill=lime, radius=4)
    c.text(fx, 47, "エタノール 76.9vol%", 3.8, INK, 800)
    c.photo("lemon", fx - 12, 55, fx + 12, 79, shape="ellipse", feather=1)
    c.text(fx, 84, "すり込むだけ  水洗い不要", 3.2, INK, 700)
    c.text(fx, H - 2.5, "300ml", 3.4, white, 900)
    c.text(0.5 * W, 12, "HAND SANITIZER GEL", 2.6, green, 800, spacing=0.4)
    caution = ("【効能】手指・皮膚の洗浄・消毒\n【用法】適量を手に取り、乾くまで手指にすり込んでください。\n"
               "【注意】火気厳禁。目に入らないようにしてください。傷・湿疹などのある部位には使わないでください。\n"
               "【成分】エタノール、グリセリン、カルボマー、香料（レモン）\n" + NOTICE)
    _caution(c, 0.25 * W - 25, 7, 0.25 * W + 25, caution, 2.1, "#FFFFFF")
    c.barcode(0.5 * W - 11, 22, 22, 14)
    c.recycle(0.5 * W - 7, 52, 7, "プラ", INK, sub="容器")
    c.recycle(0.5 * W + 7, 52, 7, "プラ", INK, sub="ポンプ")
    c.text(0.5 * W, 66, "火気厳禁", 4.0, "#C0392B", 900)
    label = finish(c.array(), "film", 1991, 0.6)
    return Product(slug="hand_sanitizer_pump", name="手指消毒ジェル 300ml", category="household", mass_kg=0.33,
                   capacity_ml=300, material="plastic",
                   description="形は一般的なポンプ式の手指消毒ジェル（ポンプ込みの高さ 191 mm・胴径 65 mm）で、寸法・質量は代表値。ポンプの軸・押し頭・ノズルは部品で表す。", parts=pump,
                   tags=["手指消毒", "消毒ジェル", "アルコール", "指定医薬部外品", "hand sanitizer", "pump bottle"],
                   photos=["lemon"], colors=Colors(cap=green, label_base=white), **revolve(form, label=label))


# ---------------------------------------------------------------- 入浴剤


def bath_salts_box() -> Product:
    W, D, H = 150.0, 60.0, 105.0
    navy, white, gold = "#21305C", "#FFFFFF", "#E2B74A"
    s = 8
    scents = (("lemon", "レモン", "#E8B92C"), ("lavender", "ラベンダー", "#8E6BBF"), ("mint", "ミント", "#2E9E78"),
              ("berries", "ベリー", "#C0395B"))

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, navy, seed)
        f.gradient(0, 0, w, h, "#2C3F78", "#17213F")
        f.rect(0, h - 3, w, h, fill=gold)
        return f

    fr = face(W, H, 2001)
    for k in range(18):  # 炭酸の泡
        x, y, r = fr.rng.uniform(4, W - 4), fr.rng.uniform(4, 40), fr.rng.uniform(0.8, 2.6)
        fr.ellipse(x - r, y - r, x + r, y + r, outline=mix("#2C3F78", white, 0.45), width=0.3)
    fr.text(W / 2, 10, "医薬部外品", 3.4, white, 700)
    fr.text(W / 2, 22, "炭酸入浴剤", 13, white, 900)
    fr.text(W / 2, 34, "4つの香りのアソート  12錠入", 5.0, gold, 800)
    for i, (pid, name, col) in enumerate(scents):
        cx = 21 + i * 36
        fr.photo(pid, cx - 15, 42, cx + 15, 72, shape="ellipse", border=white, border_w=0.8)
        fr.rect(cx - 16, 75, cx + 16, 83, fill=col, radius=4)
        fr.text(cx, 79, name, 3.8, white, 800, max_w=30)
    fr.text(W / 2, 92, "疲労回復・肩こり・冷え性に", 4.4, white, 700)
    bk = face(W, H, 2002)
    bk.rect(5, 5, W - 5, H - 8, fill=white, radius=2)
    bk.paragraph(9, 8, 98, "【効能】疲労回復、肩のこり、冷え症、腰痛、神経痛、あせも、しっしん\n"
                 "【使用方法】浴槽のお湯（約150〜200L）に1錠を入れてください。\n"
                 "【使用上の注意】飲み物ではありません。肌に合わないときは使用を中止してください。浴槽や風呂釜を"
                 "傷めるおそれがあるため、残り湯は洗濯に使わないでください。\n"
                 "【成分】炭酸水素Na、炭酸Na、フマル酸、香料、色素\n" + NOTICE, 2.6, INK, 400)
    bk.barcode(104, 12, 36, 20)
    bk.recycle(112, 50, 8, "紙", navy, sub="箱")
    bk.recycle(132, 50, 8, "プラ", navy, sub="個包装")
    sides = []
    for k, seed in enumerate((2003, 2004)):
        sd = face(D, H, seed)
        sd.text(D / 2, 22, "炭酸", 9, white, 900)
        sd.text(D / 2, 36, "入浴剤", 9, white, 900)
        sd.rect(8, 50, D - 8, 64, fill=gold, radius=3)
        sd.text(D / 2, 57, "12錠入" if k == 0 else "4つの香り", 5.0, navy, 900, max_w=D - 18)
        sd.text(D / 2, 80, "BATH TABLETS", 3.4, gold, 700, spacing=0.4)
        sides.append(sd)
    tp = face(W, D, 2005)
    tp.text(W / 2, D / 2 - 6, "炭酸入浴剤  4つの香り", 8, white, 900)
    tp.text(W / 2, D / 2 + 8, "12錠入（4種 × 3錠）", 5, gold, 700)
    bt = face(W, D, 2006)
    bt.text(W / 2, D / 2 - 4, "使用期限 2029.06", 5.0, white, 600)
    bt.text(W / 2, D / 2 + 7, NOTICE, 3.4, white, 400, max_w=W - 10)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 2010)
    return Product(slug="bath_salts_box", name="炭酸入浴剤 4つの香り 12錠入", shape_class="box", category="household",
                   dims=Dimensions(0.105, 0.15, depth=0.06), mass_kg=0.55, material="paper",
                   description="形は一般的な錠剤タイプの炭酸入浴剤の箱（幅 150 mm・奥行き 60 mm・高さ 105 mm）で、寸法・質量は代表値。",
                   tags=["入浴剤", "炭酸", "バスグッズ", "医薬部外品", "bath tablets", "bath salts"],
                   photos=[p for p, _, _ in scents], colors=Colors(label_base=navy), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 絆創膏


def adhesive_bandage_box() -> Product:
    W, D, H = 98.0, 30.0, 68.0
    white, red, beige = "#FFFFFF", "#D2312E", "#E9C9A6"
    s = 14

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFFFFF", "#F3ECE4")
        f.rect(0, 0, w, 3, fill=red)
        f.rect(0, h - 3, w, h, fill=red)
        return f

    def bandage(f: Canvas, cx: float, cy: float, L: float, Wd: float):
        f.rect(cx - L / 2, cy - Wd / 2, cx + L / 2, cy + Wd / 2, fill=beige, radius=Wd / 2)
        f.rect(cx - L * 0.17, cy - Wd / 2 + 0.6, cx + L * 0.17, cy + Wd / 2 - 0.6, fill="#F7F1EA", radius=1)
        for k in range(10):
            x = cx - L / 2 + 3 + k * (L - 6) / 9
            if abs(x - cx) < L * 0.19:
                continue
            for y in (cy - Wd * 0.3, cy + Wd * 0.3):
                f.ellipse(x - 0.25, y - 0.25, x + 0.25, y + 0.25, fill=mix(beige, "#000000", 0.2))

    fr = face(W, H, 2021)
    fr.text(6, 8, "一般医療機器", 2.6, INK, 700, anchor="lm")
    fr.text(W / 2, 18, "救急絆創膏", 10, red, 900)
    fr.text(W / 2, 28, "水に強い  通気性", 4.0, INK, 700)
    bandage(fr, W / 2, 41, 64, 14)
    fr.rect(W / 2 - 22, 52, W / 2 + 22, 61, fill=red, radius=4.5)
    fr.text(W / 2, 56.5, "30枚  Mサイズ", 4.2, white, 800)
    bk = face(W, H, 2022)
    bk.paragraph(5, 6, 62, "【使用目的】小さな切り傷・すり傷・靴ずれなどの保護\n【使用方法】傷口を清潔にしてから、"
                 "パッド部が傷にあたるように貼ってください。\n【注意】かぶれたときは使用を中止してください。\n"
                 "サイズ：19 × 72 mm  30枚\n" + NOTICE, 2.2, INK, 400)
    bk.barcode(65, 8, 28, 17)
    bk.recycle(72, 40, 7, "紙", red)
    bk.recycle(86, 40, 7, "プラ", red, sub="包装")
    sides = []
    for k, seed in enumerate((2023, 2024)):
        sd = face(D, H, seed)
        sd.text(D / 2, 20, "救急", 6, red, 900)
        sd.text(D / 2, 29, "絆創膏", 6, red, 900)
        sd.text(D / 2, 46, "30枚" if k == 0 else "Mサイズ", 4.4, INK, 800)
        sides.append(sd)
    tp = face(W, D, 2025)
    tp.text(W / 2, D / 2 - 3, "救急絆創膏  30枚", 5.0, red, 900)
    tp.text(W / 2, D / 2 + 5, "← ここからあける", 3.0, INK, 700)
    bt = face(W, D, 2026)
    bt.text(W / 2, D / 2 - 3, "使用期限 2030.03", 3.4, INK, 600)
    bt.text(W / 2, D / 2 + 5, NOTICE, 2.6, INK, 400, max_w=W - 8)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 2030)
    return Product(slug="adhesive_bandage_box", name="救急絆創膏 Mサイズ 30枚", shape_class="box", category="household",
                   dims=Dimensions(0.068, 0.098, depth=0.03), mass_kg=0.04, material="paper",
                   description="形は一般的な箱入りの救急絆創膏 30 枚（幅 98 mm・奥行き 30 mm・高さ 68 mm）で、寸法・質量は代表値。",
                   tags=["絆創膏", "ばんそうこう", "救急用品", "adhesive bandage", "first aid"], photos=[],
                   colors=Colors(label_base="#F8F4EF"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 虫よけスプレー


def insect_repellent_spray() -> Product:
    form = forms.aerosol(0.190, 0.052, cap_h=0.042, label=(0.006, 0.137))
    white, green, orange = "#FFFFFF", "#1E7A45", "#F08A24"
    c = label_canvas(form, white, seed=2041)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.photo("lake", 0, H * 0.55, W, H, crop=(0, 0.45, 1, 0.95))
    c.gradient(0, 0, W, H * 0.58, "#FFFFFF", "#E6F3EA")
    c.rect(0, 0, W, 5, fill=green)
    c.text(fx, 11, "防除用医薬部外品", 2.8, INK, 700)
    c.text(fx, 23, "虫よけ", 10, green, 900)
    c.text(fx, 35, "スプレー", 10, green, 900)
    c.rect(fx - 22, 42, fx + 22, 50, fill=orange, radius=4)
    c.text(fx, 46, "蚊・ブヨ・マダニに", 3.8, white, 800, max_w=42)
    c.text(fx, 56, "ディート 10%  約6時間", 3.4, INK, 800)
    c.text(fx, H - 6, "200ml", 4.4, white, 900, stroke=0.3, stroke_fill=green)
    caution = ("【用法】肌から 10〜15cm 離して、まんべんなくスプレーしてください。\n"
               "【使用上の注意】顔には直接スプレーせず、手に取ってから塗ってください。6か月未満の乳児には使わないこと。\n"
               "高圧ガスを使用した可燃性の製品です。火気と高温に注意。\n【成分】ディート、エタノール、LPG\n" + NOTICE)
    _caution(c, 0.25 * W - 21, 7, 0.25 * W + 21, caution, 2.1, "#FFFFFF")
    c.rect(0.5 * W - 14, 8, 0.5 * W + 14, 28, fill=white)
    c.barcode(0.5 * W - 12, 10, 24, 15)
    c.recycle(0.5 * W, 36, 7, "スチール", green, kind="can")
    c.text(0.5 * W, 48, "火気と高温に注意", 2.4, "#C0392B", 900)
    label = finish(c.array(), "metal", 2041, 0.4)
    return Product(slug="insect_repellent_spray", name="虫よけスプレー 200ml", category="household", mass_kg=0.22,
                   capacity_ml=200, material="steel",
                   description="形は一般的なエアゾール缶の虫よけスプレー（高さ 190 mm・胴径 52 mm、胴と同じ太さのキャップ）で、寸法・質量は代表値。",
                   tags=["虫よけ", "虫除けスプレー", "スプレー", "防除用医薬部外品", "insect repellent", "spray"],
                   photos=["lake"], colors=Colors(cap=green, label_base="#E6F3EA"), **revolve(form, label=label))


# ---------------------------------------------------------------- 日焼け止め（キャップを下にして立てるチューブ）


def sunscreen_tube() -> Product:
    TW, TH = 48.0, 105.0  # 胴の正面（下がキャップ側）
    blue, yellow, white = "#1677C8", "#F6C343", "#FFFFFF"
    c = Canvas(TW, TH, 16, white, seed=2051)
    c.gradient(0, 0, TW, TH, "#FFFFFF", "#BFE4F7")
    c.rect(0, 0, TW, 4, fill=blue)  # 上端（シール側）
    c.ellipse(TW - 22, 8, TW + 6, 36, fill=yellow)
    c.text(TW - 9, 18, "SPF50+", 3.4, blue, 900)
    c.text(TW - 9, 25, "PA++++", 3.4, blue, 900)
    c.text(TW / 2 - 4, 46, "日焼け止め", 6.4, blue, 900, max_w=TW - 10)
    c.text(TW / 2, 56, "ウォータープルーフ", 3.6, INK, 700)
    c.text(TW / 2, 63, "顔・からだ用  せっけんで落とせる", 2.4, INK, 600, max_w=TW - 6)
    c.photo("lake", 4, 68, TW - 4, 88, shape="round", radius=2, crop=(0, 0.1, 1, 0.6))
    c.text(TW / 2, 95, "UV MILK  40g", 3.4, blue, 800, spacing=0.3)
    c.rect(0, TH - 4, TW, TH, fill=blue)
    front = _face(c.array(), "film", 2051, 0.6)
    b = Canvas(TW, TH, 16, white, seed=2052)
    b.gradient(0, 0, TW, TH, "#FFFFFF", "#E2F2FB")
    b.rect(0, 0, TW, 4, fill=blue)
    b.paragraph(4, 7, TW - 4, "【使用方法】よく振ってから適量を手に取り、肌にムラなくのばしてください。こまめに塗り直してください。\n"
                "【使用上の注意】傷・はれもの・湿疹などのある部位には使わないでください。\n"
                "【成分】水、メトキシケイヒ酸エチルヘキシル、酸化亜鉛、エタノール、BG\n" + NOTICE, 2.1, INK, 400)
    b.barcode(8, 76, 32, 16)
    b.recycle(TW / 2, TH - 9, 5, "プラ", blue)
    b.rect(0, TH - 4, TW, TH, fill=blue)
    back = _face(b.array(), "film", 2052, 0.6)
    parts = [_cyl("Cap", (0.036, 0.026, 0.020), (0, 0, 0.010), blue, "plastic"),
             _box("Body", (0.048, 0.022, 0.105), (0, 0, 0.0725), "#DDF1FB", "glossy", {"front": 0, "back": 1}),
             _box("Crimp", (0.050, 0.004, 0.009), (0, 0, 0.1295), "#CDE9F7", "plastic")]
    return Product(slug="sunscreen_tube", name="日焼け止め ミルク SPF50+ 40g", shape_class="assembly",
                   category="household", dims=Dimensions(0.134, 0.05, depth=0.026), mass_kg=0.05, material="plastic",
                   description="形は一般的なキャップを下にして立てるチューブ入りの日焼け止め（高さ 134 mm・幅 50 mm）で、寸法・質量は代表値。"
                               "チューブのつぶれた形は直方体の胴・楕円柱のキャップ・薄いシール部で近似する。",
                   tags=["日焼け止め", "UVケア", "チューブ", "サンスクリーン", "sunscreen", "UV protection", "tube"],
                   photos=["lake"], colors=Colors(label_base="#DDF1FB"), images=[front, back], parts=parts)


PRODUCTS = {f.__name__: f for f in (
    shampoo_pump, body_soap_refill, toothpaste_box, toothbrush_blister, mouthwash_bottle, cotton_swab_case,
    face_mask_box, hand_sanitizer_pump, bath_salts_box, adhesive_bandage_box, insect_repellent_spray, sunscreen_tube)}
