"""架空の製品のデザイン: 教室・オフィス・住宅の壁掛けの黒板・ホワイトボードと、床に敷くラグ。

store_env.py と同じく、実在のメーカー名・品番は使わず、形と寸法は同じ種類の製品の一般的な値にする。
カテゴリは environment。どれも動かない物（static）。

- 黒板・ホワイトボード: 背面（y = 0）を壁に付け、正面（-Y）が室内側。原点は下端。下に粉受け・マーカー受けのトレイ。
  cafe.py のメニューボード（木の枠の看板）とは別の、教室・会議室の大きな板。
- ラグ: 厚さ 10 mm の板。上面に毛並み・柄の絵柄を貼る。原点は底面の中心。正面は -Y（長辺が X）。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions
from .base import Product
from .paint import Canvas, mix
from .store_env import ALU, ENV, _img, _p

WHITE = "#FFFFFF"
GREEN = "#2F4A3A"  # 黒板の地（濃い緑）
BOARD_WHITE = "#F2F3F3"  # ホワイトボードの地
F = 0.030  # 枠の見付け
FD = 0.025  # 枠の見込み（壁からの厚さ）
TRAY_D = 0.075  # トレイの出（壁から）
RUG_T = 0.010  # ラグの厚さ


# ---------------------------------------------------------------- 黒板・ホワイトボード


def _chalk_surface(w_mm: float, h_mm: float, seed: int):
    """黒板の地: 濃い緑に、消し跡の白いむらと粉の筋。"""
    c = Canvas(w_mm, h_mm, None, GREEN, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(GREEN, WHITE, 0.04), mix(GREEN, "#000000", 0.10))
    for _ in range(int(w_mm * h_mm / 60000)):  # 黒板消しで拭いた跡（ごく薄い横の筋）
        x, y = c.rng.uniform(0, w_mm), c.rng.uniform(0, h_mm)
        r = c.rng.uniform(150, 450)
        c.line([(x - r, y), (x + r, y + c.rng.uniform(-20, 20))], mix(GREEN, WHITE, c.rng.uniform(0.006, 0.016)),
               c.rng.uniform(30, 70))
    for _ in range(int(w_mm / 60)):  # 粉受けの上に落ちた粉
        x = c.rng.uniform(0, w_mm)
        c.line([(x, h_mm - c.rng.uniform(5, 40)), (x + c.rng.uniform(-20, 20), h_mm)], mix(GREEN, WHITE, 0.25), 1.2)
    return _img(c, "paper", seed, 0.35)


def _white_surface(w_mm: float, h_mm: float, seed: int):
    """ホワイトボードの地: 白に、消し残りのごく薄い灰色のむら。"""
    c = Canvas(w_mm, h_mm, None, BOARD_WHITE, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(BOARD_WHITE, WHITE, 0.4), mix(BOARD_WHITE, "#C9CDD0", 0.25))
    for _ in range(int(w_mm * h_mm / 120000)):
        x, y = c.rng.uniform(0, w_mm), c.rng.uniform(0, h_mm)
        r = c.rng.uniform(60, 200)
        c.line([(x - r, y), (x + r, y + c.rng.uniform(-15, 15))], mix(BOARD_WHITE, "#AEB4BA", c.rng.uniform(0.03, 0.07)),
               c.rng.uniform(20, 50))
    return _img(c, "film", seed, 0.2)


def _board(slug: str, name: str, W: float, H: float, *, chalk: bool, mass: float, tags: list[str],
           description: str, seed: int) -> Product:
    """壁掛けの板（アルミの枠・トレイ）。背面（y = 0）が壁、正面（-Y）が室内側、原点は下端。"""
    surf = _chalk_surface(W * 1000 - 2 * F * 1000, H * 1000 - 2 * F * 1000, seed) if chalk else \
        _white_surface(W * 1000 - 2 * F * 1000, H * 1000 - 2 * F * 1000, seed)
    color, fin = (GREEN, "matte") if chalk else (BOARD_WHITE, "glossy")
    yb = -FD / 2
    parts = [
        _p("Backer", "box", (W - 2 * F, 0.012, H - 2 * F), (0, -0.006, H / 2), "#8A8E92", "matte", material="steel",
           bevel=0),
        _p("Board", "box", (W - 2 * F, 0.006, H - 2 * F), (0, -0.012 - 0.003, H / 2), color, fin,
           faces={"front": 0}, material="steel", bevel=0),
        _p("FrameT", "box", (W, FD, F), (0, yb, H - F / 2), ALU, "metal", material="aluminum", bevel=0.003),
        _p("FrameB", "box", (W, FD, F), (0, yb, F / 2), ALU, "metal", material="aluminum", bevel=0.003),
        _p("FrameL", "box", (F, FD, H - 2 * F), (-W / 2 + F / 2, yb, H / 2), ALU, "metal", material="aluminum",
           bevel=0.003),
        _p("FrameR", "box", (F, FD, H - 2 * F), (W / 2 - F / 2, yb, H / 2), ALU, "metal", material="aluminum",
           bevel=0.003),
        # 粉受け・マーカー受け（下枠の前に出る浅い樋）
        _p("TrayBottom", "box", (W - 0.06, TRAY_D - FD, 0.006), (0, -FD - (TRAY_D - FD) / 2, F * 0.4), ALU, "metal",
           material="aluminum", bevel=0.001),
        _p("TrayLip", "box", (W - 0.06, 0.006, 0.022), (0, -TRAY_D + 0.003, F * 0.4 + 0.011), ALU, "metal",
           material="aluminum", bevel=0.001),
    ]
    tray_z = F * 0.4 + 0.003
    if chalk:  # チョーク 3 本と黒板消し
        for k, (x, col) in enumerate(((-0.50, "#F4F1E8"), (-0.44, "#F4F1E8"), (-0.38, "#F2C94C"))):
            parts.append(_p(f"Chalk{k}", "cylinder", (0.011, 0.011, 0.07), (x * W / 1.8, -0.050, tray_z + 0.0055),
                            col, "matte", rot=(0, 90, 0), collision=False, material="stone", segments=10))
        parts += [_p("EraserBody", "box", (0.12, 0.040, 0.022), (0.30 * W / 1.8, -0.047, tray_z + 0.023), "#3B3F6B",
                     "matte", collision=False, material="plastic", bevel=0.004),
                  _p("EraserPad", "box", (0.12, 0.040, 0.012), (0.30 * W / 1.8, -0.047, tray_z + 0.006), "#E6E2D6",
                     "matte", collision=False, material="fabric", bevel=0.003)]
    else:  # マーカー 3 本とイレーザー
        for k, cap in enumerate(("#1E1E1E", "#C0392B", "#1F5FBF")):  # 0.18 m おき（キャップまで 0.155 m）
            x = -W / 2 + 0.15 + 0.18 * k
            parts += [_p(f"Marker{k}", "cylinder", (0.018, 0.018, 0.12), (x, -0.045, tray_z + 0.009),
                         "#F0F0F0", "plastic", rot=(0, 90, 0), collision=False, segments=12),
                      _p(f"MarkerCap{k}", "cylinder", (0.019, 0.019, 0.035), (x + 0.06, -0.045, tray_z + 0.009),
                         cap, "plastic", rot=(0, 90, 0), collision=False, segments=12)]
        parts.append(_p("Eraser", "box", (0.14, 0.040, 0.030), (W / 2 - 0.25, -0.047, tray_z + 0.015), "#2B2D30",
                        "matte", collision=False, material="plastic", bevel=0.005))
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=TRAY_D), mass_kg=mass, static=True, material="steel",
                   description=description + "背面を壁に付け、正面（-Y）が室内側。トレイの小物には当たり判定が無い。",
                   tags=[*tags, "壁掛け", "内装", "wall mounted", "wall-mounted board"],
                   colors=Colors(label_base=color), images=[surf], parts=parts)


def wall_chalkboard() -> Product:
    """教室の壁掛けの黒板（3600 × 1200 mm、緑）。"""
    return _board("wall_chalkboard", "壁掛けの黒板 3600×1200（緑・粉受け付き）", 3.60, 1.20, chalk=True, mass=45.0,
                  seed=7901,
                  tags=["黒板", "緑の黒板", "教室", "学校", "塾", "chalkboard", "blackboard", "green board",
                        "greenboard", "classroom board", "school"],
                  description="形は学校の教室・塾の前の壁に付ける一般的な黒板（外寸 3600 × 1200 mm、スチールのつや消しの"
                              "緑の板、アルミの枠、下に粉受け、チョーク 3 本と黒板消し）で、寸法・質量は代表値。")


def wall_whiteboard() -> Product:
    """会議室・オフィスの壁掛けのホワイトボード（1800 × 900 mm）。"""
    return _board("wall_whiteboard", "壁掛けのホワイトボード 1800×900（マーカー受け付き）", 1.80, 0.90, chalk=False,
                  mass=14.0, seed=7911,
                  tags=["ホワイトボード", "会議室", "オフィス", "教室", "whiteboard", "white board", "marker board",
                        "dry erase board", "magnetic board", "office", "meeting room"],
                  description="形は会議室・オフィス・教室の壁に付ける一般的なホワイトボード（外寸 1800 × 900 mm、"
                              "つやのある白いスチールの板、アルミの枠、下にマーカー受け、マーカー 3 本とイレーザー）で、"
                              "寸法・質量は代表値。")


def wall_whiteboard_small() -> Product:
    """小さな壁掛けのホワイトボード（1200 × 900 mm）。"""
    return _board("wall_whiteboard_small", "壁掛けのホワイトボード 1200×900（マーカー受け付き）", 1.20, 0.90, chalk=False,
                  mass=9.5, seed=7912,
                  tags=["ホワイトボード", "小さなホワイトボード", "会議室", "オフィス", "whiteboard", "white board",
                        "marker board", "dry erase board", "small whiteboard", "office"],
                  description="形は小さな会議室・事務所・店のバックヤードの壁に付ける一般的なホワイトボード"
                              "（外寸 1200 × 900 mm、つやのある白いスチールの板、アルミの枠、下にマーカー受け、"
                              "マーカー 3 本とイレーザー）で、寸法・質量は代表値。")


# ---------------------------------------------------------------- ラグ


def _pile(c: Canvas, x0: float, y0: float, x1: float, y1: float, color: str, step: float = 3.0) -> None:
    """毛並み（ランダムな明暗の細い横筋と粒）で矩形を塗る。"""
    c.rect(x0, y0, x1, y1, fill=color)
    y = y0
    while y < y1:
        tone = mix(color, c.rng.choice(["#000000", WHITE]), c.rng.uniform(0.02, 0.09))
        c.line([(x0, y), (x1, y)], tone, step * 0.6)
        y += step
    n = int((x1 - x0) * (y1 - y0) / 400)
    for _ in range(n):
        x, yy = c.rng.uniform(x0, x1), c.rng.uniform(y0, y1)
        c.ellipse(x - 1.2, yy - 1.2, x + 1.2, yy + 1.2, fill=mix(color, c.rng.choice(["#000000", WHITE]), 0.12))


def _rug_bordered(w_mm: float, d_mm: float, base: str, border: str, seed: int):
    """無地の毛足に、内側の細い縁取り 2 本。"""
    c = Canvas(w_mm, d_mm, None, base, seed)
    _pile(c, 0, 0, w_mm, d_mm, base)
    for inset, wd in ((90, 30), (150, 10)):
        c.rect(inset, inset, w_mm - inset, d_mm - inset, outline=border, width=wd)
    return _img(c, "paper", seed, 0.35)


def _rug_geometric(w_mm: float, d_mm: float, base: str, ink: str, seed: int):
    """グレーの地に、ひし形の格子の柄と太い縁。"""
    c = Canvas(w_mm, d_mm, None, base, seed)
    _pile(c, 0, 0, w_mm, d_mm, base)
    step = 240.0
    m = 160.0
    for i in range(int((w_mm - 2 * m) / step) + 1):
        for j in range(int((d_mm - 2 * m) / step) + 1):
            cx, cy = m + step * (i + 0.5), m + step * (j + 0.5)
            if cx > w_mm - m or cy > d_mm - m:
                continue
            r = step * 0.42
            c.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=ink)
            c.polygon([(cx, cy - r * 0.35), (cx + r * 0.35, cy), (cx, cy + r * 0.35), (cx - r * 0.35, cy)], fill=ink)
    c.rect(40, 40, w_mm - 40, d_mm - 40, outline=ink, width=60)
    return _img(c, "paper", seed, 0.35)


def _rug_round(d_mm: float, base: str, ring: str, seed: int):
    """丸いラグ（同心円の縞）。絵柄は外接する正方形に描き、円柱の上面に貼る。"""
    c = Canvas(d_mm, d_mm, None, base, seed)
    _pile(c, 0, 0, d_mm, d_mm, base)
    cx = cy = d_mm / 2
    for k, r in enumerate((0.46, 0.40, 0.25, 0.10)):
        rr = d_mm * r
        c.ellipse(cx - rr, cy - rr, cx + rr, cy + rr, outline=ring, width=22 if k % 2 == 0 else 10)
    return _img(c, "paper", seed, 0.35)


def _rug_kilim(w_mm: float, d_mm: float, seed: int):
    """細長いランナー（横縞と、ジグザグの帯）。"""
    cols = ["#9C3D2E", "#D9B98A", "#2F4B5E", "#E9E1CF", "#B5652F"]
    c = Canvas(w_mm, d_mm, None, cols[3], seed)
    band = d_mm / 9
    for k in range(9):
        col = cols[k % len(cols)] if k % 2 else cols[3]
        _pile(c, 0, k * band, w_mm, (k + 1) * band, col, step=2.5)
    zig = 60.0
    for row in (band * 4, band * 4.5):
        pts = [(x * zig, row + (band * 0.35 if x % 2 else -band * 0.35)) for x in range(int(w_mm / zig) + 2)]
        c.line(pts, cols[0], 8)
    return _img(c, "paper", seed, 0.35)


def _rug(slug: str, name: str, W: float, D: float, img, color: str, *, round_: bool = False, mass: float,
         tags: list[str], description: str) -> Product:
    """厚さ 10 mm の板（丸なら円柱）の上面に柄を貼ったラグ。原点は底面の中心。"""
    shape = "cylinder" if round_ else "box"
    parts = [_p("Rug", shape, (W, D, RUG_T), (0, 0, RUG_T / 2), color, "matte", faces={"top": 0}, material="fabric",
                bevel=0.003, **({"segments": 64} if round_ else {}))]
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(RUG_T, W, depth=D), mass_kg=mass, static=True, material="fabric",
                   description=description + "床に敷く物で動かない（static）。上に家具を置ける。",
                   tags=["ラグ", "カーペット", "敷物", "床", "内装", "rug", "area rug", "carpet", "floor rug", *tags],
                   colors=Colors(label_base=color), images=[img], parts=parts)


def rug_beige_200x140() -> Product:
    """ベージュの無地のラグ（2000 × 1400 mm）。リビングのローテーブルの下に。"""
    base = "#CDB99A"
    return _rug("rug_beige_200x140", "無地のラグ 2000×1400（ベージュ）", 2.0, 1.4,
                _rug_bordered(2000, 1400, base, mix(base, "#5A4632", 0.35), 7921), base, mass=5.6,
                tags=["リビング", "居間", "ウール", "living room rug", "wool rug", "beige rug"],
                description="形はリビングのソファの前・ローテーブルの下に敷く一般的な長方形のラグ（2000 × 1400 mm、"
                            "厚さ 10 mm、ベージュの毛足に細い縁取り）で、寸法・質量は代表値。")


def rug_gray_240x170() -> Product:
    """グレーの柄のラグ（2400 × 1700 mm）。ダイニング・広いリビングに。"""
    base = "#8D9196"
    return _rug("rug_gray_240x170", "柄のラグ 2400×1700（グレー・ひし形）", 2.4, 1.7,
                _rug_geometric(2400, 1700, base, mix(base, "#1E2226", 0.55), 7922), base, mass=8.2,
                tags=["ダイニング", "リビング", "柄", "dining rug", "patterned rug", "gray rug", "grey rug"],
                description="形はダイニングテーブルの下・広いリビングに敷く一般的な長方形のラグ（2400 × 1700 mm、"
                            "厚さ 10 mm、グレーの地に濃いグレーのひし形の柄と太い縁）で、寸法・質量は代表値。")


def rug_round_120() -> Product:
    """丸いラグ（直径 1200 mm）。寝室・子ども部屋・一人掛けの椅子の下に。"""
    base = "#B9C4B0"
    return _rug("rug_round_120", "丸いラグ 直径 1200（セージグリーン）", 1.2, 1.2,
                _rug_round(1200, base, mix(base, "#3C4A36", 0.45), 7923), base, round_=True, mass=2.3,
                tags=["丸いラグ", "円形", "寝室", "子ども部屋", "round rug", "circular rug", "bedroom rug"],
                description="形は寝室・子ども部屋・一人掛けの椅子の下に敷く一般的な丸いラグ（直径 1200 mm、厚さ 10 mm、"
                            "淡いセージグリーンの毛足に同心円の縞）で、寸法・質量は代表値。")


def rug_runner_70x200() -> Product:
    """廊下・キッチンの細長いラグ（ランナー、700 × 2000 mm）。"""
    return _rug("rug_runner_70x200", "細長いラグ（ランナー）700×2000（キリム風の縞）", 2.0, 0.7,
                _rug_kilim(2000, 700, 7924), "#D9B98A", mass=2.4,
                tags=["ランナー", "キッチンマット", "廊下", "キリム", "runner", "rug runner", "hallway runner",
                      "kitchen runner", "kilim"],
                description="形は廊下・キッチンのシンクの前に敷く一般的な細長いラグ（700 × 2000 mm、厚さ 10 mm、"
                            "赤・紺・生成りの横縞とジグザグの帯のキリム風の柄）で、寸法・質量は代表値。")


PRODUCTS = {f.__name__: f for f in (
    wall_chalkboard, wall_whiteboard, wall_whiteboard_small,
    rug_beige_200x140, rug_gray_240x170, rug_round_120, rug_runner_70x200,
)}
