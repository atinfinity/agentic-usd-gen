"""架空の商品のデザイン: コンビニの食品（中食・菓子・冷凍）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import math

import numpy as np

from ..shapes.pouch import pouch_mesh
from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .food_fresh_snack import _back_panel, _pouch
from .paint import Canvas, edge_shade, finish, mix
from .products import INK, _box, _cyl, _face, _food, _food_photo, back_info, seal_crimp, steam

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _price_sticker(w: float, h: float, name: str, price: int, kcal: int, expiry: str, accent: str, seed: int,
                   heat: str | None = None):
    """お弁当・サラダのフタに貼る値札シール（ダミーのバーコード付き）。"""
    c = Canvas(w, h, 12, "#FFFFFF", seed)
    c.rect(0, 0, w, h * 0.27, fill=accent)
    c.text(w / 2, h * 0.135, name, h * 0.15, "#FFFFFF", 900, max_w=w - 6)
    c.text(4, h * 0.36, "消費期限", h * 0.075, INK, 700, anchor="lm")
    c.text(4, h * 0.47, expiry, h * 0.10, INK, 900, anchor="lm", max_w=w * 0.55)
    c.text(4, h * 0.58, f"熱量 {kcal}kcal", h * 0.075, INK, 700, anchor="lm")
    if heat:
        c.text(4, h * 0.68, heat, h * 0.07, accent, 800, anchor="lm", max_w=w * 0.55)
    c.rect(w * 0.60, h * 0.31, w - 3, h * 0.66, outline=accent, width=0.4, radius=1.0)
    c.text(w * 0.80 - 1.5, h * 0.38, "価格（税込）", h * 0.06, accent, 700)
    c.text(w * 0.80 - 1.5, h * 0.53, f"{price}円", h * 0.15, accent, 900, max_w=w * 0.36)
    c.barcode(4, h * 0.72, w * 0.42, h * 0.25)
    c.paragraph(w * 0.50, h * 0.74, w - 3, "要冷蔵（10℃以下）\n" + NOTICE, h * 0.045, INK, 500)
    return _face(c.array(), "paper", seed, 0.5)


# ---------------------------------------------------------------- お弁当


def bento_makunouchi() -> Product:
    """黒いトレー（箱）の区画にごはんとおかず（部品、上面に写真や断面）、透明なフタ（部品）と値札シール（部品）。"""
    W, D, H = 205.0, 155.0, 32.0
    black, rim, red, white = "#161616", "#2C2C2C", "#B71C1C", "#FFFFFF"
    s = 8

    def side(w: float, seed: int) -> Canvas:
        f = Canvas(w, H, s, black, seed)
        f.gradient(0, 0, w, H, "#3A3A3A", "#0E0E0E")
        f.pattern(0, 4, w, H - 2, "stripes", mix(black, white, 0.06), 3.0, 0.3)
        f.rect(0, 0, w, 2.0, fill=mix(rim, white, 0.15))  # 縁のフランジ
        return f

    fr, bk, rt, lf = side(W, 2201), side(W, 2202), side(D, 2203), side(D, 2204)

    tp = Canvas(W, D, s, black, 2205)
    tp.gradient(0, 0, W, D, "#383838", "#121212")
    tp.rect(3, 3, W - 3, D - 3, fill=black, radius=4)
    # 仕切りの区画（中身は上に載せた部品）
    for x0, y0, x1, y1 in ((7, 7, 99, D - 7), (105, 7, W - 7, 78), (105, 82, 150, D - 7), (153, 82, W - 7, 116),
                           (153, 119, W - 7, D - 7)):
        tp.rect(x0, y0, x1, y1, fill="#1E1E1E", radius=3)

    bt = Canvas(W, D, s, black, 2206)
    bt.gradient(0, 0, W, D, "#2A2A2A", "#101010")
    bt.rect(30, 14, W - 30, D - 14, fill=white, radius=2)
    back_info(bt, 34, 18, W - 34, [
        ("名称", "弁当"), ("原材料名", "ご飯、鶏肉の唐揚げ、焼き鮭、卵焼き、野菜の煮物、たくあん漬け、梅干し、黒ごま"
                                "／調味料（アミノ酸等）、pH調整剤、着色料（クチナシ）、（一部に小麦・卵・大豆・鶏肉・さけを含む）"),
        ("内容量", "1人前"), ("消費期限", "フタのシールに記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 4.0,
        [("栄養成分表示 1食当たり", ""), ("エネルギー", "812kcal"), ("たんぱく質", "31.2g"), ("脂質", "27.4g"),
         ("炭水化物", "110.6g"), ("食塩相当量", "3.6g")])
    imgs = [_face(c.array(), "plastic", 2207 + i, 0.5) for i, c in enumerate((fr, bk, rt, lf, tp, bt))]
    imgs.append(_price_sticker(88, 58, "幕の内弁当", 594, 812, "26.10.18 午前3時", red, 2214,
                               "温め 500W 1分40秒"))

    # 中身の上面の写真（7: ごはん、8〜10: からあげ、11: 焼き鮭、12: 卵焼きの断面）
    rice = Canvas(88, 137, 8, "#F4F1E8", 2215)
    rice.photo("cooked_rice", 0, 0, 88, 137, crop=(0.35, 0.25, 0.75, 0.80))
    for _ in range(40):  # 黒ごま
        x, y = rice.rng.uniform(8, 80), rice.rng.uniform(10, 127)
        rice.ellipse(x - 0.5, y - 0.3, x + 0.5, y + 0.3, fill="#111111")
    a = rice.array().astype(np.float32)  # 写真が暗めで灰色がかるので、炊いたごはんの白に寄せる
    imgs.append(finish(np.clip(a * 1.12 + 18, 0, 255).astype(np.uint8), "paper", 2215, 0.3))
    for k, crop in enumerate(((0.27, 0.06, 0.58, 0.45), (0.50, 0.05, 0.80, 0.40), (0.37, 0.55, 0.72, 0.90))):
        imgs.append(_food_photo("karaage", 32, 28, crop, 2216 + k))
    sal = Canvas(37, 55, 8, "#E9875E", 2219)
    sal.gradient(0, 0, 37, 55, "#EE9268", "#DE7A50")
    sal.rect(0, 0, 37, 5, fill="#C9603A")
    for k in range(5):
        y = 9 + k * 9
        sal.line([(2, y), (35, y + 4)], "#F7C3A5", 1.0)
    sal.rect(0, 50, 37, 55, fill="#A9A9A0")  # 皮
    imgs.append(_face(sal.array(), "paper", 2219, 0.4, 4))
    egg = Canvas(20, 28, 10, "#F4CF4A", 2220)
    egg.gradient(0, 0, 20, 28, "#F7D85E", "#E8BE36")
    for r in (8, 5, 2.5):
        egg.ellipse(10 - r, 14 - r * 1.3, 10 + r, 14 + r * 1.3, outline="#E0B22E", width=0.5)
    imgs.append(_face(egg.array(), "paper", 2220, 0.4, 4))

    def at(cx: float, cy: float) -> tuple[float, float]:  # 上面の画像の mm（左上が原点）→ トレーの中心からの m
        return (cx - W / 2) / 1000, (D / 2 - cy) / 1000

    z0 = H / 1000 - 0.001  # 区画の底（中身の置き面）
    parts = [_food("Rice", "bun", (0.090, 0.138, 0.012), (*at(53, 77.5), z0 + 0.006), "#F4F1E8", faces={"top": 7}),
             _food("Umeboshi", "dome", (0.016, 0.015, 0.008), (*at(53, 72), z0 + 0.010 + 0.004), "#9E1B2A",
                   "plastic"),
             _food("Baran", "box", (0.002, 0.140, 0.018), (*at(102, 77.5), z0 + 0.009), "#2E9D3A", "plastic")]
    for k in range(3):  # たくあん（ごはんの上に斜めに重ねる）
        parts.append(_food(f"Takuan{k}", "cylinder", (0.015, 0.015, 0.004), (*at(30 + k * 8, 112), z0 + 0.012 + k * 0.001),
                           "#E9C93A", rotation=(0, -18, 0)))
    for k, (cx, cy, rz) in enumerate(((122, 26, 10), (151, 22, -25), (180, 28, 40), (128, 58, -50), (158, 56, 15))):
        parts.append(_food(f"Karaage{k}", "bun", (0.032, 0.028, 0.022), (*at(cx, cy), z0 + 0.011), "#A8692F",
                           faces={"top": 8 + k % 3}, rotation=(0, 0, rz)))
    parts += [_food("Lemon", "cylinder", (0.020, 0.020, 0.004), (*at(186, 62), z0 + 0.012), "#F2D23C", "plastic",
                    rotation=(60, 0, 20)),
              _box("Salmon", (0.037, 0.055, 0.012), (*at(127.5, 117), z0 + 0.006), "#E9875E", "matte", {"top": 11},
                   collision=False)]
    for k in range(2):
        parts.append(_box(f"Tamagoyaki{k}", (0.020, 0.028, 0.016), (*at(166 + k * 22, 99), z0 + 0.008), "#F4CF4A",
                          "matte", {"top": 12}, collision=False))
    parts += [_food("Carrot", "cylinder", (0.015, 0.015, 0.008), (*at(163, 128), z0 + 0.004), "#E86F2C", rotation=(0, 0, 0)),
              _food("Shiitake", "dome", (0.019, 0.017, 0.008), (*at(181, 128), z0 + 0.004), "#5A3A22"),
              _food("Konnyaku", "box", (0.012, 0.012, 0.009), (*at(192, 140), z0 + 0.0045), "#7C7A76",
                    rotation=(0, 0, 30)),
              _food("Satoimo", "bun", (0.019, 0.014, 0.012), (*at(166, 141), z0 + 0.006), "#C8A060"),
              _food("Kinusaya", "box", (0.014, 0.005, 0.003), (*at(181, 141), z0 + 0.0015), "#5BAE3C",
                    rotation=(0, 0, -15))]
    for part in parts:  # ごはん・おかずは中身なので当たり判定なし
        part.collision = False
        part.material = "food"

    lid_h, lid_z0 = 0.024, H / 1000 - 0.002
    parts += [_box("Lid", (W / 1000 + 0.003, D / 1000 + 0.003, lid_h), (0, 0, lid_z0 + lid_h / 2), "#F2F6F8", "glass", thin_walled=True),
             _box("Sticker", (0.088, 0.058, 0.0006), (-0.052, -0.036, lid_z0 + lid_h + 0.0003), white, "matte",
                  {"top": 6}, collision=False)]
    return Product(slug="bento_makunouchi", name="幕の内弁当", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.52, material="plastic",
                   description="形は一般的なコンビニの幕の内弁当（黒いトレー 幅 205 mm・奥行き 155 mm・高さ 32 mm に、"
                               "高さ 24 mm の透明なフタをかぶせて値札シールを貼った形）で、寸法・質量は代表値。"
                               "ごはん・おかずは簡単な形に写真や色を付けた部品で、フタとシールも部品で表す。",
                   tags=["弁当", "幕の内弁当", "お弁当", "中食", "要冷蔵", "bento", "lunch box"],
                   photos=["cooked_rice", "karaage"], colors=Colors(label_base=black), images=imgs, faces=BOX_FACES,
                   parts=parts)


def salad_cup() -> Product:
    """透明なカップ（回転体）に盛った野菜（写真を貼った山の部品）、ドーム状の透明なフタ（部品）と値札シール（部品）。"""
    form = forms.paper_cup(0.075, 0.112, 0.086, lid_h=0.002, lid_overhang=0.0015, rim_h=0.003,
                           label_margin=(0.001, 0.001))
    green, leaf, red, white = "#2E7D32", "#7CB342", "#D84315", "#FFFFFF"
    c = label_canvas(form, "#DDEFD0", seed=2221)
    W, H = c.w_mm, c.h_mm
    # 透明な容器ごしに見える中身（写真）と、底のキャベツ
    c.photo("salad", 0, 0, W, H, crop=(0.10, 0.10, 0.90, 0.75))
    c.rect(0, H - 9, W, H, fill="#C9E39A")
    for _ in range(90):
        x, y = c.rng.uniform(0, W), c.rng.uniform(H - 9, H)
        c.ellipse(x - 1.6, y - 0.9, x + 1.6, y + 0.9, fill=c.rng.choice(["#9CCC65", "#DCEDC8", "#F5F5E0", "#E8732E"]))
    fx = 0.75 * W
    c.rect(fx - 26, 9, fx + 26, H - 12, fill=white, radius=3, outline=green, width=0.5)
    c.rect(fx - 26, 9, fx + 26, 19, fill=green, radius=3)
    c.text(fx, 14, "シャキシャキ野菜", 4.4, white, 800, max_w=48)
    c.text(fx, 27, "グリーンサラダ", 6.8, green, 900, max_w=48)
    c.text(fx, 36, "ごまドレッシング付", 3.8, red, 800, max_w=48)
    c.text(fx, 44, "GREEN SALAD", 3.0, leaf, 800, spacing=0.6)
    bx = 0.25 * W
    c.rect(bx - 30, 6, bx + 30, H - 10, fill=white, radius=2)
    back_info(c, bx - 28, 8, bx + 28, [
        ("名称", "サラダ"), ("原材料名", "レタス、キャベツ、トマト、にんじん、コーン、枝豆、ドレッシング（ごま、植物油脂、しょうゆ）"),
        ("消費期限", "フタに記載"), ("保存方法", "要冷蔵（10℃以下）")], 2.0)
    label = edge_shade(finish(c.array(), "plastic", 2221, 0.6), 4, 0.06)

    t = top_canvas(form, "#E8F2DE", seed=2222)
    d = t.w_mm
    t.ellipse(0.4, 0.4, d - 0.4, d - 0.4, fill="#D9E8CF")
    t.photo("salad", 3, 3, d - 3, d - 3, shape="ellipse", feather=1.5, crop=(0.06, 0.04, 0.94, 0.96))
    top = finish(t.array(), "plastic", 2222, 0.5)
    pk = Canvas(34, 24, 12, "#F3E2B8", 2224)  # ドレッシングの小袋
    pk.gradient(0, 0, 34, 24, "#F8EDCC", "#E9D5A0")
    pk.rect(1, 1, 33, 23, outline="#B88A3C", width=0.5, radius=2)
    pk.text(17, 10, "ごまドレ", 5.0, "#6B4A1E", 900)
    pk.text(17, 17, "SESAME", 2.6, "#8A6A3A", 800)
    sticker = _price_sticker(66, 42, "グリーンサラダ", 321, 98, "26.10.18 午後9時", green, 2223)

    r = revolve(form, label=label, top=top, body_fill="#A9C79A")
    r["images"].append(sticker)
    i_salad, i_pack = len(r["images"]), len(r["images"]) + 1
    r["images"] += [_food_photo("salad", 100, 100, (0.12, 0.08, 0.88, 0.92), 2225),
                    _face(pk.array(), "film", 2224, 0.5, 3)]
    Hm = form.height
    dome_h = 0.028
    # 盛った野菜（写真を貼った低い山）、ミニトマトとコーン、上に載せたドレッシングの小袋
    z0 = Hm - 0.003
    parts = [_food("Salad", "bun", (0.102, 0.102, 0.022), (0, 0, z0 + 0.011), "#7CB342", faces={"top": i_salad})]
    for k, (x, y) in enumerate(((0.024, 0.016), (-0.010, 0.030), (0.030, -0.014))):
        parts.append(_food(f"Tomato{k}", "dome", (0.020, 0.020, 0.010), (x, y, z0 + 0.018 + 0.005), "#D84315",
                           "plastic"))
    for k in range(8):
        a = k * 0.8
        parts.append(_food(f"Corn{k}", "dome", (0.007, 0.006, 0.004), (0.012 * math.cos(a) - 0.004,
                           0.012 * math.sin(a) + 0.004, z0 + 0.021 + 0.002), "#F2C230", "plastic"))
    parts.append(Part("Dressing", "box", [0.034, 0.024, 0.003], [-0.020, -0.014, z0 + 0.021], [6, -4, 18],
                      color="#F3E2B8", finish="plastic", faces={"top": i_pack}, collision=False))
    parts += [Part("Dome", "cylinder", [0.108, 0.108, dome_h], [0, 0, Hm - 0.001 + dome_h / 2], color="#F2F6F8",
                  finish="glass", thin_walled=True),
             _box("Sticker", (0.066, 0.042, 0.0006), (0, -0.018, Hm - 0.001 + dome_h + 0.0003), white, "matte",
                  {"top": 3}, collision=False)]
    return Product(slug="salad_cup", name="グリーンサラダ ごまドレッシング付", category="food", mass_kg=0.16,
                   material="plastic",
                   description="形は一般的なコンビニのカップサラダ（透明なカップ 上端径 112 mm・高さ 75 mm に、"
                               "高さ 28 mm の透明なドームのフタと値札シール）で、寸法・質量は代表値。盛った野菜は写真を貼った低い山、"
                               "ミニトマト・コーン・ドレッシングの小袋とフタ・シールは部品で表す。",
                   tags=["サラダ", "カップサラダ", "野菜", "中食", "要冷蔵", "salad", "salad cup"], photos=["salad"],
                   colors=Colors(cap="#F2F6F8", label_base="#DDEFD0"), parts=parts, **r)


# ---------------------------------------------------------------- カップ焼きそば


def cup_yakisoba() -> Product:
    """四角いカップ（箱）。上面がフタで、全体を透明なフィルム（部品）で包む。"""
    W, D, H = 152.0, 132.0, 56.0
    white, orange, brown, green, dark = "#FFFFFF", "#E65100", "#4E2A10", "#2E7D32", "#2B1608"
    s = 8

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFFFFF", "#F3EDE6")
        f.rect(0, 0, w, 6, fill=orange)
        f.rect(0, h - 3, w, h, fill=brown)
        return f

    fr = face(W, H, 2241)
    fr.photo("yakisoba", 4, 9, 58, H - 6, shape="round", radius=3, crop=(0.30, 0.28, 0.70, 0.78))
    fr.text(31, H - 8, "※写真はイメージです", 1.8, white, 600, stroke=0.2, stroke_fill="#333333")
    fr.text(104, 19, "ソース焼そば", 11, brown, 900, max_w=88)
    fr.text(104, 31, "濃厚ソース・青のり付", 4.4, orange, 800, max_w=88)
    fr.rect(66, 36, 142, 46, fill=orange, radius=5)
    fr.text(104, 41, "湯切り 3分  めん 100g", 4.4, white, 900, max_w=72)
    fr.text(104, 50, "即席カップめん  内容量 125g", 2.6, brown, 600)

    bk = face(W, H, 2242)
    y = back_info(bk, 4, 8, 96, [
        ("名称", "即席カップめん"), ("原材料名", "油揚げめん（小麦粉、植物油脂、食塩）、ソース（糖類、ソース、香辛料）、かやく（キャベツ、青のり）／調味料（アミノ酸等）"),
        ("内容量", "125g（めん 100g）"), ("賞味期限", "底面に記載")], 2.0,
        [("栄養成分表示 1食当たり", ""), ("エネルギー", "556kcal"), ("たんぱく質", "8.6g"), ("脂質", "22.4g"),
         ("炭水化物", "79.6g"), ("食塩相当量", "3.8g")])
    if y > H - 3:
        raise ValueError(f"裏面の表示がはみ出す（{y:.1f} mm）")
    bk.rect(100, 8, W - 4, 13, fill=orange, radius=1)
    bk.text(101.5, 10.5, "作り方", 2.8, white, 800, anchor="lm")
    bk.paragraph(101, 15, W - 5, "① フタを点線まで開け、ソースを取り出す。\n② 熱湯を内側の線まで注ぎ、3分待つ。\n"
                 "③ 湯切り口からお湯を捨て、ソースをよく混ぜる。", 2.5, INK, 500)
    bk.barcode(102, H - 21, 26, 15)
    bk.recycle(136, H - 14, 7, "プラ", orange, sub="容器")

    sides = []
    for k, seed in enumerate((2243, 2244)):
        sd = face(D, H, seed)
        sd.text(D / 2, 20, "ソース焼そば", 10, brown, 900, max_w=D - 10)
        sd.text(D / 2, 33, "YAKISOBA" if k == 0 else "熱湯 480ml  3分", 5.0, orange, 800, spacing=0.8 if k == 0 else 0)
        sd.text(D / 2, 44, "やけどに注意してください", 3.0, brown, 600)
        sides.append(sd)

    tp = Canvas(W, D, s, orange, 2245)
    tp.gradient(0, 0, W, D, "#F57C00", "#D84315")
    tp.pattern(0, 0, W, D, "waves", mix(orange, "#FFB74D", 0.4), 10, 0.5)
    tp.rect(3, 3, W - 3, D - 3, outline=white, width=0.8, radius=6)
    tp.photo("yakisoba", 10, 38, 92, D - 14, shape="round", radius=6, shadow=1.5, crop=(0.24, 0.22, 0.76, 0.84))
    tp.text(51, D - 8, "※写真は調理例です", 2.6, white, 600)
    tp.text(W / 2, 17, "ソース焼そば", 15, white, 900, stroke=0.8, stroke_fill=dark)
    tp.text(W / 2, 30, "SAUCE YAKISOBA", 4.6, "#FFE0B2", 800, spacing=1.2)
    tp.ellipse(98, 44, 142, 84, fill="#FFD54F")
    tp.text(120, 58, "大盛", 9.0, brown, 900)
    tp.text(120, 71, "めん 100g", 4.0, brown, 800)
    tp.rect(98, 90, W - 8, 110, fill=white, radius=3)
    tp.text(122, 96, "湯切り口", 4.0, green, 900)
    for k in range(6):
        tp.ellipse(104 + k * 6.4, 101, 107 + k * 6.4, 104, fill=green)
    tp.text(122, 107.5, "← ここからはがす", 2.6, INK, 700)
    tp.polygon([(W - 14, D - 12), (W - 4, D - 4), (W - 14, D - 4)], fill=white)
    steam(tp, 30, 37, 14, 6, "#FFE0B2", 0.6)

    bt = face(W, D, 2246)
    bt.text(W / 2, D / 2 - 8, "賞味期限 2027.04.15", 6.0, INK, 800)
    bt.text(W / 2, D / 2 + 6, NOTICE, 3.0, brown, 500, max_w=W - 12)
    imgs = [_face(c.array(), "paper", 2247 + i) for i, c in enumerate((fr, bk, *sides, tp, bt))]
    film = [_box("Film", (W / 1000 + 0.002, D / 1000 + 0.002, H / 1000 + 0.002), (0, 0, H / 2000), "#F2F6F8", "glass", thin_walled=True,
                 collision=False)]
    return Product(slug="cup_yakisoba", name="カップ焼そば ソース味 大盛", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.15, material="plastic",
                   description="形は一般的な四角いカップ焼きそば（幅 152 mm・奥行き 132 mm・高さ 56 mm）で、寸法・質量は代表値。"
                               "全体を包む透明なフィルムは部品で表す（コリジョンなし）。", parts=film,
                   tags=["焼きそば", "カップ焼きそば", "即席めん", "インスタント", "yakisoba", "instant noodles"],
                   photos=["yakisoba"], colors=Colors(label_base=orange), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- ホットスナック


def fried_chicken_box() -> Product:
    """紙の箱。正面の上にフタの差し込み（部品）。"""
    W, D, H = 95.0, 62.0, 42.0
    red, yellow, brown, white = "#C62828", "#FFC928", "#5D3A1A", "#FFFFFF"
    s = 12

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, yellow, seed)
        f.gradient(0, 0, w, h, "#FFD54F", "#FFB300")
        f.pattern(0, 0, w, h, "dots", mix(yellow, white, 0.4), 4.5, 0.5)
        f.rect(0, h - 4, w, h, fill=red)
        return f

    fr = face(W, H, 2261)
    fr.photo("karaage", 3, 4, 40, H - 7, shape="round", radius=3, shadow=0.8, crop=(0.22, 0.12, 0.72, 0.60))
    fr.text(68, 13, "からあげ", 10, red, 900, stroke=0.6, stroke_fill=white, max_w=50)
    fr.text(68, 23, "ジューシー しょうゆ味", 3.4, brown, 800, max_w=50)
    fr.rect(48, 27, 88, 34.5, fill=red, radius=3.7)
    fr.text(68, 30.8, "5個入", 4.4, white, 900)
    fr.text(W / 2, H - 2, "できたて・やけどに注意", 2.4, white, 700)

    bk = face(W, H, 2262)
    back_info(bk, 4, 3, W - 4, [
        ("名称", "鶏唐揚げ"), ("原材料名", "鶏肉（国産）、衣（小麦粉、でん粉、食塩）、しょうゆ、にんにく、しょうが、植物油"),
        ("内容量", "5個"), ("消費期限", "当日中")], 1.9)

    sides = []
    for k, seed in enumerate((2263, 2264)):
        sd = face(D, H, seed)
        sd.text(D / 2, 12, "KARAAGE", 6.0, red, 900, spacing=0.6)
        if k == 0:
            sd.text(D / 2, 22, "からあげ 5個入", 4.4, brown, 800)
            sd.barcode(D / 2 - 14, 25.5, 28, 11.5)
        else:
            sd.text(D / 2, 22, "熱量 312kcal", 4.4, brown, 800)
            sd.recycle(D / 2, 31, 6, "紙", brown)
        sides.append(sd)

    tp = face(W, D, 2265)
    tp.rect(3, 3, W - 3, D - 7, fill=white, radius=4)
    tp.photo("karaage", 6, 6, 44, D - 10, shape="ellipse", feather=1.2, crop=(0.18, 0.05, 0.82, 0.68))
    tp.text(70, 19, "からあげ", 9.0, red, 900, max_w=46)
    tp.text(70, 30, "揚げたて", 5.0, brown, 900)
    tp.text(70, 40, "やけどに注意してください", 2.4, INK, 700, max_w=46)
    tp.text(70, 46, NOTICE, 1.6, INK, 500, max_w=46)
    bt = face(W, D, 2266)
    bt.text(W / 2, D / 2 - 6, "からあげ 5個入", 6.0, red, 900)
    bt.text(W / 2, D / 2 + 6, "中身が熱いので開けるときに注意", 3.0, brown, 700)

    tab = Canvas(46, 9, 20, red, 2267)
    tab.gradient(0, 0, 46, 9, "#D32F2F", "#B71C1C")
    tab.text(23, 3.6, "▲ OPEN", 3.8, white, 900)
    tab.text(23, 7.3, "ここから開けてください", 1.6, "#FFE082", 700)
    imgs = [_face(c.array(), "paper", 2268 + i) for i, c in enumerate((fr, bk, *sides, tp, bt, tab))]
    parts = [_box("Flap", (0.046, 0.0008, 0.009), (0, -D / 2000 - 0.0006, H / 1000 - 0.0005), red, "matte",
                  {"front": 6, "back": 6}, collision=False)]
    return Product(slug="fried_chicken_box", name="からあげ 5個入（ホットスナック）", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.13, material="paper",
                   description="形は一般的なコンビニのホットスナックの紙箱（幅 95 mm・奥行き 62 mm・高さ 42 mm）で、寸法・質量は代表値。"
                               "正面上のフタの差し込みは部品で表す（コリジョンなし）。", parts=parts,
                   tags=["からあげ", "唐揚げ", "ホットスナック", "揚げ物", "惣菜", "karaage", "fried chicken"],
                   photos=["karaage"], colors=Colors(label_base=yellow), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 菓子パン・ゼリー飲料・アイス・飴（袋）


def melon_pan_bag() -> Product:
    """寝かせた袋。透明なフィルムごしにパンが見える。画像は横長（左右がシール）。"""
    L, Wd = 200.0, 165.0
    green, cream, white, brown = "#3E8E41", "#FBF4DA", "#FFFFFF", "#6B4A1E"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 8, cream, seed=seed)
        c.gradient(0, 0, L, Wd, "#F8F7F0", "#E9EEE6")
        c.pattern(0, 0, L, Wd, "dots", mix(cream, green, 0.15), 8, 0.6)
        seal_crimp(c, 0, 0, 12, Wd, "#E3E8DE", 1.4, vertical=True)
        seal_crimp(c, L - 12, 0, L, Wd, "#E3E8DE", 1.4, vertical=True)
        return c

    c = base(2281)
    c.photo("melon_pan", 40, 12, 160, Wd - 30, shape="ellipse", feather=4, crop=(0.47, 0.12, 0.95, 0.84))
    c.rect(14, 10, 62, 52, fill=green, radius=6)
    c.text(38, 22, "メロン", 9.0, white, 900)
    c.text(38, 34, "パン", 10, white, 900)
    c.text(38, 46, "MELON PAN", 3.4, "#DCEDC8", 800, spacing=0.4)
    c.rect(14, Wd - 26, L - 14, Wd - 10, fill=green, radius=4)
    c.text(L / 2, Wd - 18, "さくさくクッキー生地  1個入", 6.0, white, 900, max_w=L - 40)
    c.ellipse(L - 52, 14, L - 16, 50, fill="#FFD54F")
    c.text(L - 34, 27, "国産", 5.0, brown, 900)
    c.text(L - 34, 37, "小麦", 5.0, brown, 900)
    front = _pouch(c, 2281, 0.8, 16)

    b = base(2282)
    b.photo("melon_pan", 110, 14, 186, Wd - 14, shape="ellipse", feather=4, crop=(0.47, 0.12, 0.95, 0.84))
    b.rect(16, 10, 108, Wd - 10, fill=white, radius=3)
    _back_panel(b, 19, 13, 105, Wd - 40, [
        ("名称", "菓子パン"), ("原材料名", "小麦粉（国産）、砂糖、マーガリン、卵、ショートニング、パン酵母、食塩、乳等を主要原料とする食品／香料、乳化剤"),
        ("内容量", "1個"), ("消費期限", "右下に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.0,
        [("栄養成分表示 1個当たり", ""), ("エネルギー", "382kcal"), ("たんぱく質", "7.1g"), ("脂質", "12.8g"),
         ("炭水化物", "59.6g"), ("食塩相当量", "0.6g")], [], green)
    b.barcode(20, Wd - 36, 34, 22)
    b.recycle(68, Wd - 26, 10, "プラ", green, sub="袋")
    b.text(150, Wd - 8, "消費期限 26.10.20", 3.6, INK, 800)
    back = _pouch(b, 2282, 0.8, 16)
    return Product(slug="melon_pan_bag", name="メロンパン 1個入", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.06), mass_kg=0.10, material="film", orientation="lying",
                   description="形は一般的な袋入りの菓子パン（長さ 200 mm・幅 165 mm・厚さ 60 mm）で、寸法・質量は代表値。",
                   tags=["メロンパン", "菓子パン", "パン", "melon pan", "sweet bun", "bread"], photos=["melon_pan"],
                   colors=Colors(label_base=cream), images=[front, back], faces={"front": 0, "back": 1})


def jelly_drink_pouch() -> Product:
    """立てた袋の上に口（スパウト）とキャップ（部品）。"""
    W, H, depth = 95.0, 150.0, 0.032
    peach, pink, white, red = "#FFE3D6", "#F06292", "#FFFFFF", "#C2185B"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, peach, seed=seed)
        c.gradient(0, 0, W, H, "#FFF3EC", "#FFCDB8")
        c.pattern(0, 0, W, H, "waves", mix(peach, white, 0.5), 8, 0.6)
        seal_crimp(c, 0, 0, W, 10, "#FFD6C4", 1.2)
        seal_crimp(c, 0, H - 10, W, H, "#FFC2A8", 1.2)
        return c

    c = base(2301)
    c.text(W / 2, 22, "ゼリー飲料", 9.0, red, 900, stroke=0.6, stroke_fill=white)
    c.text(W / 2, 34, "白桃味", 12, pink, 900, stroke=0.8, stroke_fill=white)
    c.photo("peach", 8, 42, W - 8, 100, shape="ellipse", feather=2.5, crop=(0.30, 0.18, 0.68, 0.86))
    c.rect(10, 104, W - 10, 116, fill=red, radius=6)
    c.text(W / 2, 110, "エネルギー 180kcal", 5.0, white, 900)
    c.text(W / 2, 123, "ビタミンC 配合", 4.4, red, 800)
    c.text(W / 2, 132, "180g", 6.0, red, 900)
    c.text(W / 2, 138.5, "※写真はイメージです", 2.0, mix(red, white, 0.3), 500)
    front = _pouch(c, 2301, 0.9, 16)

    b = base(2302)
    b.text(W / 2, 16, "ゼリー飲料 白桃味 180g", 4.0, red, 900)
    b.rect(6, 20, W - 6, H - 12, fill=white, radius=2)
    _back_panel(b, 9, 22.5, W - 9, H - 34, [
        ("名称", "清涼飲料水"), ("原材料名", "果糖ぶどう糖液糖、もも果汁、砂糖／ゲル化剤（増粘多糖類）、酸味料、ビタミンC、香料"),
        ("内容量", "180g"), ("賞味期限", "キャップに記載"), ("保存方法", "直射日光・高温を避けて保存")], 2.8,
        [("栄養成分表示 1袋当たり", ""), ("エネルギー", "180kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
         ("炭水化物", "45.0g"), ("食塩相当量", "0.1g")],
        [("ご注意", "よく振ってからお飲みください。容器を温めないでください。")], pink)
    b.barcode(10, H - 32, 30, 18)
    b.recycle(W - 22, H - 23, 8, "プラ", red, sub="容器")
    back = _pouch(b, 2302, 0.9, 16)

    top = pouch_mesh(W / 1000, H / 1000, depth)["size"][2]  # 膨らんだ袋の上端 z
    parts = [_box("Fitment", (0.030, 0.009, 0.011), (0, 0, top - 0.0035), "#F7F7F5", "plastic"),
             _cyl("Spout", (0.0105, 0.0105, 0.010), (0, 0, top + 0.006), "#F7F7F5", "plastic"),
             _cyl("CapRing", (0.026, 0.026, 0.003), (0, 0, top + 0.0115), mix(pink, white, 0.3), "plastic"),
             _cyl("Cap", (0.024, 0.024, 0.020), (0, 0, top + 0.023), pink, "plastic")]
    return Product(slug="jelly_drink_pouch", name="ゼリー飲料 白桃味 180g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=depth), mass_kg=0.19, material="film", capacity_ml=180,
                   description="形は一般的な口付きパウチのゼリー飲料（袋 高さ 150 mm・幅 95 mm に、口と直径 24 mm のキャップを足した"
                               "全高 約 180 mm）で、寸法・質量は代表値。口とキャップは部品で表す。",
                   tags=["ゼリー飲料", "ゼリー", "パウチ", "白桃", "jelly drink", "spout pouch"], photos=["peach"],
                   colors=Colors(label_base=peach), images=[front, back], faces={"front": 0, "back": 1}, parts=parts)


def ice_bar_bag() -> Product:
    """寝かせた細長い袋（棒付きアイス）。画像は横長（左右がシール）。"""
    L, Wd = 195.0, 72.0
    blue, sky, white, navy = "#1E88E5", "#BBDEFB", "#FFFFFF", "#0D3C78"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 10, blue, seed=seed)
        c.gradient(0, 0, L, Wd, "#42A5F5", "#1565C0")
        c.pattern(0, 0, L, Wd, "dots", mix(blue, white, 0.35), 6, 0.6)
        seal_crimp(c, 0, 0, 10, Wd, "#64B5F6", 1.2, vertical=True)
        seal_crimp(c, L - 10, 0, L, Wd, "#1565C0", 1.2, vertical=True)
        return c

    def bar(c: Canvas, x0: float):
        """アイスバーの絵（棒は左）。"""
        c.rect(x0, Wd / 2 - 3.5, x0 + 34, Wd / 2 + 3.5, fill="#E8D2A6", radius=2)
        c.rect(x0 + 26, 12, x0 + 96, Wd - 12, fill="#8FD3F7", radius=12, outline=white, width=0.8)
        c.rect(x0 + 32, 16, x0 + 90, 26, fill="#C6ECFD", radius=5)
        for _ in range(28):
            x, y = c.rng.uniform(x0 + 32, x0 + 90), c.rng.uniform(20, Wd - 18)
            r = c.rng.uniform(0.5, 1.4)
            c.ellipse(x - r, y - r, x + r, y + r, fill=c.rng.choice([white, "#D9F2FF", "#5EC0EE"]))

    c = base(2321)
    bar(c, 14)
    c.text(150, 18, "ソーダ", 11, white, 900, stroke=0.7, stroke_fill=navy)
    c.text(150, 33, "アイスバー", 9.0, white, 900, stroke=0.6, stroke_fill=navy, max_w=66)
    c.text(150, 44, "SODA ICE BAR", 3.8, sky, 800, spacing=0.8)
    c.rect(124, 49, 176, 58, fill=white, radius=4.5)
    c.text(150, 53.5, "氷菓  1本 65ml", 3.6, blue, 900)
    c.text(150, 63, "※イラストはイメージです", 1.8, white, 500)
    front = _pouch(c, 2321, 0.8, 14)

    b = base(2322)
    b.rect(14, 6, 118, Wd - 6, fill=white, radius=3)
    back_info(b, 17, 8.5, 115, [
        ("種類別", "氷菓"), ("原材料名", "砂糖、ぶどう糖果糖液糖、水あめ／香料、安定剤（増粘多糖類）、着色料（スピルリナ青）"),
        ("内容量", "65ml"), ("保存方法", "要冷凍（-18℃以下）")], 2.6,
        [("栄養成分表示 1本当たり", ""), ("エネルギー", "68kcal"), ("炭水化物", "17.0g"), ("食塩相当量", "0g")])
    b.barcode(124, 9, 30, 18)
    b.recycle(170, 18, 10, "プラ", white, sub="袋")
    b.text(150, 40, "ご家庭では -18℃以下で保存", 3.2, white, 800)
    b.text(150, 48, "一度溶けたものを再び凍らせると", 2.6, white, 600)
    b.text(150, 53, "品質が変わることがあります", 2.6, white, 600)
    b.text(150, 62, "ソーダアイスバー", 4.4, white, 900)
    back = _pouch(b, 2322, 0.8, 14)
    return Product(slug="ice_bar_bag", name="ソーダアイスバー", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.026), mass_kg=0.07, material="film", orientation="lying",
                   description="形は一般的な袋入りの棒付きアイス（長さ 195 mm・幅 72 mm・厚さ 26 mm）で、寸法・質量は代表値。",
                   tags=["アイス", "アイスバー", "氷菓", "冷凍", "要冷凍", "ice bar", "popsicle"], photos=[],
                   colors=Colors(label_base=blue), images=[front, back], faces={"front": 0, "back": 1})


def candy_bag() -> Product:
    W, H = 150.0, 195.0
    amber, gold, brown, white, yellow = "#F2A922", "#FFE08A", "#5A3208", "#FFFFFF", "#FFF35A"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, gold, seed=seed)
        c.gradient(0, 0, W, H, "#FFF0B8", "#F7C548")
        c.pattern(0, 0, W, H, "stripes", mix(gold, white, 0.4), 7, 0.6)
        seal_crimp(c, 0, 0, W, 11, "#F7D46A", 1.4)
        seal_crimp(c, 0, H - 11, W, H, "#E9B23A", 1.4)
        c.rect(0, 11, W, 14, fill=brown)
        c.rect(0, H - 14, W, H - 11, fill=brown)
        return c

    def candy(c: Canvas, cx: float, cy: float, r: float):
        """個包装の飴（透明な包みの両端をひねった形）。"""
        for sgn in (-1, 1):
            x = cx + sgn * r
            c.polygon([(x, cy), (x + sgn * r * 0.8, cy - r * 0.55), (x + sgn * r * 0.8, cy + r * 0.55)],
                      fill=mix(white, gold, 0.3))
        c.ellipse(cx - r * 1.05, cy - r * 0.85, cx + r * 1.05, cy + r * 0.85, fill=mix(white, gold, 0.25))
        c.ellipse(cx - r * 0.85, cy - r * 0.68, cx + r * 0.85, cy + r * 0.68, fill=amber)
        c.ellipse(cx - r * 0.5, cy - r * 0.5, cx - r * 0.05, cy - r * 0.15, fill=mix(amber, white, 0.6))

    c = base(2341)
    c.photo("lemon", 70, 92, W - 6, 162, shape="ellipse", feather=3, crop=(0.10, 0.06, 0.92, 0.94))
    c.text(W / 2, 30, "はちみつレモン", 10, brown, 900, max_w=W - 20)
    c.text(W / 2, 52, "のど飴", 22, brown, 900, stroke=1.0, stroke_fill=white)
    c.text(W / 2, 68, "HONEY LEMON CANDY", 4.6, brown, 800, spacing=1.0)
    for cx, cy, r in ((34, 98, 10), (52, 122, 11), (28, 140, 9), (58, 150, 9), (96, 165, 8)):
        candy(c, cx, cy, r)
    c.ellipse(W - 44, 72, W - 8, 104, fill=yellow, outline=brown, width=0.5)
    c.text(W - 26, 84, "個包装", 4.0, brown, 900)
    c.text(W - 26, 93, "ハーブ", 3.6, brown, 800)
    c.text(W / 2, 172, "※写真はイメージです", 2.6, brown, 500)
    c.rect(W / 2 - 24, 175, W / 2 + 24, 182, fill=brown, radius=3.5)
    c.text(W / 2, 178.5, "80g", 4.4, white, 900)
    front = _pouch(c, 2341, 0.9, 18)

    b = base(2342)
    b.text(W / 2, 22, "はちみつレモンのど飴  80g", 5.0, brown, 900)
    b.rect(10, 28, W - 10, H - 17, fill=white, radius=3)
    _back_panel(b, 14, 31, W - 14, H - 46, [
        ("名称", "キャンデー"), ("原材料名", "砂糖、水あめ、はちみつ、レモン果汁、ハーブエキス／酸味料、香料、着色料（カラメル）"),
        ("内容量", "80g（個包装紙込み）"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.8,
        [("栄養成分表示 1粒（4g）当たり", ""), ("エネルギー", "15kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
         ("炭水化物", "3.8g"), ("食塩相当量", "0g")],
        [("ご注意", "小さなお子様は、のどにつまらせないようご注意ください。")], amber)
    b.barcode(16, H - 43, 36, 22)
    b.recycle(W - 30, H - 32, 11, "プラ", brown, sub="袋・個包装")
    back = _pouch(b, 2342, 0.9, 18)
    return Product(slug="candy_bag", name="はちみつレモンのど飴 80g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.04), mass_kg=0.09, material="film",
                   description="形は一般的な袋入りの個包装のど飴（高さ 195 mm・幅 150 mm）で、寸法・質量は代表値。",
                   tags=["のど飴", "飴", "キャンディ", "はちみつ", "レモン", "お菓子", "candy", "throat lozenge"],
                   photos=["lemon"], colors=Colors(label_base=gold), images=[front, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- チルド


def processed_cheese_6p() -> Product:
    """平たい丸箱（回転体）。開け口テープのつまみ（部品）。"""
    H, D, lid_h = 0.024, 0.108, 0.004
    form = forms.tin(H, D, lid_h=lid_h)
    blue, navy, red, cream, white = "#1565C0", "#0D2E5C", "#D32F2F", "#FFE9A8", "#FFFFFF"
    c = label_canvas(form, blue, seed=2361)
    W, Hl = c.w_mm, c.h_mm
    c.gradient(0, 0, W, Hl, "#1E88E5", "#0D47A1")
    c.rect(0, Hl * 0.42, W, Hl * 0.56, fill=red)  # 開け口テープ
    for k in range(4):
        x = (k + 0.5) * W / 4
        c.text(x, Hl * 0.22, "6P チーズ", Hl * 0.30, white, 900, max_w=W / 4 - 8)
        c.text(x, Hl * 0.49, "開け口 ← テープを引いてください", Hl * 0.10, white, 700, max_w=W / 4 - 8)
        c.text(x, Hl * 0.78, ["6個入 108g", "プロセスチーズ", "要冷蔵 10℃以下", "PROCESSED CHEESE"][k], Hl * 0.20,
               cream, 800, max_w=W / 4 - 8)
    label = edge_shade(finish(c.array(), "paper", 2361, 0.6), 3, 0.06)

    t = top_canvas(form, blue, seed=2362)
    d = t.w_mm
    t.ellipse(0.3, 0.3, d - 0.3, d - 0.3, fill=blue)
    t.ellipse(3, 3, d - 3, d - 3, fill="#1976D2", outline=white, width=0.6)
    cx, cy, R = d / 2, d * 0.56, d * 0.27
    for k in range(6):  # 6 個の扇形のチーズ（銀紙の縁）
        a0, a1 = math.radians(k * 60 - 90 + 3), math.radians(k * 60 - 30 - 3)
        pts = [(cx + 1.2 * math.cos((a0 + a1) / 2), cy + 1.2 * math.sin((a0 + a1) / 2))]
        pts += [(cx + R * math.cos(a0 + (a1 - a0) * i / 12), cy + R * math.sin(a0 + (a1 - a0) * i / 12))
                for i in range(13)]
        t.polygon(pts, fill="#C9CED6")
        inner = [(cx + 0.85 * (x - cx), cy + 0.85 * (y - cy)) for x, y in pts]
        t.polygon(inner, fill=cream if k else "#FFF4CF")
    t.text(d / 2, d * 0.15, "6P チーズ", 11, white, 900, stroke=0.6, stroke_fill=navy)
    t.text(d / 2, d * 0.25, "プロセスチーズ  6個入", 3.6, cream, 800)
    t.rect(d * 0.62, d * 0.76, d * 0.82, d * 0.84, fill=red, radius=1.5)
    t.text(d * 0.72, d * 0.80, "108g", 3.0, white, 900)
    t.text(d / 2, d * 0.93, "賞味期限 2027.01.10", 2.6, white, 700)
    top = finish(t.array(), "paper", 2362, 0.6)

    R0 = D / 2
    tab = [_box("TearTab", (0.010, 0.006, 0.0025), (0, -(R0 + 0.002), H - lid_h - 0.010), red, "matte",
                collision=False)]
    return Product(slug="processed_cheese_6p", name="6P チーズ 108g", category="food", mass_kg=0.12, material="paper",
                   description="形は一般的な丸箱入りの 6P のプロセスチーズ（直径 108 mm・高さ 24 mm）で、寸法・質量は代表値。"
                               "開け口テープのつまみは部品で表す（コリジョンなし）。",
                   tags=["チーズ", "プロセスチーズ", "6P", "乳製品", "要冷蔵", "cheese", "processed cheese"], photos=[],
                   colors=Colors(cap=blue, label_base=blue), parts=tab, **revolve(form, label=label, top=top))


def fish_sausage_4pack() -> Product:
    """横にした 4 本のソーセージ（円柱、両端に金具）を、印刷した紙の帯で束ねたもの。"""
    sd, sl, gap = 0.022, 0.160, 0.0002
    n = 4
    BW, BD, BH = 75.0, (n * (sd + gap) + 0.002) * 1000, sd * 1000 + 1.6
    orange, red, white, navy, yellow = "#E8622A", "#C62828", "#FFFFFF", "#173B66", "#FFD54F"
    s = 12

    def band(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFFFFF", "#E8F0FA")
        f.rect(0, 0, w, min(h, 5), fill=navy)
        f.rect(0, max(0, h - 5), w, h, fill=navy)
        return f

    tp = band(BW, BD, 2381)
    tp.pattern(0, 6, BW, BD - 6, "waves", mix(white, navy, 0.10), 7, 0.4)
    tp.text(BW / 2, 15, "魚肉", 9.0, red, 900)
    tp.text(BW / 2, 28, "ソーセージ", 10, navy, 900, max_w=BW - 8)
    tp.text(BW / 2, 37, "FISH SAUSAGE", 3.4, red, 800, spacing=0.6)
    for k in range(3):  # ソーセージの絵
        y = 46 + k * 7.5
        tp.rect(12, y, BW - 12, y + 6, fill=orange, radius=3)
        tp.rect(14, y + 1, BW - 14, y + 2.2, fill=mix(orange, white, 0.4), radius=1)
    tp.ellipse(BW - 30, 64, BW - 4, BD - 7, fill=yellow)
    tp.text(BW - 17, 72, "4本", 6.0, red, 900)
    tp.text(BW - 17, 80, "束", 4.4, red, 900)
    tp.text(26, 74, "そのまま", 4.4, navy, 900)
    tp.text(26, 81, "食べられる", 4.0, navy, 900)
    bt = band(BW, BD, 2382)
    back_info(bt, 4, 7, BW - 4, [
        ("名称", "魚肉ソーセージ"), ("原材料名", "魚肉（たら、いとより）、植物油脂、でん粉、砂糖、食塩／調味料（アミノ酸等）、着色料（紅麹）"),
        ("内容量", "280g（70g×4本）"), ("賞味期限", "帯の側面に記載"), ("保存方法", "常温で保存")], 2.0,
        [("栄養成分表示 1本当たり", ""), ("エネルギー", "112kcal"), ("たんぱく質", "8.2g"), ("脂質", "4.6g"),
         ("炭水化物", "9.4g"), ("食塩相当量", "1.4g")], navy)
    fr = band(BW, BH, 2383)
    fr.text(BW / 2, BH / 2, "魚肉ソーセージ 4本", 6.0, navy, 900)
    bk = band(BW, BH, 2384)
    bk.text(BW / 2, BH / 2, "賞味期限 2027.03.01", 4.4, INK, 800)
    sides = []
    for k, seed in enumerate((2385, 2386)):
        f = band(BD, BH, seed)
        if k == 0:
            f.barcode(BD / 2 - 18, 5.4, 36, BH - 10.8)
        else:
            f.text(BD / 2, BH / 2, "70g × 4本", 6.0, red, 900)
        sides.append(f)
    imgs = [_face(c.array(), "paper", 2387 + i) for i, c in enumerate((tp, bt, fr, bk, *sides))]

    parts = []
    y0 = -(n - 1) / 2 * (sd + gap)
    for i in range(n):
        y = y0 + i * (sd + gap)
        parts.append(Part(f"Sausage{i}", "cylinder", [sd, sd, sl], [0, y, sd / 2], [0, 90, 0], color=orange,
                          finish="plastic", material="food"))
        for sgn in (-1, 1):
            parts.append(Part(f"Clip{i}{'LR'[sgn > 0]}", "cylinder", [0.006, 0.006, 0.007],
                              [sgn * (sl / 2 + 0.0030), y, sd / 2], [0, 90, 0], color="#B8BCC0", finish="metal"))
    parts.append(_box("Band", (BW / 1000, BD / 1000, BH / 1000), (0, 0, BH / 2000), white, "matte",
                      {"top": 0, "bottom": 1, "front": 2, "back": 3, "right": 4, "left": 5}))
    total_w = sl + 2 * (0.0030 + 0.0035)
    return Product(slug="fish_sausage_4pack", name="魚肉ソーセージ 4本束", shape_class="assembly", category="food",
                   dims=Dimensions(round(BH / 1000, 4), round(total_w, 4), depth=round(BD / 1000, 4)), mass_kg=0.29,
                   material="film",
                   description="形は一般的な魚肉ソーセージの 4 本束（1 本 直径 22 mm・長さ 160 mm に両端の金具、"
                               "中央を幅 75 mm の印刷した紙の帯で束ねた形）で、寸法・質量は代表値。",
                   tags=["魚肉ソーセージ", "ソーセージ", "練り物", "おつまみ", "fish sausage", "sausage"], photos=[],
                   colors=Colors(label_base=orange), images=imgs, parts=parts)


PRODUCTS = {f.__name__: f for f in (bento_makunouchi, salad_cup, cup_yakisoba, fried_chicken_box, melon_pan_bag,
                                    jelly_drink_pouch, ice_bar_bag, candy_bag, processed_cheese_6p, fish_sausage_4pack)}
