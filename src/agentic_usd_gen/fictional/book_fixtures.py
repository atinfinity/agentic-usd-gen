"""Fictional fixtures for a bookstore (wall bookcase, double-sided island bookcase, stepped flat table, checkout counter,
hanging section sign).

As in drug_fixtures.py, no real names or logos are used, and shapes and sizes are the common values for each kind of
fixture. Front is -Y (the customer side). Floor fixtures are kinematic (static). Surfaces that books go on are thin
horizontal boards so that a tool that fills shelves with goods finds them as shelves, and nothing stands on top of a board.
Signs and POP with store copy can be switched to plain with blank (Picture variant).
Bookstore 平台 are often slightly tilted toward the customer; here both tiers are level so that fill can use them.
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from .base import Product
from .drug_fixtures import _header
from .paint import Canvas, mix
from .products import INK, _box, _cyl, _face
from .super_fixtures import _grain, _sign

BOOK_PLACES = ["bookstore"]  # the section signs only fit a bookstore
OAK, OAK_DARK, WALNUT = "#C9A27A", "#8F6A45", "#6B4A2F"
WHITE, STEEL, NAVY, GREEN, BRICK = "#F4F5F7", "#C4C8CC", "#203A5C", "#2F6B4F", "#9C3D2E"


def _book_icon(c: Canvas, cx: float, cy: float, r: float) -> None:
    """An open book (two pages and a center crease)."""
    for s in (-1, 1):
        c.polygon([(cx, cy - r * 0.35), (cx + s * r * 0.95, cy - r * 0.55), (cx + s * r * 0.95, cy + r * 0.45),
                   (cx, cy + r * 0.62)], fill="#FFFFFF")
        for k in range(3):
            y = cy - r * 0.25 + k * r * 0.22
            c.line([(cx + s * r * 0.15, y), (cx + s * r * 0.78, y - r * 0.12)], "#9AA6B2", r * 0.04)
    c.line([(cx, cy - r * 0.35), (cx, cy + r * 0.62)], "#9AA6B2", r * 0.05)


def _board(name, w, d, center, color=OAK) -> Part:
    """A shelf board (thin, horizontal, wood)."""
    return Part(name=name, shape="box", size=[w, d, 0.018], center=list(center), color=color, finish="matte",
                material="wood", bevel=0.002)


def _wood(name, size, center, color=OAK, faces=None, collision=True) -> Part:
    return Part(name=name, shape="box", size=list(size), center=list(center), color=color, finish="matte",
                faces=faces, collision=collision, material="wood")


# ---------------------------------------------------------------- wall bookcase


def bookcase_wall() -> Product:
    W, D, H = 0.90, 0.36, 2.10
    body_h = 1.90  # top of the side panels; the header sign sits above
    sd = 0.30  # shelf depth
    y_back = D / 2 - 0.02  # front face of the back panel
    ys = y_back - sd / 2
    imgs = [_grain(860, 1780, 9851, mix(OAK, "#FFFFFF", 0.15)),
            _header(900, 200, "文芸・小説", "LITERATURE  単行本・文庫・新書", 9852, NAVY, band=OAK, icon=_book_icon),
            _grain(360, 1900, 9853, OAK)]
    parts = [
        _wood("Plinth", (W - 0.04, D - 0.04, 0.08), (0, -0.01, 0.04), WALNUT),
        _board("BaseShelf", W - 0.04, sd, (0, ys, 0.089)),
        _wood("BackPanel", (W - 0.04, 0.02, body_h - 0.08), (0, D / 2 - 0.01, 0.08 + (body_h - 0.08) / 2),
              mix(OAK, "#FFFFFF", 0.15), {"front": 0}),
        _wood("SideLeft", (0.02, D, body_h), (-W / 2 + 0.01, 0, body_h / 2), OAK, {"left": 2, "right": 2}),
        _wood("SideRight", (0.02, D, body_h), (W / 2 - 0.01, 0, body_h / 2), OAK, {"left": 2, "right": 2}),
        _wood("TopBoard", (W, D, 0.02), (0, 0, body_h - 0.01), OAK),
        _sign("Header", (W, 0.02, H - body_h), (0, D / 2 - 0.03, body_h + (H - body_h) / 2), NAVY, {"front": 1},
              mix(NAVY, "#FFFFFF", 0.1), collision=True, material="wood"),
    ]
    # six shelves at a 0.28 m pitch above the base shelf (tall enough for a 四六判 hardcover standing up)
    for k in range(6):
        parts.append(_board(f"Shelf{k + 1}", W - 0.04, sd, (0, ys, 0.37 + 0.28 * k)))
    return Product(slug="bookcase_wall", name="書店の壁面の本棚 900mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=60.0, static=True, material="wood",
                   description="形は書店の壁際に並べる一般的な木製の本棚（幅 900 mm・奥行き 360 mm・高さ 2100 mm、"
                               "台輪の上の棚と棚板 6 段・背板・上の分類の表示）で、寸法・質量は代表値。単行本を立てて並べ"
                               "られる棚の間隔（280 mm）。表示の文字は架空。",
                   tags=["本棚", "書棚", "壁面", "書架", "店舗什器", "書店", "本屋", "bookcase", "bookshelf",
                         "wall shelf", "bookstore"], photos=[],
                   colors=Colors(label_base=OAK), images=imgs, parts=parts, picture_places=BOOK_PLACES)


# ---------------------------------------------------------------- double-sided island bookcase


def bookcase_island_double() -> Product:
    W, D, H = 1.20, 0.70, 1.50
    body_h = 1.32
    sd = 0.30
    imgs = [_grain(1160, 1240, 9861, mix(OAK, "#FFFFFF", 0.15)),
            _header(1200, 180, "コミック・ライトノベル", "COMICS  新刊・話題の本", 9862, BRICK, band=OAK,
                    icon=_book_icon),
            _grain(700, 1320, 9863, OAK)]
    parts = [
        _wood("Plinth", (W - 0.04, D - 0.06, 0.08), (0, 0, 0.04), WALNUT),
        _wood("CenterPanel", (W - 0.04, 0.03, body_h - 0.08), (0, 0, 0.08 + (body_h - 0.08) / 2),
              mix(OAK, "#FFFFFF", 0.15), {"front": 0, "back": 0}),
        _wood("SideLeft", (0.02, D, body_h), (-W / 2 + 0.01, 0, body_h / 2), OAK, {"left": 2, "right": 2}),
        _wood("SideRight", (0.02, D, body_h), (W / 2 - 0.01, 0, body_h / 2), OAK, {"left": 2, "right": 2}),
        _sign("Header", (W - 0.04, 0.03, H - body_h), (0, 0, body_h + (H - body_h) / 2), BRICK,
              {"front": 1, "back": 1}, mix(BRICK, "#FFFFFF", 0.1), collision=True, material="wood"),
    ]
    for side, s in (("Front", -1), ("Back", 1)):
        ys = s * (0.015 + sd / 2 + 0.005)
        parts.append(_board(f"{side}BaseShelf", W - 0.04, sd, (0, ys, 0.089)))
        for k in range(4):
            parts.append(_board(f"{side}Shelf{k + 1}", W - 0.04, sd, (0, ys, 0.37 + 0.28 * k)))
    return Product(slug="bookcase_island_double", name="書店の両面の島の本棚 1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=80.0, static=True, material="wood",
                   description="形は書店の売場の中ほどに置く一般的な両面の低い本棚（幅 1200 mm・奥行き 700 mm・高さ 1500 mm、"
                               "中央の仕切りの両側に台輪の上の棚と棚板 4 段・上の分類の表示）で、寸法・質量は代表値。"
                               "見通しのよい低い棚。表示の文字は架空。",
                   tags=["本棚", "書棚", "両面", "島", "書架", "店舗什器", "書店", "本屋", "コミック", "bookcase",
                         "double sided bookshelf", "island shelf", "bookstore"], photos=[],
                   colors=Colors(label_base=OAK), images=imgs, parts=parts, picture_places=BOOK_PLACES)


# ---------------------------------------------------------------- stepped flat table (平台)


def book_flat_table() -> Product:
    W, D = 1.20, 0.90
    low_z, high_z = 0.70, 0.82  # tops of the front and back tiers
    t = 0.018
    pop_h = 0.36
    H = high_z + pop_h + 0.02
    cw = 1100
    c = Canvas(cw, 330, None, "#FFF4D6", 9871)
    c.gradient(0, 0, cw, 330, "#FFF8E6", "#FBE7B4")
    c.rect(0, 0, cw, 60, fill=BRICK)
    c.text(cw / 2, 30, "書店員のおすすめ", 34, "#FFFFFF", 900, spacing=4)
    c.text(cw / 2, 150, "話題の本・今週の新刊", 86, BRICK, 900, max_w=cw - 80)
    c.text(cw / 2, 250, "NEW RELEASES & STAFF PICKS", 30, mix(BRICK, "#000000", 0.2), 800, spacing=4)
    c.rect(0, 300, cw, 330, fill=OAK)
    pop = _face(c.array(), "paper", 9871, 0.4, 6)
    skirt = _grain(1200, 700, 9872, OAK)
    back = _grain(1200, 800, 9873, OAK)
    parts = [
        # the front tier: a low cabinet under the front half
        _wood("FrontCabinet", (W, D / 2, low_z - t), (0, -D / 4, (low_z - t) / 2), OAK,
              {"front": 1}),
        _board("FrontTier", W, D / 2, (0, -D / 4, low_z - t / 2)),
        # the back tier: a taller cabinet under the back half (its top is a separate board, not on the front tier)
        _wood("BackCabinet", (W, D / 2, high_z - t), (0, D / 4, (high_z - t) / 2), OAK,
              {"back": 2}),
        _board("BackTier", W, D / 2, (0, D / 4, high_z - t / 2)),
        _wood("Kick", (W - 0.04, D - 0.04, 0.06), (0, 0, 0.03), WALNUT),
        # the POP stands behind the back tier on two posts fixed to the back of the cabinet
        _sign("Pop", (1.10, 0.006, pop_h - 0.03), (0, D / 2 + 0.013, high_z + 0.02 + (pop_h - 0.03) / 2), BRICK,
              {"front": 0}, "#FFF4D6", collision=False, material="paper"),
    ]
    for k, x in enumerate((-0.50, 0.50)):
        parts.append(_cyl(f"PopPost{k}", (0.012, 0.012, pop_h + 0.30), (x, D / 2 + 0.006,
                                                                          high_z - 0.30 + (pop_h + 0.30) / 2 + 0.02),
                          STEEL, "metal", collision=False))
    return Product(slug="book_flat_table", name="書店の平台 2段 1200mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D + 0.02), mass_kg=45.0, static=True, material="wood",
                   description="形は書店の入口近くで新刊を表紙を上にして積む一般的な平台（幅 1200 mm・奥行き 900 mm、"
                               "手前の段の高さ 700 mm・奥の段 820 mm の 2 段・奥の POP）で、寸法・質量は代表値。実物は"
                               "手前へ少し傾いたものが多いが、商品を並べられるように 2 段とも水平にした。POP の文字は架空。",
                   tags=["平台", "平積み", "新刊", "台", "陳列台", "店舗什器", "書店", "本屋", "book table",
                         "display table", "new releases", "bookstore"], photos=[],
                   colors=Colors(label_base=OAK), images=[pop, skirt, back], parts=parts, picture_places=BOOK_PLACES)


# ---------------------------------------------------------------- checkout counter


def book_checkout_counter() -> Product:
    W, D, H = 1.80, 0.65, 1.00
    top_t = 0.03
    cw = 1760
    c = Canvas(cw, 820, None, mix(OAK, "#FFFFFF", 0.2), 9881)
    c.gradient(0, 0, cw, 820, mix(OAK, "#FFFFFF", 0.3), mix(OAK, "#FFFFFF", 0.05))
    c.rect(0, 120, cw, 330, fill=NAVY)
    c.text(cw / 2, 200, "お会計", 110, "#FFFFFF", 900)
    c.text(cw / 2, 290, "CASHIER", 40, mix(NAVY, "#FFFFFF", 0.7), 800, spacing=8)
    c.text(cw / 2, 430, "ブックカバーをおかけします", 60, INK, 800)
    c.text(cw / 2, 520, "図書カード・各種キャッシュレス決済がご利用いただけます", 40, INK, 600, max_w=cw - 120)
    for k in range(12):
        x = 80 + k * (cw - 160) / 11
        c.rect(x - 30, 640, x + 30, 760, fill=mix(OAK, "#000000", 0.08 + 0.04 * (k % 3)), radius=4)
    front = _face(c.array(), "paper", 9881, 0.4, 6)
    parts = [
        _box("FrontPanel", (W, 0.03, H - top_t - 0.06), (0, -D / 2 + 0.015, 0.06 + (H - top_t - 0.06) / 2),
             mix(OAK, "#FFFFFF", 0.2), "matte", {"front": 0}, blank=mix(OAK, "#FFFFFF", 0.2)),
        _wood("Kick", (W - 0.04, D - 0.06, 0.06), (0, 0.0, 0.03), WALNUT),
        _wood("SideLeft", (0.03, D, H - top_t), (-W / 2 + 0.015, 0, (H - top_t) / 2), OAK),
        _wood("SideRight", (0.03, D, H - top_t), (W / 2 - 0.015, 0, (H - top_t) / 2), OAK),
        _box("Top", (W, D, top_t), (0, 0, H - top_t / 2), "#F1EEE8", "plastic"),
        # staff side (+Y): a shelf for book covers and bags halfway down, and the bottom board
        _board("StaffShelf", W - 0.06, D - 0.10, (0, 0.03, 0.50)),
        _board("StaffBase", W - 0.06, D - 0.10, (0, 0.03, 0.069)),
    ]
    return Product(slug="book_checkout_counter", name="書店のレジカウンター 1800mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=70.0, static=True, material="wood",
                   description="形は書店の一般的なレジカウンター（幅 1800 mm・奥行き 650 mm・高さ 1000 mm、天板・お客さま側の"
                               "前板・店員側の中棚と下の棚）で、寸法・質量は代表値。レジ・端末は載せていない（別のアセットを"
                               "天板に置く）。前板の文字は架空。",
                   tags=["レジカウンター", "会計", "カウンター", "レジ台", "店舗什器", "書店", "本屋",
                         "checkout counter", "cashier counter", "bookstore"], photos=[],
                   colors=Colors(label_base=OAK), images=[front], parts=parts, picture_places=BOOK_PLACES)


# ---------------------------------------------------------------- hanging section sign


def bookstore_section_sign() -> Product:
    W, bh, t, drop = 0.90, 0.25, 0.012, 0.60
    H = bh + drop
    cw, ch = W * 1000, bh * 1000

    def side(title: str, sub: str, bg: str, seed: int):
        c = Canvas(cw, ch, None, bg, seed)
        c.gradient(0, 0, cw, ch, mix(bg, "#FFFFFF", 0.12), mix(bg, "#000000", 0.18))
        c.rect(0, ch - 24, cw, ch - 16, fill=OAK)
        _book_icon(c, 130, ch / 2 - 8, 85)
        c.text(cw / 2 + 100, 100, title, 84, "#FFFFFF", 900, max_w=620)
        c.text(cw / 2 + 100, 182, sub, 30, mix(bg, "#FFFFFF", 0.75), 800, spacing=5, max_w=620)
        return _face(c.array(), "plastic", seed, 0.3, 6)

    imgs = [side("文芸・文庫", "LITERATURE / PAPERBACKS", NAVY, 9891), side("コミック", "COMICS", BRICK, 9892)]
    parts = [Part("Board", "box", [W, t, bh], [0, 0, bh / 2], color=NAVY, finish="plastic",
                  faces={"front": 0, "back": 1}, material="plastic", bevel=0.004, blank=mix(NAVY, "#FFFFFF", 0.05)),
             Part("Rail", "box", [W, t + 0.008, 0.016], [0, 0, bh + 0.008], color="#B9BEC4", finish="metal",
                  collision=False, material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.10, W / 2 - 0.10)):
        parts += [Part(f"Wire{k}", "cylinder", [0.0015, 0.0015, drop - 0.016], [x, 0, bh + 0.016 + (drop - 0.016) / 2],
                       color=STEEL, finish="metal", collision=False, material="steel"),
                  Part(f"CeilingPlate{k}", "cylinder", [0.040, 0.040, 0.006], [x, 0, H - 0.003], color=WHITE,
                       finish="plastic", collision=False)]
    return Product(slug="bookstore_section_sign", name="書店の吊り看板「文芸・文庫／コミック」", shape_class="assembly",
                   category="environment", dims=Dimensions(H, W, depth=0.040), mass_kg=2.2, static=True,
                   mount="ceiling", material="plastic",
                   description="形は書店の棚の上に天井からワイヤーで吊る一般的な売場の案内看板（900 × 250 mm・厚さ 12 mm、"
                               "吊り下げ 600 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。表は"
                               "「文芸・文庫」、裏は「コミック」。デザインは架空。",
                   tags=["吊り看板", "案内看板", "売場看板", "分類", "文芸", "コミック", "書店", "本屋", "内装",
                         "hanging sign", "section sign", "bookstore sign", "bookstore"], photos=[],
                   colors=Colors(label_base=NAVY), images=imgs, parts=parts, picture_places=BOOK_PLACES)


PRODUCTS = {f.__name__: f for f in (bookcase_wall, bookcase_island_double, book_flat_table, book_checkout_counter,
                                    bookstore_section_sign)}
