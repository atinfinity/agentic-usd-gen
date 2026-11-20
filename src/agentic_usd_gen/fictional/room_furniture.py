"""架空の製品のデザイン: 住宅・オフィスの部屋の家具 13 点。

specialty_shops.py のナイトテーブル・ワードローブと同じく、実在のメーカー名・品番は使わず、形と寸法は同じ種類の製品の
一般的な値にする。正面は -Y、Z が上、原点は底面の中心（壁掛けのペーパータオルホルダーだけは背面 y = 0 が壁）。

- 丸・楕円のテーブル: 天板は円柱（楕円は直径 X と Y を変えた円柱）。脚は一本脚に十字か円盤のベース。天板の下に幕板を
  付けず、椅子の座面と膝が天板の下に入る。
- 椅子: 脚だけで座面を支え、テーブルの天板の下に座面ごと差し込める。6 脚積みは同じ椅子を少しずつ上・後ろにずらして重ねる。
- テレビスタンド: 65 型のテレビの画面は finish screen の部品（Screen バリアントで On・Off）。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Light, Part
from .backyard import _dims
from .base import Product
from .hc_garden import _p
from .paint import Canvas, finish, mix, trim_safe
from .specialty_shops import FURNITURE_TAGS, HOME_TAGS

WHITE = "#FFFFFF"
STEEL = "#2B2D31"  # 黒い焼付塗装のスチール
CHROME = "#C9CDD1"
OAK = "#C9A27A"
WALNUT = "#6B4A33"
ALU_LIGHT = "#C7CBCF"
OFFICE_TAGS = ["オフィス", "会議室", "office", "meeting room"]
SCREEN_PLACES = ["home", "office", "school", "lab"]  # 風景の写真が合う場所（office・school・lab では画面を消して置く）


def _cross_base(prefix: str, span: float, z: float = 0.0, color: str = STEEL) -> list[Part]:
    """十字の脚（2 本の平たい角材を直角に重ねる）。"""
    t = 0.035
    parts = [_p(f"{prefix}FootX", "box", (span, 0.06, t), (0, 0, z + t / 2), color, "metal", material="steel",
                bevel=0.006),
             _p(f"{prefix}FootY", "box", (0.06, span, t), (0, 0, z + t / 2), color, "metal", material="steel",
                bevel=0.006)]
    return parts


def _column(prefix: str, x: float, y: float, d: float, z0: float, z1: float, color: str = STEEL) -> Part:
    return _p(f"{prefix}Column", "cylinder", (d, d, z1 - z0), (x, y, (z0 + z1) / 2), color, "metal", material="steel")


def _disc(prefix: str, x: float, y: float, d: float, t: float, color: str = STEEL) -> Part:
    return _p(f"{prefix}Disc", "cylinder", (d, d, t), (x, y, t / 2), color, "metal", material="steel")


# ---------------------------------------------------------------- テーブル


def meeting_table_round() -> Product:
    """4 人用の丸いミーティングテーブル（直径 1000 mm、一本脚に十字の脚）。"""
    D, H, T = 1.00, 0.72, 0.025
    parts = [_p("Top", "cylinder", (D, D, T), (0, 0, H - T / 2), WHITE, "matte", material="wood"),
             _p("TopEdge", "cylinder", (D + 0.004, D + 0.004, 0.006), (0, 0, H - T / 2), "#B9BCC0", "plastic",
                collision=False, material="plastic"),
             _p("Hub", "cylinder", (0.30, 0.30, 0.012), (0, 0, H - T - 0.006), STEEL, "metal", material="steel"),
             _column("", 0, 0, 0.076, 0.035, H - T - 0.012),
             *_cross_base("", 0.68)]
    return Product(slug="meeting_table_round", name="丸いミーティングテーブル 直径 1000（一本脚）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=24.0, static=False, material="wood",
                   description="形はオフィスの打ち合わせ・家庭のダイニングで使う一般的な 4 人用の丸テーブル（幅 1000 mm・"
                               "奥行き 1000 mm・高さ 720 mm、白いメラミンの円い天板にスチールの一本脚と十字の脚）で、"
                               "寸法・質量は代表値。天板の下に幕板が無く、椅子の座面を差し込める。動かせる（static ではない）。",
                   tags=["丸テーブル", "ミーティングテーブル", "会議テーブル", "ダイニングテーブル", "テーブル",
                         "round table", "meeting table", "round meeting table", "pedestal table", "table",
                         *OFFICE_TAGS, *HOME_TAGS], photos=[], colors=Colors(label_base=WHITE), images=[],
                   parts=parts)


def meeting_table_oval() -> Product:
    """6 人用の楕円のミーティングテーブル（1800 × 900 mm、一本脚 2 本に円盤のベース）。"""
    W, D, H, T = 1.80, 0.90, 0.72, 0.028
    top = "#E8C060"  # 明るい黄色のメラミン
    parts = [_p("Top", "cylinder", (W, D, T), (0, 0, H - T / 2), top, "matte", material="wood", segments=64),
             _p("TopEdge", "cylinder", (W + 0.004, D + 0.004, 0.008), (0, 0, H - T / 2), mix(top, "#000000", 0.25),
                "plastic", collision=False, material="plastic", segments=64),
             _p("Beam", "box", (1.00, 0.08, 0.03), (0, 0, H - T - 0.015), STEEL, "metal", material="steel")]
    for side, x in (("L", -0.50), ("R", 0.50)):
        parts += [_column(side, x, 0, 0.076, 0.015, H - T - 0.03), _disc(side, x, 0, 0.56, 0.015)]
    return Product(slug="meeting_table_oval", name="楕円のミーティングテーブル 1800×900（一本脚 2 本）",
                   shape_class="assembly", category="fixture", dims=_dims(parts), mass_kg=42.0, static=False,
                   material="wood",
                   description="形はオフィスの会議室・休憩室に置く一般的な 6 人用の楕円テーブル（幅 1800 mm・奥行き 900 mm・"
                               "高さ 720 mm、黄色いメラミンの楕円の天板、スチールの一本脚 2 本に円盤のベース）で、"
                               "寸法・質量は代表値。天板の下は脚の間をつなぐ梁だけで、椅子の座面を差し込める。"
                               "動かせる（static ではない）。",
                   tags=["楕円テーブル", "ミーティングテーブル", "会議テーブル", "テーブル", "oval table",
                         "meeting table", "conference table", "oval meeting table", "table", *OFFICE_TAGS],
                   photos=[], colors=Colors(label_base=top), images=[], parts=parts)


def coffee_table_oval() -> Product:
    """ソファの前の楕円のローテーブル（1200 × 600 mm・高さ 400 mm）。"""
    W, D, H, T = 1.20, 0.60, 0.40, 0.022
    top = "#E8C060"
    parts = [_p("Top", "cylinder", (W, D, T), (0, 0, H - T / 2), top, "matte", material="wood", segments=64),
             _p("TopEdge", "cylinder", (W + 0.004, D + 0.004, 0.006), (0, 0, H - T / 2), mix(top, "#000000", 0.25),
                "plastic", collision=False, material="plastic", segments=64),
             _p("Beam", "box", (0.70, 0.06, 0.025), (0, 0, H - T - 0.0125), STEEL, "metal", material="steel")]
    for side, x in (("L", -0.35), ("R", 0.35)):
        parts += [_column(side, x, 0, 0.060, 0.012, H - T - 0.025), _disc(side, x, 0, 0.40, 0.012)]
    return Product(slug="coffee_table_oval", name="楕円のローテーブル 1200×600", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=18.0, static=False, material="wood",
                   description="形はリビング・オフィスの休憩コーナーでソファの前に置く一般的な楕円のローテーブル"
                               "（幅 1200 mm・奥行き 600 mm・高さ 400 mm、黄色いメラミンの楕円の天板、スチールの一本脚 2 本に"
                               "円盤のベース）で、寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["ローテーブル", "コーヒーテーブル", "センターテーブル", "楕円テーブル", "coffee table",
                         "oval coffee table", "low table", "center table", *HOME_TAGS, "living room", "lounge"],
                   photos=[], colors=Colors(label_base=top), images=[], parts=parts)


def side_table_round() -> Product:
    """ソファの横の丸いサイドテーブル（直径 450 mm・高さ 550 mm、一本脚に円盤のベース）。"""
    D, H, T = 0.45, 0.55, 0.020
    parts = [_p("Top", "cylinder", (D, D, T), (0, 0, H - T / 2), OAK, "matte", material="wood"),
             _column("", 0, 0, 0.040, 0.012, H - T),
             _disc("", 0, 0, 0.36, 0.012)]
    return Product(slug="side_table_round", name="丸いサイドテーブル 直径 450（一本脚）", shape_class="assembly",
                   category="household", dims=_dims(parts), mass_kg=6.5, static=False, material="wood",
                   description="形はソファ・ベッドの横に置く一般的な丸いサイドテーブル（幅 450 mm・奥行き 450 mm・"
                               "高さ 550 mm、明るい木の円い天板に黒いスチールの一本脚と円盤のベース）で、寸法・質量は代表値。"
                               "動かせる（static ではない）。",
                   tags=["サイドテーブル", "丸テーブル", "ソファテーブル", "side table", "round side table",
                         "end table", "accent table", *FURNITURE_TAGS, *HOME_TAGS], photos=[],
                   colors=Colors(label_base=OAK), images=[], parts=parts)


# ---------------------------------------------------------------- 椅子・ソファ


CHAIR_SEAT_Z = 0.45
CHAIR_H = 0.80
CHAIR_SEAT = "#3E8C8A"  # 青緑の樹脂


def _chair_parts(prefix: str = "", dy: float = 0.0, dz: float = 0.0, seat: str = CHAIR_SEAT) -> list[Part]:
    """スタッキングチェア 1 脚（スチールの 4 本脚に樹脂の座面・背もたれ）。座面の下に横桟が無い。"""
    sz, t, leg = CHAIR_SEAT_Z, 0.030, 0.022
    yb = 0.21  # 後ろ脚・背もたれの支柱
    parts = [_p(f"{prefix}Seat", "box", (0.46, 0.44, t), (0, -0.01 + dy, dz + sz - t / 2), seat, "plastic",
                material="plastic", bevel=0.01),
             _p(f"{prefix}Back", "box", (0.44, 0.02, 0.24), (0, yb + 0.015 + dy, dz + CHAIR_H - 0.12), seat, "plastic",
                material="plastic", bevel=0.008)]
    for side, x in (("L", -0.215), ("R", 0.215)):
        parts += [_p(f"{prefix}LegF{side}", "cylinder", (leg, leg, sz - t), (x, -0.20 + dy, dz + (sz - t) / 2),
                     CHROME, "metal", material="steel", segments=16),
                  _p(f"{prefix}LegB{side}", "cylinder", (leg, leg, CHAIR_H), (x, yb + dy, dz + CHAIR_H / 2), CHROME,
                     "metal", material="steel", segments=16),
                  _p(f"{prefix}Rail{side}", "box", (leg, 0.41, 0.018), (x, 0.005 + dy, dz + sz - t - 0.009), CHROME,
                     "metal", material="steel", bevel=0.004)]
    return parts


def stacking_chair() -> Product:
    """会議室・教室のスタッキングチェア（樹脂の座面と背もたれ、スチールの脚）。"""
    parts = _chair_parts()
    return Product(slug="stacking_chair", name="スタッキングチェア（樹脂の座面・スチールの脚）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=4.5, static=False, material="plastic",
                   description="形はオフィスの会議室・休憩室・教室で使う一般的なスタッキングチェア（幅 460 mm・奥行き 470 mm・"
                               "高さ 800 mm・座面の高さ 450 mm、青緑の樹脂の座面と背もたれ、クロムめっきのスチールの 4 本脚）で、"
                               "寸法・質量は代表値。座面の下に横桟が無く、テーブルの天板の下に座面ごと差し込める。"
                               "動かせる（static ではない）。",
                   tags=["スタッキングチェア", "椅子", "いす", "会議椅子", "ミーティングチェア", "stacking chair",
                         "stackable chair", "chair", "meeting chair", "conference chair", *OFFICE_TAGS, "school"],
                   photos=[], colors=Colors(label_base=CHAIR_SEAT), images=[], parts=parts)


STACK_N, STACK_DZ, STACK_DY = 6, 0.07, 0.012  # 積んだ数と、1 脚ごとに上・後ろへずれる量


def stacking_chair_stack() -> Product:
    """スタッキングチェアを 6 脚積んだもの（1 脚ごとに少し上・後ろにずれる）。"""
    parts = []
    for k in range(STACK_N):
        parts += _chair_parts(f"C{k}", dy=k * STACK_DY - (STACK_N - 1) * STACK_DY / 2, dz=k * STACK_DZ)
    return Product(slug="stacking_chair_stack", name="積み重ねたスタッキングチェア 6 脚", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=4.5 * STACK_N, static=False, material="plastic",
                   description="形は会議室・休憩室の隅に片付けた一般的なスタッキングチェア 6 脚の山（幅 460 mm・奥行き 530 mm・"
                               "高さ 1150 mm、1 脚ごとに 70 mm 上・12 mm 後ろにずれて重なる）で、寸法・質量は代表値。"
                               "椅子は stacking_chair と同じ形。全体で 1 つの剛体。動かせる（static ではない）。",
                   tags=["スタッキングチェア", "積み重ねた椅子", "椅子の山", "椅子", "stacked chairs",
                         "stacking chairs", "chair stack", "pile of chairs", "stacking chair", *OFFICE_TAGS],
                   photos=[], colors=Colors(label_base=CHAIR_SEAT), images=[], parts=parts)


def lounge_sofa_3seat() -> Product:
    """布張りの 3 人掛けソファ（幅 2000 mm、ひじ掛け付き）。"""
    W, D, H = 2.00, 0.85, 0.80
    fab = "#B5463C"  # 赤い布
    dark = mix(fab, "#000000", 0.18)
    arm, leg_h, base_t = 0.15, 0.10, 0.18
    seat_z = 0.42
    back_d = 0.20
    inner = W - 2 * arm
    parts = [_p("Base", "box", (W - 0.02, D - 0.02, base_t), (0, 0, leg_h + base_t / 2), dark, "matte",
                material="fabric", bevel=0.02),
             _p("BackFrame", "box", (inner, back_d, H - leg_h - base_t), (0, D / 2 - back_d / 2,
                leg_h + base_t + (H - leg_h - base_t) / 2), fab, "matte", material="fabric", bevel=0.04)]
    cw = inner / 3
    for k in range(3):
        x = -inner / 2 + cw * (k + 0.5)
        parts += [_p(f"SeatCushion{k}", "box", (cw - 0.01, D - back_d - 0.02, seat_z - leg_h - base_t),
                     (x, -back_d / 2 - 0.01, leg_h + base_t + (seat_z - leg_h - base_t) / 2), fab, "matte",
                     material="fabric", bevel=0.04),
                  _p(f"BackCushion{k}", "box", (cw - 0.02, 0.14, 0.34), (x, D / 2 - back_d - 0.06, seat_z + 0.17),
                     fab, "matte", material="fabric", bevel=0.05)]
    for side, x in (("L", -W / 2 + arm / 2), ("R", W / 2 - arm / 2)):
        parts.append(_p(f"Arm{side}", "box", (arm, D, 0.62 - leg_h), (x, 0, leg_h + (0.62 - leg_h) / 2), fab, "matte",
                        material="fabric", bevel=0.04))
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(_p(f"Leg{n}", "box", (0.04, 0.04, leg_h), (sx * (W / 2 - 0.06), sy * (D / 2 - 0.06), leg_h / 2),
                        WALNUT, "matte", material="wood", bevel=0.004))
    return Product(slug="lounge_sofa_3seat", name="布張りの 3 人掛けソファ（ひじ掛け付き）", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=55.0, static=False, material="fabric",
                   description="形はリビング・オフィスの休憩室に置く一般的な布張りの 3 人掛けソファ（幅 2000 mm・"
                               "奥行き 850 mm・高さ 800 mm・座面の高さ 420 mm、赤い布、座と背のクッション 3 つずつ、"
                               "左右のひじ掛け、木の短い脚 4 本）で、寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["ソファ", "3 人掛けソファ", "布張りソファ", "長いす", "sofa", "couch", "3-seater sofa",
                         "three seater sofa", "lounge sofa", *HOME_TAGS, "living room", "lounge", "office"],
                   photos=[], colors=Colors(label_base=fab), images=[], parts=parts)


def pouf_round() -> Product:
    """丸い布張りのスツール（プフ、直径 450 mm・高さ 420 mm）。"""
    D, H = 0.45, 0.42
    fab = "#C9B79C"
    parts = [_p("Body", "cylinder", (D, D, H - 0.03), (0, 0, (H - 0.03) / 2), fab, "matte", material="fabric"),
             _p("Cushion", "bun", (D - 0.01, D - 0.01, 0.03), (0, 0, H - 0.015), mix(fab, WHITE, 0.08), "matte",
                material="fabric"),
             _p("PipingTop", "torus", (D + 0.006, D + 0.006, 0.010), (0, 0, H - 0.03), mix(fab, "#000000", 0.25),
                "matte", collision=False, material="fabric"),
             _p("PipingBottom", "torus", (D + 0.006, D + 0.006, 0.010), (0, 0, 0.012), mix(fab, "#000000", 0.25),
                "matte", collision=False, material="fabric")]
    return Product(slug="pouf_round", name="丸い布張りのスツール（プフ）直径 450", shape_class="assembly",
                   category="household", dims=_dims(parts), mass_kg=4.0, static=False, material="fabric",
                   description="形はリビングで足のせ・補助の席にする一般的な丸いプフ（幅 450 mm・奥行き 450 mm・高さ 420 mm、"
                               "ベージュの布張りの円柱、上下の縁にパイピング）で、寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["プフ", "スツール", "オットマン", "丸いスツール", "足のせ", "pouf", "pouffe", "ottoman",
                         "round stool", "footstool", *FURNITURE_TAGS, *HOME_TAGS], photos=[],
                   colors=Colors(label_base=fab), images=[], parts=parts)


# ---------------------------------------------------------------- テレビスタンド


def _tv_picture(w_mm: float, h_mm: float, seed: int):
    """テレビに映す風景（湖の写真）。"""
    c = Canvas(w_mm, h_mm, 1080 / h_mm, "#000000", seed)
    c.photo("lake", 0, 0, w_mm, h_mm)
    return trim_safe(finish(c.array(), "screen", seed, 0.6))


def tv_cart() -> Product:
    """キャスター付きのテレビスタンドに載せた 65 型のテレビ。"""
    sw, sh = 1.439, 0.809  # 65 型（16:9）の画面
    tw, th, td = 1.452, 0.840, 0.060  # テレビの外形
    tv_z = 1.30  # 画面の中心の高さ
    base_w, base_d = 0.90, 0.66
    cz = 0.11  # キャスターと脚の高さ
    tv_y = -0.06
    parts = [
        # 脚: 左右の前後に長い脚と、つなぐ横の梁
        _p("FootL", "box", (0.07, base_d, 0.05), (-base_w / 2 + 0.035, 0, cz - 0.025), STEEL, "metal",
           material="steel", bevel=0.006),
        _p("FootR", "box", (0.07, base_d, 0.05), (base_w / 2 - 0.035, 0, cz - 0.025), STEEL, "metal",
           material="steel", bevel=0.006),
        _p("FootBeam", "box", (base_w - 0.14, 0.08, 0.05), (0, 0.06, cz - 0.025), STEEL, "metal", material="steel",
           bevel=0.006),
        _p("Shelf", "box", (0.60, 0.40, 0.02), (0, 0.06, 0.75), STEEL, "metal", material="steel", bevel=0.004),
        _p("Bracket", "box", (0.70, 0.08, 0.40), (0, tv_y + td / 2 + 0.04, tv_z), STEEL, "metal",
           material="steel", bevel=0.004),
        _p("TvBody", "box", (tw, td, th), (0, tv_y, tv_z), "#151618", "plastic", material="plastic", bevel=0.006),
        _p("Screen", "box", (sw, 0.003, sh), (0, tv_y - td / 2 - 0.0015, tv_z), "#101214", "screen",
           faces={"front": 0}, collision=False, bevel=0),
    ]
    for side, x in (("L", -0.25), ("R", 0.25)):
        parts.append(_p(f"Pole{side}", "box", (0.06, 0.06, 1.60 - cz), (x, 0.06 + 0.02, cz + (1.60 - cz) / 2), STEEL,
                        "metal", material="steel", bevel=0.004))
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x, y = sx * (base_w / 2 - 0.035), sy * (base_d / 2 - 0.05)
        parts += [_p(f"Caster{n}", "cylinder", (0.06, 0.06, 0.028), (x, y, 0.03), "#1A1A1A", "plastic",
                     rot=(0, 90, 0), material="rubber", segments=20),
                  _p(f"CasterFork{n}", "box", (0.04, 0.05, 0.03), (x, y, 0.045), CHROME, "metal", material="steel",
                     bevel=0.003)]
    return Product(slug="tv_cart", name="キャスター付きスタンドのテレビ 65 型", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=62.0, static=False, material="steel",
                   description="形はオフィスの会議室・休憩室や家庭で使う一般的なキャスター付きのテレビスタンドに 65 型の液晶テレビ"
                               "を載せたもの（幅 1450 mm・奥行き 660 mm・高さ 1720 mm、黒いスチールの支柱 2 本と脚・"
                               "中ほどの棚、キャスター 4 つ）で、寸法・質量は代表値。画面は Screen バリアントで点けた（風景の"
                               "写真）・消したを切り替える。写真は CC0。動かせる（static ではない）。",
                   tags=["テレビ", "テレビスタンド", "移動式テレビスタンド", "液晶テレビ", "65型", "ディスプレイ",
                         "television", "tv", "tv stand", "tv cart", "mobile tv stand", "rolling tv stand",
                         "display", *OFFICE_TAGS, *HOME_TAGS], photos=["lake"], colors=Colors(label_base=STEEL),
                   images=[_tv_picture(sw * 1000, sh * 1000, 19701)], parts=parts, screen_places=SCREEN_PLACES)


# ---------------------------------------------------------------- 収納


def wardrobe_sliding() -> Product:
    """引き戸の大きなワードローブ（幅 1800 mm、引き戸 2 枚）。"""
    W, D, H = 1.80, 0.60, 2.00
    body = "#F1EEE8"
    door = "#E4DED3"
    plinth = 0.06
    body_d = D - 0.04
    parts = [_p("Body", "box", (W, body_d, H - plinth), (0, D / 2 - body_d / 2, plinth + (H - plinth) / 2), body,
                "matte", material="wood", bevel=0.004),
             _p("Plinth", "box", (W - 0.04, body_d - 0.04, plinth), (0, D / 2 - body_d / 2 + 0.02, plinth / 2),
                mix(body, "#000000", 0.3), "matte", material="wood"),
             _p("RailTop", "box", (W, 0.04, 0.03), (0, -D / 2 + 0.02, H - 0.015), ALU_LIGHT, "metal",
                material="aluminum", bevel=0.002)]
    y_front = -D / 2 + 0.040  # 本体の前の面
    dh = H - plinth - 0.04
    dw = W / 2 + 0.02  # 中央で 40 mm 重なる
    for side, s, y in (("L", -1, y_front - 0.030), ("R", 1, y_front - 0.010)):  # 左が手前のレール、右が奥のレール
        x = s * (W / 2 - dw / 2)
        parts += [_p(f"Door{side}", "box", (dw, 0.018, dh), (x, y, plinth + 0.01 + dh / 2), door, "matte",
                     collision=False, material="wood", bevel=0.003),
                  _p(f"Pull{side}", "box", (0.02, 0.006, 0.40), (s * (W / 2 - 0.04), y - 0.012, 1.05), ALU_LIGHT,
                     "metal", collision=False, material="aluminum", bevel=0.002)]
    return Product(slug="wardrobe_sliding", name="引き戸のワードローブ 幅 1800", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=110.0, static=True, material="wood",
                   description="形は寝室・リビングの壁際に置く一般的な引き戸のワードローブ（幅 1800 mm・奥行き 600 mm・"
                               "高さ 2000 mm、生成りの本体に手前と奥のレールの引き戸 2 枚、縦の細い取っ手、台輪）で、"
                               "寸法・質量は代表値。扉は開かない。床に固定。",
                   tags=["ワードローブ", "引き戸のクローゼット", "クローゼット", "洋服タンス", "衣装棚", "wardrobe",
                         "sliding door wardrobe", "closet", "sliding wardrobe", "armoire", *FURNITURE_TAGS,
                         *HOME_TAGS], photos=[], colors=Colors(label_base=body), images=[], parts=parts)



def glass_display_cabinet() -> Product:
    """ガラス扉の飾り棚（幅 800 mm、ガラスの棚板 3 枚）。"""
    W, D, H = 0.80, 0.40, 1.80
    wood = WALNUT
    t = 0.02
    plinth = 0.08
    parts = [_p("Plinth", "box", (W - 0.02, D - 0.03, plinth), (0, 0.01, plinth / 2), mix(wood, "#000000", 0.3),
                "matte", material="wood"),
             _p("Bottom", "box", (W, D, t), (0, 0, plinth + t / 2), wood, "matte", material="wood", bevel=0.003),
             _p("Top", "box", (W, D, t), (0, 0, H - t / 2), wood, "matte", material="wood", bevel=0.003),
             _p("SideL", "box", (t, D, H - plinth - 2 * t), (-W / 2 + t / 2, 0, (plinth + H) / 2), wood, "matte",
                material="wood"),
             _p("SideR", "box", (t, D, H - plinth - 2 * t), (W / 2 - t / 2, 0, (plinth + H) / 2), wood, "matte",
                material="wood"),
             _p("BackPanel", "box", (W - 2 * t, 0.006, H - plinth - 2 * t), (0, D / 2 - 0.003, (plinth + H) / 2),
                mix(wood, WHITE, 0.15), "matte", material="wood", bevel=0)]
    inner_w = W - 2 * t
    for k, z in enumerate((0.48, 0.88, 1.28)):  # ガラスの棚板
        parts.append(_p(f"Shelf{k}", "box", (inner_w - 0.004, D - 0.06, 0.006), (0, 0.01, z), "#DDEBEA", "glass",
                        material="glass", bevel=0))
    door_h = H - plinth - 2 * t
    for side, s in (("L", -1), ("R", 1)):
        x = s * inner_w / 4
        fw = 0.04
        dw = inner_w / 2 - 0.002
        y = -D / 2 + 0.010
        zc = (plinth + H) / 2
        parts += [_p(f"Glass{side}", "box", (dw - 2 * fw, 0.004, door_h - 2 * fw), (x, y, zc), "#DDEBEA", "glass",
                     collision=False, material="glass", bevel=0),
                  _p(f"DoorFrameT{side}", "box", (dw, 0.02, fw), (x, y, zc + door_h / 2 - fw / 2), wood, "matte",
                     collision=False, material="wood", bevel=0.002),
                  _p(f"DoorFrameB{side}", "box", (dw, 0.02, fw), (x, y, zc - door_h / 2 + fw / 2), wood, "matte",
                     collision=False, material="wood", bevel=0.002),
                  _p(f"DoorFrameO{side}", "box", (fw, 0.02, door_h - 2 * fw), (s * (inner_w / 2 - fw / 2), y, zc), wood,
                     "matte", collision=False, material="wood", bevel=0.002),
                  _p(f"DoorFrameI{side}", "box", (fw, 0.02, door_h - 2 * fw), (s * 0.001 + s * fw / 2, y, zc), wood,
                     "matte", collision=False, material="wood", bevel=0.002),
                  _p(f"Knob{side}", "cylinder", (0.016, 0.016, 0.02), (s * (fw + 0.01), y - 0.02, 1.00), ALU_LIGHT,
                     "metal", rot=(90, 0, 0), collision=False, material="steel", segments=16)]
    return Product(slug="glass_display_cabinet", name="ガラス扉の飾り棚 幅 800", shape_class="assembly",
                   category="fixture", dims=_dims(parts), mass_kg=48.0, static=True, material="wood",
                   description="形はリビングに置く一般的なガラス扉の飾り棚（幅 800 mm・奥行き 400 mm・高さ 1800 mm、"
                               "濃い木の枠、両開きのガラス扉、ガラスの棚板 3 枚、台輪）で、寸法・質量は代表値。扉は開かない。"
                               "中の棚は空（食器・置物を置く）。床に固定。",
                   tags=["飾り棚", "ガラスキャビネット", "キャビネット", "コレクションケース", "食器棚", "display cabinet",
                         "glass cabinet", "curio cabinet", "china cabinet", "vitrine", *FURNITURE_TAGS, *HOME_TAGS],
                   photos=[], colors=Colors(label_base=wood), images=[], parts=parts)


# ---------------------------------------------------------------- 照明・壁の小物


def floor_lamp() -> Product:
    """布のシェードのフロアランプ（高さ 1600 mm）。"""
    shade_d, shade_h, H = 0.42, 0.30, 1.60
    shade = "#EFE6D2"
    shade_z0 = H - shade_h
    parts = [_disc("Base", 0, 0, 0.30, 0.025, STEEL),
             _column("Pole", 0, 0, 0.022, 0.025, shade_z0 + 0.12),
             _p("Harp", "box", (0.012, 0.012, 0.12), (0, 0, shade_z0 + 0.06), CHROME, "metal", collision=False,
                material="steel", bevel=0),
             _p("Socket", "cylinder", (0.04, 0.04, 0.05), (0, 0, shade_z0 + 0.145), "#E8E2D4", "plastic",
                collision=False, material="plastic"),
             _p("Bulb", "dome", (0.06, 0.06, 0.05), (0, 0, shade_z0 + 0.17), "#FFF6E0", "light", collision=False,
                material="glass"),
             _p("Shade", "cylinder", (shade_d, shade_d, shade_h), (0, 0, shade_z0 + shade_h / 2), shade,
                "translucent", material="fabric"),
             _p("ShadeRimBottom", "torus", (shade_d + 0.004, shade_d + 0.004, 0.006), (0, 0, shade_z0 + 0.003),
                mix(shade, "#000000", 0.2), "matte", collision=False, material="fabric"),
             _p("Switch", "box", (0.03, 0.05, 0.015), (0.08, -0.08, 0.0325), "#E8E2D4", "plastic", collision=False,
                material="plastic", bevel=0.003)]
    lux = Light(name="ShadeLux", size=[0.30, 0.30], center=[0, 0, shade_z0 - 0.001], intensity=3000.0,
                kelvin=2700.0)
    return Product(slug="floor_lamp", name="布のシェードのフロアランプ", shape_class="assembly", category="fixture",
                   dims=_dims(parts), mass_kg=6.0, static=True, material="steel",
                   description="形はリビング・寝室のソファやベッドの横に置く一般的なフロアランプ（幅 420 mm・奥行き 420 mm・"
                               "高さ 1600 mm、黒いスチールの丸い台と細い支柱、生成りの布の円筒のシェード）で、寸法・質量は代表値。"
                               "電球色の光がシェードの下から出る（Lighting バリアントで消せる）。倒れないよう床に固定。",
                   tags=["フロアランプ", "フロアライト", "スタンドライト", "照明", "ランプ", "floor lamp", "standing lamp",
                         "floor light", "lamp", *FURNITURE_TAGS, *HOME_TAGS], photos=[],
                   colors=Colors(label_base=shade), images=[], parts=parts, lights=[lux])


def paper_towel_dispenser() -> Product:
    """壁掛けのペーパータオルホルダー（白い樹脂、下からペーパーを引き出す）。"""
    W, D, H = 0.28, 0.13, 0.36
    white = "#F2F3F2"
    drop = 0.04  # 下の口から垂れたペーパー
    bz = drop
    bh = H - drop
    parts = [_p("Back", "box", (W, 0.010, bh), (0, -0.005, bz + bh / 2), white, "plastic", material="plastic",
                bevel=0.004),
             _p("Cover", "box", (W, D - 0.010, bh), (0, -0.010 - (D - 0.010) / 2, bz + bh / 2), white, "plastic",
                material="plastic", bevel=0.02),
             _p("Window", "box", (0.10, 0.002, 0.03), (0, -D - 0.001, bz + bh - 0.07), "#7B8A93", "translucent",
                collision=False, material="plastic", bevel=0),
             _p("Lock", "cylinder", (0.016, 0.016, 0.004), (0, -D - 0.002, bz + bh - 0.03), "#9AA0A6", "metal",
                rot=(90, 0, 0), collision=False, material="plastic", segments=16),
             _p("Slot", "box", (0.20, 0.02, 0.004), (0, -D + 0.03, bz + 0.001), "#3A3D42", "matte", collision=False,
                material="plastic", bevel=0),
             _p("Towel", "box", (0.19, 0.002, drop), (0, -D + 0.03, drop / 2), "#FBFBF6", "matte", collision=False,
                material="paper", bevel=0)]
    return Product(slug="paper_towel_dispenser", name="壁掛けのペーパータオルホルダー", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=1.6, static=True, material="plastic",
                   description="形は洗面所・給湯室・トイレの壁に付ける一般的なペーパータオルホルダー（幅 280 mm・奥行き 130 mm・"
                               "高さ 360 mm、白い樹脂のカバーに残量の窓と鍵、下の口から 1 枚垂れる）で、寸法・質量は代表値。"
                               "背面（y = 0）を壁に付け、正面（-Y）が室内側。ペーパーには当たり判定が無い。",
                   tags=["ペーパータオルホルダー", "ペーパータオル", "タオルディスペンサー", "手拭き", "壁掛け",
                         "paper towel dispenser", "towel dispenser", "paper towel holder", "hand towel dispenser",
                         "wall mounted", "restroom", "washroom", "office"], photos=[],
                   colors=Colors(label_base=white), images=[], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    meeting_table_round, meeting_table_oval, coffee_table_oval, side_table_round, stacking_chair,
    stacking_chair_stack, lounge_sofa_3seat, pouf_round, tv_cart, wardrobe_sliding, glass_display_cabinet,
    floor_lamp, paper_towel_dispenser)}
