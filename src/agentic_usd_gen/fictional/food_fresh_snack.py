"""架空の商品のデザイン: 食品（チルド・パン・菓子・乾物など）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _face, back_info, seal_crimp, steam

FACES6 = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _pouch(c: Canvas, seed: int, strength: float = 1.0, shade: int = 24) -> np.ndarray:
    return trim_safe(edge_shade(finish(c.array(), "film", seed, strength), shade, 0.18))


def _nutrition(c: Canvas, x0: float, y0: float, x1: float, title: str, rows: list[tuple[str, str]], size: float,
               color: str = INK, bg: str = "#FFFFFF") -> float:
    """栄養成分表示だけの表（一括表示とは別の面に書くとき）。"""
    return c.table(x0, y0, x1, title, rows, size, color, bg)


# ---------------------------------------------------------------- チルド


def natto_3pack() -> Product:
    """発泡スチロールの角カップ 3 個を重ね、真ん中のカップに紙の帯を巻いたもの。"""
    cw, cd, ch, lip = 0.080, 0.070, 0.029, 0.003  # カップの胴と縁
    step = ch + lip
    bw, bd, bz0, bz1 = 0.0872, 0.0772, 0.028, 0.068  # 帯
    cream, red, green, brown = "#FBF4E2", "#C62828", "#2E7D32", "#8D5A2B"
    s = 10
    BW, BD, BH = bw * 1000, bd * 1000, (bz1 - bz0) * 1000

    def band(w: float, seed: int) -> Canvas:
        f = Canvas(w, BH, s, cream, seed)
        f.gradient(0, 0, w, BH, "#FFF8E8", "#F3E6C4")
        f.rect(0, 0, w, 2.2, fill=green)
        f.rect(0, BH - 2.2, w, BH, fill=green)
        return f

    fr = band(BW, 1300)
    fr.photo("natto", 3, 4, 34, BH - 5, shape="round", radius=3, crop=(0.34, 0.30, 0.73, 0.88))
    fr.text(18.5, BH - 3.4, "※写真はイメージです", 1.6, brown, 500)
    fr.text(61, 12, "納豆", 13, red, 900)
    fr.text(61, 23.5, "小粒  たれ・からし付", 3.6, brown, 800, max_w=46)
    fr.rect(39, 28, BW - 3, 35, fill=red, radius=3.5)
    fr.text((39 + BW - 3) / 2, 31.5, "45g × 3個パック", 3.6, "#FFFFFF", 900)

    bk = band(BW, 1301)
    back_info(bk, 3, 3.4, BW - 3, [
        ("名称", "納豆"), ("原材料名", "丸大豆（国産）、納豆菌、添付たれ、添付からし"),
        ("内容量", "45g×3"), ("消費期限", "フタに記載"), ("保存方法", "要冷蔵（10℃以下）")], 1.9)

    rt = band(BD, 1302)
    _nutrition(rt, 4, 3.6, BD - 4, "栄養成分表示 1パック（45g）当たり", [
        ("エネルギー", "90kcal"), ("たんぱく質", "7.4g"), ("脂質", "4.5g"), ("炭水化物", "5.4g"),
        ("食塩相当量", "0.0g")], 2.2)
    lf = band(BD, 1303)
    lf.barcode(6, 6, 32, 22)
    lf.recycle(50, 14, 8, "プラ", green, sub="容器")
    lf.recycle(66, 14, 8, "紙", green, sub="帯")
    lf.text(BD / 2, BH - 6, "要冷蔵 10℃以下", 3.0, red, 900)

    TW, TD = (cw + 0.006) * 1000, (cd + 0.006) * 1000
    tp = Canvas(TW, TD, s, cream, 1304)
    tp.gradient(0, 0, TW, TD, "#FFF8E8", "#F3E6C4")
    tp.pattern(0, 0, TW, TD, "dots", mix(cream, green, 0.18), 5, 0.5)
    tp.rect(2, 2, TW - 2, TD - 2, outline=green, width=0.8, radius=3)
    tp.text(TW / 2, 15, "納豆", 14, red, 900)
    tp.text(TW / 2, 26, "小粒  NATTO", 4.0, brown, 800, spacing=0.4)
    tp.photo("natto", TW / 2 - 18, 31, TW / 2 + 18, 59, shape="ellipse", feather=1.5, crop=(0.34, 0.30, 0.73, 0.88))
    tp.text(TW / 2, 64, "消費期限 2026.10.24", 3.0, INK, 700)
    tp.text(TW / 2, 69.5, NOTICE, 1.9, mix(INK, cream, 0.3), 500, max_w=TW - 6)
    imgs = [_face(f.array(), "paper", 1310 + i) for i, f in enumerate((fr, bk, rt, lf, tp))]

    foam = "#F5F3EE"
    parts = []
    for i in range(3):
        z = i * step
        parts.append(_box(f"Cup{i}", (cw, cd, ch), (0, 0, z + ch / 2), foam, "plastic"))
        if i != 1:  # 真ん中の縁は帯の中
            parts.append(_box(f"Lip{i}", (cw + 0.006, cd + 0.006, lip), (0, 0, z + ch + lip / 2), "#E9E5DB", "plastic",
                              {"top": 4} if i == 2 else None))
    parts.append(_box("Band", (bw, bd, bz1 - bz0), (0, 0, (bz0 + bz1) / 2), cream, "plastic",
                      {"front": 0, "back": 1, "right": 2, "left": 3}))
    return Product(slug="natto_3pack", name="納豆 3個パック たれ・からし付", shape_class="assembly", category="food",
                   dims=Dimensions(round(3 * step, 4), bw, depth=bd), mass_kg=0.16, material="plastic",
                   description="形は一般的な角カップ 3 個重ねの納豆（86 × 76 mm・高さ 96 mm、紙の帯付き）で、寸法・質量は代表値。",
                   tags=["納豆", "大豆", "チルド", "要冷蔵", "3個パック", "natto", "fermented soybeans"],
                   photos=["natto"], colors=Colors(label_base=cream), images=imgs, parts=parts)


def tofu_pack() -> Product:
    """透明なトレーに水と豆腐、上面にフィルムのラベル。"""
    W, D, H = 130.0, 100.0, 45.0
    blue, sky, white, navy = "#1F6FB2", "#DCEBF7", "#FFFFFF", "#173B66"
    s = 10

    def side(w: float, seed: int) -> Canvas:
        f = Canvas(w, H, s, sky, seed)
        f.gradient(0, 0, w, H, "#EEF5FB", "#CFE1F0")
        f.rect(3, 7, w - 3, H - 3, fill="#F6F3E8", radius=2)  # 豆腐
        f.gradient(3, 7, w - 3, 11, "#FFFFFF", "#F6F3E8")
        f.rect(0, 0, w, 4, fill=mix(sky, white, 0.4))  # フランジ
        f.line([(0, 4), (w, 4)], mix(blue, white, 0.5), 0.4)
        f.rect(0, H - 1.5, w, H, fill=mix(sky, navy, 0.15))
        return f

    fr = side(W, 1320)
    fr.rect(W / 2 - 24, 15, W / 2 + 24, 33, fill=white, radius=2, outline=blue, width=0.5)
    fr.text(W / 2, 21.5, "絹ごし豆腐", 6.0, navy, 900)
    fr.text(W / 2, 28.5, "要冷蔵  300g", 3.6, blue, 800)
    bk = side(W, 1321)
    bk.text(W / 2, 24, "SILKEN TOFU", 5.0, mix(navy, white, 0.4), 800, spacing=1.0)
    rt = side(D, 1322)
    lf = side(D, 1323)

    tp = Canvas(W, D, s, white, 1324)
    tp.gradient(0, 0, W, D, "#FFFFFF", sky)
    tp.pattern(0, 0, W, D, "waves", mix(sky, blue, 0.18), 6, 0.4)
    tp.rect(1.5, 1.5, W - 1.5, D - 1.5, outline=blue, width=0.8, radius=3)
    tp.photo("tofu", 5, 30, 70, 82, shape="round", radius=4, shadow=1.0, crop=(0.15, 0.05, 0.86, 0.95))
    tp.text(37.5, 12, "絹ごし", 8.5, navy, 900)
    tp.text(37.5, 24, "豆腐", 9.5, navy, 900)
    tp.text(37.5, 86, "※写真はイメージです", 2.4, INK, 500)
    tp.rect(14, 89, 61, 96, fill=blue, radius=3.5)
    tp.text(37.5, 92.5, "なめらか  300g", 3.6, white, 900)
    y = back_info(tp, 74, 4, W - 4, [
        ("名称", "絹ごし豆腐"), ("原材料名", "丸大豆（国産）／凝固剤（塩化マグネシウム（にがり））"),
        ("内容量", "300g"), ("消費期限", "上部に記載"), ("保存方法", "要冷蔵（10℃以下）")], 1.9, color=navy)
    tp.text((74 + W - 4) / 2, y + 3, "消費期限 2026.10.22", 2.8, INK, 800)

    bt = Canvas(W, D, s, sky, 1325)
    bt.gradient(0, 0, W, D, "#E6F0F8", "#CFE1F0")
    _nutrition(bt, 8, 8, 70, "栄養成分表示 100g当たり", [
        ("エネルギー", "56kcal"), ("たんぱく質", "5.3g"), ("脂質", "3.5g"), ("炭水化物", "2.0g"),
        ("食塩相当量", "0.0g")], 2.6, navy)
    bt.barcode(78, 12, 40, 26)
    bt.recycle(88, 62, 12, "プラ", navy, sub="容器")
    bt.recycle(110, 62, 12, "プラ", navy, sub="フィルム")
    imgs = [_face(f.array(), "film", 1330 + i, 0.6) for i, f in enumerate((fr, bk, rt, lf, tp, bt))]
    return Product(slug="tofu_pack", name="絹ごし豆腐 300g", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.36, material="plastic",
                   description="形は一般的なトレー入りの充てん豆腐（130 × 100 mm・高さ 45 mm）で、寸法・質量は代表値。",
                   tags=["豆腐", "絹ごし豆腐", "チルド", "要冷蔵", "tofu", "silken tofu"], photos=["tofu"],
                   colors=Colors(label_base=sky), images=imgs, faces=FACES6)


def yogurt_tub() -> Product:
    form = forms.paper_cup(0.082, 0.098, 0.084, lid_h=0.004, lid_overhang=0.002, rim_h=0.005,
                           label_margin=(0.003, 0.002))
    white, blue, sky = "#FFFFFF", "#1A4FA0", "#DCE8F7"
    c = label_canvas(form, white, seed=1340)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#EEF4FB")
    c.rect(0, 0, W, 9, fill=blue)
    c.pattern(0, H - 8, W, H, "waves", mix(blue, white, 0.5), 3.5, 0.6)
    c.text(fx, 4.6, "生乳たっぷり", 4.4, white, 800)
    c.photo("yogurt", fx - 44, 13, fx - 4, H - 12, shape="round", radius=4, shadow=1.0,
            crop=(0.17, 0.05, 0.80, 0.97))
    c.text(fx - 24, H - 9.8, "※写真はイメージです", 2.0, INK, 500)
    c.text(fx + 22, 22, "プレーン", 7.2, blue, 900, max_w=40)
    c.text(fx + 22, 33, "ヨーグルト", 7.2, blue, 900, max_w=40)
    c.text(fx + 22, 41, "PLAIN YOGURT", 3.0, mix(blue, white, 0.3), 800, spacing=0.4)
    c.rect(fx + 6, 45, fx + 38, 53, fill=blue, radius=4)
    c.text(fx + 22, 49, "400g", 5.0, white, 900)
    c.text(0.5 * W, 4.6, "PLAIN YOGURT", 4.0, white, 800, spacing=0.8)
    bx = 0.25 * W
    c.rect(bx - 33, 11, bx + 33, H - 9, fill=white, radius=1.5)
    back_info(c, bx - 32, 12, bx + 32, [
        ("種類別", "はっ酵乳"), ("無脂乳固形分", "9.5%"), ("乳脂肪分", "3.0%"), ("原材料名", "生乳、乳製品"),
        ("内容量", "400g"), ("賞味期限", "フタに記載"), ("保存方法", "要冷蔵（10℃以下）")], 1.6,
        [("栄養成分表示 100g当たり", ""), ("エネルギー", "62kcal"), ("たんぱく質", "3.6g"), ("脂質", "3.0g"),
         ("炭水化物", "4.9g"), ("食塩相当量", "0.1g")], blue)
    c.barcode(0.5 * W - 12, 14, 24, 16)
    c.recycle(0.5 * W - 7, 40, 7, "プラ", blue, sub="容器")
    c.recycle(0.5 * W + 7, 40, 7, "プラ", blue, sub="フタ")
    label = edge_shade(finish(c.array(), "paper", 1340, 0.6), 6, 0.06)

    t = top_canvas(form, white, seed=1341)
    d = t.w_mm
    t.ellipse(0.5, 0.5, d - 0.5, d - 0.5, fill=sky)
    t.ellipse(4, 4, d - 4, d - 4, fill=white, outline=blue, width=1.0)
    t.text(d / 2, d * 0.24, "要冷蔵", 4.0, blue, 800)
    t.text(d / 2, d * 0.40, "プレーン", 9.5, blue, 900)
    t.text(d / 2, d * 0.54, "ヨーグルト", 9.5, blue, 900)
    t.text(d / 2, d * 0.68, "400g", 6.0, INK, 900)
    t.text(d / 2, d * 0.80, "賞味期限 2026.11.05", 3.4, INK, 700)
    top = finish(t.array(), "metal", 1341, 0.5)
    return Product(slug="yogurt_tub", name="プレーンヨーグルト 400g", category="food", mass_kg=0.42, material="plastic",
                   description="形は一般的な 400g のカップ入りヨーグルト（高さ 82 mm・上端径約 102 mm）で、寸法・質量は代表値。",
                   tags=["ヨーグルト", "プレーン", "乳製品", "チルド", "要冷蔵", "yogurt", "plain yogurt"],
                   photos=["yogurt"], colors=Colors(cap=white, label_base=white), **revolve(form, label=label, top=top))


def pudding_cup() -> Product:
    """透明なカップ。下にカラメル、上にプリンが透けて見え、胴の中ほどに帯のラベル。"""
    form = forms.paper_cup(0.062, 0.075, 0.056, lid_h=0.0025, lid_overhang=0.002, rim_h=0.004,
                           label_margin=(0.001, 0.001))
    custard, caramel, brown, cream = "#F4D26B", "#7A3E12", "#5A2A0C", "#FFF6DD"
    c = label_canvas(form, custard, seed=1350)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H - 13, "#FBE7A2", "#F0C95A")  # プリン
    c.gradient(0, H - 13, W, H, "#9A5420", "#5E2C0B")  # カラメル
    c.rect(0, 0, W, 2.5, fill=mix(custard, "#FFFFFF", 0.6))  # 上の空き
    c.rect(0, 13, W, 36, fill=cream)
    c.rect(0, 13, W, 14.2, fill=caramel)
    c.rect(0, 34.8, W, 36, fill=caramel)
    c.photo("pudding", fx - 33, 14.2, fx - 7, 34.8, crop=(0.17, 0.12, 0.83, 0.92))
    c.text(fx + 13, 21, "カスタード", 4.8, brown, 900, max_w=34)
    c.text(fx + 13, 29.5, "プリン", 6.0, brown, 900)
    c.text(fx - 20, 39, "※写真はイメージです", 1.8, brown, 500)
    c.text(fx, 8, "CUSTARD PUDDING", 2.8, brown, 800, spacing=0.4)
    bx = 0.25 * W
    back_info(c, bx - 28, 14.6, bx + 28, [
        ("名称", "洋生菓子"), ("原材料名", "牛乳、砂糖、鶏卵、生クリーム、カラメルソース／香料"),
        ("内容量", "85g"), ("消費期限", "フタに記載")], 1.2, color=brown, bg=cream)
    c.barcode(0.5 * W - 9, 15, 18, 12)
    c.text(0.5 * W, 31, "要冷蔵 10℃以下", 2.0, brown, 900)
    c.recycle(0.08 * W, 24, 6, "プラ", brown, sub="容器・フタ")
    label = edge_shade(finish(c.array(), "film", 1350, 0.6), 6, 0.06)

    t = top_canvas(form, cream, seed=1351)
    d = t.w_mm
    t.ellipse(0.5, 0.5, d - 0.5, d - 0.5, fill=caramel)
    t.ellipse(3, 3, d - 3, d - 3, fill=cream)
    t.text(d / 2, d * 0.28, "カスタード", 7.0, brown, 900)
    t.text(d / 2, d * 0.44, "プリン", 10, brown, 900)
    t.text(d / 2, d * 0.59, "栄養成分表示 1個（85g）当たり", 2.3, brown, 700)
    t.text(d / 2, d * 0.655, "エネルギー 120kcal  たんぱく質 3.4g", 2.1, brown, 500, max_w=d - 16)
    t.text(d / 2, d * 0.715, "脂質 4.8g  炭水化物 16.0g  食塩相当量 0.1g", 2.1, brown, 500, max_w=d - 18)
    t.text(d / 2, d * 0.81, "消費期限 2026.10.21", 2.8, INK, 700)
    top = finish(t.array(), "film", 1351, 0.6)
    return Product(slug="pudding_cup", name="カスタードプリン 85g", category="food", mass_kg=0.095, material="plastic",
                   description="形は一般的なカップ入りプリン（高さ 62 mm・上端径約 79 mm）で、寸法・質量は代表値。",
                   tags=["プリン", "カスタードプリン", "デザート", "チルド", "要冷蔵", "pudding", "dessert"],
                   photos=["pudding"], colors=Colors(cap=cream, label_base=custard), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- パン


def sliced_bread() -> Product:
    """角食パン 1 斤（6 枚切）を袋に入れ、片側を絞って留めたもの。胴は箱、絞り口と留め具は小さな部品。"""
    L, D, H = 125.0, 115.0, 120.0  # 胴（x がスライスの並ぶ向き）
    tail = 0.028
    crust, crumb, white, red, wheat = "#B8732E", "#F3E3C0", "#FFFFFF", "#C0392B", "#E3B04B"
    s = 8
    x_off = -tail / 2  # 全体の中心を原点に

    def bag(w: float, h: float, seed: int, slices: bool = True) -> Canvas:
        f = Canvas(w, h, s, crust, seed)
        f.gradient(0, 0, w, h, "#C98A42", "#A9662A")
        if slices:
            for k in range(1, 6):
                f.line([(w * k / 6, 3), (w * k / 6, h - 3)], mix(crust, "#000000", 0.25), 0.5)
        f.pattern(0, 0, w, h, "dots", mix(white, crust, 0.35), 7, 0.5)  # 袋の水玉
        return f

    fr = bag(L, H, 1360)
    fr.rect(10, 12, L - 10, 62, fill=white, radius=6)
    fr.text(L / 2, 28, "食パン", 15, red, 900)
    fr.text(L / 2, 46, "6枚切", 10, crust, 900)
    fr.text(L / 2, 57, "SLICED BREAD", 3.6, mix(crust, "#000000", 0.2), 800, spacing=1.0)
    fr.photo("bread", 20, 66, L - 20, 106, shape="round", radius=4, shadow=1.0, crop=(0.20, 0.05, 0.84, 0.95))
    fr.text(L / 2, 110.5, "※写真はイメージです", 2.6, white, 500)
    fr.rect(L / 2 - 20, 113, L / 2 + 20, 118, fill=wheat, radius=2.5)
    fr.text(L / 2, 115.5, "ふんわり もっちり", 2.8, mix(crust, "#000000", 0.4), 800)

    bk = bag(L, H, 1361)
    bk.rect(6, 6, L - 6, H - 6, fill=white, radius=3)
    back_info(bk, 9, 9, L / 2 + 4, [
        ("名称", "食パン"), ("原材料名", "小麦粉、砂糖、バター入りマーガリン、パン酵母、食塩、脱脂粉乳"),
        ("内容量", "6枚"), ("消費期限", "留め具に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 2.4)
    _nutrition(bk, L / 2 + 8, 9, L - 9, "栄養成分表示 1枚当たり", [
        ("エネルギー", "158kcal"), ("たんぱく質", "5.3g"), ("脂質", "2.6g"), ("炭水化物", "28.6g"),
        ("食塩相当量", "0.7g")], 2.4)
    bk.barcode(L / 2 + 12, 60, 40, 24)
    bk.recycle(L / 2 + 20, 100, 10, "プラ", red, sub="袋")
    bk.recycle(L / 2 + 44, 100, 10, "プラ", red, sub="留め具")

    def end(seed: int, gathered: bool) -> Canvas:
        f = Canvas(D, H, s, crust, seed)
        f.gradient(0, 0, D, H, "#C98A42", "#8F5420")  # 耳
        f.rect(4, 4, D - 4, H - 3, fill=crumb, radius=5)  # 断面
        f.pattern(8, 8, D - 8, H - 7, "dots", mix(crumb, crust, 0.18), 3.2, 0.35)
        if gathered:  # 袋を絞ったしわ
            for k in range(9):
                x = D * (k + 1) / 10
                f.line([(x, 0), (D / 2 + (x - D / 2) * 0.25, H / 2), (x, H)], mix(white, crust, 0.55), 0.7)
        f.pattern(0, 0, D, H, "dots", mix(white, crust, 0.35), 7, 0.5)
        return f

    rt = end(1362, True)
    lf = end(1363, False)
    lf.text(D / 2, H / 2, "食パン", 7, mix(crust, "#000000", 0.3), 900)

    tp = bag(L, D, 1364)
    tp.rect(L / 2 - 30, D / 2 - 10, L / 2 + 30, D / 2 + 10, fill=white, radius=4)
    tp.text(L / 2, D / 2 - 3, "食パン 6枚切", 6.0, red, 900)
    tp.text(L / 2, D / 2 + 5, "消費期限 2026.10.20", 3.0, INK, 700)
    bt = bag(L, D, 1365, slices=False)
    bt.text(L / 2, D / 2, NOTICE, 3.0, white, 600)
    imgs = [_face(f.array(), "film", 1370 + i, 0.8) for i, f in enumerate((fr, bk, rt, lf, tp, bt))]
    parts = [
        _box("Loaf", (L / 1000, D / 1000, H / 1000), (x_off, 0, H / 2000), crust, "plastic", dict(FACES6)),
        _box("BagTail", (tail + 0.002, 0.03, 0.034), (x_off + L / 2000 + tail / 2 - 0.001, 0, H / 2000),
             mix(white, crust, 0.3), "plastic"),
        _box("Clip", (0.004, 0.036, 0.014), (x_off + L / 2000 + 0.012, 0, H / 2000), "#2E6FBF", "plastic"),
    ]
    return Product(slug="sliced_bread", name="食パン 6枚切", shape_class="assembly", category="food",
                   dims=Dimensions(H / 1000, round(L / 1000 + tail, 4), depth=D / 1000), mass_kg=0.40,
                   material="film",
                   description="形は一般的な袋入りの角食パン 1 斤・6 枚切（125 × 115 mm・高さ 120 mm、片側を絞って留め具で閉じる）で、寸法・質量は代表値。",
                   tags=["食パン", "パン", "6枚切", "角食", "bread", "sliced bread"], photos=["bread"],
                   colors=Colors(label_base=crust), images=imgs, parts=parts)


# ---------------------------------------------------------------- お茶


def green_tea_bag_box() -> Product:
    W, D, H = 170.0, 75.0, 85.0
    green, deep, cream, gold = "#3C7A2E", "#1F4A18", "#F6F2E3", "#C9A23A"
    s = 9

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, green, seed)
        f.gradient(0, 0, w, h, "#4B8F3A", "#2C6022")
        return f

    fr = face(W, H, 1380)
    fr.photo("tea_field", 0, 0, W, 34, crop=(0.0, 0.25, 1.0, 0.75))
    fr.gradient(0, 30, W, 36, "#2C6022", "#3C7A2E")
    fr.rect(6, 38, 98, 80, fill=cream, radius=3)
    fr.text(52, 50, "緑茶", 12, deep, 900)
    fr.text(52, 63, "ティーバッグ", 7.0, deep, 900)
    fr.text(52, 73, "GREEN TEA  2g × 50袋", 3.0, green, 800, spacing=0.3)
    fr.photo("tea_leaves", 104, 38, W - 6, 72, shape="round", radius=3, crop=(0.26, 0.40, 0.76, 0.80))
    fr.rect(110, 74, W - 12, 81, fill=gold, radius=3.5)
    fr.text((110 + W - 12) / 2, 77.5, "50袋入", 4.2, deep, 900)
    fr.text(W - 4, 4, "※写真はイメージです", 2.4, "#FFFFFF", 600, anchor="rt", stroke=0.3, stroke_fill=deep)

    bk = face(W, H, 1381)
    bk.rect(4, 4, W - 4, H - 4, fill=cream, radius=2)
    back_info(bk, 7, 7, 92, [
        ("名称", "緑茶（ティーバッグ）"), ("原材料名", "緑茶（国産）"), ("内容量", "100g（2g×50袋）"),
        ("賞味期限", "底面に記載"), ("保存方法", "高温多湿を避け、移り香にご注意ください")], 2.4, color=deep, bg=cream)
    y = _nutrition(bk, 98, 7, W - 7, "栄養成分表示 100ml当たり", [
        ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"), ("炭水化物", "0.1g"), ("食塩相当量", "0g")],
        2.4, deep, cream)
    bk.text((98 + W - 7) / 2, y + 6, "おいしい入れ方", 3.0, deep, 900)
    bk.text((98 + W - 7) / 2, y + 12, "湯のみに 1袋、熱湯 150ml で 1分", 2.4, deep, 600, max_w=W - 109)

    sides = []
    for k, seed in enumerate((1382, 1383)):
        sd = face(D, H, seed)
        sd.rect(4, 4, D - 4, H - 4, fill=cream, radius=2)
        if k == 0:
            sd.text(D / 2, 16, "緑茶", 10, deep, 900)
            sd.text(D / 2, 28, "ティーバッグ 50袋", 3.6, green, 800)
            sd.photo("tea_leaves", 8, 34, D - 8, 76, shape="round", radius=3, crop=(0.30, 0.38, 0.72, 0.80))
        else:
            sd.barcode(D / 2 - 18, 10, 36, 24)
            sd.recycle(D / 2 - 12, 52, 10, "紙", deep, sub="箱")
            sd.recycle(D / 2 + 12, 52, 10, "プラ", deep, sub="個包装")
        sides.append(sd)
    tp = face(W, D, 1384)
    tp.rect(3, 3, W - 3, D - 3, outline=gold, width=0.6, radius=2)
    tp.text(W / 2, D / 2 - 6, "緑茶 ティーバッグ", 8.0, cream, 900)
    tp.text(W / 2, D / 2 + 8, "← ここを押してあけてください", 3.4, gold, 700)
    bt = face(W, D, 1385)
    bt.text(W / 2, D / 2 - 5, "賞味期限 2027.09.30", 4.0, cream, 600)
    bt.text(W / 2, D / 2 + 5, NOTICE, 3.0, cream, 400, max_w=W - 10)
    imgs = [_face(f.array(), "paper", 1390 + i) for i, f in enumerate((fr, bk, *sides, tp, bt))]
    return Product(slug="green_tea_bag_box", name="緑茶 ティーバッグ 50袋", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.16, material="paper",
                   description="形は一般的な箱入りのティーバッグ（高さ 85 mm・幅 170 mm・奥行き 75 mm）で、寸法・質量は代表値。",
                   tags=["緑茶", "お茶", "ティーバッグ", "日本茶", "green tea", "tea bags"],
                   photos=["tea_field", "tea_leaves"], colors=Colors(label_base=green), images=imgs, faces=FACES6)


# ---------------------------------------------------------------- 菓子・麺の袋


def _back_panel(c: Canvas, x0: float, y0: float, x1: float, y_max: float, rows: list[tuple[str, str]],
                size: float, nutrition: list[tuple[str, str]], sections: list[tuple[str, str]], accent: str) -> float:
    """袋の裏面の白いパネルの中身: 一括表示・栄養成分表示・NOTICE と、見出し付きの文（作り方・注意など）。下端 y を返す。"""
    y = back_info(c, x0, y0, x1, rows, size, nutrition)
    for title, body in sections:
        y += size * 1.0
        c.rect(x0, y, x1, y + size * 1.8, fill=accent, radius=size * 0.3)
        c.text(x0 + size * 0.6, y + size * 0.9, title, size * 1.05, "#FFFFFF", 800, anchor="lm")
        y = c.paragraph(x0 + size * 0.3, y + size * 2.3, x1 - size * 0.3, body, size, INK, 500)
    if y > y_max:
        raise ValueError(f"裏面の文がパネルからはみ出す（{y:.1f} > {y_max:.1f} mm）")
    return y


def rice_cracker_bag() -> Product:
    W, H = 170.0, 260.0
    beige, red, brown, white = "#EAD9B5", "#B3261E", "#4A2A12", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, beige, seed=seed)
        c.gradient(0, 0, W, H, "#F2E4C4", "#DCC594")
        c.pattern(0, 0, W, H, "stripes", mix(beige, brown, 0.08), 6, 0.8)
        seal_crimp(c, 0, 0, W, 13, "#C9A86B", 1.6)
        seal_crimp(c, 0, H - 13, W, H, "#C9A86B", 1.6)
        c.rect(0, 13, W, 16, fill=red)
        c.rect(0, H - 16, W, H - 13, fill=red)
        return c

    c = base(1400)
    c.rect(W - 46, 24, W - 14, 112, fill=red, radius=3)
    c.vtext(W - 30, 36, "しょうゆ", 10, white, 900)
    c.vtext(W - 30, 84, "味", 10, white, 900)
    c.text(64, 44, "せんべい", 22, brown, 900, max_w=W - 80)
    c.text(64, 66, "香ばし焼き", 9, red, 900)
    c.text(64, 80, "RICE CRACKERS", 5.0, brown, 700, spacing=1.2)
    c.text(64, 92, "うるち米 100%使用", 4.4, brown, 700, max_w=W - 80)
    c.photo("senbei", 14, 120, W - 14, 222, shape="round", radius=8, shadow=2, crop=(0.03, 0.08, 0.97, 0.88))
    c.text(W / 2, 227, "※写真はイメージです", 3.0, brown, 500)
    c.rect(W / 2 - 26, 232, W / 2 + 26, 241, fill=red, radius=4.5)
    c.text(W / 2, 236.5, "12枚入", 5.0, white, 900)
    front = _pouch(c, 1400)

    b = base(1401)
    b.text(W / 2, 26, "しょうゆせんべい  12枚", 6.0, brown, 900)
    b.rect(12, 33, W - 12, H - 20, fill=white, radius=3)
    _back_panel(b, 16, 37, W - 16, H - 52, [
        ("名称", "米菓"), ("原材料名", "うるち米（国産）、しょうゆ（大豆・小麦を含む）、砂糖、でん粉"),
        ("内容量", "12枚"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存してください。")], 4.6,
        [("栄養成分表示 1枚当たり", ""), ("エネルギー", "38kcal"), ("たんぱく質", "0.7g"), ("脂質", "0.2g"),
         ("炭水化物", "8.4g"), ("食塩相当量", "0.2g")],
        [("ご注意", "開封後は湿気やすいので、お早めにお召し上がりください。かたいので、お年寄りやお子様は気をつけてお召し上がりください。")],
        red)
    b.barcode(18, H - 48, 40, 24)
    b.recycle(W - 34, H - 36, 12, "プラ", red, sub="袋")
    back = _pouch(b, 1401)
    return Product(slug="rice_cracker_bag", name="しょうゆせんべい 12枚", shape_class="pouch", category="food",
                   dims=Dimensions(0.26, 0.17, depth=0.06), mass_kg=0.14, material="film",
                   description="形は一般的なピロー包装のせんべいの袋（高さ 260 mm・幅 170 mm）で、寸法・質量は代表値。",
                   tags=["せんべい", "米菓", "しょうゆ", "お菓子", "rice crackers", "senbei"], photos=["senbei"],
                   colors=Colors(label_base=beige), images=[front, back], faces={"front": 0, "back": 1})


def gummy_candy_pouch() -> Product:
    W, H = 110.0, 150.0
    pink, magenta, yellow, white = "#F8BBD0", "#C2185B", "#FFD54F", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, pink, seed=seed)
        c.gradient(0, 0, W, H, "#FCD3E1", "#F48FB1")
        c.pattern(0, 0, W, H, "dots", mix(pink, white, 0.5), 6, 0.8)
        seal_crimp(c, 0, 0, W, 9, "#F8BBD0", 1.2)
        seal_crimp(c, 0, H - 9, W, H, "#F48FB1", 1.2)
        c.rect(0, 9, W, 10.5, fill=magenta)
        c.rect(0, H - 10.5, W, H - 9, fill=magenta)
        return c

    c = base(1410)
    c.text(W / 2, 24, "フルーツ", 10, magenta, 900, stroke=0.8, stroke_fill=white)
    c.text(W / 2, 40, "グミ", 16, magenta, 900, stroke=1.0, stroke_fill=white)
    c.text(W / 2, 52, "FRUIT GUMMY", 4.2, white, 800, spacing=0.8)
    c.photo("gummy", 10, 58, W - 10, 122, shape="ellipse", feather=2.5, crop=(0.12, 0.08, 0.88, 0.92))
    c.ellipse(W - 34, 104, W - 6, 128, fill=yellow)
    c.text(W - 20, 112, "果汁", 4.0, magenta, 900)
    c.text(W - 20, 119, "10%", 4.4, magenta, 900)
    c.text(W / 2, 127, "※写真はイメージです", 2.2, white, 600)
    c.rect(W / 2 - 16, 131, W / 2 + 16, 137, fill=white, radius=3)
    c.text(W / 2, 134, "80g", 3.8, magenta, 900)
    front = _pouch(c, 1410, 0.9, 16)

    b = base(1411)
    b.text(W / 2, 16, "フルーツグミ 80g", 4.0, magenta, 900)
    b.rect(6, 20, W - 6, H - 13, fill=white, radius=2)
    _back_panel(b, 9, 22.5, W - 9, H - 33, [
        ("名称", "グミキャンディ"), ("原材料名", "水あめ、砂糖、ゼラチン、果汁（ぶどう・りんご・もも）／酸味料、香料、着色料"),
        ("内容量", "80g"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温を避けて保存")], 3.0,
        [("栄養成分表示 1袋当たり", ""), ("エネルギー", "274kcal"), ("たんぱく質", "5.0g"), ("脂質", "0g"),
         ("炭水化物", "63.2g"), ("食塩相当量", "0.05g")],
        [("ご注意", "小さなお子様は、のどにつまらせないようよくかんでお召し上がりください。")], magenta)
    b.barcode(10, H - 31, 30, 16)
    b.recycle(W - 22, H - 23, 8, "プラ", magenta, sub="袋")
    back = _pouch(b, 1411, 0.9, 16)
    return Product(slug="gummy_candy_pouch", name="フルーツグミ 80g", shape_class="pouch", category="food",
                   dims=Dimensions(0.15, 0.11, depth=0.025), mass_kg=0.085, material="film",
                   description="形は一般的な小袋入りのグミ（高さ 150 mm・幅 110 mm）で、寸法・質量は代表値。",
                   tags=["グミ", "キャンディ", "お菓子", "フルーツ", "gummy", "candy"], photos=["gummy"],
                   colors=Colors(label_base=pink), images=[front, back], faces={"front": 0, "back": 1})


def instant_ramen_5pack() -> Product:
    """5 食をまとめた印刷フィルムの外袋（中は見えない）。"""
    W, H = 220.0, 330.0
    red, gold, white, dark = "#B71C1C", "#F2B632", "#FFFFFF", "#3A0A0A"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 6, red, seed=seed)
        c.gradient(0, 0, W, H, "#D32F2F", "#8E1414")
        c.pattern(0, 0, W, H, "waves", mix(red, gold, 0.18), 12, 0.7)
        seal_crimp(c, 0, 0, W, 16, "#C62828", 2.0)
        seal_crimp(c, 0, H - 16, W, H, "#8E1414", 2.0)
        c.rect(0, 16, W, 19, fill=gold)
        c.rect(0, H - 19, W, H - 16, fill=gold)
        return c

    c = base(1420)
    c.rect(16, 28, W - 16, 112, fill=white, radius=10)
    c.text(W / 2, 52, "袋めん", 22, red, 900)
    c.text(W / 2, 80, "しょうゆ味", 18, dark, 900)
    c.text(W / 2, 101, "SHOYU RAMEN", 7.0, red, 800, spacing=2.0)
    c.photo("ramen", 16, 120, W - 16, 268, shape="ellipse", feather=5, shadow=2, crop=(0.06, 0.08, 0.94, 0.94))
    c.ellipse(W - 72, 236, W - 12, 286, fill=gold)
    c.text(W - 42, 253, "5食", 12, red, 900)
    c.text(W - 42, 270, "パック", 6.0, red, 900)
    c.text(20, 278, "※写真は調理例です", 3.6, white, 500, anchor="lm")
    c.rect(20, 288, 126, 304, fill=gold, radius=8)
    c.text(73, 296, "めん 85g × 5食", 6.0, dark, 900)
    front = _pouch(c, 1420, 1.1, 30)

    b = base(1421)
    b.text(W / 2, 30, "袋めん しょうゆ味  5食パック", 8.0, white, 900)
    b.rect(14, 40, W - 14, H - 26, fill=white, radius=4)
    _back_panel(b, 20, 45, W - 20, H - 66, [
        ("名称", "即席中華めん"), ("原材料名", "油揚げめん（小麦粉、植物油脂、食塩）、スープ（しょうゆ、食塩、糖類、チキンエキス、香辛料）／調味料（アミノ酸等）、かんすい"),
        ("内容量", "500g（めん 425g）×5食"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 5.6,
        [("栄養成分表示 1食（100g）当たり", ""), ("エネルギー", "448kcal"), ("たんぱく質", "10.2g"), ("脂質", "16.6g"),
         ("炭水化物", "64.4g"), ("食塩相当量", "5.6g")],
        [("作り方", "沸騰したお湯 500ml にめんを入れ、3分ゆでます。火を止めて添付のスープを入れ、よくかき混ぜてできあがり。"),
         ("ご注意", "やけどに注意してください。開封後はお早めにお召し上がりください。")], red)
    b.barcode(22, H - 62, 46, 30)
    b.recycle(W - 44, H - 46, 14, "プラ", red, sub="袋")
    back = _pouch(b, 1421, 1.1, 30)
    return Product(slug="instant_ramen_5pack", name="袋めん しょうゆ味 5食パック", shape_class="pouch", category="food",
                   dims=Dimensions(0.33, 0.22, depth=0.11), mass_kg=0.52, material="film",
                   description="形は一般的な袋めんの 5 食パック（高さ 330 mm・幅 220 mm）で、寸法・質量は代表値。",
                   tags=["袋めん", "インスタントラーメン", "即席めん", "しょうゆ", "5食パック", "instant ramen", "noodles"],
                   photos=["ramen"], colors=Colors(label_base=red), images=[front, back], faces={"front": 0, "back": 1})


def spaghetti_pack() -> Product:
    """寝かせた細長い袋。右側に麺が見える窓。画像は横長（左右がシール）。"""
    L, Wd = 290.0, 85.0
    navy, white, gold, red, green = "#14365E", "#FFFFFF", "#E8C77A", "#C62828", "#2E7D32"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 8, navy, seed=seed)
        c.gradient(0, 0, L, Wd, "#1C4A80", "#0F2847")
        seal_crimp(c, 0, 0, 10, Wd, "#1C4A80", 1.4, vertical=True)
        seal_crimp(c, L - 10, 0, L, Wd, "#0F2847", 1.4, vertical=True)
        return c

    def window(c: Canvas, x0: float, x1: float):
        c.rect(x0, 8, x1, Wd - 8, fill="#F1D79A", radius=4)
        for k in range(70):
            y = 9 + k * (Wd - 18) / 70
            c.line([(x0 + 1, y), (x1 - 1, y + c.rng.uniform(-0.3, 0.3))], mix(gold, "#B8862E", c.rng.random() * 0.6), 0.45)
        c.rect(x0, 8, x1, Wd - 8, outline=white, width=0.8, radius=4)

    c = base(1430)
    window(c, 118, L - 16)
    c.rect(14, 0, 18, Wd, fill=green)
    c.rect(18, 0, 22, Wd, fill=white)
    c.rect(22, 0, 26, Wd, fill=red)
    c.text(72, 18, "スパゲッティ", 10, white, 900, max_w=86)
    c.text(72, 32, "SPAGHETTI", 5.0, gold, 800, spacing=1.2)
    c.rect(40, 38, 104, 49, fill=gold, radius=5.5)
    c.text(72, 43.5, "1.6mm  ゆで時間 7分", 4.0, navy, 900)
    c.photo("spaghetti", 34, 53, 88, 77, shape="round", radius=3, crop=(0.12, 0.22, 0.88, 0.82))
    c.text(61, 80.5, "※写真は調理例です", 1.8, white, 500)
    c.ellipse(91, 56, 113, 78, fill=gold)
    c.text(102, 67, "500g", 4.4, navy, 900)
    front = _pouch(c, 1430, 0.9, 16)

    b = base(1431)
    window(b, 14, 34)
    b.rect(40, 8, L - 14, Wd - 8, fill=white, radius=3)
    _back_panel(b, 43, 11, 152, Wd - 10, [
        ("名称", "スパゲッティ"), ("原材料名", "デュラム小麦のセモリナ"), ("内容量", "500g"),
        ("賞味期限", "右端に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.0,
        [("栄養成分表示 100g当たり", ""), ("エネルギー", "347kcal"), ("たんぱく質", "12.9g"), ("脂質", "1.8g"),
         ("炭水化物", "72.2g"), ("食塩相当量", "0g")], [], navy)
    _back_panel_sections = [
        ("ゆで方", "たっぷりのお湯（1人前 100g に 1L）に塩を少し入れ、沸騰したらめんをほぐし入れて 7分ゆでます。"),
        ("ご注意", "ゆでるときは吹きこぼれに注意してください。開封後は袋の口を閉じて保存してください。")]
    y = 11.0
    for title, body in _back_panel_sections:
        b.rect(158, y, 226, y + 5.0, fill=navy, radius=0.8)
        b.text(159.5, y + 2.5, title, 3.2, white, 800, anchor="lm")
        y = b.paragraph(159, y + 6.4, 225, body, 3.0, INK, 500) + 3.0
    if y > Wd - 10:
        raise ValueError(f"裏面の文がはみ出す（{y:.1f} mm）")
    b.text(192, Wd - 15, "1人前 100g（約 1/5 袋）", 3.4, navy, 800)
    b.barcode(L - 60, 14, 40, 22)
    b.recycle(L - 40, Wd - 24, 12, "プラ", navy, sub="袋")
    back = _pouch(b, 1431, 0.9, 16)
    return Product(slug="spaghetti_pack", name="スパゲッティ 1.6mm 500g", shape_class="pouch", category="food",
                   dims=Dimensions(0.29, 0.085, depth=0.028), mass_kg=0.51, material="film", orientation="lying",
                   description="形は一般的な袋入りのスパゲッティ 500g（長さ 290 mm・幅 85 mm・厚さ 28 mm）で、寸法・質量は代表値。",
                   tags=["スパゲッティ", "パスタ", "乾めん", "1.6mm", "spaghetti", "pasta"], photos=["spaghetti"],
                   colors=Colors(label_base=navy), images=[front, back], faces={"front": 0, "back": 1})


def granola_bag() -> Product:
    W, H = 180.0, 270.0
    cream, orange, brown, berry = "#FFF4DE", "#E07B24", "#5A3418", "#B0234A"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 7, cream, seed=seed)
        c.gradient(0, 0, W, H, "#FFF8EA", "#F8E3B8")
        seal_crimp(c, 0, 0, W, 12, "#F3D9A4", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#EBC98A", 1.6)
        c.rect(0, 12, W, 30, fill=orange)
        return c

    c = base(1440)
    c.text(W / 2, 21, "ザクザク食感の朝ごはん", 7.0, "#FFFFFF", 800, max_w=W - 20)
    c.text(W / 2, 48, "フルーツ", 14, berry, 900)
    c.text(W / 2, 70, "グラノーラ", 20, brown, 900, max_w=W - 24)
    c.text(W / 2, 88, "FRUIT GRANOLA", 6.0, orange, 800, spacing=1.6)
    c.photo("granola", 16, 96, W - 16, 228, shape="round", radius=10, shadow=2, crop=(0.30, 0.03, 0.79, 0.70))
    c.ellipse(W - 60, 200, W - 10, 246, fill=berry)
    c.text(W - 35, 217, "6種の", 5.0, "#FFFFFF", 900)
    c.text(W - 35, 228, "フルーツ", 5.0, "#FFFFFF", 900)
    c.text(18, 234, "※写真は盛りつけ例です", 3.0, brown, 500, anchor="lm")
    c.rect(16, 240, 72, 252, fill=orange, radius=6)
    c.text(44, 246, "380g", 6.0, "#FFFFFF", 900)
    front = _pouch(c, 1440)

    b = base(1441)
    b.text(W / 2, 21, "フルーツグラノーラ 380g", 7.0, "#FFFFFF", 800)
    b.rect(12, 36, W - 12, H - 16, fill="#FFFFFF", radius=3)
    _back_panel(b, 17, 40, W - 17, H - 50, [
        ("名称", "シリアル食品"), ("原材料名", "オーツ麦、ドライフルーツ（レーズン、パパイヤ、りんご、いちご、クランベリー、パイナップル）、砂糖、植物油脂、米粉／酸化防止剤（ビタミンE）"),
        ("内容量", "380g"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 4.4,
        [("栄養成分表示 1食（50g）当たり", ""), ("エネルギー", "220kcal"), ("たんぱく質", "3.9g"), ("脂質", "7.8g"),
         ("炭水化物", "35.4g"), ("食塩相当量", "0.2g")],
        [("おいしい食べ方", "1食 50g を器に入れ、牛乳やヨーグルト 150ml をかけてお召し上がりください。"),
         ("ご注意", "開封後はチャックをしっかり閉め、お早めにお召し上がりください。")], orange)
    b.barcode(18, H - 46, 40, 24)
    b.recycle(W - 34, H - 34, 12, "プラ", orange, sub="袋")
    back = _pouch(b, 1441)
    return Product(slug="granola_bag", name="フルーツグラノーラ 380g", shape_class="pouch", category="food",
                   dims=Dimensions(0.27, 0.18, depth=0.07), mass_kg=0.40, material="film",
                   description="形は一般的な袋入りのグラノーラ（高さ 270 mm・幅 180 mm）で、寸法・質量は代表値。",
                   tags=["グラノーラ", "シリアル", "朝食", "フルーツ", "granola", "cereal"], photos=["granola"],
                   colors=Colors(label_base=cream), images=[front, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- カップのみそ汁


def cup_miso_soup() -> Product:
    form = forms.paper_cup(0.060, 0.090, 0.064, foot_h=0.004, label_margin=(0.002, 0.002))
    cream, brown, green, red = "#F7EEDD", "#6B3E1E", "#2E6B2F", "#A3221B"
    c = label_canvas(form, cream, seed=1450)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.pattern(0, 0, W, H, "waves", mix(cream, brown, 0.1), 5, 0.4)
    c.rect(0, 0, W, 8, fill=brown)
    c.rect(0, H - 6, W, H, fill=green)
    c.text(fx, 4.2, "即席みそ汁", 4.2, "#FFFFFF", 800)
    c.photo("miso_soup", fx - 36, 10, fx - 2, H - 9, shape="ellipse", feather=1.0, shadow=1.0,
            crop=(0.13, 0.08, 0.87, 0.88))
    c.text(fx + 16, 18, "とうふと", 5.0, brown, 900, max_w=30)
    c.text(fx + 16, 27, "わかめ", 6.0, green, 900, max_w=30)
    c.text(fx + 16, 36, "みそ汁", 6.0, brown, 900, max_w=30)
    c.text(fx, H - 3, "熱湯 160ml  1食", 2.6, "#FFFFFF", 700)
    c.text(fx + 16, 41.5, "※写真はイメージです", 1.6, brown, 500)
    c.text(0.5 * W, 4.2, "MISO SOUP", 3.6, "#FFFFFF", 800, spacing=0.6)
    bx = 0.25 * W
    back_info(c, bx - 30, 9.5, bx + 30, [
        ("名称", "即席みそ汁"), ("原材料名", "米みそ、乾燥とうふ、わかめ、ねぎ、かつおぶし粉末／調味料（アミノ酸等）"),
        ("内容量", "18g"), ("賞味期限", "フタに記載")], 1.4,
        [("栄養成分表示 1食当たり", ""), ("エネルギー", "52kcal"), ("たんぱく質", "3.4g"), ("食塩相当量", "1.8g")], brown,
        cream)
    c.barcode(0.5 * W - 10, 11, 20, 13)
    c.recycle(0.5 * W - 6, 33, 6, "紙", brown, sub="容器")
    c.recycle(0.5 * W + 6, 33, 6, "プラ", brown, sub="フタ")
    label = edge_shade(finish(c.array(), "paper", 1450), 6, 0.08)

    t = top_canvas(form, cream, seed=1451)
    d = t.w_mm
    t.ellipse(0.5, 0.5, d - 0.5, d - 0.5, fill=brown)
    t.ellipse(3, 3, d - 3, d - 3, fill=cream)
    t.text(d / 2, d * 0.30, "とうふとわかめ", 6.0, green, 900)
    t.text(d / 2, d * 0.45, "みそ汁", 11, brown, 900)
    steam(t, d / 2, d * 0.22, 12, 5, mix(brown, cream, 0.5), 0.5)
    t.text(d / 2, d * 0.60, "熱湯を内側の線まで注ぐだけ", 3.0, INK, 700)
    t.text(d / 2, d * 0.69, "賞味期限 2027.05.31", 3.0, INK, 700)
    t.polygon([(d / 2 - 5, d - 8), (d / 2 + 5, d - 8), (d / 2, d - 4)], fill=red)
    t.text(d / 2, d - 13, "ここからあける", 2.4, red, 800)
    top = finish(t.array(), "paper", 1451, 0.8)
    return Product(slug="cup_miso_soup", name="カップみそ汁 とうふとわかめ", category="food", mass_kg=0.03,
                   material="paper",
                   description="形は一般的なカップ入りの即席みそ汁（高さ 60 mm・上端径約 92 mm）で、寸法・質量は代表値。",
                   tags=["みそ汁", "即席みそ汁", "カップ", "インスタント", "miso soup", "instant soup"],
                   photos=["miso_soup"], colors=Colors(cap=cream, label_base=cream), **revolve(form, label=label, top=top))


PRODUCTS = {f.__name__: f for f in (natto_3pack, tofu_pack, yogurt_tub, pudding_cup, sliced_bread, green_tea_bag_box,
                                    rice_cracker_bag, gummy_candy_pouch, instant_ramen_5pack, spaghetti_pack,
                                    granola_bag, cup_miso_soup)}
