"""架空の商品のデザイン: 既存の売場に足す商品（冷凍食品・酒・菓子・調味料と粉・乾めんと飲料・日用品とペット用品）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
形は近い既存の商品（袋・箱・PET ボトル・瓶・カップ）をもとに、寸法とラベルを変えた。背の高い瓶・ボトルは、
キャップを別の剛体にせず、胴とキャップの輪郭を 1 つの回転体にする既存の作り方のまま（キャップが別だと倒れて落ちる）。
写真のない絵（たこ焼き・ピザ・枝豆・ポップコーン・クラッカー・犬など）は手続きで描く。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .conv_drinks import ALCOHOL_NOTE, _alcohol_mark
from .drinks_large import _big_pet
from .food_fresh_snack import _back_panel, _pouch
from .food_pantry import _squeeze_bottle
from .forms import RevolveForm, _arc
from .household_cleaning import _info
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _bottle_back, _face, back_info, seal_crimp, steam

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}
POUCH_FACES = {"front": 0, "back": 1}
WHITE = "#FFFFFF"
FROZEN = "-18℃以下で保存してください"


# ---------------------------------------------------------------- 共通の部品


def _bag_back(b: Canvas, W: float, H: float, top: float, rows, size: float, nutrition, sections, accent: str,
              sub: str = "袋", mark: str = "プラ"):
    """袋の裏面: 白いパネルに一括表示・栄養成分表示・見出し付きの文、下にバーコードと識別表示。"""
    b.rect(12, top, W - 12, H - 20, fill=WHITE, radius=3)
    _back_panel(b, 17, top + 4, W - 17, H - 52, rows, size, nutrition, sections, accent)
    b.barcode(18, H - 47, 42, 24)
    b.recycle(W - 34, H - 36, 12, mark, accent, sub=sub)


def _paper_bag(c: Canvas, seed: int, shade: int = 22):
    """紙袋（小麦粉・ドッグフードの外袋など）の仕上げ。"""
    return trim_safe(edge_shade(finish(c.array(), "paper", seed, 1.0), shade, 0.16))


def _shouldered_bottle(H: float, D: float, *, sh_z: float, sh_top: float, neck_r: float, cap_h: float, cap_r: float,
                       label: tuple[float, float], liquid_top: float | None = None) -> RevolveForm:
    """一升瓶・梅酒の瓶のような、直胴 → なだらかな肩 → 細い首 → 口の玉縁 → キャップの瓶。
    キャップは胴と同じ輪郭の続き（1 つの回転体）にする。"""
    R = D / 2
    cap_z = H - cap_h
    body = [(0.0, R * 0.86)] + _arc(0.0005, 0.009, R * 0.92, R, 10, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, sh_top, R, neck_r * 1.06, 40, "cos")[1:]
    body += [(cap_z - 0.008, neck_r), (cap_z - 0.006, neck_r * 1.10), (cap_z - 0.003, neck_r * 1.10), (cap_z, neck_r)]
    cap = [(cap_z, cap_r), (H - 0.0012, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, label, liquid_top)


def _cap_top(form: RevolveForm, color: str, ring: str, text: str, ink: str, seed: int):
    t = top_canvas(form, color, seed=seed)
    d = t.w_mm
    t.gradient(0, 0, d, d, mix(color, WHITE, 0.15), mix(color, "#000000", 0.15))
    t.ellipse(0.6, 0.6, d - 0.6, d - 0.6, outline=mix(color, "#000000", 0.35), width=0.6)
    t.ellipse(d * 0.18, d * 0.18, d * 0.82, d * 0.82, outline=ring, width=0.5)
    t.text(d / 2, d / 2, text, d * 0.22, ink, 900, max_w=d * 0.6)
    return finish(t.array(), "film", seed, 0.5)


def _takoyaki(c: Canvas, cx: float, cy: float, r: float):
    """たこ焼き 1 個（ソース・マヨネーズ・青のり・かつお節）。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#B8702F")
    c.ellipse(cx - r * 0.9, cy - r * 0.6, cx + r * 0.8, cy + r * 0.85, fill="#D18D44")
    c.ellipse(cx - r * 0.92, cy - r * 0.96, cx + r * 0.92, cy + r * 0.2, fill="#4E220E")
    c.ellipse(cx - r * 0.5, cy - r * 0.8, cx + r * 0.1, cy - r * 0.5, fill="#7A3A1A")
    pts = [(cx - r * 0.75 + k * r * 0.3, cy - r * 0.55 + (k % 2) * r * 0.32) for k in range(6)]
    c.line(pts, "#FFF6DA", r * 0.13)
    for _ in range(7):
        a, d = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, r * 0.75)
        x, y = cx + d * math.cos(a), cy - r * 0.35 + d * 0.6 * math.sin(a)
        c.ellipse(x - r * 0.06, y - r * 0.06, x + r * 0.06, y + r * 0.06, fill="#3E7A28")
    for _ in range(3):  # かつお節
        x, y = cx + c.rng.uniform(-r * 0.5, r * 0.5), cy - r * 0.5 + c.rng.uniform(-r * 0.2, r * 0.3)
        c.polygon([(x, y), (x + r * 0.28, y - r * 0.08), (x + r * 0.22, y + r * 0.12), (x - r * 0.04, y + r * 0.14)],
                  fill="#E7B78E")


def _pizza(c: Canvas, cx: float, cy: float, r: float, slices: int = 8):
    """ミックスピザ（上から見た丸い絵）。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#C98A3E")
    c.ellipse(cx - r * 0.97, cy - r * 0.97, cx + r * 0.95, cy + r * 0.95, fill="#DDA455")
    c.ellipse(cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86, fill="#C2412B")
    for _ in range(26):  # とけたチーズ
        a, d = c.rng.uniform(0, 2 * math.pi), c.rng.uniform(0, r * 0.68)
        x, y, s = cx + d * math.cos(a), cy + d * math.sin(a), c.rng.uniform(r * 0.12, r * 0.24)
        c.ellipse(x - s, y - s * 0.8, x + s, y + s * 0.8, fill=mix("#F7D879", "#FFF1C2", c.rng.random() * 0.6))
    for k in range(9):  # サラミ
        a, d = k * 2 * math.pi / 9 + c.rng.uniform(-0.2, 0.2), r * (0.32 if k % 3 == 0 else 0.62)
        x, y, s = cx + d * math.cos(a), cy + d * math.sin(a), r * 0.13
        c.ellipse(x - s, y - s, x + s, y + s, fill="#A3271E", outline="#7E1A14", width=r * 0.015)
        c.ellipse(x - s * 0.4, y - s * 0.5, x - s * 0.1, y - s * 0.2, fill="#C9473A")
    for k in range(7):  # ピーマンの輪
        a, d = k * 2 * math.pi / 7 + 0.4, r * c.rng.uniform(0.2, 0.7)
        x, y, s = cx + d * math.cos(a), cy + d * math.sin(a), r * 0.09
        c.ellipse(x - s, y - s * 0.7, x + s, y + s * 0.7, outline="#2F7D2A", width=r * 0.03)
    for k in range(slices):  # 切れ目
        a = k * 2 * math.pi / slices
        c.line([(cx, cy), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))], mix("#C2412B", "#5A1A10", 0.4),
               r * 0.012)


def _edamame(c: Canvas, x: float, y: float, ang: float, s: float):
    """枝豆のさや（豆 3 粒のふくらみ）。ang は向き [度]。"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    pts = [(x + ux * s * k * 0.75, y + uy * s * k * 0.75) for k in range(3)]
    c.line(pts, "#6E9E34", s * 0.8)
    for k, (px, py) in enumerate(pts):
        c.ellipse(px - s * 0.45, py - s * 0.45, px + s * 0.45, py + s * 0.45, fill="#7FB03E")
        c.ellipse(px - s * 0.3, py - s * 0.32, px + s * 0.05, py - s * 0.05, fill="#A6CF63")
    ex, ey = pts[-1]
    c.line([(ex, ey), (ex + ux * s * 0.7, ey + uy * s * 0.7)], "#5B8A2B", s * 0.15)


def _popcorn(c: Canvas, cx: float, cy: float, s: float):
    """ポップコーン 1 粒（白い房の集まり、少し黄色い芯）。"""
    for k in range(5):
        a = k * 2 * math.pi / 5 + c.rng.uniform(-0.3, 0.3)
        x, y, rr = cx + s * 0.38 * math.cos(a), cy + s * 0.38 * math.sin(a), s * c.rng.uniform(0.32, 0.42)
        c.ellipse(x - rr, y - rr, x + rr, y + rr, fill=mix("#FFF8E2", "#FBE9B0", c.rng.random() * 0.5),
                  outline="#E4C877", width=s * 0.03)
    c.ellipse(cx - s * 0.18, cy - s * 0.18, cx + s * 0.18, cy + s * 0.18, fill="#F1C24E")


def _cracker(c: Canvas, x: float, y: float, w: float, h: float):
    """四角いクラッカー（焼き色・空気穴）。"""
    c.rect(x, y, x + w, y + h, fill="#C98A3A", radius=min(w, h) * 0.12)
    c.rect(x + w * 0.04, y + h * 0.04, x + w * 0.96, y + h * 0.94, fill="#E0AA55", radius=min(w, h) * 0.1)
    for i in range(4):
        for j in range(3):
            px, py = x + w * (0.2 + 0.2 * i), y + h * (0.25 + 0.25 * j)
            c.ellipse(px - w * 0.025, py - w * 0.025, px + w * 0.025, py + w * 0.025, fill="#A9692A")
    for _ in range(6):
        px, py = x + c.rng.uniform(0.1, 0.9) * w, y + c.rng.uniform(0.1, 0.9) * h
        c.ellipse(px - w * 0.012, py - w * 0.012, px + w * 0.012, py + w * 0.012, fill="#FFF4D8")


def _dog(c: Canvas, cx: float, cy: float, s: float):
    """犬の顔のイラスト（たれ耳・マズル・舌）。s は顔の幅 [mm]。"""
    tan, dark, cream = "#D9A066", "#8A5A2B", "#FBEBD2"
    c.ellipse(cx - s * 0.62, cy - s * 0.35, cx - s * 0.28, cy + s * 0.35, fill=dark)
    c.ellipse(cx + s * 0.28, cy - s * 0.35, cx + s * 0.62, cy + s * 0.35, fill=dark)
    c.ellipse(cx - s * 0.45, cy - s * 0.5, cx + s * 0.45, cy + s * 0.45, fill=tan)
    c.ellipse(cx - s * 0.28, cy - s * 0.02, cx + s * 0.28, cy + s * 0.42, fill=cream)
    for k in (-1, 1):
        ex = cx + k * s * 0.18
        c.ellipse(ex - s * 0.06, cy - s * 0.2, ex + s * 0.06, cy - s * 0.07, fill="#2A1A10")
        c.ellipse(ex - s * 0.025, cy - s * 0.18, ex + s * 0.01, cy - s * 0.14, fill=WHITE)
    c.ellipse(cx - s * 0.09, cy + s * 0.04, cx + s * 0.09, cy + s * 0.15, fill="#2A1A10")
    c.line([(cx, cy + s * 0.15), (cx, cy + s * 0.22)], "#2A1A10", s * 0.02)
    c.line([(cx - s * 0.12, cy + s * 0.26), (cx, cy + s * 0.22), (cx + s * 0.12, cy + s * 0.26)], "#2A1A10", s * 0.02)
    c.ellipse(cx - s * 0.06, cy + s * 0.25, cx + s * 0.06, cy + s * 0.37, fill="#E86A7A")


def _kibble(c: Canvas, x0: float, y0: float, x1: float, y1: float, n: int, s: float):
    for _ in range(n):
        x, y = c.rng.uniform(x0 + s, x1 - s), c.rng.uniform(y0 + s, y1 - s)
        col = mix("#8B5A2B", "#5E3A1A", c.rng.random())
        c.ellipse(x - s, y - s * 0.85, x + s, y + s * 0.85, fill=col)
        c.ellipse(x - s * 0.5, y - s * 0.5, x - s * 0.1, y - s * 0.15, fill=mix(col, WHITE, 0.25))


def _flower(c: Canvas, cx: float, cy: float, r: float, petal: str, center: str = "#F6C945"):
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        x, y = cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a)
        c.ellipse(x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45, fill=petal)
    c.ellipse(cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3, fill=center)


def _tea_cup(c: Canvas, cx: float, cy: float, s: float, liquid: str, line: str):
    """受け皿付きのティーカップ（ストレートティー）。s は幅の目安 [mm]。"""
    c.ellipse(cx - s, cy + s * 0.55, cx + s, cy + s * 0.9, fill=WHITE, outline=line, width=0.5)
    c.polygon([(cx - s * 0.72, cy - s * 0.4), (cx + s * 0.72, cy - s * 0.4), (cx + s * 0.5, cy + s * 0.62),
               (cx - s * 0.5, cy + s * 0.62)], fill=WHITE, outline=line)
    c.ellipse(cx - s * 0.72, cy - s * 0.56, cx + s * 0.72, cy - s * 0.24, fill=liquid, outline=line, width=0.5)
    c.ellipse(cx + s * 0.55, cy - s * 0.2, cx + s * 1.0, cy + s * 0.28, outline=line, width=0.9)
    steam(c, cx, cy - s * 0.7, s * 0.7, s * 0.6, mix(line, WHITE, 0.4), 0.6)


# ================================================================ 冷凍食品


def frozen_udon_5pack() -> Product:
    """冷凍うどん 5 食入り（立てたピロー袋）。表に丼のうどんの写真、裏に作り方。"""
    W, H = 230.0, 320.0
    blue, navy, white, yellow = "#1E5BB0", "#0E2D5E", WHITE, "#FFD54F"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 6, blue, seed=seed)
        c.gradient(0, 0, W, H, "#2B6CC4", "#123E7E")
        c.pattern(0, 0, W, H, "waves", mix(blue, white, 0.12), 14, 0.5)
        seal_crimp(c, 0, 0, W, 13, "#2B6CC4", 1.6)
        seal_crimp(c, 0, H - 13, W, H, "#123E7E", 1.6)
        return c

    c = base(5801)
    c.rect(0, 13, W, 32, fill=navy)
    c.text(W / 2, 22.5, "冷凍食品  " + FROZEN.replace("してください", ""), 6.0, yellow, 800, max_w=W - 16)
    c.text(W / 2, 52, "コシのある讃岐風", 10, white, 900)
    c.text(W / 2, 84, "うどん", 34, white, 900, stroke=1.0, stroke_fill=navy)
    c.text(W / 2, 108, "UDON NOODLES", 6.0, yellow, 800, spacing=1.6)
    c.ellipse(18, 118, W - 18, 252, fill="#F4EEE2")
    c.photo("udon", 26, 126, W - 26, 244, shape="ellipse", feather=3, crop=(0.08, 0.08, 0.92, 0.92))
    c.ellipse(W - 74, 228, W - 10, 292, fill=yellow)
    c.text(W - 42, 250, "5食入", 11, navy, 900)
    c.text(W - 42, 267, "1食180g", 6.0, navy, 800)
    c.rect(14, 262, 146, 292, fill=white, radius=4)
    c.text(80, 270.5, "凍ったまま ゆでて約1分", 6.0, blue, 900, max_w=126)
    c.text(80, 283, "電子レンジ 600W 約3分30秒", 5.2, INK, 700, max_w=126)
    c.text(14, 256, "※写真は調理例です", 3.4, white, 500, anchor="lm")
    front = _pouch(c, 5801)

    b = base(5802)
    b.text(W / 2, 23, "讃岐風うどん 5食入（900g）", 7.0, white, 900)
    _bag_back(b, W, H, 33, [
        ("名称", "冷凍ゆでうどん"), ("原材料名", "小麦粉（国内製造）、食塩／加工でん粉、酸味料、（一部に小麦を含む）"),
        ("内容量", "900g（180g×5食）"), ("賞味期限", "上部に記載"), ("保存方法", FROZEN)], 4.6,
        [("栄養成分表示 1食（180g）当たり", ""), ("エネルギー", "234kcal"), ("たんぱく質", "5.9g"), ("脂質", "0.8g"),
         ("炭水化物", "50.8g"), ("食塩相当量", "0.6g")],
        [("作り方", "沸騰したお湯に凍ったままのうどんを入れ、約1分ゆでてほぐします。電子レンジは袋から出して耐熱容器に入れ、"
                    "ラップをかけて600Wで約3分30秒温めてください。"),
         ("ご注意", "一度とけたものを再び凍らせると品質が変わります。")], blue)
    back = _pouch(b, 5802)
    return Product(slug="frozen_udon_5pack", name="冷凍うどん 5食入 900g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.085), mass_kg=0.93, material="film",
                   description="形は一般的な 5 食入りの冷凍うどんの袋（ピロー包装 高さ 320 mm・幅 230 mm・厚さ 85 mm）で、寸法・質量は代表値。"
                               "中の個包装 5 食は省略し、1 つの袋にした。",
                   tags=["うどん", "冷凍うどん", "冷凍食品", "冷凍", "5食入", "袋", "frozen udon", "udon", "frozen food"],
                   photos=["udon"], colors=Colors(label_base=blue), images=[front, back], faces=POUCH_FACES)


def frozen_takoyaki_bag() -> Product:
    """冷凍たこ焼き 20 個入り（立てたピロー袋）。舟皿に盛ったたこ焼きの絵（手続きで描く）。"""
    W, H = 210.0, 280.0
    orange, dark, cream, green = "#E8661E", "#5A1E08", "#FFF3DC", "#3E7A28"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 7, orange, seed=seed)
        c.gradient(0, 0, W, H, "#F07A2C", "#B8420E")
        c.pattern(0, 0, W, H, "dots", mix(orange, "#FFFFFF", 0.18), 8, 0.4)
        seal_crimp(c, 0, 0, W, 13, "#F07A2C", 1.6)
        seal_crimp(c, 0, H - 13, W, H, "#B8420E", 1.6)
        return c

    c = base(5811)
    c.rect(0, 13, W, 31, fill=dark)
    c.text(W / 2, 22, "冷凍食品  大粒のたこ入り", 6.0, "#FFD27A", 800)
    c.text(W / 2, 56, "大阪風", 11, cream, 900)
    c.text(W / 2, 84, "たこ焼", 30, WHITE, 900, stroke=1.0, stroke_fill=dark)
    c.rect(22, 112, W - 22, 214, fill=cream, radius=10)
    c.polygon([(34, 150), (W - 34, 150), (W - 46, 204), (46, 204)], fill="#D8B27A", outline="#A57D45")  # 舟皿
    for i, x in enumerate((62, 92, 122, 152)):
        _takoyaki(c, x, 182, 15)
    for x in (77, 107, 137):
        _takoyaki(c, x, 160, 15)
    c.text(W / 2, 125, "外はカリッと 中はとろ〜り", 6.4, dark, 900)
    c.text(28, 210, "※盛りつけ例", 3.2, dark, 500, anchor="lm")
    c.ellipse(W - 70, 204, W - 12, 262, fill="#FFD27A")
    c.text(W - 41, 224, "20個入", 9.0, dark, 900)
    c.text(W - 41, 240, "400g", 7.0, dark, 900)
    c.rect(14, 226, 128, 254, fill=WHITE, radius=4)
    c.text(71, 234, "電子レンジで 簡単調理", 5.4, orange, 900)
    c.text(71, 246, "ソース・青のり付き", 5.0, INK, 700)
    front = _pouch(c, 5811)

    b = base(5812)
    b.text(W / 2, 22, "大阪風たこ焼 20個入", 7.0, WHITE, 900)
    _bag_back(b, W, H, 32, [
        ("名称", "冷凍たこ焼"), ("原材料名", "小麦粉（国内製造）、たこ、キャベツ、全卵、天かす、紅しょうが、ねぎ、だし／"
                                         "膨張剤、調味料（アミノ酸等）、（一部に小麦・卵・大豆を含む）"),
        ("内容量", "400g（20個）、ソース・青のり付き"), ("賞味期限", "上部に記載"), ("保存方法", FROZEN)], 4.0,
        [("栄養成分表示 5個（100g）当たり", ""), ("エネルギー", "158kcal"), ("たんぱく質", "5.2g"), ("脂質", "5.6g"),
         ("炭水化物", "21.8g"), ("食塩相当量", "1.1g")],
        [("作り方", "凍ったまま耐熱皿に並べ、ラップをかけずに 600W で 10個 約4分温めます。ソースと青のりをかけてお召し上がりください。")],
        orange)
    back = _pouch(b, 5812)
    return Product(slug="frozen_takoyaki_bag", name="冷凍たこ焼 20個入 400g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.050), mass_kg=0.42, material="film",
                   description="形は一般的な袋入りの冷凍たこ焼（ピロー包装 高さ 280 mm・幅 210 mm・厚さ 50 mm）で、寸法・質量は代表値。"
                               "たこ焼の絵は手続きで描いた。",
                   tags=["たこ焼", "たこ焼き", "冷凍食品", "冷凍", "袋", "frozen takoyaki", "takoyaki", "frozen food"],
                   photos=[], colors=Colors(label_base=orange), images=[front, back], faces=POUCH_FACES)


def frozen_pizza_box() -> Product:
    """冷凍ピザ 2 枚入り（平たい紙箱。上面に丸いピザの絵、側面は帯）。冷凍ケースに平置きする。"""
    W, D, H = 230.0, 230.0, 40.0
    red, green, cream, dark = "#C62828", "#2E7D32", "#FFF6E3", "#3A0E0A"
    s = 6

    def band(w: float, seed: int) -> Canvas:
        f = Canvas(w, H, s, red, seed)
        f.gradient(0, 0, w, H, "#D63A2E", "#9E1B14")
        f.rect(0, 0, w, 3, fill=green)
        f.rect(0, 3, w, 5, fill=WHITE)
        f.rect(0, H - 3, w, H, fill=green)
        return f

    fr = band(W, 5821)
    fr.text(W / 2 - 22, 17, "ミックスピザ", 14, WHITE, 900, max_w=120)
    fr.text(W / 2 - 22, 30, "MIXED PIZZA  直径 20cm × 2枚", 5.0, "#FFE08A", 800, max_w=120)
    fr.rect(W - 74, 9, W - 8, 33, fill=cream, radius=4)
    fr.text(W - 41, 16.5, "冷凍食品", 5.0, red, 900)
    fr.text(W - 41, 26.5, "2枚入 440g", 6.0, INK, 900)
    bk = band(W, 5822)
    bk.rect(4, 6, W - 4, H - 4, fill=cream, radius=1.5)
    back_info(bk, 6, 7, 128, [
        ("名称", "冷凍ピザ"), ("原材料名", "小麦粉、ナチュラルチーズ、トマトペースト、サラミ、ピーマン、玉ねぎ／"
                                       "膨張剤、調味料（アミノ酸）、（一部に小麦・乳成分・豚肉を含む）"),
        ("内容量", "440g（2枚）"), ("保存方法", FROZEN)], 2.0)
    bk.barcode(136, 8, 34, 22)
    bk.recycle(186, 18, 10, "紙", red, sub="箱")
    bk.recycle(205, 18, 10, "プラ", red, sub="袋")
    sides = []
    for k, seed in enumerate((5823, 5824)):
        sd = band(D, seed)
        sd.text(D / 2, 18, "ミックスピザ 2枚入", 9.0, WHITE, 900)
        sd.text(D / 2, 30, "賞味期限 2027.08.31" if k else "オーブントースター 約6分", 5.0, "#FFE08A", 800)
        sides.append(sd.array())

    tp = Canvas(W, D, s, cream, 5825)
    tp.gradient(0, 0, W, D, "#FFF9EE", "#F5E3C0")
    tp.rect(0, 0, W, 26, fill=red)
    tp.rect(0, 26, W, 29, fill=green)
    tp.text(W / 2, 13, "ミックスピザ", 15, WHITE, 900)
    tp.ellipse(18, 40, 172, 194, fill="#E9D7B4")
    _pizza(tp, 95, 117, 72)
    tp.text(95, 202, "※写真ではなく盛りつけ例の絵です", 3.4, dark, 500)
    tp.ellipse(158, 152, 222, 216, fill=red)
    tp.text(190, 172, "2枚入", 9.0, WHITE, 900)
    tp.text(190, 188, "20cm", 7.0, "#FFE08A", 900)
    tp.rect(176, 40, 224, 76, fill=WHITE, radius=4)
    tp.text(200, 50, "チーズ", 6.0, red, 900)
    tp.text(200, 60, "たっぷり", 6.0, red, 900)
    tp.text(200, 70, "4種類", 4.4, INK, 800)
    tp.rect(176, 84, 224, 130, fill=green, radius=4)
    tp.text(200, 95, "トースター", 4.6, WHITE, 900)
    tp.text(200, 106, "約6分", 8.0, WHITE, 900)
    tp.text(200, 119, "凍ったまま", 4.2, WHITE, 800)
    tp.text(W / 2, D - 7, FROZEN, 4.0, dark, 700)

    bt = Canvas(W, D, s, cream, 5826)
    bt.gradient(0, 0, W, D, "#FFF9EE", "#F0DFC0")
    bt.text(W / 2, 12, "おいしい焼き方", 7.0, red, 900)
    bt.paragraph(14, 22, W - 14, "1. 袋から出し、凍ったままオーブントースター（1000W）で約6分、チーズがとけるまで焼きます。\n"
                                 "2. オーブンの場合は 220℃に予熱し、約8分焼いてください。\n"
                                 "3. 電子レンジは 600W で約2分30秒。焼き色は付きません。", 4.4, INK, 500)
    back_info(bt, 14, 82, W - 14, [("栄養成分表示 1枚（220g）当たり", "")], 3.6,
              [("エネルギー", "552kcal"), ("たんぱく質", "22.4g"), ("脂質", "21.1g"), ("炭水化物", "68.0g"),
               ("食塩相当量", "3.0g")], dark)
    bt.text(W / 2, D - 12, NOTICE, 3.2, dark, 500, max_w=W - 20)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 5831 + i) for i, a in enumerate(imgs)]
    return Product(slug="frozen_pizza_box", name="冷凍ミックスピザ 2枚入 440g", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.48, material="paper",
                   description="形は一般的な冷凍ピザの平たい紙箱（幅 230 mm・奥行き 230 mm・高さ 40 mm、直径 20 cm のピザ 2 枚入り）で、"
                               "寸法・質量は代表値。上面に手続きで描いたピザの絵。冷凍ケースに平置きする。",
                   tags=["ピザ", "冷凍ピザ", "冷凍食品", "冷凍", "箱", "frozen pizza", "pizza", "frozen food"],
                   photos=[], colors=Colors(label_base=red), images=imgs, faces=BOX_FACES)


def frozen_edamame_bag() -> Product:
    """冷凍枝豆 400g（立てたピロー袋、中身の見える窓に枝豆の絵）。"""
    W, H = 190.0, 260.0
    green, dark, cream, yellow = "#3E8E2F", "#1B4A14", "#F6FBEA", "#F5D33C"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 7, green, seed=seed)
        c.gradient(0, 0, W, H, "#4FA23B", "#24631C")
        seal_crimp(c, 0, 0, W, 12, "#4FA23B", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#24631C", 1.6)
        return c

    c = base(5841)
    c.rect(0, 12, W, 29, fill=dark)
    c.text(W / 2, 20.5, "冷凍食品  塩ゆで済み", 6.0, yellow, 800)
    c.text(W / 2, 54, "えだまめ", 26, WHITE, 900, stroke=0.9, stroke_fill=dark)
    c.text(W / 2, 76, "EDAMAME  ほどよい塩味", 6.0, yellow, 800)
    c.rect(20, 88, W - 20, 196, fill="#E9F3D8", radius=12)  # 窓（中身が見える）
    pods = [(36, 112, 20), (70, 104, -15), (104, 116, 30), (128, 102, 5), (44, 146, -30), (82, 140, 15),
            (118, 150, -10), (148, 132, 60), (36, 176, 10), (72, 172, -40), (108, 182, 20), (140, 170, -20)]
    for x, y, a in pods:
        _edamame(c, x, y, a, 10)
    c.rect(20, 88, W - 20, 196, outline=WHITE, width=1.2, radius=12)
    c.text(W / 2, 202, "※中身が見える窓です", 3.2, WHITE, 500)
    c.ellipse(W - 70, 190, W - 12, 248, fill=yellow)
    c.text(W - 41, 212, "400g", 11, dark, 900)
    c.text(W - 41, 228, "大袋", 6.0, dark, 900)
    c.rect(14, 214, 120, 244, fill=WHITE, radius=4)
    c.text(67, 223, "流水解凍 約5分", 5.6, green, 900)
    c.text(67, 235, "電子レンジ 600W 約4分", 5.0, INK, 700, max_w=100)
    front = _pouch(c, 5841)

    b = base(5842)
    b.text(W / 2, 20.5, "えだまめ（塩ゆで）400g", 7.0, WHITE, 900)
    _bag_back(b, W, H, 31, [
        ("名称", "冷凍えだまめ"), ("原材料名", "えだまめ（台湾産）、食塩"), ("内容量", "400g"),
        ("賞味期限", "上部に記載"), ("保存方法", FROZEN)], 4.0,
        [("栄養成分表示 100g（さやを除く可食部）当たり", ""), ("エネルギー", "143kcal"), ("たんぱく質", "13.0g"),
         ("脂質", "7.6g"), ("炭水化物", "8.9g"), ("食塩相当量", "0.9g")],
        [("解凍のしかた", "必要な量をざるに取り、流水で約5分解凍します。電子レンジは耐熱皿にのせ、ラップをかけて600Wで200g約4分。")],
        green)
    back = _pouch(b, 5842)
    return Product(slug="frozen_edamame_bag", name="冷凍えだまめ 塩ゆで 400g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.050), mass_kg=0.41, material="film",
                   description="形は一般的な袋入りの冷凍えだまめ（ピロー包装 高さ 260 mm・幅 190 mm・厚さ 50 mm）で、寸法・質量は代表値。"
                               "窓の中の枝豆は手続きで描いた絵。",
                   tags=["えだまめ", "枝豆", "冷凍野菜", "冷凍食品", "冷凍", "袋", "frozen edamame", "edamame",
                         "frozen vegetables"],
                   photos=[], colors=Colors(label_base=green), images=[front, back], faces=POUCH_FACES)


# ================================================================ 酒


def beer_can_6pack() -> Product:
    """ビール 350ml 缶の 6 缶パック（2 × 3 本を包む紙のカートン）。側面の口から缶が見え、上面に指を入れる穴。"""
    W, D, H = 203.0, 136.0, 123.0
    gold, navy, cream = "#D8A533", "#14284B", "#FFF6DC"
    s = 6

    def board(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, navy, seed)
        f.gradient(0, 0, w, h, "#1C3A6B", "#0E1D38")
        f.pattern(0, 0, w, h, "dots", mix(navy, gold, 0.18), 5, 0.4)
        return f

    fr = board(W, H, 5851)
    fr.rect(0, 0, W, 12, fill=gold)
    fr.text(W / 2, 6, "PREMIUM LAGER  麦芽100%", 5.0, navy, 900, spacing=0.6)
    fr.ellipse(10, 20, 82, 92, fill=cream, outline=gold, width=1.0)
    for k in range(-2, 3):  # 麦の穂
        x = 46 + k * 8
        fr.line([(x, 84), (x + k * 1.2, 48)], navy, 0.7)
        for j in range(6):
            y = 50 + j * 5
            fr.ellipse(x - 2.4 + k * 0.9, y, x + 0.3 + k * 0.9, y + 4, fill=gold)
            fr.ellipse(x - 0.3 + k * 0.9, y + 1.8, x + 2.4 + k * 0.9, y + 5.8, fill=gold)
    fr.text(46, 32, "麦芽100%", 5.0, navy, 900)
    fr.text(142, 42, "ビール", 26, gold, 900)
    fr.text(142, 62, "BEER", 10, cream, 900, spacing=3.0)
    fr.rect(96, 72, 188, 88, fill=gold, radius=8)
    fr.text(142, 80, "350ml × 6缶", 8.0, navy, 900)
    fr.text(56, 104, "生  アルコール分5%", 5.4, cream, 800)
    _alcohol_mark(fr, 178, 104, 12)
    fr.rect(0, H - 6, W, H, fill=gold)
    bk = board(W, H, 5852)
    bk.rect(0, 0, W, 12, fill=gold)
    bk.text(W / 2, 6, "ビール 350ml × 6缶", 5.4, navy, 900)
    bk.rect(6, 16, 120, H - 10, fill=cream, radius=2)
    _bottle_back(bk, 63, 18, 110, "ビール", "麦芽（外国製造）、ホップ", 3.0, color=navy, bg=cream,
                 extra=[("内容量", "350ml × 6缶"), ("アルコール分", "5%"), ("賞味期限", "缶底に記載"),
                        ("保存方法", "直射日光・高温を避けてください")], notice_color=navy)
    bk.paragraph(126, 18, W - 6, ALCOHOL_NOTE, 3.0, cream, 700)
    bk.rect(130, 66, 196, 98, fill=WHITE)
    bk.barcode(134, 69, 58, 26)
    bk.recycle(144, 108, 10, "紙", cream, sub="パック")
    bk.recycle(164, 108, 10, "アルミ", cream, kind="can", sub="缶")
    _alcohol_mark(bk, 186, 108, 10)
    bk.rect(0, H - 6, W, H, fill=gold)

    sides = []
    for k, seed in enumerate((5853, 5854)):
        sd = Canvas(D, H, s, "#2A2A2A", seed)
        sd.rect(0, 0, D, H, fill="#1A1A1A")
        for i in range(2):  # 口から見える 2 本の缶の胴
            x0 = 2 + i * 66
            sd.gradient(x0, 8, x0 + 66, H - 6, "#F0C14E", "#B9831F")
            for j in range(11):
                t = j / 10
                sd.rect(x0 + 66 * t * 0.98, 8, x0 + 66 * t * 0.98 + 6, H - 6,
                        fill=mix("#B9831F", "#FFF2C8", 0.5 * math.sin(t * math.pi) ** 4))
            sd.rect(x0, 8, x0 + 66, 18, fill=navy)
            sd.text(x0 + 33, 13, "PREMIUM LAGER", 3.4, gold, 800)
            sd.text(x0 + 33, 60, "ビール", 9.0, navy, 900)
            sd.rect(x0, H - 14, x0 + 66, H - 6, fill=navy)
            sd.line([(x0 + 0.5, 8), (x0 + 0.5, H - 6)], "#6E4E12", 0.8)
        sd.rect(0, 0, D, 8, fill=navy)
        sd.text(D / 2, 4, "ビール 6缶パック" if k == 0 else "お酒は20歳になってから", 4.0, gold, 900)
        sd.rect(0, H - 6, D, H, fill=gold)
        sides.append(sd.array())

    tp = board(W, D, 5855)
    tp.text(W / 2, 16, "ビール  BEER", 9.0, gold, 900, spacing=1.0)
    tp.text(W / 2, 30, "350ml × 6缶  アルコール分5%", 5.4, cream, 800)
    for x in (W / 2 - 52, W / 2 + 22):  # 指を入れる穴（持ち手）
        tp.rect(x, 52, x + 30, 82, fill="#0A0A0A", radius=12)
        tp.rect(x - 1, 51, x + 31, 83, outline=gold, width=0.6, radius=12)
    tp.text(W / 2, 67, "持ち手", 4.4, cream, 800)
    tp.text(W / 2, 100, "↑ 持ち手に指を入れて持ち上げてください", 4.6, gold, 800)
    tp.text(W / 2, 116, ALCOHOL_NOTE[:13], 4.0, cream, 700)
    bt = board(W, D, 5856)
    bt.text(W / 2, D / 2 - 8, "ビール 350ml × 6缶", 8.0, gold, 900)
    bt.text(W / 2, D / 2 + 8, NOTICE, 3.6, cream, 500, max_w=W - 20)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 5861 + i) for i, a in enumerate(imgs)]
    return Product(slug="beer_can_6pack", name="ビール 350ml 6缶パック", shape_class="box", category="beverage",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=2.26, material="paper",
                   description="形は一般的な 350ml 缶 6 本（2 × 3 本）の紙のカートン（幅 203 mm・奥行き 136 mm・高さ 123 mm、"
                               "上面に指を入れる穴）で、寸法・質量は代表値。中の缶は個別の形にせず、側面の口から見える胴を絵で描いた 1 つの箱。",
                   tags=["ビール", "6缶パック", "6缶", "ケース", "お酒", "アルコール", "酒類", "beer", "six pack", "beer 6 pack",
                         "alcohol"],
                   photos=[], colors=Colors(label_base=navy), images=imgs, faces=BOX_FACES)


def sake_isshobin_1800ml() -> Product:
    """日本酒の一升瓶 1.8L（茶色のガラス・樹脂のキャップ）。和紙風のラベルに縦書き。"""
    form = _shouldered_bottle(0.395, 0.104, sh_z=0.245, sh_top=0.318, neck_r=0.0145, cap_h=0.034, cap_r=0.0168,
                              label=(0.050, 0.225))
    brown, washi, red, ink, gold = "#4A2A12", "#F5EEDC", "#A3241B", "#1A1A1A", "#B08A3E"
    c = label_canvas(form, brown, seed=5871)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#5A3418", "#3A200C")  # ラベルの外はガラスの色
    c.rect(fx - 44, 6, fx + 44, H - 8, fill=washi)
    for _ in range(140):  # 和紙の繊維
        x, y = c.rng.uniform(fx - 43, fx + 43), c.rng.uniform(7, H - 9)
        c.line([(x, y), (x + c.rng.uniform(-3, 3), y + c.rng.uniform(-1, 1))], mix(washi, "#C9B98F", 0.5), 0.2)
    c.rect(fx - 41, 9, fx + 41, H - 11, outline=red, width=0.8)
    c.vtext(fx + 8, 18, "清酒", 30, ink, 900, gap=0.1)
    c.vtext(fx + 8, 92, "辛口", 18, ink, 900, gap=0.1)
    c.rect(fx - 30, 18, fx - 16, 62, fill=red)
    c.vtext(fx - 23, 22, "純米酒", 9.0, washi, 900)
    c.vtext(fx - 23, 72, "米と米こうじだけ", 4.2, ink, 700)
    c.ellipse(fx + 22, 130, fx + 38, 146, fill=red)
    c.text(fx + 30, 138, "吟", 9.0, washi, 900)
    c.text(fx, H - 22, "1800ml  アルコール分15度", 4.6, ink, 900)
    c.text(fx, H - 15, "SAKE  JUNMAI  KARAKUCHI", 3.2, red, 800, spacing=0.5)
    c.rect(bx - 30, 50, bx + 30, H - 8, fill=washi)
    back_info(c, bx - 28, 52, bx + 28, [("品目", "日本酒"), ("原材料名", "米（国産）、米こうじ（国産米）"),
                                         ("精米歩合", "60%"), ("内容量", "1800ml"), ("アルコール分", "15度"),
                                         ("製造年月", "キャップに記載")], 2.2, None, ink, washi)
    c.paragraph(bx - 28, 110, bx + 28, ALCOHOL_NOTE, 2.0, ink, 600)
    c.barcode(bx - 14, 136, 28, 16)
    c.text(bx, 158, "要冷蔵ではありません", 2.2, ink, 600)
    c.recycle(bx - 8, 30, 8, "プラ", washi, sub="キャップ")
    c.text(bx + 10, 30, "茶色のびんは資源ごみ", 2.4, washi, 700, anchor="lm")
    _alcohol_mark(c, bx, 16, 10)
    label = finish(c.array(), "paper", 5871, 0.5)
    top = _cap_top(form, "#C9A23E", brown, "清酒", brown, 5872)
    return Product(slug="sake_isshobin_1800ml", name="日本酒 純米酒 辛口 一升瓶 1.8L", category="beverage", mass_kg=2.75,
                   capacity_ml=1800, material="glass (opaque brown)",
                   description="形は一般的な一升瓶（1.8L、高さ 395 mm・胴径 104 mm、なだらかな肩と細い首、樹脂のキャップ）で、寸法・質量は代表値。"
                               "茶色のガラスで中身はほとんど見えないため、不透明の瓶として作った。キャップは胴と同じ輪郭の続きで、別の剛体にしない。",
                   tags=["日本酒", "清酒", "純米酒", "一升瓶", "1.8L", "お酒", "酒類", "瓶", "sake", "isshobin",
                         "sake bottle", "alcohol"],
                   photos=[], colors=Colors(cap="#C9A23E", label_base=brown), **revolve(form, label=label, top=top))


def shochu_pet_2700ml() -> Product:
    """焼酎の 2.7L 角形 PET ボトル（無色の中身、グリップのくびれ）。"""
    form = _big_pet(0.300, 0.122, shoulder_h=0.060, label=(0.110, 0.192), liquid_top=0.250,
                    grip=(0.040, 0.100), neck_r=0.0150, cap_h=0.024, cap_r=0.0185, square=5.0)
    white, navy, blue, gold = WHITE, "#13294B", "#2F5DA8", "#C9A23E"
    c = label_canvas(form, white, seed=5881)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#E6EEF8")
    c.rect(0, 0, W, 7, fill=navy)
    c.rect(0, H - 7, W, H, fill=navy)
    c.text(fx, 3.5, "SHOCHU  25%  2.7L", 3.6, gold, 800, spacing=1.0)
    c.rect(fx - 34, 10, fx + 34, H - 10, fill=WHITE, outline=navy, width=0.6, radius=3)
    c.vtext(fx + 12, 14, "焼酎", 22, navy, 900, gap=0.1)
    c.vtext(fx - 10, 14, "すっきり", 7.0, blue, 900)
    c.vtext(fx - 22, 14, "甲類", 7.0, navy, 900)
    c.text(fx - 16, 62, "25度", 7.0, navy, 900)
    c.text(fx, H - 13.5, "大容量 2700ml", 4.6, navy, 900)
    _alcohol_mark(c, fx + 26, 62, 9)
    c.rect(bx - 36, 3, bx + 36, H - 3, fill=WHITE, radius=2)
    _bottle_back(c, bx, 5, 68, "焼酎甲類", "糖蜜（外国製造）", 2.3,
                 extra=[("内容量", "2700ml"), ("アルコール分", "25度"), ("製造", "架空の酒造 株式会社")])
    c.paragraph(bx - 33, 46, bx + 33, ALCOHOL_NOTE, 2.0, INK, 600)
    c.rect(0.5 * W - 18, 4, 0.5 * W + 18, H - 4, fill=WHITE, radius=2)
    c.barcode(0.5 * W - 15, 8, 30, 18)
    c.recycle(0.5 * W - 8, 40, 10, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 8, 40, 10, "プラ", INK, sub="ラベル")
    c.text(0.5 * W, H - 12, "水割り・お湯割り", 2.6, navy, 800)
    c.text(0.5 * W, H - 8, "炭酸割りに", 2.6, navy, 800)
    label = finish(c.array(), "film", 5881, 0.8)
    return Product(slug="shochu_pet_2700ml", name="焼酎甲類 25度 2.7L", category="beverage", mass_kg=2.68,
                   capacity_ml=2700, material="PET",
                   description="形は一般的な 2.7L の焼酎の角形 PET ボトル（高さ 300 mm・胴の幅 122 mm、下部にグリップのくびれ）で、"
                               "寸法・質量は代表値。実物にある取っ手は省略。中身は無色透明。",
                   tags=["焼酎", "甲類焼酎", "大容量", "2.7L", "お酒", "酒類", "ペットボトル", "shochu", "PET bottle",
                         "alcohol"],
                   photos=[], colors=Colors(cap=navy, label_base=white),
                   **revolve(form, label=label, body_fill=None))


def umeshu_720ml() -> Product:
    """梅酒 720ml（透明のガラス瓶、琥珀色の中身）。ラベルは胴の上寄りの帯で、下の方は中身が見える。"""
    form = _shouldered_bottle(0.290, 0.080, sh_z=0.165, sh_top=0.218, neck_r=0.0140, cap_h=0.032, cap_r=0.0155,
                              label=(0.078, 0.150), liquid_top=0.228)
    cream, plum, green, gold = "#FBF4E4", "#7A1E3A", "#4F7A2A", "#B8862E"
    liquid = "#C88A2A"
    c = label_canvas(form, cream, seed=5891)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#FDF8EC", "#EFE0C0")
    c.rect(0, 0, W, 4, fill=plum)
    c.rect(0, H - 4, W, H, fill=plum)
    for k, (x, y) in enumerate(((fx - 26, 20), (fx - 18, 28), (fx - 30, 32))):  # 梅の実
        c.ellipse(x - 7, y - 7, x + 7, y + 7, fill=mix("#C9A23E", green, 0.4 + 0.2 * k))
        c.ellipse(x - 4, y - 5, x - 1, y - 2, fill="#EED98A")
    c.line([(fx - 24, 12), (fx - 20, 8)], "#5A3A1A", 0.8)
    _flower(c, fx + 28, 16, 6, "#F4B6C2")
    c.text(fx + 6, 26, "梅酒", 15, plum, 900)
    c.text(fx + 6, 40, "完熟南高梅", 4.8, INK, 800)
    c.rect(fx - 30, 46, fx + 30, 54, fill=plum, radius=4)
    c.text(fx, 50, "UMESHU  まろやかな甘さ", 3.2, cream, 800)
    c.text(fx, 62, "720ml  アルコール分12%", 3.6, INK, 800)
    _alcohol_mark(c, fx + 33, 40, 7)
    _bottle_back(c, bx, 6, 46, "リキュール", "梅（国産）、醸造アルコール、糖類", 1.8, color=INK, bg=cream,
                 extra=[("内容量", "720ml"), ("アルコール分", "12%")])
    c.paragraph(bx - 23, 38, bx + 23, ALCOHOL_NOTE, 1.5, INK, 600)
    c.barcode(0.5 * W - 10, 20, 20, 13)
    c.recycle(0.5 * W, 44, 6, "アルミ", INK, kind="can", sub="キャップ")
    label = finish(c.array(), "paper", 5891, 0.5)
    top = _cap_top(form, gold, plum, "梅", plum, 5892)
    return Product(slug="umeshu_720ml", name="梅酒 720ml", category="beverage", mass_kg=1.25, capacity_ml=720,
                   material="glass",
                   description="形は一般的な 720ml の梅酒の瓶（透明のガラス、高さ 290 mm・胴径 80 mm、アルミのねじ蓋）で、寸法・質量は代表値。"
                               "ラベルは胴の上寄りの帯で、その下と肩から琥珀色の中身が見える。キャップは胴と同じ輪郭の続き。",
                   tags=["梅酒", "リキュール", "お酒", "酒類", "瓶", "ガラス", "umeshu", "plum wine", "alcohol"],
                   photos=[], colors=Colors(cap=gold, liquid=liquid, label_base=cream, liquid_turbidity=0.0),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=liquid))


# ================================================================ 菓子


def cracker_box() -> Product:
    """クラッカーの箱（3 袋入り）。正面にクラッカーとチーズの絵。"""
    W, D, H = 190.0, 55.0, 130.0
    red, navy, cream, gold = "#C62828", "#14284B", "#FFF6E0", "#E8B34A"
    s = 7

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, red, seed)
        f.gradient(0, 0, w, h, "#D63A2E", "#A41E18")
        return f

    fr = face(W, H, 5901)
    fr.rect(0, 0, W, 11, fill=navy)
    fr.text(W / 2, 5.5, "SALTED CRACKERS  3袋入", 4.6, gold, 800, spacing=0.6)
    fr.ellipse(78, 26, W - 6, 116, fill=cream)
    _cracker(fr, 94, 44, 46, 42)
    _cracker(fr, 120, 60, 46, 42)
    _cracker(fr, 108, 80, 46, 42)
    fr.polygon([(150, 40), (178, 50), (160, 64)], fill="#F6CE4A", outline="#D9A52A")  # チーズ
    fr.text(132, 112, "※盛りつけ例", 2.8, INK, 500)
    fr.text(44, 32, "クラッカー", 13, WHITE, 900, max_w=76)
    fr.text(44, 46, "サクッと軽い", 5.4, gold, 900)
    fr.rect(8, 54, 80, 66, fill=cream, radius=6)
    fr.text(44, 60, "ほどよい塩味", 5.6, red, 900)
    fr.text(44, 80, "そのまま・", 5.0, WHITE, 800)
    fr.text(44, 88, "チーズをのせて", 5.0, WHITE, 800)
    fr.rect(8, 100, 80, 120, fill=navy, radius=4)
    fr.text(44, 107, "3袋（27枚）入", 4.8, gold, 900)
    fr.text(44, 115, "内容量 135g", 4.4, WHITE, 800)
    bk = face(W, H, 5902)
    bk.rect(4, 4, W - 4, H - 4, fill=cream, radius=2)
    back_info(bk, 7, 7, 104, [
        ("名称", "ビスケット"), ("原材料名", "小麦粉（国内製造）、植物油脂、砂糖、食塩、麦芽エキス／膨張剤、乳化剤、（一部に小麦・大豆を含む）"),
        ("内容量", "135g（45g×3袋）"), ("賞味期限", "側面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 2.6,
        [("栄養成分表示 1袋（45g）当たり", ""), ("エネルギー", "226kcal"), ("たんぱく質", "3.6g"), ("脂質", "10.4g"),
         ("炭水化物", "29.5g"), ("食塩相当量", "0.6g")], navy, cream)
    bk.text(148, 14, "おすすめの食べ方", 4.0, red, 900)
    bk.paragraph(110, 20, W - 8, "チーズ・ハム・ジャムをのせて、おつまみやおやつに。開封後はお早めにお召し上がりください。", 3.0, INK, 500)
    bk.barcode(116, 70, 40, 24)
    bk.recycle(168, 76, 9, "紙", navy, sub="箱")
    bk.recycle(180, 92, 9, "プラ", navy, sub="袋")
    sides = []
    for k, seed in enumerate((5903, 5904)):
        sd = face(D, H, seed)
        sd.rect(0, 0, D, 11, fill=navy)
        sd.vtext(D / 2, 18, "クラッカー", 8.0, WHITE, 900)
        sd.rect(5, 80, D - 5, 124, fill=cream, radius=2)
        if k == 0:
            _cracker(sd, 10, 86, 35, 32)
        else:
            sd.text(D / 2, 90, "賞味期限", 3.4, red, 700)
            sd.text(D / 2, 99, "2027.04", 4.4, INK, 900)
            sd.text(D / 2, 112, "3袋入", 5.0, red, 900)
        sides.append(sd.array())
    tp = face(W, D, 5905)
    tp.rect(0, 0, W, 4, fill=navy)
    tp.text(W / 2, 20, "クラッカー  135g（3袋入）", 7.0, WHITE, 900)
    tp.text(W / 2, 34, "↓ ここを押して開けてください", 4.0, gold, 800)
    bt = face(W, D, 5906)
    bt.text(W / 2, 16, "クラッカー  SALTED CRACKERS", 5.4, WHITE, 900)
    bt.text(W / 2, 32, NOTICE, 3.0, WHITE, 400, max_w=W - 10)
    imgs = [fr.array(), bk.array(), *sides, tp.array(), bt.array()]
    imgs = [_face(a, "paper", 5911 + i) for i, a in enumerate(imgs)]
    return Product(slug="cracker_box", name="クラッカー 3袋入 135g", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.16, material="paper",
                   description="形は一般的な箱入りのクラッカー（幅 190 mm・高さ 130 mm・奥行き 55 mm、中に 3 袋）で、寸法・質量は代表値。"
                               "クラッカーの絵は手続きで描いた。",
                   tags=["クラッカー", "ビスケット", "お菓子", "菓子", "箱", "crackers", "cracker box", "snack"],
                   photos=[], colors=Colors(label_base=red), images=imgs, faces=BOX_FACES)


def popcorn_bag() -> Product:
    """ポップコーンの袋（バター醤油味、立てたピロー袋）。手続きで描いたポップコーン。"""
    W, H = 170.0, 230.0
    yellow, red, brown, cream = "#F7C531", "#C62828", "#5A3214", "#FFF8E2"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, yellow, seed=seed)
        c.gradient(0, 0, W, H, "#FAD552", "#E9A91C")
        c.pattern(0, 0, W, H, "stripes", mix(yellow, red, 0.25), 14, 4.0)
        seal_crimp(c, 0, 0, W, 12, "#FAD552", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#E9A91C", 1.6)
        return c

    c = base(5921)
    c.rect(0, 12, W, 28, fill=red)
    c.text(W / 2, 20, "POPCORN  バター醤油味", 6.4, WHITE, 900, spacing=0.4)
    c.text(W / 2, 50, "ポップコーン", 20, red, 900, max_w=W - 16, stroke=0.8, stroke_fill=WHITE)
    c.text(W / 2, 68, "こがし醤油とバターの香り", 6.0, brown, 900)
    c.ellipse(16, 78, W - 16, 196, fill=cream)
    for k in range(26):
        a, d = k * 2.4, 6 + 3.8 * math.sqrt(k)
        _popcorn(c, W / 2 + d * 3.0 * math.cos(a) / 1.6, 137 + d * 2.6 * math.sin(a) / 1.6, 13)
    c.text(26, 194, "※イメージ", 3.0, brown, 500, anchor="lm")
    c.ellipse(W - 60, 172, W - 10, 222, fill=red)
    c.text(W - 35, 190, "60g", 9.0, WHITE, 900)
    c.text(W - 35, 205, "大袋", 5.4, WHITE, 900)
    c.rect(12, 200, 104, 216, fill=WHITE, radius=4)
    c.text(58, 208, "サクッと軽い食感", 5.0, red, 900)
    front = _pouch(c, 5921)

    b = base(5922)
    b.text(W / 2, 20, "ポップコーン バター醤油味", 6.0, red, 900)
    _bag_back(b, W, H, 30, [
        ("名称", "スナック菓子"), ("原材料名", "コーン（アメリカ産）、植物油脂、砂糖、しょうゆ、バター、食塩／調味料（アミノ酸等）、"
                                           "香料、（一部に乳成分・小麦・大豆を含む）"),
        ("内容量", "60g"), ("賞味期限", "表面上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.4,
        [("栄養成分表示 1袋（60g）当たり", ""), ("エネルギー", "312kcal"), ("たんぱく質", "4.2g"), ("脂質", "17.8g"),
         ("炭水化物", "34.0g"), ("食塩相当量", "1.0g")], [], red)
    back = _pouch(b, 5922)
    return Product(slug="popcorn_bag", name="ポップコーン バター醤油味 60g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.070), mass_kg=0.075, material="film",
                   description="形は一般的な袋入りのポップコーン（ピロー包装 高さ 230 mm・幅 170 mm、ふくらんだ厚さ 70 mm）で、寸法・質量は代表値。"
                               "ポップコーンの絵は手続きで描いた。",
                   tags=["ポップコーン", "スナック", "スナック菓子", "お菓子", "袋", "popcorn", "snack bag", "snack"],
                   photos=[], colors=Colors(label_base=yellow), images=[front, back], faces=POUCH_FACES)


def bite_chocolate_bag() -> Product:
    """ひと口チョコレートの大袋（個包装入り、立てたピロー袋）。"""
    W, H = 190.0, 260.0
    brown, dark, gold, cream = "#5A2E16", "#2E150A", "#E5B85C", "#FFF3E0"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 7, brown, seed=seed)
        c.gradient(0, 0, W, H, "#6E3A1E", "#2E150A")
        seal_crimp(c, 0, 0, W, 12, "#6E3A1E", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#2E150A", 1.6)
        c.rect(0, 12, W, 14, fill=gold)
        c.rect(0, H - 14, W, H - 12, fill=gold)
        return c

    c = base(5931)
    c.text(W / 2, 26, "MILK CHOCOLATE  BITE SIZE", 5.0, gold, 800, spacing=0.6)
    c.text(W / 2, 52, "ひと口", 14, cream, 900)
    c.text(W / 2, 78, "チョコレート", 20, gold, 900, max_w=W - 20)
    c.photo("chocolate", 20, 92, W - 20, 196, shape="round", radius=10, feather=2, shadow=1.5, crop=(0.40, 0.20, 0.88, 0.56))
    for k, (x, y) in enumerate(((44, 212), (82, 220), (120, 210))):  # 個包装
        c.rect(x - 16, y - 9, x + 16, y + 9, fill=gold if k % 2 == 0 else "#C62828", radius=2)
        c.text(x, y, "CHOCO", 3.6, dark if k % 2 == 0 else WHITE, 900)
        seal_crimp(c, x - 20, y - 9, x - 16, y + 9, gold, 0.8, vertical=True)
        seal_crimp(c, x + 16, y - 9, x + 20, y + 9, gold, 0.8, vertical=True)
    c.text(24, 202, "※写真はイメージです", 3.0, cream, 500, anchor="lm")
    c.ellipse(W - 58, 196, W - 8, 246, fill=gold)
    c.text(W - 33, 214, "大袋", 7.0, dark, 900)
    c.text(W - 33, 228, "約45個", 5.4, dark, 900)
    c.text(70, 238, "個包装  内容量 200g", 5.4, cream, 800)
    front = _pouch(c, 5931)

    b = base(5932)
    b.text(W / 2, 26, "ひと口チョコレート 200g", 6.4, gold, 900)
    _bag_back(b, W, H, 34, [
        ("名称", "チョコレート"), ("原材料名", "砂糖（外国製造）、全粉乳、カカオマス、ココアバター、植物油脂／乳化剤、香料、"
                                           "（一部に乳成分・大豆を含む）"),
        ("内容量", "200g（個包装込み）"), ("賞味期限", "裏面下部に記載"), ("保存方法", "28℃以下の涼しい所で保存")], 4.0,
        [("栄養成分表示 1個（4.4g）当たり", ""), ("エネルギー", "24kcal"), ("たんぱく質", "0.3g"), ("脂質", "1.5g"),
         ("炭水化物", "2.5g"), ("食塩相当量", "0.01g")],
        [("ご注意", "高温になる所に置くと、とけたり白く変わったりすることがあります。")], brown)
    back = _pouch(b, 5932)
    return Product(slug="bite_chocolate_bag", name="ひと口チョコレート 大袋 200g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.055), mass_kg=0.21, material="film",
                   description="形は一般的なひと口チョコレートの大袋（ピロー包装 高さ 260 mm・幅 190 mm・厚さ 55 mm、中は個包装）で、"
                               "寸法・質量は代表値。中の個包装は省略。",
                   tags=["チョコレート", "チョコ", "大袋", "個包装", "お菓子", "菓子", "袋", "chocolate", "bite size chocolate",
                         "snack"],
                   photos=["chocolate"], colors=Colors(label_base=brown), images=[front, back], faces=POUCH_FACES)


# ================================================================ 調味料・粉


def mirin_pet_1l() -> Product:
    form = forms.pet_bottle(0.250, 0.080, shoulder=0.16, neck_r=0.0135, cap_h=0.026, cap_r=0.0170,
                            label=(0.060, 0.160), liquid_top=0.190)
    cream, gold, navy, liquid = "#FFF8E6", "#B8862E", "#1F2F55", "#C9962E"
    c = label_canvas(form, cream, seed=5941)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFBF0", "#F5E6C4")
    c.rect(0, 0, W, 6, fill=navy)
    c.rect(0, H - 6, W, H, fill=navy)
    c.pattern(0, 6, W, 12, "waves", mix(gold, cream, 0.4), 3.0, 0.4)
    c.rect(fx - 22, 14, fx + 22, 84, fill=WHITE, outline=gold, width=0.8, radius=2)
    c.vtext(fx + 7, 22, "みりん", 13, navy, 900, gap=0.08)
    c.vtext(fx - 12, 21, "風調味料", 5.0, gold, 900)
    c.rect(fx - 17, 50, fx - 7, 76, fill=gold, radius=1.5)
    c.vtext(fx - 12, 54, "照り艶", 5.0, WHITE, 900)
    c.text(fx, 91, "みりん風調味料  1L", 4.6, navy, 900)
    c.text(fx, 3, "MIRIN  SWEET SEASONING", 2.8, WHITE, 800, spacing=0.5)
    c.text(fx, H - 3, "1000ml", 3.2, WHITE, 800)
    c.text(0.5 * W, H - 3, "アルコール分 1%未満", 2.4, WHITE, 700)
    _bottle_back(c, 0.25 * W, 9, 50, "みりん風調味料", "水あめ（国内製造）、米、米こうじ、醸造酢／酸味料、調味料（アミノ酸）", 2.0,
                 extra=[("内容量", "1L"), ("賞味期限", "キャップ付近に記載"), ("保存方法", "直射日光を避け、常温で保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（18g）当たり", ""), ("エネルギー", "41kcal"), ("たんぱく質", "0g"),
                            ("脂質", "0g"), ("炭水化物", "10.1g"), ("食塩相当量", "0.04g")], color=navy)
    c.barcode(0.5 * W - 13, 14, 26, 16)
    c.recycle(0.5 * W - 7, 50, 8, "PET", navy, kind="triangle")
    c.recycle(0.5 * W + 7, 50, 8, "プラ", navy, sub="ラベル")
    label = finish(c.array(), "film", 5941, 0.8)
    return Product(slug="mirin_pet_1l", name="みりん風調味料 1L", category="food", mass_kg=1.30, capacity_ml=1000,
                   material="PET",
                   description="形は一般的な 1L の調味料用 PET ボトル（高さ 250 mm・胴径 80 mm）で、寸法・質量は代表値。中身は琥珀色。",
                   tags=["みりん", "みりん風調味料", "調味料", "ペットボトル", "mirin", "seasoning"], photos=[],
                   colors=Colors(cap=navy, liquid=liquid, label_base=cream, liquid_turbidity=0.0),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def rice_vinegar_pet_500ml() -> Product:
    form = forms.pet_bottle(0.215, 0.066, shoulder=0.18, neck_r=0.0120, cap_h=0.024, cap_r=0.0155,
                            label=(0.050, 0.140), liquid_top=0.165)
    white, green, dark, liquid = WHITE, "#3E7D3A", "#1E3F1C", "#EDE2B0"
    c = label_canvas(form, white, seed=5951)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#EEF4E4")
    c.photo("rice_field", 0, H - 22, W, H, crop=(0, 0.45, 1, 0.75))
    c.rect(0, 0, W, 6, fill=green)
    c.text(fx, 3, "RICE VINEGAR", 3.0, WHITE, 800, spacing=0.8)
    c.rect(fx - 20, 9, fx + 20, 64, fill=WHITE, outline=green, width=0.7, radius=2)
    c.vtext(fx + 6, 14, "米酢", 15, dark, 900, gap=0.08)
    c.vtext(fx - 11, 14, "国産米100%", 4.4, green, 800)
    c.text(fx, 70, "まろやかな酸味", 3.8, dark, 900)
    c.text(fx, H - 6, "500ml", 4.8, WHITE, 900, stroke=0.4, stroke_fill=dark)
    bx = 0.25 * W
    c.rect(bx - 25, 8, bx + 25, 64, fill=WHITE, radius=1.5)
    _bottle_back(c, bx, 9, 48, "米酢", "米（国産）、アルコール", 1.8,
                 extra=[("内容量", "500ml"), ("酸度", "4.5%"), ("賞味期限", "キャップに記載"), ("保存方法", "直射日光を避けて保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（15ml）当たり", ""), ("エネルギー", "7kcal"), ("炭水化物", "1.1g"),
                            ("食塩相当量", "0g")], color=dark)
    c.barcode(0.5 * W - 11, 10, 22, 14)
    c.recycle(0.5 * W - 6, 36, 7, "PET", dark, kind="triangle")
    c.recycle(0.5 * W + 6, 36, 7, "プラ", dark, sub="ラベル")
    label = finish(c.array(), "film", 5951, 0.8)
    return Product(slug="rice_vinegar_pet_500ml", name="米酢 500ml", category="food", mass_kg=0.54, capacity_ml=500,
                   material="PET",
                   description="形は一般的な 500ml の食酢用 PET ボトル（高さ 215 mm・胴径 66 mm）で、寸法・質量は代表値。中身は淡い黄色。",
                   tags=["酢", "米酢", "食酢", "調味料", "ペットボトル", "rice vinegar", "vinegar", "seasoning"],
                   photos=["rice_field"], colors=Colors(cap=green, liquid=liquid, label_base=white, liquid_turbidity=0.0),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


def miso_cup_750g() -> Product:
    """カップ入りのみそ 750g（樹脂の容器・かぶせ蓋）。胴に全周ラベル、蓋の上に商品名。"""
    form = forms.paper_cup(0.092, 0.132, 0.118, lid_h=0.012, lid_overhang=0.003, rim_h=0.004,
                           label_margin=(0.004, 0.003))
    cream, brown, red, white = "#FBF1DD", "#6B3A1A", "#B3261E", WHITE
    c = label_canvas(form, cream, seed=5961)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#FDF6E8", "#EBD7B0")
    c.rect(0, 0, W, 8, fill=brown)
    c.rect(0, H - 6, W, H, fill=brown)
    c.text(fx, 4, "MISO  合わせみそ", 3.6, cream, 800, spacing=0.6)
    c.photo("miso_soup", fx - 60, 12, fx - 14, H - 9, shape="ellipse", feather=1.2, shadow=1.0, crop=(0.1, 0.1, 0.9, 0.9))
    c.text(fx - 37, H - 3, "※写真は調理例です", 2.2, cream, 500)
    c.text(fx + 22, 22, "合わせ", 9.0, brown, 900)
    c.text(fx + 22, 38, "みそ", 15, brown, 900)
    c.rect(fx + 2, 48, fx + 42, 56, fill=red, radius=4)
    c.text(fx + 22, 52, "だし入り", 5.0, white, 900)
    c.text(fx + 22, 63, "750g", 6.0, INK, 900)
    c.text(0.5 * W, 4, "米みそ・豆みそ", 3.4, cream, 800)
    c.rect(bx - 44, 11, bx + 44, H - 9, fill=white, radius=1.5)
    back_info(c, bx - 43, 12, bx + 2, [
        ("名称", "調味みそ（だし入り）"), ("原材料名", "米みそ（国内製造）、豆みそ、かつおぶし粉末、こんぶエキス／調味料（アミノ酸等）、酒精"),
        ("内容量", "750g"), ("賞味期限", "フタに記載"), ("保存方法", "要冷蔵（10℃以下）")], 1.8, None, brown)
    back_info(c, bx + 4, 12, bx + 43, [("栄養成分表示 大さじ1杯（18g）当たり", "")], 1.8,
              [("エネルギー", "35kcal"), ("たんぱく質", "2.1g"), ("脂質", "1.0g"), ("炭水化物", "4.4g"), ("食塩相当量", "2.0g")],
              brown)
    c.barcode(bx + 8, 44, 30, 16)
    c.recycle(0.5 * W - 6, 40, 8, "プラ", brown, sub="容器")
    c.recycle(0.5 * W + 7, 40, 8, "プラ", brown, sub="フタ")
    label = edge_shade(finish(c.array(), "film", 5961, 0.6), 6, 0.06)

    t = top_canvas(form, cream, seed=5962)
    d = t.w_mm
    t.ellipse(0.5, 0.5, d - 0.5, d - 0.5, fill=brown)
    t.ellipse(5, 5, d - 5, d - 5, fill=cream, outline=red, width=1.0)
    t.text(d / 2, d * 0.26, "要冷蔵", 6.0, red, 800)
    t.text(d / 2, d * 0.43, "合わせみそ", 15, brown, 900)
    t.text(d / 2, d * 0.58, "だし入り  750g", 8.0, INK, 900)
    t.text(d / 2, d * 0.72, "賞味期限 2027.03.31", 5.0, INK, 700)
    top = finish(t.array(), "film", 5962, 0.5)
    return Product(slug="miso_cup_750g", name="合わせみそ だし入り 750g", category="food", mass_kg=0.80, material="plastic",
                   description="形は一般的な 750g のカップ入りみそ（樹脂の容器、高さ 92 mm・上端径約 135 mm、かぶせ蓋）で、寸法・質量は代表値。",
                   tags=["みそ", "味噌", "合わせみそ", "だし入り", "調味料", "要冷蔵", "miso", "miso paste", "seasoning"],
                   photos=["miso_soup"], colors=Colors(cap=brown, label_base=cream),
                   **revolve(form, label=label, top=top))


def ketchup_bottle_500g() -> Product:
    form = _squeeze_bottle(0.205, 0.072, body_h=0.172, neck_r=0.0145, cap_r=0.0190, cap_h=0.020, tip_r=0.0050,
                           label=(0.040, 0.125), liquid_top=0.160)
    white, red, green, liquid = WHITE, "#C62828", "#2E7D32", "#B3160E"
    c = label_canvas(form, white, seed=5971)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#FBEDE6")
    c.rect(0, 0, W, 5, fill=green)
    c.rect(0, H - 5, W, H, fill=green)
    # 断面が楕円なので、文字は平らな正面（fx ± 22 mm）と裏面（bx ± 24 mm）に寄せる
    c.text(fx, 13.5, "TOMATO KETCHUP", 3.0, red, 800, spacing=0.4, max_w=44)
    c.text(fx, 25, "トマト", 9.0, red, 900)
    c.text(fx, 36, "ケチャップ", 7.6, red, 900, max_w=44)
    for x, y, r in ((fx - 10, 52, 8), (fx + 8, 55, 9)):  # トマトの絵
        c.ellipse(x - r, y - r * 0.85, x + r, y + r * 0.85, fill="#D7261E")
        c.ellipse(x - r * 0.6, y - r * 0.6, x - r * 0.1, y - r * 0.2, fill="#F06A55")
        c.polygon([(x - r * 0.5, y - r * 0.8), (x, y - r * 0.55), (x + r * 0.5, y - r * 0.8), (x, y - r * 1.1)], fill=green)
    c.rect(fx - 18, 68, fx + 18, 76, fill=red, radius=4)
    c.text(fx, 72, "500g", 5.0, white, 900)
    c.text(fx, H - 2.5, "完熟トマト使用", 2.6, white, 800)
    c.text(bx, H - 2.5, "開封後は要冷蔵", 2.4, white, 700)
    y = _bottle_back(c, bx, 8, 48, "トマトケチャップ", "トマト（輸入）、糖類（砂糖・ぶどう糖果糖液糖）、醸造酢、食塩、たまねぎ、香辛料",
                     1.8, extra=[("内容量", "500g"), ("賞味期限", "キャップに記載"), ("保存方法", "開封後は冷蔵庫に保存")],
                     nutrition=[("栄養成分表示 大さじ1杯（15g）当たり", ""), ("エネルギー", "18kcal"), ("たんぱく質", "0.2g"),
                                ("脂質", "0g"), ("炭水化物", "4.3g"), ("食塩相当量", "0.5g")], color=red)
    c.barcode(bx - 25, y + 1.5, 24, min(14.0, H - 7 - y))
    c.recycle(bx + 8, y + 6, 6.5, "プラ", red, sub="容器")
    c.recycle(bx + 19, y + 6, 6.5, "プラ", red, sub="キャップ")
    label = finish(c.array(), "film", 5971, 0.7)
    return Product(slug="ketchup_bottle_500g", name="トマトケチャップ 500g", category="food", mass_kg=0.53,
                   material="polyethylene (translucent)",
                   description="形は一般的な 500g のケチャップのやわらかいボトル（高さ 205 mm・幅 72 mm・奥行き 50 mm の楕円断面、"
                               "口の細いキャップ）で、寸法・質量は代表値。ラベルの上下から赤い中身が透けて見える。",
                   tags=["ケチャップ", "トマトケチャップ", "調味料", "ketchup", "tomato ketchup", "seasoning"], photos=[],
                   colors=Colors(cap=red, liquid=liquid, label_base="#F4F4F0", liquid_turbidity=1.0),
                   **revolve(form, label=label, body_fill=None, liquid=liquid, depth=0.050))


def sugar_bag_1kg() -> Product:
    """上白糖 1kg（底マチで立つ袋）。"""
    W, H = 140.0, 220.0
    white, blue, navy, sky = WHITE, "#1E63B5", "#0E2D5E", "#DCEBFA"
    c = Canvas(W, H, 8, white, seed=5981)
    c.gradient(0, 0, W, H, "#FFFFFF", "#E8F1FB")
    seal_crimp(c, 0, 0, W, 10, "#D7E4F4", 1.4)
    c.rect(0, H - 6, W, H, fill=blue)
    c.rect(0, 10, W, 26, fill=blue)
    c.text(W / 2, 18, "SUGAR  上白糖", 6.0, white, 900, spacing=0.6)
    c.pattern(0, 26, W, 60, "waves", mix(sky, blue, 0.2), 8, 0.5)
    c.ellipse(16, 46, W - 16, 150, fill=white, outline=blue, width=1.4)
    c.text(W / 2, 80, "上白糖", 22, navy, 900)
    c.text(W / 2, 100, "しっとり 料理に", 5.8, blue, 800)
    for k in range(18):  # 砂糖の粒
        x, y = W / 2 + c.rng.uniform(-30, 30), 120 + c.rng.uniform(-12, 12)
        c.rect(x - 1.4, y - 1.4, x + 1.4, y + 1.4, fill=mix(sky, white, 0.4), outline="#B5C9E2", width=0.2)
    c.rect(26, 160, W - 26, 182, fill=blue, radius=11)
    c.text(W / 2, 171, "1kg", 13, white, 900)
    c.text(W / 2, 196, "てんさい・さとうきび原料", 4.4, navy, 700)
    img = trim_safe(edge_shade(finish(c.array(), "film", 5981, 0.8), 20, 0.12))
    b = Canvas(W, H, 8, white, seed=5982)
    b.gradient(0, 0, W, H, "#FFFFFF", "#E8F1FB")
    seal_crimp(b, 0, 0, W, 10, "#D7E4F4", 1.4)
    b.rect(0, H - 6, W, H, fill=blue)
    b.rect(0, 10, W, 20, fill=blue)
    b.text(W / 2, 15, "上白糖 1kg", 5.0, white, 900)
    y = back_info(b, 10, 26, W - 10, [("名称", "砂糖（上白糖）"), ("原材料名", "原料糖（外国製造、国内製造）"), ("内容量", "1kg"),
                                      ("保存方法", "においの強いもの・湿気を避けて保存")], 4.0, None, navy)
    y = b.paragraph(10, y + 4, W - 10, "砂糖は長期間保存しても品質の変化がきわめて少ないため、賞味期限の表示を省略しています。"
                                       "固まったときは、霧を吹いて袋の口を閉じておくとほぐれます。", 3.8, INK, 500)
    b.barcode(12, y + 6, 46, 26)
    b.recycle(W - 32, y + 19, 14, "プラ", navy, sub="袋")
    if y + 34 > H - 6:
        raise ValueError(f"砂糖の裏面がはみ出す（{y:.1f} mm）")
    back = trim_safe(edge_shade(finish(b.array(), "film", 5982, 0.8), 20, 0.12))
    return Product(slug="sugar_bag_1kg", name="上白糖 1kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.22, 0.14, depth=0.07, gusset=0.07, square=3), mass_kg=1.01, material="film",
                   description="形は一般的な 1kg の砂糖の袋（高さ 220 mm・幅 140 mm・厚さ約 70 mm、底マチで自立）で、寸法・質量は代表値。",
                   tags=["砂糖", "上白糖", "調味料", "製菓材料", "袋", "sugar", "sugar bag"], photos=[],
                   colors=Colors(label_base=white), images=[img, back], faces=POUCH_FACES)


def flour_bag_1kg() -> Product:
    """薄力小麦粉 1kg（紙袋、底マチで立つ）。"""
    W, H = 150.0, 240.0
    kraft, red, brown, cream = "#F4ECDC", "#B3261E", "#5A3A1A", "#FFFDF6"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, kraft, seed=seed)
        c.gradient(0, 0, W, H, "#FAF4E8", "#EADCC2")
        c.rect(0, 0, W, 12, fill=mix(kraft, brown, 0.15))
        for x in range(0, int(W), 3):  # 折り返しのギザ
            c.line([(x, 12), (x + 1.5, 13.5), (x + 3, 12)], mix(kraft, brown, 0.3), 0.3)
        return c

    c = base(5991)
    c.rect(0, 16, W, 32, fill=red)
    c.text(W / 2, 24, "FLOUR  薄力小麦粉", 6.0, WHITE, 900, spacing=0.4)
    c.text(W / 2, 58, "薄力粉", 24, brown, 900)
    c.text(W / 2, 80, "お菓子・天ぷらに", 6.4, red, 900)
    c.photo("butter_cookies", 18, 92, W - 18, 172, shape="round", radius=8, feather=1.5, shadow=1.2,
            crop=(0.1, 0.1, 0.9, 0.9))
    c.text(W / 2, 178, "※写真は調理例です", 3.2, brown, 500)
    for k in range(-3, 4):  # 小麦の穂
        x = W / 2 + k * 9
        c.line([(x, 214), (x + k * 0.6, 192)], brown, 0.5)
        for j in range(4):
            c.ellipse(x - 2.2 + k * 0.4, 192 + j * 4.5, x + 0.4 + k * 0.4, 196 + j * 4.5, fill="#D9A441")
    c.rect(30, 218, W - 30, 234, fill=red, radius=8)
    c.text(W / 2, 226, "1kg", 10, WHITE, 900)
    front = _paper_bag(c, 5991)

    b = base(5992)
    b.text(W / 2, 22, "薄力小麦粉 1kg", 6.0, red, 900)
    b.rect(8, 30, W - 8, H - 8, fill=cream, radius=2)
    y = back_info(b, 12, 33, W - 12, [
        ("名称", "小麦粉"), ("原材料名", "小麦（アメリカ産）"), ("内容量", "1kg"), ("賞味期限", "上部に記載"),
        ("保存方法", "においの強いもの・湿気を避け、涼しい所で保存")], 3.8,
        [("栄養成分表示 100g当たり", ""), ("エネルギー", "349kcal"), ("たんぱく質", "8.3g"), ("脂質", "1.5g"),
         ("炭水化物", "75.8g"), ("食塩相当量", "0g")], brown, cream)
    y = b.paragraph(12, y + 3, W - 12, "【ご注意】開封後はしっかり封をして、早めにお使いください。生のままでは食べないでください。", 3.6,
                    INK, 500)
    b.barcode(14, y + 5, 46, 26)
    b.recycle(W - 30, y + 18, 14, "紙", brown, sub="袋")
    if y + 33 > H - 8:
        raise ValueError(f"小麦粉の裏面がはみ出す（{y:.1f} mm）")
    back = _paper_bag(b, 5992)
    return Product(slug="flour_bag_1kg", name="薄力小麦粉 1kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.24, 0.15, depth=0.075, gusset=0.075, square=3), mass_kg=1.02, material="paper",
                   description="形は一般的な 1kg の小麦粉の紙袋（高さ 240 mm・幅 150 mm・厚さ約 75 mm、底マチで自立、上は折り返し）で、"
                               "寸法・質量は代表値。",
                   tags=["小麦粉", "薄力粉", "製菓材料", "粉", "袋", "flour", "flour bag", "wheat flour"],
                   photos=["butter_cookies"], colors=Colors(label_base=kraft), images=[front, back], faces=POUCH_FACES)


def salad_oil_pet_1000g() -> Product:
    form = forms.pet_bottle(0.272, 0.084, shoulder=0.16, neck_r=0.0135, cap_h=0.026, cap_r=0.0180,
                            label=(0.080, 0.178), liquid_top=0.212, waist=(0.020, 0.070))
    white, yellow, green, liquid = WHITE, "#F2C230", "#2E7D32", "#E8C95A"
    c = label_canvas(form, white, seed=6001)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#FFF7D6")
    c.rect(0, 0, W, 7, fill=green)
    c.rect(0, H - 7, W, H, fill=green)
    c.text(fx, 3.5, "SALAD OIL  1000g", 3.4, WHITE, 800, spacing=0.8)
    c.photo("salad", fx - 28, 10, fx + 28, 48, shape="ellipse", feather=1.2, shadow=1.0, crop=(0, 0.03, 0.96, 0.98))
    c.text(fx, 51, "※写真はイメージです", 1.8, INK, 500)
    c.text(fx, 60, "サラダ油", 11, green, 900)
    c.rect(fx - 26, 67, fx + 26, 75, fill=yellow, radius=4)
    c.text(fx, 71, "揚げ物・炒め物・ドレッシングに", 3.0, green, 800, max_w=50)
    c.text(fx, 84, "大豆・なたね  1000g", 4.0, INK, 900)
    c.text(fx, H - 3.5, "からっと軽い", 3.0, WHITE, 800)
    bx = 0.25 * W
    c.rect(bx - 30, 9, bx + 30, H - 9, fill=WHITE, radius=1.5)
    _bottle_back(c, bx, 10, 56, "食用調合油", "食用大豆油（国内製造）、食用なたね油", 2.0,
                 extra=[("内容量", "1000g"), ("賞味期限", "キャップ付近に記載"), ("保存方法", "直射日光・高温を避けて保存")],
                 nutrition=[("栄養成分表示 大さじ1杯（14g）当たり", ""), ("エネルギー", "126kcal"), ("たんぱく質", "0g"),
                            ("脂質", "14g"), ("炭水化物", "0g"), ("食塩相当量", "0g")], color=green)
    c.barcode(0.5 * W - 13, 12, 26, 16)
    c.recycle(0.5 * W - 7, 48, 8, "PET", green, kind="triangle")
    c.recycle(0.5 * W + 7, 48, 8, "プラ", green, sub="ラベル")
    c.text(0.5 * W, 64, "使用後の油は", 2.4, green, 700)
    c.text(0.5 * W, 68, "排水口に流さない", 2.4, green, 700)
    label = finish(c.array(), "film", 6001, 0.8)
    return Product(slug="salad_oil_pet_1000g", name="サラダ油 1000g", category="food", mass_kg=1.06, capacity_ml=1090,
                   material="PET",
                   description="形は一般的な 1000g の食用油の PET ボトル（高さ 272 mm・胴径 84 mm、下部に持ちやすいくびれ）で、寸法・質量は代表値。"
                               "中身は淡い黄色の澄んだ油。",
                   tags=["サラダ油", "食用油", "油", "調味料", "ペットボトル", "salad oil", "cooking oil", "vegetable oil"],
                   photos=["salad"], colors=Colors(cap=green, liquid=liquid, label_base=white, liquid_turbidity=0.0),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


# ================================================================ 乾めん・飲料


def somen_pack() -> Product:
    """そうめん 300g（50g × 6 束、寝かせた細長い袋）。右に白い麺の窓、束の帯。"""
    L, Wd = 230.0, 110.0
    navy, white, red, gold = "#14365E", WHITE, "#C62828", "#E8C77A"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 8, white, seed=seed)
        c.gradient(0, 0, L, Wd, "#FFFFFF", "#EEF2F7")
        c.pattern(0, 0, L, Wd, "waves", mix(white, "#9EC3E6", 0.35), 10, 0.5)
        seal_crimp(c, 0, 0, 10, Wd, "#DDE5EE", 1.4, vertical=True)
        seal_crimp(c, L - 10, 0, L, Wd, "#DDE5EE", 1.4, vertical=True)
        return c

    def window(c: Canvas, x0: float, x1: float, bands: bool):
        c.rect(x0, 10, x1, Wd - 10, fill="#F7F3E8", radius=4)
        for k in range(110):
            y = 11 + k * (Wd - 22) / 110
            c.line([(x0 + 1, y), (x1 - 1, y + c.rng.uniform(-0.2, 0.2))], mix("#FFFFFF", "#E6DDC6", c.rng.random()), 0.35)
        if bands:
            for k in range(3):  # 束の帯
                x = x0 + (x1 - x0) * (0.5 + 0.0 * k)
                yy = 10 + (Wd - 20) * (k + 0.5) / 3
                c.rect(x - 7, yy - 13, x + 7, yy + 13, fill=red)
                c.text(x, yy, "50g", 2.8, white, 800)
        c.rect(x0, 10, x1, Wd - 10, outline=navy, width=0.6, radius=4)

    c = base(6011)
    window(c, 128, L - 16, True)
    c.rect(14, 8, 118, 34, fill=navy, radius=3)
    c.text(66, 21, "手延べ風", 9.0, gold, 900)
    c.text(66, 52, "そうめん", 17, navy, 900, max_w=100)
    c.text(66, 66, "SOMEN  細くなめらか", 4.4, red, 800, spacing=0.4)
    c.photo("deli_soba", 18, 72, 70, 102, shape="round", radius=3, crop=(0.1, 0.2, 0.9, 0.8))
    c.text(44, 105, "※写真はイメージです", 2.0, INK, 500)
    c.ellipse(80, 72, 114, 104, fill=red)
    c.text(97, 84, "300g", 5.6, white, 900)
    c.text(97, 94, "6束", 5.0, gold, 900)
    front = _pouch(c, 6011, 0.9, 16)

    b = base(6012)
    window(b, 14, 34, False)
    b.rect(40, 10, L - 14, Wd - 10, fill=white, radius=3)
    _back_panel(b, 43, 13, 136, Wd - 12, [
        ("名称", "干しめん"), ("原材料名", "小麦粉（国内製造）、食塩、食用植物油"), ("内容量", "300g（50g×6束）"),
        ("賞味期限", "右端に記載"), ("保存方法", "直射日光・湿気を避けて保存")], 2.8,
        [("栄養成分表示 1束（50g）当たり", ""), ("エネルギー", "167kcal"), ("たんぱく質", "4.5g"), ("脂質", "0.6g"),
         ("炭水化物", "36.1g"), ("食塩相当量", "1.9g")], [], navy)
    y = 13.0
    for title, body in [("ゆで方", "たっぷりのお湯（1束に 1L）を沸騰させ、ほぐし入れて 1分30秒〜2分ゆでます。"
                                    "冷水でよくもみ洗いしてください。"),
                        ("ご注意", "ゆでるときは吹きこぼれに注意してください。")]:
        b.rect(142, y, 214, y + 5.0, fill=navy, radius=0.8)
        b.text(143.5, y + 2.5, title, 3.2, white, 800, anchor="lm")
        y = b.paragraph(143, y + 6.4, 213, body, 3.0, INK, 500) + 3.0
    b.barcode(146, y + 1, 36, 20)
    b.recycle(200, y + 11, 11, "プラ", navy, sub="袋")
    if y + 22 > Wd - 10:
        raise ValueError(f"そうめんの裏面がはみ出す（{y:.1f} mm）")
    back = _pouch(b, 6012, 0.9, 16)
    return Product(slug="somen_pack", name="そうめん 300g（6束）", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.028), mass_kg=0.31, material="film", orientation="lying",
                   description="形は一般的な袋入りのそうめん 300g（50g の束が 6 つ、長さ 230 mm・幅 110 mm・厚さ 28 mm）で、"
                               "寸法・質量は代表値。寝かせて置く。",
                   tags=["そうめん", "素麺", "乾めん", "干しめん", "袋", "somen", "dried noodles", "noodles"],
                   photos=["deli_soba"], colors=Colors(label_base=white), images=[front, back], faces=POUCH_FACES)


def black_tea_pet_500ml() -> Product:
    form = forms.pet_bottle(0.212, 0.067, shoulder=0.24, cap_h=0.019, cap_r=0.0148, label=(0.040, 0.142),
                            liquid_top=0.176, ribs=(0.010, 0.036))
    cream, red, dark, gold = "#FFF7EC", "#8E1B1B", "#3A0E0A", "#C9A23E"
    liquid = "#8E3B14"
    c = label_canvas(form, cream, seed=6021)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFAF2", "#F1E2CA")
    c.rect(0, 0, W, 7, fill=red)
    c.rect(0, H - 7, W, H, fill=red)
    c.text(fx, 3.5, "STRAIGHT TEA", 3.2, gold, 800, spacing=0.8)
    _tea_cup(c, fx - 14, 40, 15, liquid, red)
    c.photo("lemon", fx - 30, 54, fx - 14, 70, shape="ellipse", feather=0.6, crop=(0.1, 0.05, 0.9, 0.95))
    c.vtext(fx + 16, 12, "紅茶", 10, red, 900, gap=0.05)
    c.vtext(fx + 6, 22, "無糖", 7.0, dark, 900, gap=0.03)
    c.rect(fx - 28, 74, fx + 28, 83, fill=red, radius=4.5)
    c.text(fx, 78.5, "ダージリン茶葉ブレンド", 3.6, cream, 800)
    c.text(fx, 90, "紅茶飲料  500ml", 3.8, dark, 900)
    c.text(fx, H - 3.5, "BLACK TEA", 3.0, cream, 700, spacing=0.8)
    c.vtext(0.5 * W, 14, "すっきり香る", 4.0, red, 900)
    _bottle_back(c, 0.25 * W, 11, 46, "紅茶飲料", "紅茶（インド産）／ビタミンC", 1.8,
                 extra=[("内容量", "500ml"), ("賞味期限", "キャップに記載"), ("保存方法", "高温・直射日光を避けてください")],
                 nutrition=[("栄養成分表示 100ml当たり", ""), ("エネルギー", "0kcal"), ("たんぱく質", "0g"), ("脂質", "0g"),
                            ("炭水化物", "0.2g"), ("食塩相当量", "0.02g")])
    c.barcode(0.5 * W - 13, 50, 26, 16)
    c.recycle(0.5 * W - 6, 78, 8, "PET", INK, kind="triangle")
    c.recycle(0.5 * W + 7, 78, 8, "プラ", INK, sub="ラベル")
    label = finish(c.array(), "film", 6021, 0.8)
    return Product(slug="black_tea_pet_500ml", name="無糖紅茶 500ml", category="beverage", mass_kg=0.53,
                   capacity_ml=500, material="PET",
                   description="形は一般的な 500ml の紅茶飲料用 PET ボトル（高さ 212 mm・胴径 67 mm）で、寸法・質量は代表値。中身は赤茶色の澄んだ紅茶。",
                   tags=["紅茶", "ストレートティー", "無糖", "紅茶飲料", "ペットボトル", "black tea", "tea", "PET bottle"],
                   photos=["lemon"], colors=Colors(cap=red, liquid=liquid, label_base=cream, liquid_turbidity=0.0),
                   **revolve(form, label=label, body_fill=None, liquid=liquid))


# ================================================================ 日用品・ペット用品


def fabric_softener_bottle() -> Product:
    """柔軟剤のボトル（扁平な楕円断面、計量キャップ）。不透明の淡いピンクの容器。"""
    R, H = 0.045, 0.228
    body = [(0.0, R * 0.90)] + _arc(0.0005, 0.008, R * 0.94, R, 8, "out")[1:]
    body += [(0.160, R)] + _arc(0.160, 0.188, R, 0.021, 24, "cos")[1:] + [(0.193, 0.021)]
    cap = [(0.193, 0.0245), (0.226, 0.0245), (H, 0.0228)]
    form = RevolveForm(body, cap, (0.018, 0.152), liquid_top=0.170)
    pink, purple, white, rose = "#F7D8E4", "#7B3F8C", WHITE, "#E58AA8"
    c = label_canvas(form, white, seed=6031)
    W, Hh = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, Hh, "#FFFFFF", "#F6E3F0")
    c.rect(0, 0, W, 5, fill=purple)
    c.rect(0, Hh - 5, W, Hh, fill=purple)
    # 断面が楕円なので、文字は平らな正面（fx ± 26 mm）と裏面（bx ± 26 mm）に寄せる
    c.text(fx, 13, "FABRIC SOFTENER", 3.0, purple, 700, spacing=0.4, max_w=48)
    c.text(fx, 27, "柔軟剤", 12, purple, 900)
    c.text(fx, 40, "ふんわり やわらか", 4.6, INK, 800, max_w=48)
    c.photo("lavender", fx - 24, 46, fx + 24, 92, shape="ellipse", feather=1.5, shadow=1.0, crop=(0.1, 0.05, 0.9, 0.95))
    for x, y in ((fx - 20, 92), (fx + 21, 50)):
        _flower(c, x, y, 6, rose)
    c.text(fx, 98, "※写真はイメージです", 2.0, INK, 500)
    c.rect(fx - 24, 104, fx + 24, 113, fill=purple, radius=4.5)
    c.text(fx, 108.5, "ラベンダーの香り", 4.0, white, 800)
    c.text(fx, 124, "部屋干しでも におわない", 3.2, purple, 800, max_w=48)
    rows = [("品名", "柔軟仕上げ剤"), ("成分", "界面活性剤（エステル型ジアルキルアンモニウム塩）、安定化剤、香料"),
            ("液性", "弱酸性"), ("正味量", "600ml"), ("用途", "衣料用")]
    caution = ("【使用量の目安】水量 30L に対してキャップの線 1（約 15ml）。\n"
               "【使用上の注意】用途外に使わない。子供の手の届く所に置かない。原液が衣類に直接かからないようにする。"
               "目に入ったときは、こすらずにすぐ水で十分に洗い流す。")
    y = _info(c, bx - 25, 8, bx + 25, rows, caution, 2.2)
    c.rect(bx - 25, y + 2, bx + 2, y + 20, fill=white)
    c.barcode(bx - 24, y + 3, 25, 16)
    c.recycle(bx + 10, y + 10, 7, "プラ", INK, sub="容器")
    c.recycle(bx + 20, y + 10, 7, "プラ", INK, sub="キャップ")
    if y + 22 > Hh - 5:
        raise ValueError(f"柔軟剤の裏面がはみ出す（{y:.1f} mm）")
    label = finish(c.array(), "film", 6031, 0.6)
    t = top_canvas(form, purple, seed=6032)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#9257A3", "#6A3279")
    t.ellipse(1.0, 1.0, d - 1.0, d - 1.0, outline="#4E2259", width=0.6)
    t.text(d / 2, d / 2 - 4, "計量", 5.0, white, 900)
    t.text(d / 2, d / 2 + 4, "キャップ", 4.0, white, 800)
    top = finish(t.array(), "film", 6032, 0.5)
    return Product(slug="fabric_softener_bottle", name="柔軟剤 ラベンダーの香り 600ml", category="household",
                   mass_kg=0.68, capacity_ml=600, material="polyethylene (opaque)",
                   description="形は一般的な柔軟剤の本体ボトル（高さ 228 mm・幅 90 mm・奥行き 58 mm の扁平な楕円断面、"
                               "大きな計量キャップ）で、寸法・質量は代表値。取っ手は省略。容器は不透明の淡いピンクの樹脂。",
                   tags=["柔軟剤", "柔軟仕上げ剤", "洗濯", "ラベンダー", "fabric softener", "laundry"], photos=["lavender"],
                   colors=Colors(cap=purple, label_base=pink),
                   **revolve(form, label=label, top=top, depth=0.058))


def dog_food_bag() -> Product:
    """ドライのドッグフード 2kg（底マチで立つ袋）。犬の顔のイラストと粒の絵。"""
    W, H = 220.0, 330.0
    green, dark, cream, orange = "#2E7D4F", "#143D26", "#FFF8E8", "#F08A24"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, None, green, seed=seed)
        c.gradient(0, 0, W, H, "#3A9460", "#1C5534")
        seal_crimp(c, 0, 0, W, 14, "#3A9460", 2.0)
        return c

    c = base(6041)
    c.rect(0, 14, W, 34, fill=orange)
    c.text(W / 2, 24, "DOG FOOD  成犬用  チキン＆野菜", 6.4, WHITE, 900, spacing=0.4)
    c.text(W / 2, 58, "ドッグフード", 24, cream, 900, max_w=W - 20)
    c.text(W / 2, 80, "総合栄養食  ドライタイプ", 7.0, "#FFD27A", 800)
    c.ellipse(24, 92, W - 24, 236, fill=cream)
    _dog(c, W / 2, 158, 110)
    c.ellipse(20, 236, 112, 292, fill="#E9D4AE")
    _kibble(c, 30, 244, 102, 284, 34, 4.0)
    c.text(66, 298, "※粒のイメージ", 3.4, cream, 500)
    c.ellipse(W - 92, 238, W - 14, 312, fill=orange)
    c.text(W - 53, 266, "2kg", 16, WHITE, 900)
    c.text(W - 53, 288, "1歳以上", 7.0, WHITE, 900)
    c.text(W / 2, 320, "小粒  食べやすい", 6.0, cream, 800)
    img = _paper_bag(c, 6041, 25)

    b = base(6042)
    b.rect(0, 14, W, 26, fill=orange)
    b.text(W / 2, 20, "ドッグフード 成犬用 2kg", 6.0, WHITE, 900)
    b.rect(12, 32, W - 12, 224, fill=WHITE, radius=4)
    y = b.paragraph(18, 38, W - 18, "【名称】ドッグフード（総合栄養食）\n【原材料名】穀類（とうもろこし、小麦粉）、肉類（チキンミール）、"
                    "動物性油脂、豆類、野菜類（にんじん、かぼちゃ）、ビタミン類、ミネラル類、酸化防止剤（ミックストコフェロール）\n"
                    "【内容量】2kg\n【賞味期限】下部に記載\n【原産国】日本\n【保存方法】開封後はチャックを閉め、直射日光・高温多湿を避けて保存",
                    4.4, INK, 400)
    y = b.table(18, y + 4, W - 18, "成分（保証値）", [("たんぱく質", "21.0%以上"), ("脂質", "8.0%以上"), ("粗繊維", "5.0%以下"),
                                                  ("灰分", "9.0%以下"), ("水分", "10.0%以下"), ("エネルギー", "350kcal/100g")], 4.2)
    if y > 222:
        raise ValueError(f"ドッグフードの裏面がはみ出す（{y:.1f} mm）")
    b.rect(12, 230, W - 12, H - 14, fill=WHITE, radius=4)
    b.table(18, 236, 120, "1日の給与量の目安", [("体重 5kg", "約95g"), ("体重 10kg", "約160g"), ("体重 20kg", "約270g")], 4.0)
    b.barcode(128, 238, 72, 40)
    b.recycle(146, 296, 16, "プラ", dark, sub="袋")
    b.text(184, 296, "ペット用", 5.0, dark, 900)
    b.paragraph(18, 284, 120, NOTICE, 3.4, INK, 500)
    back = _paper_bag(b, 6042, 25)
    return Product(slug="dog_food_bag", name="ドッグフード 成犬用 チキン＆野菜 2kg", shape_class="pouch", category="household",
                   dims=Dimensions(0.33, 0.22, depth=0.09, gusset=0.09, square=3), mass_kg=2.05, material="film",
                   description="形は一般的な 2kg のドライのドッグフードの袋（高さ 330 mm・幅 220 mm・厚さ約 90 mm、底マチで自立）で、"
                               "寸法・質量は代表値。チャックは省略。犬と粒の絵は手続きで描いた。",
                   tags=["ドッグフード", "ペットフード", "犬", "ペット用品", "袋", "dog food", "pet food", "dog food bag", "pet food bag"],
                   photos=[], colors=Colors(label_base=green), images=[img, back], faces=POUCH_FACES)


PRODUCTS = {p.__name__: p for p in (
    frozen_udon_5pack, frozen_takoyaki_bag, frozen_pizza_box, frozen_edamame_bag,
    beer_can_6pack, sake_isshobin_1800ml, shochu_pet_2700ml, umeshu_720ml,
    cracker_box, popcorn_bag, bite_chocolate_bag,
    mirin_pet_1l, rice_vinegar_pet_500ml, miso_cup_750g, ketchup_bottle_500g, sugar_bag_1kg, flour_bag_1kg,
    salad_oil_pet_1000g,
    somen_pack, black_tea_pet_500ml,
    fabric_softener_bottle, dog_food_bag)}
