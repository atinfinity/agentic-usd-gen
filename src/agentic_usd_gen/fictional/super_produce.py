"""架空の商品のデザイン: スーパーの青果（ばら売り・袋・パック）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の青果の一般的な値にする。
野菜・果物の形は丸い山（dome・bun）や回転体の部品を組み合わせ、皮の色・模様は描いた絵（いちごだけ CC0 の写真）。
袋・フィルムは薄い透明の膜（thin_walled）で、値札は産地「国産」とダミーのバーコード（インストアコード）。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .paint import Canvas, finish, mix
from .products import INK, _box, _face, _food_photo

CLEAR = "#F2F6F8"
WHITE = "#FFFFFF"
GREEN_TAG = "#2E7D32"


# ---------------------------------------------------------------- 共通の部品と絵


def _p(name: str, shape: str, size, center, color: str, finish_: str = "plastic", rotation=None, faces=None,
       collision: bool = True, material: str | None = "food", profile=None, thin_walled: bool = False) -> Part:
    return Part(name, shape, [float(v) for v in size], [float(v) for v in center],
                [float(v) for v in (rotation or (0, 0, 0))], color=color, finish=finish_, faces=faces,
                collision=collision, material=material, profile=profile, thin_walled=thin_walled)


def _along(a, b) -> tuple[list[float], list[float], float]:
    """a から b へ向かう細長い部品（Z 軸が長さ）の中心・回転 [度]・長さ。"""
    d = np.subtract(b, a)
    L = float(np.linalg.norm(d))
    u = d / L
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, u[2]))))
    yaw = math.degrees(math.atan2(u[1], u[0]))
    return [float(v) for v in (np.add(a, b) / 2)], [0.0, pitch, yaw], L


def _film(name: str, size, center, collision: bool = True) -> Part:
    """袋・ラップの薄い透明フィルム（肩の丸い山形）。"""
    return _p(name, "bun", size, center, CLEAR, "glass", collision=collision, material="film", thin_walled=True)


def _label(w: float, h: float, title: str, sub: str, price: int, accent: str, seed: int, *,
           photo: tuple | None = None, keep: str | None = None) -> np.ndarray:
    """青果の値札シール（品名・産地「国産」・価格・ダミーのバーコード）。"""
    c = Canvas(w, h, 14, WHITE, seed)
    c.rect(0, 0, w, h * 0.34, fill=accent)
    c.text(w / 2, h * 0.10, sub, h * 0.10, mix(accent, WHITE, 0.8), 800, max_w=w - 6)
    c.text(w / 2, h * 0.24, title, h * 0.15, WHITE, 900, max_w=w - 6)
    x0 = 3.0
    if photo:
        pid, crop = photo
        c.photo(pid, 2.5, h * 0.38, 2.5 + h * 0.30, h * 0.68, shape="round", radius=1.5, crop=crop)
        x0 = 2.5 + h * 0.30 + 2
    c.text(x0, h * 0.44, "産地  国産", h * 0.08, INK, 800, anchor="lm", max_w=w * 0.52 - x0)
    c.text(x0, h * 0.56, keep or "お早めにお召し上がりください", h * 0.06, INK, 600, anchor="lm", max_w=w * 0.56 - x0)
    c.text(w - 3, h * 0.48, f"{price}円", h * 0.16, accent, 900, anchor="rm", max_w=w * 0.38)
    c.text(w - 3, h * 0.61, "税込", h * 0.06, accent, 700, anchor="rm")
    c.barcode(3, h * 0.70, w * 0.46, h * 0.24)
    c.paragraph(w * 0.54, h * 0.71, w - 3, NOTICE, h * 0.045, INK, 500)
    return _face(c.array(), "paper", seed, 0.5, 4)


def _radial(c: Canvas, cx: float, cy: float, r: float, inner: str, outer: str, steps: int = 40):
    """中心から外へ色が変わる円（上から見た丸い山の色の濃淡）。"""
    for k in range(steps):
        t = k / (steps - 1)
        rr = r * (1 - t) + 1e-3
        c.ellipse(cx - rr, cy - rr, cx + rr, cy + rr, fill=mix(outer, inner, t))


def _speckle(c: Canvas, n: int, colors: list[str], a: tuple[float, float]):
    """細かい点（皮のつぶ・果点）。"""
    for _ in range(n):
        x, y = c.rng.uniform(0, c.w_mm), c.rng.uniform(0, c.h_mm)
        r = c.rng.uniform(*a)
        c.ellipse(x - r, y - r, x + r, y + r, fill=c.rng.choice(colors))


def _skin(c: Canvas, seed: int, strength: float = 0.4) -> np.ndarray:
    return finish(c.array(), "paper", seed, strength)


def _product(slug: str, name: str, dims: Dimensions, mass: float, description: str, tags: list[str], parts,
             images, base: str, material: str = "food", photos: list[str] | None = None) -> Product:
    return Product(slug=slug, name=name, shape_class="assembly", category="food", dims=dims, mass_kg=mass,
                   material=material, description=description, tags=[*tags, "青果", "生鮮", "produce"],
                   photos=photos or [], colors=Colors(label_base=base), images=images, parts=parts)


# ---------------------------------------------------------------- りんご


def apple_single() -> Product:
    """りんご 1 個（ばら売り）。下半分と上半分の肩の張った山（bun）を合わせ、上半分に赤いすじ模様の皮を
    真上から貼る（すじが軸から放射状に見える）。軸と、肩に小さな値札シール。"""
    D, h_lo, h_up = 0.085, 0.036, 0.046
    red, dark = "#B3202A", "#7A1018"
    s = D * 1000
    c = Canvas(s, s, 8, dark, 7101)
    _radial(c, s / 2, s / 2, s / 2, "#D8A63A", dark)
    _radial(c, s / 2, s / 2, s * 0.40, mix(red, "#E0B040", 0.35), red)
    for _ in range(160):  # 赤いすじ（軸から外へ）
        a = c.rng.uniform(0, 2 * math.pi)
        r0, r1 = c.rng.uniform(4, 12), c.rng.uniform(s * 0.30, s * 0.5)
        col = mix(dark, red, c.rng.uniform(0, 0.8))
        c.line([(s / 2 + r0 * math.cos(a), s / 2 + r0 * math.sin(a)),
                (s / 2 + r1 * math.cos(a + 0.05), s / 2 + r1 * math.sin(a + 0.05))], col, c.rng.uniform(0.4, 1.4))
    _speckle(c, 260, ["#E9C78A", "#D7A86A", "#F0D9A8"], (0.25, 0.5))  # 果点
    c.ellipse(s / 2 - 6, s / 2 - 6, s / 2 + 6, s / 2 + 6, fill="#5A3A1A")  # くぼみ
    c.ellipse(s / 2 - 3, s / 2 - 3, s / 2 + 3, s / 2 + 3, fill="#3A2410")
    skin = _skin(c, 7101, 0.25)
    label = _label(24, 20, "りんご", "大玉 1個", 198, "#C62828", 7102)
    zs = h_lo + h_up - 0.006  # 軸の付け根（上の山の頂点の少し下）
    # 値札は上の山の肩（中心から 18 mm）に、面に沿うよう傾けて貼る
    r_tag = 0.020
    dz, tilt = _dome_tilt(r_tag, D / 2, h_up)
    parts = [
        _p("Lower", "dome", (D, D, h_lo), (0, 0, h_lo / 2), mix(red, dark, 0.4), "glossy", rotation=(180, 0, 0)),
        _p("Upper", "dome", (D, D, h_up), (0, 0, h_lo + h_up / 2), red, "glossy", faces={"top": 0}),
        _p("Stem", "cylinder", (0.004, 0.004, 0.018), (0.001, 0, zs + 0.009), "#5A3A1A", "matte",
           rotation=(0, 8, 0), collision=False, material="wood"),
        _box("Sticker", (0.024, 0.020, 0.0006), (0, -r_tag, h_lo + dz + 0.0006), WHITE, "matte", {"top": 1},
             rotation=(tilt, 0, 0), collision=False),
    ]
    return _product("apple_single", "りんご 大玉 1個", Dimensions(round(zs + 0.018, 4), D, depth=D), 0.30,
                    "形は一般的なりんご（大玉、直径 85 mm・高さ 80 mm、質量 300 g）。上下 2 つの丸い山で形を作り、"
                    "皮の赤いすじと果点は描いた絵。",
                    ["りんご", "リンゴ", "林檎", "果物", "フルーツ", "ばら売り", "apple", "fruit", "red apple"],
                    parts, [skin, label], red)


# ---------------------------------------------------------------- みかん（ネット入り）


def _mikan_skin(seed: int, d_mm: float) -> np.ndarray:
    c = Canvas(d_mm, d_mm, 8, "#E07A10", seed)
    _radial(c, d_mm / 2, d_mm / 2, d_mm / 2, "#F7A41E", "#D0680C")
    _speckle(c, int(d_mm * d_mm * 1.2), ["#E8830F", "#EE9420", "#D9720C", "#F29A28"], (0.2, 0.4))  # 油胞
    c.ellipse(d_mm / 2 - 4, d_mm / 2 - 4, d_mm / 2 + 4, d_mm / 2 + 4, fill="#7A8A2A")  # へた
    c.ellipse(d_mm / 2 - 1.5, d_mm / 2 - 1.5, d_mm / 2 + 1.5, d_mm / 2 + 1.5, fill="#4E5A18")
    return _skin(c, seed, 0.25)


def mikan_net_bag() -> Product:
    """みかん 6 個を赤いネットに入れたもの。みかんは上下 2 つの丸い山で平たい球にし、5 個を輪に並べて
    1 個を真ん中のすき間に載せる。ネットは外形に沿って左右に巻く細いひも（ひし形の網目）と、底・口の輪。"""
    Dm, h_lo, h_up = 0.060, 0.020, 0.025
    ring = 0.052
    red = "#D32F2F"
    skin = _mikan_skin(7111, Dm * 1000)
    label = _label(46, 30, "みかん", "ネット 6個入", 398, "#E65100", 7112)
    parts = []
    z_mid = 0.022  # 真ん中の 1 個は輪の 5 個のすき間に載る
    spots = [(ring * math.cos(math.radians(90 + 72 * k)), ring * math.sin(math.radians(90 + 72 * k)), 0.0)
             for k in range(5)] + [(0.0, 0.0, z_mid)]
    for k, (x, y, z0) in enumerate(spots):
        parts += [_p(f"Mikan{k}Lower", "dome", (Dm, Dm, h_lo), (x, y, z0 + h_lo / 2), "#D8700E", "glossy",
                     rotation=(180, 0, 0)),
                  _p(f"Mikan{k}Upper", "dome", (Dm, Dm, h_up), (x, y, z0 + h_lo + h_up / 2), "#E07A10", "glossy",
                     rotation=(0, 0, 37 * k), faces={"top": 0})]
    H = z_mid + h_lo + h_up
    R_out = ring + Dm / 2 + 0.0015
    # ネットの外形（半径, 高さ）：底 → 胴 → 肩 → 真ん中のみかん → 口
    hull = [(R_out - 0.010, 0.002), (R_out, h_lo), (R_out - 0.010, h_lo + 0.017), (ring, h_lo + h_up + 0.002),
            (0.030, H - 0.006), (0.010, H + 0.002)]
    n = 10
    for sgn in (1, -1):  # 左巻き・右巻きのひもが交差してひし形の網目になる
        for k in range(n):
            a0 = 2 * math.pi * k / n
            pts = [(r * math.cos(a0 + sgn * 0.26 * i), r * math.sin(a0 + sgn * 0.26 * i), z)
                   for i, (r, z) in enumerate(hull)]
            for i in range(len(pts) - 1):
                c, rot, L = _along(pts[i], pts[i + 1])
                parts.append(_p(f"Net{'LR'[sgn < 0]}{k}_{i}", "box", (0.0016, 0.0016, L + 0.0016), c, red, "matte",
                                rotation=rot, collision=False, material="plastic"))
    parts += [_p("NetRingBottom", "torus", (2 * (R_out - 0.010), 2 * (R_out - 0.010), 0.002), (0, 0, 0.002), red,
                 "matte", collision=False, material="plastic"),
              _p("NetRingWaist", "torus", (2 * R_out, 2 * R_out, 0.002), (0, 0, h_lo), red, "matte", collision=False,
                 material="plastic")]
    # 口の結び目とクリップ・値札（上に寝かせる）
    parts += [_p("NetKnot", "pointed_dome", (0.016, 0.016, 0.012), (0, 0, H + 0.004), red, "matte",
                 collision=False, material="plastic"),
              _box("Clip", (0.020, 0.008, 0.006), (0, 0, H + 0.011), "#F2C230", "plastic", collision=False),
              _box("Tag", (0.046, 0.030, 0.0008), (0, -0.026, H - 0.003), WHITE, "matte", {"top": 1},
                   rotation=(16, 0, 0), collision=False)]
    W = round(2 * R_out, 4)
    return _product("mikan_net_bag", "みかん ネット 6個入", Dimensions(round(H + 0.014, 4), W, depth=W), 0.62,
                    "形は一般的なみかんのネット入り（M 玉 直径 60 mm を 6 個、赤いネットの口をクリップで留め値札を付ける）で、"
                    "寸法・質量は代表値。ネットは外形に沿って巻く細いひもで表し、皮のつぶつぶは描いた絵。",
                    ["みかん", "温州みかん", "ミカン", "果物", "フルーツ", "ネット", "mandarin orange", "mikan",
                     "mandarin oranges in net bag"],
                    parts, [skin, label], "#E07A10")


# ---------------------------------------------------------------- トマト（4 個パック）


def _tomato_skin(seed: int, d_mm: float) -> np.ndarray:
    c = Canvas(d_mm, d_mm, 8, "#B71C1C", seed)
    cx = cy = d_mm / 2
    _radial(c, cx, cy, d_mm / 2, "#E53935", "#A31515")
    for k in range(6):  # 肩の筋（へたから外へ）
        a = k * math.pi / 3 + 0.3
        c.line([(cx, cy), (cx + d_mm * 0.42 * math.cos(a), cy + d_mm * 0.42 * math.sin(a))], "#C62424", 1.6)
    c.ellipse(cx - 18, cy - 9, cx - 6, cy - 3, fill="#F08080")  # つやの映り込み
    for k in range(5):  # へた（星形の緑の葉）
        a = k * 2 * math.pi / 5
        tip = (cx + 13 * math.cos(a), cy + 13 * math.sin(a))
        lft = (cx + 3 * math.cos(a - 0.6), cy + 3 * math.sin(a - 0.6))
        rgt = (cx + 3 * math.cos(a + 0.6), cy + 3 * math.sin(a + 0.6))
        c.polygon([lft, tip, rgt], fill="#3E7B27")
    c.ellipse(cx - 3, cy - 3, cx + 3, cy + 3, fill="#2E5E1C")
    c.ellipse(cx - 1.2, cy - 1.2, cx + 1.2, cy + 1.2, fill="#6B8E23")
    return _skin(c, seed, 0.2)


def tomato_pack_4() -> Product:
    """トマト 4 個を白いトレーに並べ、透明なフィルムで包んだもの。トマトは肩の張った山（bun）にへたを描いた絵。"""
    Dt, Ht = 0.072, 0.056
    pitch = 0.074
    TW, TD, tray_h = 0.160, 0.160, 0.016
    skin = _tomato_skin(7121, Dt * 1000)
    label = _label(54, 34, "トマト", "4個入", 398, "#C62828", 7122)
    parts = [_box("Tray", (TW, TD, tray_h), (0, 0, tray_h / 2), "#F4F4F2", "matte")]
    for k, (i, j) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        x, y = (i - 0.5) * pitch, (j - 0.5) * pitch
        z0 = tray_h - 0.004
        parts += [_p(f"Tomato{k}Lower", "dome", (Dt, Dt, 0.024), (x, y, z0 + 0.012), "#B71C1C", "glossy",
                     rotation=(180, 0, 0), collision=False),
                  _p(f"Tomato{k}Upper", "bun", (Dt, Dt, Ht - 0.024), (x, y, z0 + 0.024 + (Ht - 0.024) / 2), "#C62828",
                     "glossy", rotation=(0, 0, 50 * k), faces={"top": 0}, collision=False)]
    top = tray_h - 0.004 + Ht
    H = top + 0.003
    parts += [_film("Wrap", (TW + 0.006, TD + 0.006, H), (0, 0, H / 2)),
              _box("Sticker", (0.054, 0.034, 0.0006), (0.020, -0.026, top + 0.0005), WHITE, "matte", {"top": 1},
                   collision=False)]
    return _product("tomato_pack_4", "トマト 4個入", Dimensions(round(H, 4), round(TW + 0.006, 4),
                                                             depth=round(TD + 0.006, 4)), 0.68,
                    "形は一般的なトマトのパック（直径 72 mm・高さ 56 mm のトマト 4 個を 160 mm 角の発泡トレーに並べ、"
                    "ラップで包む）で、寸法・質量は代表値。へたと肩の筋は描いた絵。",
                    ["トマト", "とまと", "野菜", "トレーパック", "tomato", "tomatoes", "tomatoes in tray"],
                    parts, [skin, label], "#C62828", material="film")


# ---------------------------------------------------------------- きゅうり・にんじん（袋）


def cucumber_bag_3() -> Product:
    """きゅうり 3 本を透明な袋に入れ、口をテープの値札で留めたもの。きゅうりは両端の丸い回転体を寝かせ、
    いぼは小さな突起（dome）で表す。"""
    L, Dc = 0.210, 0.030
    green, dark = "#3F6B25", "#24451A"
    prof = [[0, 0], [0.55, 0.01], [0.85, 0.04], [0.97, 0.09], [1.0, 0.18], [1.0, 0.80], [0.94, 0.90],
            [0.80, 0.955], [0.50, 0.988], [0, 1]]
    parts = []
    rng = np.random.default_rng(7131)
    z = Dc / 2 + 0.001
    for k, y in enumerate((-0.031, 0.0, 0.031)):
        x = (k - 1) * 0.006
        parts.append(_p(f"Cucumber{k}", "revolve", (Dc, Dc, L), (x, y, z), green, "glossy",
                        rotation=(0, 90, (-2, 1, 3)[k]), profile=prof, collision=False))
        parts.append(_p(f"Cucumber{k}End", "dome", (Dc * 0.5, Dc * 0.5, 0.003), (x - L / 2 + 0.001, y, z),
                        "#C9B85A", "matte", rotation=(0, -90, 0), collision=False))
        for j in range(12):  # いぼ（上面に散らす）
            px = x - L / 2 + 0.03 + rng.uniform(0, L - 0.06)
            a = rng.uniform(-1.2, 1.2)
            parts.append(_p(f"Bump{k}_{j}", "dome", (0.003, 0.003, 0.0016),
                            (px, y + Dc / 2 * math.sin(a), z + Dc / 2 * math.cos(a)), dark, "matte",
                            rotation=(-math.degrees(a), 0, 0), collision=False))
    BW, BD, BH = L + 0.030, 0.112, Dc + 0.016
    tape = _label(50, 30, "きゅうり", "3本入", 198, GREEN_TAG, 7132, keep="野菜室で保存してください")
    parts += [_film("Bag", (BW, BD, BH), (0.003, 0, BH / 2)),
              _box("Tape", (0.050, 0.030, 0.0008), (0.040, -0.010, BH + 0.0004), WHITE, "matte", {"top": 0},
                   collision=False)]
    return _product("cucumber_bag_3", "きゅうり 3本入", Dimensions(round(BH + 0.001, 4), round(BW, 4),
                                                                depth=round(BD, 4)), 0.31,
                    "形は一般的なきゅうりの袋入り（長さ 210 mm・直径 30 mm のきゅうり 3 本を透明な袋に入れ、"
                    "値札のテープを貼る）で、寸法・質量は代表値。きゅうりは寝かせた回転体と小さないぼで表す。",
                    ["きゅうり", "胡瓜", "キュウリ", "野菜", "袋入り", "cucumber", "cucumbers in bag"],
                    parts, [tape], green, material="film")


def carrot_bag_3() -> Product:
    """にんじん 3 本を透明な袋に入れたもの。にんじんは先の細い回転体を寝かせ、肩に葉の付け根を付ける。"""
    L, Dc = 0.175, 0.042
    orange = "#E8711C"
    prof = [[0, 0], [0.12, 0.03], [0.30, 0.15], [0.55, 0.40], [0.80, 0.70], [0.95, 0.88], [1.0, 0.95],
            [0.85, 0.99], [0, 1]]
    parts = []
    for k, (y, x, rz) in enumerate(((-0.044, 0.006, -3), (0.0, -0.008, 2), (0.044, 0.004, -1))):
        z = Dc / 2 + 0.001
        # 回転体の 0 → 1 が先 → 肩。Y 軸 90° で 0 が −X、1 が +X（肩を右に）
        parts.append(_p(f"Carrot{k}", "revolve", (Dc, Dc, L), (x, y, z), orange, "matte",
                        rotation=(0, 90, rz), profile=prof, collision=False))
        parts.append(_p(f"Crown{k}", "cylinder", (0.016, 0.016, 0.006), (x + L / 2 + 0.002, y, z), "#5E7A2A",
                        "matte", rotation=(0, 90, 0), collision=False))
    BW, BD, BH = L + 0.040, 0.145, Dc + 0.016
    tape = _label(50, 30, "にんじん", "3本入", 178, "#E65100", 7142, keep="野菜室で保存してください")
    parts += [_film("Bag", (BW, BD, BH), (0, 0, BH / 2)),
              _box("Tape", (0.050, 0.030, 0.0008), (-0.030, -0.020, BH + 0.0004), WHITE, "matte", {"top": 0},
                   collision=False)]
    return _product("carrot_bag_3", "にんじん 3本入", Dimensions(round(BH + 0.001, 4), round(BW, 4),
                                                              depth=round(BD, 4)), 0.47,
                    "形は一般的なにんじんの袋入り（長さ 175 mm・肩の直径 42 mm のにんじん 3 本を透明な袋に入れ、"
                    "値札のテープを貼る）で、寸法・質量は代表値。にんじんは寝かせた先の細い回転体で表す。",
                    ["にんじん", "人参", "ニンジン", "野菜", "袋入り", "carrot", "carrots in bag"],
                    parts, [tape], orange, material="film")


# ---------------------------------------------------------------- 玉ねぎ（3 個袋）


def _onion_skin(seed: int, d_mm: float) -> np.ndarray:
    c = Canvas(d_mm, d_mm, 8, "#B87A32", seed)
    _radial(c, d_mm / 2, d_mm / 2, d_mm / 2, "#8A5320", "#C98E44")
    for _ in range(90):  # 縦の筋（頂点から外へ）
        a = c.rng.uniform(0, 2 * math.pi)
        r1 = d_mm * c.rng.uniform(0.35, 0.5)
        c.line([(d_mm / 2, d_mm / 2), (d_mm / 2 + r1 * math.cos(a), d_mm / 2 + r1 * math.sin(a))],
               mix("#7A4A1A", "#E0B070", c.rng.random()), c.rng.uniform(0.3, 0.8))
    c.ellipse(d_mm / 2 - 4, d_mm / 2 - 4, d_mm / 2 + 4, d_mm / 2 + 4, fill="#6A4018")
    return _skin(c, seed, 0.5)


def onion_bag_3() -> Product:
    """玉ねぎ 3 個を透明な袋に入れたもの。玉ねぎは下の丸い山と上のとがった山を合わせ、茶色い皮の筋を描く。"""
    Do, h_lo, h_up = 0.080, 0.030, 0.050
    brown = "#B87A32"
    skin = _onion_skin(7151, Do * 1000)
    tape = _label(50, 30, "玉ねぎ", "3個入", 198, "#8D5A1E", 7152, keep="風通しの良い所で保存")
    parts = []
    for k, x in enumerate((-0.084, 0.0, 0.084)):
        y = (0.004, -0.004, 0.003)[k]
        parts += [_p(f"Onion{k}Lower", "bun", (Do, Do, h_lo), (x, y, h_lo / 2), "#A86A28", "plastic",
                     rotation=(180, 0, 0), collision=False),
                  _p(f"Onion{k}Upper", "pointed_dome", (Do, Do, h_up), (x, y, h_lo + h_up / 2), brown, "plastic",
                     rotation=(0, 0, 60 * k), faces={"top": 0}, collision=False),
                  _p(f"Onion{k}Tip", "cylinder", (0.006, 0.006, 0.012), (x, y, h_lo + h_up + 0.004), "#8A5A24",
                     "matte", rotation=(0, 12, 40 * k), collision=False)]
    H = h_lo + h_up + 0.014
    BW, BD = 0.255, Do + 0.012
    parts += [_film("Bag", (BW, BD, H), (0, 0, H / 2)),
              _box("Tape", (0.050, 0.030, 0.0008), (0.0, -0.022, H - 0.006), WHITE, "matte", {"top": 1},
                   rotation=(22, 0, 0), collision=False)]
    return _product("onion_bag_3", "玉ねぎ 3個入", Dimensions(round(H + 0.002, 4), BW, depth=round(BD, 4)), 0.62,
                    "形は一般的な玉ねぎの袋入り（直径 80 mm の玉ねぎ 3 個を一列に透明な袋へ入れ、値札のテープを貼る）で、"
                    "寸法・質量は代表値。皮の筋は描いた絵。",
                    ["玉ねぎ", "たまねぎ", "タマネギ", "野菜", "袋入り", "onion", "onions in bag"],
                    parts, [skin, tape], brown, material="film")


# ---------------------------------------------------------------- キャベツ・レタス（1 玉）


def _leafy(seed: int, d_mm: float, center: str, edge: str, vein: str, n_veins: int) -> np.ndarray:
    """上から見た葉物の玉（外葉の重なりと太い葉脈）。"""
    c = Canvas(d_mm, d_mm, 6, edge, seed)
    _radial(c, d_mm / 2, d_mm / 2, d_mm / 2, center, edge)
    cx = cy = d_mm / 2
    for k in range(7):  # 外葉の縁（中心をずらした弧）
        a = k * 2 * math.pi / 7 + c.rng.uniform(-0.2, 0.2)
        r = d_mm * c.rng.uniform(0.28, 0.40)
        ox, oy = cx + d_mm * 0.16 * math.cos(a), cy + d_mm * 0.16 * math.sin(a)
        c.d.arc(c.box(ox - r, oy - r, ox + r, oy + r), math.degrees(a) - 70, math.degrees(a) + 70,
                fill=mix(edge, "#FFFFFF", 0.25), width=max(1, round(1.2 * c.s)))
    for _ in range(n_veins):  # 太い葉脈と細い枝
        a = c.rng.uniform(0, 2 * math.pi)
        r0, r1 = d_mm * c.rng.uniform(0.04, 0.12), d_mm * c.rng.uniform(0.38, 0.5)
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a + 0.12), cy + r1 * math.sin(a + 0.12)
        c.line([(x0, y0), (x1, y1)], vein, c.rng.uniform(1.0, 2.2))
        for j in range(4):
            t = 0.25 + j * 0.18
            bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            side = 1 if j % 2 else -1
            c.line([(bx, by), (bx + (y1 - y0) * 0.15 * side + (x1 - x0) * 0.1,
                               by - (x1 - x0) * 0.15 * side + (y1 - y0) * 0.1)], vein, 0.6)
    _speckle(c, int(d_mm * 2), [mix(edge, "#FFFFFF", 0.15), mix(edge, "#000000", 0.08)], (0.6, 1.6))
    return _skin(c, seed, 0.6)


def _dome_tilt(r: float, R: float, h: float) -> tuple[float, float]:
    """dome（(r/R)^2 + (z/h)^2 = 1）の半径 r での高さと面の傾き [度]。"""
    q = r / R
    z = h * math.sqrt(max(1 - q * q, 1e-9))
    return z, math.degrees(math.atan(h / R * q / math.sqrt(max(1 - q * q, 1e-9))))


def cabbage_whole() -> Product:
    """キャベツ 1 玉（ばら売り）。下の浅い山と上の丸い山を合わせ、上に外葉と白い葉脈を描く。
    底に切り口（芯）、肩に値札シール。"""
    D, h_lo, h_up = 0.200, 0.075, 0.085
    pale = "#A9CB76"
    skin = _leafy(7161, D * 1000, "#D9EAB4", "#8DB85A", "#EEF4D8", 22)
    label = _label(40, 28, "キャベツ", "1玉", 228, GREEN_TAG, 7162)
    r_tag = 0.050
    dz, tilt = _dome_tilt(r_tag, D / 2, h_up)
    parts = [_p("Lower", "dome", (D, D, h_lo), (0, 0, h_lo / 2), "#9CC46A", "plastic", rotation=(180, 0, 0)),
             _p("Upper", "dome", (D, D, h_up), (0, 0, h_lo + h_up / 2), pale, "plastic", faces={"top": 0}),
             _p("Core", "cylinder", (0.032, 0.032, 0.002), (0, 0, 0.0005), "#E8E4C8", "matte", collision=False),
             _box("Sticker", (0.040, 0.028, 0.0006), (0, -r_tag, h_lo + dz + 0.0006), WHITE, "matte", {"top": 1},
                  rotation=(tilt, 0, 0), collision=False)]
    return _product("cabbage_whole", "キャベツ 1玉", Dimensions(h_lo + h_up, D, depth=D), 1.2,
                    "形は一般的なキャベツ（直径 200 mm・高さ 160 mm、質量 1.2 kg）。下の浅い山と上の丸い山で形を作り、"
                    "外葉と葉脈は描いた絵。",
                    ["キャベツ", "きゃべつ", "甘藍", "野菜", "葉物", "ばら売り", "cabbage", "whole cabbage"],
                    parts, [skin, label], pale)


def lettuce_whole() -> Product:
    """レタス 1 玉を透明なフィルムで包み、肩に値札テープを貼ったもの。玉は下の山と上の丸い山。"""
    D, h_lo, h_up = 0.150, 0.060, 0.070
    green = "#9CCB5E"
    skin = _leafy(7171, D * 1000, "#E4F0C4", "#86BF4A", "#F2F8E2", 16)
    tape = _label(44, 28, "レタス", "1玉", 198, GREEN_TAG, 7172, keep="野菜室で保存してください")
    H = h_lo + h_up
    Df, hf = D + 0.006, h_up + 0.003
    r_tag = 0.040
    dz, tilt = _dome_tilt(r_tag, Df / 2, hf)
    parts = [_p("Lower", "dome", (D, D, h_lo), (0, 0, h_lo / 2), "#8EC255", "plastic", rotation=(180, 0, 0),
                collision=False),
             _p("Upper", "dome", (D, D, h_up), (0, 0, h_lo + h_up / 2), green, "plastic", faces={"top": 0},
                collision=False),
             _p("WrapLower", "dome", (Df, Df, h_lo + 0.002), (0, 0, (h_lo + 0.002) / 2), CLEAR, "glass",
                rotation=(180, 0, 0), material="film", thin_walled=True),
             _p("WrapUpper", "dome", (Df, Df, hf), (0, 0, h_lo + hf / 2), CLEAR, "glass", material="film",
                thin_walled=True),
             _p("Twist", "pointed_dome", (0.022, 0.022, 0.012), (0, 0, h_lo + hf + 0.005), CLEAR, "glass",
                collision=False, material="film", thin_walled=True),
             _box("Tape", (0.044, 0.028, 0.0008), (0, -r_tag, h_lo + dz + 0.0006), WHITE, "matte", {"top": 1},
                  rotation=(tilt, 0, 0), collision=False)]
    return _product("lettuce_whole", "レタス 1玉", Dimensions(round(h_lo + hf + 0.011, 4), round(Df, 4),
                                                           depth=round(Df, 4)), 0.45,
                    "形は一般的なレタス（直径 150 mm・高さ 130 mm、質量 450 g をフィルムで包み、値札のテープを貼る）。"
                    "玉は 2 つの山で形を作り、葉と葉脈は描いた絵。",
                    ["レタス", "玉レタス", "野菜", "葉物", "フィルム包装", "lettuce", "iceberg lettuce",
                     "lettuce in film wrap"],
                    parts, [skin, tape], green, material="film")


# ---------------------------------------------------------------- バナナ（1 房）


def banana_bunch() -> Product:
    """バナナ 1 房（5 本）。1 本を 5 つの回転体の節でつなぎ、軸（クラウン）から先へ反りながら扇状に広げる。
    先は茶色、真ん中の 1 本に値札シール。"""
    yellow, tip_c, crown_c = "#F4C21C", "#4A3A20", "#7A8A3A"
    Rf = 0.017
    n_seg = 5
    seg_prof = [[0.88, 0], [0.97, 0.1], [1.0, 0.25], [1.0, 0.75], [0.97, 0.9], [0.88, 1]]
    tip_prof = [[1.0, 0], [0.9, 0.35], [0.55, 0.75], [0.25, 0.95], [0, 1]]
    crown = (-0.112, 0.0, Rf + 0.035)
    parts: list[Part] = []
    mid = None
    for j in range(5):
        off = j - 2
        lift = 0.010 * (2 - abs(off))  # 真ん中の指ほど上に重なる
        pts = []
        for i in range(n_seg + 1):
            t = i / n_seg
            pts.append((-0.085 + 0.190 * t, off * (0.010 + 0.022 * t),
                        Rf + lift + 0.15 * (t - 0.58) ** 2 - 0.003 * abs(off)))
        for i in range(n_seg):
            c, rot, L = _along(pts[i], pts[i + 1])
            r_scale = 1.0 - 0.18 * (i / (n_seg - 1)) ** 2
            parts.append(_p(f"Finger{j}_{i}", "revolve", (2 * Rf * r_scale, 2 * Rf * r_scale, L + 0.008), c,
                            yellow, "matte", rotation=rot, profile=seg_prof))
        d = np.subtract(pts[-1], pts[-2])
        d /= np.linalg.norm(d)
        c, rot, L = _along(pts[-1], np.add(pts[-1], d * 0.018))
        parts.append(_p(f"Tip{j}", "revolve", (0.018, 0.018, L), c, tip_c, "matte", rotation=rot, profile=tip_prof,
                        collision=False))
        c, rot, L = _along(crown, pts[0])
        parts.append(_p(f"Stalk{j}", "cylinder", (0.012, 0.012, L), c, "#B9A83C", "matte", rotation=rot,
                        collision=False))
        if j == 2:
            mid = pts
    parts.append(_p("Crown", "cylinder", (0.030, 0.034, 0.030), crown, crown_c, "matte", rotation=(0, 90, 0)))
    parts.append(_p("CrownCut", "cylinder", (0.026, 0.030, 0.002), (crown[0] - 0.0155, 0, crown[2]), "#D8C89A",
                    "matte", rotation=(0, 90, 0), collision=False))
    label = _label(26, 18, "バナナ", "1房", 158, "#F9A825", 7182)
    c, rot, _ = _along(mid[2], mid[3])
    parts.append(_box("Sticker", (0.026, 0.018, 0.0006), (c[0], c[1], c[2] + Rf + 0.0004), WHITE, "matte",
                      {"top": 0}, rotation=(0, rot[1] - 90, 0), collision=False))
    return _product("banana_bunch", "バナナ 1房 5本", Dimensions(0.105, 0.26, depth=0.16), 0.90,
                    "形は一般的なバナナの房（長さ約 200 mm・太さ 34 mm の 5 本を軸から扇状に広げ、寝かせて置く）で、"
                    "寸法・質量は代表値。1 本は回転体の節をつないだ反った形で表す。",
                    ["バナナ", "ばなな", "果物", "フルーツ", "房", "banana", "bananas", "banana bunch"],
                    parts, [label], yellow)


# ---------------------------------------------------------------- いちご（1 パック）


def strawberry_pack() -> Product:
    """いちご 1 パック（平たい透明なパックに 12 粒を寝かせて並べ、フィルムのふたと値札）。
    粒はとがった山（pointed_dome）を寝かせ、写真のいちごの皮を貼る。へたは緑の小さな山。

    写真: photos.json の strawberry（Wikimedia Commons、CC0）
    """
    W, D, H = 0.160, 0.115, 0.050
    red = "#C8102E"
    skin = _food_photo("strawberry", 40, 40, (0.38, 0.35, 0.62, 0.65), 7191, 0.2)
    label = _label(60, 34, "いちご", "1パック（270g）", 598, "#C62828", 7192,
                   photo=("strawberry", (0.25, 0.10, 0.70, 0.75)), keep="要冷蔵  お早めに")
    # 透明なパック（ふたのフィルムまで含めた 1 つの閉じた箱）
    parts = [_box("Tray", (W, D, H), (0, 0, H / 2), CLEAR, "glass", thin_walled=True),
             _box("TrayFloor", (W - 0.006, D - 0.006, 0.002), (0, 0, 0.001), WHITE, "matte", collision=False)]
    Lb, Db = 0.040, 0.032
    k = 0
    for row in range(3):
        for col in range(4):
            x = -W / 2 + 0.022 + col * 0.038 + (0.006 if row % 2 else 0)
            y = -D / 2 + 0.020 + row * 0.036
            yaw = (90 if row % 2 else -90) + (-8, 6, -4, 9)[col]
            z = Db / 2 + 0.002
            a = math.radians(yaw)
            # 寝かせた粒（とがった山の先を横へ）。Y 軸 90° で先が +X、それを yaw だけ回す
            parts.append(_p(f"Berry{k}", "pointed_dome", (Db, Db, Lb), (x, y, z), red, "glossy",
                            rotation=(0, 90, yaw), faces={"top": 0}, collision=False))
            parts.append(_p(f"Calyx{k}", "dome", (Db * 0.8, Db * 0.8, 0.004),
                            (x - Lb / 2 * math.cos(a), y - Lb / 2 * math.sin(a), z), "#4C8A2A", "matte",
                            rotation=(0, -90, yaw), collision=False))
            k += 1
    parts.append(_box("Label", (0.060, 0.034, 0.0008), (0.040, -0.034, H + 0.0004), WHITE, "matte", {"top": 1},
                      collision=False))
    return _product("strawberry_pack", "いちご 1パック", Dimensions(round(H + 0.001, 4), W, depth=D), 0.31,
                    "形は一般的ないちごの平パック（160×115 mm・高さ 50 mm の透明なパックに 12 粒を並べ、"
                    "フィルムのふたに値札を貼る、内容量 270 g）で、寸法・質量は代表値。粒は寝かせたとがった山に写真の皮を貼る。",
                    ["いちご", "イチゴ", "苺", "果物", "フルーツ", "パック", "strawberry", "strawberries",
                     "strawberry pack"],
                    parts, [skin, label], red, material="plastic", photos=["strawberry"])


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    apple_single, mikan_net_bag, tomato_pack_4, cucumber_bag_3, cabbage_whole, onion_bag_3, banana_bunch,
    lettuce_whole, carrot_bag_3, strawberry_pack)}
