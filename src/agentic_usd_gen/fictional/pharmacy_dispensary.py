"""架空の商品のデザイン: 調剤薬局の調剤室の機器と什器（錠剤分包機・散剤分包機・散薬台・電子天秤・錠剤のピッキング棚・
麻薬金庫・クリーンベンチ・調剤用の流し台・調剤カート・調剤監査台・薬袋プリンター）。

pharmacy_fixtures.py と同じく、実在の商品名・メーカー名・ロゴは使わず、形と寸法は同じ種類の機器の一般的な値にする。
正面は −Y（薬剤師が立つ側）。床置きの什器はキネマティック（static）、卓上の機器は動く剛体。
物を並べる面は薄い水平の板にする（agentic-sim-world-gen の fill が棚板として見つけられるように）。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .drug_fixtures import GRAY, GREEN, NAVY, _shelf
from .paint import Canvas, mix
from .pharmacy_fixtures import CREAM, PHARMACY_TAGS
from .products import COOL_WHITE, INK, _box, _cyl, _face, _lamp

WHITE, DARK, STEEL = "#FFFFFF", "#2B2E31", "#C3C8CD"
BODY = "#EEF0F2"
ROOM = ["調剤室", "調剤機器", *PHARMACY_TAGS, "dispensary"]


def _plate(w_mm: float, h_mm: float, seed: int, bg: str = BODY) -> Canvas:
    """機器の前板の下地（上から下へ明るさが変わり、下の縁が少し暗い）。"""
    c = Canvas(w_mm, h_mm, None, bg, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(bg, WHITE, 0.4), mix(bg, "#000000", 0.06))
    c.rect(0, h_mm - max(2.0, h_mm * 0.03), w_mm, h_mm, fill=mix(bg, "#000000", 0.18))
    return c


def _title(c: Canvas, text: str, sub: str, y: float, size: float, color: str = NAVY) -> None:
    c.text(c.w_mm / 2, y, text, size, color, 900, max_w=c.w_mm * 0.9)
    c.text(c.w_mm / 2, y + size * 1.1, sub, size * 0.45, INK, 700, max_w=c.w_mm * 0.9)


def _vents(c: Canvas, x0: float, y0: float, x1: float, n: int, gap: float) -> None:
    for k in range(n):
        y = y0 + k * gap
        c.rect(x0, y, x1, y + gap * 0.4, fill="#A9AFB5", radius=gap * 0.2)


# ---------------------------------------------------------------- 錠剤分包機


def tablet_packaging_machine() -> Product:
    W, D, H = 0.80, 0.75, 1.75
    pw, ph = 760.0, 950.0
    c = Canvas(pw, ph, None, "#2E3338", 13401)  # 上の前板（カセットの並ぶ窓）
    c.gradient(0, 0, pw, ph, "#E9ECEF", "#D3D8DD")
    c.rect(0, 0, pw, 90, fill=NAVY)
    c.text(pw / 2, 45, "錠剤分包機  TP-48", 46, WHITE, 900)
    c.rect(30, 120, pw - 30, ph - 40, fill="#1E2328", radius=10)
    colors = ["#E86A5C", "#F2A93B", "#F2D44A", "#6CC08A", "#4FA3D9", "#B07CC6"]
    for r in range(8):
        for k in range(6):
            x0, y0 = 55 + k * 113, 145 + r * 97
            col = colors[(r + k) % len(colors)]
            c.rect(x0, y0, x0 + 98, y0 + 82, fill="#F2F4F6", radius=5)
            c.rect(x0 + 6, y0 + 6, x0 + 92, y0 + 26, fill=col, radius=3)
            c.text(x0 + 49, y0 + 16, f"{r * 6 + k + 1:02d}", 15, WHITE, 900)
            c.rect(x0 + 18, y0 + 36, x0 + 80, y0 + 74, fill=mix(col, "#FFFFFF", 0.65), radius=4)
    upper = _face(c.array(), "plastic", 13401, 0.6, 6)
    sc = Canvas(260, 170, None, "#0D1B2A", 13402)  # 操作の画面
    sc.gradient(0, 0, 260, 170, "#16304D", "#0A1522")
    sc.rect(0, 0, 260, 30, fill=GREEN)
    sc.text(130, 15, "分包中", 18, WHITE, 900)
    sc.text(130, 62, "12 / 28 包", 30, WHITE, 900)
    sc.rect(20, 95, 240, 115, outline="#BFD3F0", width=2, radius=4)
    sc.rect(22, 97, 22 + 216 * 12 / 28, 113, fill="#5CFF8A", radius=3)
    sc.text(130, 145, "朝食後  7日分", 16, "#BFD3F0", 800)
    screen = _face(sc.array(), "screen", 13402, 0.6, 3)
    lo = _plate(760, 520, 13403)  # 下の前板（分包紙の扉）
    lo.rect(60, 60, 700, 470, outline="#9EA4AA", width=3, radius=8)
    lo.ellipse(280, 160, 480, 360, outline="#9EA4AA", width=3)
    lo.ellipse(350, 230, 410, 290, fill="#9EA4AA")
    lo.text(380, 410, "分包紙", 34, INK, 900)
    lo.rect(600, 240, 640, 300, fill="#8E9399", radius=6)
    lower = _face(lo.array(), "plastic", 13403, 0.6, 6)
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.06), (0, 0, 0.03), GRAY, "matte"),
        _box("Body", (W, D, H - 0.06), (0, 0, 0.06 + (H - 0.06) / 2), BODY, "plastic"),
        _box("UpperPanel", (pw / 1000, 0.004, ph / 1000), (0, -D / 2 - 0.002, H - 0.04 - ph / 2000), BODY, "plastic",
             {"front": 0}, collision=False),
        _box("LowerPanel", (0.76, 0.004, 0.52), (0, -D / 2 - 0.002, 0.08 + 0.26), BODY, "plastic", {"front": 2},
             collision=False),
        Part("Screen", "box", [0.26, 0.006, 0.17], [0.22, -D / 2 - 0.003, 0.70], color="#0D1B2A", finish="screen",
             faces={"front": 1}, collision=False, bevel=0),
        _box("OutletTray", (0.30, 0.18, 0.012), (-0.18, -D / 2 - 0.09, 0.66), STEEL, "metal"),
        _box("OutletLip", (0.30, 0.012, 0.03), (-0.18, -D / 2 - 0.174, 0.681), STEEL, "metal"),
        _box("Outlet", (0.20, 0.006, 0.04), (-0.18, -D / 2 - 0.003, 0.70), DARK, "matte", collision=False),
    ]
    return Product(slug="tablet_packaging_machine", name="錠剤分包機 カセット 48 個", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.18), mass_kg=260.0, static=True,
                   material="steel",
                   description="形は調剤薬局の調剤室に置く一般的な全自動の錠剤分包機（幅 800 mm・奥行き 930 mm・高さ 1750 mm、"
                               "本体の奥行き 750 mm に出口の受け皿が前へ 180 mm 出る、前に錠剤のカセット 48 個の窓・操作の画面・分包した薬の出口の受け皿、下に分包紙の扉）で、"
                               "寸法・質量は代表値。扉は開かない。表示の文字と型番は架空。",
                   tags=["錠剤分包機", "分包機", "一包化", "調剤機器", *ROOM, "tablet packaging machine",
                         "unit dose packaging machine"], photos=[],
                   colors=Colors(label_base=BODY), images=[upper, screen, lower], parts=parts)


# ---------------------------------------------------------------- 散剤分包機


def powder_packaging_machine() -> Product:
    W, D = 0.65, 0.60
    deck = 0.90  # 円盤を載せる台の上面
    tower_d, tower_h = 0.15, 0.35
    H = deck + 0.02 + tower_h
    hd = _plate(610, 300, 13411)
    hd.rect(0, 0, 610, 70, fill=NAVY)
    hd.text(305, 35, "散剤分包機", 40, WHITE, 900)
    hd.rect(40, 100, 300, 230, fill="#0B1A10", radius=6)
    hd.text(170, 140, "28 包", 40, "#5CFF8A", 900)
    hd.text(170, 195, "1包 0.5g", 26, "#5CFF8A", 800)
    for k, (lab, col) in enumerate((("開始", "#3BAA5C"), ("停止", "#E53935"), ("清掃", "#4FA3D9"))):
        x = 380 + k * 75
        hd.ellipse(x - 28, 120, x + 28, 176, fill=col)
        hd.text(x, 205, lab, 20, INK, 800)
    head = _face(hd.array(), "plastic", 13411, 0.6, 6)
    fr = _plate(610, 820, 13412)
    fr.rect(40, 60, 570, 760, outline="#9EA4AA", width=3, radius=8)
    fr.rect(160, 120, 450, 150, fill="#4A4F55", radius=6)
    fr.text(305, 190, "分包した薬の出口", 26, INK, 800)
    _vents(fr, 120, 560, 490, 6, 28)
    front = _face(fr.array(), "plastic", 13412, 0.6, 6)
    yt = D / 2 - tower_d / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.06), (0, 0, 0.03), GRAY, "matte"),
        _box("Cabinet", (W, D, deck - 0.06), (0, 0, 0.06 + (deck - 0.06) / 2), BODY, "plastic"),
        _box("CabinetFront", (0.61, 0.004, 0.82), (0, -D / 2 - 0.002, 0.06 + 0.41), BODY, "plastic", {"front": 1},
             collision=False),
        _box("Deck", (W, D, 0.02), (0, 0, deck + 0.01), "#DADDE1", "metal"),
        _cyl("Dish", (0.40, 0.40, 0.035), (0, -0.05, deck + 0.02 + 0.0175), STEEL),
        _cyl("DishGroove", (0.34, 0.34, 0.002), (0, -0.05, deck + 0.02 + 0.036), "#9EA4AA", "metal", False),
        _box("Tower", (W, tower_d, tower_h), (0, yt, deck + 0.02 + tower_h / 2), BODY, "plastic"),
        _box("TowerFront", (0.61, 0.004, 0.30), (0, D / 2 - tower_d - 0.002, deck + 0.02 + tower_h / 2), BODY,
             "plastic", {"front": 0}, collision=False),
        _cyl("Hopper", (0.10, 0.10, 0.12), (0.17, -0.05, deck + 0.02 + 0.10), "#E2E5E9", "plastic"),
        _box("HopperArm", (0.04, 0.17, 0.03), (0.17, 0.08, deck + 0.02 + 0.17), "#E2E5E9", "plastic"),
        _box("Outlet", (0.29, 0.006, 0.03), (0, -D / 2 - 0.003, 0.06 + 0.82 - 0.135), DARK, "matte",
             collision=False),
    ]
    return Product(slug="powder_packaging_machine", name="散剤分包機（円盤式）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D + 0.006), mass_kg=120.0, static=True,
                   material="steel",
                   description="形は調剤薬局の調剤室に置く一般的な円盤式の散剤分包機（幅 650 mm・奥行き 600 mm・高さ約 1270 mm、"
                               "台の上に粉薬をならす円盤とホッパー、奥に操作部、前に分包した薬の出口）で、寸法・質量は代表値。"
                               "表示の文字は架空。",
                   tags=["散剤分包機", "分包機", "粉薬", "散剤", "調剤機器", *ROOM, "powder packaging machine",
                         "powder dispensing machine"], photos=[],
                   colors=Colors(label_base=BODY), images=[head, front], parts=parts)


# ---------------------------------------------------------------- 散薬台（局所排気のフード付き）


def powder_dispensing_table() -> Product:
    W, D, H = 1.20, 0.70, 1.80
    top = 0.85  # 作業台の上面
    hood_d, hood_h = 0.35, 0.25
    hf = _plate(1180, 230, 13421)
    hf.rect(0, 0, 1180, 60, fill=GREEN)
    hf.text(590, 30, "散薬調剤台  局所排気", 34, WHITE, 900)
    _vents(hf, 120, 95, 1060, 4, 30)
    hood = _face(hf.array(), "plastic", 13421, 0.6, 6)
    cf = _plate(1180, 800, 13422, CREAM)
    for k in range(4):  # 左に引き出し 4 段、右に開き戸 2 枚
        y0 = 30 + k * 190
        cf.rect(30, y0, 560, y0 + 170, outline="#B9BEC4", width=3, radius=4)
        cf.rect(220, y0 + 70, 370, y0 + 95, fill="#8E9399", radius=10)
    for k in range(2):
        x0 = 600 + k * 285
        cf.rect(x0, 30, x0 + 265, 770, outline="#B9BEC4", width=3, radius=4)
        cf.rect(x0 + (220 if k == 0 else 25), 330, x0 + (240 if k == 0 else 45), 470, fill="#8E9399", radius=8)
    cab = _face(cf.array(), "paper", 13422, 0.8, 6)
    yh = D / 2 - hood_d / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.06, 0.06), (0, -0.01, 0.03), GRAY, "matte"),
        _box("Cabinet", (W, D - 0.02, top - 0.03 - 0.06), (0, 0.01, 0.06 + (top - 0.09) / 2), CREAM, "matte"),
        _box("CabinetFront", (1.18, 0.004, top - 0.11), (0, -D / 2 + 0.008, 0.06 + (top - 0.09) / 2),
             CREAM, "matte", {"front": 1}, collision=False),
        _box("Worktop", (W, D, 0.03), (0, 0, top - 0.015), "#E4E0D8", "plastic"),
        _box("BackPanel", (W, 0.03, H - top), (0, D / 2 - 0.015, top + (H - top) / 2), CREAM, "matte"),
        _box("Hood", (W, hood_d, hood_h), (0, yh, H - hood_h / 2), BODY, "plastic"),
        _box("HoodFront", (1.18, 0.004, 0.23), (0, D / 2 - hood_d - 0.002, H - hood_h / 2), BODY, "plastic",
             {"front": 0}, collision=False),
        _shelf("UpperShelf", W - 0.10, 0.16, (0, D / 2 - 0.03 - 0.08, 1.25), CREAM),
    ]
    for side, x in (("L", -W / 2 + 0.004), ("R", W / 2 - 0.004)):  # 粉が舞わないよう左右にガラスの袖
        parts.append(Part(f"SideGuard{side}", "box", [0.008, hood_d, H - hood_h - top],
                          [x, yh, top + (H - hood_h - top) / 2], color="#EAF2F5", finish="glass", thin_walled=True))
    lamp, lux = _lamp("HoodLight", (W - 0.20, 0.04, 0.008), (0, D / 2 - hood_d + 0.05, H - hood_h - 0.0045),
                      "#F4F8FF", 4000.0, COOL_WHITE)
    parts.append(lamp)
    return Product(slug="powder_dispensing_table", name="散薬台 局所排気のフード付き 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.002), mass_kg=110.0, static=True,
                   material="wood", lights=[lux],
                   description="形は調剤薬局で粉薬（散剤）を量る一般的な散薬台（幅 1200 mm・奥行き 700 mm・作業台の高さ 850 mm・"
                               "全高 1800 mm、上に局所排気のフードと照明、左右にガラスの袖、奥に散剤の瓶を並べる棚、"
                               "下に引き出しと開き戸の収納）で、寸法・質量は代表値。引き出しと戸は開かない。"
                               "電子天秤は含まない（electronic_balance を作業台に置く）。",
                   tags=["散薬台", "調剤台", "作業台", "局所排気", "散剤", *ROOM, "powder dispensing table",
                         "dispensing workbench"], photos=[],
                   colors=Colors(label_base=CREAM), images=[hood, cab], parts=parts)


# ---------------------------------------------------------------- 電子天秤（風防付き）


def electronic_balance() -> Product:
    W, D = 0.22, 0.32
    base_h, shield_h = 0.08, 0.22
    H = base_h + shield_h
    lc = Canvas(200, 50, None, "#E9ECEF", 13431)
    lc.gradient(0, 0, 200, 50, "#F4F6F8", "#D9DDE1")
    lc.rect(10, 8, 110, 42, fill="#0B1A10", radius=3)
    lc.text(60, 25, "0.500 g", 17, "#5CFF8A", 900)
    for k, lab in enumerate(("ON", "TARE", "CAL")):
        x = 132 + k * 24
        lc.rect(x - 10, 15, x + 10, 35, fill="#8E9399", radius=3)
        lc.text(x, 43, lab, 4.5, INK, 800)
    panel = _face(lc.array(), "plastic", 13431, 0.5, 4)
    ys = D / 2 - 0.105
    parts = [
        Part("Base", "box", [W, D, base_h], [0, 0, base_h / 2], color="#E9ECEF", finish="plastic", material="plastic",
             bevel=0.006),
        _box("Display", (0.20, 0.004, 0.05), (0, -D / 2 - 0.002, base_h / 2), "#E9ECEF", "plastic", {"front": 0},
             collision=False),
        Part("Shield", "box", [0.20, 0.21, shield_h - 0.01], [0, ys, base_h + (shield_h - 0.01) / 2], color="#EAF2F5",
             finish="glass", thin_walled=True),
        _box("ShieldTop", (0.21, 0.22, 0.01), (0, ys, H - 0.005), "#D9DDE1", "plastic"),
        _cyl("Pan", (0.09, 0.09, 0.006), (0, ys, base_h + 0.003), STEEL, "metal", False),
    ]
    return Product(slug="electronic_balance", name="電子天秤 風防付き（最小表示 1 mg）", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D + 0.004), mass_kg=4.5, static=False,
                   material="plastic",
                   description="形は調剤薬局の散薬台で粉薬を量る一般的な電子天秤（幅 220 mm・奥行き 320 mm・高さ 300 mm、"
                               "前に表示とボタン、奥の皿をガラスの風防が囲む）で、寸法・質量は代表値。風防の戸は開かない。"
                               "表示の文字は架空。",
                   tags=["電子天秤", "天秤", "はかり", "計量", "散剤", *ROOM, "electronic balance",
                         "analytical balance", "scale"], photos=[],
                   colors=Colors(label_base="#E9ECEF"), images=[panel], parts=parts)


# ---------------------------------------------------------------- 錠剤のピッキング棚


_PICK = [("A-01", "アムロジピン錠 5mg"), ("A-02", "アムロジピン錠 2.5mg"), ("A-03", "カンデサルタン錠 8mg"),
         ("A-04", "ロスバスタチン錠 2.5mg"), ("A-05", "メトホルミン錠 250mg"), ("A-06", "ランソプラゾール OD錠"),
         ("B-01", "ロキソプロフェン錠 60mg"), ("B-02", "レバミピド錠 100mg"), ("B-03", "アセトアミノフェン錠 200mg"),
         ("B-04", "セフカペン錠 100mg"), ("B-05", "フェキソフェナジン錠 60mg"), ("B-06", "モンテルカスト錠 10mg")]


def picking_shelf_rack() -> Product:
    W, D, H = 1.20, 0.35, 1.90
    t = 0.018
    levels = (0.12, 0.42, 0.72, 1.02, 1.32, 1.62)
    imgs = []
    for k in range(2):  # 棚の前の名札（6 区画ずつ、2 種類を段ごとに交互に使う）
        c = Canvas(1160, 28, None, WHITE, 13441 + k)
        c.gradient(0, 0, 1160, 28, "#FFFFFF", "#EEF1F4")
        c.rect(0, 22, 1160, 28, fill="#C9CED3")
        for j in range(6):
            code, name = _PICK[k * 6 + j]
            x0 = j * 193.3
            c.rect(x0 + 2, 2, x0 + 40, 20, fill=NAVY if k == 0 else GREEN, radius=2)
            c.text(x0 + 21, 11, code, 9, WHITE, 900)
            c.text(x0 + 117, 11, name, 9.5, INK, 800, max_w=145)
        imgs.append(_face(c.array(), "paper", 13441 + k, 0.8, 6))
    parts = [
        _box("Back", (W, t, H), (0, D / 2 - t / 2, H / 2), CREAM, "matte"),
        _box("Top", (W, D, t), (0, 0, H - t / 2), CREAM, "matte"),
        _box("Plinth", (W - 2 * t, D - t - 0.03, 0.08), (0, -t / 2 + 0.015, 0.04), GRAY, "matte"),
    ]
    for side, x in (("L", -W / 2 + t / 2), ("R", W / 2 - t / 2)):
        parts.append(_box(f"Side{side}", (t, D, H - t), (x, 0, (H - t) / 2), CREAM, "matte"))
    sd = D - t - 0.005
    yc = -D / 2 + sd / 2
    for i, z in enumerate(levels):
        parts.append(_shelf(f"Shelf{i + 1}", W - 2 * t, sd, (0, yc, z), "#E4E0D8"))
        parts.append(_box(f"Label{i + 1}", (1.16, 0.002, 0.028), (0, -D / 2 - 0.001, z - 0.0075 + 0.014), WHITE,
                          "matte", {"front": i % 2}, collision=False))
        for j in range(1, 6):  # 区画の仕切り（薬の箱が混ざらないように）
            x = -W / 2 + t + j * (W - 2 * t) / 6
            parts.append(_box(f"Divider{i + 1}_{j}", (0.004, sd - 0.02, 0.08), (x, yc + 0.01, z + 0.0075 + 0.04),
                              "#EAF2F5", "plastic"))
    return Product(slug="picking_shelf_rack", name="錠剤のピッキング棚 6 段 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.002), mass_kg=55.0, static=True,
                   material="wood",
                   description="形は調剤薬局の調剤室で錠剤の箱を薬の名前順に並べる一般的な薬品棚（幅 1200 mm・奥行き 350 mm・"
                               "高さ 1900 mm、棚 6 段、各段を透明な仕切りで 6 区画に分け、前に薬の名前の札）で、"
                               "寸法・質量は代表値。札の薬の名前は一般名で、番号は架空。",
                   tags=["薬品棚", "ピッキング棚", "錠剤棚", "調剤棚", "収納棚", *ROOM, "medicine shelf",
                         "pharmacy picking shelf"], photos=[],
                   colors=Colors(label_base=CREAM), images=imgs, parts=parts)


# ---------------------------------------------------------------- 麻薬金庫


def narcotics_safe() -> Product:
    W, D, H = 0.40, 0.40, 0.50
    t, wall = 0.05, 0.035  # 扉の厚さ・壁の厚さ
    body = "#5E6670"
    pl = Canvas(390, 490, None, body, 13451)
    pl.gradient(0, 0, 390, 490, "#727B85", "#545B64")
    pl.rect(0, 470, 390, 490, fill="#3E444B")
    pl.rect(95, 50, 295, 120, fill="#F4F1E8", radius=4)
    pl.text(195, 85, "麻 薬", 44, "#B3261E", 900)
    pl.rect(30, 30, 360, 450, outline="#8A939C", width=3, radius=6)
    pl.ellipse(180, 390, 210, 420, fill="#2B2E31")
    img = _face(pl.array(), "metal", 13451, 0.6, 6)
    y0, y1 = -D / 2 + t, D / 2
    zc = H / 2
    parts = [
        _box("SideL", (wall, y1 - y0, H), (-W / 2 + wall / 2, (y0 + y1) / 2, zc), body, "metal"),
        _box("SideR", (wall, y1 - y0, H), (W / 2 - wall / 2, (y0 + y1) / 2, zc), body, "metal"),
        _box("Back", (W - 2 * wall, wall, H), (0, y1 - wall / 2, zc), body, "metal"),
        _box("Bottom", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, wall / 2), body, "metal"),
        _box("Top", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, H - wall / 2), body, "metal"),
        _shelf("Shelf", W - 2 * wall - 0.004, y1 - y0 - wall - 0.01, (0, (y0 + y1 - wall) / 2, 0.25), "#8A939C"),
    ]
    dw, dh = W - 0.004, H - 0.004
    yd = -D / 2 + t / 2
    door = [
        _box("Door", (dw, t, dh), (0, yd, zc), body, "metal", {"front": 0}),
        _cyl("Dial", (0.07, 0.07, 0.02), (-0.06, -D / 2 - 0.01, 0.30), "#C9CED3", "metal", False),
        _box("Handle", (0.03, 0.03, 0.12), (-0.14, -D / 2 - 0.015, 0.25), "#C9CED3", "metal", collision=False),
    ]
    door[1].rotation = [90.0, 0.0, 0.0]
    for p in door:
        p.link = "DoorLink"
    parts += door
    return Product(slug="narcotics_safe", name="麻薬金庫（小型・ダイヤル錠）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.02), mass_kg=70.0, static=True,
                   material="steel", joints=[Joint(link="DoorLink", anchor=[dw / 2, -D / 2, zc], limits=[0.0, 100.0])],
                   description="形は調剤薬局で麻薬を保管する一般的な小型の金庫（幅 400 mm・奥行き 420 mm・高さ 500 mm、"
                               "本体の奥行き 400 mm にダイヤルと取っ手が前へ 20 mm 出る、ダイヤル錠と取っ手の付いた扉 1 枚、中に棚 1 段）で、寸法・質量は代表値。"
                               "扉（DoorLink）は右端の蝶番で手前に 100° まで開く。床や棚に固定して使う。",
                   tags=["麻薬金庫", "金庫", "保管庫", "麻薬", *ROOM, "narcotics safe", "drug safe"], photos=[],
                   colors=Colors(label_base=body), images=[img], parts=parts)


# ---------------------------------------------------------------- クリーンベンチ（無菌調剤）


def clean_bench() -> Product:
    W, D = 1.30, 0.75
    stand = 0.70  # 台の高さ
    ch = 0.85  # 作業室の高さ
    fu = 0.35  # 上のフィルターの箱の高さ
    H = stand + ch + fu
    z0 = stand
    pf = _plate(1260, 330, 13461)
    pf.rect(0, 0, 1260, 70, fill=NAVY)
    pf.text(630, 35, "クリーンベンチ  無菌調剤", 38, WHITE, 900)
    pf.rect(80, 110, 420, 270, fill="#0B1A10", radius=6)
    pf.text(250, 160, "風速 0.45 m/s", 30, "#5CFF8A", 900)
    pf.text(250, 220, "HEPA  正常", 28, "#5CFF8A", 800)
    for k, (lab, col) in enumerate((("送風", "#3BAA5C"), ("照明", "#F2D44A"), ("UV", "#7C5CD6"))):
        x = 560 + k * 110
        pf.ellipse(x - 35, 140, x + 35, 210, fill=col)
        pf.text(x, 245, lab, 24, INK, 800)
    _vents(pf, 900, 110, 1180, 6, 30)
    panel = _face(pf.array(), "plastic", 13461, 0.6, 6)
    ss = "#D9DDE1"
    parts = [
        _box("Worktop", (W, D, 0.03), (0, 0, z0 + 0.015), ss, "metal"),
        _box("SideL", (0.04, D, ch), (-W / 2 + 0.02, 0, z0 + ch / 2), BODY, "metal"),
        _box("SideR", (0.04, D, ch), (W / 2 - 0.02, 0, z0 + ch / 2), BODY, "metal"),
        _box("Back", (W - 0.08, 0.04, ch), (0, D / 2 - 0.02, z0 + ch / 2), BODY, "metal"),
        _box("FilterUnit", (W, D, fu), (0, 0, z0 + ch + fu / 2), BODY, "metal"),
        _box("FilterFront", (1.26, 0.004, 0.33), (0, -D / 2 - 0.002, z0 + ch + fu / 2), BODY, "plastic",
             {"front": 0}, collision=False),
        Part("Sash", "box", [W - 0.08, 0.008, 0.55], [0, -D / 2 + 0.02, z0 + ch - 0.275], color="#EAF2F5",
             finish="glass", thin_walled=True),
        _box("SashRail", (W - 0.08, 0.03, 0.02), (0, -D / 2 + 0.02, z0 + ch - 0.55 - 0.01), STEEL, "metal"),
        _box("StandRail", (W - 0.10, 0.04, 0.04), (0, 0, 0.15), GRAY, "metal"),
    ]
    for k, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_box(f"Leg{k}", (0.05, 0.05, stand), (x * (W / 2 - 0.05), y * (D / 2 - 0.05), stand / 2), GRAY,
                          "metal"))
    lamp, lux = _lamp("InnerLight", (W - 0.20, 0.04, 0.008), (0, 0.05, z0 + ch - 0.0045), "#F4F8FF", 5000.0,
                      COOL_WHITE)
    parts.append(lamp)
    return Product(slug="clean_bench", name="クリーンベンチ 無菌調剤用 1300mm（台付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.002), mass_kg=230.0, static=True,
                   material="steel", lights=[lux],
                   description="形は調剤薬局で注射薬や点眼薬を無菌で調製する一般的なクリーンベンチ（幅 1300 mm・奥行き 750 mm・"
                               "高さ 1900 mm、脚の台・ステンレスの作業台・前のガラスの窓・上の HEPA フィルターと操作部・"
                               "庫内の照明）で、寸法・質量は代表値。前の窓は動かない。表示の文字は架空。",
                   tags=["クリーンベンチ", "無菌調剤", "安全キャビネット", "調剤機器", *ROOM, "clean bench",
                         "laminar flow hood", "aseptic workstation"], photos=[],
                   colors=Colors(label_base=BODY), images=[panel], parts=parts)


# ---------------------------------------------------------------- 調剤用の流し台（水剤）


def dispensing_sink() -> Product:
    W, D = 0.90, 0.60
    top = 0.85
    bw, bd, bh = 0.50, 0.38, 0.20  # 槽の内寸
    H = 1.30
    ss = "#D9DDE1"
    cf = _plate(880, 760, 13471, CREAM)
    for k in range(2):
        x0 = 30 + k * 420
        cf.rect(x0, 30, x0 + 400, 730, outline="#B9BEC4", width=3, radius=4)
        cf.rect(x0 + (360 if k == 0 else 20), 300, x0 + (380 if k == 0 else 40), 460, fill="#8E9399", radius=8)
    cab = _face(cf.array(), "paper", 13471, 0.8, 6)
    yb = -0.02
    side_w = (W - bw) / 2
    front_d = (D - bd) / 2 + yb
    back_d = D - bd - front_d
    zt = top - 0.015
    parts = [
        _box("Plinth", (W - 0.04, D - 0.06, 0.08), (0, -0.01, 0.04), GRAY, "matte"),
        _box("Cabinet", (W, D - 0.02, top - 0.03 - 0.08), (0, 0.01, 0.08 + (top - 0.11) / 2), CREAM, "matte"),
        _box("CabinetFront", (0.88, 0.004, top - 0.11 - 0.02), (0, -D / 2 + 0.008, 0.08 + (top - 0.11) / 2), CREAM,
             "matte", {"front": 0}, collision=False),
        _box("TopFront", (W, front_d, 0.03), (0, -D / 2 + front_d / 2, zt), ss, "metal"),
        _box("TopBack", (W, back_d, 0.03), (0, D / 2 - back_d / 2, zt), ss, "metal"),
        _box("TopL", (side_w, bd, 0.03), (-W / 2 + side_w / 2, yb, zt), ss, "metal"),
        _box("TopR", (side_w, bd, 0.03), (W / 2 - side_w / 2, yb, zt), ss, "metal"),
        _box("BasinFloor", (bw, bd, 0.01), (0, yb, top - bh + 0.005), ss, "metal"),
        _box("BasinF", (bw, 0.01, bh), (0, yb - bd / 2 + 0.005, top - bh / 2), ss, "metal"),
        _box("BasinB", (bw, 0.01, bh), (0, yb + bd / 2 - 0.005, top - bh / 2), ss, "metal"),
        _box("BasinL", (0.01, bd, bh), (-bw / 2 + 0.005, yb, top - bh / 2), ss, "metal"),
        _box("BasinR", (0.01, bd, bh), (bw / 2 - 0.005, yb, top - bh / 2), ss, "metal"),
        _cyl("Drain", (0.06, 0.06, 0.002), (0, yb, top - bh + 0.011), "#8E9399", "metal", False),
        _box("Splash", (W, 0.02, 0.20), (0, D / 2 - 0.01, top + 0.10), ss, "metal"),
        _cyl("FaucetPost", (0.03, 0.03, 0.25), (0, D / 2 - 0.06, top + 0.125), STEEL),
        _box("FaucetSpout", (0.025, 0.18, 0.025), (0, D / 2 - 0.06 - 0.09, top + 0.24), STEEL, "metal"),
        _box("FaucetLever", (0.02, 0.10, 0.012), (0, D / 2 - 0.03, top + 0.26), STEEL, "metal", collision=False),
    ]
    for side, x in (("L", -W / 2 + 0.03), ("R", W / 2 - 0.03)):  # 投薬瓶を並べる棚の支柱
        parts.append(_box(f"ShelfPost{side}", (0.02, 0.02, H - top - 0.20), (x, D / 2 - 0.01, top + 0.20 +
                                                                            (H - top - 0.20) / 2), ss, "metal"))
    parts.append(_shelf("BottleShelf", W, 0.16, (0, D / 2 - 0.08, H - 0.0075), ss))
    return Product(slug="dispensing_sink", name="調剤用の流し台 900mm（投薬瓶の棚付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.002), mass_kg=65.0, static=True,
                   material="steel",
                   description="形は調剤薬局で水剤（シロップ）の調製や器具の洗浄に使う一般的な流し台（幅 900 mm・奥行き 600 mm・"
                               "天板の高さ 850 mm、ステンレスの天板と槽・水栓、奥の上に投薬瓶を並べる棚、下に開き戸の収納）で、"
                               "寸法・質量は代表値。戸は開かない。",
                   tags=["流し台", "シンク", "水剤", "洗い場", *ROOM, "dispensing sink", "pharmacy sink"], photos=[],
                   colors=Colors(label_base=CREAM), images=[cab], parts=parts)


# ---------------------------------------------------------------- 調剤カート


def medicine_cart() -> Product:
    W, D, H = 0.60, 0.45, 0.95
    frame = "#B9BEC4"
    tray = "#E9ECEF"
    sc = Canvas(300, 60, None, WHITE, 13481)
    sc.gradient(0, 0, 300, 60, "#FFFFFF", "#E7F0FA")
    sc.rect(0, 0, 60, 60, fill=NAVY)
    sc.text(30, 30, "3", 40, WHITE, 900)
    sc.text(180, 22, "調剤カート", 22, NAVY, 900)
    sc.text(180, 46, "一包化・施設用", 14, INK, 700)
    tag = _face(sc.array(), "plastic", 13481, 0.6, 4)
    parts = []
    for k, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        px, py = x * (W / 2 - 0.02), y * (D / 2 - 0.02)
        parts.append(_box(f"Post{k}", (0.025, 0.025, H - 0.08), (px, py, 0.08 + (H - 0.08) / 2), frame, "metal"))
        parts.append(_cyl(f"Caster{k}", (0.07, 0.07, 0.05), (px, py, 0.035), DARK, "matte"))
        parts.append(_box(f"CasterMount{k}", (0.05, 0.05, 0.02), (px, py, 0.07), frame, "metal"))
    for i, z in enumerate((0.20, 0.50, 0.80)):  # 縁の立った棚 3 段
        parts.append(_shelf(f"Shelf{i + 1}", W - 0.06, D - 0.06, (0, 0, z), tray))
        parts.append(_box(f"LipF{i + 1}", (W - 0.06, 0.008, 0.04), (0, -D / 2 + 0.034, z + 0.0275), tray, "plastic"))
        parts.append(_box(f"LipB{i + 1}", (W - 0.06, 0.008, 0.04), (0, D / 2 - 0.034, z + 0.0275), tray, "plastic"))
    parts += [
        _box("Handle", (W - 0.04, 0.025, 0.025), (0, D / 2 + 0.03, H - 0.05), frame, "metal"),
        _box("HandleArmL", (0.02, 0.05, 0.02), (-W / 2 + 0.04, D / 2 + 0.005, H - 0.05), frame, "metal"),
        _box("HandleArmR", (0.02, 0.05, 0.02), (W / 2 - 0.04, D / 2 + 0.005, H - 0.05), frame, "metal"),
        _box("Tag", (0.30, 0.004, 0.06), (0, -D / 2 + 0.028, 0.80 + 0.0075 + 0.03), WHITE, "plastic", {"front": 0},
             collision=False),
    ]
    return Product(slug="medicine_cart", name="調剤カート 3 段（キャスター付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.05), mass_kg=18.0, static=True,
                   material="steel",
                   description="形は調剤薬局で一包化した薬や施設に届ける薬を運ぶ一般的な調剤カート（幅 600 mm・奥行き 500 mm・"
                               "高さ 950 mm、棚の奥行き 450 mm に押し手が奥へ 50 mm 出る、縁の立った棚 3 段・奥に押し手・キャスター 4 個）で、寸法・質量は代表値。"
                               "什器として床に固定した扱い（キャスターは回らない）。番号札の文字は架空。",
                   tags=["調剤カート", "カート", "ワゴン", "配薬カート", *ROOM, "medicine cart", "pharmacy trolley"],
                   photos=[], colors=Colors(label_base=tray), images=[tag], parts=parts)


# ---------------------------------------------------------------- 調剤監査台（画面・バーコードの読み取り機）


def audit_workstation() -> Product:
    W, D = 1.20, 0.70
    top = 0.72
    sw, sh = 0.55, 0.33
    sc = Canvas(sw * 1000, sh * 1000, None, "#F4F6F8", 13491)
    sc.gradient(0, 0, sw * 1000, sh * 1000, "#FFFFFF", "#E9EEF3")
    sc.rect(0, 0, 550, 40, fill=NAVY)
    sc.text(275, 20, "調剤監査  受付番号 108", 22, WHITE, 900)
    rows = [("アムロジピン錠 5mg", "1錠 朝食後", "14日分"), ("レバミピド錠 100mg", "1錠 毎食後", "7日分"),
            ("ロキソプロフェン錠 60mg", "1錠 毎食後", "7日分"), ("湿布薬 70枚", "1日1回", "—")]
    for k, (name, how, days) in enumerate(rows):
        y = 70 + k * 52
        sc.rect(15, y - 20, 535, y + 20, fill=WHITE, outline="#C9D3DD", width=1.5, radius=4)
        sc.text(30, y, name, 15, INK, 800, anchor="lm")
        sc.text(330, y, how, 13, INK, 700, anchor="lm")
        sc.text(445, y, days, 13, INK, 700, anchor="lm")
        sc.rect(490, y - 13, 525, y + 13, fill="#3BAA5C", radius=4)
        sc.text(507, y, "OK", 11, WHITE, 900)
    sc.text(275, 300, "すべて照合しました", 20, "#3BAA5C", 900)
    screen = _face(sc.array(), "screen", 13491, 0.6, 3)
    wood = "#D8CBB5"
    ym = D / 2 - 0.15
    parts = [
        _box("Desktop", (W, D, 0.03), (0, 0, top - 0.015), wood, "matte"),
        _box("Pedestal", (0.40, D - 0.05, top - 0.03), (W / 2 - 0.22, 0.02, (top - 0.03) / 2), CREAM, "matte"),
        _box("LegL", (0.03, D - 0.05, top - 0.03), (-W / 2 + 0.035, 0.02, (top - 0.03) / 2), CREAM, "matte"),
        _box("Modesty", (W - 0.50, 0.02, 0.40), (-0.18, D / 2 - 0.04, top - 0.03 - 0.20), CREAM, "matte"),
        _box("MonitorFoot", (0.22, 0.18, 0.015), (-0.15, ym, top + 0.0075), DARK, "matte"),
        _box("MonitorNeck", (0.05, 0.03, 0.12), (-0.15, ym + 0.04, top + 0.075), DARK, "matte"),
        _box("Monitor", (sw + 0.02, 0.03, sh + 0.02), (-0.15, ym, top + 0.12 + sh / 2), "#1A1C20", "plastic"),
        Part("Screen", "box", [sw, 0.004, sh], [-0.15, ym - 0.017, top + 0.12 + sh / 2], color="#F4F6F8",
             finish="screen", faces={"front": 0}, collision=False, bevel=0),
        _box("Keyboard", (0.44, 0.14, 0.02), (-0.15, -0.10, top + 0.01), "#E2E5E9", "plastic"),
        _box("ScannerBase", (0.08, 0.10, 0.02), (0.38, 0.05, top + 0.01), DARK, "matte"),
        _box("ScannerHead", (0.06, 0.05, 0.12), (0.38, 0.06, top + 0.08), "#3B3F44", "plastic"),
        _box("ScannerWindow", (0.04, 0.004, 0.03), (0.38, 0.033, top + 0.11), "#B3261E", "glass", collision=False),
    ]
    H = top + 0.12 + sh + 0.01
    return Product(slug="audit_workstation", name="調剤監査台 1200mm（画面・バーコードの読み取り機付き）",
                   shape_class="assembly", category="fixture", dims=Dimensions(round(H, 3), W, depth=D),
                   mass_kg=45.0, static=True, material="wood",
                   description="形は調剤薬局で取りそろえた薬を処方と照らし合わせる一般的な監査台（幅 1200 mm・奥行き 700 mm・"
                               "机の高さ 720 mm、画面・キーボード・バーコードの読み取り機、右に引き出しの袖）で、"
                               "寸法・質量は代表値。机の上に調剤トレーや薬を置ける。画面の文字は架空。",
                   tags=["監査台", "調剤監査", "パソコン", "机", "バーコード", *ROOM, "audit workstation",
                         "pharmacy verification desk"], photos=[],
                   colors=Colors(label_base=wood), images=[screen], parts=parts)


# ---------------------------------------------------------------- 薬袋プリンター


def medicine_bag_printer() -> Product:
    W, D, H = 0.40, 0.45, 0.26
    fp = _plate(360, 120, 13495, "#E9ECEF")
    fp.text(110, 30, "薬袋プリンター", 22, NAVY, 900)
    fp.rect(20, 55, 170, 105, fill="#0B1A10", radius=4)
    fp.text(95, 80, "印刷待ち 3", 18, "#5CFF8A", 900)
    for k, col in enumerate(("#3BAA5C", "#F2A93B", "#E53935")):
        x = 230 + k * 45
        fp.ellipse(x - 16, 60, x + 16, 92, fill=col)
    front = _face(fp.array(), "plastic", 13495, 0.6, 4)
    bag = Canvas(130, 200, None, WHITE, 13496)  # 受け皿に出た薬袋（上面）
    bag.gradient(0, 0, 130, 200, "#FFFFFF", "#F1F4F2")
    bag.rect(0, 0, 130, 10, fill="#1F7A5C")
    bag.text(65, 32, "お くすり", 18, "#1F7A5C", 900)
    bag.rect(20, 55, 110, 75, outline=INK, width=0.6)
    bag.text(65, 100, "内 服 薬", 13, INK, 900)
    for k in range(4):
        bag.rect(18, 120 + k * 16, 112, 122 + k * 16, fill="#C9D3CD")
    bag.rect(0, 192, 130, 200, fill="#C9D3CD")
    top_img = _face(bag.array(), "paper", 13496, 0.8, 6)
    parts = [
        Part("Body", "box", [W, D, H], [0, 0, H / 2], color="#E9ECEF", finish="plastic", material="plastic",
             bevel=0.008),
        _box("FrontPanel", (0.36, 0.004, 0.12), (0, -D / 2 - 0.002, H - 0.07), "#E9ECEF", "plastic", {"front": 0},
             collision=False),
        _box("Slot", (0.26, 0.006, 0.012), (0, -D / 2 - 0.003, 0.10), DARK, "matte", collision=False),
        _box("Tray", (0.26, 0.14, 0.008), (0, -D / 2 - 0.07, 0.07), "#D3D8DD", "plastic"),
        _box("Bags", (0.13, 0.20, 0.006), (0, -D / 2 - 0.05, 0.077), WHITE, "matte", {"top": 1}, collision=False),
    ]
    return Product(slug="medicine_bag_printer", name="薬袋プリンター（卓上）", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D + 0.14), mass_kg=13.0, static=False,
                   material="plastic",
                   description="形は調剤薬局で患者名と用法を薬袋に印刷する一般的な卓上のプリンター（幅 400 mm・奥行き 590 mm・"
                               "高さ 260 mm、本体の奥行き 450 mm に受け皿が前へ 140 mm 出る、前に表示とランプ・出口・受け皿と印刷した薬袋）で、寸法・質量は代表値。"
                               "表示の文字は架空。",
                   tags=["プリンター", "薬袋プリンター", "薬袋", "印刷", *ROOM, "medicine bag printer",
                         "label printer"], photos=[],
                   colors=Colors(label_base="#E9ECEF"), images=[front, top_img], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    tablet_packaging_machine, powder_packaging_machine, powder_dispensing_table, electronic_balance, picking_shelf_rack,
    narcotics_safe, clean_bench, dispensing_sink, medicine_cart, audit_workstation, medicine_bag_printer)}
