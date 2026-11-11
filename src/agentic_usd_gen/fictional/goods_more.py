"""架空の商品のデザイン: コンビニの日用品（吊り下げ・袋入りの雑貨）と、レジまわりの小さな什器。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
参考にした写真は各関数の docstring に書く（Wikimedia Commons の CC0 / パブリックドメインのもののみ）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .conv_goods import BOX_FACES, _faces, _hang_hole
from .paint import Canvas, finish, mix, trim_safe
from .products import INK, _box, _cyl, _face, seal_crimp

WHITE = "#FFFFFF"
FILM = "#F2F6F8"  # 透明なブリスター・袋の色味


def _card_edges(c: Canvas, color: str, h: float = 2.0):
    """台紙の上下の帯（縁が単色だと切り抜かれるため、上下に色の帯を入れる）。"""
    c.rect(0, 0, c.w_mm, h, fill=color)
    c.rect(0, c.h_mm - h, c.w_mm, c.h_mm, fill=color)


def _tilt(center, pivot, deg: float) -> list[float]:
    """pivot を通る X 軸まわりに deg [度] 回した点（部品の rotation [deg, 0, 0] と同じ向き。負で上が奥へ倒れる）。"""
    a = math.radians(deg)
    y, z = center[1] - pivot[1], center[2] - pivot[2]
    return [center[0], pivot[1] + y * math.cos(a) - z * math.sin(a), pivot[2] + y * math.sin(a) + z * math.cos(a)]


def _pse(c: Canvas, cx: float, cy: float, s: float, color: str = INK):
    """電気用品の表示（ひし形の枠に PSE。簡略形）。"""
    c.polygon([(cx, cy - s * 0.5), (cx + s * 0.62, cy), (cx, cy + s * 0.5), (cx - s * 0.62, cy)], outline=color)
    c.polygon([(cx, cy - s * 0.42), (cx + s * 0.52, cy), (cx, cy + s * 0.42), (cx - s * 0.52, cy)], outline=color)
    c.text(cx, cy, "PSE", s * 0.3, color, 800)


def _mat(parts: list[Part], prefixes: tuple[str, ...], material: str) -> list[Part]:
    """名前が prefixes で始まる部品の素材（意味ラベル）を決める。"""
    for p in parts:
        if p.name.startswith(prefixes):
            p.material = material
    return parts


# ---------------------------------------------------------------- モバイルバッテリー


def mobile_battery_blister() -> Product:
    """台紙とブリスターに入ったモバイルバッテリー（5000mAh の薄型）。

    参考: https://commons.wikimedia.org/wiki/File:Itel_power_bank_Nigeria.jpg（CC0）
    """
    CW, CH = 100.0, 180.0
    navy, orange, white = "#14213D", "#F28C28", WHITE
    c = Canvas(CW, CH, 10, navy, seed=7101)
    c.gradient(0, 0, CW, CH, "#24365E", "#0B1222")
    _hang_hole(c, CW / 2, 5, "#060A14")
    c.rect(0, 13, CW, 36, fill=orange)
    c.text(CW / 2, 21, "モバイルバッテリー", 8.2, navy, 900, max_w=CW - 8)
    c.text(CW / 2, 31, "5000mAh  薄型・軽量", 5.0, navy, 800)
    c.rect(6, 148, CW - 6, 158, fill=orange, radius=3)
    c.text(CW / 2, 153, "スマホ約 1 回分  USB-C 入出力", 4.2, navy, 900, max_w=CW - 16)
    c.text(CW / 2, 163, "残量ランプ  PSE 適合品", 4.0, white, 700)
    c.rect(6, 168, CW - 6, 176, fill="#2A3550", radius=2)
    c.text(CW / 2, 172, "1年保証  架空の電源", 3.4, mix(white, orange, 0.3), 700)
    _card_edges(c, orange)
    front = _face(c.array(), "film", 7101, 0.6)
    b = Canvas(CW, CH, 10, white, seed=7102)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF1F6")
    _card_edges(b, navy)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 15, CW, 25, fill=navy)
    b.text(CW / 2, 20, "MOBILE BATTERY 5000mAh", 4.2, white, 800, spacing=0.3)
    yb = b.table(6, 30, CW - 6, "", [("品名", "リチウムイオン蓄電池"), ("定格容量", "5000mAh / 3.7V（18.5Wh）"),
                                    ("入力", "USB-C  5V 2A"), ("出力", "USB-C  5V 2.4A"),
                                    ("大きさ", "約 64 × 100 × 13 mm"), ("質量", "約 115g")], 3.3)
    b.paragraph(6, yb + 3, CW - 6, "【ご注意】高温になる場所に置かないでください。落としたり強い衝撃を与えたりしないでください。"
                "膨らみ・発熱・異臭があるときはすぐに使用をやめてください。"
                "飛行機には預け入れ荷物に入れず、機内に持ち込んでください。\n" + NOTICE, 2.9, INK, 400)
    b.barcode(8, 148, 42, 22)
    _pse(b, 63, 160, 12)
    b.recycle(78, 158, 7, "紙", navy, sub="台紙")
    b.recycle(91, 158, 7, "プラ", navy, sub="ケース")
    back = _face(b.array(), "paper", 7102, 0.6)
    k = Canvas(64.0, 100.0, 16, "#1C1F26", seed=7103)  # 本体の正面
    k.gradient(0, 0, 64, 100, "#30353F", "#15181E")
    k.text(32, 40, "5000mAh", 6.4, "#D8DCE2", 800, spacing=0.3)
    k.text(32, 49, "POWER BANK", 3.0, "#8C939E", 700, spacing=0.6)
    for i in range(4):  # 残量ランプ
        x = 23.5 + i * 5.5
        k.ellipse(x - 0.9, 84.1, x + 0.9, 85.9, fill="#3FB6FF" if i < 3 else "#3A4250")
    k.rect(1.5, 1.5, 62.5, 98.5, outline="#454B57", width=0.5, radius=5)
    body = _face(k.array(), "film", 7103, 0.3)
    graphite = "#23262D"
    parts = [_box("Card", (0.10, 0.0012, 0.18), (0, 0, 0.09), navy, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.074, 0.018, 0.108), (0, -0.0096, 0.088), FILM, "glass", thin_walled=True, collision=False),
             _box("Battery", (0.064, 0.013, 0.100), (0, -0.0071, 0.084), graphite, "plastic", {"front": 2}),
             _box("PortC", (0.009, 0.0035, 0.002), (0, -0.0071, 0.1345), "#0C0D10", "matte", collision=False)]
    _mat(parts, ("Card",), "paper")
    return Product(slug="mobile_battery_blister", name="モバイルバッテリー 5000mAh", shape_class="assembly",
                   category="household", dims=Dimensions(0.18, 0.10, depth=0.0192), mass_kg=0.15, material="plastic",
                   description="形は一般的な台紙とブリスターに入った薄型のモバイルバッテリー（台紙 100 × 180 mm、本体 64 × 100 × 13 mm、5000mAh）で、寸法・質量は代表値。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["モバイルバッテリー", "充電器", "スマホ用品", "ブリスター", "mobile battery", "power bank",
                         "power bank blister pack"],
                   photos=[], colors=Colors(label_base=navy), images=[front, back, body], parts=parts)


# ---------------------------------------------------------------- 使い捨てカミソリ


def _razor(prefix: str, x: float, y: float, z_head: float, up: bool, handle: str, head: str) -> list[Part]:
    """使い捨てカミソリ 1 本（台紙に沿って立てた向き）。up なら刃が上。z_head は刃の中心の高さ。"""
    s = 1 if up else -1
    hl = 0.098  # 柄の長さ
    zh = z_head - s * (0.006 + hl / 2)
    return [_box(f"{prefix}Handle", (0.0095, 0.0050, hl), (x, y, zh), handle, "plastic"),
            _box(f"{prefix}Grip", (0.0105, 0.0054, 0.028), (x, y, zh - s * 0.030), mix(handle, "#000000", 0.25),
                 "matte", collision=False),
            _box(f"{prefix}Head", (0.037, 0.0085, 0.012), (x, y - 0.0005, z_head), head, "plastic"),
            _box(f"{prefix}Blade", (0.033, 0.0008, 0.0035), (x, y - 0.0048, z_head + s * 0.0005), "#C9CDD2",
                 "metal", collision=False),
            _box(f"{prefix}Strip", (0.033, 0.0008, 0.0022), (x, y - 0.0048, z_head + s * 0.0042), "#9FD8C9",
                 "plastic", collision=False)]


def disposable_razor_pack() -> Product:
    """台紙とブリスターに入った 2 枚刃の使い捨てカミソリ 3 本（刃を互い違いに並べる）。

    参考: https://commons.wikimedia.org/wiki/File:Bic_razor.jpg（CC0）
    """
    CW, CH = 85.0, 190.0
    blue, sky, white = "#1450A0", "#DCEBFA", WHITE
    c = Canvas(CW, CH, 10, sky, seed=7111)
    c.gradient(0, 0, CW, CH, "#EAF4FF", "#B9D6F2")
    c.pattern(0, 36, CW, CH, "waves", mix("#B9D6F2", white, 0.4), 7, 0.3)
    _hang_hole(c, CW / 2, 5, "#0B3470")
    c.rect(0, 14, CW, 34, fill=blue)
    c.text(CW / 2, 21, "使い捨てカミソリ", 6.8, white, 900, max_w=CW - 6)
    c.text(CW / 2, 29.5, "2枚刃  首振り", 4.2, mix(white, sky, 0.3), 800)
    c.ellipse(CW - 26, 152, CW - 4, 174, fill="#F2C230")
    c.text(CW - 15, 160, "3本", 6.2, blue, 900)
    c.text(CW - 15, 168, "入", 3.6, blue, 900)
    c.rect(5, 156, 56, 172, fill=white, radius=3)
    c.text(30.5, 161.5, "潤滑ストリップ付", 3.4, blue, 900, max_w=48)
    c.text(30.5, 167.5, "肌にやさしい", 3.0, INK, 700)
    c.rect(0, CH - 12, CW, CH, fill=blue)
    c.text(CW / 2, CH - 6, "DISPOSABLE RAZOR", 3.6, white, 800, spacing=0.6)
    _card_edges(c, blue)
    front = _face(c.array(), "film", 7111, 0.6)
    b = Canvas(CW, CH, 10, white, seed=7112)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EAF2FB")
    _card_edges(b, blue)
    _hang_hole(b, CW / 2, 5, "#8FA9C8")
    b.rect(0, 14, CW, 24, fill=blue)
    b.text(CW / 2, 19, "使い捨てカミソリ  2枚刃  3本入", 3.8, white, 800, max_w=CW - 6)
    yb = b.table(5, 29, CW - 5, "", [("品名", "かみそり（使い捨て）"), ("刃", "ステンレス 2枚刃"),
                                    ("柄", "ポリスチレン"), ("数量", "3本"), ("販売者", "架空の会社")], 3.3)
    b.paragraph(5, yb + 3, CW - 5, "【使用方法】肌をぬらし、シェービング剤をつけてから、毛の流れに沿ってそってください。"
                "\n【ご注意】刃に直接触れないでください。乳幼児の手の届かない所に保管してください。"
                "使用後はキャップをして捨ててください。\n" + NOTICE, 3.0, INK, 400)
    b.barcode(7, 150, 40, 22)
    b.recycle(60, 160, 8, "紙", blue, sub="台紙")
    b.recycle(74, 160, 8, "プラ", blue, sub="ケース")
    back = _face(b.array(), "paper", 7112, 0.6)
    parts = [_box("Card", (0.085, 0.0012, 0.19), (0, 0, 0.095), blue, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.080, 0.016, 0.142), (0, -0.0086, 0.084), FILM, "glass", thin_walled=True, collision=False)]
    yb_, yf_ = -0.0006 - 0.0029, -0.0006 - 0.0029 - 0.0062  # 奥の 2 本・手前の 1 本（柄の中心）
    parts += _razor("Razor0", -0.020, yb_, 0.142, True, "#2F6FB5", "#E8ECEF")
    parts += _razor("Razor1", 0.020, yb_, 0.142, True, "#2F6FB5", "#E8ECEF")
    parts += _razor("Razor2", 0.0, yf_, 0.026, False, "#2F6FB5", "#E8ECEF")
    _mat(parts, ("Card",), "paper")
    return Product(slug="disposable_razor_pack", name="使い捨てカミソリ 2枚刃 3本入", shape_class="assembly",
                   category="household", dims=Dimensions(0.19, 0.085, depth=0.0172), mass_kg=0.04, material="plastic",
                   description="形は一般的な台紙とブリスターに入った使い捨てカミソリ 3 本（台紙 85 × 190 mm、1 本の長さ約 115 mm）で、寸法・質量は代表値。3 本は刃を互い違いにして重ねて並べる。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["カミソリ", "使い捨てカミソリ", "髭剃り", "シェーバー", "ブリスター", "disposable razor",
                         "razors blister pack"],
                   photos=[], colors=Colors(label_base=sky), images=[front, back], parts=parts)


# ---------------------------------------------------------------- ビジネスソックス


def socks_pack() -> Product:
    """たたんだ黒の靴下 1 足を、上の台紙（二つ折りで挟む）で留めたもの。

    参考: https://commons.wikimedia.org/wiki/File:Socks_for_sale_in_Tokyo.jpg（CC0）
    """
    W, D = 95.0, 22.0  # 靴下の幅・厚さ [mm]
    SH, HH = 200.0, 72.0  # 靴下の長さ、台紙の高さ
    black, gray, gold, white = "#16171A", "#2A2C31", "#B8964A", WHITE
    s = 8

    def sock(seed: int, back: bool) -> np.ndarray:
        c = Canvas(W, SH, s, black, seed)
        c.gradient(0, 0, W, SH, "#26282D", "#121315")
        for k in range(int(W / 1.6)):  # リブ
            x = 0.8 + k * 1.6
            c.line([(x, 0), (x, SH - 30)], mix(black, "#4A4D55", 0.5), 0.35)
        c.line([(2, SH - 30), (W - 2, SH - 30)], "#33363C", 0.6)  # 足先の折り目
        c.polygon([(2, SH - 26), (W - 2, SH - 26), (W - 8, SH - 3), (8, SH - 3)], fill="#1D1E22")
        c.rect(0, 0, W, 1.0, fill=gray)
        c.rect(0, SH - 1.0, W, SH, fill=gray)
        if not back:
            c.text(W / 2, SH - 15, "25-27", 3.2, "#5A5E66", 700)
        return _face(c.array(), "film", seed, 0.3, 4)

    h = Canvas(W + 2, HH, s, white, seed=7123)  # 台紙の正面
    h.gradient(0, 0, W + 2, HH, "#FFFFFF", "#ECEDEF")
    h.rect(0, 0, W + 2, 2, fill=black)
    _hang_hole(h, (W + 2) / 2, 4, "#A0A3A8")
    h.text((W + 2) / 2, 19, "ビジネスソックス", 8.6, black, 900, max_w=W - 4)
    h.rect(4, 26, W - 2, 27, fill=gold)
    h.text((W + 2) / 2, 34, "綿混  消臭  つま先・かかと補強", 4.0, INK, 700, max_w=W - 6)
    h.rect(6, 41, 46, 64, fill=black, radius=2)
    h.text(26, 49, "黒", 7.0, white, 900)
    h.text(26, 58.5, "BLACK", 3.4, gold, 800, spacing=0.4)
    h.text(71, 47, "25〜27", 7.6, black, 900)
    h.text(71, 56, "cm", 4.0, black, 800)
    h.text(71, 64, "1足", 4.2, INK, 800)
    h.rect(0, HH - 2, W + 2, HH, fill=gold)
    head_front = _face(h.array(), "paper", 7123, 0.5)
    hb = Canvas(W + 2, HH, s, white, seed=7124)
    hb.rect(0, 0, W + 2, 2, fill=black)
    hb.rect(0, HH - 2, W + 2, HH, fill=gold)
    _hang_hole(hb, (W + 2) / 2, 4, "#A0A3A8")
    hb.table(4, 13, 60, "", [("品名", "紳士靴下"), ("組成", "綿 65% ポリエステル 30% ポリウレタン 5%"),
                             ("サイズ", "25〜27cm")], 2.6)
    hb.paragraph(4, 46, 60, NOTICE, 2.4, INK, 400)
    hb.barcode(64, 20, 28, 18)
    hb.recycle(78, 52, 7, "紙", INK, sub="台紙")
    head_back = _face(hb.array(), "paper", 7124, 0.5)
    t = Canvas(W + 2, D + 2, s, white, seed=7125)
    t.rect(0, 0, W + 2, 1.2, fill=gold)
    t.rect(0, D + 0.8, W + 2, D + 2, fill=gold)
    t.text((W + 2) / 2, (D + 2) / 2, "ビジネスソックス  黒  25〜27cm", 3.6, black, 900, max_w=W - 4)
    head_top = _face(t.array(), "paper", 7125, 0.5)
    sh, hh = SH / 1000, HH / 1000
    parts = [_box("Sock", (W / 1000, D / 1000, sh), (0, 0, sh / 2), black, "matte", {"front": 0, "back": 1}),
             _box("Header", ((W + 2) / 1000, (D + 2) / 1000, hh), (0, 0, sh - hh / 2 + 0.012), white, "matte",
                  {"front": 2, "back": 3, "top": 4})]
    _mat(parts, ("Sock",), "fabric")
    _mat(parts, ("Header",), "paper")
    return Product(slug="socks_pack", name="ビジネスソックス 黒 25〜27cm", shape_class="assembly",
                   category="household", dims=Dimensions(sh + 0.012, (W + 2) / 1000, depth=(D + 2) / 1000),
                   mass_kg=0.06, material="fabric",
                   description="形は一般的な、たたんだ紳士靴下 1 足（幅 95 mm・長さ 200 mm・厚さ 22 mm）の上部を二つ折りの台紙で挟んで留めたもので、寸法・質量は代表値。台紙は靴下の上端を包む直方体で表す。吊り下げ穴は穴を開けず印刷で表す。",
                   tags=["靴下", "ソックス", "ビジネスソックス", "紳士靴下", "衣料", "socks", "folded socks with header card"],
                   photos=[], colors=Colors(label_base=white),
                   images=[sock(7121, False), sock(7122, True), head_front, head_back, head_top], parts=parts)


# ---------------------------------------------------------------- フェイスタオル


def face_towel_pack() -> Product:
    """透明な袋に入った、たたんだ白のフェイスタオル（中に紙の帯）。

    参考: https://commons.wikimedia.org/wiki/File:Zusammengelegte_Handt%C3%BCcher.jpg（PD）
    """
    W, H, T = 140.0, 205.0, 28.0  # たたんだタオル [mm]
    white, blue = "#F7F6F2", "#2C6FB7"
    s = 6

    def pile(w: float, h: float, seed: int, folds: list[float], band: tuple[float, float] | None) -> np.ndarray:
        c = Canvas(w, h, s, white, seed)
        c.gradient(0, 0, w, h, "#FBFAF7", "#E9E7E0")
        if band:  # ドビー織りの帯
            c.rect(0, band[0], w, band[1], fill="#EFEDE6")
            for k in range(int((band[1] - band[0]) / 1.2)):
                y = band[0] + 0.6 + k * 1.2
                c.line([(0, y), (w, y)], "#DCD9D0", 0.25)
        for y in folds:  # たたんだ折り目の陰
            c.gradient(0, y - 3, w, y, "#F3F1EC", "#CFCCC3")
        a = c.array().astype(np.float32)
        rng = np.random.default_rng(seed)  # パイルの粒
        a += rng.normal(0, 7, a.shape[:2])[..., None]
        return _face(np.clip(a, 0, 255).astype(np.uint8), "paper", seed, 0.6, 6)

    front = pile(W, H, 7131, [70, 140], (176, 190))
    back = pile(W, H, 7132, [102], None)
    side = pile(T, H, 7133, [], None)
    b = Canvas(W, 52, 8, blue, seed=7134)  # 中の紙の帯
    b.gradient(0, 0, W, 52, "#3A82CC", "#1D5596")
    b.rect(0, 0, W, 1.5, fill="#F2C230")
    b.rect(0, 50.5, W, 52, fill="#F2C230")
    b.text(W / 2, 13, "フェイスタオル", 10, WHITE, 900)
    b.text(W / 2, 25, "白  綿 100%  約 34 × 80 cm", 4.6, "#E6F0FA", 800)
    b.rect(10, 31, W - 10, 45, fill=WHITE, radius=3)
    b.text(W / 2, 38, "ふんわり吸水  まとめ洗いOK", 4.6, blue, 900)
    band = _face(b.array(), "paper", 7134, 0.5)
    bk = Canvas(W, 52, 8, WHITE, seed=7135)
    bk.rect(0, 0, W, 1.5, fill=blue)
    bk.rect(0, 50.5, W, 52, fill=blue)
    bk.table(4, 5, 86, "", [("品名", "タオル"), ("組成", "綿 100%"), ("サイズ", "約 34 × 80 cm"),
                            ("販売者", "架空の会社")], 3.0)
    bk.paragraph(4, 37, 86, "初めてお使いの前に一度洗ってください。" + NOTICE, 2.4, INK, 400)
    bk.barcode(92, 14, 40, 24)
    band_back = _face(bk.array(), "paper", 7135, 0.5)
    w, h, t = W / 1000, H / 1000, T / 1000
    parts = [_box("Towel", (w, t, h), (0, 0, h / 2), white, "matte",
                  {"front": 0, "back": 1, "left": 2, "right": 2}),
             _box("Band", (w + 0.002, t + 0.002, 0.052), (0, 0, h - 0.045), WHITE, "matte",
                  {"front": 3, "back": 4}),
             _box("Bag", (w + 0.008, t + 0.006, h + 0.022), (0, 0, (h + 0.022) / 2), FILM, "glass", thin_walled=True, collision=False)]
    _mat(parts, ("Towel",), "fabric")
    _mat(parts, ("Band",), "paper")
    return Product(slug="face_towel_pack", name="フェイスタオル 白", shape_class="assembly", category="household",
                   dims=Dimensions(h + 0.022, w + 0.008, depth=t + 0.006), mass_kg=0.085, material="fabric",
                   description="形は一般的な、たたんで透明な袋に入れた白のフェイスタオル（約 34 × 80 cm を 140 × 205 mm に折ったもの、厚さ 28 mm）で、寸法・質量は代表値。中に巻いた紙の帯で品名を表す。",
                   tags=["タオル", "フェイスタオル", "白", "綿", "日用品", "face towel", "towel in plastic bag"],
                   photos=[], colors=Colors(label_base=white), images=[front, back, side, band, band_back],
                   parts=parts)


# ---------------------------------------------------------------- 封筒


def envelope_pack() -> Product:
    """フィルムの袋に入った長形 3 号の白い封筒 10 枚（表に郵便番号の枠）。

    参考: https://commons.wikimedia.org/wiki/File:Not_recycle-friendly,_envelope_sealed_with_plastic_tag_fastener,_in_Japan.jpg（CC0）
    """
    W, H, D = 128.0, 252.0, 5.0  # 袋（封筒は 120 × 235 mm）
    red, navy, white = "#D23A2E", "#1E3A6E", WHITE
    s = 6

    def bag(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, "#FAFAF8", seed)
        f.gradient(0, 0, w, h, "#FDFDFC", "#ECEDEE")
        return f

    fr = bag(W, H, 7141)
    seal_crimp(fr, 0, 0, W, 9, "#E4E6E8", 1.2)
    fr.rect(4, 13, W - 4, H - 4, fill=WHITE, outline="#D8DADC", width=0.4)  # いちばん上の封筒（表）
    for k in range(7):  # 郵便番号の枠（右上。3 桁 + 4 桁）
        x = 46 + k * 10 + (3 if k >= 3 else 0)
        fr.rect(x, 22, x + 8, 32, outline=red, width=0.45)
    fr.line([(75.5, 27), (78.5, 27)], red, 0.45)
    fr.rect(14, 150, W - 14, 214, fill=navy, radius=3)  # 品名のシール
    fr.text(W / 2, 166, "封筒", 13, white, 900)
    fr.text(W / 2, 182, "長形 3 号  白  10枚入", 6.4, white, 800, max_w=W - 34)
    fr.rect(22, 192, W - 22, 206, fill=white, radius=2)
    fr.text(W / 2, 199, "120 × 235 mm  A4 三つ折り", 4.4, navy, 900, max_w=W - 48)
    fr.text(W / 2, 228, "郵便番号枠付き  ケント紙 80g/㎡", 4.2, "#4A4F57", 700)
    fr.rect(0, H - 4, W, H, fill="#E4E6E8")
    bk = bag(W, H, 7142)
    seal_crimp(bk, 0, 0, W, 9, "#E4E6E8", 1.2)
    bk.rect(4, 13, W - 4, H - 4, fill=WHITE, outline="#D8DADC", width=0.4)  # 封筒の裏（ふた）
    bk.polygon([(4, 13), (W - 4, 13), (W - 4, 40), (W / 2, 52), (4, 40)], fill="#F6F6F4", outline="#C9CBCE")
    yb = bk.table(12, 72, W - 12, "", [("品名", "封筒（長形 3 号）"), ("大きさ", "120 × 235 mm"),
                                     ("紙", "白ケント 80g/㎡"), ("枚数", "10枚"), ("販売者", "架空の会社")], 4.0)
    bk.paragraph(12, yb + 4, W - 12, "定形郵便物に使えます。A4 の用紙を三つ折りにして入ります。\n" + NOTICE,
                 3.6, INK, 400)
    bk.barcode(14, 196, 46, 28)
    bk.recycle(84, 208, 10, "プラ", navy, sub="袋")
    bk.rect(0, H - 4, W, H, fill="#E4E6E8")
    sides = []
    for seed in (7143, 7144):
        sd = bag(D, H, seed)
        sd.rect(0, 0, D, 9, fill="#E4E6E8")
        sd.rect(0.6, 13, D - 0.6, H - 4, fill=WHITE)
        sd.rect(0, H - 4, D, H, fill="#E4E6E8")
        sides.append(sd)
    tp, bt = bag(W, D, 7145), bag(W, D, 7146)
    seal_crimp(tp, 0, 0, W, D, "#E4E6E8", 1.2, vertical=True)
    tp.rect(W / 2 - 9, 1, W / 2 + 9, D - 1, fill="#C9CBCE", radius=1)  # 吊り下げ穴（印刷）
    bt.rect(4, 0.8, W - 4, D - 0.8, fill=WHITE)
    for k in range(int(W / 3)):  # 重なった封筒の縁
        bt.rect(4 + k * 3, 0, 5.5 + k * 3, 0.8, fill="#D8DADC")
        bt.rect(4.8 + k * 3, D - 0.8, 6.3 + k * 3, D, fill="#D8DADC")
    imgs = _faces((fr, bk, *sides, tp, bt), "film", 7150, 0.5)
    return Product(slug="envelope_pack", name="封筒 長形3号 白 10枚入", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.05, material="paper",
                   description="形は一般的なフィルムの袋に入った長形 3 号の封筒 10 枚（封筒 120 × 235 mm、袋 128 × 252 mm・厚さ 5 mm）を箱で近似したもので、寸法・質量は代表値。表に郵便番号の枠、裏に封筒のふたが見える。",
                   tags=["封筒", "長形3号", "長3", "文房具", "事務用品", "envelope", "envelopes in plastic bag"],
                   photos=[], colors=Colors(label_base="#FAFAF8"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- カルトン


def cash_tray() -> Product:
    """レジで釣り銭・レシートを受け渡す樹脂のトレー（カルトン）。底に滑り止めのマット。

    参考: https://commons.wikimedia.org/wiki/File:Carton_2015-08-23.jpg（CC0）
    """
    W, D, H = 0.215, 0.150, 0.016
    resin, mat = "#2F4E6F", "#3A3D42"
    t = 0.003  # 壁の厚さ
    lean = 18.0  # 壁を外へ倒す角度
    wall_h = (H - 0.002) / math.cos(math.radians(lean))
    off = (H - 0.002) / 2 * math.tan(math.radians(lean))
    m = Canvas(W * 1000 - 20, D * 1000 - 20, None, mat, seed=7161)
    m.gradient(0, 0, m.w_mm, m.h_mm, "#43474E", "#2E3136")
    m.pattern(2, 2, m.w_mm - 2, m.h_mm - 2, "dots", "#55595F", 4.0, 0.9)
    m.rect(m.w_mm / 2 - 50, m.h_mm - 22, m.w_mm / 2 + 50, m.h_mm - 10, fill="#2E3136", radius=3)
    m.text(m.w_mm / 2, m.h_mm - 16, "ありがとうございました", 6.0, "#C9CDD2", 700)
    mat_img = _face(m.array(), "film", 7161, 0.4)
    zc = 0.002 + (H - 0.002) / 2
    iw, idp = W - 0.014, D - 0.014  # 底板（壁の下端の内側）
    lw, ld = iw + 2 * off + t, idp + 2 * off + t  # 壁の長さ（高さの中ほどで角が合う長さ）
    parts = [_box("Base", (iw, idp, 0.003), (0, 0, 0.0015), resin, "plastic"),
             _box("Mat", (iw - 0.006, idp - 0.006, 0.0015), (0, 0, 0.00375), mat, "matte", {"top": 0}),
             _box("WallFront", (lw, t, wall_h), (0, -idp / 2 - off, zc), resin, "glossy",
                  rotation=[lean, 0, 0]),
             _box("WallBack", (lw, t, wall_h), (0, idp / 2 + off, zc), resin, "glossy",
                  rotation=[-lean, 0, 0]),
             _box("WallLeft", (t, ld, wall_h), (-iw / 2 - off, 0, zc), resin, "glossy",
                  rotation=[0, -lean, 0]),
             _box("WallRight", (t, ld, wall_h), (iw / 2 + off, 0, zc), resin, "glossy",
                  rotation=[0, lean, 0])]
    _mat(parts, ("Mat",), "rubber")
    return Product(slug="cash_tray", name="カルトン（コイントレー）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=0.22, material="plastic",
                   description="形は一般的なレジのカルトン（角形の樹脂のトレー、215 × 150 mm・高さ 16 mm、底に滑り止めのマット）で、寸法・質量は代表値。外へ開いた 4 枚の壁と底板で表す。",
                   tags=["カルトン", "コイントレー", "釣り銭皿", "レジ用品", "店舗備品", "cash tray", "coin tray",
                         "plastic cash tray"],
                   photos=[], colors=Colors(label_base=resin), images=[mat_img], parts=parts)


# ---------------------------------------------------------------- 決済端末


def payment_terminal() -> Product:
    """レジのカウンターに置く、お客さま向けの決済端末（カード・電子マネー・QR コード）。台座に斜めに立てる。

    参考: https://commons.wikimedia.org/wiki/File:Card_Payment_(176811287).jpeg（CC0）
    """
    bw, bd, bh = 0.082, 0.030, 0.165  # 端末の本体
    tilt = -22.0  # 上を奥へ倒す
    dark, gray, blue = "#1E2126", "#3A3F47", "#2D7FD0"
    sw, sh = 70.0, 88.0  # 画面 [mm]
    c = Canvas(sw, sh, 1200 / sh, "#F4F7FA", seed=7171)
    c.gradient(0, 0, sw, sh, "#FFFFFF", "#E3EAF1")
    c.rect(0, 0, sw, 9, fill=blue)
    c.text(sw / 2, 4.5, "お支払い", 4.6, WHITE, 900)
    c.text(sw / 2, 16, "お支払い金額", 3.6, INK, 700)
    c.text(sw / 2, 25, "¥1,280", 9.0, "#C0392B", 900)
    c.line([(5, 32), (sw - 5, 32)], "#C9D2DC", 0.4)
    for i, (title, sub) in enumerate((("クレジット", "カード"), ("電子マネー", "タッチ"), ("QR コード", "スキャン"))):
        y = 36 + i * 15
        c.rect(5, y, sw - 5, y + 12, fill=WHITE, outline="#B8C4D0", width=0.4, radius=2)
        c.rect(8, y + 2.5, 15, y + 9.5, fill=(blue, "#1F9E6E", "#E08A1E")[i], radius=1.2)
        c.text(19, y + 6, title, 3.8, INK, 800, anchor="lm")
        c.text(sw - 8, y + 6, sub, 3.0, "#5A6470", 600, anchor="rm")
    c.text(sw / 2, 84, "カードを挿入するか、タッチしてください", 2.7, INK, 600, max_w=sw - 6)
    screen = trim_safe(finish(c.array(), "screen", 7171, 0.5))
    f = Canvas(bw * 1000 - 4, 66.0, 12, dark, seed=7172)  # 本体の正面の下（非接触の読み取り部）
    f.gradient(0, 0, f.w_mm, 66, "#2A2E35", "#181A1E")
    cx = f.w_mm / 2
    for r in (5.0, 9.0, 13.0):  # 非接触の電波マーク（簡略形）
        f.d.arc(f.box(cx - r - 4, 24 - r, cx + r - 4, 24 + r), -50, 50, fill="#E8ECF0", width=round(0.9 * f.s))
    f.text(cx, 46, "ここにタッチ", 4.2, "#E8ECF0", 800)
    f.rect(cx - 16, 52, cx + 16, 53, fill=blue)
    f.text(cx, 59, "IC カードは下から挿入", 2.8, "#9AA3AE", 600)
    lower = _face(f.array(), "film", 7172, 0.3)
    pivot = (0.0, 0.004, 0.046)  # 本体の下端の中心（首の上）
    rot = [tilt, 0, 0]
    z0 = pivot[2]
    yf = pivot[1] - bd / 2  # 本体の正面（倒す前）
    parts = [_cyl("Base", (0.105, 0.095, 0.012), (0, 0.004, 0.006), gray, "plastic"),
             _cyl("Neck", (0.030, 0.030, 0.030), (0, 0.004, 0.027), dark, "plastic"),
             _box("Hinge", (0.050, 0.026, 0.012), (0, 0.004, 0.044), dark, "plastic"),
             _box("Body", (bw, bd, bh), _tilt((0, pivot[1], z0 + bh / 2), pivot, tilt), dark, "plastic",
                  rotation=rot),
             _box("Screen", (sw / 1000, 0.0015, sh / 1000),
                  _tilt((0, yf - 0.0006, z0 + bh - 0.008 - sh / 2000), pivot, tilt), "#101215", "screen",
                  {"front": 0}, rot, collision=False),
             _box("ReaderPanel", (bw - 0.004, 0.0012, 0.066),
                  _tilt((0, yf - 0.0005, z0 + 0.003 + 0.033), pivot, tilt), dark, "glossy",
                  {"front": 1}, rot, collision=False),
             _box("CardSlot", (0.062, 0.010, 0.003), _tilt((0, yf + 0.008, z0 - 0.0012), pivot, tilt), "#08090B",
                  "matte", rotation=rot, collision=False),
             _box("Camera", (0.010, 0.002, 0.005), _tilt((0.028, yf - 0.0006, z0 + bh - 0.004), pivot, tilt),
                  "#050506", "glossy", rotation=rot, collision=False)]
    return Product(slug="payment_terminal", name="決済端末", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.204, 0.105, depth=0.123), mass_kg=0.55, material="plastic",
                   description="形は一般的なレジのお客さま向けの決済端末（本体 82 × 165 × 30 mm、台座に約 22° 倒して立てる。カード・電子マネー・QR コードに対応）で、寸法・質量は代表値。画面は架空の支払い画面。",
                   tags=["決済端末", "カード決済", "キャッシュレス", "電子マネー", "QR コード決済", "レジ",
                         "payment terminal", "card reader on stand"],
                   photos=[], colors=Colors(label_base=dark), images=[screen, lower], parts=parts)


# ---------------------------------------------------------------- 飛沫防止パーティション


def register_partition() -> Product:
    """レジのカウンターに置く、透明なアクリル板の飛沫防止パーティション（下の中央に受け渡しの開口、足 2 枚）。

    参考: https://commons.wikimedia.org/wiki/File:Screen_protecting_supermarket_cashier.jpg（CC0）、
    https://commons.wikimedia.org/wiki/File:BHC_Makalapa_Pharmacy_Implements_Plexiglass_Screens_200429-N-WF582-038_(49837821562).jpg（PD）
    """
    W, H, t = 0.80, 0.65, 0.003
    ow, oh = 0.30, 0.12  # 受け渡しの開口
    acryl = "#EEF4F6"
    side_w = (W - ow) / 2
    st = Canvas(140.0, 42.0, None, WHITE, seed=7181)
    st.rect(0, 0, 140, 4, fill="#2D7FD0")
    st.rect(0, 38, 140, 42, fill="#2D7FD0")
    st.text(70, 15, "飛沫感染防止のため", 7.6, INK, 900)
    st.text(70, 28, "パーティションを設置しています", 6.0, INK, 700)
    sticker = _face(st.array(), "paper", 7181, 0.4)
    parts = [_box("PanelLeft", (side_w, t, H), (-(ow + side_w) / 2, 0, H / 2), acryl, "glass"),
             _box("PanelRight", (side_w, t, H), ((ow + side_w) / 2, 0, H / 2), acryl, "glass"),
             _box("PanelTop", (ow, t, H - oh), (0, 0, oh + (H - oh) / 2), acryl, "glass"),
             _box("Sticker", (0.14, 0.0004, 0.042), (0, -t / 2 - 0.0002, H - 0.06), WHITE, "matte", {"front": 0},
                  collision=False)]
    for k, x in enumerate((-0.31, 0.31)):  # 足（板に差し込んだ透明な板）と滑り止め・差し込みの金具
        parts.append(_box(f"Foot{k}", (0.008, 0.20, 0.06), (x, 0, 0.03), acryl, "glass"))
        parts.append(_box(f"FootPad{k}", (0.010, 0.20, 0.002), (x, 0, 0.001), "#2A2C30", "matte", collision=False))
        parts.append(_box(f"Clip{k}", (0.03, 0.012, 0.012), (x, 0, 0.066), "#B8BCC2", "metal", collision=False))
    _mat(parts, ("Panel", "Foot0", "Foot1"), "plexiglass")
    _mat(parts, ("FootPad",), "rubber")
    _mat(parts, ("Sticker",), "paper")
    return Product(slug="register_partition", name="レジ用 飛沫防止パーティション", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=0.20), mass_kg=2.1, material="plexiglass",
                   description="形は一般的なカウンター置きの透明アクリルのパーティション（幅 800 × 高さ 650 mm・厚さ 3 mm、下の中央に 300 × 120 mm の受け渡し口、差し込み式の足 2 枚）で、寸法・質量は代表値。",
                   tags=["パーティション", "飛沫防止", "アクリル板", "仕切り", "レジ", "店舗備品",
                         "sneeze guard", "acrylic partition", "checkout partition"],
                   photos=[], colors=Colors(label_base=acryl), images=[sticker], parts=parts)


# ---------------------------------------------------------------- セルフコーヒーの備品台


def coffee_condiment_station() -> Product:
    """セルフコーヒーの横に置く備品台（カップのふた・ストロー・マドラー・ガムシロップとミルクのポーション）。

    参考: https://commons.wikimedia.org/wiki/File:Caps-of-convenience-store-coffee-cup.JPG（CC0）、
    https://commons.wikimedia.org/wiki/File:Dispenser_for_plastic_straws_with_handmade_label.jpg（CC0）、
    https://commons.wikimedia.org/wiki/File:Des_touillettes_(b%C3%A2tonnets_m%C3%A9langeurs)_pour_le_caf%C3%A9_%C3%A0_%C3%94_Totem_(Rillieux-la-Pape)_en_juin_2023.jpg（CC0）
    """
    W, D = 0.45, 0.20
    wood, white, brown = "#B98A5A", "#F4F2EE", "#5A3A22"
    bh = 0.015  # 底板
    pw, ph = 430.0, 120.0
    c = Canvas(pw, ph, None, brown, seed=7191)  # 背板の表示
    c.gradient(0, 0, pw, ph, "#6B4529", "#3E2716")
    c.rect(0, 0, pw, 4, fill="#D9B27A")
    c.text(pw / 2, 15, "ご自由にお使いください", 12, WHITE, 900)
    for i, (jp, en) in enumerate((("ふた", "LID"), ("ストロー", "STRAW"), ("マドラー", "STIRRER"),
                                  ("シロップ・ミルク", "SYRUP / MILK"))):
        x = (90, 220, 295, 380)[i]
        c.text(x, 32, jp, 10, "#F6E7CF", 800, max_w=90)
        c.text(x, 43, en, 5.5, "#D9B27A", 700, spacing=0.6)
    c.text(pw / 2, 92, "ホットはふたの飲み口を合わせてしっかり閉めてください", 8.0, WHITE, 600)
    c.text(pw / 2, 108, "使い終わったマドラー・ストローはごみ箱へ", 6.6, "#E8D8C0", 500)
    c.rect(0, ph - 4, pw, ph, fill="#D9B27A")
    sign = _face(c.array(), "paper", 7191, 0.3)
    parts = [_box("Base", (W, D, bh), (0, 0, bh / 2), wood, "plastic"),
             _box("BackPanel", (W, 0.012, 0.29 - bh), (0, D / 2 - 0.006, bh + (0.29 - bh) / 2), wood, "plastic"),
             _box("Sign", (pw / 1000, 0.001, ph / 1000), (0, D / 2 - 0.0125, 0.215), brown, "matte", {"front": 0},
                  collision=False),
             _box("SideLeft", (0.012, D - 0.012, 0.10 - bh), (-W / 2 + 0.006, -0.006, bh + (0.10 - bh) / 2), wood,
                  "plastic"),
             _box("SideRight", (0.012, D - 0.012, 0.10 - bh), (W / 2 - 0.006, -0.006, bh + (0.10 - bh) / 2), wood,
                  "plastic"),
             _box("FrontLip", (W - 0.024, 0.010, 0.025), (0, -D / 2 + 0.005, bh + 0.0125), wood, "plastic")]
    for k, x in enumerate((-0.035, 0.045, 0.115)):  # 仕切り
        parts.append(_box(f"Divider{k}", (0.006, D - 0.022, 0.06), (x, -0.001, bh + 0.03), wood, "plastic"))
    _mat(parts, ("Base", "BackPanel", "Side", "FrontLip", "Divider"), "wood")
    _mat(parts, ("Sign",), "paper")
    z0 = bh
    # ふた（重ねたもの。手前の 2 本が M、奥の 2 本が L）
    for k, (x, y, dia, col) in enumerate(((-0.170, -0.040, 0.080, "#1E1E20"), (-0.085, -0.040, 0.080, white),
                                          (-0.170, 0.045, 0.090, "#1E1E20"), (-0.085, 0.045, 0.090, "#4A2F20"))):
        n = 0.070 if k < 2 else 0.055
        parts.append(_cyl(f"LidStack{k}", (dia, dia, n), (x, y, z0 + n / 2), col, "plastic"))
        parts.append(_cyl(f"LidTop{k}", (dia * 0.62, dia * 0.62, 0.006), (x, y, z0 + n + 0.003),
                          mix(col, "#808080", 0.25), "plastic", collision=False))
    # ストロー立て（半透明の筒）とストロー
    sx, sy = 0.005, -0.01
    parts.append(_cyl("StrawCup", (0.060, 0.060, 0.12), (sx, sy, z0 + 0.06), "#E6ECEF", "frosted"))
    for k in range(11):
        a = k / 11 * 2 * math.pi
        r = 0.012 + 0.006 * (k % 2)
        tx, ty = 8 * math.cos(a), 8 * math.sin(a)
        col = ("#2D7FD0", "#E04C3A", "#F4F4F4")[k % 3]
        parts.append(Part(f"Straw{k}", "cylinder", [0.006, 0.006, 0.21],
                          [sx + r * math.cos(a), sy + r * math.sin(a), z0 + 0.108], [ty, -tx, 0], col,
                          "plastic", collision=False))
    # マドラー立て（金属の筒）と木の棒
    mx, my = 0.080, -0.01
    parts.append(_cyl("StirrerCup", (0.050, 0.050, 0.10), (mx, my, z0 + 0.05), "#C4C7CB", "metal"))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        r = 0.008 + 0.006 * (k % 2)
        tx, ty = 9 * math.cos(a), 9 * math.sin(a)
        parts.append(Part(f"Stirrer{k}", "box", [0.0055, 0.0015, 0.14],
                          [mx + r * math.cos(a), my + r * math.sin(a), z0 + 0.082],
                          [ty, -tx, 0], "#E3C89A", "matte", collision=False, material="wood"))
    # ポーション入れ（浅いトレー）とガムシロップ・ミルク
    px = 0.170
    parts.append(_box("PortionTray", (0.090, 0.150, 0.025), (px, -0.005, z0 + 0.0125), white, "plastic"))
    zt = z0 + 0.025
    for i in range(3):
        for j in range(4):
            x, y = px - 0.028 + i * 0.028, -0.0575 + j * 0.035
            milk = i == 2
            nm = "Milk" if milk else "Syrup"
            parts.append(_cyl(f"{nm}{i}{j}", (0.024, 0.024, 0.018), (x, y, zt + 0.009),
                              "#FAFAFA" if milk else "#EDE7D8", "plastic" if milk else "translucent",
                              collision=False))
            parts.append(_cyl(f"{nm}Lid{i}{j}", (0.027, 0.027, 0.0012), (x, y, zt + 0.0186),
                              "#2D7FD0" if milk else "#C8A040", "metal", collision=False))
    return Product(slug="coffee_condiment_station", name="セルフコーヒーの備品台", shape_class="assembly",
                   category="fixture", dims=Dimensions(0.29, W, depth=D), mass_kg=3.2, material="wood",
                   description="形は一般的なコンビニのセルフコーヒーの横に置く卓上の備品台（幅 450 × 奥行き 200 × 高さ 290 mm、木目の樹脂）に、カップのふた・ストロー・マドラー・ガムシロップとミルクのポーションを並べたもので、寸法・質量は代表値。重ねたふたは円柱で表す。",
                   tags=["コーヒー", "セルフコーヒー", "備品台", "ストロー", "マドラー", "ガムシロップ", "店舗備品",
                         "coffee condiment station", "lids and straws organizer"],
                   photos=[], colors=Colors(label_base=wood), images=[sign], parts=parts)


# ---------------------------------------------------------------- 踏み台


def step_stool() -> Product:
    """品出しに使う 2 段の樹脂の踏み台（踏み面に滑り止め）。

    参考: https://commons.wikimedia.org/wiki/File:HK_CWB_%E9%8A%85%E9%91%BC%E7%81%A3_Causeway_Bay_%E6%9F%8F%E5%AF%A7%E9%85%92%E5%BA%97_Park_Lane_Hotel_basement_%E5%AE%9C%E5%AE%B6%E5%AE%B6%E5%B1%85_IKEA_Store_August_2026_N13P_215.jpg（CC0）
    """
    W, D = 0.42, 0.44
    h1, h2 = 0.20, 0.40  # 1 段目・2 段目の踏み面の高さ
    body, tread = "#D6DADF", "#3E4349"
    tt = 0.025  # 踏み面の厚さ
    sd = 0.03  # 側板の厚さ

    def tread_img(w: float, d: float, seed: int) -> np.ndarray:
        c = Canvas(w, d, None, tread, seed)
        c.gradient(0, 0, w, d, "#474C53", "#363A40")
        c.pattern(6, 6, w - 6, d - 20, "dots", "#5C626A", 12.0, 2.6)
        c.rect(0, d - 14, w, d, fill="#E8B020")  # 前の縁の黄色
        for k in range(int(w / 16) + 1):
            c.polygon([(k * 16, d - 14), (k * 16 + 8, d - 14), (k * 16 + 2, d), (k * 16 - 6, d)], fill="#26292D")
        return _face(c.array(), "film", seed, 0.4)

    lab = Canvas(120.0, 70.0, None, WHITE, seed=7203)  # 側板の注意ラベル
    lab.rect(0, 0, 120, 14, fill="#E8B020")
    lab.text(60, 7, "注意", 8, INK, 900)
    lab.text(60, 24, "耐荷重 100kg", 8.6, INK, 900)
    lab.paragraph(6, 33, 114, "平らな床で使い、踏み面の端に乗らないでください。" + NOTICE, 4.0, INK, 400)
    lab.rect(0, 67, 120, 70, fill="#E8B020")
    label = _face(lab.array(), "paper", 7203, 0.4)
    parts = [_box("Tread1", (W, D / 2, tt), (0, -D / 4, h1 - tt / 2), tread, "matte", {"top": 0}),
             _box("Tread2", (W, D / 2, tt), (0, D / 4, h2 - tt / 2), tread, "matte", {"top": 1}),
             _box("Riser", (W - 2 * sd, 0.02, h2 - h1 - tt), (0, 0.01, h1 + (h2 - h1 - tt) / 2), body),
             _box("BackBrace", (W - 2 * sd, 0.02, 0.12), (0, D / 2 - 0.02, h2 - tt - 0.06), body),
             _box("FrontBrace", (W - 2 * sd, 0.02, 0.06), (0, -D / 2 + 0.02, h1 - tt - 0.03), body),
             _box("Label", (0.0006, 0.12, 0.07), (W / 2 + 0.0003, D / 4, h1 + 0.06), WHITE, "matte",
                  {"right": 2}, collision=False)]
    for k, sx in enumerate((-1, 1)):  # 側板（前の低い脚・後ろの高い脚）と滑り止めの足
        x = sx * (W / 2 - sd / 2)
        parts.append(_box(f"SideFront{k}", (sd, D / 2, h1 - tt), (x, -D / 4, (h1 - tt) / 2), body))
        parts.append(_box(f"SideBack{k}", (sd, D / 2, h2 - tt), (x, D / 4, (h2 - tt) / 2), body))
        for j, y in enumerate((-D / 2 + 0.03, D / 2 - 0.03)):
            parts.append(_box(f"Foot{k}{j}", (sd + 0.004, 0.05, 0.008), (x, y, 0.004), "#2A2C30", "matte",
                              collision=False))
    _mat(parts, ("Tread", "Foot"), "rubber")
    _mat(parts, ("Label",), "paper")
    return Product(slug="step_stool", name="踏み台 2段", shape_class="assembly", category="fixture",
                   dims=Dimensions(h2, W, depth=D), mass_kg=3.4, material="plastic",
                   description="形は一般的な品出し用の 2 段の樹脂の踏み台（幅 420 × 奥行き 440 mm、踏み面の高さ 200 mm・400 mm、耐荷重 100 kg、滑り止めの踏み面）で、寸法・質量は代表値。側板は脚の形の直方体で表す。",
                   tags=["踏み台", "脚立", "ステップ", "品出し", "店舗備品", "step stool", "plastic two-step stool"],
                   photos=[], colors=Colors(label_base=body),
                   images=[tread_img(W * 1000, D * 500, 7201), tread_img(W * 1000, D * 500, 7202), label],
                   parts=parts)


PRODUCTS = {f.__name__: f for f in (mobile_battery_blister, disposable_razor_pack, socks_pack, face_towel_pack,
                                    envelope_pack, cash_tray, payment_terminal, register_partition,
                                    coffee_condiment_station, step_stool)}
