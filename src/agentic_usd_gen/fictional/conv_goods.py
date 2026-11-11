"""架空の商品のデザイン: コンビニの日用品・雑貨。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _cyl, _face, back_info, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _faces(canvases, kind: str, seed: int, strength: float = 0.8) -> list[np.ndarray]:
    """箱の 6 面（正面・裏・右・左・上・底の順）を仕上げる。"""
    return [_face(c.array(), kind, seed + i, strength) for i, c in enumerate(canvases)]


def _columns(c: Canvas, x_right: float, y0: float, y1: float, text: str, size: float, x_left: float,
             color: str = INK, gap: float = 1.25):
    """縦書きの本文（右の列から左へ、x_left まで）。文は足りなければくり返す。"""
    per = max(1, int((y1 - y0) / size))
    x, i = x_right - size / 2, 0
    while x - size / 2 >= x_left:
        col = "".join(text[(i + k) % len(text)] for k in range(per))
        c.vtext(x, y0 + size / 2, col, size, color, 400, gap=0)
        i += per
        x -= size * gap


def _page_edges(c: Canvas, color: str, w: float = 1.2, step: float = 3.0):
    """紙の縁からのぞく下のページ（縁を細かい破線にする。縁が単色だと切り抜かれるため）。"""
    dark = mix(color, "#6F6A60", 0.45)
    W, H = c.w_mm, c.h_mm
    for k in range(int(W / step) + 1):
        x = k * step + (k % 3) * 0.4
        c.rect(x, 0, x + step * 0.45, w, fill=dark)
        c.rect(x + step * 0.3, H - w, x + step * 0.8, H, fill=dark)
    for k in range(int(H / step) + 1):
        y = k * step + (k % 3) * 0.4
        c.rect(0, y, w, y + step * 0.45, fill=dark)
        c.rect(W - w, y + step * 0.3, W, y + step * 0.8, fill=dark)


def _hang_hole(c: Canvas, cx: float, y: float, color: str):
    """吊り下げ穴（穴は開けず印刷で表す）。"""
    c.rect(cx - 9, y, cx + 9, y + 6, fill=color, radius=3)


# ---------------------------------------------------------------- ビニール傘


def vinyl_umbrella_65cm() -> Product:
    clear, white, metal = "#F2F6F8", "#F4F4F2", "#B8BCC0"
    parts = [_cyl("Ferrule", (0.008, 0.008, 0.075), (0, 0, 0.0375), "#E8E8E6", "plastic"),
             _cyl("Shaft", (0.007, 0.007, 0.70), (0, 0, 0.42), metal, "metal", collision=False)]
    # 閉じた傘の生地は、一番太い所（z = 0.20 m、半径 26 mm）から上下に細くなる 2 つの山で近似する
    # （上は先端の 0.69 m、下は石突きの 0.075 m まで）。たたんだビニールは何枚も重なるので、すりガラスのような半透明にする
    vinyl = "#E6EEF0"
    parts += [Part("CanopyUpper", "dome", [0.052, 0.052, 0.52], [0, 0, 0.46], color=vinyl, finish="frosted"),
              Part("CanopyLower", "dome", [0.052, 0.052, 0.13], [0, 0, 0.135], [180, 0, 0], color=vinyl,
                   finish="frosted")]
    parts += [_cyl("Strap", (0.0535, 0.0535, 0.024), (0, 0, 0.27), white, "plastic", collision=False),
              _box("StrapTab", (0.012, 0.004, 0.030), (0, -0.0285, 0.27), white, "plastic", collision=False),
              _cyl("TopNotch", (0.014, 0.014, 0.02), (0, 0, 0.70), "#DADCDE", "plastic"),
              _cyl("UpperShaft", (0.010, 0.010, 0.05), (0, 0, 0.725), metal, "metal"),
              _cyl("Grip", (0.024, 0.024, 0.065), (0, 0, 0.7825), clear, "frosted")]
    # J 字の持ち手（半円を短い棒で近似。中心 (R, cz)、半径 R）
    R, cz, n, t = 0.034, 0.815, 16, 0.020
    for k in range(n):
        am = math.pi * (k + 0.5) / n
        seg = 2 * R * math.sin(math.pi / n / 2) + 0.002
        parts.append(Part(f"Hook{k}", "cylinder", [t, t, seg], [R - R * math.cos(am), 0, cz + R * math.sin(am)],
                          [0, math.degrees(am), 0], color=clear, finish="frosted"))
    parts.append(_cyl("HookEnd", (t, t, 0.018), (2 * R, 0, cz - 0.009), clear, "frosted"))
    return Product(slug="vinyl_umbrella_65cm", name="ビニール傘 65cm", shape_class="assembly", category="household",
                   dims=Dimensions(0.860, 0.107, depth=0.057), mass_kg=0.33, material="plastic",
                   description="形は一般的なコンビニのビニール傘（親骨 65 cm、閉じた全長 86 cm・持ち手は J 字）で、寸法・質量は代表値。"
                               "閉じた生地は半透明の 2 つの山形で近似し、持ち手の曲がりは短い棒で表す。骨は省略。",
                   tags=["ビニール傘", "傘", "雨具", "透明", "umbrella", "vinyl umbrella", "rain"],
                   photos=[], colors=Colors(label_base=clear), images=[], parts=parts)


# ---------------------------------------------------------------- 週刊誌


def weekly_magazine() -> Product:
    W, H, D = 182.0, 257.0, 8.0  # B5、立てて置く
    red, white, yellow, navy = "#D7262E", "#FFFFFF", "#FFE14D", "#1B2440"
    s = 5
    fr = Canvas(W, H, s, white, seed=2411)
    fr.photo("lake", 0, 0, W, H, crop=(0.1, 0.0, 0.9, 1.0))
    fr.gradient(0, 0, W, 50, "#0E1A2E", mix("#0E1A2E", "#6A88A8", 0.6))
    fr.text(10, 23, "週刊ミライ", 22, white, 900, anchor="lm", stroke=0.6, stroke_fill=navy)
    fr.text(W - 8, 11, "10月24日号", 4.6, white, 800, anchor="rm")
    fr.rect(W - 46, 18, W - 8, 30, fill=red, radius=2)
    fr.text(W - 27, 24, "特別定価 480円", 4.2, white, 900)
    fr.text(W - 27, 38, "毎週木曜日発売", 3.6, white, 700)
    fr.rect(0, 50, W, 52, fill=red)
    fr.rect(W - 30, 58, W - 6, 146, fill=yellow)
    fr.vtext(W - 18, 66, "秋の絶景さんぽ", 11, navy, 900)
    fr.rect(6, 58, 26, 146, fill=red)
    fr.vtext(16, 65, "完全保存版", 10, white, 900)
    fr.vtext(16, 122, "全国", 9, yellow, 900)
    fr.photo("rice_field", 34, 150, 92, 192, border=white, border_w=1.2)
    fr.photo("tea_field", 98, 150, 150, 192, border=white, border_w=1.2)
    fr.text(63, 197, "実りの里を歩く", 4.6, white, 900, stroke=0.4, stroke_fill=navy)
    fr.text(124, 197, "茶畑の朝", 4.6, white, 900, stroke=0.4, stroke_fill=navy)
    fr.rect(0, 204, W, H, fill="#0E1A2E")
    for i, t in enumerate(("巻頭特集  いま行きたい湖と高原 30選", "家計  ポイントを上手にためる 12 のコツ",
                           "健康  ぐっすり眠るための夜の習慣", "連載  まちの喫茶店めぐり 第48回")):
        fr.text(10, 212 + i * 9.5, t, 5.0 if i == 0 else 4.4, yellow if i == 0 else white, 800, anchor="lm",
                max_w=W - 54)
    fr.barcode(W - 34, 224, 26, 16)
    fr.text(W - 21, 245, "雑誌 01234-10/24", 2.8, white, 600)
    fr.text(W / 2, H - 4, NOTICE, 2.4, mix(white, "#0E1A2E", 0.3), 500)
    bk = Canvas(W, H, s, white, seed=2412)  # 裏表紙は広告
    bk.gradient(0, 0, W, H, "#FFF6E8", "#F2C9A0")
    bk.photo("coffee_cup", 20, 30, W - 20, 160, shape="round", radius=8)
    bk.text(W / 2, 182, "ほっとひと息、", 12, "#5A3418", 900)
    bk.text(W / 2, 200, "秋のブレンド", 12, "#5A3418", 900)
    bk.text(W / 2, 220, "架空のコーヒー店  全店で発売中", 4.6, INK, 700)
    bk.text(W / 2, H - 14, "広告", 3.4, "#7A5A40", 700)
    bk.text(W / 2, H - 7, NOTICE, 2.6, "#7A5A40", 500)
    sp = Canvas(D, H, 10, red, seed=2413)  # 背（右綴じなので表紙の右）
    sp.gradient(0, 0, D, H, "#C81E28", "#A3141C")
    sp.vtext(D / 2, 12, "週刊ミライ", 5.0, white, 900)
    sp.vtext(D / 2, 60, "十月二十四日号", 3.6, yellow, 800)
    sp.vtext(D / 2, 120, "秋の絶景さんぽ", 3.8, white, 800)
    ed = Canvas(D, H, 10, "#F1EEE6", seed=2414)  # 小口（紙の重なり）
    for k in range(40):
        ed.line([(k * D / 40, 0), (k * D / 40, H)], mix("#F1EEE6", "#A9A39A", 0.25 + 0.2 * (k % 3 == 0)), 0.05)
    tp, bt = Canvas(W, D, 6, "#F1EEE6", seed=2415), Canvas(W, D, 6, "#F1EEE6", seed=2416)
    for e in (tp, bt):
        for k in range(16):
            e.line([(0, k * D / 16), (W, k * D / 16)], mix("#F1EEE6", "#A9A39A", 0.35), 0.06)
    tp.rect(W - 3, 0, W, D, fill="#B0171F")  # 背の側（上面は右、底面は左右が逆になる）
    bt.rect(0, 0, 3, D, fill="#B0171F")
    imgs = _faces((fr, bk, sp, ed, tp, bt), "paper", 2420, 0.6)
    return Product(slug="weekly_magazine", name="週刊ミライ 10月24日号", shape_class="box", category="household",
                   dims=Dimensions(0.257, 0.182, depth=0.008), mass_kg=0.30, material="paper",
                   description="形は一般的な週刊誌（B5 判 182 × 257 mm・厚さ 8 mm、右綴じ）を立てた箱で近似したもので、寸法・質量は代表値。誌名・記事・広告はすべて架空。",
                   tags=["週刊誌", "雑誌", "本", "B5", "magazine", "weekly magazine"],
                   photos=["lake", "rice_field", "tea_field", "coffee_cup"], colors=Colors(label_base=white),
                   images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 新聞


_ARTICLE = ("市の中心部と港を結ぶ新しい橋の工事が大詰めを迎え、来年春の開通に向けて最後の点検が始まった。"
            "橋は長さ約六百メートルで、歩道と自転車道を備える。完成すれば港までの移動時間が半分ほどになる見込みで、"
            "地元の商店街では観光客の増加に期待する声が上がっている。")
_ARTICLE2 = ("県内の各地で稲刈りが始まった。今年は夏の天候に恵まれ、実りは平年並みかやや良いという。"
             "田んぼでは家族総出で作業する姿も見られ、新米は来週から店頭に並ぶ予定だ。")


def newspaper_folded() -> Product:
    W, D, H = 406.0, 272.0, 6.0  # ブランケット判を二つ折りにして寝かせる
    paper, red, blue = "#EFECE4", "#C4262E", "#1C3F7A"
    s = 3
    tp = Canvas(W, D, s, paper, seed=2431)  # 1 面の上半分（画像の下が折り目）
    tp.rect(W - 62, 8, W - 8, 92, fill=red)
    tp.vtext(W - 35, 22, "日刊", 18, "#FFFFFF", 900)
    tp.vtext(W - 35, 62, "ニュース", 6.5, "#FFFFFF", 900)
    tp.paragraph(W - 60, 96, W - 8, "2026年（令和8年）10月17日 土曜日\n第 28,415 号\n1部 160円", 3.4, INK, 600)
    tp.rect(W - 62, 122, W - 8, 123, fill=INK)
    _columns(tp, W - 8, 128, D - 4, _ARTICLE2, 3.2, W - 62)
    tp.rect(8, 8, W - 70, 46, fill=blue)
    tp.text((W - 62) / 2, 27, "港の新しい橋  来春開通へ", 22, "#FFFFFF", 900, max_w=W - 90)
    tp.vtext(W - 82, 56, "最終点検始まる", 12, INK, 900)
    tp.vtext(W - 100, 56, "移動時間半分に", 9, red, 900)
    _columns(tp, W - 110, 56, 180, _ARTICLE, 3.6, 220)
    tp.photo("rice_field", 14, 54, 214, 176, border=INK, border_w=0.4)
    tp.text(16, 182, "稲刈りが始まった田んぼ（写真はイメージ）", 3.4, INK, 600, anchor="lm")
    tp.rect(8, 190, W - 70, 191, fill=INK)
    tp.vtext(W - 82, 198, "実りの秋", 10, INK, 900)
    _columns(tp, W - 94, 198, D - 6, _ARTICLE2 + _ARTICLE, 3.2, 110)
    tp.rect(14, 198, 104, D - 8, fill="#FFFFFF", outline=INK, width=0.4)
    tp.text(59, 208, "きょうの紙面", 5.0, red, 900)
    for i, t in enumerate(("経済 … 4面", "地域 … 18面", "スポーツ … 20面", "テレビ … 32面")):
        tp.text(22, 220 + i * 9, t, 4.0, INK, 700, anchor="lm")
    tp.text(59, D - 14, NOTICE, 2.6, INK, 500, max_w=86)
    bt = Canvas(W, D, s, paper, seed=2432)  # 最終面（テレビ欄）
    bt.rect(8, 8, W - 8, 24, fill=INK)
    bt.text(W / 2, 16, "テレビ  10月17日（土）", 8, "#FFFFFF", 900)
    shows = ("ニュース", "天気", "旅番組 秋の湖", "ドラマ 港町の人びと", "料理 新米を味わう", "音楽", "クイズ", "映画")
    n = 8
    cw = (W - 16) / n
    for i in range(n):
        x0 = 8 + i * cw
        bt.rect(x0, 26, x0 + cw, 34, fill=mix(paper, blue, 0.25 if i % 2 else 0.12))
        bt.text(x0 + cw / 2, 30, f"架空 {i + 1}ch", 4.0, INK, 900)
        bt.line([(x0, 26), (x0, D - 8)], "#888888", 0.3)
        for r in range(9):
            y = 36 + r * 25
            bt.rect(x0, y, x0 + cw, y + 0.3, fill="#888888")
            bt.text(x0 + 2, y + 4, f"{17 + r // 2}:{'00' if r % 2 == 0 else '30'}", 3.0, red, 800, anchor="lm")
            bt.paragraph(x0 + 2, y + 7, x0 + cw - 2, shows[(i + r) % 8] + "　ゆっくり楽しむ時間", 2.6, INK, 500)
    edge = Canvas(W, H, 8, paper, seed=2433)
    side = Canvas(D, H, 8, paper, seed=2434)
    for e, w in ((edge, W), (side, D)):
        for k in range(12):
            e.line([(0, k * H / 12), (w, k * H / 12)], mix(paper, "#8F8A80", 0.3 + 0.2 * (k % 2)), 0.08)
    _page_edges(tp, paper)
    _page_edges(bt, paper)
    fold = Canvas(W, H, 8, paper, seed=2435)  # 折り目の側
    fold.gradient(0, 0, W, H, mix(paper, "#FFFFFF", 0.3), mix(paper, "#8F8A80", 0.25))
    imgs = _faces((fold, edge, side, side, tp, bt), "paper", 2440, 0.7)
    return Product(slug="newspaper_folded", name="日刊ニュース 朝刊", shape_class="box", category="household",
                   dims=Dimensions(0.006, 0.406, depth=0.272), mass_kg=0.20, material="paper",
                   description="形は一般的な朝刊（ブランケット判 406 × 545 mm を二つ折り、約 32 ページ）を寝かせた薄い箱で近似したもので、寸法・質量は代表値。紙名・記事はすべて架空。",
                   tags=["新聞", "朝刊", "新聞紙", "newspaper", "morning paper"], photos=["rice_field"],
                   colors=Colors(label_base=paper), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- ロックアイス


def _ice(c: Canvas, x0: float, y0: float, x1: float, y1: float, seed: int):
    """袋ごしに見える氷（透き通った多角形を重ねる）。"""
    rng = np.random.default_rng(seed)
    c.gradient(x0, y0, x1, y1, "#C9E4F4", "#9CC6E2")
    for _ in range(int((x1 - x0) * (y1 - y0) / 150)):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(9, 18)
        n = int(rng.integers(5, 8))
        a0 = rng.uniform(0, 2 * math.pi)
        pts = [(cx + r * rng.uniform(0.7, 1.1) * math.cos(a0 + 2 * math.pi * k / n),
                cy + r * rng.uniform(0.7, 1.1) * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]
        pts = [(min(max(x, x0), x1), min(max(y, y0), y1)) for x, y in pts]
        base = mix("#F2FAFE", "#7FB4D8", rng.uniform(0, 0.9))
        c.polygon(pts, fill=base, outline=mix(base, "#FFFFFF", 0.7))
        c.line([pts[0], pts[1], pts[2]], "#FFFFFF", 0.9)


def rock_ice_1kg() -> Product:
    W, H = 200.0, 320.0
    blue, navy, white = "#1C6FC4", "#0E3A70", "#FFFFFF"
    c = Canvas(W, H, 5, white, seed=2451)
    _ice(c, 0, 0, W, H, 2451)
    seal_crimp(c, 0, 0, W, 14, "#CFE4F2", 1.6)
    seal_crimp(c, 0, H - 14, W, H, "#CFE4F2", 1.6)
    c.rect(0, 14, W, 26, fill=blue)
    c.text(W / 2, 20, "純氷  かち割り  ROCK ICE", 5.0, white, 800, spacing=0.4)
    c.rect(14, 40, W - 14, 118, fill=white, radius=8)
    c.rect(14, 40, W - 14, 118, outline=blue, width=1.2, radius=8)
    c.text(W / 2, 64, "ロックアイス", 22, blue, 900, max_w=W - 40)
    c.text(W / 2, 88, "透きとおった かたい氷", 7.0, navy, 800)
    c.text(W / 2, 104, "ゆっくり溶けて 飲みものが薄まりにくい", 4.6, INK, 700, max_w=W - 40)
    c.ellipse(W - 72, H - 84, W - 14, H - 26, fill=blue)
    c.text(W - 43, H - 62, "1kg", 15, white, 900)
    c.text(W - 43, H - 46, "冷凍", 6, "#BFE3FF", 900)
    c.rect(14, H - 50, 104, H - 26, fill=white, radius=4)
    c.text(59, H - 42, "-18℃以下で保存", 5.0, navy, 900)
    c.text(59, H - 33, "食品・飲料用の氷", 3.8, INK, 700)
    img = trim_safe(edge_shade(finish(c.array(), "film", 2451, 1.0), 25, 0.15))
    b = Canvas(W, H, 5, white, seed=2452)
    _ice(b, 0, 0, W, H, 2452)
    seal_crimp(b, 0, 0, W, 14, "#CFE4F2", 1.6)
    seal_crimp(b, 0, H - 14, W, H, "#CFE4F2", 1.6)
    b.rect(0, 14, W, 26, fill=blue)
    b.text(W / 2, 20, "ロックアイス 1kg", 5.4, white, 900)
    b.rect(12, 34, W - 12, 236, fill=white, radius=4)
    yb = back_info(b, 18, 40, W - 18, [("名称", "氷雪"), ("内容量", "1kg"), ("保存方法", "-18℃以下で保存してください"),
                                     ("使用水", "飲用適の水"), ("販売者", "架空の会社")], 5.0)
    b.paragraph(18, yb + 4, W - 18,
                "【ご注意】氷どうしがくっついたときは、袋の上から軽くたたいてほぐしてください。"
                "袋を落としたり強くたたいたりすると破れることがあります。"
                "凍ったままの氷を直接口に入れないでください。素手で長く持たないでください。", 4.4, INK, 400)
    b.rect(12, 242, W - 12, H - 20, fill=white, radius=4)
    b.barcode(20, 250, 60, 34)
    b.recycle(120, 266, 16, "プラ", blue, sub="袋")
    b.text(165, 266, "1kg", 9, blue, 900)
    back = trim_safe(edge_shade(finish(b.array(), "film", 2452, 1.0), 25, 0.15))
    return Product(slug="rock_ice_1kg", name="ロックアイス 1kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.32, 0.20, depth=0.06), mass_kg=1.03, material="film",
                   description="形は一般的なコンビニのかち割り氷の袋（高さ 320 mm・幅 200 mm）をピロー包装で近似したもので、寸法・質量は代表値。中の氷の凹凸は絵で表す。",
                   tags=["氷", "ロックアイス", "かち割り氷", "冷凍", "ice", "rock ice", "frozen"], photos=[],
                   colors=Colors(label_base="#DCEEF8"), images=[img, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- USB ケーブル（台紙とブリスター）


def usb_cable_blister() -> Product:
    CW, CH = 90.0, 200.0
    black, cyan, white = "#1A1C20", "#18B4D8", "#FFFFFF"
    c = Canvas(CW, CH, 10, black, seed=2461)
    c.gradient(0, 0, CW, CH, "#3A404C", "#08090C")
    c.pattern(0, 34, CW, CH, "stripes", mix("#22262D", cyan, 0.08), 6, 0.3)
    _hang_hole(c, CW / 2, 6, "#05070A")
    c.rect(0, 16, CW, 34, fill=cyan)
    c.text(CW / 2, 25, "USB 充電ケーブル", 7.6, black, 900, max_w=CW - 8)
    c.text(CW / 2, 41, "Type-C ⇔ Type-A", 5.6, white, 800)
    c.rect(8, 159, CW - 8, 171, fill=cyan, radius=3)
    c.text(CW / 2, 165, "1.0m  急速充電  データ通信", 4.4, black, 900, max_w=CW - 20)
    c.text(CW / 2, 177, "最大 3A  断線に強い編み込み", 3.8, white, 700)
    c.rect(8, 182, CW - 8, 194, fill="#2E333B", radius=2)
    c.text(CW / 2, 188, "1年保証  架空のケーブル", 3.6, mix(white, cyan, 0.3), 700)
    c.rect(0, CH - 3, CW, CH, fill=cyan)
    front = _face(c.array(), "film", 2461, 0.6)
    b = Canvas(CW, CH, 10, white, seed=2462)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#E8F4F8")
    b.rect(0, CH - 3, CW, CH, fill=black)
    b.rect(0, 0, CW, 2, fill=black)
    _hang_hole(b, CW / 2, 6, "#4B5058")
    b.rect(0, 16, CW, 26, fill=black)
    b.text(CW / 2, 21, "USB CHARGING CABLE", 4.2, white, 800, spacing=0.4)
    yb = b.table(6, 32, CW - 6, "", [("品名", "USB ケーブル"), ("コネクタ", "USB Type-C / USB Type-A"),
                                    ("長さ", "約 1.0m"), ("最大電流", "3A"), ("通信速度", "USB 2.0"),
                                    ("被覆", "ナイロン編み込み")], 3.4)
    b.paragraph(6, yb + 4, CW - 6, "【ご注意】コネクタの向きを確かめてまっすぐ差し込んでください。"
                "ケーブルを強く折り曲げたり、引っぱって抜いたりしないでください。"
                "ぬれた手で触らないでください。発熱や異臭があるときはすぐに使用をやめてください。\n" + NOTICE,
                3.0, INK, 400)
    b.barcode(8, 168, 42, 22)
    b.recycle(64, 178, 8, "紙", black, sub="台紙")
    b.recycle(79, 178, 8, "プラ", black, sub="ケース")
    back = _face(b.array(), "paper", 2462, 0.6)
    coil = "#F2F3F5"
    cyl = lambda name, dia, h, y, z, color, fin, col=True: Part(name, "cylinder", [dia, dia, h], [0, y, z], [90, 0, 0],
                                                               color, fin, collision=col)
    parts = [_box("Card", (0.09, 0.0012, 0.20), (0, 0, 0.10), black, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.074, 0.022, 0.104), (0, -0.0117, 0.088), "#F2F6F8", "glass", thin_walled=True, collision=False),
             cyl("Coil", 0.060, 0.013, -0.0081, 0.102, coil, "plastic"),
             cyl("CoilHole", 0.028, 0.0136, -0.0081, 0.102, "#22262D", "matte", False),
             _box("Tie", (0.008, 0.0145, 0.064), (0, -0.0081, 0.102), cyan, "plastic", collision=False),
             _box("PlugC", (0.009, 0.006, 0.022), (-0.016, -0.0062, 0.054), "#C9CDD2", "metal"),
             _box("PlugCBoot", (0.011, 0.007, 0.016), (-0.016, -0.0062, 0.069), coil, "plastic"),
             _box("PlugA", (0.013, 0.0055, 0.022), (0.016, -0.0062, 0.054), "#C9CDD2", "metal"),
             _box("PlugABoot", (0.016, 0.008, 0.016), (0.016, -0.0062, 0.069), coil, "plastic")]
    return Product(slug="usb_cable_blister", name="USB 充電ケーブル Type-C 1.0m", shape_class="assembly",
                   category="household", dims=Dimensions(0.20, 0.09, depth=0.0233), mass_kg=0.06,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入った USB ケーブル（台紙 90 × 200 mm）で、寸法・質量は代表値。巻いたケーブルは円柱、コネクタは直方体で表す。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["USB ケーブル", "充電ケーブル", "Type-C", "スマホ用品", "ブリスター", "USB cable",
                         "charging cable", "blister pack"],
                   photos=[], colors=Colors(label_base=black), images=[front, back], parts=parts)


# ---------------------------------------------------------------- ストッキング


def stockings_pack() -> Product:
    W, H, D = 140.0, 215.0, 15.0
    rose, wine, beige, white = "#F6E3E3", "#8C2F4A", "#E3C2A6", "#FFFFFF"
    s = 6

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#FFF6F6", "#F0D6D9")
        return f

    fr = face(W, H, 2471)
    _hang_hole(fr, W / 2, 4, "#5E1A2E")
    fr.rect(0, 14, W, 40, fill=wine)
    fr.text(W / 2, 27, "ストッキング", 13, white, 900)
    fr.text(W / 2, 48, "伝線しにくい  つま先補強", 5.0, wine, 800)
    fr.rect(22, 58, W - 22, 160, fill="#FFFFFF", radius=4)  # 中の商品が見える窓（たたんだストッキング）
    fr.gradient(26, 62, W - 26, 156, mix(beige, white, 0.25), mix(beige, "#B48A6A", 0.25))
    fr.pattern(26, 62, W - 26, 156, "stripes", mix(beige, "#FFFFFF", 0.35), 2.0, 0.2)
    for k in range(4):
        y = 70 + k * 24
        fr.line([(26, y), (W - 26, y)], mix(beige, "#8A6448", 0.4), 0.5)
    fr.rect(W - 56, 140, W - 14, 172, fill=wine, radius=4)
    fr.text(W - 35, 150, "M〜L", 8, white, 900)
    fr.text(W - 35, 162, "1足", 5, white, 800)
    fr.rect(14, 166, 76, 180, fill=white, radius=2)
    fr.rect(16, 168, 26, 178, fill=beige)
    fr.text(51, 173, "ナチュラルベージュ", 3.4, INK, 800, max_w=46)
    fr.text(W / 2, 192, "静電気防止  UV カット", 4.4, INK, 700)
    fr.rect(0, H - 12, W, H, fill=wine)
    fr.text(W / 2, H - 6, "PANTYHOSE", 4.0, white, 800, spacing=1.0)
    bk = face(W, H, 2472)
    _hang_hole(bk, W / 2, 4, "#5E1A2E")
    bk.rect(0, 14, W, 26, fill=wine)
    bk.text(W / 2, 20, "ストッキング  ナチュラルベージュ  M〜L", 5.0, white, 800)
    bk.rect(10, 32, W - 10, 200, fill=white, radius=3)
    yb = bk.table(16, 38, W - 16, "サイズ", [("M〜L", "身長 150〜170cm  ヒップ 85〜98cm")], 4.2)
    yb = bk.table(16, yb + 4, W - 16, "", [("品名", "パンティストッキング"), ("組成", "ナイロン 86%  ポリウレタン 14%"),
                                         ("数量", "1足"), ("販売者", "架空の会社")], 4.2)
    bk.paragraph(16, yb + 4, W - 16, "【お取り扱い】はく前にアクセサリーを外し、爪を整えてください。"
                 "洗濯はネットに入れて手洗いまたは弱水流で。乾燥機は使わないでください。\n" + NOTICE, 3.6, INK, 400)
    bk.barcode(16, 164, 46, 28)
    bk.recycle(86, 178, 10, "紙", wine, sub="台紙")
    bk.recycle(108, 178, 10, "プラ", wine, sub="袋")
    sides = []
    for k, seed in enumerate((2473, 2474)):
        sd = face(D, H, seed)
        sd.vtext(D / 2, 30, "ストッキング", 8, wine, 900)
        sd.vtext(D / 2, 140, "M〜L" if k == 0 else "1足", 7, INK, 900)
        sides.append(sd)
    tp, bt = face(W, D, 2475), face(W, D, 2476)
    tp.text(W / 2, D / 2, "ストッキング  M〜L  ナチュラルベージュ", 5.4, wine, 900)
    bt.text(W / 2, D / 2, NOTICE, 4.0, INK, 500, max_w=W - 10)
    imgs = _faces((fr, bk, *sides, tp, bt), "film", 2480, 0.7)
    return Product(slug="stockings_pack", name="ストッキング ナチュラルベージュ M〜L", shape_class="box",
                   category="household", dims=Dimensions(0.215, 0.14, depth=0.015), mass_kg=0.045, material="paper",
                   description="形は一般的な台紙入りのストッキングの平たい袋（140 × 215 mm・厚さ 15 mm）を箱で近似したもので、寸法・質量は代表値。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["ストッキング", "パンスト", "衣料", "stockings", "pantyhose"], photos=[],
                   colors=Colors(label_base=rose), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 冷却シート


def cooling_gel_sheet_box() -> Product:
    W, H, D = 125.0, 150.0, 45.0
    sky, blue, navy, white = "#DDF1FB", "#1E7BD0", "#0D3E78", "#FFFFFF"
    s = 7

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#F3FBFF", "#BFE3F7")
        f.rect(0, h - 5, w, h, fill=navy)
        return f

    fr = face(W, H, 2491)
    fr.pattern(0, 26, W, H - 5, "dots", mix("#DDF1FB", white, 0.6), 6, 0.5)
    fr.rect(0, 0, W, 26, fill=blue)
    fr.text(W / 2, 13, "ひんやり 8時間", 8, white, 900)
    fr.text(W / 2, 42, "冷却ジェルシート", 12, navy, 900, max_w=W - 12)
    fr.text(W / 2, 56, "おでこに貼って すっきり冷やす", 4.6, INK, 700)
    fr.rect(18, 66, 84, 106, fill="#FFFFFF", outline=mix(blue, white, 0.4), width=0.6, radius=6)  # シートの絵
    fr.rect(21, 69, 81, 103, fill="#BFE6FA", radius=5)
    fr.pattern(21, 69, 81, 103, "waves", mix("#BFE6FA", blue, 0.25), 4, 0.4)
    for k in range(3):  # 冷たさの線
        fr.line([(90 + k * 6, 72), (96 + k * 6, 86), (90 + k * 6, 100)], mix(blue, white, 0.2), 1.0)
    fr.ellipse(W - 42, 100, W - 8, 134, fill="#F2C230")
    fr.text(W - 25, 112, "12枚", 7, navy, 900)
    fr.text(W - 25, 123, "入り", 4.6, navy, 900)
    fr.rect(10, 114, 76, 138, fill=white, radius=3)
    fr.text(43, 121, "メントール配合", 4.2, blue, 900)
    fr.text(43, 131, "はがれにくい  無香料", 3.6, INK, 700)
    fr.text(W / 2, H - 2.5, "COOLING GEL SHEET", 3.0, white, 800, spacing=0.8)
    bk = face(W, H, 2492)
    bk.rect(8, 8, W - 8, H - 12, fill=white, radius=3)
    yb = bk.table(12, 12, W - 12, "", [("品名", "冷却ジェルシート"), ("サイズ", "50 × 110 mm"), ("枚数", "12枚"),
                                     ("成分", "水、グリセリン、ポリアクリル酸Na、メントール"), ("販売者", "架空の会社")], 3.6)
    bk.paragraph(12, yb + 3, W - 12, "【使用方法】フィルムをはがし、ジェル面を肌に貼ってください。"
                 "1枚の使用は約8時間を目安にしてください。\n【ご注意】傷・湿疹のある所には使わないでください。"
                 "かぶれたときはすぐにはがしてください。乳幼児に使うときは大人がそばで見守ってください。"
                 "使用後は袋のチャックをしっかり閉めてください。\n" + NOTICE, 3.2, INK, 400)
    bk.barcode(14, H - 38, 36, 22)
    bk.recycle(70, H - 27, 9, "紙", navy, sub="箱")
    bk.recycle(90, H - 27, 9, "プラ", navy, sub="袋")
    sides = []
    for k, seed in enumerate((2493, 2494)):
        sd = face(D, H, seed)
        sd.rect(0, 0, D, 16, fill=blue)
        sd.text(D / 2, 8, "8時間", 6, white, 900)
        sd.vtext(D / 2, 26, "冷却ジェルシート", 6.2, navy, 900)
        sd.text(D / 2, H - 14, "12枚" if k == 0 else "無香料", 5, blue, 900)
        sides.append(sd)
    tp = face(W, D, 2495)
    tp.text(W / 2, 14, "冷却ジェルシート  12枚入", 6.4, navy, 900)
    tp.rect(W / 2 - 28, 22, W / 2 + 28, 34, outline=blue, width=0.6, radius=6)
    tp.text(W / 2, 28, "ここを押してあける", 4.0, blue, 800)
    bt = face(W, D, 2496)
    bt.text(W / 2, 14, "使用期限 2029.03", 4.6, INK, 700)
    bt.text(W / 2, 26, NOTICE, 3.2, INK, 500, max_w=W - 10)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 2500)
    return Product(slug="cooling_gel_sheet_box", name="冷却ジェルシート 12枚入", shape_class="box", category="household",
                   dims=Dimensions(0.15, 0.125, depth=0.045), mass_kg=0.24, material="paper",
                   description="形は一般的な冷却ジェルシートの箱（幅 125 mm・高さ 150 mm・奥行き 45 mm、12 枚入り）で、寸法・質量は代表値。",
                   tags=["冷却シート", "冷却ジェルシート", "ひんやり", "衛生用品", "cooling gel sheet"],
                   photos=[], colors=Colors(label_base=sky), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- ボールペン


def ballpoint_pen() -> Product:
    L, d = 0.140, 0.0108  # 長さ・軸の太さ。寝かせて置く（長い軸が X、ペン先が -X）
    clear, ink, grip, metal = "#DCE6EE", "#1A2A6C", "#2B2F36", "#C4C8CC"
    x0 = -L / 2

    def seg(name, a, b, dia, color, fin="plastic", collision=True):
        return Part(name, "cylinder", [dia, dia, b - a], [x0 + (a + b) / 2, 0, d / 2], [0, 90, 0], color, fin,
                    collision=collision)

    c = Canvas(52.0, 4.0, 40, ink, seed=2511)  # クリップの上面
    c.gradient(0, 0, 52, 4, "#2A3C88", "#14205A")
    c.text(26, 2, "BALL PEN 0.5  架空の文具", 2.2, "#FFFFFF", 800, max_w=50)
    clip_img = _face(c.array(), "film", 2511, 0.4)
    parts = [seg("Tip", 0.000, 0.004, 0.0016, metal, "metal"),
             seg("Cone", 0.003, 0.012, 0.0055, metal, "metal"),
             seg("Grip", 0.011, 0.042, 0.0108, grip, "matte"),
             seg("Barrel", 0.041, 0.118, 0.0100, clear, "glass"),
             seg("Refill", 0.012, 0.120, 0.0032, ink, "plastic", collision=False),
             seg("Cap", 0.117, 0.132, 0.0104, ink, "glossy"),
             seg("Knock", 0.131, 0.140, 0.0070, ink, "glossy"),
             _box("Clip", (0.052, 0.004, 0.0016), (x0 + 0.098, 0, d + 0.0002), ink, "glossy", {"top": 0})]
    return Product(slug="ballpoint_pen", name="ノック式ボールペン 0.5mm 黒", shape_class="assembly",
                   category="household", dims=Dimensions(0.0118, 0.140, depth=0.0108), mass_kg=0.009,
                   material="plastic",
                   description="形は一般的なノック式の油性ボールペン（長さ 140 mm・軸径 10 mm、0.5 mm）を寝かせた円柱の組み合わせで近似したもので、寸法・質量は代表値。透明な軸から芯が見える。クリップは軸の上に置いた板で表す。",
                   tags=["ボールペン", "文房具", "筆記具", "ノック式", "ballpoint pen", "pen", "stationery"],
                   photos=[], colors=Colors(label_base=ink), images=[clip_img], parts=parts)


# ---------------------------------------------------------------- プリペイドカード


def prepaid_gift_card() -> Product:
    HW, HH = 90.0, 150.0  # 台紙
    KW, KH = 54.0, 85.6  # カード（ID-1 を縦にして貼る）
    violet, pink, gold, white = "#4A2C8C", "#E04C8A", "#F2C230", "#FFFFFF"
    h = Canvas(HW, HH, 10, white, seed=2521)
    h.gradient(0, 0, HW, HH, "#F7F2FF", "#DCCDF5")
    h.rect(0, 0, HW, 2, fill=violet)
    h.rect(0, HH - 2, HW, HH, fill=violet)
    _hang_hole(h, HW / 2, 5, violet)
    h.text(HW / 2, 21, "ギフトカード", 9, violet, 900)
    h.rect(HW / 2 - KW / 2 - 2, 30, HW / 2 + KW / 2 + 2, 30 + KH + 4, fill=mix("#DCCDF5", violet, 0.15), radius=4)
    h.text(HW / 2, 128, "3,000円分", 7, pink, 900)
    h.rect(8, 136, HW - 8, 146, fill=violet, radius=3)
    h.text(HW / 2, 141, "レジでお支払い後に使えます", 3.8, white, 800, max_w=HW - 20)
    front = _face(h.array(), "paper", 2521, 0.6)
    b = Canvas(HW, HH, 10, white, seed=2522)
    b.gradient(0, 0, HW, HH, "#FFFFFF", "#EEE8F8")
    b.rect(0, 0, HW, 2, fill=violet)
    b.rect(0, HH - 2, HW, HH, fill=violet)
    _hang_hole(b, HW / 2, 5, violet)
    b.text(HW / 2, 18, "ご利用方法", 5.4, violet, 900)
    y = b.paragraph(8, 24, HW - 8, "① レジでカードを店員に渡し、代金をお支払いください。\n"
                    "② レシートを受け取るとカードが有効になります。\n"
                    "③ カード裏面の銀色の部分をけずり、番号をサイトで登録してください。", 3.4, INK, 500)
    b.paragraph(8, y + 3, HW - 8, "【ご注意】有効にする前のカードには価値がありません。"
                "購入後の返品・換金はできません。番号を他人に教えないでください。"
                "「電話で番号を教えて」などと言われたら詐欺の可能性があります。\n" + NOTICE, 3.0, INK, 400)
    b.barcode(HW / 2 - 24, HH - 34, 48, 22)
    b.recycle(HW - 12, HH - 6, 6, "紙", violet)
    back = _face(b.array(), "paper", 2522, 0.6)
    k = Canvas(KW, KH, 14, violet, seed=2523)
    k.gradient(0, 0, KW, KH, "#6A3CC8", "#2A145C")
    for i in range(6):  # 斜めの光の帯
        k.polygon([(-10 + i * 14, KH), (4 + i * 14, KH), (KW + i * 14 - 30, 0), (KW + i * 14 - 44, 0)],
                  fill=mix("#5130A8", pink, 0.08 + 0.05 * (i % 3)))
    k.text(KW / 2, 14, "GIFT CARD", 6.4, white, 900, spacing=0.6)
    k.ellipse(KW / 2 - 14, 26, KW / 2 + 14, 54, fill=gold)
    k.text(KW / 2, 40, "¥", 16, violet, 900)
    k.text(KW / 2, 66, "3,000円", 9, white, 900)
    k.text(KW / 2, 77, "架空のギフトカード", 3.4, mix(white, pink, 0.3), 700)
    card = _face(k.array(), "film", 2523, 0.5)
    parts = [_box("Holder", (0.090, 0.0008, 0.150), (0, 0, 0.075), white, "matte", {"front": 0, "back": 1}),
             _box("Card", (0.054, 0.0008, 0.0856), (0, -0.00085, 0.150 - 0.032 - 0.0428), violet, "glossy",
                  {"front": 2})]
    return Product(slug="prepaid_gift_card", name="ギフトカード 3,000円", shape_class="assembly",
                   category="household", dims=Dimensions(0.150, 0.090, depth=0.00165), mass_kg=0.012,
                   material="paper",
                   description="形は一般的なコンビニの吊り下げ式プリペイドカード（台紙 90 × 150 mm に ID-1 サイズのカード 54 × 85.6 mm を貼ったもの）で、寸法・質量は代表値。カード名・金額の表記は架空。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["プリペイドカード", "ギフトカード", "カード", "prepaid card", "gift card"], photos=[],
                   colors=Colors(label_base="#EEE8F8"), images=[front, back, card], parts=parts)


# ---------------------------------------------------------------- ミントタブレット


def mint_tablet_case() -> Product:
    W, H, D = 40.0, 56.0, 16.0  # 本体（ふたは部品）
    mint, green, dark, white = "#DFF5EA", "#1C9C6A", "#0E4D35", "#FFFFFF"
    s = 16

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, white, seed)
        f.gradient(0, 0, w, h, "#F2FCF7", "#BDE8D2")
        return f

    fr = face(W, H, 2541)
    fr.photo("mint", 0, 30, W, H, crop=(0.2, 0.2, 0.8, 0.7))
    fr.text(W / 2, 7, "STRONG", 3.6, green, 900, spacing=0.6)
    fr.text(W / 2, 16, "ミント", 9, dark, 900)
    fr.text(W / 2, 25, "タブレット", 5.0, dark, 900)
    fr.rect(4, H - 11, W - 4, H - 3, fill=white, radius=3)
    fr.text(W / 2, H - 7, "シュガーレス 30g", 3.4, green, 900)
    bk = face(W, H, 2542)
    yb = bk.table(2.5, 3, W - 2.5, "", [("名称", "清涼菓子"), ("原材料名", "還元パラチノース、ハッカ油、甘味料（スクラロース）、香料"),
                                       ("内容量", "30g"), ("販売者", "架空の会社")], 2.0)
    yb = bk.paragraph(2.5, yb + 1, W - 2.5, NOTICE, 1.8, INK, 500)
    bk.barcode(4, H - 13, 22, 11)
    bk.recycle(33, H - 7, 5, "プラ", dark)
    sides = []
    for k, seed in enumerate((2543, 2544)):
        sd = face(D, H, seed)
        sd.vtext(D / 2, 6, "ミント", 5, dark, 900)
        sd.text(D / 2, H - 8, "30g" if k == 0 else "MINT", 3.6, green, 900)
        sides.append(sd)
    tp = face(W, D, 2545)
    bt = face(W, D, 2546)
    bt.text(W / 2, 5, "賞味期限 2027.08", 2.6, INK, 700)
    bt.text(W / 2, 10, "MINT TABLET 30g", 2.0, INK, 500, max_w=W - 3)
    lid = Canvas(W + 1, 12.0, s, green, seed=2547)  # ふたの正面・裏
    lid.gradient(0, 0, W + 1, 12, "#25B57E", "#147550")
    lid.text((W + 1) / 2, 6, "MINT TABLET", 3.4, white, 900, spacing=0.4)
    lt = Canvas(W + 1, D + 0.8, s, green, seed=2548)  # ふたの上面
    lt.gradient(0, 0, W + 1, D + 0.8, "#25B57E", "#147550")
    lt.rect(W / 2 - 8, D / 2 - 2.5, W / 2 + 9, D / 2 + 3.3, fill=mix(green, "#000000", 0.25), radius=2)
    lt.text((W + 1) / 2, D / 2 + 0.4, "OPEN", 2.6, white, 900)
    imgs = _faces((fr, bk, *sides, tp, bt), "film", 2550, 0.5) + [_face(lid.array(), "film", 2557, 0.5),
                                                                    _face(lt.array(), "film", 2558, 0.5)]
    parts = [_box("Lid", (0.041, 0.0168, 0.012), (0, 0, H / 1000 + 0.0055), green, "glossy",
                  {"front": 6, "back": 6, "top": 7})]
    return Product(slug="mint_tablet_case", name="ミントタブレット ストロング 30g", shape_class="box", category="food",
                   dims=Dimensions(0.056, 0.040, depth=0.016), mass_kg=0.04, material="plastic",
                   description="形は一般的なフリップ式のふたが付いたミントタブレットのケース（本体 40 × 56 × 16 mm、ふた 12 mm）で、寸法・質量は代表値。ふたは部品で表す。",
                   tags=["ミント", "タブレット", "清涼菓子", "お菓子", "mint", "mint tablets", "candy"],
                   photos=["mint"], colors=Colors(cap=green, label_base=mint), images=imgs, faces=BOX_FACES,
                   parts=parts)


PRODUCTS = {f.__name__: f for f in (vinyl_umbrella_65cm, weekly_magazine, newspaper_folded, rock_ice_1kg,
                                    usb_cable_blister, stockings_pack, cooling_gel_sheet_box, ballpoint_pen,
                                    prepaid_gift_card, mint_tablet_case)}
