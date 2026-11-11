"""Fictional products for an apparel store: folded clothes, a shoe box, a sneaker and a cap.

Clothes are rigid bodies (no cloth simulation): a folded T-shirt is a flat box, a stack of folded clothes is one box
textured as several layers (one part per layer would multiply the texture size). Garments on hangers are parts of the
hanger rack fixtures (apparel_fixtures.py) instead of separate products, because a rigid hanger would not stay on a
rail. No real brands or logos; prints are simple shapes and generic words. Barcodes on tags are dummy EAN-13 in the
in-store range (starting with 2). Front is -Y.
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .conv_goods import BOX_FACES, _faces
from .paint import Canvas, mix
from .products import INK, _face

WHITE = "#FFFFFF"
APPAREL_TAGS = ["衣料品", "アパレル", "服", "apparel", "clothing", "apparel store"]
STACK_FACES = {"top": 0, "bottom": 1, "front": 2, "back": 3, "right": 4, "left": 5}


def _knit(w: float, h: float, color: str, seed: int, px: float | None = 6) -> Canvas:
    """Jersey knit: fine vertical wales on a soft gradient."""
    c = Canvas(w, h, px, color, seed)
    c.gradient(0, 0, w, h, mix(color, WHITE, 0.06), mix(color, "#000000", 0.06))
    x = 0.0
    while x < w:
        c.line([(x, 0), (x, h)], mix(color, "#000000", 0.05), 0.15)
        x += 1.2
    return c


def _denim(w: float, h: float, seed: int, color: str = "#2F4A6E", px: float | None = 6) -> Canvas:
    """Denim twill: diagonal lines over an indigo gradient."""
    c = Canvas(w, h, px, color, seed)
    c.gradient(0, 0, w, h, mix(color, WHITE, 0.10), mix(color, "#000000", 0.08))
    k = -h
    while k < w:
        c.line([(k, h), (k + h, 0)], mix(color, WHITE, 0.12), 0.25)
        k += 1.6
    return c


def _fold_side(w: float, h: float, color: str, seed: int, layers: int, fabric=_knit) -> Canvas:
    """A side of folded clothes: each layer shows a rounded fold with a shadow line between layers."""
    c = fabric(w, h, color, seed) if fabric is _knit else fabric(w, h, seed, color)
    lh = h / layers
    for k in range(layers):
        y0 = k * lh
        c.rect(0, y0, w, y0 + lh * 0.12, fill=mix(color, "#000000", 0.32))  # the crease between layers
        c.line([(0, y0 + lh * 0.55), (w, y0 + lh * 0.55)], mix(color, "#000000", 0.10), lh * 0.06)
        c.rect(0, y0 + lh * 0.88, w, y0 + lh, fill=mix(color, WHITE, 0.14))  # the rounded fold catches the light
    return c


def _tee_top(W: float, D: float, color: str, seed: int, print_: str) -> Canvas:
    """A folded T-shirt from above: collar at the back edge (+Y, the top of the image), sleeves folded behind."""
    c = _knit(W, D, color, seed)
    rib = mix(color, "#000000", 0.18)
    c.ellipse(W * 0.32, -D * 0.10, W * 0.68, D * 0.12, fill=rib)  # the collar
    c.ellipse(W * 0.35, -D * 0.08, W * 0.65, D * 0.09, fill=mix(color, "#000000", 0.08))
    c.rect(W * 0.46, D * 0.01, W * 0.54, D * 0.05, fill=WHITE)  # the neck label
    for s in (0.04, 0.96):  # folded sleeve edges
        c.line([(W * s, D * 0.05), (W * s, D * 0.98)], mix(color, "#000000", 0.18), 0.8)
    if print_:
        c.text(W / 2, D * 0.42, print_, W * 0.11, mix(color, WHITE, 0.75) if color != WHITE else INK, 900,
               spacing=W * 0.01)
        c.rect(W * 0.30, D * 0.50, W * 0.70, D * 0.51, fill=mix(color, WHITE, 0.6) if color != WHITE else INK)
    c.line([(0, D * 0.97), (W, D * 0.97)], mix(color, "#000000", 0.20), 0.8)  # the folded hem
    return c


def _tag(c: Canvas, x: float, y: float, w: float, h: float, size: str, price: str) -> None:
    """A paper size / price sticker."""
    c.rect(x, y, x + w, y + h, fill=WHITE, outline="#BBBBBB", width=0.3, radius=1)
    c.rect(x, y, x + w, y + h * 0.3, fill="#C62828")
    c.text(x + w / 2, y + h * 0.15, size, h * 0.2, WHITE, 900)
    c.text(x + w / 2, y + h * 0.48, price, h * 0.17, INK, 900)
    c.barcode(x + w * 0.1, y + h * 0.62, w * 0.8, h * 0.3)


def folded_tshirt() -> Product:
    W, D, H = 250.0, 300.0, 25.0
    seed, color = 10101, "#2E4057"
    top = _tee_top(W, D, color, seed, "EVERYDAY")
    _tag(top, W * 0.70, D * 0.72, 40, 30, "M", "1,990円")
    bottom = _knit(W, D, color, seed + 1)
    bottom.line([(W / 2, 0), (W / 2, D)], mix(color, "#000000", 0.2), 0.8)  # the sleeves folded to the middle
    imgs = _faces((top, bottom, _fold_side(W, H, color, seed + 2, 1), _fold_side(W, H, color, seed + 3, 1),
                   _fold_side(D, H, color, seed + 4, 1), _fold_side(D, H, color, seed + 5, 1)), "paper", seed, 0.4)
    return Product(slug="folded_tshirt", name="Tシャツ（たたみ）", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.18, material="fabric",
                   description="形はアパレル店の棚・台にたたんで並べる一般的な半袖 T シャツ（たたんだ大きさ 250 × 300 mm・"
                               "厚さ 25 mm）を平たい箱で近似したもので、寸法・質量は代表値。布の変形はしない剛体。"
                               "胸の文字・サイズシールは架空。",
                   tags=["Tシャツ", "たたみ", "半袖", "トップス", "t-shirt", "folded t-shirt", "tee",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=color), images=imgs, faces=STACK_FACES)


def folded_tshirt_stack() -> Product:
    W, D, n, t = 250.0, 300.0, 5, 25.0
    H = n * t
    seed, color = 10111, "#B8BCC2"
    top = _tee_top(W, D, color, seed, "BASIC")
    _tag(top, W * 0.70, D * 0.72, 40, 30, "L", "1,490円")
    bottom = _knit(W, D, color, seed + 1)
    imgs = _faces((top, bottom, _fold_side(W, H, color, seed + 2, n), _fold_side(W, H, color, seed + 3, n),
                   _fold_side(D, H, color, seed + 4, n), _fold_side(D, H, color, seed + 5, n)), "paper", seed, 0.4)
    return Product(slug="folded_tshirt_stack", name="Tシャツ（たたみ）5枚重ね", shape_class="box",
                   category="household", dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.9,
                   material="fabric",
                   description="形はアパレル店の台に同じ色・サイズを重ねて並べる一般的な半袖 T シャツ 5 枚（たたんだ大きさ "
                               "250 × 300 mm・1 枚 25 mm）を 1 つの箱で近似したもので、寸法・質量は代表値。5 枚で 1 つの"
                               "剛体。胸の文字・サイズシールは架空。",
                   tags=["Tシャツ", "たたみ", "重ね", "半袖", "トップス", "t-shirt stack", "folded t-shirts",
                         "stack of shirts", *APPAREL_TAGS], photos=[], colors=Colors(label_base=color), images=imgs,
                   faces=STACK_FACES)


def folded_jeans_stack() -> Product:
    W, D, n, t = 300.0, 350.0, 3, 40.0
    H = n * t
    seed, color = 10121, "#2F4A6E"
    top = _denim(W, D, seed, color)
    stitch = "#C9923A"
    top.rect(0, 0, W, D * 0.10, fill=mix(color, "#000000", 0.12))  # the waistband
    top.line([(0, D * 0.10), (W, D * 0.10)], stitch, 0.6)
    for k in range(4):  # belt loops
        x = W * (0.12 + 0.25 * k)
        top.rect(x - 4, 0, x + 4, D * 0.13, fill=mix(color, "#000000", 0.2))
    for x0 in (W * 0.12, W * 0.58):  # back pockets with stitching
        top.polygon([(x0, D * 0.22), (x0 + W * 0.30, D * 0.22), (x0 + W * 0.28, D * 0.50),
                     (x0 + W * 0.15, D * 0.56), (x0 + W * 0.02, D * 0.50)], outline=stitch)
        top.line([(x0 + W * 0.05, D * 0.36), (x0 + W * 0.15, D * 0.42), (x0 + W * 0.25, D * 0.36)], stitch, 0.6)
    top.rect(W * 0.70, D * 0.03, W * 0.90, D * 0.09, fill="#B08A5A", radius=1)  # a leather-look patch, no logo
    top.line([(0, D * 0.97), (W, D * 0.97)], mix(color, "#000000", 0.25), 1.0)
    _tag(top, W * 0.36, D * 0.70, 56, 40, "W76", "4,990円")
    bottom = _denim(W, D, seed + 1, color)
    imgs = _faces((top, bottom, _fold_side(W, H, color, seed + 2, n, _denim), _fold_side(W, H, color, seed + 3, n, _denim),
                   _fold_side(D, H, color, seed + 4, n, _denim), _fold_side(D, H, color, seed + 5, n, _denim)),
                  "paper", seed, 0.4)
    return Product(slug="folded_jeans_stack", name="ジーンズ（たたみ）3本重ね", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=2.1, material="fabric",
                   description="形はアパレル店の棚・台に重ねて並べる一般的なジーンズ 3 本（たたんだ大きさ 300 × 350 mm・"
                               "1 本 40 mm、後ろのポケットが見える向き）を 1 つの箱で近似したもので、寸法・質量は代表値。"
                               "3 本で 1 つの剛体。革風のパッチは無地、サイズシールは架空。",
                   tags=["ジーンズ", "デニム", "パンツ", "たたみ", "重ね", "jeans", "denim", "folded jeans",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=color), images=imgs, faces=STACK_FACES)


def shoe_box() -> Product:
    W, D, H = 330.0, 200.0, 120.0
    seed, bg, accent = 10131, "#E8E2D6", "#E0582B"
    lid = 40.0  # the lid overlaps the top of the box

    def side(w: float, label: bool, sd: int) -> Canvas:
        c = Canvas(w, H, None, bg, sd)
        c.gradient(0, 0, w, H, mix(bg, WHITE, 0.2), mix(bg, "#000000", 0.05))
        c.rect(0, 0, w, lid, fill=accent)
        c.line([(0, lid), (w, lid)], mix(accent, "#000000", 0.35), 0.8)
        c.text(w / 2, lid / 2, "RUNNING SHOES", lid * 0.32, WHITE, 900, spacing=1.0, max_w=w * 0.9)
        if label:  # the size label on the end
            c.rect(w * 0.12, lid + 12, w * 0.88, H - 10, fill=WHITE, outline="#BBBBBB", width=0.4)
            c.text(w * 0.3, lid + 30, "26.0", 16, INK, 900)
            c.text(w * 0.3, lid + 48, "cm", 7, INK, 700)
            c.barcode(w * 0.5, lid + 18, w * 0.34, 32)
            c.text(w / 2, H - 15, "ネイビー / 架空の靴", 5, INK, 700, max_w=w * 0.7)
        return c

    top = Canvas(W, D, None, accent, seed + 6)
    top.gradient(0, 0, W, D, mix(accent, WHITE, 0.1), mix(accent, "#000000", 0.1))
    top.text(W / 2, D * 0.45, "RUN", D * 0.28, WHITE, 900, spacing=6)
    top.text(W / 2, D * 0.70, "FICTIONAL FOOTWEAR", D * 0.07, mix(accent, WHITE, 0.6), 800, spacing=2)
    bottom = Canvas(W, D, None, bg, seed + 7)
    bottom.gradient(0, 0, W, D, bg, mix(bg, "#000000", 0.08))
    bottom.text(W / 2, D * 0.5, NOTICE, 6, INK, 600, max_w=W * 0.9)
    bottom.rect(0, 0, W, 6, fill=accent)
    imgs = _faces((side(W, False, seed), side(W, False, seed + 1), side(D, True, seed + 2), side(D, False, seed + 3),
                   top, bottom), "paper", seed, 0.5)
    return Product(slug="shoe_box", name="スニーカーの箱", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.95, material="paper",
                   description="形は靴売場の棚に積む一般的なスニーカー 1 足入りの箱（330 × 200 × 120 mm、かぶせ蓋、端にサイズの"
                               "ラベル）で、寸法・質量は靴を含む代表値。印刷・ブランドはすべて架空。",
                   tags=["靴箱", "シューズボックス", "スニーカー", "靴", "shoe box", "shoebox", "sneaker box", "footwear", "shoe store",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=accent), images=imgs, faces=BOX_FACES)


def sneaker() -> Product:
    """One low-cut sneaker, toe toward the customer (-Y). The side view is painted on a prism's end faces."""
    L, Wd, sole_h, H = 0.27, 0.10, 0.03, 0.105
    seed, upper, sole = 10141, "#1F2A44", "#F4F2EE"
    sw, sh = L * 1000, (H - sole_h) * 1000
    # side view of the upper: toe at the left (prism x = -0.5 is the toe after rotating, see below)
    c = Canvas(sw, sh, 8, upper, seed)
    c.gradient(0, 0, sw, sh, mix(upper, WHITE, 0.10), mix(upper, "#000000", 0.10))
    c.polygon([(sw * 0.30, sh * 0.95), (sw * 0.55, sh * 0.30), (sw * 0.62, sh * 0.30), (sw * 0.40, sh * 0.95)],
              fill=WHITE)  # a plain side stripe
    c.polygon([(sw * 0.45, sh * 0.95), (sw * 0.68, sh * 0.30), (sw * 0.73, sh * 0.30), (sw * 0.52, sh * 0.95)],
              fill=WHITE)
    for k in range(5):  # eyelets
        x = sw * (0.38 + 0.06 * k)
        c.ellipse(x - 1.4, sh * (0.42 - 0.04 * k) - 1.4, x + 1.4, sh * (0.42 - 0.04 * k) + 1.4, fill="#B9BEC4")
    c.rect(sw * 0.80, sh * 0.12, sw * 0.98, sh * 0.70, fill=mix(upper, "#000000", 0.25))  # the heel counter
    c.rect(0, sh * 0.85, sw, sh, fill=mix(upper, "#000000", 0.3))
    side = _face(c.array(), "paper", seed, 0.4)
    s = Canvas(Wd * 1000, L * 1000, 6, sole, seed + 1)  # the top of the sole around the upper (heel at the top)
    s.gradient(0, 0, Wd * 1000, L * 1000, sole, mix(sole, "#000000", 0.08))
    s.rect(0, 0, Wd * 1000, 6, fill=mix(sole, "#000000", 0.15))
    sole_img = _face(s.array(), "plastic", seed + 1, 0.3)
    tongue = mix(upper, WHITE, 0.08)
    # profile in prism coordinates (x = -0.5 toe ... +0.5 heel, z = 0 bottom ... 1 top); convex
    profile = [[-0.5, 0.0], [0.5, 0.0], [0.5, 0.9], [0.32, 1.0], [-0.05, 0.85], [-0.42, 0.45], [-0.5, 0.25]]
    parts = [Part("Sole", "box", [Wd, L, sole_h], [0, 0, sole_h / 2], color=sole, finish="matte",
                  faces={"top": 1}, material="rubber", bevel=0.008),
             # rotated 90 deg about Z: prism X (length) -> -Y? +90 maps +X to +Y, so the heel (+0.5) goes to +Y
             Part("Upper", "prism", [L * 0.96, Wd * 0.92, H - sole_h], [0, 0, sole_h + (H - sole_h) / 2], [0, 0, 90],
                  color=upper, finish="matte", faces={"front": 0, "back": 0}, material="fabric", profile=profile),
             Part("Laces", "box", [Wd * 0.5, L * 0.28, 0.006], [0, -L * 0.02, H - 0.022], [-18, 0, 0], color=WHITE,
                  finish="matte", collision=False, material="fabric"),
             Part("Tongue", "box", [Wd * 0.45, 0.02, 0.03], [0, L * 0.10, H - 0.019], [-20, 0, 0], color=tongue,
                  finish="matte", collision=False, material="fabric")]
    return Product(slug="sneaker", name="スニーカー（片足）", shape_class="assembly", category="household",
                   dims=Dimensions(H, Wd, depth=L), mass_kg=0.32, material="fabric",
                   description="形は一般的なローカットのスニーカー（26 cm・幅 100 mm・高さ 105 mm）の片足を、靴底の箱と"
                               "横から見た形の柱で近似したもので、寸法・質量は代表値。つま先が正面（−Y）。靴売場の棚に"
                               "見本として片足ずつ並べる。横のラインは無地の形で、ブランドはない。",
                   tags=["スニーカー", "靴", "運動靴", "シューズ", "片足", "見本", "sneaker", "sneakers", "shoe", "footwear", "shoe store",
                         *APPAREL_TAGS], photos=[], colors=Colors(label_base=upper), images=[side, sole_img],
                   parts=parts)


def baseball_cap() -> Product:
    seed, color = 10151, "#7A2E2E"
    crown_w, crown_d, crown_h = 0.19, 0.21, 0.105
    brim_d = 0.075  # how far the brim sticks out in front of the crown
    depth = crown_d + brim_d
    yc, yb = depth / 2 - crown_d / 2, -depth / 2 + 0.08  # crown at the back, brim (0.16 deep) at the front
    c = Canvas(190.0, 210.0, 6, color, seed)  # the crown from above (front = -Y = the bottom of the image)
    c.gradient(0, 0, 190, 210, mix(color, WHITE, 0.08), mix(color, "#000000", 0.08))
    for k in range(3):  # panel seams
        c.line([(95, 105), (95 + 95 * (k - 1) * 1.2, 0)], mix(color, "#000000", 0.25), 0.8)
        c.line([(95, 105), (95 + 95 * (k - 1) * 1.2, 210)], mix(color, "#000000", 0.25), 0.8)
    cx, cy, r = 95, 160, 14  # a plain star emblem on the front panel
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.polygon(pts, fill="#F2E6C9")
    crown = _face(c.array(), "paper", seed, 0.4)
    parts = [Part("Crown", "dome", [crown_w, crown_d, crown_h], [0, yc, crown_h / 2], color=color, finish="matte",
                  faces={"top": 0}, material="fabric"),
             Part("Brim", "cylinder", [0.18, 0.16, 0.006], [0, yb, 0.004],
                  color=mix(color, "#000000", 0.1), finish="matte", material="fabric"),
             Part("Button", "cylinder", [0.014, 0.014, 0.006], [0, yc, crown_h + 0.002], color=color,
                  finish="matte", collision=False, material="fabric")]
    return Product(slug="baseball_cap", name="キャップ（野球帽）", shape_class="assembly", category="household",
                   dims=Dimensions(round(crown_h + 0.005, 3), crown_w, depth=round(depth, 3)), mass_kg=0.09,
                   material="fabric",
                   description="形は一般的な 6 枚はぎのキャップ（頭まわり 57 cm 前後、つば付き）を、半楕円体の山と楕円の"
                               "つばで近似したもので、寸法・質量は代表値。前の星形の刺しゅうは架空で、ブランドはない。",
                   tags=["キャップ", "帽子", "野球帽", "cap", "baseball cap", "hat", *APPAREL_TAGS], photos=[],
                   colors=Colors(label_base=color), images=[crown], parts=parts)


PRODUCTS = {f.__name__: f for f in (folded_tshirt, folded_tshirt_stack, folded_jeans_stack, shoe_box, sneaker,
                                    baseball_cap)}
