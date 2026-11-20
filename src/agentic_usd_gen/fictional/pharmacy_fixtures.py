"""架空の商品のデザイン: 薬局の什器（調剤室の棚・薬用冷蔵庫・調剤トレー、待合いの自動血圧計・呼び出し番号の表示器・
足踏み式の消毒スタンド）。

drug_fixtures.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
正面は −Y（調剤室の棚は薬剤師側、待合いの什器はお客さま側）。床置きの什器はキネマティック（static）。
商品を並べる面は薄い水平の板にする（agentic-sim-world-gen の fill が棚板として見つけられるように）。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .drug_fixtures import (
    DRUG_PLACES,
    GRAY,
    GREEN,
    NAVY,
    _capsule,
    _cross,
    _shelf,
)
from .paint import Canvas, mix
from .products import COOL_WHITE, INK, _box, _cyl, _face, _lamp
from .super_fixtures import _sign

CREAM, BLUE = "#F1EEE8", "#2F6DB5"
PHARMACY_TAGS = ["薬局", "調剤薬局", "ドラッグストア", "pharmacy", "drugstore"]


# ---------------------------------------------------------------- 調剤棚（引き出しと棚）


def _drawer_front(w_mm: float, h_mm: float, seed: int, code: str, kind: str) -> Canvas:
    """引き出しの前板（クリームの化粧板に、名札差しと取っ手の凹み）。"""
    c = Canvas(w_mm, h_mm, None, CREAM, seed)
    c.gradient(0, 0, w_mm, h_mm, mix(CREAM, "#FFFFFF", 0.3), mix(CREAM, "#000000", 0.05))
    lw, lh = w_mm * 0.62, h_mm * 0.24
    x0, y0 = (w_mm - lw) / 2, h_mm * 0.14
    c.rect(x0 - 2, y0 - 2, x0 + lw + 2, y0 + lh + 2, fill="#B9BEC4", radius=2)
    c.rect(x0, y0, x0 + lw, y0 + lh, fill="#FFFFFF")
    c.text(x0 + lw * 0.22, y0 + lh / 2, code, lh * 0.5, NAVY, 900, max_w=lw * 0.36)
    c.text(x0 + lw * 0.66, y0 + lh / 2, kind, lh * 0.42, INK, 700, max_w=lw * 0.6)
    c.rect(w_mm * 0.3, h_mm * 0.62, w_mm * 0.7, h_mm * 0.78, fill="#8E9399", radius=h_mm * 0.08)
    return c


def dispensing_drawer_cabinet() -> Product:
    W, D, H = 0.90, 0.45, 1.80
    t = 0.018  # 板の厚さ
    base = 0.08
    rows, cols = 3, 3
    top_z = 0.88  # 引き出しの段の上の天板（作業台）の上面
    cell_w = (W - (cols + 1) * t) / cols
    cell_h = (top_z - t - base - (rows + 1) * t) / rows
    up_d = 0.30  # 上の棚の奥行き
    imgs = []
    for r, (code, kind) in enumerate((("A", "錠剤"), ("B", "カプセル"), ("C", "外用薬"))):
        imgs.append(_face(_drawer_front(cell_w * 1000, cell_h * 1000, 13101 + r, code, kind).array(), "paper",
                          13101 + r, 0.8, 6))
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, base), (0, 0.0, base / 2), GRAY, "matte"),
        _box("Bottom", (W, D, t), (0, 0, base + t / 2), CREAM, "matte"),
        _box("Back", (W, t, H - base), (0, D / 2 - t / 2, base + (H - base) / 2), CREAM, "matte"),
        _box("Counter", (W, D, t), (0, 0, top_z - t / 2), "#E4E0D8", "plastic"),
        _box("Top", (W, up_d, t), (0, D / 2 - up_d / 2, H - t / 2), CREAM, "matte"),
    ]
    for side, x in (("L", -W / 2 + t / 2), ("R", W / 2 - t / 2)):
        parts += [_box(f"Side{side}", (t, D, top_z - t - base), (x, 0, base + (top_z - t - base) / 2), CREAM, "matte"),
                  _box(f"UpperSide{side}", (t, up_d, H - top_z - t), (x, D / 2 - up_d / 2, (top_z + H - t) / 2), CREAM,
                       "matte")]
    z_cells = base + t
    for r in range(1, rows):  # 段の間の棚板
        z = z_cells + r * (cell_h + t) + t / 2 - t
        parts.append(_box(f"RowDivider{r}", (W - 2 * t, D - t, t), (0, -t / 2, z + t / 2), CREAM, "matte"))
    for k in range(1, cols):  # 列の間の仕切り
        x = -W / 2 + t + k * (cell_w + t) - t / 2
        parts.append(_box(f"ColDivider{k}", (t, D - t, top_z - t - base - t),
                          (x, -t / 2, base + t + (top_z - t - base - t) / 2), CREAM, "matte"))
    for k, z in enumerate((1.18, 1.48)):  # 上の棚（薬の箱を並べる）
        parts.append(_shelf(f"Shelf{k + 1}", W - 2 * t, up_d - t - 0.005, (0, D / 2 - up_d / 2 - t / 2, z), CREAM))
    # 引き出し 3 段 × 3 列。前板・底・左右・奥の箱で、手前（−Y）へ 300 mm 引き出せる
    joints: list[Joint] = []
    dd = D - t - 0.012  # 引き出しの奥行き
    gap = 0.003
    for r in range(rows):
        zc = z_cells + t / 2 + r * (cell_h + t) + cell_h / 2 - t / 2 + t / 2
        for k in range(cols):
            xc = -W / 2 + t + k * (cell_w + t) + cell_w / 2
            link = f"Drawer{r}{k}Link"
            fw, fh = cell_w - 2 * gap, cell_h - 2 * gap
            iw = fw - 0.012
            yc = -D / 2 + dd / 2
            box_h = fh * 0.7
            zb = zc - fh / 2 + 0.004
            drawer = [
                _box(f"Drawer{r}{k}Front", (fw, t, fh), (xc, -D / 2 + t / 2, zc), CREAM, "matte", {"front": r}),
                _box(f"Drawer{r}{k}Floor", (iw, dd - t, 0.008), (xc, yc + t / 2, zb + 0.004), "#E8E4DC", "matte"),
                _box(f"Drawer{r}{k}SideL", (0.008, dd - t, box_h), (xc - iw / 2 + 0.004, yc + t / 2, zb + box_h / 2),
                     "#E8E4DC", "matte"),
                _box(f"Drawer{r}{k}SideR", (0.008, dd - t, box_h), (xc + iw / 2 - 0.004, yc + t / 2, zb + box_h / 2),
                     "#E8E4DC", "matte"),
                _box(f"Drawer{r}{k}Rear", (iw, 0.008, box_h), (xc, -D / 2 + dd - 0.004, zb + box_h / 2), "#E8E4DC",
                     "matte"),
            ]
            for p in drawer:
                p.link = link
            parts += drawer
            joints.append(Joint(link=link, anchor=[xc, -D / 2, zc], limits=[-0.30, 0.0], type="prismatic", axis="Y"))
    return Product(slug="dispensing_drawer_cabinet", name="調剤棚 引き出し 9 杯・上棚付き 900mm", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D), mass_kg=85.0, static=True, material="wood",
                   joints=joints,
                   description="形は薬局の調剤室の一般的な薬品棚（幅 900 mm・奥行き 450 mm・高さ 1800 mm、下は 3 段 × 3 列の"
                               "引き出しと作業台の天板、上は奥行き 300 mm の棚 2 段）で、寸法・質量は代表値。"
                               "引き出し（Drawer00Link〜Drawer22Link）は手前（−Y）へ 300 mm まで引き出せる。"
                               "前板の名札の文字は架空。",
                   tags=["調剤棚", "薬品棚", "引き出し", "調剤室", "収納棚", *PHARMACY_TAGS, "dispensing cabinet",
                         "medicine drawer cabinet", "dispensary"], photos=[],
                   colors=Colors(label_base=CREAM), images=imgs, parts=parts)


# ---------------------------------------------------------------- 薬用冷蔵庫（ガラス扉）


def medicine_refrigerator() -> Product:
    W, D, H = 0.60, 0.60, 1.75
    t, wall, base = 0.04, 0.04, 0.08  # 扉の厚さ・断熱の壁・台の高さ
    mach = 0.12  # 上の操作部の高さ
    y0, y1 = -D / 2 + t, D / 2
    z_top = H - mach
    zc = base + (z_top - base) / 2
    panel = Canvas(W * 1000, mach * 1000, None, "#F4F5F7", 13111)
    panel.gradient(0, 0, W * 1000, mach * 1000, "#FAFBFC", "#E2E5E9")
    panel.rect(30, 30, 230, 90, fill="#0B1A10", radius=4)
    panel.text(130, 60, "5.0℃", 36, "#5CFF8A", 900)
    panel.text(330, 45, "薬用冷蔵庫", 22, NAVY, 900)
    panel.text(330, 80, "2〜8℃ 管理", 16, INK, 700)
    for k in range(3):
        panel.ellipse(470 + k * 34, 50, 492 + k * 34, 72, fill="#9EA4AA")
    imgs = [_face(panel.array(), "metal", 13111, 0.4, 4)]
    body = "#EEF0F2"
    parts = [
        _box("Base", (W - 0.02, D - 0.02, base), (0, 0, base / 2), GRAY, "matte"),
        _box("SideL", (wall, y1 - y0, z_top - base), (-W / 2 + wall / 2, (y0 + y1) / 2, zc), body, "metal"),
        _box("SideR", (wall, y1 - y0, z_top - base), (W / 2 - wall / 2, (y0 + y1) / 2, zc), body, "metal"),
        _box("Back", (W - 2 * wall, wall, z_top - base), (0, y1 - wall / 2, zc), body, "metal"),
        _box("Floor", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, base + wall / 2), body,
             "metal"),
        _box("Ceiling", (W - 2 * wall, y1 - y0 - wall, wall), (0, (y0 + y1 - wall) / 2, z_top - wall / 2), body,
             "metal"),
        _box("Control", (W, D, mach), (0, 0, z_top + mach / 2), body, "metal"),
        _box("ControlFront", (W, 0.004, mach - 0.004), (0, -D / 2 - 0.002, z_top + mach / 2), body, "metal",
             {"front": 0}, collision=False),
    ]
    sd = y1 - y0 - wall - 0.03
    for k, z in enumerate((0.42, 0.72, 1.02, 1.32)):  # 庫内の網棚
        parts.append(_shelf(f"Shelf{k + 1}", W - 2 * wall - 0.01, sd, (0, (y0 + y1 - wall) / 2 + 0.005, z),
                            "#D6D9DC"))
    lamp, lux = _lamp("InnerLight", (W - 2 * wall - 0.06, 0.03, 0.008), (0, -0.05, z_top - wall - 0.0045), "#F4F8FF",
                      5000.0, COOL_WHITE)
    parts.append(lamp)
    # ガラス扉（右の蝶番で手前に開く）。枠と取っ手は扉と一緒に動く
    dw, dh = W - 0.006, z_top - base - 0.006
    dz, yd = base + 0.003 + dh / 2, -D / 2 + t / 2
    fr = 0.045  # 枠の幅
    door = [
        Part("DoorGlass", "box", [dw - 2 * fr + 0.01, 0.008, dh - 2 * fr + 0.01], [0, yd, dz], color="#EAF2F5",
             finish="glass", thin_walled=True),
        _box("DoorFrameL", (fr, t, dh), (-dw / 2 + fr / 2, yd, dz), body, "metal"),
        _box("DoorFrameR", (fr, t, dh), (dw / 2 - fr / 2, yd, dz), body, "metal"),
        _box("DoorFrameT", (dw - 2 * fr, t, fr), (0, yd, dz + dh / 2 - fr / 2), body, "metal"),
        _box("DoorFrameB", (dw - 2 * fr, t, fr), (0, yd, dz - dh / 2 + fr / 2), body, "metal"),
        _box("DoorGrip", (0.022, 0.03, 0.40), (-dw / 2 + fr / 2, -D / 2 - 0.015, dz), "#9EA4AA", "metal",
             collision=False),
        _cyl("DoorLock", (0.016, 0.016, 0.01), (-dw / 2 + fr / 2, -D / 2 - 0.004, dz + 0.30), "#D4AF37", "metal",
             False),
    ]
    door[-1].rotation = [90.0, 0.0, 0.0]
    for p in door:
        p.link = "DoorLink"
    parts += door
    joints = [Joint(link="DoorLink", anchor=[dw / 2, -D / 2, dz], limits=[0.0, 100.0])]
    return Product(slug="medicine_refrigerator", name="薬用冷蔵庫 ガラス扉 1 枚", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=D + 0.03), mass_kg=75.0, static=True,
                   material="steel", joints=joints, lights=[lux],
                   description="形は薬局の調剤室に置く一般的な薬用の冷蔵庫（幅 600 mm・奥行き 630 mm・高さ 1750 mm、"
                               "本体の奥行き 600 mm に扉の取っ手が前へ 30 mm 出る、ガラス扉 1 枚・庫内の網棚 4 段と照明・上に温度表示の操作部）で、寸法・質量は代表値。"
                               "扉（DoorLink）は右端の蝶番で手前に 100° まで開く。表示の文字は架空。",
                   tags=["薬用冷蔵庫", "冷蔵庫", "保冷庫", "ガラス扉", "調剤室", *PHARMACY_TAGS, "medical refrigerator",
                         "pharmacy refrigerator", "glass door fridge"], photos=[],
                   colors=Colors(label_base=body), images=imgs, parts=parts)


# ---------------------------------------------------------------- 調剤トレー


def dispensing_tray() -> Product:
    W, D, H = 0.30, 0.22, 0.06
    color = "#4C8FD6"
    t, rim = 0.004, 0.004
    lb = Canvas(80, 30, None, "#FFFFFF", 13121)
    lb.rect(0, 0, 80, 8, fill=color)
    lb.text(40, 4, "調剤", 5, "#FFFFFF", 900)
    lb.text(40, 19, "No. 12", 12, INK, 900)
    imgs = [_face(lb.array(), "paper", 13121, 0.3, 2)]
    parts = [Part("Floor", "box", [W - 0.01, D - 0.01, t], [0, 0, t / 2], color=color, finish="plastic",
                  material="plastic", bevel=0.002)]
    for side, (size, c) in (("F", ((W, rim, H), (0, -D / 2 + rim / 2, H / 2))),
                            ("B", ((W, rim, H), (0, D / 2 - rim / 2, H / 2))),
                            ("L", ((rim, D - 2 * rim, H), (-W / 2 + rim / 2, 0, H / 2))),
                            ("R", ((rim, D - 2 * rim, H), (W / 2 - rim / 2, 0, H / 2)))):
        parts.append(Part(f"Wall{side}", "box", list(size), list(c), color=color, finish="plastic", material="plastic",
                          bevel=0.0015))
    parts.append(Part("LabelCard", "box", [0.08, 0.001, 0.03], [0, -D / 2 - 0.0005, H * 0.55], color="#FFFFFF",
                      finish="matte", faces={"front": 0}, collision=False, material="paper", bevel=0))
    return Product(slug="dispensing_tray", name="調剤トレー 300×220 mm（番号札付き）", shape_class="assembly",
                   category="household", dims=Dimensions(H, W, depth=D + 0.001), mass_kg=0.25, static=False,
                   material="plastic",
                   description="形は薬局の調剤室で患者ごとの薬と処方せんを取りそろえる一般的な樹脂のトレー（外寸 300 × 220 mm・"
                               "高さ 60 mm、前に番号札）で、寸法・質量は代表値。中に薬の箱や薬袋を入れられる。番号札の文字は架空。",
                   tags=["調剤トレー", "トレー", "薬かご", "調剤室", *PHARMACY_TAGS, "dispensing tray",
                         "prescription tray"], photos=[],
                   colors=Colors(label_base=color), images=imgs, parts=parts)


# ---------------------------------------------------------------- 自動血圧計


def blood_pressure_kiosk() -> Product:
    W, D = 0.55, 0.62
    cab_h = 0.70  # 台の高さ（腕を載せる高さ）
    head_d, head_h = 0.26, 0.42
    H = cab_h + head_h
    sc = Canvas(300, 190, None, "#0D1B2A", 13131)  # 画面（測定結果）
    sc.gradient(0, 0, 300, 190, "#16304D", "#0A1522")
    sc.rect(0, 0, 300, 30, fill=GREEN)
    sc.text(150, 15, "測定結果", 18, "#FFFFFF", 900)
    for k, (lab, val, unit) in enumerate((("最高血圧", "128", "mmHg"), ("最低血圧", "82", "mmHg"), ("脈拍", "70", "拍/分"))):
        y = 58 + k * 46
        sc.text(60, y, lab, 15, "#BFD3F0", 800)
        sc.text(170, y, val, 34, "#FFFFFF", 900)
        sc.text(250, y + 4, unit, 12, "#BFD3F0", 700)
    screen = _face(sc.array(), "screen", 13131, 0.6, 3)
    fr = Canvas(500, 420, None, "#FFFFFF", 13132)  # 台の前の案内
    fr.gradient(0, 0, 500, 420, "#FFFFFF", "#E9F3EE")
    fr.rect(0, 0, 500, 90, fill=GREEN)
    fr.text(250, 46, "血圧測定", 54, "#FFFFFF", 900)
    _cross(fr, 250, 190, 70)
    fr.text(250, 300, "ご自由にお使いください", 32, GREEN, 900)
    fr.paragraph(40, 335, 460, "1. いすに座り、腕を奥まで入れてください\n2. スタートを押すと測定します", 20, INK, 700)
    front = _face(fr.array(), "plastic", 13132, 0.35, 6)
    body, dark = "#F2F4F5", "#2B2E31"
    yh = D / 2 - head_d / 2
    parts = [
        _box("Plinth", (W - 0.04, D - 0.04, 0.06), (0, 0, 0.03), GRAY, "matte"),
        _box("Cabinet", (W, D, cab_h - 0.06), (0, 0, 0.06 + (cab_h - 0.06) / 2), body, "plastic"),
        _sign("FrontSign", (W - 0.05, 0.004, 0.42), (0, -D / 2 - 0.002, 0.38), GREEN, {"front": 1}, body),
        _box("Armrest", (0.16, D - head_d - 0.02, 0.03), (0, -D / 2 + (D - head_d) / 2, cab_h + 0.015), dark,
             "matte"),
        _box("Head", (W, head_d, head_h), (0, yh, cab_h + head_h / 2), body, "plastic"),
        # 腕を入れる筒（口は黒い円で表す）。筒の軸は Y
        Part("CuffTube", "cylinder", [0.20, 0.20, 0.08], [0, D / 2 - head_d - 0.04, cab_h + 0.03 + 0.10],
             [90.0, 0.0, 0.0], color=body, finish="plastic"),
        Part("CuffOpening", "cylinder", [0.15, 0.15, 0.004], [0, D / 2 - head_d - 0.082, cab_h + 0.13],
             [90.0, 0.0, 0.0], color="#15171A", finish="matte", collision=False),
        Part("Screen", "box", [0.30, 0.006, 0.19], [0, D / 2 - head_d - 0.003, cab_h + head_h - 0.12], color="#0D1B2A",
             finish="screen", faces={"front": 0}, collision=False, bevel=0),
        _cyl("StartButton", (0.05, 0.05, 0.01), (0.20, D / 2 - head_d - 0.005, cab_h + 0.30), "#E53935", "plastic",
             False),
        _box("PrinterSlot", (0.10, 0.004, 0.008), (-0.18, D / 2 - head_d - 0.002, cab_h + 0.30), dark, "matte",
             collision=False),
    ]
    parts[-2].rotation = [90.0, 0.0, 0.0]
    return Product(slug="blood_pressure_kiosk", name="自動血圧計 据え置き型（腕を入れる筒型）", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), W, depth=D + 0.004), mass_kg=60.0, static=True,
                   material="plastic",
                   description="形は薬局・ドラッグストアの待合いに置く一般的な据え置きの自動血圧計（幅 550 mm・奥行き 620 mm・"
                               "高さ 1120 mm、腕を入れる筒・結果の画面・スタートのボタン・前の案内）で、寸法・質量は代表値。"
                               "前にいすを置いて座って使う（いすは含まない）。筒の口は黒い円で表し、中は空いていない。"
                               "画面と案内の文字は架空。",
                   tags=["血圧計", "自動血圧計", "健康チェック", "待合い", *PHARMACY_TAGS, "blood pressure monitor",
                         "blood pressure kiosk", "health kiosk"], photos=[],
                   colors=Colors(label_base=body), images=[screen, front], parts=parts, picture_places=DRUG_PLACES)


# ---------------------------------------------------------------- 呼び出し番号の表示器（壁付け）


def queue_number_display() -> Product:
    W, H, D = 0.80, 0.36, 0.06
    pw, ph = 760.0, 320.0
    c = Canvas(pw, ph, None, "#0B1320", 13141)
    c.gradient(0, 0, pw, ph, "#122036", "#070C16")
    c.rect(0, 0, pw, 60, fill=GREEN)
    _capsule(c, 50, 30, 22)
    c.text(pw / 2 + 20, 30, "お薬のご用意ができました", 34, "#FFFFFF", 900)
    c.text(pw / 2, 88, "お呼び出し番号", 22, "#BFD3F0", 800)
    for k, num in enumerate(("101", "103", "104", "107", "108", "112")):
        col, row = k % 3, k // 3
        x, y = 140 + col * 240, 150 + row * 100
        c.rect(x - 100, y - 38, x + 100, y + 38, outline="#3D5A80", width=2, radius=6)
        c.text(x, y, num, 60, "#FFE45C", 900)
    img = _face(c.array(), "screen", 13141, 0.4, 3)
    parts = [Part("Housing", "box", [W, D, H], [0, D / 2 - D, H / 2], color="#1A1C20", finish="plastic",
                  material="plastic", bevel=0.006),
             Part("Panel", "box", [pw / 1000, 0.004, ph / 1000], [0, -D - 0.001, H / 2], color="#0B1320",
                  finish="screen", faces={"front": 0}, collision=False, bevel=0)]
    for p in parts:  # 背面（y = 0）が壁に付く
        p.center[1] += D / 2
    return Product(slug="queue_number_display", name="呼び出し番号の表示器（壁付け）", shape_class="assembly",
                   category="environment", dims=Dimensions(H, W, depth=D + 0.003), mass_kg=6.0, static=True,
                   material="plastic",
                   description="形は薬局の待合いの壁に付ける一般的な呼び出し番号の表示器（800 × 360 × 60 mm、"
                               "薬の用意ができた受付番号を並べる液晶）で、寸法・質量は代表値。背面を壁に付ける。"
                               "表示の文字と番号は架空。",
                   tags=["番号表示", "呼び出し表示", "順番待ち", "表示器", "待合い", "内装", *PHARMACY_TAGS,
                         "queue number display", "calling display", "waiting room display"], photos=[],
                   colors=Colors(label_base="#1A1C20"), images=[img], parts=parts)


# ---------------------------------------------------------------- 足踏み式の手指消毒スタンド


def hand_sanitizer_stand() -> Product:
    bw, bd = 0.30, 0.30
    hold_z = 0.90  # ボトル受けの台の上面
    bottle_h = 0.20
    H = hold_z + bottle_h + 0.03
    white, frame = "#F4F5F7", "#B9BEC4"
    sg = Canvas(200, 260, None, "#FFFFFF", 13151)
    sg.gradient(0, 0, 200, 260, "#FFFFFF", "#E7F4EC")
    sg.rect(0, 0, 200, 50, fill=GREEN)
    sg.text(100, 25, "手指消毒", 30, "#FFFFFF", 900)
    _cross(sg, 100, 115, 45)
    sg.text(100, 190, "ご協力ください", 22, GREEN, 900)
    sg.text(100, 228, "ペダルを踏むと出ます", 15, INK, 700)
    imgs = [_face(sg.array(), "plastic", 13151, 0.35, 4)]
    parts = [
        _box("BasePlate", (bw, bd, 0.015), (0, 0, 0.0075), frame, "metal"),
        _box("Pole", (0.035, 0.035, hold_z - 0.015), (0, 0.08, 0.015 + (hold_z - 0.015) / 2), frame, "metal"),
        _box("Pedal", (0.10, 0.12, 0.025), (0, -0.09, 0.03), "#2B2E31", "matte"),
        _box("PushRod", (0.008, 0.008, hold_z + 0.10 - 0.05), (0.03, 0.055, 0.05 + (hold_z + 0.05) / 2), frame,
             "metal", collision=False),
        _box("Holder", (0.12, 0.12, 0.012), (0, 0.04, hold_z - 0.006), frame, "metal"),
        _cyl("Bottle", (0.08, 0.08, bottle_h - 0.04), (0, 0.04, hold_z + (bottle_h - 0.04) / 2), white, "plastic"),
        _cyl("PumpHead", (0.035, 0.035, 0.03), (0, 0.04, hold_z + bottle_h - 0.025), white, "plastic"),
        _box("PumpPress", (0.06, 0.03, 0.01), (0.015, 0.055, hold_z + bottle_h - 0.005), frame, "metal",
             collision=False),
        _sign("Sign", (0.20, 0.004, 0.26), (0, 0.08 - 0.0195, 0.55), GREEN, {"front": 0}, white),
    ]
    return Product(slug="hand_sanitizer_stand", name="足踏み式の手指消毒スタンド", shape_class="assembly",
                   category="fixture", dims=Dimensions(round(H, 3), bw, depth=bd), mass_kg=6.5, static=True,
                   material="steel",
                   description="形は薬局・店舗の入口に置く一般的な足踏み式の消毒液スタンド（台 300 × 300 mm・高さ約 1130 mm、"
                               "足元のペダル・押し棒・上の台に消毒液のボトル・支柱に案内）で、寸法・質量は代表値。"
                               "ペダルは動かない。案内の文字は架空。",
                   tags=["消毒スタンド", "手指消毒", "足踏み式", "消毒液", "入口", *PHARMACY_TAGS, "店舗什器",
                         "hand sanitizer stand", "pedal sanitizer dispenser"], photos=[],
                   colors=Colors(label_base=white), images=imgs, parts=parts, picture_places=DRUG_PLACES)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    dispensing_drawer_cabinet, medicine_refrigerator, dispensing_tray, blood_pressure_kiosk, queue_number_display,
    hand_sanitizer_stand)}
