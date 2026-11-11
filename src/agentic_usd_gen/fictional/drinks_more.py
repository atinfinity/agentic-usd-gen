"""架空の商品のデザイン: コンビニの飲料と、レジまわりの小物（カップ酒・ワイン・紙パック・ホットコーヒー・ライター・コミック）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
形・寸法・色・部品構成は、各関数の docstring に書いた CC0 / パブリックドメインの写真（Wikimedia Commons）を参考にした。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .conv_drinks import ALCOHOL_NOTE, _alcohol_mark
from .forms import RevolveForm, _arc
from .paint import Canvas, finish, mix
from .products import INK, steam, _bottle_back, _box, _can_top, _face, back_info

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _faces(canvases, kind: str, seed: int, strength: float = 0.8) -> list:
    """箱の面（渡した順）を仕上げる。"""
    return [_face(c.array(), kind, seed + i, strength) for i, c in enumerate(canvases)]


# ---------------------------------------------------------------- カップ酒


def _sake_cup(H: float, D: float, *, cap_h: float) -> RevolveForm:
    """カップ酒のガラスのコップ（少し上広がりの円筒、口の縁は丸い玉縁）と、引き開けるアルミのふた。"""
    R, Rb = D / 2, D / 2 * 0.92
    cap_z = H - cap_h
    body = [(0.0, Rb * 0.90)] + _arc(0.0005, 0.006, Rb * 0.95, Rb, 8, "out")[1:]
    body += [(cap_z - 0.006, R)] + _arc(cap_z - 0.005, cap_z, R, R - 0.0008, 6, "cos")[1:]
    cap = [(cap_z, R + 0.0004), (H - 0.0010, R + 0.0004), (H, R - 0.0012)]
    return RevolveForm(body, cap, (0.026, 0.074), cap_z - 0.016)


def sake_cup_180ml() -> Product:
    """カップ酒 180ml（ガラスのコップに金属の引き開けぶた、中身は無色に近い日本酒）。

    参考: https://commons.wikimedia.org/wiki/File:Sake_of_Yoshinoya.jpg（CC0）
    """
    form = _sake_cup(0.108, 0.062, cap_h=0.006)
    white, navy, red = "#FFFFFF", "#1C2A55", "#C3252C"
    c = label_canvas(form, white, seed=5001)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#EEF1F6")
    c.rect(0, 0, W, 3, fill=navy)
    c.rect(0, H - 3, W, H, fill=navy)
    c.rect(fx - 15, 5, fx + 15, 43, fill=white, outline=navy, width=0.5)
    c.ellipse(fx + 5, 25, fx + 12, 32, fill=red)
    c.vtext(fx + 8.5, 8, "上撰", 5.2, red, 900, gap=0.02)
    c.vtext(fx - 4, 8, "清酒", 11.5, navy, 900, gap=0.02)
    c.text(fx, 39, "CUP SAKE", 2.6, navy, 800, spacing=0.5)
    c.text(fx, H - 1.5, "180ml", 2.0, white, 800)
    c.text(fx - 26, 24, "辛口", 4.0, navy, 900)
    c.text(fx + 26, 24, "本醸造", 3.6, navy, 900)
    _alcohol_mark(c, fx + 26, 36, 6.5)
    bx = 0.25 * W
    back_info(c, bx - 22, 5, bx + 22, [("品目", "日本酒"), ("原材料名", "米（国産）、米こうじ（国産米）、醸造アルコール"),
                                       ("内容量", "180ml"), ("アルコール分", "15度")], 1.45, None, navy)
    c.paragraph(bx - 22, 34, bx + 22, ALCOHOL_NOTE, 1.25, navy, 600)
    c.barcode(0.5 * W - 9, 26, 18, 11)
    c.recycle(0.04 * W, 34, 5.5, "アルミ", navy, kind="can", sub="ふた")
    c.pattern(0, H - 9, W, H - 3, "waves", mix(navy, white, 0.6), 3.0, 0.4)
    label = finish(c.array(), "film", 5001, 0.4)

    t = top_canvas(form, "#C8CCD0", seed=5002)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#DDE0E3", "#A9AEB3")
    t.ellipse(0.8, 0.8, d - 0.8, d - 0.8, outline="#8C9196", width=0.8)
    t.ellipse(d * 0.12, d * 0.12, d * 0.88, d * 0.88, outline="#C2C6CA", width=0.5)
    t.rect(d / 2 - 7, d * 0.74, d / 2 + 7, d * 0.94, fill="#C9CDD1", outline="#868B90", width=0.5, radius=4)  # 引き手
    t.ellipse(d / 2 - 4, d * 0.79, d / 2 + 4, d * 0.89, fill="#A5AAAF")
    t.text(d / 2, d * 0.38, "清酒", 7.0, navy, 900)
    t.text(d / 2, d * 0.55, "ここを引いてあける", 2.4, red, 800)
    top = finish(t.array(), "metal", 5002, 0.6)
    sake = "#F3EED6"
    return Product(slug="sake_cup_180ml", name="カップ酒 本醸造 180ml", category="beverage", mass_kg=0.31,
                   capacity_ml=180, material="glass",
                   description="形は一般的な 180ml のカップ酒（ガラスのコップ、高さ 108 mm・口径 62 mm、アルミの引き開けぶた）で、寸法・質量は代表値。"
                               "コップの胴に印刷の帯があり、上下のすき間から無色に近い中身が見える。",
                   tags=["カップ酒", "日本酒", "清酒", "お酒", "酒類", "ガラス", "sake", "cup sake", "glass cup", "alcohol"],
                   photos=[], colors=Colors(cap="#C8CCD0", liquid=sake, label_base=white, liquid_turbidity=0.0),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=sake))


# ---------------------------------------------------------------- 赤ワイン


def _wine_bottle(H: float, D: float, *, cap_h: float, cap_r: float, neck_r: float) -> RevolveForm:
    """ボルドー型のワインボトル。底の丸み → 直胴 → いかり肩 → 長い首 → ねじ蓋（ロングスカート）。"""
    R = D / 2
    cap_z = H - cap_h
    sh_z = 0.62 * H
    body = [(0.0, R * 0.86)] + _arc(0.0005, 0.007, R * 0.92, R, 10, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, sh_z + 0.040, R, neck_r * 1.08, 30, "cos")[1:]
    body += [(cap_z - 0.004, neck_r), (cap_z, neck_r)]
    cap = [(cap_z, cap_r), (H - 0.0012, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, (0.045, 0.150), None)


def red_wine_bottle_720ml() -> Product:
    """赤ワイン 720ml（濃い緑のガラス瓶・ねじ蓋）。

    参考: https://commons.wikimedia.org/wiki/File:Bottle_and_glass_of_red_wine.jpg（CC0）、
    https://commons.wikimedia.org/wiki/File:BVS_Screwcap_30x60.jpg（CC0、30 × 60 mm のねじ蓋）。
    ラベルの写真: drk_grapes（https://commons.wikimedia.org/wiki/File:Red_grapes_with_the_leaves.jpg、CC0）
    """
    form = _wine_bottle(0.290, 0.075, cap_h=0.060, cap_r=0.0152, neck_r=0.0140)
    cream, wine, gold, green = "#F4EEDF", "#6A1424", "#B08A3E", "#1E3A26"
    c = label_canvas(form, cream, seed=5011)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FAF6EC", "#EADFC6")
    c.rect(fx - 40, 0, fx + 40, H, fill=cream)
    c.rect(fx - 38, 3, fx + 38, H - 3, outline=gold, width=0.5)
    c.photo("drk_grapes", fx - 20, 8, fx + 20, 52, shape="ellipse", crop=(0.15, 0.08, 0.85, 0.85), feather=1.0)
    c.text(fx, 62, "VINO ROSSO", 6.4, wine, 900, spacing=1.0)
    c.text(fx, 74, "赤ワイン", 8.0, INK, 900)
    c.text(fx, 83, "ミディアムボディ  辛口", 3.4, wine, 800)
    c.rect(fx - 26, 88, fx + 26, 95, fill=wine, radius=1)
    c.text(fx, 91.5, "ぶどう本来の果実味", 2.8, cream, 700)
    c.text(fx, 99.5, "720ml  アルコール分12%", 2.8, INK, 800)
    _alcohol_mark(c, fx + 31, 72, 7)
    c.vtext(0.5 * W, 8, "ぶどうの香り豊か", 3.4, wine, 800)
    _bottle_back(c, 0.25 * W, 6, 46, "果実酒", "ぶどう（輸入）／酸化防止剤（亜硫酸塩）", 1.8, color=INK, bg=cream,
                 extra=[("内容量", "720ml"), ("アルコール分", "12%"), ("輸入者", "架空の洋酒 株式会社"),
                        ("保存方法", "直射日光・高温を避けて保存")])
    c.paragraph(0.25 * W - 23, 66, 0.25 * W + 23, ALCOHOL_NOTE, 1.6, INK, 600)
    c.barcode(0.25 * W - 12, 84, 24, 14)
    c.recycle(0.5 * W, 96, 6, "アルミ", INK, kind="can", sub="キャップ")
    label = finish(c.array(), "paper", 5011, 0.5)

    t = top_canvas(form, wine, seed=5012)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#7E1C2E", "#4C0E19")
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline="#3A0A13", width=0.6)
    t.ellipse(d * 0.2, d * 0.2, d * 0.8, d * 0.8, outline=gold, width=0.5)
    t.text(d / 2, d / 2, "VR", 6.0, gold, 900)
    top = finish(t.array(), "metal", 5012, 0.6)
    return Product(slug="red_wine_bottle_720ml", name="赤ワイン 辛口 720ml", category="beverage", mass_kg=1.2,
                   capacity_ml=720, material="glass (opaque dark green)",
                   description="形は一般的な 720ml のボルドー型ワインボトル（高さ 290 mm・胴径 75 mm、30 × 60 mm のアルミのねじ蓋）で、寸法・質量は代表値。"
                               "濃い緑のガラスで中身はほとんど見えないため、不透明の瓶として作った。",
                   tags=["ワイン", "赤ワイン", "果実酒", "お酒", "酒類", "瓶", "red wine", "wine bottle", "alcohol"],
                   photos=["drk_grapes"], colors=Colors(cap=wine, label_base=green), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- のむヨーグルト


def drink_yogurt_pet() -> Product:
    """のむヨーグルト 500g（乳白の樹脂ボトル・広口のねじ蓋、白く濁った中身）。

    参考: https://commons.wikimedia.org/wiki/File:Soy_milk_bottles_2.jpg（CC0、白い乳飲料のボトル）
    """
    form = forms.pet_bottle(0.180, 0.068, shoulder=0.16, neck_r=0.0165, cap_h=0.017, cap_r=0.0182,
                            label=(0.012, 0.128), liquid_top=0.150)
    white, blue, pink, sky = "#FFFFFF", "#2459A8", "#E85A7A", "#DCEAF8"
    c = label_canvas(form, white, seed=5021)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#E5F0FB")
    c.pattern(0, H - 18, W, H, "waves", mix(blue, white, 0.7), 4.0, 0.6)
    c.rect(0, 0, W, 7, fill=blue)
    c.text(fx, 3.5, "生乳たっぷり  乳酸菌", 3.2, white, 800)
    c.text(fx, 20, "のむ", 8.0, blue, 900)
    c.text(fx, 36, "ヨーグルト", 11.0, blue, 900, max_w=70)
    c.text(fx, 46, "DRINK YOGURT", 3.6, pink, 800, spacing=0.8)
    c.ellipse(fx - 16, 52, fx + 16, 80, fill=white, outline=sky, width=0.8)  # 白いヨーグルトの絵
    c.ellipse(fx - 10, 58, fx + 10, 70, fill="#F7F5EE", outline=mix(blue, white, 0.6), width=0.4)
    c.polygon([(fx + 4, 58), (fx + 13, 50), (fx + 15, 52), (fx + 7, 60)], fill=mix(pink, white, 0.3))
    c.rect(fx - 24, 86, fx + 24, 94, fill=pink, radius=4)
    c.text(fx, 90, "プレーン  加糖", 4.0, white, 900)
    c.text(fx, 103, "500g", 6.0, blue, 900)
    c.text(fx, 110, "要冷蔵", 3.0, blue, 800)
    c.vtext(0.5 * W, 12, "よく振ってから", 3.6, blue, 800)
    _bottle_back(c, 0.25 * W, 9, 46, "はっ酵乳", "生乳（国産）、乳製品、砂糖／安定剤（ペクチン）、香料", 1.9, color=blue,
                 extra=[("内容量", "500g"), ("無脂乳固形分", "8.0%"), ("乳脂肪分", "0.5%"), ("賞味期限", "キャップに記載"),
                        ("保存方法", "要冷蔵（10℃以下）")],
                 nutrition=[("栄養成分表示 100g当たり", ""), ("エネルギー", "65kcal"), ("たんぱく質", "3.0g"),
                            ("脂質", "0.5g"), ("炭水化物", "12.0g"), ("食塩相当量", "0.1g")])
    c.barcode(0.5 * W - 12, 56, 24, 15)
    c.recycle(0.5 * W - 7, 82, 7, "プラ", blue, sub="ボトル")
    c.recycle(0.5 * W + 7, 82, 7, "プラ", blue, sub="キャップ")
    label = finish(c.array(), "film", 5021, 0.6)

    t = top_canvas(form, blue, seed=5022)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#3A72C2", "#1E4C90")
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline="#173B70", width=0.6)
    t.text(d / 2, d * 0.40, "賞味期限", 3.0, white, 700)
    t.text(d / 2, d * 0.58, "26.11.12", 3.6, white, 800)
    top = finish(t.array(), "film", 5022, 0.5)
    yog = "#F7F5EE"
    return Product(slug="drink_yogurt_pet", name="のむヨーグルト プレーン 500g", category="beverage", mass_kg=0.53,
                   capacity_ml=480, material="HDPE (translucent)",
                   description="形は一般的な 500g ののむヨーグルトのボトル（高さ 180 mm・胴径 68 mm、口径 36 mm の広口のねじ蓋）で、寸法・質量は代表値。"
                               "容器は乳白の樹脂で、ラベルの上の肩から白く濁った中身がうっすら見える。",
                   tags=["のむヨーグルト", "ドリンクヨーグルト", "はっ酵乳", "乳製品", "要冷蔵", "drinking yogurt",
                         "yogurt drink bottle"],
                   photos=[], colors=Colors(cap=blue, liquid=yog, label_base="#F4F4F0"),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=yog))


# ---------------------------------------------------------------- 豆乳（紙パック）


def soy_milk_pack_200ml() -> Product:
    """豆乳 200ml のブリック型紙パック（細長い直方体、裏にストロー）。

    参考: https://commons.wikimedia.org/wiki/File:Tetra_Brik_Aseptic_bottom_20110702.jpg（CC0）
    """
    W, D, H = 50.0, 37.0, 115.0
    green, beige, brown, cream = "#3B7A3A", "#EADBB8", "#8A6A3A", "#FBF6EA"
    s = 12

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, cream, seed)
        f.gradient(0, 0, w, h, "#FFFDF6", "#F1E6CC")
        f.rect(0, 0, w, 5, fill=green)
        return f

    def beans(f: Canvas, cx: float, cy: float, r: float, n: int):
        for _ in range(n):
            x, y = cx + f.rng.uniform(-r, r), cy + f.rng.uniform(-r * 0.5, r * 0.5)
            a = f.rng.uniform(2.0, 2.8)
            f.ellipse(x - a, y - a * 0.82, x + a, y + a * 0.82, fill="#E8CF8E", outline="#B9965A", width=0.25)
            f.ellipse(x - a * 0.5, y - a * 0.55, x - a * 0.05, y - a * 0.2, fill="#F6E7BE")

    fr = face(W, H, 5031)
    fr.text(W / 2, 2.5, "大豆固形分 8%以上", 2.4, "#FFFFFF", 800)
    fr.text(W / 2, 11, "調製", 4.6, brown, 900)
    fr.vtext(W / 2, 17, "豆乳", 15, green, 900, gap=0.04)
    fr.ellipse(4, 58, W - 4, 88, fill="#FFFFFF", outline=mix(green, "#FFFFFF", 0.5), width=0.5)
    beans(fr, W / 2, 73, 12, 9)
    fr.polygon([(W / 2 + 4, 62), (W / 2 + 14, 58), (W / 2 + 10, 66)], fill="#5BA04A")  # 葉
    fr.rect(5, 92, W - 5, 99, fill=green, radius=3.5)
    fr.text(W / 2, 95.5, "コレステロール0", 3.2, "#FFFFFF", 900)
    fr.text(W / 2, 105, "SOY MILK  200ml", 3.2, green, 800, spacing=0.3)
    fr.pattern(0, 110, W, H, "waves", beige, 3.0, 0.5)

    bk = face(W, H, 5032)
    bk.text(W / 2, 2.5, "国産大豆 使用", 2.4, "#FFFFFF", 800)
    back_info(bk, 3, 8, W - 3, [
        ("名称", "調製豆乳"), ("原材料名", "大豆（国産、遺伝子組換えでない）、砂糖、米油、天日塩／乳化剤、糊料（カラギナン）、香料"),
        ("内容量", "200ml"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温を避けてください")], 1.9,
        [("栄養成分表示 1本当たり", ""), ("エネルギー", "118kcal"), ("たんぱく質", "6.6g"), ("脂質", "7.1g"),
         ("炭水化物", "7.0g"), ("食塩相当量", "0.3g")], green)
    bk.barcode(W / 2 - 15, H - 23, 30, 16)
    rt = face(D, H, 5033)
    rt.vtext(D / 2, 12, "まろやか豆乳", 6.6, green, 900, gap=0.04)
    rt.text(D / 2, 92, "よく振って", 3.0, brown, 900)
    rt.text(D / 2, 97, "お飲みください", 3.0, brown, 900)
    rt.recycle(D / 2, 106, 6.5, "紙パック", green)
    lf = face(D, H, 5034)
    lf.vtext(D / 2 + 6, 12, "大豆のおいしさ", 4.4, green, 900)
    lf.vtext(D / 2 - 6, 12, "毎日の健康習慣に", 3.8, brown, 800)
    lf.recycle(D / 2 - 7, 105, 5.5, "プラ", green, sub="ストロー袋")
    lf.recycle(D / 2 + 7, 105, 5.5, "紙", green, sub="パック")
    tp = Canvas(W, D, s, cream, 5035)
    tp.gradient(0, 0, W, D, "#FFFDF6", "#EFE3C4")
    tp.ellipse(W * 0.66, D * 0.30, W * 0.66 + 7, D * 0.30 + 7, fill="#E8E2D0", outline="#B8B09A", width=0.4)
    tp.text(W * 0.34, D * 0.42, "賞味期限", 2.4, INK, 700)
    tp.text(W * 0.34, D * 0.60, "2027.02.20", 2.6, INK, 700)
    tp.text(W * 0.73, D * 0.78, "ストロー", 2.0, green, 700)
    bt = Canvas(W, D, s, cream, 5036)
    bt.gradient(0, 0, W, D, "#F1E6CC", "#E6D8B6")
    bt.text(W / 2, D / 2, NOTICE, 1.5, INK, 500, max_w=W - 4)
    imgs = _faces((fr, bk, rt, lf, tp, bt), "paper", 5037)
    yb = D / 2000 + 0.0022  # 裏面に貼り付けたストロー（透明の袋入り）
    parts = [_box("Straw", (0.0045, 0.0040, 0.095), (0.010, yb, 0.058), "#F4F4F0", "plastic", rotation=[0, 5, 0],
                  collision=False),
             _box("StrawBag", (0.0085, 0.0044, 0.103), (0.010, yb, 0.058), "#F2F6F8", "glass", thin_walled=True, rotation=[0, 5, 0],
                  collision=False)]
    return Product(slug="soy_milk_pack_200ml", name="調製豆乳 200ml 紙パック", shape_class="box", category="beverage",
                   dims=Dimensions(0.115, 0.050, depth=0.037), mass_kg=0.215, capacity_ml=200, material="paper",
                   description="形は一般的な 200ml のスリムなブリック型紙パック（高さ 115 mm・幅 50 mm・奥行き 37 mm、裏面にストロー付き）で、寸法・質量は代表値。",
                   tags=["豆乳", "調製豆乳", "紙パック", "大豆", "soy milk", "soy milk carton", "juice box"], photos=[],
                   colors=Colors(label_base=cream), images=imgs, parts=parts, faces=BOX_FACES)


# ---------------------------------------------------------------- コーヒー牛乳（屋根型紙パック）


def coffee_milk_pack_500ml() -> Product:
    """コーヒー牛乳 500ml の屋根型紙パック（milk_carton_1l と同じ作り）。

    参考: https://commons.wikimedia.org/wiki/File:Ouchiyama_Milk_carton_cropped_to_show_seam.jpg（PD）
    写真: drk_coffee_milk（https://commons.wikimedia.org/wiki/File:Coffee_with_milk_(563800)_(cropped).jpg、CC0）
    """
    W, H = 70.0, 110.0  # 胴の 1 面
    brown, cream, white, caramel = "#5A3420", "#F5E9D6", "#FFFFFF", "#B8834A"
    s = 10

    fr = Canvas(W, H, s, cream, 5041)
    fr.gradient(0, 0, W, H, "#FBF3E6", "#EAD6B8")
    fr.rect(0, 0, W, 9, fill=brown)
    fr.text(W / 2, 4.5, "乳飲料  要冷蔵", 3.6, cream, 800)
    fr.text(W / 2, 20, "コーヒー", 9.0, brown, 900)
    fr.text(W / 2, 32, "牛乳", 11.0, brown, 900)
    fr.photo("drk_coffee_milk", 7, 40, W - 7, 82, shape="round", radius=4, crop=(0.10, 0.05, 0.88, 0.92))
    fr.text(W - 8, 84.5, "※写真はイメージです", 1.5, INK, 500, anchor="rm")
    fr.rect(8, 88, W - 8, 96, fill=caramel, radius=4)
    fr.text(W / 2, 92, "生乳 50%以上使用", 3.8, white, 900)
    fr.text(W / 2, 103, "COFFEE MILK  500ml", 3.6, brown, 800, spacing=0.3)

    rt = Canvas(W, H, s, cream, 5042)
    rt.rect(0, 0, W, 6, fill=brown)
    y = back_info(rt, 4, 9, W - 4, [
        ("種類別名称", "乳飲料"), ("無脂乳固形分", "5.0%"), ("乳脂肪分", "1.5%"),
        ("原材料名", "生乳（国産）、砂糖、乳製品、コーヒー／カラメル色素、香料"), ("内容量", "500ml"),
        ("賞味期限", "上部に記載"), ("保存方法", "要冷蔵（10℃以下）")], 2.2,
        [("栄養成分表示 200ml当たり", ""), ("エネルギー", "128kcal"), ("たんぱく質", "4.2g"), ("脂質", "3.4g"),
         ("炭水化物", "20.1g"), ("食塩相当量", "0.2g")], brown)
    rt.text(W / 2, min(y + 5, H - 4), "開封後はお早めにお飲みください", 2.4, brown, 700)

    bk = Canvas(W, H, s, cream, 5043)
    bk.rect(0, 0, W, 6, fill=brown)
    bk.vtext(W / 2, 12, "まろやか", 8, brown, 900, gap=0.05)
    bk.barcode(W / 2 - 17, 58, 34, 19)
    bk.recycle(W / 2, 92, 10, "紙パック", brown)
    bk.text(W / 2, 104, "洗って開いてリサイクルへ", 2.6, brown, 700)

    lf = Canvas(W, H, s, cream, 5044)
    lf.gradient(0, 0, W, H, white, cream)
    lf.vtext(W / 2 + 12, 10, "コーヒー牛乳", 7, brown, 900)
    lf.vtext(W / 2 - 10, 10, "ほっとする甘さ", 4.0, caramel, 800)
    lf.text(W / 2, 103, "500ml", 4.4, brown, 800)

    gd = 49.5  # 屋根の斜面（45° に回した角柱の面）
    gf = Canvas(W, gd, s, brown, 5045)
    gf.gradient(0, 0, W, gd, "#6E432A", brown)
    gf.text(W / 2, gd * 0.42, "コーヒー牛乳", 7.4, cream, 900)
    gf.text(W / 2, gd * 0.75, "500ml", 4.6, cream, 800)
    gb = Canvas(W, gd, s, cream, 5046)
    gb.gradient(0, 0, W, gd, white, cream)
    gb.text(W / 2, gd * 0.38, "あけくち", 6.0, brown, 900)
    gb.polygon([(W / 2 - 5, gd * 0.55), (W / 2 + 5, gd * 0.55), (W / 2, gd * 0.68)], fill=brown)
    gb.text(W / 2, gd * 0.82, "賞味期限 2026.11.08", 3.0, INK, 600)
    imgs = [_face(c.array(), "paper", 5050 + i) for i, c in enumerate((fr, rt, bk, lf, gf, gb))]

    sq, bh = 0.0495, 0.110
    parts = [_box("Body", (0.07, 0.07, bh), (0, 0, bh / 2), cream, "plastic",
                  {"front": 0, "right": 1, "back": 2, "left": 3}),
             _box("Gable", (0.0694, sq, sq), (0, 0, bh), cream, "plastic", {"top": 4, "back": 5}, [45, 0, 0]),
             _box("TopFin", (0.07, 0.006, 0.012), (0, 0, bh + 0.037), "#F2EBDD")]
    return Product(slug="coffee_milk_pack_500ml", name="コーヒー牛乳 500ml", shape_class="assembly", category="beverage",
                   dims=Dimensions(round(bh + 0.043, 4), 0.07, depth=0.07), mass_kg=0.545, capacity_ml=500,
                   material="paper",
                   description="形は一般的な 500ml の屋根型紙パック（胴 70 × 70 mm・高さ 153 mm）で、寸法・質量は代表値。",
                   tags=["コーヒー牛乳", "乳飲料", "紙パック", "要冷蔵", "500ml", "coffee milk", "coffee milk carton"],
                   photos=["drk_coffee_milk"], colors=Colors(label_base=cream), images=imgs, parts=parts)


# ---------------------------------------------------------------- コーンスープ缶


def corn_soup_can() -> Product:
    """コーンスープ 185g のショート缶（スチール、ホット用）。

    参考: https://commons.wikimedia.org/wiki/File:Drink_vending_machine_at_Narita_Airport.jpg（CC0、自販機のホット缶）
    写真: drk_corn（https://commons.wikimedia.org/wiki/File:Corn_kernels_in_bowl_-_Massachusetts.jpg、CC0）
    """
    form = forms.beverage_can(0.105, 0.053, label_margin=0.005)
    yellow, cream, red, brown = "#F2C230", "#FFF6D8", "#C8352B", "#6B4A1E"
    c = label_canvas(form, yellow, seed=5061)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#F7D352", "#E3A91E")
    c.rect(0, 0, W, 6, fill=red)
    c.rect(0, H - 6, W, H, fill=red)
    c.text(fx, 3, "HOT  あたたか〜い", 3.0, cream, 800)
    c.photo("drk_corn", fx - 22, 9, fx + 22, 47, shape="ellipse", shadow=1.0, crop=(0.18, 0.18, 0.82, 0.82))
    c.text(fx + 21, 47, "※写真はイメージです", 1.4, INK, 500, anchor="lm")
    c.rect(fx - 23, 50, fx + 23, 70, fill=cream, radius=2)
    c.text(fx, 56, "粒入り", 4.0, red, 900)
    c.text(fx, 65, "コーンスープ", 6.8, brown, 900, max_w=44)
    c.text(fx, 76, "CORN POTAGE", 3.2, red, 800, spacing=0.6)
    c.text(fx, H - 3, "185g", 3.2, cream, 900)
    c.vtext(0.5 * W, 9, "よく振ってから", 3.0, red, 800)
    _bottle_back(c, 0.25 * W, 8, 40, "スープ", "スイートコーン（遺伝子組換えでない）、牛乳、砂糖、乳製品、でん粉、食塩、"
                 "植物油脂／増粘剤、乳化剤、香料", 1.55, color=brown, bg=cream,
                 extra=[("内容量", "185g"), ("賞味期限", "缶底に記載")],
                 nutrition=[("栄養成分表示 1本当たり", ""), ("エネルギー", "96kcal"), ("たんぱく質", "1.9g"),
                            ("脂質", "2.6g"), ("炭水化物", "16.3g"), ("食塩相当量", "0.9g")], notice_color=brown)
    c.rect(0.5 * W - 14, 30, 0.5 * W + 14, 49, fill="#FFFFFF")
    c.barcode(0.5 * W - 12, 31, 24, 15)
    c.recycle(0.5 * W, 60, 7, "スチール", brown, kind="can")
    label = finish(c.array(), "metal", 5061, 0.7)
    return Product(slug="corn_soup_can", name="コーンスープ 粒入り 185g 缶", category="beverage", mass_kg=0.22,
                   capacity_ml=185, material="steel",
                   description="形は一般的な 185g のショート缶（高さ 105 mm・胴径 53 mm、スチール）で、寸法・質量は代表値。",
                   tags=["コーンスープ", "コーンポタージュ", "スープ", "ホット", "缶", "スチール缶", "corn soup", "corn soup can",
                         "canned soup"],
                   photos=["drk_corn"], colors=Colors(cap="#BFC2C5", label_base=yellow),
                   **revolve(form, label=label, top=_can_top(form, 5062)))


# ---------------------------------------------------------------- セルフ式ホットコーヒー


def _hot_cup(H_cup: float, top_d: float, bottom_d: float, lid_h: float) -> RevolveForm:
    """紙のカップに、飲み口のある樹脂のふた（縁が盛り上がり、上面は平ら）をかぶせた形。"""
    base = forms.paper_cup(H_cup, top_d, bottom_d, lid_h=0.0005, lid_overhang=0.0, rim_h=0.004, foot_h=0.006,
                           label_margin=(0.004, 0.003))
    cap_z = base.body[-1][0]
    rl = top_d / 2 + 0.0022  # ふたは巻き縁を覆う
    cap = [(cap_z, rl), (cap_z + 0.0045, rl), (cap_z + 0.0060, rl - 0.0018)]
    cap += _arc(cap_z + 0.0060, cap_z + lid_h - 0.0010, rl - 0.0018, rl - 0.0050, 8, "in")[1:]
    cap += [(cap_z + lid_h, rl - 0.0068)]
    return RevolveForm(base.body, cap, base.label)


def hot_coffee_cup_r() -> Product:
    """セルフ式のホットコーヒー R サイズ（紙カップ + 飲み口付きのふた）。

    参考: https://commons.wikimedia.org/wiki/File:DB-Kaffeebecher_am_Platz_(ICE).JPG（PD、ふた付きの紙カップ）
    """
    form = _hot_cup(0.094, 0.080, 0.056, lid_h=0.013)
    white, brown, red, beige = "#FBFAF7", "#4A2C1C", "#B3262B", "#E7D9C4"
    c = label_canvas(form, white, seed=5071)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#FFFFFF", "#F1ECE4")
    c.rect(0, H - 22, W, H, fill=brown)
    c.pattern(0, H - 22, W, H, "stripes", mix(brown, "#FFFFFF", 0.12), 5.0, 1.0)
    c.rect(0, H - 24, W, H - 22, fill=red)
    for x in (0.75 * W, 0.25 * W):  # 正面と裏面
        c.ellipse(x - 9, 12, x + 9, 30, fill=beige)
        c.ellipse(x - 7, 14, x + 7, 28, fill=brown)
        c.line([(x, 14.3), (x - 1.6, 18), (x + 1.6, 24), (x, 27.7)], beige, 0.7)  # コーヒー豆
        steam(c, x, 11, 8, 7, mix(brown, "#FFFFFF", 0.5), 0.5)
        c.text(x, 38, "HOT COFFEE", 4.6, brown, 900, spacing=0.4)
        c.text(x, 45, "ホットコーヒー", 3.6, red, 800)
        c.text(x, H - 15, "R", 6.0, "#FFFFFF", 900)
        c.text(x, H - 7, "freshly brewed", 2.4, beige, 700)
    for x in (0.5 * W, 0.0 * W + 0.02 * W, 0.98 * W):
        c.vtext(x, 8, "やけどに注意", 2.6, red, 800)
    c.recycle(0.5 * W, 44, 5, "紙", brown, sub="カップ")
    label = finish(c.array(), "paper", 5071, 0.5)

    t = top_canvas(form, white, seed=5072)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FFFFFF", "#E6E6E3")
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline="#C9C9C5", width=1.2)
    t.ellipse(d * 0.08, d * 0.08, d * 0.92, d * 0.92, outline="#D9D9D5", width=0.6)
    t.ellipse(d * 0.20, d * 0.20, d * 0.80, d * 0.80, outline="#E0E0DC", width=0.5)
    # 飲み口（正面寄りの細長い穴）と、湯気の抜ける小さな穴（奥）
    t.rect(d / 2 - 8, d * 0.80, d / 2 + 8, d * 0.86, fill="#2B1A10", radius=1.6)
    t.rect(d / 2 - 10, d * 0.77, d / 2 + 10, d * 0.89, outline="#CFCFCB", width=0.4, radius=3)
    t.ellipse(d / 2 - 1, d * 0.16 - 1, d / 2 + 1, d * 0.16 + 1, fill="#3A3A38")
    t.text(d / 2, d * 0.45, "HOT", 5.0, "#BDBDB9", 900, spacing=1.0)
    t.text(d / 2, d * 0.56, "飲み口", 2.4, "#A9A9A5", 700)
    top = finish(t.array(), "film", 5072, 0.4)
    return Product(slug="hot_coffee_cup_r", name="ホットコーヒー R サイズ", category="beverage", mass_kg=0.17,
                   capacity_ml=150, material="paper",
                   description="形は一般的なコンビニのセルフ式ホットコーヒー R サイズの紙カップ（口径 80 mm・底径 56 mm・高さ 94 mm、ふた込みで約 107 mm）に、"
                               "飲み口のある樹脂のふた（高さ 13 mm）をかぶせたもので、寸法・質量は代表値。",
                   tags=["ホットコーヒー", "コーヒー", "セルフコーヒー", "紙コップ", "hot coffee", "coffee cup", "paper cup"],
                   photos=[], colors=Colors(cap=white, label_base=white), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- ハイボール缶


def highball_can_350ml() -> Product:
    """ウイスキーのハイボール 350ml 缶。

    参考: https://commons.wikimedia.org/wiki/File:Orion_beer_350ml_can_01.jpg（CC0、350ml 缶の形）、
    https://commons.wikimedia.org/wiki/File:Alcohol_vending_machine_-_night_-_Kanagawa_2024_Jan_30_05-30PM_-_pd.jpeg（CC0）
    写真: drk_ice（https://commons.wikimedia.org/wiki/File:Ice_cubes_on_water.jpg、CC0）
    """
    form = forms.aluminum_can(0.122, 0.066, top_d=0.054, label_margin=0.008)
    black, amber, gold, white = "#15120E", "#C9832A", "#D9B25A", "#FFFFFF"
    c = label_canvas(form, black, seed=5081)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#2A2118", "#0E0B08")
    c.pattern(0, 0, W, H, "stripes", mix(amber, black, 0.85), 7, 1.2)
    c.rect(0, 0, W, 2, fill=gold)
    c.rect(0, H - 2, W, H, fill=gold)
    c.photo("drk_ice", fx - 20, 6, fx + 20, 50, shape="round", radius=3, crop=(0.42, 0.18, 0.96, 0.86), border=gold,
            border_w=0.6)
    c.text(fx + 21, 49, "※写真はイメージです", 1.4, white, 500, anchor="lm")
    c.text(fx, 58, "WHISKY HIGHBALL", 3.8, gold, 800, spacing=0.6)
    c.text(fx, 70, "ハイボール", 10.0, white, 900)
    c.rect(fx - 22, 77, fx + 22, 84, fill=amber, radius=3.5)
    c.text(fx, 80.5, "強炭酸  すっきり辛口", 3.6, black, 900)
    c.text(fx, 90, "350ml  アルコール分7%", 3.2, gold, 800)
    _alcohol_mark(c, fx - 27, 60, 8)
    c.vtext(0.5 * W, 8, "ウイスキーを炭酸で割った", 2.8, gold, 800)
    _bottle_back(c, 0.25 * W, 7, 42, "リキュール（発泡性）①", "ウイスキー（国内製造）、レモンスピリッツ／炭酸、香料、酸味料",
                 1.7, color=white, bg=black, extra=[("内容量", "350ml"), ("アルコール分", "7%"), ("賞味期限", "缶底に記載")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "43kcal"), ("炭水化物", "0.4g"),
                            ("糖類", "0g"), ("食塩相当量", "0.03g")], notice_color=white)
    c.paragraph(0.25 * W - 21, 72, 0.25 * W + 21, ALCOHOL_NOTE, 1.6, gold, 700)
    c.rect(0.5 * W - 14, 50, 0.5 * W + 14, 68, fill=white)
    c.barcode(0.5 * W - 12, 51.5, 24, 14)
    c.recycle(0.5 * W + 10, 80, 7, "アルミ", white, kind="can")
    _alcohol_mark(c, 0.5 * W - 10, 80, 7)
    label = finish(c.array(), "metal", 5081, 0.7)
    return Product(slug="highball_can_350ml", name="ハイボール 350ml 缶", category="beverage", mass_kg=0.368,
                   capacity_ml=350, material="aluminum",
                   description="形は一般的な 350ml のアルミ缶（高さ 122 mm・胴径 66 mm、上すぼまりのネック）で、寸法・質量は代表値。",
                   tags=["ハイボール", "ウイスキー", "お酒", "アルコール", "酒類", "アルミ缶", "highball", "whisky highball can",
                         "alcohol", "can"],
                   photos=["drk_ice"], colors=Colors(cap="#BFC2C5", label_base=black),
                   **revolve(form, label=label, top=_can_top(form, 5082)))


# ---------------------------------------------------------------- 使い捨てライター


def disposable_lighter() -> Product:
    """使い捨てライター（半透明の樹脂の胴 + 金属の風防・やすり車 + 黒い押し金）。

    参考: https://commons.wikimedia.org/wiki/File:Disposable_BIC_lighter.JPG（PD）、
    https://commons.wikimedia.org/wiki/File:Disposable_lighter.JPG（PD）
    """
    body_c, metal, black = "#E2455A", "#C2C6CA", "#1E1E20"
    s = 40
    # 風防の正面・裏（細かい穴の並んだ金属の板）と側面
    wf = Canvas(12, 13, s, metal, 5091)
    wf.gradient(0, 0, 12, 13, "#DADDE0", "#9EA3A8")
    for i in range(4):
        for j in range(3):
            x, y = 2.2 + i * 2.5, 3.0 + j * 2.6
            wf.ellipse(x - 0.5, y - 0.5, x + 0.5, y + 0.5, fill="#2A2C2E")
    ws = Canvas(11.5, 13, s, metal, 5092)
    ws.gradient(0, 0, 11.5, 13, "#D0D3D6", "#9599A0")
    ws.rect(2, 1.5, 9.5, 5, fill="#2A2C2E", radius=1)  # 炎の出る口の切り欠き
    imgs = [_face(wf.array(), "metal", 5093, 0.5, 4), _face(ws.array(), "metal", 5094, 0.5, 4)]
    BW, BD, BH = 0.025, 0.0120, 0.062
    parts = [Part("Body", "box", [BW, BD, BH], [0, 0, BH / 2], color=body_c, finish="translucent", bevel=0.0035),
             Part("Fuel", "box", [BW - 0.004, BD - 0.004, 0.034], [0, 0, 0.019], color="#F1E9C8", finish="glass",
                  collision=False, bevel=0.002),
             Part("Head", "box", [BW - 0.001, BD - 0.0005, 0.004], [0, 0, BH + 0.002], color=black, finish="plastic",
                  bevel=0.001),
             _box("Windguard", (0.012, 0.0115, 0.013), (-0.0045, 0, BH + 0.0105), metal, "metal",
                  {"front": 0, "back": 0, "left": 1, "right": 1}),
             Part("FlintWheel", "cylinder", [0.0095, 0.0095, 0.0085], [0.0065, 0, BH + 0.0105], [90, 0, 0],
                  color="#9AA0A6", finish="metal"),
             _box("Lever", (0.0085, 0.0100, 0.0035), (0.0075, 0, BH + 0.0055), black, "plastic")]
    return Product(slug="disposable_lighter", name="使い捨てライター", shape_class="assembly", category="household",
                   dims=Dimensions(round(BH + 0.017, 4), BW, depth=BD), mass_kg=0.020, material="plastic",
                   description="形は一般的な使い捨てのやすり式ライター（幅 25 mm・厚さ 12 mm・高さ 79 mm）で、寸法・質量は代表値。"
                               "胴は半透明の樹脂で中の燃料（液化ガス）がうっすら見え、上に金属の風防・やすり車と黒い押し金が付く。",
                   tags=["ライター", "使い捨てライター", "喫煙具", "lighter", "disposable lighter", "butane lighter"],
                   photos=[], colors=Colors(label_base=body_c), images=imgs, parts=parts)


# ---------------------------------------------------------------- コミック（新書判）


def comic_paperback() -> Product:
    """コミックの単行本（新書判、シュリンク包装）。表紙の絵は図形だけで描いた架空の作品。

    参考: https://commons.wikimedia.org/wiki/File:Manga_(1).jpg（CC0、書店の棚のコミック）
    """
    W, H, D = 112.0, 174.0, 16.0  # 新書判、立てて置く
    navy, sky, orange, white, yellow, red = "#18234A", "#7FB7E6", "#F08A3C", "#FFFFFF", "#FFE14D", "#D7262E"
    s = 8
    fr = Canvas(W, H, s, sky, seed=5101)
    fr.gradient(0, 0, W, H * 0.7, "#2B3F7E", "#F2A86A")  # 夕方の空
    for _ in range(30):  # 星
        x, y = fr.rng.uniform(0, W), fr.rng.uniform(0, 50)
        fr.ellipse(x - 0.5, y - 0.5, x + 0.5, y + 0.5, fill="#FFF6D0")
    fr.ellipse(W * 0.62, 70, W * 0.62 + 30, 100, fill="#FFD27A")  # 夕日
    fr.polygon([(0, 120), (25, 96), (48, 112), (74, 88), (W, 116), (W, H), (0, H)], fill="#3D4C7A")  # 山
    fr.polygon([(0, 132), (30, 118), (60, 128), (90, 112), (W, 124), (W, H), (0, H)], fill="#26305A")
    # 丘の上に立つ人影（図形）とマフラー
    cx, gy = W * 0.38, 124
    fr.ellipse(cx - 4, gy - 38, cx + 4, gy - 30, fill="#141A33")
    fr.polygon([(cx - 5, gy - 30), (cx + 5, gy - 30), (cx + 6, gy - 12), (cx - 6, gy - 12)], fill="#141A33")
    fr.polygon([(cx - 4, gy - 12), (cx - 1, gy - 12), (cx - 2, gy), (cx - 5, gy)], fill="#141A33")
    fr.polygon([(cx + 1, gy - 12), (cx + 4, gy - 12), (cx + 5, gy), (cx + 2, gy)], fill="#141A33")
    fr.polygon([(cx + 3, gy - 30), (cx + 20, gy - 34), (cx + 18, gy - 30), (cx + 4, gy - 27)], fill=red)
    for k in range(3):  # 鳥
        bx, by = 70 + k * 9, 48 + k * 5
        fr.line([(bx - 3, by - 1.5), (bx, by), (bx + 3, by - 1.5)], navy, 0.5)
    fr.rect(6, 6, 40, 56, fill=white)  # 縦書きの題名
    fr.vtext(28, 10, "空のむこう", 8.0, navy, 900, gap=0.02)
    fr.vtext(15, 12, "の約束", 6.5, red, 900, gap=0.02)
    fr.ellipse(W - 30, 6, W - 6, 30, fill=orange)
    fr.text(W - 18, 13, "第", 3.6, white, 800)
    fr.text(W - 18, 22, "3巻", 7.0, white, 900)
    fr.text(W - 8, 38, "作・架空 一郎", 3.6, white, 800, anchor="rm")
    fr.rect(0, H - 40, W, H, fill=yellow)  # 帯
    fr.text(W / 2, H - 31, "待望の第3巻、ついに発売！", 6.0, red, 900, max_w=W - 8)
    fr.text(W / 2, H - 20, "旅は、空のむこうの町へ。", 4.4, navy, 800)
    fr.text(W / 2, H - 9, "架空コミックス", 3.6, navy, 800)
    bk = Canvas(W, H, s, white, seed=5102)  # 裏表紙
    bk.gradient(0, 0, W, H, "#F7F1E4", "#E9DDC6")
    bk.rect(10, 10, W - 10, 64, fill=white, outline=navy, width=0.5)
    bk.paragraph(15, 16, W - 15, "空に浮かぶ町を目指して旅を続ける少年と、言葉を話す一羽の鳥。"
                 "嵐の夜に出会った不思議な少女は、二人に古い地図を手渡した——。ひとつの約束が、新しい冒険のはじまりになる。", 3.4, INK, 600)
    bk.rect(0, H - 40, W, H, fill=yellow)
    bk.barcode(W - 46, H - 76, 36, 14)
    bk.barcode(W - 46, H - 58, 36, 14)
    bk.text(12, H - 70, "書籍コード（ダミー）", 2.6, INK, 600, anchor="lm")
    bk.text(12, H - 62, "定価 572円", 4.0, INK, 900, anchor="lm")
    bk.text(12, H - 55, "（本体520円＋税10%）", 2.8, INK, 600, anchor="lm")
    bk.text(W / 2, H - 28, "大好評発売中  第1巻・第2巻", 4.2, red, 900)
    bk.text(W / 2, H - 14, NOTICE, 2.2, INK, 500, max_w=W - 8)
    sp = Canvas(D, H, 10, navy, seed=5103)  # 背（右綴じなので表紙の右）
    sp.gradient(0, 0, D, H * 0.7, "#2B3F7E", "#F2A86A")
    sp.rect(0, 4, D, 66, fill=white)
    sp.vtext(D / 2, 7, "空のむこうの約束", 6.0, navy, 900, gap=0.02)
    sp.ellipse(D / 2 - 6, 74, D / 2 + 6, 86, fill=orange)
    sp.text(D / 2, 80, "3", 7.0, white, 900)
    sp.vtext(D / 2, 92, "架空一郎", 3.6, white, 800)
    sp.rect(0, H - 40, D, H, fill=yellow)
    sp.vtext(D / 2, H - 36, "架空コミックス", 2.6, navy, 800)
    paper = "#EFEBE1"
    ed = Canvas(D, H, 10, paper, seed=5104)  # 小口（紙の重なり）
    for k in range(64):
        ed.line([(k * D / 64, 0), (k * D / 64, H)], mix(paper, "#A9A39A", 0.2 + 0.2 * (k % 4 == 0)), 0.05)
    tp, bt = Canvas(W, D, 6, paper, seed=5105), Canvas(W, D, 6, paper, seed=5106)
    for e in (tp, bt):
        for k in range(24):
            e.line([(0, k * D / 24), (W, k * D / 24)], mix(paper, "#A9A39A", 0.3), 0.06)
    tp.rect(W - 2, 0, W, D, fill=navy)  # 背の側（上面は右、底面は左右が逆になる）
    bt.rect(0, 0, 2, D, fill=navy)
    imgs = _faces((fr, bk, sp, ed, tp, bt), "paper", 5110, 0.6)
    # シュリンク包装（透明のフィルムで本全体を包む）
    parts = [_box("Shrink", (0.1134, 0.0172, 0.1752), (0, 0, 0.0876), "#F2F6F8", "glass", thin_walled=True, collision=False)]
    return Product(slug="comic_paperback", name="コミック 空のむこうの約束 第3巻", shape_class="box", category="household",
                   dims=Dimensions(0.174, 0.112, depth=0.016), mass_kg=0.13, material="paper",
                   description="形は一般的なコミックの単行本（新書判 112 × 174 mm・厚さ 16 mm、右綴じ、シュリンク包装）を立てた箱で近似したもので、"
                               "寸法・質量は代表値。作品名・作者名・あらすじ・表紙の絵はすべて架空。",
                   tags=["コミック", "漫画", "マンガ", "単行本", "本", "新書判", "comic", "manga", "comic book",
                         "shrink-wrapped book"],
                   photos=[], colors=Colors(label_base=white), images=imgs, faces=BOX_FACES, parts=parts)


PRODUCTS = {f.__name__: f for f in (
    sake_cup_180ml, red_wine_bottle_720ml, drink_yogurt_pet, soy_milk_pack_200ml, coffee_milk_pack_500ml, corn_soup_can,
    hot_coffee_cup_r, highball_can_350ml, disposable_lighter, comic_paperback)}
