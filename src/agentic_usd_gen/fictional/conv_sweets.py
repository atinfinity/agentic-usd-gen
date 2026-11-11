"""架空の商品のデザイン: コンビニのチルドスイーツ。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import Product, label_canvas, revolve, top_canvas
from .food_fresh_snack import _back_panel, _pouch
from .paint import Canvas, edge_shade, finish, mix
from .products import INK, _box, _face, back_info, seal_crimp

CLEAR = "#F2F6F8"
WHITE = "#FFFFFF"
SPONGE, SPONGE_DARK, CREAM = "#F1CF7A", "#C98B3E", "#FFFBF0"


def _mound(name: str, R: float, h: float, z0: float, xy, color: str, finish_: str = "matte",
           pointed: bool = False) -> list[Part]:
    """底が平らな丸い山（まんじゅう・クリーム・いちご）。pointed=True は先のとがった山。"""
    return [Part(name, "pointed_dome" if pointed else "dome", [2 * R, 2 * R, h], [xy[0], xy[1], z0 + h / 2],
                 color=color, finish=finish_, collision=False, material="food")]


def _dome_r(R: float, h: float, z: float) -> float:
    """dome 部品の高さ z での半径。"""
    return R * math.sqrt(max(1 - (z / h) ** 2, 0.0))


def _sticker(w: float, h: float, title: str, sub: str, accent: str, seed: int, kcal: int, price: int):
    """ケース・フタに貼る商品名シール（名前・熱量・価格・ダミーのバーコード）。"""
    c = Canvas(w, h, 14, WHITE, seed)
    c.rect(0, 0, w, h * 0.42, fill=accent)
    c.text(w / 2, h * 0.15, sub, h * 0.11, mix(accent, WHITE, 0.75), 800, max_w=w - 6)
    c.text(w / 2, h * 0.31, title, h * 0.17, WHITE, 900, max_w=w - 6)
    c.text(4, h * 0.56, f"熱量 {kcal}kcal", h * 0.09, INK, 700, anchor="lm")
    c.text(4, h * 0.70, "要冷蔵 10℃以下", h * 0.08, INK, 700, anchor="lm")
    c.text(w - 4, h * 0.62, f"{price}円", h * 0.16, accent, 900, anchor="rm")
    c.barcode(w * 0.52, h * 0.75, w * 0.44, h * 0.22)
    c.text(4, h * 0.86, "消費期限 26.10.19", h * 0.075, INK, 700, anchor="lm", max_w=w * 0.46)
    return _face(c.array(), "paper", seed, 0.5)


def _band(w: float, h: float, text: str, accent: str, seed: int):
    """ケースの正面の下に貼る細い帯シール。"""
    c = Canvas(w, h, 14, accent, seed)
    c.gradient(0, 0, w, h, mix(accent, WHITE, 0.15), accent)
    c.rect(1.2, 1.2, w - 1.2, h - 1.2, outline=mix(accent, "#FFE9A8", 0.6), width=0.3, radius=1)
    c.text(w / 2, h / 2, text, h * 0.45, WHITE, 900, max_w=w - 6)
    return _face(c.array(), "paper", seed, 0.5)


def _sponge(c: Canvas, x0, y0, x1, y1, top: str = SPONGE, bottom: str | None = None):
    """スポンジ生地の断面（気泡の点つき）。"""
    c.gradient(x0, y0, x1, y1, top, bottom or mix(top, SPONGE_DARK, 0.25))
    n = int((x1 - x0) * (y1 - y0) / 4)
    for _ in range(n):
        x, y = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        r = c.rng.uniform(0.2, 0.55)
        c.ellipse(x - r, y - r * 0.8, x + r, y + r * 0.8, fill=mix(top, SPONGE_DARK, c.rng.uniform(0.2, 0.45)))


def _bumpy(c: Canvas, x0, y0, x1, y1, base: str, light: str, n: int, size=(0.4, 1.0)):
    c.rect(x0, y0, x1, y1, fill=base)
    for _ in range(n):
        x, y = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        r = c.rng.uniform(*size)
        c.ellipse(x - r, y - r, x + r, y + r, fill=mix(base, light, c.rng.uniform(0.2, 0.7)))


# ---------------------------------------------------------------- ケーキ（透明なケース）


def strawberry_shortcake_case() -> Product:
    """白い台の上にショートケーキ 1 個（箱、断面の画像）、上にクリームといちご（部品）。透明な角ケースと商品名シール。"""
    red, pink = "#C8102E", "#E8506A"
    CW, CH = 70.0, 52.0
    s = 12

    def side(seed: int) -> Canvas:
        c = Canvas(CW, CH, s, CREAM, seed)
        c.gradient(0, 0, CW, 5, "#FFFFFF", "#FBF3E2")  # 上のクリーム
        y = 5.0
        for k in range(3):
            _sponge(c, 0, y, CW, y + 11.5)
            y += 11.5
            if k < 2:
                c.rect(0, y, CW, y + 5, fill=CREAM)
                for x in range(4, int(CW) - 6, 11):  # 断面のいちご
                    c.ellipse(x, y + 0.6, x + 8.5, y + 4.6, fill=red)
                    c.ellipse(x + 1.5, y + 1.6, x + 7.0, y + 3.6, fill=pink)
                    c.line([(x + 4.25, y + 1.2), (x + 4.25, y + 4.0)], "#FCE4E8", 0.4)
                y += 5
        c.rect(0, CH - 1.5, CW, CH, fill=SPONGE_DARK)
        return c

    imgs = [_face(side(2901 + i).array(), "matte", 2901 + i, 0.4, 4) for i in range(4)]
    t = Canvas(CW, CW, s, CREAM, 2905)
    t.gradient(0, 0, CW, CW, "#FFFFFF", "#F7EEDC")
    for _ in range(140):  # クリームの波
        x, y = t.rng.uniform(2, CW - 2), t.rng.uniform(2, CW - 2)
        t.ellipse(x - 2.5, y - 0.6, x + 2.5, y + 0.6, fill="#F2E6CF")
    imgs.append(_face(t.array(), "matte", 2905, 0.4, 4))
    imgs.append(_sticker(60, 34, "いちごのショートケーキ", "STRAWBERRY SHORTCAKE", red, 2906, 312, 398))
    imgs.append(_band(64, 10, "とろける生クリーム", red, 2907))

    bh, ch = 0.004, CH / 1000
    cake = _box("Cake", (CW / 1000, CW / 1000, ch), (0, 0, bh + ch / 2), CREAM, "matte",
                {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4}, collision=False)
    cake.material = "food"
    top = bh + ch
    parts = [_box("Base", (0.086, 0.086, bh), (0, 0, bh / 2), "#F4EFE4", "plastic"), cake]
    for i, (x, y) in enumerate([(-0.024, -0.024), (0.024, -0.024), (-0.024, 0.024), (0.024, 0.024)]):
        parts += _mound(f"Rosette{i}", 0.0075, 0.009, top, (x, y), "#FFFDF6", pointed=True)
    parts += _mound("CenterCream", 0.016, 0.006, top, (0, 0), "#FFFDF6")
    parts += _mound("Strawberry", 0.0115, 0.024, top + 0.005, (0, 0), red, "glossy", pointed=True)
    parts.append(Part("Calyx", "cylinder", [0.014, 0.014, 0.0015], [0, 0, top + 0.0055], color="#3E8E2E",
                      finish="matte", collision=False, material="food"))
    case_h = 0.080
    parts += [_box("Case", (0.084, 0.084, case_h), (0, 0, bh + case_h / 2), CLEAR, "glass", thin_walled=True),
              _box("Sticker", (0.060, 0.034, 0.0006), (0, 0, bh + case_h + 0.0003), WHITE, "matte", {"top": 5},
                   collision=False),
              _box("Band", (0.064, 0.0006, 0.010), (0, -0.042 - 0.0003, bh + 0.008), red, "matte", {"front": 6},
                   collision=False)]
    return Product(slug="strawberry_shortcake_case", name="いちごのショートケーキ", shape_class="assembly",
                   category="food", dims=Dimensions(bh + case_h + 0.0006, 0.086, depth=0.086), mass_kg=0.12,
                   material="plastic",
                   description="形は一般的なコンビニのカットケーキ（白い台 86 mm 角に 70 mm 角・高さ 52 mm のショートケーキ、"
                               "高さ 80 mm の透明な角ケースと商品名シール）で、寸法・質量は代表値。"
                               "ケーキの断面は画像、上のクリームといちごは簡単な形で表す。",
                   tags=["ショートケーキ", "いちご", "ケーキ", "スイーツ", "洋生菓子", "要冷蔵", "shortcake",
                         "strawberry", "cake", "dessert"],
                   colors=Colors(label_base=CREAM), images=imgs, parts=parts)


def roll_cake_pack() -> Product:
    """白いトレーにロールケーキ 2 切れを立てて並べ（クリームの渦巻きは細い板を渦に沿って並べる）、透明なフタと商品名シール。"""
    brown, accent = "#9C5A22", "#8A5A2B"
    tray_h, d, th = 0.006, 0.062, 0.028
    imgs = [_sticker(62, 34, "ふんわりロールケーキ", "ROLL CAKE  2切れ入", accent, 2911, 268, 298),
            _band(70, 10, "北海道産生クリーム使用", accent, 2912)]
    parts = [_box("Tray", (0.130, 0.072, tray_h), (0, 0, tray_h / 2), "#F6F3EC", "plastic")]
    # 切り口の絵（焼き色の皮・スポンジ・クリームの渦巻き）。円柱の両端に貼る
    D = d * 1000
    c = Canvas(D, D, 16, "#F6F3EC", 2913)
    c.ellipse(0, 0, D, D, fill=brown)
    _sponge(c, 0, 0, D, D)
    c.ellipse(-1, -1, D + 1, D + 1, outline=brown, width=2.6)
    c.ellipse(0, 0, D, D, outline=mix(brown, "#3A1E08", 0.3), width=0.8)
    r0, r1, turns = 1.5, D / 2 - 4.5, 2.4
    pts = []
    for i in range(400):
        t = i / 399
        a = t * turns * 2 * math.pi
        rr = r0 + (r1 - r0) * t
        pts.append((D / 2 + rr * math.cos(a), D / 2 - rr * math.sin(a)))
    c.line(pts, mix(CREAM, SPONGE, 0.15), 4.4)
    c.line(pts, CREAM, 3.4)
    c.ellipse(D / 2 - 2.6, D / 2 - 2.6, D / 2 + 2.6, D / 2 + 2.6, fill=CREAM)
    imgs.append(_face(c.array(), "matte", 2913, 0.4, 4))
    for k, x in enumerate((-0.032, 0.032)):
        parts.append(Part(f"Slice{k}", "cylinder", [d, d, th], [x, 0, tray_h + d / 2], [90, 0, 0], color=brown,
                          finish="matte", faces={"top": 2, "bottom": 2}, material="food"))
    lid_h = 0.066
    parts += [_box("Lid", (0.134, 0.076, lid_h), (0, 0, 0.004 + lid_h / 2), CLEAR, "glass", thin_walled=True),
              _box("Sticker", (0.062, 0.034, 0.0006), (0, 0, 0.004 + lid_h + 0.0003), WHITE, "matte", {"top": 0},
                   collision=False),
              _box("Band", (0.070, 0.0006, 0.010), (0, -0.038 - 0.0003, 0.011), accent, "matte", {"front": 1},
                   collision=False)]
    return Product(slug="roll_cake_pack", name="ふんわりロールケーキ 2切れ入", shape_class="assembly", category="food",
                   dims=Dimensions(0.004 + lid_h + 0.0006, 0.134, depth=0.0766), mass_kg=0.13, material="plastic",
                   description="形は一般的なコンビニのカットロールケーキ（白いトレー 130×72 mm に直径 62 mm・厚さ 28 mm の 2 切れを"
                               "立てて並べ、高さ 66 mm の透明なフタと商品名シール）で、寸法・質量は代表値。"
                               "クリームの渦巻きは細い板を並べて表す。",
                   tags=["ロールケーキ", "ケーキ", "スイーツ", "洋生菓子", "生クリーム", "要冷蔵", "roll cake",
                         "swiss roll", "dessert"],
                   colors=Colors(label_base=CREAM), images=imgs, parts=parts)


# ---------------------------------------------------------------- カップスイーツ


def mont_blanc_cup() -> Product:
    """透明なカップ（回転体）に層が透け、上に透明なドームのフタ（部品）。中に栗のクリームの山と栗（部品）。"""
    form = forms.paper_cup(0.048, 0.090, 0.068, lid_h=0.002, lid_overhang=0.0015, rim_h=0.003,
                           label_margin=(0.001, 0.001))
    marron, chestnut, brown = "#B07A45", "#D9A441", "#5B3416"
    c = label_canvas(form, CREAM, seed=2921)
    W, H = c.w_mm, c.h_mm
    _bumpy(c, 0, 0, W, 13, marron, "#E2B98A", 900, (0.3, 0.8))  # 上の栗のクリーム
    c.rect(0, 13, W, 22, fill=CREAM)  # ホイップ
    for x in range(0, int(W), 14):  # 刻んだ渋皮栗
        c.ellipse(x + 3, 16, x + 9, 20.5, fill=chestnut)
    _sponge(c, 0, 22, W, H - 3, "#D9A86A", "#B98048")  # スポンジ
    c.rect(0, H - 3, W, H, fill=mix(marron, "#000000", 0.2))
    fx = 0.75 * W
    c.rect(fx - 26, 9, fx + 26, H - 6, fill=WHITE, radius=3, outline=brown, width=0.4)
    c.rect(fx - 26, 9, fx + 26, 17, fill=brown, radius=3)
    c.text(fx, 13, "渋皮栗入り", 4.0, "#F3D9A8", 800)
    c.text(fx, 24.5, "栗のモンブラン", 6.4, brown, 900, max_w=48)
    c.text(fx, 32, "MONT BLANC", 2.8, marron, 800, spacing=0.6)
    c.text(fx, 37.5, "要冷蔵 10℃以下", 2.2, INK, 700)
    bx = 0.25 * W
    c.rect(bx - 30, 6, bx + 30, H - 4, fill=WHITE, radius=2)
    back_info(c, bx - 28, 7.5, bx + 28, [
        ("名称", "洋生菓子"), ("原材料名", "栗ペースト、乳等を主要原料とする食品、砂糖、小麦粉、卵、渋皮栗甘露煮／乳化剤"),
        ("内容量", "1個"), ("消費期限", "フタに記載")], 1.9)
    label = edge_shade(finish(c.array(), "plastic", 2921, 0.6), 4, 0.06)

    t = top_canvas(form, marron, seed=2922)
    d = t.w_mm
    t.ellipse(0.4, 0.4, d - 0.4, d - 0.4, fill=CREAM)
    t.ellipse(4, 4, d - 4, d - 4, fill=marron)
    for k in range(10):  # 絞り出したクリームの筋
        r = (d / 2 - 5) * (1 - k / 11)
        t.ellipse(d / 2 - r, d / 2 - r, d / 2 + r, d / 2 + r, outline=mix(marron, "#E2B98A", 0.35 + 0.04 * k),
                  width=0.7)
    top = finish(t.array(), "plastic", 2922, 0.5)
    sticker = _sticker(56, 32, "栗のモンブラン", "MONT BLANC", brown, 2923, 356, 368)

    r = revolve(form, label=label, top=top, body_fill="#CDA77A")
    r["images"].append(sticker)
    Hm = form.height
    dome_h = 0.050
    parts = _mound("Marron", 0.033, 0.034, Hm, (0, 0), marron)
    for k in range(6):  # 山に巻いた筋（少し明るい細い輪）
        z = 0.004 + k * 0.0048
        rr = _dome_r(0.033, 0.034, z) + 0.0006
        parts.append(Part(f"Strand{k}", "cylinder", [2 * rr, 2 * rr, 0.0012], [0, 0, Hm + z], color="#C99560",
                          finish="matte", collision=False, material="food"))
    parts += _mound("Chestnut", 0.0105, 0.013, Hm + 0.031, (0, 0), chestnut, "glossy")
    parts += [Part("Dome", "cylinder", [0.092, 0.092, dome_h], [0, 0, Hm - 0.001 + dome_h / 2], color=CLEAR,
                   finish="glass", thin_walled=True),
              _box("Sticker", (0.056, 0.032, 0.0006), (0, -0.012, Hm - 0.001 + dome_h + 0.0003), WHITE, "matte",
                   {"top": 3}, collision=False)]
    return Product(slug="mont_blanc_cup", name="栗のモンブラン", category="food", mass_kg=0.14, material="plastic",
                   description="形は一般的なコンビニのカップ入りモンブラン（透明なカップ 上端径 90 mm・高さ 48 mm に、"
                               "高さ 50 mm の透明なドームのフタと商品名シール）で、寸法・質量は代表値。"
                               "栗のクリームの山と栗は簡単な形で表す。",
                   tags=["モンブラン", "栗", "マロン", "ケーキ", "スイーツ", "洋生菓子", "要冷蔵", "mont blanc", "chestnut",
                         "dessert"],
                   colors=Colors(cap=CLEAR, label_base=CREAM), parts=parts, **r)


def tiramisu_cup() -> Product:
    """透明なカップ（回転体）。ココア・マスカルポーネ・コーヒーのスポンジの層が透け、透明なフタごしにココアが見える。"""
    form = forms.paper_cup(0.056, 0.086, 0.070, lid_h=0.0025, lid_overhang=0.002, rim_h=0.004,
                           label_margin=(0.001, 0.001))
    cocoa, cream, brown = "#5A3520", "#FBF1DD", "#3B2314"
    c = label_canvas(form, cream, seed=2931)
    W, H = c.w_mm, c.h_mm
    c.rect(0, 0, W, 3, fill=mix(cream, WHITE, 0.5))  # 上の空き
    _bumpy(c, 0, 3, W, 7, cocoa, "#8A5A3A", 500, (0.2, 0.5))
    c.gradient(0, 7, W, 22, "#FFF8EA", "#F6E8CC")  # マスカルポーネ
    _sponge(c, 0, 22, W, 30, "#8B5A33", "#6A3F22")  # コーヒーをしみこませたスポンジ
    c.gradient(0, 30, W, 42, "#FFF8EA", "#F3E3C2")
    _sponge(c, 0, 42, W, H, "#8B5A33", "#5E371C")
    fx = 0.75 * W
    c.rect(fx - 25, 11, fx + 25, 38, fill=brown, radius=3)
    c.rect(fx - 23.5, 12.5, fx + 23.5, 36.5, outline="#C9A46A", width=0.4, radius=2)
    c.text(fx, 18, "マスカルポーネ", 3.6, "#E9CF9C", 800)
    c.text(fx, 26, "ティラミス", 7.0, WHITE, 900, max_w=44)
    c.text(fx, 33, "TIRAMISU", 2.8, "#C9A46A", 800, spacing=0.8)
    bx = 0.25 * W
    c.rect(bx - 30, 9, bx + 30, H - 3, fill=WHITE, radius=2)
    back_info(c, bx - 28, 10.5, bx + 28, [
        ("名称", "洋生菓子"), ("原材料名", "マスカルポーネチーズ、乳等を主要原料とする食品、砂糖、卵、小麦粉、コーヒー、ココアパウダー"),
        ("内容量", "1個"), ("消費期限", "フタに記載")], 1.9)
    label = edge_shade(finish(c.array(), "plastic", 2931, 0.6), 4, 0.06)

    t = top_canvas(form, cocoa, seed=2932)
    d = t.w_mm
    t.ellipse(0.4, 0.4, d - 0.4, d - 0.4, fill=mix(cocoa, WHITE, 0.25))
    t.ellipse(2.5, 2.5, d - 2.5, d - 2.5, fill=cocoa)
    for _ in range(1600):  # ココアパウダー
        x, y = t.rng.uniform(4, d - 4), t.rng.uniform(4, d - 4)
        if (x - d / 2) ** 2 + (y - d / 2) ** 2 < (d / 2 - 4) ** 2:
            rr = t.rng.uniform(0.2, 0.6)
            t.ellipse(x - rr, y - rr, x + rr, y + rr, fill=mix(cocoa, "#9A6A44", t.rng.uniform(0.1, 0.6)))
    t.rect(d * 0.22, d * 0.36, d * 0.78, d * 0.64, fill=WHITE, radius=2.5, outline=brown, width=0.4)
    t.text(d / 2, d * 0.43, "ティラミス", 7.0, brown, 900)
    t.text(d / 2, d * 0.52, "熱量 298kcal  要冷蔵", 2.6, INK, 700)
    t.text(d / 2, d * 0.585, "消費期限 26.10.19", 2.6, INK, 700)
    top = finish(t.array(), "film", 2932, 0.5)
    return Product(slug="tiramisu_cup", name="マスカルポーネのティラミス", category="food", mass_kg=0.12,
                   material="plastic",
                   description="形は一般的なコンビニのカップ入りティラミス（透明なカップ 上端径 86 mm・高さ 56 mm、"
                               "透明なフタに商品名を印刷）で、寸法・質量は代表値。",
                   tags=["ティラミス", "マスカルポーネ", "ココア", "スイーツ", "洋生菓子", "カップデザート", "要冷蔵",
                         "tiramisu", "dessert"],
                   colors=Colors(cap=CLEAR, label_base=cream), **revolve(form, label=label, top=top, body_fill="#8B5A33"))


# ---------------------------------------------------------------- 袋入り


def _clear_bag(L: float, Wd: float, seed: int, tint: str) -> Canvas:
    """透明に近い袋の地（左右がシール）。"""
    c = Canvas(L, Wd, 8, "#F7F7F2", seed=seed)
    c.gradient(0, 0, L, Wd, "#FBFBF7", mix("#ECEFE9", tint, 0.15))
    seal_crimp(c, 0, 0, 10, Wd, "#E2E6DE", 1.3, vertical=True)
    seal_crimp(c, L - 10, 0, L, Wd, "#E2E6DE", 1.3, vertical=True)
    return c


def cream_puff_bag() -> Product:
    """寝かせた袋。透明なフィルムごしにシュー（描いた絵）が見える。画像は横長（左右がシール）。"""
    L, Wd = 150.0, 135.0
    gold, blue, cream, brown = "#E0A64B", "#1F4E99", "#FFF4CC", "#6B4A1E"

    def puff(c: Canvas, cx: float, cy: float, rx: float, ry: float):
        c.ellipse(cx - rx, cy - ry + 3, cx + rx, cy + ry + 3, fill="#D9D3C2")  # 影
        c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, fill="#C98536")
        c.ellipse(cx - rx * 0.92, cy - ry * 0.92, cx + rx * 0.9, cy + ry * 0.85, fill=gold)
        for _ in range(26):  # ひび割れの山
            a, rr = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0.1, 0.7)
            x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
            w = c.rng.uniform(5, 11)
            c.ellipse(x - w, y - w * 0.6, x + w, y + w * 0.6, fill=mix(gold, "#F6CF7E", c.rng.uniform(0.2, 0.8)))
            c.line([(x - w * 0.7, y + w * 0.5), (x + w * 0.6, y + w * 0.55)], "#A9692A", 0.6)
        for _ in range(260):  # 粉糖
            a, rr = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, 0.75) ** 0.5
            x, y = cx + rx * rr * math.cos(a), cy - ry * 0.2 + ry * 0.7 * rr * math.sin(a)
            c.ellipse(x - 0.4, y - 0.4, x + 0.4, y + 0.4, fill="#FFFDF5")

    c = _clear_bag(L, Wd, 2941, gold)
    puff(c, L / 2 + 10, Wd / 2 + 6, 48, 42)
    c.rect(12, 8, 62, 50, fill=blue, radius=5)
    c.text(37, 17, "カスタード", 5.6, cream, 900, max_w=46)
    c.text(37, 29, "シュー", 9.0, WHITE, 900)
    c.text(37, 39, "クリーム", 6.4, WHITE, 900)
    c.text(37, 46, "CREAM PUFF", 3.0, "#BBD0F0", 800, spacing=0.4)
    c.rect(12, Wd - 20, L - 12, Wd - 8, fill=blue, radius=4)
    c.text(L / 2, Wd - 14, "たっぷりカスタード＆ホイップ", 5.2, cream, 900, max_w=L - 34)
    c.ellipse(L - 46, 8, L - 14, 40, fill="#FFD54F")
    c.text(L - 30, 19, "要冷蔵", 4.0, brown, 900)
    c.text(L - 30, 28, "10℃以下", 3.6, brown, 800)
    front = _pouch(c, 2941, 0.8, 16)

    b = _clear_bag(L, Wd, 2942, gold)
    b.rect(14, 8, L - 14, Wd - 8, fill=WHITE, radius=3)
    _back_panel(b, 17, 11, L / 2 + 14, Wd - 12, [
        ("名称", "洋生菓子"), ("原材料名", "カスタードクリーム、乳等を主要原料とする食品、小麦粉、卵、ショートニング、砂糖／香料"),
        ("内容量", "1個"), ("消費期限", "右下に記載"), ("保存方法", "要冷蔵（10℃以下）")], 2.6,
        [("栄養成分表示 1個当たり", ""), ("エネルギー", "248kcal"), ("たんぱく質", "4.6g"), ("脂質", "15.2g"),
         ("炭水化物", "23.4g"), ("食塩相当量", "0.2g")], [], blue)
    b.barcode(L / 2 + 22, 16, 40, 24)
    b.recycle(L / 2 + 42, 58, 10, "プラ", blue, sub="袋")
    b.text(L / 2 + 42, Wd - 18, "消費期限 26.10.19", 3.6, INK, 800, max_w=50)
    back = _pouch(b, 2942, 0.8, 16)
    return Product(slug="cream_puff_bag", name="カスタードシュークリーム", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.055), mass_kg=0.09, material="film",
                   orientation="lying",
                   description="形は一般的な袋入りのコンビニのシュークリーム（長さ 150 mm・幅 135 mm・厚さ 55 mm）で、"
                               "寸法・質量は代表値。袋ごしに見えるシューは描いた絵。",
                   tags=["シュークリーム", "カスタード", "シュー", "スイーツ", "洋生菓子", "要冷蔵", "cream puff",
                         "choux", "dessert"],
                   colors=Colors(label_base=cream), images=[front, back], faces={"front": 0, "back": 1})


def dorayaki_bag() -> Product:
    """寝かせた個包装の袋。透明なフィルムごしにどら焼き（描いた絵）が見え、左上に和風の名前ラベル。"""
    L, Wd = 120.0, 115.0
    dark, red, paper = "#5B2C10", "#9E1B1B", "#F3E9D2"

    c = _clear_bag(L, Wd, 2951, "#B4692A")
    cx, cy, R = L / 2 + 4, Wd / 2 + 4, 44
    c.ellipse(cx - R, cy - R + 2.5, cx + R, cy + R + 2.5, fill="#D7D0C0")
    c.ellipse(cx - R, cy - R, cx + R, cy + R, fill="#E7C27A")  # 縁の明るい生地
    for k in range(12):  # 焼き色のむら（中心ほど濃い）
        r = (R - 3) * (1 - k / 13)
        c.ellipse(cx - r, cy - r, cx + r, cy + r, fill=mix("#A9581F", dark, k / 16))
    for _ in range(120):
        a, rr = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, R - 6)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        c.ellipse(x - 0.7, y - 0.5, x + 0.7, y + 0.5, fill=mix(dark, "#A9581F", c.rng.uniform(0.2, 0.7)))
    c.ellipse(cx - 16, cy - 30, cx - 2, cy - 24, fill="#B9763B")  # つや
    c.rect(12, 7, 44, 62, fill=paper, radius=2, outline=red, width=0.6)
    c.vtext(28, 15, "どら焼き", 9.0, dark, 900)
    c.rect(12, Wd - 18, 70, Wd - 7, fill=red, radius=2)
    c.text(41, Wd - 12.5, "北海道産小豆のつぶあん", 4.2, WHITE, 900, max_w=54)
    front = _pouch(c, 2951, 0.8, 14)

    b = _clear_bag(L, Wd, 2952, "#B4692A")
    b.rect(13, 7, L - 13, Wd - 7, fill=WHITE, radius=3)
    back_info(b, 16, 10, L - 16, [
        ("名称", "和生菓子"), ("原材料名", "つぶあん（小豆、砂糖、水あめ）、小麦粉、卵、砂糖、はちみつ、みりん／膨張剤"),
        ("内容量", "1個"), ("消費期限", "下に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 2.4,
        [("栄養成分表示 1個当たり", ""), ("エネルギー", "286kcal"), ("たんぱく質", "5.8g"), ("脂質", "2.6g"),
         ("炭水化物", "60.2g"), ("食塩相当量", "0.3g")])
    b.barcode(16, Wd - 30, 32, 20)
    b.recycle(60, Wd - 20, 9, "プラ", dark, sub="袋")
    b.text(88, Wd - 14, "消費期限 26.10.22", 3.4, INK, 800, max_w=40)
    back = _pouch(b, 2952, 0.8, 14)
    return Product(slug="dorayaki_bag", name="どら焼き つぶあん", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.035), mass_kg=0.085, material="film",
                   orientation="lying",
                   description="形は一般的な個包装のどら焼き（長さ 120 mm・幅 115 mm・厚さ 35 mm）で、寸法・質量は代表値。"
                               "袋ごしに見えるどら焼きは描いた絵。",
                   tags=["どら焼き", "つぶあん", "和菓子", "和生菓子", "スイーツ", "dorayaki", "japanese sweets"],
                   colors=Colors(label_base=paper), images=[front, back], faces={"front": 0, "back": 1})


def daifuku_2pack() -> Product:
    """白いトレーに豆大福 2 個（山形の部品と豆の粒）、透明なフィルムのケースと商品名シール。"""
    mochi, bean, green = "#F7F2E6", "#3A2430", "#2F6B3A"
    imgs = [_sticker(60, 32, "豆大福 2個入", "つぶあん・赤えんどう豆", green, 2961, 212, 248),
            _band(64, 9, "国産もち米使用", green, 2962)]
    tray_h, R, h = 0.008, 0.027, 0.030
    parts = [_box("Tray", (0.116, 0.064, tray_h), (0, 0, tray_h / 2), "#FBFAF6", "plastic")]
    for k, x in enumerate((-0.028, 0.028)):
        parts += _mound(f"Daifuku{k}", R, h, tray_h - 0.001, (x, 0), mochi)
        for j, (z, a) in enumerate([(0.006, -100), (0.012, -60), (0.010, -135), (0.018, -85), (0.022, -40),
                                    (0.016, -160), (0.008, 30), (0.020, 150), (0.025, -110), (0.014, 90)]):
            rr = _dome_r(R, h, z) - 0.0008
            parts.append(Part(f"Bean{k}{j}", "cylinder", [0.0055, 0.0045, 0.004],
                              [x + rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a)), tray_h + z],
                              [0, 0, a], color=bean, finish="glossy", collision=False, material="food"))
    film_h = 0.040
    parts += [_box("Film", (0.118, 0.066, film_h), (0, 0, 0.002 + film_h / 2), CLEAR, "glass", thin_walled=True),
              _box("Sticker", (0.060, 0.032, 0.0006), (0, 0, 0.002 + film_h + 0.0003), WHITE, "matte", {"top": 0},
                   collision=False),
              _box("Band", (0.064, 0.0006, 0.009), (0, -0.033 - 0.0003, 0.0085), green, "matte", {"front": 1},
                   collision=False)]
    return Product(slug="daifuku_2pack", name="豆大福 2個入", shape_class="assembly", category="food",
                   dims=Dimensions(0.002 + film_h + 0.0006, 0.118, depth=0.0666), mass_kg=0.15, material="plastic",
                   description="形は一般的なコンビニの豆大福 2 個入（白いトレー 116×64 mm に直径 54 mm・高さ 30 mm の大福 2 個、"
                               "高さ 40 mm の透明なケースと商品名シール）で、寸法・質量は代表値。大福と豆は簡単な形で表す。",
                   tags=["大福", "豆大福", "和菓子", "和生菓子", "もち", "つぶあん", "スイーツ", "daifuku", "mochi",
                         "japanese sweets"],
                   colors=Colors(label_base=mochi), images=imgs, parts=parts)


PRODUCTS = {f.__name__: f for f in (strawberry_shortcake_case, cream_puff_bag, roll_cake_pack, mont_blanc_cup,
                                     dorayaki_bag, daifuku_2pack, tiramisu_cup)}
