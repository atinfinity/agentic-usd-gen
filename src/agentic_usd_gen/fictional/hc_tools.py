"""Fictional product designs: home-center tools and hardware (hand tools in blister packs, a boxed drill,
screws, tape, cable ties, paint and a brush).

As in products.py, no real product names, brands or logos are used; shapes and sizes are typical values for
the kind of product. Front is -Y. Products are dynamic rigid bodies.
The blister packs are built by `*_pack()` functions that return images and parts in a local frame (card
bottom at z=0, card plane at y=0), so the pegboard wall in hc_fixtures can hang the same packs on its hooks.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product, revolve, label_canvas, top_canvas
from . import forms
from .conv_goods import BOX_FACES, _faces, _hang_hole
from .paint import Canvas, finish, mix
from .products import INK, _box, _cyl, _face, seal_crimp

WHITE = "#FFFFFF"
FILM = "#F2F6F8"  # clear blister / bag tint
STEEL, CHROME = "#9AA0A6", "#D4D7DB"
HC_ORANGE, HC_NAVY = "#E8701A", "#1F3A5F"
CARD_T = 0.0012  # card thickness [m]


@dataclasses.dataclass
class Pack:
    """A product in a local frame: images, parts (face indices into images), size (W, D, H) and mass."""

    images: list[np.ndarray]
    parts: list[Part]
    size: tuple[float, float, float]
    mass: float


def place(pack: Pack, prefix: str, dx: float, dy: float, dz: float, k: int, collision: bool | None = None,
          ) -> list[Part]:
    """The pack's parts moved by (dx, dy, dz), renamed with prefix, face indices shifted by k (images appended
    after k others). collision overrides every part's collision when given."""
    out = []
    for p in pack.parts:
        faces = {f: (None if i is None else i + k) for f, i in p.faces.items()} if p.faces else None
        blank = p.blank + k if isinstance(p.blank, int) else p.blank
        out.append(dataclasses.replace(p, name=f"{prefix}{p.name}", center=[p.center[0] + dx, p.center[1] + dy,
                                                                             p.center[2] + dz],
                                       faces=faces, blank=blank,
                                       collision=p.collision if collision is None else collision))
    return out


def _paper(parts: list[Part], *names: str) -> list[Part]:
    for p in parts:
        if p.name in names:
            p.material = "paper"
    return parts


def _card(CW: float, CH: float, seed: int, accent: str, title: str, sub: str, badge: str, base: str = WHITE
          ) -> Canvas:
    """The front of a blister card [mm]: hang hole, a title band at the top and a band at the bottom."""
    c = Canvas(CW, CH, 10, base, seed)
    c.gradient(0, 0, CW, CH, mix(base, WHITE, 0.4), mix(base, "#000000", 0.08))
    c.rect(0, 0, CW, 3, fill=accent)
    _hang_hole(c, CW / 2, 5, "#2A2C30")
    c.rect(0, 14, CW, 32, fill=accent)
    c.text(CW / 2, 21, title, 7.0, WHITE, 900, max_w=CW - 6)
    c.text(CW / 2, 28.5, sub, 3.6, mix(accent, WHITE, 0.8), 800, max_w=CW - 6)
    c.pattern(0, 34, CW, CH - 22, "stripes", mix(base, accent, 0.10), 8, 1.2)
    c.rect(4, CH - 20, CW - 4, CH - 6, fill=accent, radius=2)
    c.text(CW / 2, CH - 13, badge, 4.2, WHITE, 900, max_w=CW - 12)
    c.rect(0, CH - 3, CW, CH, fill=accent)
    return c


def _card_back(CW: float, CH: float, seed: int, accent: str, title: str, rows: list[tuple[str, str]], note: str
               ) -> np.ndarray:
    b = Canvas(CW, CH, 10, WHITE, seed)
    b.gradient(0, 0, CW, CH, "#FFFFFF", "#EEF0F3")
    b.rect(0, 0, CW, 3, fill=accent)
    _hang_hole(b, CW / 2, 5, "#9AA3B2")
    b.rect(0, 14, CW, 22, fill=accent)
    b.text(CW / 2, 18, title, 3.6, WHITE, 800, max_w=CW - 6)
    y = b.table(5, 26, CW - 5, "", rows, 3.0)
    b.paragraph(5, y + 2, CW - 5, note + "\n" + NOTICE, 2.6, INK, 400)
    bw = min(40.0, CW - 20)
    b.barcode((CW - bw) / 2, CH - 26, bw, 20)
    b.rect(0, CH - 3, CW, CH, fill=accent)
    return _face(b.array(), "paper", seed, 0.5)


def _blister(name, w, d, h, z0) -> Part:
    """A clear blister bubble in front of the card (no collision; the item inside has it)."""
    return _box(name, (w, d, h), (0, -CARD_T / 2 - d / 2, z0 + h / 2), FILM, "glass", thin_walled=True,
                collision=False)


def _card_part(CW: float, CH: float) -> Part:
    p = _box("Card", (CW / 1000, CARD_T, CH / 1000), (0, 0, CH / 2000), WHITE, "matte", {"front": 0, "back": 1})
    p.material = "paper"
    return p


# ---------------------------------------------------------------- screwdriver


def screwdriver_pack() -> Pack:
    CW, CH = 70.0, 240.0
    red = "#C62828"
    c = _card(CW, CH, 9301, red, "ドライバー", "プラス +2 × 100mm", "マグネット付き  先端焼入れ")
    front = _face(c.array(), "film", 9301, 0.5)
    back = _card_back(CW, CH, 9302, red, "SCREWDRIVER +2 × 100", [("サイズ", "+2 × 100mm"), ("軸", "クロムバナジウム鋼"),
                                                                  ("グリップ", "樹脂（PP・エラストマー）"), ("全長", "約 205mm")],
                      "電気工事には使えません。先端を人に向けないでください。")
    bd = 0.032
    yc = -CARD_T / 2 - bd / 2
    parts = [_card_part(CW, CH), _blister("Blister", 0.040, bd, 0.205, 0.012),
             _cyl("Handle", (0.028, 0.028, 0.095), (0, yc, 0.165), red, "plastic"),
             _cyl("Grip", (0.030, 0.030, 0.040), (0, yc, 0.150), "#2A2C30", "matte"),
             _cyl("Shaft", (0.006, 0.006, 0.100), (0, yc, 0.068), CHROME),
             _cyl("Tip", (0.0045, 0.0045, 0.008), (0, yc, 0.016), "#3A3D42")]
    for p in parts:
        if p.name == "Grip":
            p.material = "rubber"
        elif p.name in ("Shaft", "Tip"):
            p.material = "steel"
    return Pack([front, back], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.09)


def screwdriver_blister() -> Product:
    p = screwdriver_pack()
    return Product(slug="screwdriver_blister", name="ドライバー プラス +2×100mm", shape_class="assembly",
                   category="household", dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass,
                   material="steel",
                   description="形は一般的な台紙とブリスターに入ったプラスドライバー（+2 × 100 mm、全長約 205 mm、"
                               "台紙 70 × 240 mm）で、寸法・質量は代表値。吊り下げ穴は印刷で表す。",
                   tags=["ドライバー", "プラスドライバー", "工具", "ハンドツール", "ブリスター", "ホームセンター",
                         "screwdriver", "phillips screwdriver", "hand tool", "blister pack"],
                   photos=[], colors=Colors(label_base=WHITE), images=p.images, parts=p.parts)


# ---------------------------------------------------------------- pliers


def pliers_pack() -> Pack:
    CW, CH = 90.0, 220.0
    blue = "#1565C0"
    c = _card(CW, CH, 9311, blue, "ペンチ", "150mm  切断・つかみ", "刃先焼入れ  滑りにくいグリップ")
    front = _face(c.array(), "film", 9311, 0.5)
    back = _card_back(CW, CH, 9312, blue, "COMBINATION PLIERS 150mm", [("全長", "約 150mm"), ("材質", "炭素鋼"),
                                                                      ("切断能力", "軟鉄線 φ2.0mm"),
                                                                      ("グリップ", "塩化ビニル")],
                      "通電中の電線を切らないでください。切断の際は保護めがねを使用してください。")
    bd = 0.022
    yc = -CARD_T / 2 - bd / 2
    grip = "#D32F2F"
    parts = [_card_part(CW, CH), _blister("Blister", 0.064, bd, 0.170, 0.030)]
    for k, s in enumerate((-1, 1)):
        parts += [Part(f"Grip{k}", "box", [0.016, 0.012, 0.100], [s * 0.014, yc, 0.090], [0, -s * 7.0, 0],
                       color=grip, finish="plastic", material="pvc"),
                  Part(f"Jaw{k}", "box", [0.011, 0.010, 0.045], [s * 0.0055, yc, 0.168], [0, s * 3.0, 0],
                       color=STEEL, finish="metal", material="steel")]
    parts.append(Part("Pivot", "cylinder", [0.022, 0.022, 0.014], [0, yc, 0.144], [90.0, 0, 0], color=STEEL,
                      finish="metal", material="steel"))
    return Pack([front, back], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.20)


def pliers_blister() -> Product:
    p = pliers_pack()
    return Product(slug="pliers_blister", name="ペンチ 150mm", shape_class="assembly", category="household",
                   dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass, material="steel",
                   description="形は一般的な台紙とブリスターに入ったペンチ（全長約 150 mm、台紙 90 × 220 mm）で、"
                               "寸法・質量は代表値。柄・刃は直方体で近似。吊り下げ穴は印刷で表す。",
                   tags=["ペンチ", "プライヤー", "工具", "ハンドツール", "ブリスター", "ホームセンター", "pliers",
                         "combination pliers", "hand tool", "blister pack"],
                   photos=[], colors=Colors(label_base=WHITE), images=p.images, parts=p.parts)


# ---------------------------------------------------------------- tape measure


def tape_measure_pack() -> Pack:
    CW, CH = 100.0, 160.0
    yellow = "#F9B000"
    c = _card(CW, CH, 9321, HC_NAVY, "コンベックス", "5.5m × 25mm  メートル目盛", "ロック付き  JIS 1級", "#FFFFFF")
    front = _face(c.array(), "film", 9321, 0.5)
    back = _card_back(CW, CH, 9322, HC_NAVY, "TAPE MEASURE 5.5m", [("長さ", "5.5m"), ("テープ幅", "25mm"),
                                                                 ("精度", "JIS 1級"), ("ケース", "ABS 樹脂")],
                      "テープを急に戻すと手を切るおそれがあります。")
    k = Canvas(68, 68, 10, yellow, 9323)  # the body's front label
    k.gradient(0, 0, 68, 68, "#FFC533", "#E09A00")
    k.ellipse(8, 8, 60, 60, fill="#2A2C30")
    k.ellipse(12, 12, 56, 56, fill="#3A3D42")
    k.text(34, 28, "5.5m", 11, yellow, 900)
    k.text(34, 41, "25mm", 6, WHITE, 800)
    k.text(34, 50, "LOCK", 4, "#C9CDD1", 800, spacing=0.6)
    body = _face(k.array(), "film", 9323, 0.3)
    bd = 0.040
    yc = -CARD_T / 2 - bd / 2
    parts = [_card_part(CW, CH), _blister("Blister", 0.082, bd, 0.088, 0.022),
             Part("Body", "box", [0.068, 0.032, 0.068], [0, yc + 0.003, 0.064], color=yellow, finish="plastic",
                  faces={"front": 2}, bevel=0.012),
             _box("Lock", (0.012, 0.010, 0.020), (0.022, yc + 0.003, 0.100), "#2A2C30", "matte"),
             _box("Blade", (0.026, 0.020, 0.004), (0, yc + 0.003, 0.028), "#F2D21B", "plastic"),
             _box("Hook", (0.028, 0.004, 0.010), (0, yc + 0.003 - 0.010, 0.027), CHROME, "metal")]
    return Pack([front, back, body], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.24)


def tape_measure_blister() -> Product:
    p = tape_measure_pack()
    return Product(slug="tape_measure_blister", name="コンベックス 5.5m×25mm", shape_class="assembly",
                   category="household", dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass,
                   material="plastic",
                   description="形は一般的な台紙とブリスターに入ったメジャー（コンベックス 5.5 m・テープ幅 25 mm、"
                               "ケース約 68 mm 角、台紙 100 × 160 mm）で、寸法・質量は代表値。吊り下げ穴は印刷で表す。",
                   tags=["メジャー", "コンベックス", "巻尺", "スケール", "工具", "ブリスター", "ホームセンター",
                         "tape measure", "measuring tape", "blister pack"],
                   photos=[], colors=Colors(label_base=WHITE), images=p.images, parts=p.parts)


# ---------------------------------------------------------------- screws


def _screws(w: float, h: float, seed: int) -> np.ndarray:
    """A pile of cross-head wood screws seen through the blister [mm]."""
    c = Canvas(w, h, 10, "#8E8F8C", seed)
    c.gradient(0, 0, w, h, "#B5B6B2", "#7C7D79")
    rng = c.rng
    for _ in range(int(w * h / 55)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(16, 26)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        shade = mix("#C9CAC5", "#6E6F6B", rng.uniform(0, 0.6))
        c.line([(x - dx, y - dy), (x + dx, y + dy)], shade, 2.2)
        for t in np.linspace(-0.4, 0.9, 7):  # thread
            px, py = x + dx * t, y + dy * t
            c.line([(px - dy * 0.12, py + dx * 0.12), (px + dy * 0.12, py - dx * 0.12)], mix(shade, "#000000", 0.3), 0.4)
        c.ellipse(x - dx - 3, y - dy - 3, x - dx + 3, y - dy + 3, fill=mix(shade, WHITE, 0.25))
        c.line([(x - dx - 1.8, y - dy), (x - dx + 1.8, y - dy)], "#4A4B48", 0.6)
        c.line([(x - dx, y - dy - 1.8), (x - dx, y - dy + 1.8)], "#4A4B48", 0.6)
    return finish(c.array(), "metal", seed, 0.6)


def screw_pack() -> Pack:
    CW, CH = 80.0, 140.0
    green = "#2E7D32"
    c = _card(CW, CH, 9331, green, "木ねじ", "3.8 × 32mm  約 60本入", "ユニクロめっき  十字穴")
    front = _face(c.array(), "film", 9331, 0.5)
    back = _card_back(CW, CH, 9332, green, "WOOD SCREWS 3.8 × 32mm", [("呼び径", "3.8mm"), ("長さ", "32mm"),
                                                                     ("入数", "約 60本"), ("材質", "鉄（ユニクロめっき）")],
                      "下穴をあけてからねじ込むと木が割れにくくなります。")
    pile = _screws(56, 62, 9333)
    bd = 0.014
    yc = -CARD_T / 2 - bd / 2
    parts = [_card_part(CW, CH), _blister("Blister", 0.062, bd, 0.072, 0.034),
             _box("Screws", (0.056, 0.010, 0.062), (0, yc + 0.001, 0.070), "#8E8F8C", "metal", {"front": 2})]
    parts[-1].material = "steel"
    return Pack([front, back, pile], parts, (CW / 1000, bd + CARD_T, CH / 1000), 0.18)


def screw_blister() -> Product:
    p = screw_pack()
    return Product(slug="screw_blister", name="木ねじ 3.8×32mm 約60本入", shape_class="assembly",
                   category="household", dims=Dimensions(p.size[2], p.size[0], depth=p.size[1]), mass_kg=p.mass,
                   material="steel",
                   description="形は一般的な台紙とブリスターに入った木ねじ（3.8 × 32 mm・約 60 本、台紙 80 × 140 mm）で、"
                               "寸法・質量は代表値。ねじはブリスターの中の板に描いた絵で表す。吊り下げ穴は印刷で表す。",
                   tags=["木ねじ", "ねじ", "ビス", "金物", "DIY", "ブリスター", "ホームセンター", "wood screws",
                         "screws", "hardware", "blister pack"],
                   photos=[], colors=Colors(label_base=WHITE), images=p.images, parts=p.parts)


# ---------------------------------------------------------------- claw hammer


def claw_hammer() -> Product:
    """A claw hammer lying on its side (handle along X), with a paper price tag on the handle."""
    grip, handle = "#E8701A", "#2A2C30"
    t = Canvas(50, 70, 10, WHITE, 9341)
    t.gradient(0, 0, 50, 70, "#FFFFFF", "#ECEDEE")
    t.rect(0, 0, 50, 14, fill=HC_ORANGE)
    t.text(25, 7, "げんのう", 6.5, WHITE, 900)
    t.text(25, 22, "先割れ  450g", 5.0, INK, 800)
    t.text(25, 31, "全長 約 320mm", 3.6, INK, 600)
    t.barcode(7, 40, 36, 22)
    t.rect(0, 67, 50, 70, fill=HC_ORANGE)
    tag = _face(t.array(), "paper", 9341, 0.5)
    parts = [_box("Handle", (0.250, 0.026, 0.022), (0.0, 0, 0.016), handle, "metal"),
             _box("Grip", (0.120, 0.032, 0.028), (-0.110, 0, 0.016), grip, "matte"),
             _box("Head", (0.030, 0.070, 0.030), (0.135, -0.012, 0.016), STEEL, "metal"),
             Part("Face", "cylinder", [0.030, 0.030, 0.022], [0.135, -0.058, 0.016], [90.0, 0, 0], color=CHROME,
                  finish="metal"),
             Part("Claw", "box", [0.026, 0.045, 0.012], [0.135, 0.042, 0.012], [-12.0, 0, 0], color=STEEL,
                  finish="metal"),
             _box("Tag", (0.050, 0.070, 0.0006), (0.020, 0, 0.0273), WHITE, "matte", {"top": 0}, collision=False)]
    for p in parts:
        p.material = {"Grip": "rubber", "Tag": "paper", "Handle": "steel"}.get(p.name, "steel")
    return Product(slug="claw_hammer", name="先割れげんのう 450g", shape_class="assembly", category="household",
                   dims=Dimensions(0.031, 0.32, depth=0.134), mass_kg=0.62, material="steel",
                   description="形は一般的な先割れのげんのう（くぎ抜き付きのハンマー、全長約 320 mm・頭の長さ約 130 mm、"
                               "頭の質量 450 g）を横に寝かせた向きで、寸法・質量は代表値。柄に紙の値札。",
                   tags=["ハンマー", "げんのう", "金づち", "くぎ抜き", "工具", "ハンドツール", "ホームセンター",
                         "claw hammer", "hammer", "hand tool"],
                   photos=[], colors=Colors(label_base=STEEL), images=[tag], parts=parts)


# ---------------------------------------------------------------- cordless drill (boxed)


def _drill(c: Canvas, x: float, y: float, s: float):
    """A generic pistol-grip drill drawn in profile (no brand), top-left at (x, y), size s [mm]."""
    body, dark = "#E8701A", "#2A2C30"
    c.rect(x + 0.30 * s, y + 0.10 * s, x + 0.95 * s, y + 0.38 * s, fill=body, radius=0.08 * s)  # motor housing
    c.rect(x + 0.08 * s, y + 0.18 * s, x + 0.32 * s, y + 0.30 * s, fill=dark, radius=0.03 * s)  # chuck
    c.rect(x - 0.12 * s, y + 0.22 * s, x + 0.10 * s, y + 0.26 * s, fill="#B8BDC3")  # bit
    c.polygon([(x + 0.55 * s, y + 0.36 * s), (x + 0.82 * s, y + 0.36 * s), (x + 0.78 * s, y + 0.86 * s),
               (x + 0.55 * s, y + 0.86 * s)], fill=dark)  # grip
    c.rect(x + 0.42 * s, y + 0.84 * s, x + 0.92 * s, y + 1.0 * s, fill=body, radius=0.04 * s)  # battery
    c.rect(x + 0.50 * s, y + 0.42 * s, x + 0.56 * s, y + 0.54 * s, fill="#B8BDC3")  # trigger
    c.rect(x + 0.62 * s, y + 0.16 * s, x + 0.88 * s, y + 0.22 * s, fill=dark)


def power_drill_box() -> Product:
    W, H, D = 300.0, 250.0, 90.0
    navy, orange = HC_NAVY, HC_ORANGE

    def base(w, h, seed):
        c = Canvas(w, h, 4, WHITE, seed)
        c.gradient(0, 0, w, h, "#FFFFFF", "#E9ECF0")
        c.rect(0, 0, w, h * 0.10, fill=navy)
        c.rect(0, h * 0.94, w, h, fill=orange)
        return c

    fr = base(W, H, 9351)
    fr.text(18, 13, "10.8V 充電式", 9, WHITE, 900, anchor="lm")
    fr.text(W - 14, 13, "DIY", 9, orange, 900, anchor="rm")
    _drill(fr, 30, 62, 118)  # the drill stays left of x = 140 so the text never overlaps it
    fr.text(222, 60, "ドライバー", 20, navy, 900, max_w=W - 162)
    fr.text(222, 84, "ドリル", 20, navy, 900)
    fr.rect(152, 104, W - 12, 128, fill=orange, radius=6)
    fr.text(152 + (W - 164) / 2, 116, "バッテリー・充電器付き", 9.6, WHITE, 900, max_w=W - 176)
    fr.paragraph(156, 138, W - 12, "・締付けトルク 15段階\n・LEDライト付き\n・ビット 2 本付属", 8.2, INK, 700)
    fr.text(W - 16, H * 0.97, NOTICE, 4.2, WHITE, 500, anchor="rm")
    bk = base(W, H, 9352)
    bk.text(W / 2, 13, "CORDLESS DRIVER DRILL 10.8V", 8, WHITE, 800, spacing=0.6)
    y = bk.table(16, 34, W / 2 + 20, "仕様", [("電圧", "10.8V"), ("回転数", "0〜1,300 min⁻¹"),
                                            ("最大トルク", "24N·m"), ("質量", "約 1.0kg（電池含む）"),
                                            ("充電時間", "約 60分"), ("付属品", "電池・充電器・ビット")], 6.6)
    bk.paragraph(16, y + 6, W / 2 + 20, "回転中のビットに触れないでください。ご使用前に取扱説明書をお読みください。",
                 5.6, INK, 400)
    bk.barcode(W / 2 + 40, H * 0.62, 100, 60)
    sides = []
    for seed in (9353, 9354):
        sd = base(D, H, seed)
        _drill(sd, 14, 60, 60)
        sd.text(D / 2, 150, "10.8V", 12, navy, 900)
        sd.text(D / 2, 170, "ドライバードリル", 7, navy, 800, max_w=D - 8)
        sides.append(sd)
    tp, bt = base(W, D, 9355), base(W, D, 9356)
    tp.text(W / 2, D / 2 + 2, "充電式ドライバードリル 10.8V", 10, navy, 900)
    bt.text(W / 2, D / 2, "この面を下に", 8, INK, 700)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", 9357, 0.5)
    return Product(slug="power_drill_box", name="充電式ドライバードリル 10.8V（箱）", shape_class="box",
                   category="household", dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=1.8,
                   material="cardboard",
                   description="形は一般的な家庭用の充電式ドライバードリル（10.8 V）の化粧箱（300 × 90 × 250 mm）で、"
                               "寸法・質量は代表値。箱の絵は架空の機種。",
                   tags=["電動ドリル", "ドライバードリル", "充電式", "電動工具", "箱", "ホームセンター",
                         "cordless drill", "power drill", "power tool box"],
                   photos=[], colors=Colors(label_base=WHITE), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- duct tape


def _roll(d_mm: float, core_mm: float, hole_mm: float, tape: str, seed: int) -> np.ndarray:
    """The end face of a roll of tape: wound layers, a cardboard core and the hole (drawn, not cut)."""
    c = Canvas(d_mm, d_mm, 8, tape, seed)
    r = d_mm / 2
    c.gradient(0, 0, d_mm, d_mm, mix(tape, WHITE, 0.15), mix(tape, "#000000", 0.15))
    for k, rr in enumerate(np.linspace(r * 0.98, core_mm / 2, 14)):
        c.ellipse(r - rr, r - rr, r + rr, r + rr, outline=mix(tape, "#000000", 0.12 + 0.05 * (k % 2)), width=0.3)
    cr, hr = core_mm / 2, hole_mm / 2
    c.ellipse(r - cr, r - cr, r + cr, r + cr, fill="#B98D5C")
    c.ellipse(r - hr, r - hr, r + hr, r + hr, fill="#1A1A1A")
    c.ellipse(r - hr * 0.8, r - hr * 0.8, r + hr * 0.8, r + hr * 0.8, fill="#262626")
    return finish(c.array(), "film", seed, 0.4)


def duct_tape() -> Product:
    silver = "#A9AEB3"
    end = _roll(100, 80, 76, silver, 9361)
    parts = [Part("Roll", "cylinder", [0.100, 0.100, 0.048], [0, 0, 0.024], color=silver, finish="plastic",
                  faces={"top": 0, "bottom": 0}, material="fabric")]
    return Product(slug="duct_tape", name="布粘着テープ シルバー 48mm×25m", shape_class="assembly",
                   category="household", dims=Dimensions(0.048, 0.10, depth=0.10), mass_kg=0.30, material="fabric",
                   description="形は一般的な布の粘着テープ（ダクトテープ、幅 48 mm・長さ 25 m、外径約 100 mm・紙管の内径 76 mm）"
                               "で、寸法・質量は代表値。紙管の穴は端面に描いた絵で表す（当たり判定は円柱）。",
                   tags=["ダクトテープ", "布テープ", "ガムテープ", "粘着テープ", "梱包", "DIY", "ホームセンター",
                         "duct tape", "cloth tape", "tape roll"],
                   photos=[], colors=Colors(label_base=silver), images=[end], parts=parts)


# ---------------------------------------------------------------- cable ties


def cable_ties_bag() -> Product:
    W, H, D = 90.0, 240.0, 12.0
    black = "#202226"

    def bag(w, h, seed):
        c = Canvas(w, h, 6, FILM, seed)
        c.gradient(0, 0, w, h, "#F7F9FA", "#E3E8EB")
        return c

    def ties(c: Canvas, x0, y0, x1, y1):
        x = x0 + 1
        while x < x1 - 1:
            c.line([(x, y0), (x + c.rng.uniform(-1.5, 1.5), y1)], c.rng.choice(["#F4F4F0", "#E9E9E3", "#DCDCD5"]), 1.6)
            c.rect(x - 1.3, y1 - 6, x + 1.3, y1, fill="#E1E1DA")  # the lock head
            x += c.rng.uniform(1.6, 2.4)

    fr = bag(W, H, 9371)
    ties(fr, 6, 66, W - 6, H - 8)
    fr.rect(0, 0, W, 60, fill=black)
    _hang_hole(fr, W / 2, 6, "#55585E")
    fr.text(W / 2, 26, "結束バンド", 10, WHITE, 900)
    fr.text(W / 2, 40, "200mm × 4.8mm  100本入", 5.0, "#F9B000", 800, max_w=W - 8)
    fr.text(W / 2, 52, "ナイロン66  白", 4.4, WHITE, 700)
    fr.rect(0, H - 4, W, H, fill="#C9CBCE")
    bk = bag(W, H, 9372)
    ties(bk, 6, 140, W - 6, H - 8)
    bk.rect(0, 0, W, 132, fill=WHITE)
    bk.rect(0, 0, W, 16, fill=black)
    _hang_hole(bk, W / 2, 6, "#55585E")
    y = bk.table(6, 22, W - 6, "", [("長さ", "200mm"), ("幅", "4.8mm"), ("結束径", "最大 50mm"), ("入数", "100本")], 4.0)
    bk.paragraph(6, y + 2, W - 6, "屋外では耐候性のものをお使いください。\n" + NOTICE, 3.4, INK, 400)
    bk.barcode(14, 100, 46, 26)
    bk.rect(0, H - 4, W, H, fill="#C9CBCE")
    sides = []
    for seed in (9373, 9374):
        sd = bag(D, H, seed)
        sd.rect(0, 0, D, 60, fill=black)
        sd.rect(0, H - 4, D, H, fill="#C9CBCE")
        sides.append(sd)
    tp, bt = bag(W, D, 9375), bag(W, D, 9376)
    seal_crimp(tp, 0, 0, W, D, "#3A3D42", 1.2, vertical=True)
    tp.rect(W / 2 - 9, 2, W / 2 + 9, D - 2, fill="#55585E", radius=2)
    seal_crimp(bt, 0, 0, W, D, "#C9CBCE", 1.2, vertical=True)
    imgs = _faces((fr, bk, *sides, tp, bt), "film", 9377, 0.5)
    return Product(slug="cable_ties_bag", name="結束バンド 200mm 100本入", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.12, material="plastic",
                   description="形は一般的な袋入りの結束バンド（ナイロン、長さ 200 mm・100 本、袋 90 × 240 mm・厚さ 12 mm）"
                               "を箱で近似したもので、寸法・質量は代表値。吊り下げ穴は印刷で表す。",
                   tags=["結束バンド", "ケーブルタイ", "インシュロック", "配線", "DIY", "ホームセンター",
                         "cable ties", "zip ties", "cable tie bag"],
                   photos=[], colors=Colors(label_base=black), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- paint can


def paint_can() -> Product:
    form = forms.tin(0.110, 0.099, lid_h=0.008)
    teal, cream = "#1E7F86", "#F6F1E7"
    c = label_canvas(form, cream, seed=9381)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#FBF8F1", "#E8E1D2")
    c.rect(0, 0, W, H * 0.16, fill=teal)
    c.rect(0, H * 0.86, W, H, fill=teal)
    fx = 0.75 * W
    c.rect(fx - 42, H * 0.22, fx + 42, H * 0.52, fill=teal, radius=4)  # colour swatch
    c.text(fx, H * 0.30, "水性", 9, WHITE, 900)
    c.text(fx, H * 0.43, "多用途ペイント", 7.5, WHITE, 900)
    c.text(fx, H * 0.62, "ターコイズ  0.7L", 6.6, INK, 900)
    c.text(fx, H * 0.75, "木部・鉄部・コンクリート", 4.6, INK, 700, max_w=90)
    c.text(fx, H * 0.08, "WATER-BASED PAINT", 3.6, WHITE, 800, spacing=0.4)
    bx = 0.25 * W
    c.paragraph(bx - 40, H * 0.20, bx + 40, "塗り面積：約 3.5〜4.5㎡（2回塗り）\n乾燥時間：約 1時間（夏期）\n"
                "うすめ液：水\n" + NOTICE, 3.0, INK, 400)
    c.barcode(bx - 18, H * 0.58, 36, 20)
    label = finish(c.array(), "metal", 9381, 0.4)
    t = top_canvas(form, "#C9CDD1", seed=9382)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#D4D7DB", "#A9AEB3")
    for rr in (0.46, 0.40, 0.30):
        t.ellipse(d / 2 - d * rr, d / 2 - d * rr, d / 2 + d * rr, d / 2 + d * rr, outline="#8A9096", width=0.6)
    t.ellipse(d * 0.42, d * 0.06, d * 0.58, d * 0.14, fill=teal)  # a drip of the colour on the rim
    top = finish(t.array(), "metal", 9382, 0.4)
    return Product(slug="paint_can", name="水性多用途ペイント 0.7L ターコイズ", category="household", mass_kg=0.98,
                   material="steel", capacity_ml=700.0,
                   description="形は一般的な丸缶の水性塗料（0.7 L、高さ 110 mm・径 99 mm）で、寸法・質量は代表値。"
                               "持ち手（つる）は省略。",
                   tags=["ペンキ", "塗料", "水性塗料", "ペイント", "缶", "DIY", "ホームセンター", "paint can",
                         "paint", "water-based paint"],
                   photos=[], colors=Colors(cap="#C9CDD1", label_base=cream), **revolve(form, label=label, top=top))


# ---------------------------------------------------------------- paint brush


def paint_brush() -> Product:
    """A flat paint brush lying flat (handle along X), its bristles in a cardboard sleeve."""
    s = Canvas(60, 56, 10, "#F2E8D6", 9391)
    s.gradient(0, 0, 60, 56, "#F7EFDF", "#E2D4B9")
    s.rect(0, 0, 60, 12, fill=HC_ORANGE)
    s.text(30, 6, "刷毛", 7, WHITE, 900)
    s.text(30, 22, "水性・油性用", 5.2, INK, 900)
    s.text(30, 32, "50mm", 8, HC_NAVY, 900)
    s.barcode(12, 38, 36, 14)
    sleeve = _face(s.array(), "paper", 9391, 0.5)
    wood = "#C8955A"
    parts = [_box("Handle", (0.120, 0.024, 0.012), (-0.060, 0, 0.007), wood, "matte"),
             _box("Ferrule", (0.028, 0.052, 0.013), (0.014, 0, 0.0075), CHROME, "metal"),
             _box("Sleeve", (0.062, 0.056, 0.014), (0.059, 0, 0.0075), "#F2E8D6", "matte", {"top": 0})]
    parts[0].material, parts[1].material, parts[2].material = "wood", "steel", "paper"
    return Product(slug="paint_brush", name="刷毛 50mm 水性・油性用", shape_class="assembly", category="household",
                   dims=Dimensions(0.014, 0.21, depth=0.056), mass_kg=0.05, material="wood",
                   description="形は一般的な平刷毛（毛の幅 50 mm・全長約 210 mm、毛先に紙のさや）を寝かせた向きで、"
                               "寸法・質量は代表値。",
                   tags=["刷毛", "はけ", "ペイントブラシ", "塗装", "DIY", "ホームセンター", "paint brush", "brush"],
                   photos=[], colors=Colors(label_base=wood), images=[sleeve], parts=parts)


PRODUCTS = {f.__name__: f for f in (claw_hammer, screwdriver_blister, pliers_blister, tape_measure_blister,
                                    power_drill_box, screw_blister, duct_tape, cable_ties_bag, paint_can,
                                    paint_brush)}
