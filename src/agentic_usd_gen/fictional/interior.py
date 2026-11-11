"""架空の製品のデザイン: 内装の仕上げ材と天井の設備（間仕切り・床・壁・天井）。

store_env.py・windows.py と同じく、実在のメーカー名・品番は使わず、形と寸法は同じ種類の製品の一般的な値にする。
カテゴリは environment、どれも固定（static）。原点は底面の中央、正面（-Y）が部屋の側。
- 間仕切り・衝立は床に立つ。厚みの中心が y = 0（両面が見える）。ガラスの間仕切りの戸は縦軸の回転の関節で開く。
- 床材は上面が見える面（z = 厚さ）。並べて敷けるよう、外周の目地は半分の幅にする。
- 壁材は背面を壁に付け、前（-Y）へ出る。
- 天井の設備は mount = "ceiling"（上面が天井に付く）。天井裏に入る本体は省き、天井の下に見える部分だけを作る。
"""

from __future__ import annotations

import math

import numpy as np

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .paint import Canvas, mix
from .store_env import ALU, ALU_DARK, ENV, GLASS, STAINLESS, WHITE, _img, _link, _p

FROSTED = "#E6ECEF"
CEIL_WHITE = "#F3F3F1"


def _wood(w_mm: float, h_mm: float, base: str, light: str, dark: str, seed: int, n: int = 120,
          vertical: bool = True) -> Canvas:
    """木目（縦か横の筋）を描いた Canvas。"""
    c = Canvas(w_mm, h_mm, None, base, seed)
    c.gradient(0, 0, w_mm, h_mm, light, dark, horizontal=not vertical)
    L, S = (h_mm, w_mm) if vertical else (w_mm, h_mm)
    for _ in range(n):
        s = c.rng.uniform(0, S)
        amp, ph = c.rng.uniform(1, 6), c.rng.uniform(0, 6.28)
        pts = [(s + amp * math.sin(t / 160 + ph), t) for t in np.arange(0, L + 1, max(L / 60, 5))]
        if not vertical:
            pts = [(t, v) for v, t in pts]
        c.line(pts, c.rng.choice([mix(base, dark, 0.5), mix(base, light, 0.5), dark]), c.rng.uniform(0.6, 2.0))
    return c


def _rough_edges(c: Canvas, w_mm: float, h_mm: float, colors: list[str], r: float = 2.0, n: int = 600) -> None:
    """縁に粒を散らす（縁が単色の画像は切り抜かれるため）。"""
    for _ in range(n):
        t = c.rng.uniform(0, 1)
        rr = c.rng.uniform(r * 0.5, r)
        col = c.rng.choice(colors)
        for x, y in ((t * w_mm, 0), (t * w_mm, h_mm), (0, t * h_mm), (w_mm, t * h_mm)):
            c.ellipse(x - rr, y - rr, x + rr, y + rr, fill=col)


def _fabric(w_mm: float, h_mm: float, base: str, seed: int) -> np.ndarray:
    """織物の面（細かい縦横の糸のむら）。"""
    c = Canvas(w_mm, h_mm, None, base, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(base, WHITE, 0.08), mix(base, "#000000", 0.08))
    step = 4.0
    y = 0.0
    while y < h_mm:
        c.line([(0, y), (w_mm, y)], mix(base, "#000000", c.rng.uniform(0.05, 0.15)), 0.8)
        y += step
    x = 0.0
    while x < w_mm:
        c.line([(x, 0), (x, h_mm)], mix(base, WHITE, c.rng.uniform(0.03, 0.10)), 0.6)
        x += step
    return _img(c, "paper", seed, 0.3)


def _tatami(w_mm: float, h_mm: float, seed: int, heri: str | None = "#2E3B2F", heri_w: float = 30.0,
            sides: str = "all") -> Canvas:
    """畳表（い草の目を縦に）と縁（へり）。sides は縁を付ける辺（"all" か "long"＝長辺だけ）。"""
    base = "#C9C08A"
    c = Canvas(w_mm, h_mm, None, base, seed)
    c.gradient(0, 0, w_mm, h_mm, "#D2CA96", "#BDB27A", horizontal=True)
    x = 0.0
    while x < w_mm:  # い草の目（縦）
        c.line([(x, 0), (x, h_mm)], c.rng.choice(["#B3A86F", "#D9D2A2", "#C2B880"]), 1.2)
        x += 3.0
    y = 0.0
    while y < h_mm:  # 経糸（たていと）の目
        c.line([(0, y), (w_mm, y)], "#B9AE76", 0.5)
        y += 15.0
    if heri:
        if w_mm >= h_mm or sides == "all":  # 長辺（ここでは上下）
            c.rect(0, 0, w_mm, heri_w, fill=heri)
            c.rect(0, h_mm - heri_w, w_mm, h_mm, fill=heri)
        if sides == "all" or h_mm > w_mm:
            c.rect(0, 0, heri_w, h_mm, fill=heri)
            c.rect(w_mm - heri_w, 0, w_mm, h_mm, fill=heri)
        _rough_edges(c, w_mm, h_mm, [mix(heri, "#000000", 0.25), mix(heri, WHITE, 0.15)], heri_w * 0.2)
    return c


# ---------------------------------------------------------------- 間仕切り


def office_partition_panel() -> Product:
    """事務所のローパーティション（幅 1.2 m・高さ 1.6 m）。布張りのパネルをアルミの枠で囲み、足 2 本で立つ。"""
    W, H, D = 1.2, 1.6, 0.05
    fabric, frame = "#7D8790", "#C4C8CC"
    fw, foot_h = 0.025, 0.03
    img = _fabric(1150, 1520, fabric, 7001)
    pz0, ph = foot_h + fw, H - foot_h - 2 * fw
    parts = [_p("Panel", "box", (W - 2 * fw, 0.036, ph), (0, 0, pz0 + ph / 2), fabric, "matte",
                faces={"front": 0, "back": 0}, material="fabric", bevel=0.002),
             _p("FrameL", "box", (fw, 0.040, H - foot_h), (-W / 2 + fw / 2, 0, foot_h + (H - foot_h) / 2), frame,
                "metal", material="aluminum", bevel=0.003),
             _p("FrameR", "box", (fw, 0.040, H - foot_h), (W / 2 - fw / 2, 0, foot_h + (H - foot_h) / 2), frame,
                "metal", material="aluminum", bevel=0.003),
             _p("FrameT", "box", (W - 2 * fw, 0.040, fw), (0, 0, H - fw / 2), frame, "metal", material="aluminum",
                bevel=0.003),
             _p("FrameB", "box", (W - 2 * fw, 0.040, fw), (0, 0, foot_h + fw / 2), frame, "metal",
                material="aluminum", bevel=0.003)]
    for k, x in enumerate((-W / 2 + 0.15, W / 2 - 0.15)):
        parts.append(_p(f"Foot{k}", "box", (0.05, 0.45, foot_h), (x, 0, foot_h / 2), ALU_DARK, "metal",
                        material="steel", bevel=0.004))
    return Product(slug="office_partition_panel", name="ローパーティション 幅1200×高さ1600（布張り）",
                   shape_class="assembly", category=ENV, dims=Dimensions(H, W, depth=0.45), mass_kg=14.0, static=True,
                   material="fabric",
                   description="形は事務所の机の島や受付の仕切りに使う一般的なローパーティション（布張りのパネル、"
                               "幅 1200 mm・高さ 1600 mm・厚さ 40 mm、アルミの枠、奥行き 450 mm の足 2 本）で、寸法・質量は代表値。"
                               "厚みの中心が y = 0 で、両面とも同じ布。横に並べて仕切りにする。",
                   tags=["パーティション", "ローパーティション", "間仕切り", "衝立", "事務所", "内装", "partition",
                         "office partition", "panel screen", "room divider", "cubicle panel"],
                   colors=Colors(label_base=fabric), images=[img], parts=parts)


def _glass_wall_frame(W: float, H: float, D: float, fw: float) -> list[Part]:
    return [_p("FrameL", "box", (fw, D, H), (-W / 2 + fw / 2, 0, H / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("FrameR", "box", (fw, D, H), (W / 2 - fw / 2, 0, H / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("FrameT", "box", (W - 2 * fw, D, fw), (0, 0, H - fw / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("FrameB", "box", (W - 2 * fw, D, fw), (0, 0, fw / 2), ALU, "metal", material="aluminum", bevel=0.002)]


def _band(name: str, w: float, y: float, z: float) -> list[Part]:
    """ガラスの両面の衝突防止のすりガラス調の帯（高さ 1.0〜1.1 m）。"""
    return [_p(f"{name}{k}", "box", (w, 0.0005, 0.10), (0, y + s * 0.0045, z), FROSTED, "frosted", collision=False,
               material="film", bevel=0) for k, s in enumerate((-1, 1))]


def glass_partition() -> Product:
    """床から天井までのガラスの間仕切り（幅 1.2 m・高さ 2.7 m）。アルミの枠に強化ガラス、衝突防止の帯。"""
    W, H, D, fw = 1.2, 2.7, 0.08, 0.04
    parts = _glass_wall_frame(W, H, D, fw)
    parts.append(_p("Glass", "box", (W - 2 * fw + 0.01, 0.008, H - 2 * fw + 0.01), (0, 0, H / 2), GLASS, "glass",
                    material="glass", bevel=0))
    parts += _band("Band", W - 2 * fw, 0, 1.05)
    return Product(slug="glass_partition", name="ガラスパーティション 幅1200×高さ2700", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D), mass_kg=60.0, static=True, material="glass",
                   description="形は事務所の会議室や店の個室を仕切る床から天井までのガラスの間仕切り（強化ガラス 8 mm、"
                               "見付け 40 mm・見込み 80 mm のアルミの枠、高さ 1.0〜1.1 m にすりガラス調の衝突防止の帯）で、"
                               "寸法・質量は代表値。天井高 2.7 m の部屋で床から天井まで届く。横に並べて間仕切りにする。",
                   tags=["ガラスパーティション", "間仕切り", "ガラス", "会議室", "内装", "glass partition",
                         "glass wall", "office partition", "room divider"],
                   colors=Colors(label_base=GLASS), images=[], parts=parts)


def glass_partition_door() -> Product:
    """ガラスの間仕切りに入れる開き戸（枠の幅 0.9 m・高さ 2.7 m）。ガラスの戸の上に欄間のガラス。"""
    W, H, D, fw = 0.9, 2.7, 0.08, 0.04
    lw, lh, lt = W - 2 * fw - 0.006, 2.10, 0.040
    z0 = fw + 0.003
    tz = z0 + lh + 0.003  # 無目の下端
    parts = _glass_wall_frame(W, H, D, fw)
    parts += [_p("Transom", "box", (W - 2 * fw, D, fw), (0, 0, tz + fw / 2), ALU, "metal", material="aluminum",
                 bevel=0.002),
              _p("TransomGlass", "box", (W - 2 * fw + 0.01, 0.008, H - tz - 2 * fw + 0.01), (0, 0, (tz + fw + H - fw) / 2),
                 GLASS, "glass", material="glass", bevel=0)]
    st, rb = 0.045, 0.10
    x0 = -lw / 2  # 蝶番（左端）
    leaf = [_p("LeafGlass", "box", (lw - 2 * st + 0.01, 0.008, lh - st - rb + 0.01), (0, 0, z0 + rb + (lh - st - rb) / 2),
               GLASS, "glass", material="glass", bevel=0),
            _p("LeafStileL", "box", (st, lt, lh), (x0 + st / 2, 0, z0 + lh / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("LeafStileR", "box", (st, lt, lh), (lw / 2 - st / 2, 0, z0 + lh / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("LeafRailT", "box", (lw - 2 * st, lt, st), (0, 0, z0 + lh - st / 2), ALU, "metal", material="aluminum",
               bevel=0.002),
            _p("LeafRailB", "box", (lw - 2 * st, lt, rb), (0, 0, z0 + rb / 2), ALU, "metal", material="aluminum",
               bevel=0.002)]
    leaf += _band("LeafBand", lw - 2 * st, 0, 1.05)
    hx = lw / 2 - st / 2
    for k, s in enumerate((-1, 1)):  # 縦長のバーハンドル（両面）
        leaf += [_p(f"LeafBar{k}", "cylinder", (0.025, 0.025, 0.60), (hx, s * (lt / 2 + 0.045), 1.05), STAINLESS,
                    "metal", collision=False, material="steel"),
                 _p(f"LeafPost{k}a", "cylinder", (0.016, 0.016, 0.045), (hx, s * (lt / 2 + 0.0225), 1.25), STAINLESS,
                    "metal", rot=(90, 0, 0), collision=False, material="steel"),
                 _p(f"LeafPost{k}b", "cylinder", (0.016, 0.016, 0.045), (hx, s * (lt / 2 + 0.0225), 0.85), STAINLESS,
                    "metal", rot=(90, 0, 0), collision=False, material="steel")]
    _link(leaf, "Leaf", "LeafLink")
    parts += leaf
    return Product(slug="glass_partition_door", name="ガラスパーティションの開き戸 幅900×高さ2700",
                   shape_class="assembly", category=ENV, dims=Dimensions(H, W, depth=lt + 0.11), mass_kg=55.0,
                   static=True, material="glass",
                   description="形はガラスの間仕切りに入れる一般的な開き戸（枠の幅 900 mm・高さ 2700 mm、強化ガラスの戸 "
                               "約 810 × 2100 mm をアルミの框で囲み、上に欄間のガラス、両面に長さ 600 mm のバーハンドル）で、"
                               "寸法・質量は代表値。glass_partition と並べて使う。戸（LeafLink）は左の蝶番で奥（+Y）へ 90° まで開く。",
                   tags=["ガラスドア", "ドア", "開き戸", "ガラスパーティション", "間仕切り", "会議室", "建具", "内装",
                         "glass door", "glass partition door", "office door", "hinged door"],
                   colors=Colors(label_base=GLASS), images=[], parts=parts,
                   joints=[Joint(link="LeafLink", anchor=[x0, lt / 2, z0 + lh / 2], limits=[0.0, 90.0])])


def tsuitate_screen() -> Product:
    """飲食店の衝立（幅 0.9 m・高さ 1.5 m）。木の枠に格子とすりガラス調の和紙、台の足 2 本。"""
    W, H, D = 0.9, 1.5, 0.03
    wood, dark = "#8A6440", "#5E4128"
    frame_w, foot_h = 0.035, 0.06
    paper = Canvas(830, 1360, None, "#F2EEE3", 7011)
    paper.gradient(0, 0, 830, 1360, "#F5F1E7", "#ECE6D8")
    for _ in range(300):  # 和紙の繊維
        x, y = paper.rng.uniform(0, 830), paper.rng.uniform(0, 1360)
        a = paper.rng.uniform(0, 6.28)
        r = paper.rng.uniform(6, 22)
        paper.line([(x, y), (x + r * math.cos(a), y + r * math.sin(a))], "#E2DACA", 0.7)
    img = _img(paper, "paper", 7011, 0.3)
    wimg = _img(_wood(900, 1500, wood, "#9A7350", dark, 7012, 60), "paper", 7012, 0.3)
    pz0, ph = foot_h + frame_w, H - foot_h - 2 * frame_w
    pw = W - 2 * frame_w
    parts = [_p("Paper", "box", (pw, 0.004, ph), (0, 0, pz0 + ph / 2), "#F2EEE3", "translucent",
                faces={"front": 0, "back": 0}, collision=False, material="paper", bevel=0),
             _p("Back", "box", (pw, 0.002, ph), (0, 0.006, pz0 + ph / 2), "#EDE7DA", "matte", collision=True,
                material="paper", bevel=0),
             _p("FrameL", "box", (frame_w, D, H - foot_h), (-W / 2 + frame_w / 2, 0, foot_h + (H - foot_h) / 2), wood,
                "matte", faces={"front": 1}, material="wood", bevel=0.003),
             _p("FrameR", "box", (frame_w, D, H - foot_h), (W / 2 - frame_w / 2, 0, foot_h + (H - foot_h) / 2), wood,
                "matte", faces={"front": 1}, material="wood", bevel=0.003),
             _p("FrameT", "box", (pw, D, frame_w), (0, 0, H - frame_w / 2), wood, "matte", material="wood",
                bevel=0.003),
             _p("FrameB", "box", (pw, D, frame_w), (0, 0, foot_h + frame_w / 2), wood, "matte", material="wood",
                bevel=0.003)]
    for k in range(1, 4):  # 縦の格子
        x = -pw / 2 + k * pw / 4
        parts.append(_p(f"KumikoV{k}", "box", (0.012, 0.016, ph), (x, -0.004, pz0 + ph / 2), wood, "matte",
                        collision=False, material="wood", bevel=0.001))
    for k in range(1, 6):  # 横の格子
        z = pz0 + k * ph / 6
        parts.append(_p(f"KumikoH{k}", "box", (pw, 0.016, 0.012), (0, -0.004, z), wood, "matte", collision=False,
                        material="wood", bevel=0.001))
    for k, x in enumerate((-W / 2 + 0.12, W / 2 - 0.12)):
        parts.append(_p(f"Foot{k}", "box", (0.06, 0.32, foot_h), (x, 0, foot_h / 2), dark, "matte", material="wood",
                        bevel=0.006))
    return Product(slug="tsuitate_screen", name="衝立 幅900×高さ1500（木枠・和紙調）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=0.32), mass_kg=7.0, static=True, material="wood",
                   description="形は和食店・居酒屋の座敷やテーブルの間に置く一般的な衝立（幅 900 mm・高さ 1500 mm・厚さ 30 mm、"
                               "木の枠に組子の格子と和紙調の面、奥行き 320 mm の足 2 本）で、寸法・質量は代表値。"
                               "厚みの中心が y = 0。",
                   tags=["衝立", "ついたて", "間仕切り", "和風", "飲食店", "居酒屋", "内装", "folding screen",
                         "room divider", "japanese screen", "privacy screen"],
                   colors=Colors(label_base=wood), images=[img, wimg], parts=parts)


# ---------------------------------------------------------------- 床


def oki_tatami() -> Product:
    """置き畳（820 角・厚さ 15 mm、縁付き）。フローリングの上に並べて敷く。"""
    W, T = 0.82, 0.015
    img = _img(_tatami(820, 820, 7021, heri_w=25), "paper", 7021, 0.3)
    parts = [_p("Mat", "box", (W, W, T), (0, 0, T / 2), "#C9C08A", "matte", faces={"top": 0}, material="fabric",
                bevel=0.003)]
    return Product(slug="oki_tatami", name="置き畳 820角（縁付き）", shape_class="assembly", category=ENV,
                   dims=Dimensions(T, W, depth=W), mass_kg=2.5, static=True, material="fabric",
                   description="形はフローリングの上に敷く一般的な置き畳（820 mm 角・厚さ 15 mm、い草の畳表に緑の縁）で、"
                               "寸法・質量は代表値。並べて和のコーナーにする。",
                   tags=["畳", "置き畳", "ユニット畳", "和室", "床", "内装", "tatami", "tatami mat", "floor mat"],
                   colors=Colors(label_base="#C9C08A"), images=[img], parts=parts)


def genkan_step() -> Product:
    """住宅の玄関の上がり框（幅 1.69 m・奥行き 0.9 m・段差 180 mm）。フローリングの床と框の木。"""
    W, D, H = 1.69, 0.90, 0.18
    oak, frame = "#C8A57A", "#8C6239"
    c = _wood(1690, 900, oak, "#D4B58C", "#B48E62", 7031, 160, vertical=False)
    for y in range(0, 900, 150):  # フローリングの板の継ぎ目（幅 150 mm）
        c.rect(0, y, 1690, y + 1.2, fill="#9C7A52")
        x = c.rng.uniform(300, 1300)
        c.rect(x, y, x + 1.2, y + 150, fill="#9C7A52")
    floor_img = _img(c, "paper", 7031, 0.3)
    kam = _img(_wood(1690, 180, frame, "#9A6E44", "#6E4A2A", 7032, 40, vertical=False), "paper", 7032, 0.3)
    kd = 0.10  # 框の奥行き
    parts = [_p("Floor", "box", (W, D - kd, H), (0, kd / 2, H / 2), oak, "glossy", faces={"top": 0},
                material="wood", bevel=0.001),
             _p("Kamachi", "box", (W, kd, H), (0, -D / 2 + kd / 2, H / 2), frame, "glossy",
                faces={"front": 1, "top": 1}, material="wood", bevel=0.004)]
    return Product(slug="genkan_step", name="玄関の上がり框 幅1690×奥行900×高さ180", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D), mass_kg=60.0, static=True, material="wood",
                   description="形は住宅の玄関の土間から上がる一般的な上がり框（段差 180 mm、手前に奥行き 100 mm の框の木、"
                               "奥はフローリング）で、寸法・質量は代表値。正面（-Y）が土間の側。玄関の土間に置いて段差にする。",
                   tags=["上がり框", "玄関", "段差", "式台", "床", "住宅", "内装", "entrance step", "genkan",
                         "raised floor step", "step"],
                   colors=Colors(label_base=oak), images=[floor_img, kam], parts=parts)


def koagari_platform() -> Product:
    """飲食店・住宅の小上がり（1.8 m 角・高さ 0.4 m）。畳 2 枚の座敷と木の框。"""
    W, H = 1.8, 0.40
    frame = "#8C6239"
    t1 = _tatami(900, 1800, 7042, heri_w=28, sides="long")
    t2 = _tatami(900, 1800, 7043, heri_w=28, sides="long")
    top = np.concatenate([t1.array(), t2.array()], axis=1)  # 畳 2 枚（長辺を Y に）
    top_img = _img_array(top, 7041)
    side = _img(_wood(1800, 400, frame, "#9A6E44", "#6E4A2A", 7044, 50, vertical=False), "paper", 7044, 0.3)
    kt = 0.05  # 框の幅
    parts = [_p("Base", "box", (W - 2 * kt, W - 2 * kt, H - 0.06), (0, 0, (H - 0.06) / 2), "#6E4A2A", "matte",
                material="wood", bevel=0),
             _p("Tatami", "box", (W - 2 * kt, W - 2 * kt, 0.06), (0, 0, H - 0.03), "#C9C08A", "matte",
                faces={"top": 0}, material="fabric", bevel=0.002)]
    for k, (sx, sy, sw, sd) in enumerate(((0, -1, W, kt), (0, 1, W, kt), (-1, 0, kt, W - 2 * kt),
                                          (1, 0, kt, W - 2 * kt))):
        parts.append(_p(f"Kamachi{k}", "box", (sw, sd, H), (sx * (W / 2 - kt / 2), sy * (W / 2 - kt / 2), H / 2),
                        frame, "glossy", faces={"front": 1, "back": 1, "left": 1, "right": 1}, material="wood",
                        bevel=0.004))
    return Product(slug="koagari_platform", name="小上がり 1800角×高さ400（畳 2 枚）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=W), mass_kg=120.0, static=True, material="wood",
                   description="形は居酒屋・和食店の座敷や住宅のリビングの一角に作る一般的な小上がり（1800 mm 角・高さ 400 mm、"
                               "畳 2 枚に幅 50 mm の木の框）で、寸法・質量は代表値。上に座卓や座布団を置く。",
                   tags=["小上がり", "座敷", "畳", "和室", "居酒屋", "床", "内装", "raised tatami platform",
                         "tatami platform", "zashiki", "tatami"],
                   colors=Colors(label_base="#C9C08A"), images=[top_img, side], parts=parts)


def _img_array(a: np.ndarray, seed: int) -> np.ndarray:
    from .paint import finish, trim_safe

    return trim_safe(finish(a, "paper", seed, 0.3))


def tile_carpet_panel() -> Product:
    """タイルカーペット（500 角 4 枚＝1 m 角、厚さ 7 mm）。毛並みを市松に向きを変えて敷く。"""
    W, T = 1.0, 0.007
    base = "#5B6068"
    c = Canvas(1000, 1000, None, base, 7051)
    for i in range(2):
        for j in range(2):
            x0, y0 = i * 500, j * 500
            col = mix(base, "#000000", 0.08) if (i + j) % 2 else mix(base, WHITE, 0.05)
            c.rect(x0, y0, x0 + 500, y0 + 500, fill=col)
            horiz = (i + j) % 2 == 0
            for k in range(0, 500, 6):  # 毛並みの筋
                tone = mix(col, c.rng.choice(["#000000", WHITE]), c.rng.uniform(0.04, 0.12))
                if horiz:
                    c.line([(x0, y0 + k), (x0 + 500, y0 + k)], tone, 2.0)
                else:
                    c.line([(x0 + k, y0), (x0 + k, y0 + 500)], tone, 2.0)
    for _ in range(6000):  # ループの粒
        x, y = c.rng.uniform(0, 1000), c.rng.uniform(0, 1000)
        c.ellipse(x - 1, y - 1, x + 1, y + 1, fill=c.rng.choice(["#4A4E55", "#6A6F77", "#3F434A"]))
    img = _img(c, "paper", 7051, 0.4)
    parts = [_p("Tiles", "box", (W, W, T), (0, 0, T / 2), base, "matte", faces={"top": 0}, material="fabric",
                bevel=0)]
    return Product(slug="tile_carpet_panel", name="タイルカーペット 500角 4枚（1 m 角）", shape_class="assembly",
                   category=ENV, dims=Dimensions(T, W, depth=W), mass_kg=4.5, static=True, material="fabric",
                   description="形は事務所の床に多いタイルカーペット（500 mm 角・厚さ 7 mm のグレーのループパイル）を "
                               "2 × 2 枚、毛並みの向きを市松に変えて敷いた 1 m 角で、寸法・質量は代表値。",
                   tags=["タイルカーペット", "カーペット", "床", "事務所", "内装", "carpet tile", "tile carpet",
                         "office carpet", "floor"],
                   colors=Colors(label_base=base), images=[img], parts=parts)


def floor_access_hatch() -> Product:
    """床下点検口（600 角）。アルミの額縁に、周りの床と同じ木目のふた。"""
    W, T = 0.60, 0.012
    oak = "#C8A57A"
    c = _wood(560, 560, oak, "#D4B58C", "#B48E62", 7061, 70, vertical=False)
    for y in range(0, 560, 150):
        c.rect(0, y, 560, y + 1.2, fill="#9C7A52")
    c.rect(500, 270, 540, 290, fill="#8A8F95", radius=4)  # 取っ手の溝
    img = _img(c, "paper", 7061, 0.3)
    fw = 0.02
    parts = [_p("Lid", "box", (W - 2 * fw, W - 2 * fw, T), (0, 0, T / 2), oak, "glossy", faces={"top": 0},
                material="wood", bevel=0.001)]
    for k, (sx, sy, sw, sd) in enumerate(((0, -1, W, fw), (0, 1, W, fw), (-1, 0, fw, W - 2 * fw),
                                          (1, 0, fw, W - 2 * fw))):
        parts.append(_p(f"Frame{k}", "box", (sw, sd, T), (sx * (W / 2 - fw / 2), sy * (W / 2 - fw / 2), T / 2), ALU,
                        "metal", material="aluminum", bevel=0.001))
    return Product(slug="floor_access_hatch", name="床下点検口 600角（木目のふた）", shape_class="assembly",
                   category=ENV, dims=Dimensions(T, W, depth=W), mass_kg=4.0, static=True, material="wood",
                   description="形は住宅のキッチンや洗面所の床に付ける一般的な床下点検口（600 mm 角、幅 20 mm のアルミの額縁、"
                               "フローリングと同じ木目のふた・取っ手の溝）で、寸法・質量は代表値。床の上に置く。",
                   tags=["床下点検口", "点検口", "床", "住宅", "内装", "floor access hatch", "floor hatch",
                         "access panel", "inspection hatch"],
                   colors=Colors(label_base=oak), images=[img], parts=parts)


def raised_floor_panel() -> Product:
    """データセンター・事務所の OA フロアのパネル（600 角 4 枚＝1.2 m 角、うち 1 枚は穴あきの給気パネル）。"""
    W, T = 1.2, 0.035
    base = "#B9BCBF"
    c = Canvas(1200, 1200, None, base, 7071)
    for i in range(2):
        for j in range(2):
            x0, y0 = i * 600, j * 600
            c.rect(x0, y0, x0 + 600, y0 + 600, fill=mix(base, ("#C2C5C8", "#B3B6BA", "#BDC0C3", "#B6B9BD")[i * 2 + j], 0.5))
            for _ in range(500):  # 帯電防止の床材の斑
                x, y = c.rng.uniform(x0, x0 + 600), c.rng.uniform(y0, y0 + 600)
                c.ellipse(x - 1.5, y - 1.5, x + 1.5, y + 1.5, fill=c.rng.choice(["#A6A9AD", "#CDD0D3", "#9EA2A6"]))
    yy = 650.0  # 右下（前の右）の 1 枚は穴あき
    while yy < 1150:
        xx = 650.0
        while xx < 1150:
            c.rect(xx, yy, xx + 14, yy + 14, fill="#2B2E31", radius=2)
            xx += 22
        yy += 22
    edge = "#7A7E83"
    c.rect(598, 0, 602, 1200, fill=edge)
    c.rect(0, 598, 1200, 602, fill=edge)
    t = 0.0
    while t < 1200:  # 外周の目地（半分の幅、むらを付ける）
        seg = c.rng.uniform(8, 40)
        col = c.rng.choice([edge, "#8A8E93", "#6E7277"])
        for v in (0, 1198):
            c.rect(t, v, t + seg, v + 2, fill=col)
            c.rect(v, t, v + 2, t + seg, fill=col)
        t += seg
    img = _img(c, "paper", 7071, 0.3)
    parts = [_p("Panels", "box", (W, W, T), (0, 0, T / 2), base, "plastic", faces={"top": 0}, material="steel",
                bevel=0)]
    return Product(slug="raised_floor_panel", name="OA フロアのパネル 600角 4枚（給気パネル 1 枚）",
                   shape_class="assembly", category=ENV, dims=Dimensions(T, W, depth=W), mass_kg=40.0, static=True,
                   material="steel",
                   description="形はデータセンターや事務所の二重床（フリーアクセスフロア）の一般的なパネル（600 mm 角・"
                               "厚さ 35 mm の鋼製、帯電防止のグレーの床材）を 2 × 2 枚敷いた 1.2 m 角で、うち 1 枚（前の右）は"
                               "冷気を出す穴あきの給気パネル。寸法・質量は代表値。床の上に並べて二重床の見た目にする（脚は省略）。",
                   tags=["OAフロア", "フリーアクセスフロア", "二重床", "床", "データセンター", "給気パネル", "内装",
                         "raised floor", "raised floor tile", "access floor", "perforated floor tile", "data center floor"],
                   colors=Colors(label_base=base), images=[img], parts=parts)


# ---------------------------------------------------------------- 壁


def _on_wall(parts: list[Part], depth: float) -> list[Part]:
    """厚みの中心が y = 0 の部品を、背面（y = 0）が壁に付くように前（-Y）へずらす。"""
    for p in parts:
        p.center[1] -= depth / 2
    return parts


def wood_slat_wall_panel() -> Product:
    """木のルーバーの壁パネル（幅 1.2 m・高さ 2.4 m）。黒い下地に縦の木の桟。"""
    W, H = 1.2, 2.4
    back_t, slat_w, slat_d, pitch = 0.012, 0.030, 0.020, 0.050
    wood = "#B88A5A"
    wimg = _img(_wood(30, 2400, wood, "#C79A6A", "#9E7244", 7081, 6), "paper", 7081, 0.3)
    D = back_t + slat_d
    parts = [_p("Back", "box", (W, back_t, H), (0, D / 2 - back_t / 2, H / 2), "#1E1F21", "matte", material="wood",
                bevel=0)]
    n = int(round(W / pitch))
    for k in range(n):
        x = -W / 2 + pitch / 2 + k * pitch
        parts.append(_p(f"Slat{k:02d}", "box", (slat_w, slat_d, H), (x, D / 2 - back_t - slat_d / 2, H / 2), wood,
                        "matte", faces={"front": 0}, collision=k in (0, n - 1), material="wood", bevel=0.002))
    # 桟の当たり判定は両端の 2 本と下地だけ（細い桟 24 本の凸包はいらない）
    _on_wall(parts, D)
    return Product(slug="wood_slat_wall_panel", name="木のルーバー壁パネル 幅1200×高さ2400", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D), mass_kg=25.0, static=True, material="wood",
                   description="形はカフェ・店舗・事務所の受付の壁に貼る一般的な木のルーバーの化粧パネル（幅 1200 mm・"
                               "高さ 2400 mm、黒い下地に幅 30 mm・奥行き 20 mm の木の桟を 50 mm ピッチ）で、寸法・質量は代表値。"
                               "背面を壁に付ける。横に並べて壁一面にする。",
                   tags=["壁パネル", "ルーバー", "木の壁", "アクセントウォール", "化粧パネル", "壁", "内装",
                         "wood slat wall", "slat wall panel", "wood wall panel", "accent wall", "acoustic panel"],
                   colors=Colors(label_base=wood), images=[wimg], parts=parts)


def kitchen_tile_backsplash() -> Product:
    """キッチンの壁のタイル（幅 1.8 m・高さ 0.8 m）。白いサブウェイタイル（75 × 150 mm）の馬目地。"""
    W, H, T = 1.8, 0.80, 0.010
    grout, tile = "#C9C6C0", "#F4F3EF"
    c = Canvas(1800, 800, None, grout, 7091)
    tw, th, g = 150.0, 75.0, 3.0
    row = 0
    y = 0.0
    while y < 800:
        x = -tw / 2 if row % 2 else 0.0
        while x < 1800:
            col = mix(tile, c.rng.choice(["#FFFFFF", "#E8E6E0", "#EEF0F0"]), c.rng.uniform(0.1, 0.5))
            c.rect(x + g / 2, y + g / 2, x + tw - g / 2, y + th - g / 2, fill=col, radius=3)
            c.rect(x + 8, y + 6, x + tw - 20, y + 12, fill=mix(col, WHITE, 0.6), radius=3)  # 釉薬の照り
            x += tw
        y += th
        row += 1
    img = _img(c, "paper", 7091, 0.2)
    parts = _on_wall([_p("Tiles", "box", (W, T, H), (0, 0, H / 2), tile, "glossy", faces={"front": 0},
                         material="ceramic", bevel=0)], T)
    return Product(slug="kitchen_tile_backsplash", name="キッチンの壁タイル 幅1800×高さ800（白のサブウェイタイル）",
                   shape_class="assembly", category=ENV, dims=Dimensions(H, W, depth=T), mass_kg=18.0, static=True,
                   material="ceramic",
                   description="形は住宅のキッチンやカフェの厨房のコンロ・シンクの奥の壁に貼る白いサブウェイタイル"
                               "（75 × 150 mm、馬目地、グレーの目地）の 1800 × 800 mm の区画で、寸法・質量は代表値。"
                               "背面を壁に付け、下端をカウンターの天板の高さに合わせる。",
                   tags=["タイル", "壁タイル", "キッチン", "サブウェイタイル", "キッチンパネル", "壁", "内装",
                         "kitchen backsplash", "subway tile", "wall tile", "tile wall", "backsplash"],
                   colors=Colors(label_base=tile), images=[img], parts=parts)


def pegboard_wall_panel() -> Product:
    """有孔ボード（910 × 1820 mm）。壁から 20 mm 浮かせる胴縁付き。"""
    W, H, T, gap = 0.91, 1.82, 0.005, 0.020
    board = "#D8C3A0"
    c = Canvas(910, 1820, None, board, 7101)
    c.gradient(0, 0, 910, 1820, "#DDC9A8", "#CDB792")
    for _ in range(3000):
        x, y = c.rng.uniform(0, 910), c.rng.uniform(0, 1820)
        c.ellipse(x - 1.5, y - 0.6, x + 1.5, y + 0.6, fill=c.rng.choice(["#CBB590", "#E2D0B2"]))
    yy = 25.0
    while yy < 1820:  # 25 mm ピッチの穴（φ5）
        xx = 17.5
        while xx < 910:
            c.ellipse(xx - 2.5, yy - 2.5, xx + 2.5, yy + 2.5, fill="#3A3226")
            xx += 25
        yy += 25
    img = _img(c, "paper", 7101, 0.25)
    D = T + gap
    parts = [_p("Board", "box", (W, T, H), (0, D / 2 - gap - T / 2, H / 2), board, "matte", faces={"front": 0},
                material="wood", bevel=0)]
    for k, z in enumerate((0.03, H / 2, H - 0.03)):  # 胴縁
        parts.append(_p(f"Batten{k}", "box", (W - 0.04, gap, 0.04), (0, D / 2 - gap / 2, z), "#B9A27C", "matte",
                        material="wood", bevel=0.001))
    _on_wall(parts, D)
    return Product(slug="pegboard_wall_panel", name="有孔ボード 910×1820", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D), mass_kg=6.0, static=True, material="wood",
                   description="形は作業場・ガレージ・店のバックヤードや雑貨店の壁に付ける一般的な有孔ボード（910 × 1820 mm・"
                               "厚さ 5 mm、φ5 の穴を 25 mm ピッチ、壁から 20 mm 浮かせる胴縁）で、寸法・質量は代表値。"
                               "背面を壁に付ける。",
                   tags=["有孔ボード", "パンチングボード", "ペグボード", "壁", "作業場", "内装", "pegboard",
                         "perforated board", "pegboard wall", "tool wall"],
                   colors=Colors(label_base=board), images=[img], parts=parts)


# ---------------------------------------------------------------- 天井の設備（上面が天井に付く）


def ceiling_ac_cassette() -> Product:
    """天井埋め込みの 4 方向カセット形エアコンの化粧パネル（950 角）。中央の吸込みグリルと 4 辺の吹出しのフラップ。"""
    W, H = 0.95, 0.045
    white = "#F2F2EF"
    c = Canvas(950, 950, None, white, 7111)
    c.gradient(0, 0, 950, 950, "#F5F5F2", "#EAEAE6")
    c.rect(225, 225, 725, 725, fill="#E4E4E0", outline="#CFCFCA", width=3)
    for k in range(240, 712, 12):  # 吸込みグリルの格子
        c.line([(k, 235), (k, 715)], "#BDBDB8", 3)
    for x0, y0, x1, y1 in ((110, 160, 840, 200), (110, 750, 840, 790), (160, 110, 200, 840), (750, 110, 790, 840)):
        c.rect(x0, y0, x1, y1, fill="#3A3D40", radius=6)  # 吹出し口
    _rough_edges(c, 950, 950, ["#E2E2DE", "#FAFAF8", "#D8D8D4"], 3.0, 800)
    img = _img(c, "plastic", 7111, 0.2)
    pt = 0.030
    parts = [_p("Panel", "box", (W, W, pt), (0, 0, H - pt / 2), white, "plastic", faces={"bottom": 0},
                material="plastic", bevel=0.006),
             _p("Grille", "box", (0.50, 0.50, H - pt), (0, 0, (H - pt) / 2), "#E4E4E0", "plastic",
                faces={"bottom": 0}, collision=False, material="plastic", bevel=0.004)]
    for k, (x, y, sx, sy) in enumerate(((0, -0.30, 0.70, 0.05), (0, 0.30, 0.70, 0.05), (-0.30, 0, 0.05, 0.70),
                                        (0.30, 0, 0.05, 0.70))):
        tilt = (15 * (1 if y < 0 else -1), 0, 0) if sx > sy else (0, 15 * (1 if x > 0 else -1), 0)
        parts.append(_p(f"Flap{k}", "box", (sx, sy, 0.004), (x, y, H - pt - 0.005), white, "plastic", rot=tilt,
                        collision=False, material="plastic", bevel=0.001))
    return Product(slug="ceiling_ac_cassette", name="天井カセット形エアコン 4方向（化粧パネル 950角）",
                   shape_class="assembly", category=ENV, dims=Dimensions(H, W, depth=W), mass_kg=5.0, static=True,
                   mount="ceiling", material="plastic",
                   description="形は店舗・事務所・飲食店の天井に埋め込む一般的な 4 方向カセット形エアコンの化粧パネル"
                               "（950 mm 角、中央に吸込みグリル、4 辺に吹出し口と風向きのフラップ）で、寸法・質量は代表値。"
                               "上面が天井に付く向きで、天井裏の本体は省略。",
                   tags=["エアコン", "空調", "天井カセット", "業務用エアコン", "天井", "設備", "内装", "air conditioner",
                         "ceiling cassette", "cassette air conditioner", "HVAC", "ceiling ac"],
                   colors=Colors(label_base=white), images=[img], parts=parts)


def ceiling_air_diffuser() -> Product:
    """天井の丸形の吹出し口（アネモ形、首径 φ200・外径 φ400）。同心の羽根が段になって下がる。"""
    D, H = 0.40, 0.060
    white = CEIL_WHITE
    parts = [_p("Flange", "torus", (D, D, 0.012), (0, 0, H - 0.006), white, "metal", material="steel")]
    for k, (d, z) in enumerate(((0.34, H - 0.020), (0.27, H - 0.032), (0.20, H - 0.044))):
        parts.append(_p(f"Cone{k}", "revolve", (d, d, 0.016), (0, 0, z), white, "metal", collision=k == 0,
                        profile=[[0.55, 0.0], [1.0, 1.0], [0.92, 1.0], [0.48, 0.0]], material="steel"))
    parts += [_p("Throat", "cylinder", (0.20, 0.20, 0.004), (0, 0, H - 0.002), "#2B2D30", "matte", collision=False,
                 material="steel"),
              _p("Center", "cylinder", (0.12, 0.12, 0.008), (0, 0, 0.004), white, "metal", material="steel")]
    return Product(slug="ceiling_air_diffuser", name="天井の吹出し口 アネモ形 φ400", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, D, depth=D), mass_kg=1.8, static=True, mount="ceiling",
                   material="steel",
                   description="形は事務所・店舗の天井に付く一般的な丸形の空調の吹出し口（アネモ形、首径 200 mm・外径 400 mm、"
                               "白い鋼板の同心の羽根 3 段）で、寸法・質量は代表値。上面が天井に付く向きで、ダクトは省略。",
                   tags=["吹出し口", "アネモ", "ディフューザー", "空調", "天井", "設備", "内装", "air diffuser",
                         "ceiling diffuser", "anemostat", "air vent", "HVAC"],
                   colors=Colors(label_base=white), images=[], parts=parts)


def sprinkler_head() -> Product:
    """天井のスプリンクラーヘッド（フラッシュ形）。座金の下に感熱部とデフレクター。"""
    D, H = 0.075, 0.040
    parts = [_p("Escutcheon", "cylinder", (D, D, 0.004), (0, 0, H - 0.002), CEIL_WHITE, "metal", material="steel"),
             _p("Body", "cylinder", (0.030, 0.030, 0.014), (0, 0, H - 0.011), "#C9A45A", "metal", collision=False,
                material="steel"),
             _p("Bulb", "cylinder", (0.008, 0.008, 0.016), (0, 0, H - 0.026), "#D32F2F", "glass", collision=False,
                material="glass"),
             _p("ArmL", "box", (0.004, 0.004, 0.022), (-0.012, 0, H - 0.026), "#C9A45A", "metal", collision=False,
                material="steel", bevel=0),
             _p("ArmR", "box", (0.004, 0.004, 0.022), (0.012, 0, H - 0.026), "#C9A45A", "metal", collision=False,
                material="steel", bevel=0),
             _p("Deflector", "cylinder", (0.040, 0.040, 0.003), (0, 0, 0.0015), "#C9A45A", "metal", collision=False,
                material="steel")]
    return Product(slug="sprinkler_head", name="スプリンクラーヘッド（天井・フラッシュ形）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, D, depth=D), mass_kg=0.15, static=True, mount="ceiling",
                   material="steel",
                   description="形は店舗・事務所・倉庫の天井に付く一般的なスプリンクラーヘッド（白い座金 φ75、真鍮の本体、"
                               "赤い液体のガラスバルブ、デフレクター、天井からの出 40 mm）で、寸法・質量は代表値。"
                               "上面が天井に付く向き。",
                   tags=["スプリンクラー", "消火設備", "防災", "天井", "設備", "内装", "sprinkler", "sprinkler head",
                         "fire sprinkler", "fire protection"],
                   colors=Colors(label_base=CEIL_WHITE), images=[], parts=parts)


def smoke_detector() -> Product:
    """天井の煙感知器（光電式・φ100）。白い丸形で、側面に煙の入るすき間、表示灯。"""
    D, H = 0.100, 0.045
    white = "#F4F4F2"
    parts = [_p("Base", "cylinder", (D, D, 0.012), (0, 0, H - 0.006), white, "plastic", material="plastic"),
             _p("Chamber", "cylinder", (0.090, 0.090, 0.020), (0, 0, H - 0.022), "#D6D6D2", "plastic",
                collision=False, material="plastic"),
             _p("Cover", "revolve", (0.094, 0.094, 0.013), (0, 0, 0.0065), white, "plastic",
                profile=[[0, 0], [0.75, 0], [1.0, 0.6], [1.0, 1.0], [0, 1.0]], material="plastic"),
             _p("Indicator", "cylinder", (0.006, 0.006, 0.002), (0.030, 0, 0.001), "#C62828", "glossy",
                collision=False, material="plastic")]
    for k in range(12):  # 煙の入るすき間の柱
        a = k * math.pi / 6
        parts.append(_p(f"Rib{k:02d}", "box", (0.006, 0.004, 0.020), (0.044 * math.cos(a), 0.044 * math.sin(a), H - 0.022),
                        white, "plastic", rot=(0, 0, math.degrees(a)), collision=False, material="plastic", bevel=0))
    return Product(slug="smoke_detector", name="煙感知器（天井・光電式 φ100）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, D, depth=D), mass_kg=0.12, static=True, mount="ceiling", material="plastic",
                   description="形は住宅・店舗・事務所の天井に付く一般的な光電式の煙感知器（直径 100 mm・高さ 45 mm の白い丸形、"
                               "側面に煙の入るすき間、赤い表示灯）で、寸法・質量は代表値。上面が天井に付く向き。",
                   tags=["煙感知器", "火災報知器", "感知器", "防災", "天井", "設備", "内装", "smoke detector",
                         "smoke alarm", "fire alarm", "fire detector"],
                   colors=Colors(label_base=white), images=[], parts=parts)


def ceiling_access_hatch() -> Product:
    """天井点検口（450 角）。白いアルミの額縁に、天井と同じ白い石こうボードのふた。"""
    W, H = 0.45, 0.012
    c = Canvas(430, 430, None, CEIL_WHITE, 7121)
    c.gradient(0, 0, 430, 430, "#F5F5F3", "#ECECE8")
    for _ in range(400):
        x, y = c.rng.uniform(0, 430), c.rng.uniform(0, 430)
        c.ellipse(x - 0.8, y - 0.8, x + 0.8, y + 0.8, fill="#E0E0DB")
    c.ellipse(395, 205, 415, 225, fill="#D8D8D3", outline="#BDBDB8", width=1.5)  # 鍵穴
    img = _img(c, "paper", 7121, 0.2)
    fw = 0.012
    parts = [_p("Lid", "box", (W - 2 * fw, W - 2 * fw, 0.009), (0, 0, H - 0.0045), CEIL_WHITE, "matte",
                faces={"bottom": 0}, material="paper", bevel=0)]
    for k, (sx, sy, sw, sd) in enumerate(((0, -1, W, fw), (0, 1, W, fw), (-1, 0, fw, W - 2 * fw),
                                          (1, 0, fw, W - 2 * fw))):
        parts.append(_p(f"Frame{k}", "box", (sw, sd, H), (sx * (W / 2 - fw / 2), sy * (W / 2 - fw / 2), H / 2), WHITE,
                        "metal", material="aluminum", bevel=0.001))
    return Product(slug="ceiling_access_hatch", name="天井点検口 450角", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=W), mass_kg=2.0, static=True, mount="ceiling", material="paper",
                   description="形は住宅・店舗・事務所の天井に付く一般的な点検口（450 mm 角、幅 12 mm の白いアルミの額縁に"
                               "石こうボードのふた、鍵穴）で、寸法・質量は代表値。上面が天井に付く向き。",
                   tags=["天井点検口", "点検口", "天井", "設備", "内装", "ceiling access hatch", "access panel",
                         "ceiling hatch", "inspection hatch"],
                   colors=Colors(label_base=CEIL_WHITE), images=[img], parts=parts)


def emergency_light() -> Product:
    """天井埋め込みの非常用照明（埋込穴 φ100）。普段は消えていて、停電のときだけ点く。"""
    D, H = 0.130, 0.030
    white = CEIL_WHITE
    c = Canvas(40, 40, None, "#2E7D32", 7131)
    c.gradient(0, 0, 40, 40, "#388E3C", "#1B5E20")
    _rough_edges(c, 40, 40, ["#1B5E20", "#43A047"], 1.0, 80)
    c.text(20, 21, "非", 22, WHITE, 900)
    mark = _img(c, "plastic", 7131, 0.2)
    parts = [_p("Flange", "torus", (D, D, 0.008), (0, 0, H - 0.004), white, "plastic", material="plastic"),
             _p("Reflector", "revolve", (0.105, 0.105, 0.020), (0, 0, H - 0.018), "#E9E9E6", "metal",
                profile=[[0, 0], [0.55, 0], [1.0, 1.0], [0, 1.0]], material="aluminum"),
             _p("Lamp", "dome", (0.040, 0.040, 0.012), (0, 0, 0.006), "#FBFBF6", "frosted", rot=(180, 0, 0),
                collision=False, material="plastic"),
             _p("Mark", "cylinder", (0.016, 0.016, 0.002), (0.040, 0, H - 0.009), "#2E7D32", "plastic",
                faces={"bottom": 0}, collision=False, material="plastic")]
    return Product(slug="emergency_light", name="非常用照明（天井埋込 φ100）", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, D, depth=D), mass_kg=0.5, static=True, mount="ceiling", material="aluminum",
                   description="形は店舗・事務所・飲食店の天井に埋め込む一般的な非常用照明（埋込穴 φ100・フランジ φ130、"
                               "反射板と乳白の電球のカバー、緑の表示）で、寸法・質量は代表値。上面が天井に付く向き。"
                               "普段は消えているので光源は付けていない。",
                   tags=["非常用照明", "非常灯", "防災", "照明", "天井", "設備", "内装", "emergency light",
                         "emergency lighting", "ceiling light"],
                   colors=Colors(label_base=white), images=[mark], parts=parts)


PRODUCTS = {f.__name__: f for f in (
    office_partition_panel, glass_partition, glass_partition_door, tsuitate_screen,
    oki_tatami, genkan_step, koagari_platform, tile_carpet_panel, floor_access_hatch, raised_floor_panel,
    wood_slat_wall_panel, kitchen_tile_backsplash, pegboard_wall_panel,
    ceiling_ac_cassette, ceiling_air_diffuser, sprinkler_head, smoke_detector, ceiling_access_hatch, emergency_light,
)}
