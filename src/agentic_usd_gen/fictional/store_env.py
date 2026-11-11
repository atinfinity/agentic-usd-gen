"""架空の商品のデザイン: 店舗の内装・建具（床・壁・天井・照明・掲示物・ドア・トイレ）。

products.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の製品の一般的な値にする。
カテゴリは environment（売り場やバックヤードを組み立てる内装・設備）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Joint, Light, Part
from .base import Product
from .paint import Canvas, finish, mix, trim_safe
from .products import _lamp

ENV = "environment"
WHITE = "#FFFFFF"
ALU, ALU_DARK = "#B9BEC4", "#8E949B"
STAINLESS = "#C9CDD1"
GLASS = "#F2F6F8"
PORCELAIN = "#F6F6F3"
DAYLIGHT = 5000.0  # 店舗の天井照明（昼白色）の色温度 [K]


def _p(name, shape, size, center, color, finish_="plastic", rot=None, faces=None, collision=True, material=None,
       **kw) -> Part:
    return Part(name=name, shape=shape, size=list(size), center=list(center), rotation=list(rot or [0, 0, 0]),
                color=color, finish=finish_, faces=faces, collision=collision, material=material, **kw)


def _img(c: Canvas, kind: str, seed: int, strength: float = 0.4) -> np.ndarray:
    return trim_safe(finish(c.array(), kind, seed, strength))


def _link(parts: list[Part], prefix: str, link: str) -> None:
    for p in parts:
        if p.name.startswith(prefix):
            p.link = link


# ---------------------------------------------------------------- 床・壁・天井


def floor_tile_panel() -> Product:
    """600 角の磁器質の床タイル 4 枚（1.2 m 角）。目地は中央の十字と、敷き詰めたときの外周の半分。

    参考: https://commons.wikimedia.org/wiki/File:LAWSON-FushimiMinami.JPG（PD）、
    https://commons.wikimedia.org/wiki/File:Detail_of_ceramic_tile_floor_in_store_-_Fort_McDowell,_Post_Exchange,_Angel_Island_State_Park,_Angel_Island,_Marin_County,_CA_HABS_CAL,21-ANGEL,2H-12.tif（PD）
    """
    W, T = 1.2, 0.010
    base, grout = "#E4E1DA", "#B7B2A8"
    c = Canvas(1200, 1200, None, base, 6001)
    c.gradient(0, 0, 1200, 1200, "#E8E5DE", "#DEDAD2")
    for i in range(2):
        for j in range(2):  # 1 枚ずつ少し色をずらす
            x0, y0 = i * 600, j * 600
            c.rect(x0, y0, x0 + 600, y0 + 600, fill=mix(base, ("#EFECE6", "#DAD6CD", "#E2DFD7", "#E9E6DF")[i * 2 + j], 0.5))
    for _ in range(9000):  # 御影石風の粒
        x, y = c.rng.uniform(0, 1200), c.rng.uniform(0, 1200)
        r = c.rng.uniform(0.4, 1.6)
        c.ellipse(x - r, y - r, x + r, y + r, fill=c.rng.choice(["#C9C4BA", "#F4F2EE", "#B0AAA0", "#D4CFC6"]))
    c.rect(598.5, 0, 601.5, 1200, fill=grout)
    c.rect(0, 598.5, 1200, 601.5, fill=grout)
    t = 0.0
    while t < 1200:  # 外周の目地（半分の幅）。汚れのむらを付ける（縁が単色だと切り抜かれる）
        seg = c.rng.uniform(8, 40)
        col = c.rng.choice([grout, "#9C968B", "#C9C4BA"])
        for v in (0, 1198.5):
            c.rect(t, v, t + seg, v + 1.5, fill=col)
            c.rect(v, t, v + 1.5, t + seg, fill=col)
        t += seg
    img = _img(c, "paper", 6001, 0.25)
    parts = [_p("Tiles", "box", (W, W, T), (0, 0, T / 2), base, "plastic", faces={"top": 0}, material="stone", bevel=0)]
    return Product(slug="floor_tile_panel", name="床タイル 600角 4枚（1.2 m 角）", shape_class="assembly", category=ENV,
                   dims=Dimensions(T, W, depth=W), mass_kg=30.0, static=True, material="stone",
                   description="形はコンビニの売り場に多い 600 角の磁器質タイル（明るい御影石調・厚さ 10 mm）を 2 × 2 枚敷いた "
                               "1.2 m 角の床で、寸法・質量は代表値。並べて敷けるよう、外周の目地は半分の幅にしている。",
                   tags=["床", "床タイル", "磁器質タイル", "内装", "floor", "floor tile", "porcelain tile"],
                   colors=Colors(label_base=base), images=[img], parts=parts)


def entrance_mat() -> Product:
    """入口の足ふきマット（1.5 × 0.9 m）。グレーの畝に縁取りと文字。

    参考: https://commons.wikimedia.org/wiki/File:7-Eleven_JR_Kyobashi_station%27s_western_entrance_store.JPG（CC0。形の参考のみ）
    """
    W, D, T = 1.5, 0.9, 0.010
    gray, edge, ink = "#4A4D52", "#2E3034", "#C9CCD0"

    def face(text: bool) -> np.ndarray:
        c = Canvas(1500, 900, None, gray, 6011)
        c.gradient(0, 0, 1500, 900, "#53565B", "#43464B")
        for y in range(20, 880, 8):  # 畝
            c.line([(20, y), (1480, y)], mix(gray, "#000000", 0.25), 2.5)
        c.rect(0, 0, 1500, 20, fill=edge)
        c.rect(0, 880, 1500, 900, fill=edge)
        c.rect(0, 0, 20, 900, fill=edge)
        c.rect(1480, 0, 1500, 900, fill=edge)
        for k in range(700):  # 縁のゴムの粒（縁まで届かせる。縁が単色だと切り抜かれる）
            t, r = c.rng.uniform(0, 1500), c.rng.uniform(1.5, 3.5)
            col = c.rng.choice(["#3E4045", "#25272A"])
            c.ellipse(t - r, -r, t + r, r, fill=col)
            c.ellipse(t - r, 900 - r, t + r, 900 + r, fill=col)
            u = t * 0.6
            c.ellipse(-r, u - r, r, u + r, fill=col)
            c.ellipse(1500 - r, u - r, 1500 + r, u + r, fill=col)
        if text:
            c.rect(150, 300, 1350, 600, outline=ink, width=5, radius=30)
            c.text(750, 420, "いらっしゃいませ", 110, ink, 900)
            c.text(750, 535, "WELCOME", 60, ink, 800, spacing=12)
        return _img(c, "paper", 6011, 0.5)

    img, blank = face(True), face(False)  # 無地（Picture バリアントの Blank）は文字なし
    parts = [_p("Mat", "box", (W, D, T), (0, 0, T / 2), gray, "matte", faces={"top": 0}, material="fabric",
                bevel=0.004, blank=1)]
    return Product(slug="entrance_mat", name="入口の足ふきマット 1500×900", shape_class="assembly", category=ENV,
                   dims=Dimensions(T, W, depth=D), mass_kg=6.0, static=True, material="fabric",
                   description="形は店の自動ドアの内側に敷く一般的な足ふきマット（1500 × 900 mm・厚さ 10 mm、"
                               "ナイロンの畝にゴムの縁）で、寸法・質量は代表値。文字は架空のデザイン。",
                   tags=["玄関マット", "足ふきマット", "入口", "内装", "entrance mat", "door mat", "floor mat"],
                   colors=Colors(label_base=gray), images=[img, blank], parts=parts,
                   picture_places=["shop", "convenience_store", "supermarket", "cafe", "restaurant"])


def wall_panel_baseboard() -> Product:
    """白い化粧壁パネル（幅 1.2 m・高さ 2.7 m）と、下端のビニルの幅木。

    参考: https://commons.wikimedia.org/wiki/File:JRE_Fukushima-STA_NEWDAYS_Fukushima-West.jpg（CC0）
    """
    W, H, D = 1.2, 2.7, 0.020
    c = Canvas(1200, 2700, None, "#F3F2EE", 6021)
    c.gradient(0, 0, 1200, 2700, "#F6F5F2", "#ECEBE6")
    for _ in range(2500):  # 塗装のごく細かいむら
        x, y = c.rng.uniform(0, 1200), c.rng.uniform(0, 2700)
        c.ellipse(x - 1.5, y - 1.5, x + 1.5, y + 1.5, fill=c.rng.choice(["#EFEEEA", "#F7F6F3"]))
    c.rect(0, 0, 2, 2700, fill="#DCDAD4")  # 隣のパネルとの目地
    c.rect(1198, 0, 1200, 2700, fill="#DCDAD4")
    img = _img(c, "paper", 6021, 0.2)
    bb_h, bb_d = 0.10, 0.008
    parts = [_p("Panel", "box", (W, D, H), (0, 0, H / 2), "#F3F2EE", "matte", faces={"front": 0}, bevel=0),
             _p("Baseboard", "box", (W, bb_d, bb_h), (0, -D / 2 - bb_d / 2, bb_h / 2), "#4B4D50", "plastic",
                material="vinyl", bevel=0.002),
             _p("BaseboardLip", "box", (W, 0.004, 0.006), (0, -D / 2 - bb_d - 0.002, bb_h - 0.003), "#56585B",
                "plastic", collision=False, material="vinyl", bevel=0.001)]
    return Product(slug="wall_panel_baseboard", name="壁パネル（幅木付き）1.2 × 2.7 m", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D + bb_d + 0.004), mass_kg=28.0, static=True,
                   material="plastic",
                   description="形は売り場の壁の白い化粧パネル（幅 1.2 m・高さ 2.7 m・厚さ 20 mm）に、"
                               "高さ 100 mm のビニルの幅木を付けたもので、寸法・質量は代表値。横に並べて壁にする。",
                   tags=["壁", "壁パネル", "幅木", "内装", "wall", "wall panel", "baseboard", "skirting board"],
                   colors=Colors(label_base="#F3F2EE"), images=[img], parts=parts)


def ceiling_panel() -> Product:
    """システム天井（1.2 m 角）。穴あきの化粧石こうボード 4 枚を白い T バーで支える。上面が天井裏。

    参考: https://commons.wikimedia.org/wiki/File:LAWSON-FushimiMinami.JPG（PD）
    """
    W, T, bar_h = 1.2, 0.012, 0.004
    c = Canvas(1200, 1200, None, "#F1F0EC", 6031)
    c.gradient(0, 0, 1200, 1200, "#F4F3EF", "#EAE9E4")
    c.pattern(0, 0, 1200, 1200, "dots", "#C6C4BE", 12, 1.2)  # 吸音の穴
    for _ in range(1500):
        x, y = c.rng.uniform(0, 1200), c.rng.uniform(0, 1200)
        c.ellipse(x - 0.6, y - 0.6, x + 0.6, y + 0.6, fill="#D9D7D1")
    img = _img(c, "paper", 6031, 0.3)
    H = T + bar_h
    parts = [_p("Boards", "box", (W, W, T), (0, 0, bar_h + T / 2), "#F1F0EC", "matte", faces={"bottom": 0},
                material="paper", bevel=0)]
    bw = 0.024
    for k, v in enumerate((-W / 2 + bw / 4, 0.0, W / 2 - bw / 4)):  # T バー（外周は隣と分け合うので半分の幅）
        w = bw / 2 if k != 1 else bw
        parts += [_p(f"BarX{k}", "box", (W, w, bar_h), (0, v, bar_h / 2), WHITE, "plastic", collision=False,
                     material="steel", bevel=0),
                  _p(f"BarY{k}", "box", (w, W, bar_h), (v, 0, bar_h / 2), WHITE, "plastic", collision=False,
                     material="steel", bevel=0)]
    return Product(slug="ceiling_panel", name="システム天井 1.2 m 角（穴あきボード）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=W), mass_kg=12.0, static=True, mount="ceiling",
                   material="paper",
                   description="形は店舗の天井に多いシステム天井（600 角の穴あき化粧石こうボード 4 枚と、幅 24 mm の白い T バー）"
                               "の 1.2 m 角の区画で、寸法・質量は代表値。上面が天井裏に付く向き。外周の T バーは半分の幅で、"
                               "並べると隣とつながる。",
                   tags=["天井", "システム天井", "天井ボード", "Tバー", "内装", "ceiling", "ceiling panel",
                         "suspended ceiling", "ceiling tile"],
                   colors=Colors(label_base="#F1F0EC"), images=[img], parts=parts)


# ---------------------------------------------------------------- 照明


def ceiling_base_light() -> Product:
    """天井付けの LED ベースライト（40 形・逆富士）。下面の乳白のカバーが光る。上面が天井に付く。

    参考: https://commons.wikimedia.org/wiki/File:LAWSON-FushimiMinami.JPG（PD）
    """
    L, Wd, H = 1.25, 0.23, 0.060
    lens_t = 0.006
    body = "#F3F3F1"
    lamp, lux = _lamp("Lens", (L - 0.05, 0.11, lens_t), (0, 0, lens_t / 2), "#FBFBF8", 8000.0, DAYLIGHT)
    # 逆富士の断面（天井側が広く、下が細い台形）を X 方向に伸ばす: prism は Y に押し出すので Z まわりに 90° 回す
    parts = [_p("Body", "prism", (Wd, L, H - lens_t), (0, 0, lens_t + (H - lens_t) / 2), body, "plastic",
                rot=(0, 0, 90), material="steel", profile=[[-0.26, 0.0], [0.26, 0.0], [0.5, 1.0], [-0.5, 1.0]]),
             lamp]
    return Product(slug="ceiling_base_light", name="LED ベースライト 40形（逆富士・天井付け）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, L, depth=Wd), mass_kg=3.0, static=True, mount="ceiling",
                   material="steel",
                   description="形は店舗・事務所の天井に付ける一般的な 40 形の LED ベースライト（逆富士形、長さ 1250 mm・"
                               "幅 230 mm・高さ 60 mm）で、寸法・質量は代表値。上面が天井に付く向き。"
                               "下面の乳白のカバーが昼白色（5000 K）で光る（Lighting バリアント）。",
                   tags=["照明", "天井照明", "ベースライト", "LED", "逆富士", "内装", "ceiling light", "LED base light",
                         "linear light", "fluorescent fixture"],
                   colors=Colors(label_base=body), images=[], parts=parts, lights=[lux])


def downlight() -> Product:
    """埋め込みのダウンライト（埋込穴 φ125）。天井板の下面はフランジの上面（z = 10 mm）で、本体は天井裏に入る。

    参考: https://commons.wikimedia.org/wiki/File:JRE_Fukushima-STA_NEWDAYS_Fukushima-West.jpg（CC0）
    """
    D, H = 0.150, 0.100
    white = "#F5F5F3"
    parts = [_p("Flange", "torus", (D, D, 0.010), (0, 0, 0.005), white, "plastic"),
             _p("Reflector", "cylinder", (0.132, 0.132, 0.003), (0, 0, 0.0145), "#E9E9E6", "metal", collision=False),
             _p("Lens", "cylinder", (0.090, 0.090, 0.002), (0, 0, 0.012), "#FDFCF6", "light", collision=False),
             _p("Housing", "revolve", (0.120, 0.120, H - 0.016), (0, 0, 0.016 + (H - 0.016) / 2), "#D9DADC", "metal",
                profile=[[0, 0], [0.95, 0], [1.0, 0.1], [1.0, 0.75], [0.7, 1.0], [0, 1.0]], material="aluminum"),
             _p("SpringL", "box", (0.004, 0.012, 0.05), (-0.064, 0, 0.045), STAINLESS, "metal", collision=False),
             _p("SpringR", "box", (0.004, 0.012, 0.05), (0.064, 0, 0.045), STAINLESS, "metal", collision=False)]
    lux = Light(name="LensLux", size=[0.08, 0.08], center=[0, 0, 0.0105], intensity=40000.0, kelvin=3500.0)
    return Product(slug="downlight", name="LED ダウンライト 埋込穴φ125", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, D, depth=D), mass_kg=0.6, static=True, mount="ceiling", material="aluminum",
                   description="形は店舗の天井に埋め込む一般的な LED ダウンライト（埋込穴 φ125・フランジ φ150・高さ 100 mm）で、"
                               "寸法・質量は代表値。天井板の下面はフランジの上面（底から 10 mm）で、それより上は天井裏に入る。"
                               "下向きに温白色（3500 K）で光る（Lighting バリアント）。",
                   tags=["照明", "天井照明", "ダウンライト", "LED", "埋込", "内装", "downlight", "recessed light",
                         "can light"],
                   colors=Colors(label_base=white), images=[], parts=parts, lights=[lux])


def _runner(c: Canvas, x: float, y: float, s: float, color: str) -> None:
    """走る人の絵記号（x, y は頭の中心、s は大きさ [mm]）。"""
    w = s * 0.13
    c.ellipse(x - s * 0.11, y - s * 0.11, x + s * 0.11, y + s * 0.11, fill=color)
    hip = (x - s * 0.18, y + s * 0.55)
    neck = (x - s * 0.02, y + s * 0.17)
    c.line([neck, hip], color, w * 1.3)
    c.line([hip, (x + s * 0.12, y + s * 0.78), (x + s * 0.05, y + s * 1.08)], color, w)  # 前の脚
    c.line([hip, (x - s * 0.36, y + s * 0.80), (x - s * 0.62, y + s * 0.90)], color, w)  # 後ろの脚
    c.line([(x - s * 0.06, y + s * 0.27), (x + s * 0.22, y + s * 0.40), (x + s * 0.36, y + s * 0.26)], color, w * 0.8)
    c.line([(x - s * 0.06, y + s * 0.27), (x - s * 0.34, y + s * 0.30), (x - s * 0.46, y + s * 0.48)], color, w * 0.8)


def emergency_exit_sign() -> Product:
    """壁付けの避難口誘導灯（緑の地に、扉へ走る人の白い絵記号）。表示面は常に光る。

    参考: https://commons.wikimedia.org/wiki/File:Japanese_Square_Old_Style_Exit_Sign.jpg（PD）、
    https://commons.wikimedia.org/wiki/File:%E5%B7%A6%E3%83%94%E3%82%AF%E3%83%88%E5%8F%B3%E7%9F%A2%E5%8D%B0_%E8%83%BD%E7%BE%8E%E9%98%B2%E7%81%BD%E8%A3%BD.jpg（CC0）
    """
    W, H, D = 0.38, 0.20, 0.045
    green = "#009A44"
    pw, ph = 340.0, 160.0
    c = Canvas(pw, ph, None, green, 6041)
    c.gradient(0, 0, pw, ph, "#08A34C", "#00893C")
    c.rect(4, 4, pw - 4, ph - 4, outline="#E8F6EC", width=1.2, radius=6)
    c.rect(220, 22, 300, 140, fill=WHITE)  # 扉の開口
    c.rect(232, 30, 292, 140, fill="#00893C")
    c.polygon([(232, 30), (268, 42), (268, 140), (232, 140)], fill=WHITE)  # 開いた扉
    _runner(c, 150, 38, 100, WHITE)
    c.text(70, 140, "非常口", 18, WHITE, 900)
    img = _img(c, "screen", 6041, 0.3)
    parts = [_p("Housing", "box", (W, D, H), (0, D / 2 - D, H / 2), "#F4F4F2", "plastic", bevel=0.004),
             _p("Panel", "box", (pw / 1000, 0.004, ph / 1000), (0, -D - 0.001, H / 2), green, "screen",
                faces={"front": 0}, collision=False, bevel=0)]
    for p in parts:  # 背面（y = 0）が壁に付く
        p.center[1] += D / 2
    return Product(slug="emergency_exit_sign", name="避難口誘導灯（壁付け）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D + 0.003), mass_kg=2.5, static=True, material="plastic",
                   description="形は店舗の出入口の上に付ける一般的な LED の避難口誘導灯（B 級相当、表示面 340 × 160 mm・"
                               "本体 380 × 200 × 45 mm）で、寸法・質量は代表値。背面を壁に付ける。表示面（緑の地に扉へ走る人）"
                               "は停電時も光る設備なので、常に光る面にしている。絵記号は簡単に描いたもの。",
                   tags=["誘導灯", "避難口誘導灯", "非常口", "非常口サイン", "内装", "exit sign", "emergency exit sign",
                         "exit light"],
                   colors=Colors(label_base=green), images=[img], parts=parts,
                   screen_places=["any"])  # 誘導灯はどの建物にも付く


def aisle_sign_hanging() -> Product:
    """天井から 2 本のワイヤーで吊る売り場の案内板（両面）。上面が天井に付く。

    参考: https://commons.wikimedia.org/wiki/File:LAWSON-FushimiMinami.JPG（PD）
    """
    W, bh, t, drop = 0.90, 0.25, 0.010, 0.60
    H = bh + drop
    navy = "#1F3B73"

    def face(num: str, ja: str, en: str, accent: str, seed: int) -> np.ndarray:
        c = Canvas(900, 250, None, WHITE, seed)
        c.gradient(0, 0, 900, 250, "#FFFFFF", "#EEF1F5")
        c.rect(0, 0, 900, 14, fill=accent)
        c.rect(0, 236, 900, 250, fill=accent)
        c.ellipse(40, 55, 180, 195, fill=accent)
        c.text(110, 125, num, 96, WHITE, 900)
        c.text(530, 108, ja, 78, navy, 900, max_w=620)
        c.text(530, 188, en, 40, mix(navy, WHITE, 0.25), 800, spacing=4, max_w=620)
        return _img(c, "plastic", seed, 0.3)

    imgs = [face("3", "お弁当・おにぎり", "BENTO・RICE BALLS", "#D84315", 6051),
            face("4", "お飲み物", "DRINKS", "#1565C0", 6052)]
    parts = [_p("Board", "box", (W, t, bh), (0, 0, bh / 2), WHITE, "plastic", faces={"front": 0, "back": 1},
                bevel=0.003, blank="#F6F7F9"),
             _p("Rail", "box", (W, t + 0.006, 0.012), (0, 0, bh + 0.006), "#B9BEC4", "metal", collision=False,
                material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.08, W / 2 - 0.08)):
        parts += [_p(f"Wire{k}", "cylinder", (0.0015, 0.0015, drop - 0.012), (x, 0, bh + 0.012 + (drop - 0.012) / 2),
                     STAINLESS, "metal", collision=False, material="steel"),
                  _p(f"CeilingPlate{k}", "cylinder", (0.040, 0.040, 0.006), (x, 0, H - 0.003), WHITE, "plastic",
                     collision=False)]
    return Product(slug="aisle_sign_hanging", name="売り場の吊り案内板（両面）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=0.040), mass_kg=1.8, static=True, mount="ceiling", material="plastic",
                   description="形は売り場の通路の上に天井からワイヤーで吊る一般的な案内板（900 × 250 mm・厚さ 10 mm、"
                               "吊り下げ 600 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。"
                               "表と裏で別の売り場を表示する。文字とデザインは架空。",
                   tags=["案内板", "吊り看板", "売り場サイン", "通路", "内装", "aisle sign", "hanging sign",
                         "store signage"],
                   colors=Colors(label_base=WHITE), images=imgs, parts=parts,
                   picture_places=["convenience_store", "supermarket", "shop"])


# ---------------------------------------------------------------- 掲示物


def wall_poster() -> Product:
    """アルミのスナップフレーム（B2）に入れた売り場のポスター。背面を壁に付ける。

    写真: karaage（CC0。ポスターに合成）
    """
    pw, ph = 515.0, 728.0
    fw, fh, fd = 0.545, 0.758, 0.012
    red, yellow = "#C62828", "#FFD54F"
    c = Canvas(pw, ph, None, red, 6061)
    c.gradient(0, 0, pw, ph, "#D32F2F", "#9E1B1B")
    c.photo("karaage", 0, 150, pw, 560, crop=(0.12, 0.04, 0.92, 0.80))
    c.rect(0, 0, pw, 150, fill="#B71C1C")
    c.text(pw / 2, 52, "期間限定", 40, yellow, 900)
    c.text(pw / 2, 112, "からあげ 増量中！", 64, WHITE, 900, max_w=480)
    c.rect(0, 560, pw, ph, fill="#FFF8E1")
    c.ellipse(30, 580, 190, 700, fill=red)
    c.text(110, 625, "1個", 26, WHITE, 900)
    c.text(110, 665, "増量", 34, WHITE, 900)
    c.text(350, 610, "5個入", 44, "#3E2723", 900)
    c.text(350, 670, "238円（税込）", 52, red, 900, max_w=300)
    c.text(pw / 2, ph - 12, "※写真はイメージです。なくなり次第終了します。", 13, "#5D4037", 700)
    img = _img(c, "paper", 6061, 0.3)
    parts = [_p("Frame", "box", (fw, fd, fh), (0, fd / 2, fh / 2), ALU, "metal", material="aluminum", bevel=0.004),
             _p("Poster", "box", (pw / 1000, 0.001, ph / 1000), (0, -0.0005, fh / 2), WHITE, "matte",
                faces={"front": 0}, collision=False, material="paper", bevel=0, blank="#F7F5F0"),
             _p("Cover", "box", (pw / 1000, 0.0005, ph / 1000), (0, -0.0015, fh / 2), GLASS, "glass",
                collision=False, thin_walled=True, bevel=0)]
    for p in parts:  # 背面（y = 0）が壁に付く
        p.center[1] -= fd / 2
    return Product(slug="wall_poster", name="売り場のポスター（B2・アルミフレーム）", shape_class="assembly",
                   category=ENV, dims=Dimensions(fh, fw, depth=fd + 0.002), mass_kg=1.6, static=True,
                   material="aluminum",
                   description="形は売り場の壁に掛ける一般的なアルミのスナップフレーム（B2 のポスター 515 × 728 mm、"
                               "外寸 545 × 758 mm・厚さ 12 mm）と、透明な PET の保護シートで、寸法・質量は代表値。"
                               "背面を壁に付ける。ポスターのデザインは架空。",
                   tags=["ポスター", "販促", "POP", "フレーム", "内装", "poster", "poster frame", "promotional poster"],
                   photos=["karaage"], colors=Colors(label_base=red), images=[img], parts=parts,
                   picture_places=["convenience_store", "supermarket", "shop"])


def window_poster() -> Product:
    """店のガラスに外向きに貼るアルバイト募集のポスター（A1）。裏は白い紙。

    参考: https://commons.wikimedia.org/wiki/File:Poster_saying_%22No_masks%22_at_Japanese_supermarket_entrance.jpeg（CC0。貼り方の参考のみ）
    """
    pw, ph, t = 594.0, 841.0, 0.001
    orange, navy = "#EF6C00", "#1A237E"
    c = Canvas(pw, ph, None, WHITE, 6071)
    c.gradient(0, 0, pw, ph, "#FFFFFF", "#FFF3E0")
    c.rect(0, 0, pw, 190, fill=orange)
    c.text(pw / 2, 70, "STAFF WANTED", 34, "#FFE0B2", 900, spacing=6)
    c.text(pw / 2, 140, "アルバイト・パート募集", 58, WHITE, 900, max_w=550)
    rows = [("時給", "1,150円〜（22時〜翌5時 1,438円〜）"), ("時間", "6:00〜22:00 の間で 1日 3時間〜 OK"),
            ("日数", "週 2日〜 相談に応じます"), ("待遇", "制服貸与・交通費規定支給・社員登用あり")]
    y = 250
    for k, v in rows:
        c.rect(40, y - 32, 150, y + 32, fill=navy, radius=6)
        c.text(95, y, k, 30, WHITE, 900)
        c.text(370, y, v, 25, "#212121", 800, max_w=420)
        y += 92
    c.rect(40, 640, pw - 40, 760, fill="#FFE0B2", radius=12)
    c.text(pw / 2, 682, "未経験の方・学生・主婦（夫）の方 歓迎！", 30, "#BF360C", 900, max_w=500)
    c.text(pw / 2, 730, "お気軽にレジのスタッフまでお声がけください", 24, "#4E342E", 800, max_w=500)
    c.text(pw / 2, ph - 40, "店長", 22, "#616161", 700)
    img = _img(c, "paper", 6071, 0.3)
    back = Canvas(pw, ph, None, "#F7F5F0", 6072)
    back.gradient(0, 0, pw, ph, "#F8F6F1", "#EFECE5")
    for x in (0, pw - 30):  # 両面テープの跡
        back.rect(x + 8, 10, x + 22, 50, fill="#E6E1D6")
        back.rect(x + 8, ph - 50, x + 22, ph - 10, fill="#E6E1D6")
    bimg = _img(back, "paper", 6072, 0.4)
    parts = [_p("Sheet", "box", (pw / 1000, t, ph / 1000), (0, 0, ph / 2000), WHITE, "matte",
                faces={"front": 0, "back": 1}, material="paper", bevel=0, blank="#F7F5F0")]
    return Product(slug="window_poster", name="アルバイト募集のポスター（A1・窓貼り）", shape_class="assembly",
                   category=ENV, dims=Dimensions(ph / 1000, pw / 1000, depth=t), mass_kg=0.08, static=True,
                   material="paper",
                   description="形はコンビニの窓ガラスに外向きに貼る一般的な求人のポスター（A1、594 × 841 mm）で、寸法・質量は代表値。"
                               "正面（-Y）が外から見える面で、裏は白い紙。文字・時給などは架空。",
                   tags=["ポスター", "求人", "アルバイト募集", "窓", "掲示物", "内装", "poster", "help wanted poster",
                         "window poster", "job posting"],
                   colors=Colors(label_base=WHITE), images=[img, bimg], parts=parts,
                   picture_places=["shop", "convenience_store", "supermarket", "cafe", "restaurant"])


def _plate(slug, name, w_mm, h_mm, img, color, desc, tags, standoffs: bool = True, mass=0.4) -> Product:
    """壁に付ける表示板（背面 y = 0 を壁に付ける）。standoffs なら化粧ビスで少し浮かせる。"""
    t = 0.003
    gap = 0.008 if standoffs else 0.0
    parts = [_p("Plate", "box", (w_mm / 1000, t, h_mm / 1000), (0, -gap - t / 2, h_mm / 2000), color, "plastic",
                faces={"front": 0}, material="plexiglass" if standoffs else "aluminum", bevel=0.0008)]
    if standoffs:
        for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            x, z = sx * (w_mm / 2000 - 0.015), h_mm / 2000 + sz * (h_mm / 2000 - 0.015)
            parts += [_p(f"Standoff{k}", "cylinder", (0.012, 0.012, gap + t + 0.004), (x, -(gap + t + 0.004) / 2, z),
                         STAINLESS, "metal", rot=(90, 0, 0), collision=False, material="steel")]
    D = gap + t + (0.004 if standoffs else 0.0)
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(h_mm / 1000, w_mm / 1000, depth=D), mass_kg=mass, static=True,
                   material="plexiglass" if standoffs else "aluminum", description=desc, tags=tags,
                   colors=Colors(label_base=color), images=[img], parts=parts)


def business_hours_sign() -> Product:
    """入口の横に付ける営業時間の表示板（アクリル板を化粧ビスで浮かせる）。"""
    w, h = 300.0, 200.0
    green = "#2E7D32"
    c = Canvas(w, h, None, WHITE, 6081)
    c.gradient(0, 0, w, h, "#FFFFFF", "#F1F4F1")
    c.rect(0, 0, w, 46, fill=green)
    c.text(w / 2, 24, "営業時間  OPEN", 24, WHITE, 900)
    c.text(w / 2, 92, "24時間営業", 44, "#1B1B1B", 900)
    c.text(w / 2, 130, "年中無休", 26, green, 900)
    c.text(w / 2, 162, "OPEN 24 HOURS / 365 DAYS", 14, "#555555", 800, spacing=2)
    c.text(w / 2, 186, "※お酒の販売は 20歳以上の方に限ります", 9, "#777777", 700)
    img = _img(c, "plastic", 6081, 0.3)
    return _plate("business_hours_sign", "営業時間の表示板（アクリル）", w, h, img, WHITE,
                  "形は店の入口の横に付ける一般的なアクリルの表示板（300 × 200 mm・厚さ 3 mm を化粧ビスで壁から 8 mm 浮かせる）"
                  "で、寸法・質量は代表値。背面を壁に付ける。文字は架空。",
                  ["営業時間", "表示板", "24時間営業", "サイン", "掲示物", "内装", "business hours sign",
                   "opening hours sign", "open 24 hours"])


def security_camera_sign() -> Product:
    """「防犯カメラ作動中」の表示板（黄色の地に黒の文字とカメラの絵）。アルミ複合板を壁に直に貼る。"""
    w, h = 300.0, 200.0
    yellow, black = "#FFD600", "#111111"
    c = Canvas(w, h, None, yellow, 6091)
    c.gradient(0, 0, w, h, "#FFE033", "#F7CB00")
    for k in range(13):  # 上下の黒黄の帯
        x = k * 25
        c.polygon([(x, 0), (x + 12, 0), (x + 4, 14), (x - 8, 14)], fill=black)
        c.polygon([(x, h - 14), (x + 12, h - 14), (x + 4, h), (x - 8, h)], fill=black)
    # カメラの絵
    c.polygon([(40, 56), (118, 44), (124, 78), (46, 90)], fill=black)
    c.polygon([(118, 52), (140, 46), (142, 74), (122, 76)], fill=black)
    c.line([(76, 86), (82, 112)], black, 6)
    c.rect(62, 110, 104, 118, fill=black)
    c.ellipse(126, 54, 138, 66, fill=yellow)
    c.text(222, 62, "防犯カメラ", 34, black, 900, max_w=150)
    c.text(222, 104, "作動中", 38, black, 900)
    c.text(w / 2, 148, "SECURITY CAMERA IN OPERATION", 13, black, 800, spacing=1)
    c.text(w / 2, 170, "店内の様子は録画しています", 12, black, 800)
    img = _img(c, "plastic", 6091, 0.3)
    return _plate("security_camera_sign", "「防犯カメラ作動中」の表示板", w, h, img, yellow,
                  "形は店内の壁や入口に付ける一般的な防犯カメラの表示板（アルミ複合板 300 × 200 mm・厚さ 3 mm）で、"
                  "寸法・質量は代表値。背面を壁に付ける。文字と絵は架空のデザイン。",
                  ["防犯カメラ作動中", "防犯", "表示板", "サイン", "掲示物", "内装", "security camera sign", "CCTV sign",
                   "warning sign"], standoffs=False, mass=0.3)


# ---------------------------------------------------------------- 入口・窓


def _glass_leaf(prefix: str, x: float, y: float, w: float, h: float, z0: float, stile: float = 0.045,
                rail_b: float = 0.10) -> list[Part]:
    """アルミの框（かまち）の付いたガラスの戸（中心 x、下端 z0）。"""
    zc = z0 + h / 2
    return [_p(f"{prefix}Glass", "box", (w - 2 * stile + 0.01, 0.008, h - stile - rail_b + 0.01), (x, y, z0 + rail_b + (h - stile - rail_b) / 2),
               GLASS, "glass", material="glass", bevel=0),
            _p(f"{prefix}StileL", "box", (stile, 0.040, h), (x - w / 2 + stile / 2, y, zc), ALU, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}StileR", "box", (stile, 0.040, h), (x + w / 2 - stile / 2, y, zc), ALU, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}RailT", "box", (w - 2 * stile, 0.040, stile), (x, y, z0 + h - stile / 2), ALU, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}RailB", "box", (w - 2 * stile, 0.040, rail_b), (x, y, z0 + rail_b / 2), ALU, "metal",
               material="aluminum", bevel=0.002)]


def automatic_door() -> Product:
    """両引きの自動ドア（引き戸 2 枚と左右のはめ殺し）。上の無目（むめ）に駆動部とセンサー。引き戸はスライドの関節。

    参考: https://commons.wikimedia.org/wiki/File:7-Eleven_JR_Kyobashi_station%27s_western_entrance_store.JPG（CC0。形の参考のみ）、
    https://commons.wikimedia.org/wiki/File:K-FamilyMart_Kintetsu_Nagoya_station_No.4_platform_north_store.JPG（CC0。形の参考のみ）
    """
    W, H, D = 3.2, 2.4, 0.16
    door_h, head_h, sill = 2.08, 0.30, 0.012
    leaf_w = 0.82
    fix_w = (W - 0.10 - 2 * (leaf_w - 0.02)) / 2  # はめ殺しの幅（引き戸と 20 mm 重ねる）
    c = Canvas(300, 90, None, WHITE, 6101)  # 引き戸のステッカー
    c.gradient(0, 0, 300, 90, "#FFFFFF", "#D5E0EC")
    c.rect(3, 3, 297, 87, outline="#1565C0", width=2, radius=8)
    c.text(150, 38, "自動ドア", 38, "#1565C0", 900)
    c.text(150, 72, "AUTOMATIC DOOR", 17, "#1565C0", 800, spacing=3)
    sticker = _img(c, "film", 6101, 0.3)
    yf, yl = 0.030, -0.025  # はめ殺し（奥）と引き戸（手前）の面
    parts = [_p("JambL", "box", (0.05, D, H), (-W / 2 + 0.025, 0, H / 2), ALU_DARK, "metal", material="aluminum"),
             _p("JambR", "box", (0.05, D, H), (W / 2 - 0.025, 0, H / 2), ALU_DARK, "metal", material="aluminum"),
             _p("Header", "box", (W - 0.10, D, head_h), (0, 0, door_h + head_h / 2 + sill), ALU_DARK, "metal",
                material="aluminum", bevel=0.003),
             _p("Sill", "box", (W - 0.10, D, sill), (0, 0, sill / 2), STAINLESS, "metal", material="steel", bevel=0.001),
             _p("Sensor", "box", (0.26, 0.07, 0.045), (0, -D / 2 - 0.035, door_h + sill + 0.05), "#2A2C30", "plastic",
                collision=False, bevel=0.006),
             _p("SensorWindow", "box", (0.20, 0.05, 0.004), (0, -D / 2 - 0.035, door_h + sill + 0.026), "#5A1A22",
                "glossy", collision=False, bevel=0)]
    for k, sx in enumerate((-1, 1)):
        x = sx * (W / 2 - 0.05 - fix_w / 2)
        parts += _glass_leaf(f"Fixed{k}", x, yf, fix_w, door_h, sill)
    joints = []
    for k, sx in enumerate((-1, 1)):
        x = sx * leaf_w / 2
        pre = f"Leaf{k}"
        leaf = _glass_leaf(pre, x, yl, leaf_w, door_h, sill)
        leaf += [_p(f"{pre}Sticker", "box", (0.30, 0.0006, 0.09), (x, yl - 0.0043, 1.10), WHITE, "matte",
                    faces={"front": 0}, collision=False, bevel=0),
                 _p(f"{pre}Edge", "box", (0.012, 0.044, door_h - 0.02), (x - sx * (leaf_w / 2 - 0.006), yl, sill + door_h / 2),
                    "#222222", "matte", collision=False, material="rubber", bevel=0)]
        for p in leaf:
            p.link = f"{pre}Link"
        parts += leaf
        # 引き戸は X 方向にスライドして、左の戸は左へ・右の戸は右へ開く
        stroke = leaf_w - 0.04
        joints.append(Joint(link=f"{pre}Link", anchor=[x, yl, sill + door_h / 2], type="prismatic", axis="X",
                            limits=[-stroke, 0.0] if sx < 0 else [0.0, stroke]))
    return Product(slug="automatic_door", name="自動ドア（両引き・はめ殺し付き）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D + 0.07), mass_kg=220.0, static=True, material="aluminum",
                   description="形はコンビニの入口に多い両引きの自動ドア（引き戸 2 枚 820 × 2080 mm と左右のはめ殺し、"
                               "幅 3.2 m・高さ 2.4 m、上の無目に駆動部とセンサー）で、寸法・質量は代表値。"
                               "引き戸（Leaf0Link・Leaf1Link）は X 方向のスライドの関節で、左右へ 780 mm まで開く。ステッカーは架空。",
                   tags=["自動ドア", "入口", "ドア", "引き戸", "建具", "内装", "automatic door", "sliding door",
                         "store entrance"],
                   colors=Colors(label_base=ALU_DARK), images=[sticker], parts=parts, joints=joints)


def glass_facade() -> Product:
    """店の正面のはめ殺しの窓（アルミのサッシ、上に欄間）。並べて正面のガラス面にする。

    参考: https://commons.wikimedia.org/wiki/File:K-FamilyMart_Kintetsu_Nagoya_station_No.4_platform_south_store.JPG（CC0。形の参考のみ）
    """
    W, H, D = 1.8, 2.7, 0.07
    f, tr = 0.05, 2.30  # 枠の見付け・無目（欄間の下端）の高さ
    parts = [_p("JambL", "box", (f / 2, D, H), (-W / 2 + f / 4, 0, H / 2), ALU_DARK, "metal", material="aluminum"),
             _p("JambR", "box", (f / 2, D, H), (W / 2 - f / 4, 0, H / 2), ALU_DARK, "metal", material="aluminum"),
             _p("Head", "box", (W - f, D, f), (0, 0, H - f / 2), ALU_DARK, "metal", material="aluminum"),
             _p("Sill", "box", (W - f, D, 0.08), (0, 0, 0.04), ALU_DARK, "metal", material="aluminum"),
             _p("Transom", "box", (W - f, D, f), (0, 0, tr + f / 2), ALU_DARK, "metal", material="aluminum"),
             _p("GlassLower", "box", (W - f + 0.01, 0.010, tr - 0.08 + 0.01), (0, 0, 0.08 + (tr - 0.08) / 2), GLASS,
                "glass", material="glass", bevel=0),
             _p("GlassUpper", "box", (W - f + 0.01, 0.010, H - tr - 2 * f + 0.01), (0, 0, tr + f + (H - tr - 2 * f) / 2),
                GLASS, "glass", material="glass", bevel=0)]
    for k in range(2):  # ガラス押さえのゴム（内外）
        y = (-1) ** k * 0.008
        parts += [_p(f"Gasket{k}", "box", (W - f, 0.004, 0.006), (0, y, 0.083), "#1E1E1E", "matte", collision=False,
                     material="rubber", bevel=0)]
    return Product(slug="glass_facade", name="店の正面のはめ殺し窓（欄間付き）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D), mass_kg=95.0, static=True, material="aluminum",
                   description="形はコンビニの正面のガラス面（アルミのサッシ・幅 1.8 m・高さ 2.7 m、高さ 2.3 m の無目の上に欄間）"
                               "で、寸法・質量は代表値。左右の縦枠は半分の見付けで、横に並べるとつながる。",
                   tags=["窓", "ガラス", "はめ殺し窓", "ファサード", "サッシ", "建具", "内装", "window", "storefront",
                         "glass facade", "shop window"],
                   colors=Colors(label_base=ALU_DARK), images=[], parts=parts)


# ---------------------------------------------------------------- ドア（開き戸）


def _frame(W: float, H: float, D: float, color: str, f: float = 0.045) -> list[Part]:
    """開き戸の枠（縦枠 2 本と上枠）。W・H は外寸。"""
    return [_p("FrameL", "box", (f, D, H), (-W / 2 + f / 2, 0, H / 2), color, "plastic", bevel=0.002),
            _p("FrameR", "box", (f, D, H), (W / 2 - f / 2, 0, H / 2), color, "plastic", bevel=0.002),
            _p("FrameT", "box", (W - 2 * f, D, f), (0, 0, H - f / 2), color, "plastic", bevel=0.002)]


def _lever(prefix: str, x: float, y_face: float, z: float, side: int, color: str = STAINLESS) -> list[Part]:
    """レバーハンドル（座と握り）。y_face は戸の面、side は -1 で手前（-Y）、+1 で奥。握りは戸の中央へ向ける。"""
    s = side
    return [_p(f"{prefix}Rose", "cylinder", (0.055, 0.055, 0.010), (x, y_face + s * 0.005, z), color, "metal",
               rot=(90, 0, 0), collision=False, material="steel"),
            _p(f"{prefix}Neck", "cylinder", (0.018, 0.018, 0.050), (x, y_face + s * 0.035, z), color, "metal",
               rot=(90, 0, 0), collision=False, material="steel"),
            _p(f"{prefix}Grip", "box", (0.12, 0.020, 0.018), (x - math.copysign(0.05, x) * 0 + (-0.05 if x > 0 else 0.05),
                                                           y_face + s * 0.058, z), color, "metal",
               collision=False, material="steel", bevel=0.006)]


def _pictogram_plate(seed: int) -> np.ndarray:
    """トイレの扉の絵記号の板（男女と車いす）。"""
    c = Canvas(180, 180, None, WHITE, seed)
    c.gradient(0, 0, 180, 180, "#FFFFFF", "#D3DADF")
    blue, red, ink = "#1565C0", "#C62828", "#263238"
    # 男性
    c.ellipse(30, 22, 52, 44, fill=blue)
    c.rect(26, 48, 56, 94, fill=blue, radius=5)
    c.rect(30, 92, 40, 128, fill=blue)
    c.rect(42, 92, 52, 128, fill=blue)
    # 女性
    c.ellipse(80, 22, 102, 44, fill=red)
    c.polygon([(91, 48), (110, 100), (72, 100)], fill=red)
    c.rect(80, 98, 88, 128, fill=red)
    c.rect(94, 98, 102, 128, fill=red)
    # 車いす
    c.ellipse(132, 22, 150, 40, fill=ink)
    c.line([(140, 46), (140, 82), (160, 82), (166, 104)], ink, 7)
    c.ellipse(118, 76, 158, 116, outline=ink, width=5)
    c.line([(60, 18), (60, 132)], "#B0BEC5", 1.5)
    c.line([(116, 18), (116, 132)], "#B0BEC5", 1.5)
    c.text(90, 150, "トイレ", 20, ink, 900)
    c.text(90, 170, "RESTROOM", 11, "#546E7A", 800, spacing=2)
    return _img(c, "plastic", seed, 0.3)


def toilet_door() -> Product:
    """トイレの開き戸（木目の化粧板、レバーハンドルと表示錠、絵記号の板）。左の蝶番で奥へ開く。

    参考: https://commons.wikimedia.org/wiki/File:The_toilets_in_Morinomiya_station.jpg（CC0。形の参考のみ）
    """
    W, H, D = 0.90, 2.08, 0.12
    lw, lh, lt = 0.80, 2.00, 0.036
    wood = "#D9C4A0"
    c = Canvas(800, 2000, None, wood, 6111)  # 木目
    c.gradient(0, 0, 800, 2000, "#E3D0AE", "#C9AF86")
    for _ in range(140):
        x = c.rng.uniform(0, 800)
        amp, ph = c.rng.uniform(2, 9), c.rng.uniform(0, 6.28)
        pts = [(x + amp * math.sin(y / 180 + ph), y) for y in range(0, 2001, 40)]
        c.line(pts, c.rng.choice(["#C7AE84", "#CDB58C", "#E2D0B0"]), c.rng.uniform(0.8, 2.4))
    wood_img = _img(c, "paper", 6111, 0.3)
    ind = Canvas(60, 24, None, "#1E88E5", 6112)  # 表示錠の窓（空き）
    ind.gradient(0, 0, 60, 24, "#2196F3", "#1565C0")
    ind.text(30, 12.5, "空き", 13, WHITE, 900)
    ind_img = _img(ind, "plastic", 6112, 0.2)
    plate = _pictogram_plate(6113)
    x0, z0 = -lw / 2, 0.01  # 戸の左端（蝶番）・下端
    hx = x0 + lw - 0.07  # ハンドルの位置
    parts = _frame(W, H, D, "#E9E4DA")
    leaf = [_p("LeafPanel", "box", (lw, lt, lh), (0, 0, z0 + lh / 2), wood, "matte", faces={"front": 0, "back": 0},
               material="wood", bevel=0.002),
            _p("LeafPlate", "box", (0.18, 0.003, 0.18), (0, -lt / 2 - 0.0015, 1.50), WHITE, "plastic",
               faces={"front": 2}, collision=False, bevel=0.001),
            _p("LeafIndicator", "box", (0.07, 0.008, 0.032), (hx, -lt / 2 - 0.004, 1.05 + 0.10), STAINLESS, "metal",
               collision=False, material="steel", bevel=0.002),
            _p("LeafIndicatorWin", "box", (0.06, 0.002, 0.024), (hx, -lt / 2 - 0.0085, 1.05 + 0.10), "#1E88E5",
               "plastic", faces={"front": 1}, collision=False, bevel=0)]
    leaf += _lever("LeafLeverF", hx, -lt / 2, 0.95, -1) + _lever("LeafLeverB", hx, lt / 2, 0.95, 1)
    for k in range(3):  # 蝶番
        leaf.append(_p(f"LeafHinge{k}", "cylinder", (0.014, 0.014, 0.10), (x0 - 0.002, lt / 2 - 0.004, 0.25 + k * 0.75),
                       STAINLESS, "metal", collision=False, material="steel"))
    _link(leaf, "Leaf", "LeafLink")
    parts += leaf
    return Product(slug="toilet_door", name="トイレのドア（絵記号・表示錠付き）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=lt + 0.136), mass_kg=32.0, static=True, material="wood",
                   description="形は店舗のトイレの一般的な木目の開き戸（戸 800 × 2000 mm・厚さ 36 mm、枠の外寸 900 × 2080 mm、"
                               "レバーハンドル・表示錠・絵記号の板）で、寸法・質量は代表値。戸（LeafLink）は左の蝶番で奥（+Y）へ "
                               "90° まで開く。絵記号は簡単に描いたもの。",
                   tags=["ドア", "トイレ", "トイレのドア", "開き戸", "建具", "内装", "door", "restroom door",
                         "toilet door", "hinged door"],
                   colors=Colors(label_base=wood), images=[wood_img, ind_img, plate], parts=parts,
                   joints=[Joint(link="LeafLink", anchor=[x0, lt / 2, z0 + lh / 2], limits=[0.0, 90.0])])


def backyard_swing_door() -> Product:
    """売り場とバックヤードの間の両開きのスイングドア（片開き 1 枚、縦長の窓・けり板・押し板）。

    参考: https://commons.wikimedia.org/wiki/File:LAWSON-FushimiMinami.JPG（PD。奥の扉の参考）
    """
    W, H, D = 0.95, 2.0, 0.10
    lw, lh, lt = 0.85, 1.93, 0.040
    gray = "#8F969D"
    z0 = 0.015
    win_w, win_h, win_z = 0.24, 0.42, 1.25  # 窓の幅・高さ・下端
    side = (lw - win_w) / 2
    x0 = -lw / 2
    c = Canvas(160, 60, None, WHITE, 6121)
    c.gradient(0, 0, 160, 60, "#FFFFFF", "#D3D8DD")
    c.text(80, 24, "押す  PUSH", 20, "#263238", 900)
    c.text(80, 46, "扉の向こうに注意", 11, "#C62828", 800)
    push = _img(c, "film", 6121, 0.3)
    leaf = [_p("LeafBottom", "box", (lw, lt, win_z - z0), (0, 0, z0 + (win_z - z0) / 2), gray, "plastic",
               material="fiberglass", bevel=0.003),
            _p("LeafTop", "box", (lw, lt, z0 + lh - win_z - win_h), (0, 0, (win_z + win_h + z0 + lh) / 2), gray,
               "plastic", material="fiberglass", bevel=0.003),
            _p("LeafSideL", "box", (side, lt, win_h), (x0 + side / 2, 0, win_z + win_h / 2), gray, "plastic",
               material="fiberglass", bevel=0),
            _p("LeafSideR", "box", (side, lt, win_h), (-x0 - side / 2, 0, win_z + win_h / 2), gray, "plastic",
               material="fiberglass", bevel=0),
            _p("LeafWindow", "box", (win_w + 0.01, 0.006, win_h + 0.01), (0, 0, win_z + win_h / 2), GLASS, "glass",
               material="plexiglass", bevel=0)]
    for s, nm in ((-1, "F"), (1, "B")):
        y = s * (lt / 2 + 0.0015)
        leaf += [_p(f"LeafKick{nm}", "box", (lw - 0.02, 0.003, 0.30), (0, y, z0 + 0.16), STAINLESS, "metal",
                    collision=False, material="steel", bevel=0.001),
                 _p(f"LeafPush{nm}", "box", (0.10, 0.003, 0.30), (-x0 - 0.10, y, 1.05), STAINLESS, "metal",
                    collision=False, material="steel", bevel=0.001),
                 _p(f"LeafLabel{nm}", "box", (0.16, 0.0006, 0.06), (-x0 - 0.10, y + s * 0.0018, 1.27), WHITE, "matte",
                    faces={"front" if s < 0 else "back": 0}, collision=False, bevel=0)]
        for k, (gx, gz, gw, gh) in enumerate(((0, win_z - 0.012, win_w + 0.024, 0.024),
                                              (0, win_z + win_h + 0.012, win_w + 0.024, 0.024),
                                              (-win_w / 2 - 0.012, win_z + win_h / 2, 0.024, win_h),
                                              (win_w / 2 + 0.012, win_z + win_h / 2, 0.024, win_h))):
            leaf.append(_p(f"LeafGasket{nm}{k}", "box", (gw, 0.006, gh), (gx, s * (lt / 2 + 0.002), gz), "#1E1E1E",
                           "matte", collision=False, material="rubber", bevel=0.002))
    _link(leaf, "Leaf", "LeafLink")
    parts = _frame(W, H + 0.04, D, "#6E757C") + leaf
    return Product(slug="backyard_swing_door", name="バックヤードのスイングドア（窓付き）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H + 0.04, W, depth=D), mass_kg=28.0, static=True,
                   material="fiberglass",
                   description="形は売り場とバックヤードの間に付ける一般的な FRP のスイングドア（戸 850 × 1930 mm・厚さ 40 mm、"
                               "縦長の窓・ステンレスのけり板と押し板）で、寸法・質量は代表値。戸（LeafLink）は左の蝶番で"
                               "手前にも奥にも 90° まで開く（台車で押して通る）。表示は架空。",
                   tags=["ドア", "スイングドア", "バックヤード", "従業員通路", "建具", "内装", "swing door",
                         "double acting door", "backroom door", "stockroom door"],
                   colors=Colors(label_base=gray), images=[push], parts=parts,
                   joints=[Joint(link="LeafLink", anchor=[x0, 0.0, z0 + lh / 2], limits=[-90.0, 90.0])])


def staff_office_door() -> Product:
    """事務所（従業員用）の鋼製の開き戸。「STAFF ONLY」の表示とドアクローザー。右の蝶番で奥へ開く。"""
    W, H, D = 0.90, 2.08, 0.12
    lw, lh, lt = 0.80, 2.00, 0.040
    beige = "#CFCAC0"
    z0 = 0.01
    x_hinge = lw / 2
    c = Canvas(260, 110, None, "#263238", 6131)
    c.gradient(0, 0, 260, 110, "#3A4A53", "#151D21")
    c.rect(4, 4, 256, 106, outline="#FFC107", width=2, radius=6)
    c.text(130, 40, "STAFF ONLY", 34, "#FFC107", 900, spacing=2)
    c.text(130, 80, "関係者以外立入禁止", 24, WHITE, 900)
    sign = _img(c, "plastic", 6131, 0.3)
    c2 = Canvas(140, 50, None, WHITE, 6132)
    c2.gradient(0, 0, 140, 50, "#FFFFFF", "#D3DADF")
    c2.text(70, 20, "事務所", 20, "#263238", 900)
    c2.text(70, 40, "OFFICE", 11, "#607D8B", 800, spacing=3)
    room = _img(c2, "plastic", 6132, 0.3)
    hx = -lw / 2 + 0.07
    leaf = [_p("LeafPanel", "box", (lw, lt, lh), (0, 0, z0 + lh / 2), beige, "plastic", material="steel", bevel=0.003),
            _p("LeafSign", "box", (0.26, 0.002, 0.11), (0, -lt / 2 - 0.001, 1.55), "#263238", "plastic",
               faces={"front": 0}, collision=False, bevel=0.0005),
            _p("LeafRoom", "box", (0.14, 0.002, 0.05), (0, -lt / 2 - 0.001, 1.40), WHITE, "plastic",
               faces={"front": 1}, collision=False, bevel=0.0005),
            _p("LeafCylinder", "cylinder", (0.03, 0.03, 0.006), (hx, -lt / 2 - 0.003, 1.08), STAINLESS, "metal",
               rot=(90, 0, 0), collision=False, material="steel"),
            _p("LeafCloserBody", "box", (0.26, 0.05, 0.06), (x_hinge - 0.20, lt / 2 + 0.025, z0 + lh - 0.06), "#B0B3B6",
               "metal", collision=False, material="aluminum", bevel=0.01)]
    leaf += _lever("LeafLeverF", hx, -lt / 2, 0.95, -1) + _lever("LeafLeverB", hx, lt / 2, 0.95, 1)
    for k in range(3):
        leaf.append(_p(f"LeafHinge{k}", "cylinder", (0.014, 0.014, 0.10), (x_hinge + 0.002, lt / 2 - 0.004, 0.25 + k * 0.75),
                       STAINLESS, "metal", collision=False, material="steel"))
    _link(leaf, "Leaf", "LeafLink")
    parts = _frame(W, H, D, "#B9B4AA") + leaf
    parts.append(_p("CloserArm", "box", (0.22, 0.016, 0.012), (x_hinge - 0.12, D / 2 + 0.008, H - 0.06), "#9EA2A6", "metal",
                    collision=False, material="aluminum", bevel=0.003))
    return Product(slug="staff_office_door", name="事務所のドア（STAFF ONLY・ドアクローザー付き）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=lt + 0.136), mass_kg=45.0, static=True, material="steel",
                   description="形は店舗の事務所・従業員エリアの一般的な鋼製の開き戸（戸 800 × 2000 mm・厚さ 40 mm、"
                               "枠の外寸 900 × 2080 mm、レバーハンドル・シリンダー錠・奥側のドアクローザー）で、寸法・質量は代表値。"
                               "戸（LeafLink）は右の蝶番で奥（+Y）へ 90° まで開く。表示は架空。",
                   tags=["ドア", "事務所", "STAFF ONLY", "関係者以外立入禁止", "従業員エリア", "開き戸", "建具", "内装",
                         "door", "staff only door", "office door", "steel door"],
                   colors=Colors(label_base=beige), images=[sign, room], parts=parts,
                   joints=[Joint(link="LeafLink", anchor=[x_hinge, lt / 2, z0 + lh / 2], limits=[-90.0, 0.0])])


# ---------------------------------------------------------------- トイレの中


def toilet_bowl() -> Product:
    """手洗い付きタンクの洋式便器と温水洗浄便座。便ふたは後ろの蝶番で上へ開く。背面を壁に付ける。

    参考: https://commons.wikimedia.org/wiki/File:Flush_toilet.jpg（CC0）、
    https://commons.wikimedia.org/wiki/File:Multi-Function_Toilet,_at_Google_Japan_office_.jpg（CC0）
    """
    D = 0.76
    yb = -D / 2 + 0.23  # 便器の鉢の中心
    rim = 0.40  # 鉢の上端
    c = Canvas(30, 150, None, "#ECEFF1", 6141)  # 便座の横の操作部
    c.gradient(0, 0, 30, 150, "#F7F9FA", "#D0D6DA")
    for k, (t, col) in enumerate((("止", "#E53935"), ("おしり", "#1E88E5"), ("ビデ", "#EC407A"), ("乾燥", "#43A047"))):
        y = 20 + k * 34
        c.ellipse(5, y - 11, 25, y + 9, fill=col)
        c.text(15, y - 1, t, 5.5 if len(t) > 1 else 9, WHITE, 900)
    panel = _img(c, "plastic", 6141, 0.3)
    ceramic = "ceramic"
    parts = [
        _p("Pedestal", "revolve", (0.25, 0.36, rim - 0.06), (0, yb + 0.05, (rim - 0.06) / 2), PORCELAIN, "glossy",
           profile=[[0, 0], [0.92, 0], [0.80, 0.25], [0.78, 0.6], [0.95, 0.9], [1.0, 1.0], [0, 1.0]], material=ceramic),
        # 鉢の後ろから壁までの胴（便座の後ろとタンクを載せる）
        _p("RearBody", "box", (0.34, D / 2 - yb - 0.12, 0.16), (0, (yb + 0.12 + D / 2) / 2, rim - 0.08), PORCELAIN,
           "glossy", bevel=0.04, material=ceramic),
        _p("RearFoot", "box", (0.24, D / 2 - yb - 0.10, rim - 0.16), (0, (yb + 0.10 + D / 2) / 2, (rim - 0.16) / 2),
           PORCELAIN, "glossy", bevel=0.03, material=ceramic),
        _p("Bowl", "revolve", (0.36, 0.46, 0.12), (0, yb, rim - 0.06), PORCELAIN, "glossy",
           profile=[[0, 0], [0.75, 0], [0.97, 0.80], [1.0, 1.0], [0.88, 1.0], [0.62, 0.55], [0.28, 0.22], [0, 0.18]],
           material=ceramic),
        _p("Water", "cylinder", (0.13, 0.15, 0.002), (0, yb + 0.03, rim - 0.12 + 0.027), "#C9DCE3", "glossy",
           collision=False, material="water"),
        _p("Seat", "torus", (0.37, 0.45, 0.022), (0, yb, rim + 0.011), "#F4F2EE", "plastic"),
        _p("WashletBody", "box", (0.40, 0.14, 0.075), (0, yb + 0.23 + 0.07 - 0.01, rim + 0.0375), "#F4F2EE", "plastic",
           bevel=0.025),
        _p("Nozzle", "box", (0.03, 0.04, 0.012), (0, yb + 0.20, rim + 0.004), "#DADCDD", "plastic", collision=False,
           bevel=0.004),
        _p("SidePanel", "box", (0.03, 0.15, 0.045), (0.215, yb + 0.03, rim + 0.025), "#ECEFF1", "plastic",
           faces={"top": 0}, collision=False, bevel=0.006),
        _p("Tank", "box", (0.40, 0.18, 0.36), (0, D / 2 - 0.09, rim + 0.02 + 0.18), PORCELAIN, "glossy", bevel=0.03,
           material=ceramic),
        _p("TankBasin", "revolve", (0.34, 0.16, 0.035), (0, D / 2 - 0.09, rim + 0.38 + 0.0175), PORCELAIN, "glossy",
           profile=[[0, 0], [0.92, 0], [1.0, 1.0], [0.88, 1.0], [0.45, 0.35], [0, 0.3]], material=ceramic),
        _p("Spout", "cylinder", (0.018, 0.018, 0.06), (0, D / 2 - 0.035, rim + 0.415 + 0.03), STAINLESS, "metal",
           collision=False, material="steel"),
        _p("SpoutNozzle", "cylinder", (0.016, 0.016, 0.06), (0, D / 2 - 0.06, rim + 0.44), STAINLESS, "metal",
           rot=(90, 0, 0), collision=False, material="steel"),
        _p("FlushLever", "box", (0.06, 0.014, 0.014), (-0.20, D / 2 - 0.17, rim + 0.30), STAINLESS, "metal",
           collision=False, material="steel", bevel=0.004),
        _p("SupplyPipe", "cylinder", (0.016, 0.016, 0.30), (-0.14, D / 2 - 0.02, 0.24), STAINLESS, "metal",
           collision=False, material="steel"),
    ]
    lid_y0 = yb + 0.23 - 0.005  # 便ふたの蝶番（鉢の後ろ）
    parts.append(_p("Lid", "bun", (0.37, 0.44, 0.032), (0, yb - 0.005, rim + 0.022 + 0.016), "#F4F2EE", "plastic",
                    link="LidLink"))
    H = rim + 0.44 + 0.012
    return Product(slug="toilet_bowl", name="洋式便器（手洗い付きタンク・温水洗浄便座）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, 0.45, depth=D), mass_kg=38.0, static=True, material="ceramic",
                   description="形は店舗のトイレの一般的な手洗い付きタンクの洋式便器と温水洗浄便座（幅 450 mm・奥行き 760 mm・"
                               "高さ 850 mm、便座の高さ 410 mm）で、寸法・質量は代表値。背面を壁に付ける。鉢と手洗いはくぼみまで作る。"
                               "便ふた（LidLink）は後ろの蝶番で上へ 105° まで開く。",
                   tags=["便器", "洋式便器", "トイレ", "温水洗浄便座", "タンク", "衛生陶器", "内装", "toilet",
                         "western toilet", "toilet bowl", "bidet toilet seat"],
                   colors=Colors(label_base=PORCELAIN), images=[panel], parts=parts,
                   joints=[Joint(link="LidLink", anchor=[0, lid_y0, rim + 0.022], axis="X", limits=[-105.0, 0.0])])


def hand_wash_basin() -> Product:
    """壁付けの手洗い器（陶器の鉢に自動水栓）。排水管は壁へ。背面を壁に付ける。原点は排水トラップの下端。

    参考: https://commons.wikimedia.org/wiki/File:Bathroom_sink_with_overflow_hole_circled.jpg（PD）、
    https://commons.wikimedia.org/wiki/File:The_toilets_in_Morinomiya_station.jpg（CC0）
    """
    W, D = 0.45, 0.36
    rim, bh = 0.76, 0.15
    yb = D / 2 - 0.04 - 0.16  # 鉢の中心
    ceramic = "ceramic"
    parts = [
        _p("Basin", "revolve", (W, 0.32, bh), (0, yb, rim - bh / 2), PORCELAIN, "glossy",
           profile=[[0, 0], [0.55, 0], [0.85, 0.45], [1.0, 0.95], [0.97, 1.0], [0.90, 1.0], [0.74, 0.55],
                    [0.34, 0.22], [0, 0.20]], material=ceramic),
        _p("Deck", "box", (0.40, 0.06, 0.05), (0, D / 2 - 0.03, rim - 0.025), PORCELAIN, "glossy", bevel=0.01,
           material=ceramic),
        _p("Drain", "cylinder", (0.035, 0.035, 0.003), (0, yb, rim - bh + 0.2 * bh + 0.0015), STAINLESS, "metal",
           collision=False, material="steel"),
        _p("FaucetBody", "cylinder", (0.040, 0.040, 0.10), (0, D / 2 - 0.03, rim + 0.05), STAINLESS, "metal",
           material="steel"),
        _p("FaucetSpout", "box", (0.032, 0.11, 0.024), (0, D / 2 - 0.085, rim + 0.088), STAINLESS, "metal",
           collision=False, material="steel", bevel=0.008),
        _p("Sensor", "box", (0.018, 0.010, 0.008), (0, D / 2 - 0.125, rim + 0.074), "#1E1E1E", "glossy",
           collision=False, bevel=0.002),
        _p("Trap", "cylinder", (0.032, 0.032, 0.18), (0, yb, rim - bh + 0.03 - 0.09), STAINLESS, "metal",
           collision=False, material="steel"),
        _p("TrapToWall", "cylinder", (0.032, 0.032, D / 2 - yb), (0, (yb + D / 2) / 2, rim - bh - 0.06), STAINLESS,
           "metal", rot=(90, 0, 0), collision=False, material="steel"),
        _p("WallFlange", "cylinder", (0.07, 0.07, 0.008), (0, D / 2 - 0.004, rim - bh - 0.06), STAINLESS, "metal",
           rot=(90, 0, 0), collision=False, material="steel"),
    ]
    H = 0.40  # 排水トラップの下端（鉢の上端の 300 mm 下）から水栓の上端まで
    return Product(slug="hand_wash_basin", name="壁付けの手洗い器（自動水栓）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D), mass_kg=14.0, static=True, material="ceramic",
                   description="形は店舗のトイレの一般的な壁付けの陶器の手洗い器（幅 450 mm・奥行き 320 mm、鉢の上端は床から 760 mm が標準）"
                               "に、自動水栓と排水のトラップを付けたもので、寸法・質量は代表値。原点は排水トラップの下端で、背面を壁に付ける"
                               "（床から 460 mm に置くと鉢の上端が 760 mm になる）。"
                               "鉢はくぼみまで作る。",
                   tags=["手洗い器", "洗面器", "洗面台", "自動水栓", "トイレ", "衛生陶器", "内装", "hand wash basin",
                         "wash basin", "sink", "lavatory"],
                   colors=Colors(label_base=PORCELAIN), images=[], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    floor_tile_panel, entrance_mat, wall_panel_baseboard, ceiling_panel, ceiling_base_light, downlight,
    emergency_exit_sign, aisle_sign_hanging, wall_poster, window_poster, business_hours_sign, security_camera_sign,
    automatic_door, glass_facade, toilet_door, backyard_swing_door, staff_office_door, toilet_bowl, hand_wash_basin,
)}
