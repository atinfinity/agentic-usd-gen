"""架空の商品 35 点のデザイン。

どれも実在の商品名・ブランド名・ロゴ・商品写真を使わず、一般的な名前（種類・味・容量）だけを書く。
形と寸法は同じ種類の商品の一般的な値。写真は data/photos のパブリックドメイン素材を合成する。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Light, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .paint import Canvas, edge_shade, finish, mix, trim_safe

INK = "#222222"


# ---------------------------------------------------------------- 共通の部品


def back_info(c: Canvas, x0: float, y0: float, x1: float, rows: list[tuple[str, str]], size: float,
              nutrition: list[tuple[str, str]] | None = None, color: str = INK, bg: str = "#FFFFFF",
              notice_color: str | None = None) -> float:
    """一括表示（と栄養成分表示）。下端 y [mm] を返す。notice_color は表の外に書く架空の表記の色（地が暗いとき）。"""
    y = c.table(x0, y0, x1, "", rows, size, color, bg)
    if nutrition:
        y = c.table(x0, y + size * 0.8, x1, nutrition[0][0], nutrition[1:], size, color, bg)
    y = c.paragraph(x0, y + size * 0.6, x1, NOTICE, size * 0.9, notice_color or color, 500)
    return y


def seal_crimp(c: Canvas, x0: float, y0: float, x1: float, y1: float, color: str, step: float, vertical: bool = False):
    """袋のシール部のギザギザ（細かい縞）。"""
    dark = mix(color, "#000000", 0.25)
    light = mix(color, "#FFFFFF", 0.35)
    if vertical:  # 縞が縦（左右のシール）
        x, k = x0, 0
        while x < x1:
            c.rect(x, y0, min(x1, x + step / 2), y1, fill=dark if k % 2 else light)
            x += step / 2
            k += 1
    else:
        y, k = y0, 0
        while y < y1:
            c.rect(x0, y, x1, min(y1, y + step / 2), fill=dark if k % 2 else light)
            y += step / 2
            k += 1


def steam(c: Canvas, cx: float, y: float, w: float, h: float, color: str, width: float):
    for k in (-1, 0, 1):
        x = cx + k * w / 3
        pts = [(x + w * 0.06 * math.sin(t / h * 2 * math.pi), y - t) for t in np.linspace(0, h, 24)]
        c.line(pts, color, width)


# ---------------------------------------------------------------- カップ麺（縦型）


def cup_noodle_tall() -> Product:
    form = forms.paper_cup(0.105, 0.093, 0.066, foot_h=0.006, label_margin=(0.002, 0.003))
    base, navy, orange, cream = "#F6F1E6", "#1F3557", "#E07A1F", "#FBF7EE"
    c = label_canvas(form, base, seed=11)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.pattern(0, 0, W, H, "dots", mix(base, orange, 0.18), 4.0, 0.35)
    c.rect(0, 0, W, 11, fill=navy)
    c.rect(0, 11, W, 12.2, fill=orange)
    c.rect(0, H - 9, W, H, fill=navy)
    c.text(fx, 5.6, "みそラーメン", 6.2, "#FFFFFF", 900)
    c.photo("ramen", fx - 30, 16, fx + 30, 58, shape="ellipse", feather=1.2, shadow=1.5, crop=(0.08, 0.15, 0.92, 0.9))
    c.rect(fx - 34, 59, fx + 34, 70, fill=orange, radius=2.5)
    c.text(fx, 64.5, "濃厚みそ味スープ", 6.5, "#FFFFFF", 900, max_w=64)
    c.text(fx, 74, "コク深い味噌と香ばしいごま", 3.0, navy, 600)
    c.text(fx, H - 4.5, "カップめん  内容量 80g（めん 65g）", 3.0, "#FFFFFF", 600)
    # 横・裏
    c.text(0.5 * W, 5.6, "MISO RAMEN", 4.6, "#FFFFFF", 800, spacing=0.8)
    c.rect(0.47 * W, 24, 0.53 * W + 2, 46, fill="#FFFFFF", radius=1)
    c.text(0.5 * W + 1, 28, "熱湯", 3.2, navy, 900)
    c.text(0.5 * W + 1, 35, "3分", 6.0, orange, 900)
    c.text(0.5 * W + 1, 42, "目安", 2.6, navy, 600)
    bx = 0.25 * W
    back_info(c, bx - 24, 15, bx + 34, [
        ("名称", "即席カップめん"), ("原材料名", "油揚げめん（小麦粉、植物油脂、食塩）、スープ（みそ、糖類、ごま、香辛料）、かやく（キャベツ、コーン、ねぎ）"),
        ("内容量", "80g（めん 65g）"), ("賞味期限", "フタに記載"), ("保存方法", "においが強いもののそばや直射日光を避け、常温で保存")],
        2.1, [("栄養成分表示 1食（80g）当たり", ""), ("エネルギー", "355kcal"), ("たんぱく質", "8.9g"), ("脂質", "14.6g"),
              ("炭水化物", "47.0g"), ("食塩相当量", "5.1g")])
    c.barcode(0.5 * W - 12, 52, 26, 16)
    c.recycle(0.12 * W, 22, 8, "紙", navy, sub="容器")
    c.recycle(0.12 * W, 38, 8, "プラ", navy, sub="フタ")
    label = edge_shade(finish(c.array(), "paper", 11), 6, 0.08)

    t = top_canvas(form, cream, seed=12)
    d = t.w_mm
    t.ellipse(1, 1, d - 1, d - 1, fill=cream, outline=mix(cream, "#000000", 0.15), width=0.4)
    t.ellipse(10, 10, d - 10, d - 10, outline=navy, width=0.8)
    t.text(d / 2, d * 0.30, "みそラーメン", 8.5, navy, 900)
    t.photo("ramen", d / 2 - 18, d * 0.40, d / 2 + 18, d * 0.40 + 22, shape="round", radius=3, crop=(0.15, 0.2, 0.85, 0.8))
    t.text(d / 2, d * 0.73, "熱湯を内側の線まで注いで3分", 3.2, INK, 700)
    t.polygon([(d / 2 - 6, d - 9), (d / 2 + 6, d - 9), (d / 2, d - 4)], fill=orange)
    t.text(d / 2, d - 15, "ここからあける", 2.6, orange, 800)
    steam(t, d / 2, d * 0.22, 14, 6, mix(navy, cream, 0.5), 0.5)
    top = finish(t.array(), "paper", 12, 0.8)

    return Product(
        slug="cup_noodle_tall", name="カップめん みそ味", category="food", mass_kg=0.095, material="paper",
        description="形は一般的な縦型カップめん（高さ約 105 mm・上端径約 95 mm）の円錐台で、寸法・質量は代表値。",
        tags=["カップめん", "即席めん", "ラーメン", "みそ", "instant noodles", "cup noodle", "miso ramen"],
        photos=["ramen"], colors=Colors(cap=cream, label_base=base),
        **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- ポテトチップスの袋


def potato_chips_bag() -> Product:
    W, H = 180.0, 260.0
    blue, white, yellow = "#163E86", "#FFFFFF", "#F6C343"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, blue, seed=seed)
        c.gradient(0, 0, W, H, "#1E57B5", "#0E2A5E")
        c.pattern(0, 0, W, H, "waves", mix("#1E57B5", "#FFFFFF", 0.12), 9, 0.5)
        seal_crimp(c, 0, 0, W, 14, "#1E57B5", 1.6)
        seal_crimp(c, 0, H - 14, W, H, "#0E2A5E", 1.6)
        c.rect(0, 14, W, 15, fill=yellow)
        c.rect(0, H - 15, W, H - 14, fill=yellow)
        return c

    c = base(21)
    c.rect(18, 30, W - 18, 92, fill=white, radius=10)
    c.text(W / 2, 52, "ポテトチップス", 19, blue, 900, max_w=W - 46)
    c.text(W / 2, 77, "うすしお味", 15, "#D8462B", 900)
    c.text(W / 2, 102, "POTATO CHIPS", 7, white, 700, spacing=2.0)
    c.photo("potato_chips", 22, 112, W - 22, 220, shape="ellipse", feather=6, crop=(0.05, 0.1, 0.95, 0.9))
    c.ellipse(W - 62, 196, W - 16, 238, fill=yellow)
    c.text(W - 39, 210, "じゃがいも", 4.6, blue, 800)
    c.text(W - 39, 220, "の味わい", 4.6, blue, 800)
    c.text(W - 39, 230, "60g", 6.0, "#D8462B", 900)
    c.text(26, 236, "※写真はイメージです", 3.4, white, 500, anchor="lm")
    img = trim_safe(edge_shade(finish(c.array(), "film", 21, 1.2), 30, 0.18))

    # 裏面（後ろから見た向き）: 一括表示・栄養成分表示・注意・バーコード
    b = base(22)
    b.text(W / 2, 28, "ポテトチップス うすしお味", 9, white, 900, max_w=W - 30)
    b.rect(16, 38, W - 16, 238, fill=white, radius=6)
    rows = [("名称", "ポテトチップス"), ("原材料名", "じゃがいも（国産）、植物油、食塩、デキストリン／調味料（アミノ酸）"),
            ("内容量", "60g"), ("賞味期限", "表面上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存してください。")]
    nutrition = [("栄養成分表示 1袋（60g）当たり", ""), ("エネルギー", "336kcal"), ("たんぱく質", "3.0g"),
                 ("脂質", "21.6g"), ("炭水化物", "32.4g"), ("食塩相当量", "0.5g")]
    y = back_info(b, 24, 46, W - 24, rows, 4.2, nutrition)
    y += 4
    b.rect(24, y, W - 24, y + 7, fill=blue, radius=1.5)
    b.text(28, y + 3.5, "ご注意", 4.4, white, 800, anchor="lm")
    y = b.paragraph(25, y + 9.5, W - 25, "開封後はお早めにお召し上がりください。袋の中の空気は品質を保つための窒素ガスです。", 4.0, INK, 500)
    assert y < 196, y
    b.barcode(24, 202, 46, 28)
    b.recycle(W - 40, 216, 12, "プラ", blue, sub="袋")
    back = trim_safe(edge_shade(finish(b.array(), "film", 22, 1.2), 30, 0.18))
    return Product(
        slug="potato_chips_bag", name="ポテトチップス うすしお味 60g", shape_class="pouch", category="food",
        dims=Dimensions(0.26, 0.18, depth=0.055), mass_kg=0.062, material="film",
        description="形は一般的なピロー包装のスナック袋（高さ 260 mm・幅 180 mm）で、寸法・質量は代表値。表に商品名と写真、裏に一括表示と栄養成分表示。",
        tags=["ポテトチップス", "うすしお", "スナック菓子", "袋", "potato chips", "snack"], photos=["potato_chips"],
        colors=Colors(label_base="#163E86"), images=[img, back], faces={"front": 0, "back": 1})




# ---------------------------------------------------------------- 飲料


def _bottle_back(c: Canvas, bx: float, y0: float, width: float, name: str, materials: str, size: float, color=INK,
                 bg="#FFFFFF", extra: list[tuple[str, str]] | None = None, nutrition=None, notice_color=None):
    rows = [("名称", name), ("原材料名", materials), ("内容量", extra[0][1] if extra else "")] + (extra[1:] if extra else [])
    rows = [r for r in rows if r[1]]
    return back_info(c, bx - width / 2, y0, bx + width / 2, rows, size, nutrition, color, bg, notice_color)


def soda_pet_500ml() -> Product:
    form = forms.pet_bottle(0.215, 0.066, shoulder=0.24, cap_h=0.019, cap_r=0.0148, label=(0.082, 0.140),
                            liquid_top=0.172, waist=(0.03, 0.075))
    white, yellow, teal = "#FFFFFF", "#F4C531", "#1A8C8A"
    c = label_canvas(form, white, seed=31)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFBEA", "#FFF2B8")
    c.pattern(0, 0, W, H, "dots", mix("#FFF2B8", teal, 0.15), 5, 0.5)
    c.rect(0, 0, W, 6, fill=teal)
    c.rect(0, H - 6, W, H, fill=teal)
    c.photo("lemon", fx - 34, 7, fx - 4, 37, shape="ellipse", shadow=1.0, crop=(0.1, 0.05, 0.9, 0.95))
    c.text(fx + 14, 17, "レモン", 9.5, teal, 900)
    c.text(fx + 14, 30, "ソーダ", 9.5, teal, 900)
    c.rect(fx - 34, 40, fx + 34, 48, fill=yellow, radius=4)
    c.text(fx, 44, "炭酸飲料  すっきり微糖", 4.2, INK, 800)
    c.text(fx, 3, "LEMON SODA", 3.2, white, 700, spacing=1.0)
    c.text(fx, H - 3, "500ml", 3.4, white, 800)
    _bottle_back(c, 0.25 * W, 9, 46, "炭酸飲料", "果糖ぶどう糖液糖、レモン果汁、食塩／炭酸、酸味料、香料、ビタミンC", 1.9,
                 extra=[("内容量", "500ml"), ("賞味期限", "キャップに記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "22kcal"), ("炭水化物", "5.5g"), ("食塩相当量", "0.04g")])
    c.barcode(0.5 * W - 13, 14, 26, 16)
    c.recycle(0.5 * W - 6, 41, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 41, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 31, 0.8)
    return Product(slug="soda_pet_500ml", name="レモンソーダ 500ml", category="beverage", mass_kg=0.53,
                   capacity_ml=500, material="PET",
                   description="形は一般的な 500ml の炭酸飲料用 PET ボトル（高さ 215 mm・胴径 66 mm）で、寸法・質量は代表値。",
                   tags=["炭酸飲料", "レモン", "ソーダ", "ペットボトル", "soda", "lemon", "PET bottle"], photos=["lemon"],
                   colors=Colors(cap=yellow, label_base="#FFF7D6"), **revolve(form, label=label, body_fill=None))


def green_tea_pet_600ml() -> Product:
    form = forms.pet_bottle(0.225, 0.070, shoulder=0.22, cap_h=0.020, cap_r=0.0150, label=(0.060, 0.158),
                            liquid_top=0.186, ribs=(0.012, 0.050))
    cream, green, dark = "#F5F1E2", "#3E8E41", "#1F4D22"
    c = label_canvas(form, cream, seed=41)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.photo("tea_field", 0, H * 0.62, W, H, crop=(0, 0.35, 1, 0.95))
    c.gradient(0, H * 0.58, W, H * 0.68, cream, mix(cream, green, 0.25))
    c.rect(0, 0, W, 5, fill=green)
    c.rect(fx - 20, 9, fx + 20, 62, fill="#FFFFFF", radius=3)
    c.vtext(fx + 5, 18, "緑茶", 15, dark, 900, gap=0.1)
    c.vtext(fx - 12, 16, "国産茶葉", 4.6, green, 700)
    c.photo("tea_leaves", fx - 17, 46, fx - 4, 59, shape="ellipse", crop=(0.2, 0.2, 0.8, 0.8))
    c.text(fx + 9, 54, "無香料", 3.4, green, 800)
    c.text(fx + 9, 59, "無調味", 3.4, green, 800)
    c.rect(fx - 26, H - 16, fx + 26, H - 8, fill=dark, radius=4)
    c.text(fx, H - 12, "緑茶飲料  600ml", 4.2, "#FFFFFF", 800)
    c.text(0.5 * W, 20, "GREEN TEA", 3.2, dark, 700, spacing=0.8)
    _bottle_back(c, 0.25 * W, 8, 48, "緑茶（清涼飲料水）", "緑茶（国産）／ビタミンC", 2.0,
                 extra=[("内容量", "600ml"), ("賞味期限", "キャップに記載"), ("保存方法", "直射日光を避けて保存")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
                            ("炭水化物", "0g"), ("食塩相当量", "0.02g")])
    c.barcode(0.5 * W - 13, 30, 26, 16)
    c.recycle(0.5 * W - 6, 58, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 58, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 41, 0.8)
    return Product(slug="green_tea_pet_600ml", name="緑茶 600ml", category="beverage", mass_kg=0.625,
                   capacity_ml=600, material="PET",
                   description="形は一般的な 600ml のお茶用 PET ボトル（高さ 225 mm・胴径 70 mm）で、寸法・質量は代表値。",
                   tags=["緑茶", "お茶", "茶飲料", "ペットボトル", "green tea", "PET bottle"],
                   photos=["tea_field", "tea_leaves"], colors=Colors(cap="#2E7D32", liquid="#C9B848", label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid="#C9B848"))


def mineral_water_pet_550ml() -> Product:
    form = forms.pet_bottle(0.210, 0.068, shoulder=0.26, cap_h=0.019, cap_r=0.0148, label=(0.090, 0.135),
                            liquid_top=0.178, ribs=(0.010, 0.085))
    sky, blue = "#DDEFF8", "#1F6FA8"
    c = label_canvas(form, sky, seed=51)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.photo("lake", 0, 0, W, H, crop=(0, 0.15, 1, 0.75))
    c.gradient(0, 0, W, 8, "#FFFFFF", mix("#FFFFFF", sky, 0.6))
    c.rect(fx - 30, 9, fx + 30, 30, fill=(255, 255, 255), radius=3)
    c.text(fx, 16, "天然水", 8.5, blue, 900)
    c.text(fx, 25, "ナチュラルミネラルウォーター", 3.0, blue, 700)
    c.text(fx, 4, "MINERAL WATER  550ml", 2.8, blue, 700, spacing=0.4)
    c.rect(fx - 22, H - 9, fx + 22, H - 3, fill=blue, radius=3)
    c.text(fx, H - 6, "軟水  硬度 約30mg/L", 3.0, "#FFFFFF", 700)
    c.rect(0.25 * W - 26, 2, 0.25 * W + 26, H - 2, fill="#FFFFFF")
    _bottle_back(c, 0.25 * W, 4, 48, "ナチュラルミネラルウォーター", "水（鉱水）", 1.8,
                 extra=[("内容量", "550ml"), ("採水地", "架空の山の湧水"), ("賞味期限", "キャップに記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("ナトリウム", "0.6mg"),
                            ("カルシウム", "0.9mg")])
    c.rect(0.5 * W - 15, 3, 0.5 * W + 15, H - 3, fill="#FFFFFF")
    c.barcode(0.5 * W - 13, 5, 26, 16)
    c.recycle(0.5 * W - 6, 33, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 33, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 51, 0.8)
    return Product(slug="mineral_water_pet_550ml", name="天然水 550ml", category="beverage", mass_kg=0.572,
                   capacity_ml=550, material="PET",
                   description="形は一般的な 550ml の水用 PET ボトル（高さ 210 mm・胴径 68 mm、胴に横リブ）で、寸法・質量は代表値。",
                   tags=["水", "ミネラルウォーター", "天然水", "ペットボトル", "mineral water", "PET bottle"],
                   photos=["lake"], colors=Colors(cap="#F4F6F8", label_base=sky),
                   **revolve(form, label=label, body_fill=None))


def canned_coffee_185g() -> Product:
    form = forms.beverage_can(0.105, 0.053, label_margin=0.005)
    brown, cream, gold = "#3B2416", "#F1E6D2", "#C79A4A"
    c = label_canvas(form, brown, seed=61)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#4A2E1C", "#24150C")
    c.photo("coffee_beans", 0, H * 0.58, W, H, crop=(0, 0.2, 1, 0.8))
    c.gradient(0, H * 0.52, W, H * 0.62, "#3F2718", "#3F2718")
    c.rect(0, 4, W, 5, fill=gold)
    c.rect(fx - 22, 10, fx + 22, 46, fill=cream, radius=2)
    c.text(fx, 18, "COFFEE", 6.0, brown, 900, spacing=0.6)
    c.text(fx, 29, "微糖", 9.0, brown, 900)
    c.text(fx, 40, "深煎り豆使用", 3.6, gold, 800)
    c.text(fx, 51, "コーヒー  185g", 3.6, cream, 700)
    c.text(0.5 * W, 20, "BLACK & MILK", 2.6, gold, 700, spacing=0.4)
    _bottle_back(c, 0.25 * W, 7, 40, "コーヒー", "牛乳、砂糖、コーヒー、全粉乳／乳化剤、香料、甘味料", 1.6,
                 extra=[("内容量", "185g"), ("賞味期限", "缶底に記載")],
                 nutrition=[("栄養成分表示 100g当たり", ""), ("エネルギー", "18kcal"), ("脂質", "0.5g"), ("炭水化物", "2.9g"),
                            ("食塩相当量", "0.1g")], bg=cream, notice_color=cream)
    c.rect(0.5 * W - 14, 28, 0.5 * W + 14, 47, fill="#FFFFFF")
    c.barcode(0.5 * W - 12, 29, 24, 15)
    c.recycle(0.04 * W, 50, 7, "スチール", cream, kind="can")
    label = finish(c.array(), "metal", 61, 0.7)

    t = top_canvas(form, "#B9BDC1", seed=62)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D5D8DB", "#9DA2A7")
    t.ellipse(2, 2, d - 2, d - 2, outline="#8D9196", width=0.8)
    t.ellipse(5, 5, d - 5, d - 5, outline="#C7CACD", width=0.5)
    t.rect(d / 2 - 6, d * 0.58, d / 2 + 6, d * 0.84, fill="#C4C7CA", outline="#8A8E92", width=0.4, radius=5)
    t.ellipse(d / 2 - 3, d * 0.7, d / 2 + 3, d * 0.8, fill="#9DA2A7")
    t.ellipse(d / 2 - 1.2, d * 0.5, d / 2 + 1.2, d * 0.55, fill="#8A8E92")
    t.rect(d / 2 - 7, d * 0.2, d / 2 + 7, d * 0.42, outline="#A4A8AC", width=0.4, radius=6)
    top = finish(t.array(), "metal", 62, 0.6)
    return Product(slug="canned_coffee_185g", name="缶コーヒー 微糖 185g", category="beverage", mass_kg=0.215,
                   capacity_ml=185, material="steel",
                   description="形は一般的な 185g のショート缶（高さ 105 mm・胴径 53 mm）で、寸法・質量は代表値。",
                   tags=["コーヒー", "缶コーヒー", "微糖", "スチール缶", "coffee", "canned coffee"], photos=["coffee_beans"],
                   colors=Colors(cap="#BFC2C5", label_base=brown), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 食品（カップ）


def cup_noodle_bowl() -> Product:
    form = forms.paper_cup(0.075, 0.141, 0.098, foot_h=0.005, lid_overhang=0.0015, label_margin=(0.002, 0.003))
    white, indigo, red = "#FAFAF7", "#24305E", "#C8392B"
    c = label_canvas(form, white, seed=71)
    W, H = c.w_mm, c.h_mm
    c.pattern(0, 0, W, H, "waves", mix(white, indigo, 0.12), 6, 0.35)
    c.rect(0, H - 8, W, H, fill=indigo)
    for fx in (0.75 * W, 0.25 * W):
        c.photo("udon", fx - 36, 4, fx + 6, 46, shape="ellipse", feather=1.0, shadow=1.2, crop=(0.1, 0.1, 0.9, 0.9))
        c.vtext(fx + 18, 9, "うどん", 9.5, indigo, 900, gap=0.08)
        c.rect(fx + 8, 6, fx + 9, 44, fill=red)
        c.text(fx + 36, 14, "かつお", 3.6, red, 800)
        c.text(fx + 36, 20, "だし", 3.6, red, 800)
        c.text(fx - 15, H - 4, "即席カップうどん  内容量 95g（めん 74g）", 3.0, "#FFFFFF", 600)
    c.rect(0.5 * W - 26, 4, 0.5 * W + 26, H - 10, fill="#FFFFFF", outline=indigo, width=0.3)
    back_info(c, 0.5 * W - 25, 5, 0.5 * W + 9, [("名称", "即席カップめん"), ("原材料名", "油揚げめん（小麦粉、植物油脂、食塩）、スープ（食塩、しょうゆ、かつおぶし粉末、昆布エキス）、かやく（味付豚肉、ねぎ）"),
                                                ("内容量", "95g"), ("賞味期限", "フタに記載")], 1.6)
    c.barcode(0.5 * W + 11, 6, 14, 9)
    c.recycle(0.5 * W + 15, 25, 6, "紙", indigo, sub="容器")
    c.recycle(0.5 * W + 15, 38, 6, "プラ", indigo, sub="フタ")
    c.recycle(0.0 * W + 9, 20, 6, "プラ", indigo, sub="小袋")
    label = finish(c.array(), "paper", 71)

    t = top_canvas(form, white, seed=72)
    d = t.w_mm
    t.ellipse(1, 1, d - 1, d - 1, fill=white, outline=mix(white, "#000000", 0.2), width=0.4)
    t.photo("udon", d * 0.18, d * 0.18, d * 0.82, d * 0.70, shape="ellipse", feather=2, crop=(0.05, 0.0, 0.95, 0.9))
    t.rect(d * 0.2, d * 0.72, d * 0.8, d * 0.84, fill=indigo, radius=3)
    t.text(d / 2, d * 0.78, "豚しゃぶうどん", 8, "#FFFFFF", 900)
    t.text(d / 2, d * 0.12, "熱湯5分  フタの上で温めないでください", 3, indigo, 700)
    t.polygon([(d / 2 - 7, d - 6), (d / 2 + 7, d - 6), (d / 2, d - 1.5)], fill=red)
    top = finish(t.array(), "paper", 72, 0.8)
    return Product(slug="cup_noodle_bowl", name="カップうどん 豚しゃぶ", category="food", mass_kg=0.107, material="paper",
                   description="形は一般的などんぶり型カップめん（高さ 75 mm・上端径約 144 mm）で、寸法・質量は代表値。",
                   tags=["カップめん", "カップうどん", "豚しゃぶうどん", "即席めん", "instant noodles", "udon"], photos=["udon"],
                   colors=Colors(cap=white, label_base=white), **revolve(form, label=label, top=top))


def snack_cup() -> Product:
    form = forms.paper_cup(0.088, 0.083, 0.064, lid_h=0.0015, lid_overhang=0.0012, rim_h=0.003,
                           label_margin=(0.002, 0.002))
    orange, white, green = "#EE7A1E", "#FFFFFF", "#2E8B57"
    c = label_canvas(form, orange, seed=81)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F59A3B", "#E5661A")
    c.pattern(0, 0, W, H, "stripes", mix("#F08A2E", "#FFFFFF", 0.15), 6, 1.2)
    c.photo("potato_sticks", fx - 30, 30, fx + 30, 72, shape="ellipse", feather=2, shadow=1.0)
    c.rect(fx - 30, 6, fx + 30, 26, fill=white, radius=4)
    c.text(fx, 13, "じゃがいも", 5.6, orange, 900)
    c.text(fx, 21.5, "スティック", 6.4, orange, 900)
    c.ellipse(fx + 14, 52, fx + 32, 70, fill=green)
    c.text(fx + 23, 58.5, "サラダ", 3.6, white, 900)
    c.text(fx + 23, 64, "味", 3.6, white, 900)
    c.text(fx, H - 4, "スナック菓子  内容量 55g", 3.0, white, 700)
    c.rect(0.25 * W - 26, 6, 0.25 * W + 26, H - 6, fill=white, radius=2)
    back_info(c, 0.25 * W - 24, 8, 0.25 * W + 24, [("名称", "スナック菓子"), ("原材料名", "じゃがいも（国産）、植物油、脱脂粉乳、乾燥野菜（にんじん、パセリ）、食塩／調味料"),
                                                  ("内容量", "55g"), ("賞味期限", "フタに記載")], 1.8,
              [("栄養成分表示 1カップ当たり", ""), ("エネルギー", "290kcal"), ("脂質", "14.0g"), ("炭水化物", "37.0g"),
               ("食塩相当量", "0.6g")])
    c.rect(0.5 * W - 14, 30, 0.5 * W + 14, 50, fill=white)
    c.barcode(0.5 * W - 12, 32, 24, 15)
    c.recycle(0.5 * W - 6, 60, 7, "紙", white, sub="容器")
    c.recycle(0.5 * W + 8, 60, 7, "プラ", white, sub="フタ")
    label = finish(c.array(), "paper", 81)

    t = top_canvas(form, "#F2F2F0", seed=82)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#F7F7F5", "#DADAD6")
    t.ellipse(1.5, 1.5, d - 1.5, d - 1.5, outline=orange, width=1.2)
    t.text(d / 2, d * 0.32, "じゃがいも", 8, orange, 900)
    t.text(d / 2, d * 0.46, "スティック", 8, orange, 900)
    t.rect(d * 0.25, d * 0.56, d * 0.75, d * 0.68, fill=green, radius=3)
    t.text(d / 2, d * 0.62, "サラダ味", 5, white, 800)
    t.text(d / 2, d * 0.80, "ここからはがしてください", 3, INK, 700)
    t.polygon([(d / 2 - 5, d - 8), (d / 2 + 5, d - 8), (d / 2, d - 3)], fill=orange)
    top = finish(t.array(), "film", 82, 0.8)
    return Product(slug="snack_cup", name="じゃがいもスティック サラダ味", category="food", mass_kg=0.065, material="paper",
                   description="形は一般的なカップ入りスナック（高さ 88 mm・上端径約 86 mm）で、寸法・質量は代表値。",
                   tags=["スナック菓子", "ポテトスナック", "サラダ味", "カップ", "snack", "potato sticks"],
                   photos=["potato_sticks"], colors=Colors(cap="#EDEDEA", label_base=orange),
                   **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 日用品


def deodorant_spray_150g() -> Product:
    form = forms.aerosol(0.200, 0.053, cap_h=0.045, label=(0.006, 0.145))
    white, lilac, purple = "#FBFAFD", "#C9B6E4", "#5B3F8C"
    c = label_canvas(form, white, seed=91)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#ECE4F7")
    c.photo("lavender", 0, H * 0.55, W, H, crop=(0, 0.3, 1, 0.9))
    c.gradient(0, H * 0.50, W, H * 0.60, "#F1EBF8", "#F1EBF8")
    c.rect(fx - 24, 14, fx + 24, 15, fill=purple)
    c.text(fx, 26, "パウダー", 7.0, purple, 900)
    c.text(fx, 37, "スプレー", 7.0, purple, 900)
    c.text(fx, 47, "制汗・デオドラント", 3.6, INK, 700)
    c.rect(fx - 20, 54, fx + 20, 62, fill=lilac, radius=4)
    c.text(fx, 58, "ラベンダーの香り", 3.8, purple, 800)
    c.text(fx, 8, "DEODORANT POWDER SPRAY", 2.4, purple, 700, spacing=0.4)
    c.text(fx, H - 6, "150g", 4.0, "#FFFFFF", 900, stroke=0.25, stroke_fill=purple)
    caution = ("【使用方法】よく振ってから、肌から 15cm 以上離して使用してください。\n"
               "【使用上の注意】高圧ガスを使用した可燃性の製品です。火気と高温に注意。直射日光の当たる所や火気の近くなど、"
               "温度が 40℃以上となる所に置かないこと。使い切って捨てること。\n"
               "【成分】ラベンダー油、タルク、エタノール、LPG\n" + NOTICE)
    n = len(c.wrap(caution, 2.2, 0.25 * W - 21, 0.25 * W + 21))
    c.rect(0.25 * W - 23, 6, 0.25 * W + 23, 8 + n * 2.2 * 1.45 + 1.5, fill="#FFFFFF")
    c.paragraph(0.25 * W - 21, 8, 0.25 * W + 21, caution, 2.2, INK, 400)
    c.rect(0.5 * W - 14, 40, 0.5 * W + 14, 60, fill="#FFFFFF")
    c.barcode(0.5 * W - 12, 42, 24, 15)
    c.recycle(0.5 * W, 66, 7, "アルミ", purple, kind="can")
    c.text(0.5 * W, 76, "火気と高温に注意", 2.4, "#C0392B", 900)
    label = finish(c.array(), "metal", 91, 0.4)
    return Product(slug="deodorant_spray_150g", name="パウダースプレー ラベンダーの香り 150g", category="household",
                   mass_kg=0.19, material="aluminum",
                   description="形は一般的なエアゾール缶（高さ 200 mm・胴径 53 mm、胴と同じ太さのキャップ）で、寸法・質量は代表値。",
                   tags=["制汗剤", "デオドラント", "スプレー", "ラベンダー", "deodorant", "spray"], photos=["lavender"],
                   colors=Colors(cap="#F2EEF7", label_base="#F1EBF8"), **revolve(form, label=label))


def lip_balm_stick() -> Product:
    form = forms.stick(0.071, 0.0165, cap_h=0.025, label=(0.004, 0.044))
    white, navy, mint = "#F7F9F8", "#1E2E57", "#3BB59A"
    c = label_canvas(form, white, seed=101)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.rect(0, 0, W, 3, fill=navy)
    c.rect(0, H - 3, W, H, fill=navy)
    c.photo("mint", fx - 9, 4, fx + 9, 14, shape="ellipse")
    c.vtext(fx + 0.5, 17, "リップ", 3.8, navy, 900, gap=0.05)
    c.rect(fx - 5.5, 31, fx - 4.8, 35, fill=mint)
    c.vtext(fx - 2.6, 17, "薬用", 2.4, mint, 800)
    c.text(fx, H - 1.5, "MINT", 1.6, white, 800)
    c.barcode(0.25 * W - 6, 4.5, 12, 11)
    c.paragraph(0.25 * W - 11, 17, 0.25 * W + 11, "医薬部外品\nくちびるの荒れ・乾燥を防ぐ\n成分：l-メントール、ワセリン、"
                "ミツロウ\n" + NOTICE, 1.2, INK, 400)
    label = finish(c.array(), "film", 101, 0.5)
    return Product(slug="lip_balm_stick", name="薬用リップスティック ミント", category="household", mass_kg=0.009,
                   material="plastic",
                   description="形は一般的なスティック容器のリップクリーム（高さ 71 mm・径 16.5 mm）で、寸法・質量は代表値。",
                   tags=["リップクリーム", "リップスティック", "ミント", "lip balm"], photos=["mint"],
                   colors=Colors(cap=navy, label_base=white), **revolve(form, label=label))


def skin_cream_tin() -> Product:
    form = forms.tin(0.022, 0.075, lid_h=0.012)
    coral, cream = "#E57062", "#FFF6EC"
    c = label_canvas(form, coral, seed=111)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#EC8577", "#D85D50")
    for k in range(4):
        c.text((k + 0.5) * W / 4, H / 2, "SKIN CREAM", 3.0, cream, 700, spacing=0.6)
    label = finish(c.array(), "metal", 111, 0.5)
    t = top_canvas(form, coral, seed=112)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#EF8D80", "#D45A4D")
    t.ellipse(3, 3, d - 3, d - 3, outline=cream, width=0.6)
    t.text(d / 2, d * 0.38, "スキンクリーム", 7.0, cream, 900)
    t.text(d / 2, d * 0.50, "全身用保湿クリーム", 3.4, cream, 700)
    t.rect(d * 0.3, d * 0.58, d * 0.7, d * 0.66, fill=cream, radius=4)
    t.text(d / 2, d * 0.62, "無香料  60g", 3.4, coral, 800)
    t.text(d / 2, d * 0.78, NOTICE, 1.8, cream, 400, max_w=d * 0.6)
    top = finish(t.array(), "metal", 112, 0.4)
    return Product(slug="skin_cream_tin", name="スキンクリーム 缶 60g", category="household", mass_kg=0.07,
                   material="aluminum",
                   description="形は一般的な平たい缶入りクリーム（高さ 22 mm・径 75 mm）で、寸法・質量は代表値。",
                   tags=["保湿クリーム", "スキンクリーム", "缶", "skin cream", "tin"], photos=[],
                   colors=Colors(cap=coral, label_base=coral), **revolve(form, label=label, top=top))


def aa_battery() -> Product:
    form = forms.battery(0.0505, 0.0145)
    teal, white = "#0F7C7A", "#FFFFFF"
    c = label_canvas(form, teal, seed=121)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#16A3A0", "#0B5E5C")
    c.rect(0, 0, W, H * 0.16, fill=white)
    c.text(0.75 * W, H * 0.08, "+", 3.4, teal, 900)
    c.text(0.25 * W, H * 0.08, "+", 3.4, teal, 900)
    c.vtext(0.75 * W, H * 0.30, "単3形", 3.0, white, 900)
    c.text(0.75 * W, H * 0.68, "1.5V", 2.4, white, 800)
    c.vtext(0.25 * W, H * 0.24, "アルカリ乾電池", 2.6, white, 800, gap=0.02)
    y = c.paragraph(0.5 * W - 5.5, H * 0.2, 0.5 * W + 5.5, "LR6\n1.5V\n使用推奨期限 2031-10", 1.1, white, 600)
    c.paragraph(0.5 * W - 5.5, y + 1.0, 0.5 * W + 5.5, "ショート・充電・分解・火中投入しないこと", 1.0, white, 500)
    label = finish(c.array(), "film", 121, 0.4)
    return Product(slug="aa_battery", name="アルカリ乾電池 単3形", category="household", mass_kg=0.023, material="steel",
                   description="形は JIS（IEC LR6）の単3形の寸法（高さ 50.5 mm・径 14.5 mm）で、質量は代表値。",
                   tags=["乾電池", "単3", "アルカリ", "電池", "AA battery", "battery"], photos=[],
                   colors=Colors(cap="#B8B8B8", label_base=teal), **revolve(form, label=label))


# ---------------------------------------------------------------- 袋・箱


def chocolate_bar() -> Product:
    L, Wd = 115.0, 51.0  # 寝かせた袋。画像は横長（左右がシール）
    brown, cream, red = "#3A2218", "#F3E3C3", "#B8322A"
    c = Canvas(L, Wd, 14, brown, seed=131)
    c.gradient(0, 0, L, Wd, "#4A2C1F", "#2A170F")
    c.photo("chocolate", 56, 0, L - 8, Wd, crop=(0.41, 0.26, 0.61, 0.41), feather=6)
    seal_crimp(c, 0, 0, 8, Wd, "#4A2C1F", 1.0, vertical=True)
    seal_crimp(c, L - 8, 0, L, Wd, "#2A170F", 1.0, vertical=True)
    c.rect(12, 8, 60, 30, fill=cream, radius=3)
    c.text(36, 15.5, "チョコレート", 6.0, brown, 900)
    c.text(36, 24.5, "ココアクッキー入り", 3.8, red, 800)
    c.text(36, 36, "CHOCOLATE BAR", 3.4, cream, 700, spacing=0.6)
    c.text(14, 44, "準チョコレート菓子  1本", 2.6, cream, 500, anchor="lm")
    img = trim_safe(edge_shade(finish(c.array(), "film", 131, 1.0), 20, 0.2))

    # 裏面（表と同じ横長の向き。長い辺を軸に裏返すと読める）
    b = Canvas(L, Wd, 14, brown, seed=132)
    b.gradient(0, 0, L, Wd, "#4A2C1F", "#2A170F")
    seal_crimp(b, 0, 0, 8, Wd, "#4A2C1F", 1.0, vertical=True)
    seal_crimp(b, L - 8, 0, L, Wd, "#2A170F", 1.0, vertical=True)
    b.rect(11, 4, L - 11, Wd - 4, fill=cream, radius=2)
    rows = [("名称", "準チョコレート菓子"), ("原材料名", "砂糖、植物油脂、小麦粉、ココアパウダー、全粉乳、カカオマス／乳化剤、香料"),
            ("内容量", "1本"), ("賞味期限", "この面の右下に記載"), ("保存方法", "28℃以下で保存")]
    y = b.table(13, 6, 66, "", rows, 1.9, INK, "#FFFFFF")
    y = b.paragraph(13, y + 1.0, 66, NOTICE, 1.6, INK, 500)
    nutrition = [("エネルギー", "118kcal"), ("たんぱく質", "1.4g"), ("脂質", "6.9g"), ("炭水化物", "12.8g"), ("食塩相当量", "0.05g")]
    y2 = b.table(69, 6, L - 13, "栄養成分表示 1本当たり", nutrition, 1.9, INK, "#FFFFFF")
    assert y < Wd - 5 and y2 < Wd - 17, (y, y2)
    b.barcode(69, Wd - 16, 22, 11)
    b.recycle(L - 18, Wd - 10.5, 6, "プラ", brown)
    back = trim_safe(edge_shade(finish(b.array(), "film", 132, 1.0), 20, 0.2))
    return Product(slug="chocolate_bar", name="チョコレートバー ココアクッキー", shape_class="pouch", category="food",
                   dims=Dimensions(0.115, 0.051, depth=0.02), mass_kg=0.022, material="film", orientation="lying",
                   description="形は一般的な個包装のチョコバー（長さ 115 mm・幅 51 mm・厚さ 20 mm）で、寸法・質量は代表値。裏に一括表示と栄養成分表示。",
                   tags=["チョコレート", "チョコバー", "お菓子", "chocolate bar", "snack"], photos=["chocolate"],
                   colors=Colors(label_base=brown), images=[img, back], faces={"front": 0, "back": 1})


def pocket_tissue() -> Product:
    L, Wd = 105.0, 75.0
    sky, white, blue = "#CFE6F5", "#FFFFFF", "#2D6FA3"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 12, white, seed=seed)
        c.gradient(0, 0, L, Wd, "#E4F1FA", "#BCDCF0")
        c.pattern(0, 0, L, Wd, "dots", mix(sky, white, 0.6), 4, 0.6)
        seal_crimp(c, 0, 0, 5, Wd, "#D6EAF7", 0.8, vertical=True)
        seal_crimp(c, L - 5, 0, L, Wd, "#C4E0F2", 0.8, vertical=True)
        return c

    c = base(141)
    # 取り出し口のミシン目
    x = 20.0
    while x < L - 20:
        c.rect(x, Wd / 2 - 0.25, x + 2.2, Wd / 2 + 0.25, fill=mix(blue, white, 0.3))
        x += 3.6
    c.text(L / 2, 18, "ポケットティッシュ", 6.4, blue, 900)
    c.text(L / 2, 27, "やわらか 2枚重ね", 3.6, mix(blue, white, 0.2), 700)
    c.text(L / 2, 50, "POCKET TISSUE", 3.6, blue, 700, spacing=1.0)
    c.text(L / 2, 60, "20枚（10組）", 3.4, INK, 600)
    img = trim_safe(edge_shade(finish(c.array(), "film", 141, 0.9), 15, 0.12))

    # 裏面（表と同じ横長の向き）: 表示とバーコード。取り出し口は表だけ
    b = base(142)
    b.text(L / 2, 13, "POCKET TISSUE", 4.0, blue, 800, spacing=1.0)
    b.rect(12, 20, L - 12, 66, fill=white, radius=2)
    rows = [("品名", "ティシュペーパー"), ("材質", "パルプ 100%"), ("枚数", "20枚（10組）"), ("寸法", "195 × 205 mm")]
    y = b.table(15, 23, 64, "", rows, 2.4, INK, white)
    y = b.paragraph(15, y + 1.2, 64, "水に溶けにくいので、トイレに流さないでください。\n" + NOTICE, 2.1, INK, 500)
    assert y < 64, y
    b.barcode(68, 24, 24, 16)
    b.recycle(80, 54, 8, "プラ", blue, sub="袋")
    back = trim_safe(edge_shade(finish(b.array(), "film", 142, 0.9), 15, 0.12))
    return Product(slug="pocket_tissue", name="ポケットティッシュ 20枚", shape_class="pouch", category="household",
                   dims=Dimensions(0.105, 0.075, depth=0.012), mass_kg=0.012, material="film", orientation="lying",
                   description="形は一般的なポケットティッシュ（105 × 75 mm、厚さ 12 mm）で、寸法・質量は代表値。表に取り出し口、裏に表示。",
                   tags=["ティッシュ", "ポケットティッシュ", "pocket tissue", "tissue"], photos=[],
                   colors=Colors(label_base=sky), images=[img, back], faces={"front": 0, "back": 1})


def stick_snack_box() -> Product:
    W, D, H = 90.0, 23.0, 162.0
    navy, cream, gold = "#1F2F5C", "#F7EEDB", "#E2A93B"
    s = 10

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, navy, seed)
        f.gradient(0, 0, w, h, "#2A3E78", "#17234A")
        return f

    fr = face(W, H, 151)
    fr.pattern(0, 0, W, H, "stripes", mix("#2A3E78", "#FFFFFF", 0.08), 8, 1.5)
    fr.photo("cheese_sticks", 6, 62, W - 6, 138, shape="round", radius=5, shadow=1.5, crop=(0.05, 0.1, 0.95, 0.9))
    fr.rect(8, 12, W - 8, 52, fill=cream, radius=4)
    fr.text(W / 2, 24, "チーズ", 11, navy, 900)
    fr.text(W / 2, 40, "スティック", 11, navy, 900, max_w=W - 22)
    fr.rect(W / 2 - 22, 142, W / 2 + 22, 152, fill=gold, radius=5)
    fr.text(W / 2, 147, "焼き菓子  2袋入", 4.4, navy, 900)
    fr.text(W / 2, 57, "CHEESE STICKS", 4.0, gold, 700, spacing=1.0)
    front = fr.array()

    bk = face(W, H, 152)
    bk.rect(5, 5, W - 5, H - 5, fill=cream, radius=2)
    y = back_info(bk, 8, 9, W - 8, [("名称", "焼き菓子"), ("原材料名", "小麦粉、ナチュラルチーズ、ショートニング、砂糖、全粉乳、食塩、酵母／膨脹剤"),
                                    ("内容量", "2袋（1袋 18本）"), ("賞味期限", "底面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")],
                  3.4, [("栄養成分表示 1袋当たり", ""), ("エネルギー", "182kcal"), ("たんぱく質", "3.6g"), ("脂質", "9.2g"),
                        ("炭水化物", "21.0g"), ("食塩相当量", "0.5g")], navy, cream)
    bk.barcode(W / 2 - 18, H - 32, 36, 20)
    bk.recycle(16, H - 22, 9, "紙", navy, sub="箱")
    bk.recycle(W - 16, H - 22, 9, "プラ", navy, sub="袋")
    back = bk.array()

    sides = []
    for k, seed in enumerate((153, 154)):
        sd = face(D, H, seed)
        sd.vtext(D / 2, 20, "チーズスティック", 6.5, cream, 900, gap=0.05)
        sd.rect(3, 120, D - 3, 150, fill=gold, radius=2)
        sd.vtext(D / 2, 125, "2袋", 4.4, navy, 900) if k == 0 else sd.vtext(D / 2, 125, "焼菓子", 4.4, navy, 900)
        sides.append(sd.array())
    tp = face(W, D, 155)
    tp.rect(3, 3, W - 3, D - 3, outline=gold, width=0.5, radius=2)
    tp.text(W / 2, D / 2 - 3, "チーズスティック", 5.0, cream, 900)
    tp.text(W / 2, D / 2 + 5, "← ここを押してあけてください", 2.6, gold, 700)
    bt = face(W, D, 156)
    bt.text(W / 2, D / 2 - 2, "賞味期限 2027.04.30", 3.0, cream, 600)
    bt.text(W / 2, D / 2 + 4, NOTICE, 2.0, cream, 400)
    imgs = [front, back, *sides, tp.array(), bt.array()]
    imgs = [trim_safe(edge_shade(finish(a, "paper", 160 + i, 0.8), 8, 0.1)) for i, a in enumerate(imgs)]
    return Product(slug="stick_snack_box", name="チーズスティック 2袋入", shape_class="box", category="food",
                   dims=Dimensions(0.162, 0.09, depth=0.023), mass_kg=0.07, material="paper",
                   description="形は一般的な細長い箱菓子（高さ 162 mm・幅 90 mm・奥行き 23 mm）で、寸法・質量は代表値。",
                   tags=["お菓子", "箱菓子", "チーズ", "スティック菓子", "snack", "cheese sticks"], photos=["cheese_sticks"],
                   colors=Colors(label_base=navy), images=imgs,
                   faces={"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5})


# ---------------------------------------------------------------- 什器（部品の組み合わせ）


def _screen(w_mm: float, h_mm: float, seed: int, px: int = 1600) -> Canvas:
    return Canvas(w_mm, h_mm, px / max(w_mm, h_mm), "#000000", seed)


def _ad(pid: str, title: str, sub: str, price: str, accent: str, seed: int, crop=None) -> np.ndarray:
    """横長の画面広告（16:9）。"""
    w, h = 930.0, 523.0
    c = _screen(w, h, seed)
    c.photo(pid, 0, 0, w, h, crop=crop)
    c.gradient(0, 0, w * 0.48, h, "#0D0D0D", "#2A2A2A", horizontal=False)
    c.photo(pid, w * 0.42, 0, w, h, crop=crop, feather=60)
    c.rect(40, 60, 70, 64, fill=accent)
    c.text(40, 120, title, 64, "#FFFFFF", 900, anchor="lm", max_w=w * 0.4)
    c.text(40, 190, sub, 30, "#DDDDDD", 600, anchor="lm", max_w=w * 0.4)
    c.rect(40, 330, 330, 430, fill=accent, radius=14)
    c.text(185, 380, price, 54, "#FFFFFF", 900, max_w=260)
    c.text(40, 490, "※写真はイメージです", 16, "#BBBBBB", 400, anchor="lm")
    return trim_safe(finish(c.array(), "screen", seed, 0.6))


def _box(name, size, center, color, finish_="plastic", faces=None, rotation=None, collision=True,
         thin_walled=False, blank=None) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=rotation or [0, 0, 0],
                color=color, finish=finish_, faces=faces, collision=collision, thin_walled=thin_walled, blank=blank)


COOL_WHITE, WARM_WHITE = 5700.0, 2800.0  # 冷蔵ケースの LED（昼白色）・温蔵ケースのランプ（電球色）の色温度 [K]
# 照明の輝度 [nit] は、ケースの中の棚の上が天井照明（office）の下の床・台と同じくらい（1000〜2000 lx）、
# 冷蔵ケースは商品の正面が棚の前面と同じくらい（500〜1000 lx）になるように選ぶ（tests/test_lighting.py）
LAMP_TILT = 35.0  # 棚の前の縁の LED を奥へ傾ける角度 [度]


def _lamp(name, size, center, color, intensity, kelvin, facing="down", tilt=0.0) -> tuple[Part, Light]:
    """照明の面の部品（finish light）と、その光る面のすぐ外に置く面光源。
    facing が down なら size は (幅, 奥行き, 厚さ) で下へ照らす。tilt [度] だけ奥へ傾ける（棚の前の縁の LED を
    奥の商品の正面へ向ける）。back なら (幅, 厚さ, 高さ) で奥（+Y）へ照らす。"""
    x, y, z = center
    if facing == "down":
        a = math.radians(tilt)
        off = size[2] / 2 + 0.001  # 光る面（部品の下の面）のすぐ外
        light = Light(name=f"{name}Lux", size=[size[0], size[1]],
                      center=[x, y + off * math.sin(a), z - off * math.cos(a)], rotation=[tilt, 0.0, 0.0],
                      intensity=intensity, kelvin=kelvin)
        rot = [tilt, 0.0, 0.0]
    else:
        light = Light(name=f"{name}Lux", size=[size[0], size[2]], center=[x, y + size[1] / 2 + 0.001, z],
                      rotation=[90.0, 0.0, 0.0], intensity=intensity, kelvin=kelvin)
        rot = None
    return _box(name, size, center, color, "light", rotation=rot, collision=False), light


def _cyl(name, size, center, color, finish_="metal", collision=True) -> Part:
    return Part(name=name, shape="cylinder", size=list(size), center=list(center), color=color, finish=finish_,
                collision=collision)


def _pump_bottle(D: float, body_h: float, label: tuple[float, float], color: str) -> tuple[forms.RevolveForm, list[Part]]:
    """ポンプ式のボトル。回転体はボトルとねじ蓋（カラー）まで、軸・押し頭・ノズルは部品で足す。"""
    base = forms.pump_bottle(body_h + 0.05, D, body_h=body_h, label=label)
    collar_r = 0.0145
    top = body_h + 0.018  # カラーの上面（回転体の高さ）
    form = forms.RevolveForm(base.body, [(body_h, collar_r), (body_h + 0.016, collar_r), (top, collar_r * 0.85)], label)
    parts = [Part("PumpStem", "cylinder", [0.009, 0.009, 0.026], [0, 0, top + 0.012], color=color, finish="plastic"),
             Part("PumpHead", "cylinder", [0.030, 0.030, 0.014], [0, 0, top + 0.031], color=color, finish="plastic"),
             Part("Nozzle", "box", [0.010, 0.032, 0.008], [0, -0.020, top + 0.033], color=color, finish="plastic")]
    return form, parts


def digital_signage_ceiling_3x() -> Product:
    ads = [_ad("onigiri", "おにぎりフェア", "具だくさんの手づくり風", "2個で 260円", "#C0392B", 171, (0.0, 0.1, 1.0, 0.9)),
           _ad("latte", "カフェラテ", "ミルクたっぷり ホット／アイス", "Mサイズ 180円", "#8D5A2B", 172, (0.0, 0.1, 1.0, 0.9)),
           _ad("berries", "フルーツカップ", "旬のベリーをひとくちサイズで", "298円", "#2E8B57", 173, (0.0, 0.15, 1.0, 0.85))]
    parts = []
    for k, x in enumerate((-0.97, 0.0, 0.97)):
        tag = ("Left", "Center", "Right")[k]
        parts.append(_box(f"Bezel{tag}", (0.955, 0.03, 0.55), (x, 0, 0.275), "#161616"))
        parts.append(_box(f"Screen{tag}", (0.93, 0.002, 0.523), (x, -0.016, 0.275), "#D8E0EE", "screen", {"front": k},
                          collision=False))
    parts += [_box("MountRail", (2.6, 0.04, 0.04), (0, 0.035, 0.44), "#2A2A2A", "metal")]
    for tag, x in (("Left", -0.97), ("Right", 0.97)):
        parts += [_cyl(f"HangerPipe{tag}", (0.034, 0.034, 0.35), (x, 0.035, 0.635), "#2A2A2A"),
                  _cyl(f"CeilingPlate{tag}", (0.1, 0.1, 0.01), (x, 0.035, 0.815), "#2A2A2A")]
    return Product(slug="digital_signage_ceiling_3x", name="天井吊りデジタルサイネージ 3面", shape_class="assembly",
                   category="fixture", dims=Dimensions(0.82, 2.895, depth=0.1), mass_kg=36.0, static=True, mount="ceiling",
                   description="形は 42 型前後の横長ディスプレイ 3 面を天井から吊る一般的なサイネージで、寸法・質量は代表値。画面は架空の広告。",
                   tags=["デジタルサイネージ", "ディスプレイ", "天井吊り", "店舗什器", "digital signage", "display"],
                   photos=["onigiri", "latte", "berries"], images=ads, parts=parts)


def digital_signage_stand_43() -> Product:
    w, h = 535.0, 950.0
    c = Canvas(w, h, 1600 / h, "#000000", 181)
    c.photo("latte", 0, 0, w, h * 0.62, crop=(0.15, 0.0, 0.85, 1.0))
    c.gradient(0, h * 0.55, w, h, "#3A2416", "#1A0F08")
    c.photo("coffee_beans", 0, h * 0.86, w, h, crop=(0, 0.3, 1, 0.6), feather=20)
    c.text(w / 2, h * 0.66, "本日のおすすめ", 34, "#E9C27A", 700)
    c.text(w / 2, h * 0.72, "カフェラテ", 70, "#FFFFFF", 900)
    c.text(w / 2, h * 0.78, "エスプレッソ × ミルク", 28, "#DDDDDD", 600)
    c.rect(w / 2 - 160, h * 0.81, w / 2 + 160, h * 0.86, fill="#C8873A", radius=12)
    c.text(w / 2, h * 0.835, "180円（税込）", 40, "#FFFFFF", 900, max_w=290)
    ad = trim_safe(finish(c.array(), "screen", 181, 0.6))
    parts = [_box("BasePlate", (0.62, 0.44, 0.025), (0, 0, 0.0125), "#1A1A1A", "metal"),
             _box("BaseRise", (0.6, 0.16, 0.035), (0, -0.01, 0.0425), "#1A1A1A", "metal"),
             _box("Frame", (0.62, 0.035, 1.73), (0, -0.028, 0.925), "#202020"),
             _box("RearHousing", (0.48, 0.06, 0.48), (0, 0.016, 0.3), "#202020"),
             _box("FrontGlass", (0.608, 0.003, 1.715), (0, -0.047, 0.925), "#0A0A0A", "glossy", collision=False),
             _box("Screen", (0.535, 0.003, 0.95), (0, -0.0495, 1.27), "#1E2226", "screen", {"front": 0}, collision=False)]
    return Product(slug="digital_signage_stand_43", name="スタンド型デジタルサイネージ 43型", shape_class="assembly",
                   category="fixture", dims=Dimensions(1.79, 0.62, depth=0.44), mass_kg=50.0, static=True,
                   description="形は 43 型の縦置きディスプレイを使う一般的なスタンド型サイネージで、寸法・質量は代表値。画面は架空の広告。",
                   tags=["デジタルサイネージ", "スタンド", "縦型ディスプレイ", "店舗什器", "digital signage"],
                   photos=["latte", "coffee_beans"], images=[ad], parts=parts)


def coffee_machine() -> Product:
    w, h = 300.0, 318.0
    c = Canvas(w, h, 1400 / h, "#2A2C30", 191)
    c.gradient(0, 0, w, h, "#3A3D42", "#1C1D20")
    c.rect(20, 18, w - 20, 120, fill="#101113", radius=6)
    c.photo("coffee_cup", 24, 22, 120, 116, shape="round", radius=4, crop=(0.15, 0.1, 0.85, 0.9))
    c.text(130, 44, "セルフコーヒー", 16, "#FFFFFF", 900, anchor="lm")
    c.text(130, 70, "カップを置いて", 11, "#CCCCCC", 600, anchor="lm")
    c.text(130, 88, "ボタンを押してください", 11, "#CCCCCC", 600, anchor="lm")
    labels = [("ホット R", "#B5452F"), ("ホット L", "#B5452F"), ("カフェラテ", "#8D5A2B"),
              ("アイス R", "#2F6DB5"), ("アイス L", "#2F6DB5"), ("アイスラテ", "#5B7FA6")]
    for i, (t, col) in enumerate(labels):
        x0 = 22 + (i % 3) * 88
        y0 = 140 + (i // 3) * 64
        c.rect(x0, y0, x0 + 80, y0 + 52, fill=col, radius=8, outline="#E6E6E6", width=1.0)
        c.text(x0 + 40, y0 + 26, t, 13, "#FFFFFF", 800)
    c.text(w / 2, 282, "抽出中はカップを取り出さないでください", 10, "#E9C27A", 700)
    c.text(w / 2, 302, NOTICE, 7, "#9A9A9A", 400)
    panel = trim_safe(finish(c.array(), "metal", 191, 0.6))
    parts = [_box("Base", (0.31, 0.56, 0.07), (0, 0, 0.035), "#141416"),
             _box("Body", (0.295, 0.46, 0.63), (0, 0.05, 0.385), "#1C1D20"),
             _box("Panel", (0.31, 0.12, 0.318), (0, -0.22, 0.476), "#2A2C30", "metal", {"front": 0}),
             _box("StageWallLeft", (0.02, 0.12, 0.25), (-0.145, -0.22, 0.195), "#1C1D20"),
             _box("StageWallRight", (0.02, 0.12, 0.25), (0.145, -0.22, 0.195), "#1C1D20"),
             _box("StageRecess", (0.27, 0.04, 0.25), (0, -0.18, 0.195), "#0A0A0B", "matte"),
             _box("DripTray", (0.26, 0.1, 0.02), (0, -0.225, 0.08), "#3C3F44", "metal"),
             _box("Nozzle", (0.07, 0.05, 0.03), (0, -0.205, 0.305), "#9EA2A8", "metal", collision=False),
             _box("BeanHopper", (0.2, 0.2, 0.13), (0, -0.04, 0.765), "#202226", "glossy")]
    return Product(slug="coffee_machine", name="セルフ式コーヒーマシン", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.83, 0.31, depth=0.56), mass_kg=40.0, static=True,
                   description="形は店舗のセルフ式コーヒーマシンの一般的な構成（本体・操作パネル・抽出口・豆ホッパー）で、寸法・質量は代表値。",
                   tags=["コーヒーマシン", "セルフコーヒー", "店舗什器", "coffee machine"], photos=["coffee_cup"],
                   images=[panel], parts=parts)


def chest_freezer_showcase() -> Product:
    w, h = 1120.0, 205.0
    c = Canvas(w, h, 2400 / w, "#F4F5F7", 201)
    c.gradient(0, 0, w, h, "#2C6FB7", "#174C8A")
    c.pattern(0, 0, w, h, "dots", "#3B82C9", 14, 2.0)
    for k in range(5):
        cx = 70 + k * 245
        c.ellipse(cx - 30, h / 2 - 30, cx + 30, h / 2 + 30, outline="#BFE0FF", width=3)
        c.line([(cx - 22, h / 2), (cx + 22, h / 2)], "#BFE0FF", 3)
        c.line([(cx, h / 2 - 22), (cx, h / 2 + 22)], "#BFE0FF", 3)
    c.rect(170, 35, w - 170, h - 35, fill="#FFFFFF", radius=16)
    c.text(w / 2, h / 2 - 12, "冷凍食品", 72, "#174C8A", 900)
    c.text(w / 2, h / 2 + 42, "FROZEN FOODS  −18℃以下で保存", 24, "#2C6FB7", 700)
    sign = trim_safe(finish(c.array(), "film", 201, 0.6))
    parts = []
    for tag, x, y in (("FL", -0.54, -0.29), ("FR", 0.54, -0.29), ("BL", -0.54, 0.29), ("BR", 0.54, 0.29)):
        parts.append(_cyl(f"Caster{tag}", (0.06, 0.06, 0.075), (x, y, 0.0375), "#8E9296"))
    parts += [_box("CabinetLower", (1.2, 0.7, 0.38), (0, 0, 0.26), "#F4F5F7"),
              _box("FrontWall", (1.12, 0.04, 0.205), (0, -0.33, 0.5525), "#F4F5F7", faces={"front": 0}),
              _box("FrontWindow", (1.12, 0.008, 0.12), (0, -0.346, 0.715), "#EAF2F5", "glass"),
              _box("FrontRail", (1.12, 0.04, 0.025), (0, -0.33, 0.7875), "#F4F5F7"),
              _box("SideWallL", (0.04, 0.7, 0.35), (-0.58, 0, 0.625), "#F4F5F7"),
              _box("SideWallR", (0.04, 0.7, 0.35), (0.58, 0, 0.625), "#F4F5F7"),
              _box("BackWall", (1.12, 0.04, 0.35), (0, 0.33, 0.625), "#F4F5F7"),
              _box("InnerLiner", (1.12, 0.62, 0.005), (0, 0, 0.4525), "#DCE3E8", "matte", collision=False),
              _box("BottomTrim", (1.18, 0.69, 0.03), (0, 0, 0.085), "#C9CCCF"),
              _box("TopRim", (1.2, 0.56, 0.03), (0, -0.07, 0.815), "#B9BCBE", "metal"),
              _box("Shade", (1.2, 0.14, 0.12), (0, 0.28, 0.86), "#EEF0EE"),
              _box("ShadeCap", (1.2, 0.14, 0.012), (0, 0.28, 0.914), "#6A6B66", "metal")]
    # ガラスの引き戸 2 枚（右を少し上に重ねる）。縁は細い金属の枠で、中は透けて商品が見える
    for side, x, z in (("Left", -0.29, 0.835), ("Right", 0.29, 0.837)):
        parts.append(_box(f"GlassLid{side}", (0.57, 0.51, 0.006), (x, -0.07, z), "#EAF2F5", "glass"))
        for edge, size, dx, dy in (("Front", (0.57, 0.02, 0.012), 0, -0.245), ("Back", (0.57, 0.02, 0.012), 0, 0.245),
                                   ("L", (0.02, 0.47, 0.012), -0.275, 0), ("R", (0.02, 0.47, 0.012), 0.275, 0)):
            parts.append(_box(f"LidFrame{side}{edge}", size, (x + dx, -0.07 + dy, z), "#B9BCBE", "metal",
                              collision=False))
    # 奥の覆い（Shade）の下の面の LED。手前へ傾けて、ふたの下の商品の上面を照らす
    part, light = _lamp("ShadeLight", (1.08, 0.04, 0.008), (0, 0.26, 0.796), "#FFFFFF", 12000.0, COOL_WHITE,
                        tilt=-50.0)
    parts.append(part)
    return Product(slug="chest_freezer_showcase", name="平型冷凍ショーケース", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.92, 1.2, depth=0.7), mass_kg=75.0, static=True, material="steel",
                   description="形は店舗の平型（チェスト型）冷凍ショーケースの一般的な構成（キャスター・本体・ガラスの引き戸・上部の覆い）で、寸法・質量は代表値。",
                   tags=["冷凍ショーケース", "冷凍庫", "ショーケース", "店舗什器", "freezer", "showcase"], photos=[],
                   colors=Colors(label_base="#F4F5F7"), images=[sign], parts=parts, lights=[light])


def self_checkout() -> Product:
    w, h = 359.0, 280.0
    c = Canvas(w, h, 1600 / w, "#FFFFFF", 211)
    c.gradient(0, 0, w, h, "#FFFFFF", "#E9EEF3")
    c.rect(0, 0, w, 28, fill="#1F6F5C")
    c.text(12, 14, "お会計", 14, "#FFFFFF", 900, anchor="lm")
    c.text(w - 12, 14, "1 / 2", 10, "#FFFFFF", 600, anchor="rm")
    items = [("おにぎり 鮭", "150"), ("おにぎり 昆布", "130"), ("カフェラテ M", "180"), ("緑茶 600ml", "140"),
             ("ポテトチップス うすしお", "150")]
    y = 40.0
    for name, price in items:
        c.text(14, y + 8, name, 10, INK, 600, anchor="lm")
        c.text(232, y + 8, f"{price}円", 10, INK, 700, anchor="rm")
        c.line([(10, y + 17), (240, y + 17)], "#CCD3DA", 0.6)
        y += 22
    c.rect(250, 40, w - 10, 160, fill="#F4F7FA", outline="#CCD3DA", width=0.6, radius=6)
    c.text((250 + w - 10) / 2, 58, "点数 5点", 10, INK, 700)
    c.text((250 + w - 10) / 2, 86, "合計", 11, INK, 700)
    c.text((250 + w - 10) / 2, 112, "750円", 22, "#C0392B", 900)
    c.text((250 + w - 10) / 2, 140, "（税込）", 9, INK, 500)
    c.rect(12, 200, 170, 262, fill="#E0E5EA", radius=8)
    c.text(91, 231, "商品をスキャン", 13, INK, 800)
    c.rect(186, 200, w - 12, 262, fill="#1F6F5C", radius=8)
    c.text((186 + w - 12) / 2, 231, "お支払いへ", 15, "#FFFFFF", 900)
    screen = trim_safe(finish(c.array(), "screen", 211, 0.5))
    parts = [_box("Plinth", (0.98, 0.66, 0.06), (-0.16, 0.06, 0.03), "#26282B", "matte"),
             _box("CashCabinet", (0.4, 0.69, 0.92), (-0.45, 0.05, 0.51), "#EEEFF0"),
             _box("CashPanel", (0.22, 0.11, 0.31), (-0.47, -0.34, 0.745), "#1E2023"),
             _box("CenterCabinet", (0.42, 0.69, 0.53), (-0.035, 0.05, 0.315), "#EEEFF0"),
             _box("BagCabinet", (0.16, 0.5, 0.5), (0.255, 0.1, 0.3), "#EEEFF0"),
             _box("BagTable", (0.47, 0.45, 0.03), (0.41, 0.05, 0.565), "#E2E3E5"),
             _box("ScannerTower", (0.37, 0.12, 0.6), (-0.03, 0.3, 0.87), "#C9CBCE", "metal"),
             _box("ScannerShelf", (0.37, 0.4, 0.04), (-0.03, 0.1, 0.94), "#D5D7DA", "metal"),
             _box("Screen", (0.359, 0.05, 0.28), (-0.035, 0.2, 1.29), "#1A1B1D", "screen", {"front": 0}, [-20, 0, 0]),
             _box("Printer", (0.18, 0.3, 0.17), (-0.3, 0.1, 1.075), "#3A3C40"),
             _box("PaymentTerminal", (0.085, 0.09, 0.16), (-0.31, 0.06, 1.24), "#1A1A1A", rotation=[-15, 0, 0]),
             _box("HandScanner", (0.14, 0.12, 0.32), (0.25, 0.24, 1.13), "#2A2C2F"),
             _cyl("SignalPole", (0.075, 0.075, 1.18), (0.255, 0.32, 1.55), "#DADDE0", "plastic")]
    return Product(slug="self_checkout", name="セルフレジ", shape_class="assembly", category="fixture",
                   dims=Dimensions(2.14, 1.29, depth=0.79), mass_kg=200.0, static=True, material="steel",
                   description="形は店舗のセルフレジの一般的な構成（精算機・スキャナー・画面・袋詰め台・表示灯）で、寸法・質量は代表値。画面は架空の会計画面。",
                   tags=["セルフレジ", "レジ", "POS", "店舗什器", "self checkout"], photos=[],
                   colors=Colors(label_base="#EEEFF0"), images=[screen], parts=parts)


# ---------------------------------------------------------------- 追加分（飲料）


def _face(img: np.ndarray, kind: str, seed: int, strength: float = 0.8, shade: int = 8) -> np.ndarray:
    """箱・部品の面の仕上げ（質感・縁の陰）。縁が単色だと切り抜かれるので trim_safe で確かめる。"""
    return trim_safe(edge_shade(finish(img, kind, seed, strength), shade, 0.1))


def _food(name: str, shape: str, size, center, color: str, finish_: str = "matte", rotation=None,
          profile=None, faces=None) -> Part:
    """中身の部品（コリジョンなし、素材 food）。faces={"top": i} で dome・bun の山に写真を真上から貼れる。"""
    return Part(name, shape, list(size), list(center), list(rotation or [0, 0, 0]), color=color, finish=finish_,
                collision=False, material="food", profile=profile, faces=faces)


def _food_photo(pid: str, w: float, d: float, crop, seed: int, strength: float = 0.3) -> np.ndarray:
    """中身の部品の上面に貼る写真（w×d mm をすき間なく覆う）。"""
    c = Canvas(w, d, 8, "#808080", seed)
    c.photo(pid, 0, 0, w, d, crop=crop)
    return finish(c.array(), "paper", seed, strength)


def _can_top(form, seed: int) -> np.ndarray:
    """缶の上面（ステイオンタブ）。"""
    t = top_canvas(form, "#B9BDC1", seed=seed)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D5D8DB", "#9DA2A7")
    t.ellipse(2, 2, d - 2, d - 2, outline="#8D9196", width=0.8)
    t.ellipse(5, 5, d - 5, d - 5, outline="#C7CACD", width=0.5)
    t.rect(d / 2 - 6, d * 0.58, d / 2 + 6, d * 0.84, fill="#C4C7CA", outline="#8A8E92", width=0.4, radius=5)
    t.ellipse(d / 2 - 3, d * 0.7, d / 2 + 3, d * 0.8, fill="#9DA2A7")
    t.ellipse(d / 2 - 1.2, d * 0.5, d / 2 + 1.2, d * 0.55, fill="#8A8E92")
    t.rect(d / 2 - 8, d * 0.2, d / 2 + 8, d * 0.42, outline="#A4A8AC", width=0.4, radius=6)
    return finish(t.array(), "metal", seed, 0.6)


def milk_carton_1l() -> Product:
    W, H = 70.0, 195.0  # 胴の 1 面
    blue, sky, white = "#1D4F9C", "#D9E8F7", "#FFFFFF"
    s = 10

    fr = Canvas(W, H, s, white, 221)
    fr.gradient(0, 0, W, 34, "#2A63B8", blue)
    fr.text(W / 2, 11, "成分無調整", 5.2, white, 800)
    fr.text(W / 2, 24, "生乳 100%", 6.0, white, 900)
    fr.vtext(W / 2, 45, "牛乳", 20, blue, 900, gap=0.05)
    fr.text(W / 2, 92, "MILK", 6.0, blue, 800, spacing=1.6)
    fr.photo("milk", 6, 99, W - 6, 158, shape="round", radius=4, crop=(0.33, 0.4, 0.67, 0.95))
    fr.rect(8, 162, W - 8, 171, fill=sky, radius=4.5)
    fr.text(W / 2, 166.5, "種類別  牛乳", 4.0, blue, 800)
    fr.text(W / 2, 182, "1000ml", 9.0, blue, 900)
    fr.pattern(0, 189, W, H, "waves", "#7FA7DB", 3.2, 0.5)

    rt = Canvas(W, H, s, white, 222)
    rt.rect(0, 0, W, 8, fill=blue)
    y = back_info(rt, 4, 12, W - 4, [
        ("種類別名称", "牛乳"), ("無脂乳固形分", "8.3%以上"), ("乳脂肪分", "3.5%以上"), ("原材料名", "生乳 100%"),
        ("殺菌", "130℃ 2秒間"), ("内容量", "1000ml"), ("賞味期限", "上部に記載"), ("保存方法", "要冷蔵（10℃以下）"),
        ("製造所", "架空の乳業 第一工場")], 2.4,
        [("栄養成分表示 200ml当たり", ""), ("エネルギー", "137kcal"), ("たんぱく質", "6.8g"), ("脂質", "7.8g"),
         ("炭水化物", "9.9g"), ("食塩相当量", "0.2g"), ("カルシウム", "227mg")], blue)
    rt.text(W / 2, y + 6, "開封後は賞味期限にかかわらず", 2.6, blue, 700)
    rt.text(W / 2, y + 10, "なるべく早くお飲みください", 2.6, blue, 700)

    bk = Canvas(W, H, s, white, 223)
    bk.rect(0, 0, W, 8, fill=blue)
    bk.vtext(W / 2, 22, "おいしい牛乳", 9, blue, 900, gap=0.05)
    bk.barcode(W / 2 - 18, 112, 36, 20)
    bk.recycle(W / 2, 150, 12, "紙パック", blue)
    bk.text(W / 2, 166, "洗って開いて", 3.0, blue, 700)
    bk.text(W / 2, 171, "リサイクルへ", 3.0, blue, 700)
    bk.pattern(0, 189, W, H, "waves", "#7FA7DB", 3.2, 0.5)

    lf = Canvas(W, H, s, sky, 224)
    lf.gradient(0, 0, W, H, white, sky)
    lf.vtext(W / 2 + 12, 20, "成分無調整", 7, blue, 900)
    lf.vtext(W / 2 - 10, 20, "生乳だけでつくりました", 4.0, blue, 700)
    lf.text(W / 2, 170, "MILK 1000ml", 4.4, blue, 800, spacing=0.4)
    lf.pattern(0, 189, W, H, "waves", "#7FA7DB", 3.2, 0.5)

    gd = 49.5  # 屋根の斜面（45° に回した角柱の面）
    gf = Canvas(W, gd, s, blue, 225)
    gf.gradient(0, 0, W, gd, "#2A63B8", blue)
    gf.text(W / 2, gd * 0.42, "牛乳", 11, white, 900)
    gf.text(W / 2, gd * 0.75, "1000ml", 4.6, white, 800)
    gb = Canvas(W, gd, s, white, 226)
    gb.gradient(0, 0, W, gd, white, sky)
    gb.text(W / 2, gd * 0.38, "あけくち", 6.0, blue, 900)
    gb.polygon([(W / 2 - 5, gd * 0.55), (W / 2 + 5, gd * 0.55), (W / 2, gd * 0.68)], fill=blue)
    gb.text(W / 2, gd * 0.82, "賞味期限 2026.11.02", 3.0, INK, 600)
    imgs = [_face(c.array(), "paper", 230 + i) for i, c in enumerate((fr, rt, bk, lf, gf, gb))]

    sq = 0.0495
    parts = [_box("Body", (0.07, 0.07, 0.195), (0, 0, 0.0975), white, "plastic",
                  {"front": 0, "right": 1, "back": 2, "left": 3}),
             _box("Gable", (0.0694, sq, sq), (0, 0, 0.195), white, "plastic", {"top": 4, "back": 5}, [45, 0, 0]),
             _box("TopFin", (0.07, 0.006, 0.012), (0, 0, 0.232), "#F2F4F7")]
    return Product(slug="milk_carton_1l", name="牛乳 1000ml", shape_class="assembly", category="beverage",
                   dims=Dimensions(0.238, 0.07, depth=0.07), mass_kg=1.06, capacity_ml=1000, material="paper",
                   description="形は一般的な 1000ml の屋根型紙パック（胴 70 × 70 mm・高さ 238 mm）で、寸法・質量は代表値。",
                   tags=["牛乳", "紙パック", "乳製品", "1000ml", "milk", "milk carton"], photos=["milk"],
                   colors=Colors(label_base=white), images=imgs, parts=parts)


def sparkling_water_can_350ml() -> Product:
    form = forms.aluminum_can(0.122, 0.066, top_d=0.054, label_margin=0.008)
    navy, cyan, white = "#0B2A4A", "#3FB6E0", "#FFFFFF"
    c = label_canvas(form, navy, seed=241)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#0E3A66", "#081D33")
    for _ in range(140):  # 泡
        x, y, r = c.rng.uniform(0, W), c.rng.uniform(0, H), c.rng.uniform(0.6, 3.2)
        c.ellipse(x - r, y - r, x + r, y + r, outline=mix(cyan, navy, c.rng.uniform(0.1, 0.6)), width=0.35)
    c.rect(0, 0, W, 3, fill=cyan)
    c.rect(0, H - 3, W, H, fill=cyan)
    c.rect(fx - 13, 7, fx + 13, 66, fill=white, radius=2)
    c.vtext(fx, 13, "強炭酸水", 11.5, navy, 900, gap=0.02)
    c.text(fx, 72, "SPARKLING WATER", 3.6, cyan, 800, spacing=0.5)
    c.rect(fx - 18, 77, fx + 18, 84, fill=cyan, radius=3.5)
    c.text(fx, 80.5, "無糖  0kcal", 4.0, navy, 900)
    c.text(fx, H - 7, "350ml", 4.2, white, 800)
    c.vtext(fx + 22, 12, "刺激的", 4.4, cyan, 900)
    c.vtext(0.5 * W, 8, "炭酸ガス圧が高い", 3.6, white, 800)
    _bottle_back(c, 0.25 * W, 8, 42, "炭酸水", "水／炭酸", 1.9, color=white, bg=navy,
                 extra=[("内容量", "350ml"), ("賞味期限", "缶底に記載"), ("保存方法", "高温・直射日光を避けて保存")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
                            ("炭水化物", "0g"), ("食塩相当量", "0.02g")], notice_color=white)
    c.rect(0.5 * W - 14, 46, 0.5 * W + 14, 66, fill=white)
    c.barcode(0.5 * W - 12, 48, 24, 15)
    c.recycle(0.5 * W, 76, 8, "アルミ", white, kind="can")
    label = finish(c.array(), "metal", 241, 0.7)
    return Product(slug="sparkling_water_can_350ml", name="強炭酸水 350ml 缶", category="beverage", mass_kg=0.365,
                   capacity_ml=350, material="aluminum",
                   description="形は一般的な 350ml のアルミ缶（高さ 122 mm・胴径 66 mm、上すぼまりのネック）で、寸法・質量は代表値。",
                   tags=["炭酸水", "強炭酸", "アルミ缶", "無糖", "sparkling water", "soda water", "can"], photos=[],
                   colors=Colors(cap="#BFC2C5", label_base=navy), **revolve(form, label=label, top=_can_top(form, 242)))


def hojicha_pet_hot_345ml() -> Product:
    form = forms.pet_bottle(0.160, 0.066, shoulder=0.22, cap_h=0.019, cap_r=0.0148, label=(0.012, 0.088),
                            liquid_top=0.122)
    cream, brown, orange = "#F4EAD8", "#6B3E1F", "#E2701E"
    c = label_canvas(form, cream, seed=251)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F8F0E2", "#E9D6B8")
    c.pattern(0, 0, W, H, "waves", mix("#E9D6B8", brown, 0.18), 5, 0.4)
    c.rect(0, 0, W, 9, fill=orange)
    c.text(fx, 4.5, "HOT  加温販売できます", 3.6, "#FFFFFF", 900)
    c.rect(fx - 17, 12, fx + 17, 66, fill="#FFFFFF", radius=3)
    c.vtext(fx + 5, 18, "ほうじ茶", 10.5, brown, 900, gap=0.05)
    c.vtext(fx - 10, 18, "香ばしい焙煎", 4.0, orange, 800)
    steam(c, fx - 10, 64, 8, 5, mix(brown, "#FFFFFF", 0.4), 0.5)
    c.text(fx, H - 4, "茶飲料  345ml", 3.6, brown, 800)
    c.text(0.5 * W, 15, "ROASTED GREEN TEA", 2.6, brown, 700, spacing=0.4)
    _bottle_back(c, 0.25 * W, 12, 44, "ほうじ茶（清涼飲料水）", "緑茶（国産）／ビタミンC", 1.8,
                 extra=[("内容量", "345ml"), ("賞味期限", "キャップに記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("炭水化物", "0g"),
                            ("食塩相当量", "0.02g")])
    c.barcode(0.5 * W - 12, 24, 24, 15)
    c.recycle(0.5 * W - 6, 50, 7, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 50, 7, "プラ", INK, sub="ラベル")
    c.text(0.5 * W, 64, "電子レンジ不可", 2.6, "#C0392B", 900)
    label = finish(c.array(), "film", 251, 0.8)
    return Product(slug="hojicha_pet_hot_345ml", name="ほうじ茶 ホット 345ml", category="beverage", mass_kg=0.37,
                   capacity_ml=345, material="PET",
                   description="形は一般的な加温販売用の小型 PET ボトル（高さ 160 mm・胴径 66 mm、オレンジのキャップ）で、寸法・質量は代表値。",
                   tags=["ほうじ茶", "お茶", "茶飲料", "ホット", "ペットボトル", "hojicha", "roasted tea", "PET bottle"],
                   photos=[], colors=Colors(cap=orange, liquid="#9A5A2A", label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid="#9A5A2A"))


# ---------------------------------------------------------------- 追加分（食品）


def ice_cream_cup() -> Product:
    form = forms.paper_cup(0.052, 0.088, 0.066, lid_h=0.003, lid_overhang=0.0015, rim_h=0.004,
                           label_margin=(0.002, 0.002))
    pink, rose, white = "#F7C9D4", "#C2185B", "#FFFFFF"
    c = label_canvas(form, pink, seed=261)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FBDDE4", "#F3B3C3")
    c.pattern(0, 0, W, H, "dots", mix("#F3B3C3", white, 0.5), 5, 0.6)
    c.rect(0, H - 6, W, H, fill=rose)
    c.photo("berries", fx - 34, 4, fx - 2, 33, shape="ellipse", feather=1.0, shadow=1.0, crop=(0.25, 0.2, 0.75, 0.8))
    c.text(fx + 18, 13, "ストロベリー", 6.0, rose, 900, max_w=34)
    c.text(fx + 18, 23, "アイスクリーム", 4.2, rose, 800, max_w=34)
    c.text(fx + 18, 31, "STRAWBERRY", 2.8, white, 800, spacing=0.4)
    c.text(fx, H - 3, "種類別 アイスミルク  120ml", 2.8, white, 700)
    c.rect(0.25 * W - 28, 3, 0.25 * W + 28, H - 8, fill=white, radius=1.5)
    back_info(c, 0.25 * W - 27, 4, 0.25 * W + 27, [
        ("種類別", "アイスミルク"), ("無脂乳固形分", "8.0%"), ("乳脂肪分", "3.5%"),
        ("原材料名", "乳製品、砂糖、いちご果汁、水あめ／安定剤、香料、着色料"), ("内容量", "120ml")], 1.6, color=INK)
    c.barcode(0.5 * W - 10, 6, 20, 12)
    c.recycle(0.5 * W - 6, 27, 6, "紙", rose, sub="容器")
    c.recycle(0.5 * W + 6, 27, 6, "プラ", rose, sub="フタ")
    label = finish(c.array(), "paper", 261)

    t = top_canvas(form, pink, seed=262)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FBDDE4", "#F3B3C3")
    t.ellipse(1.5, 1.5, d - 1.5, d - 1.5, outline=rose, width=1.0)
    t.photo("berries", d * 0.25, d * 0.12, d * 0.75, d * 0.50, shape="ellipse", feather=1.5, crop=(0.25, 0.2, 0.75, 0.8))
    t.text(d / 2, d * 0.60, "ストロベリー", 7.5, rose, 900)
    t.text(d / 2, d * 0.71, "アイスクリーム", 4.4, rose, 800)
    t.text(d / 2, d * 0.82, "要冷凍 −18℃以下", 3.2, INK, 700)
    top = finish(t.array(), "paper", 262, 0.8)
    return Product(slug="ice_cream_cup", name="カップアイス ストロベリー 120ml", category="food", mass_kg=0.13,
                   material="paper",
                   description="形は一般的なカップ入りアイス（高さ 52 mm・上端径約 91 mm）で、寸法・質量は代表値。",
                   tags=["アイス", "アイスクリーム", "ストロベリー", "冷凍食品", "ice cream", "strawberry"],
                   photos=["berries"], colors=Colors(cap=pink, label_base=pink), **revolve(form, label=label, top=top))


def butter_cookie_box() -> Product:
    W, D, H = 115.0, 45.0, 155.0
    red, cream, gold = "#8E1B1B", "#FBF3E2", "#D9A441"
    s = 10

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, red, seed)
        f.gradient(0, 0, w, h, "#A52525", "#6E1212")
        return f

    fr = face(W, H, 271)
    fr.pattern(0, 0, W, H, "dots", mix("#A52525", gold, 0.3), 6, 0.5)
    fr.rect(6, 8, W - 6, 46, fill=cream, radius=4)
    fr.text(W / 2, 22, "バター", 11, red, 900)
    fr.text(W / 2, 37, "クッキー", 11, red, 900)
    fr.text(W / 2, 53, "BUTTER COOKIES", 4.6, gold, 700, spacing=1.0)
    fr.photo("butter_cookies", 6, 59, W - 6, 133, shape="round", radius=5, shadow=1.5, crop=(0.1, 0.0, 0.9, 1.0))
    fr.rect(W / 2 - 26, 138, W / 2 + 26, 149, fill=gold, radius=5.5)
    fr.text(W / 2, 143.5, "発酵バター使用  12枚入", 4.0, red, 900, max_w=48)
    front = fr.array()

    bk = face(W, H, 272)
    bk.rect(5, 5, W - 5, H - 5, fill=cream, radius=2)
    back_info(bk, 9, 9, W - 9, [("名称", "クッキー"), ("原材料名", "小麦粉、バター、砂糖、鶏卵、アーモンドパウダー、食塩／膨脹剤、香料"),
                                ("内容量", "12枚（個包装）"), ("賞味期限", "底面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")],
              3.2, [("栄養成分表示 1枚当たり", ""), ("エネルギー", "52kcal"), ("たんぱく質", "0.6g"), ("脂質", "2.9g"),
                    ("炭水化物", "6.0g"), ("食塩相当量", "0.03g")], red, cream)
    bk.barcode(W / 2 - 18, H - 34, 36, 20)
    bk.recycle(18, H - 22, 10, "紙", red, sub="箱")
    bk.recycle(W - 18, H - 22, 10, "プラ", red, sub="袋")
    back = bk.array()

    sides = []
    for k, seed in enumerate((273, 274)):
        sd = face(D, H, seed)
        sd.vtext(D / 2, 18, "バタークッキー", 9, cream, 900, gap=0.05)
        sd.rect(5, 115, D - 5, 148, fill=gold, radius=2)
        sd.vtext(D / 2, 121, "12枚" if k == 0 else "焼菓子", 6, red, 900)
        sides.append(sd.array())
    tp = face(W, D, 275)
    tp.rect(3, 3, W - 3, D - 3, outline=gold, width=0.6, radius=2)
    tp.text(W / 2, D / 2 - 5, "バタークッキー", 7.0, cream, 900)
    tp.text(W / 2, D / 2 + 8, "← ここを押してあけてください", 3.4, gold, 700)
    bt = face(W, D, 276)
    bt.text(W / 2, D / 2 - 4, "賞味期限 2027.03.31", 4.0, cream, 600)
    bt.text(W / 2, D / 2 + 5, NOTICE, 2.8, cream, 400, max_w=W - 10)
    imgs = [front, back, *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 280 + i) for i, a in enumerate(imgs)]
    return Product(slug="butter_cookie_box", name="バタークッキー 12枚入", shape_class="box", category="food",
                   dims=Dimensions(0.155, 0.115, depth=0.045), mass_kg=0.17, material="paper",
                   description="形は一般的な箱入りクッキー（高さ 155 mm・幅 115 mm・奥行き 45 mm）で、寸法・質量は代表値。",
                   tags=["お菓子", "クッキー", "箱菓子", "焼き菓子", "cookies", "butter cookies"], photos=["butter_cookies"],
                   colors=Colors(label_base=red), images=imgs,
                   faces={"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5})


def bottle_gum() -> Product:
    form = forms.jar(0.085, 0.066, cap_h=0.022, cap_d=0.068, label=(0.006, 0.056))
    mint_c, green, white = "#BFEBDD", "#0F7B5F", "#FFFFFF"
    c = label_canvas(form, mint_c, seed=291)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#DDF6EE", "#9EDDC9")
    c.pattern(0, 0, W, H, "stripes", mix("#9EDDC9", white, 0.4), 7, 1.2)
    c.photo("mint", fx - 30, 22, fx - 6, 46, shape="ellipse", feather=0.8, shadow=0.8)
    c.rect(fx - 30, 4, fx + 30, 19, fill=green, radius=3)
    c.text(fx, 11.5, "ミントガム", 8.5, white, 900)
    c.text(fx + 15, 28, "粒ガム", 6.0, green, 900)
    c.text(fx + 15, 36, "シュガーレス", 3.6, green, 800)
    c.text(fx + 15, 43, "140g", 4.4, INK, 900)
    c.text(0.5 * W, 6, "MINT GUM", 3.4, green, 800, spacing=0.6)
    c.rect(0.25 * W - 26, 3, 0.25 * W + 26, H - 3, fill=white, radius=2)
    back_info(c, 0.25 * W - 25, 4, 0.25 * W + 25, [
        ("名称", "ガム"), ("原材料名", "マルチトール、ガムベース、還元水あめ／甘味料、香料、光沢剤"),
        ("内容量", "140g"), ("賞味期限", "底面に記載")], 1.7)
    c.barcode(0.5 * W - 11, 14, 22, 13)
    c.recycle(0.5 * W - 6, 39, 6, "プラ", green, sub="容器")
    c.recycle(0.5 * W + 6, 39, 6, "紙", green, sub="包み紙")
    label = finish(c.array(), "film", 291, 0.7)

    t = top_canvas(form, white, seed=292)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FFFFFF", "#E3E8E6")
    t.ellipse(2, 2, d - 2, d - 2, outline=green, width=1.2)
    t.text(d / 2, d * 0.40, "ミントガム", 8.5, green, 900)
    t.text(d / 2, d * 0.55, "MINT GUM", 4.4, green, 700, spacing=0.8)
    t.text(d / 2, d * 0.72, "噛んだあとは紙に包んで捨ててください", 2.4, INK, 600, max_w=d * 0.7)
    top = finish(t.array(), "film", 292, 0.6)
    return Product(slug="bottle_gum", name="ボトルガム ミント 140g", category="food", mass_kg=0.17, material="plastic",
                   description="形は一般的なボトル入りの粒ガム（高さ 85 mm・胴径 66 mm、ねじ蓋）で、寸法・質量は代表値。",
                   tags=["ガム", "ボトルガム", "ミント", "お菓子", "chewing gum", "mint"], photos=["mint"],
                   colors=Colors(cap="#F4F6F5", label_base=mint_c), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 追加分（日用品）


def box_tissue() -> Product:
    W, D, H = 240.0, 115.0, 65.0
    sky, blue, white = "#DCEBF7", "#2F6EA8", "#FFFFFF"
    s = 6

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#F4F9FD", sky)
        f.pattern(0, 0, w, h, "waves", mix(sky, blue, 0.18), 9, 0.5)
        f.rect(0, 0, w, 3, fill=blue)
        f.rect(0, h - 3, w, h, fill=blue)
        return f

    fr = face(W, H, 301)
    fr.text(W / 2, 22, "ボックスティッシュ", 11, blue, 900)
    fr.text(W / 2, 38, "やわらか 2枚重ね", 6.0, mix(blue, white, 0.2), 700)
    fr.rect(W / 2 - 40, 46, W / 2 + 40, 57, fill=blue, radius=5.5)
    fr.text(W / 2, 51.5, "200組（400枚）", 5.4, white, 800)
    bk = face(W, H, 302)
    bk.text(W / 2, 16, "BOX TISSUE", 8, blue, 800, spacing=2.0)
    bk.paragraph(20, 28, W - 70, "品名：ティシュペーパー  材質：パルプ 100%  枚数：200組（400枚）\n"
                 "寸法：197 × 207 mm  水に溶けないので、トイレに流さないでください。\n" + NOTICE, 3.2, INK, 500)
    bk.barcode(W - 62, 26, 46, 26)
    sides = []
    for k, seed in enumerate((303, 304)):
        sd = face(D, H, seed)
        sd.text(D / 2, 24, "ティッシュ", 9, blue, 900)
        sd.text(D / 2, 40, "200組" if k == 0 else "パルプ 100%", 6, mix(blue, white, 0.2), 800)
        if k == 1:
            sd.recycle(D / 2, 54, 8, "紙", blue)
        sides.append(sd)
    tp = face(W, D, 305)
    tp.ellipse(W / 2 - 75, D / 2 - 17, W / 2 + 75, D / 2 + 17, fill="#EEF3F6", outline=mix(blue, white, 0.4), width=0.8)
    # 取り出し口は開けた状態（切れ目から 1 組が出ている。シートは部品）
    tp.line([(W / 2 - 62, D / 2), (W / 2 + 62, D / 2)], "#8FA3B0", 1.6)
    tp.text(W / 2, D / 2 - 26, "やわらか 2枚重ね", 4.4, blue, 700)
    tp.text(W / 2, D / 2 + 30, "BOX TISSUE  200組", 5.0, blue, 800, spacing=0.8)
    bt = face(W, D, 306)
    bt.text(W / 2, D / 2 - 6, "ボックスティッシュ  200組", 7, blue, 800)
    bt.text(W / 2, D / 2 + 8, NOTICE, 4.0, INK, 500)
    imgs = [_face(c.array(), "paper", 310 + i) for i, c in enumerate((fr, bk, *sides, tp, bt))]
    top_z = H / 1000
    sheets = [_box("Tissue", (0.11, 0.0012, 0.040), (0, 0.002, top_z + 0.016), "#FBFBF8", "matte",
                   rotation=[8, 0, 0], collision=False),
              _box("Tissue2", (0.085, 0.0012, 0.030), (0.006, -0.003, top_z + 0.011), "#F5F6F2", "matte",
                   rotation=[-14, 0, 4], collision=False)]
    return Product(slug="box_tissue", name="ボックスティッシュ 200組", shape_class="box", category="household",
                   dims=Dimensions(0.065, 0.24, depth=0.115), mass_kg=0.32, material="paper",
                   description="形は一般的な箱入りティッシュ（幅 240 mm・奥行き 115 mm・高さ 65 mm）で、寸法・質量は代表値。"
                               "取り出し口から出た 1 組のシートは部品で表す（コリジョンなし）。", parts=sheets,
                   tags=["ティッシュ", "ボックスティッシュ", "日用品", "tissue", "box tissue"], photos=[],
                   colors=Colors(label_base=sky), images=imgs,
                   faces={"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5})


def hand_soap_pump() -> Product:
    form, pump = _pump_bottle(0.068, 0.145, (0.012, 0.110), "#2E7D4F")
    white, yellow, green = "#FFFFFF", "#F2C230", "#3E8E41"
    c = label_canvas(form, white, seed=321)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#FFF6D6")
    c.photo("lemon", fx - 26, 44, fx + 26, 86, shape="ellipse", feather=2, shadow=1.0, crop=(0.1, 0.05, 0.9, 0.95))
    c.rect(fx - 30, 6, fx + 30, 8, fill=green)
    c.text(fx, 15, "薬用", 5.0, green, 900)
    c.text(fx, 26, "ハンドソープ", 8.0, INK, 900, max_w=58)
    c.text(fx, 35, "殺菌・消毒  手肌にやさしい", 3.4, green, 700)
    c.rect(fx - 18, 88, fx + 18, 95, fill=yellow, radius=3.5)
    c.text(fx, 91.5, "シトラスの香り", 3.6, INK, 800)
    c.text(fx + 24, 13, "医薬部外品", 2.6, INK, 700, anchor="rm")
    c.text(0.5 * W, 8, "HAND SOAP", 3.2, green, 800, spacing=0.6)
    c.text(0.5 * W, H - 5, "250ml", 4.0, INK, 900)
    caution = ("【使用方法】適量を手に取り、よく泡立ててから洗い流してください。\n"
               "【使用上の注意】傷・はれもの・湿疹など異常のある部位には使わないでください。目に入ったときはすぐに洗い流してください。\n"
               "【成分】イソプロピルメチルフェノール、ラウレス硫酸Na、グリセリン、香料\n" + NOTICE)
    c.paragraph(0.25 * W - 24, 8, 0.25 * W + 24, caution, 2.2, INK, 400)
    c.barcode(0.5 * W - 12, 20, 24, 15)
    c.recycle(0.5 * W - 7, 52, 7, "プラ", INK, sub="容器")
    c.recycle(0.5 * W + 7, 52, 7, "プラ", INK, sub="ポンプ")
    label = finish(c.array(), "film", 321, 0.6)
    return Product(slug="hand_soap_pump", name="薬用ハンドソープ シトラスの香り 250ml", category="household",
                   mass_kg=0.29, capacity_ml=250, material="plastic",
                   description="形は一般的なポンプ式のハンドソープ（ポンプ込みの高さ 201 mm・胴径 68 mm）で、寸法・質量は代表値。"
                               "ポンプの軸・押し頭・ノズルは部品で表す。", parts=pump,
                   tags=["ハンドソープ", "石けん", "ポンプ", "シトラス", "hand soap", "pump bottle"], photos=["lemon"],
                   colors=Colors(cap="#2E7D4F", label_base=white), **revolve(form, label=label))


# ---------------------------------------------------------------- 追加分（什器）


# ゴンドラの天板の案内表示（売り場）が合う場所（Picture バリアント。ほかの店では Blank＝無地の天板にする）
GONDOLA_PLACES: dict[str, list[str]] = {
    "gondola_shelf": ["convenience_store", "supermarket", "drugstore", "hundred_yen_shop"],
    "gondola_shelf_food": ["convenience_store", "supermarket", "drugstore"],
    "gondola_shelf_daily": ["convenience_store", "supermarket", "drugstore", "hundred_yen_shop", "home_center"],
    "gondola_shelf_bakery": ["bakery", "convenience_store", "supermarket"],
}

# ゴンドラの天板の案内表示（売り場）。slug → (表示、英語の表示、表示の乱数の種、名前の後ろ、タグ)
GONDOLA_HEADERS: dict[str, tuple[str, str, int, str, list[str]]] = {
    "gondola_shelf": ("お菓子・スナック", "SNACKS & SWEETS", 350, "", []),
    "gondola_shelf_food": ("カップ麺・食品", "INSTANT FOODS", 351, "（カップ麺・食品）",
                           ["カップ麺・食品", "食品売り場", "instant food shelf", "food aisle"]),
    "gondola_shelf_daily": ("日用品", "DAILY GOODS", 352, "（日用品）",
                            ["日用品", "日用品売り場", "daily goods shelf", "household goods"]),
    "gondola_shelf_bakery": ("パン・お菓子", "BAKERY & SWEETS", 353, "（パン・お菓子）",
                             ["パン・お菓子", "パン売り場", "bakery shelf", "bread aisle"]),
}


def gondola_shelf() -> Product:
    return _gondola("gondola_shelf")


def gondola_shelf_food() -> Product:
    return _gondola("gondola_shelf_food")


def gondola_shelf_daily() -> Product:
    return _gondola("gondola_shelf_daily")


def gondola_shelf_bakery() -> Product:
    return _gondola("gondola_shelf_bakery")


def _gondola(slug: str) -> Product:
    """片面ゴンドラ。形は共通で、天板の案内表示（売り場）だけが違う。"""
    title, sub, seed, suffix, extra_tags = GONDOLA_HEADERS[slug]
    pb = Canvas(900, 1400, 1.5, "#E6E8EB", 331)  # 背板（有孔ボード）
    pb.gradient(0, 0, 900, 1400, "#ECEEF0", "#DADDE1")
    yy = 25.0
    while yy < 1400:
        xx = 25.0
        while xx < 900:
            pb.ellipse(xx - 2.5, yy - 2.5, xx + 2.5, yy + 2.5, fill="#9AA0A6")
            xx += 25
        yy += 25
    pb.rect(0, 0, 12, 1400, fill="#9EA3A9")  # 左右の縁（支柱に掛かる部分）
    pb.rect(888, 0, 900, 1400, fill="#9EA3A9")
    backboard = _face(pb.array(), "metal", 331, 0.3, 12)

    prices = (("108円", "128円", "98円", "158円", "138円", "118円"), ("198円", "248円", "178円", "218円", "198円", "168円"),
              ("88円", "98円", "128円", "88円", "108円", "98円"), ("298円", "258円", "328円", "278円", "298円", "348円"))
    strips = []
    for k, row in enumerate(prices):
        st = Canvas(870, 35, 4, "#FFFFFF", 340 + k)
        st.gradient(0, 0, 870, 35, "#FFFFFF", "#EEF0F2")
        st.rect(0, 32, 870, 35, fill="#AEB3B8")  # レールの下縁
        for i, p in enumerate(row):
            x0 = 20 + i * 142
            st.rect(x0, 4, x0 + 64, 31, fill="#FFE45C", outline="#D4B52E", width=0.6, radius=2)
            st.text(x0 + 32, 13, "本体価格", 4.6, INK, 600)
            st.text(x0 + 32, 24, p, 9, "#C0392B", 900, max_w=58)
        strips.append(_face(st.array(), "film", 340 + k, 0.4, 3))

    hd = Canvas(900, 150, 2.5, "#1F6F5C", seed)
    hd.gradient(0, 0, 900, 150, "#24826B", "#185747")
    hd.rect(0, 120, 900, 128, fill="#F2C230")
    hd.text(450, 58, title, 62, "#FFFFFF", 900)
    hd.text(450, 105, sub, 24, "#F2C230", 800, spacing=4)
    header = _face(hd.array(), "film", seed, 0.4, 6)

    gray, steel = "#5A5F66", "#C4C8CC"
    parts = [_box("BasePlinth", (0.9, 0.42, 0.1), (0, -0.015, 0.05), gray, "matte"),
             _box("BaseShelf", (0.9, 0.42, 0.015), (0, -0.015, 0.1075), steel, "metal"),
             _box("BackPanel", (0.9, 0.03, 1.4), (0, 0.21, 0.8), "#E6E8EB", "plastic", {"front": 0}),
             _box("UprightLeft", (0.03, 0.05, 1.5), (-0.435, 0.2, 0.75), gray, "metal"),
             _box("UprightRight", (0.03, 0.05, 1.5), (0.435, 0.2, 0.75), gray, "metal"),
             _box("Header", (0.9, 0.025, 0.15), (0, 0.2075, 1.575), "#1F6F5C", "plastic", {"front": 5}, blank="#1F6F5C"),
             _box("BaseRail", (0.87, 0.012, 0.035), (0, -0.231, 0.1), "#FFFFFF", "plastic", {"front": 1})]
    for k, z in enumerate((0.45, 0.8, 1.15)):
        parts += [_box(f"Shelf{k + 1}", (0.87, 0.36, 0.015), (0, 0.015, z), steel, "metal"),
                  _box(f"PriceRail{k + 1}", (0.87, 0.012, 0.035), (0, -0.171, z - 0.008), "#FFFFFF", "plastic",
                       {"front": 2 + k})]
    return Product(slug=slug, name="陳列棚 ゴンドラ 片面 900mm" + suffix, shape_class="assembly", category="fixture",
                   dims=Dimensions(1.65, 0.9, depth=0.462), mass_kg=60.0, static=True, material="steel",
                   description="形は店舗の片面ゴンドラ什器の一般的な構成（幅 900 mm・高さ 1650 mm、有孔の背板・棚板 3 段・値札レール・天板の案内表示）で、寸法・質量は代表値。",
                   tags=["陳列棚", "ゴンドラ", "商品棚", "店舗什器", "gondola", "store shelf", "shelf", *extra_tags], photos=[],
                   colors=Colors(label_base="#E6E8EB"), images=[backboard, *strips, header], parts=parts,
                   picture_places=GONDOLA_PLACES[slug])


_BASKET_RED = "#C62828"


def _basket_wall(w: float, h: float, seed: int, tag: bool) -> np.ndarray:
    """買い物かごの側面（穴の並び）。"""
    red, dark = _BASKET_RED, "#7A1010"
    c = Canvas(w, h, 4, red, seed)
    c.gradient(0, 0, w, h, "#D33434", "#B21F1F")
    c.rect(0, 0, w, 14, fill="#A91D1D")
    c.rect(0, h - 10, w, h, fill="#A91D1D")
    y = 22.0
    while y < h - 22:
        x = 14.0
        while x < w - 12:
            c.rect(x, y, x + 7, y + 10, fill=dark, radius=2)
            x += 12
        y += 15
    if tag:
        c.rect(w / 2 - 34, 2, w / 2 + 34, 12, fill="#FFFFFF", radius=2)
        c.text(w / 2, 7, "店内専用  SHOPPING BASKET", 4.4, red, 800, max_w=64)
    return _face(c.array(), "film", seed, 0.4, 4)


def _basket_images() -> list[np.ndarray]:
    return [_basket_wall(460, 220, 361, True), _basket_wall(318, 220, 362, False)]


def _basket_parts(prefix: str = "", dy: float = 0.0, dz: float = 0.0, long_img: int = 0, short_img: int = 1) -> list[Part]:
    """買い物かごの部品（底の中心が (0, dy, dz)）。ずらさないときは元の値のまま（出力のハッシュを変えない）。"""
    red = _BASKET_RED
    spec = [("Feet", (0.42, 0.29, 0.01), (0, 0, 0.005), "#9E1C1C", None),
            ("Floor", (0.44, 0.31, 0.008), (0, 0, 0.014), red, None),
            ("WallFront", (0.46, 0.006, 0.22), (0, -0.162, 0.12), red, {"front": long_img, "back": long_img}),
            ("WallBack", (0.46, 0.006, 0.22), (0, 0.162, 0.12), red, {"front": long_img, "back": long_img}),
            ("WallLeft", (0.006, 0.318, 0.22), (-0.227, 0, 0.12), red, {"left": short_img, "right": short_img}),
            ("WallRight", (0.006, 0.318, 0.22), (0.227, 0, 0.12), red, {"left": short_img, "right": short_img}),
            ("RimFront", (0.474, 0.014, 0.012), (0, -0.165, 0.234), "#B71C1C", None),
            ("RimBack", (0.474, 0.014, 0.012), (0, 0.165, 0.234), "#B71C1C", None),
            ("RimLeft", (0.014, 0.33, 0.012), (-0.23, 0, 0.234), "#B71C1C", None),
            ("RimRight", (0.014, 0.33, 0.012), (0.23, 0, 0.234), "#B71C1C", None),
            ("HandleFront", (0.3, 0.008, 0.02), (0, -0.176, 0.2), "#3A3A3A", None),
            ("HandleBack", (0.3, 0.008, 0.02), (0, 0.176, 0.2), "#3A3A3A", None)]
    return [_box(prefix + n, size, (x, y + dy if dy else y, z + dz if dz else z), col, "plastic", faces) for n, size, (x, y, z), col, faces in spec]


def shopping_basket() -> Product:
    red = _BASKET_RED
    imgs = _basket_images()
    parts = _basket_parts()
    return Product(slug="shopping_basket", name="買い物かご", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.24, 0.474, depth=0.36), mass_kg=0.75, material="plastic",
                   description="形は店舗の一般的なプラスチック製の買い物かご（幅 474 mm・奥行き 330 mm・高さ 240 mm、取っ手を倒した状態）で、寸法・質量は代表値。側面の穴は絵で、形は板。",
                   tags=["買い物かご", "かご", "バスケット", "店舗備品", "shopping basket", "basket"], photos=[],
                   colors=Colors(label_base=red), images=imgs, parts=parts)


# ---------------------------------------------------------------- 追加分（什器 2）


def _price_strip(prices: list[str], w: float, seed: int, step: float) -> np.ndarray:
    """棚の値札レール（黄色の値札を等間隔に並べる）。"""
    st = Canvas(w, 35, 4, "#FFFFFF", seed)
    st.gradient(0, 0, w, 35, "#FFFFFF", "#EEF0F2")
    st.rect(0, 32, w, 35, fill="#AEB3B8")
    for i, p in enumerate(prices):
        x0 = 20 + i * step
        st.rect(x0, 4, x0 + 64, 31, fill="#FFE45C", outline="#D4B52E", width=0.6, radius=2)
        st.text(x0 + 32, 13, "本体価格", 4.6, INK, 600)
        st.text(x0 + 32, 24, p, 9, "#C0392B", 900, max_w=58)
    return _face(st.array(), "film", seed, 0.4, 3)


def open_showcase_multideck() -> Product:
    hd = Canvas(1120, 220, 2.0, "#1C5FA8", 371)  # 上部の案内表示
    hd.gradient(0, 0, 1120, 220, "#2A74C4", "#174C8A")
    hd.rect(0, 180, 1120, 190, fill="#9FD3F5")
    hd.text(560, 82, "チルド・デザート", 78, "#FFFFFF", 900)
    hd.text(560, 148, "CHILLED & DESSERTS  10℃以下で保存", 28, "#BFE0FF", 700, spacing=3)
    header = _face(hd.array(), "film", 371, 0.4, 6)

    gr = Canvas(1200, 120, 2.0, "#2F3236", 372)  # 台輪の吸気口
    gr.gradient(0, 0, 1200, 120, "#3A3E43", "#25282C")
    gr.rect(0, 0, 1200, 10, fill="#4A4F55")
    x = 60.0
    while x < 1140:
        gr.rect(x, 30, x + 8, 95, fill="#121315", radius=3)
        x += 16
    grille = _face(gr.array(), "metal", 372, 0.3, 4)

    rows = (["128円", "158円", "98円", "138円", "148円", "118円", "168円"],
            ["198円", "228円", "178円", "248円", "198円", "218円", "188円"],
            ["108円", "128円", "148円", "108円", "98円", "138円", "128円"],
            ["298円", "348円", "258円", "328円", "298円", "278円", "318円"],
            ["158円", "138円", "178円", "158円", "148円", "168円", "138円"])
    strips = [_price_strip(r, 1120, 373 + k, 155) for k, r in enumerate(rows)]

    white, liner, steel = "#F4F5F7", "#E3E7EB", "#C4C8CC"
    parts = [_box("Plinth", (1.2, 0.76, 0.12), (0, 0, 0.06), "#2F3236", "matte", {"front": 1}),
             _box("SideLeft", (0.04, 0.8, 1.78), (-0.58, 0, 1.01), white),
             _box("SideRight", (0.04, 0.8, 1.78), (0.58, 0, 1.01), white),
             _box("FrontPanel", (1.12, 0.05, 0.3), (0, -0.375, 0.27), white),
             _box("Bumper", (1.2, 0.03, 0.04), (0, -0.405, 0.3), "#9AA0A6", "metal"),
             _box("BaseDeck", (1.12, 0.7, 0.02), (0, 0, 0.43), liner, "matte"),
             _box("DeckGrille", (1.12, 0.08, 0.008), (0, -0.31, 0.444), "#2B2E31", "matte", collision=False),
             _box("BaseRail", (1.12, 0.012, 0.035), (0, -0.406, 0.4), "#FFFFFF", "plastic", {"front": 2}),
             _box("BackWall", (1.12, 0.05, 1.26), (0, 0.375, 1.05), liner, "matte"),
             _box("Canopy", (1.12, 0.62, 0.22), (0, 0.09, 1.79), white, "plastic", {"front": 0}),
             ]
    # 照明：上部の覆いの下と、各棚の前寄りの下に LED（下の段を照らす）
    lamp, lux = _lamp("CanopyLight", (1.12, 0.05, 0.01), (0, -0.15, 1.675), "#FBFBF6", 15000.0, COOL_WHITE)
    parts.append(lamp)
    lights = [lux]
    for k, (z, d) in enumerate(((0.72, 0.48), (0.98, 0.44), (1.22, 0.40), (1.44, 0.36))):
        yf = 0.35 - d
        parts += [_box(f"Shelf{k + 1}", (1.12, d, 0.015), (0, 0.35 - d / 2, z), steel, "metal"),
                  _box(f"PriceRail{k + 1}", (1.12, 0.012, 0.035), (0, yf - 0.006, z - 0.008), "#FFFFFF", "plastic",
                       {"front": 3 + k})]
        lamp, lux = _lamp(f"ShelfLight{k + 1}", (1.08, 0.02, 0.008), (0, yf + 0.03, z - 0.0115), "#FBFBF6",
                          8000.0, COOL_WHITE, tilt=LAMP_TILT)
        parts.append(lamp)
        lights.append(lux)
    return Product(slug="open_showcase_multideck", name="多段オープン冷蔵ショーケース 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(1.9, 1.2, depth=0.82), mass_kg=250.0, static=True,
                   material="steel",
                   description="形は店舗の扉のない多段オープン冷蔵ショーケースの一般的な構成（台輪・棚板 4 段と底の陳列面・値札レール・上部の照明と案内表示）で、寸法・質量は代表値。冷気の吹き出し口は絵と薄い板で表す。",
                   tags=["冷蔵ショーケース", "オープンショーケース", "多段", "店舗什器", "refrigerated showcase",
                         "multideck", "open chiller"], photos=[],
                   colors=Colors(label_base=white), images=[header, grille, *strips], parts=parts, lights=lights)


def checkout_counter() -> Product:
    fr = Canvas(1500, 820, 1.2, "#E8DCC6", 381)  # お客さま側の前板
    fr.gradient(0, 0, 1500, 820, "#EFE5D3", "#D9C7A8")
    for k in range(14):  # 木目風の縦縞
        x = 50 + k * 105 + fr.rng.uniform(-10, 10)
        fr.line([(x, 0), (x + fr.rng.uniform(-6, 6), 680)], mix("#D9C7A8", "#8B6A3E", 0.18), 1.2)
    fr.rect(0, 680, 1500, 820, fill="#1F6F5C")
    fr.rect(0, 672, 1500, 680, fill="#F2C230")
    fr.text(750, 160, "いらっしゃいませ", 92, "#1F6F5C", 900)
    fr.text(750, 250, "WELCOME", 40, "#8B6A3E", 800, spacing=10)
    fr.rect(420, 330, 1080, 600, fill="#FFFFFF", radius=18)
    fr.text(750, 380, "各種キャッシュレス決済", 40, INK, 900)
    fr.text(750, 430, "ご利用いただけます", 34, INK, 700)
    for i, (t, col) in enumerate((("クレジット", "#2F6DB5"), ("電子マネー", "#C0392B"), ("コード決済", "#2E8B57"))):
        cx = 530 + i * 220
        fr.rect(cx - 90, 470, cx + 90, 570, fill=col, radius=12)
        if i == 0:
            fr.rect(cx - 50, 490, cx + 50, 550, outline="#FFFFFF", width=3, radius=6)
            fr.rect(cx - 50, 505, cx + 50, 517, fill="#FFFFFF")
        elif i == 1:
            fr.ellipse(cx - 28, 492, cx + 28, 548, outline="#FFFFFF", width=4)
            fr.ellipse(cx - 14, 506, cx + 14, 534, outline="#FFFFFF", width=4)
        else:
            for gx in range(3):
                for gy in range(3):
                    if (gx + gy) % 2 == 0:
                        fr.rect(cx - 30 + gx * 20, 490 + gy * 20, cx - 14 + gx * 20, 506 + gy * 20, fill="#FFFFFF")
        fr.text(cx, 590, t, 22, INK, 800)
    fr.text(750, 750, "レジ袋は有料です  マイバッグをご利用ください", 34, "#FFFFFF", 800)
    front = _face(fr.array(), "paper", 381, 0.5, 10)

    pos = Canvas(320, 240, 1600 / 320, "#FFFFFF", 382)  # 店員側の画面
    pos.gradient(0, 0, 320, 240, "#FFFFFF", "#E9EEF3")
    pos.rect(0, 0, 320, 24, fill="#1F6F5C")
    pos.text(10, 12, "登録", 12, "#FFFFFF", 900, anchor="lm")
    pos.text(310, 12, "担当 0012", 9, "#FFFFFF", 600, anchor="rm")
    y = 32.0
    for name, price in (("おにぎり 鮭", "150"), ("カフェラテ M", "180"), ("牛乳 1000ml", "238"), ("バタークッキー", "398")):
        pos.text(12, y + 8, name, 10, INK, 600, anchor="lm")
        pos.text(200, y + 8, f"{price}円", 10, INK, 700, anchor="rm")
        pos.line([(8, y + 17), (206, y + 17)], "#CCD3DA", 0.6)
        y += 21
    pos.rect(214, 32, 312, 120, fill="#F4F7FA", outline="#CCD3DA", width=0.6, radius=5)
    pos.text(263, 52, "合計 4点", 9, INK, 700)
    pos.text(263, 84, "966円", 20, "#C0392B", 900)
    pos.text(263, 108, "（税込）", 8, INK, 500)
    for i, (t, col) in enumerate((("現金", "#2F6DB5"), ("クレジット", "#5B7FA6"), ("電子マネー", "#C0392B"),
                                  ("コード決済", "#2E8B57"), ("取消", "#7F8C8D"), ("小計", "#F2994A"))):
        x0 = 10 + (i % 3) * 102
        y0 = 132 + (i // 3) * 52
        pos.rect(x0, y0, x0 + 96, y0 + 44, fill=col, radius=6)
        pos.text(x0 + 48, y0 + 22, t, 11, "#FFFFFF", 800)
    pos_screen = trim_safe(finish(pos.array(), "screen", 382, 0.5))

    cd = Canvas(200, 130, 1200 / 200, "#0B0F14", 383)  # お客さま向けの表示
    cd.gradient(0, 0, 200, 130, "#16202B", "#06090D")
    cd.rect(0, 0, 200, 18, fill="#1F6F5C")
    cd.text(100, 9, "お買い上げありがとうございます", 8, "#FFFFFF", 700)
    cd.text(16, 48, "合計", 13, "#CCCCCC", 700, anchor="lm")
    cd.text(186, 48, "966円", 26, "#7CFC9A", 900, anchor="rm")
    cd.text(16, 86, "お預かり", 10, "#AAAAAA", 600, anchor="lm")
    cd.text(186, 86, "1,000円", 14, "#FFFFFF", 800, anchor="rm")
    cd.text(16, 112, "おつり", 10, "#AAAAAA", 600, anchor="lm")
    cd.text(186, 112, "34円", 14, "#FFFFFF", 800, anchor="rm")
    cust_screen = trim_safe(finish(cd.array(), "screen", 383, 0.5))

    pt = Canvas(90, 170, 8, "#1E1E1E", 384)  # 決済端末（上から見た面）
    pt.gradient(0, 0, 90, 170, "#2A2A2A", "#151515")
    pt.rect(8, 10, 82, 62, fill="#20303F", radius=3)
    pt.text(45, 28, "カードを", 7, "#FFFFFF", 700)
    pt.text(45, 42, "タッチしてください", 6, "#FFFFFF", 700)
    for i in range(12):
        x0 = 12 + (i % 3) * 23
        y0 = 72 + (i // 3) * 21
        pt.rect(x0, y0, x0 + 19, y0 + 16, fill="#3E3E3E" if i < 9 else ("#C0392B", "#3E3E3E", "#2E8B57")[i - 9], radius=3)
        pt.text(x0 + 9.5, y0 + 8, "123456789X0○"[i], 7, "#FFFFFF", 700)
    pt.rect(0, 160, 90, 170, fill="#444444")
    terminal = _face(pt.array(), "film", 384, 0.4, 3)

    wood, top_c = "#E8DCC6", "#EEE8DE"
    parts = [_box("Plinth", (1.46, 0.54, 0.08), (0, 0.04, 0.04), "#2B2B2B", "matte"),
             _box("Body", (1.5, 0.6, 0.82), (0, 0.02, 0.49), wood, "plastic", {"front": 0}),
             _box("Top", (1.54, 0.66, 0.03), (0, 0.02, 0.915), top_c, "glossy"),
             _box("PosBase", (0.38, 0.36, 0.11), (-0.4, 0.12, 0.985), "#2A2C30"),
             _cyl("PosPole", (0.05, 0.05, 0.12), (-0.4, 0.2, 1.1), "#2A2C30", "plastic"),
             _box("PosScreen", (0.32, 0.04, 0.24), (-0.4, 0.21, 1.27), "#1A1B1D", "screen", {"back": 1}, [15, 0, 0]),
             _cyl("CustomerPole", (0.03, 0.03, 0.18), (-0.4, -0.02, 1.13), "#2A2C30", "plastic"),
             _box("CustomerDisplay", (0.2, 0.03, 0.13), (-0.4, -0.04, 1.28), "#1A1B1D", "screen", {"front": 2},
                  [-10, 0, 0]),
             _box("ReceiptPrinter", (0.16, 0.2, 0.13), (-0.08, 0.15, 0.995), "#3A3C40"),
             _box("HandScanner", (0.07, 0.11, 0.17), (0.12, 0.2, 1.015), "#2A2C2F", rotation=[-10, 0, 0]),
             _box("PaymentTerminal", (0.09, 0.17, 0.045), (0.05, -0.17, 0.9525), "#1E1E1E", "plastic", {"top": 3}),
             _box("CashTray", (0.2, 0.14, 0.012), (-0.4, -0.2, 0.936), "#3C3C3C", "matte")]
    return Product(slug="checkout_counter", name="レジカウンター 1500mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(1.39, 1.54, depth=0.66), mass_kg=120.0, static=True, material="wood",
                   description="形は店舗の有人レジカウンターの一般的な構成（カウンター・POS レジと店員側の画面・お客さま向けの表示・レシートプリンター・ハンドスキャナー・決済端末・カルトン）で、寸法・質量は代表値。画面は架空の会計画面。お客さま側が正面（-Y）。",
                   tags=["レジカウンター", "レジ", "POS", "カウンター", "店舗什器", "checkout counter", "cash register"],
                   photos=[], colors=Colors(label_base=wood), images=[front, pos_screen, cust_screen, terminal],
                   parts=parts)


def magazine_rack() -> Product:
    covers_spec = [("lake", "鉄道と旅", "TRAVEL", "春の絶景ルート 30", "#1F4E79"),
                   ("berries", "まちのグルメ", "GOURMET", "旬のフルーツ特集", "#B03A2E"),
                   ("lavender", "はじめての家庭菜園", "GARDEN", "ハーブを育てよう", "#6C4F9C"),
                   ("coffee_cup", "月刊 喫茶時間", "CAFE", "おうちで淹れるコーヒー", "#5D3A1A"),
                   ("tea_field", "週刊 にっぽん散歩", "WALK", "茶畑の里をたずねて", "#2E7D32"),
                   ("onigiri", "おべんとう帖", "BENTO", "毎日のおにぎり 50", "#D35400")]
    covers = []
    for k, (pid, title, en, sub, col) in enumerate(covers_spec):
        c = Canvas(210, 280, 5, "#FFFFFF", 391 + k)
        c.photo(pid, 0, 0, 210, 280, crop=(0.1, 0.05, 0.9, 0.95))
        c.gradient(0, 0, 210, 70, col, mix(col, "#000000", 0.3))
        c.text(105, 30, title, 24, "#FFFFFF", 900, max_w=196)
        c.text(105, 58, en, 11, "#FFFFFF", 700, spacing=6)
        c.rect(12, 196, 198, 236, fill="#FFFFFF", radius=4)
        c.text(105, 216, sub, 15, col, 900, max_w=180)
        c.rect(12, 244, 60, 270, fill="#FFFFFF")
        c.barcode(14, 246, 44, 22)
        c.text(196, 258, "定価 580円", 10, "#FFFFFF", 800, anchor="rm", stroke=0.6, stroke_fill="#000000")
        covers.append(_face(c.array(), "film", 391 + k, 0.4, 3))
    hd = Canvas(950, 120, 2, "#2E3A46", 397)
    hd.gradient(0, 0, 950, 120, "#3B4A59", "#222C35")
    hd.rect(0, 100, 950, 108, fill="#F2C230")
    hd.text(475, 46, "雑誌・コミック", 48, "#FFFFFF", 900)
    hd.text(475, 84, "MAGAZINES  立ち読みはご遠慮ください", 18, "#F2C230", 700, spacing=2)
    header = _face(hd.array(), "film", 397, 0.4, 5)

    frame, board_c = "#4A4F55", "#D9DCE0"
    parts = [_box("Base", (0.9, 0.42, 0.1), (0, 0, 0.05), frame, "matte"),
             _box("SideLeft", (0.025, 0.42, 1.3), (-0.4625, 0, 0.65), frame, "metal"),
             _box("SideRight", (0.025, 0.42, 1.3), (0.4625, 0, 0.65), frame, "metal"),
             _box("BackPanel", (0.9, 0.02, 1.2), (0, 0.2, 0.7), board_c),
             _box("Header", (0.95, 0.02, 0.12), (0, 0.2, 1.36), "#2E3A46", "plastic", {"front": 6})]
    tilt = 15.0
    t = math.radians(tilt)
    up = (math.sin(t), math.cos(t))  # 板に沿って上へ（y, z）
    nrm = (-math.cos(t), -math.sin(t))  # 板の表の向き（手前・やや下）
    for k in range(3):
        z, y = 0.12 + 0.38 * k, -0.17 + 0.09 * k
        parts += [_box(f"Ledge{k + 1}", (0.9, 0.08, 0.02), (0, y, z), "#C9CED3", "metal"),
                  _box(f"Lip{k + 1}", (0.9, 0.006, 0.05), (0, y - 0.037, z + 0.025), "#EEF3F6", "glossy")]
        by, bz = y + 0.02, z + 0.01  # 板の下端
        parts.append(_box(f"Board{k + 1}", (0.9, 0.012, 0.34), (0, by + 0.17 * up[0], bz + 0.17 * up[1]), board_c,
                          rotation=[-tilt, 0, 0]))
        for i, x in enumerate((-0.33, -0.11, 0.11, 0.33)):
            s_, off = 0.012 + 0.14, 0.0095
            cy, cz = by + s_ * up[0] + off * nrm[0], bz + s_ * up[1] + off * nrm[1]
            parts.append(_box(f"Magazine{k + 1}{'ABCD'[i]}", (0.21, 0.006, 0.28), (x, round(cy, 5), round(cz, 5)),
                              "#FFFFFF", "glossy", {"front": (k * 4 + i) % 6}, [-tilt, 0, 0]))
    return Product(slug="magazine_rack", name="雑誌ラック 3段 900mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(1.42, 0.95, depth=0.42), mass_kg=30.0, static=True, material="steel",
                   description="形は店舗の傾斜した棚が 3 段ある雑誌ラックの一般的な構成（幅 950 mm・高さ 1420 mm）で、寸法・質量は代表値。雑誌の表紙はすべて架空。雑誌は棚と一体の固定物。",
                   tags=["雑誌ラック", "マガジンラック", "雑誌", "店舗什器", "magazine rack", "magazine"],
                   photos=[p[0] for p in covers_spec], colors=Colors(label_base=board_c), images=[*covers, header],
                   parts=parts)


def a_frame_sign() -> Product:
    def board(seed: int, lines: list[tuple], photos: list[tuple]) -> np.ndarray:
        w, h = 600.0, 920.0
        c = Canvas(w, h, 1.6, "#22382E", seed)
        c.gradient(0, 0, w, h, "#A9784A", "#6E4522", horizontal=True)  # 木枠
        c.rect(30, 30, w - 30, h - 30, fill="#24392F")
        c.gradient(30, 30, w - 30, h - 30, "#2B4337", "#1B2D24")
        for _ in range(60):  # チョークの粉
            x, y = c.rng.uniform(40, w - 40), c.rng.uniform(40, h - 40)
            c.ellipse(x - 1, y - 1, x + 1, y + 1, fill="#4C6358")
        for pid, x0, y0, x1, y1 in photos:
            c.photo(pid, x0, y0, x1, y1, shape="round", radius=12, border="#F4F1E8", border_w=4)
        for x, y, s, size, col, weight in lines:
            c.text(x, y, s, size, col, weight, max_w=w - 90)
        c.rect(30, h - 70, w - 30, h - 30, fill="#5A3A1E")  # チョーク置き
        c.rect(120, h - 64, 190, h - 50, fill="#F4F1E8", radius=4)
        c.rect(220, h - 62, 270, h - 50, fill="#F2C230", radius=4)
        return _face(c.array(), "paper", seed, 0.5, 6)

    chalk, yel, pink = "#F4F1E8", "#F7D774", "#F5A9B8"
    front = board(401, [(300, 95, "本日のおすすめ", 62, yel, 900), (300, 150, "TODAY'S SPECIAL", 24, chalk, 700),
                        (300, 470, "おにぎり 2個で 260円", 40, chalk, 900),
                        (300, 770, "カフェラテ M 180円", 40, pink, 900), (300, 820, "ホット／アイス", 26, chalk, 700)],
                  [("onigiri", 110, 190, 490, 430), ("latte", 150, 510, 450, 730)])
    back = board(402, [(300, 110, "いらっしゃいませ", 58, yel, 900), (300, 170, "WELCOME", 26, chalk, 700),
                       (300, 520, "営業時間  24時間", 40, chalk, 900), (300, 590, "店内でお召し上がりいただけます", 26, chalk, 700),
                       (300, 760, "コーヒー豆 量り売り", 36, pink, 900), (300, 810, "100g 580円", 30, chalk, 800)],
                 [("coffee_beans", 110, 210, 490, 440), ("coffee_beans", 160, 620, 440, 720)])
    blank = board(403, [], [])  # 何も書いていない黒板（Picture バリアントの Blank）
    a, L, T = 14.0, 0.92, 0.025
    t = math.radians(a)
    cy, cz = L / 2 * math.sin(t), L / 2 * math.cos(t)
    wood = "#8B5E34"
    parts = [_box("BoardFront", (0.6, T, L), (0, round(-cy, 5), round(cz, 5)), wood, "matte", {"front": 0}, [-a, 0, 0],
                  blank=2),
             _box("BoardBack", (0.6, T, L), (0, round(cy, 5), round(cz, 5)), wood, "matte", {"back": 1}, [a, 0, 0],
                  blank=2),
             _box("Hinge", (0.62, 0.035, 0.03), (0, 0, round(L * math.cos(t) - 0.005, 5)), "#5A3A1E", "matte"),
             _box("Stay", (0.5, 0.26, 0.006), (0, 0, 0.32), "#3A3A3A", "metal", collision=False)]
    return Product(slug="a_frame_sign", name="A型看板 黒板", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.91, 0.62, depth=0.47), mass_kg=7.0, material="wood",
                   description="形は店先に置く一般的な A 型の黒板看板（幅 600 mm・高さ約 900 mm、両面）で、寸法・質量は代表値。書かれた内容は架空。",
                   tags=["看板", "A型看板", "黒板", "スタンド看板", "店舗備品", "a-frame sign", "chalkboard"],
                   photos=["onigiri", "latte", "coffee_beans"], colors=Colors(label_base="#24392F"),
                   images=[front, back, blank], parts=parts, picture_places=["convenience_store", "cafe"])


def shopping_cart() -> Product:
    steel, blue = "#B9BEC4", "#1E5AA8"

    def axle_cyl(name, size, center, color, finish_):
        return Part(name=name, shape="cylinder", size=list(size), center=list(center), rotation=[0, 90, 0],
                    color=color, finish=finish_)

    parts = []
    for tag, x, y in (("FL", -0.22, -0.35), ("FR", 0.22, -0.35), ("RL", -0.22, 0.33), ("RR", 0.22, 0.33)):
        parts += [axle_cyl(f"Wheel{tag}", (0.1, 0.1, 0.03), (x, y, 0.05), "#2A2A2A", "matte"),
                  _box(f"Fork{tag}", (0.045, 0.05, 0.05), (x, y, 0.115), "#8E9399", "metal")]
    parts += [_box("RailLeft", (0.025, 0.78, 0.025), (-0.22, -0.01, 0.152), steel, "metal"),
              _box("RailRight", (0.025, 0.78, 0.025), (0.22, -0.01, 0.152), steel, "metal"),
              _box("RailFront", (0.465, 0.025, 0.025), (0, -0.39, 0.152), steel, "metal"),
              _box("RailRear", (0.465, 0.025, 0.025), (0, 0.37, 0.152), steel, "metal"),
              _box("LowerTray", (0.44, 0.62, 0.008), (0, -0.02, 0.169), "#8E9399", "metal"),
              _box("UprightLeft", (0.025, 0.025, 0.84), (-0.22, 0.37, 0.585), steel, "metal"),
              _box("UprightRight", (0.025, 0.025, 0.84), (0.22, 0.37, 0.585), steel, "metal"),
              axle_cyl("Handle", (0.035, 0.035, 0.5), (0, 0.385, 1.0), blue, "plastic"),
              _box("UpperRailLeft", (0.02, 0.54, 0.02), (-0.24, 0.1, 0.78), steel, "metal"),
              _box("UpperRailRight", (0.02, 0.54, 0.02), (0.24, 0.1, 0.78), steel, "metal"),
              _box("UpperRailFront", (0.5, 0.02, 0.02), (0, -0.16, 0.78), steel, "metal")]
    ly, lz = 0.39 - 0.16, 0.78 - 0.152  # 前の斜めの支柱（下端 y=-0.39 → 上端 y=-0.16）
    ang = math.degrees(math.atan2(ly, lz))
    for tag, x in (("Left", -0.22), ("Right", 0.22)):
        parts.append(_box(f"FrontStrut{tag}", (0.022, 0.022, round(math.hypot(ly, lz), 4)),
                          (x, round(-0.39 + ly / 2, 4), round(0.152 + lz / 2, 4)), steel, "metal",
                          rotation=[round(-ang, 3), 0, 0]))
    parts += _basket_parts("Basket", dy=0.1, dz=0.79)
    return Product(slug="shopping_cart", name="ショッピングカート かご付き", shape_class="assembly", category="fixture",
                   dims=Dimensions(1.03, 0.5, depth=0.8), mass_kg=13.0, material="steel",
                   description="形は店舗の一般的な買い物かごを載せるショッピングカート（上段にかご 1 つ、下段は台）で、寸法・質量は代表値。車輪は回らない固定の円柱、かごは本体と一体。",
                   tags=["ショッピングカート", "カート", "買い物かご", "店舗備品", "shopping cart", "trolley"], photos=[],
                   colors=Colors(label_base=_BASKET_RED), images=_basket_images(), parts=parts)


PRODUCTS = {f.__name__: f for f in (
    soda_pet_500ml, green_tea_pet_600ml, mineral_water_pet_550ml, canned_coffee_185g,
    cup_noodle_tall, cup_noodle_bowl, snack_cup, potato_chips_bag, chocolate_bar, stick_snack_box,
    deodorant_spray_150g, lip_balm_stick, skin_cream_tin, aa_battery, pocket_tissue,
    digital_signage_ceiling_3x, digital_signage_stand_43, coffee_machine, chest_freezer_showcase, self_checkout,
    milk_carton_1l, sparkling_water_can_350ml, hojicha_pet_hot_345ml, ice_cream_cup, butter_cookie_box, bottle_gum,
    box_tissue, hand_soap_pump, gondola_shelf, gondola_shelf_food, gondola_shelf_daily, gondola_shelf_bakery,
    shopping_basket,
    open_showcase_multideck, checkout_counter, magazine_rack, a_frame_sign, shopping_cart)}
