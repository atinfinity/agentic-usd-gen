"""架空の商品のデザイン: カフェの什器・備品。

products.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
正面は −Y（お客さま側）。床置きの重い什器はキネマティック（static）、テーブル・椅子は動かせる。
商品（ケーキ・カップ）を並べる面は薄い水平の板にする（商品を並べるツールが棚板として見つけられるように）。
メニュー・看板（店の売り文句の入った面）は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product, label_canvas, revolve, top_canvas
from .drinks_more import _hot_cup
from .paint import Canvas, finish, mix
from .products import INK, _box, _cyl, _face
from .super_fixtures import _grain, _sign

CAFE_PLACES = ["cafe", "restaurant"]  # カフェのメニュー・看板が合う場所
WOOD, WOOD_DARK, WALNUT = "#B98A57", "#7A5533", "#5B3B26"
STAINLESS, BLACK, GLASS, CREAM = "#C4C8CC", "#2A2B2E", "#EAF2F5", "#F3EBDD"
CHALK = "#2E3430"


def _wood(name, size, center, color=WOOD, faces=None, collision=True, rotation=None) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish="matte", faces=faces, collision=collision, material="wood")


def _fabric(name, size, center, color, rotation=None, bevel=None) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), rotation=list(rotation or [0, 0, 0]),
                color=color, finish="matte", material="fabric", bevel=bevel)


def _chalk_bg(c: Canvas) -> None:
    """黒板の地（濃い緑がかった灰色に、消し跡のむら）。"""
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, mix(CHALK, "#FFFFFF", 0.06), mix(CHALK, "#000000", 0.12))
    for _ in range(14):
        x, y = c.rng.uniform(0, W), c.rng.uniform(0, H)
        r = c.rng.uniform(40, 140)
        c.ellipse(x - r, y - r * 0.35, x + r, y + r * 0.35, fill=mix(CHALK, "#FFFFFF", c.rng.uniform(0.03, 0.07)))


# ---------------------------------------------------------------- 注文カウンター


def _counter_front(w_mm: float, h_mm: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """カウンターの腰板（木目に店の看板）と、文字・写真を抜いた無地の木目。"""
    blank = _grain(w_mm, h_mm, seed, WOOD)
    c = Canvas(w_mm, h_mm, None, WOOD, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(WOOD, "#FFFFFF", 0.08), mix(WOOD, "#000000", 0.06))
    y = 6.0
    while y < h_mm:
        c.line([(0, y), (w_mm * 0.4, y + c.rng.uniform(-3, 3)), (w_mm, y + c.rng.uniform(-4, 4))],
               mix(WOOD, WOOD_DARK, c.rng.uniform(0.15, 0.35)), c.rng.uniform(0.6, 1.6))
        y += c.rng.uniform(8, 22)
    cx = w_mm * 0.72
    c.rect(cx - 420, 120, cx + 420, 520, fill=CHALK, outline=WOOD_DARK, width=10, radius=6)
    c.text(cx, 190, "ORDER HERE", 58, CREAM, 900, spacing=6)
    c.text(cx, 260, "ご注文はこちらで", 40, "#F6D58E", 800)
    c.photo("latte", cx - 380, 300, cx - 80, 500, shape="ellipse", crop=(0.15, 0.1, 0.85, 0.9))
    c.paragraph(cx - 40, 310, cx + 390, "お会計のあと、受け取り口でお待ちください。", 30, CREAM, 700)
    c.text(cx + 175, 470, "COFFEE & CAKE", 34, "#F6D58E", 900, spacing=3)
    c.text(w_mm * 0.22, 140, "CAKE", 70, CREAM, 900, spacing=10)
    c.text(w_mm * 0.22, 210, "本日のケーキ", 38, CREAM, 800)
    return _face(c.array(), "paper", seed, 0.5, 6), blank


def _pos_screen(seed: int) -> np.ndarray:
    """店員側の会計画面（架空）。"""
    c = Canvas(300, 200, None, "#F4F5F7", seed)
    c.gradient(0, 0, 300, 200, "#FFFFFF", "#E8EAED")
    c.rect(0, 0, 300, 24, fill="#4E342E")
    c.text(10, 12, "注文入力", 11, "#FFFFFF", 800, anchor="lm")
    c.text(290, 12, "12:34", 10, "#FFFFFF", 700, anchor="rm")
    items = [("ブレンド", "#6D4C41"), ("カフェラテ", "#A1887F"), ("カプチーノ", "#8D6E63"), ("紅茶", "#C0763A"),
             ("ケーキ", "#D88FA0"), ("焼き菓子", "#C9A26B"), ("サイズ変更", "#78909C"), ("持ち帰り", "#607D8B")]
    for i, (s, col) in enumerate(items):
        x0, y0 = 8 + (i % 4) * 46, 32 + (i // 4) * 50
        c.rect(x0, y0, x0 + 42, y0 + 44, fill=col, radius=4)
        c.text(x0 + 21, y0 + 22, s, 7, "#FFFFFF", 800, max_w=38)
    c.rect(196, 32, 292, 180, fill="#FFFFFF", outline="#C8CCD0", width=1)
    for j, (s, p) in enumerate([("カフェラテ M", "450"), ("ブレンド S", "350"), ("ケーキ", "480")]):
        c.text(200, 46 + j * 16, s, 7, INK, 700, anchor="lm")
        c.text(288, 46 + j * 16, p, 7, INK, 700, anchor="rm")
    c.rect(196, 150, 292, 180, fill="#2E7D32")
    c.text(244, 165, "会計 1,280", 10, "#FFFFFF", 900)
    c.rect(8, 136, 188, 180, fill="#ECEFF1", radius=4)
    c.text(98, 158, "テイクアウト / 店内", 9, "#455A64", 800)
    return _face(c.array(), "screen", seed, 0.6, 4)


def _customer_display(seed: int) -> np.ndarray:
    """お客さま向けの小さな表示（合計金額）。"""
    c = Canvas(160, 100, None, "#0B1A24", seed)
    c.gradient(0, 0, 160, 100, "#11283A", "#08131B")
    c.text(80, 22, "ご注文の合計", 11, "#B3E5FC", 800)
    c.text(80, 56, "¥1,280", 26, "#FFFFFF", 900)
    c.text(80, 86, "ありがとうございます", 9, "#80CBC4", 700)
    return _face(c.array(), "screen", seed, 0.6, 4)


def cafe_order_counter() -> Product:
    """カフェの注文カウンター（2400 mm）。左にケーキのショーケース（ガラス・中段の棚）、右にレジ。

    写真: latte（CC0。腰板の看板に合成）
    """
    W, D, top_z = 2.40, 0.70, 0.95
    front, blank = _counter_front(2360, 780, 5701)
    images = [front, blank, _pos_screen(5702), _customer_display(5703)]
    parts: list[Part] = [
        _box("Plinth", (2.34, 0.62, 0.08), (0, 0.02, 0.04), BLACK, "matte"),
        _wood("Body", (W, 0.68, 0.83), (0, 0.01, 0.08 + 0.415), WOOD),
        Part("FrontPanel", "box", [2.36, 0.006, 0.78], [0, -0.333, 0.08 + 0.01 + 0.39], color=WOOD, finish="matte",
             faces={"front": 0}, collision=False, material="wood", bevel=0, blank=1),
        # 天板はショーケースの下とレジの側で分ける（それぞれが商品を置ける面になる）
        _wood("TopCase", (1.00, D, 0.04), (-0.70, 0, top_z - 0.02), WALNUT),
        _wood("TopRegister", (1.40, D, 0.04), (0.50, 0, top_z - 0.02), WALNUT),
    ]
    # ケーキのショーケース（x −1.2〜−0.2）。前のガラスは奥へ傾け、中段はガラスの棚
    cx, case_h = -0.70, 0.35
    y_front, y_top_front, y_back = -0.33, -0.20, 0.32
    glen = math.hypot(y_top_front - y_front, case_h)
    tilt = -math.degrees(math.atan2(y_top_front - y_front, case_h))
    parts += [
        Part("CaseFront", "box", [0.98, 0.006, glen], [cx, (y_front + y_top_front) / 2, top_z + case_h / 2],
             [tilt, 0, 0], color=GLASS, finish="glass", thin_walled=True, material="glass", bevel=0),
        Part("CaseTop", "box", [0.98, y_back - y_top_front, 0.008], [cx, (y_back + y_top_front) / 2, top_z + case_h],
             color=GLASS, finish="glass", thin_walled=True, material="glass", bevel=0),
        Part("CaseShelf", "box", [0.94, 0.40, 0.008], [cx, 0.09, top_z + 0.17], color=GLASS, finish="glass",
             thin_walled=True, material="glass", bevel=0),
        Part("CaseBack", "box", [0.98, 0.006, case_h - 0.01], [cx, y_back, top_z + case_h / 2], color=GLASS,
             finish="frosted", thin_walled=True, material="glass", bevel=0),
    ]
    for side, x in (("L", cx - 0.495), ("R", cx + 0.495)):
        parts.append(Part(f"CaseSide{side}", "box", [0.008, y_back - y_front, case_h],
                          [x, (y_back + y_front) / 2, top_z + case_h / 2], color=GLASS, finish="glass",
                          thin_walled=True, material="glass", bevel=0))
    for i, (y, z) in enumerate([(y_back, top_z + case_h / 2)]):
        for x in (cx - 0.49, cx + 0.49):
            parts.append(_box(f"CasePost{i}{'L' if x < cx else 'R'}", (0.014, 0.014, case_h), (x, y, z), STAINLESS,
                              "metal", collision=False))
    parts += [_box("CaseRailTop", (1.00, 0.014, 0.014), (cx, y_top_front, top_z + case_h), STAINLESS, "metal",
                   collision=False),
              _box("CaseShelfRail", (0.94, 0.012, 0.012), (cx, 0.09 - 0.20, top_z + 0.17 - 0.010), STAINLESS,
                   "metal", collision=False)]
    # レジ（店員側を向いた画面）・お客さま向けの表示・決済端末
    rx = 0.55
    parts += [
        _box("PosBase", (0.22, 0.20, 0.06), (rx, 0.12, top_z + 0.03), BLACK, "plastic"),
        _box("PosStand", (0.05, 0.04, 0.16), (rx, 0.14, top_z + 0.05 + 0.08), BLACK, "plastic"),
        Part("PosScreen", "box", [0.34, 0.025, 0.23], [rx, 0.12, top_z + 0.235], [-12, 0, 0], color=BLACK,
             finish="screen", faces={"back": 2}, material="plastic", bevel=0.004),
        _box("CustomerStand", (0.03, 0.03, 0.10), (rx + 0.30, -0.05, top_z + 0.05), BLACK, "plastic"),
        Part("CustomerDisplay", "box", [0.17, 0.02, 0.11], [rx + 0.30, -0.06, top_z + 0.155], [8, 0, 0],
             color=BLACK, finish="screen", faces={"front": 3}, material="plastic", bevel=0.003),
        _box("PayTerminal", (0.08, 0.15, 0.04), (rx - 0.30, -0.20, top_z + 0.02), "#3A3D42", "plastic"),
        _box("PayKeys", (0.06, 0.07, 0.003), (rx - 0.30, -0.23, top_z + 0.0415), "#9EA4AA", "plastic",
             collision=False),
    ]
    return Product(slug="cafe_order_counter", name="カフェの注文カウンター（ケーキのショーケース・レジ付き 2400 mm）",
                   shape_class="assembly", category="fixture",
                   dims=Dimensions(top_z + case_h + 0.004, W, depth=D), mass_kg=180.0, static=True, material="wood",
                   description="形はカフェの注文カウンターの一般的な構成（幅 2400 mm・奥行き 700 mm・天板の高さ 950 mm、"
                               "左に幅 1000 mm・高さ 350 mm の前傾ガラスのケーキのショーケース（中段にガラスの棚）、右にレジ・"
                               "お客さま向けの表示・決済端末）で、寸法・質量は代表値。会計画面・腰板の看板は架空。",
                   tags=["カフェ", "注文カウンター", "レジカウンター", "ショーケース", "ケーキ", "店舗什器",
                         "cafe counter", "order counter", "cake showcase", "register"],
                   photos=["latte"], colors=Colors(label_base=WOOD), images=images, parts=parts,
                   picture_places=CAFE_PLACES)


# ---------------------------------------------------------------- エスプレッソマシン


def _espresso_panel(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    """エスプレッソマシンの正面の板（ステンレスにメーター 2 つ・ボタン）。"""
    c = Canvas(w_mm, h_mm, None, STAINLESS, seed)
    c.gradient(0, 0, w_mm, h_mm, "#D9DCDF", "#A9AEB3", horizontal=True)
    c.rect(0, 0, w_mm, 40, fill="#B23A2E")
    c.text(w_mm / 2, 20, "ESPRESSO  2 GROUP", 18, "#F5E9DC", 900, spacing=4)
    for x in (w_mm * 0.38, w_mm * 0.62):  # 圧力計
        c.ellipse(x - 28, 60, x + 28, 116, fill="#F7F7F5", outline="#555A60", width=4)
        c.line([(x, 88), (x + 14, 72)], "#C62828", 2)
        for k in range(7):
            a = math.radians(210 - k * 40)
            c.line([(x + 22 * math.cos(a), 88 - 22 * math.sin(a)), (x + 26 * math.cos(a), 88 - 26 * math.sin(a))],
                   "#333333", 1.2)
    for x in (w_mm * 0.24, w_mm * 0.76):  # 抽出ボタン
        for k in range(4):
            c.rect(x - 46 + k * 24, 70, x - 28 + k * 24, 88, fill="#33373C", radius=3)
            c.ellipse(x - 41 + k * 24, 75, x - 33 + k * 24, 83, fill="#8FD3FF" if k else "#FFB74D")
    c.text(w_mm / 2, h_mm - 18, "HOT WATER", 10, "#555A60", 800, spacing=2)
    return _face(c.array(), "metal", seed, 0.5, 8)


def espresso_machine() -> Product:
    """業務用のエスプレッソマシン（2 グループ）。上はカップウォーマー、手前に抽出口と受け皿。"""
    W, D = 0.75, 0.55
    y0, y1 = -0.10, D / 2  # 本体の前・後ろ
    images = [_espresso_panel(730, 300, 5711)]
    parts: list[Part] = [
        _box("Base", (W, D, 0.08), (0, 0, 0.04), BLACK, "metal"),
        _box("Body", (W, y1 - y0, 0.34), (0, (y0 + y1) / 2, 0.08 + 0.17), STAINLESS, "metal"),
        Part("FrontPanel", "box", [0.73, 0.004, 0.30], [0, y0 - 0.002, 0.08 + 0.17], color=STAINLESS,
             finish="metal", faces={"front": 0}, collision=False, material="steel", bevel=0),
        _box("DripGrate", (0.62, 0.16, 0.004), (0, -0.18, 0.082), "#8E949B", "metal"),
        _box("CupWarmer", (0.70, 0.36, 0.008), (0, (y0 + y1) / 2, 0.42 + 0.004), "#9EA4AA", "metal"),
    ]
    for side, x in (("L", -0.36), ("R", 0.36)):  # カップウォーマーの柵
        parts.append(_box(f"Rail{side}", (0.012, 0.36, 0.06), (x, (y0 + y1) / 2, 0.42 + 0.03), STAINLESS, "metal",
                          collision=False))
    parts.append(_box("RailBack", (0.73, 0.012, 0.06), (0, y1 - 0.01, 0.42 + 0.03), STAINLESS, "metal",
                      collision=False))
    for i, x in enumerate((-0.18, 0.18)):  # 抽出口（グループ）とポルタフィルター
        parts += [
            _box(f"GroupNeck{i}", (0.08, 0.05, 0.05), (x, -0.12, 0.33), STAINLESS, "metal", collision=False),
            _cyl(f"GroupHead{i}", (0.095, 0.095, 0.055), (x, -0.15, 0.295), STAINLESS, "metal"),
            _cyl(f"Portafilter{i}", (0.08, 0.08, 0.03), (x, -0.15, 0.253), "#9EA4AA", "metal"),
            _box(f"Handle{i}", (0.028, 0.085, 0.026), (x, -0.232, 0.247), BLACK, "plastic", rotation=[-8, 0, 0]),
            _cyl(f"Spout{i}", (0.014, 0.014, 0.02), (x, -0.15, 0.228), STAINLESS, "metal", collision=False),
        ]
    for i, x in enumerate((-0.33, 0.33)):  # スチームノズル
        parts += [_cyl(f"SteamKnob{i}", (0.03, 0.03, 0.03), (x, -0.115, 0.36), BLACK, "plastic"),
                  Part(f"SteamWand{i}", "cylinder", [0.012, 0.012, 0.16], [x, -0.14, 0.22], [12, 0, 0],
                       color=STAINLESS, finish="metal", collision=False)]
    parts.append(Part("WaterSpout", "cylinder", [0.014, 0.014, 0.08], [0, -0.13, 0.20], color=STAINLESS,
                      finish="metal", collision=False))
    return Product(slug="espresso_machine", name="業務用エスプレッソマシン（2 グループ）", shape_class="assembly",
                   category="fixture", dims=Dimensions(0.48, W, depth=D), mass_kg=65.0, static=True,
                   material="steel",
                   description="形はカフェの業務用エスプレッソマシンの一般的な構成（2 グループ、幅 750 mm・奥行き 550 mm・高さ 480 mm、"
                               "上にカップウォーマー、両側にスチームノズル、中央に給湯口、手前に受け皿）で、寸法・質量は代表値。",
                   tags=["カフェ", "エスプレッソマシン", "コーヒーマシン", "厨房機器", "espresso machine",
                         "coffee machine", "barista"],
                   photos=[], colors=Colors(label_base=STAINLESS), images=images, parts=parts)


# ---------------------------------------------------------------- メニューボード


def _menu(w_mm: float, h_mm: float, seed: int, text: bool = True) -> np.ndarray:
    """黒板のメニュー（チョークの文字と写真）。text=False は文字・写真を抜いた黒板。"""
    c = Canvas(w_mm, h_mm, None, CHALK, seed)
    _chalk_bg(c)
    if not text:
        return _face(c.array(), "paper", seed, 0.5, 6)
    chalk, yellow, pink = "#F2EFE6", "#F6D58E", "#F2A9B6"
    c.text(w_mm / 2, 70, "MENU", 72, chalk, 900, spacing=14)
    c.line([(w_mm / 2 - 260, 118), (w_mm / 2 + 260, 118)], chalk, 2.5)
    cols = [("COFFEE", [("ブレンド", "S 350 / M 400"), ("アメリカーノ", "S 380 / M 430"),
                        ("エスプレッソ", "320"), ("カフェラテ", "S 420 / M 470"), ("カプチーノ", "S 420 / M 470")]),
            ("TEA & OTHERS", [("紅茶", "380"), ("抹茶ラテ", "480"), ("ココア", "450"), ("オレンジジュース", "420")])]
    for k, (head, rows) in enumerate(cols):
        x0 = 60 + k * 400
        c.text(x0, 170, head, 34, yellow, 900, anchor="lm", spacing=3)
        for j, (s, p) in enumerate(rows):
            y = 225 + j * 50
            c.text(x0, y, s, 28, chalk, 700, anchor="lm")
            c.text(x0 + 350, y + 22, p, 20, pink, 700, anchor="rm")
    c.photo("latte", 860, 150, 1140, 400, shape="ellipse", crop=(0.1, 0.05, 0.9, 0.95))
    c.photo("coffee_beans", 870, 470, 1130, 740, radius=12)
    c.text(1000, 440, "本日のおすすめ", 28, yellow, 900)
    c.text(400, 520, "CAKE SET  +300", 34, yellow, 900)
    c.text(400, 575, "お好きなケーキとドリンクのセット", 24, chalk, 700)
    c.text(400, 660, "TAKE OUT OK", 30, pink, 900, spacing=4)
    c.text(400, 710, "※価格は税込みです", 18, chalk, 400)
    return _face(c.array(), "paper", seed, 0.5, 6)


def cafe_menu_board() -> Product:
    """壁掛けの黒板のメニューボード（木の枠、1200 × 800 mm）。背面を壁に付ける。

    写真: latte・coffee_beans（CC0。メニューに合成）
    """
    W, H, fd = 1.20, 0.80, 0.03
    bw, bh = 1.14, 0.74
    images = [_menu(bw * 1000, bh * 1000, 5721), _menu(bw * 1000, bh * 1000, 5721, text=False)]
    parts = [
        _wood("FrameTop", (W, fd, 0.03), (0, fd / 2, H - 0.015), WALNUT),
        _wood("FrameBottom", (W, fd, 0.03), (0, fd / 2, 0.015), WALNUT),
        _wood("FrameLeft", (0.03, fd, H - 0.06), (-W / 2 + 0.015, fd / 2, H / 2), WALNUT),
        _wood("FrameRight", (0.03, fd, H - 0.06), (W / 2 - 0.015, fd / 2, H / 2), WALNUT),
        _wood("Backer", (W - 0.06, 0.012, H - 0.06), (0, fd - 0.006, H / 2), WOOD_DARK),
        Part("Board", "box", [bw, 0.006, bh], [0, fd - 0.015, H / 2], color=CHALK, finish="matte",
             faces={"front": 0}, collision=False, material="wood", bevel=0, blank=1),
        _wood("ChalkLedge", (0.50, 0.03, 0.012), (0.25, -0.015, 0.036), WALNUT, collision=False),
    ]
    for p in parts:  # 背面（y = 0）が壁に付く
        p.center[1] -= fd
    return Product(slug="cafe_menu_board", name="カフェの壁掛けメニューボード（黒板）", shape_class="assembly",
                   category="environment", dims=Dimensions(H, W, depth=fd + 0.03), mass_kg=7.0, static=True,
                   material="wood",
                   description="形はカフェの壁に掛ける一般的な木枠の黒板のメニュー（外寸 1200 × 800 mm・厚さ 30 mm、下にチョーク置き）"
                               "で、寸法・質量は代表値。背面を壁に付ける。メニューの内容は架空。",
                   tags=["カフェ", "メニュー", "メニューボード", "黒板", "看板", "内装", "menu board", "chalkboard",
                         "cafe menu"],
                   photos=["latte", "coffee_beans"], colors=Colors(label_base=CHALK), images=images, parts=parts,
                   picture_places=CAFE_PLACES)


# ---------------------------------------------------------------- テーブル・椅子・ベンチソファ


def _tabletop(w_mm: float, d_mm: float, seed: int, base: str = WOOD) -> np.ndarray:
    return _grain(w_mm, d_mm, seed, base)


def cafe_table_round() -> Product:
    """カフェの丸テーブル（2 人用、直径 600 mm）。一本脚に十字の脚。"""
    D, H, t = 0.60, 0.72, 0.025
    images = [_tabletop(600, 600, 5731)]
    parts: list[Part] = [
        Part("Top", "cylinder", [D, D, t], [0, 0, H - t / 2], color=WOOD, finish="matte", faces={"top": 0},
             material="wood"),
        _cyl("Plate", (0.16, 0.16, 0.012), (0, 0, H - t - 0.006 - 0.006), BLACK, "metal"),
        _cyl("Column", (0.06, 0.06, H - t - 0.012 - 0.03), (0, 0, 0.03 + (H - t - 0.012 - 0.03) / 2), BLACK, "metal"),
        _cyl("Hub", (0.10, 0.10, 0.03), (0, 0, 0.015 + 0.01), BLACK, "metal"),
    ]
    for i in range(2):  # 十字の脚
        size = (0.52, 0.05, 0.02) if i == 0 else (0.05, 0.52, 0.02)
        parts.append(_box(f"Foot{i}", size, (0, 0, 0.01), BLACK, "metal"))
    return Product(slug="cafe_table_round", name="カフェの丸テーブル（2 人用）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, D, depth=D), mass_kg=12.0, static=False, material="wood",
                   description="形はカフェの 2 人用の一般的な丸テーブル（天板の直径 600 mm・高さ 720 mm、木の天板にスチールの一本脚と"
                               "十字の脚）で、寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["カフェ", "テーブル", "丸テーブル", "カフェテーブル", "家具", "cafe table", "round table",
                         "table"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


def cafe_table_square() -> Product:
    """カフェの角テーブル（2 人用、600 × 600 mm）。木の 4 本脚。"""
    W, H, t = 0.60, 0.72, 0.025
    images = [_tabletop(600, 600, 5741)]
    parts: list[Part] = [
        _wood("Top", (W, W, t), (0, 0, H - t / 2), WOOD, faces={"top": 0}),
    ]
    leg, apron = 0.04, 0.07
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        parts.append(_wood(f"Leg{i}", (leg, leg, H - t), (sx * (W / 2 - 0.04), sy * (W / 2 - 0.04), (H - t) / 2),
                           WOOD_DARK))
    inner = W - 0.08 - leg
    for name, size, c in (("ApronF", (inner, 0.02, apron), (0, -(W / 2 - 0.05), H - t - apron / 2)),
                          ("ApronB", (inner, 0.02, apron), (0, W / 2 - 0.05, H - t - apron / 2)),
                          ("ApronL", (0.02, inner, apron), (-(W / 2 - 0.05), 0, H - t - apron / 2)),
                          ("ApronR", (0.02, inner, apron), (W / 2 - 0.05, 0, H - t - apron / 2))):
        parts.append(_wood(name, size, c, WOOD_DARK, collision=False))
    return Product(slug="cafe_table_square", name="カフェの角テーブル（2 人用）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=W), mass_kg=11.0, static=False, material="wood",
                   description="形はカフェの 2 人用の一般的な角テーブル（天板 600 × 600 mm・高さ 720 mm、木の 4 本脚と幕板）で、"
                               "寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["カフェ", "テーブル", "角テーブル", "カフェテーブル", "家具", "cafe table", "square table",
                         "table"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


def cafe_chair() -> Product:
    """カフェの木の椅子（座面の高さ 450 mm）。正面（座る人の向き）は −Y、背もたれは +Y。"""
    W, D, H = 0.42, 0.48, 0.82
    seat_z, seat_t, leg = 0.45, 0.025, 0.03
    images = [_grain(420, 420, 5751, WOOD)]
    parts: list[Part] = [
        _wood("Seat", (W, 0.42, seat_t), (0, -0.02, seat_z - seat_t / 2), WOOD, faces={"top": 0}),
    ]
    fy, by = -0.02 - 0.21 + 0.03, -0.02 + 0.21 - 0.02
    for i, (x, y) in enumerate([(-W / 2 + 0.03, fy), (W / 2 - 0.03, fy)]):
        parts.append(_wood(f"FrontLeg{i}", (leg, leg, seat_z - seat_t), (x, y, (seat_z - seat_t) / 2), WOOD_DARK))
    back_h = H - (seat_z - seat_t)
    for i, x in enumerate((-W / 2 + 0.03, W / 2 - 0.03)):  # 後ろの脚は背もたれの柱まで通す
        parts += [_wood(f"BackLeg{i}", (leg, leg, seat_z - seat_t), (x, by, (seat_z - seat_t) / 2), WOOD_DARK),
                  _wood(f"BackPost{i}", (leg, leg, back_h), (x, by + 0.015, seat_z - seat_t + back_h / 2), WOOD_DARK,
                        rotation=[-4, 0, 0])]
    parts += [_wood("BackRestTop", (W - 0.06, 0.02, 0.09), (0, by + 0.03, H - 0.06), WOOD, rotation=[-4, 0, 0]),
              _wood("BackRestMid", (W - 0.06, 0.02, 0.05), (0, by + 0.022, seat_z + 0.13), WOOD, rotation=[-4, 0, 0],
                    collision=False)]
    for name, size, c in (("StretcherL", (0.02, 0.32, 0.02), (-W / 2 + 0.03, -0.01, 0.16)),
                          ("StretcherR", (0.02, 0.32, 0.02), (W / 2 - 0.03, -0.01, 0.16)),
                          ("StretcherF", (W - 0.08, 0.02, 0.02), (0, fy, 0.20))):
        parts.append(_wood(name, size, c, WOOD_DARK, collision=False))
    # 寸法（D）に合わせて奥行きの中心を 0 にそろえる
    ys = [p.center[1] - p.size[1] / 2 for p in parts] + [p.center[1] + p.size[1] / 2 for p in parts]
    mid = (min(ys) + max(ys)) / 2
    for p in parts:
        p.center[1] -= mid
    D = max(ys) - min(ys)
    return Product(slug="cafe_chair", name="カフェの木の椅子", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=round(D, 3)), mass_kg=4.5, static=False, material="wood",
                   description="形はカフェの一般的な木の椅子（座面の高さ 450 mm・幅 420 mm・全高 820 mm、横桟の背もたれ）で、"
                               "寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["カフェ", "椅子", "木の椅子", "ダイニングチェア", "家具", "cafe chair", "wooden chair",
                         "chair"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts)


def cafe_sofa_bench() -> Product:
    """壁際のベンチソファ（幅 1800 mm）。背面（+Y）を壁に付け、座面の高さ 450 mm。"""
    W, D, H = 1.80, 0.55, 0.85
    fabric, fabric_dark = "#6B4A3A", "#563B2E"
    parts: list[Part] = [
        _wood("Plinth", (W, 0.50, 0.30), (0, -0.025 + 0.0, 0.15), WALNUT),
        _fabric("SeatCushion", (W - 0.02, 0.50, 0.12), (0, -0.025, 0.30 + 0.06), fabric, bevel=0.02),
        _wood("BackPanel", (W, 0.05, H), (0, D / 2 - 0.025, H / 2), WALNUT),
        _fabric("BackCushion", (W - 0.04, 0.10, 0.38), (0, D / 2 - 0.05 - 0.05, 0.45 + 0.20), fabric_dark,
                rotation=[-8, 0, 0], bevel=0.025),
    ]
    for i, x in enumerate((-0.45, 0.45)):  # 背もたれの縫い目（区切り）
        parts.append(Part(f"Seam{i}", "box", [0.006, 0.006, 0.36], [x, D / 2 - 0.152, 0.65], [-8, 0, 0],
                          color=mix(fabric_dark, "#000000", 0.3), finish="matte", collision=False, material="fabric",
                          bevel=0))
    return Product(slug="cafe_sofa_bench", name="カフェの壁際ベンチソファ", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=45.0, static=True, material="fabric",
                   description="形はカフェの壁際に置く一般的なベンチソファ（幅 1800 mm・奥行き 550 mm・高さ 850 mm、座面の高さ 450 mm、"
                               "木の台に布張りの座面と背もたれ）で、寸法・質量は代表値。背面（+Y）を壁に付ける。",
                   tags=["カフェ", "ソファ", "ベンチソファ", "ベンチシート", "家具", "bench sofa", "banquette",
                         "sofa", "bench"],
                   photos=[], colors=Colors(label_base=fabric), images=[], parts=parts)


# ---------------------------------------------------------------- 返却台


def _return_sign(w_mm: float, h_mm: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    c = Canvas(w_mm, h_mm, None, CREAM, seed)
    c.gradient(0, 0, w_mm, h_mm, "#FBF6EC", "#EADFCB")
    c.rect(0, 0, w_mm, 70, fill="#4E342E")
    c.text(w_mm / 2, 36, "RETURN", 40, CREAM, 900, spacing=10)
    c.text(w_mm / 2, 120, "返却口", 58, "#4E342E", 900)
    c.text(w_mm / 2, 185, "トレー・食器はこちらへお返しください", 24, "#5D4037", 700)
    for k, s in enumerate(("飲み残し", "紙コップ", "トレー")):
        x = w_mm * (0.2 + 0.3 * k)
        c.rect(x - 90, 220, x + 90, 270, fill=("#8D6E63", "#C9A26B", "#6D8B74")[k], radius=8)
        c.text(x, 245, s, 24, "#FFFFFF", 800)
    blank = Canvas(w_mm, h_mm, None, CREAM, seed)
    blank.gradient(0, 0, w_mm, h_mm, "#FBF6EC", "#EADFCB")
    blank.rect(0, 0, w_mm, 70, fill="#4E342E")
    return _face(c.array(), "paper", seed, 0.5, 6), _face(blank.array(), "paper", seed, 0.5, 6)


def tray_return_station() -> Product:
    """カフェの返却台（トレー・食器を戻す棚、飲み残し入れ・ごみ入れ付き）。正面は −Y。"""
    W, D, H, top_z = 0.90, 0.45, 1.20, 0.90
    sign, blank = _return_sign(860, 290, 5761)
    t = 0.018
    parts: list[Part] = [
        _wood("SideL", (t, D, top_z), (-W / 2 + t / 2, 0, top_z / 2), WOOD_DARK),
        _wood("SideR", (t, D, top_z), (W / 2 - t / 2, 0, top_z / 2), WOOD_DARK),
        _wood("Back", (W - 2 * t, t, top_z), (0, D / 2 - t / 2, top_z / 2), WOOD_DARK),
        _wood("Kick", (W - 2 * t, D - t, 0.06), (0, -t / 2, 0.03), WALNUT),
        _wood("Top", (W, D, 0.03), (0, 0, top_z - 0.015), WALNUT),
    ]
    for i, z in enumerate((0.30, 0.56)):  # トレーを戻す棚（薄い板）
        parts.append(_wood(f"Shelf{i}", (W - 2 * t, D - t - 0.01, t), (0, -t / 2 - 0.005, z), WOOD))
    parts += [
        _wood("SignBoard", (W, 0.025, H - top_z), (0, D / 2 - 0.0125, top_z + (H - top_z) / 2), WALNUT),
        Part("Sign", "box", [0.86, 0.004, 0.29], [0, D / 2 - 0.025 - 0.002, top_z + (H - top_z) / 2],
             color=CREAM, finish="matte", faces={"front": 0}, collision=False, material="paper", bevel=0, blank=1),
        # 天板の上: 飲み残し入れ（ステンレスの角の器）・カップを捨てる口
        _box("Sink", (0.20, 0.20, 0.06), (-0.24, -0.04, top_z + 0.03), STAINLESS, "metal"),
        _box("SinkWater", (0.17, 0.17, 0.004), (-0.24, -0.04, top_z + 0.057), "#4A3426", "glossy", collision=False),
        _box("CupSlot", (0.20, 0.14, 0.012), (0.24, -0.04, top_z + 0.006), BLACK, "plastic"),
        _box("CupSlotHole", (0.13, 0.08, 0.002), (0.24, -0.04, top_z + 0.013), "#0E0E0E", "matte", collision=False),
    ]
    images = [sign, blank]
    return Product(slug="tray_return_station", name="カフェの返却台（トレー・食器の返却棚）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=40.0, static=True, material="wood",
                   description="形はセルフ式のカフェの一般的な返却台（幅 900 mm・奥行き 450 mm・天板の高さ 900 mm、天板に飲み残し入れと"
                               "カップを捨てる口、下にトレーを戻す 2 段の棚、奥に返却口の案内板）で、寸法・質量は代表値。案内の文面は架空。",
                   tags=["カフェ", "返却台", "返却口", "トレー返却", "ごみ箱", "店舗什器", "tray return",
                         "return station", "cafe"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts,
                   picture_places=[*CAFE_PLACES, "bakery", "convenience_store"])


# ---------------------------------------------------------------- 紙コップ（フタ付き）


def paper_cup_lid() -> Product:
    """カフェの紙コップ M サイズ（350 ml、飲み口付きのふた）。クラフト紙の帯に架空の店名。"""
    form = _hot_cup(0.108, 0.090, 0.060, lid_h=0.014)
    white, kraft, brown = "#FBFAF7", "#C9A577", "#4A2C1C"
    c = label_canvas(form, white, seed=5771)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#FFFFFF", "#EFEAE2")
    c.rect(0, H * 0.32, W, H * 0.80, fill=kraft)  # クラフト紙のスリーブ
    c.pattern(0, H * 0.32, W, H * 0.80, "stripes", mix(kraft, "#000000", 0.06), 3.0, 0.6)
    for x in (0.75 * W, 0.25 * W):
        c.ellipse(x - 13, H * 0.40, x + 13, H * 0.40 + 26, outline=brown, width=1.4)
        c.ellipse(x - 5, H * 0.40 + 7, x + 5, H * 0.40 + 19, fill=brown)
        c.text(x, H * 0.62, "CAFE", 8.0, brown, 900, spacing=1.2)
        c.text(x, H * 0.70, "coffee & bakery", 3.0, brown, 700)
        c.text(x, H * 0.16, "M", 6.0, brown, 900)
    c.vtext(0.5 * W, H * 0.36, "やけどに注意", 2.6, "#B3262B", 800)
    c.recycle(0.5 * W, H * 0.88, 4.5, "紙", brown, sub="カップ")
    label = finish(c.array(), "paper", 5771, 0.5)

    t = top_canvas(form, white, seed=5772)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FFFFFF", "#E2E2DE")
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline="#C9C9C5", width=1.2)
    t.ellipse(d * 0.10, d * 0.10, d * 0.90, d * 0.90, outline="#D6D6D2", width=0.6)
    t.rect(d / 2 - 9, d * 0.80, d / 2 + 9, d * 0.86, fill="#2B1A10", radius=1.6)
    t.ellipse(d / 2 - 1, d * 0.16 - 1, d / 2 + 1, d * 0.16 + 1, fill="#3A3A38")
    top = t.array()
    return Product(slug="paper_cup_lid", name="カフェの紙コップ M サイズ（フタ付き）", category="beverage", mass_kg=0.37,
                   capacity_ml=350, material="paper",
                   description="形はカフェのテイクアウト用の一般的な紙コップ M サイズ（350 ml、口径 90 mm・底径 60 mm・高さ 108 mm）に、"
                               "飲み口のある樹脂のふた（高さ 14 mm、ふた込みで約 122 mm）をかぶせたもので、寸法・質量（中身込み）は代表値。店名は架空。",
                   tags=["カフェ", "紙コップ", "コーヒー", "テイクアウト", "フタ付き", "paper cup", "coffee cup",
                         "takeout cup", "cup with lid"],
                   photos=[], colors=Colors(cap=white, label_base=white), **revolve(form, label=label, top=top))


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    cafe_order_counter, espresso_machine, cafe_menu_board, cafe_table_round, cafe_table_square, cafe_chair,
    cafe_sofa_bench, tray_return_station, paper_cup_lid)}
