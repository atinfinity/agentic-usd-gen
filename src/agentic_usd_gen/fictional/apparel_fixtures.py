"""Fictional fixtures for an apparel store (garment racks with shirts, trousers or coats, folded-clothes table, cubby wall shelf, shoe wall shelf,
section sign, mannequin, fitting room, full-length mirror).

As in drug_fixtures.py, no real names or logos are used, and shapes and sizes are the common values for each kind of
fixture. Front is -Y (the customer side). Floor fixtures are kinematic (static). Surfaces that goods go on are thin
horizontal boards (so that a tool that fills shelves with goods finds them as shelves), and nothing stands on top of a board. Signs and POP can be
switched to plain with blank (Picture variant). Garments on the rack are static parts of the rack: a rigid shirt on a
rigid hanger would not stay on the rail in a physics simulation. The mannequin, the fitting room and the mirror have
no pictures (like waiting_bench_3seat).
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from .base import Product
from .book_fixtures import _board, _wood
from .drug_fixtures import _header
from .paint import Canvas, mix
from .products import INK, _box, _cyl, _face, _price_strip
from .super_fixtures import _grain, _sign

APPAREL_PLACES = ["apparel_store"]
WHITE, STEEL, CHROME, BLACK = "#F4F5F7", "#C4C8CC", "#D6DADE", "#232326"
ASH, ASH_DARK = "#D9CBB4", "#9C8466"  # white-washed ash, the usual light wood of casual clothing stores
TERRA, NAVY = "#B5563B", "#22324A"
SHIRTS = ["#FFFFFF", "#2E4057", "#B8BCC2", "#8E3B46", "#3F6B52", "#D9C9A8", "#1F1F22", "#6A8CAF"]
APPAREL_TAGS = ["店舗什器", "アパレル", "衣料品店", "服屋", "apparel store", "clothing store"]


def _tee_icon(c: Canvas, cx: float, cy: float, r: float) -> None:
    """A T-shirt silhouette (two polygons: the sleeves and the body)."""
    c.polygon([(cx - r, cy - r * 0.55), (cx - r * 0.35, cy - r * 0.85), (cx + r * 0.35, cy - r * 0.85),
               (cx + r, cy - r * 0.55), (cx + r * 0.75, cy - r * 0.15), (cx - r * 0.75, cy - r * 0.15)],
              fill="#FFFFFF")
    c.rect(cx - r * 0.52, cy - r * 0.6, cx + r * 0.52, cy + r * 0.85, fill="#FFFFFF")
    c.ellipse(cx - r * 0.2, cy - r * 0.95, cx + r * 0.2, cy - r * 0.65, fill=mix(TERRA, "#000000", 0.1))


def _shoe_icon(c: Canvas, cx: float, cy: float, r: float) -> None:
    """A sneaker silhouette."""
    c.polygon([(cx - r, cy + r * 0.5), (cx - r, cy - r * 0.1), (cx - r * 0.2, cy - r * 0.5), (cx + r * 0.3, cy - r * 0.1),
               (cx + r, cy + r * 0.15), (cx + r, cy + r * 0.5)], fill="#FFFFFF")
    c.rect(cx - r, cy + r * 0.5, cx + r, cy + r * 0.68, fill="#FFFFFF")


# ---------------------------------------------------------------- garment rack


def _rack_sign(seed: int, head: str, title: str, price: str, note: str):
    """The price sign on top of a rack post."""
    c = Canvas(220, 140, None, "#FFFFFF", seed)
    c.gradient(0, 0, 220, 140, "#FFFFFF", "#F1EEE8")
    c.rect(0, 0, 220, 34, fill=TERRA)
    c.text(110, 17, head, 15, "#FFFFFF", 900, spacing=2)
    c.text(110, 62, title, 26, INK, 900)
    c.text(110, 102, price, 30, TERRA, 900)
    c.text(110, 128, note, 10, INK, 700)
    return _face(c.array(), "paper", seed, 0.3, 4)


def _rack_frame(W: float, D: float, rail_z: float, sign_h: float) -> tuple[list[Part], float]:
    """The pipe rack without garments: rail, two posts on feet, a low wooden shelf and the price sign (image 0).
    Returns the parts and the height."""
    post_x = W / 2 - 0.02
    sign_w = 0.22
    H = rail_z + 0.02 + sign_h + 0.01
    parts = [
        Part("Rail", "cylinder", [0.03, 0.03, W - 0.02], [0, 0, rail_z], [0, 90, 0], color=CHROME, finish="metal",
             material="steel"),
        _box("ShelfBarFront", (W - 0.06, 0.02, 0.02), (0, -0.20, 0.18), CHROME, "metal"),
        _box("ShelfBarBack", (W - 0.06, 0.02, 0.02), (0, 0.20, 0.18), CHROME, "metal"),
        Part("BottomShelf", "box", [W - 0.08, 0.46, 0.015], [0, 0, 0.1975], color=ASH, finish="matte",
             material="wood", bevel=0.002),
        _sign("PriceSign", (sign_w, 0.006, sign_h), (-post_x + sign_w / 2 - 0.016, 0, rail_z + 0.02 + 0.005 + sign_h / 2), TERRA,
              {"front": 0}, "#FFFFFF", material="paper"),
    ]
    for k, x in enumerate((-post_x, post_x)):
        parts += [_box(f"Foot{k}", (0.04, D, 0.04), (x, 0, 0.02), CHROME, "metal"),
                  _cyl(f"Post{k}", (0.032, 0.032, rail_z - 0.04 + 0.015), (x, 0, 0.04 + (rail_z - 0.04 + 0.015) / 2),
                       CHROME, "metal")]
    return parts, H


def _hook(name: str, x: float, rail_z: float) -> Part:
    return Part(name, "cylinder", [0.004, 0.004, 0.06], [x, 0, rail_z - 0.03], color=CHROME, finish="metal",
                collision=False, material="steel")


def garment_rack() -> Product:
    W, D = 1.20, 0.55
    rail_z = 1.50
    sign = _rack_sign(10201, "NEW ARRIVAL", "Tシャツ", "1,990円", "税込 / S・M・L・XL")
    parts, H = _rack_frame(W, D, rail_z, 0.14)
    n = 8
    for k in range(n):  # shirts on hangers, perpendicular to the rail
        x = -0.46 + k * 0.92 / (n - 1)
        col = SHIRTS[k % len(SHIRTS)]
        parts += [
            Part(f"Shirt{k}", "box", [0.03, 0.46, 0.70], [x, 0, rail_z - 0.09 - 0.35], color=col, finish="matte",
                 material="fabric", bevel=0.01),
            Part(f"Sleeves{k}", "prism", [0.50, 0.035, 0.10], [x, 0, rail_z - 0.13], [0, 0, 90], color=col,
                 finish="matte", collision=False, material="fabric"),
            _hook(f"Hook{k}", x, rail_z),
        ]
    return Product(slug="garment_rack", name="ハンガーラック（シャツ掛け）1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=18.0, static=True,
                   material="steel",
                   description="形は衣料品店の売場の一般的なパイプのハンガーラック（幅 1200 mm・パイプの高さ 1500 mm・"
                               "下に靴や箱を置く木の棚板・柱の上の値札）で、寸法・質量は代表値。ハンガーに掛けたシャツ 8 枚は"
                               "ラックの固定の部品（布は動かない）。値札の文字は架空。",
                   tags=["ハンガーラック", "ハンガー", "パイプラック", "シャツ", "洋服掛け", "garment rack",
                         "clothing rack", "clothes rail", "hanging clothes", *APPAREL_TAGS], photos=[],
                   colors=Colors(label_base=CHROME), images=[sign], parts=parts, picture_places=APPAREL_PLACES)


PANTS = ["#2F4A6E", "#1F1F22", "#B9A684", "#6B6E73", "#3E4A3A", "#24344F", "#8A7A66", "#4A3A34"]
COATS = ["#2B2E33", "#8C6E52", "#3A4656", "#B8AE9C", "#5A2E32", "#6D7067"]


def garment_rack_pants() -> Product:
    W, D = 1.20, 0.55
    rail_z = 1.50
    sign = _rack_sign(10211, "BOTTOMS", "パンツ", "3,990円", "税込 / ウエスト 61〜91")
    parts, H = _rack_frame(W, D, rail_z, 0.14)
    n = 10
    leg_h, hip_h, leg_w, gap = 0.74, 0.24, 0.175, 0.01
    for k in range(n):  # trousers on clip hangers, hung by the waist, perpendicular to the rail
        x = -0.47 + k * 0.94 / (n - 1)
        col = PANTS[k % len(PANTS)]
        top = rail_z - 0.10  # waistband under the clip bar
        parts += [
            _hook(f"Hook{k}", x, rail_z),
            _box(f"ClipBar{k}", (0.012, 0.40, 0.012), (x, 0, top + 0.03), "#2A2C30", "plastic", collision=False),
            Part(f"Hip{k}", "box", [0.03, 2 * leg_w + gap, hip_h], [x, 0, top - hip_h / 2], color=col,
                 finish="matte", material="fabric", bevel=0.008),
            Part(f"Waist{k}", "box", [0.032, 2 * leg_w + gap, 0.035], [x, 0, top - 0.0175],
                 color=mix(col, "#000000", 0.15), finish="matte", collision=False, material="fabric"),
        ]
        for j, s in enumerate((-1, 1)):
            parts.append(Part(f"Leg{k}_{j}", "box", [0.026, leg_w, leg_h],
                              [x, s * (leg_w + gap) / 2, top - hip_h - leg_h / 2 + 0.01], color=col, finish="matte",
                              material="fabric", bevel=0.006))
    return Product(slug="garment_rack_pants", name="ハンガーラック（パンツ掛け）1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=18.0, static=True,
                   material="steel",
                   description="形は garment_rack と同じパイプのハンガーラック（幅 1200 mm・パイプの高さ 1500 mm・下に木の棚板・"
                               "柱の上の値札）に、クリップハンガーでウエストを挟んで吊ったパンツ 10 本を掛けたもので、寸法・質量は"
                               "代表値。パンツはラックの固定の部品（布は動かない）。値札の文字は架空。",
                   tags=["ハンガーラック", "ハンガー", "パイプラック", "パンツ", "ズボン", "スラックス", "チノパン",
                         "クリップハンガー", "garment rack", "clothing rack", "trousers", "pants", "hanging pants",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=CHROME), images=[sign], parts=parts,
                   picture_places=APPAREL_PLACES)


def garment_rack_coats() -> Product:
    W, D = 1.20, 0.60
    rail_z = 1.70  # coats are long, so the rail is higher than for shirts
    sign = _rack_sign(10221, "OUTER", "コート", "9,900円", "税込 / S・M・L")
    parts, H = _rack_frame(W, D, rail_z, 0.14)
    n = 6
    body_h, body_w, t = 1.00, 0.50, 0.07
    for k in range(n):  # coats on wide shoulder hangers, perpendicular to the rail
        x = -0.45 + k * 0.90 / (n - 1)
        col = COATS[k % len(COATS)]
        top = rail_z - 0.08
        parts += [
            _hook(f"Hook{k}", x, rail_z),
            Part(f"Coat{k}", "box", [t, body_w, body_h], [x, 0, top - 0.04 - body_h / 2], color=col, finish="matte",
                 material="fabric", bevel=0.015),
            Part(f"Shoulders{k}", "prism", [body_w + 0.04, t + 0.01, 0.10], [x, 0, top - 0.06], [0, 0, 90],
                 color=col, finish="matte", collision=False, material="fabric"),
            Part(f"Collar{k}", "box", [t + 0.012, 0.16, 0.06], [x, 0, top - 0.02], color=mix(col, "#000000", 0.2),
                 finish="matte", collision=False, material="fabric", bevel=0.01),
        ]
        for j, s in enumerate((-1, 1)):  # sleeves hang down the sides
            parts.append(Part(f"Sleeve{k}_{j}", "box", [t + 0.006, 0.07, 0.62],
                              [x, s * (body_w / 2 + 0.02), top - 0.10 - 0.31], color=mix(col, "#000000", 0.06),
                              finish="matte", collision=False, material="fabric", bevel=0.01))
    return Product(slug="garment_rack_coats", name="ハンガーラック（コート掛け）1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D), mass_kg=20.0, static=True,
                   material="steel",
                   description="形は衣料品店の売場の一般的なパイプのハンガーラックで、丈の長いコートが床に付かないようパイプを"
                               "高くしたもの（幅 1200 mm・パイプの高さ 1700 mm・下に木の棚板・柱の上の値札）。肩の厚いハンガーに"
                               "掛けたコート 6 着はラックの固定の部品（布は動かない）。寸法・質量は代表値、値札の文字は架空。",
                   tags=["ハンガーラック", "ハンガー", "パイプラック", "コート", "アウター", "ジャケット", "洋服掛け",
                         "garment rack", "clothing rack", "coat rack", "coats", "outerwear", "hanging coats",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=CHROME), images=[sign], parts=parts,
                   picture_places=APPAREL_PLACES)


# ---------------------------------------------------------------- folded-clothes display table


def folded_display_table() -> Product:
    W, D = 1.50, 0.90
    low_z, high_z = 0.72, 0.88
    t = 0.018
    pop_h = 0.36
    H = high_z + pop_h + 0.02
    cw = 1400
    c = Canvas(cw, 330, None, "#F7F3EC", 10211)
    c.gradient(0, 0, cw, 330, "#FBF8F3", "#EDE5D8")
    c.rect(0, 0, cw, 60, fill=NAVY)
    c.text(cw / 2, 30, "SEASON COLLECTION", 32, "#FFFFFF", 900, spacing=8)
    c.text(cw / 2, 150, "定番 T シャツ 全 8 色", 88, NAVY, 900, max_w=cw - 80)
    c.text(cw / 2, 250, "2 枚で 3,500 円（税込）", 46, TERRA, 900)
    c.rect(0, 300, cw, 330, fill=ASH_DARK)
    pop = _face(c.array(), "paper", 10211, 0.4, 6)
    skirt = _grain(1500, 700, 10212, ASH)
    back = _grain(1500, 860, 10213, ASH)
    parts = [
        _wood("FrontCabinet", (W, D / 2, low_z - t), (0, -D / 4, (low_z - t) / 2), ASH, {"front": 1}),
        _board("FrontTier", W, D / 2, (0, -D / 4, low_z - t / 2), ASH),
        _wood("BackCabinet", (W, D / 2, high_z - t), (0, D / 4, (high_z - t) / 2), ASH, {"back": 2}),
        _board("BackTier", W, D / 2, (0, D / 4, high_z - t / 2), ASH),
        _wood("Kick", (W - 0.04, D - 0.04, 0.06), (0, 0, 0.03), ASH_DARK),
        _sign("Pop", (1.40, 0.006, pop_h - 0.03), (0, D / 2 + 0.013, high_z + 0.02 + (pop_h - 0.03) / 2), NAVY,
              {"front": 0}, "#F7F3EC", collision=False, material="paper"),
    ]
    for k, x in enumerate((-0.65, 0.65)):
        parts.append(_cyl(f"PopPost{k}", (0.012, 0.012, pop_h + 0.30),
                          (x, D / 2 + 0.006, high_z - 0.30 + (pop_h + 0.30) / 2 + 0.02), STEEL, "metal",
                          collision=False))
    return Product(slug="folded_display_table", name="たたみの陳列台 2段 1500mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.02), mass_kg=55.0, static=True,
                   material="wood",
                   description="形は衣料品店の通路に置く、たたんだ T シャツ・ニット・ジーンズを色別に重ねる一般的な木の"
                               "陳列台（幅 1500 mm・奥行き 900 mm、手前の段の高さ 720 mm・奥の段 880 mm・奥の POP）で、"
                               "寸法・質量は代表値。POP の文字は架空。",
                   tags=["陳列台", "平台", "テーブル什器", "たたみ", "display table", "folding table", "clothes table",
                         *APPAREL_TAGS], photos=[],
                   colors=Colors(label_base=ASH), images=[pop, skirt, back], parts=parts,
                   picture_places=APPAREL_PLACES)


# ---------------------------------------------------------------- cubby wall shelf for folded clothes


def folded_wall_shelf() -> Product:
    W, D, H = 1.20, 0.40, 2.10
    cols, t = 3, 0.02
    head_h = 0.25
    body_h = H - head_h
    cw = (W - (cols + 1) * t) / cols
    imgs = [_header(1200, 250, "メンズ トップス", "MEN'S TOPS  T シャツ・スウェット・ニット", 10221, NAVY, band=ASH,
                    icon=_tee_icon)]
    parts = [
        _wood("Plinth", (W, D - 0.02, 0.08), (0, 0.01, 0.04), ASH_DARK),
        _wood("Back", (W, 0.02, body_h - 0.08), (0, D / 2 - 0.01, 0.08 + (body_h - 0.08) / 2), mix(ASH, "#FFFFFF", 0.3)),
        _board("Top", W, D, (0, 0, body_h - 0.009), ASH),
        _sign("Header", (W, 0.02, head_h), (0, D / 2 - 0.01, body_h + head_h / 2), NAVY, {"front": 0}, ASH,
              collision=True, material="wood"),
    ]
    for k in range(cols + 1):
        x = -W / 2 + t / 2 + k * (cw + t)
        parts.append(_wood(f"Divider{k}", (t, D - 0.02, body_h - 0.08 - 0.018), (x, -0.01, 0.08 + (body_h - 0.098) / 2),
                           ASH))
    levels = [0.08 + 0.009 + k * 0.35 for k in range(5)]  # the floor of each cubby (0.35 m pitch)
    for k in range(cols):
        x = -W / 2 + t + cw / 2 + k * (cw + t)
        for j, z in enumerate(levels):
            parts.append(_board(f"Shelf{k}_{j}", cw, D - 0.04, (x, -0.01, z), ASH))
    return Product(slug="folded_wall_shelf", name="たたみの壁面棚（ボックス 3×5）1200mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=85.0, static=True, material="wood",
                   description="形は衣料品店の壁際で、たたんだ服を色・サイズ別に入れる一般的なボックス棚（幅 1200 mm・"
                               "奥行き 400 mm・高さ 2100 mm、3 列 × 5 段のボックス・上の案内表示）で、寸法・質量は代表値。"
                               "案内表示の文字は架空。",
                   tags=["壁面棚", "ボックス棚", "棚", "たたみ", "wall shelf", "cubby shelf", "folded clothes shelf",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=ASH), images=imgs, parts=parts,
                   picture_places=APPAREL_PLACES)


# ---------------------------------------------------------------- shoe wall shelf


def shoe_wall_shelf() -> Product:
    W, D, H = 0.90, 0.35, 1.80
    head_h = 0.20
    body_h = H - head_h
    sd = 0.30
    zs = [0.10 + k * 0.29 for k in range(5)] + [1.48]
    imgs = [_header(900, 200, "シューズ", "SHOES  スニーカー・サンダル", 10231, BLACK, band=TERRA, icon=_shoe_icon),
            _price_strip(["5,990円", "7,990円", "3,990円", "6,490円", "4,990円"], 870, 10232, 35)]
    parts = [
        _box("Plinth", (W, D - 0.02, 0.08), (0, 0.01, 0.04), BLACK, "matte"),
        _box("Back", (W, 0.02, body_h - 0.08), (0, D / 2 - 0.01, 0.08 + (body_h - 0.08) / 2), WHITE, "matte"),
        _box("SideLeft", (0.02, D, body_h), (-W / 2 + 0.01, 0, body_h / 2), BLACK, "matte"),
        _box("SideRight", (0.02, D, body_h), (W / 2 - 0.01, 0, body_h / 2), BLACK, "matte"),
        _sign("Header", (W, 0.02, head_h), (0, D / 2 - 0.01, body_h + head_h / 2), BLACK, {"front": 0}, WHITE,
              collision=True, material="plastic"),
    ]
    ys = D / 2 - 0.02 - sd / 2
    for k, z in enumerate(zs):
        parts += [_box(f"Shelf{k + 1}", (W - 0.04, sd, 0.015), (0, ys, z), WHITE, "plastic"),
                  _box(f"PriceRail{k + 1}", (W - 0.04, 0.012, 0.035), (0, ys - sd / 2 - 0.006, z - 0.008), WHITE,
                       "plastic", {"front": 1}, collision=False)]
    return Product(slug="shoe_wall_shelf", name="靴の壁面棚 900mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=40.0, static=True, material="wood",
                   description="形は衣料品店・靴売場の壁際の一般的な靴の見本棚（幅 900 mm・奥行き 350 mm・高さ 1800 mm、"
                               "水平の棚板 6 段・値札レール・上の案内表示）で、寸法・質量は代表値。実物は前へ傾けた棚板も"
                               "多いが、商品を並べられるように水平にした。値札・案内表示の文字は架空。",
                   tags=["靴棚", "シューズラック", "壁面棚", "靴", "スニーカー", "shoe shelf", "shoe display",
                         "shoe rack", *APPAREL_TAGS], photos=[], colors=Colors(label_base=WHITE), images=imgs,
                   parts=parts, picture_places=[*APPAREL_PLACES, "shoe_store"])


# ---------------------------------------------------------------- section sign (hanging)


def apparel_section_sign() -> Product:
    W, bh, t, drop = 0.90, 0.25, 0.012, 0.60
    H = bh + drop
    cw, ch = W * 1000, bh * 1000

    def side(title: str, sub: str, bg: str, seed: int):
        c = Canvas(cw, ch, None, bg, seed)
        c.gradient(0, 0, cw, ch, mix(bg, "#FFFFFF", 0.12), mix(bg, "#000000", 0.18))
        c.rect(0, ch - 24, cw, ch - 16, fill=ASH)
        _tee_icon(c, 130, ch / 2 - 8, 70)
        c.text(cw / 2 + 100, 100, title, 84, "#FFFFFF", 900, max_w=620)
        c.text(cw / 2 + 100, 182, sub, 30, mix(bg, "#FFFFFF", 0.75), 800, spacing=5, max_w=620)
        return _face(c.array(), "plastic", seed, 0.3, 6)

    imgs = [side("メンズ", "MEN'S", NAVY, 10241), side("レディース", "WOMEN'S", TERRA, 10242)]
    parts = [Part("Board", "box", [W, t, bh], [0, 0, bh / 2], color=NAVY, finish="plastic",
                  faces={"front": 0, "back": 1}, material="plastic", bevel=0.004, blank=mix(NAVY, "#FFFFFF", 0.05)),
             Part("Rail", "box", [W, t + 0.008, 0.016], [0, 0, bh + 0.008], color="#B9BEC4", finish="metal",
                  collision=False, material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.10, W / 2 - 0.10)):
        parts += [Part(f"Wire{k}", "cylinder", [0.0015, 0.0015, drop - 0.016], [x, 0, bh + 0.016 + (drop - 0.016) / 2],
                       color=STEEL, finish="metal", collision=False, material="steel"),
                  Part(f"CeilingPlate{k}", "cylinder", [0.040, 0.040, 0.006], [x, 0, H - 0.003], color=WHITE,
                       finish="plastic", collision=False)]
    return Product(slug="apparel_section_sign", name="衣料品店の吊り看板「メンズ／レディース」", shape_class="assembly",
                   category="environment", dims=Dimensions(H, W, depth=0.040), mass_kg=2.2, static=True,
                   mount="ceiling", material="plastic",
                   description="形は衣料品店の売場の上に天井からワイヤーで吊る一般的な案内看板（900 × 250 mm・厚さ 12 mm、"
                               "吊り下げ 600 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。表は"
                               "「メンズ」、裏は「レディース」。デザインは架空。",
                   tags=["吊り看板", "案内看板", "売場看板", "メンズ", "レディース", "内装", "hanging sign",
                         "section sign", *APPAREL_TAGS], photos=[],
                   colors=Colors(label_base=NAVY), images=imgs, parts=parts, picture_places=APPAREL_PLACES)


# ---------------------------------------------------------------- mannequin


def mannequin_standing() -> Product:
    skin, shirt, pants = "#ECE9E4", "#2E4057", "#2F4A6E"
    torso = [[0, 0], [0.85, 0], [0.92, 0.15], [0.80, 0.42], [0.92, 0.68], [1.0, 0.86], [0.75, 0.95], [0.30, 1.0],
             [0, 1.0]]
    head = [[0, 0], [0.6, 0.03], [0.95, 0.3], [1.0, 0.5], [0.9, 0.75], [0.6, 0.93], [0, 1.0]]
    parts = [
        _cyl("Base", (0.35, 0.35, 0.02), (0, 0, 0.01), CHROME, "metal"),
        _cyl("Rod", (0.02, 0.02, 0.10), (0, 0.06, 0.07), CHROME, "metal"),
        Part("Torso", "revolve", [0.36, 0.22, 0.62], [0, 0, 1.17], color=shirt, finish="matte", material="fabric",
             profile=torso),
        _cyl("Neck", (0.10, 0.10, 0.10), (0, 0, 1.53), skin, "plastic"),
        Part("Head", "revolve", [0.17, 0.20, 0.22], [0, 0, 1.69], color=skin, finish="plastic", material="plastic",
             profile=head),
    ]
    for k, x in enumerate((-0.07, 0.07)):
        parts.append(Part(f"Leg{k}", "cylinder", [0.13, 0.13, 0.84], [x, 0, 0.44], color=pants, finish="matte",
                          material="fabric"))
    for k, x in enumerate((-0.215, 0.215)):
        parts += [Part(f"Sleeve{k}", "cylinder", [0.08, 0.08, 0.22], [x, 0, 1.36], color=shirt, finish="matte",
                       material="fabric"),
                  Part(f"Arm{k}", "cylinder", [0.06, 0.06, 0.42], [x, 0, 1.04], color=skin, finish="plastic",
                       material="plastic")]
    return Product(slug="mannequin_standing", name="マネキン（全身・立ち姿）", shape_class="assembly", category="fixture",
                   dims=Dimensions(1.80, 0.50, depth=0.35), mass_kg=12.0, static=True, material="plastic",
                   description="形は衣料品店の一般的な全身の立ち姿のマネキン（身長 1800 mm・丸い台座）を、楕円の胴・"
                               "円柱の手足・卵形の頭で近似したもので、寸法・質量は代表値。紺の T シャツとジーンズを着た形"
                               "（服は固定の部品）。顔は無地。",
                   tags=["マネキン", "ディスプレイ", "人台", "mannequin", "display mannequin", "dress form",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=skin), images=[], parts=parts)


# ---------------------------------------------------------------- fitting room


def _mirror_img(w_mm: float, h_mm: float, seed: int):
    c = Canvas(w_mm, h_mm, None, "#DDE3E8", seed)  # a mirror: a bright reflection streak
    c.gradient(0, 0, w_mm, h_mm, "#F2F5F8", "#B9C3CC")
    c.polygon([(w_mm * 0.15, 0), (w_mm * 0.4, 0), (w_mm * 0.1, h_mm), (0, h_mm), (0, h_mm * 0.4)], fill="#F7F9FB")
    return _face(c.array(), "screen", seed, 0.6, 3)


def fitting_room() -> Product:
    W, D, H = 1.00, 1.00, 2.10
    t = 0.03
    wall, curtain = "#EFEBE4", "#5B6B5A"
    parts = [
        _box("Floor", (W, D, 0.06), (0, 0, 0.03), ASH_DARK, "matte"),
        _box("BackWall", (W, t, H), (0, D / 2 - t / 2, H / 2), wall, "matte"),
        _box("SideLeft", (t, D - t, H), (-W / 2 + t / 2, -t / 2, H / 2), wall, "matte"),
        _box("SideRight", (t, D - t, H), (W / 2 - t / 2, -t / 2, H / 2), wall, "matte"),
        _box("Lintel", (W - 2 * t, t, 0.12), (0, -D / 2 + t / 2, H - 0.06), wall, "matte"),
        Part("CurtainRail", "cylinder", [0.02, 0.02, W - 2 * t], [0, -D / 2 + 0.05, H - 0.14], [0, 90, 0],
             color=CHROME, finish="metal", collision=False, material="steel"),
        # the curtain is drawn two thirds of the way (the opening on the right)
        _box("Curtain", (0.62, 0.03, 1.86), (-W / 2 + t + 0.31, -D / 2 + 0.05, 0.08 + 0.93), curtain, "matte"),
        Part("Mirror", "box", [0.45, 0.006, 1.40], [0, D / 2 - t - 0.003, 1.05], color="#DDE3E8", finish="glossy",
             faces={"front": 0}, collision=False, bevel=0),
        _box("Stool", (0.32, 0.32, 0.40), (W / 2 - t - 0.18, D / 2 - t - 0.18, 0.06 + 0.20), ASH, "matte"),
    ]
    for k, z in enumerate((1.55, 1.70)):  # hooks on the left wall
        parts.append(Part(f"Hook{k}", "cylinder", [0.012, 0.012, 0.06], [-W / 2 + t + 0.03, 0.15 * k, z], [0, 90, 0],
                          color=CHROME, finish="metal", collision=False, material="steel"))
    return Product(slug="fitting_room", name="試着室 1000mm 角", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=120.0, static=True, material="wood",
                   description="形は衣料品店の一般的な 1 人用の試着室（幅・奥行き 1000 mm・高さ 2100 mm、一段上がった床・"
                               "三方の壁・奥の姿見・小さな腰掛け・壁のフック・正面のカーテン）で、寸法・質量は代表値。"
                               "カーテンは 3 分の 2 まで閉めた形の固定の板（開閉しない）。入口は正面の右側。",
                   tags=["試着室", "フィッティングルーム", "更衣室", "カーテン", "fitting room", "changing room",
                         "dressing room", *APPAREL_TAGS], photos=[], colors=Colors(label_base=wall),
                   images=[_mirror_img(450, 1400, 10251)], parts=parts)


# ---------------------------------------------------------------- full-length mirror


def full_length_mirror() -> Product:
    W, D = 0.45, 0.40
    base_h, frame_h = 0.06, 1.56
    H = base_h + frame_h
    parts = [
        _box("Base", (W, D, base_h), (0, 0, base_h / 2), BLACK, "matte"),
        Part("Frame", "box", [W, 0.03, frame_h], [0, 0.05, base_h + frame_h / 2], color=BLACK, finish="matte",
             material="wood"),
        Part("Mirror", "box", [W - 0.05, 0.006, frame_h - 0.05], [0, 0.05 - 0.018, base_h + frame_h / 2],
             color="#DDE3E8", finish="glossy", faces={"front": 0}, collision=False, bevel=0),
    ]
    return Product(slug="full_length_mirror", name="姿見（スタンドミラー）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D), mass_kg=9.0, static=True, material="glass",
                   description="形は衣料品店の売場・試着室の前に置く一般的な自立式の姿見（幅 450 mm・高さ 1620 mm、黒い枠・"
                               "重い台座）で、寸法・質量は代表値。鏡は明るい映り込みを描いた光沢の板（実際には映らない）。",
                   tags=["姿見", "鏡", "スタンドミラー", "ミラー", "full-length mirror", "standing mirror", "mirror",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=BLACK),
                   images=[_mirror_img(400, 1510, 10261)], parts=parts)


PRODUCTS = {f.__name__: f for f in (garment_rack, garment_rack_pants, garment_rack_coats, folded_display_table,
                                    folded_wall_shelf, shoe_wall_shelf, apparel_section_sign, mannequin_standing, fitting_room, full_length_mirror)}
