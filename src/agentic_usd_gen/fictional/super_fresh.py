"""架空の商品のデザイン: スーパーの生鮮・惣菜・大容量（精肉・鮮魚のトレーパック、卵、惣菜、米 10 kg、箱買いの段ボール）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
写真は CC0 の素材（photos.json）だけを合成し、肉・魚の身などは描いた絵で表す。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .conv_deli import _nori, _rice
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _face, _food, _food_photo, back_info, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}
WHITE = "#FFFFFF"
CLEAR = "#F2F6F8"
FOAM = "#F7F7F4"  # 発泡スチロールのトレー
KRAFT = "#B98D5C"  # 段ボール
KARAAGE_CROPS = ((0.27, 0.06, 0.58, 0.45), (0.50, 0.05, 0.80, 0.40), (0.37, 0.55, 0.72, 0.90))


# ---------------------------------------------------------------- 共通


def _blob(c: Canvas, cx: float, cy: float, a: float, b: float, ang: float, fill: str, wobble: float = 0.12,
          n: int = 18):
    """傾けた不規則な楕円（肉の切れ・魚の身など）。"""
    t = math.radians(ang)
    pts = []
    for k in range(n):
        u = 2 * math.pi * k / n
        r = 1 + c.rng.uniform(-wobble, wobble)
        x, y = a * r * math.cos(u), b * r * math.sin(u)
        pts.append((cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)))
    c.polygon(pts, fill=fill)


def _shreds(c: Canvas, n: int, length: float, light: str, dark: str, width: float = 0.6, spread: float = math.pi):
    """細い千切り（キャベツ・大根のつま）。"""
    for _ in range(n):
        x, y = c.rng.uniform(0, c.w_mm), c.rng.uniform(0, c.h_mm)
        a = c.rng.uniform(-spread / 2, spread / 2)
        c.line([(x, y), (x + length * math.cos(a), y + length * math.sin(a))], mix(light, dark, c.rng.random()), width)


def _pack_label(w: float, h: float, title: str, origin: str, per100: int | None, amount: int, price: int,
                accent: str, seed: int, keep: str = "4℃以下", kind: str = "加工") -> np.ndarray:
    """スーパーのパックに貼る計量ラベル（品名・産地/内容・100g 当たりの単価・内容量・価格・ダミーのバーコード）。

    per100 が None なら内容量は個数（amount 個）。
    """
    c = Canvas(w, h, 14, WHITE, seed)
    c.gradient(0, 0, w, h, "#FFFFFF", "#F1F1EC")
    c.rect(0, 0, w, h * 0.22, fill=accent)
    c.text(w / 2, h * 0.11, title, h * 0.13, WHITE, 900, max_w=w - 4)
    c.text(2.5, h * 0.30, origin, h * 0.065, INK, 800, anchor="lm", max_w=w * 0.58)
    c.text(2.5, h * 0.40, f"{kind}日 26.10.19", h * 0.06, INK, 600, anchor="lm")
    c.text(2.5, h * 0.49, "消費期限 26.10.21", h * 0.06, INK, 800, anchor="lm")
    c.text(2.5, h * 0.58, f"保存温度 {keep}", h * 0.055, INK, 600, anchor="lm", max_w=w * 0.58)
    x0 = w * 0.62
    c.rect(x0, h * 0.25, w - 2, h * 0.64, outline=accent, width=0.3, radius=0.8)
    rows = [("100g当り(円)", f"{per100}"), ("内容量(g)", f"{amount}")] if per100 else [("内容量", f"{amount}個")]
    y = h * 0.31
    for k, v in rows:
        c.text(x0 + 1.5, y, k, h * 0.045, INK, 600, anchor="lm", max_w=(w - x0) * 0.6)
        c.text(w - 3, y, v, h * 0.065, INK, 900, anchor="rm")
        y += h * 0.10
    c.text(x0 + 1.5, h * 0.53, "価格(円)", h * 0.05, accent, 800, anchor="lm")
    c.text(w - 3, h * 0.56, f"{price}", h * 0.12, accent, 900, anchor="rm", max_w=(w - x0) * 0.55)
    c.barcode(2.5, h * 0.66, w * 0.50, h * 0.30)
    c.paragraph(w * 0.58, h * 0.70, w - 2, "税込価格\n" + NOTICE, h * 0.042, INK, 500)
    return _face(c.array(), "paper", seed, 0.4, 3)


def _foam_tray(W: float, D: float, H: float, color: str, seed: int, ribs: bool = True) -> list[np.ndarray]:
    """発泡スチロールのトレーの上面（内側の底と縁）と側面（正面・背面、左右）の画像。mm。"""
    t = Canvas(W, D, 6, color, seed)
    t.gradient(0, 0, W, D, mix(color, WHITE, 0.4), mix(color, INK, 0.08))
    t.rect(6, 6, W - 6, D - 6, fill=mix(color, INK, 0.03), radius=6)
    if ribs:
        for x in np.arange(14, W - 12, 9.0):  # 底の溝
            t.line([(x, 10), (x, D - 10)], mix(color, INK, 0.08), 0.5)
    imgs = [_face(t.array(), "paper", seed, 0.6)]
    for i, w in enumerate((W, D)):
        s = Canvas(w, H, 6, color, seed + 1 + i)
        s.gradient(0, 0, w, H, mix(color, WHITE, 0.3), mix(color, INK, 0.14))
        s.rect(0, 0, w, 2.0, fill=mix(color, WHITE, 0.5))  # 縁のフランジ
        imgs.append(_face(s.array(), "paper", seed + 3 + i, 0.6))
    return imgs


def _dark_tray(W: float, D: float, H: float, seed: int, inner: str | None = None, rim: str = "#3C3C3C",
               wells=()) -> list[np.ndarray]:
    """黒い成形トレー（寿司・刺身・弁当）の上面と側面の画像。mm。inner は内側の地の色、wells は仕切りの矩形。"""
    black = "#161616"
    t = Canvas(W, D, 6, black, seed)
    t.gradient(0, 0, W, D, "#383838", "#0E0E0E")
    if inner:
        t.rect(4, 4, W - 4, D - 4, fill=inner, radius=6)
    t.rect(7, 7, W - 7, D - 7, fill="#1C1C1C", radius=5)
    for x0, y0, x1, y1 in wells:
        t.rect(x0, y0, x1, y1, fill="#232323", radius=3)
    imgs = [_face(t.array(), "plastic", seed, 0.4)]
    for i, w in enumerate((W, D)):
        s = Canvas(w, H, 6, black, seed + 1 + i)
        s.gradient(0, 0, w, H, "#3A3A3A", "#0E0E0E")
        s.pattern(0, 4, w, H - 1, "stripes", mix(black, WHITE, 0.07), 3.0, 0.3)
        s.rect(0, 0, w, 1.8, fill=rim)
        imgs.append(_face(s.array(), "plastic", seed + 1 + i, 0.5))
    return imgs


def _tray_pack(slug: str, name: str, W: float, D: float, tray_h: float, food_h: float, tray_imgs: list[np.ndarray],
               food: list[Part], label: np.ndarray, label_size: tuple[float, float], tray_color: str, mass: float,
               description: str, tags: list[str], photos: list[str] | None = None, lid_h: float | None = None,
               extra_imgs: list[np.ndarray] | None = None) -> Product:
    """トレー（画像 0: 上面、1: 正面・背面、2: 左右）に中身を載せ、ラップ（lid_h なら透明なフタ）とラベルを付ける。

    画像は tray_imgs（3 枚）、label（3）、extra_imgs（4〜）の順。寸法は m。food_h はトレーの縁から上の中身の高さ。
    """
    imgs = [*tray_imgs, label, *(extra_imgs or [])]
    parts = [_box("Tray", (W, D, tray_h), (0, 0, tray_h / 2), tray_color, "plastic",
                  {"top": 0, "front": 1, "back": 1, "left": 2, "right": 2}), *food]
    if lid_h:  # 透明なフタ（トレーの縁にかぶせる）
        pw, pd = W + 0.003, D + 0.003
        top = tray_h - 0.003 + lid_h
        parts.append(_box("Lid", (pw, pd, lid_h), (0, 0, tray_h - 0.003 + lid_h / 2), CLEAR, "glass",
                          thin_walled=True))
    else:  # ラップ（トレーごと包む）
        pw, pd = W + 0.002, D + 0.002
        top = tray_h + food_h
        parts.append(_box("Wrap", (pw, pd, top), (0, 0, top / 2), CLEAR, "glass", thin_walled=True,
                          collision=False))
    lw, lh = label_size[0] / 1000, label_size[1] / 1000
    parts.append(_box("Label", (lw, lh, 0.0006), (W / 2 - lw / 2 - 0.012, -D / 2 + lh / 2 + 0.010, top + 0.0003),
                      WHITE, "matte", {"top": 3}, collision=False))
    return Product(slug=slug, name=name, shape_class="assembly", category="food",
                   dims=Dimensions(round(top + 0.0006, 4), round(pw, 4), depth=round(pd, 4)),
                   mass_kg=mass, material="plastic", description=description, tags=tags, photos=photos or [],
                   colors=Colors(label_base=tray_color), images=imgs, parts=parts)


def _top_art(w: float, d: float, base: str, seed: int, draw) -> np.ndarray:
    """中身の部品の上面に貼る絵（w×d mm）。draw(c) で描く。"""
    c = Canvas(w, d, 8, base, seed)
    draw(c)
    return finish(c.array(), "paper", seed, 0.3)


# ---------------------------------------------------------------- 精肉


def pork_komagire_tray() -> Product:
    """白いトレーに豚こま切れ（低い山、上面に脂身の筋の入った薄切りの絵）、ラップと計量ラベル。"""
    W, D, th, fh = 0.210, 0.150, 0.018, 0.026

    def draw(c: Canvas):
        c.rect(0, 0, c.w_mm, c.h_mm, fill="#D98F88")
        for _ in range(70):  # 薄切りを重ねる
            cx, cy = c.rng.uniform(0, c.w_mm), c.rng.uniform(0, c.h_mm)
            a, b, ang = c.rng.uniform(18, 32), c.rng.uniform(8, 14), c.rng.uniform(0, 180)
            _blob(c, cx, cy, a, b, ang, mix("#D97C78", "#B5555A", c.rng.uniform(0, 1)))
            t = math.radians(ang)
            for s in (-0.6,):  # 脂身の縁
                ox, oy = -math.sin(t) * b * s, math.cos(t) * b * s
                c.line([(cx + ox - math.cos(t) * a * 0.8, cy + oy - math.sin(t) * a * 0.8),
                        (cx + ox + math.cos(t) * a * 0.8, cy + oy + math.sin(t) * a * 0.8)],
                       mix("#F2D6CC", "#E6B2A8", c.rng.uniform(0, 1)), c.rng.uniform(1.5, 3.5))

    top = _top_art(180, 122, "#D98F88", 6101, draw)
    meat = _food("Meat", "bun", (0.180, 0.122, fh), (0, 0, th - 0.003 + fh / 2), "#D98F88", "matte",
                 faces={"top": 4})
    return _tray_pack("pork_komagire_tray", "豚こま切れ 300g パック", W, D, th, fh - 0.003,
                      _foam_tray(W * 1000, D * 1000, th * 1000, FOAM, 6102), [meat],
                      _pack_label(62, 40, "豚こま切れ", "国産 豚肉（こま切れ）", 158, 312, 493, "#C62828", 6103),
                      (62, 40), FOAM, 0.33,
                      "形は一般的なスーパーの精肉のトレーパック（白い発泡トレー 210×150 mm・深さ 18 mm に豚こま切れ"
                      "約 300 g、ラップと計量ラベル）で、寸法・質量は代表値。肉は上面に薄切りの絵を貼った低い山で表す。",
                      ["豚肉", "豚こま切れ", "こま切れ", "精肉", "トレーパック", "要冷蔵", "生鮮", "pork",
                       "sliced pork", "meat tray pack"], extra_imgs=[top])


def chicken_thigh_tray() -> Product:
    """白いトレーに鶏もも肉 2 枚（皮目を上にした平たい山）、ラップと計量ラベル。"""
    W, D, th, fh = 0.220, 0.160, 0.020, 0.028

    def skin(c: Canvas):
        w, d = c.w_mm, c.h_mm
        c.gradient(0, 0, w, d, "#F3D9C2", "#E7BFA2")
        for _ in range(900):  # 皮の毛穴・凹凸
            x, y = c.rng.uniform(0, w), c.rng.uniform(0, d)
            r = c.rng.uniform(0.3, 0.9)
            c.ellipse(x - r, y - r, x + r, y + r, fill=mix("#E9C6AA", "#D7A487", c.rng.uniform(0, 1)))
        for _ in range(6):  # 皮の下の脂
            _blob(c, c.rng.uniform(10, w - 10), c.rng.uniform(8, d - 8), c.rng.uniform(8, 18),
                  c.rng.uniform(5, 10), c.rng.uniform(0, 180), mix("#F5E2B8", "#F3D9C2", 0.5), 0.2)
        for _ in range(4):  # 縁にのぞく身
            _blob(c, c.rng.choice([3, w - 3]), c.rng.uniform(5, d - 5), 6, 4, 90, "#E39A8C", 0.2)

    imgs = [_top_art(118, 92, "#F3D9C2", 6111 + k, skin) for k in range(2)]
    food = [_food(f"Thigh{k}", "bun", (0.118, 0.092, fh), (x, y, th - 0.003 + fh / 2), "#F3D9C2", "glossy",
                  rotation=(0, 0, r), faces={"top": 4 + k})
            for k, (x, y, r) in enumerate(((-0.040, 0.008, 12), (0.042, -0.006, -9)))]
    return _tray_pack("chicken_thigh_tray", "鶏もも肉 2枚 パック", W, D, th, fh - 0.003,
                      _foam_tray(W * 1000, D * 1000, th * 1000, FOAM, 6113), food,
                      _pack_label(62, 40, "鶏もも肉", "国産 若どり（もも）", 128, 524, 670, "#E65100", 6114),
                      (62, 40), FOAM, 0.58,
                      "形は一般的なスーパーの鶏もも肉のトレーパック（白い発泡トレー 220×160 mm に 2 枚約 520 g、"
                      "ラップと計量ラベル）で、寸法・質量は代表値。もも肉は皮目の絵を貼った平たい山で表す。",
                      ["鶏肉", "鶏もも肉", "もも肉", "若どり", "精肉", "トレーパック", "要冷蔵", "生鮮", "chicken thigh",
                       "chicken", "meat tray pack"], extra_imgs=imgs)


def ground_meat_tray() -> Product:
    """白いトレーに合いびき肉（角の丸い平たい山、上面に細かいひき肉の粒）、ラップと計量ラベル。"""
    W, D, th, fh = 0.180, 0.130, 0.018, 0.026

    def draw(c: Canvas):
        w, d = c.w_mm, c.h_mm
        c.rect(0, 0, w, d, fill="#C2626A")
        for _ in range(int(w * d / 1.2)):  # ひき肉の粒（赤身と脂）
            x, y = c.rng.uniform(0, w), c.rng.uniform(0, d)
            r = c.rng.uniform(0.5, 1.3)
            col = mix("#EBC0BA", "#DDA09C", c.rng.random()) if c.rng.random() < 0.07 else \
                mix("#C9555E", "#93303C", c.rng.random())
            c.ellipse(x - r, y - r * 0.7, x + r, y + r * 0.7, fill=col)

    top = _top_art(156, 108, "#C2626A", 6121, draw)
    meat = _food("Mince", "bun", (0.156, 0.108, fh), (0, 0, th - 0.003 + fh / 2), "#C2626A", "matte",
                 faces={"top": 4})
    return _tray_pack("ground_meat_tray", "合いびき肉 300g パック", W, D, th, fh - 0.003,
                      _foam_tray(W * 1000, D * 1000, th * 1000, FOAM, 6122), [meat],
                      _pack_label(58, 38, "合いびき肉", "牛肉（輸入）・豚肉（国産）", 138, 305, 420, "#AD1457", 6123),
                      (58, 38), FOAM, 0.33,
                      "形は一般的なスーパーのひき肉のトレーパック（白い発泡トレー 180×130 mm に約 300 g、"
                      "ラップと計量ラベル）で、寸法・質量は代表値。ひき肉は粒の絵を貼った平たい山で表す。",
                      ["ひき肉", "合いびき肉", "挽肉", "精肉", "トレーパック", "要冷蔵", "生鮮", "ground meat",
                       "minced meat", "meat tray pack"], extra_imgs=[top])


# ---------------------------------------------------------------- 鮮魚


def _salmon_flesh(c: Canvas, skin: bool = True):
    """鮭の身（橙の地に白い脂の筋、下の縁に銀色の皮）をキャンバス全体に描く。"""
    w, h = c.w_mm, c.h_mm
    c.gradient(0, 0, w, h, "#F49A6A", "#E6774A")
    for k in range(int(w / 6) + 2):
        x = -h * 0.3 + k * 6
        c.line([(x, 0), (x + h * 0.35, h * 0.5), (x + h * 0.1, h)], "#FBD3BA", 1.0)
    if skin:
        c.rect(0, h * 0.90, w, h, fill="#9AA0A6")
        c.rect(0, h * 0.90, w, h * 0.93, fill="#C7CCD0")


def salmon_fillet_tray() -> Product:
    """白いトレーに鮭の切り身 2 切れ（平たい山、上面に身の絵）と笹の敷物、ラップと計量ラベル。"""
    W, D, th, fh = 0.190, 0.125, 0.016, 0.022
    imgs = [_top_art(82, 58, "#F49A6A", 6131 + k, _salmon_flesh) for k in range(2)]
    leaf = Canvas(150, 100, 6, "#3E8E41", 6133)
    leaf.gradient(0, 0, 150, 100, "#4CAF50", "#2E7D32")
    for k in range(9):
        leaf.line([(0, 6 + k * 11), (150, 2 + k * 11)], "#81C784", 0.6)
    imgs.append(_face(leaf.array(), "film", 6133, 0.3))
    # 画像 4・5: 切り身、6: 笹
    food = [_food("Leaf", "box", (0.150, 0.100, 0.0012), (0, 0, th - 0.0024), "#3E8E41", "glossy",
                  faces={"top": 6})]
    for k, (x, r) in enumerate(((-0.042, 8), (0.042, -6))):
        food.append(_food(f"Fillet{k}", "bun", (0.082, 0.058, fh), (x, 0, th - 0.0018 + fh / 2), "#F49A6A",
                          "glossy", rotation=(0, 0, r), faces={"top": 4 + k}))
    return _tray_pack("salmon_fillet_tray", "生鮭 切り身 2切 パック", W, D, th, fh - 0.0018,
                      _foam_tray(W * 1000, D * 1000, th * 1000, FOAM, 6134, ribs=False), food,
                      _pack_label(56, 36, "生鮭 切り身", "チリ産 養殖（解凍）", None, 2, 398, "#1565C0", 6135,
                                  "4℃以下", "加工"),
                      (56, 36), FOAM, 0.22,
                      "形は一般的なスーパーの鮮魚の切り身のトレーパック（白い発泡トレー 190×125 mm に切り身 2 切れと"
                      "笹の敷物、ラップと計量ラベル）で、寸法・質量は代表値。切り身は身の絵を貼った平たい山で表す。",
                      ["鮭", "生鮭", "サーモン", "切り身", "鮮魚", "トレーパック", "要冷蔵", "生鮮", "salmon fillet",
                       "fish fillet", "fish tray pack"], extra_imgs=imgs)


def sashimi_assorted_tray() -> Product:
    """黒いトレーに大根のつま（山）・大葉・刺身 4 種 12 切れ・わさび・菊、透明なフタと計量ラベル。"""
    W, D, th = 0.190, 0.135, 0.018
    tray_imgs = _dark_tray(190, 135, th * 1000, 6141, inner="#B8964A", rim="#B8964A")

    tsuma = Canvas(150, 60, 8, "#F4F4EE", 6144)  # 大根のつま（細い千切り）
    tsuma.gradient(0, 0, 150, 60, "#FAFAF5", "#E4E6DA")
    _shreds(tsuma, 1400, 6, "#FFFFFF", "#D4D8C8", 0.4, 0.8)
    salmon = Canvas(48, 26, 10, "#F49A6A", 6145)
    _salmon_flesh(salmon, skin=False)
    tuna = Canvas(48, 26, 10, "#B3243A", 6146)
    tuna.gradient(0, 0, 48, 26, "#C02C42", "#981A2E")
    for k in range(7):
        tuna.line([(k * 8 - 4, 0), (k * 8 + 4, 26)], "#A81F35", 0.6)
    hamachi = Canvas(48, 26, 10, "#F1D9C9", 6147)
    hamachi.gradient(0, 0, 48, 26, "#F6E3D6", "#E9C4B0")
    hamachi.rect(0, 21, 48, 26, fill="#B85A55")  # 血合い
    ika = Canvas(48, 26, 10, "#F2EFE6", 6148)
    ika.gradient(0, 0, 48, 26, "#FBFAF5", "#E6E1D2")
    for k in range(9):  # 鹿の子の包丁目
        ika.line([(k * 6, 0), (k * 6 + 6, 26)], "#DCD6C4", 0.4)
    shiso = Canvas(60, 50, 8, "#3C8D3A", 6149)
    shiso.gradient(0, 0, 60, 50, "#4CAF50", "#2E7D32")
    shiso.line([(30, 2), (30, 48)], "#9CCC65", 0.7)
    for k in range(5):
        shiso.line([(30, 8 + k * 8), (8, 4 + k * 8)], "#81C784", 0.5)
        shiso.line([(30, 8 + k * 8), (52, 4 + k * 8)], "#81C784", 0.5)
    extra = [finish(x.array(), "paper", 6144 + i, 0.25) for i, x in enumerate((tsuma, tuna, salmon, hamachi, ika,
                                                                              shiso))]
    # 画像 4: つま、5: まぐろ、6: サーモン、7: はまち、8: いか、9: 大葉
    z0 = th - 0.004
    food = [_food("Tsuma", "bun", (0.150, 0.050, 0.026), (0, 0.034, z0 + 0.013), "#F4F4EE", "matte",
                  faces={"top": 4})]
    for k, x in enumerate((-0.050, 0.0, 0.050)):  # 大葉（つまの前に立てかける）
        food.append(_food(f"Shiso{k}", "box", (0.040, 0.034, 0.001), (x, 0.012, z0 + 0.014), "#3C8D3A", "matte",
                          rotation=(25, 0, (k - 1) * 8), faces={"top": 9}))
    kinds = (("Tuna", 5, "#B3243A", -0.060), ("Salmon", 6, "#F49A6A", -0.020), ("Hamachi", 7, "#F1D9C9", 0.020),
             ("Ika", 8, "#F2EFE6", 0.060))
    for nm, img, col, x in kinds:  # 4 種を 3 切れずつ、つまに立てかけるように傾けて重ねる
        for j in range(3):
            food.append(_food(f"{nm}{j}", "box", (0.030, 0.026, 0.006),
                              (x + (j - 1) * 0.003, -0.032 + j * 0.011, z0 + 0.010 + j * 0.002), col, "glossy",
                              rotation=(-22, 0, 0), faces={"top": img}))
    food += [_food("Wasabi", "pointed_dome", (0.016, 0.014, 0.011), (0.078, 0.042, z0 + 0.0055), "#9CCC65",
                   "matte"),
             _food("Kiku", "dome", (0.014, 0.014, 0.006), (-0.078, 0.044, z0 + 0.003), "#FDD835", "matte")]
    return _tray_pack("sashimi_assorted_tray", "お刺身 4点盛り", W, D, th, 0.0, tray_imgs, food,
                      _pack_label(58, 38, "お刺身 4点盛", "まぐろ・サーモン・はまち・いか", None, 12, 980, "#0D47A1",
                                  6150, "10℃以下"),
                      (58, 38), "#161616", 0.26,
                      "形は一般的なスーパーの刺身の盛り合わせ（黒いトレー 190×135 mm に大根のつま・大葉・"
                      "刺身 4 種 12 切れ、高さ 38 mm の透明なフタと計量ラベル）で、寸法・質量は代表値。"
                      "刺身は身の色の絵を貼った傾けた板で表す。",
                      ["刺身", "お刺身", "刺身盛り合わせ", "まぐろ", "サーモン", "鮮魚", "要冷蔵", "生鮮", "sashimi",
                       "assorted sashimi", "sashimi platter"], lid_h=0.038, extra_imgs=extra)


# ---------------------------------------------------------------- 卵


def egg_10pack() -> Product:
    """透明な卵パック（下のトレーと上のフタ、まわりのフランジ）に卵 10 個（回転体）、上に紙の帯ラベル。"""
    W, D = 0.255, 0.108
    base_h, lid_h = 0.036, 0.034
    shell = "#F1E6D8"
    prof = [[0, 0], [0.50, 0.02], [0.75, 0.07], [0.92, 0.16], [1.0, 0.32], [0.98, 0.46], [0.90, 0.61],
            [0.75, 0.76], [0.52, 0.89], [0.27, 0.97], [0, 1]]
    band = Canvas(150, 60, 12, WHITE, 6151)
    band.gradient(0, 0, 150, 60, "#FFFDF4", "#F6EED8")
    band.rect(0, 0, 150, 14, fill="#F2A900")
    band.text(75, 7, "新鮮 たまご", 9, WHITE, 900)
    band.ellipse(6, 18, 40, 52, fill="#FFE082")
    band.ellipse(13, 25, 33, 45, fill="#F9A825")
    band.text(98, 23, "白玉 Mサイズ", 7.5, INK, 900)
    band.text(98, 33, "10個入", 9.5, "#E65100", 900)
    band.text(98, 42, "賞味期限 26.11.02", 3.6, INK, 700)
    band.text(98, 47, "保存方法 10℃以下で保存", 3.0, INK, 600)
    band.barcode(48, 50, 28, 8)
    band.text(118, 55, NOTICE, 1.5, INK, 500, max_w=56)
    imgs = [_face(band.array(), "paper", 6151, 0.4, 3)]
    parts = [_box("Base", (W, D, base_h), (0, 0, base_h / 2), CLEAR, "glass", thin_walled=True),
             _box("Lid", (W, D, lid_h), (0, 0, base_h + 0.002 + lid_h / 2), CLEAR, "glass", thin_walled=True)]
    eh, ed = 0.057, 0.043
    for r in range(2):
        for k in range(5):
            x, y = (k - 2) * 0.049, (r - 0.5) * 0.051
            parts.append(Part(f"Egg{r}{k}", "revolve", [ed, ed, eh], [x, y, 0.005 + eh / 2], color=shell,
                              finish="plastic", collision=False, material="food", profile=prof))
    top = base_h + 0.002 + lid_h
    parts.append(_box("Band", (0.150, 0.060, 0.0006), (0, 0, top + 0.0003), WHITE, "matte", {"top": 0},
                      collision=False))
    return Product(slug="egg_10pack", name="たまご Mサイズ 10個パック", shape_class="assembly", category="food",
                   dims=Dimensions(round(top + 0.0006, 4), W, depth=D),
                   mass_kg=0.66, material="plastic",
                   description="形は一般的なスーパーの卵 10 個入りの透明なパック（255×108 mm・高さ約 73 mm、"
                               "上に紙の帯ラベル。まわりのフランジは省略）で、寸法・質量は代表値。卵は M サイズ"
                               "（直径 43 mm・高さ 57 mm、約 60 g）の回転体で、パックのくぼみは省いて箱で表す。",
                   tags=["卵", "たまご", "鶏卵", "卵パック", "10個入り", "要冷蔵", "eggs", "egg carton",
                         "10 eggs pack"],
                   colors=Colors(label_base=CLEAR), images=imgs, parts=parts)


# ---------------------------------------------------------------- 惣菜


def _clear_tray(W: float, D: float, H: float, seed: int) -> list[np.ndarray]:
    """透明なフードパックの下（少し白く曇った成形トレー）の上面と側面の画像。mm。"""
    t = Canvas(W, D, 6, "#F2F2EE", seed)
    t.gradient(0, 0, W, D, "#FAFAF6", "#E2E3DC")
    t.rect(4, 4, W - 4, D - 4, fill="#ECEDE6", radius=6)
    imgs = [_face(t.array(), "film", seed, 0.4)]
    for i, w in enumerate((W, D)):
        s = Canvas(w, H, 6, "#EDEEE8", seed + 1 + i)
        s.gradient(0, 0, w, H, "#F7F7F3", "#D8DAD2")
        s.pattern(0, 3, w, H, "stripes", "#E1E2DA", 3.0, 0.3)
        imgs.append(_face(s.array(), "film", seed + 1 + i, 0.5))
    return imgs


def fried_food_pack() -> Product:
    """透明なフードパックに、からあげ 3 個・コロッケ 2 個・キャベツの千切り・レモン、フタに惣菜のラベル。"""
    W, D, th = 0.190, 0.135, 0.022
    cabbage = Canvas(70, 110, 8, "#DDEBB8", 6164)
    _shreds(cabbage, 900, 7, "#F3F8E2", "#A9CC6A")
    croq = Canvas(70, 50, 8, "#B9772E", 6165)
    croq.gradient(0, 0, 70, 50, "#C98A3E", "#A0602A")
    for _ in range(700):  # パン粉
        x, y = croq.rng.uniform(0, 70), croq.rng.uniform(0, 50)
        r = croq.rng.uniform(0.4, 1.1)
        croq.ellipse(x - r, y - r * 0.6, x + r, y + r * 0.6, fill=mix("#E3B36A", "#8A4E1F", croq.rng.random()))
    extra = [finish(cabbage.array(), "paper", 6164, 0.2), finish(croq.array(), "paper", 6165, 0.3)]
    extra += [_food_photo("karaage", 34, 30, crop, 6166 + k) for k, crop in enumerate(KARAAGE_CROPS)]
    # 画像 4: キャベツ、5: コロッケ、6〜8: からあげ
    z0 = th - 0.003
    food = [_food("Cabbage", "bun", (0.070, 0.110, 0.022), (-0.055, 0.004, z0 + 0.011), "#DDEBB8", "matte",
                  faces={"top": 4})]
    for k, (x, y, r) in enumerate(((0.010, 0.030, 8), (0.010, -0.030, -6))):
        food.append(_food(f"Croquette{k}", "bun", (0.070, 0.050, 0.022), (x, y, z0 + 0.011), "#B9772E", "matte",
                          rotation=(0, 0, r), faces={"top": 5}))
    for k, (x, y, r) in enumerate(((0.066, 0.036, 15), (0.068, 0.000, -30), (0.064, -0.036, 50))):
        food.append(_food(f"Karaage{k}", "bun", (0.034, 0.030, 0.024), (x, y, z0 + 0.012), "#A8692F", "matte",
                          rotation=(0, 0, r), faces={"top": 6 + k}))
    food.append(_food("Lemon", "cylinder", (0.026, 0.026, 0.004), (-0.030, -0.045, z0 + 0.022), "#F2D23C",
                      "plastic", rotation=(50, 0, 10)))
    return _tray_pack("fried_food_pack", "揚げ物盛り合わせ（からあげ・コロッケ）", W, D, th, 0.0,
                      _clear_tray(190, 135, th * 1000, 6161), food,
                      _pack_label(60, 40, "揚げ物盛り合わせ", "からあげ 3個・コロッケ 2個", None, 5, 498, "#E65100",
                                  6169, "高温多湿を避ける", "製造"),
                      (60, 40), "#F2F2EE", 0.42,
                      "形は一般的なスーパーの惣菜売場の揚げ物のパック（透明なフードパック 190×135 mm・高さ約 60 mm に"
                      "からあげ 3 個・コロッケ 2 個・キャベツの千切り・レモン、フタにラベル）で、寸法・質量は代表値。"
                      "揚げ物は写真や絵を貼った山で表す。",
                      ["惣菜", "揚げ物", "からあげ", "コロッケ", "フードパック", "fried food", "karaage", "croquette",
                       "deli pack"], photos=["karaage"], lid_h=0.040, extra_imgs=extra)


def sushi_pack() -> Product:
    """黒いトレーに握り寿司 10 貫（シャリの山とネタの山）・軍艦 2 貫・がり・バラン、透明なフタと計量ラベル。"""
    W, D, th = 0.210, 0.145, 0.016
    tray_imgs = _dark_tray(210, 145, th * 1000, 6171, inner="#B71C1C", rim="#B71C1C")

    def neta(base: str, seed: int, draw=None) -> np.ndarray:
        c = Canvas(30, 54, 10, base, seed)
        c.gradient(0, 0, 30, 54, mix(base, WHITE, 0.15), mix(base, INK, 0.12))
        if draw:
            draw(c)
        return finish(c.array(), "paper", seed, 0.2)

    def stripes(col: str, step: float, wdt: float):
        def draw(c):
            for k in range(int(54 / step) + 2):
                c.line([(0, k * step - 4), (30, k * step + 4)], col, wdt)
        return draw

    def tamago(c):
        c.rect(0, 0, 30, 54, fill="#F6CF4A")
        c.rect(0, 22, 30, 32, fill="#1E2A1A")  # のりの帯

    def ebi(c):
        for k in range(6):
            c.rect(0, k * 9, 30, k * 9 + 4, fill="#F07A55")

    rice = Canvas(26, 44, 10, "#F4F1E8", 6174)
    _rice(rice, 0, 0, 26, 44)
    gunkan = Canvas(30, 30, 10, "#E8641E", 6181)
    gunkan.gradient(0, 0, 30, 30, "#E8641E", "#B8400E")
    for _ in range(40):  # いくら
        x, y = gunkan.rng.uniform(4, 26), gunkan.rng.uniform(4, 26)
        gunkan.ellipse(x - 2.6, y - 2.6, x + 2.6, y + 2.6, fill=mix("#F57C2A", "#C0410E", gunkan.rng.random()))
        gunkan.ellipse(x - 1.4, y - 1.6, x - 0.4, y - 0.6, fill="#FFD3A8")
    imgs = [finish(rice.array(), "paper", 6174, 0.2),
            neta("#B3243A", 6175, stripes("#A21C30", 9, 0.6)),  # 5 まぐろ
            neta("#F49A6A", 6176, stripes("#FBD3BA", 6, 1.0)),  # 6 サーモン
            neta("#F2EFE6", 6177, stripes("#DCD6C4", 5, 0.4)),  # 7 いか
            neta("#F6CF4A", 6178, tamago),  # 8 たまご
            neta("#F6E6DA", 6179, ebi),  # 9 えび
            neta("#E9D0C2", 6180, lambda c: c.rect(24, 0, 30, 54, fill="#B85A55")),  # 10 はまち
            finish(gunkan.array(), "paper", 6181, 0.2)]
    # 画像 4: シャリ、5〜10: ネタ、11: いくら
    z0 = th - 0.003
    food = []
    for k, img in enumerate((5, 6, 7, 8, 9, 10, 5, 6, 9, 10)):  # 握り 10 貫（2 列 × 5、縦長に並べる）
        r, j = divmod(k, 5)
        x, y = -0.084 + j * 0.031, 0.033 - r * 0.064
        food += [_food(f"Shari{k}", "bun", (0.024, 0.042, 0.016), (x, y, z0 + 0.008), "#F4F1E8", "matte",
                       faces={"top": 4}),
                 _food(f"Neta{k}", "dome", (0.028, 0.052, 0.008), (x, y, z0 + 0.0125), "#C0C0C0", "glossy",
                       faces={"top": img})]
    for k, y in enumerate((0.040, 0.004)):  # 軍艦 2 貫（右の列）
        food += [_food(f"GunkanNori{k}", "cylinder", (0.030, 0.030, 0.024), (0.080, y, z0 + 0.012), "#26301F",
                       "glossy"),
                 _food(f"Ikura{k}", "dome", (0.028, 0.028, 0.008), (0.080, y, z0 + 0.024), "#E8641E", "glossy",
                       faces={"top": 11})]
    food += [_food("Gari", "dome", (0.026, 0.020, 0.008), (0.080, -0.040, z0 + 0.000), "#F3A5B5", "plastic"),
             _food("Baran", "box", (0.004, 0.120, 0.018), (0.062, -0.002, z0 + 0.009), "#2E9D3A", "plastic")]
    return _tray_pack("sushi_pack", "にぎり寿司 12貫", W, D, th, 0.0, tray_imgs, food,
                      _pack_label(58, 38, "にぎり寿司 12貫", "まぐろ・サーモン・いか・えび ほか", None, 12, 1180,
                                  "#B71C1C", 6183, "10℃以下", "製造"),
                      (58, 38), "#161616", 0.45,
                      "形は一般的なスーパーの寿司のパック（黒いトレー 210×145 mm に握り 10 貫・軍艦 2 貫・がり・バラン、"
                      "高さ 40 mm の透明なフタと計量ラベル）で、寸法・質量は代表値。シャリは米粒の絵の山、"
                      "ネタは絵を貼った薄い山で表す。",
                      ["寿司", "すし", "にぎり寿司", "握り寿司", "盛り合わせ", "惣菜", "要冷蔵", "sushi",
                       "nigiri sushi", "sushi pack"], lid_h=0.040, extra_imgs=imgs)


def bento_large() -> Product:
    """大きい黒いトレーにごはん（大盛り）・からあげ 5 個・スパゲティ・キャベツ・漬物、透明なフタとラベル。"""
    W, D, th = 0.235, 0.175, 0.036
    tray_imgs = _dark_tray(235, 175, th * 1000, 6191,
                           wells=((9, 9, 118, 166), (122, 9, 226, 100), (122, 104, 172, 166), (176, 104, 226, 166)))
    rice = Canvas(108, 158, 8, "#F4F1E8", 6194)
    _rice(rice, 0, 0, 108, 158)
    rice.ellipse(46, 70, 62, 86, fill="#9E1B2A")  # 梅干し
    cabbage = Canvas(50, 62, 8, "#DDEBB8", 6195)
    _shreds(cabbage, 500, 6, "#F3F8E2", "#A9CC6A")
    extra = [finish(rice.array(), "paper", 6194, 0.25), finish(cabbage.array(), "paper", 6195, 0.2),
             _food_photo("spaghetti", 48, 60, (0.25, 0.20, 0.75, 0.80), 6196)]
    extra += [_food_photo("karaage", 34, 30, crop, 6197 + k) for k, crop in enumerate(KARAAGE_CROPS)]
    # 画像 4: ごはん、5: キャベツ、6: スパゲティ、7〜9: からあげ

    def at(cx: float, cy: float) -> tuple[float, float]:
        """トレーの上面の画像の mm（左上が原点、下が手前）を部品の座標 m に。"""
        return (cx - 117.5) / 1000, (87.5 - cy) / 1000

    z0 = th - 0.004
    food = [_food("Rice", "bun", (0.106, 0.154, 0.024), (*at(63.5, 87.5), z0 + 0.012), "#F4F1E8", "matte",
                  faces={"top": 4}),
            _food("Cabbage", "bun", (0.048, 0.060, 0.016), (*at(147, 135), z0 + 0.008), "#DDEBB8", "matte",
                  faces={"top": 5}),
            _food("Spaghetti", "bun", (0.048, 0.060, 0.014), (*at(201, 135), z0 + 0.007), "#D9A35A", "matte",
                  faces={"top": 6})]
    for k, (cx, cy, r) in enumerate(((140, 28, 10), (172, 24, -25), (206, 30, 40), (148, 70, -50), (192, 74, 15))):
        food.append(_food(f"Karaage{k}", "bun", (0.036, 0.032, 0.026), (*at(cx, cy), z0 + 0.013), "#A8692F", "matte",
                          rotation=(0, 0, r), faces={"top": 7 + k % 3}))
    for k in range(3):  # 柴漬け（ごはんの上の隅）
        food.append(_food(f"Pickle{k}", "box", (0.012, 0.010, 0.005), (*at(30 + k * 10, 140), z0 + 0.022),
                          "#8E3B6E", "plastic", rotation=(0, 0, k * 25)))
    return _tray_pack("bento_large", "からあげ弁当 ごはん大盛り", W, D, th, 0.0, tray_imgs, food,
                      _pack_label(70, 46, "からあげ弁当 大盛", "ごはん 350g・からあげ 5個", None, 1, 598, "#C62828",
                                  6200, "高温多湿を避ける", "製造"),
                      (70, 46), "#161616", 0.82,
                      "形は一般的なスーパーの大きめの弁当（黒いトレー 235×175 mm・深さ 36 mm にごはん大盛り・"
                      "からあげ 5 個・スパゲティ・キャベツ・漬物、高さ 26 mm の透明なフタとラベル）で、寸法・質量は"
                      "代表値。ごはん・おかずは写真や絵を貼った山で表す。",
                      ["弁当", "お弁当", "からあげ弁当", "大盛り", "惣菜", "bento", "lunch box", "karaage bento"],
                      photos=["karaage", "spaghetti"], lid_h=0.026, extra_imgs=extra)


# ---------------------------------------------------------------- 大容量


def rice_bag_10kg() -> Product:
    """精米 10 kg の袋（袋の形 pouch、正面と裏面の画像）。"""
    W, H = 380.0, 580.0
    cream, navy, red = "#F7F3E6", "#1F3A68", "#B8322A"
    c = Canvas(W, H, 3, cream, seed=6201)
    c.gradient(0, 0, W, H, "#FFFDF5", "#EEE4C8")
    c.photo("rice_field", 0, 370, W, H, crop=(0, 0.35, 1, 1))
    c.gradient(0, 362, W, 374, "#EFE6CC", mix("#EFE6CC", "#C9B46A", 0.4))
    seal_crimp(c, 0, 0, W, 16, "#E4DAC0", 2.6)  # 上だけシール。底はマチを折り込んだ平らな底（下端の紺の帯が底面の色）
    c.rect(0, 16, W, 24, fill=navy)
    c.rect(0, H - 10, W, H, fill=navy)
    c.text(W / 2, 48, "国内産 ブレンド米", 18, navy, 800)
    c.text(W / 2, 74, "POLISHED RICE  ━  10kg", 7, mix(navy, cream, 0.3), 700, spacing=2)
    c.text(W / 2, 128, "精 米", 88, INK, 900)
    c.rect(W / 2 - 92, 180, W / 2 + 92, 210, fill=navy, radius=15)
    c.text(W / 2, 195, "毎日のごはんに  お徳用", 14, WHITE, 900)
    c.photo("cooked_rice", W / 2 - 112, 222, W / 2 + 68, 350, shape="ellipse", feather=3, shadow=3,
            crop=(0.04, 0.10, 0.96, 0.92))
    c.ellipse(W - 116, 236, W - 18, 334, fill=red, outline=WHITE, width=2.5)
    c.text(W - 67, 278, "10kg", 30, WHITE, 900)
    c.text(W - 67, 308, "内容量", 8, WHITE, 700)
    c.text(W / 2 - 22, 358, "※写真はイメージです", 6, INK, 500)
    c.rect(W / 2 - 110, 500, W / 2 + 110, 540, fill=mix(cream, WHITE, 0.5), radius=7)
    c.text(W / 2, 513, "精米  10kg", 13, INK, 900)
    c.text(W / 2, 530, "国内産 ブレンド米", 8, navy, 800)
    front = trim_safe(edge_shade(finish(c.array(), "film", 6201, 1.0), 30, 0.15))

    b = Canvas(W, H, 3, cream, seed=6202)
    b.gradient(0, 0, W, H, "#FFFDF5", "#EEE4C8")
    seal_crimp(b, 0, 0, W, 16, "#E4DAC0", 2.6)
    b.rect(0, 16, W, 24, fill=navy)
    b.rect(0, H - 10, W, H, fill=navy)
    b.text(W / 2, 44, "精米 10kg  国内産 ブレンド米", 13, navy, 900)
    b.rect(18, 60, W - 18, 180, fill=WHITE, radius=5)
    back_info(b, 26, 68, W - 26, [
        ("名称", "精米"), ("原料玄米", "国内産 複数原料米"), ("内容量", "10kg"), ("精米年月日", "2026年10月中旬"),
        ("保存方法", "直射日光・高温多湿を避け、涼しい所で保存してください")], 9.5)
    b.rect(18, 196, W - 18, 320, fill=WHITE, radius=5)
    b.rect(18, 196, W - 18, 216, fill=navy, radius=5)
    b.text(W / 2, 206, "おいしいご飯の炊き方", 11, WHITE, 900)
    b.paragraph(30, 226, W - 30, "1. 計量カップで正確に量り、たっぷりの水で手早くとぎます。\n"
                                 "2. 水がほぼ透明になるまで、2〜3回水を替えます。\n"
                                 "3. 炊飯器の目盛りに合わせて水を加え、30分以上浸してから炊きます。\n"
                                 "4. 炊きあがったら、すぐに全体をさっくりとほぐします。", 9.6, INK, 500)
    b.rect(18, 336, W - 18, 420, fill=mix(red, WHITE, 0.88), radius=5)
    b.text(30, 350, "【ご注意】", 9.5, red, 900, anchor="lm")
    b.paragraph(30, 362, W - 30, "お米は生鮮食品です。精米後はお早めにお召し上がりください。"
                                 "重いので持ち運びの際は袋の底を支えてください。袋の破れにご注意ください。", 8.4, INK, 500)
    b.rect(18, 440, 168, 530, fill=WHITE, radius=5)
    b.barcode(28, 450, 130, 72)
    b.recycle(205, 485, 28, "プラ", navy, sub="袋")
    b.rect(W - 132, 446, W - 18, 524, fill=WHITE, radius=5)
    b.text(W - 75, 462, "保存の目安", 9.5, navy, 900)
    b.text(W - 75, 484, "夏場 約1か月", 9.5, INK, 700)
    b.text(W - 75, 504, "冬場 約2か月", 9.5, INK, 700)
    back = trim_safe(edge_shade(finish(b.array(), "film", 6203, 1.0), 30, 0.15))
    return Product(slug="rice_bag_10kg", name="精米 10kg", shape_class="pouch", category="food",
                   # 底マチ（厚さ 130 mm の平らな底）と角の丸い四角の断面で自立させる。マチのない袋（底がシールの線）だと
                   # 倒れ始める角度が 0° で、2° 傾けて置くと倒れた
                   dims=Dimensions(0.58, 0.38, depth=0.13, gusset=0.13, square=3), mass_kg=10.08, material="film",
                   description="形は一般的な 10kg 入りの米袋（高さ 580 mm・幅 380 mm・厚さ約 130 mm、底マチで自立し、"
                               "上端だけシール）で、寸法・質量は代表値。持ち手の穴は省略。",
                   tags=["米", "お米", "精米", "10kg", "大容量", "rice", "rice bag", "10kg rice bag"],
                   photos=["rice_field", "cooked_rice"], colors=Colors(label_base=cream), images=[front, back],
                   faces={"front": 0, "back": 1})


def _carton(W: float, D: float, H: float, seed: int, title: str, sub: str, count: str, accent: str,
            side_note: str, photo: str | None = None, crop=None) -> list[np.ndarray]:
    """飲料の段ボールケースの 6 面（正面・背面・右・左・上・下）。mm。上面は中央の合わせ目とテープ。"""

    def kraft(w: float, h: float, sd: int) -> Canvas:
        c = Canvas(w, h, 3, KRAFT, sd)
        c.gradient(0, 0, w, h, "#C49A69", "#AE8352")
        return c

    def big(w: float, h: float, sd: int, barcode: bool) -> Canvas:
        c = kraft(w, h, sd)
        c.rect(0, 0, w, h * 0.12, fill=accent)
        c.rect(0, h * 0.88, w, h, fill=accent)
        if photo:
            c.photo(photo, w * 0.05, h * 0.20, w * 0.38, h * 0.80, shape="round", radius=6, crop=crop)
        x, mw = (w * 0.69, w * 0.56) if photo else (w / 2, w * 0.9)
        c.text(x, h * 0.32, title, min(h * 0.20, w * 0.10), accent, 900, max_w=mw)
        c.text(x, h * 0.48, sub, h * 0.06, INK, 800, max_w=mw)
        c.rect(x - w * 0.16, h * 0.56, x + w * 0.16, h * 0.72, fill=WHITE, radius=4)
        c.text(x, h * 0.64, count, h * 0.09, accent, 900, max_w=w * 0.3)
        c.text(w / 2, h * 0.06, "↑ この面を上に  天地無用 ↑", h * 0.05, WHITE, 800)
        if barcode:
            c.barcode(w * 0.70 - w * 0.11, h * 0.75, w * 0.22, h * 0.11)
        c.text(w - 4, h * 0.94, NOTICE, h * 0.028, WHITE, 500, anchor="rm", max_w=w * 0.6)
        return c

    def side(w: float, h: float, sd: int) -> Canvas:
        c = kraft(w, h, sd)
        c.rect(0, 0, w, h * 0.12, fill=accent)
        c.rect(0, h * 0.88, w, h, fill=accent)
        c.ellipse(w / 2 - w * 0.17, h * 0.17, w / 2 + w * 0.17, h * 0.27, fill="#3E2A16")  # 手かけの穴
        c.text(w / 2, h * 0.40, title, min(h * 0.12, w * 0.14), accent, 900, max_w=w * 0.9)
        c.text(w / 2, h * 0.53, count, h * 0.07, INK, 800, max_w=w * 0.9)
        c.paragraph(w * 0.08, h * 0.61, w * 0.80, side_note, min(h * 0.032, 5.5), INK, 600)
        c.recycle(w * 0.88, h * 0.80, min(w, h) * 0.08, "段", INK)
        return c

    top = kraft(W, D, seed + 4)
    top.rect(0, D / 2 - 24, W, D / 2 + 24, fill=mix(KRAFT, "#E8D3B0", 0.45))  # 透明テープ
    top.rect(0, D / 2 - 1.0, W, D / 2 + 1.0, fill="#7A5634")  # フラップの合わせ目
    top.text(W / 2, D * 0.18, title + "  " + count, min(D * 0.08, 14), accent, 900, max_w=W * 0.9)
    top.text(W / 2, D * 0.84, "開けるときは カッターで中身を傷つけないようご注意ください", min(D * 0.04, 7), INK, 700,
             max_w=W * 0.9)
    bot = kraft(W, D, seed + 5)
    bot.rect(0, D / 2 - 1.0, W, D / 2 + 1.0, fill="#7A5634")
    faces = [big(W, H, seed, True), big(W, H, seed + 1, False), side(D, H, seed + 2), side(D, H, seed + 3), top, bot]
    return [_face(f.array(), "paper", seed + 10 + i, 1.0, 10) for i, f in enumerate(faces)]


def water_2l_case_6() -> Product:
    """天然水 2L × 6 本の段ボールケース（閉じた箱）。"""
    W, D, H = 295.0, 198.0, 318.0
    imgs = _carton(W, D, H, 6211, "天然水", "やわらかな口あたり  採水地 国内", "2L × 6本", "#1565C0",
                   "品名：ナチュラルミネラルウォーター\n内容量：2L×6本\n保存方法：直射日光・高温多湿を避けて保存",
                   "lake", (0.1, 0.1, 0.9, 0.9))
    return Product(slug="water_2l_case_6", name="天然水 2L × 6本 ケース", shape_class="box", category="beverage",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=12.6, material="paper",
                   description="形は 2L の角形ペットボトル 6 本（3 × 2）を入れた一般的な段ボールケース"
                               "（幅 295 mm・奥行き 198 mm・高さ 318 mm）で、寸法・質量は代表値。閉じた箱で、中身は無い。",
                   tags=["水", "天然水", "ミネラルウォーター", "2L", "ケース", "段ボール", "箱買い", "まとめ買い", "大容量",
                         "water", "case of water", "cardboard box"],
                   photos=["lake"], colors=Colors(label_base=KRAFT), images=imgs, faces=BOX_FACES)


def drink_cardboard_case_24() -> Product:
    """炭酸水 350ml 缶 × 24 本の段ボールケース（閉じた箱）。"""
    W, D, H = 404.0, 272.0, 125.0
    imgs = _carton(W, D, H, 6221, "炭酸水", "強炭酸  無糖・ゼロカロリー", "350ml × 24缶", "#00838F",
                   "品名：炭酸飲料\n内容量：350ml×24缶", "lemon", (0.15, 0.15, 0.85, 0.85))
    return Product(slug="drink_cardboard_case_24", name="炭酸水 350ml × 24缶 ケース", shape_class="box",
                   category="beverage", dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=9.2,
                   material="paper",
                   description="形は 350ml 缶 24 本（6 × 4）を入れた一般的な段ボールケース（幅 404 mm・奥行き 272 mm・"
                               "高さ 125 mm）で、寸法・質量は代表値。閉じた箱で、中身は無い。",
                   tags=["炭酸水", "缶", "350ml", "24本", "ケース", "段ボール", "箱買い", "まとめ買い", "大容量",
                         "sparkling water", "case of cans", "cardboard box"],
                   photos=["lemon"], colors=Colors(label_base=KRAFT), images=imgs, faces=BOX_FACES)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    pork_komagire_tray, chicken_thigh_tray, ground_meat_tray, sashimi_assorted_tray, salmon_fillet_tray, egg_10pack,
    fried_food_pack, sushi_pack, bento_large, rice_bag_10kg, water_2l_case_6, drink_cardboard_case_24)}
