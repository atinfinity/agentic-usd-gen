"""架空の商品のデザイン: 店舗の設備（監視カメラなど）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の製品の一般的な値にする。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .paint import Canvas, finish, trim_safe
from .products import INK, _box, _cyl


def security_camera_dome() -> Product:
    """天井に付けるドーム型の監視カメラ。原点はドームの下端で、上面（z = H）が天井に付く。"""
    white, trim, smoke, black = "#F3F3F1", "#D9DBDD", "#4A5058", "#141414"
    H, D = 0.105, 0.140
    parts: list[Part] = [_cyl("MountBase", (D, D, 0.012), (0, 0, H - 0.006), white, "plastic")]
    # 本体（まっすぐな円筒の下に、すぼまる肩を 2 段）
    parts += [_cyl("Housing", (0.132, 0.132, 0.026), (0, 0, H - 0.012 - 0.013), white, "plastic"),
              _cyl("Shoulder0", (0.126, 0.126, 0.007), (0, 0, 0.0635), white, "plastic"),
              _cyl("Shoulder1", (0.118, 0.118, 0.005), (0, 0, 0.0575), white, "plastic")]
    z_bot = 0.055
    parts.append(_cyl("TrimRing", (0.112, 0.112, 0.006), (0, 0, z_bot - 0.003), trim, "plastic"))
    # スモークのドーム（下向きの半球。中のカメラが透けて見える）
    R, zc = 0.048, 0.050
    parts.append(Part("Dome", "dome", [2 * R, 2 * R, R], [0, 0, zc - R / 2], [180, 0, 0], color=smoke, finish="glass"))
    # 中のカメラ（球状の台座と、前下がり 45° を向くレンズ）
    a = math.radians(135)
    dy, dz = -math.sin(a), math.cos(a)  # レンズの向き (0, dy, dz) = 前・下
    g = (0.0, 0.0, 0.032)
    r = 0.019  # 球状の台座（上下 2 つの半球）
    parts += [Part("GimbalUpper", "dome", [2 * r, 2 * r, r], [0, 0, g[2] + r / 2], color=black, finish="plastic",
                   collision=False),
              Part("GimbalLower", "dome", [2 * r, 2 * r, r], [0, 0, g[2] - r / 2], [180, 0, 0], color=black,
                   finish="plastic", collision=False)]
    parts += [
              Part("LensBarrel", "cylinder", [0.022, 0.022, 0.016], [0, g[1] + dy * 0.024, g[2] + dz * 0.024],
                   [135, 0, 0], color="#0C0C0C", finish="plastic", collision=False),
              Part("LensGlass", "cylinder", [0.014, 0.014, 0.002], [0, g[1] + dy * 0.0325, g[2] + dz * 0.0325],
                   [135, 0, 0], color="#1E2A44", finish="glossy", collision=False)]
    for k in range(6):  # 赤外線 LED（レンズのまわり）
        t = 2 * math.pi * k / 6
        ox, oz = 0.0105 * math.cos(t), 0.0105 * math.sin(t)
        # レンズ面に沿った 2 方向: X と、(0, -dz, dy)
        parts.append(Part(f"IrLed{k}", "cylinder", [0.003, 0.003, 0.002],
                          [ox, g[1] + dy * 0.0315 - dz * oz, g[2] + dz * 0.0315 + dy * oz], [135, 0, 0],
                          color="#5A1820", finish="glossy", collision=False))
    return Product(slug="security_camera_dome", name="ドーム型 監視カメラ（天井付け）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, D, depth=D), mass_kg=0.6, static=True, mount="ceiling",
                   description="形は店舗の天井に付ける一般的なドーム型の防犯カメラ（直径 140 mm・高さ 105 mm）で、寸法・質量は代表値。"
                               "上面が天井に付く向き。スモークのドームは下向きの半球で、中のレンズは前下がり 45° を向く。",
                   tags=["監視カメラ", "防犯カメラ", "ドームカメラ", "天井", "店舗設備", "security camera",
                         "surveillance camera", "dome camera", "CCTV"],
                   photos=[], images=[], parts=parts)


# ---------------------------------------------------------------- 電子レンジ（業務用）


def microwave_commercial() -> Product:
    W, D, H = 0.422, 0.476, 0.337
    w, h = W * 1000, H * 1000
    c = Canvas(w, h, 1600 / w, "#C9CCD0", 2611)
    c.gradient(0, 0, w, h, "#D8DBDF", "#B9BDC2")
    for k in range(int(h / 1.2)):  # ヘアライン
        c.line([(0, k * 1.2), (w, k * 1.2)], "#C2C6CB", 0.15)
    # 扉と窓
    c.rect(8, 8, 300, h - 8, fill="#2B2D30", radius=6)
    c.rect(28, 34, 272, h - 52, fill="#0D0E10", radius=4)
    c.gradient(30, 36, 270, 120, "#3A3F46", "#0D0E10")
    c.pattern(28, 34, 272, h - 52, "dots", "#202226", 2.4, 0.5)
    c.text(154, h - 30, "業務用 1500W", 8, "#C9CCD0", 700)
    # 操作パネル
    x0, x1 = 310, w - 10
    xc = (x0 + x1) / 2
    c.rect(x0, 12, x1, h - 12, fill="#2A2C30", radius=6)
    c.rect(x0 + 8, 24, x1 - 8, 58, fill="#0B1A10", radius=3)
    c.text(xc, 41, "1:30", 18, "#59F08A", 800)
    c.text(xc, 70, "出力  1500W", 6.5, "#E6E6E6", 700)
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "とりけし", "0", "+10秒"]
    for i, k in enumerate(keys):
        bx = x0 + 8 + (i % 3) * 30
        by = 82 + (i // 3) * 30
        c.rect(bx, by, bx + 26, by + 25, fill="#44474D", radius=4)
        c.text(bx + 13, by + 12.5, k, 9 if len(k) == 1 else 5.6, "#FFFFFF", 800)
    c.rect(x0 + 8, 208, x1 - 8, 240, fill="#2F6DB5", radius=5)
    c.text(xc, 224, "あたため", 11, "#FFFFFF", 900)
    c.rect(x0 + 8, 248, x1 - 8, 284, fill="#D14B2E", radius=5)
    c.text(xc, 266, "スタート", 12, "#FFFFFF", 900)
    c.text(xc, h - 26, "扉を閉めてから", 5.2, "#CCCCCC", 600)
    c.text(xc, h - 18, "スタートしてください", 5.2, "#CCCCCC", 600)
    front = trim_safe(finish(c.array(), "metal", 2611, 0.5))
    foot = 0.012
    parts = [_box("Body", (W, D, H), (0, 0, foot + H / 2), "#C4C7CB", "metal", {"front": 0}),
             _box("Handle", (0.022, 0.03, 0.24), (-W / 2 + 0.292, -D / 2 - 0.015, foot + H / 2), "#A8ACB1", "metal"),
             _box("HandlePostTop", (0.016, 0.02, 0.016), (-W / 2 + 0.292, -D / 2 - 0.006, foot + H / 2 + 0.11),
                  "#A8ACB1", "metal", collision=False),
             _box("HandlePostBottom", (0.016, 0.02, 0.016), (-W / 2 + 0.292, -D / 2 - 0.006, foot + H / 2 - 0.11),
                  "#A8ACB1", "metal", collision=False),
             _box("Vent", (0.30, 0.004, 0.03), (0, D / 2 + 0.002, foot + H - 0.04), "#7A7E84", "metal",
                  collision=False)]
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_cyl(f"Foot{k}", (0.03, 0.03, foot), (sx * (W / 2 - 0.035), sy * (D / 2 - 0.04), foot / 2),
                          "#1A1A1A", "plastic"))
    return Product(slug="microwave_commercial", name="業務用 電子レンジ 1500W", shape_class="assembly", category="fixture",
                   dims=Dimensions(round(H + foot, 4), W, depth=round(D + 0.03, 4)), mass_kg=30.0, static=True,
                   material="steel",
                   description="形はコンビニのレジ裏で使う一般的な業務用電子レンジ（ステンレス、テンキー式、1500W）で、寸法・質量は代表値。"
                               "操作パネルは架空。",
                   tags=["電子レンジ", "業務用", "レンジ", "店舗設備", "microwave", "commercial microwave"], photos=[],
                   colors=Colors(label_base="#C4C7CB"), images=[front], parts=parts)


# ---------------------------------------------------------------- マルチコピー機


def multifunction_copier() -> Product:
    gray, light, dark = "#E4E5E7", "#EEEFF0", "#2A2C30"
    accent = "#1F6F9C"
    # 本体の前面（幅 620 × 高さ 1000 mm）
    w, h = 620.0, 1000.0
    c = Canvas(w, h, 1600 / h, gray, 2621)
    c.gradient(0, 0, w, h, "#EEEFF0", "#DADCDF")
    c.rect(20, 40, w - 20, 250, fill="#C9CCD0", radius=6)  # 排紙口のくぼみ
    c.rect(40, 150, w - 40, 240, fill="#3A3D42", radius=4)
    c.text(w / 2, 90, "コピー ・ プリント ・ スキャン", 26, accent, 900)
    c.text(w / 2, 128, "排紙口  印刷した紙はこちらに出ます", 13, INK, 700)
    c.rect(0, 268, w, 276, fill=accent)
    for i, (sz, lab) in enumerate((("A4", "A4 ヨコ"), ("B4", "B4"), ("A3", "A3"), ("B5", "B5 ヨコ"))):
        y0 = 300 + i * 160
        c.rect(14, y0, w - 14, y0 + 148, outline="#B5B8BC", width=1.5, radius=4)
        c.rect(w / 2 - 90, y0 + 18, w / 2 + 90, y0 + 40, fill="#BFC2C6", radius=10)  # 取っ手
        c.rect(30, y0 + 70, 120, y0 + 110, fill="#FFFFFF", outline="#9A9DA2", width=1)
        c.text(75, y0 + 90, lab, 15, INK, 800)
        c.text(w - 40, y0 + 90, f"トレイ {i + 1}", 13, "#6A6E74", 700, anchor="rm")
    c.text(w / 2, h - 30, "用紙の補充は店員がおこないます", 12, "#6A6E74", 600)
    body = trim_safe(finish(c.array(), "metal", 2621, 0.4))
    # 操作画面
    sw, sh = 300.0, 200.0
    s = Canvas(sw, sh, 1400 / sw, "#FFFFFF", 2622)
    s.gradient(0, 0, sw, sh, "#FFFFFF", "#E8F0F6")
    s.rect(0, 0, sw, 24, fill=accent)
    s.text(10, 12, "メニューを選んでください", 11, "#FFFFFF", 800, anchor="lm")
    tiles = [("コピー", "#2F6DB5"), ("プリント", "#2E8B57"), ("スキャン", "#8D5A2B"),
             ("写真プリント", "#C0392B"), ("行政サービス", "#5B4B8A"), ("チケット", "#D17A1E")]
    for i, (t, col) in enumerate(tiles):
        x0 = 10 + (i % 3) * 95
        y0 = 34 + (i // 3) * 74
        s.rect(x0, y0, x0 + 88, y0 + 66, fill=col, radius=6)
        s.text(x0 + 44, y0 + 33, t, 11 if len(t) <= 4 else 9, "#FFFFFF", 900)
    s.text(sw / 2, sh - 8, "画面にふれて操作してください", 7, INK, 600)
    screen = trim_safe(finish(s.array(), "screen", 2622, 0.5))
    # 料金の支払い機（幅 300 × 高さ 1100 mm）
    pw, ph = 300.0, 1100.0
    p = Canvas(pw, ph, 1600 / ph, gray, 2623)
    p.gradient(0, 0, pw, ph, "#EEEFF0", "#DADCDF")
    p.rect(0, 0, pw, 60, fill=accent)
    p.text(pw / 2, 30, "料金のお支払い", 20, "#FFFFFF", 900)
    p.rect(30, 110, pw - 30, 190, fill="#FFFFFF", outline="#B5B8BC", width=1.5, radius=6)
    p.text(pw / 2, 132, "ご利用金額", 12, INK, 700)
    p.rect(50, 145, pw - 50, 180, fill="#0B1A10", radius=3)
    p.text(pw / 2, 162, "60円", 18, "#59F08A", 800)
    p.text(pw / 2, 230, "硬貨投入口", 13, INK, 800)
    p.rect(pw / 2 - 40, 250, pw / 2 + 40, 262, fill="#1A1A1A", radius=3)
    p.text(pw / 2, 310, "紙幣投入口（千円札）", 13, INK, 800)
    p.rect(40, 330, pw - 40, 350, fill="#1A1A1A", radius=4)
    p.rect(40, 400, pw - 40, 500, fill="#FFFFFF", outline="#B5B8BC", width=1.5, radius=6)
    p.text(pw / 2, 430, "電子マネー", 13, INK, 800)
    p.text(pw / 2, 465, "ここにタッチ", 15, accent, 900)
    p.text(pw / 2, 560, "レシート", 12, INK, 700)
    p.rect(70, 575, pw - 70, 583, fill="#1A1A1A", radius=2)
    p.text(pw / 2, 650, "おつり・返却", 12, INK, 700)
    p.rect(80, 665, pw - 80, 745, fill="#2A2C30", radius=8)
    p.rect(110, 760, pw - 110, 780, fill="#BFC2C6", radius=6)
    p.text(pw / 2, 772, "返却", 10, INK, 800)
    p.text(pw / 2, ph - 40, NOTICE, 9, "#8A8E94", 500)
    pay = trim_safe(finish(p.array(), "metal", 2623, 0.4))
    parts = [_box("Plinth", (0.60, 0.62, 0.05), (0, 0.01, 0.025), "#3A3C40", "matte"),
             _box("Cabinet", (0.62, 0.66, 1.0), (0, 0, 0.55), gray, "plastic", {"front": 0}),
             _box("Scanner", (0.62, 0.62, 0.10), (0, 0.02, 1.10), light, "plastic"),
             _box("DocFeeder", (0.52, 0.50, 0.08), (0, 0.04, 1.19), "#D9DBDE", "plastic"),
             _box("DocTray", (0.34, 0.26, 0.012), (0, 0.02, 1.245), "#C9CCD0", "plastic", rotation=[-8, 0, 0],
                  collision=False),
             _box("OutputTray", (0.20, 0.32, 0.012), (-0.40, 0.0, 0.86), "#C9CCD0", "plastic", rotation=[0, 10, 0]),
             _box("PanelArm", (0.06, 0.10, 0.04), (0.12, -0.34, 1.07), dark, "plastic", collision=False),
             _box("Screen", (0.30, 0.035, 0.20), (0.12, -0.40, 1.13), dark, "screen", {"front": 1}, [-35, 0, 0]),
             _box("PayStation", (0.30, 0.50, 1.10), (0.47, 0.08, 0.55), gray, "plastic", {"front": 2})]
    return Product(slug="multifunction_copier", name="マルチコピー機（料金支払い機付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(1.269, 1.12, depth=0.802), mass_kg=220.0, static=True,
                   material="steel",
                   description="形はコンビニに置く一般的なマルチコピー機（コピー・プリント・スキャンの複合機に、硬貨・紙幣・電子マネーの支払い機を横付け）で、"
                               "寸法・質量は代表値。画面と表示は架空。",
                   tags=["マルチコピー機", "複合機", "コピー機", "プリンター", "店舗什器", "multifunction printer",
                         "copier", "MFP"], photos=[], colors=Colors(label_base=gray), images=[body, screen, pay],
                   parts=parts)


# ---------------------------------------------------------------- ATM


def atm_kiosk() -> Product:
    body_c, dark, accent = "#ECEDEE", "#26282C", "#1E8A6E"
    W = 0.52
    # 下の筐体の前面（520 × 900 mm）
    lw, lh = 520.0, 900.0
    lo = Canvas(lw, lh, 1400 / lh, body_c, 2631)
    lo.gradient(0, 0, lw, lh, "#F2F3F4", "#D8DADD")
    lo.rect(0, 0, lw, 14, fill=accent)
    lo.text(lw / 2, 120, "ATM", 90, accent, 900)
    lo.text(lw / 2, 200, "24時間 365日 ご利用いただけます", 17, INK, 800)
    lo.text(lw / 2, 240, "お引出し ・ お預入れ ・ 残高照会", 15, "#555A60", 700)
    for k in range(10):  # 通気口
        lo.rect(60, lh - 140 + k * 8, lw - 60, lh - 136 + k * 8, fill="#BFC2C6", radius=2)
    lo.text(lw / 2, lh - 30, NOTICE, 9, "#8A8E94", 500)
    lower = trim_safe(finish(lo.array(), "metal", 2631, 0.4))
    # 操作台（カード・通帳・紙幣）の上面（520 × 300 mm）
    cw, ch = 520.0, 300.0
    co = Canvas(cw, ch, 1400 / cw, "#D4D6D9", 2632)
    co.gradient(0, 0, cw, ch, "#E2E4E6", "#C9CCD0")
    co.rect(40, 30, 300, 270, fill="#3A3D42", radius=10)  # 紙幣の入出金口
    co.rect(60, 60, 280, 240, fill="#15171A", radius=6)
    co.text(170, 20, "紙幣  入出金口", 13, INK, 800)
    co.rect(330, 60, 490, 110, fill="#2A2C30", radius=6)
    co.rect(345, 80, 475, 88, fill="#0A0A0A", radius=2)
    co.text(410, 45, "カード", 13, INK, 800)
    co.ellipse(470, 64, 482, 76, fill="#3CD16E")
    co.rect(330, 150, 490, 200, fill="#2A2C30", radius=6)
    co.rect(345, 170, 475, 178, fill="#0A0A0A", radius=2)
    co.text(410, 135, "通帳", 13, INK, 800)
    co.rect(330, 230, 490, 270, fill="#2A2C30", radius=6)
    co.rect(355, 246, 465, 252, fill="#0A0A0A", radius=2)
    co.text(410, 222, "明細書", 11, INK, 800)
    console = trim_safe(finish(co.array(), "metal", 2632, 0.4))
    # 画面（360 × 270 mm）
    sw, sh = 360.0, 270.0
    s = Canvas(sw, sh, 1400 / sw, "#FFFFFF", 2633)
    s.gradient(0, 0, sw, sh, "#FFFFFF", "#E6F3EE")
    s.rect(0, 0, sw, 34, fill=accent)
    s.text(sw / 2, 17, "いらっしゃいませ", 15, "#FFFFFF", 900)
    s.text(sw / 2, 56, "ご希望のお取引を選んでください", 12, INK, 800)
    btn = [("お引出し", "#2F6DB5"), ("お預入れ", "#2E8B57"), ("残高照会", "#8D5A2B"), ("お振込み", "#C0392B")]
    for i, (t, col) in enumerate(btn):
        x0 = 20 + (i % 2) * 165
        y0 = 80 + (i // 2) * 80
        s.rect(x0, y0, x0 + 155, y0 + 68, fill=col, radius=8)
        s.text(x0 + 77, y0 + 34, t, 16, "#FFFFFF", 900)
    s.text(sw / 2, sh - 14, "画面にふれて操作してください", 9, INK, 600)
    screen = trim_safe(finish(s.array(), "screen", 2633, 0.5))
    # 上の看板（560 × 120 mm）
    gw, gh = 560.0, 120.0
    g = Canvas(gw, gh, 1400 / gw, accent, 2634)
    g.gradient(0, 0, gw, gh, "#25A582", "#17735B")
    g.text(150, gh / 2, "ATM", 62, "#FFFFFF", 900)
    g.text(400, 44, "24時間", 26, "#FFFFFF", 900)
    g.text(400, 82, "ご利用いただけます", 17, "#FFFFFF", 800)
    sign = trim_safe(finish(g.array(), "metal", 2634, 0.4))
    parts = [_box("LowerCabinet", (W, 0.70, 0.90), (0, 0, 0.45), body_c, "plastic", {"front": 0}),
             _box("Console", (W, 0.30, 0.04), (0, -0.21, 0.93), "#D4D6D9", "plastic", {"top": 1}, [-12, 0, 0]),
             _box("UpperBody", (W, 0.40, 0.58), (0, 0.15, 1.19), body_c, "plastic"),
             _box("ScreenBezel", (0.40, 0.04, 0.31), (0, -0.07, 1.13), dark, "plastic", rotation=[-15, 0, 0]),
             _box("Screen", (0.36, 0.01, 0.27), (0, -0.095, 1.13), "#101114", "screen", {"front": 2}, [-15, 0, 0],
                  collision=False),
             _box("PrivacyLeft", (0.02, 0.34, 0.58), (-W / 2 - 0.01, -0.12, 1.19), dark, "plastic"),
             _box("PrivacyRight", (0.02, 0.34, 0.58), (W / 2 + 0.01, -0.12, 1.19), dark, "plastic"),
             _box("Hood", (W + 0.04, 0.36, 0.03), (0, -0.11, 1.495), dark, "plastic"),
             _box("Sign", (0.56, 0.42, 0.12), (0, 0.05, 1.57), accent, "plastic", {"front": 3}),
             _cyl("Camera", (0.018, 0.018, 0.01), (0, -0.25, 1.475), "#0A0A0A", "glossy", collision=False)]
    return Product(slug="atm_kiosk", name="ATM（コンビニ設置型）", shape_class="assembly", category="fixture",
                   dims=Dimensions(1.63, 0.56, depth=0.72), mass_kg=300.0, static=True, material="steel",
                   description="形はコンビニに置く一般的な ATM（画面・カード／通帳口・紙幣の入出金口・のぞき見防止の仕切り・看板）で、"
                               "寸法・質量は代表値。銀行名は付けず、画面と表示は架空。",
                   tags=["ATM", "現金自動預け払い機", "銀行", "店舗設備", "atm", "cash machine"], photos=[],
                   colors=Colors(label_base=body_c), images=[lower, console, screen, sign], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    security_camera_dome, microwave_commercial, multifunction_copier, atm_kiosk)}
