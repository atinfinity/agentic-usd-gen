"""架空の商品のデザイン: ドラッグストアの売場の什器（医薬品・調剤・化粧品・ベビー用品）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
正面は −Y（お客さま側）。床置きの什器はキネマティック（static）。
商品を並べる面は薄い水平の板にする（商品を並べるツールが棚板として見つけられるように）。棚板の上に支柱などの
物を立てない（商品を並べるツールは板の全面に並べるので、支柱と重なると物理で押し出される）。
売場の看板・POP（店の売り文句の入った面）は blank で無地に切り替えられる（Picture バリアント）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .paint import Canvas, mix
from .products import COOL_WHITE, INK, _box, _cyl, _face, _lamp, _price_strip
from .super_fixtures import _sign

DRUG_PLACES = ["drugstore"]  # 医薬品・調剤の看板が合う場所
SHOP_PLACES = ["drugstore", "shop"]  # 化粧品・ベビー用品の看板（スーパーなどにもある売場）
WHITE, STEEL, GRAY = "#F4F5F7", "#C4C8CC", "#5A5F66"
GLASS = "#EAF2F5"
GREEN, NAVY, ROSE = "#1F7A5C", "#1E3F73", "#C2507A"


def _perforated(w_mm: float, h_mm: float, seed: int, base: str = "#ECEEF0") -> np.ndarray:
    """有孔ボードの背板。"""
    c = Canvas(w_mm, h_mm, 1.5, base, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(base, "#FFFFFF", 0.2), mix(base, "#000000", 0.06))
    y = 25.0
    while y < h_mm:
        x = 25.0
        while x < w_mm:
            c.ellipse(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill="#9AA0A6")
            x += 25
        y += 25
    c.rect(0, 0, 12, h_mm, fill="#9EA3A9")  # 左右の縁（支柱に掛かる部分）
    c.rect(w_mm - 12, 0, w_mm, h_mm, fill="#9EA3A9")
    return _face(c.array(), "metal", seed, 0.3, 12)


def _header(w_mm: float, h_mm: float, title: str, sub: str, seed: int, bg: str, band: str = "#F2C230",
            icon=None) -> np.ndarray:
    """売場の案内表示（色地に大きな文字・下に帯と英字）。icon(c, cx, cy, r) で左に絵を描く。"""
    c = Canvas(w_mm, h_mm, None, bg, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(bg, "#FFFFFF", 0.12), mix(bg, "#000000", 0.15))
    c.rect(0, h_mm * 0.80, w_mm, h_mm * 0.85, fill=band)
    cx = w_mm / 2
    if icon:
        r = h_mm * 0.30
        icon(c, h_mm * 0.55, h_mm * 0.42, r)
        cx = w_mm / 2 + h_mm * 0.35
    c.text(cx, h_mm * 0.38, title, h_mm * 0.38, "#FFFFFF", 900, max_w=w_mm * 0.7)
    c.text(cx, h_mm * 0.68, sub, h_mm * 0.13, mix(band, "#FFFFFF", 0.3), 800, spacing=h_mm * 0.02,
           max_w=w_mm * 0.8)
    return _face(c.array(), "plastic", seed, 0.35, 6)


def _capsule(c: Canvas, cx: float, cy: float, r: float) -> None:
    """カプセル（薬）の絵。白い丸の上に斜めのカプセル（半分が赤・半分が白）。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#FFFFFF", outline="#D0D0D0", width=r * 0.03)
    w, h, t = r * 1.3, r * 0.52, math.radians(-30)

    def half(side: float) -> list[tuple[float, float]]:
        """カプセルの片側（side=-1 で左、+1 で右）。中央の切れ目 → 直線 → 半円の端 → 直線 → 中央。30° 傾ける。"""
        e = w / 2 - h / 2  # 半円の中心
        loc = [(0.0, -h / 2)]
        for k in range(25):
            a = math.radians(-90 + 180 * k / 24)
            loc.append((side * (e + h / 2 * math.cos(a)), h / 2 * math.sin(a)))
        loc.append((0.0, h / 2))
        return [(cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)) for x, y in loc]

    c.polygon(half(-1), fill="#E53935", outline="#B71C1C")
    c.polygon(half(1), fill="#E6EBF0", outline="#9E9E9E")


def _cross(c: Canvas, cx: float, cy: float, r: float) -> None:
    """白い丸に緑の十字（医薬品の案内の目印）。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#FFFFFF")
    a, b = r * 0.62, r * 0.22
    c.rect(cx - a, cy - b, cx + a, cy + b, fill=GREEN)
    c.rect(cx - b, cy - a, cx + b, cy + a, fill=GREEN)


def _lips(c: Canvas, cx: float, cy: float, r: float) -> None:
    """白い丸に口紅とコンパクトの絵。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#FFFFFF")
    c.rect(cx - r * 0.55, cy - r * 0.05, cx - r * 0.15, cy + r * 0.6, fill="#2B2B2B", radius=r * 0.04)
    c.polygon([(cx - r * 0.5, cy - r * 0.05), (cx - r * 0.2, cy - r * 0.05), (cx - r * 0.2, cy - r * 0.45),
               (cx - r * 0.5, cy - r * 0.25)], fill=ROSE)
    c.ellipse(cx + r * 0.0, cy - r * 0.15, cx + r * 0.65, cy + r * 0.5, fill="#D9B38C", outline="#8C6A4A",
              width=r * 0.05)


def _baby(c: Canvas, cx: float, cy: float, r: float) -> None:
    """白い丸に哺乳びんの絵。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#FFFFFF")
    c.rect(cx - r * 0.28, cy - r * 0.15, cx + r * 0.28, cy + r * 0.65, fill="#BBDEFB", outline="#1E88E5",
           width=r * 0.05, radius=r * 0.12)
    c.rect(cx - r * 0.32, cy - r * 0.30, cx + r * 0.32, cy - r * 0.15, fill="#F48FB1")
    c.ellipse(cx - r * 0.14, cy - r * 0.62, cx + r * 0.14, cy - r * 0.28, fill="#FFE0B2")
    for k in range(3):
        y = cy + r * (0.05 + 0.18 * k)
        c.line([(cx - r * 0.28, y), (cx - r * 0.12, y)], "#1E88E5", r * 0.04)


def _shelf(name, w, d, center, color=STEEL) -> Part:
    return _box(name, (w, d, 0.015), center, color, "metal")


# ---------------------------------------------------------------- 医薬品の浅型ゴンドラ


def medicine_shelf_gondola() -> Product:
    W, D, H = 0.90, 0.36, 1.80
    back_h = 1.62
    sd = 0.28  # 棚板の奥行き（薬の箱は小さいので浅い）
    y_back = D / 2 - 0.03  # 背板の前面
    ys = y_back - sd / 2
    imgs = [_perforated(900, 1500, 9301),
            _price_strip(["980円", "1,280円", "698円", "1,580円", "880円", "1,180円"], 870, 9302, 142),
            _header(900, 180, "医薬品", "MEDICINE  かぜ薬・胃腸薬・解熱鎮痛薬", 9303, GREEN, icon=_cross)]
    parts = [
        _box("BasePlinth", (W, D - 0.02, 0.10), (0, -0.01, 0.05), GRAY, "matte"),
        _shelf("BaseShelf", W - 0.04, D - 0.06, (0, -0.02, 0.1075)),
        _box("BackPanel", (W, 0.03, back_h - 0.10), (0, D / 2 - 0.015, 0.10 + (back_h - 0.10) / 2), "#E6E8EB",
             "plastic", {"front": 0}),
        _box("SideLeft", (0.02, D, back_h), (-W / 2 + 0.01, 0, back_h / 2), GRAY, "metal"),
        _box("SideRight", (0.02, D, back_h), (W / 2 - 0.01, 0, back_h / 2), GRAY, "metal"),
        _sign("Header", (W, 0.02, H - back_h), (0, D / 2 - 0.02, back_h + (H - back_h) / 2), GREEN, {"front": 2},
              "#E6E8EB", collision=True, material="plastic"),
        _box("BaseRail", (W - 0.04, 0.012, 0.035), (0, -D / 2 + 0.016, 0.10), "#FFFFFF", "plastic", {"front": 1},
             collision=False),
    ]
    for k, z in enumerate((0.48, 0.76, 1.04)):  # 台の棚の上は約 350 mm（1 kg のプロテインの袋など大きな物）、上の 2 段は約 260 mm
        parts += [_shelf(f"Shelf{k + 1}", W - 0.04, sd, (0, ys, z)),
                  _box(f"PriceRail{k + 1}", (W - 0.04, 0.012, 0.035), (0, ys - sd / 2 - 0.006, z - 0.008), "#FFFFFF",
                       "plastic", {"front": 1}, collision=False)]
    # 最上段の上はフックバー（湿布・目薬などを吊る）。棒は細いので棚板の上の物には数えられない
    bar_z = 1.48
    parts.append(_box("HookBar", (W - 0.04, 0.02, 0.02), (0, y_back - 0.01, bar_z), STEEL, "metal"))
    for k in range(6):
        x = -W / 2 + 0.10 + k * (W - 0.20) / 5
        parts += [_box(f"Hook{k}", (0.005, 0.18, 0.005), (x, y_back - 0.11, bar_z), STEEL, "metal", collision=False),
                  _box(f"HookTag{k}", (0.03, 0.002, 0.02), (x, y_back - 0.201, bar_z + 0.004), "#FFE45C", "plastic",
                       collision=False)]
    return Product(slug="medicine_shelf_gondola", name="医薬品の浅型ゴンドラ 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=55.0, static=True, material="steel",
                   description="形はドラッグストアの医薬品売場の一般的な浅型ゴンドラ（幅 900 mm・奥行き 360 mm・高さ 1800 mm、"
                               "有孔の背板・浅い棚板 3 段と大きな物を置く背の高い台の棚・値札レール・上部のフックバー 6 本・案内表示）で、"
                               "寸法・質量は代表値。小箱の薬を並べる浅い棚。案内表示の文字は架空。",
                   tags=["医薬品", "薬", "ゴンドラ", "浅型", "陳列棚", "フックバー", "店舗什器", "ドラッグストア",
                         "medicine shelf", "pharmacy shelf", "gondola", "drugstore"], photos=[],
                   colors=Colors(label_base="#E6E8EB"), images=imgs, parts=parts, picture_places=DRUG_PLACES)


# ---------------------------------------------------------------- 第1類医薬品の施錠ガラスケース


def locked_medicine_case() -> Product:
    W, D = 0.90, 0.45
    deck_z, top_z = 0.825, 1.685
    head_h = 0.15
    H = top_z + 0.06 + head_h
    imgs = [_header(900, 150, "第1類医薬品", "薬剤師が説明します  お気軽にお声がけください", 9311, NAVY, "#E53935",
                    icon=_cross)]
    lo = Canvas(840, 560, None, "#E9E4DA", 9312)  # 下の収納の前板（木目調の化粧板）
    lo.gradient(0, 0, 840, 560, "#EFEAE0", "#D9D2C4")
    for k in range(1, 3):
        lo.line([(k * 280, 0), (k * 280, 560)], "#BFB6A6", 2)
    for k in range(3):
        lo.rect(k * 280 + 120, 40, k * 280 + 160, 52, fill="#9C958A", radius=3)
    imgs.append(_face(lo.array(), "paper", 9312, 0.4, 6))
    glass_h = top_z - deck_z
    gz = deck_z + glass_h / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.08), (0, 0.0, 0.04), GRAY, "matte"),
        _box("Cabinet", (W, D, deck_z - 0.015 - 0.08), (0, 0, 0.08 + (deck_z - 0.095) / 2), "#E9E4DA", "matte",
             {"front": 1}),
        _shelf("Deck", W - 0.06, 0.38, (0, 0.015, deck_z - 0.0075), "#F2F2F0"),
        _box("Back", (W, 0.02, glass_h), (0, D / 2 - 0.01, gz), "#F2F2F0", "plastic"),
        _box("EndL", (0.02, D - 0.02, glass_h), (-W / 2 + 0.01, -0.01, gz), GLASS, "glass"),
        _box("EndR", (0.02, D - 0.02, glass_h), (W / 2 - 0.01, -0.01, gz), GLASS, "glass"),
        _box("Top", (W, D, 0.06), (0, 0, top_z + 0.03), "#E9E4DA", "matte"),
        _box("TrackBottom", (W - 0.04, 0.04, 0.012), (0, -D / 2 + 0.02, deck_z + 0.006), "#9AA0A6", "metal"),
        _box("TrackTop", (W - 0.04, 0.04, 0.012), (0, -D / 2 + 0.02, top_z - 0.006), "#9AA0A6", "metal"),
        _sign("Header", (W, 0.015, head_h), (0, -D / 2 + 0.0075, top_z + 0.06 + head_h / 2), NAVY, {"front": 0},
              "#E9E4DA", collision=True, material="plastic"),
    ]
    for k, z in enumerate((1.10, 1.39)):  # ガラスの棚板
        parts.append(Part(f"GlassShelf{k}", "box", [W - 0.06, 0.36, 0.008], [0, 0.025, z], color=GLASS,
                          finish="glass", thin_walled=True))
    lamp, lux = _lamp("CaseLight", (W - 0.12, 0.03, 0.008), (0, -0.10, top_z - 0.0045), "#F4F8FF", 6000.0,
                      COOL_WHITE)
    parts.append(lamp)
    # ガラスの引き戸 2 枚（前後 2 本の溝。左は右へ、右は左へ開く）。中央に鍵
    joints: list[Joint] = []
    dw, dh = W / 2 + 0.01, glass_h - 0.03
    for k, (x, y, lim) in enumerate(((-W / 4 + 0.005, -D / 2 + 0.012, [0.0, 0.40]),
                                     (W / 4 - 0.005, -D / 2 + 0.028, [-0.40, 0.0]))):
        link = f"Door{k}Link"
        door = Part(f"Door{k}", "box", [dw - 0.04, 0.006, dh], [x, y, gz], color=GLASS, finish="glass",
                    thin_walled=True)
        stile_x = x + (dw / 2 - 0.02) * (1 if k == 0 else -1)
        frame = _box(f"Door{k}Stile", (0.025, 0.012, dh), (stile_x, y, gz), "#B8BCC0", "metal", collision=False)
        door.link = frame.link = link
        parts += [door, frame]
        if k == 0:
            lock = _cyl("Lock", (0.016, 0.016, 0.01), (stile_x, y - 0.011, gz - 0.10), "#D4AF37", "metal", False)
            lock.rotation = [90.0, 0.0, 0.0]
            lock.link = link
            parts.append(lock)
        joints.append(Joint(link=link, anchor=[x, y, gz], limits=lim, type="prismatic", axis="X"))
    return Product(slug="locked_medicine_case", name="第1類医薬品の施錠ガラスケース 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=95.0, static=True,
                   material="wood", joints=joints, lights=[lux],
                   description="形はドラッグストアの第1類医薬品を置く一般的な鍵付きのガラスケース（幅 900 mm・奥行き 450 mm、"
                               "下は収納、上はガラスの引き戸 2 枚とガラスの棚板 2 段・内部の照明・上の案内表示）で、"
                               "寸法・質量は代表値。引き戸（Door0Link・Door1Link）は X 方向に 400 mm まで動く。"
                               "案内表示の文字は架空。",
                   tags=["第1類医薬品", "医薬品", "ガラスケース", "ショーケース", "鍵付き", "引き戸", "店舗什器",
                         "ドラッグストア", "薬局", "locked case", "glass showcase", "pharmacy", "drugstore"], photos=[],
                   colors=Colors(label_base="#E9E4DA"), images=imgs, parts=parts, picture_places=DRUG_PLACES)


# ---------------------------------------------------------------- 調剤カウンター


def dispensing_counter() -> Product:
    W, D = 1.80, 0.60
    top_z = 1.00
    sign_z0, sign_h = 1.72, 0.26
    H = sign_z0 + sign_h
    hd = Canvas(1760, 260, None, NAVY, 9321)
    hd.gradient(0, 0, 1760, 260, "#2A5797", "#16305A")
    hd.rect(880 - 2, 30, 880 + 2, 230, fill="#FFFFFF")
    for k, (ja, en) in enumerate((("処方せん受付", "PRESCRIPTIONS"), ("お薬お渡し", "PICK UP"))):
        cx = 440 + k * 880
        _capsule(hd, cx - 330, 115, 70)
        hd.text(cx + 50, 105, ja, 92, "#FFFFFF", 900, max_w=600)
        hd.text(cx + 50, 195, en, 36, "#BFD3F0", 800, spacing=6)
    imgs = [_face(hd.array(), "plastic", 9321, 0.35, 6)]
    fr = Canvas(1760, 300, None, "#F3EFE8", 9322)  # 前板の案内（お薬相談）
    fr.gradient(0, 0, 1760, 300, "#FAF7F2", "#E7E0D4")
    fr.rect(0, 0, 1760, 16, fill=GREEN)
    fr.text(880, 120, "お薬のご相談は薬剤師へ", 80, GREEN, 900)
    fr.text(880, 220, "お薬手帳をお持ちの方はご提示ください", 40, INK, 700)
    imgs.append(_face(fr.array(), "paper", 9322, 0.35, 6))
    wood = "#D8C3A5"
    parts = [
        _box("Plinth", (W - 0.04, D - 0.10, 0.08), (0, 0.03, 0.04), GRAY, "matte"),
        _box("Body", (W, D - 0.06, top_z - 0.04 - 0.08), (0, 0.03, 0.08 + (top_z - 0.12) / 2), wood, "matte"),
        _box("Top", (W, D, 0.04), (0, 0, top_z - 0.02), "#F2EFEA", "plastic"),
        _sign("FrontSign", (W - 0.04, 0.01, 0.30), (0, -D / 2 + 0.025, 0.62), "#F3EFE8", {"front": 1}, wood,
              material="plastic"),
        # 受け渡しの口（下が 120 mm 開いた）アクリルの仕切り
        Part("Partition", "box", [W - 0.24, 0.008, 0.50], [0, 0.04, top_z + 0.12 + 0.25], color="#F1F7F9",
             finish="glass", thin_walled=True),
    ]
    for k, x in enumerate((-W / 2 + 0.10, W / 2 - 0.10)):
        parts += [_box(f"PartitionPost{k}", (0.03, 0.03, 0.62), (x, 0.04, top_z + 0.31), STEEL, "metal"),
                  _box(f"SignPost{k}", (0.04, 0.04, sign_z0 - top_z), (x * 0.95, D / 2 - 0.04,
                                                                     (top_z + sign_z0) / 2), STEEL, "metal")]
    parts.append(_sign("Header", (W, 0.02, sign_h), (0, D / 2 - 0.04, sign_z0 + sign_h / 2), NAVY, {"front": 0},
                       "#E6E8EB", collision=True, material="plastic"))
    return Product(slug="dispensing_counter", name="調剤カウンター 処方せん受付 1800mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=120.0, static=True,
                   material="wood",
                   description="形はドラッグストアの調剤コーナーの一般的な受付カウンター（幅 1800 mm・高さ 1000 mm、"
                               "受け渡しの口が開いたアクリルの仕切り・奥の支柱に「処方せん受付／お薬お渡し」の案内・"
                               "前板の案内）で、寸法・質量は代表値。天板は水平の板。案内の文字は架空。",
                   tags=["調剤", "調剤カウンター", "処方せん", "薬局", "受付", "カウンター", "店舗什器", "ドラッグストア",
                         "pharmacy counter", "prescription counter", "dispensary", "drugstore"], photos=[],
                   colors=Colors(label_base=wood), images=imgs, parts=parts, picture_places=DRUG_PLACES)


# ---------------------------------------------------------------- 待合いの 3 人掛けベンチ


def waiting_bench_3seat() -> Product:
    n, sw = 3, 0.52  # 席の数・幅
    W = n * sw + 0.06 * (n + 1)
    H = 0.80
    seat_z, seat_t = 0.42, 0.07
    cushion, frame = "#3E7CA6", "#8A9096"
    parts = [_box("Beam", (W - 0.10, 0.06, 0.06), (0, 0.02, seat_z - seat_t - 0.03), frame, "metal")]
    for k, x in enumerate((-W / 2 + 0.25, W / 2 - 0.25)):  # T 字の脚
        parts += [_box(f"Foot{k}", (0.06, 0.56, 0.03), (x, 0.0, 0.015), frame, "metal"),
                  _box(f"Leg{k}", (0.05, 0.05, seat_z - seat_t - 0.06 - 0.03), (x, 0.02,
                                                                                  0.03 + (seat_z - seat_t - 0.09) / 2),
                       frame, "metal")]
    x0 = -W / 2 + 0.06
    for k in range(n):
        cx = x0 + sw / 2 + k * (sw + 0.06)
        parts += [_box(f"Seat{k}", (sw, 0.46, seat_t), (cx, -0.05, seat_z - seat_t / 2), cushion, "matte"),
                  Part(f"Back{k}", "box", [sw, 0.06, 0.36], [cx, 0.24, seat_z + 0.20], [-8.0, 0, 0], color=cushion,
                       finish="matte")]
    for k in range(n + 1):  # ひじ掛け
        x = x0 - 0.03 + k * (sw + 0.06)
        parts.append(_box(f"Arm{k}", (0.04, 0.46, 0.04), (x, -0.03, seat_z + 0.20), frame, "metal"))
        parts.append(_box(f"ArmPost{k}", (0.04, 0.04, 0.20), (x, 0.17, seat_z + 0.10), frame, "metal"))
    return Product(slug="waiting_bench_3seat", name="待合いのベンチ 3人掛け", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, round(W, 3), depth=0.58), mass_kg=32.0, static=True,
                   material="steel",
                   description="形は薬局・病院の待合いの一般的な連結の長いす（3 人掛け・座面の高さ 420 mm・梁と T 字の脚・"
                               "ひじ掛け・少し後ろへ倒れた背）で、寸法・質量は代表値。座面は厚いクッション（棚板ではない）。",
                   tags=["ベンチ", "長いす", "待合い", "いす", "3人掛け", "薬局", "ドラッグストア", "病院",
                         "waiting bench", "beam seating", "waiting room chair", "drugstore"], photos=[],
                   colors=Colors(label_base=cushion), images=[], parts=parts)


# ---------------------------------------------------------------- 処方せん受付の吊り看板


def prescription_sign_hanging() -> Product:
    W, bh, t, drop = 0.90, 0.30, 0.012, 0.60
    H = bh + drop
    cw, ch = W * 1000, bh * 1000
    c = Canvas(cw, ch, None, GREEN, 9331)
    c.gradient(0, 0, cw, ch, mix(GREEN, "#FFFFFF", 0.12), mix(GREEN, "#000000", 0.18))
    c.rect(0, ch - 26, cw, ch - 18, fill="#FFFFFF")
    _capsule(c, 150, ch / 2 - 10, 100)
    c.text(cw / 2 + 120, 115, "処方せん受付", 92, "#FFFFFF", 900, max_w=620)
    c.text(cw / 2 + 120, 210, "PRESCRIPTIONS", 34, mix(GREEN, "#FFFFFF", 0.8), 800, spacing=6)
    img = _face(c.array(), "plastic", 9331, 0.3, 6)
    parts = [Part("Board", "box", [W, t, bh], [0, 0, bh / 2], color=GREEN, finish="plastic",
                  faces={"front": 0, "back": 0}, material="plastic", bevel=0.004, blank=mix(GREEN, "#FFFFFF", 0.05)),
             Part("Rail", "box", [W, t + 0.008, 0.016], [0, 0, bh + 0.008], color="#B9BEC4", finish="metal",
                  collision=False, material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.10, W / 2 - 0.10)):
        parts += [Part(f"Wire{k}", "cylinder", [0.0015, 0.0015, drop - 0.016], [x, 0, bh + 0.016 + (drop - 0.016) / 2],
                       color=STEEL, finish="metal", collision=False, material="steel"),
                  Part(f"CeilingPlate{k}", "cylinder", [0.040, 0.040, 0.006], [x, 0, H - 0.003], color=WHITE,
                       finish="plastic", collision=False)]
    return Product(slug="prescription_sign_hanging", name="吊り看板「処方せん受付」", shape_class="assembly",
                   category="environment", dims=Dimensions(H, W, depth=0.040), mass_kg=2.4, static=True,
                   mount="ceiling", material="plastic",
                   description="形はドラッグストアの調剤コーナーの上に天井からワイヤーで吊る一般的な案内看板（900 × 300 mm・"
                               "厚さ 12 mm、吊り下げ 600 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。"
                               "表と裏に同じ「処方せん受付」を表示する。デザインは架空。",
                   tags=["処方せん", "調剤", "薬局", "吊り看板", "案内看板", "売場看板", "ドラッグストア", "内装",
                         "prescription sign", "pharmacy sign", "hanging sign", "drugstore"], photos=[],
                   colors=Colors(label_base=GREEN), images=[img], parts=parts, picture_places=DRUG_PLACES)


# ---------------------------------------------------------------- 化粧品のテスター什器（鏡・照明付き）


def cosmetics_tester_stand() -> Product:
    W, D, H = 0.90, 0.50, 1.80
    cab_z = 0.90  # 下の収納の上面
    back_top = 1.60
    mirror_w, mirror_h, mirror_z = 0.48, 0.42, 1.36
    side_w = (W - 0.04 - mirror_w) / 2
    pink = "#F6E3E8"
    imgs = [_header(900, 200, "コスメ テスター", "COSMETICS  ご自由にお試しください", 9341, ROSE, "#F8BBD0",
                    icon=_lips)]
    mr = Canvas(480, 420, None, "#DDE3E8", 9342)  # 鏡（明るい空の映り込み）
    mr.gradient(0, 0, 480, 420, "#F2F5F8", "#B9C3CC")
    mr.polygon([(60, 0), (160, 0), (40, 420), (0, 420), (0, 200)], fill="#F7F9FB")
    imgs.append(_face(mr.array(), "screen", 9342, 0.6, 3))
    imgs.append(_price_strip(["1,650円", "1,320円", "1,980円", "1,100円", "2,200円"], 860, 9343, 165))
    y_back = D / 2 - 0.04  # 背板の前面
    cf_d, riser_d = 0.20, D - 0.04 - 0.20 - 0.02  # 手前の台・奥の段の奥行き
    yf = -D / 2 + cf_d / 2
    yr = -D / 2 + cf_d + riser_d / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.08), (0, 0.0, 0.04), GRAY, "matte"),
        _box("Cabinet", (W, D, cab_z - 0.08), (0, 0, 0.08 + (cab_z - 0.08) / 2), WHITE, "plastic"),
        _box("Counter", (W - 0.04, cf_d, 0.02), (0, yf, cab_z + 0.01), pink, "plastic"),
        _box("PriceRail", (W - 0.04, 0.012, 0.03), (0, -D / 2 - 0.006, cab_z + 0.005), "#FFFFFF", "plastic",
             {"front": 2}, collision=False),
        _box("Riser", (W - 0.04, riser_d, 0.08), (0, yr, cab_z + 0.04), WHITE, "plastic"),
        _box("RiserTop", (W - 0.04, riser_d, 0.012), (0, yr, cab_z + 0.086), pink, "plastic"),
        _box("BackPanel", (W, 0.04, back_top - cab_z), (0, D / 2 - 0.02, (cab_z + back_top) / 2), WHITE, "plastic"),
        _box("SideL", (0.02, D, back_top - cab_z), (-W / 2 + 0.01, 0, (cab_z + back_top) / 2), WHITE, "plastic"),
        _box("SideR", (0.02, D, back_top - cab_z), (W / 2 - 0.01, 0, (cab_z + back_top) / 2), WHITE, "plastic"),
        Part("Mirror", "box", [mirror_w, 0.006, mirror_h], [0, y_back - 0.003, mirror_z], color="#DDE3E8",
             finish="glossy", faces={"front": 1}, collision=False, bevel=0),
        _sign("Header", (W, 0.03, H - back_top), (0, D / 2 - 0.015, back_top + (H - back_top) / 2), ROSE,
              {"front": 0}, WHITE, collision=True, material="plastic"),
    ]
    sd, sw = 0.19, side_w - 0.03  # 鏡の左右の小さな棚（鏡の脇の照明の外）
    for k, z in enumerate((1.20, 1.44)):
        for side, sx in (("L", -1), ("R", 1)):
            x = sx * (W / 2 - 0.02 - sw / 2)
            parts.append(_box(f"SideShelf{side}{k}", (sw, sd, 0.012), (x, y_back - sd / 2, z), "#F2F2F2", "glossy"))
    lights = []
    for side, sx in (("L", -1), ("R", 1)):  # 鏡の左右の縦の LED（お客さま側へ照らす）
        lamp, lux = _lamp(f"MirrorLed{side}", (0.02, mirror_h, 0.008),
                          (sx * (mirror_w / 2 + 0.012), y_back - 0.005, mirror_z), "#FFF8F2", 4000.0, 4500.0,
                          tilt=-90.0)
        parts.append(lamp)
        lights.append(lux)
    lamp, lux = _lamp("CounterLight", (W - 0.10, 0.03, 0.008), (0, y_back - 0.02, back_top - 0.03), "#FFF8F2",
                      5000.0, 4500.0, tilt=-30.0)
    parts.append(lamp)
    lights.append(lux)
    return Product(slug="cosmetics_tester_stand", name="化粧品のテスター什器 鏡・照明付き 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.012), mass_kg=70.0, static=True,
                   material="plastic", lights=lights,
                   description="形はドラッグストアの化粧品売場の一般的な壁付けのテスター什器（幅 900 mm・台の高さ約 900 mm、"
                               "手前の台・奥の一段高い台・中央の鏡と左右の縦の照明・鏡の脇の小さな棚 2 段・上の案内表示）で、"
                               "寸法・質量は代表値。台と棚は水平の板。案内表示の文字と値段は架空。",
                   tags=["化粧品", "コスメ", "テスター", "鏡", "照明", "陳列台", "店舗什器", "ドラッグストア",
                         "cosmetics display", "tester stand", "makeup display", "drugstore"], photos=[],
                   colors=Colors(label_base=WHITE), images=imgs, parts=parts, picture_places=SHOP_PLACES)


# ---------------------------------------------------------------- 回転ラック（ネイル・小物）


def rotating_accessory_rack() -> Product:
    tiers = (0.40, 0.72, 1.04, 1.36)
    q, gap = 0.19, 0.04  # 1 区画の板の辺・支柱の通る十字の隙間
    half = gap / 2 + q
    pole_top = 1.56
    H = pole_top + 0.17
    chrome = "#C9CDD1"
    pop = Canvas(300, 150, None, ROSE, 9351)
    pop.gradient(0, 0, 300, 150, mix(ROSE, "#FFFFFF", 0.15), mix(ROSE, "#000000", 0.12))
    pop.rect(0, 112, 300, 150, fill="#FFFFFF")
    pop.text(150, 58, "ネイル・小物", 46, "#FFFFFF", 900, max_w=280)
    pop.text(150, 131, "回してお選びください", 20, ROSE, 800)
    imgs = [_face(pop.array(), "plastic", 9351, 0.35, 4)]
    parts = [_cyl("Base", (0.50, 0.50, 0.06), (0, 0, 0.03), "#3A3D42", "plastic"),
             _cyl("Bearing", (0.08, 0.08, 0.03), (0, 0, 0.075), "#2B2E31")]
    spin = [_cyl("Pole", (0.03, 0.03, pole_top - 0.09), (0, 0, 0.09 + (pole_top - 0.09) / 2), chrome)]
    for k, z in enumerate(tiers):
        # 板は支柱の十字の隙間を空けた 4 区画（1 枚の円板だと商品を並べるツールが支柱の位置にも商品を並べる）
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            c = (sx * (gap / 2 + q / 2), sy * (gap / 2 + q / 2), z)
            spin.append(_box(f"Tray{k}_{i}", (q, q, 0.012), c, "#F4F4F4", "plastic"))
        spin += [_box(f"Arm{k}X", (2 * half, 0.012, 0.012), (0, 0, z - 0.012), chrome, "metal", collision=False),
                 _box(f"Arm{k}Y", (0.012, 2 * half, 0.012), (0, 0, z - 0.012), chrome, "metal", collision=False)]
        for name, size, center in ((f"Lip{k}F", (2 * half, 0.004, 0.018), (0, -half, z + 0.009)),
                                   (f"Lip{k}B", (2 * half, 0.004, 0.018), (0, half, z + 0.009)),
                                   (f"Lip{k}L", (0.004, 2 * half, 0.018), (-half, 0, z + 0.009)),
                                   (f"Lip{k}R", (0.004, 2 * half, 0.018), (half, 0, z + 0.009))):
            spin.append(Part(name, "box", list(size), list(center), color="#F4F6F8", finish="glass",
                             collision=False, thin_walled=True, bevel=0))
    spin += [_cyl("Cap", (0.04, 0.04, 0.02), (0, 0, pole_top + 0.01), chrome),
             _sign("PopCard", (0.30, 0.006, 0.15), (0, 0, pole_top + 0.02 + 0.075), ROSE,
                   {"front": 0, "back": 0}, "#F7F5F0")]
    for p in spin:
        p.link = "SpinnerLink"
    parts += spin
    joints = [Joint(link="SpinnerLink", anchor=[0.0, 0.0, 0.09], limits=None, axis="Z")]  # 限界なし（回り続ける）
    return Product(slug="rotating_accessory_rack", name="回転ラック ネイル・小物 4段", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), 0.50, depth=0.50), mass_kg=12.0, static=True,
                   material="steel", joints=joints,
                   description="形はドラッグストアのレジ前・化粧品売場の一般的な回転式の小物ラック（丸い台・支柱・4 段の"
                               "トレー・上の POP）で、寸法・質量は代表値。トレーは支柱の通る十字の隙間を空けた 4 区画の板で、"
                               "縁の透明な立ち上がりは見た目だけ（当たり判定なし）。支柱から上（SpinnerLink）は Z 軸まわりに回る。"
                               "POP の文字は架空。",
                   tags=["回転ラック", "スピナー", "ネイル", "小物", "陳列台", "店舗什器", "ドラッグストア",
                         "spinner rack", "rotating display", "nail polish display", "drugstore"], photos=[],
                   colors=Colors(label_base=chrome), images=imgs, parts=parts, picture_places=SHOP_PLACES)


# ---------------------------------------------------------------- ベビー・介護用品の棚


def baby_care_shelf() -> Product:
    W, D, H = 1.20, 0.60, 1.80
    back_h = 1.60
    sd = D - 0.06
    imgs = [_perforated(1200, 1500, 9361, "#EEF3F8"),
            _price_strip(["1,280円", "1,580円", "980円", "2,180円", "1,480円", "1,780円", "1,080円", "1,980円"], 1160,
                         9362, 140),
            _header(1200, 200, "ベビー・介護用品", "BABY & CARE  紙おむつ・ミルク・おしりふき", 9363, "#3A8FD0",
                    "#FFD54F", icon=_baby)]
    parts = [
        _box("BasePlinth", (W, D - 0.02, 0.10), (0, -0.01, 0.05), GRAY, "matte"),
        _shelf("BaseShelf", W - 0.04, sd, (0, -0.01, 0.1075)),
        _box("BackPanel", (W, 0.03, back_h - 0.10), (0, D / 2 - 0.015, 0.10 + (back_h - 0.10) / 2), "#EEF3F8",
             "plastic", {"front": 0}),
        _box("SideLeft", (0.02, D, back_h), (-W / 2 + 0.01, 0, back_h / 2), GRAY, "metal"),
        _box("SideRight", (0.02, D, back_h), (W / 2 - 0.01, 0, back_h / 2), GRAY, "metal"),
        _sign("Header", (W, 0.02, H - back_h), (0, D / 2 - 0.02, back_h + (H - back_h) / 2), "#3A8FD0",
              {"front": 2}, "#EEF3F8", collision=True, material="plastic"),
        _box("BaseRail", (W - 0.04, 0.012, 0.035), (0, -D / 2 + 0.016, 0.10), "#FFFFFF", "plastic", {"front": 1},
             collision=False),
    ]
    for k, z in enumerate((0.62, 1.12)):  # 紙おむつの大袋（高さ約 400 mm）が入る間隔
        parts += [_shelf(f"Shelf{k + 1}", W - 0.04, sd, (0, -0.01, z)),
                  _box(f"PriceRail{k + 1}", (W - 0.04, 0.012, 0.035), (0, -0.01 - sd / 2 - 0.006, z - 0.008),
                       "#FFFFFF", "plastic", {"front": 1}, collision=False)]
    return Product(slug="baby_care_shelf", name="ベビー・介護用品の棚 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=75.0, static=True, material="steel",
                   description="形はドラッグストアのベビー用品・介護用品の売場の一般的な深型ゴンドラ（幅 1200 mm・奥行き "
                               "600 mm・高さ 1800 mm、台の棚と棚板 2 段の間隔約 500 mm で紙おむつの大袋が入る・値札レール・"
                               "案内表示）で、寸法・質量は代表値。案内表示の文字は架空。",
                   tags=["ベビー用品", "介護用品", "紙おむつ", "ゴンドラ", "陳列棚", "深型", "店舗什器", "ドラッグストア",
                         "baby care shelf", "diaper shelf", "gondola", "drugstore"], photos=[],
                   colors=Colors(label_base="#EEF3F8"), images=imgs, parts=parts, picture_places=SHOP_PLACES)


# ---------------------------------------------------------------- 紙おむつの山積み台


def diaper_stack_platform() -> Product:
    W, D = 1.20, 0.80
    deck_z = 0.15
    H = 1.30
    pop = Canvas(1100, 300, None, "#3A8FD0", 9371)
    pop.gradient(0, 0, 1100, 300, "#5AA7E0", "#2471AD")
    pop.rect(0, 220, 1100, 300, fill="#FFD54F")
    _baby(pop, 150, 110, 85)
    pop.text(640, 105, "紙おむつ まとめ買い", 100, "#FFFFFF", 900, max_w=860)
    pop.text(550, 262, "2 パックでお得  ポイント 5 倍", 48, INK, 800)
    imgs = [_face(pop.array(), "plastic", 9371, 0.35, 6)]
    parts = [
        _box("Base", (W - 0.04, D - 0.04, deck_z - 0.02), (0, 0, (deck_z - 0.02) / 2), GRAY, "matte"),
        _box("Deck", (W, D, 0.02), (0, 0, deck_z - 0.01), "#D8DADC", "metal"),
        _sign("Skirt", (W - 0.04, 0.004, 0.10), (0, -D / 2 - 0.002, 0.065), "#FFD54F", {"front": 0}, "#F7F5F0"),
    ]
    for k, x in enumerate((-W / 2 + 0.03, W / 2 - 0.03)):
        parts.append(_cyl(f"Post{k}", (0.025, 0.025, H - deck_z), (x, D / 2 + 0.0125, deck_z + (H - deck_z) / 2),
                          "#B9BEC4"))
    parts.append(_sign("PopBoard", (W - 0.02, 0.01, 0.30), (0, D / 2 + 0.0125, H - 0.16), "#3A8FD0", {"front": 0},
                       "#F7F5F0", collision=True, material="plastic"))
    return Product(slug="diaper_stack_platform", name="紙おむつの山積み台 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.03), mass_kg=30.0, static=True,
                   material="steel",
                   description="形はドラッグストアの通路やエンドに置く一般的な紙おむつの大袋を積む低い台（幅 1200 mm・"
                               "奥行き 800 mm・台の高さ 150 mm、奥の支柱に POP の看板・前に帯）で、寸法・質量は代表値。"
                               "台は水平の板で、支柱は台の外（奥）に立てる。POP の文字は架空。",
                   tags=["山積み", "平台", "紙おむつ", "特売", "POP", "店舗什器", "ドラッグストア", "stack platform",
                         "pallet display", "diaper display", "drugstore"], photos=[],
                   colors=Colors(label_base=GRAY), images=imgs, parts=parts, picture_places=SHOP_PLACES)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    medicine_shelf_gondola, locked_medicine_case, dispensing_counter, waiting_bench_3seat, prescription_sign_hanging,
    cosmetics_tester_stand, rotating_accessory_rack, baby_care_shelf, diaper_stack_platform)}
