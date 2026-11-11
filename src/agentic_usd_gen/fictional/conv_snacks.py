"""架空の商品のデザイン: コンビニの菓子・おつまみ・袋もの・小物。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
形・寸法・色・部品構成は Wikimedia Commons の CC0 / パブリックドメインの写真を参考にした（各関数の docstring）。
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np

from ..shapes.pouch import pouch_mesh
from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product, label_canvas, revolve
from .food_fresh_snack import _back_panel, _pouch
from .forms import RevolveForm, _arc
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _face, back_info, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}
WHITE = "#FFFFFF"


# ---------------------------------------------------------------- 共通の小物


def _star(c: Canvas, cx: float, cy: float, r: float, fill: str, points: int = 5, inner: float = 0.45,
          rot: float = -90.0):
    pts = []
    for k in range(points * 2):
        rr = r if k % 2 == 0 else r * inner
        a = math.radians(rot + k * 180 / points)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.polygon(pts, fill=fill)


def _hang_slot(c: Canvas, cx: float, cy: float, w: float, h: float, color: str):
    """吊り下げ穴（ユーロスロット。穴は開けず印刷で表す）。"""
    c.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=color, radius=h / 2)
    c.ellipse(cx - h * 0.9, cy - h * 0.9, cx + h * 0.9, cy + h * 0.9, fill=color)


def _notch(c: Canvas, x: float, y: float, color: str, right: bool = False):
    """袋の側面の切り口（Ｖノッチ）の印と「ここから切れます」。"""
    d = -1 if right else 1
    c.polygon([(x, y - 1.6), (x + d * 2.6, y), (x, y + 1.6)], fill=color)


def _stick(c: Canvas, x0: float, y0: float, x1: float, y1: float, w: float, coat: str, biscuit: str,
           grip: float = 0.22):
    """チョコがけのスティック（先端側 1 - grip がチョコ、手元が素焼きのビスケット）。"""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy * w / 2, ux * w / 2

    def seg(a: float, b: float, color: str):
        ax, ay, bx, by = x0 + ux * n * a, y0 + uy * n * a, x0 + ux * n * b, y0 + uy * n * b
        c.polygon([(ax + px, ay + py), (bx + px, by + py), (bx - px, by - py), (ax - px, ay - py)], fill=color)

    seg(0, grip, biscuit)
    seg(grip, 1, coat)
    # チョコの縁のたれと、つやのハイライト
    gx, gy = x0 + ux * n * grip, y0 + uy * n * grip
    c.ellipse(gx - w * 0.55, gy - w * 0.55, gx + w * 0.55, gy + w * 0.55, fill=coat)
    hx0, hy0 = x0 + ux * n * (grip + 0.08) + px * 0.45, y0 + uy * n * (grip + 0.08) + py * 0.45
    hx1, hy1 = x0 + ux * n * 0.95 + px * 0.45, y0 + uy * n * 0.95 + py * 0.45
    c.line([(hx0, hy0), (hx1, hy1)], mix(coat, WHITE, 0.35), w * 0.16)
    ex, ey = x1, y1
    c.ellipse(ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2, fill=coat)


# ---------------------------------------------------------------- 冷凍チャーハン


def frozen_fried_rice_bag() -> Product:
    """ピロー包装の冷凍チャーハン（立てた袋）。表に皿に盛ったチャーハンの写真、裏に作り方と一括表示。

    参考: https://commons.wikimedia.org/wiki/File:Yakimeshi_Houhi.jpg（CC0。チャーハンの写真として合成）
    """
    W, H = 200.0, 270.0
    red, dark, gold, cream = "#B71C1C", "#5A0E0E", "#F2C14E", "#FFF6E0"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 7, red, seed=seed)
        c.gradient(0, 0, W, H, "#C62828", "#6E1010")
        c.pattern(0, 0, W, H, "waves", mix(red, gold, 0.12), 12, 0.5)
        seal_crimp(c, 0, 0, W, 13, "#C62828", 1.6)
        seal_crimp(c, 0, H - 13, W, H, "#6E1010", 1.6)
        c.rect(0, 13, W, 15, fill=gold)
        c.rect(0, H - 15, W, H - 13, fill=gold)
        return c

    c = base(5001)
    c.rect(0, 15, W, 33, fill=dark)
    c.text(W / 2, 24, "冷凍食品  -18℃以下で保存", 6.0, gold, 800)
    c.text(W / 2, 54, "本格炒め", 12, cream, 900, spacing=1.0)
    c.text(W / 2, 82, "チャーハン", 26, gold, 900, max_w=W - 24, stroke=0.9, stroke_fill=dark)
    c.text(W / 2, 103, "強火で炒めた パラッと食感", 7.0, cream, 800)
    c.ellipse(16, 112, W - 16, 226, fill="#F4EEE2")
    c.ellipse(19, 115, W - 19, 223, outline="#2D5AA0", width=1.4)
    c.photo("snk_fried_rice", 24, 120, W - 24, 218, shape="ellipse", feather=3, crop=(0.10, 0.10, 0.80, 0.80))
    c.ellipse(W - 68, 196, W - 10, 252, fill=gold)
    c.text(W - 39, 214, "450g", 11, dark, 900)
    c.text(W - 39, 230, "2〜3人前", 6.0, dark, 800)
    c.rect(14, 232, 124, 252, fill=cream, radius=4)
    c.text(69, 238.5, "フライパンで 約5分", 5.4, red, 900)
    c.text(69, 246.5, "電子レンジ 600W 約4分", 4.6, INK, 700)
    c.text(14, 227, "※写真は調理例です", 3.2, cream, 500, anchor="lm")
    front = _pouch(c, 5001)

    b = base(5002)
    b.text(W / 2, 24, "本格炒め チャーハン 450g", 7.0, gold, 900)
    b.rect(12, 33, W - 12, H - 20, fill=WHITE, radius=3)
    _back_panel(b, 17, 37, W - 17, H - 52, [
        ("名称", "冷凍米飯類（チャーハン）"),
        ("原材料名", "米（国産）、卵、焼豚、ねぎ、植物油脂、しょうゆ、食塩、にんにく、こしょう／調味料（アミノ酸等）、"
                     "（一部に小麦・卵・大豆・豚肉を含む）"),
        ("内容量", "450g"), ("賞味期限", "上部に記載"), ("保存方法", "-18℃以下で保存してください")], 4.2,
        [("栄養成分表示 1/3袋（150g）当たり", ""), ("エネルギー", "246kcal"), ("たんぱく質", "6.3g"),
         ("脂質", "7.4g"), ("炭水化物", "38.7g"), ("食塩相当量", "1.6g")],
        [("作り方", "フライパンに凍ったまま入れ、中火で約5分炒めてください。油はひかなくてもできます。"
                    "電子レンジは耐熱皿に1/3袋を広げ、ラップをかけずに600Wで約4分温めてください。"),
         ("ご注意", "加熱してお召し上がりください。一度とけたものを再び凍らせると品質が変わります。")], red)
    b.barcode(18, H - 47, 42, 24)
    b.recycle(W - 34, H - 36, 12, "プラ", red, sub="袋")
    back = _pouch(b, 5002)
    return Product(slug="frozen_fried_rice_bag", name="冷凍チャーハン 450g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=0.045), mass_kg=0.46, material="film",
                   description="形は一般的な袋入りの冷凍チャーハン（ピロー包装 高さ 270 mm・幅 200 mm・厚さ 45 mm）で、"
                               "寸法・質量は代表値。表に商品名と写真、裏に作り方・一括表示・栄養成分表示。",
                   tags=["チャーハン", "炒飯", "冷凍食品", "冷凍", "袋", "frozen fried rice bag", "fried rice",
                         "frozen food"],
                   photos=["snk_fried_rice"], colors=Colors(label_base=red), images=[front, back],
                   faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- さきいか


@dataclasses.dataclass
class HangBag:
    """吊り下げ用のヘッダーが付いた袋の絵と寸法（袋 W×H [mm]・膨らんだ厚さ depth [m]・ヘッダーの高さ HH [mm]）。

    images は [表, 裏, ヘッダーの表, ヘッダーの裏]。単体の商品（pouch）と、吊り下げ什器に掛けた固定の部品
    （store_more.hook_display_rack_snacks）で同じ画像を使う。
    """

    images: list[np.ndarray]
    W: float
    H: float
    depth: float
    HH: float
    mass: float

    @property
    def top(self) -> float:
        """膨らんだ袋の上端 z [m]（ヘッダーの下端）。"""
        return pouch_mesh(self.W / 1000, self.H / 1000, self.depth)["size"][2]


HANG_SLOT_Z = 9.0  # ヘッダーの上端から吊り下げ穴の中心まで [mm]


def _bag_header(W: float, HH: float, seed: int, text: str, base: str, accent: str,
                grad: tuple[str, str] = ("#F3E6C8", "#FFFDF6"), crimp: str = "#E8D9B4") -> np.ndarray:
    """袋の上の平らなヘッダー（吊り下げ穴は印刷）。"""
    h = Canvas(W, HH, 10, base, seed)
    h.gradient(0, 0, W, HH, *grad)
    seal_crimp(h, 0, HH - 4, W, HH, crimp, 1.2)
    h.rect(0, 0, W, 2.0, fill=accent)
    _hang_slot(h, W / 2, HANG_SLOT_Z, 14, 4.0, "#3A3A3A")
    h.text(W / 2, 20, text, 4.0, accent, 800)
    return _face(h.array(), "film", seed, 0.8, 4)


def _hang_header(b: HangBag, color: str = "#FFF8E8") -> Part:
    hh = b.HH / 1000
    return _box("Header", (b.W / 1000, 0.0008, hh), (0, 0, b.top + hh / 2 - 0.001), color, "plastic",
                {"front": 2, "back": 3})


def hung_bag_parts(b: HangBag, prefix: str, x: float, y: float, z_hook: float, k: int, color: str) -> list[Part]:
    """フック（中心の高さ z_hook、半径 2.5 mm）に吊り下げ穴で掛けた袋の部品。袋は角の丸い箱で表し、当たり判定なし。

    k は images の先頭の番号（HangBag.images を什器の images の k 番目から足したもの）。"""
    hh = b.HH / 1000
    zt = z_hook + 0.0025 + (HANG_SLOT_Z - 2.0) / 1000  # 穴の上の縁がフックの上に乗る
    top = zt - hh + 0.001  # 袋の上端
    body = Part(name=f"{prefix}Bag", shape="box", size=[b.W / 1000, b.depth * 0.8, b.top],
                center=[x, y, top - b.top / 2], color=color, finish="plastic", faces={"front": k, "back": k + 1},
                collision=False, material="plastic", bevel=b.depth * 0.35)
    head = Part(name=f"{prefix}Header", shape="box", size=[b.W / 1000, 0.0008, hh], center=[x, y, zt - hh / 2],
                color=color, finish="plastic", faces={"front": k + 2, "back": k + 3}, collision=False,
                material="plastic")
    return [body, head]


def dried_squid_hang() -> HangBag:
    """さきいかの袋の絵（dried_squid_bag と hook_display_rack_snacks で共用）。"""
    W, H, depth = 120.0, 165.0, 0.022
    HH = 30.0  # ヘッダー（吊り下げ穴のあるシール部）の高さ [mm]
    navy, red, cream, yellow = "#16305E", "#C62828", "#FFF8E8", "#F5C518"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, cream, seed=seed)
        c.gradient(0, 0, W, H, "#FFFDF6", "#F3E6C8")
        seal_crimp(c, 0, 0, W, 10, "#E8D9B4", 1.2)
        seal_crimp(c, 0, H - 10, W, H, "#E3D2A8", 1.2)
        c.rect(0, 10, W, 26, fill=navy)
        return c

    c = base(5011)
    c.text(W / 2, 18, "おつまみ  珍味", 5.4, yellow, 800, spacing=0.6)
    c.text(W / 2, 40, "さきいか", 17, navy, 900, max_w=W - 14, stroke=0.6, stroke_fill=WHITE)
    c.text(W / 2, 53, "やわらか ソフト仕立て", 5.0, red, 800)
    # 中身の見える窓（透明フィルム越しのさきいか）
    c.rect(12, 60, W - 12, 136, fill="#E9DCC0", radius=8)
    c.photo("snk_dried_squid", 13, 61, W - 13, 135, shape="round", radius=7, crop=(0.08, 0.20, 0.92, 0.75))
    c.rect(12, 60, W - 12, 136, outline=navy, width=0.6, radius=8)
    c.ellipse(W - 40, 116, W - 6, 150, fill=red)
    c.text(W - 23, 129, "40g", 8.0, WHITE, 900)
    c.text(W - 23, 140, "内容量", 3.4, WHITE, 700)
    c.text(14, 143, "ビールのおともに", 4.4, navy, 800, anchor="lm")
    c.text(14, 150, "※写真は中身の例です", 2.8, INK, 500, anchor="lm")
    front = _pouch(c, 5011, 0.9, 16)

    b = base(5012)
    b.text(W / 2, 18, "さきいか 40g", 5.4, yellow, 900)
    b.rect(7, 30, W - 7, H - 13, fill=WHITE, radius=2)
    _back_panel(b, 10, 32.5, W - 10, H - 38, [
        ("名称", "いか加工品"), ("原材料名", "いか（ペルー産）、砂糖、食塩、還元水あめ／ソルビトール、調味料（アミノ酸）、"
                                        "酸味料、甘味料（ステビア）"),
        ("内容量", "40g"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.0,
        [("栄養成分表示 1袋（40g）当たり", ""), ("エネルギー", "112kcal"), ("たんぱく質", "17.6g"), ("脂質", "0.6g"),
         ("炭水化物", "9.2g"), ("食塩相当量", "2.6g")],
        [("ご注意", "開封後はお早めにお召し上がりください。")], navy)
    b.barcode(11, H - 36, 32, 20)
    b.recycle(W - 22, H - 26, 9, "プラ", navy, sub="袋")
    back = _pouch(b, 5012, 0.9, 16)

    imgs = [front, back, _bag_header(W, HH, 5013, "珍味  さきいか", cream, navy),
            _bag_header(W, HH, 5014, "おつまみ  40g", cream, navy)]
    return HangBag(imgs, W, H, depth, HH, 0.046)


def dried_squid_bag() -> Product:
    """吊り下げ用のヘッダー（穴の付いた平らなシール部、部品）がある袋のさきいか。中身の見える窓に写真。

    参考: https://commons.wikimedia.org/wiki/File:HK_Sai_Kung_District_將軍澳_TKO_康城路1號_Lohas_Park_Road_Montara_LOHAS_Park_日出康城商場_The_Lohas_Shopping_Mall_shop_FRESH_新鮮生活_Supermarket_尤魚絲_snack_February_2024_R12S_03.jpg
    （CC0。袋入りのさきいか。中身の写真として合成）
    """
    b = dried_squid_hang()
    return Product(slug="dried_squid_bag", name="さきいか 40g", shape_class="pouch", category="food",
                   dims=Dimensions(b.H / 1000, b.W / 1000, depth=b.depth), mass_kg=b.mass, material="film",
                   description="形は一般的な吊り下げ什器に掛けるおつまみの袋（袋 高さ 165 mm・幅 120 mm に、吊り下げ穴のある"
                               "高さ 30 mm のヘッダーを足した全高 約 190 mm）で、寸法・質量は代表値。ヘッダーは平らな部品で、"
                               "穴は開けず印刷で表す（フックに掛けた売場は hook_display_rack_snacks）。",
                   tags=["さきいか", "おつまみ", "珍味", "いか", "袋", "吊り下げ", "dried squid bag",
                         "shredded squid", "snack"],
                   photos=["snk_dried_squid"], colors=Colors(label_base="#FFF8E8"), images=b.images,
                   faces={"front": 0, "back": 1}, parts=[_hang_header(b)])


# ---------------------------------------------------------------- あたりめ・ビーフジャーキー（吊り下げの珍味の袋）


def _whole_squid(c: Canvas, cx: float, y0: float, y1: float, w: float, rot: float, seed: int):
    """焼いて平たくのしたいか 1 枚（あたりめ）。上が耳（三角のひれ）、下が足。rot は傾き [度]。"""
    rng = np.random.default_rng(seed)
    L = y1 - y0
    a = math.radians(rot)

    def P(x: float, y: float) -> tuple[float, float]:  # 中心線の局所座標（x 横、y 上から下）→ 画像
        yy = y - L / 2
        return cx + x * math.cos(a) - yy * math.sin(a), (y0 + y1) / 2 + x * math.sin(a) + yy * math.cos(a)

    amber, dark, light = "#D9A45A", "#9A6428", "#F1CF92"
    c.polygon([P(0, 0), P(w * 0.62, L * 0.20), P(w * 0.30, L * 0.22), P(-w * 0.30, L * 0.22), P(-w * 0.62, L * 0.20)],
              fill=dark)  # 耳
    c.polygon([P(0, L * 0.02), P(w * 0.52, L * 0.19), P(-w * 0.52, L * 0.19)], fill=amber)
    c.polygon([P(-w * 0.30, L * 0.16), P(w * 0.30, L * 0.16), P(w * 0.36, L * 0.58), P(w * 0.22, L * 0.66),
               P(-w * 0.22, L * 0.66), P(-w * 0.36, L * 0.58)], fill=dark)  # 胴
    c.polygon([P(-w * 0.26, L * 0.18), P(w * 0.26, L * 0.18), P(w * 0.31, L * 0.57), P(w * 0.19, L * 0.63),
               P(-w * 0.19, L * 0.63), P(-w * 0.31, L * 0.57)], fill=amber)
    for k in range(7):  # 焼き色の筋
        yy = L * (0.22 + 0.055 * k)
        c.line([P(-w * 0.24, yy + rng.uniform(-1, 1)), P(w * 0.24, yy + rng.uniform(-1, 1))],
               mix(dark, amber, 0.5), 0.5)
    c.line([P(0, L * 0.20), P(0, L * 0.60)], light, 0.9)
    for k in range(8):  # 足
        x0 = (k - 3.5) * w * 0.055
        x1 = x0 * 2.2 + rng.uniform(-1.5, 1.5)
        c.line([P(x0, L * 0.64), P(x0 * 1.6, L * 0.82), P(x1, L * (0.95 + rng.uniform(0, 0.05)))], dark, 1.5)
        c.line([P(x0, L * 0.64), P(x0 * 1.6, L * 0.82), P(x1, L * (0.95 + rng.uniform(0, 0.05)))], amber, 0.9)


def atarime_hang() -> HangBag:
    """あたりめの袋の絵（atarime_bag と hook_display_rack_snacks で共用）。中身の窓に、絵で描いたいか 2 枚。"""
    W, H, depth = 110.0, 160.0, 0.018
    HH = 30.0
    red, black, paper, gold = "#B71C1C", "#1E1A18", "#FBF6EC", "#D4A017"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, paper, seed=seed)
        c.gradient(0, 0, W, H, "#FFFDF8", "#EFE4CF")
        seal_crimp(c, 0, 0, W, 10, "#E6DAC2", 1.2)
        seal_crimp(c, 0, H - 10, W, H, "#E1D3B6", 1.2)
        c.rect(0, 10, W, 24, fill=red)
        return c

    c = base(5031)
    c.text(W / 2, 17, "炙り  珍味", 5.2, WHITE, 800, spacing=0.6)
    c.text(W / 2, 37, "あたりめ", 16, black, 900, max_w=W - 14)
    c.text(W / 2, 50, "いか一枚を じっくり炙り焼き", 4.4, red, 800)
    c.rect(11, 56, W - 11, 132, fill="#3A2A20", radius=8)  # 中身の窓（暗い台紙の上のいか）
    _whole_squid(c, W / 2 - 18, 59, 129, 30, -8, 5033)
    _whole_squid(c, W / 2 + 18, 60, 130, 30, 9, 5034)
    c.rect(11, 56, W - 11, 132, outline=black, width=0.6, radius=8)
    c.ellipse(W - 34, 113, W - 5, 142, fill=gold)
    c.text(W - 19.5, 125, "25g", 7.2, black, 900)
    c.text(W - 19.5, 134, "内容量", 3.2, black, 700)
    c.text(13, 140, "かむほどに うまみ", 4.4, black, 800, anchor="lm")
    c.text(13, 147, "※絵は中身のイメージです", 2.8, INK, 500, anchor="lm")
    front = _pouch(c, 5031, 0.9, 16)

    b = base(5032)
    b.text(W / 2, 17, "あたりめ 25g", 5.2, WHITE, 900)
    b.rect(7, 28, W - 7, H - 13, fill=WHITE, radius=2)
    _back_panel(b, 10, 30.5, W - 10, H - 38, [
        ("名称", "するめ"), ("原材料名", "するめいか（国産）"), ("内容量", "25g"), ("賞味期限", "上部に記載"),
        ("保存方法", "直射日光・高温多湿を避けて保存")], 3.0,
        [("栄養成分表示 1袋（25g）当たり", ""), ("エネルギー", "84kcal"), ("たんぱく質", "17.3g"), ("脂質", "1.1g"),
         ("炭水化物", "0.1g"), ("食塩相当量", "0.6g")],
        [("ご注意", "かたいので、よくかんでお召し上がりください。")], red)
    b.barcode(11, H - 36, 32, 20)
    b.recycle(W - 22, H - 26, 9, "プラ", black, sub="袋")
    back = _pouch(b, 5032, 0.9, 16)
    grad = ("#EFE4CF", "#FFFDF8")
    imgs = [front, back, _bag_header(W, HH, 5035, "珍味  あたりめ", paper, red, grad, "#E6DAC2"),
            _bag_header(W, HH, 5036, "炙り  25g", paper, red, grad, "#E6DAC2")]
    return HangBag(imgs, W, H, depth, HH, 0.031)


def atarime_bag() -> Product:
    """吊り下げ用のヘッダーがある袋のあたりめ（焼いたするめ 1 枚もの）。中身の窓の絵は架空。"""
    b = atarime_hang()
    return Product(slug="atarime_bag", name="あたりめ 25g", shape_class="pouch", category="food",
                   dims=Dimensions(b.H / 1000, b.W / 1000, depth=b.depth), mass_kg=b.mass, material="film",
                   description="形は一般的な吊り下げ什器に掛けるおつまみの袋（袋 高さ 160 mm・幅 110 mm に、吊り下げ穴のある"
                               "高さ 30 mm のヘッダーを足した全高 約 185 mm）で、寸法・質量は代表値。ヘッダーは平らな部品で、"
                               "穴は開けず印刷で表す（フックに掛けた売場は hook_display_rack_snacks）。窓の中身は絵。",
                   tags=["あたりめ", "するめ", "おつまみ", "珍味", "いか", "袋", "吊り下げ", "dried squid",
                         "grilled dried squid", "atarime", "snack"],
                   photos=[], colors=Colors(label_base="#FBF6EC"), images=b.images,
                   faces={"front": 0, "back": 1}, parts=[_hang_header(b, "#FBF6EC")])


def _jerky(c: Canvas, x0: float, y0: float, x1: float, y1: float, seed: int, n: int = 7):
    """ビーフジャーキーの切れ端を重ねた絵（黒こしょうの粒つき）。"""
    rng = np.random.default_rng(seed)
    for k in range(n):
        cx = rng.uniform(x0 + 12, x1 - 12)
        cy = y0 + (y1 - y0) * (k + 0.5) / n + rng.uniform(-3, 3)
        L, T = rng.uniform(34, 48), rng.uniform(9, 13)
        a = math.radians(rng.uniform(-35, 35))
        pts = []
        for j in range(10):  # ふちの波打った細長い切れ端
            t = j / 9
            pts.append((-L / 2 + L * t, -T / 2 + rng.uniform(-1.2, 1.2)))
        for j in range(10):
            t = 1 - j / 9
            pts.append((-L / 2 + L * t, T / 2 + rng.uniform(-1.2, 1.2)))
        rot = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
        base = rng.choice(["#5E2416", "#6E2C19", "#7A341E"])
        c.polygon(rot, fill=base)
        for _ in range(3):  # つやと筋
            u = rng.uniform(-0.35, 0.35) * L
            v = rng.uniform(-0.25, 0.25) * T
            p0 = (cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a))
            u2 = u + L * 0.25
            p1 = (cx + u2 * math.cos(a) - v * math.sin(a), cy + u2 * math.sin(a) + v * math.cos(a))
            c.line([p0, p1], mix(base, "#C07040", 0.5), 0.7)
        for _ in range(10):
            u, v = rng.uniform(-0.45, 0.45) * L, rng.uniform(-0.4, 0.4) * T
            px, py = cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a)
            c.ellipse(px - 0.5, py - 0.5, px + 0.5, py + 0.5, fill="#1A1210")


def beef_jerky_hang() -> HangBag:
    """ビーフジャーキーの袋の絵（beef_jerky_bag と hook_display_rack_snacks で共用）。中身の窓に、絵で描いた切れ端。"""
    W, H, depth = 120.0, 170.0, 0.020
    HH = 30.0
    brown, orange, cream, black = "#3B2416", "#E8701A", "#F6E9D2", "#1A1210"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 10, brown, seed=seed)
        c.gradient(0, 0, W, H, "#4A2E1C", "#2C1A10")
        seal_crimp(c, 0, 0, W, 10, "#5A3A26", 1.2)
        seal_crimp(c, 0, H - 10, W, H, "#4E3220", 1.2)
        c.rect(0, 10, W, 25, fill=orange)
        return c

    c = base(5041)
    c.text(W / 2, 17.5, "おつまみ  珍味", 5.2, black, 800, spacing=0.6)
    c.text(W / 2, 39, "ビーフジャーキー", 11.5, cream, 900, max_w=W - 12, stroke=0.5, stroke_fill=black)
    c.text(W / 2, 52, "ブラックペッパー", 5.2, orange, 900)
    c.rect(12, 58, W - 12, 138, fill="#D9C3A0", radius=8)  # 中身の見える窓
    _jerky(c, 13, 60, W - 13, 136, 5043)
    c.rect(12, 58, W - 12, 138, outline=cream, width=0.6, radius=8)
    c.ellipse(W - 38, 120, W - 6, 152, fill=orange)
    c.text(W - 22, 133, "40g", 7.6, WHITE, 900)
    c.text(W - 22, 143, "内容量", 3.2, WHITE, 700)
    c.text(14, 147, "やわらか 厚切り", 4.6, cream, 800, anchor="lm")
    c.text(14, 154, "※絵は中身のイメージです", 2.8, cream, 500, anchor="lm")
    front = _pouch(c, 5041, 0.9, 16)

    b = base(5042)
    b.text(W / 2, 17.5, "ビーフジャーキー 40g", 5.2, black, 900)
    b.rect(7, 29, W - 7, H - 13, fill=WHITE, radius=2)
    _back_panel(b, 10, 31.5, W - 10, H - 38, [
        ("名称", "ビーフジャーキー"), ("原材料名", "牛肉（オーストラリア産）、しょうゆ、砂糖、食塩、黒こしょう、"
                                              "香辛料／調味料（アミノ酸等）、酸化防止剤（V.C）、発色剤（亜硝酸Na）"),
        ("内容量", "40g"), ("賞味期限", "上部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.0,
        [("栄養成分表示 1袋（40g）当たり", ""), ("エネルギー", "126kcal"), ("たんぱく質", "20.4g"), ("脂質", "2.4g"),
         ("炭水化物", "5.8g"), ("食塩相当量", "1.9g")],
        [("ご注意", "開封後はお早めにお召し上がりください。")], brown)
    b.barcode(11, H - 36, 32, 20)
    b.recycle(W - 22, H - 26, 9, "プラ", brown, sub="袋")
    back = _pouch(b, 5042, 0.9, 16)
    grad = ("#2C1A10", "#4A2E1C")
    imgs = [front, back, _bag_header(W, HH, 5045, "珍味  ビーフジャーキー", brown, orange, grad, "#5A3A26"),
            _bag_header(W, HH, 5046, "黒こしょう  40g", brown, orange, grad, "#5A3A26")]
    return HangBag(imgs, W, H, depth, HH, 0.048)


def beef_jerky_bag() -> Product:
    """吊り下げ用のヘッダーがある袋のビーフジャーキー（黒こしょう味）。中身の窓の絵は架空。"""
    b = beef_jerky_hang()
    return Product(slug="beef_jerky_bag", name="ビーフジャーキー ブラックペッパー 40g", shape_class="pouch",
                   category="food",
                   dims=Dimensions(b.H / 1000, b.W / 1000, depth=b.depth), mass_kg=b.mass, material="film",
                   description="形は一般的な吊り下げ什器に掛けるおつまみの袋（袋 高さ 170 mm・幅 120 mm に、吊り下げ穴のある"
                               "高さ 30 mm のヘッダーを足した全高 約 195 mm）で、寸法・質量は代表値。ヘッダーは平らな部品で、"
                               "穴は開けず印刷で表す（フックに掛けた売場は hook_display_rack_snacks）。窓の中身は絵。",
                   tags=["ビーフジャーキー", "ジャーキー", "おつまみ", "珍味", "牛肉", "袋", "吊り下げ", "beef jerky",
                         "jerky", "dried meat", "snack"],
                   photos=[], colors=Colors(label_base="#3B2416"), images=b.images,
                   faces={"front": 0, "back": 1}, parts=[_hang_header(b, "#3B2416")])


# ---------------------------------------------------------------- ミックスナッツ


def mixed_nuts_bag() -> Product:
    """チャック付きのスタンドパウチ（立てた袋）。クラフト紙調の地に、中身の見える窓とナッツの写真。

    参考: https://commons.wikimedia.org/wiki/File:Charcoal_roasted_cashews.jpg（CC0。カシューナッツの写真として合成）、
    https://commons.wikimedia.org/wiki/File:Almonds02.jpg（PD。アーモンドの写真として合成）、
    https://commons.wikimedia.org/wiki/File:Ziplock.jpg（PD。チャックの形）
    """
    W, H, depth = 140.0, 200.0, 0.045
    kraft, brown, green, white = "#C49A6C", "#4A2C14", "#3D7A3A", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 9, kraft, seed=seed)
        c.gradient(0, 0, W, H, "#CFA676", "#B48A5C")
        for _ in range(500):  # クラフト紙の繊維
            x, y = c.rng.uniform(0, W), c.rng.uniform(0, H)
            c.line([(x, y), (x + c.rng.uniform(-2, 2), y + c.rng.uniform(-0.6, 0.6))],
                   mix(kraft, c.rng.choice([brown, "#E8C9A0"]), 0.25), 0.15)
        seal_crimp(c, 0, 0, W, 10, "#C9A070", 1.2)
        seal_crimp(c, 0, H - 9, W, H, "#AE8558", 1.2)
        # チャック（2 本の細い畝）と切り口の印
        c.rect(0, 22, W, 23.2, fill=mix(kraft, brown, 0.35))
        c.rect(0, 24.2, W, 25.4, fill=mix(kraft, brown, 0.35))
        _notch(c, 0, 16, brown)
        _notch(c, W, 16, brown, right=True)
        return c

    c = base(5021)
    c.text(W / 2, 16, "ここから切ってください → チャック付", 3.0, brown, 700)
    c.text(W / 2, 38, "素焼き", 9.0, green, 900)
    c.text(W / 2, 56, "ミックスナッツ", 15, brown, 900, max_w=W - 16)
    c.text(W / 2, 68, "MIXED NUTS", 4.6, white, 800, spacing=1.2)
    # 中身の見える窓
    c.rect(18, 76, W - 18, 150, fill="#E4D6BF", radius=14)
    c.photo("snk_cashews", 19, 77, W - 19, 149, shape="round", radius=13, crop=(0.15, 0.15, 0.85, 0.75))
    c.rect(18, 76, W - 18, 150, outline=brown, width=0.6, radius=14)
    c.photo("snk_almonds", 8, 124, 46, 160, shape="ellipse", crop=(0.22, 0.10, 0.80, 0.90), shadow=1.0,
            border=white, border_w=1.2)
    c.rect(48, 154, W - 10, 168, fill=green, radius=7)
    c.text((48 + W - 10) / 2, 161, "食塩・油 不使用", 5.4, white, 900)
    c.text(W / 2, 174, "アーモンド・カシューナッツ・くるみ", 4.2, brown, 800, max_w=W - 16)
    c.text(W / 2, 180.5, "内容量 120g", 4.6, brown, 900)
    front = _pouch(c, 5021, 0.7, 14)

    b = base(5022)
    b.text(W / 2, 16, "素焼きミックスナッツ 120g", 3.6, brown, 900)
    b.rect(8, 30, W - 8, H - 12, fill=white, radius=2)
    _back_panel(b, 11, 32.5, W - 11, H - 40, [
        ("名称", "ミックスナッツ"), ("原材料名", "アーモンド（アメリカ産）、カシューナッツ、くるみ"),
        ("内容量", "120g"), ("賞味期限", "下部に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 3.2,
        [("栄養成分表示 1袋（120g）当たり", ""), ("エネルギー", "727kcal"), ("たんぱく質", "22.8g"),
         ("脂質", "62.4g"), ("炭水化物", "23.0g"), ("食塩相当量", "0g")],
        [("ご注意", "開封後はチャックをしっかり閉めて、お早めにお召し上がりください。"
                    "本品製造工場では落花生を含む製品を生産しています。")], green)
    b.barcode(12, H - 38, 34, 22)
    b.recycle(W - 24, H - 27, 10, "プラ", brown, sub="袋")
    back = _pouch(b, 5022, 0.7, 14)
    return Product(slug="mixed_nuts_bag", name="素焼きミックスナッツ 120g", shape_class="pouch", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=depth), mass_kg=0.13, material="film",
                   description="形は一般的なチャック付きのスタンドパウチ（高さ 200 mm・幅 140 mm）で、寸法・質量は代表値。"
                               "底のガゼットは省略し、チャックと中身の見える窓は絵で表す。",
                   tags=["ミックスナッツ", "ナッツ", "素焼き", "おつまみ", "スタンドパウチ", "mixed nuts stand-up pouch",
                         "mixed nuts", "zipper pouch"],
                   photos=["snk_cashews", "snk_almonds"], colors=Colors(label_base=kraft), images=[front, back],
                   faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- チョコがけスティック


def chocolate_stick_box() -> Product:
    """細長い紙箱（2 袋入り）。正面に斜めに並べたチョコがけのスティックの絵。特定の商品の配色を避け、緑と金にする。

    参考: https://commons.wikimedia.org/wiki/File:Mango_Pocky_sticks.jpg（CC0。スティックの太さと長さ。絵は描き起こし）
    """
    W, D, H = 72.0, 21.0, 150.0
    green, deep, gold, cream = "#1E5B47", "#123A2D", "#D9B25B", "#FBF3E2"
    coat, biscuit = "#4A2516", "#E2B979"
    s = 10

    def face(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, green, seed)
        f.gradient(0, 0, w, h, "#24705A", "#123A2D")
        return f

    fr = face(W, H, 5031)
    fr.pattern(0, 0, W, H, "dots", mix(green, gold, 0.2), 5, 0.35)
    fr.rect(0, 6, W, 8, fill=gold)
    fr.text(W / 2, 18, "チョコがけ", 8.0, cream, 900)
    fr.text(W / 2, 32, "スティック", 11, gold, 900, max_w=W - 8, stroke=0.4, stroke_fill=deep)
    fr.text(W / 2, 42, "CHOCOLATE STICKS", 3.4, cream, 700, spacing=0.6)
    for k in range(7):  # 斜めに並べたスティック
        x = 4 + k * 9.5
        _stick(fr, x - 8, 128 - k * 1.5, x + 18, 52 + k * 1.5, 4.2, coat, biscuit)
    fr.rect(6, 128, W - 6, 140, fill=cream, radius=6)
    fr.text(W / 2, 134, "ビスケット  2袋入", 4.6, deep, 900)
    fr.text(W / 2, 145, "※写真はイメージです", 2.4, cream, 500)
    front = fr

    bk = face(W, H, 5032)
    bk.rect(4, 4, W - 4, H - 4, fill=cream, radius=2)
    back_info(bk, 7, 8, W - 7, [
        ("名称", "チョコレート菓子"), ("原材料名", "小麦粉、砂糖、カカオマス、植物油脂、全粉乳、ショートニング、ココアバター、"
                                            "食塩、イースト／乳化剤、香料、膨脹剤"),
        ("内容量", "2袋（72g）"), ("賞味期限", "底面に記載"), ("保存方法", "28℃以下で保存")], 2.8,
        [("栄養成分表示 1袋（36g）当たり", ""), ("エネルギー", "182kcal"), ("たんぱく質", "2.8g"), ("脂質", "8.3g"),
         ("炭水化物", "24.0g"), ("食塩相当量", "0.2g")], deep, cream)
    bk.barcode(W / 2 - 16, H - 30, 32, 18)
    bk.recycle(14, H - 20, 8, "紙", deep, sub="箱")
    bk.recycle(W - 14, H - 20, 8, "プラ", deep, sub="袋")

    sides = []
    for k, seed in enumerate((5033, 5034)):
        sd = face(D, H, seed)
        sd.vtext(D / 2, 14, "チョコがけスティック", 6.2, cream, 900, gap=0.05)
        sd.rect(2.5, 120, D - 2.5, 142, fill=gold, radius=2)
        sd.vtext(D / 2, 125, "2袋" if k == 0 else "72g", 4.6, deep, 900)
        sides.append(sd)
    tp = face(W, D, 5035)
    tp.rect(2, 2, W - 2, D - 2, outline=gold, width=0.5, radius=2)
    tp.text(W / 2, D / 2 - 3, "チョコがけスティック", 4.6, cream, 900)
    tp.text(W / 2, D / 2 + 4.5, "← ここを押してあけてください", 2.6, gold, 700)
    bt = face(W, D, 5036)
    bt.text(W / 2, D / 2 - 2, "賞味期限 2027.06.30", 3.0, cream, 600)
    bt.text(W / 2, D / 2 + 4, NOTICE, 2.0, cream, 400)
    imgs = [_face(f.array(), "paper", 5040 + i, 0.8) for i, f in enumerate((front, bk, *sides, tp, bt))]
    return Product(slug="chocolate_stick_box", name="チョコがけスティック 2袋入", shape_class="box", category="food",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.085, material="paper",
                   description="形は一般的な細長い箱入りのチョコがけスティックビスケット（高さ 150 mm・幅 72 mm・奥行き 21 mm）で、"
                               "寸法・質量は代表値。スティックは絵で表す。",
                   tags=["チョコレート", "チョコ菓子", "スティック", "ビスケット", "箱菓子", "お菓子",
                         "chocolate sticks box", "chocolate biscuit sticks", "snack"],
                   photos=[], colors=Colors(label_base=green), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 筒入りポテトチップス


def _canister_form(H: float, D: float, *, cap_h: float, cap_d: float) -> RevolveForm:
    """紙筒（底は金属の巻き締め）に、筒より少し太いプラスチックのふたがかぶさる形。"""
    R, Rc = D / 2, cap_d / 2
    cap_z = H - cap_h
    body = [(0.0, R * 0.95)] + _arc(0.0006, 0.004, R * 0.975, R, 8, "out")[1:] + [(cap_z, R)]
    cap = [(cap_z, Rc), (H - 0.0025, Rc)] + _arc(H - 0.0025, H, Rc, Rc * 0.95, 8, "out")[1:]
    return RevolveForm(body, cap, (0.005, cap_z - 0.002))


def potato_crisps_canister() -> Product:
    """紙筒入りの成型ポテトチップス（回転体）。全周ラベルに商品名と写真、裏に一括表示。ふたは不透明の樹脂。

    参考: https://commons.wikimedia.org/wiki/File:Pringles-165g-to-134g.jpg（CC0。筒の太さと高さ、ふたの形だけを参考にし、
    配色・ロゴは使わない）
    """
    form = _canister_form(0.232, 0.075, cap_h=0.016, cap_d=0.0785)
    sky, navy, white, yellow = "#5BB4E5", "#0F3D6E", "#FFFFFF", "#FFD34D"
    c = label_canvas(form, sky, seed=5051)
    W, H = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, H, "#7CC7EE", "#3C94CB")
    c.pattern(0, 0, W, H, "waves", mix(sky, white, 0.25), 10, 0.5)
    c.rect(0, 0, W, 12, fill=navy)
    c.rect(0, H - 10, W, H, fill=navy)
    c.text(fx, 6, "成型ポテトチップス", 5.0, white, 800)
    c.ellipse(fx - 30, 20, fx + 30, 62, fill=white)
    c.text(fx, 34, "ポテト", 11, navy, 900)
    c.text(fx, 50, "クリスプ", 10, navy, 900)
    c.photo("potato_chips", fx - 34, 70, fx + 34, 140, shape="ellipse", feather=3, crop=(0.10, 0.15, 0.90, 0.85))
    c.rect(fx - 28, 148, fx + 28, 166, fill=navy, radius=9)
    c.text(fx, 157, "うすしお味", 8.0, yellow, 900)
    c.text(fx, 178, "重ねてサクッと", 5.4, navy, 800)
    c.text(fx, 192, "内容量 110g", 5.4, white, 900)
    c.text(fx, H - 5, "※写真はイメージです", 3.0, white, 500)
    # 横（正面と裏のあいだ）: 大きな縦書き
    c.vtext(0.5 * W, 24, "うすしお", 12, white, 900)
    c.vtext(0.0 * W + 8, 24, "ポテト", 10, navy, 900)
    c.vtext(W - 8, 24, "ポテト", 10, navy, 900)
    c.text(bx, 6, "POTATO CRISPS", 4.4, white, 800, spacing=0.6)
    c.rect(bx - 30, 16, bx + 30, H - 14, fill=white, radius=3)
    y = back_info(c, bx - 28, 19, bx + 28, [
        ("名称", "ポテトチップス"), ("原材料名", "乾燥じゃがいも（アメリカ製造）、植物油脂、コーンフラワー、小麦でん粉、米粉、"
                                             "食塩、ぶどう糖／乳化剤、調味料（アミノ酸）"),
        ("内容量", "110g"), ("賞味期限", "底面に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")], 2.6,
        [("栄養成分表示 1筒（110g）当たり", ""), ("エネルギー", "583kcal"), ("たんぱく質", "4.6g"), ("脂質", "36.3g"),
         ("炭水化物", "58.3g"), ("食塩相当量", "1.3g")])
    assert y < H - 46, y
    c.barcode(bx - 26, H - 42, 30, 22)
    c.recycle(bx + 14, H - 36, 8, "紙", navy, sub="筒")
    c.recycle(bx + 24, H - 36, 8, "プラ", navy, sub="ふた")
    label = edge_shade(finish(c.array(), "paper", 5051, 0.7), 6, 0.08)
    return Product(slug="potato_crisps_canister", name="成型ポテトチップス うすしお味 110g", category="food",
                   mass_kg=0.155, material="paper",
                   description="形は一般的な筒入りの成型ポテトチップス（紙筒 直径 75 mm・全高 232 mm に、直径 78.5 mm の"
                               "樹脂のふた）で、寸法・質量は代表値。",
                   tags=["ポテトチップス", "成型ポテトチップス", "うすしお", "スナック菓子", "筒", "potato crisps canister",
                         "potato chips", "snack"],
                   photos=["potato_chips"], colors=Colors(cap="#E8F1F7", label_base=sky),
                   **revolve(form, label=label, body_fill="#8C8C8C"))


# ---------------------------------------------------------------- コーンスナック（駄菓子）


def corn_puff_stick() -> Product:
    """駄菓子の棒状のコーンスナック 1 本（細長い小袋。寝かせた向き）。窓に写真。

    参考: https://commons.wikimedia.org/wiki/File:Кукурузные_палочки.JPG（PD。コーンスナックの写真として合成）
    """
    L, Wd = 150.0, 48.0
    yellow, orange, red, white = "#FFD23F", "#F08A24", "#D32F2F", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 14, yellow, seed=seed)
        c.gradient(0, 0, L, Wd, "#FFE066", "#F7B731")
        c.pattern(0, 0, L, Wd, "dots", mix(yellow, orange, 0.35), 4.5, 0.5)
        seal_crimp(c, 0, 0, 9, Wd, "#FFE066", 1.0, vertical=True)
        seal_crimp(c, L - 9, 0, L, Wd, "#F7B731", 1.0, vertical=True)
        return c

    c = base(5061)
    c.rect(12, 4, 74, 44, fill=red, radius=6)
    c.text(43, 15, "コーン", 9.5, white, 900, stroke=0.4, stroke_fill="#7A1010")
    c.text(43, 28, "スナック", 9.5, yellow, 900, stroke=0.4, stroke_fill="#7A1010")
    c.text(43, 39, "チーズ味", 5.6, white, 900)
    c.rect(78, 9, L - 13, 39, fill="#FFF3C4", radius=10)
    c.photo("snk_corn_puff", 79, 10, L - 14, 38, shape="round", radius=9, crop=(0.20, 0.25, 0.80, 0.60))
    c.rect(78, 9, L - 13, 39, outline=orange, width=0.5, radius=10)
    _star(c, L - 20, 8, 6.5, red)
    c.text(L - 20, 8.3, "1本", 3.0, white, 900)
    c.text(108, 43.5, "※写真はイメージです", 2.2, INK, 500)
    front = trim_safe(edge_shade(finish(c.array(), "film", 5061, 1.0), 14, 0.18))

    b = base(5062)
    b.rect(12, 3, L - 12, Wd - 3, fill=white, radius=2)
    y = b.table(14, 5, 84, "", [("名称", "スナック菓子"), ("原材料名", "コーングリッツ、植物油脂、チーズパウダー、砂糖、食塩／調味料（アミノ酸等）、香料"),
                                ("内容量", "6g"), ("賞味期限", "右下に記載"), ("保存方法", "直射日光・高温多湿を避けて保存")],
                1.9, INK, white)
    b.paragraph(14, y + 0.8, 84, NOTICE, 1.6, INK, 500)
    b.table(87, 5, L - 14, "栄養成分表示 1本当たり", [("エネルギー", "33kcal"), ("脂質", "2.0g"), ("炭水化物", "3.4g"),
                                                     ("食塩相当量", "0.06g")], 1.9, INK, white)
    b.barcode(88, Wd - 17, 24, 12)
    b.recycle(L - 20, Wd - 11, 6, "プラ", red)
    back = trim_safe(edge_shade(finish(b.array(), "film", 5062, 1.0), 14, 0.18))
    return Product(slug="corn_puff_stick", name="コーンスナック チーズ味 1本", shape_class="pouch", category="food",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.024), mass_kg=0.007, material="film",
                   orientation="lying",
                   description="形は一般的な駄菓子の棒状のコーンスナック 1 本入りの小袋（長さ 150 mm・幅 48 mm・厚さ 24 mm）で、"
                               "寸法・質量は代表値。",
                   tags=["駄菓子", "コーンスナック", "スナック菓子", "チーズ", "corn puff stick bag", "corn snack",
                         "dagashi"],
                   photos=["snk_corn_puff"], colors=Colors(label_base=yellow), images=[front, back],
                   faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- トレーディングカード


def trading_card_pack() -> Product:
    """架空のカードゲームの拡張パック（5 枚入りの細い袋。寝かせた向き）。ホログラム調のフィルム。

    参考: https://commons.wikimedia.org/wiki/File:RWBY_Trading_Cards_Foil_02.jpg（CC0。袋の大きさと上下のシール。絵は描き起こし）
    """
    PW, PH = 72.0, 118.0  # 縦に描いてから、シールが左右に来るよう横に回す
    night, violet, cyan, gold, white = "#0B1640", "#5B2A9E", "#36D1DC", "#F2C94C", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(PW, PH, 14, night, seed=seed)
        c.gradient(0, 0, PW, PH, "#1A2A6C", "#0B1033")
        for k, col in enumerate(("#FF6FD8", "#36D1DC", "#F2C94C", "#7CFFB2", "#8E7CFF")):  # ホログラムの帯
            c.pattern(0, 8 + k * 2, PW, PH - 8, "stripes", mix(night, col, 0.18), 11, 0.6)
        seal_crimp(c, 0, 0, PW, 8, "#8A93B8", 0.9)
        seal_crimp(c, 0, PH - 8, PW, PH, "#8A93B8", 0.9)
        _notch(c, 0, 11, "#C9CEE2")
        return c

    c = base(5071)
    _star(c, PW / 2, 46, 26, mix(violet, cyan, 0.3), points=8, inner=0.55)
    _star(c, PW / 2, 46, 18, gold, points=5, inner=0.48)
    c.ellipse(PW / 2 - 7, 39, PW / 2 + 7, 53, fill=white)
    c.text(PW / 2, 16, "トレーディングカードゲーム", 3.4, cyan, 800)
    c.text(PW / 2, 78, "ほしぞら", 10, white, 900, stroke=0.6, stroke_fill=violet)
    c.text(PW / 2, 90, "デュエル", 10, gold, 900, stroke=0.6, stroke_fill=violet)
    c.rect(8, 96, PW - 8, 103, fill=violet, radius=3.5)
    c.text(PW / 2, 99.5, "拡張パック 第1弾「蒼き流星」", 3.2, white, 800, max_w=PW - 18)
    c.text(14, 108, "5枚入り", 3.6, cyan, 900, anchor="lm")
    c.text(PW - 12, 108, "6才以上", 3.0, white, 700, anchor="rm")
    front = np.rot90(trim_safe(edge_shade(finish(c.array(), "film", 5071, 1.2), 10, 0.16)), 1).copy()

    b = base(5072)
    b.text(PW / 2, 15, "ほしぞらデュエル 拡張パック", 3.6, gold, 900)
    b.rect(6, 20, PW - 6, PH - 11, fill=white, radius=2)
    y = b.table(8, 22, PW - 8, "", [("品名", "トレーディングカード"), ("内容", "1パック 5枚入り"),
                                    ("材質", "紙"), ("対象年齢", "6才以上")], 2.6)
    y = b.paragraph(8, y + 1.5, PW - 8,
                    "カードの種類はえらべません。どのカードが入っているかは開けるまでわかりません。"
                    "袋を開けるときは、手を切らないよう注意してください。小さなお子様の手の届かないところに保管してください。\n"
                    + NOTICE, 2.3, INK, 400)
    assert y < PH - 36, y
    b.barcode(9, PH - 34, 30, 18)
    b.recycle(PW - 16, PH - 26, 8, "プラ", night, sub="袋")
    back = np.rot90(trim_safe(edge_shade(finish(b.array(), "film", 5072, 1.2), 10, 0.16)), 1).copy()
    return Product(slug="trading_card_pack", name="トレーディングカード 拡張パック 5枚入", shape_class="pouch",
                   category="household", dims=Dimensions(PH / 1000, PW / 1000, depth=0.004), mass_kg=0.012,
                   material="film", orientation="lying",
                   description="形は一般的なトレーディングカードの拡張パック（袋 118 × 72 mm・厚さ 4 mm、カード 5 枚入り）を"
                               "寝かせた向きで、寸法・質量は代表値。カードゲームは架空のもの。",
                   tags=["トレーディングカード", "カードゲーム", "拡張パック", "おもちゃ", "trading card pack",
                         "booster pack", "trading cards"],
                   photos=[], colors=Colors(label_base=night), images=[front, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- キャットフード


def _cat(c: Canvas, cx: float, cy: float, r: float, fur: str, line: str):
    """ねこの顔の絵（耳・目・鼻・ひげ）。"""
    c.polygon([(cx - r * 0.92, cy - r * 0.15), (cx - r * 0.78, cy - r * 1.15), (cx - r * 0.25, cy - r * 0.78)], fill=fur)
    c.polygon([(cx + r * 0.92, cy - r * 0.15), (cx + r * 0.78, cy - r * 1.15), (cx + r * 0.25, cy - r * 0.78)], fill=fur)
    c.polygon([(cx - r * 0.75, cy - r * 0.4), (cx - r * 0.7, cy - r * 0.95), (cx - r * 0.38, cy - r * 0.7)],
              fill="#F4A9B8")
    c.polygon([(cx + r * 0.75, cy - r * 0.4), (cx + r * 0.7, cy - r * 0.95), (cx + r * 0.38, cy - r * 0.7)],
              fill="#F4A9B8")
    c.ellipse(cx - r, cy - r * 0.85, cx + r, cy + r * 0.8, fill=fur)
    for sx in (-1, 1):
        ex = cx + sx * r * 0.38
        c.ellipse(ex - r * 0.16, cy - r * 0.25, ex + r * 0.16, cy + r * 0.12, fill="#4CAF50")
        c.ellipse(ex - r * 0.05, cy - r * 0.2, ex + r * 0.05, cy + r * 0.08, fill="#111111")
        for dy in (-0.05, 0.12):
            c.line([(cx + sx * r * 0.3, cy + r * 0.3), (cx + sx * r * 1.15, cy + r * (0.2 + dy))], line, r * 0.03)
    c.polygon([(cx - r * 0.1, cy + r * 0.18), (cx + r * 0.1, cy + r * 0.18), (cx, cy + r * 0.3)], fill="#E57373")


def cat_food_pouch() -> Product:
    """レトルトパウチのキャットフード（立てた平たい袋）。ねこの顔とまぐろの絵、切り口の印。

    参考: https://commons.wikimedia.org/wiki/File:20250828_Sheba_Auchan_Mikołów_03.jpg（CC0。売り場に並ぶパウチの大きさと形だけを参考にし、
    配色・ロゴは使わない）
    """
    W, H, depth = 88.0, 128.0, 0.014
    blue, navy, salmon, white, cream = "#2F7FC1", "#0F2E55", "#E9967A", "#FFFFFF", "#F8F2E6"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 12, blue, seed=seed)
        c.gradient(0, 0, W, H, "#4A9AD8", "#1E5A94")
        c.pattern(0, 0, W, H, "waves", mix(blue, white, 0.15), 7, 0.4)
        seal_crimp(c, 0, 0, W, 9, "#4A9AD8", 1.0)
        seal_crimp(c, 0, H - 7, W, H, "#1E5A94", 1.0)
        _notch(c, 0, 14, white)
        _notch(c, W, 14, white, right=True)
        return c

    c = base(5081)
    c.text(W / 2, 14, "ここから切れます", 2.6, white, 700)
    c.text(W / 2, 24, "ねこのごちそう", 8.0, white, 900, max_w=W - 10, stroke=0.4, stroke_fill=navy)
    c.text(W / 2, 33, "まぐろ ゼリー仕立て", 4.8, "#FFE082", 900)
    # まぐろのほぐし身の器
    c.ellipse(10, 70, W - 10, 108, fill=cream)
    c.ellipse(16, 74, W - 16, 100, fill="#D8C9B0")
    for _ in range(60):
        x, y = c.rng.uniform(22, W - 22), c.rng.uniform(77, 97)
        w = c.rng.uniform(3, 7)
        c.ellipse(x - w / 2, y - w * 0.3, x + w / 2, y + w * 0.3,
                  fill=c.rng.choice([salmon, "#D7745A", "#F2B49C", "#C9604A"]))
    for _ in range(14):  # ゼリーのつや
        x, y = c.rng.uniform(24, W - 24), c.rng.uniform(78, 96)
        c.ellipse(x - 1.6, y - 0.8, x + 1.6, y + 0.8, fill="#F6E4D0")
    _cat(c, W / 2, 54, 15, "#F2F2F0", "#555555")
    c.rect(8, 110, W - 8, 120, fill=navy, radius=5)
    c.text(W / 2, 115, "一般食  成猫用  70g", 4.0, white, 900)
    c.text(W / 2, 124.5, "※写真はイメージです", 2.0, white, 500)
    front = _pouch(c, 5081, 0.9, 12)

    b = base(5082)
    b.text(W / 2, 14, "ねこのごちそう まぐろ 70g", 3.4, white, 900)
    b.rect(5, 18, W - 5, H - 9, fill=white, radius=2)
    y = b.table(7, 20, W - 7, "", [
        ("名称", "ペットフード（一般食）"), ("原材料名", "まぐろ、鶏肉、増粘多糖類、ビタミン E"),
        ("成分", "たんぱく質 10.0%以上、脂質 0.3%以上、粗繊維 0.1%以下、灰分 2.0%以下、水分 87.0%以下"),
        ("内容量", "70g"), ("賞味期限", "裏面下部に記載"), ("原産国", "日本")], 2.5)
    b.table(7, y + 1.2, W - 7, "給与量の目安（1日）", [("体重 3kg", "2袋"), ("体重 5kg", "3袋")], 2.5)
    b.paragraph(7, y + 15, W - 7, "総合栄養食と一緒に与えてください。開封後は器に移し、冷蔵庫で保存して当日中に与えてください。"
                "\n" + NOTICE, 2.1, INK, 400)
    b.barcode(8, H - 28, 26, 15)
    b.recycle(W - 18, H - 21, 8, "プラ", navy, sub="袋")
    back = _pouch(b, 5082, 0.9, 12)
    return Product(slug="cat_food_pouch", name="キャットフード パウチ まぐろ 70g", shape_class="pouch",
                   category="household", dims=Dimensions(H / 1000, W / 1000, depth=depth), mass_kg=0.074,
                   material="film",
                   description="形は一般的なキャットフードのレトルトパウチ（高さ 128 mm・幅 88 mm・厚さ 14 mm）で、"
                               "寸法・質量は代表値。中身の絵は描き起こし。",
                   tags=["キャットフード", "ペットフード", "パウチ", "ねこ", "まぐろ", "cat food pouch",
                         "pet food", "retort pouch"],
                   photos=[], colors=Colors(label_base=blue), images=[front, back], faces={"front": 0, "back": 1})


# ---------------------------------------------------------------- 割り箸


def disposable_chopsticks_bundle() -> Product:
    """紙の袋で個包装した割り箸 50 膳を、透明な袋に入れて寝かせた束（箱）。正面は袋の縁、上面に袋の絵とラベル。

    参考: https://commons.wikimedia.org/wiki/File:Chopstick_cover.jpg（PD。割り箸の紙の袋）
    """
    W, D, H = 232.0, 100.0, 46.0  # 長さ（X）× 奥行き（Y、5 列）× 高さ（10 段）
    paper, wood, red, film = "#F7F3EA", "#E6CFA0", "#B3261E", "#EEF3F6"
    cols, rows = 5, 10
    sleeve = 210.0  # 袋の長さ（両端のフィルムのシール分を残す）
    m = (W - sleeve) / 2
    s = 8

    def film_canvas(w: float, h: float, seed: int) -> Canvas:
        f = Canvas(w, h, s, film, seed)
        f.gradient(0, 0, w, h, "#F4F7F9", "#DCE4EA")
        return f

    def long_side(seed: int) -> Canvas:
        """正面・裏面: 10 段に重なった袋の縁。"""
        f = film_canvas(W, H, seed)
        seal_crimp(f, 0, 0, m, H, "#E3EAEF", 1.0, vertical=True)
        seal_crimp(f, W - m, 0, W, H, "#E3EAEF", 1.0, vertical=True)
        rh = H / rows
        for r in range(rows):
            y0 = r * rh
            f.rect(m, y0 + 0.25, W - m, y0 + rh - 0.25, fill=paper, radius=1.2)
            f.rect(m, y0 + rh - 1.0, W - m, y0 + rh - 0.25, fill=mix(paper, "#8A8170", 0.25))
        return f

    def top(seed: int, label: bool) -> Canvas:
        """上面: 5 列に並んだ袋（文字入り）と、真ん中の帯のラベル。"""
        f = film_canvas(W, D, seed)
        seal_crimp(f, 0, 0, m, D, "#E3EAEF", 1.0, vertical=True)
        seal_crimp(f, W - m, 0, W, D, "#E3EAEF", 1.0, vertical=True)
        cw = D / cols
        for k in range(cols):
            y0 = k * cw
            f.rect(m, y0 + 0.4, W - m, y0 + cw - 0.4, fill=paper, radius=1.5)
            f.rect(m, y0 + cw - 2.0, W - m, y0 + cw - 0.4, fill=mix(paper, "#8A8170", 0.18))
            f.rect(m + 4, y0 + cw / 2 - 3.2, m + 30, y0 + cw / 2 + 3.2, fill=red, radius=1)
            f.text(m + 17, y0 + cw / 2, "おてもと", 4.0, WHITE, 900)
            f.rect(W - m - 6, y0 + 2.5, W - m - 1, y0 + cw - 3, fill=mix(paper, wood, 0.35))  # 袋の口から見える箸
        if label:
            f.rect(W / 2 - 34, 10, W / 2 + 34, D - 10, fill=WHITE, radius=3)
            f.rect(W / 2 - 34, 10, W / 2 + 34, 26, fill=red, radius=3)
            f.text(W / 2, 18, "個包装", 7.0, WHITE, 900)
            f.text(W / 2, 37, "割り箸", 13, INK, 900)
            f.text(W / 2, 51, "50膳入", 9.0, red, 900)
            f.text(W / 2, 61, "長さ 21cm  天然木", 4.2, INK, 700)
            f.barcode(W / 2 - 18, 67, 36, 20)
        else:
            f.rect(W / 2 - 34, 12, W / 2 + 34, D - 12, fill=WHITE, radius=3)
            y = f.table(W / 2 - 32, 14, W / 2 + 32, "", [("品名", "割り箸（個包装）"), ("材質", "白樺（天然木）"),
                                                         ("寸法", "長さ 21cm"), ("入数", "50膳")], 3.0)
            f.paragraph(W / 2 - 32, y + 1.2, W / 2 + 32, "割るときはささくれに注意してください。" + NOTICE, 2.6, INK, 400)
            f.recycle(W / 2 + 24, D - 20, 9, "プラ", INK, sub="袋")
        return f

    def end(seed: int) -> Canvas:
        """端面: 5 列 × 10 段の袋の口と、のぞく箸の端。"""
        f = film_canvas(D, H, seed)
        cw, rh = D / cols, H / rows
        for k in range(cols):
            for r in range(rows):
                x0, y0 = k * cw, r * rh
                f.rect(x0 + 0.4, y0 + 0.3, x0 + cw - 0.4, y0 + rh - 0.3, fill=paper, radius=1.0)
                f.rect(x0 + cw / 2 - 5, y0 + rh / 2 - 1.3, x0 + cw / 2 - 0.4, y0 + rh / 2 + 1.3, fill=wood)
                f.rect(x0 + cw / 2 + 0.4, y0 + rh / 2 - 1.3, x0 + cw / 2 + 5, y0 + rh / 2 + 1.3, fill=wood)
        return f

    canvases = [long_side(5091), long_side(5092), end(5093), end(5094), top(5095, True), top(5096, False)]
    imgs = [_face(f.array(), "film", 5100 + i, 0.7, 6) for i, f in enumerate(canvases)]
    return Product(slug="disposable_chopsticks_bundle", name="割り箸 個包装 50膳", shape_class="box",
                   category="household", dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.24,
                   material="plastic",
                   description="形は一般的な紙の袋で個包装した割り箸（長さ 21 cm）50 膳を透明な袋に入れた束"
                               "（長さ 232 mm・幅 100 mm・高さ 46 mm）で、寸法・質量は代表値。袋と箸は絵で表す。",
                   tags=["割り箸", "割りばし", "箸", "個包装", "使い捨て", "disposable chopsticks bundle",
                         "chopsticks", "wooden chopsticks"],
                   photos=[], colors=Colors(label_base=film), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- レジ袋


def shopping_bag_l() -> Product:
    """有料のレジ袋 L サイズを、小さくたたんだ状態（寝かせた平たい袋）。乳白のフィルムに折り目と取っ手の線。

    参考: https://commons.wikimedia.org/wiki/File:White_plastic_bag_on_white_kitchen_counter.jpg（CC0。乳白のレジ袋の色とつや）
    """
    L, Wd = 170.0, 120.0
    milk, crease, green, white = "#EEF0EE", "#C9CEC9", "#2E7D32", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 10, milk, seed=seed)
        c.gradient(0, 0, L, Wd, "#F6F7F5", "#DCE0DC")
        # たたんだフィルムの重なり（層の縁）と、細かいしわ
        for k in range(4):
            x = 6 + k * 3.0
            c.line([(x, 2), (x + 0.6, Wd - 2)], crease, 0.35)
            c.line([(L - x, 2), (L - x - 0.6, Wd - 2)], crease, 0.35)
        for _ in range(26):
            x, y = c.rng.uniform(10, L - 10), c.rng.uniform(6, Wd - 6)
            a = c.rng.uniform(0, math.pi)
            ln = c.rng.uniform(6, 22)
            c.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], mix(milk, crease, 0.7), 0.25)
        c.line([(4, Wd / 2), (L - 4, Wd / 2 + 1.0)], crease, 0.5)  # 半分に折った折り目
        return c

    c = base(5111)
    # 取っ手の切り欠きの線（たたんだ袋の上に透けて見える）
    c.line([(L * 0.32, 8), (L * 0.36, 24), (L * 0.64, 24), (L * 0.68, 8)], mix(crease, "#9AA09A", 0.4), 0.5)
    c.text(L / 2, 46, "レジ袋", 13, green, 900)
    c.rect(L / 2 - 20, 54, L / 2 + 20, 70, fill=green, radius=3)
    c.text(L / 2, 62, "L", 11, white, 900)
    c.text(L / 2, 80, "植物由来原料 25% 配合", 4.6, green, 800)
    c.text(L / 2, 89, "この袋は有料です  ご協力ありがとうございます", 3.4, green, 600)
    c.recycle(L - 28, Wd - 20, 10, "プラ", green, sub="袋")
    c.text(26, Wd - 14, "45号  ポリエチレン", 3.2, mix(green, milk, 0.2), 600, anchor="lm")
    front = trim_safe(edge_shade(finish(c.array(), "film", 5111, 0.8), 10, 0.10))

    b = base(5112)
    b.text(L / 2, 40, "レジ袋 L", 7.0, green, 900)
    b.paragraph(30, 52, L - 30, "材質：ポリエチレン（バイオマス 25%）\n寸法：横 45cm × 縦 65cm（取っ手を含む）\n"
                "耐荷重の目安：約 8kg\n" + NOTICE, 3.4, mix(green, INK, 0.4), 500)
    back = trim_safe(edge_shade(finish(b.array(), "film", 5112, 0.8), 10, 0.10))
    return Product(slug="shopping_bag_l", name="レジ袋 L サイズ", shape_class="pouch", category="household",
                   dims=Dimensions(L / 1000, Wd / 1000, depth=0.006), mass_kg=0.008, material="film",
                   orientation="lying",
                   description="形は一般的なコンビニの有料のレジ袋 L サイズ（45 号、広げると横 45 cm・縦 65 cm）を"
                               "小さくたたんだ状態（170 × 120 mm・厚さ 6 mm）で、寸法・質量は代表値。折り目と取っ手は絵で表す。",
                   tags=["レジ袋", "買い物袋", "ポリ袋", "有料", "plastic shopping bag", "shopping bag", "carrier bag"],
                   photos=[], colors=Colors(label_base=milk), images=[front, back], faces={"front": 0, "back": 1})


PRODUCTS = {f.__name__: f for f in (frozen_fried_rice_bag, dried_squid_bag, atarime_bag, beef_jerky_bag, mixed_nuts_bag,
                                    chocolate_stick_box, potato_crisps_canister, corn_puff_stick, trading_card_pack, cat_food_pouch,
                                    disposable_chopsticks_bundle, shopping_bag_l)}
