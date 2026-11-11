"""Fictional product designs: home-center storage and daily goods (a storage case, a bucket, a broom, a
dustpan, an extension cord, an LED bulb) and long goods (2x4 lumber, a PVC pipe).

No real product names, brands or logos; shapes and sizes are typical values. Front is -Y. All are dynamic
rigid bodies. Long goods lie with their length along X.
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .conv_goods import BOX_FACES, _faces
from .paint import Canvas, finish, mix
from .products import INK, _face

WHITE = "#FFFFFF"
HC_ORANGE, HC_NAVY = "#E8701A", "#1F3A5F"


def _p(name, shape, size, center, color, finish_="plastic", rot=None, faces=None, collision=True, material=None,
       **kw) -> Part:
    return Part(name=name, shape=shape, size=list(size), center=list(center), rotation=list(rot or [0, 0, 0]),
                color=color, finish=finish_, faces=faces, collision=collision, material=material, **kw)


def _tag(w: float, h: float, seed: int, title: str, sub: str, price: str, accent: str) -> np.ndarray:
    c = Canvas(w, h, 10, WHITE, seed)
    c.gradient(0, 0, w, h, "#FFFFFF", "#ECEDEF")
    c.rect(0, 0, w, h * 0.28, fill=accent)
    c.text(w / 2, h * 0.14, title, h * 0.15, WHITE, 900, max_w=w - 4)
    c.text(w / 2, h * 0.45, sub, h * 0.11, INK, 800, max_w=w - 4)
    c.barcode(w * 0.12, h * 0.56, w * 0.5, h * 0.36)
    c.text(w * 0.82, h * 0.74, price, h * 0.13, "#C62828", 900, max_w=w * 0.32)
    return _face(c.array(), "paper", seed, 0.4, 4)


# ---------------------------------------------------------------- storage case


def storage_case() -> Product:
    """A stackable translucent storage case with a lid (about 45 L)."""
    W, D, H = 0.39, 0.53, 0.30
    body, lid = "#E9EDF0", "#F6F7F8"
    tag = _tag(90, 60, 9501, "収納ケース", "深型 45L  フタ付き", "1,280円", HC_NAVY)
    parts = [_p("Body", "box", (W - 0.02, D - 0.02, H - 0.025), (0, 0, (H - 0.025) / 2), body, "frosted",
                bevel=0.012, material="plastic"),
             _p("Lid", "box", (W, D, 0.025), (0, 0, H - 0.0125), lid, "plastic", bevel=0.008, material="plastic"),
             _p("Grip", "box", (0.12, 0.012, 0.025), (0, -D / 2 + 0.004, H - 0.04), lid, "plastic",
                collision=False, material="plastic"),
             _p("Tag", "box", (0.09, 0.0005, 0.06), (0, -(D - 0.02) / 2 - 0.0003, 0.14), WHITE, "matte",
                faces={"front": 0}, collision=False, material="paper")]
    return Product(slug="storage_case", name="収納ケース 深型 45L フタ付き", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D), mass_kg=1.9, material="plastic",
                   description="形は一般的な半透明の衣装・収納ケース（幅 390 × 奥行き 530 × 高さ 300 mm、約 45 L、"
                               "フタ付きで積み重ね可）で、寸法・質量は代表値。中は空（当たり判定は箱）。",
                   tags=["収納ケース", "収納ボックス", "衣装ケース", "フタ付き", "収納", "日用品", "ホームセンター",
                         "storage case", "storage box", "plastic storage bin"],
                   photos=[], colors=Colors(label_base=body), images=[tag], parts=parts)


# ---------------------------------------------------------------- bucket


def bucket() -> Product:
    """A 10 L plastic bucket with a wire bail handle (folded down, so it does not collide)."""
    Dt, Db, H = 0.29, 0.22, 0.25
    blue = "#2E86C1"
    tag = _tag(70, 46, 9511, "バケツ", "10L  目盛り付き", "398円", blue)
    prof = [[0, 0], [Db / Dt, 0], [0.98, 0.94], [1.0, 0.95], [1.0, 1.0], [0.95, 1.0], [Db / Dt - 0.04, 0.03],
            [0, 0.03]]
    parts = [_p("Pail", "revolve", (Dt, Dt, H), (0, 0, H / 2), blue, "plastic", profile=prof, material="plastic"),
             _p("Tag", "box", (0.07, 0.0005, 0.046), (0, -(Db + Dt) / 4 - 0.006, H * 0.55), WHITE, "matte",
                (-7.0, 0, 0), faces={"front": 0}, collision=False, material="paper")]
    # the bail lies along the rim, drawn as short straight segments of a half circle (visual only)
    n, r, zb = 8, Dt / 2 - 0.004, H + 0.004
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        x0, y0, x1, y1 = r * math.cos(a0), -r * math.sin(a0), r * math.cos(a1), -r * math.sin(a1)
        L = math.hypot(x1 - x0, y1 - y0)
        parts.append(_p(f"Bail{k}", "cylinder", (0.004, 0.004, L), ((x0 + x1) / 2, (y0 + y1) / 2, zb), "#B0B4B8",
                        "metal", (0, 90, math.degrees(math.atan2(y1 - y0, x1 - x0))), collision=False,
                        material="steel"))
    for s in (-1, 1):
        parts.append(_p(f"Ear{s:+d}", "box", (0.012, 0.02, 0.03), (s * (Dt / 2 - 0.006), 0, H - 0.02), blue,
                        collision=False, material="plastic"))
    return Product(slug="bucket", name="バケツ 10L", shape_class="assembly", category="household",
                   dims=Dimensions(H + 0.008, Dt, depth=Dt), mass_kg=0.45, material="plastic",
                   description="形は一般的な樹脂のバケツ（容量 10 L、口径 290 mm・底径 220 mm・高さ 250 mm、針金の取っ手は"
                               "縁に倒した状態）で、寸法・質量は代表値。中は空（当たり判定は外形の凸包）。",
                   tags=["バケツ", "ポリバケツ", "掃除用品", "日用品", "ホームセンター", "bucket", "plastic bucket",
                         "pail"],
                   photos=[], colors=Colors(label_base=blue), images=[tag], parts=parts)


# ---------------------------------------------------------------- broom and dustpan


def _bristles(w_mm: float, h_mm: float, seed: int, color: str) -> np.ndarray:
    c = Canvas(w_mm, h_mm, 4, color, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(color, WHITE, 0.15), mix(color, "#000000", 0.15))
    rng = c.rng
    for _ in range(int(w_mm * 3)):
        x = rng.uniform(0, w_mm)
        c.line([(x, 0), (x + rng.uniform(-3, 3), h_mm)], mix(color, rng.choice(["#000000", WHITE]), 0.25), 0.4)
    return finish(c.array(), "matte", seed, 0.5)


def broom() -> Product:
    """An indoor broom lying on its side: a long handle along X and a fan of bristles."""
    L, hw, ht = 1.20, 0.26, 0.05
    red, handle = "#C0392B", "#D9D4C7"
    brist = _bristles(190, 260, 9521, "#7E2A22")
    tag = _tag(60, 40, 9522, "ほうき", "室内用  1.2m", "698円", red)
    hx = -L / 2 + 0.08  # the bristles' centre
    parts = [_p("Handle", "cylinder", (0.024, 0.024, 0.95), (L / 2 - 0.475, 0, ht / 2), handle, "plastic",
                (0, 90, 0), material="steel"),
             _p("Cap", "cylinder", (0.026, 0.026, 0.03), (L / 2 - 0.015, 0, ht / 2), red, "plastic", (0, 90, 0),
                material="plastic"),
             _p("Head", "box", (0.06, 0.18, 0.04), (-L / 2 + 0.22, 0, ht / 2), red, "plastic", bevel=0.01,
                material="plastic"),
             _p("Bristles", "box", (0.19, hw, ht), (hx, 0, ht / 2), "#7E2A22", "matte",
                faces={"top": 0, "bottom": 0}, bevel=0.015, material="nylon"),
             _p("Tag", "box", (0.06, 0.04, 0.0005), (0.05, 0, ht / 2 + 0.0123), WHITE, "matte", faces={"top": 1},
                collision=False, material="paper")]
    return Product(slug="broom", name="室内ほうき 1.2m", shape_class="assembly", category="household",
                   dims=Dimensions(ht, L, depth=hw), mass_kg=0.40, material="plastic",
                   description="形は一般的な室内用のほうき（全長約 1.2 m、穂の幅約 260 mm、柄はスチールに樹脂被覆）を横に寝かせた"
                               "もので、寸法・質量は代表値。穂は角の丸い板で表す。",
                   tags=["ほうき", "箒", "室内ほうき", "掃除用品", "日用品", "ホームセンター", "broom", "indoor broom"],
                   photos=[], colors=Colors(label_base=red), images=[brist, tag], parts=parts)


def dustpan() -> Product:
    """A dustpan with a short handle, lying flat (the lip toward -Y)."""
    W, D = 0.25, 0.30
    green = "#3E9B4F"
    tag = _tag(60, 40, 9531, "ちりとり", "フチゴム付き", "298円", green)
    parts = [_p("Pan", "box", (W, 0.20, 0.003), (0, -D / 2 + 0.10, 0.0015), green, "plastic", material="plastic"),
             _p("Lip", "box", (W, 0.02, 0.0015), (0, -D / 2 + 0.01, 0.0035), "#2A2C30", "matte", collision=False,
                material="rubber"),
             _p("Back", "box", (W, 0.012, 0.05), (0, -D / 2 + 0.206, 0.025), green, "plastic", material="plastic"),
             _p("SideL", "box", (0.006, 0.20, 0.03), (-W / 2 + 0.003, -D / 2 + 0.10, 0.015), green, "plastic",
                material="plastic"),
             _p("SideR", "box", (0.006, 0.20, 0.03), (W / 2 - 0.003, -D / 2 + 0.10, 0.015), green, "plastic",
                material="plastic"),
             _p("Grip", "box", (0.04, 0.088, 0.025), (0, D / 2 - 0.044, 0.0125), mix(green, "#000000", 0.2),
                "plastic", bevel=0.008, material="plastic"),
             _p("Tag", "box", (0.06, 0.04, 0.0005), (0, -0.04, 0.0033), WHITE, "matte", faces={"top": 0},
                collision=False, material="paper")]
    return Product(slug="dustpan", name="ちりとり フチゴム付き", shape_class="assembly", category="household",
                   dims=Dimensions(0.05, W, depth=D), mass_kg=0.18, material="plastic",
                   description="形は一般的な手持ちのちりとり（幅 250 mm・奥行き 300 mm、短い持ち手、先にゴムのフチ）を寝かせた"
                               "もので、寸法・質量は代表値。",
                   tags=["ちりとり", "塵取り", "掃除用品", "日用品", "ホームセンター", "dustpan"],
                   photos=[], colors=Colors(label_base=green), images=[tag], parts=parts)


# ---------------------------------------------------------------- boxed electric goods


def _boxed(slug: str, name: str, mm: tuple[float, float, float], seed: int, accent: str, title: str, sub: str,
           draw, specs: list[tuple[str, str]], mass: float, description: str, tags: list[str]) -> Product:
    """A printed carton (W, D, H in mm) with the item drawn on the front and the specs on the back."""
    W, D, H = mm

    def base(w, h, s):
        c = Canvas(w, h, 6, WHITE, s)
        c.gradient(0, 0, w, h, "#FFFFFF", "#E8ECEF")
        c.rect(0, 0, w, h * 0.12, fill=accent)
        c.rect(0, h * 0.95, w, h, fill=mix(accent, "#000000", 0.3))
        return c

    fr = base(W, H, seed)
    fr.text(W / 2, H * 0.06, title, H * 0.07, WHITE, 900, max_w=W - 6)
    draw(fr, W / 2, H * 0.48, min(W, H) * 0.34)
    fr.text(W / 2, H * 0.82, sub, H * 0.055, INK, 900, max_w=W - 6)
    fr.text(W / 2, H * 0.975, NOTICE, H * 0.022, WHITE, 500, max_w=W - 4)
    bk = base(W, H, seed + 1)
    bk.text(W / 2, H * 0.06, title, H * 0.06, WHITE, 900, max_w=W - 6)
    y = bk.table(W * 0.06, H * 0.16, W * 0.94, "仕様", specs, H * 0.035)
    bk.barcode(W * 0.2, max(y + 3, H * 0.66), W * 0.6, H * 0.2)
    sides = []
    for k in range(2):
        sd = base(D, H, seed + 2 + k)
        draw(sd, D / 2, H * 0.45, D * 0.3)
        sd.text(D / 2, H * 0.8, sub, H * 0.04, INK, 800, max_w=D - 4)
        sides.append(sd)
    tp, bt = base(W, D, seed + 4), base(W, D, seed + 5)
    tp.text(W / 2, D * 0.6, name, D * 0.16, INK, 900, max_w=W - 6)
    bt.text(W / 2, D * 0.6, "MADE IN —", D * 0.14, INK, 700)
    imgs = _faces((fr, bk, *sides, tp, bt), "paper", seed + 6, 0.5)
    return Product(slug=slug, name=name, shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=mass, material="cardboard",
                   description=description, tags=tags, photos=[], colors=Colors(label_base=WHITE), images=imgs,
                   faces=BOX_FACES)


def _draw_strip(c: Canvas, cx: float, cy: float, s: float):
    """A power strip with three outlets and a coiled cord."""
    c.rect(cx - s, cy - s * 0.28, cx + s, cy + s * 0.28, fill="#F4F4F2", outline="#9AA0A6", width=0.6, radius=s * 0.1)
    for k in range(3):
        x = cx - s * 0.6 + k * s * 0.6
        c.ellipse(x - s * 0.18, cy - s * 0.18, x + s * 0.18, cy + s * 0.18, fill="#E6E6E2", outline="#9AA0A6",
                  width=0.4)
        for dx in (-0.06, 0.06):
            c.rect(x + dx * s - s * 0.015, cy - s * 0.07, x + dx * s + s * 0.015, cy + s * 0.07, fill="#2A2C30")
    for k in range(4):
        r = s * (0.25 + 0.06 * k)
        c.ellipse(cx + s * 0.55 - r, cy + s * 0.75 - r * 0.5, cx + s * 0.55 + r, cy + s * 0.75 + r * 0.5,
                  outline="#D8D8D4", width=0.8)


def _draw_bulb(c: Canvas, cx: float, cy: float, s: float):
    """A pear-shaped LED bulb with an E26 screw base."""
    c.ellipse(cx - s * 0.55, cy - s * 0.95, cx + s * 0.55, cy + s * 0.25, fill="#FFF6D8", outline="#D8CFAE",
              width=0.6)
    c.polygon([(cx - s * 0.4, cy), (cx + s * 0.4, cy), (cx + s * 0.25, cy + s * 0.45), (cx - s * 0.25, cy + s * 0.45)],
              fill="#F4F4F2")
    for k in range(4):
        y = cy + s * (0.47 + k * 0.1)
        c.rect(cx - s * 0.22, y, cx + s * 0.22, y + s * 0.07, fill="#B8BCC0")
    c.ellipse(cx - s * 0.1, cy + s * 0.88, cx + s * 0.1, cy + s * 1.0, fill="#2A2C30")
    for a in range(8):  # glow rays
        t = a * math.pi / 4
        c.line([(cx + s * 0.7 * math.cos(t), cy - s * 0.35 + s * 0.7 * math.sin(t)),
                (cx + s * 0.9 * math.cos(t), cy - s * 0.35 + s * 0.9 * math.sin(t))], "#F2B705", 0.8)


def extension_cord_box() -> Product:
    return _boxed("extension_cord_box", "延長コード 3個口 2m（箱）", (70.0, 45.0, 160.0), 9541, HC_NAVY,
                  "延長コード", "3個口  2m  雷ガード付", _draw_strip,
                  [("定格", "15A 125V"), ("コード長", "2m"), ("口数", "3個口"), ("その他", "雷ガード・ほこり防止")],
                  0.25, "形は一般的な家庭用の延長コード（3 個口・2 m）の化粧箱（70 × 45 × 160 mm）で、寸法・質量は代表値。",
                  ["延長コード", "電源タップ", "テーブルタップ", "コンセント", "電材", "日用品", "ホームセンター",
                   "extension cord", "power strip", "electrical"])


def led_bulb_box() -> Product:
    return _boxed("led_bulb_box", "LED 電球 E26 60形 電球色（箱）", (65.0, 65.0, 125.0), 9551, "#F2B705",
                  "LED電球", "E26  60形相当  電球色", _draw_bulb,
                  [("口金", "E26"), ("明るさ", "810lm（60形相当）"), ("光色", "電球色 2700K"), ("消費電力", "7.0W"),
                   ("寿命", "約 40,000 時間")],
                  0.07, "形は一般的な LED 電球（E26 口金・60 形相当）の化粧箱（65 × 65 × 125 mm）で、寸法・質量は代表値。",
                  ["LED電球", "電球", "E26", "照明", "電材", "日用品", "ホームセンター", "LED bulb", "light bulb",
                   "bulb box"])


# ---------------------------------------------------------------- long goods


def _wood_face(w_mm: float, h_mm: float, seed: int, base: str = "#D9B98A", stamp: str | None = None) -> np.ndarray:
    """Planed softwood seen along the grain (streaks along the length = canvas x)."""
    c = Canvas(w_mm, h_mm, 2, base, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(base, WHITE, 0.1), mix(base, "#8A5A2B", 0.15))
    rng = c.rng
    for _ in range(int(h_mm * 1.2)):
        y = rng.uniform(0, h_mm)
        amp, ph = rng.uniform(0.2, 2.0), rng.uniform(0, 6.3)
        pts = [(x, y + amp * math.sin(x / rng.uniform(60, 200) + ph)) for x in np.linspace(0, w_mm, 40)]
        c.line(pts, mix(base, "#8A5A2B", rng.uniform(0.2, 0.5)), rng.uniform(0.2, 0.6))
    for _ in range(max(1, int(w_mm / 600))):  # knots
        x, y = rng.uniform(40, w_mm - 40), rng.uniform(h_mm * 0.2, h_mm * 0.8)
        r = rng.uniform(3, 7)
        c.ellipse(x - r * 1.6, y - r, x + r * 1.6, y + r, fill="#9B6A3A")
        c.ellipse(x - r * 0.7, y - r * 0.4, x + r * 0.7, y + r * 0.4, fill="#6B4423")
    if stamp:
        c.text(w_mm * 0.2, h_mm / 2, stamp, h_mm * 0.4, "#3A5F9A", 800)
    return finish(c.array(), "paper", seed, 0.6)


def _end_grain(w_mm: float, h_mm: float, seed: int) -> np.ndarray:
    c = Canvas(w_mm, h_mm, 8, "#D2AE7B", seed)
    c.gradient(0, 0, w_mm, h_mm, "#DDBC8A", "#C09868")
    cx, cy = w_mm * 0.3, h_mm * 1.6  # the pith lies outside the board
    for k in range(30):
        r = 6 + k * 4.5
        c.ellipse(cx - r, cy - r, cx + r, cy + r, outline="#A57A4A", width=0.4)
    return finish(c.array(), "paper", seed, 0.6)


def lumber_2x4() -> Product:
    """A 2x4 (SPF, 38 x 89 mm) six-foot stud lying flat, length along X."""
    L, W, T = 1.820, 0.089, 0.038
    face = _wood_face(1820, 89, 9561, stamp="SPF 2×4  6F  KD")
    edge = _wood_face(1820, 38, 9562)
    end = _end_grain(89, 38, 9563)
    imgs = [face, face, edge, edge, end, end]
    parts = [_p("Board", "box", (L, W, T), (0, 0, T / 2), "#D9B98A", "matte",
                faces={"top": 0, "bottom": 1, "front": 2, "back": 3, "right": 4, "left": 5}, material="wood")]
    # The canvas x of the top/bottom faces runs along X; the side faces run along X too; end faces are the YZ ends.
    return Product(slug="lumber_2x4", name="ツーバイ材 2×4 6フィート（1820mm）", shape_class="assembly",
                   category="household", dims=Dimensions(T, L, depth=W), mass_kg=2.6, material="wood",
                   description="形は一般的な SPF のツーバイフォー材（38 × 89 mm、長さ 1820 mm＝6 フィート、乾燥材）を"
                               "平らに寝かせたもので、寸法・質量は代表値。長さは X 方向。",
                   tags=["木材", "角材", "ツーバイ材", "2x4", "SPF", "長尺物", "DIY", "ホームセンター", "lumber",
                         "2x4 lumber", "wood stud", "timber"],
                   photos=[], colors=Colors(label_base="#D9B98A"), images=imgs, parts=parts)


def pvc_pipe() -> Product:
    """A 1 m length of grey PVC pipe (nominal 25, OD 32 mm) lying along X, with a printed line."""
    L, OD = 1.0, 0.032
    grey = "#9EA3A8"
    e = Canvas(32, 32, 16, grey, 9572)
    e.gradient(0, 0, 32, 32, mix(grey, WHITE, 0.2), mix(grey, "#000000", 0.2))
    e.ellipse(2.5, 2.5, 29.5, 29.5, fill="#1E2023")
    e.ellipse(4.5, 4.5, 27.5, 27.5, fill="#2E3034")
    end = finish(e.array(), "plastic", 9572, 0.3)
    parts = [_p("Pipe", "cylinder", (OD, OD, L), (0, 0, OD / 2), grey, "plastic", (0, 90, 0),
                faces={"top": 0, "bottom": 0}, material="pvc")]
    return Product(slug="pvc_pipe", name="塩ビ管 VP25 1m", shape_class="assembly", category="household",
                   dims=Dimensions(OD, L, depth=OD), mass_kg=0.36, material="pvc",
                   description="形は一般的な硬質塩化ビニル管（呼び径 25、外径 32 mm、長さ 1 m に切ったもの）を寝かせたもので、"
                               "寸法・質量は代表値。中空は端面の絵で表す（当たり判定は円柱）。長さは X 方向。",
                   tags=["塩ビ管", "塩ビパイプ", "VP管", "パイプ", "配管", "長尺物", "DIY", "ホームセンター", "PVC pipe",
                         "pipe", "plumbing"],
                   photos=[], colors=Colors(label_base=grey), images=[end], parts=parts)


PRODUCTS = {f.__name__: f for f in (storage_case, bucket, broom, dustpan, extension_cord_box, led_bulb_box,
                                    lumber_2x4, pvc_pipe)}
