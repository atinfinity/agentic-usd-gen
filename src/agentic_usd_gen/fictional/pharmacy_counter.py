"""架空の商品のデザイン: 調剤薬局の受付・服薬指導・待合い（服薬指導のカウンター・卓上の飛沫よけの板・受付番号の発券機・
処方せんの受付トレー・顔認証付きのカードリーダー・パンフレットのラック・待合いのソファ）。

pharmacy_fixtures.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の物の一般的な値にする。
正面は −Y（お客さま側）。床置きの什器はキネマティック（static）、卓上の物は動く剛体。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from .base import Product
from .drug_fixtures import DRUG_PLACES, GRAY, GREEN, NAVY, _capsule, _cross
from .paint import Canvas, mix
from .pharmacy_fixtures import CREAM, PHARMACY_TAGS
from .products import INK, _box, _cyl, _face
from .super_fixtures import _sign

WHITE, DARK = "#FFFFFF", "#2B2E31"
COUNTER = ["受付", "待合い", *PHARMACY_TAGS]


def _panel(w: float, h: float, seed: int, bg: str = WHITE, tint: str = "#E7F4EC") -> Canvas:
    c = Canvas(w, h, None, bg, seed)
    c.gradient(0, 0, w, h, bg, tint)
    c.rect(0, h - max(2.0, h * 0.03), w, h, fill=mix(tint, "#000000", 0.15))
    return c


# ---------------------------------------------------------------- 服薬指導のカウンター（仕切り付き）


def counseling_counter() -> Product:
    W, D = 1.00, 0.60
    top = 0.72  # 座って話す高さ
    H = 1.40
    wood = "#D8CBB5"
    sg = _panel(900, 560, 13501)
    sg.rect(0, 0, 900, 110, fill=GREEN)
    sg.text(450, 55, "お薬のご相談", 64, WHITE, 900)
    _capsule(sg, 450, 240, 80)
    sg.text(450, 380, "服薬指導・お薬の飲み合わせ", 40, GREEN, 900)
    sg.text(450, 450, "お気軽に薬剤師へお声かけください", 30, INK, 700)
    sign = _face(sg.array(), "plastic", 13501, 0.35, 6)
    parts = [
        _box("Plinth", (W - 0.04, 0.10, 0.06), (0, -D / 2 + 0.10, 0.03), GRAY, "matte"),
        _box("Top", (W, D, 0.03), (0, 0, top - 0.015), wood, "matte"),
        _box("Modesty", (W - 0.06, 0.03, top - 0.03 - 0.06), (0, -D / 2 + 0.10, 0.06 + (top - 0.09) / 2), CREAM,
             "matte"),
        _sign("FrontSign", (0.90, 0.004, 0.56), (0, -D / 2 + 0.083, 0.06 + (top - 0.09) / 2), GREEN, {"front": 0},
              CREAM),
        Part("Screen", "box", [W - 0.06, 0.006, 0.55], [0, 0, top + 0.08 + 0.275], color="#EAF2F5", finish="glass",
             thin_walled=True),
        _box("ScreenFootL", (0.04, 0.12, 0.08), (-W / 2 + 0.05, 0, top + 0.04), "#C9CED3", "metal"),
        _box("ScreenFootR", (0.04, 0.12, 0.08), (W / 2 - 0.05, 0, top + 0.04), "#C9CED3", "metal"),
    ]
    for side, x in (("L", -W / 2 - 0.015), ("R", W / 2 + 0.015)):  # 隣の席と区切る袖の板
        parts.append(_box(f"Partition{side}", (0.03, D + 0.20, H), (x, -0.10 + 0.10, H / 2), CREAM, "matte"))
    return Product(slug="counseling_counter", name="服薬指導のカウンター 1 席（仕切り付き・座り）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W + 0.06, depth=D + 0.20), mass_kg=55.0, static=True,
                   material="wood", picture_places=DRUG_PLACES,
                   description="形は調剤薬局で薬剤師が座って薬の説明をする一般的な服薬指導のカウンター（幅 1000 mm・奥行き 600 mm・"
                               "天板の高さ 720 mm、左右に高さ 1400 mm の仕切り、天板の中央に下の空いた透明の飛沫よけ、"
                               "前に案内の板）で、寸法・質量は代表値。いすは含まない。案内の文字は架空。",
                   tags=["服薬指導", "カウンター", "相談カウンター", "投薬台", *COUNTER, "counseling counter",
                         "pharmacy consultation desk"], photos=[],
                   colors=Colors(label_base=CREAM), images=[sign], parts=parts)


# ---------------------------------------------------------------- 卓上の飛沫よけの板


def acrylic_splash_guard() -> Product:
    W, D, H = 0.60, 0.20, 0.60
    slot = 0.10  # 下の受け渡しの口の高さ
    st = _panel(160, 50, 13511, WHITE, "#E7F0FA")
    st.text(80, 18, "お声かけください", 13, NAVY, 900)
    st.text(80, 37, "書類はこちらから", 10, INK, 700)
    sticker = _face(st.array(), "paper", 13511, 0.5, 4)
    parts = [
        _box("FootL", (0.04, D, 0.015), (-W / 2 + 0.03, 0, 0.0075), "#C9CED3", "metal"),
        _box("FootR", (0.04, D, 0.015), (W / 2 - 0.03, 0, 0.0075), "#C9CED3", "metal"),
        Part("PostL", "box", [0.04, 0.005, slot - 0.015], [-W / 2 + 0.03, 0, 0.015 + (slot - 0.015) / 2],
             color="#EAF2F5", finish="glass", thin_walled=True),
        Part("PostR", "box", [0.04, 0.005, slot - 0.015], [W / 2 - 0.03, 0, 0.015 + (slot - 0.015) / 2],
             color="#EAF2F5", finish="glass", thin_walled=True),
        Part("Panel", "box", [W, 0.005, H - slot], [0, 0, slot + (H - slot) / 2], color="#EAF2F5", finish="glass",
             thin_walled=True),
        _box("Sticker", (0.16, 0.001, 0.05), (0, -0.003, slot + 0.08), WHITE, "matte", {"front": 0}, collision=False),
    ]
    return Product(slug="acrylic_splash_guard", name="卓上の飛沫よけの板 600×600mm（受け渡しの口付き）",
                   shape_class="assembly", category="household", dims=Dimensions(H, W, depth=D), mass_kg=1.8,
                   static=False, material="plastic",
                   description="形は受付のカウンターに立てる一般的な透明の樹脂の飛沫よけ（幅 600 mm・高さ 600 mm、"
                               "左右の足・下に高さ 100 mm の書類の受け渡しの口・案内のシール）で、寸法・質量は代表値。"
                               "シールの文字は架空。",
                   tags=["飛沫よけ", "パーティション", "アクリル板", "感染対策", "仕切り", *COUNTER, "sneeze guard",
                         "acrylic partition", "splash guard"], photos=[],
                   colors=Colors(label_base=WHITE), images=[sticker], parts=parts)


# ---------------------------------------------------------------- 受付番号の発券機（卓上）


def number_ticket_machine() -> Product:
    W, D, H = 0.26, 0.24, 0.38
    sc = Canvas(200, 140, None, "#0D1B2A", 13521)
    sc.gradient(0, 0, 200, 140, "#16304D", "#0A1522")
    sc.rect(0, 0, 200, 26, fill=GREEN)
    sc.text(100, 13, "受付", 15, WHITE, 900)
    sc.rect(20, 40, 180, 86, fill="#3B7DD8", radius=8)
    sc.text(100, 63, "処方せんの方", 17, WHITE, 900)
    sc.rect(20, 94, 180, 130, fill="#6CC08A", radius=8)
    sc.text(100, 112, "お薬のご相談・お買い物", 12, WHITE, 900)
    screen = _face(sc.array(), "screen", 13521, 0.6, 3)
    lp = _panel(220, 90, 13522, WHITE, "#E7F4EC")
    lp.text(110, 22, "番号札をお取りください", 15, GREEN, 900)
    lp.rect(50, 50, 170, 62, fill="#3B3F44", radius=3)
    lp.text(110, 77, "↑ ここから出ます", 11, INK, 700)
    lower = _face(lp.array(), "plastic", 13522, 0.5, 4)
    tk = Canvas(60, 40, None, WHITE, 13523)
    tk.gradient(0, 0, 60, 40, "#FFFFFF", "#F1F3F4")
    tk.text(30, 11, "受付番号", 7, INK, 800)
    tk.text(30, 27, "112", 16, NAVY, 900)
    tk.rect(0, 37, 60, 40, fill="#D9DDE1")
    ticket = _face(tk.array(), "paper", 13523, 0.8, 4)
    yt = 0.04
    parts = [
        Part("Base", "box", [W, D, 0.04], [0, 0, 0.02], color="#E9ECEF", finish="plastic", material="plastic",
             bevel=0.004),
        Part("Tower", "box", [W, 0.16, H - 0.04], [0, yt, 0.04 + (H - 0.04) / 2], color="#F4F5F7", finish="plastic",
             material="plastic", bevel=0.006),
        Part("Screen", "box", [0.20, 0.006, 0.14], [0, yt - 0.083, 0.26], color="#0D1B2A", finish="screen",
             faces={"front": 0}, collision=False, bevel=0),
        _box("LowerPanel", (0.22, 0.004, 0.09), (0, yt - 0.082, 0.11), WHITE, "plastic", {"front": 1},
             collision=False),
        _box("Ticket", (0.06, 0.03, 0.001), (0, yt - 0.095, 0.124), WHITE, "matte", collision=False),
        _box("TicketFace", (0.06, 0.001, 0.04), (0, yt - 0.11, 0.105), WHITE, "matte", {"front": 2}, collision=False),
    ]
    return Product(slug="number_ticket_machine", name="受付番号の発券機（卓上・タッチ画面）", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D), mass_kg=5.0, static=False, material="plastic",
                   description="形は薬局の受付のカウンターに置く一般的な卓上の発券機（幅 260 mm・奥行き 240 mm・高さ 380 mm、"
                               "用件を選ぶタッチ画面・番号札の出口と出た札）で、寸法・質量は代表値。画面と札の文字は架空。",
                   tags=["発券機", "番号札", "受付", "順番待ち", *COUNTER, "ticket dispenser", "queue ticket machine"],
                   photos=[], colors=Colors(label_base="#F4F5F7"), images=[screen, lower, ticket], parts=parts)


# ---------------------------------------------------------------- 処方せんの受付トレー


def prescription_reception_tray() -> Product:
    W, D, h = 0.25, 0.33, 0.05  # A4 が入るトレー
    card_h = 0.14
    H = card_h
    color = "#2F86C8"
    cd = _panel(250, 140, 13531, WHITE, "#E7F0FA")
    cd.rect(0, 0, 250, 36, fill=color)
    cd.text(125, 18, "処方せん受付", 22, WHITE, 900)
    cd.text(125, 66, "処方せんはこちらへ", 20, color, 900)
    cd.text(125, 98, "お薬手帳・保険証も", 14, INK, 700)
    cd.text(125, 118, "ごいっしょにお出しください", 14, INK, 700)
    card = _face(cd.array(), "plastic", 13531, 0.5, 4)
    rx = Canvas(210, 297, None, WHITE, 13532)  # トレーの中の処方せん（上面）
    rx.gradient(0, 0, 210, 297, "#FFFFFF", "#F6F7F2")
    rx.text(105, 22, "処  方  箋", 16, INK, 900)
    rx.rect(12, 38, 198, 280, outline="#7F8A84", width=0.6)
    for k in range(10):
        y = 52 + k * 22
        rx.line([(12, y), (198, y)], "#B9C2BD", 0.4)
    rx.line([(60, 38), (60, 280)], "#B9C2BD", 0.4)
    for k, s in enumerate(("Rp.  アムロジピン錠 5mg  1錠", "     1日1回 朝食後  14日分", "Rp.  レバミピド錠 100mg  3錠",
                           "     1日3回 毎食後  7日分")):
        rx.text(66, 108 + k * 22, s, 7, "#1B2F5E", 700, anchor="lm")
    rx.rect(0, 292, 210, 297, fill="#D9DDE1")
    sheet = _face(rx.array(), "paper", 13532, 0.8, 6)
    parts = [Part("Floor", "box", [W - 0.006, D - 0.006, 0.004], [0, 0, 0.002], color=color, finish="plastic",
                  material="plastic", bevel=0.002)]
    for side, (size, c) in (("F", ((W, 0.004, 0.025), (0, -D / 2 + 0.002, 0.0125))),
                            ("L", ((0.004, D - 0.008, h), (-W / 2 + 0.002, 0, h / 2))),
                            ("R", ((0.004, D - 0.008, h), (W / 2 - 0.002, 0, h / 2)))):
        parts.append(Part(f"Wall{side}", "box", list(size), list(c), color=color, finish="plastic", material="plastic",
                          bevel=0.0015))
    parts += [
        Part("Card", "box", [W, 0.004, card_h], [0, D / 2 - 0.002, card_h / 2], color=color, finish="plastic",
             faces={"front": 0}, material="plastic", bevel=0.0015),
        _box("Sheet", (0.21, 0.297, 0.002), (0, -0.012, 0.005), WHITE, "matte", {"top": 1}, collision=False),
    ]
    return Product(slug="prescription_reception_tray", name="処方せんの受付トレー A4（案内の札付き）",
                   shape_class="assembly", category="household", dims=Dimensions(H, W, depth=D), mass_kg=0.45,
                   static=False, material="plastic",
                   description="形は調剤薬局の受付のカウンターに置く一般的な A4 の書類トレー（幅 250 mm・奥行き 330 mm・"
                               "縁の高さ 50 mm、奥に高さ 140 mm の案内の札、中に処方せん 1 枚）で、寸法・質量は代表値。"
                               "案内と処方せんの文字は架空。",
                   tags=["処方せん", "処方箋", "受付トレー", "書類トレー", *COUNTER, "prescription tray",
                         "document tray"], photos=[],
                   colors=Colors(label_base=color), images=[card, sheet], parts=parts)


# ---------------------------------------------------------------- 顔認証付きのカードリーダー


def face_auth_card_reader() -> Product:
    W, D = 0.17, 0.18
    head_w, head_d, head_h = 0.16, 0.045, 0.20
    zh = 0.13  # 頭の下端
    H = zh + head_h
    sc = Canvas(130, 100, None, "#F4F6F8", 13541)
    sc.gradient(0, 0, 130, 100, "#FFFFFF", "#E7F0FA")
    sc.rect(0, 0, 130, 20, fill=NAVY)
    sc.text(65, 10, "保険証の確認", 11, WHITE, 900)
    sc.rect(35, 30, 95, 68, outline=NAVY, width=2, radius=4)
    sc.ellipse(53, 36, 77, 60, outline=NAVY, width=2)
    sc.text(65, 82, "カードを置いて", 9, INK, 800)
    sc.text(65, 93, "画面を見てください", 8, INK, 700)
    screen = _face(sc.array(), "screen", 13541, 0.6, 3)
    yh = 0.02
    parts = [
        Part("Base", "box", [W, D, 0.02], [0, 0, 0.01], color="#2B2E31", finish="plastic", material="plastic",
             bevel=0.004),
        _box("Neck", (0.04, 0.04, zh - 0.02), (0, yh + 0.01, 0.02 + (zh - 0.02) / 2), "#3B3F44", "plastic"),
        Part("Head", "box", [head_w, head_d, head_h], [0, yh, zh + head_h / 2], color="#1A1C20", finish="plastic",
             material="plastic", bevel=0.006),
        Part("Screen", "box", [0.13, 0.004, 0.10], [0, yh - head_d / 2 - 0.002, zh + 0.085], color="#F4F6F8",
             finish="screen", faces={"front": 0}, collision=False, bevel=0),
        _cyl("Camera", (0.016, 0.016, 0.006), (0, yh - head_d / 2 - 0.003, zh + head_h - 0.03), "#0B0C0E", "glass",
             False),
        _box("CardTray", (0.11, 0.07, 0.012), (0, -0.045, 0.026), "#3B3F44", "plastic"),
        _box("CardMark", (0.086, 0.054, 0.001), (0, -0.045, 0.0325), "#5B6168", "matte", collision=False),
    ]
    parts[4].rotation = [90.0, 0.0, 0.0]
    return Product(slug="face_auth_card_reader", name="顔認証付きのカードリーダー（受付用）", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D), mass_kg=1.3, static=False, material="plastic",
                   description="形は医療機関・薬局の受付に置く一般的な顔認証付きのカードリーダー（幅 170 mm・奥行き 180 mm・"
                               "高さ 330 mm、台にカードを置くトレー、支柱の上に画面とカメラ）で、寸法・質量は代表値。"
                               "画面の文字は架空。",
                   tags=["カードリーダー", "顔認証", "保険証", "受付端末", *COUNTER, "card reader",
                         "face recognition terminal"], photos=[],
                   colors=Colors(label_base="#1A1C20"), images=[screen], parts=parts)


# ---------------------------------------------------------------- パンフレットのラック


_LEAFLETS = [("ジェネリック医薬品", "お薬代の負担を軽く", "#3B7DD8"), ("お薬手帳", "いつも持ち歩きましょう", "#E57A9A"),
             ("熱中症に注意", "こまめに水分補給", "#F2A93B"), ("禁煙のすすめ", "薬剤師がお手伝いします", "#3BAA5C")]


def pamphlet_rack() -> Product:
    W, D, H = 0.40, 0.30, 1.30
    tiers = (0.40, 0.62, 0.84, 1.06)
    imgs = []
    for k, (title, sub, col) in enumerate(_LEAFLETS):
        c = Canvas(148, 210, None, WHITE, 13551 + k)  # A5
        c.gradient(0, 0, 148, 210, "#FFFFFF", mix(col, WHITE, 0.8))
        c.rect(0, 0, 148, 48, fill=col)
        c.text(74, 24, title, 15, WHITE, 900, max_w=136)
        (_capsule if k % 2 == 0 else _cross)(c, 74, 100, 32)
        c.text(74, 160, sub, 11, col, 900, max_w=136)
        c.text(74, 190, "なかよし調剤薬局", 8, INK, 700)
        c.rect(0, 205, 148, 210, fill=mix(col, "#000000", 0.2))
        imgs.append(_face(c.array(), "paper", 13551 + k, 0.8, 6))
    frame = "#C9CED3"
    parts = [
        _box("Base", (W, D, 0.02), (0, 0, 0.01), frame, "metal"),
        _box("Back", (W, 0.015, H - 0.02), (0, D / 2 - 0.0075 - 0.10, 0.02 + (H - 0.02) / 2), WHITE, "plastic"),
        _box("Post", (0.04, 0.04, 0.38), (0, 0.0, 0.02 + 0.19), frame, "metal"),
    ]
    yb = D / 2 - 0.015 - 0.10  # 背板の前の面
    for k, z in enumerate(tiers):
        parts += [
            _box(f"PocketFloor{k}", (W - 0.02, 0.05, 0.006), (0, yb - 0.025, z), "#EAF2F5", "plastic"),
            Part(f"PocketFront{k}", "box", [W - 0.02, 0.005, 0.10], [0, yb - 0.05, z + 0.05], color="#EAF2F5",
                 finish="glass", thin_walled=True),
        ]
        for j, x in enumerate((-0.095, 0.095)):
            parts.append(_box(f"Leaflet{k}_{j}", (0.148, 0.01, 0.21), (x, yb - 0.02, z + 0.003 + 0.105), WHITE,
                              "matte", {"front": k}, collision=False))
    return Product(slug="pamphlet_rack", name="パンフレットのラック 4 段（A5）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=9.0, static=True, material="steel",
                   description="形は薬局の待合いに置く一般的なパンフレットのスタンド（幅 400 mm・奥行き 300 mm・高さ 1300 mm、"
                               "透明のポケット 4 段に A5 のパンフレットを 2 枚ずつ）で、寸法・質量は代表値。"
                               "パンフレットの文字と薬局名は架空。",
                   tags=["パンフレットラック", "パンフレット", "チラシ", "ラック", *COUNTER, "pamphlet rack",
                         "brochure stand"], photos=[],
                   colors=Colors(label_base=WHITE), images=imgs, parts=parts)


# ---------------------------------------------------------------- 待合いのソファ 2 人掛け


def waiting_sofa_2seat() -> Product:
    W, D, H = 1.20, 0.65, 0.80
    vinyl, frame = "#3E8C8A", "#B9BEC4"
    seat_z = 0.42
    arm = 0.08
    parts = [
        _box("SeatBase", (W - 2 * arm, D - 0.06, 0.08), (0, 0.0, 0.18 + 0.04), DARK, "matte"),
        Part("Seat", "box", [W - 2 * arm, D - 0.18, seat_z - 0.26], [0, -0.06, 0.26 + (seat_z - 0.26) / 2],
             color=vinyl, finish="plastic", material="vinyl", bevel=0.02),
        Part("Backrest", "box", [W - 2 * arm, 0.15, H - 0.26], [0, D / 2 - 0.075 - 0.03, 0.26 + (H - 0.26) / 2],
             color=vinyl, finish="plastic", material="vinyl", bevel=0.02),
        Part("SeamLine", "box", [0.01, D - 0.20, 0.002], [0, -0.06, seat_z + 0.001], color=mix(vinyl, "#000000", 0.3),
             finish="matte", collision=False, bevel=0),
    ]
    for side, x in (("L", -W / 2 + arm / 2), ("R", W / 2 - arm / 2)):
        parts.append(Part(f"Arm{side}", "box", [arm, D - 0.04, 0.62 - 0.18], [x, 0, 0.18 + (0.62 - 0.18) / 2],
                          color=vinyl, finish="plastic", material="vinyl", bevel=0.015))
    for k, (x, y) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_box(f"Leg{k}", (0.04, 0.04, 0.18), (x * (W / 2 - 0.06), y * (D / 2 - 0.07), 0.09), frame,
                          "metal"))
    return Product(slug="waiting_sofa_2seat", name="待合いのソファ 2 人掛け（ひじ掛け付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D - 0.04), mass_kg=32.0, static=True,
                   material="vinyl",
                   description="形は薬局・医院の待合いに置く一般的なビニールレザーの 2 人掛けソファ（幅 1200 mm・奥行き 650 mm・"
                               "高さ 800 mm・座面の高さ 420 mm、左右にひじ掛け、金属の脚 4 本）で、寸法・質量は代表値。",
                   tags=["ソファ", "待合いソファ", "長いす", "いす", *COUNTER, "waiting room sofa", "lobby sofa"],
                   photos=[], colors=Colors(label_base=vinyl), images=[], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    counseling_counter, acrylic_splash_guard, number_ticket_machine, prescription_reception_tray,
    face_auth_card_reader, pamphlet_rack, waiting_sofa_2seat)}
