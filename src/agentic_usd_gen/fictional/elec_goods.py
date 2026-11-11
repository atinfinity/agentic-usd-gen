"""Fictional products for an electronics store: appliance cartons, boxed small appliances and accessories.

The appliances themselves come from SimReady Central, so this module only makes what an electronics store stacks and
hangs: corrugated cartons of large appliances (TV, microwave, rice cooker, stick vacuum), retail boxes (hair dryer,
headphones, USB charger) and blister cards (earphones, phone case, AA batteries, LED bulb). The battery and bulb
cards are built by `*_pack()` functions in a local frame (as in hc_tools), so elec_fixtures can hang the same packs on
pegboard hooks as static parts. No real brands, model numbers or logos; the
appliance drawings are made from shapes, and barcodes are dummy EAN-13 in the in-store range (starting with 2).
Front is -Y.
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .conv_goods import BOX_FACES, _faces, _hang_hole
from .goods_more import FILM, _card_edges, _pse
from .hc_tools import CARD_T, Pack, _blister, _card, _card_back, _card_part
from .paint import Canvas, mix
from .products import INK, _box, _cyl, _face

WHITE, KRAFT, KRAFT_DARK = "#FFFFFF", "#C49A6C", "#8A6440"
CHROME_E = "#D4D7DB"
ELEC_TAGS = ["家電", "家電量販店", "electronics", "electronics store"]


# ---------------------------------------------------------------- corrugated cartons


def _kraft(w: float, h: float, seed: int) -> Canvas:
    c = Canvas(w, h, None, KRAFT, seed)
    c.gradient(0, 0, w, h, mix(KRAFT, "#FFFFFF", 0.08), mix(KRAFT, "#000000", 0.06))
    step = max(4.0, w / 160)  # faint flutes
    x = 0.0
    while x < w:
        c.line([(x, 0), (x, h)], mix(KRAFT, KRAFT_DARK, 0.12), max(0.3, step * 0.08))
        x += step
    return c


def _marks(c: Canvas, x: float, y: float, s: float) -> None:
    """Handling marks: this side up (two arrows), fragile (a glass), keep dry (an umbrella)."""
    for k in (0, 1):
        cx = x + s * 0.3 + k * s * 0.4
        c.polygon([(cx, y), (cx - s * 0.15, y + s * 0.3), (cx + s * 0.15, y + s * 0.3)], fill=INK)
        c.rect(cx - s * 0.05, y + s * 0.3, cx + s * 0.05, y + s * 0.8, fill=INK)
    gx = x + s * 1.4
    c.polygon([(gx - s * 0.25, y), (gx + s * 0.25, y), (gx + s * 0.08, y + s * 0.45), (gx - s * 0.08, y + s * 0.45)],
              outline=INK)
    c.line([(gx, y + s * 0.45), (gx, y + s * 0.75)], INK, s * 0.05)
    c.line([(gx - s * 0.18, y + s * 0.78), (gx + s * 0.18, y + s * 0.78)], INK, s * 0.05)
    ux = x + s * 2.3
    c.polygon([(ux - s * 0.32, y + s * 0.35), (ux, y + s * 0.02), (ux + s * 0.32, y + s * 0.35)], fill=INK)
    c.line([(ux, y + s * 0.35), (ux, y + s * 0.72), (ux - s * 0.1, y + s * 0.78)], INK, s * 0.05)


def _carton(W: float, D: float, H: float, seed: int, title: str, en: str, sub: str, accent: str, draw, rows,
            handles: bool = True) -> list:
    """Six faces of a printed corrugated carton (mm). draw(c, x0, y0, x1, y1) draws the appliance on the front."""
    big = max(W, H)
    fr = _kraft(W, H, seed)
    fr.rect(0, H * 0.90, W, H, fill=accent)
    fr.text(W * 0.05, H * 0.10, title, big * 0.055, INK, 900, anchor="lm", max_w=W * 0.6)
    fr.text(W * 0.05, H * 0.19, en, big * 0.028, accent, 800, anchor="lm", max_w=W * 0.6)
    fr.text(W * 0.05, H * 0.95, sub, big * 0.03, WHITE, 800, anchor="lm", max_w=W * 0.9)
    draw(fr, W * 0.08, H * 0.26, W * 0.92, H * 0.86)
    bk = _kraft(W, H, seed + 1)
    bk.rect(0, H * 0.90, W, H, fill=accent)
    s = min(W, H)
    y = bk.table(W * 0.06, H * 0.08, W * 0.55, "仕様", rows, s * 0.035)
    bk.paragraph(W * 0.06, y + s * 0.03, W * 0.55, "開梱のときは刃物で中の商品を傷つけないようご注意ください。"
                 "梱包材はお住まいの地域の分別ルールに従って処分してください。\n" + NOTICE, s * 0.026, INK, 500)
    bk.barcode(W * 0.65, H * 0.12, W * 0.28, W * 0.12)
    _marks(bk, W * 0.62, H * 0.55, s * 0.12)
    sides = []
    for k in range(2):
        sd = _kraft(D, H, seed + 2 + k)
        sd.rect(0, H * 0.90, D, H, fill=accent)
        sd.text(D / 2, H * 0.12, title, min(D * 0.09, H * 0.05), INK, 900, max_w=D * 0.9)
        sd.text(D / 2, H * 0.20, en, min(D * 0.05, H * 0.03), accent, 800, max_w=D * 0.9)
        if handles and H > 250:  # printed hand holes
            sd.rect(D * 0.3, H * 0.33, D * 0.7, H * 0.33 + min(30, H * 0.06), fill=KRAFT_DARK, radius=12)
        _marks(sd, D * 0.12, H * 0.62, min(D * 0.25, H * 0.12))
        sides.append(sd)
    tops = []
    for k in range(2):  # the flaps and the packing tape across them
        t = _kraft(W, D, seed + 4 + k)
        t.rect(0, D / 2 - 0.5, W, D / 2 + 0.5, fill=KRAFT_DARK)
        t.rect(0, D / 2 - D * 0.12, W, D / 2 + D * 0.12, fill=mix(KRAFT, "#E8D3A8", 0.6))
        t.rect(0, 0, W, D * 0.04, fill=accent)
        tops.append(t)
    return _faces((fr, bk, *sides, *tops), "paper", seed, 0.6)


def _carton_product(slug, name, W, D, H, mass, imgs, description, tags, accent, photos=()) -> Product:
    return Product(slug=slug, name=name, shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=mass, material="paper",
                   description=description, tags=[*tags, "段ボール", "外箱", "carton", "cardboard box", *ELEC_TAGS],
                   photos=list(photos), colors=Colors(label_base=KRAFT), images=imgs, faces=BOX_FACES)


def tv_carton_43() -> Product:
    W, D, H = 1070.0, 150.0, 700.0

    def draw(c, x0, y0, x1, y1):
        w = (x1 - x0) * 0.82
        h = w * 9 / 16
        cx = (x0 + x1) / 2
        top = y0
        c.rect(cx - w / 2, top, cx + w / 2, top + h, fill="#16181C", radius=6)
        c.photo("lake", cx - w / 2 + 8, top + 8, cx + w / 2 - 8, top + h - 8)
        c.rect(cx - w * 0.06, top + h, cx + w * 0.06, top + h + 20, fill="#2A2D33")
        c.rect(cx - w * 0.22, top + h + 20, cx + w * 0.22, top + h + 30, fill="#2A2D33", radius=4)
        c.text(x1, y1 - 14, "43V型", 70, "#C62828", 900, anchor="rm")

    imgs = _carton(W, D, H, 9901, "4K 液晶テレビ", "4K LED TV  43\"", "地上・BS・110度CS デジタル  倍速なし  架空の電機",
                   "#1E3F73", draw, [("画面サイズ", "43V 型（対角 108 cm）"), ("解像度", "3840 × 2160"),
                                     ("消費電力", "約 110 W"), ("本体質量", "約 8.5 kg（スタンド含む）")])
    return _carton_product("tv_carton_43", "液晶テレビ 43V型の外箱", W, D, H, 13.0, imgs,
                           "形は一般的な 43V 型の液晶テレビを入れた段ボールの外箱（1070 × 150 × 700 mm）で、寸法・質量は"
                           "テレビと梱包材を含む代表値。印刷・型番・メーカー名はすべて架空。画面の写真は CC0。",
                           ["テレビ", "液晶テレビ", "4K", "43型", "television box", "TV box", "TV carton"],
                           "#1E3F73", photos=["lake"])


def microwave_carton() -> Product:
    W, D, H = 540.0, 440.0, 380.0

    def draw(c, x0, y0, x1, y1):
        w, h = (x1 - x0) * 0.8, (y1 - y0) * 0.78
        bx = x0 + (x1 - x0 - w) / 2
        c.rect(bx, y0, bx + w, y0 + h, fill="#F2F2F0", outline="#9A9A9A", width=2, radius=8)
        c.rect(bx + w * 0.06, y0 + h * 0.12, bx + w * 0.68, y0 + h * 0.88, fill="#2A2D33", radius=6)
        c.rect(bx + w * 0.10, y0 + h * 0.20, bx + w * 0.64, y0 + h * 0.80, fill="#3B3F46", radius=4)
        c.rect(bx + w * 0.74, y0 + h * 0.14, bx + w * 0.94, y0 + h * 0.30, fill="#1C2A22")
        c.text(bx + w * 0.84, y0 + h * 0.22, "500W", h * 0.07, "#7CFFB0", 800)
        for k in range(4):
            yy = y0 + h * (0.40 + 0.11 * k)
            c.rect(bx + w * 0.76, yy, bx + w * 0.92, yy + h * 0.07, fill="#D0D0CC", radius=3)

    imgs = _carton(W, D, H, 9911, "オーブンレンジ", "MICROWAVE OVEN  18L", "フラット庫内  解凍・あたため自動  架空の電機",
                   "#B23A2E", draw, [("総庫内容量", "18 L"), ("レンジ出力", "500・600 W"), ("ヒーター", "1000 W"),
                                     ("本体質量", "約 12 kg")])
    return _carton_product("microwave_carton", "オーブンレンジの外箱", W, D, H, 13.5, imgs,
                           "形は一般的な単機能〜オーブンレンジ（庫内 18 L）を入れた段ボールの外箱（540 × 440 × 380 mm）で、"
                           "寸法・質量はレンジと梱包材を含む代表値。印刷・型番・メーカー名はすべて架空。",
                           ["電子レンジ", "オーブンレンジ", "キッチン家電", "microwave box", "microwave carton"],
                           "#B23A2E")


def rice_cooker_carton() -> Product:
    W, D, H = 300.0, 380.0, 270.0

    def draw(c, x0, y0, x1, y1):
        cx, w = (x0 + x1) / 2, (x1 - x0) * 0.72
        top, h = y0 + (y1 - y0) * 0.05, (y1 - y0) * 0.85
        c.rect(cx - w / 2, top + h * 0.25, cx + w / 2, top + h, fill="#F4F4F2", outline="#A0A0A0", width=1.5,
               radius=16)
        c.ellipse(cx - w / 2, top, cx + w / 2, top + h * 0.5, fill="#E6E6E2", outline="#A0A0A0", width=1.5)
        c.rect(cx - w * 0.25, top + h * 0.55, cx + w * 0.25, top + h * 0.78, fill="#2A2D33", radius=6)
        c.text(cx, top + h * 0.665, "炊飯", h * 0.08, "#FFB74D", 800)
        c.text(x1, y1, "5.5合", 26, "#C62828", 900, anchor="rb")

    imgs = _carton(W, D, H, 9921, "IH ジャー炊飯器", "IH RICE COOKER  5.5", "かまど炊き風  玄米・炊き込み  架空の電機",
                   "#2F6B4F", draw, [("炊飯容量", "0.09〜1.0 L（5.5 合）"), ("消費電力", "1200 W"),
                                     ("本体質量", "約 4.5 kg")])
    return _carton_product("rice_cooker_carton", "IH炊飯器 5.5合の外箱", W, D, H, 5.6, imgs,
                           "形は一般的な 5.5 合炊きの IH 炊飯器を入れた段ボールの外箱（300 × 380 × 270 mm）で、寸法・質量は"
                           "炊飯器と梱包材を含む代表値。印刷・型番・メーカー名はすべて架空。",
                           ["炊飯器", "ジャー炊飯器", "IH", "キッチン家電", "rice cooker box"], "#2F6B4F")


def stick_vacuum_carton() -> Product:
    W, D, H = 290.0, 170.0, 760.0

    def draw(c, x0, y0, x1, y1):
        cx = (x0 + x1) / 2
        c.line([(cx + 20, y0 + 10), (cx - 10, y1 - 60)], "#8A9096", 8)
        c.rect(cx + 2, y0, cx + 52, y0 + 150, fill="#5B3C8C", radius=16)
        c.rect(cx + 10, y0 + 150, cx + 44, y0 + 210, fill="#3A3D44", radius=10)
        c.polygon([(cx - 70, y1 - 60), (cx + 50, y1 - 60), (cx + 55, y1 - 30), (cx - 75, y1 - 30)], fill="#3A3D44")
        c.text(cx, y1 - 10, "コードレス", 22, "#5B3C8C", 900)

    imgs = _carton(W, D, H, 9931, "スティック掃除機", "CORDLESS STICK VACUUM", "サイクロン式  最長 40 分  架空の電機",
                   "#5B3C8C", draw, [("集じん方式", "サイクロン式"), ("運転時間", "最長約 40 分"),
                                     ("充電時間", "約 3.5 時間"), ("本体質量", "約 1.5 kg")])
    return _carton_product("stick_vacuum_carton", "コードレススティック掃除機の外箱", W, D, H, 3.6, imgs,
                           "形は一般的なコードレスのスティック掃除機を入れた縦長の外箱（290 × 170 × 760 mm）で、寸法・質量は"
                           "掃除機と付属品・梱包材を含む代表値。印刷・型番・メーカー名はすべて架空。",
                           ["掃除機", "スティック掃除機", "コードレス", "生活家電", "vacuum cleaner box",
                            "stick vacuum box"], "#5B3C8C")


# ---------------------------------------------------------------- retail boxes


def _retail_box(W, D, H, seed, bg, accent, title, en, sub, draw, rows, back_note) -> list:
    """Six faces of a printed retail box (mm). draw(c, x0, y0, x1, y1) draws the product on the front."""
    s = min(W, H)
    fr = Canvas(W, H, None, bg, seed)
    fr.gradient(0, 0, W, H, mix(bg, WHITE, 0.15), mix(bg, "#000000", 0.2))
    draw(fr, W * 0.1, H * 0.12, W * 0.9, H * 0.70)
    fr.rect(0, H * 0.74, W, H * 0.76, fill=accent)
    fr.text(W / 2, H * 0.82, title, s * 0.085, WHITE, 900, max_w=W * 0.9)
    fr.text(W / 2, H * 0.89, en, s * 0.045, accent, 800, spacing=s * 0.004, max_w=W * 0.9)
    fr.text(W / 2, H * 0.95, sub, s * 0.04, mix(WHITE, bg, 0.2), 700, max_w=W * 0.9)
    fr.text(W * 0.06, H * 0.05, "架空の電機", s * 0.045, WHITE, 800, anchor="lm")
    bk = Canvas(W, H, None, WHITE, seed + 1)
    bk.gradient(0, 0, W, H, "#FFFFFF", "#EEF0F3")
    bk.rect(0, 0, W, H * 0.07, fill=bg)
    bk.text(W / 2, H * 0.035, en, s * 0.04, WHITE, 800, max_w=W * 0.9)
    y = bk.table(W * 0.06, H * 0.10, W * 0.94, "仕様", rows, s * 0.042)
    bk.paragraph(W * 0.06, y + s * 0.03, W * 0.94, back_note + "\n" + NOTICE, s * 0.032, INK, 500)
    bk.barcode(W * 0.06, H * 0.80, W * 0.42, W * 0.18)
    _pse(bk, W * 0.62, H * 0.86, s * 0.10)
    bk.recycle(W * 0.82, H * 0.86, s * 0.08, "紙", bg, sub="箱")
    bk.rect(0, H * 0.96, W, H, fill=bg)
    sides = []
    for k in range(2):
        sd = Canvas(D, H, None, bg, seed + 2 + k)
        sd.gradient(0, 0, D, H, mix(bg, WHITE, 0.1), mix(bg, "#000000", 0.2))
        sd.vtext(D / 2, H * 0.12, title[:8], min(D * 0.3, H * 0.06), WHITE, 900)
        sd.rect(0, H * 0.90, D, H * 0.92, fill=accent)
        sides.append(sd)
    tops = []
    for k in range(2):
        t = Canvas(W, D, None, bg, seed + 4 + k)
        t.gradient(0, 0, W, D, mix(bg, WHITE, 0.1), bg, horizontal=True)
        t.text(W / 2, D / 2, en, min(D * 0.2, W * 0.06), WHITE, 800, max_w=W * 0.9)
        tops.append(t)
    return _faces((fr, bk, *sides, *tops), "film", seed, 0.5)


def hair_dryer_box() -> Product:
    W, D, H = 220.0, 100.0, 260.0
    bg, accent = "#2E2A33", "#E8A0B4"

    def draw(c, x0, y0, x1, y1):
        cx, cy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.35
        r = (x1 - x0) * 0.22
        c.rect(cx - r * 1.8, cy - r * 0.55, cx + r * 0.6, cy + r * 0.55, fill="#F1D3DC", radius=r * 0.5)
        c.ellipse(cx + r * 0.1, cy - r * 0.95, cx + r * 1.9, cy + r * 0.95, fill="#F1D3DC")
        c.ellipse(cx + r * 0.6, cy - r * 0.5, cx + r * 1.4, cy + r * 0.5, fill="#C9A7B2")
        c.rect(cx + r * 0.55, cy + r * 0.6, cx + r * 1.15, cy + r * 2.6, fill="#F1D3DC", radius=r * 0.25)
        c.rect(cx + r * 0.7, cy + r * 1.2, cx + r * 1.0, cy + r * 1.5, fill="#7A5A66", radius=r * 0.1)

    imgs = _retail_box(W, D, H, 9941, bg, accent, "ヘアドライヤー", "HAIR DRYER 1200W", "大風量  マイナスイオン  折りたたみ",
                       draw, [("消費電力", "1200 W"), ("風量", "約 1.9 m³/分"), ("コード", "約 1.7 m"),
                              ("本体質量", "約 550 g")],
                       "浴室など湿気の多い場所では使わないでください。吸込口をふさがないでください。")
    return Product(slug="hair_dryer_box", name="ヘアドライヤーの箱", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.85, material="paper",
                   description="形は一般的な折りたたみ式のヘアドライヤーの化粧箱（220 × 100 × 260 mm）で、寸法・質量は"
                               "本体と梱包を含む代表値。印刷・型番・メーカー名はすべて架空。",
                   tags=["ドライヤー", "ヘアドライヤー", "理美容家電", "化粧箱", "hair dryer box", *ELEC_TAGS],
                   photos=[], colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


def headphones_box() -> Product:
    W, D, H = 200.0, 90.0, 240.0
    bg, accent = "#14161A", "#3FB6FF"

    def draw(c, x0, y0, x1, y1):
        cx, w = (x0 + x1) / 2, (x1 - x0) * 0.7
        top, h = y0 + 4, (y1 - y0) * 0.9
        c.ellipse(cx - w / 2, top, cx + w / 2, top + h * 0.9, outline="#9EA6B2", width=w * 0.07)
        c.rect(cx - w / 2 - w * 0.06, top + h * 0.45, cx - w / 2 + w * 0.18, top + h * 0.95, fill="#2C3038",
               radius=w * 0.08)
        c.rect(cx + w / 2 - w * 0.18, top + h * 0.45, cx + w / 2 + w * 0.06, top + h * 0.95, fill="#2C3038",
               radius=w * 0.08)
        c.rect(0, top + h * 0.40, x0 * 0.5, top + h * 0.42, fill=accent)

    imgs = _retail_box(W, D, H, 9951, bg, accent, "ワイヤレスヘッドホン", "WIRELESS HEADPHONES",
                       "ノイズキャンセリング  連続 30 時間", draw,
                       [("接続", "Bluetooth 5.3"), ("連続再生", "最大 30 時間"), ("充電", "USB-C 約 2 時間"),
                        ("質量", "約 250 g")],
                       "大きな音量で長時間使用しないでください。歩行中・運転中は周囲の音が聞こえる音量でご使用ください。")
    return Product(slug="headphones_box", name="ワイヤレスヘッドホンの箱", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.48, material="paper",
                   description="形は一般的なオーバーヘッド型のワイヤレスヘッドホンの化粧箱（200 × 90 × 240 mm）で、寸法・質量は"
                               "本体と梱包を含む代表値。印刷・型番・メーカー名はすべて架空。",
                   tags=["ヘッドホン", "ワイヤレス", "オーディオ", "化粧箱", "headphones box", "audio",
                         *ELEC_TAGS], photos=[], colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


def usb_charger_box() -> Product:
    W, D, H = 70.0, 45.0, 115.0
    bg, accent = "#F4F6F8", "#1E88E5"

    def draw(c, x0, y0, x1, y1):
        cx, w = (x0 + x1) / 2, (x1 - x0) * 0.6
        top, h = y0 + 2, (y1 - y0) * 0.75
        c.rect(cx - w / 2, top + h * 0.2, cx + w / 2, top + h, fill="#FFFFFF", outline="#B5BBC2", width=0.6,
               radius=w * 0.15)
        for s in (-1, 1):
            c.rect(cx + s * w * 0.18 - 1.2, top, cx + s * w * 0.18 + 1.2, top + h * 0.2, fill="#B5BBC2")
        c.rect(cx - w * 0.15, top + h * 0.75, cx + w * 0.15, top + h * 0.82, fill="#2A2D33", radius=1)
        c.text(cx, top + h * 0.5, "30W", w * 0.25, accent, 900)

    imgs = _retail_box(W, D, H, 9961, "#1E3F73", accent, "USB 充電器", "USB-C CHARGER 30W", "急速充電  折りたたみプラグ",
                       draw, [("入力", "AC100-240V"), ("出力", "USB-C 最大 30W"), ("質量", "約 55 g")],
                       "濡れた手で抜き差ししないでください。")
    return Product(slug="usb_charger_box", name="USB充電器 30W の箱", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.09, material="paper",
                   description="形は一般的な USB-C の AC 充電器（30W）の小箱（70 × 45 × 115 mm）で、寸法・質量は"
                               "本体と梱包を含む代表値。印刷・型番・メーカー名はすべて架空。",
                   tags=["充電器", "USB充電器", "ACアダプター", "スマホ用品", "charger box", "usb charger",
                         *ELEC_TAGS], photos=[], colors=Colors(label_base="#1E3F73"), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- blister cards


def _blister_card(CW, CH, seed, bg, accent, title, en, foot, rows, note) -> tuple:
    c = Canvas(CW, CH, 10, bg, seed)
    c.gradient(0, 0, CW, CH, mix(bg, WHITE, 0.12), mix(bg, "#000000", 0.25))
    _hang_hole(c, CW / 2, 5, mix(bg, "#000000", 0.5))
    c.rect(0, 13, CW, 32, fill=accent)
    c.text(CW / 2, 20, title, 7.4, bg, 900, max_w=CW - 8)
    c.text(CW / 2, 28, en, 3.8, bg, 800, spacing=0.3, max_w=CW - 8)
    c.rect(6, CH - 22, CW - 6, CH - 10, fill=accent, radius=3)
    c.text(CW / 2, CH - 16, foot, 4.0, bg, 900, max_w=CW - 16)
    c.text(CW / 2, CH - 5, "架空の電機", 3.4, WHITE, 700)
    _card_edges(c, accent)
    front = _face(c.array(), "film", seed, 0.6)
    b = Canvas(CW, CH, 10, WHITE, seed + 1)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF1F6")
    _card_edges(b, bg)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 15, CW, 25, fill=bg)
    b.text(CW / 2, 20, en, 3.8, WHITE, 800, max_w=CW - 8)
    yb = b.table(6, 30, CW - 6, "", rows, 3.2)
    b.paragraph(6, yb + 3, CW - 6, note + "\n" + NOTICE, 2.8, INK, 400)
    b.barcode(8, CH - 32, 40, 20)
    b.recycle(CW - 26, CH - 20, 7, "紙", bg, sub="台紙")
    b.recycle(CW - 12, CH - 20, 7, "プラ", bg, sub="ケース")
    back = _face(b.array(), "paper", seed + 1, 0.6)
    return front, back


def earphones_blister() -> Product:
    CW, CH = 100.0, 170.0
    bg, accent = "#1B1E24", "#7FD1AE"
    front, back = _blister_card(CW, CH, 9971, bg, accent, "完全ワイヤレスイヤホン", "TRUE WIRELESS EARBUDS",
                                "最大 24 時間（ケース併用）", [("接続", "Bluetooth 5.3"), ("再生", "約 6 時間"),
                                                              ("防水", "IPX4 相当"), ("質量", "約 40 g（ケース込み）")],
                                "耳に痛みを感じたら使用をやめてください。")
    k = Canvas(60.0, 48.0, 16, "#F4F5F7", 9973)  # the charging case
    k.gradient(0, 0, 60, 48, "#FFFFFF", "#DDE0E4")
    k.line([(2, 16), (58, 16)], "#B5BBC2", 0.5)
    k.ellipse(28, 28, 32, 30, fill=accent)
    case = _face(k.array(), "plastic", 9973, 0.3)
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), bg, "matte", {"front": 0, "back": 1}),
             _box("Blister", (0.074, 0.034, 0.090), (0, -0.0176, 0.090), FILM, "glass", thin_walled=True,
                  collision=False),
             _box("Case", (0.060, 0.026, 0.048), (0, -0.0146, 0.072), "#F4F5F7", "plastic", {"front": 2}),
             Part("BudL", "cylinder", [0.016, 0.016, 0.022], [-0.016, -0.0146, 0.116], color="#F4F5F7",
                  finish="plastic", collision=False),
             Part("BudR", "cylinder", [0.016, 0.016, 0.022], [0.016, -0.0146, 0.116], color="#F4F5F7",
                  finish="plastic", collision=False)]
    for p in parts:
        p.material = "paper" if p.name == "Card" else "plastic"
    return Product(slug="earphones_blister", name="完全ワイヤレスイヤホン（ブリスター）", shape_class="assembly",
                   category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0352), mass_kg=0.12,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入った完全ワイヤレスイヤホン（台紙 100 × 170 mm、充電ケース "
                               "60 × 26 × 48 mm と左右のイヤホン）で、寸法・質量は代表値。吊り下げ穴は穴を開けず印刷で"
                               "表す。印刷・型番・メーカー名はすべて架空。",
                   tags=["イヤホン", "ワイヤレスイヤホン", "オーディオ", "ブリスター", "earbuds", "earphones",
                         "blister pack", *ELEC_TAGS], photos=[], colors=Colors(label_base=bg),
                   images=[front, back, case], parts=parts)


def phone_case_blister() -> Product:
    CW, CH = 100.0, 200.0
    bg, accent = "#F5EEE6", "#D1786A"
    front, back = _blister_card(CW, CH, 9981, "#3A3F4A", accent, "スマートフォンケース", "SMARTPHONE CASE 6.1\"",
                                "6.1 インチ用  耐衝撃・薄型", [("対応", "6.1 インチの機種（架空）"),
                                                              ("素材", "TPU・ポリカーボネート"),
                                                              ("大きさ", "約 75 × 150 × 11 mm")],
                                "対応機種をお確かめのうえお求めください。")
    k = Canvas(75.0, 150.0, 10, accent, 9983)  # the back of the case faces the customer
    k.gradient(0, 0, 75, 150, mix(accent, WHITE, 0.2), mix(accent, "#000000", 0.1))
    k.rect(6, 6, 30, 34, fill=mix(accent, "#000000", 0.35), radius=6)
    for i, (x, y) in enumerate(((13, 13), (23, 13), (13, 25))):
        k.ellipse(x - 4, y - 4, x + 4, y + 4, fill="#1A1C20")
    case = _face(k.array(), "plastic", 9983, 0.3)
    parts = [_box("Card", (CW / 1000, 0.0012, CH / 1000), (0, 0, CH / 2000), "#3A3F4A", "matte",
                  {"front": 0, "back": 1}),
             _box("Blister", (0.082, 0.014, 0.158), (0, -0.0076, 0.092), FILM, "glass", thin_walled=True,
                  collision=False),
             _box("Case", (0.075, 0.011, 0.150), (0, -0.0066, 0.090), accent, "plastic", {"front": 2})]
    for p in parts:
        p.material = "paper" if p.name == "Card" else "plastic"
    return Product(slug="phone_case_blister", name="スマートフォンケース（ブリスター）", shape_class="assembly",
                   category="household", dims=Dimensions(CH / 1000, CW / 1000, depth=0.0152), mass_kg=0.07,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入った 6.1 インチ用のスマートフォンケース（台紙 100 × 200 mm、"
                               "ケース 75 × 150 × 11 mm）で、寸法・質量は代表値。吊り下げ穴は穴を開けず印刷で表す。"
                               "印刷・対応機種・メーカー名はすべて架空。",
                   tags=["スマホケース", "スマートフォンケース", "スマホ用品", "ブリスター", "phone case",
                         "smartphone case", "blister pack", *ELEC_TAGS], photos=[], colors=Colors(label_base=accent),
                   images=[front, back, case], parts=parts)


# ---------------------------------------------------------------- hanging packs (AA batteries, LED bulb)


def aa_battery_pack() -> Pack:
    CW, CH = 80.0, 150.0
    red = "#C62828"
    c = _card(CW, CH, 9991, red, "アルカリ乾電池", "単3形  4本パック", "長持ち  液もれ防止設計", base="#1E2126")
    front = _face(c.array(), "film", 9991, 0.5)
    back = _card_back(CW, CH, 9992, red, "ALKALINE BATTERY AA × 4", [("種類", "アルカリ乾電池 LR6"),
                                                                    ("電圧", "1.5 V"), ("本数", "4 本"),
                                                                    ("使用推奨期限", "裏面に記載（架空）")],
                      "充電・分解・ショートさせないでください。＋－を正しく入れてください。")
    bd = 0.0152
    yc = -CARD_T / 2 - bd / 2
    parts = [_card_part(CW, CH), _blister("Blister", 0.066, bd, 0.058, 0.046)]
    for k in range(4):  # four AA cells standing side by side
        x = -0.0234 + k * 0.0156
        parts += [_cyl(f"Cell{k}", (0.0145, 0.0145, 0.0485), (x, yc, 0.0750), red, "metal"),
                  _cyl(f"Cap{k}", (0.0055, 0.0055, 0.0015), (x, yc, 0.1000), CHROME_E, "metal")]
    for p in parts:
        if p.name.startswith(("Cell", "Cap")):
            p.material = "steel"
            p.collision = p.name.startswith("Cell")
    return Pack([front, back], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.11)


BULB = [[0.70, 0], [0.70, 0.16], [0.80, 0.30], [0.96, 0.48], [1.0, 0.62], [0.92, 0.80], [0.62, 0.95], [0, 1.0]]


def led_bulb_pack() -> Pack:
    CW, CH = 100.0, 180.0
    amber = "#F2A33A"
    c = _card(CW, CH, 9995, amber, "LED電球", "E26口金  60形相当  電球色", "約 40,000 時間  省エネ", base="#24364F")
    front = _face(c.array(), "film", 9995, 0.5)
    back = _card_back(CW, CH, 9996, amber, "LED BULB E26 60W EQUIVALENT", [("口金", "E26"), ("全光束", "810 lm"),
                                                                           ("消費電力", "7.3 W"), ("光色", "電球色 2700 K")],
                      "調光器・密閉形器具には使えません。点灯中・消灯直後は熱いので触れないでください。")
    bd = 0.062
    yc = -CARD_T / 2 - bd / 2
    parts = [_card_part(CW, CH), _blister("Blister", 0.070, bd + 0.003, 0.120, 0.026),
             Part("Bulb", "revolve", [0.060, 0.060, 0.086], [0, yc, 0.100], color="#F6F4EE", finish="plastic",
                  material="plastic", profile=BULB),
             _cyl("Base", (0.026, 0.026, 0.024), (0, yc, 0.045), CHROME_E, "metal"),
             _cyl("Tip", (0.010, 0.010, 0.004), (0, yc, 0.031), "#3A3D42", "metal", collision=False)]
    for p in parts:
        if p.name in ("Base", "Tip"):
            p.material = "steel"
    return Pack([front, back], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.08)


def aa_battery_blister() -> Product:
    p = aa_battery_pack()
    return Product(slug="aa_battery_blister", name="アルカリ乾電池 単3形 4本（吊り下げパック）", shape_class="assembly",
                   category="household", dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass,
                   material="steel",
                   description="形は一般的な台紙とブリスターに入った単3形アルカリ乾電池の 4 本パック（台紙 80 × 150 mm・"
                               "上に吊り下げ穴）で、寸法・質量は代表値。吊り下げ穴は印刷で表す（フックに吊った売場は "
                               "pegboard_batteries_bulbs）。印刷・メーカー名はすべて架空。",
                   tags=["乾電池", "電池", "単3", "単3形", "アルカリ乾電池", "4本パック", "吊り下げ", "ブリスター",
                         "aa battery", "batteries", "battery pack", "blister pack", "hanging pack", *ELEC_TAGS],
                   photos=[], colors=Colors(label_base="#1E2126"), images=p.images, parts=p.parts)


def led_bulb_blister() -> Product:
    p = led_bulb_pack()
    return Product(slug="led_bulb_blister", name="LED電球 E26 60形相当 電球色（吊り下げパック）", shape_class="assembly",
                   category="household", dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入った E26 口金・60 形相当の LED 電球（台紙 100 × 180 mm・"
                               "上に吊り下げ穴、電球は直径 60 mm）で、寸法・質量は代表値。吊り下げ穴は印刷で表す（フックに吊った"
                               "売場は pegboard_batteries_bulbs）。箱入りは led_bulb_box。印刷・メーカー名はすべて架空。",
                   tags=["LED電球", "電球", "LED", "E26", "照明", "吊り下げ", "ブリスター", "led bulb", "light bulb",
                         "blister pack", "hanging pack", *ELEC_TAGS],
                   photos=[], colors=Colors(label_base="#24364F"), images=p.images, parts=p.parts)


PRODUCTS = {f.__name__: f for f in (tv_carton_43, microwave_carton, rice_cooker_carton, stick_vacuum_carton,
                                    hair_dryer_box, headphones_box, usb_charger_box, earphones_blister,
                                    phone_case_blister, aa_battery_blister, led_bulb_blister)}
