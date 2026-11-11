"""架空の商品のデザイン: ファミレスの客席まわり・配膳の備品。

products.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の備品の一般的な値にする。
正面は −Y（お客さま側。デシャップ台はホール側）。床置きの重い什器はキネマティック（static）、ワゴン・トレー・スタンドは動かせる。
物を置く面（天板・棚板）は薄い水平の板にする（商品を並べるツールが棚板として見つけられるように）。
店の文面のある面は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .paint import Canvas, mix
from .products import INK, WARM_WHITE, _box, _cyl, _face, _lamp

RESTAURANT_PLACES = ["restaurant"]  # ファミレスの文面が合う場所
STAINLESS, STAINLESS_DARK, BLACK = "#C4C8CC", "#9EA4AA", "#2A2B2E"
WOOD, WOOD_DARK = "#B98A57", "#6E4A2C"
RED, CREAM = "#B8322A", "#FBF6EC"


# ---------------------------------------------------------------- ドリンクバー


def _drink_bar_front(w_mm: float, h_mm: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """ドリンクバーの台の腰板（木目調に案内）と、文字を抜いた無地。"""
    def base() -> Canvas:
        c = Canvas(w_mm, h_mm, None, WOOD, seed)
        c.gradient(0, 0, w_mm, h_mm, mix(WOOD, "#FFFFFF", 0.10), mix(WOOD, "#000000", 0.08))
        y = 8.0
        while y < h_mm:
            c.line([(0, y), (w_mm * 0.5, y + c.rng.uniform(-3, 3)), (w_mm, y + c.rng.uniform(-3, 3))],
                   mix(WOOD, WOOD_DARK, c.rng.uniform(0.15, 0.3)), c.rng.uniform(0.6, 1.4))
            y += c.rng.uniform(10, 24)
        c.rect(0, h_mm - 60, w_mm, h_mm, fill=WOOD_DARK)
        return c

    blank = base()
    c = base()
    cx = w_mm / 2
    c.rect(cx - 520, 90, cx + 520, 400, fill=CREAM, outline=RED, width=8, radius=12)
    c.text(cx, 160, "DRINK BAR", 72, RED, 900, spacing=10)
    c.text(cx, 240, "ドリンクバー", 48, INK, 900)
    c.text(cx, 310, "グラス・カップはお一人さまひとつずつお使いください", 26, INK, 700)
    c.text(cx, 360, "おかわり自由 ／ ホット・アイス", 24, mix(RED, INK, 0.4), 700)
    return _face(c.array(), "paper", seed, 0.5, 6), _face(blank.array(), "paper", seed, 0.5, 6)


def _dispenser_panel(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    """ジュースのディスペンサーの正面（味ごとのボタン 6 つ）。"""
    c = Canvas(w_mm, h_mm, None, "#E9ECEF", seed)
    c.gradient(0, 0, w_mm, h_mm, "#F7F8F9", "#C9CED3")
    c.rect(0, 0, w_mm, 70, fill="#1F5FA8")
    c.text(w_mm / 2, 35, "SOFT DRINK", 30, "#FFFFFF", 900, spacing=4)
    flavors = [("オレンジ", "#F29A1F"), ("メロン", "#4FB04A"), ("コーラ", "#5A2E1E"), ("ジンジャー", "#D9B24A"),
               ("ウーロン茶", "#9C5B2A"), ("乳酸飲料", "#F2F2F2")]
    bw = (w_mm - 40) / 3 - 16
    for i, (s, col) in enumerate(flavors):
        x0 = 28 + (i % 3) * (w_mm - 40) / 3
        y0 = 100 + (i // 3) * 150
        c.rect(x0, y0, x0 + bw, y0 + 120, fill=col, outline="#888C90", width=3, radius=10)
        c.text(x0 + bw / 2, y0 + 60, s, 22, INK if col == "#F2F2F2" else "#FFFFFF", 900, max_w=bw - 10)
    c.text(w_mm / 2, h_mm - 40, "ボタンを押している間だけ出ます", 20, INK, 700)
    return _face(c.array(), "plastic", seed, 0.5, 6)


def _coffee_panel(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    """コーヒーマシンの正面（タッチパネルとメニュー）。"""
    c = Canvas(w_mm, h_mm, None, BLACK, seed)
    c.gradient(0, 0, w_mm, h_mm, "#3A3C40", "#151618")
    c.rect(30, 30, w_mm - 30, 260, fill="#0E1A22", outline="#5A5E63", width=3, radius=8)
    c.text(w_mm / 2, 60, "HOT / ICE", 22, "#B3E5FC", 900, spacing=3)
    bw = (w_mm - 90) / 2 - 10
    for i, s in enumerate(("ブレンド", "アメリカン", "カフェラテ", "カプチーノ", "ココア", "紅茶")):
        x0 = 45 + (i % 2) * (w_mm - 90) / 2
        y0 = 90 + (i // 2) * 55
        c.rect(x0, y0, x0 + bw, y0 + 44, fill=("#6D4C41", "#8D6E63", "#A1887F")[i % 3], radius=6)
        c.text(x0 + bw / 2, y0 + 22, s, 16, "#FFFFFF", 800, max_w=bw - 6)
    c.text(w_mm / 2, 310, "COFFEE", 30, "#E0C9A6", 900, spacing=6)
    c.text(w_mm / 2, 355, "カップを置いてから押してください", 13, "#CFCFCF", 700, max_w=w_mm - 30)
    c.rect(w_mm / 2 - 70, 385, w_mm / 2 + 70, h_mm - 20, fill="#0B0C0D", radius=10)  # 抽出口のくぼみ
    return _face(c.array(), "screen", seed, 0.6, 6)


def _ice_panel(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    c = Canvas(w_mm, h_mm, None, "#E9ECEF", seed)
    c.gradient(0, 0, w_mm, h_mm, "#F7F8F9", "#C9CED3")
    c.rect(0, 0, w_mm, 70, fill="#3E8EC9")
    c.text(w_mm / 2, 35, "ICE", 34, "#FFFFFF", 900, spacing=8)
    c.ellipse(w_mm / 2 - 60, 120, w_mm / 2 + 60, 240, fill="#2C6FA3", outline="#1C4E78", width=4)
    c.text(w_mm / 2, 180, "PUSH", 24, "#FFFFFF", 900)
    c.text(w_mm / 2, 290, "こおり", 30, INK, 900)
    c.rect(30, 340, w_mm - 30, 470, fill="#DDE3E8", outline="#9AA3AB", width=3, radius=10)
    c.text(w_mm / 2, 385, "グラスを", 20, "#3A4A58", 800)
    c.text(w_mm / 2, 425, "当ててください", 20, "#3A4A58", 800, max_w=w_mm - 70)
    return _face(c.array(), "plastic", seed, 0.5, 6)


def drink_bar() -> Product:
    """ファミレスのドリンクバー（幅 1800 mm）。台の上に左からグラス置き・ジュースのディスペンサー・氷・コーヒーマシン。"""
    W, D, top_z = 1.80, 0.65, 0.90
    body_h = top_z - 0.03 - 0.08
    front, blank = _drink_bar_front(1760, 780, 7101)
    images = [front, blank, _dispenser_panel(440, 460, 7102), _coffee_panel(360, 460, 7103),
              _ice_panel(300, 540, 7104)]
    parts: list[Part] = [
        _box("Plinth", (W - 0.06, D - 0.08, 0.08), (0, 0.02, 0.04), BLACK, "matte"),
        Part("Body", "box", [W, D - 0.02, body_h], [0, 0.01, 0.08 + body_h / 2], color=WOOD, finish="matte",
             material="wood"),
        Part("FrontPanel", "box", [1.76, 0.006, 0.78], [0, -D / 2 + 0.017, 0.08 + body_h / 2], color=WOOD,
             finish="matte", faces={"front": 0}, collision=False, material="wood", bevel=0, blank=1),
        # 天板はグラス置きと機械の側で分ける（グラス置きは物を並べる面になる）
        _box("TopGlasses", (0.50, D, 0.03), (-0.65, 0, top_z - 0.015), "#E6E2DA", "matte"),
        _box("TopMachines", (1.30, D, 0.03), (0.25, 0, top_z - 0.015), "#E6E2DA", "matte"),
        # 奥の立ち上がり（機械の背面を覆う高さ。機械が背より高いので上の棚は付けない）
        _box("Backsplash", (W, 0.02, 0.80), (0, D / 2 - 0.01, top_z + 0.40), "#D9D5CC", "matte"),
        _box("BacksplashCap", (W, 0.04, 0.02), (0, D / 2 - 0.02, top_z + 0.81), WOOD, "matte"),
        _box("GlassMat", (0.44, 0.40, 0.006), (-0.65, -0.06, top_z + 0.003), "#3A3D42", "plastic", collision=False),
    ]
    back = D / 2 - 0.02  # 機械の背面（立ち上がりの手前）
    # ジュースのディスペンサー（x −0.15）。下は空けてグラスを置く
    jx, jw, jd, jh = -0.15, 0.46, 0.50, 0.68
    jy = back - jd / 2
    parts += [
        _box("JuiceBody", (jw, jd, jh - 0.18), (jx, jy, top_z + 0.18 + (jh - 0.18) / 2), "#D9DDE1", "metal",
             {"front": 2}),
        _box("JuiceBack", (jw, 0.18, 0.18), (jx, back - 0.09, top_z + 0.09), "#B9BEC3", "metal"),
        _box("JuiceDrip", (jw - 0.04, jd - 0.20, 0.02), (jx, jy - 0.09, top_z + 0.01), "#6E7378", "metal"),
    ]
    for i in range(6):
        nx = jx - jw / 2 + 0.06 + i * (jw - 0.12) / 5
        parts.append(_cyl(f"JuiceNozzle{i}", (0.022, 0.022, 0.03), (nx, jy - 0.10, top_z + 0.165), STAINLESS_DARK,
                          collision=False))
    # 氷のディスペンサー（x 0.25）
    ix, iw, idp, ih = 0.25, 0.30, 0.50, 0.76
    iy = back - idp / 2
    parts += [
        _box("IceBody", (iw, idp, ih - 0.22), (ix, iy, top_z + 0.22 + (ih - 0.22) / 2), "#D9DDE1", "metal",
             {"front": 4}),
        _box("IceBack", (iw, 0.18, 0.22), (ix, back - 0.09, top_z + 0.11), "#B9BEC3", "metal"),
        _box("IceChute", (0.08, 0.08, 0.06), (ix, iy - 0.10, top_z + 0.19), STAINLESS_DARK, "metal",
             collision=False),
        _box("IceDrip", (iw - 0.04, idp - 0.20, 0.02), (ix, iy - 0.09, top_z + 0.01), "#6E7378", "metal"),
    ]
    # コーヒーマシン（x 0.65）
    cx, cw, cd, ch = 0.65, 0.36, 0.48, 0.66
    cy = back - cd / 2
    parts += [
        _box("CoffeeBody", (cw, cd, ch - 0.20), (cx, cy, top_z + 0.20 + (ch - 0.20) / 2), BLACK, "plastic",
             {"front": 3}),
        _box("CoffeeBack", (cw, 0.20, 0.20), (cx, back - 0.10, top_z + 0.10), "#1E1F22", "plastic"),
        _box("CoffeeDrip", (cw - 0.06, cd - 0.22, 0.015), (cx, cy - 0.10, top_z + 0.0075), "#55595E", "metal"),
        _cyl("CoffeeSpout", (0.03, 0.03, 0.03), (cx, cy - 0.10, top_z + 0.185), STAINLESS, collision=False),
    ]
    return Product(slug="drink_bar", name="ファミレスのドリンクバー（ジュース・氷・コーヒー 1800 mm）",
                   shape_class="assembly", category="fixture", dims=Dimensions(top_z + ih, W, depth=D),
                   mass_kg=160.0, static=True, material="wood",
                   description="形はファミリーレストランのセルフのドリンクバーの一般的な構成（台の幅 1800 mm・奥行き 650 mm・天板の高さ "
                               "900 mm、左からグラス置き・6 種のジュースのディスペンサー（幅 460 mm）・氷のディスペンサー（幅 300 mm）・"
                               "コーヒーマシン（幅 360 mm）、奥に高さ 800 mm の立ち上がり）で、寸法・質量は代表値。案内の文面・"
                               "ボタンの表示は架空。",
                   tags=["ファミレス", "ドリンクバー", "ドリンクディスペンサー", "コーヒーマシン", "製氷機", "セルフサービス",
                         "飲食店", "drink bar", "drink dispenser", "soda fountain", "self service", "family restaurant"],
                   photos=[], colors=Colors(label_base=WOOD), images=images, parts=parts,
                   picture_places=RESTAURANT_PLACES)


# ---------------------------------------------------------------- 受付表のスタンド


def _waiting_sheet(w_mm: float, h_mm: float, seed: int, text: bool = True) -> np.ndarray:
    """順番待ちの受付表（名前・人数・席の希望の欄）。text=False は罫線も抜いた白い紙。"""
    c = Canvas(w_mm, h_mm, None, "#FFFFFF", seed)
    c.gradient(0, 0, w_mm, h_mm, "#FFFFFF", "#F1F1EE")
    c.rect(0, 0, w_mm, 12, RED)  # 上端の帯（刷り込みの見出し。無地の紙にも残る）
    if not text:
        return _face(c.array(), "paper", seed, 0.4, 4)
    c.text(w_mm / 2, 6, "WAITING LIST", 7, "#FFFFFF", 800)
    c.text(w_mm / 2, 22, "ご案内のお待ち表", 15, INK, 900)
    c.text(w_mm / 2, 40, "お名前・人数をご記入のうえ、お呼びするまでお待ちください", 6.5, "#555555", 700, max_w=w_mm - 16)
    top, row_h, n = 52, 16, 12
    x0, x1 = 8, w_mm - 8
    for k in range(n + 1):
        c.line([(x0, top + k * row_h), (x1, top + k * row_h)], "#9A9A9A", 0.6)
    for x, s in ((0.0, "No."), (0.10, "お名前"), (0.55, "人数"), (0.70, "テーブル/カウンター"), (1.0, "")):
        xx = x0 + x * (x1 - x0)
        c.line([(xx, top), (xx, top + n * row_h)], "#9A9A9A", 0.6)
        if s:
            c.text(xx + 3, top + row_h / 2, s, 6.0, INK, 800, anchor="lm")
    for k in range(1, n):
        c.text(x0 + 0.05 * (x1 - x0), top + k * row_h + row_h / 2, str(k), 6.5, "#555555", 700)
    for k, (name, num) in enumerate((("ヤマダ", "2"), ("スズキ", "4"), ("タナカ", "3"))):  # 記入例（架空）
        y = top + (k + 1) * row_h + row_h / 2
        c.text(x0 + 0.13 * (x1 - x0), y, name, 8, "#1F3E7A", 500, anchor="lm")
        c.text(x0 + 0.62 * (x1 - x0), y, num, 8, "#1F3E7A", 500)
        if k < 2:
            c.line([(x0 + 2, y), (x1 - 2, y + 1)], "#7A7A7A", 0.5)  # ご案内済みの線
    return _face(c.array(), "paper", seed, 0.4, 4)


def _waiting_header(w_mm: float, h_mm: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    def base() -> Canvas:
        c = Canvas(w_mm, h_mm, None, RED, seed)
        c.gradient(0, 0, w_mm, h_mm, mix(RED, "#FFFFFF", 0.08), mix(RED, "#000000", 0.08))
        return c

    blank, c = base(), base()
    c.text(w_mm / 2, h_mm * 0.38, "いらっしゃいませ", 22, "#FFFFFF", 900)
    c.text(w_mm / 2, h_mm * 0.74, "こちらにお名前をご記入ください", 12, CREAM, 800)
    return _face(c.array(), "paper", seed, 0.4, 4), _face(blank.array(), "paper", seed, 0.4, 4)


def waiting_board() -> Product:
    """入口の順番待ちの受付表のスタンド（高さ約 1100 mm）。丸い台座に支柱、手前へ傾けた記入台に受付表・ペン、奥に案内の札。"""
    base_d, pole_h = 0.36, 0.95
    bw, bd, tilt = 0.32, 0.40, -25.0  # 記入台（奥を上げて手前へ傾ける）
    a = math.radians(-tilt)
    ca, sa = math.cos(a), math.sin(a)

    def on_desk(v: float, up: float) -> list[float]:
        """記入台の面の上の点（奥へ v、面から up）。"""
        return [0.0, v * ca - up * sa, pole_h + 0.01 + v * sa + up * ca]

    sheet, sheet_blank = _waiting_sheet(250, 260, 7111), _waiting_sheet(250, 260, 7111, text=False)
    header, header_blank = _waiting_header(320, 110, 7112)
    images = [sheet, sheet_blank, header, header_blank]
    back_y, back_z = on_desk(bd / 2, 0)[1:]
    parts: list[Part] = [
        _cyl("Base", (base_d, base_d, 0.025), (0, 0, 0.0125), BLACK, "metal"),
        _cyl("Pole", (0.04, 0.04, pole_h - 0.025), (0, 0, 0.025 + (pole_h - 0.025) / 2), BLACK, "metal"),
        _box("Desk", (bw, bd, 0.015), on_desk(0, 0), WOOD_DARK, "matte", rotation=[-tilt, 0, 0]),
        Part("Sheet", "box", [0.25, 0.26, 0.002], on_desk(-0.02, 0.0085), [-tilt, 0, 0], color="#FFFFFF",
             finish="matte", faces={"top": 0}, collision=False, material="paper", bevel=0, blank=1),
        _box("Clip", (0.10, 0.025, 0.008), on_desk(0.15, 0.012), STAINLESS, "metal", rotation=[-tilt, 0, 0],
             collision=False),
        Part("Pen", "cylinder", [0.010, 0.010, 0.14], on_desk(-0.02, 0.014), [0, 90, 20], color="#1F3E7A",
             finish="plastic", collision=False),
        _box("HeaderPost", (0.02, 0.02, 0.10), (0, back_y - 0.01, back_z + 0.05), BLACK, "metal", collision=False),
        Part("Header", "box", [0.32, 0.006, 0.11], [0, back_y - 0.01, back_z + 0.155], color=RED, finish="matte",
             faces={"front": 2, "back": 3}, collision=False, material="paper", bevel=0, blank=3),
    ]
    return Product(slug="waiting_board", name="入口の順番待ち受付表のスタンド", shape_class="assembly", category="fixture",
                   dims=Dimensions(round(back_z + 0.21, 3), max(bw, base_d), depth=base_d), mass_kg=6.0, static=False,
                   material="steel",
                   description="形は飲食店の入口に置く一般的な順番待ちの記入台（直径 360 mm の丸い台座に支柱、高さ約 950 mm に 320×400 mm の"
                               "手前へ傾けた記入台、受付表・ペン、奥に案内の札）で、寸法・質量は代表値。受付表・札の文面と記入例は架空。"
                               "動かせる（static ではない）。",
                   tags=["ファミレス", "受付", "受付表", "順番待ち", "ウェイティングボード", "記入台", "入口", "飲食店",
                         "waiting list", "waiting board", "host stand", "sign-in stand", "restaurant entrance"],
                   photos=[], colors=Colors(label_base="#FFFFFF"), images=images, parts=parts,
                   picture_places=RESTAURANT_PLACES)


# ---------------------------------------------------------------- 配膳ワゴン


def serving_wagon() -> Product:
    """ステンレスの配膳ワゴン（3 段、800 × 500 mm、キャスター 4 つ）。押し手は +X の端。"""
    W, D, H = 0.80, 0.50, 0.88
    wheel_d, wheel_w = 0.10, 0.03
    caster_h = wheel_d + 0.03  # 車輪＋金具
    t = 0.02
    shelves_z = (caster_h + 0.03, caster_h + 0.36, H - t / 2)
    sw, sd = W - 0.04, D - 0.04
    parts: list[Part] = []
    for i, z in enumerate(shelves_z):
        parts.append(_box(f"Shelf{i}", (sw, sd, t), (0, 0, z), STAINLESS, "metal"))
        rz = z + t / 2 + 0.0175  # 縁の中心（棚の上に 35 mm 立ち上がる）
        for side, (size, c) in (("F", ((sw, 0.012, 0.035), (0, -sd / 2 + 0.006, rz))),
                                ("B", ((sw, 0.012, 0.035), (0, sd / 2 - 0.006, rz))),
                                ("L", ((0.012, sd - 0.024, 0.035), (-sw / 2 + 0.006, 0, rz))),
                                ("R", ((0.012, sd - 0.024, 0.035), (sw / 2 - 0.006, 0, rz)))):
            parts.append(_box(f"Shelf{i}Rim{side}", size, c, STAINLESS, "metal"))
    post_h = H - caster_h
    for sx in (-1, 1):
        for sy in (-1, 1):
            k = f"{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}"
            x, y = sx * (W / 2 - 0.0125), sy * (D / 2 - 0.0125)
            wy = sy * (D / 2 - wheel_d / 2)  # 首振りの車輪は柱より内側（奥行きからはみ出さない）
            parts += [
                _cyl(f"Post{k}", (0.025, 0.025, post_h), (x, y, caster_h + post_h / 2), STAINLESS_DARK),
                _box(f"CasterMount{k}", (0.025, 0.05, 0.03), (x, y - sy * 0.0125, caster_h - 0.015), "#55595E", "metal"),
                Part(f"Wheel{k}", "cylinder", [wheel_d, wheel_d, wheel_w], [x, wy, wheel_d / 2], [0, 90, 0],
                     color=BLACK, finish="matte", material="rubber"),
            ]
    # 押し手（+X の端、天板より少し上）
    hx = W / 2 + 0.05
    hz = H + 0.04
    parts += [
        Part("Handle", "cylinder", [0.025, 0.025, D - 0.025], [hx, 0, hz], [90, 0, 0], color=STAINLESS,
             finish="metal"),
        _box("HandleArmF", (0.06, 0.02, 0.06), (W / 2 + 0.02, -(D / 2 - 0.0125), hz - 0.02), STAINLESS, "metal",
             collision=False),
        _box("HandleArmB", (0.06, 0.02, 0.06), (W / 2 + 0.02, D / 2 - 0.0125, hz - 0.02), STAINLESS, "metal",
             collision=False),
    ]
    xs = [p.center[0] - p.size[0] / 2 for p in parts] + [p.center[0] + p.size[0] / 2 for p in parts]
    mid = (min(xs) + max(xs)) / 2
    for p in parts:  # 横幅の中心を 0 にそろえる
        p.center[0] -= mid
    return Product(slug="serving_wagon", name="配膳ワゴン（ステンレス 3 段・キャスター付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(hz + 0.0125, 3), round(max(xs) - min(xs), 3), depth=D),
                   mass_kg=16.0, static=False, material="steel",
                   description="形は飲食店・厨房の一般的なステンレスのサービスワゴン（棚 3 段・外寸 800 × 500 mm・天板の高さ 880 mm、"
                               "縁の立ち上がり 35 mm、直径 100 mm のキャスター 4 つ、片側に押し手）で、寸法・質量は代表値。"
                               "動かせる（static ではない）。",
                   tags=["配膳ワゴン", "サービスワゴン", "ワゴン", "台車", "キャスター", "厨房", "飲食店", "ファミレス",
                         "serving cart", "service trolley", "utility cart", "kitchen cart", "restaurant"],
                   photos=[], colors=Colors(label_base=STAINLESS), images=[], parts=parts)


# ---------------------------------------------------------------- 配膳トレー


def _tray_top(w_mm: float, d_mm: float, seed: int, color: str) -> np.ndarray:
    """滑り止めの細かい凹凸のある樹脂の盆の上面。"""
    c = Canvas(w_mm, d_mm, 4, color, seed)
    c.gradient(0, 0, w_mm, d_mm, mix(color, "#FFFFFF", 0.22), mix(color, "#000000", 0.25))
    c.pattern(0, 0, w_mm, d_mm, "dots", mix(color, "#000000", 0.14), 6.0, 1.0)
    return _face(c.array(), "plastic", seed, 0.4, 6)


def serving_tray() -> Product:
    """配膳トレー（角盆 450 × 330 mm、滑り止め付き）。縁は低い立ち上がり。"""
    W, D, H = 0.45, 0.33, 0.022
    color = "#4A2E22"
    t, rim = 0.006, 0.012
    images = [_tray_top(450, 330, 7131, color)]
    parts: list[Part] = [
        Part("Base", "box", [W - 0.004, D - 0.004, t], [0, 0, t / 2], color=color, finish="plastic", faces={"top": 0},
             material="plastic", bevel=0.002),
    ]
    for side, (size, c) in (("F", ((W, rim, H), (0, -D / 2 + rim / 2, H / 2))),
                            ("B", ((W, rim, H), (0, D / 2 - rim / 2, H / 2))),
                            ("L", ((rim, D - 2 * rim, H), (-W / 2 + rim / 2, 0, H / 2))),
                            ("R", ((rim, D - 2 * rim, H), (W / 2 - rim / 2, 0, H / 2)))):
        parts.append(Part(f"Rim{side}", "box", list(size), list(c), color=mix(color, "#000000", 0.1),
                          finish="plastic", material="plastic", bevel=0.003))
    return Product(slug="serving_tray", name="配膳トレー（角盆 450×330 mm）", shape_class="assembly", category="household",
                   dims=Dimensions(H, W, depth=D), mass_kg=0.55, static=False, material="plastic",
                   description="形は飲食店の一般的な配膳用の角盆（外寸 450 × 330 mm・高さ 22 mm、滑り止め付きの樹脂、"
                               "縁の幅 12 mm）で、寸法・質量は代表値。上に食器を載せられる。",
                   tags=["トレー", "配膳トレー", "お盆", "角盆", "飲食店", "ファミレス", "食器", "serving tray", "tray",
                         "restaurant tray"],
                   photos=[], colors=Colors(label_base=color), images=images, parts=parts)


# ---------------------------------------------------------------- デシャップ台


def deshap_counter() -> Product:
    """デシャップ台（厨房と客席の間の料理の受け渡し台、1800 mm）。ステンレスの天板・下棚、上の棚の下に保温ランプ。

    正面 −Y がホール側、+Y が厨房側。上の棚のホール側の縁に伝票差し。
    """
    W, D, top_z = 1.80, 0.60, 0.90
    upper_z = 1.45  # 上の棚の中心
    t = 0.03
    parts: list[Part] = [
        _box("Top", (W, D, t), (0, 0, top_z - t / 2), STAINLESS, "metal"),
        _box("TopEdgeF", (W, 0.012, 0.04), (0, -D / 2 - 0.006, top_z - 0.02), STAINLESS_DARK, "metal",
             collision=False),
        _box("UnderShelf", (W - 0.08, D - 0.08, 0.02), (0, 0, 0.20), STAINLESS, "metal"),
        _box("UpperShelf", (W, 0.35, t), (0, 0, upper_z), STAINLESS, "metal"),
        _box("TicketRail", (W - 0.10, 0.02, 0.04), (0, -0.175 - 0.01, upper_z - 0.005), STAINLESS_DARK, "metal",
             collision=False),
    ]
    leg_h = top_z - t - 0.03
    for sx in (-1, 1):
        for sy in (-1, 1):
            k = f"{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}"
            x, y = sx * (W / 2 - 0.03), sy * (D / 2 - 0.03)
            parts += [_box(f"Leg{k}", (0.04, 0.04, leg_h), (x, y, 0.03 + leg_h / 2), STAINLESS_DARK, "metal"),
                      _cyl(f"Foot{k}", (0.05, 0.05, 0.03), (x, y, 0.015), "#55595E")]
    post_h = upper_z - t / 2 - top_z
    for i, x in enumerate((-W / 2 + 0.015, W / 2 - 0.015)):  # 上の棚の支柱（両端、天板の中央の線）
        parts.append(_box(f"UpperPost{i}", (0.03, 0.03, post_h), (x, 0.0, top_z + post_h / 2), STAINLESS_DARK,
                          "metal"))
    lights = []
    for i, x in enumerate((-0.60, 0.0, 0.60)):  # 保温ランプ（電球色、天板の受け渡し面を照らす）
        parts.append(_box(f"LampHousing{i}", (0.50, 0.14, 0.04), (x, 0, upper_z - t / 2 - 0.02), BLACK, "metal",
                          collision=False))
        lamp, lux = _lamp(f"Lamp{i}", (0.46, 0.10, 0.006), (x, 0, upper_z - t / 2 - 0.043), "#FFD9A0", 6000.0,
                          WARM_WHITE)
        parts.append(lamp)
        lights.append(lux)
    for i, x in enumerate((-0.45, 0.05, 0.40)):  # 伝票（ホール側の伝票差しに 3 枚）
        parts.append(_box(f"Ticket{i}", (0.07, 0.002, 0.11), (x, -0.175 - 0.022, upper_z - 0.06), "#FFFFFF", "matte",
                          collision=False))
    return Product(slug="deshap_counter", name="デシャップ台（料理の受け渡し台・保温ランプ付き 1800 mm）",
                   shape_class="assembly", category="fixture", dims=Dimensions(upper_z + t / 2, W, depth=D + 0.012),
                   mass_kg=70.0, static=True, material="steel",
                   description="形は飲食店の厨房とホールの間に置く一般的なデシャップ台（ステンレスの作業台 幅 1800 mm・奥行き 600 mm・"
                               "天板の高さ 900 mm と下棚、天板の上 550 mm に奥行き 350 mm の上棚、その下に電球色の保温ランプ 3 灯、"
                               "上棚のホール側に伝票差し）で、寸法・質量は代表値。正面 −Y がホール側。",
                   tags=["デシャップ", "デシャップ台", "パス", "受け渡し台", "ディッシュアップ", "保温ランプ", "厨房", "飲食店",
                         "ファミレス", "pass", "pass-through counter", "heat lamp", "food warmer", "kitchen pass",
                         "restaurant kitchen"],
                   photos=[], colors=Colors(label_base=STAINLESS), images=[], parts=parts, lights=lights)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    drink_bar, waiting_board, serving_wagon, serving_tray, deshap_counter)}
