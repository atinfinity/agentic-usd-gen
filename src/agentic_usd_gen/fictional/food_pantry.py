"""架空の商品のデザイン: 食品（常温: レトルト・缶詰・調味料・瓶など）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from ..spec import Colors, Dimensions
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .forms import RevolveForm, _arc
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _bottle_back, _face, back_info, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


# ---------------------------------------------------------------- 共通の部品


def _food_can(H: float, D: float, seam: float = 0.003) -> RevolveForm:
    """食缶（3 ピース缶）。上下の巻き締めが胴より少し太い。上の巻き締めと蓋をキャップ扱いにする。"""
    R = D / 2
    Rs = R + 0.0007
    body = [(0.0, R * 0.93), (0.0005, Rs), (seam - 0.0004, Rs), (seam, R), (H - seam, R)]
    cap = [(H - seam, Rs), (H - 0.0005, Rs), (H, R * 0.95)]
    return RevolveForm(body, cap, (seam + 0.0005, H - seam - 0.0005))


def _squeeze_bottle(H: float, D: float, *, body_h: float, neck_r: float, cap_r: float, cap_h: float,
                    tip_r: float, label: tuple[float, float], liquid_top: float) -> RevolveForm:
    """マヨネーズなどのやわらかいボトル。胴 → 丸い肩 → 首、キャップは円筒の上に細い口のとんがり。"""
    R = D / 2
    neck_z = body_h + 0.004
    body = [(0.0, R * 0.82)] + _arc(0.0005, 0.010, R * 0.86, R, 10, "out")[1:]
    body += [(body_h - 0.033, R)] + _arc(body_h - 0.033, body_h, R, neck_r, 30, "cos")[1:] + [(neck_z, neck_r)]
    cyl_top = neck_z + cap_h
    cap = [(neck_z, cap_r), (cyl_top - 0.001, cap_r), (cyl_top, cap_r * 0.92)]
    cap += _arc(cyl_top, H, cap_r * 0.92, tip_r, 12, "in")[1:]
    return RevolveForm(body, cap, label, liquid_top)


def _eo_lid(form: RevolveForm, seed: int, stamp: str = "") -> np.ndarray:
    """食缶のイージーオープンの蓋（上面）。画像の下（手前）にプルタブ。"""
    t = top_canvas(form, "#B9BDC1", seed=seed)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#DADDE0", "#A1A6AB")
    t.ellipse(0.5, 0.5, d - 0.5, d - 0.5, outline="#868A8F", width=1.0)  # 巻き締め
    t.ellipse(2.2, 2.2, d - 2.2, d - 2.2, outline="#CBCED1", width=0.6)
    t.ellipse(d * 0.09, d * 0.09, d * 0.91, d * 0.91, outline="#8B8F94", width=0.35)  # スコア（切れ目）
    for k in (0.22, 0.30):
        t.ellipse(d * k, d * k, d * (1 - k), d * (1 - k), outline="#B6BABE", width=0.5)
    cx, rw = d / 2, d * 0.15
    t.ellipse(cx - d * 0.035, d * 0.53, cx + d * 0.035, d * 0.60, fill="#878B90")  # リベット
    t.rect(cx - rw, d * 0.58, cx + rw, d * 0.86, fill="#C9CCCF", outline="#7C8085", width=0.5, radius=rw * 0.9)
    t.rect(cx - rw * 0.62, d * 0.68, cx + rw * 0.62, d * 0.81, fill="#989DA2", radius=rw * 0.5)
    if stamp:
        t.text(cx, d * 0.40, stamp, d * 0.045, "#55595E", 700)
    return finish(t.array(), "metal", seed, 0.6)


def _heat(c: Canvas, x: float, y: float, level: int, on: str, size: float = 4.0, n: int = 5):
    """辛さの目盛り（左端 x、中心 y）。"""
    c.text(x, y, "辛さ", size, INK, 800, anchor="lm")
    x0 = x + size * 2.4
    for i in range(n):
        c.rect(x0 + i * size * 1.35, y - size * 0.5, x0 + i * size * 1.35 + size, y + size * 0.5,
               fill=on if i < level else mix(on, "#FFFFFF", 0.7), radius=size * 0.2)


def _checks(c: Canvas, x0: float, y0: float, x1: float, y1: float, color: str, step: float):
    """ギンガムチェック（2 色の格子を半透明に重ねたように塗る）。"""
    light = mix(color, "#FFFFFF", 0.55)
    y, j = y0, 0
    while y < y1:
        x, i = x0, 0
        while x < x1:
            if i % 2 or j % 2:
                c.rect(x, y, min(x1, x + step), min(y1, y + step), fill=color if (i % 2 and j % 2) else light)
            x += step
            i += 1
        y += step
        j += 1


# ---------------------------------------------------------------- レトルトカレー（箱）


def retort_curry_box() -> Product:
    W, D, H = 125.0, 26.0, 170.0
    red, cream, gold, brown = "#8E2A17", "#FBF1DE", "#E8B04A", "#4A2412"
    s = 8

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, cream, seed)
        f.gradient(0, 0, w, h, "#FDF5E6", "#F1DDBA")
        return f

    fr = face(W, H, 1001)
    fr.rect(0, 0, W, 34, fill=red)
    fr.rect(0, 34, W, 35.5, fill=gold)
    fr.text(W / 2, 13, "ビーフカレー", 13, cream, 900, max_w=W - 16)
    fr.text(W / 2, 27, "じっくり煮込んだ牛肉と野菜", 4.6, gold, 700, max_w=W - 14)
    fr.photo("curry", 6, 40, W - 6, 128, shape="round", radius=5, shadow=1.5, crop=(0.10, 0.03, 0.90, 0.97))
    fr.text(11, 124, "※写真はイメージです", 2.6, "#FFFFFF", 600, anchor="lm", stroke=0.25, stroke_fill="#333333")
    fr.ellipse(W - 40, 108, W - 6, 142, fill=gold, outline=red, width=0.6)
    fr.text(W - 23, 122, "中辛", 10, red, 900)
    fr.text(W - 23, 133, "MEDIUM HOT", 2.6, brown, 800)
    _heat(fr, 9, 139, 3, red, 4.0)
    fr.rect(8, 150, W - 8, 162, fill=brown, radius=6)
    fr.text(W / 2, 156, "箱ごとレンジで 600W 約2分", 4.6, cream, 800, max_w=W - 24)
    fr.text(W / 2, 166.5, "カレー（レトルトパウチ食品）  内容量 200g（1人前）", 2.6, brown, 600, max_w=W - 10)

    bk = face(W, H, 1002)
    bk.rect(5, 5, W - 5, H - 5, fill="#FFFFFF", radius=2)
    y = back_info(bk, 9, 9, W - 9, [
        ("名称", "カレー（レトルトパウチ食品）"),
        ("原材料名", "野菜（じゃがいも、にんじん、たまねぎ）、牛肉、小麦粉、食用油脂、カレー粉、砂糖、食塩、トマトペースト／調味料（アミノ酸等）、カラメル色素"),
        ("内容量", "200g"), ("賞味期限", "底面に記載"), ("保存方法", "直射日光を避け、常温で保存")], 2.8,
        [("栄養成分表示 1袋（200g）当たり", ""), ("エネルギー", "176kcal"), ("たんぱく質", "4.9g"), ("脂質", "8.6g"),
         ("炭水化物", "19.8g"), ("食塩相当量", "2.6g")], red)
    bk.text(9, y + 4, "【温め方】", 3.0, red, 900, anchor="lm")
    bk.paragraph(9, y + 7, W - 9, "電子レンジ：箱の上部を開けて袋の封を切らずに立てて入れ、600W で約2分温めます。\n"
                                  "湯せん：袋の封を切らずに沸騰したお湯に入れ、3〜5分温めます。", 2.6, INK, 500)
    bk.barcode(W / 2 - 18, H - 32, 36, 20)
    bk.recycle(18, H - 22, 9, "紙", red, sub="箱")
    bk.recycle(W - 18, H - 22, 9, "プラ", red, sub="袋")

    sides = []
    for k, seed in enumerate((1003, 1004)):
        sd = face(D, H, seed)
        sd.rect(0, 0, D, 34, fill=red)
        sd.text(D / 2, 17, "CURRY", 4.0, gold, 800)
        sd.vtext(D / 2, 44, "ビーフカレー", 8.5, brown, 900)
        sd.rect(3, 118, D - 3, 160, fill=red, radius=2)
        if k == 0:
            sd.vtext(D / 2, 128, "中辛", 7.5, cream, 900)
        else:
            sd.text(D / 2, 130, "200g", 5.0, cream, 900)
            sd.text(D / 2, 142, "1人前", 4.4, cream, 800)
        sides.append(sd.array())
    tp = face(W, D, 1005)
    tp.rect(0, 0, W, 5, fill=red)
    tp.text(W / 2, 12, "ビーフカレー 中辛", 6.0, red, 900)
    tp.text(W / 2, 20.5, "↓ ここから開けてください", 3.2, brown, 700)
    bt = face(W, D, 1006)
    bt.rect(0, D - 5, W, D, fill=red)
    bt.text(W / 2, 8, "賞味期限 2028.04.30", 4.0, INK, 700)
    bt.text(W / 2, 15, NOTICE, 2.4, brown, 400, max_w=W - 10)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 1011 + i) for i, a in enumerate(imgs)]
    return Product(slug="retort_curry_box", name="レトルトカレー 中辛", shape_class="box", category="food",
                   dims=Dimensions(0.17, 0.125, depth=0.026), mass_kg=0.23, material="paper",
                   description="形は一般的な箱入りのレトルトカレー（高さ 170 mm・幅 125 mm・奥行き 26 mm）で、寸法・質量は代表値。",
                   tags=["カレー", "レトルトカレー", "レトルト食品", "中辛", "retort curry", "curry"], photos=["curry"],
                   colors=Colors(label_base=red), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- カレールウ（箱）


def curry_roux_box() -> Product:
    W, D, H = 180.0, 35.0, 105.0
    orange, brown, cream, red = "#E8901E", "#4A2412", "#FFF4DD", "#B5261A"
    s = 8

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, orange, seed)
        f.gradient(0, 0, w, h, "#F5B13A", "#DC7414")
        return f

    fr = face(W, H, 1021)
    fr.rect(0, 0, W, 9, fill=brown)
    fr.text(W / 2, 4.5, "CURRY ROUX  欧風カレーのもと", 3.6, "#F5C76A", 800, spacing=0.3)
    fr.photo("curry", 86, 13, W - 4, 101, shape="ellipse", feather=1.5, shadow=1.5, crop=(0.10, 0.03, 0.90, 0.97))
    fr.text(W - 40, 99, "※写真はイメージです", 2.4, brown, 600)
    fr.text(43, 23, "カレールウ", 14, brown, 900, max_w=76)
    fr.text(43, 36, "スパイス香る欧風仕立て", 4.6, red, 800, max_w=76)
    fr.rect(7, 44, 46, 62, fill=red, radius=3)
    fr.text(26.5, 53, "中辛", 10, cream, 900)
    fr.photo("curry_spices", 52, 43, 78, 69, shape="ellipse", feather=0.8, shadow=0.8, crop=(0.18, 0, 0.92, 1))
    _heat(fr, 8, 69, 3, red, 3.6)
    fr.rect(7, 77, 79, 89, fill=brown, radius=6)
    fr.text(43, 83, "約8皿分  180g", 5.0, cream, 900)
    fr.text(43, 95, "8つに割れるブロックタイプ", 3.0, brown, 700)

    bk = face(W, H, 1022)
    bk.rect(4, 4, W - 4, H - 4, fill=cream, radius=2)
    back_info(bk, 7, 7, 92, [
        ("名称", "カレールウ"),
        ("原材料名", "食用油脂（牛脂豚脂混合油、パーム油）、小麦粉、でんぷん、食塩、カレー粉、砂糖、香辛料、ソテーオニオン／調味料（アミノ酸等）、カラメル色素、酸味料"),
        ("内容量", "180g（約8皿分）"), ("賞味期限", "側面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 2.4,
        [("栄養成分表示 1皿分（22.5g）当たり", ""), ("エネルギー", "115kcal"), ("たんぱく質", "1.3g"), ("脂質", "8.2g"),
         ("炭水化物", "9.1g"), ("食塩相当量", "2.4g")], brown, cream)
    bk.text(136, 11, "おいしい作り方（約8皿分）", 3.6, red, 900)
    bk.paragraph(98, 16, W - 8, "1. 肉・野菜（合計 約1000g）を一口大に切り、サラダ油で炒めます。\n"
                               "2. 水 1100ml を加えて沸騰させ、あくを取り、材料がやわらかくなるまで約15分煮込みます。\n"
                               "3. いったん火を止めてルウを割り入れ、溶かしてから弱火で約10分煮込みます。", 2.6, INK, 500)
    bk.barcode(108, 72, 34, 19)
    bk.recycle(156, 76, 8, "紙", brown, sub="箱")
    bk.recycle(168, 76, 8, "プラ", brown, sub="トレー")

    sides = []
    for k, seed in enumerate((1023, 1024)):
        sd = face(D, H, seed)
        sd.rect(0, 0, D, 9, fill=brown)
        sd.vtext(D / 2, 18, "カレールウ", 7.0, brown, 900)
        sd.rect(5, 63, D - 5, 98, fill=red, radius=2)
        if k == 0:
            sd.vtext(D / 2, 71, "中辛", 8.0, cream, 900)
        else:
            sd.text(D / 2, 72, "賞味期限", 3.0, cream, 700)
            sd.text(D / 2, 80, "2027.10", 3.6, cream, 900)
            sd.text(D / 2, 89, "8皿分", 4.0, cream, 900)
        sides.append(sd.array())
    tp = face(W, D, 1025)
    tp.rect(0, 0, W, 4, fill=brown)
    tp.text(W / 2, 15, "カレールウ 中辛", 7.0, brown, 900)
    tp.text(W / 2, 26, "↓ ここを押して開けてください", 3.4, red, 700)
    bt = face(W, D, 1026)
    bt.rect(0, D - 4, W, D, fill=brown)
    bt.text(W / 2, 10, "カレールウ  180g（約8皿分）", 4.0, brown, 800)
    bt.text(W / 2, 20, NOTICE, 2.6, brown, 400, max_w=W - 10)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 1031 + i) for i, a in enumerate(imgs)]
    return Product(slug="curry_roux_box", name="カレールウ 中辛", shape_class="box", category="food",
                   dims=Dimensions(0.105, 0.18, depth=0.035), mass_kg=0.2, material="paper",
                   description="形は一般的な箱入りのカレールウ（高さ 105 mm・幅 180 mm・奥行き 35 mm）で、寸法・質量は代表値。",
                   tags=["カレー", "カレールウ", "ルウ", "調味料", "中辛", "curry roux", "curry"],
                   photos=["curry", "curry_spices"], colors=Colors(label_base=orange), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- パックごはん


def cooked_rice_pack() -> Product:
    W, D, H = 150.0, 115.0, 37.0
    green, red, white = "#2E7D32", "#C62828", "#FFFFFF"
    s = 10

    def tray(w: float, seed: int) -> Canvas:
        """トレーの側面（半透明の白いトレー越しにごはんが少し見える）。"""
        f = Canvas(w, H, s, "#F2F2EE", seed)
        f.photo("cooked_rice", 0, 4, w, H, crop=(0.25, 0.35, 0.75, 0.6))
        f.img = Image.blend(f.img, Image.new("RGB", f.img.size, "#F4F4F0"), 0.6)
        f.d = ImageDraw.Draw(f.img)
        f.gradient(0, 0, w, 2.2, mix(green, white, 0.3), green)  # フィルムの縁
        f.rect(0, 2.2, w, 4.2, fill="#E4E4DE")  # トレーのフランジ
        x = 6.0
        while x < w - 4:  # 側面のリブ
            f.rect(x, 8, x + 0.6, H - 4, fill="#E2E2DB")
            x += 9.0
        f.rect(0, H - 1.5, w, H, fill="#D8D8D2")
        return f

    fr = tray(W, 1041)
    fr.text(W / 2, H - 6, "パックごはん  200g", 3.0, mix(green, white, 0.2), 700)
    bk = tray(W, 1042)
    sides = [tray(D, 1043).array(), tray(D, 1044).array()]

    tp = Canvas(W, D, s, white, 1045)
    tp.gradient(0, 0, W, D, "#FFFFFF", "#F3EFE2")
    tp.rect(0, 0, W, 16, fill=green)
    tp.text(W / 2, 8, "国内産米 100%  ふっくら炊きたて", 5.2, white, 800, max_w=W - 10)
    tp.photo("cooked_rice", 7, 22, 71, 86, shape="ellipse", feather=2, shadow=1.5, crop=(0.04, 0.10, 0.96, 0.92))
    tp.text(39, 91, "※写真はイメージです", 2.4, INK, 500)
    tp.text(110, 32, "パック", 9, green, 900)
    tp.text(110, 47, "ごはん", 13, INK, 900)
    tp.rect(84, 57, 136, 69, fill=red, radius=6)
    tp.text(110, 63, "200g", 7, white, 900)
    tp.rect(80, 74, 140, 98, fill=white, outline=green, width=0.4, radius=2)
    tp.text(110, 79.5, "電子レンジ 600W", 3.6, INK, 800)
    tp.text(110, 87, "約2分", 6.0, red, 900)
    tp.text(110, 94, "フィルムを少しはがして加熱", 2.6, INK, 600, max_w=56)
    for k in range(9):  # はがし口の点線（手前の左の角）
        t0, t1 = k / 9, k / 9 + 0.06
        tp.line([(3 + 22 * t0, 92 + 20 * t0), (3 + 22 * t1, 92 + 20 * t1)], red, 0.5)
    tp.text(30, 108, "← ここからはがす", 3.0, red, 800, anchor="lm")
    tp.rect(W - 40, D - 9, W, D, fill=mix(green, white, 0.75))
    tp.text(W - 20, D - 4.5, "賞味期限 2027.06.30", 2.6, INK, 700)

    bt = Canvas(W, D, s, "#F2F2EE", 1046)
    bt.gradient(0, 0, W, D, "#F6F6F2", "#E3E3DD")
    back_info(bt, 6, 6, 96, [
        ("名称", "包装米飯"), ("原材料名", "うるち米（国産）"), ("内容量", "200g"),
        ("賞味期限", "フィルムに記載"), ("保存方法", "直射日光・高温多湿を避け、常温で保存")], 2.6,
        [("栄養成分表示 1食（200g）当たり", ""), ("エネルギー", "294kcal"), ("たんぱく質", "4.6g"), ("脂質", "0.6g"),
         ("炭水化物", "68.4g"), ("食塩相当量", "0g")], INK)
    bt.barcode(105, 8, 36, 22)
    bt.recycle(113, 44, 9, "プラ", INK, sub="容器")
    bt.recycle(133, 44, 9, "プラ", INK, sub="フィルム")
    bt.text(102, 62, "【温め方】", 3.0, green, 900, anchor="lm")
    bt.paragraph(102, 66, W - 5, "フィルムを点線まではがし、600W で約2分、500W で約2分20秒温めます。"
                                 "加熱後は容器が熱くなるので注意してください。", 2.4, INK, 500)
    bt.rect(0, 0, W, 2, fill=green)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "film", 1051 + i, 0.6) for i, a in enumerate(imgs)]
    return Product(slug="cooked_rice_pack", name="パックごはん 200g", shape_class="box", category="food",
                   dims=Dimensions(0.037, 0.15, depth=0.115), mass_kg=0.215, material="plastic",
                   description="形は一般的なトレー入りの包装米飯（幅 150 mm・奥行き 115 mm・高さ 37 mm）で、寸法・質量は代表値。"
                               "トレーのテーパーとフランジは省略した直方体。",
                   tags=["ごはん", "パックごはん", "包装米飯", "電子レンジ", "cooked rice", "rice pack"],
                   photos=["cooked_rice"], colors=Colors(label_base="#F2F2EE"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 精米 5kg（袋）


def rice_bag_5kg() -> Product:
    W, H = 320.0, 470.0
    cream, green, red, white = "#FAF6EA", "#2F6B2F", "#B8322A", "#FFFFFF"
    c = Canvas(W, H, 4, cream, seed=1061)
    c.gradient(0, 0, W, H, "#FFFCF2", "#F1E8CF")
    c.photo("rice_field", 0, 300, W, H, crop=(0, 0.40, 1, 1))
    c.gradient(0, 292, W, 304, "#F2EAD3", mix("#F2EAD3", "#C9B46A", 0.4))
    seal_crimp(c, 0, 0, W, 14, "#E9DFC2", 2.2)
    seal_crimp(c, 0, H - 14, W, H, "#B9A563", 2.2)
    c.rect(0, 14, W, 20, fill=green)
    c.rect(0, H - 20, W, H - 14, fill=green)
    c.text(W / 2, 40, "国内産 複数原料米", 15, green, 800)
    c.text(W / 2, 62, "RICE  ━  POLISHED", 6, mix(green, cream, 0.3), 700, spacing=2)
    c.text(W / 2, 106, "精 米", 72, INK, 900)
    c.rect(W / 2 - 74, 148, W / 2 + 74, 172, fill=red, radius=12)
    c.text(W / 2, 160, "ふっくら炊きあがり", 12, white, 900)
    c.photo("cooked_rice", W / 2 - 92, 182, W / 2 + 58, 286, shape="ellipse", feather=3, shadow=3,
            crop=(0.04, 0.10, 0.96, 0.92))
    c.ellipse(W - 96, 196, W - 16, 276, fill=red, outline=white, width=2)
    c.text(W - 56, 230, "5kg", 26, white, 900)
    c.text(W - 56, 256, "内容量", 7, white, 700)
    c.text(W / 2 - 17, 292, "※写真はイメージです", 5, INK, 500)
    c.rect(W / 2 - 90, 404, W / 2 + 90, 436, fill=mix(cream, "#FFFFFF", 0.5), radius=6)
    c.text(W / 2, 414, "精米  5kg", 11, INK, 900)
    c.text(W / 2, 428, "国内産 複数原料米", 6.5, green, 800)
    front = trim_safe(edge_shade(finish(c.array(), "film", 1061, 1.0), 30, 0.15))

    # 裏面: 一括表示・炊き方・注意・バーコードをまとめる
    b = Canvas(W, H, 4, cream, seed=1062)
    b.gradient(0, 0, W, H, "#FFFCF2", "#F1E8CF")
    seal_crimp(b, 0, 0, W, 14, "#E9DFC2", 2.2)
    seal_crimp(b, 0, H - 14, W, H, "#B9A563", 2.2)
    b.rect(0, 14, W, 20, fill=green)
    b.rect(0, H - 20, W, H - 14, fill=green)
    b.text(W / 2, 36, "精米 5kg  国内産 複数原料米", 11, green, 900)
    b.rect(16, 50, W - 16, 150, fill=white, radius=4)
    y = back_info(b, 22, 56, W - 22, [
        ("名称", "精米"), ("原料玄米", "国内産 複数原料米"), ("内容量", "5kg"), ("精米年月日", "2026年10月上旬"),
        ("保存方法", "直射日光・高温多湿を避け、涼しい所で保存してください")], 8.0)
    b.rect(16, 162, W - 16, 262, fill=white, radius=4)
    b.rect(16, 162, W - 16, 178, fill=green, radius=4)
    b.text(W / 2, 170, "おいしいご飯の炊き方", 9, white, 900)
    b.paragraph(26, 186, W - 26, "1. 計量カップで正確に量り、たっぷりの水で手早くとぎます。\n"
                                 "2. 水がほぼ透明になるまで、2〜3回水を替えます。\n"
                                 "3. 炊飯器の目盛りに合わせて水を加え、30分以上浸してから炊きます。\n"
                                 "4. 炊きあがったら、すぐに全体をさっくりとほぐします。\n"
                                 "5. 長時間の保温は風味が落ちるので、早めにお召し上がりください。", 8.2, INK, 500)
    b.rect(16, 274, W - 16, 344, fill=mix(red, "#FFFFFF", 0.88), radius=4)
    b.text(26, 285, "【ご注意】", 8, red, 900, anchor="lm")
    b.paragraph(26, 294, W - 26, "お米は生鮮食品です。精米後はお早めにお召し上がりください。"
                                 "開封後は密閉容器に移し、冷蔵庫の野菜室などで保存すると風味が長持ちします。"
                                 "袋の持ち運びの際は、破れにご注意ください。", 7.0, INK, 500)
    b.rect(16, 360, 140, 440, fill=white, radius=4)
    b.barcode(24, 368, 108, 64)
    b.recycle(170, 400, 24, "プラ", green, sub="袋")
    b.rect(W - 112, 370, W - 16, 432, fill=white, radius=4)
    b.text(W - 64, 384, "保存の目安", 8, green, 900)
    b.text(W - 64, 402, "夏場 約1か月", 8, INK, 700)
    b.text(W - 64, 418, "冬場 約2か月", 8, INK, 700)
    back = trim_safe(edge_shade(finish(b.array(), "film", 1063, 1.0), 30, 0.15))
    return Product(slug="rice_bag_5kg", name="精米 5kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.47, 0.32, depth=0.1), mass_kg=5.05, material="film",
                   description="形は一般的な 5kg 入りの米袋（高さ 470 mm・幅 320 mm・厚さ約 100 mm）で、寸法・質量は代表値。"
                               "持ち手の穴は省略。",
                   tags=["米", "お米", "精米", "5kg", "rice", "rice bag"], photos=["rice_field", "cooked_rice"],
                   colors=Colors(label_base=cream), images=[front, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- 缶詰


def tuna_can() -> Product:
    form = _food_can(0.035, 0.066)
    blue, white, gold, navy = "#1F57A8", "#FFFFFF", "#F2C14E", "#0F2A55"
    c = label_canvas(form, blue, seed=1071)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#2766BF", "#173F80")
    c.pattern(0, 0, W, H - 4, "waves", mix("#2766BF", white, 0.12), 5, 0.4)
    c.rect(0, H - 4, W, H, fill=gold)
    c.photo("tuna", fx - 36, 1.5, fx - 6, H - 5, shape="ellipse", feather=0.6, shadow=0.6, crop=(0.25, 0.22, 0.82, 0.82))
    c.text(fx + 15, 7.5, "ツナ", 7.5, white, 900)
    c.text(fx + 15, 15.5, "油漬 フレーク", 3.8, gold, 800)
    c.text(fx + 15, 20.5, "まぐろ  70g", 3.0, white, 700)
    c.text(fx, H - 2, "※写真はイメージです   内容量 70g（固形量 50g）", 1.8, navy, 700)
    c.text(0.5 * W + 6, H - 2, "TUNA FLAKES", 2.0, navy, 800, spacing=0.4)
    bx = 0.25 * W
    c.rect(bx - 31, 1, bx + 36, 18.5, fill=white, radius=1)
    back_info(c, bx - 30, 1.6, bx + 6, [
        ("名称", "まぐろ油漬（フレーク）"), ("原材料名", "まぐろ、大豆油、食塩、野菜エキス"),
        ("内容量", "70g（固形量 50g）"), ("賞味期限", "缶ふたに記載")], 1.2)
    c.table(bx + 8, 1.6, bx + 35, "栄養成分表示 1缶当たり", [
        ("エネルギー", "190kcal"), ("たんぱく質", "12.1g"), ("脂質", "15.4g"), ("炭水化物", "0.1g"), ("食塩相当量", "0.6g")], 1.15)
    c.barcode(0.5 * W - 8, 2, 18, 11)
    c.recycle(0.5 * W + 1, 18.5, 5, "スチール", white, kind="can")
    label = finish(c.array(), "paper", 1071, 0.7)
    top = _eo_lid(form, 1072, "賞味期限 2029.10")
    return Product(slug="tuna_can", name="ツナ缶 油漬 70g", category="food", mass_kg=0.09, material="steel",
                   description="形は一般的な 70g のツナ缶（高さ 35 mm・胴径 66 mm、イージーオープン）で、寸法・質量は代表値。",
                   tags=["ツナ", "ツナ缶", "缶詰", "まぐろ", "tuna", "canned tuna"], photos=["tuna"],
                   colors=Colors(cap="#C3C6C9", label_base=blue), **revolve(form, label=label, top=top))


def mackerel_can() -> Product:
    form = _food_can(0.046, 0.084)
    navy, white, red = "#16325C", "#FFFFFF", "#C62828"
    c = label_canvas(form, white, seed=1081)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#E5ECF4")
    c.pattern(0, 5, W, H - 5, "waves", mix(navy, white, 0.85), 6, 0.5)
    c.rect(0, 0, W, 5, fill=navy)
    c.rect(0, H - 5, W, H, fill=navy)
    c.photo("mackerel", fx - 46, 8, fx - 2, H - 8, shape="round", radius=3, shadow=0.8, crop=(0.02, 0.28, 0.88, 0.75))
    c.text(fx - 24, H - 6.4, "※写真はイメージです", 1.7, navy, 600)
    c.text(fx + 22, 12.5, "さば", 10, navy, 900)
    c.text(fx + 22, 23, "水煮", 8, navy, 900)
    c.text(fx + 22, 30.5, "国産さば使用", 3.0, red, 800)
    c.text(fx, H - 2.5, "内容総量 190g（固形量 140g）", 2.8, white, 700)
    c.text(fx, 2.5, "MACKEREL IN WATER", 2.4, white, 800, spacing=0.5)
    c.text(0.5 * W, 2.5, "SABA", 2.4, white, 800, spacing=0.5)
    c.rect(28, 7, 116, 27.5, fill=white, radius=1)
    back_info(c, 29, 7.6, 77, [
        ("名称", "さば水煮"), ("原材料名", "さば（国産）、食塩"), ("内容総量", "190g"), ("固形量", "140g"),
        ("賞味期限", "缶ふたに記載"), ("保存方法", "直射日光を避け、常温で保存")], 1.45, color=navy)
    c.table(79, 7.6, 115, "栄養成分表示 1缶当たり", [
        ("エネルギー", "320kcal"), ("たんぱく質", "29.8g"), ("脂質", "22.4g"), ("炭水化物", "0.3g"),
        ("食塩相当量", "1.6g")], 1.45, navy)
    c.barcode(119, 8, 24, 14)
    c.recycle(131, 29, 6, "スチール", navy, kind="can")
    label = finish(c.array(), "paper", 1081, 0.7)
    top = _eo_lid(form, 1082, "賞味期限 2029.09")
    return Product(slug="mackerel_can", name="さば水煮缶 190g", category="food", mass_kg=0.23, material="steel",
                   description="形は一般的な 190g のさば缶（高さ 46 mm・胴径 84 mm、イージーオープン）で、寸法・質量は代表値。",
                   tags=["さば", "さば缶", "水煮", "缶詰", "mackerel", "canned fish"], photos=["mackerel"],
                   colors=Colors(cap="#C3C6C9", label_base=white), **revolve(form, label=label, top=top))


def peach_can() -> Product:
    form = _food_can(0.113, 0.074)
    rose, dark, white, green = "#E8798A", "#A3324A", "#FFFFFF", "#5E8C3A"
    c = label_canvas(form, white, seed=1091)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFF5EF", "#F9D3CA")
    c.pattern(0, 12, W, H - 4, "dots", mix("#F9D3CA", white, 0.5), 6, 0.6)
    c.rect(0, 0, W, 12, fill=rose)
    c.rect(0, H - 4, W, H, fill=green)
    c.text(fx, 6, "WHITE PEACH", 4.0, white, 800, spacing=0.8)
    c.text(0.5 * W, 6, "白桃", 4.4, white, 900)
    c.photo("peach", fx - 30, 15, fx + 30, 60, shape="ellipse", feather=1.5, shadow=1.5, crop=(0.36, 0.30, 0.62, 0.85))
    c.text(fx, 63, "※写真はイメージです", 2.0, INK, 500)
    c.text(fx, 74, "白桃", 16, dark, 900)
    c.rect(fx - 27, 84, fx + 27, 92, fill=rose, radius=4)
    c.text(fx, 88, "ハーフカット  シラップづけ", 3.4, white, 800, max_w=50)
    c.text(fx, 97, "内容総量 425g（固形量 250g）", 3.0, INK, 700)
    bx = 0.25 * W
    c.rect(bx - 28, 15, bx + 28, 66, fill=white, radius=1.5)
    back_info(c, bx - 27, 16, bx + 27, [
        ("名称", "白桃シラップづけ"), ("原材料名", "白桃、砂糖、ぶどう糖果糖液糖／酸味料、酸化防止剤（ビタミンC）"),
        ("内容総量", "425g"), ("固形量", "250g"), ("賞味期限", "缶ふたに記載"), ("保存方法", "直射日光を避け、常温で保存")], 2.0,
        [("栄養成分表示 100g当たり", ""), ("エネルギー", "82kcal"), ("たんぱく質", "0.4g"), ("脂質", "0.1g"),
         ("炭水化物", "20.2g"), ("食塩相当量", "0g")], dark)
    c.barcode(0.5 * W - 12, 18, 24, 16)
    c.recycle(0.5 * W, 47, 8, "スチール", dark, kind="can")
    c.paragraph(0.5 * W - 13, 60, 0.5 * W + 13, "開缶後はガラスなどの容器に移し、冷蔵庫に入れてお早めにお召し上がりください。",
                2.2, INK, 500)
    label = finish(c.array(), "paper", 1091, 0.7)
    top = _eo_lid(form, 1092, "賞味期限 2029.08")
    return Product(slug="peach_can", name="白桃 缶詰 425g", category="food", mass_kg=0.48, material="steel",
                   description="形は一般的な 4 号缶の果物缶詰（高さ 113 mm・胴径 74 mm、イージーオープン）で、寸法・質量は代表値。",
                   tags=["白桃", "もも", "桃缶", "缶詰", "フルーツ", "canned peach", "peach"], photos=["peach"],
                   colors=Colors(cap="#C3C6C9", label_base="#FFF5EF"), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- 調味料


def soy_sauce_pet() -> Product:
    form = forms.pet_bottle(0.250, 0.080, shoulder=0.16, neck_r=0.0135, cap_h=0.026, cap_r=0.0170,
                            label=(0.060, 0.160), liquid_top=0.190)
    white, red, liquid = "#FFFFFF", "#B71C1C", "#3A1A0E"
    c = label_canvas(form, white, seed=1101)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#F6EFE2")
    c.rect(0, 0, W, 6, fill=red)
    c.rect(0, H - 6, W, H, fill=red)
    c.rect(fx - 22, 11, fx + 22, 82, fill=white, outline=red, width=0.8, radius=2)
    c.vtext(fx + 7, 20, "しょうゆ", 13, INK, 900, gap=0.08)
    c.vtext(fx - 12, 19, "こいくち", 5.5, red, 900)
    c.rect(fx - 17, 46, fx - 7, 70, fill=red, radius=1.5)
    c.vtext(fx - 12, 51, "本醸造", 5.0, white, 900)
    c.text(fx, 89, "濃口しょうゆ  1L", 4.6, INK, 900)
    c.text(fx, 3, "SOY SAUCE", 3.0, white, 800, spacing=0.8)
    c.text(fx, H - 3, "1000ml", 3.2, white, 800)
    c.text(0.5 * W, H - 3, "開栓後は冷蔵庫に保存してください", 2.4, white, 700)
    _bottle_back(c, 0.25 * W, 9, 50, "こいくちしょうゆ（本醸造）", "脱脂加工大豆（国内製造）、小麦、食塩、大豆／アルコール", 2.0,
                 extra=[("内容量", "1L"), ("賞味期限", "キャップ付近に記載"), ("保存方法", "直射日光を避け、常温で保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（15ml）当たり", ""), ("エネルギー", "13kcal"), ("たんぱく質", "1.2g"),
                            ("脂質", "0g"), ("炭水化物", "1.5g"), ("食塩相当量", "2.6g")])
    c.barcode(0.5 * W - 13, 14, 26, 16)
    c.recycle(0.5 * W - 7, 50, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 50, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 1101, 0.8)
    return Product(slug="soy_sauce_pet", name="こいくちしょうゆ 1L", category="food", mass_kg=1.22, capacity_ml=1000,
                   material="PET",
                   description="形は一般的な 1L のしょうゆ用 PET ボトル（高さ 250 mm・胴径 80 mm）で、寸法・質量は代表値。持ち手のくびれは省略。",
                   tags=["しょうゆ", "醤油", "調味料", "ペットボトル", "soy sauce", "seasoning"], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base=white),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def sesame_dressing() -> Product:
    form = forms.pet_bottle(0.200, 0.064, shoulder=0.20, neck_r=0.012, cap_h=0.028, cap_r=0.0165,
                            label=(0.020, 0.115), liquid_top=0.150)
    cream, brown, gold, white, liquid = "#FBF3E4", "#4E2E17", "#D9A441", "#FFFFFF", "#D9BE8E"
    c = label_canvas(form, cream, seed=1111)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FDF7EC", "#EDDDBE")
    c.photo("sesame", 0, H - 18, W, H, crop=(0.22, 0.44, 0.9, 0.56))
    c.gradient(0, H - 21, W, H - 18, "#EDDDBE", mix("#EDDDBE", "#B89A6A", 0.5))
    c.rect(0, 0, W, 7, fill=brown)
    c.text(fx, 3.5, "SESAME DRESSING", 3.0, gold, 800, spacing=0.6)
    c.text(0.25 * W, 3.5, "ROASTED SESAME", 2.6, gold, 700, spacing=0.4)
    c.photo("salad", fx - 26, 10, fx + 26, 44, shape="ellipse", feather=1.2, shadow=1.0, crop=(0, 0.03, 0.96, 0.98))
    c.text(fx, 46.5, "※写真はイメージです", 1.8, brown, 500)
    c.text(fx, 55, "ごま", 11, brown, 900)
    c.text(fx, 66, "ドレッシング", 6.4, brown, 900, max_w=50)
    c.rect(fx - 24, 70, fx + 24, 76, fill=brown, radius=3)
    c.text(fx, 73, "香ばしい焙煎ごま", 3.4, cream, 800)
    c.text(fx, H - 9, "380ml", 5.0, white, 900, stroke=0.4, stroke_fill=brown)
    bx = 0.25 * W
    c.rect(bx - 27, 9, bx + 27, 57, fill=white, radius=1.5)
    _bottle_back(c, bx, 10, 52, "乳化液状ドレッシング",
                 "食用植物油脂（国内製造）、ごま、しょうゆ、砂糖、醸造酢、卵黄、食塩、ごま油／調味料（アミノ酸）、増粘剤（キサンタン）", 1.7,
                 extra=[("内容量", "380ml"), ("賞味期限", "キャップに記載"), ("保存方法", "開栓後は冷蔵庫に保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（15g）当たり", ""), ("エネルギー", "68kcal"), ("たんぱく質", "0.4g"),
                            ("脂質", "6.8g"), ("炭水化物", "1.3g"), ("食塩相当量", "0.4g")], color=brown)
    c.barcode(0.5 * W - 11, 11, 22, 14)
    c.recycle(0.5 * W - 6, 39, 7, "プラ", brown, sub="容器")
    c.recycle(0.5 * W + 6, 39, 7, "プラ", brown, sub="キャップ")
    c.paragraph(0.5 * W - 11, 52, 0.5 * W + 12, "よく振ってから\nお使いください", 2.4, brown, 800)
    label = finish(c.array(), "film", 1111, 0.7)
    return Product(slug="sesame_dressing", name="ごまドレッシング 380ml", category="food", mass_kg=0.41, capacity_ml=380,
                   material="PET",
                   description="形は一般的な 380ml のドレッシングボトル（高さ 200 mm・胴径 64 mm）で、寸法・質量は代表値。",
                   tags=["ドレッシング", "ごま", "ごまドレッシング", "調味料", "sesame dressing", "dressing"],
                   photos=["salad", "sesame"], colors=Colors(cap="#F3EBDD", liquid=liquid, label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def mayonnaise_bottle() -> Product:
    form = _squeeze_bottle(0.198, 0.068, body_h=0.168, neck_r=0.0135, cap_r=0.0175, cap_h=0.018, tip_r=0.0045,
                           label=(0.040, 0.120), liquid_top=0.150)
    cream, green, yellow, white, liquid = "#FFFBEA", "#2F6E3B", "#F3C623", "#FFFFFF", "#F2DE9C"
    c = label_canvas(form, cream, seed=1121)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFDF4", "#FFF0BF")
    c.rect(0, 0, W, 5, fill=green)
    c.rect(0, H - 5, W, H, fill=green)
    c.rect(0, 5, W, 6.2, fill=yellow)
    c.text(fx, 15.5, "マヨネーズ", 9.5, green, 900, max_w=62)
    c.text(fx, 26, "卵黄タイプ  コクのある味わい", 3.4, mix(green, yellow, 0.3), 800, max_w=60)
    c.photo("salad", fx - 22, 30, fx + 22, 60, shape="ellipse", feather=1.0, shadow=0.8, crop=(0, 0.03, 0.96, 0.98))
    c.text(fx, 62.3, "※写真はイメージです", 1.6, INK, 500)
    c.rect(fx - 18, 65, fx + 18, 73, fill=yellow, radius=4)
    c.text(fx, 69, "450g", 5.0, green, 900)
    c.text(fx, H - 2.5, "MAYONNAISE", 2.8, white, 800, spacing=0.8)
    c.text(0.25 * W, H - 2.5, "開封後は要冷蔵", 2.4, white, 700)
    y = _bottle_back(c, 0.25 * W, 8, 50, "半固体状ドレッシング",
                 "食用植物油脂（国内製造）、卵黄、醸造酢、食塩、香辛料／調味料（アミノ酸）、香辛料抽出物", 1.8,
                 extra=[("内容量", "450g"), ("賞味期限", "キャップに記載"),
                        ("保存方法", "開封前は直射日光を避けて保存。開封後は冷蔵庫（1〜10℃）に保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（12g）当たり", ""), ("エネルギー", "84kcal"), ("たんぱく質", "0.3g"),
                            ("脂質", "9.0g"), ("炭水化物", "0.1g"), ("食塩相当量", "0.2g")], color=green)
    # 楕円断面なので、側面（0.5W 付近）は避けて裏面のパネルに寄せる
    bx = 0.25 * W
    c.barcode(bx - 25, y + 1.5, 24, min(14.0, H - 7 - y))
    c.recycle(bx + 8, y + 6, 6.5, "プラ", green, sub="容器")
    c.recycle(bx + 19, y + 6, 6.5, "プラ", green, sub="キャップ")
    label = finish(c.array(), "film", 1121, 0.7)
    return Product(slug="mayonnaise_bottle", name="マヨネーズ 450g", category="food", mass_kg=0.47, material="plastic",
                   description="形は一般的な 450g のマヨネーズのやわらかいボトル（高さ 198 mm・幅 68 mm・奥行き 44 mm の楕円断面）で、"
                               "寸法・質量は代表値。",
                   tags=["マヨネーズ", "調味料", "ドレッシング", "mayonnaise", "seasoning"], photos=["salad"],
                   colors=Colors(cap="#E53935", liquid=liquid, label_base=cream),
                   **revolve(form, label=label, body_fill=None, liquid=liquid, depth=0.044))


# ---------------------------------------------------------------- 瓶


def strawberry_jam_jar() -> Product:
    form = forms.jar(0.100, 0.072, cap_h=0.016, cap_d=0.068, label=(0.018, 0.074))
    form.liquid_top = 0.080
    red, cream, white, liquid = "#C0182F", "#FFF8F0", "#FFFFFF", "#8E1426"
    c = label_canvas(form, cream, seed=1131)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFF9F2", "#FBE3D8")
    _checks(c, 0, 0, W, 8, red, 2.0)
    c.rect(0, 8, W, 9, fill=red)
    c.rect(0, H - 5, W, H, fill=red)
    c.photo("strawberry", fx - 31, 11, fx - 3, 44, shape="ellipse", feather=1.0, shadow=1.0, crop=(0.08, 0.05, 0.72, 0.92))
    c.text(fx - 17, 47.5, "※写真はイメージです", 1.6, INK, 500)
    c.text(fx + 14, 18, "いちご", 8.0, red, 900)
    c.text(fx + 14, 28, "ジャム", 8.0, red, 900)
    c.text(fx + 14, 36, "果肉たっぷり", 3.4, INK, 800)
    c.text(fx + 14, 42.5, "300g", 4.0, red, 900)
    c.text(fx, H - 2.5, "STRAWBERRY JAM", 2.8, white, 800, spacing=0.6)
    c.text(0.5 * W, H - 2.5, "開封後要冷蔵", 2.4, white, 700)
    bx = 0.25 * W
    c.rect(bx - 28, 10, bx + 28, 37, fill=white, radius=1.5)
    back_info(c, bx - 27, 10.6, bx + 27, [
        ("名称", "いちごジャム"), ("原材料名", "いちご（国内製造）、砂糖、水あめ／ゲル化剤（ペクチン）、酸味料"),
        ("内容量", "300g"), ("賞味期限", "ふたに記載"), ("保存方法", "開封後は冷蔵庫に保存")], 1.45,
        [("栄養成分表示 大さじ1杯（20g）当たり", ""), ("エネルギー", "51kcal"), ("炭水化物", "12.6g"), ("食塩相当量", "0g")], red)
    c.barcode(0.5 * W - 10, 12, 20, 13)
    c.recycle(0.5 * W, 37, 6, "スチール", red, kind="can")
    c.text(0.5 * W, 45, "ふた", 1.8, red, 600)
    label = finish(c.array(), "paper", 1131, 0.6)

    t = top_canvas(form, red, seed=1132)
    d = t.w_mm
    t.rect(0, 0, d, d, fill=white)
    _checks(t, 0, 0, d, d, red, d / 14)
    t.ellipse(1.2, 1.2, d - 1.2, d - 1.2, outline="#8A1022", width=1.0)
    t.ellipse(d * 0.2, d * 0.24, d * 0.8, d * 0.76, fill=cream, outline=red, width=0.6)
    t.text(d / 2, d * 0.42, "いちご", 7.0, red, 900)
    t.text(d / 2, d * 0.55, "ジャム", 7.0, red, 900)
    t.text(d / 2, d * 0.66, "賞味期限 2027.09", 2.2, INK, 600)
    top = finish(t.array(), "metal", 1132, 0.5)
    return Product(slug="strawberry_jam_jar", name="いちごジャム 300g", category="food", mass_kg=0.5, material="glass",
                   description="形は一般的な瓶入りのジャム（高さ 100 mm・胴径 72 mm、金属のねじ蓋）で、寸法・質量は代表値。",
                   tags=["ジャム", "いちご", "いちごジャム", "瓶", "strawberry jam", "jam"], photos=["strawberry"],
                   colors=Colors(cap=red, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


def instant_coffee_jar() -> Product:
    form = forms.jar(0.120, 0.075, cap_h=0.024, cap_d=0.073, label=(0.022, 0.088))
    form.liquid_top = 0.092
    brown, gold, cream, liquid = "#2E1B10", "#C99A45", "#F3E6CF", "#3A2416"
    c = label_canvas(form, brown, seed=1141)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#43291A", "#1E120A")
    c.rect(0, 4, W, 5, fill=gold)
    c.rect(0, H - 5, W, H - 4, fill=gold)
    c.photo("coffee_cup", fx - 28, 8, fx + 28, 40, shape="ellipse", feather=1.2, shadow=0.8, crop=(0.1, 0.1, 0.9, 0.9))
    c.text(fx + 29, 38, "※写真はイメージです", 1.6, cream, 500, anchor="lm")
    c.text(fx, 46, "インスタントコーヒー", 5.4, cream, 900, max_w=58)
    c.text(fx, 53, "香り深い まろやかブレンド", 3.0, gold, 700, max_w=56)
    c.text(fx, 58.5, "80g", 3.6, cream, 900)
    c.text(fx, 2, "INSTANT COFFEE", 2.4, gold, 700, spacing=0.6)
    c.text(0.5 * W, H - 2, "約40杯分", 2.4, gold, 700)
    bx = 0.25 * W
    c.rect(bx - 28, 7, bx + 28, 25, fill=cream, radius=1.5)
    back_info(c, bx - 27, 7.6, bx + 27, [
        ("名称", "インスタントコーヒー"), ("原材料名", "コーヒー豆（生豆生産国名：ブラジル、ベトナム、その他）"),
        ("内容量", "80g"), ("賞味期限", "ふたに記載"), ("保存方法", "高温多湿を避け、使用後はふたをしっかり閉めてください")], 1.6,
        color=brown, bg=cream)
    c.barcode(0.5 * W - 11, 8, 22, 14)
    c.text(0.5 * W, 28, "おいしい飲み方", 2.6, gold, 900)
    c.paragraph(0.5 * W - 13, 31, 0.5 * W + 13, "ティースプーン山盛り1杯（約2g）に熱湯 約140ml を注いでください。", 2.2, cream, 500)
    c.recycle(0.5 * W - 6, 52, 6, "プラ", cream, sub="ふた")
    c.recycle(0.5 * W + 6, 52, 6, "紙", cream, sub="ラベル")
    label = finish(c.array(), "paper", 1141, 0.6)

    t = top_canvas(form, "#4A2C1A", seed=1142)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#5A3721", "#3A2213")
    t.ellipse(1.5, 1.5, d - 1.5, d - 1.5, outline=gold, width=0.8)
    t.ellipse(d * 0.12, d * 0.12, d * 0.88, d * 0.88, outline=mix(gold, "#4A2C1A", 0.5), width=0.4)
    t.text(d / 2, d * 0.40, "COFFEE", 9.0, gold, 900, spacing=0.8)
    t.text(d / 2, d * 0.54, "インスタントコーヒー", 4.0, cream, 800)
    t.text(d / 2, d * 0.66, "賞味期限 2028.03", 2.4, cream, 500)
    top = finish(t.array(), "film", 1142, 0.5)
    return Product(slug="instant_coffee_jar", name="インスタントコーヒー 80g", category="food", mass_kg=0.33,
                   material="glass",
                   description="形は一般的な瓶入りのインスタントコーヒー（高さ 120 mm・胴径 75 mm、ねじ蓋）で、寸法・質量は代表値。",
                   tags=["コーヒー", "インスタントコーヒー", "瓶", "instant coffee", "coffee"], photos=["coffee_cup"],
                   colors=Colors(cap="#4A2C1A", liquid=liquid, label_base=brown),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


def salt_pepper_shaker() -> Product:
    form = forms.jar(0.135, 0.058, cap_h=0.030, cap_d=0.0585, label=(0.012, 0.096))
    form.liquid_top = 0.100
    white, red, liquid = "#FFFFFF", "#C62828", "#B8B0A2"
    c = label_canvas(form, white, seed=1151)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#F2EEE6")
    c.rect(0, 0, W, 6, fill=red)
    c.rect(0, H - 6, W, H, fill=red)
    c.text(fx, 17, "塩こしょう", 10, INK, 900, max_w=54)
    c.text(fx, 28, "あらびき胡椒入り", 3.8, red, 800)
    c.ellipse(fx - 21, 33, fx + 21, 66, fill="#EDE6DA")
    rng = c.rng
    for _ in range(260):  # 塩とこしょうの粒
        a, r = rng.uniform(0, 6.283), rng.uniform(0, 1) ** 0.5
        x, y = fx + 19 * r * np.cos(a), 49.5 + 15 * r * np.sin(a)
        g = rng.uniform(0.25, 0.7)
        col = "#FFFFFF" if rng.random() < 0.55 else rng.choice(["#2B2420", "#4A3C32", "#6B5A4A"])
        c.ellipse(x - g, y - g, x + g, y + g, fill=col)
    c.rect(fx - 24, 69, fx + 24, 76, fill=INK, radius=3.5)
    c.text(fx, 72.5, "下味・炒め物に", 3.6, white, 800)
    c.text(fx, 3, "SALT & PEPPER", 2.8, white, 800, spacing=0.6)
    c.text(fx, H - 3, "内容量 250g", 3.0, white, 800)
    c.text(0.5 * W, H - 3, "PEPPER", 2.4, white, 700, spacing=0.4)
    _bottle_back(c, 0.25 * W, 9, 46, "食塩こしょう", "食塩（国内製造）、こしょう、ぶどう糖／調味料（アミノ酸）", 1.8,
                 extra=[("内容量", "250g"), ("賞味期限", "底面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")],
                 nutrition=[("栄養成分表示 1g当たり", ""), ("エネルギー", "0.4kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
                            ("炭水化物", "0.1g"), ("食塩相当量", "0.8g")])
    c.barcode(0.5 * W - 10, 10, 20, 13)
    c.recycle(0.5 * W - 6, 36, 6.5, "プラ", INK, sub="容器")
    c.recycle(0.5 * W + 6, 36, 6.5, "プラ", INK, sub="キャップ")
    label = finish(c.array(), "film", 1151, 0.6)

    t = top_canvas(form, red, seed=1152)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D84040", "#A81E1E")
    t.ellipse(1.2, 1.2, d - 1.2, d - 1.2, outline="#7E1515", width=0.8)
    t.line([(d * 0.1, d * 0.5), (d * 0.9, d * 0.5)], "#8E1818", 0.4)  # ふたの合わせ目
    t.ellipse(d * 0.2, d * 0.55, d * 0.8, d * 0.88, fill="#B52525", outline="#8E1818", width=0.3)
    for row in range(4):  # 小さい穴（手前の半分）
        for k in range(-3 + row % 2, 4, 2):
            x, y = d / 2 + k * d * 0.055, d * 0.62 + row * d * 0.065
            t.ellipse(x - 0.9, y - 0.9, x + 0.9, y + 0.9, fill="#3A0A0A")
    t.rect(d * 0.3, d * 0.18, d * 0.7, d * 0.40, fill="#B52525", outline="#8E1818", width=0.3, radius=3)
    t.text(d / 2, d * 0.29, "大きい穴", 2.8, "#FFE0E0", 800)
    t.text(d / 2, d * 0.93, "ふりかけ口", 2.0, "#FFE0E0", 700)
    top = finish(t.array(), "film", 1152, 0.5)
    return Product(slug="salt_pepper_shaker", name="塩こしょう 250g", category="food", mass_kg=0.29, material="plastic",
                   description="形は一般的な振り出し容器入りの塩こしょう（高さ 135 mm・胴径 58 mm）で、寸法・質量は代表値。",
                   tags=["塩こしょう", "こしょう", "塩", "調味料", "スパイス", "salt and pepper", "seasoning"], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base=white),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


PRODUCTS = {f.__name__: f for f in (
    retort_curry_box, curry_roux_box, cooked_rice_pack, rice_bag_5kg, tuna_can, mackerel_can, peach_can,
    soy_sauce_pet, sesame_dressing, mayonnaise_bottle, strawberry_jam_jar, instant_coffee_jar, salt_pepper_shaker)}
