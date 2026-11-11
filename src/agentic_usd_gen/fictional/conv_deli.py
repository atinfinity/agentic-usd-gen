"""架空の商品のデザイン: コンビニの中食・ホットスナック・冷凍食品。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
写真は CC0 の素材（photos.json の deli_* など）だけを合成し、参考にした写真の出典は各関数の docstring に書く。
"""

from __future__ import annotations

import math

import numpy as np

from ..shapes.assembly import prism_outline
from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .food_fresh_snack import _back_panel, _pouch
from .paint import Canvas, edge_shade, finish, mix
from .products import INK, _box, _face, _food, _food_photo, back_info, seal_crimp, steam

CLEAR = "#F2F6F8"
WHITE = "#FFFFFF"
NORI, NORI_DARK = "#26301F", "#141A11"
BREAD = "#EADBB8"


def _sticker(w: float, h: float, title: str, sub: str, price: int, kcal: int, accent: str, seed: int,
             heat: str | None = None, keep: str = "要冷蔵（10℃以下）"):
    """フタに貼る商品名と値札のシール（ダミーのバーコード付き）。"""
    c = Canvas(w, h, 14, WHITE, seed)
    c.rect(0, 0, w, h * 0.40, fill=accent)
    c.text(w / 2, h * 0.13, sub, h * 0.10, mix(accent, WHITE, 0.78), 800, max_w=w - 6)
    c.text(w / 2, h * 0.29, title, h * 0.17, WHITE, 900, max_w=w - 6)
    c.text(3, h * 0.50, "消費期限 26.10.19 午後2時", h * 0.07, INK, 700, anchor="lm", max_w=w * 0.55)
    c.text(3, h * 0.60, f"熱量 {kcal}kcal", h * 0.07, INK, 700, anchor="lm")
    c.text(3, h * 0.70, heat or keep, h * 0.065, accent if heat else INK, 800, anchor="lm", max_w=w * 0.55)
    c.text(w - 3, h * 0.58, f"{price}円", h * 0.16, accent, 900, anchor="rm", max_w=w * 0.4)
    c.barcode(w * 0.56, h * 0.74, w * 0.40, h * 0.22)
    c.text(3, h * 0.86, "税込価格", h * 0.06, INK, 600, anchor="lm")
    return _face(c.array(), "paper", seed, 0.5)


def _rice(c: Canvas, x0: float, y0: float, x1: float, y1: float):
    """ごはんの粒（写真の上に明るい粒を散らす）。"""
    c.photo("cooked_rice", x0, y0, x1, y1, crop=(0.30, 0.28, 0.70, 0.62))
    c.rect(x0, y0, x1, y1, fill="#EEEBE2")
    n = int((x1 - x0) * (y1 - y0) / 1.6)
    for _ in range(n):  # 米粒（長さ 4〜5 mm）。少し傾けた楕円の代わりに縦横をばらつかせる
        x, y = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        a, b = (2.3, 1.2) if c.rng.random() < 0.5 else (1.3, 2.1)
        c.ellipse(x - a, y - b, x + a, y + b, fill=mix("#FFFFFF", "#D9D3C2", c.rng.uniform(0, 0.7)),
                  outline=mix("#FFFFFF", "#BDB5A0", 0.6), width=0.15)


def _nori(c: Canvas, x0: float, y0: float, x1: float, y1: float):
    """のり（つやのある黒緑に細かいむら）。"""
    c.gradient(x0, y0, x1, y1, NORI, NORI_DARK)
    n = int((x1 - x0) * (y1 - y0) / 3)
    for _ in range(n):
        x, y = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        a = c.rng.uniform(0.4, 1.4)
        c.ellipse(x - a, y - a * 0.4, x + a, y + a * 0.4, fill=mix(NORI, "#4A5A35", c.rng.uniform(0, 0.7)))


# ---------------------------------------------------------------- おにぎり・サンドイッチ（角の丸い三角柱）


def onigiri_salmon() -> Product:
    """フィルムで包んだ手巻きおにぎり（角の丸い三角柱 prism 1 つ）。正面・背面に、フィルムごしのごはんとのり、
    中央の開け口テープ、商品名ラベルを描く。側面（厚み）はのりの色。

    参考: https://commons.wikimedia.org/wiki/File:Store_bought_rice_ball_-_Japan_-_Nov_8_2017.jpg（CC0）
    """
    W, H, D = 100.0, 92.0, 38.0
    red, salmon, white = "#C62828", "#F08A5D", WHITE
    s = 10

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, s, NORI, seed)
        _rice(c, 0, 0, W, H * 0.62)
        _nori(c, 0, H * 0.58, W, H)
        c.line([(0, H * 0.58), (W, H * 0.58)], mix(NORI, "#7A8A62", 0.4), 0.5)
        for k in range(14):  # フィルムの光り（細い斜めの線）
            x = 8 + k * 7
            c.line([(x, H * 0.62), (x + 5, H * 0.95)], mix(NORI, "#FFFFFF", 0.10), 0.3)
        return c

    fr = base(5001)
    tw = 9.0  # 開け口のテープ（頂点から底まで）
    fr.rect(W / 2 - tw / 2, 0, W / 2 + tw / 2, H, fill=red)
    fr.rect(W / 2 - tw / 2 + 0.8, 0, W / 2 - tw / 2 + 1.3, H, fill="#E57373")
    fr.ellipse(W / 2 - 4, 13, W / 2 + 4, 21, fill=white)
    fr.text(W / 2, 17, "1", 5.5, red, 900)
    for y in (27, 33):
        fr.polygon([(W / 2 - 2.5, y), (W / 2 + 2.5, y), (W / 2, y + 3)], fill=white)
    lx0, lx1, ly0, ly1 = 21, 79, 50, 80  # 商品名ラベル（テープの上に貼る）
    fr.rect(lx0, ly0, lx1, ly1, fill=white, radius=3, outline=salmon, width=0.6)
    fr.rect(lx0, ly0, lx1, ly0 + 7, fill=salmon, radius=3)
    fr.rect(lx0, ly0 + 4, lx1, ly0 + 7, fill=salmon)
    fr.text(W / 2, ly0 + 3.6, "手巻おにぎり", 4.0, white, 900)
    fr.text(W / 2 - 9, ly0 + 15.5, "鮭", 13, red, 900)
    fr.text(W / 2 + 10, ly0 + 12.5, "焼き鮭", 4.2, INK, 900)
    fr.text(W / 2 + 10, ly0 + 18.5, "ほぐし身", 3.4, INK, 800)
    fr.text(W / 2, ly0 + 26, "SALMON  しお味", 2.8, salmon, 800, spacing=0.2)
    for k, x in enumerate((7.0, W - 7.0)):  # 左右の角の引き手
        fr.ellipse(x - 3.2, H - 9.5, x + 3.2, H - 3.1, fill=white)
        fr.text(x, H - 6.3, "2" if k == 0 else "3", 4.2, red, 900)

    bk = base(5002)
    bk.rect(W / 2 - tw / 2, 0, W / 2 + tw / 2, H * 0.35, fill=red)
    px0, px1, py0 = 16, 84, 36
    bk.rect(px0, py0, px1, H - 3, fill=white, radius=2)
    bk.rect(px0, py0, px1, py0 + 6, fill=red, radius=2)
    bk.rect(px0, py0 + 3, px1, py0 + 6, fill=red)
    bk.text(W / 2, py0 + 3.2, "開け方", 3.6, white, 900)
    bk.paragraph(px0 + 2, py0 + 8, px1 - 2, "① 中央のテープを下まで引く\n② 左右のフィルムを横に引く\n③ のりで包んでお召し上がりください",
                 2.2, INK, 700)
    back_info(bk, px0 + 2, py0 + 21, px1 - 30, [
        ("名称", "おにぎり"), ("原材料名", "ご飯、焼き鮭、のり、食塩／調味料（アミノ酸等）"),
        ("消費期限", "表面に記載")], 1.4)
    bk.barcode(px1 - 26, py0 + 22, 22, 14)
    bk.recycle(px1 - 15, H - 10, 6, "プラ", red, sub="フィルム")
    imgs = [_face(c.array(), "film", 5001 + i, 0.6, 6) for i, c in enumerate((fr, bk))]
    body = Part("Body", "prism", [W / 1000, D / 1000, H / 1000], [0, 0, H / 2000], color=NORI, finish="plastic",
                faces={"front": 0, "back": 1}, material="food")
    return Product(slug="onigiri_salmon", name="手巻おにぎり 鮭", shape_class="assembly", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.11, material="film",
                   description="形は一般的なコンビニのフィルム包装の手巻きおにぎり（幅 100 mm・高さ 92 mm・厚さ 38 mm の"
                               "角の丸い三角形）で、寸法・質量は代表値。フィルムごしのごはんとのり、開け口のテープは描いた絵。",
                   tags=["おにぎり", "手巻おにぎり", "鮭", "しゃけ", "中食", "rice ball", "onigiri",
                         "salmon rice ball in film wrap"],
                   photos=["cooked_rice"], colors=Colors(label_base=NORI), images=imgs, parts=[body])


def sandwich_mixed_pack() -> Product:
    """透明な三角柱のパック（側面が直角三角形で、斜めの面が正面の上を向く）に、三角のサンドイッチ 4 切れを立てて並べる。
    サンドイッチはパンと具の薄い三角柱を重ねた形で、斜めの切り口に具の層が見える。斜めの面に商品名シール。

    参考: https://commons.wikimedia.org/wiki/File:Tamagosando01.jpg（CC0）
    """
    green = "#2E7D32"
    PD, PW, PH = 0.088, 0.100, 0.110  # パックの奥行き（断面の底辺）・幅・高さ
    tri = [[-0.5, 0.0, 0.06], [0.5, 0.0, 0.06], [0.5, 1.0, 0.06]]  # 背面（+Y）が垂直の直角三角形
    base_h = 0.002
    parts = [_box("Base", (PW + 0.004, PD + 0.004, base_h), (0, 0, base_h / 2), CLEAR, "glass", thin_walled=True),
             Part("Pack", "prism", [PD, PW, PH], [0, 0, base_h + PH / 2], [0, 0, 90], color=CLEAR, finish="glass", thin_walled=True,
                  profile=tri)]
    sd, sh = 0.080, 0.100  # サンドイッチの断面の底辺・高さ（パックと同じ傾き）
    sy = PD / 2 - 0.003 - sd / 2
    egg = [(0.007, BREAD), (0.009, "#F0C24A"), (0.007, BREAD)]
    ham = [(0.007, BREAD), (0.003, "#7FAF3A"), (0.003, "#E59A9A"), (0.003, "#7FAF3A"), (0.007, BREAD)]
    x = -PW / 2 + 0.003
    for k, layers in enumerate((egg, egg, ham, ham)):
        for j, (t, color) in enumerate(layers):
            parts.append(_food(f"Sandwich{k}_{j}", "prism", [sd, t, sh], [x + t / 2, sy, base_h + 0.0005 + sh / 2],
                               color, rotation=[0, 0, 90], profile=[[-0.5, 0, 0.05], [0.5, 0, 0.05], [0.5, 1, 0.05]]))
            x += t
        x += 0.0005
    # 斜めの面（外向きの法線が奥から手前上へ傾く）に貼るシール
    tilt = math.degrees(math.atan2(PH, PD))
    n = (-math.sin(math.radians(tilt)), math.cos(math.radians(tilt)))
    zc = base_h + PH * 0.42
    yc = -PD / 2 + PD * 0.42
    # 角を丸めた外形は size に合わせて伸ばすので、斜めの面は元の線より外にある。その分だけ外へ出す
    ol = prism_outline(PD, PH, tri)
    off = float(np.max((ol - [-PD / 2, 0]) @ [n[0], n[1]])) + 0.0004
    parts.append(_box("Sticker", (0.070, 0.040, 0.0006), (0, yc + n[0] * off, zc + n[1] * off), WHITE, "matte",
                      {"top": 0}, rotation=[tilt, 0, 0], collision=False))
    imgs = [_sticker(70, 40, "ミックスサンド", "たまご・ハムレタス", 328, 336, green, 5011)]
    return Product(slug="sandwich_mixed_pack", name="ミックスサンド たまご・ハムレタス", shape_class="assembly",
                   category="food", dims=Dimensions(base_h + PH, PW + 0.004, depth=PD + 0.004), mass_kg=0.16,
                   material="plastic",
                   description="形は一般的なコンビニのサンドイッチのパック（側面が直角三角形の透明な三角柱 幅 100 mm・奥行き 88 mm・"
                               "高さ 110 mm に、三角のサンドイッチ 4 切れを立てて並べ、斜めの面に商品名シール）で、寸法・質量は代表値。"
                               "サンドイッチはパンと具の薄い三角柱を重ねて表す。",
                   tags=["サンドイッチ", "ミックスサンド", "たまごサンド", "ハムサンド", "中食", "要冷蔵", "sandwich",
                         "sandwiches in triangle pack"],
                   colors=Colors(label_base=WHITE), images=imgs, parts=parts)


# ---------------------------------------------------------------- 寿司・めん・パスタ（トレーと透明なフタ）


def inari_sushi_pack() -> Product:
    """黒いトレー（箱、上面に笹の葉の敷き紙の絵）にいなり寿司 4 個（肩の張った山形 bun）、透明なフタと商品名シール。

    参考: https://commons.wikimedia.org/wiki/File:Onigiri_and_Inarizushi_in_Brighton_and_Hove_Japanese_Club_Open_Day_2023.jpg（CC0）
    """
    W, D, tray_h = 150.0, 100.0, 0.016
    black, leaf, brown = "#161616", "#3E8E41", "#B7782F"
    t = Canvas(W, D, 8, black, 5021)
    t.gradient(0, 0, W, D, "#2C2C2C", "#0E0E0E")
    t.rect(4, 4, W - 4, D - 4, fill="#1B1B1B", radius=4)
    for k in range(7):  # 笹の葉の敷き紙（バラン）
        cx = 14 + k * 20.5
        t.polygon([(cx - 9, D - 6), (cx, 6), (cx + 9, D - 6)], fill=mix(leaf, "#1E5E22", (k % 2) * 0.4))
        t.line([(cx, 8), (cx, D - 8)], "#8BC34A", 0.5)
    t.ellipse(W - 26, D - 26, W - 8, D - 8, fill="#F3A5B5")  # がり
    t.ellipse(W - 23, D - 23, W - 11, D - 11, fill="#F8C9D2")
    side = Canvas(W, tray_h * 1000, 8, black, 5022)
    side.gradient(0, 0, W, tray_h * 1000, "#3A3A3A", "#0E0E0E")
    imgs = [_face(t.array(), "plastic", 5021, 0.5),
            _face(side.array(), "plastic", 5022, 0.5),
            _sticker(62, 36, "いなり寿司 4個入", "甘辛く煮たおあげ", 298, 412, "#8D5A1E", 5023)]
    parts = [_box("Tray", (W / 1000, D / 1000, tray_h), (0, 0, tray_h / 2), black, "plastic",
                  {"top": 0, "front": 1, "back": 1})]
    for k, (x, y) in enumerate([(-0.034, -0.022), (0.034, -0.022), (-0.034, 0.022), (0.034, 0.022)]):
        parts.append(_food(f"Inari{k}", "bun", [0.062, 0.040, 0.030], [x * 1.05, y, tray_h - 0.001 + 0.015], brown,
                           "plastic", rotation=[0, 0, (-4, 3, 5, -2)[k]]))
    lid_h = 0.040
    parts += [_box("Lid", (W / 1000 + 0.003, D / 1000 + 0.003, lid_h), (0, 0, tray_h - 0.003 + lid_h / 2), CLEAR,
                   "glass", thin_walled=True),
              _box("Sticker", (0.062, 0.036, 0.0006), (0.030, -0.020, tray_h - 0.003 + lid_h + 0.0003), WHITE, "matte",
                   {"top": 2}, collision=False)]
    return Product(slug="inari_sushi_pack", name="いなり寿司 4個入", shape_class="assembly", category="food",
                   dims=Dimensions(tray_h - 0.003 + lid_h + 0.0006, W / 1000 + 0.003, depth=D / 1000 + 0.003),
                   mass_kg=0.21, material="plastic",
                   description="形は一般的なコンビニのいなり寿司（黒いトレー 150×100 mm に長さ 62 mm のいなり 4 個、"
                               "高さ 40 mm の透明なフタと商品名シール）で、寸法・質量は代表値。いなりは簡単な形で表す。",
                   tags=["いなり寿司", "いなり", "稲荷寿司", "寿司", "中食", "要冷蔵", "inari sushi",
                         "inari sushi in tray"],
                   colors=Colors(label_base=black), images=imgs, parts=parts)


def zaru_soba_tray() -> Product:
    """角型の容器（箱、上面にすだれ）に、そばの山（写真を貼った部品）とつゆのカップ（円柱）と薬味の小袋（薄い箱）、透明なフタと商品名シール。

    参考: https://commons.wikimedia.org/wiki/File:Zaru-Soba-1.jpg（CC0）、
    https://commons.wikimedia.org/wiki/File:Mori-soba_002.jpg（CC0）
    """
    W, D, tray_h = 185.0, 135.0, 0.026
    dark, bamboo, navy = "#2A1D14", "#D7C08A", "#1F3557"
    t = Canvas(W, D, 8, dark, 5031)
    t.gradient(0, 0, W, D, "#3A2A1E", "#1E140D")
    sx1 = 122.0  # そば（左）とつゆ・薬味（右）の境
    t.rect(5, 5, sx1, D - 5, fill=bamboo, radius=3)
    for y in range(7, int(D) - 6, 3):  # すだれ
        t.line([(6, y), (sx1 - 1, y)], mix(bamboo, "#8D7442", 0.5), 0.5)
    t.rect(sx1 + 3, 5, W - 5, D - 5, fill="#2E2219", radius=3)
    side = Canvas(W, tray_h * 1000, 8, dark, 5032)
    side.gradient(0, 0, W, tray_h * 1000, "#4A3626", "#1A110B")
    side.pattern(0, 3, W, tray_h * 1000, "stripes", mix(dark, WHITE, 0.07), 3.0, 0.3)
    side.rect(0, 0, W, 1.6, fill="#5A4430")
    # つゆのカップのフタ（円）
    cd = 54.0
    lid = Canvas(cd, cd, 14, WHITE, 5033)
    lid.gradient(0, 0, cd, cd, "#FFFFFF", "#E6E9EA")
    lid.ellipse(0.5, 0.5, cd - 0.5, cd - 0.5, fill=WHITE)
    lid.ellipse(4, 4, cd - 4, cd - 4, outline=navy, width=1.0)
    lid.text(cd / 2, cd / 2 - 6, "そばつゆ", 7.5, navy, 900)
    lid.text(cd / 2, cd / 2 + 4, "ストレート", 3.6, navy, 800)
    lid.text(cd / 2, cd / 2 + 11, "ここからはがす ▶", 2.6, "#C62828", 800)
    pk = Canvas(44, 26, 14, "#F7F7F2", 5034)  # 薬味の小袋
    pk.gradient(0, 0, 44, 26, "#F7F9F2", "#E3E8DA")
    pk.rect(2, 2, 22, 24, fill="#9CCC65", radius=2)
    pk.text(12, 13, "ねぎ", 5.0, "#33691E", 900)
    pk.rect(24, 2, 42, 24, fill="#C5E1A5", radius=2)
    pk.text(33, 10, "わさび", 3.6, "#33691E", 900)
    pk.text(33, 17, "WASABI", 2.4, "#33691E", 800)
    imgs = [_face(t.array(), "plastic", 5031, 0.4), _face(side.array(), "plastic", 5032, 0.5),
            _face(lid.array(), "paper", 5033, 0.4), _face(pk.array(), "film", 5034, 0.5),
            _sticker(66, 38, "ざるそば", "つゆ・ねぎ・わさび付", 450, 386, navy, 5035)]
    side2 = Canvas(D, tray_h * 1000, 8, dark, 5036)
    side2.gradient(0, 0, D, tray_h * 1000, "#4A3626", "#1A110B")
    side2.pattern(0, 3, D, tray_h * 1000, "stripes", mix(dark, WHITE, 0.07), 3.0, 0.3)
    side2.rect(0, 0, D, 1.6, fill="#5A4430")
    imgs.append(_face(side2.array(), "plastic", 5036, 0.5))
    imgs.append(_food_photo("deli_soba", 108, 118, (0.52, 0.36, 0.94, 0.84), 5037))  # 6: そばの山の上面
    cup_h = 0.026
    z0 = tray_h - 0.001
    sx = (sx1 / 2 + 2.5 - W / 2) / 1000  # すだれの中心
    noodles = [_food("Soba", "bun", (0.108, 0.118, 0.018), (sx, 0, z0 + 0.009), "#7A6E5E", faces={"top": 6})]
    rng = np.random.default_rng(5038)
    for k in range(16):  # きざみのり（山の上に散らす）
        x, y = rng.uniform(-0.022, 0.022), rng.uniform(-0.026, 0.026)
        noodles.append(_food(f"Nori{k}", "box", (0.007, 0.0016, 0.0006), (sx + x, y, z0 + 0.0178),
                             "#1E2A1A", rotation=(0, 0, rng.uniform(0, 180))))
    parts = noodles + [_box("Tray", (W / 1000, D / 1000, tray_h), (0, 0, tray_h / 2), dark, "plastic",
                  {"top": 0, "front": 1, "back": 1, "left": 5, "right": 5}),
             Part("SoupCup", "cylinder", [cd / 1000, cd / 1000, cup_h], [0.0625, 0.028, tray_h - 0.004 + cup_h / 2],
                  color=WHITE, finish="plastic", faces={"top": 2}, collision=False),
             Part("Condiments", "box", [0.044, 0.026, 0.004], [0.0625, -0.036, tray_h + 0.002], [0, 0, 8],
                  color="#F4F6EE", finish="glossy", faces={"top": 3}, collision=False, material="food")]
    lid_h = 0.034
    parts += [_box("Lid", (W / 1000 + 0.003, D / 1000 + 0.003, lid_h), (0, 0, tray_h - 0.004 + lid_h / 2), CLEAR,
                   "glass", thin_walled=True),
              _box("Sticker", (0.066, 0.038, 0.0006), (-0.036, -0.026, tray_h - 0.004 + lid_h + 0.0003), WHITE,
                   "matte", {"top": 4}, collision=False)]
    return Product(slug="zaru_soba_tray", name="ざるそば つゆ・薬味付", shape_class="assembly", category="food",
                   dims=Dimensions(tray_h - 0.004 + lid_h + 0.0006, W / 1000 + 0.003, depth=D / 1000 + 0.003),
                   mass_kg=0.36, material="plastic",
                   description="形は一般的なコンビニのざるそば（角型の容器 185×135 mm に、すだれに載せたそば・つゆのカップ・"
                               "薬味の小袋、高さ 34 mm の透明なフタと商品名シール）で、寸法・質量は代表値。"
                               "そばは写真を貼った低い山、きざみのりは細い板で表す。",
                   tags=["ざるそば", "そば", "蕎麦", "めん", "中食", "要冷蔵", "zaru soba", "soba noodles",
                         "cold soba in tray"],
                   photos=["deli_soba"], colors=Colors(label_base=dark), images=imgs, parts=parts)


def napolitan_pasta_tray() -> Product:
    """電子レンジ対応の黒い容器（角の丸い箱）にパスタの山（写真を貼った部品）と具、透明なフタと温め時間入りのシール。

    参考: https://commons.wikimedia.org/wiki/File:Naporitan_of_Lawson.jpg（CC0。形と色の参考のみ）、
    https://commons.wikimedia.org/wiki/File:Spaghetti_Naporitan_001.jpg（CC0。パスタの山に合成）
    """
    W, D, tray_h = 190.0, 140.0, 0.030
    black, red = "#141414", "#C62828"
    t = Canvas(W, D, 8, black, 5041)
    t.gradient(0, 0, W, D, "#303030", "#0C0C0C")
    t.rect(7, 7, W - 7, D - 7, fill="#7A2A14", radius=16)
    side = Canvas(W, tray_h * 1000, 8, black, 5042)
    side.gradient(0, 0, W, tray_h * 1000, "#3A3A3A", "#0C0C0C")
    side.rect(0, 0, W, 2.0, fill="#444444")
    imgs = [_face(t.array(), "plastic", 5041, 0.4), _face(side.array(), "plastic", 5042, 0.5),
            _sticker(70, 42, "ナポリタン", "喫茶店風 ケチャップ炒め", 498, 682, red, 5043, heat="温め 500W 2分30秒")]
    side2 = Canvas(D, tray_h * 1000, 8, black, 5044)
    side2.gradient(0, 0, D, tray_h * 1000, "#3A3A3A", "#0C0C0C")
    side2.rect(0, 0, D, 2.0, fill="#444444")
    imgs.append(_face(side2.array(), "plastic", 5044, 0.5))
    imgs.append(_food_photo("spaghetti", 170, 122, (0.24, 0.17, 0.76, 0.84), 5045))  # 4: パスタの山の上面
    bevel = 0.007
    parts = [Part("Tray", "box", [W / 1000, D / 1000, tray_h], [0, 0, tray_h / 2], color=black, finish="plastic",
                  faces={"top": 0, "front": 1, "back": 1, "left": 3, "right": 3}, bevel=bevel)]
    # パスタは写真を貼った低い山、ソーセージの輪切りとピーマンを上に載せる
    z0 = tray_h - 0.001
    parts.append(_food("Pasta", "bun", (0.170, 0.122, 0.020), (0, 0, z0 + 0.010), "#D9692E", faces={"top": 4}))
    for k, (x, y, rx) in enumerate(((-0.040, 0.014, 15), (-0.012, -0.022, -20), (0.018, 0.020, 25),
                                    (0.042, -0.008, -10), (-0.028, -0.004, 30), (0.006, 0.002, -25))):
        parts.append(_food(f"Sausage{k}", "cylinder", (0.016, 0.016, 0.005), (x, y, z0 + 0.0195), "#C0563A",
                           "plastic", rotation=(rx, 0, k * 40)))
    for k, (x, y, rz) in enumerate(((-0.024, 0.026, 30), (0.030, 0.004, -40), (-0.002, -0.030, 70),
                                    (0.050, 0.018, 10), (-0.052, -0.014, -60))):
        parts.append(_food(f"Pepper{k}", "box", (0.020, 0.005, 0.0025), (x, y, z0 + 0.0185), "#4E9A2A", "plastic",
                           rotation=(0, 0, rz)))
    lid_h = 0.030
    parts += [Part("Lid", "box", [W / 1000 + 0.003, D / 1000 + 0.003, lid_h], [0, 0, tray_h - 0.003 + lid_h / 2],
                   color=CLEAR, finish="glass", thin_walled=True, bevel=bevel),
              _box("Sticker", (0.070, 0.042, 0.0006), (0.040, -0.024, tray_h - 0.003 + lid_h + 0.0003), WHITE, "matte",
                   {"top": 2}, collision=False)]
    return Product(slug="napolitan_pasta_tray", name="ナポリタン", shape_class="assembly", category="food",
                   dims=Dimensions(tray_h - 0.003 + lid_h + 0.0006, W / 1000 + 0.003, depth=D / 1000 + 0.003),
                   mass_kg=0.42, material="plastic",
                   description="形は一般的なコンビニの電子レンジ対応のパスタ（黒い容器 190×140 mm・高さ 30 mm に、"
                               "高さ 30 mm の透明なフタと温め時間入りのシール）で、寸法・質量は代表値。"
                               "パスタは写真を貼った低い山、ソーセージとピーマンは簡単な形で表す。",
                   tags=["ナポリタン", "スパゲッティ", "パスタ", "中食", "電子レンジ", "要冷蔵", "napolitan",
                         "spaghetti", "pasta in microwave tray"],
                   photos=["spaghetti"], colors=Colors(label_base=black), images=imgs, parts=parts)


# ---------------------------------------------------------------- ホットスナック


def frankfurter_stick() -> Product:
    """串に刺したフランクフルトを寝かせた形。ソーセージは両端の丸い回転体、串は細い円柱。

    参考: https://commons.wikimedia.org/wiki/File:Frankfurter_wurst.JPG（PD）
    """
    L, Dm = 0.150, 0.027
    skin, wood = "#8F3A17", "#D9C089"
    prof = [[0, 0], [0.55, 0.008], [0.80, 0.03], [0.94, 0.065], [1.0, 0.11], [1.0, 0.89], [0.94, 0.935],
            [0.80, 0.97], [0.55, 0.992], [0, 1]]
    x0 = 0.030  # ソーセージの中心（串の持ち手を左に出す）
    parts = [Part("Sausage", "revolve", [Dm, Dm, L], [x0, 0, Dm / 2], [0, 90, 0], color=skin, finish="plastic",
                  material="food", profile=prof)]
    for k in range(5):  # 焼き目（表面に浅く埋めた細い輪）
        x = x0 - L / 2 + 0.030 + k * 0.022
        parts.append(_food(f"Grill{k}", "torus", [Dm * 1.01, Dm * 1.01, 0.003], [x, 0, Dm / 2], "#4E1E0A",
                           "matte", rotation=[0, 90, 0]))
    stick_l = 0.200  # 先はソーセージの中で止める
    left = x0 - L / 2 - 0.065
    right = x0 + L / 2
    parts.append(Part("Skewer", "cylinder", [0.004, 0.004, stick_l], [left + stick_l / 2, 0, Dm / 2], [0, 90, 0],
                      color=wood, finish="matte", material="wood"))
    W = right - left
    return Product(slug="frankfurter_stick", name="フランクフルト（ホットスナック）", shape_class="assembly",
                   category="food", dims=Dimensions(Dm, W, depth=Dm), mass_kg=0.075, material="food",
                   description="形は一般的なコンビニのホットスナックのフランクフルト（長さ 150 mm・直径 27 mm のソーセージを"
                               "長さ 200 mm の串に刺し、寝かせて置いた形）で、寸法・質量は代表値。焼き目は細い輪で表す。",
                   tags=["フランクフルト", "ソーセージ", "ホットスナック", "串", "frankfurter", "sausage",
                         "sausage on skewer"],
                   colors=Colors(label_base=skin), images=[], parts=parts)


def nikuman_wrapped() -> Product:
    """紙のシート（薄い箱）に載せた肉まん（肩の張った山形 bun と、頂上のひだのつまみ）。

    参考: https://commons.wikimedia.org/wiki/File:Steamed_pork_buns_-_San_Francisco,_CA.jpg（CC0）
    """
    S, sheet_h = 105.0, 0.0006
    dough, red = "#F1E7D3", "#B71C1C"
    c = Canvas(S, S, 10, WHITE, 5061)
    c.gradient(0, 0, S, S, "#FFFFFF", "#F3F0EA")
    c.pattern(0, 0, S, S, "stripes", "#EEE9DF", 3.0, 0.3)  # 紙のすき目
    c.rect(2, 2, S - 2, S - 2, outline=red, width=0.6)
    c.rect(3.5, 3.5, S - 3.5, S - 3.5, outline=red, width=0.3)
    for k in range(4):  # 角の雷文風の飾り
        x, y = (6, 6) if k == 0 else (S - 18, 6) if k == 1 else (6, S - 18) if k == 2 else (S - 18, S - 18)
        c.rect(x, y, x + 12, y + 12, outline=red, width=0.5)
        c.rect(x + 3, y + 3, x + 9, y + 9, outline=red, width=0.4)
    c.text(S / 2, S - 7, "ほかほか 肉まん", 4.0, red, 900)
    c.text(S / 2, 7, NOTICE, 1.8, red, 600, max_w=S - 40)
    imgs = [_face(c.array(), "paper", 5061, 0.6)]
    bun_d, bun_h = 0.092, 0.050
    parts = [_box("Sheet", (S / 1000, S / 1000, sheet_h), (0, 0, sheet_h / 2), WHITE, "matte", {"top": 0}),
             Part("Bun", "bun", [bun_d, bun_d, bun_h], [0, 0, sheet_h + bun_h / 2], color=dough, finish="matte",
                  material="food")]
    top = sheet_h + bun_h
    knot_h = 0.009
    parts.append(_food("Knot", "pointed_dome", [0.022, 0.022, knot_h], [0, 0, top - 0.003 + knot_h / 2],
                       mix(dough, "#C9B48A", 0.25)))
    for k in range(6):  # ひだ（頂上のまわりの細長い山）
        a = math.radians(k * 60 + 10)
        r = 0.013
        parts.append(_food(f"Pleat{k}", "dome", [0.016, 0.006, 0.004],
                           [r * math.cos(a), r * math.sin(a), top - 0.0025 + 0.002],
                           mix(dough, "#C9B48A", 0.20), rotation=[0, 0, k * 60 + 10]))
    height = top - 0.003 + knot_h
    return Product(slug="nikuman_wrapped", name="肉まん（ホットスナック）", shape_class="assembly", category="food",
                   dims=Dimensions(round(height, 4), S / 1000, depth=S / 1000), mass_kg=0.115,
                   material="food",
                   description="形は一般的なコンビニの中華まんの肉まん（直径 92 mm・高さ 56 mm を 105 mm 角の紙のシートに"
                               "載せた形）で、寸法・質量は代表値。頂上のひだは簡単な形で表す。",
                   tags=["肉まん", "中華まん", "ホットスナック", "nikuman", "steamed bun", "pork bun",
                         "steamed bun on paper sheet"],
                   colors=Colors(label_base=dough), images=imgs, parts=parts)


def oden_cup() -> Product:
    """使い捨てのカップ（回転体）。上面がつゆで、頭を出した具（部品、大根と卵は写真）と透明な平たいフタ（部品）。

    参考: https://commons.wikimedia.org/wiki/File:Oden_001.jpg（CC0。大根と卵の上面に合成）
    """
    form = forms.paper_cup(0.072, 0.122, 0.088, lid_h=0.002, lid_overhang=0.0, rim_h=0.004,
                           label_margin=(0.002, 0.002))
    white, brown, red = "#FBFAF6", "#6B3A1A", "#B71C1C"
    c = label_canvas(form, white, seed=5071)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#FFFFFF", "#EFEBE2")
    c.pattern(0, 0, W, H, "waves", mix(white, "#C9B48A", 0.35), 9, 0.5)
    c.rect(0, H - 9, W, H, fill=brown)
    for fx in (0.75 * W, 0.25 * W):
        c.rect(fx - 30, 8, fx + 30, H - 14, fill=WHITE, radius=4, outline=brown, width=0.6)
        c.text(fx - 12, 26, "おでん", 11, brown, 900)
        c.ellipse(fx + 6, 14, fx + 22, 30, fill="#F3E5C0", outline=brown, width=0.5)  # 大根
        c.polygon([(fx + 14, 33), (fx + 24, 33), (fx + 19, 43)], fill="#8A8A82")  # こんにゃく
        c.ellipse(fx + 4, 32, fx + 14, 44, fill="#E0A85A", outline=brown, width=0.4)  # 卵
        c.text(fx, 47, "だしがしみた 秋冬の味", 3.6, red, 800, max_w=56)
        steam(c, fx + 14, 13, 10, 5, "#B0A08A", 0.5)
    c.text(0.75 * W, H - 4.5, "やけどに注意してください", 3.4, WHITE, 800)
    c.text(0.25 * W, H - 4.5, NOTICE, 2.4, WHITE, 600, max_w=70)
    label = edge_shade(finish(c.array(), "paper", 5071, 0.6), 4, 0.06)

    t = top_canvas(form, "#C9A462", seed=5072)
    d = t.w_mm
    t.ellipse(0.3, 0.3, d - 0.3, d - 0.3, fill="#C49A55")
    t.ellipse(4, 4, d - 4, d - 4, fill="#8A5622")  # つゆ（具は上に出した部品）
    t.ellipse(14, 12, d * 0.55, d * 0.4, fill="#9A6630")
    t.ellipse(0.3, 0.3, d - 0.3, d - 0.3, outline="#F5F2EA", width=2.4)  # カップの縁
    top = finish(t.array(), "plastic", 5072, 0.4)
    r = revolve(form, label=label, top=top, body_fill="#E9E4D8")
    i_daikon, i_egg = len(r["images"]), len(r["images"]) + 1
    r["images"] += [_food_photo("deli_oden", 42, 42, (0.30, 0.21, 0.54, 0.56), 5073),
                    _food_photo("deli_oden", 30, 40, (0.16, 0.43, 0.39, 0.70), 5074)]
    Hm = form.height
    lid_h = 0.010
    # つゆから頭を出した具（大根・卵・こんにゃく・ちくわ）
    parts = [_food("Daikon", "cylinder", (0.042, 0.042, 0.014), (-0.018, 0.014, Hm - 0.001), "#E9D9A8",
                   faces={"top": i_daikon}),
             _food("Egg", "bun", (0.030, 0.040, 0.020), (-0.020, -0.026, Hm - 0.004), "#C98A3A", "plastic",
                   faces={"top": i_egg}),
             _food("Konnyaku", "box", (0.028, 0.028, 0.010), (0.022, -0.022, Hm - 0.003), "#6E6C64",
                   rotation=(20, 0, 45)),
             _food("Chikuwa", "cylinder", (0.018, 0.018, 0.048), (0.020, 0.018, Hm - 0.004), "#B98A52",
                   rotation=(0, 90, 30))]
    parts += [Part("Lid", "cylinder", [0.126, 0.126, lid_h], [0, 0, Hm - 0.001 + lid_h / 2], color=CLEAR,
                  finish="glass", thin_walled=True),
             Part("Vent", "cylinder", [0.010, 0.010, 0.0008], [0.040, 0, Hm - 0.001 + lid_h + 0.0004],
                  color="#D8DCDE", finish="plastic", collision=False)]
    return Product(slug="oden_cup", name="おでん カップ入り", category="food", mass_kg=0.38, material="paper",
                   description="形は一般的なコンビニのおでんの使い捨てカップ（上端径 122 mm・高さ 72 mm に、"
                               "高さ 10 mm の透明なフタ）で、寸法・質量は代表値。つゆはカップの上面の色、頭を出した具とフタは部品で表す。",
                   tags=["おでん", "ホットスナック", "大根", "煮物", "oden", "oden in disposable cup"],
                   photos=["deli_oden"], colors=Colors(cap="#C9A462", label_base=white), parts=parts, **r)


# ---------------------------------------------------------------- 袋（寝かせて置く）


def seasoned_egg_2pack() -> Product:
    """寝かせた透明な袋。ゆで卵 2 個（描いた絵）が透けて見え、左に商品名のラベル。画像は横長（左右がシール）。

    参考: https://commons.wikimedia.org/wiki/File:Tonkotsu_ramen_with_seasoned_boiled_egg_of_Japanese_National_Diet_Library.jpg（CC0）
    """
    L, Wd = 130.0, 85.0
    amber, brown, orange = "#E8C98E", "#5D3A1A", "#E65100"

    def bag(seed: int) -> Canvas:
        c = Canvas(L, Wd, 10, "#F3E7CC", seed)
        c.gradient(0, 0, L, Wd, "#F6EEDC", mix("#EBDDBF", amber, 0.3))
        seal_crimp(c, 0, 0, 9, Wd, "#E9DDC3", 1.2, vertical=True)
        seal_crimp(c, L - 9, 0, L, Wd, "#E9DDC3", 1.2, vertical=True)
        return c

    def egg(c: Canvas, cx: float, cy: float, rx: float, ry: float):
        c.ellipse(cx - rx, cy - ry + 2, cx + rx, cy + ry + 2, fill="#D8C9A8")  # 影
        for k in range(40):  # 外は濃い飴色、中ほど明るい
            f = 1 - k / 44
            c.ellipse(cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f, fill=mix("#8A4E1C", "#D9A35E", (k / 40) ** 0.7))
        c.ellipse(cx - rx * 0.45, cy - ry * 0.65, cx - rx * 0.05, cy - ry * 0.30, fill="#ECC283")  # つや

    c = bag(5081)
    egg(c, 72, Wd / 2 + 2, 19, 25)
    egg(c, 106, Wd / 2 + 2, 19, 25)
    c.rect(12, 7, 50, Wd - 7, fill=WHITE, radius=3, outline=orange, width=0.6)
    c.rect(12, 7, 50, 19, fill=orange, radius=3)
    c.rect(12, 15, 50, 19, fill=orange)
    c.text(31, 13, "半熟", 6.5, WHITE, 900)
    c.text(31, 29, "味付け", 7.0, brown, 900)
    c.text(31, 39, "たまご", 7.0, brown, 900)
    c.text(31, 50, "2個入", 5.6, orange, 900)
    c.text(31, 59, "しょうゆだれ漬け", 3.0, brown, 800, max_w=34)
    c.text(31, 69, "要冷蔵 10℃以下", 2.8, INK, 700, max_w=34)
    front = _pouch(c, 5081, 0.8, 12)

    b = bag(5082)
    b.rect(12, 6, L - 12, Wd - 6, fill=WHITE, radius=3)
    back_info(b, 15, 9, 82, [
        ("名称", "味付け卵"), ("原材料名", "鶏卵（国産）、しょうゆ、砂糖、みりん、食塩／調味料（アミノ酸等）"),
        ("内容量", "2個"), ("消費期限", "右に記載"), ("保存方法", "要冷蔵（10℃以下）")], 2.2,
        [("栄養成分表示 1個当たり", ""), ("エネルギー", "78kcal"), ("たんぱく質", "6.4g"), ("脂質", "5.1g"),
         ("炭水化物", "1.6g"), ("食塩相当量", "0.9g")])
    b.barcode(88, 12, 28, 18)
    b.recycle(102, 46, 8, "プラ", orange, sub="袋")
    b.text(102, Wd - 14, "消費期限", 3.0, INK, 700)
    b.text(102, Wd - 9, "26.10.24", 3.6, INK, 900)
    back = _pouch(b, 5082, 0.8, 12)
    return Product(slug="seasoned_egg_2pack", name="半熟味付けたまご 2個入", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.036), mass_kg=0.13, material="film",
                   orientation="lying",
                   description="形は一般的なコンビニの袋入りの味付けたまご 2 個入（長さ 130 mm・幅 85 mm・厚さ 36 mm）で、"
                               "寸法・質量は代表値。袋ごしに見える卵は描いた絵。",
                   tags=["味付けたまご", "味玉", "ゆで卵", "卵", "惣菜", "要冷蔵", "seasoned egg", "boiled egg",
                         "seasoned eggs in clear bag"],
                   colors=Colors(label_base="#F3E7CC"), images=[front, back], faces={"front": 0, "back": 1})


def frozen_gyoza_bag() -> Product:
    """寝かせた平たい冷凍食品の袋。焼き餃子の写真（調理例）と商品名、裏面に作り方と一括表示。画像は横長（左右がシール）。

    参考: https://commons.wikimedia.org/wiki/File:Hamamatsu_Gy%C5%8Dza_001.jpg（CC0。表面に合成）
    """
    L, Wd = 230.0, 170.0
    navy, red, yellow = "#16264A", "#C62828", "#FFD54F"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 8, navy, seed)
        c.gradient(0, 0, L, Wd, "#22386A", "#0F1A36")
        c.pattern(0, 0, L, Wd, "dots", mix(navy, "#FFFFFF", 0.08), 7, 0.5)
        seal_crimp(c, 0, 0, 10, Wd, "#2A3F70", 1.4, vertical=True)
        seal_crimp(c, L - 10, 0, L, Wd, "#2A3F70", 1.4, vertical=True)
        return c

    c = base(5091)
    c.photo("deli_gyoza", 82, 30, L - 14, Wd - 12, shape="round", radius=8, shadow=1.5, crop=(0.25, 0.05, 0.80, 0.66))
    c.text(L - 48, Wd - 16, "※写真は調理例です", 3.0, WHITE, 700, stroke=0.25, stroke_fill="#333333")
    c.rect(14, 10, L - 14, 26, fill=red, radius=3)
    c.text(L / 2, 18, "冷凍食品  油・水・ふた なしで焼ける", 7.0, WHITE, 900, max_w=L - 40)
    c.text(46, 48, "焼き", 14, WHITE, 900)
    c.text(46, 70, "餃子", 22, yellow, 900, stroke=0.8, stroke_fill="#7A1A10")
    c.text(46, 88, "GYOZA", 6.0, "#B8C6E6", 800, spacing=1.2)
    c.ellipse(18, 98, 74, 154, fill=yellow)
    c.text(46, 116, "12個入", 9.5, red, 900)
    c.text(46, 130, "1袋 276g", 5.0, navy, 800)
    c.text(46, 141, "国産野菜使用", 4.2, navy, 800)
    front = _pouch(c, 5091, 0.9, 18)

    b = base(5092)
    b.rect(14, 8, L - 14, Wd - 8, fill=WHITE, radius=4)
    _back_panel(b, 18, 12, 128, Wd - 12, [
        ("名称", "冷凍ぎょうざ"), ("原材料名", "野菜（キャベツ、たまねぎ、にら、にんにく）、食肉（豚肉、鶏肉）、豚脂、しょうゆ、"
                                    "ごま油、皮（小麦粉、植物油脂、食塩）／調味料（アミノ酸等）、（一部に小麦・ごま・大豆・鶏肉・豚肉を含む）"),
        ("内容量", "276g（12個入）"), ("賞味期限", "右下に記載"), ("保存方法", "-18℃以下で保存してください"),
        ("凍結前加熱の有無", "加熱してありません"), ("加熱調理の必要性", "加熱してお召し上がりください")], 2.6,
        [("栄養成分表示 6個（138g）当たり", ""), ("エネルギー", "286kcal"), ("たんぱく質", "10.2g"),
         ("脂質", "14.8g"), ("炭水化物", "28.4g"), ("食塩相当量", "1.9g")], [], red)
    b.rect(134, 12, L - 18, 20, fill=red, radius=1.5)
    b.text(136, 16, "フライパンでの焼き方", 3.6, WHITE, 900, anchor="lm")
    b.paragraph(135, 23, L - 19, "① 凍ったままの餃子をフライパンに並べる。\n② ふたをせず中火で約5分焼く。\n"
                "③ 羽根がきつね色になったら皿をかぶせて返す。\n※油・水は不要です。", 3.0, INK, 600)
    b.barcode(138, Wd - 58, 40, 26)
    b.recycle(196, Wd - 46, 13, "プラ", red, sub="袋")
    b.text(176, Wd - 20, "賞味期限 2027.09.30", 4.0, INK, 800, max_w=L - 196)
    back = _pouch(b, 5092, 0.9, 18)
    return Product(slug="frozen_gyoza_bag", name="冷凍 焼き餃子 12個入", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.028), mass_kg=0.29, material="film",
                   orientation="lying",
                   description="形は一般的な冷凍の焼き餃子の平たい袋（長さ 230 mm・幅 170 mm・厚さ 28 mm）で、寸法・質量は代表値。",
                   tags=["餃子", "ぎょうざ", "冷凍食品", "冷凍餃子", "中華", "frozen gyoza", "dumplings",
                         "frozen dumplings bag"],
                   photos=["deli_gyoza"], colors=Colors(label_base=navy), images=[front, back],
                   faces={"front": 0, "back": 1})


PRODUCTS = {f.__name__: f for f in (onigiri_salmon, sandwich_mixed_pack, inari_sushi_pack, zaru_soba_tray,
                                     napolitan_pasta_tray, frankfurter_stick, nikuman_wrapped, oden_cup,
                                     seasoned_egg_2pack, frozen_gyoza_bag)}
