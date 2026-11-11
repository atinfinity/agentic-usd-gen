"""Fictional designs for specialty shop fixtures and goods: a bicycle shop, woven baskets, a wagashi shop, a record shop, a sports shop,
a furniture shop, a cosmetics shop, a souvenir shop and an Asian grocery.

No real product names, brands or logos; shapes and sizes are typical values. Front is -Y.
Goods (helmet, basket, wagashi, LP, balls, racket, nightstand, Asian foods) are rigid bodies; fixtures,
bicycles, furniture too big to push and the window are static.
"""

from __future__ import annotations

import math
import random

import numpy as np

from ..spec import Colors, Dimensions, Joint, Part
from .backyard import RUBBER, _dims, _wheel
from .base import Product, label_canvas, revolve, top_canvas
from .conv_sweets import CLEAR, _band, _sticker
from .food_fresh_snack import _pouch
from .forms import RevolveForm, _arc, jar
from .hc_garden import _p, _seg
from .paint import Canvas, finish, mix
from .products import INK, _bottle_back, _face, seal_crimp
from .store_env import ALU_DARK, ENV
from .store_env import GLASS as WINDOW_GLASS
from .windows import F, _frame

WHITE = "#FFFFFF"
BLACK = "#1E1E1E"
OAK, WALNUT = "#C8A57A", "#6B4A2E"
CHROME, STEEL = "#D4D7DB", "#9AA0A6"
GLASS = "#E6F0F2"
WICKER = "#B48A55"

STORE_TAGS = ["店舗", "店舗什器", "store fixture", "shop", "store"]
BIKE_TAGS = ["自転車店", "サイクルショップ", "自転車", "bicycle shop", "bike shop", "cycle shop"]
WAGASHI_TAGS = ["和菓子屋", "和菓子店", "和菓子", "wagashi shop", "japanese confectionery", "japanese sweets"]
RECORD_TAGS = ["レコード店", "レコードショップ", "中古レコード", "record shop", "record store", "vinyl"]
SPORTS_TAGS = ["スポーツ用品店", "スポーツ用品", "sporting goods store", "sports shop", "sporting goods"]
FURNITURE_TAGS = ["家具店", "家具", "寝室", "furniture store", "furniture", "bedroom"]
COSME_TAGS = ["化粧品店", "コスメ", "化粧品", "cosmetics store", "beauty store", "cosmetics", "makeup"]
SOUVENIR_TAGS = ["土産物店", "お土産", "みやげ物", "souvenir shop", "gift shop", "souvenir"]
ASIAN_TAGS = ["アジア食材店", "輸入食材", "エスニック", "asian grocery", "asian supermarket", "asian food"]
HOME_TAGS = ["住宅", "インテリア", "home", "interior"]


def _grain(c: Canvas, x0, y0, x1, y1, color: str, n: int, seed: int, vertical: bool = False):
    """Wood grain: n thin wavy lines across the rectangle."""
    rng = random.Random(seed)
    for _ in range(n):
        if vertical:
            x = rng.uniform(x0, x1)
            c.line([(x, y0), (x + rng.uniform(-4, 4), y1)], color, rng.uniform(0.4, 1.4))
        else:
            y = rng.uniform(y0, y1)
            c.line([(x0, y), (x1, y + rng.uniform(-4, 4))], color, rng.uniform(0.4, 1.4))


# ================================================================ bicycle shop

def _spokes(prefix: str, y: float, z: float, r: float, n: int = 16) -> list[Part]:
    """Look-only spokes of a wheel in the YZ plane (x = 0) from the hub to the rim."""
    out = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        p = _seg(f"{prefix}{k}", (0, y, z), (0, y + r * math.cos(a), z + r * math.sin(a)), 0.002, CHROME, "metal",
                 collision=False, material="steel")
        p.segments = 6
        out.append(p)
    return out


def _bike_wheel(name: str, y: float, d: float, tire: float, rim: str = "#2B2D31") -> list[Part]:
    """A tyre (collides), a rim, a hub and spokes, rolling along Y, standing on z = 0."""
    z = d / 2
    return [_p(f"{name}Tire", "torus", (d, d, tire), (0, y, z), RUBBER, "matte", rot=(0, 90, 0), material="rubber"),
            _p(f"{name}Rim", "torus", (d - 2 * tire + 0.006, d - 2 * tire + 0.006, 0.014), (0, y, z), rim, "metal",
               rot=(0, 90, 0), collision=False, material="aluminum"),
            _p(f"{name}Hub", "cylinder", (0.04, 0.04, 0.10), (0, y, z), "#3A3D42", "metal", rot=(0, 90, 0),
               collision=False, material="aluminum"),
            *_spokes(f"{name}Spoke", y, z, d / 2 - tire)]


def _tube(name, p0, p1, d, color, collision=False, finish_="glossy") -> Part:
    p = _seg(name, p0, p1, d, color, finish_, collision=collision, material="aluminum")
    p.segments = 16
    return p


def _drive(bb, color: str = "#2B2D31") -> list[Part]:
    """Chainring, cranks and pedals at the bottom bracket bb = (y, z) (right side is +X)."""
    y, z = bb
    return [_p("Chainring", "cylinder", (0.19, 0.19, 0.005), (0.07, y, z), "#5A5E64", "metal", rot=(0, 90, 0),
               collision=False, material="steel"),
            _p("CrankR", "box", (0.012, 0.03, 0.17), (0.085, y + 0.03, z - 0.07), color, "metal", rot=(-25, 0, 0),
               collision=False, material="aluminum"),
            _p("CrankL", "box", (0.012, 0.03, 0.17), (-0.085, y - 0.03, z + 0.07), color, "metal", rot=(-25, 0, 0),
               collision=False, material="aluminum"),
            _p("PedalR", "box", (0.09, 0.06, 0.02), (0.13, y + 0.065, z - 0.14), BLACK, "plastic", collision=False,
               material="plastic"),
            _p("PedalL", "box", (0.09, 0.06, 0.02), (-0.13, y - 0.065, z + 0.14), BLACK, "plastic", collision=False,
               material="plastic"),
            _tube("Chain", (0.07, y, z - 0.09), (0.07, 0.49, 0.30), 0.006, "#4A4D53", finish_="metal")]


def road_bicycle() -> Product:
    """A 700c drop-bar road bike standing on both tyres (front wheel -Y)."""
    paint, dark = "#C62828", "#2B2D31"
    yf, yr, d = -0.49, 0.49, 0.68
    bb = (0.08, 0.27)
    st, ht_top, ht_bot = (0.23, 0.80), (-0.36, 0.82), (-0.39, 0.70)
    parts = [*_bike_wheel("Front", yf, d, 0.025), *_bike_wheel("Rear", yr, d, 0.025),
             _tube("TopTube", (0, *st), (0, *ht_top), 0.032, paint, True),
             _tube("DownTube", (0, *bb), (0, *ht_bot), 0.040, paint, True),
             _tube("SeatTube", (0, *bb), (0, *st), 0.032, paint, True),
             _tube("HeadTube", (0, *ht_bot), (0, *ht_top), 0.040, paint),
             _tube("Seatpost", (0, *st), (0, 0.26, 0.90), 0.027, dark, finish_="metal"),
             _p("Saddle", "box", (0.13, 0.27, 0.045), (0, 0.25, 0.92), BLACK, "matte", material="rubber", bevel=0.015),
             _tube("Stem", (0, *ht_top), (0, -0.46, 0.85), 0.03, dark, finish_="metal"),
             _p("BarTop", "cylinder", (0.025, 0.025, 0.42), (0, -0.46, 0.86), BLACK, "matte", rot=(0, 90, 0),
                material="rubber"),
             _p("BottomBracket", "cylinder", (0.045, 0.045, 0.07), (0, *bb), dark, "metal", rot=(0, 90, 0),
                collision=False, material="steel"),
             *_drive(bb)]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        parts += [_tube(f"ChainStay{side}", (s * 0.04, *bb), (s * 0.04, yr, d / 2), 0.020, paint),
                  _tube(f"SeatStay{side}", (s * 0.04, 0.22, 0.78), (s * 0.04, yr, d / 2), 0.016, paint),
                  _tube(f"Fork{side}", (s * 0.045, *ht_bot), (s * 0.045, yf, d / 2), 0.022, paint),
                  _tube(f"Drop{side}", (s * 0.20, -0.46, 0.86), (s * 0.20, -0.56, 0.80), 0.024, BLACK, finish_="matte"),
                  _tube(f"Hook{side}", (s * 0.20, -0.56, 0.80), (s * 0.20, -0.50, 0.73), 0.024, BLACK, finish_="matte"),
                  _p(f"Hood{side}", "box", (0.03, 0.07, 0.04), (s * 0.20, -0.56, 0.88), dark, "plastic",
                     rot=(20, 0, 0), collision=False, material="rubber")]
    return Product(slug="road_bicycle", name="ロードバイク（700C・ドロップハンドル）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=9.0, static=True, material="aluminum",
                   description="形は一般的な 700C のロードバイク（全長約 1.7 m・ハンドル幅 420 mm・サドル高さ 920 mm、赤いアルミの"
                               "ダイヤモンドフレーム、ドロップハンドル）で、寸法・質量は代表値。前輪が -Y。2 輪で立つよう床に固定して"
                               "書き出す（剛体にすると倒れる）。当たり判定はタイヤ・主なパイプ・サドル・ハンドル、スポーク等は見た目だけ。"
                               "名前・メーカー名はすべて架空。",
                   tags=["ロードバイク", "自転車", "スポーツ自転車", "road bike", "road bicycle", "bicycle", "bike",
                         "racing bike", *BIKE_TAGS], photos=[], colors=Colors(label_base=paint), images=[],
                   parts=parts)


def _mesh(w_mm: float, h_mm: float, seed: int, bg: str = "#3A3C40", wire: str = "#C9CCD1", step: float = 20):
    """A wire mesh seen square on (a basket side, a cart wall)."""
    c = Canvas(w_mm, h_mm, 2, bg, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(bg, WHITE, 0.08), mix(bg, "#000000", 0.15))
    x = step / 2
    while x < w_mm:
        c.line([(x, 0), (x, h_mm)], wire, 1.8)
        x += step
    y = step / 2
    while y < h_mm:
        c.line([(0, y), (w_mm, y)], wire, 1.8)
        y += step
    c.rect(0, 0, w_mm, 6, fill=mix(wire, WHITE, 0.2))
    return _face(c.array(), "metal", seed, 0.5, 4)


def city_bicycle() -> Product:
    """A Japanese city bike (mamachari): 26-inch wheels, a step-through frame, a front basket, mudguards,
    a rear carrier, a chain guard and a kickstand (front wheel -Y)."""
    paint, dark = "#E8E4D8", "#3A3D42"
    yf, yr, d = -0.55, 0.53, 0.66
    bb = (0.10, 0.28)
    st, ht_top, ht_bot = (0.25, 0.78), (-0.40, 0.78), (-0.43, 0.66)
    low = (-0.20, 0.40)
    mesh, mesh_side = _mesh(360, 240, 8102), _mesh(260, 240, 8106)
    parts = [*_bike_wheel("Front", yf, d, 0.04, CHROME), *_bike_wheel("Rear", yr, d, 0.04, CHROME),
             _tube("DownTube", (0, *bb), (0, *low), 0.042, paint, True),
             _tube("DownTube2", (0, *low), (0, *ht_bot), 0.042, paint, True),
             _tube("SeatTube", (0, *bb), (0, *st), 0.034, paint, True),
             _tube("HeadTube", (0, *ht_bot), (0, *ht_top), 0.040, paint),
             _tube("Seatpost", (0, *st), (0, 0.28, 0.88), 0.026, CHROME, finish_="metal"),
             _p("Saddle", "box", (0.20, 0.25, 0.07), (0, 0.29, 0.92), "#5A3A28", "matte", material="rubber",
                bevel=0.025),
             _tube("Stem", (0, *ht_top), (0, -0.38, 1.00), 0.026, CHROME, finish_="metal"),
             _p("Bar", "cylinder", (0.024, 0.024, 0.56), (0, -0.33, 1.02), CHROME, "metal", rot=(0, 90, 0),
                material="steel"),
             _p("BasketBottom", "box", (0.36, 0.26, 0.006), (0, -0.60, 0.72), "#3A3C40", "metal", material="steel"),
             _p("BasketF", "box", (0.36, 0.006, 0.24), (0, -0.73, 0.84), "#3A3C40", "metal", faces={"front": 0},
                material="steel", bevel=0),
             _p("BasketB", "box", (0.36, 0.006, 0.24), (0, -0.47, 0.84), "#3A3C40", "metal", faces={"back": 0},
                collision=False, material="steel", bevel=0),
             _p("BasketL", "box", (0.006, 0.26, 0.24), (-0.18, -0.60, 0.84), "#3A3C40", "metal", faces={"left": 1},
                collision=False, material="steel", bevel=0),
             _p("BasketR", "box", (0.006, 0.26, 0.24), (0.18, -0.60, 0.84), "#3A3C40", "metal", faces={"right": 1},
                collision=False, material="steel", bevel=0),
             _p("Lamp", "cylinder", (0.06, 0.06, 0.06), (0, -0.50, 0.62), dark, "plastic", rot=(90, 0, 0),
                collision=False, material="plastic"),
             _p("LampLens", "cylinder", (0.05, 0.05, 0.004), (0, -0.531, 0.62), "#FFF6D8", "glass", rot=(90, 0, 0),
                collision=False, material="glass"),
             _p("Carrier", "box", (0.15, 0.32, 0.012), (0, 0.46, 0.72), CHROME, "metal", material="steel"),
             _p("ChainGuard", "box", (0.006, 0.46, 0.09), (0.07, 0.31, 0.31), paint, "glossy", rot=(6.6, 0, 0),
                collision=False, material="steel"),
             _p("BottomBracket", "cylinder", (0.045, 0.045, 0.07), (0, *bb), dark, "metal", rot=(0, 90, 0),
                collision=False, material="steel"),
             *_drive(bb)[:5]]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        parts += [_tube(f"ChainStay{side}", (s * 0.045, *bb), (s * 0.045, yr, d / 2), 0.020, paint),
                  _tube(f"SeatStay{side}", (s * 0.045, 0.24, 0.74), (s * 0.045, yr, d / 2), 0.016, paint),
                  _tube(f"Fork{side}", (s * 0.05, *ht_bot), (s * 0.05, yf, d / 2), 0.024, paint),
                  _tube(f"CarrierStay{side}", (s * 0.06, 0.60, 0.72), (s * 0.06, yr, d / 2), 0.010, CHROME,
                        finish_="metal"),
                  _tube(f"BasketStay{side}", (s * 0.08, -0.55, 0.72), (s * 0.06, yf, d / 2), 0.010, CHROME,
                        finish_="metal"),
                  _p(f"Grip{side}", "cylinder", (0.032, 0.032, 0.12), (s * 0.24, -0.29, 1.02), "#4A3428", "matte",
                     rot=(0, 90, 0), collision=False, material="rubber"),
                  _tube(f"Kickstand{side}", (s * 0.06, 0.46, 0.30), (s * 0.12, 0.50, 0.005), 0.014, CHROME,
                        finish_="metal")]
    for name, y in (("Front", yf), ("Rear", yr)):  # mudguards: short plates along the upper arc of each wheel
        r = d / 2 + 0.02
        for k in range(9):
            a = math.radians(30 + k * 15)
            parts.append(_p(f"Guard{name}{k}", "box", (0.06, 0.098, 0.004),
                            (0, y + r * math.cos(a), d / 2 + r * math.sin(a)), CHROME, "metal",
                            rot=(math.degrees(a) - 90, 0, 0), collision=False, material="steel", bevel=0))
    return Product(slug="city_bicycle", name="シティサイクル（26 インチ・前かご付き）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=18.0, static=True, material="steel",
                   description="形は一般的な 26 インチのシティサイクル（ママチャリ。全長約 1.8 m・ハンドル幅 580 mm、白い"
                               "低床フレーム、前かご・泥よけ・荷台・チェーンカバー・スタンド・ライト）で、寸法・質量は代表値。前輪が -Y。"
                               "床に固定して書き出す。当たり判定はタイヤ・主なパイプ・サドル・ハンドル・かごの底と前・荷台。"
                               "名前・メーカー名はすべて架空。",
                   tags=["シティサイクル", "ママチャリ", "自転車", "軽快車", "city bike", "city bicycle", "bicycle", "bike",
                         "commuter bike", "mamachari", *BIKE_TAGS], photos=[], colors=Colors(label_base=paint),
                   images=[mesh, mesh_side], parts=parts)


def _helmet_top(seed: int, color: str) -> object:
    w, d = 220, 280
    c = Canvas(w, d, 2, color, seed)
    c.gradient(0, 0, w, d, mix(color, WHITE, 0.15), mix(color, "#000000", 0.20))
    for k in range(5):  # vents: long slots running front to back
        x = 40 + k * 35
        c.rect(x - 8, 50 + abs(k - 2) * 12, x + 8, 230 - abs(k - 2) * 12, fill="#1A1A1C", radius=8)
    c.rect(102, 20, 118, 260, fill=WHITE)
    c.text(110, 248, "AERO", 10, BLACK, 900)
    return _face(c.array(), "plastic", seed, 0.5, 6)


def bicycle_helmet() -> Product:
    """A vented bicycle helmet standing on its rim (visor to -Y)."""
    color = "#1F6FB2"
    parts = [_p("Shell", "dome", (0.22, 0.28, 0.15), (0, 0, 0.012 + 0.075), color, "glossy", faces={"top": 0},
                material="plastic"),
             _p("Liner", "cylinder", (0.21, 0.27, 0.012), (0, 0, 0.006), "#2B2D31", "matte", material="plastic"),
             _p("Visor", "box", (0.14, 0.035, 0.004), (0, -0.142, 0.07), "#2B2D31", "plastic", rot=(15, 0, 0),
                collision=False, material="plastic")]
    for s in (-1, 1):
        parts.append(_p(f"Strap{'L' if s < 0 else 'R'}", "box", (0.003, 0.02, 0.10), (s * 0.095, 0.02, -0.0), BLACK,
                        "matte", collision=False, material="fabric", bevel=0))
    parts[-1].center[2] = 0.006
    parts[-2].center[2] = 0.006
    parts[-1].size[2] = parts[-2].size[2] = 0.012
    return Product(slug="bicycle_helmet", name="自転車のヘルメット", shape_class="assembly", category="household",
                   dims=_dims(parts), mass_kg=0.28, material="plastic",
                   description="形は一般的な自転車用のヘルメット（幅 220 mm・長さ 280 mm・高さ 160 mm、青い殻に縦長の通気口、"
                               "前にひさし）で、寸法・質量は代表値。縁を下にして棚に置く向き。名前・メーカー名はすべて架空。",
                   tags=["ヘルメット", "自転車ヘルメット", "サイクルヘルメット", "helmet", "bicycle helmet", "bike helmet",
                         "cycling helmet", *BIKE_TAGS], photos=[], colors=Colors(label_base=color),
                   images=[_helmet_top(8103, color)], parts=parts)


def bicycle_stand_rack() -> Product:
    """A floor bicycle rack for five bikes: wire loops that hold the front wheel, on two base rails."""
    n, pitch = 5, 0.32
    W = n * pitch
    galv = "#B9BEC4"
    parts = [_p("RailF", "box", (W, 0.03, 0.03), (0, -0.20, 0.015), galv, "metal", material="steel", bevel=0.003),
             _p("RailB", "box", (W, 0.03, 0.03), (0, 0.20, 0.015), galv, "metal", material="steel", bevel=0.003)]
    for k in range(n):
        x0 = -W / 2 + (k + 0.5) * pitch
        for j, s in enumerate((-1, 1)):
            x = x0 + s * 0.035
            for i, (a, b) in enumerate((((x, -0.20, 0.03), (x, -0.12, 0.34)), ((x, -0.12, 0.34), (x, 0.12, 0.34)),
                                        ((x, 0.12, 0.34), (x, 0.20, 0.03)))):
                p = _seg(f"Loop{k}{j}{i}", a, b, 0.012, galv, "metal", material="steel")
                p.segments = 12
                parts.append(p)
    return Product(slug="bicycle_stand_rack", name="サイクルスタンド（5 台用）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=22.0, static=True, material="steel",
                   description="形は駐輪場・自転車店の前の一般的な前輪差し込み式のサイクルスタンド（幅 1600 mm・奥行き 430 mm・"
                               "高さ 340 mm、ピッチ 320 mm で 5 台、亜鉛めっきの鋼線のループ 2 本で前輪をはさむ）で、"
                               "寸法・質量は代表値。床に固定。自転車は -Y から前輪を差し込む。",
                   tags=["サイクルスタンド", "駐輪スタンド", "自転車スタンド", "駐輪場", "bicycle rack", "bike rack",
                         "bicycle stand", "bike stand", "cycle stand", "bike parking", *BIKE_TAGS, *STORE_TAGS],
                   photos=[], colors=Colors(label_base=galv), images=[], parts=parts)


# ================================================================ woven baskets

def _wicker(w_mm: float, h_mm: float, seed: int, base: str = WICKER) -> object:
    """A basket weave: rows of short strands over and under vertical stakes."""
    c = Canvas(w_mm, h_mm, 3, base, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(base, WHITE, 0.10), mix(base, "#000000", 0.22))
    rng = random.Random(seed)
    row = 0
    y = 0.0
    while y < h_mm:
        x = -8.0 if row % 2 else 0.0
        while x < w_mm:
            col = mix(base, WHITE, rng.uniform(0.0, 0.22))
            c.ellipse(x + 1, y + 0.6, x + 15, y + 6.4, fill=col, outline=mix(base, "#000000", 0.45), width=0.7)
            x += 16
        y += 7
        row += 1
    c.rect(0, 0, w_mm, 5, fill=mix(base, "#000000", 0.15))
    return _face(c.array(), "paper", seed, 0.7, 6)


def _wicker_set(W: float, D: float, H: float, seed: int) -> list:
    """Bottom, long-wall and short-wall weave images for a basket W x D x H [m]."""
    return [_wicker(W * 1000, D * 1000, seed), _wicker(W * 1000, H * 1000, seed + 1000),
            _wicker(D * 1000, H * 1000, seed + 2000)]


def _basket_parts(prefix: str, W, D, H, z0, img: int, *, x=0.0, y=0.0, collide=True) -> list[Part]:
    """An open woven basket: the bottom sits between the walls (it is the fill shelf), four walls, a rim.
    Images: img = bottom, img + 1 = long walls, img + 2 = short walls (see _wicker_set)."""
    t = 0.008
    return [_p(f"{prefix}Bottom", "box", (W - 2 * t, D - 2 * t, 0.012), (x, y, z0 + 0.006), WICKER, "matte",
               faces={"top": img}, material="wood", bevel=0),
            _p(f"{prefix}Front", "box", (W, t, H), (x, y - D / 2 + t / 2, z0 + H / 2), WICKER, "matte",
               faces={"front": img + 1, "back": img + 1}, collision=collide, material="wood", bevel=0.002),
            _p(f"{prefix}Rear", "box", (W, t, H), (x, y + D / 2 - t / 2, z0 + H / 2), WICKER, "matte",
               faces={"front": img + 1, "back": img + 1}, collision=collide, material="wood", bevel=0.002),
            _p(f"{prefix}Left", "box", (t, D - 2 * t, H), (x - W / 2 + t / 2, y, z0 + H / 2), WICKER, "matte",
               faces={"left": img + 2, "right": img + 2}, collision=collide, material="wood", bevel=0.002),
            _p(f"{prefix}Right", "box", (t, D - 2 * t, H), (x + W / 2 - t / 2, y, z0 + H / 2), WICKER, "matte",
               faces={"left": img + 2, "right": img + 2}, collision=collide, material="wood", bevel=0.002),
            *[_p(f"{prefix}Rim{k}", "box", size, (x + dx, y + dy, z0 + H - 0.006), mix(WICKER, "#000000", 0.25),
                 "matte", collision=False, material="wood", bevel=0.004)
              for k, (size, dx, dy) in enumerate((((W + 0.006, 0.014, 0.014), 0, -D / 2 + t / 2),
                                                  ((W + 0.006, 0.014, 0.014), 0, D / 2 - t / 2),
                                                  ((0.014, D - 0.008, 0.014), -W / 2 + t / 2, 0),
                                                  ((0.014, D - 0.008, 0.014), W / 2 - t / 2, 0)))]]


def woven_basket() -> Product:
    """A light rectangular woven basket (360 x 260 mm, 180 mm tall), open on top."""
    W, D, H = 0.36, 0.26, 0.18
    parts = _basket_parts("", W, D, H, 0.0, 0)
    for s in (-1, 1):  # cut-out handles on the short sides
        parts.append(_p(f"Handle{'L' if s < 0 else 'R'}", "box", (0.004, 0.09, 0.025),
                        (s * (W / 2 + 0.001), 0, H - 0.035), "#3A2A1A", "matte", collision=False, material="wood",
                        bevel=0))
    return Product(slug="woven_basket", name="編みかご（角型・中）", shape_class="assembly", category="household",
                   dims=_dims(parts), mass_kg=0.35, material="wood",
                   description="形は一般的な角型の編みかご（ラタン調。360 × 260 mm・高さ 180 mm、上は開いていて短い辺に手かけの穴）"
                               "で、寸法・質量は代表値。軽い剛体。底は壁の内側にあり、商品を並べる棚板として小物を入れられる。",
                   tags=["かご", "編みかご", "バスケット", "ラタン", "収納かご", "basket", "woven basket", "wicker basket",
                         "rattan basket", "storage basket", *HOME_TAGS, "雑貨", "variety store"], photos=[],
                   colors=Colors(label_base=WICKER), images=_wicker_set(W, D, H, 8104), parts=parts)


def basket_display_stand() -> Product:
    """A two-tier store stand holding six shallow woven baskets (three per tier, the upper tier set back)."""
    W, D = 1.20, 0.62
    bw, bd, bh = 0.38, 0.27, 0.12
    frame = "#2B2D31"
    parts: list[Part] = []
    tiers = ((0.40, -0.15), (0.80, 0.15))  # (bottom z, centre y)
    for t, (z, y) in enumerate(tiers):
        for k in range(3):
            x = (k - 1) * (bw + 0.01)
            parts += _basket_parts(f"Basket{t}{k}_", bw, bd, bh, z, 0, x=x, y=y)
        for nm, dy in (("F", -bd / 2 + 0.03), ("B", bd / 2 - 0.03)):  # rails under the baskets (not boards)
            parts.append(_p(f"Rail{t}{nm}", "box", (W, 0.025, 0.025), (0, y + dy, z - 0.0125), frame, "metal",
                            material="steel", bevel=0.002))
    for sx in (-1, 1):
        for sy, top in ((-1, 0.40), (1, 0.80)):
            y = sy * (D / 2 - 0.02)
            parts.append(_p(f"Leg{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", "box", (0.025, 0.025, top),
                            (sx * (W / 2 - 0.0125), y, top / 2), frame, "metal", material="steel", bevel=0.002))
        parts += [_p(f"Side{'L' if sx < 0 else 'R'}0", "box", (0.025, D, 0.025), (sx * (W / 2 - 0.0125), 0, 0.10),
                     frame, "metal", material="steel", bevel=0.002),
                  _p(f"Side{'L' if sx < 0 else 'R'}1", "box", (0.025, D - 0.04, 0.025),
                     (sx * (W / 2 - 0.0125), 0, 0.3875), frame, "metal", material="steel", bevel=0.002),
                  _p(f"Mid{'L' if sx < 0 else 'R'}", "box", (0.025, 0.025, 0.40), (sx * (W / 2 - 0.0125), 0.0, 0.60),
                     frame, "metal", material="steel", bevel=0.002)]
    return Product(slug="basket_display_stand", name="かごの陳列台（2 段・6 かご）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=14.0, static=True, material="steel",
                   description="形は雑貨店・青果店の一般的なかごの陳列台（幅 1200 mm・奥行き 620 mm・高さ 920 mm、黒い鉄の枠に"
                               "浅い編みかご 3 つずつ 2 段、上の段は奥へずらす）で、寸法・質量は代表値。床に固定。各かごの底が"
                               "商品を並べる棚板で、小物・果物・パンを並べる。",
                   tags=["かご什器", "かごの陳列台", "バスケット什器", "陳列台", "basket display", "basket stand",
                         "basket display stand", "wicker basket display", "produce basket stand", *STORE_TAGS, "雑貨",
                         "variety store"], photos=[], colors=Colors(label_base=WICKER),
                   images=_wicker_set(bw, bd, bh, 8105), parts=parts)


# ================================================================ wagashi shop

def _ball(name: str, d: float, center, color: str, finish_: str = "matte", face: int | None = None,
          collision: bool = False, material: str = "food", segments: int | None = None) -> list[Part]:
    """A sphere made of two domes (the lower one upside down)."""
    x, y, z = center
    faces = None if face is None else {"top": face}
    return [_p(f"{name}T", "dome", (d, d, d / 2), (x, y, z + d / 4), color, finish_, faces=faces,
               collision=collision, material=material, segments=segments),
            _p(f"{name}B", "dome", (d, d, d / 2), (x, y, z - d / 4), color, finish_, rot=(180, 0, 0), faces=faces,
               collision=collision, material=material, segments=segments)]


def _film_case(L: float, Wd: float, H: float, z0: float = 0.002) -> Part:
    return _p("Film", "box", (L, Wd, H), (0, 0, z0 + H / 2), CLEAR, "glass", material="plastic", thin_walled=True,
              bevel=0.004)


def dango_pack() -> Product:
    """Three skewers of dango (two mitarashi, one three-colour) on a tray in a clear case."""
    brown = "#B5732E"
    imgs = [_sticker(60, 32, "だんご 3本入", "みたらし・三色", "#8C4A1E", 8110, 368, 298),
            _band(64, 9, "その日に作りました", "#8C4A1E", 8111)]
    L, Wd, tray_h, d = 0.150, 0.096, 0.008, 0.024
    parts = [_p("Tray", "box", (L, Wd, tray_h), (0, 0, tray_h / 2), "#FBFAF6", "plastic", material="plastic")]
    for k, y in enumerate((-0.030, 0.0, 0.030)):
        z = tray_h + d / 2
        stick = _p(f"Stick{k}", "cylinder", (0.003, 0.003, 0.135), (0, y, z), "#E6D4AA", "matte", rot=(0, 90, 0),
                   collision=False, material="wood")
        stick.segments = 8
        parts.append(stick)
        cols = [brown] * 4 if k < 2 else ["#F2A7B5", "#F5F1E6", "#8DB86A"]
        for j, col in enumerate(cols):
            x = -0.040 + j * (d + 0.001) + (0.012 if k == 2 else 0)
            parts += _ball(f"Dango{k}{j}", d, (x, y, z), col, "glossy" if k < 2 else "matte", segments=16)
    film_h = 0.036
    parts += [_film_case(L + 0.002, Wd + 0.002, film_h),
              _p("Sticker", "box", (0.060, 0.032, 0.0006), (0.03, 0, 0.002 + film_h + 0.0003), WHITE, "matte",
                 faces={"top": 0}, collision=False, material="paper"),
              _p("Band", "box", (0.064, 0.0006, 0.009), (0, -Wd / 2 - 0.0013, 0.0085), "#8C4A1E", "matte",
                 faces={"front": 1}, collision=False, material="paper")]
    return Product(slug="dango_pack", name="だんご 3本入（みたらし・三色）", shape_class="assembly", category="food",
                   dims=_dims(parts), mass_kg=0.20, material="plastic",
                   description="形は和菓子屋の一般的な串だんごのパック（白いトレー 150 × 96 mm にみたらし団子 2 本・三色団子 1 本、"
                               "高さ 36 mm の透明なケースと商品名シール）で、寸法・質量は代表値。団子は球で表す。名前・店名は架空。",
                   tags=["団子", "だんご", "みたらし団子", "三色団子", "串団子", "dango", "mitarashi dango", "rice dumpling",
                         *WAGASHI_TAGS], photos=[], colors=Colors(label_base=brown), images=imgs, parts=parts)


def _yakiin(seed: int, mark: str, base: str = "#C98A4A") -> object:
    """A manju seen from above: a baked brown top with a branded mark in the middle."""
    c = Canvas(60, 60, 8, base, seed)
    c.gradient(0, 0, 60, 60, mix(base, WHITE, 0.25), mix(base, "#000000", 0.25))
    c.ellipse(8, 8, 52, 52, fill=mix(base, WHITE, 0.12))
    c.ellipse(19, 19, 41, 41, outline="#4A2412", width=1.4)
    c.text(30, 30.5, mark, 13, "#4A2412", 900)
    return _face(c.array(), "paper", seed, 0.6, 6)


def manju_pack() -> Product:
    """Four baked manju with a branded mark, on a tray in a clear case."""
    base = "#C98A4A"
    imgs = [_sticker(60, 32, "栗まんじゅう 4個入", "白あん・栗入り", "#6B3A1E", 8112, 520, 540),
            _band(64, 9, "焼きたて", "#6B3A1E", 8113), _yakiin(8114, "栗", base)]
    L, Wd, tray_h, R, h = 0.130, 0.130, 0.008, 0.028, 0.030
    parts = [_p("Tray", "box", (L, Wd, tray_h), (0, 0, tray_h / 2), "#F4EFE4", "plastic", material="plastic")]
    for k, (x, y) in enumerate(((-0.031, -0.031), (0.031, -0.031), (-0.031, 0.031), (0.031, 0.031))):
        parts.append(_p(f"Manju{k}", "bun", (2 * R, 2 * R, h), (x, y, tray_h - 0.001 + h / 2), base, "matte",
                        faces={"top": 2}, collision=False, material="food", segments=32))
    film_h = 0.042
    parts += [_film_case(L + 0.002, Wd + 0.002, film_h),
              _p("Sticker", "box", (0.060, 0.032, 0.0006), (0, -0.03, 0.002 + film_h + 0.0003), WHITE, "matte",
                 faces={"top": 0}, collision=False, material="paper"),
              _p("Band", "box", (0.064, 0.0006, 0.009), (0, -Wd / 2 - 0.0013, 0.0085), "#6B3A1E", "matte",
                 faces={"front": 1}, collision=False, material="paper")]
    return Product(slug="manju_pack", name="栗まんじゅう 4個入", shape_class="assembly", category="food",
                   dims=_dims(parts), mass_kg=0.24, material="plastic",
                   description="形は和菓子屋の一般的な焼きまんじゅうのパック（130 mm 角のトレーに直径 56 mm の焼き印付きのまんじゅう"
                               " 4 個、透明なケースと商品名シール）で、寸法・質量は代表値。名前・店名は架空。",
                   tags=["まんじゅう", "饅頭", "栗まんじゅう", "焼きまんじゅう", "manju", "steamed bun", "baked bun",
                         *WAGASHI_TAGS], photos=[], colors=Colors(label_base=base), images=imgs, parts=parts)


def _monaka_top(seed: int) -> object:
    base = "#D9B271"
    c = Canvas(64, 64, 8, base, seed)
    c.gradient(0, 0, 64, 64, mix(base, WHITE, 0.25), mix(base, "#000000", 0.18))
    for k in range(5):  # a five-petal flower pressed into the wafer
        a = math.radians(90 + 72 * k)
        x, y = 32 + 14 * math.cos(a), 32 - 14 * math.sin(a)
        c.ellipse(x - 9, y - 9, x + 9, y + 9, outline=mix(base, "#000000", 0.35), width=0.9)
    c.ellipse(26, 26, 38, 38, fill=mix(base, "#000000", 0.12), outline=mix(base, "#000000", 0.35), width=0.8)
    for k in range(0, 64, 4):
        c.line([(k, 0), (k, 64)], mix(base, "#000000", 0.06), 0.3)
    return _face(c.array(), "paper", seed, 0.7, 6)


def monaka_pack() -> Product:
    """Three flower-shaped monaka (wafer shells filled with bean paste) on a tray in a clear case."""
    base = "#D9B271"
    imgs = [_sticker(60, 32, "最中 3個入", "つぶあん", "#3E5A2A", 8115, 450, 390),
            _band(64, 9, "北海道産小豆", "#3E5A2A", 8116), _monaka_top(8117)]
    L, Wd, tray_h, d, h = 0.200, 0.075, 0.008, 0.060, 0.026
    parts = [_p("Tray", "box", (L, Wd, tray_h), (0, 0, tray_h / 2), "#F4EFE4", "plastic", material="plastic")]
    for k, x in enumerate((-0.064, 0.0, 0.064)):
        z = tray_h + h / 2
        parts += [_p(f"Monaka{k}T", "dome", (d, d, h / 2), (x, 0, z + h / 4), base, "matte", faces={"top": 2},
                     collision=False, material="food", segments=32),
                  _p(f"Monaka{k}B", "dome", (d, d, h / 2), (x, 0, z - h / 4), base, "matte", rot=(180, 0, 0),
                     faces={"top": 2}, collision=False, material="food", segments=32),
                  _p(f"Anko{k}", "cylinder", (d * 0.92, d * 0.92, 0.004), (x, 0, z), "#3A1E22", "matte",
                     collision=False, material="food", segments=32)]
    film_h = 0.034
    parts += [_film_case(L + 0.002, Wd + 0.002, film_h),
              _p("Sticker", "box", (0.060, 0.032, 0.0006), (0.064, -0.012, 0.002 + film_h + 0.0003), WHITE, "matte",
                 faces={"top": 0}, collision=False, material="paper"),
              _p("Band", "box", (0.064, 0.0006, 0.009), (0, -Wd / 2 - 0.0013, 0.0085), "#3E5A2A", "matte",
                 faces={"front": 1}, collision=False, material="paper")]
    return Product(slug="monaka_pack", name="最中 3個入", shape_class="assembly", category="food",
                   dims=_dims(parts), mass_kg=0.18, material="plastic",
                   description="形は和菓子屋の一般的な最中のパック（200 × 75 mm のトレーに直径 60 mm の花形の最中 3 個、皮の間に"
                               "あん、透明なケースと商品名シール）で、寸法・質量は代表値。花形は皮の絵で表す。名前・店名は架空。",
                   tags=["最中", "もなか", "和菓子", "monaka", "wafer cake", "bean paste wafer", *WAGASHI_TAGS], photos=[],
                   colors=Colors(label_base=base), images=imgs, parts=parts)


def _yokan_top(seed: int) -> object:
    bg, gold = "#4A1E22", "#D9B25A"
    c = Canvas(180, 55, 6, bg, seed)
    c.gradient(0, 0, 180, 55, mix(bg, WHITE, 0.12), mix(bg, "#000000", 0.25))
    c.rect(4, 4, 176, 51, outline=gold, width=0.8)
    c.rect(7, 7, 173, 48, outline=gold, width=0.3)
    c.text(70, 27, "羊羹", 24, gold, 900, spacing=3)
    c.text(128, 22, "小倉", 9, WHITE, 800)
    c.text(128, 36, "一本入", 6, WHITE, 700)
    c.text(162, 27, "架空堂", 5, gold, 800)
    return _face(c.array(), "paper", seed, 0.5, 4)


def _yokan_side(seed: int) -> object:
    bg, gold = "#4A1E22", "#D9B25A"
    c = Canvas(180, 30, 6, bg, seed)
    c.gradient(0, 0, 180, 30, mix(bg, WHITE, 0.10), mix(bg, "#000000", 0.20))
    c.rect(0, 3, 180, 4, fill=gold)
    c.rect(0, 26, 180, 27, fill=gold)
    c.text(60, 15.5, "本練 小倉羊羹", 8, WHITE, 900)
    c.text(140, 15.5, "内容量 280g", 4.5, gold, 700)
    return _face(c.array(), "paper", seed, 0.5, 3)


def yokan_bar() -> Product:
    """A bar of yokan in its paper box, lying flat."""
    L, Wd, H = 0.180, 0.055, 0.030
    imgs = [_yokan_top(8118), _yokan_side(8119)]
    parts = [_p("Box", "box", (L, Wd, H), (0, 0, H / 2), "#4A1E22", "matte",
                faces={"top": 0, "front": 1, "back": 1}, material="paper", bevel=0.001)]
    return Product(slug="yokan_bar", name="小倉羊羹 一本入", shape_class="assembly", category="food",
                   dims=Dimensions(H, L, depth=Wd), mass_kg=0.30, material="paper",
                   description="形は和菓子屋の一般的な棹物の羊羹（180 × 55 mm・高さ 30 mm の紙箱、えんじ地に金の枠）で、"
                               "寸法・質量は代表値。寝かせて置く。名前・店名は架空。",
                   tags=["羊羹", "ようかん", "小倉羊羹", "練り羊羹", "yokan", "red bean jelly", "sweet bean jelly",
                         *WAGASHI_TAGS], photos=[], colors=Colors(label_base="#4A1E22"), images=imgs, parts=parts)


def _wrap(c: Canvas, x0, y0, x1, y1, base: str):
    c.gradient(x0, y0, x1, y1, mix(base, WHITE, 0.15), mix(base, "#000000", 0.08))
    c.pattern(x0, y0, x1, y1, "waves", mix(base, WHITE, 0.45), 14, 0.8)


def _gift_top(seed: int) -> object:
    base, red = "#C9A3B2", "#C62828"
    c = Canvas(300, 220, 3, base, seed)
    _wrap(c, 0, 0, 300, 220, base)
    c.rect(105, 0, 195, 220, fill="#FBFAF6", outline="#D9D4C8", width=0.6)  # the noshi paper
    for k, col in enumerate((red, red, red, WHITE, WHITE)):  # mizuhiki cords tied across
        y = 104 + k * 3
        c.line([(105, y), (195, y)], col if col != WHITE else "#E0DCD2", 1.6)
    c.ellipse(140, 96, 160, 128, outline=red, width=1.4)
    c.text(150, 52, "御礼", 26, INK, 900, spacing=6)
    c.text(150, 165, "架空堂", 14, INK, 800)
    c.polygon([(186, 10), (194, 10), (194, 30)], fill="#E6C34A")  # the noshi mark
    return _face(c.array(), "paper", seed, 0.6, 6)


def _gift_side(seed: int, w: float) -> object:
    base = "#C9A3B2"
    c = Canvas(w, 70, 3, base, seed)
    _wrap(c, 0, 0, w, 70, base)
    c.rect(w / 2 - 45, 0, w / 2 + 45, 70, fill="#FBFAF6", outline="#D9D4C8", width=0.6)
    return _face(c.array(), "paper", seed, 0.6, 4)


def wagashi_gift_box() -> Product:
    """A boxed assortment of wagashi wrapped in paper with a noshi (a gift box), lying flat."""
    L, Wd, H = 0.30, 0.22, 0.07
    imgs = [_gift_top(8120), _gift_side(8121, 300), _gift_side(8122, 220)]
    parts = [_p("Box", "box", (L, Wd, H), (0, 0, H / 2), "#C9A3B2", "matte",
                faces={"top": 0, "front": 1, "back": 1, "left": 2, "right": 2}, material="paper", bevel=0.002)]
    return Product(slug="wagashi_gift_box", name="和菓子の詰め合わせ（菓子折り・のし付き）", shape_class="assembly",
                   category="food", dims=Dimensions(H, L, depth=Wd), mass_kg=0.85, material="paper",
                   description="形は和菓子屋の一般的な菓子折り（300 × 220 mm・高さ 70 mm、包装紙で包み、のし紙と水引の絵）で、"
                               "寸法・質量は代表値。中身は見えない。店名は架空。",
                   tags=["菓子折り", "菓子箱", "詰め合わせ", "和菓子詰め合わせ", "のし", "手土産", "ギフト", "gift box",
                         "wagashi gift box", "sweets gift box", "confectionery box", *WAGASHI_TAGS, *SOUVENIR_TAGS],
                   photos=[], colors=Colors(label_base="#C9A3B2"), images=imgs, parts=parts)


def wagashi_showcase() -> Product:
    """A low glass showcase for wagashi: a wooden cabinet, a lit deck behind glass on three sides, a glass
    shelf at the back and a glass top."""
    W, D, H = 1.50, 0.60, 1.05
    base_h, g = 0.70, 0.006
    wood = "#5A3A24"
    parts = [_p("Cabinet", "box", (W, D, base_h), (0, 0, base_h / 2), wood, "matte", material="wood"),
             _p("Kick", "box", (W - 0.04, 0.006, 0.08), (0, -D / 2 - 0.002, 0.04), "#2B1E14", "matte",
                collision=False, material="wood"),
             # the deck sits inside the glass walls so the fill shelf it makes ends at their inner faces
             _p("Deck", "box", (W - 2 * g, D - 2 * g, 0.025), (0, 0, base_h + 0.0125), "#F4EFE4", "matte",
                material="wood"),
             _p("GlassF", "box", (W, g, H - base_h - 0.006), (0, -D / 2 + g / 2, base_h + (H - base_h - 0.006) / 2),
                GLASS, "glass", material="glass", thin_walled=True, bevel=0),
             _p("GlassB", "box", (W, g, H - base_h - 0.006), (0, D / 2 - g / 2, base_h + (H - base_h - 0.006) / 2),
                GLASS, "glass", material="glass", thin_walled=True, bevel=0),
             _p("GlassL", "box", (g, D - 2 * g, H - base_h - 0.006), (-W / 2 + g / 2, 0, base_h + (H - base_h - 0.006) / 2),
                GLASS, "glass", material="glass", thin_walled=True, bevel=0),
             _p("GlassR", "box", (g, D - 2 * g, H - base_h - 0.006), (W / 2 - g / 2, 0, base_h + (H - base_h - 0.006) / 2),
                GLASS, "glass", material="glass", thin_walled=True, bevel=0),
             _p("GlassTop", "box", (W, D, 0.006), (0, 0, H - 0.003), GLASS, "glass", material="glass", thin_walled=True,
                bevel=0),
             _p("Shelf", "box", (W - 2 * g - 0.02, 0.26, 0.008), (0, D / 2 - g - 0.13, base_h + 0.025 + 0.14), GLASS,
                "glass", material="glass", thin_walled=True, bevel=0),
             _p("Lamp", "box", (W - 0.10, 0.04, 0.008), (0, -0.10, H - 0.010), "#FFF8EC", "light", collision=False,
                material="plastic")]
    for s in (-1, 1):  # shelf brackets at both ends
        parts.append(_p(f"Bracket{'L' if s < 0 else 'R'}", "box", (0.012, 0.26, 0.14),
                        (s * (W / 2 - g - 0.006), D / 2 - g - 0.13, base_h + 0.025 + 0.07), GLASS, "glass",
                        collision=False, material="glass", thin_walled=True, bevel=0))
    return Product(slug="wagashi_showcase", name="和菓子のショーケース（ガラス・低め）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=120.0, static=True, material="wood",
                   description="形は和菓子屋の一般的な対面のショーケース（幅 1500 mm・奥行き 600 mm・高さ 1050 mm、こげ茶の木の"
                               "台に照明付きの台板、前・左右・後ろ・上がガラス、奥にガラスの棚 1 段）で、寸法・質量は代表値。"
                               "台板（ガラスの内側）・奥の棚・天板が 商品を並べる棚板。冷蔵しない常温のケース。",
                   tags=["ショーケース", "和菓子ケース", "ガラスケース", "対面ケース", "陳列ケース", "showcase",
                         "display case", "glass display case", "wagashi showcase", "pastry case", *WAGASHI_TAGS,
                         *STORE_TAGS], photos=[], colors=Colors(label_base=wood), images=[], parts=parts)


def _noren_panels(seed: int) -> list[object]:
    """The three panels of an indigo noren: one dyed picture cut into thirds, front and (mirrored) back."""
    W, H = 870, 880
    indigo = "#22335A"
    c = Canvas(W, H, 1, indigo, seed)
    c.gradient(0, 0, W, H, "#1C2B4E", "#33497A")
    c.rect(0, 0, W, 70, fill="#18243F")
    for k, ch in enumerate("和菓子"):
        x = 145 + k * 290
        c.ellipse(x - 120, 260, x + 120, 500, outline="#F2EEE4", width=6)
        c.text(x, 382, ch, 190, "#F2EEE4", 900)
    c.text(W / 2, 740, "架 空 堂", 70, "#F2EEE4", 800, spacing=40)
    for y in (640, 820):
        c.line([(20, y), (W - 20, y)], "#F2EEE480", 3)
    arr = finish(c.array(), "paper", seed, 0.7)
    n = arr.shape[1]
    cuts = [arr[:, round(n * k / 3):round(n * (k + 1) / 3)] for k in range(3)]
    return [*cuts, *[np.ascontiguousarray(np.fliplr(a)) for a in cuts]]


def noren() -> Product:
    """A shop-entrance noren: three indigo panels with white lettering hanging from a wooden rod."""
    W, Hp = 0.90, 0.88
    pw = 0.292
    rod_z = Hp + 0.035
    parts = [_p("Rod", "cylinder", (0.025, 0.025, W + 0.06), (0, 0, rod_z), "#8A6A44", "matte", rot=(0, 90, 0),
                material="wood"),
             _p("CapL", "cylinder", (0.032, 0.032, 0.02), (-(W + 0.06) / 2, 0, rod_z), "#2B1E14", "matte",
                rot=(0, 90, 0), collision=False, material="wood"),
             _p("CapR", "cylinder", (0.032, 0.032, 0.02), ((W + 0.06) / 2, 0, rod_z), "#2B1E14", "matte",
                rot=(0, 90, 0), collision=False, material="wood")]
    for k in range(3):
        x = (k - 1) * (pw + 0.004)
        parts.append(_p(f"Panel{k}", "box", (pw, 0.002, Hp), (x, 0, Hp / 2), "#22335A", "matte",
                        faces={"front": k, "back": 3 + k}, collision=False, material="fabric", bevel=0))
        for j in (-1, 1):  # the loops (chichi) the rod runs through
            parts.append(_p(f"Loop{k}{j + 1}", "box", (0.04, 0.03, 0.05), (x + j * (pw / 2 - 0.04), 0, Hp + 0.02),
                            "#18243F", "matte", collision=False, material="fabric", bevel=0.004))
    return Product(slug="noren", name="のれん（藍染め風・3 枚）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=1.2, static=True, material="fabric",
                   description="形は和菓子屋・飲食店の入口の一般的なのれん（幅 900 mm・丈 880 mm の 3 枚、藍色の地に白抜きの文字、"
                               "木の竿に乳（ち）で通す）で、寸法・質量は代表値。床置きではなく、入口の上の壁に掛ける"
                               "（下端の高さは 1.0〜1.1 m）。布は見た目だけで、"
                               "当たり判定は竿だけ。文字・店名は架空。",
                   tags=["のれん", "暖簾", "店先", "入口", "noren", "shop curtain", "doorway curtain",
                         "japanese curtain", *WAGASHI_TAGS, "和食", "japanese restaurant", *STORE_TAGS], photos=[],
                   colors=Colors(label_base="#22335A"), images=_noren_panels(8123), parts=parts)


# ================================================================ record shop

def _lp_front(seed: int, a: str, b: str, title: str, artist: str) -> object:
    c = Canvas(314, 314, 2, a, seed)
    c.gradient(0, 0, 314, 314, a, b)
    for k in range(6):
        r = 30 + k * 26
        c.ellipse(157 - r, 140 - r, 157 + r, 140 + r, outline=mix(WHITE, a, 0.3 + 0.1 * k), width=2.5)
    c.text(157, 262, title, 24, WHITE, 900, max_w=290, spacing=3)
    c.text(157, 290, artist, 11, mix(WHITE, a, 0.2), 700, max_w=290, spacing=2)
    return _face(c.array(), "paper", seed, 0.7, 8)


def _lp_back(seed: int, title: str) -> object:
    c = Canvas(314, 314, 2, "#EDE7DA", seed)
    c.gradient(0, 0, 314, 314, "#F4EFE4", "#DCD3C0")
    c.text(157, 30, title, 14, INK, 900, max_w=290)
    for side, x in (("SIDE A", 80), ("SIDE B", 234)):
        c.text(x, 62, side, 8, INK, 900)
        for k in range(5):
            c.text(x, 84 + k * 18, f"{k + 1}. Track {('ABCDE' if side == 'SIDE A' else 'FGHIJ')[k]}", 6.5, INK, 600)
    c.rect(20, 210, 294, 211, fill=INK)
    c.text(157, 236, "33⅓ RPM · STEREO", 7, INK, 800)
    c.text(157, 256, "架空レコード  FR-0001", 6, INK, 700)
    c.barcode(240, 270, 50, 26)
    return _face(c.array(), "paper", seed, 0.6, 6)


LPS = [("#1F3A5F", "#E07A3E", "MIDNIGHT TRAIN", "THE FICTIONAL QUARTET"),
       ("#5A1E3A", "#E8C64A", "SUMMER STATIC", "NOWHERE BAND"),
       ("#1E4A3A", "#9AD0B0", "QUIET HARBOR", "IMAGINARY TRIO"),
       ("#3A2A5A", "#E86A8A", "NEON CITY", "PAPER MOON ORCHESTRA")]


def lp_record() -> Product:
    """A 12-inch LP record in its printed jacket, standing up (cover to -Y)."""
    a, b, title, artist = LPS[0]
    imgs = [_lp_front(8130, a, b, title, artist), _lp_back(8131, title)]
    S, T = 0.314, 0.004
    parts = [_p("Jacket", "box", (S, T, S), (0, 0, S / 2), a, "matte", faces={"front": 0, "back": 1}, material="paper",
                bevel=0.0005)]
    return Product(slug="lp_record", name="LP レコード（12 インチ・ジャケット入り）", shape_class="assembly",
                   category="household", dims=Dimensions(S, S, depth=T), mass_kg=0.25, material="paper",
                   description="形は一般的な 12 インチの LP レコード（ジャケット 314 mm 角・厚さ 4 mm）で、寸法・質量は代表値。"
                               "立てて置く向き（ジャケットの表が -Y）。題名・アーティスト・レーベルはすべて架空。",
                   tags=["レコード", "LP", "LP レコード", "アナログ盤", "ジャケット", "LP record", "vinyl record", "record",
                         "album", "vinyl", *RECORD_TAGS], photos=[], colors=Colors(label_base=a), images=imgs, parts=parts)


def lp_record_bin() -> Product:
    """A wooden record bin (esa-bako) on legs: two rows of LPs standing in it, browsed from the front."""
    cols, t = 2, 0.018
    inner = 0.33
    W = cols * inner + (cols + 1) * t
    D, z0 = 0.40, 0.55
    wood = "#A9805A"
    imgs = [_lp_front(8132 + k, *LPS[k]) for k in range(4)]
    parts = [_p("Cabinet", "box", (W, D, z0), (0, 0, z0 / 2), mix(wood, "#000000", 0.15), "matte", material="wood"),
             _p("Bottom", "box", (W - 2 * t, D - 2 * t, 0.018), (0, 0, z0 + 0.009), wood, "matte", material="wood"),
             _p("Front", "box", (W, t, 0.12), (0, -D / 2 + t / 2, z0 + 0.06), wood, "matte", material="wood"),
             _p("Rear", "box", (W, t, 0.24), (0, D / 2 - t / 2, z0 + 0.12), wood, "matte", material="wood")]
    for k in range(cols + 1):
        x = -W / 2 + t / 2 + k * (inner + t)
        parts.append(_p(f"Side{k}", "box", (t, D - 2 * t, 0.20), (x, 0, z0 + 0.10), wood, "matte", material="wood"))
    rng = random.Random(8136)
    sleeve = ["#2B2D31", "#E8E2D2", "#8A2A2A", "#2A4A6A", "#C9A23E", "#4A6A3A", "#6A4A8A"]
    for c in range(cols):
        xc = -W / 2 + t + inner / 2 + c * (inner + t)
        for k in range(22):
            y = -D / 2 + t + 0.03 + k * 0.0145
            first = k == 0
            parts.append(_p(f"LP{c}_{k}", "box", (0.312, 0.004, 0.312), (xc, y, z0 + 0.018 + 0.155), sleeve[rng.randrange(7)],
                            "matte", rot=(-8, 0, 0), faces={"front": (2 * c) % 4 + (k % 2)} if first else None,
                            collision=False, material="paper", bevel=0))
        parts.append(_p(f"Divider{c}", "box", (0.32, 0.002, 0.34), (xc, -D / 2 + t + 0.17, z0 + 0.018 + 0.17), WHITE,
                        "matte", rot=(-8, 0, 0), collision=False, material="plastic", bevel=0))
    return Product(slug="lp_record_bin", name="レコードのエサ箱（2 列）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=40.0, static=True, material="wood",
                   description="形はレコード店の一般的な木のエサ箱（幅 714 mm・奥行き 400 mm・高さ約 890 mm、台の上に LP が立つ"
                               "箱 2 列、前は低く奥は高い縁、仕切り板）で、寸法・質量は代表値。中の LP（各列 22 枚）は見た目だけで、"
                               "先頭の 1 枚にジャケットの絵。題名はすべて架空。",
                   tags=["エサ箱", "レコード棚", "レコードラック", "LP 棚", "record bin", "record crate", "vinyl bin",
                         "record rack", "record display", *RECORD_TAGS, *STORE_TAGS], photos=[],
                   colors=Colors(label_base=wood), images=imgs, parts=parts)


# ================================================================ sports shop

def _pentagon(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(rot + 90 + 72 * k)), cy - r * math.sin(math.radians(rot + 90 + 72 * k)))
            for k in range(5)]


def _soccer_top(seed: int) -> object:
    d = 220
    c = Canvas(d, d, 2, WHITE, seed)
    c.gradient(0, 0, d, d, "#FFFFFF", "#D8DADC")
    c.polygon(_pentagon(110, 110, 30), fill=BLACK)
    for k in range(5):  # the next ring of pentagons, foreshortened toward the rim
        a = math.radians(90 + 36 + 72 * k)
        x, y = 110 + 78 * math.cos(a), 110 - 78 * math.sin(a)
        c.polygon(_pentagon(x, y, 20, 36 + 72 * k), fill=BLACK)
    for k in range(5):  # seams between them
        a0 = math.radians(90 + 72 * k)
        c.line([(110 + 30 * math.cos(a0), 110 - 30 * math.sin(a0)),
                (110 + 70 * math.cos(a0), 110 - 70 * math.sin(a0))], "#6A6E74", 1.0)
    return _face(c.array(), "plastic", seed, 0.4, 4)


def soccer_ball() -> Product:
    """A size-5 football (soccer ball): white with black pentagons."""
    d = 0.22
    parts = _ball("Ball", d, (0, 0, d / 2), WHITE, "plastic", face=0, collision=True, material="rubber")
    return Product(slug="soccer_ball", name="サッカーボール（5 号）", shape_class="assembly", category="household",
                   dims=Dimensions(d, d, depth=d), mass_kg=0.43, material="rubber",
                   description="形は一般的な 5 号のサッカーボール（直径 220 mm、白地に黒い五角形）で、寸法・質量は代表値。"
                               "転がる剛体（棚に置くときはかごか縁のある段に）。名前・メーカー名はすべて架空。",
                   tags=["サッカーボール", "ボール", "サッカー", "soccer ball", "football", "ball", "sports ball",
                         *SPORTS_TAGS], photos=[], colors=Colors(label_base=WHITE), images=[_soccer_top(8140)],
                   parts=parts)


def _basket_top(seed: int) -> object:
    d, orange = 240, "#D9661E"
    c = Canvas(d, d, 2, orange, seed)
    c.gradient(0, 0, d, d, mix(orange, WHITE, 0.15), mix(orange, "#000000", 0.20))
    rng = random.Random(seed)
    for _ in range(900):  # pebbled grain
        x, y = rng.uniform(0, d), rng.uniform(0, d)
        c.ellipse(x - 0.8, y - 0.8, x + 0.8, y + 0.8, fill=mix(orange, "#000000", 0.18))
    c.line([(0, 120), (240, 120)], BLACK, 3.5)
    c.line([(120, 0), (120, 240)], BLACK, 3.5)
    c.ellipse(-150, 20, 70, 220, outline=BLACK, width=3.5)
    c.ellipse(170, 20, 390, 220, outline=BLACK, width=3.5)
    return _face(c.array(), "plastic", seed, 0.4, 4)


def basketball() -> Product:
    """A size-7 basketball: orange pebbled rubber with black seams."""
    d = 0.24
    parts = _ball("Ball", d, (0, 0, d / 2), "#D9661E", "matte", face=0, collision=True, material="rubber")
    return Product(slug="basketball", name="バスケットボール（7 号）", shape_class="assembly", category="household",
                   dims=Dimensions(d, d, depth=d), mass_kg=0.60, material="rubber",
                   description="形は一般的な 7 号のバスケットボール（直径 240 mm、オレンジのゴムに黒い溝）で、寸法・質量は代表値。"
                               "転がる剛体。名前・メーカー名はすべて架空。",
                   tags=["バスケットボール", "ボール", "バスケ", "basketball", "ball", "sports ball", *SPORTS_TAGS],
                   photos=[], colors=Colors(label_base="#D9661E"), images=[_basket_top(8141)], parts=parts)


def ball_cart() -> Product:
    """A wire ball cart on casters, full of balls (the balls are look only)."""
    W, D, H = 0.90, 0.55, 0.95
    z0, bh = 0.18, 0.62
    mesh_l, mesh_s = _mesh(900, 620, 8142), _mesh(550, 620, 8143)
    wire = "#3A3C40"
    parts = [_p("Floor", "box", (W - 0.01, D - 0.01, 0.01), (0, 0, z0 + 0.005), wire, "metal", material="steel", bevel=0),
             _p("WallF", "box", (W, 0.006, bh), (0, -D / 2, z0 + bh / 2), wire, "metal", faces={"front": 0, "back": 0},
                material="steel", bevel=0),
             _p("WallB", "box", (W, 0.006, bh), (0, D / 2, z0 + bh / 2), wire, "metal", faces={"front": 0, "back": 0},
                material="steel", bevel=0),
             _p("WallL", "box", (0.006, D, bh), (-W / 2, 0, z0 + bh / 2), wire, "metal", faces={"left": 1, "right": 1},
                material="steel", bevel=0),
             _p("WallR", "box", (0.006, D, bh), (W / 2, 0, z0 + bh / 2), wire, "metal", faces={"left": 1, "right": 1},
                material="steel", bevel=0),
             _p("Handle", "cylinder", (0.025, 0.025, W - 0.10), (0, D / 2 + 0.03, H - 0.0125), BLACK, "matte",
                rot=(0, 90, 0), collision=False, material="rubber")]
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x, y = sx * (W / 2 - 0.05), sy * (D / 2 - 0.05)
        parts += [_wheel(f"Caster{n}", 0.10, 0.03, (x, y, 0.05)),
                  _p(f"Fork{n}", "box", (0.05, 0.06, z0 - 0.10), (x, y, 0.10 + (z0 - 0.10) / 2), CHROME, "metal",
                     collision=False, material="steel")]
    for s in (-1, 1):
        parts.append(_seg(f"HandlePost{'L' if s < 0 else 'R'}", (s * (W / 2 - 0.05), D / 2, z0 + bh),
                          (s * (W / 2 - 0.05), D / 2 + 0.03, H - 0.0125), 0.02, wire, "metal", collision=False,
                          material="steel"))
    rng = random.Random(8144)
    kinds = [(0.22, WHITE), (0.24, "#D9661E"), (0.21, "#F2D64A"), (0.22, "#2A5AA8")]
    k = 0
    for layer in range(3):
        for i in range(4):
            for j in range(2):
                dd, col = kinds[(k + layer) % 4]
                x = -W / 2 + 0.12 + i * 0.22 + rng.uniform(-0.02, 0.02)
                y = -D / 2 + 0.14 + j * 0.26 + rng.uniform(-0.02, 0.02)
                z = z0 + 0.01 + dd / 2 + layer * 0.20
                parts += _ball(f"Ball{k}", dd, (x, y, z), col, "plastic", material="rubber", segments=20)
                k += 1
    return Product(slug="ball_cart", name="ボールかご（キャスター付き）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=18.0, static=True, material="steel",
                   description="形はスポーツ用品店・体育館の一般的なキャスター付きのボールかご（900 × 550 mm・高さ 950 mm、黒い"
                               "鋼線の箱に押し手）で、寸法・質量は代表値。中のボール 24 個（サッカー・バスケット・バレー等）は"
                               "見た目だけ。床に固定。",
                   tags=["ボールかご", "ボールカート", "ボール入れ", "ボール", "ball cart", "ball basket", "ball bin",
                         "ball cage", *SPORTS_TAGS, *STORE_TAGS], photos=[], colors=Colors(label_base=wire),
                   images=[mesh_l, mesh_s], parts=parts)


def _strings(seed: int) -> object:
    c = Canvas(230, 300, 2, "#3A3D42", seed)
    c.gradient(0, 0, 230, 300, "#4A4D53", "#2B2D31")
    for x in range(8, 230, 14):
        c.line([(x, 0), (x, 300)], "#E8E4C8", 1.4)
    for y in range(8, 300, 14):
        c.line([(0, y), (230, y)], "#E8E4C8", 1.4)
    c.text(115, 150, "F", 60, "#C62828", 900)
    return _face(c.array(), "plastic", seed, 0.3, 4)


def tennis_racket() -> Product:
    """A tennis racket lying flat (head to -Y)."""
    L, hw, hl = 0.685, 0.25, 0.32
    hy = -L / 2 + hl / 2
    col = "#1F6FB2"
    parts = [_p("Head", "torus", (hw, hl, 0.022), (0, hy, 0.011), col, "glossy", material="plastic", segments=40),
             _p("Strings", "cylinder", (hw - 0.03, hl - 0.03, 0.002), (0, hy, 0.011), "#3A3D42", "plastic",
                faces={"top": 0, "bottom": 0}, collision=False, material="plastic"),
             _p("Grip", "box", (0.03, 0.20, 0.025), (0, L / 2 - 0.10, 0.0125), BLACK, "matte", material="rubber",
                bevel=0.006),
             _p("Shaft", "box", (0.022, 0.10, 0.02), (0, L / 2 - 0.25, 0.011), col, "glossy", material="plastic",
                bevel=0.004)]
    # The open throat: two arms from the shaft to where the frame's centre line is xs off the axis.
    xs, ra, rb = 0.07, hw / 2 - 0.011, hl / 2 - 0.011
    y0, y1 = hy + rb * math.sqrt(1 - (xs / ra) ** 2), L / 2 - 0.30
    for s in (-1, 1):
        a = math.degrees(math.atan2(s * xs, y1 - y0))
        parts.append(_p(f"Throat{'L' if s < 0 else 'R'}", "box", (0.016, math.hypot(xs, y1 - y0) + 0.01, 0.02),
                        (s * xs / 2, (y0 + y1) / 2, 0.011), col, "glossy", rot=(0, 0, a), collision=False,
                        material="plastic", bevel=0.003))
    return Product(slug="tennis_racket", name="テニスラケット（硬式）", shape_class="assembly", category="household",
                   dims=_dims(parts), mass_kg=0.30, material="plastic",
                   description="形は一般的な硬式テニスのラケット（全長 685 mm・フェイス 250 × 320 mm、青いフレームにガット、"
                               "黒いグリップ）で、寸法・質量は代表値。寝かせて置く向き（フェイスが -Y）。ガットは絵。"
                               "名前・メーカー名はすべて架空。",
                   tags=["テニスラケット", "ラケット", "テニス", "tennis racket", "racket", "racquet", "tennis",
                         *SPORTS_TAGS], photos=[], colors=Colors(label_base=col), images=[_strings(8145)], parts=parts)


# ================================================================ furniture store

def modern_bed() -> Product:
    """A double bed with a low wooden frame, a headboard (+Y, against the wall), a mattress, a duvet and pillows."""
    W, L = 1.46, 2.08
    wood = "#A9805A"
    parts = [_p("Frame", "box", (W, L, 0.22), (0, 0, 0.08 + 0.11), wood, "matte", material="wood", bevel=0.01),
             _p("Headboard", "box", (W, 0.05, 0.90), (0, L / 2 - 0.025, 0.45), wood, "matte", material="wood",
                bevel=0.01),
             _p("Mattress", "box", (1.40, 1.95, 0.22), (0, -0.04, 0.30 + 0.11), "#F2F0EC", "matte", material="fabric",
                bevel=0.03),
             _p("Duvet", "box", (1.44, 1.35, 0.07), (0, -0.33, 0.52 + 0.035), "#9AA8B8", "matte", material="fabric",
                bevel=0.03),
             _p("DuvetFold", "box", (1.44, 0.20, 0.08), (0, 0.32, 0.52 + 0.04), "#E8E4DA", "matte", material="fabric",
                bevel=0.03)]
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_p(f"Leg{n}", "box", (0.05, 0.05, 0.08), (sx * (W / 2 - 0.06), sy * (L / 2 - 0.10), 0.04),
                        mix(wood, "#000000", 0.3), "matte", material="wood"))
    for s in (-1, 1):
        parts.append(_p(f"Pillow{'L' if s < 0 else 'R'}", "box", (0.60, 0.40, 0.13), (s * 0.34, 0.68, 0.52 + 0.065),
                        WHITE, "matte", collision=False, material="fabric", bevel=0.05))
    return Product(slug="modern_bed", name="ダブルベッド（木のフレーム・寝具付き）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=75.0, static=True, material="wood",
                   description="形は家具店・寝室の一般的なダブルベッド（1460 × 2080 mm、マットレス上面 520 mm、ヘッドボード"
                               "高さ 900 mm、明るい木のフレームにマットレス・掛け布団・枕 2 つ）で、寸法・質量は代表値。"
                               "頭側（ヘッドボード）が +Y で壁に寄せる。床に固定。名前・メーカー名はすべて架空。",
                   tags=["ベッド", "ダブルベッド", "寝具", "bed", "double bed", "bed frame", "queen bed", *FURNITURE_TAGS,
                         *HOME_TAGS], photos=[], colors=Colors(label_base=wood), images=[], parts=parts)


def nightstand() -> Product:
    """A small bedside table with two drawers."""
    W, D, H = 0.45, 0.40, 0.50
    wood = "#A9805A"
    parts = [_p("Body", "box", (W, D, H - 0.10 - 0.02), (0, 0, 0.10 + (H - 0.12) / 2), wood, "matte", material="wood",
                bevel=0.004),
             _p("Top", "box", (W + 0.01, D + 0.01, 0.02), (0, 0, H - 0.01), mix(wood, "#000000", 0.08), "matte",
                material="wood", bevel=0.003)]
    for k in range(2):
        z = 0.10 + 0.02 + k * 0.18 + 0.08
        parts += [_p(f"Drawer{k}", "box", (W - 0.03, 0.006, 0.16), (0, -D / 2 - 0.002, z), mix(wood, WHITE, 0.08),
                     "matte", collision=False, material="wood", bevel=0.002),
                  _p(f"Knob{k}", "box", (0.08, 0.012, 0.012), (0, -D / 2 - 0.011, z), "#2B2D31", "metal",
                     collision=False, material="steel", bevel=0.002)]
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_p(f"Leg{n}", "box", (0.03, 0.03, 0.10), (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0.05),
                        mix(wood, "#000000", 0.3), "matte", material="wood"))
    return Product(slug="nightstand", name="ナイトテーブル（引き出し 2 段）", shape_class="assembly",
                   category="household", dims=_dims(parts), mass_kg=9.0, material="wood",
                   description="形は一般的なベッドの横のナイトテーブル（幅 450 mm・奥行き 400 mm・高さ 500 mm、明るい木、"
                               "引き出し 2 段と脚）で、寸法・質量は代表値。剛体。天板にランプや時計を置ける。",
                   tags=["ナイトテーブル", "サイドテーブル", "ベッドサイドテーブル", "nightstand", "bedside table",
                         "night table", "side table", *FURNITURE_TAGS, *HOME_TAGS], photos=[],
                   colors=Colors(label_base=wood), images=[], parts=parts)


def wardrobe() -> Product:
    """A two-door wardrobe (closet cabinet) on a plinth."""
    W, D, H = 1.00, 0.60, 1.90
    body = "#EDE8DE"
    parts = [_p("Body", "box", (W, D, H - 0.06), (0, 0, 0.06 + (H - 0.06) / 2), body, "matte", material="wood",
                bevel=0.004),
             _p("Plinth", "box", (W - 0.04, D - 0.04, 0.06), (0, 0.0, 0.03), mix(body, "#000000", 0.3), "matte",
                material="wood")]
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        parts += [_p(f"Door{side}", "box", (W / 2 - 0.006, 0.018, H - 0.08), (s * W / 4, -D / 2 - 0.009, 0.06 + (H - 0.08) / 2 + 0.01),
                     body, "matte", collision=False, material="wood", bevel=0.003),
                  _p(f"Handle{side}", "box", (0.012, 0.02, 0.30), (s * 0.04, -D / 2 - 0.028, 1.05), "#2B2D31", "metal",
                     collision=False, material="steel", bevel=0.003)]
    return Product(slug="wardrobe", name="ワードローブ（両開き・幅 1000）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=70.0, static=True, material="wood",
                   description="形は家具店・寝室の一般的な両開きのワードローブ（幅 1000 mm・奥行き 600 mm・高さ 1900 mm、生成りの"
                               "扉に黒い縦の取っ手、台輪）で、寸法・質量は代表値。扉は開かない。床に固定。名前・メーカー名はすべて架空。",
                   tags=["ワードローブ", "洋服タンス", "クローゼット", "衣装棚", "wardrobe", "closet", "armoire",
                         "clothes cabinet", *FURNITURE_TAGS, *HOME_TAGS], photos=[], colors=Colors(label_base=body),
                   images=[], parts=parts)


# ================================================================ cosmetics store

def round_display_table() -> Product:
    """A two-tier round display table on a pedestal (the tops are fill shelves)."""
    top = "#F4F1EC"
    base = "#C9A97A"
    parts = [_p("Foot", "cylinder", (0.50, 0.50, 0.04), (0, 0, 0.02), base, "metal", material="steel"),
             _p("Post", "cylinder", (0.10, 0.10, 0.66), (0, 0, 0.04 + 0.33), base, "metal", material="steel"),
             _p("TopLow", "cylinder", (1.00, 1.00, 0.03), (0, 0, 0.715), top, "glossy", material="wood"),
             _p("EdgeLow", "torus", (1.01, 1.01, 0.03), (0, 0, 0.715), base, "metal", collision=False,
                material="steel"),
             _p("PostUp", "cylinder", (0.08, 0.08, 0.22), (0, 0, 0.73 + 0.11), base, "metal", material="steel"),
             _p("TopUp", "cylinder", (0.55, 0.55, 0.025), (0, 0, 0.95 + 0.0125), top, "glossy", material="wood"),
             _p("EdgeUp", "torus", (0.56, 0.56, 0.025), (0, 0, 0.9625), base, "metal", collision=False,
                material="steel")]
    return Product(slug="round_display_table", name="丸い陳列台（2 段）", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=35.0, static=True, material="wood",
                   description="形は化粧品店・雑貨店・アパレルの一般的な丸い 2 段の陳列台（下段の直径 1000 mm・高さ 730 mm、上段の"
                               "直径 550 mm・高さ 975 mm、白い天板に金色の縁と脚）で、寸法・質量は代表値。床に固定。両段が商品を並べる"
                               "棚板（下段の上の空きは 220 mm）。",
                   tags=["丸テーブル", "陳列台", "丸い陳列台", "ラウンドテーブル", "什器", "round display table",
                         "display table", "round table", "tiered display table", "cosmetics display", *COSME_TAGS,
                         *STORE_TAGS, "雑貨", "variety store"], photos=[], colors=Colors(label_base=top), images=[],
                   parts=parts)


def _tester_sign(seed: int) -> object:
    c = Canvas(800, 200, 1, "#F6E8EC", seed)
    c.gradient(0, 0, 800, 200, "#FBF2F4", "#EBCBD3")
    c.text(400, 80, "TESTER", 80, "#8A2A4A", 900, spacing=20)
    c.text(400, 155, "ご自由にお試しください", 40, "#8A2A4A", 800)
    return _face(c.array(), "paper", seed, 0.4, 6)


def cosmetics_tester_island() -> Product:
    """A cosmetics tester island: a white cabinet, tester trays of lipsticks and bottles, a mirror and a sign."""
    W, D, Hb = 1.20, 0.60, 0.80
    parts = [_p("Cabinet", "box", (W, D, Hb), (0, 0, Hb / 2), "#F4F2EE", "glossy", material="wood"),
             _p("Top", "box", (W + 0.04, D + 0.04, 0.03), (0, 0, Hb + 0.015), WHITE, "glossy", material="stone"),
             _p("Mirror", "box", (0.40, 0.02, 0.40), (0, 0.10, Hb + 0.03 + 0.22), CHROME, "metal", material="glass",
                bevel=0.004),
             _p("MirrorFoot", "box", (0.20, 0.10, 0.02), (0, 0.10, Hb + 0.04), "#C9A97A", "metal", collision=False,
                material="steel"),
             _p("Sign", "box", (0.80, 0.02, 0.20), (0, 0.22, 1.60), WHITE, "matte", faces={"front": 0, "back": 0},
                collision=False, material="plastic")]
    for s in (-1, 1):
        parts.append(_p(f"SignPost{'L' if s < 0 else 'R'}", "cylinder", (0.02, 0.02, 1.50 - Hb - 0.03),
                        (s * 0.36, 0.22, Hb + 0.03 + (1.50 - Hb - 0.03) / 2), "#C9A97A", "metal", material="steel"))
    shades = ["#B3202A", "#D84A6A", "#E88A8A", "#A0424A", "#C96A4A", "#8A2A4A", "#F0A0A8", "#7A3030", "#D06A80", "#B85A5A"]
    for side, x0 in (("L", -0.50), ("R", 0.12)):
        parts.append(_p(f"Tray{side}", "box", (0.38, 0.22, 0.02), (x0 + 0.19, -0.14, Hb + 0.04), "#E8E4EC",
                        "glass", material="plastic", thin_walled=True, bevel=0.002))
        for r in range(2):
            for k in range(8):
                x = x0 + 0.03 + k * 0.045
                y = -0.20 + r * 0.10
                if side == "L":
                    parts += [_p(f"Lip{side}{r}{k}", "cylinder", (0.018, 0.018, 0.06), (x, y, Hb + 0.05 + 0.03),
                                 "#1E1E1E", "glossy", collision=False, material="plastic", segments=16),
                              _p(f"LipTip{side}{r}{k}", "cylinder", (0.012, 0.012, 0.015), (x, y, Hb + 0.11 + 0.0075),
                                 shades[(r * 8 + k) % 10], "glossy", collision=False, material="plastic", segments=12)]
                else:
                    h = 0.07 + 0.02 * ((k + r) % 3)
                    parts += [_p(f"Bottle{side}{r}{k}", "cylinder", (0.03, 0.03, h), (x, y, Hb + 0.05 + h / 2),
                                 mix("#E8D4C8", "#8A5A4A", 0.12 * ((k * 3 + r) % 6)), "glass", collision=False,
                                 material="glass", segments=16),
                              _p(f"BottleCap{side}{r}{k}", "cylinder", (0.018, 0.018, 0.02), (x, y, Hb + 0.05 + h + 0.01),
                                 "#C9A97A", "metal", collision=False, material="steel", segments=12)]
    return Product(slug="cosmetics_tester_island", name="化粧品のテスター台（島型）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=80.0, static=True, material="wood",
                   description="形は化粧品店・ドラッグストアの売場の中央に置く一般的なテスター台（幅 1240 mm・奥行き 640 mm・"
                               "台の高さ 830 mm、白い台にアクリルのトレー 2 枚の口紅・小瓶のテスター、鏡、上に「TESTER」の看板）で、"
                               "寸法・質量は代表値。テスターは見た目だけ。看板の文字は架空。",
                   tags=["テスター", "テスター台", "化粧品テスター", "コスメ什器", "化粧品什器", "tester counter",
                         "tester stand", "makeup tester", "cosmetics display", "cosmetics counter", "beauty counter",
                         *COSME_TAGS, *STORE_TAGS], photos=[], colors=Colors(label_base="#F4F2EE"),
                   images=[_tester_sign(8150)], parts=parts)


# ================================================================ souvenir shop

def _postcard(seed: int, kind: int) -> object:
    c = Canvas(100, 148, 4, WHITE, seed)
    if kind == 0:  # a mountain at dawn
        c.gradient(0, 0, 100, 148, "#F6C28A", "#7AA8D8")
        c.polygon([(0, 120), (50, 40), (100, 120)], fill="#3E5A8A")
        c.polygon([(38, 59), (50, 40), (62, 59), (55, 55), (50, 60), (44, 55)], fill=WHITE)
        c.ellipse(70, 18, 88, 36, fill="#E8503A")
    elif kind == 1:  # waves
        c.gradient(0, 0, 100, 148, "#E8F0F4", "#2A5A8A")
        c.pattern(0, 60, 100, 148, "waves", WHITE, 10, 1.4)
    elif kind == 2:  # flowers
        c.gradient(0, 0, 100, 148, "#FBE8EE", "#E8A8B8")
        rng = random.Random(seed)
        for _ in range(18):
            x, y = rng.uniform(8, 92), rng.uniform(10, 120)
            for k in range(5):
                a = math.radians(72 * k)
                c.ellipse(x + 4 * math.cos(a) - 3, y + 4 * math.sin(a) - 3, x + 4 * math.cos(a) + 3,
                          y + 4 * math.sin(a) + 3, fill="#F4F4F0")
            c.ellipse(x - 1.6, y - 1.6, x + 1.6, y + 1.6, fill="#E8B83A")
    else:  # a town at night
        c.gradient(0, 0, 100, 148, "#1A2244", "#4A3A6A")
        rng = random.Random(seed)
        x = 0.0
        while x < 100:
            w, h = rng.uniform(8, 16), rng.uniform(30, 80)
            c.rect(x, 128 - h, x + w, 128, fill="#14182A")
            for wy in range(int(128 - h + 4), 124, 8):
                c.rect(x + 2, wy, x + 4, wy + 3, fill="#F2D07A")
            x += w + 1
    c.rect(0, 128, 100, 148, fill=WHITE)
    c.text(50, 138, "POST CARD", 6, INK, 800, spacing=1.5)
    return _face(c.array(), "paper", seed, 0.5, 3)


def postcard_spinner_rack() -> Product:
    """A souvenir-shop spinner rack: four faces of wire pockets full of postcards, turning on a round base."""
    pole_top, Hr = 1.62, 0.96
    rows, cols = 6, 2
    imgs = [_postcard(8160 + k, k) for k in range(4)]
    wire = "#3A3C40"
    parts = [_p("Base", "cylinder", (0.46, 0.46, 0.05), (0, 0, 0.025), wire, "metal", material="steel"),
             _p("Bearing", "cylinder", (0.08, 0.08, 0.03), (0, 0, 0.065), "#2B2D31", "metal", material="steel")]
    spin = [_p("Pole", "cylinder", (0.03, 0.03, pole_top - 0.08), (0, 0, 0.08 + (pole_top - 0.08) / 2), wire, "metal",
               material="steel"),
            _p("Cap", "cylinder", (0.05, 0.05, 0.02), (0, 0, pole_top + 0.01), wire, "metal", collision=False,
               material="steel")]
    z_low = pole_top - Hr
    for f in range(4):
        a = math.radians(90 * f)
        ca, sa = math.cos(a), math.sin(a)

        def at(x, y, z):
            return (x * ca - y * sa, x * sa + y * ca, z)

        spin.append(_p(f"Panel{f}", "box", (0.26, 0.006, Hr), at(0, -0.08, z_low + Hr / 2), wire, "metal",
                       rot=(0, 0, 90 * f), material="steel", bevel=0))
        for r in range(rows):
            zb = z_low + 0.01 + r * Hr / rows
            spin.append(_p(f"Lip{f}{r}", "box", (0.26, 0.04, 0.008), at(0, -0.10, zb), wire, "metal",
                           rot=(0, 0, 90 * f), collision=False, material="steel", bevel=0))
            for c in range(cols):
                x = (c - 0.5) * 0.125
                spin.append(_p(f"Card{f}{r}{c}", "box", (0.10, 0.003, 0.148), at(x, -0.105, zb + 0.004 + 0.074),
                               WHITE, "matte", rot=(-6, 0, 90 * f), faces={"front": (f + r + c) % 4},
                               collision=False, material="paper", bevel=0))
    for p in spin:
        p.link = "SpinnerLink"
    parts += spin
    joints = [Joint(link="SpinnerLink", anchor=[0.0, 0.0, 0.08], limits=None, axis="Z")]
    return Product(slug="postcard_spinner_rack", name="絵はがきの回転ラック", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=15.0, static=True, material="steel", joints=joints,
                   description="形は土産物店・書店の一般的な絵はがきの回転ラック（丸い台の直径 460 mm・高さ 1640 mm、4 面に"
                               "鋼線のポケットが 6 段 × 2 列）で、寸法・質量は代表値。支柱から上（SpinnerLink）は Z 軸まわりに回る。"
                               "絵はがき（48 枚）は見た目だけで、絵柄は架空の風景。",
                   tags=["回転ラック", "絵はがき", "ポストカード", "ポストカードラック", "スピナー", "spinner rack",
                         "postcard rack", "postcard spinner", "rotating rack", "card rack", *SOUVENIR_TAGS,
                         *STORE_TAGS], photos=[], colors=Colors(label_base=wire), images=imgs, parts=parts)


def shop_fix_window() -> Product:
    """A wide fixed shop window (2600 x 2000 mm) with a centre mullion: two big panes that do not open."""
    W, H, D = 2.60, 2.00, 0.070
    color = ALU_DARK
    parts = _frame(W, H, D, color)
    parts.append(_p("Mullion", "box", (F, D, H - 2 * F), (0, 0, H / 2), color, "metal", material="aluminum",
                    bevel=0.002))
    pw = W / 2 - 1.5 * F
    for k, s in enumerate((-1, 1)):
        x = s * (W / 4 - F / 4)
        parts.append(_p(f"Glass{k}", "box", (pw + 0.01, 0.010, H - 2 * F + 0.01), (x, 0, H / 2), WINDOW_GLASS, "glass",
                        material="glass", bevel=0))
        for j, y in enumerate((-0.009, 0.009)):
            parts += [_p(f"Bead{k}{j}T", "box", (pw, 0.006, 0.010), (x, y, H - F - 0.005), "#202224", "matte",
                         collision=False, material="rubber", bevel=0),
                      _p(f"Bead{k}{j}B", "box", (pw, 0.006, 0.010), (x, y, F + 0.005), "#202224", "matte",
                         collision=False, material="rubber", bevel=0)]
    return Product(slug="shop_fix_window", name="店の FIX 窓 2600×2000（中央方立て）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D), mass_kg=110.0, static=True, material="aluminum",
                   description="形は店舗の前面の一般的なアルミのはめ殺し窓（枠の外寸 2600 × 2000 mm、見込み 70 mm、中央に方立て、"
                               "ダークブロンズの枠に大きな透明ガラス 2 枚）で、寸法・質量は代表値。開かない。正面（-Y）が室内側。"
                               "幅 2〜3 m の開口に伸縮して入れる（0.75〜1.33 倍で 1.95〜3.46 m）。",
                   tags=["窓", "FIX 窓", "はめ殺し窓", "店の窓", "ショーウィンドウ", "大開口", "サッシ", "建具", "内装",
                         "window", "fixed window", "shop window", "storefront window", "display window", "wide window",
                         "picture window", "aluminum window", *STORE_TAGS], photos=[], colors=Colors(label_base=color),
                   images=[], parts=parts)


# ================================================================ Asian grocery

def asian_noodle_bag() -> Product:
    """A single pack of Asian instant noodles (tom yum flavour) in a printed film bag."""
    W, H = 120.0, 160.0
    orange, green, dark = "#E8641E", "#2E7D32", "#3A1A0A"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 6, orange, seed)
        c.gradient(0, 0, W, H, "#F07A2E", "#C24A12")
        seal_crimp(c, 0, 0, W, 10, "#D85A1A", 1.6)
        seal_crimp(c, 0, H - 10, W, H, "#B8420E", 1.6)
        return c

    c = base(8170)
    c.rect(10, 18, W - 10, 62, fill="#FFF4E0", radius=6)
    c.text(W / 2, 32, "トムヤム麺", 13, "#B3202A", 900)
    c.text(W / 2, 48, "TOM YUM NOODLES", 6.0, green, 900, spacing=1.0)
    c.text(W / 2, 57, "HOT & SOUR", 4.5, dark, 800, spacing=1.0)
    c.ellipse(20, 70, 100, 130, fill="#F6E2B8", outline="#8A4A1A", width=1.2)  # a bowl of noodles (drawn)
    for k in range(9):
        c.line([(28 + k * 7, 92), (34 + k * 7, 118)], "#E8C46A", 1.4)
    c.ellipse(36, 84, 50, 96, fill="#E8503A")
    c.ellipse(70, 86, 84, 98, fill="#7FB04A")
    c.ellipse(W - 40, 122, W - 8, 146, fill=green)
    c.text(W - 24, 134, "辛口", 7, WHITE, 900)
    c.text(28, 140, "めん 70g", 5, WHITE, 800)
    front = _pouch(c, 8170, 1.0, 16)
    b = base(8171)
    b.rect(10, 16, W - 10, H - 16, fill=WHITE, radius=3)
    b.text(W / 2, 26, "トムヤム麺（輸入品）", 6.5, orange, 900)
    rows = [("名称", "即席めん"), ("原材料名", "めん（小麦粉、パーム油、食塩）、スープ（香辛料、砂糖、食塩、えび粉末）"),
            ("内容量", "70g"), ("原産国名", "架空国"), ("輸入者", "架空食品貿易 株式会社")]
    y = 36.0
    for k, v in rows:
        b.text(14, y, f"{k}：{v}", 3.6, INK, 600, anchor="lm", max_w=W - 28)
        y += 9
    b.barcode(W / 2 - 18, H - 46, 36, 24)
    back = _pouch(b, 8171, 1.0, 16)
    return Product(slug="asian_noodle_bag", name="トムヤム麺（輸入の袋めん）", shape_class="pouch", category="food",
                   dims=Dimensions(0.16, 0.12, depth=0.035), mass_kg=0.075, material="film",
                   description="形はアジア食材店の一般的な輸入の袋入り即席めん（高さ 160 mm・幅 120 mm・厚さ約 35 mm、オレンジの袋に"
                               "日本語の表示シール）で、寸法・質量は代表値。商品名・輸入者・原産国はすべて架空。",
                   tags=["袋めん", "袋麺", "インスタントラーメン", "即席めん", "トムヤム", "輸入食品", "instant noodles",
                         "noodle pack", "ramen", "asian noodles", "tom yum", *ASIAN_TAGS], photos=[],
                   colors=Colors(label_base=orange), images=[front, back], faces={"front": 0, "back": 1})


def jasmine_rice_bag() -> Product:
    """A 5 kg bag of jasmine rice in a printed film bag."""
    W, H = 300.0, 450.0
    green, gold, cream = "#1E6B3A", "#D9B25A", "#FBF6E8"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 3, cream, seed)
        c.gradient(0, 0, W, H, "#FFFBF0", "#EDE3C8")
        seal_crimp(c, 0, 0, W, 18, gold, 2.4)
        seal_crimp(c, 0, H - 18, W, H, gold, 2.4)
        return c

    c = base(8172)
    c.rect(0, 40, W, 150, fill=green)
    c.text(W / 2, 80, "JASMINE RICE", 30, gold, 900, spacing=2)
    c.text(W / 2, 122, "ジャスミンライス", 24, WHITE, 900)
    for k in range(7):  # rice ears (drawn)
        x = 60 + k * 30
        c.line([(x, 330), (x + 10, 200)], "#8A7A3A", 2.0)
        for j in range(6):
            c.ellipse(x + 4 + j * 1.2, 205 + j * 18, x + 14 + j * 1.2, 218 + j * 18, fill="#E8D49A")
    c.ellipse(W - 110, 340, W - 20, 430, fill=green)
    c.text(W - 65, 375, "5kg", 26, WHITE, 900)
    c.text(W - 65, 402, "香り米", 12, gold, 900)
    c.text(30, 420, "長粒種・精米", 12, green, 900, anchor="lm")
    front = _pouch(c, 8172, 1.0, 24)
    b = base(8173)
    b.rect(20, 40, W - 20, H - 40, fill=WHITE, radius=4)
    b.text(W / 2, 62, "ジャスミンライス 5kg（輸入米）", 13, green, 900)
    rows = [("名称", "精米"), ("原料玄米", "単一原料米 長粒種"), ("内容量", "5kg"), ("原産国名", "架空国"),
            ("輸入者", "架空食品貿易 株式会社"), ("炊き方", "洗米後、水は米の 1.2 倍。30 分浸してから炊く。")]
    y = 92.0
    for k, v in rows:
        b.text(34, y, f"{k}：{v}", 9, INK, 600, anchor="lm", max_w=W - 68)
        y += 24
    b.barcode(W / 2 - 40, H - 120, 80, 50)
    back = _pouch(b, 8173, 1.0, 24)
    return Product(slug="jasmine_rice_bag", name="ジャスミンライス 5kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.45, 0.30, depth=0.10), mass_kg=5.05, material="film",
                   description="形はアジア食材店の一般的な輸入米の袋（5 kg、高さ 450 mm・幅 300 mm・厚さ約 100 mm、生成りに緑の帯と"
                               "金の文字）で、寸法・質量は代表値。商品名・輸入者・原産国はすべて架空。",
                   tags=["米", "米袋", "ジャスミンライス", "タイ米", "長粒米", "輸入米", "rice", "rice bag", "jasmine rice",
                         "thai rice", "long grain rice", *ASIAN_TAGS], photos=[], colors=Colors(label_base=cream),
                   images=[front, back], faces={"front": 0, "back": 1})


def chili_oil_jar() -> Product:
    """A glass jar of crunchy chili oil with a red screw lid."""
    form = jar(0.105, 0.068, cap_h=0.018, cap_d=0.066, label=(0.016, 0.078))
    form.liquid_top = 0.082
    red, cream, liquid = "#B3202A", "#FFF4E0", "#8E1A10"
    c = label_canvas(form, cream, seed=8174)
    Wc, Hc = c.w_mm, c.h_mm
    fx = 0.75 * Wc
    c.gradient(0, 0, Wc, Hc, "#FFF8EC", "#F2DCC0")
    c.rect(fx - 40, 0, fx + 40, Hc, fill=red)
    c.rect(fx - 38, 3, fx + 38, Hc - 3, outline="#E8C64A", width=0.6)
    c.text(fx, 18, "食べるラー油", 8, WHITE, 900)
    c.text(fx, 31, "CHILI OIL", 6.5, "#E8C64A", 900, spacing=1.2)
    c.text(fx, 42, "辣油 · CRISPY", 4, WHITE, 800)
    c.text(fx, 54, "内容量 210g", 3.6, WHITE, 700)
    _bottle_back(c, 0.25 * Wc, 4, 44, "食べるラー油", "食用植物油脂、唐辛子、にんにく、たまねぎ、ごま、食塩", 1.6,
                 color=INK, bg=cream, extra=[("内容量", "210g"), ("原産国名", "架空国"), ("輸入者", "架空食品貿易 株式会社")])
    c.barcode(0.25 * Wc - 10, 48, 20, 11)
    label = finish(c.array(), "paper", 8174, 0.5)
    t = top_canvas(form, red, seed=8175)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#C62828", "#8E1414")
    t.ellipse(d * 0.12, d * 0.12, d * 0.88, d * 0.88, outline="#E8C64A", width=0.8)
    t.text(d / 2, d / 2, "辣", 22, "#E8C64A", 900)
    top = finish(t.array(), "metal", 8175, 0.5)
    return Product(slug="chili_oil_jar", name="食べるラー油（瓶）", category="food", mass_kg=0.40, material="glass",
                   description="形はアジア食材店の一般的な瓶入りの食べるラー油（高さ 105 mm・胴径 68 mm、赤いねじ蓋）で、"
                               "寸法・質量は代表値。中身は赤い油の色。商品名・輸入者・原産国はすべて架空。",
                   tags=["ラー油", "食べるラー油", "調味料", "瓶", "中華調味料", "chili oil", "chili crisp", "condiment",
                         "seasoning", "sauce jar", *ASIAN_TAGS], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


def _sauce_bottle(H: float, D: float) -> RevolveForm:
    R = D / 2
    neck_r, cap_r, cap_h = 0.0135, 0.0165, 0.022
    cap_z = H - cap_h
    sh_z = 0.58 * H
    body = [(0.0, R * 0.88)] + _arc(0.0005, 0.006, R * 0.93, R, 8, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, sh_z + 0.045, R, neck_r * 1.1, 30, "cos")[1:]
    body += [(cap_z - 0.004, neck_r), (cap_z, neck_r)]
    cap = [(cap_z, cap_r), (H - 0.0015, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, (0.020, 0.108), None)


def oyster_sauce_bottle() -> Product:
    """A glass bottle of oyster sauce with a red cap."""
    form = _sauce_bottle(0.200, 0.064)
    form.liquid_top = 0.150
    red, cream, liquid = "#B3202A", "#FFF4E0", "#2A140C"
    c = label_canvas(form, cream, seed=8176)
    Wc, Hc = c.w_mm, c.h_mm
    fx = 0.75 * Wc
    c.gradient(0, 0, Wc, Hc, "#FFF8EC", "#EAD8B8")
    c.rect(fx - 36, 0, fx + 36, 24, fill=red)
    c.text(fx, 12, "OYSTER SAUCE", 7, WHITE, 900, spacing=1.2)
    c.ellipse(fx - 16, 30, fx + 16, 54, fill="#5A6A7A", outline="#2B3A4A", width=0.8)  # an oyster shell (drawn)
    for k in range(4):
        c.line([(fx - 12 + k * 7, 34), (fx - 4 + k * 3, 50)], "#9AA8B4", 0.6)
    c.text(fx, 64, "オイスターソース", 6, red, 900)
    c.text(fx, 74, "かき油  510g", 4, INK, 800)
    c.rect(fx - 36, Hc - 8, fx + 36, Hc, fill=red)
    _bottle_back(c, 0.25 * Wc, 4, 44, "オイスターソース", "かきエキス、砂糖、食塩、でん粉、しょうゆ", 1.7, color=INK,
                 bg=cream, extra=[("内容量", "510g"), ("原産国名", "架空国"), ("輸入者", "架空食品貿易 株式会社")])
    c.barcode(0.25 * Wc - 11, 62, 22, 12)
    label = finish(c.array(), "paper", 8176, 0.5)
    t = top_canvas(form, red, seed=8177)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#C62828", "#8E1414")
    t.ellipse(d * 0.15, d * 0.15, d * 0.85, d * 0.85, outline=WHITE, width=0.6)
    top = finish(t.array(), "plastic", 8177, 0.5)
    return Product(slug="oyster_sauce_bottle", name="オイスターソース（瓶 510g）", category="food", mass_kg=0.85,
                   capacity_ml=420, material="glass",
                   description="形はアジア食材店の一般的な瓶入りのオイスターソース（高さ 200 mm・胴径 64 mm、赤いキャップ）で、"
                               "寸法・質量は代表値。キャップは瓶と同じ 1 つの剛体。中身は濃い茶色。商品名・輸入者・原産国はすべて架空。",
                   tags=["オイスターソース", "かき油", "調味料", "中華調味料", "ソース", "瓶", "oyster sauce", "sauce",
                         "condiment", "seasoning", "sauce bottle", *ASIAN_TAGS], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base=cream),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


PRODUCTS = {f.__name__: f for f in (
    road_bicycle, city_bicycle, bicycle_helmet, bicycle_stand_rack,
    woven_basket, basket_display_stand,
    dango_pack, manju_pack, monaka_pack, yokan_bar, wagashi_gift_box, wagashi_showcase, noren,
    lp_record, lp_record_bin,
    soccer_ball, basketball, ball_cart, tennis_racket,
    modern_bed, nightstand, wardrobe,
    round_display_table, cosmetics_tester_island,
    postcard_spinner_rack, shop_fix_window,
    asian_noodle_bag, jasmine_rice_bag, chili_oil_jar, oyster_sauce_bottle,
)}
