"""架空の商品の一般的な形（回転体のプロファイル）と、形を取るための側面のシルエット画像。

プロファイルは (z, r) [m] の列で、胴（底 z=0 → キャップの下端）とキャップ（下端 → 全高）に分ける。
シルエットは白背景に描き、通常の生成（輪郭抽出 → 回転体）でそのまま形になるようにする。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

Profile = list[tuple[float, float]]


@dataclass
class RevolveForm:
    body: Profile  # 底 → キャップの下端
    cap: Profile  # キャップの下端 → 頂部
    label: tuple[float, float] | None  # ラベルの (下端 z, 上端 z) [m]
    liquid_top: float | None = None  # 透明容器の液面 z [m]
    square: float | None = None  # 胴の断面を角の丸い四角にする（超楕円の指数。2 で円。キャップと首は丸のまま）
    lobes: list[float] | None = None  # 炭酸ボトルの花形の底 [脚の数, 高さ m, くぼみの深さ（半径比）]

    @property
    def height(self) -> float:
        return self.cap[-1][0]

    @property
    def cap_z(self) -> float:
        return self.cap[0][0]

    @property
    def diameter(self) -> float:
        return 2 * max(r for _, r in self.body + self.cap)

    def radius_at(self, z: float) -> float:
        pts = self.body + self.cap
        return float(np.interp(z, [p[0] for p in pts], [p[1] for p in pts]))

    def landmarks(self) -> dict:
        H = self.height

        def ratio(z: float | None) -> float | None:
            return None if z is None else round((H - z) / H, 4)

        return {"cap_bottom": ratio(self.cap_z),
                "label_top": ratio(self.label[1]) if self.label else None,
                "label_bottom": ratio(self.label[0]) if self.label else None,
                "liquid_top": ratio(self.liquid_top)}

    def label_circumference(self) -> float:
        """全周ラベルの横の長さ [m]（ラベル帯の中ほどの胴の周長）。"""
        z0, z1 = self.label
        return 2 * math.pi * self.radius_at((z0 + z1) / 2) * perimeter_ratio(self.square)


def perimeter_ratio(n: float | None) -> float:
    """超楕円 |x|^n + |y|^n = 1 の周長 ÷ 円周（2π）。"""
    if not n or n == 2:
        return 1.0
    t = np.linspace(0, 2 * math.pi, 4001)
    c, s = np.cos(t), np.sin(t)
    x, y = np.sign(c) * np.abs(c) ** (2 / n), np.sign(s) * np.abs(s) ** (2 / n)
    return float(np.hypot(np.diff(x), np.diff(y)).sum() / (2 * math.pi))


def _arc(z0: float, z1: float, r0: float, r1: float, n: int = 24, ease: str = "cos") -> Profile:
    t = np.linspace(0, 1, n)
    if ease == "cos":
        s = (1 - np.cos(t * math.pi)) / 2
    elif ease == "out":  # 始めが急
        s = np.sin(t * math.pi / 2)
    else:  # in: 終わりが急
        s = 1 - np.cos(t * math.pi / 2)
    return [(float(z0 + (z1 - z0) * ti), float(r0 + (r1 - r0) * si)) for ti, si in zip(t, s)]


def pet_bottle(H: float, D: float, *, shoulder: float = 0.30, neck_r: float = 0.0125, cap_h: float = 0.020,
               cap_r: float = 0.0150, label: tuple[float, float], liquid_top: float, ribs: tuple[float, float] | None = None,
               waist: tuple[float, float] | None = None) -> RevolveForm:
    """一般的な PET ボトル。底の丸み → 直胴（任意でくびれ・リブ）→ 肩（cos）→ 首 → キャップ。shoulder は肩の高さの比率。"""
    R = D / 2
    cap_z = H - cap_h
    neck_z = cap_z - 0.016  # 首の長さ（サポートリングを含む）
    sh_z = neck_z - shoulder * H
    body: Profile = [(0.0, R * 0.80)] + _arc(0.0015, 0.008, R * 0.90, R, 10, "out")[1:]
    zs = np.linspace(0.009, sh_z, 120)
    for z in zs:
        r = R
        if waist and waist[0] < z < waist[1]:
            r -= 0.0025 * math.sin((z - waist[0]) / (waist[1] - waist[0]) * math.pi)
        if ribs and ribs[0] < z < ribs[1]:
            r -= 0.0009 * (0.5 + 0.5 * math.cos((z - ribs[0]) / 0.008 * 2 * math.pi))
        body.append((float(z), r))
    body += _arc(sh_z, neck_z, R, neck_r, 40, "cos")[1:]
    body += [(neck_z + 0.004, neck_r), (neck_z + 0.0045, neck_r + 0.0035), (neck_z + 0.0065, neck_r + 0.0035),
             (neck_z + 0.007, neck_r), (cap_z, neck_r)]
    cap: Profile = [(cap_z, cap_r), (H - 0.0015, cap_r), (H, cap_r - 0.0012)]
    return RevolveForm(body, cap, label, liquid_top)


def beverage_can(H: float, D: float, *, label_margin: float = 0.006) -> RevolveForm:
    """スチール缶（ショート缶）。底のくぼみの縁 → 直胴 → 上のネック → 巻き締めの縁（キャップ扱い）。"""
    R = D / 2
    rim_h = 0.003
    neck_h = 0.010
    cap_z = H - rim_h
    body: Profile = [(0.0, R * 0.84)] + _arc(0.0005, 0.005, R * 0.88, R, 10, "out")[1:]
    body += [(H - rim_h - neck_h, R)] + _arc(H - rim_h - neck_h, cap_z, R, R * 0.86, 16, "cos")[1:]
    cap: Profile = [(cap_z, R * 0.875), (H - 0.0008, R * 0.875), (H, R * 0.85)]
    return RevolveForm(body, cap, (label_margin, H - rim_h - neck_h - 0.001))


def aluminum_can(H: float, D: float, *, top_d: float, label_margin: float = 0.006) -> RevolveForm:
    """2 ピースのアルミ缶（350ml など）。底のドームの縁 → 直胴 → 上すぼまりのネック → 巻き締めの縁（キャップ扱い）。"""
    R, Rt = D / 2, top_d / 2
    rim_h = 0.003
    neck_h = 0.014
    cap_z = H - rim_h
    body: Profile = [(0.0, R * 0.80)] + _arc(0.0005, 0.008, R * 0.84, R, 12, "out")[1:]
    body += [(cap_z - neck_h, R)] + _arc(cap_z - neck_h, cap_z, R, Rt * 0.96, 20, "cos")[1:]
    cap: Profile = [(cap_z, Rt), (H - 0.0008, Rt), (H, Rt * 0.97)]
    return RevolveForm(body, cap, (label_margin, cap_z - neck_h - 0.001))


def jar(H: float, D: float, *, cap_h: float, cap_d: float, label: tuple[float, float]) -> RevolveForm:
    """広口のボトル容器（ボトルガムなど）。底の丸み → 直胴 → 短い肩 → 胴より少し太いねじ蓋。"""
    R, Rc = D / 2, cap_d / 2
    cap_z = H - cap_h
    body: Profile = [(0.0, R * 0.90)] + _arc(0.0005, 0.005, R * 0.94, R, 8, "out")[1:]
    body += [(cap_z - 0.006, R)] + _arc(cap_z - 0.006, cap_z, R, R * 0.93, 10, "cos")[1:]
    cap: Profile = [(cap_z, Rc), (H - 0.002, Rc)] + _arc(H - 0.002, H, Rc, Rc * 0.94, 6, "out")[1:]
    return RevolveForm(body, cap, label)


def pump_bottle(H: float, D: float, *, body_h: float, label: tuple[float, float]) -> RevolveForm:
    """ポンプ式のボトル（ハンドソープなど）。胴 → 肩 → 首までがボトル、ねじ蓋・軸・押し頭がキャップ扱い。
    吐出口のノズルは回転体で作れないため省略する。"""
    R = D / 2
    neck_r = 0.012
    sh_z = body_h - 0.028
    body: Profile = [(0.0, R * 0.90)] + _arc(0.0005, 0.006, R * 0.95, R, 8, "out")[1:]
    body += [(sh_z, R)] + _arc(sh_z, body_h - 0.006, R, neck_r + 0.002, 24, "cos")[1:] + [(body_h, neck_r)]
    collar_r, stem_r, head_r = 0.0145, 0.0045, 0.016
    cap: Profile = [(body_h, collar_r), (body_h + 0.016, collar_r), (body_h + 0.018, collar_r * 0.85),
                    (body_h + 0.0185, stem_r), (H - 0.020, stem_r), (H - 0.0195, head_r * 0.8),
                    (H - 0.017, head_r)] + _arc(H - 0.006, H, head_r, head_r * 0.75, 8, "out")
    return RevolveForm(body, cap, label)


def paper_cup(H: float, top_d: float, bottom_d: float, *, lid_h: float = 0.0025, lid_overhang: float = 0.0015,
              rim_h: float = 0.004, foot_h: float = 0.0, label_margin: tuple[float, float] = (0.003, 0.002)) -> RevolveForm:
    """紙のカップ（円錐台）。底の脚 → 胴 → 上の巻き縁 → 蓋（フタ材）。"""
    rt, rb = top_d / 2, bottom_d / 2
    cap_z = H - lid_h
    body: Profile = [(0.0, rb)]
    if foot_h:
        body += [(foot_h, rb), (foot_h + 0.0005, rb * 0.985)]
    z_rim = cap_z - rim_h
    for z in np.linspace(foot_h + 0.001, z_rim, 30):
        body.append((float(z), rb + (rt - rb) * (z / z_rim)))
    body += [(z_rim + 0.0005, rt + 0.0012), (cap_z - 0.0005, rt + 0.0012), (cap_z, rt + 0.0004)]
    rl = rt + lid_overhang
    cap: Profile = [(cap_z, rl), (H - 0.0004, rl), (H, rl - 0.0006)]
    label = (foot_h + label_margin[0], z_rim - label_margin[1])
    return RevolveForm(body, cap, label)


def aerosol(H: float, D: float, *, cap_h: float, label: tuple[float, float]) -> RevolveForm:
    """エアゾール缶。底の丸み → 直胴 → 肩のドーム → キャップ（胴と同じ太さで覆う）。"""
    R = D / 2
    cap_z = H - cap_h
    body: Profile = [(0.0, R * 0.9)] + _arc(0.0005, 0.004, R * 0.94, R, 8, "out")[1:]
    body += [(cap_z - 0.010, R)] + _arc(cap_z - 0.010, cap_z, R, R * 0.93, 12, "cos")[1:]
    cap: Profile = [(cap_z, R * 0.985)] + _arc(cap_z + 0.001, H - 0.008, R * 0.985, R * 0.97, 8, "cos")[1:]
    cap += _arc(H - 0.008, H, R * 0.97, R * 0.80, 10, "out")[1:]
    return RevolveForm(body, cap, label)


def stick(H: float, D: float, *, cap_h: float, label: tuple[float, float]) -> RevolveForm:
    """スティック容器（リップクリームなど）。胴とキャップが同じ太さ。"""
    R = D / 2
    cap_z = H - cap_h
    body: Profile = [(0.0, R * 0.92), (0.0008, R)] + [(cap_z - 0.0004, R), (cap_z, R * 0.97)]
    cap: Profile = [(cap_z, R), (H - 0.0012, R), (H - 0.0003, R * 0.93), (H, R * 0.85)]
    return RevolveForm(body, cap, label)


def tin(H: float, D: float, *, lid_h: float) -> RevolveForm:
    """平たい缶（クリーム缶など）。胴に、少し太い蓋がかぶさる。"""
    R = D / 2
    cap_z = H - lid_h
    body: Profile = [(0.0, R * 0.965), (0.0006, R * 0.975), (cap_z, R * 0.975)]
    cap: Profile = [(cap_z, R)] + _arc(H - 0.0018, H, R, R * 0.95, 8, "out")
    return RevolveForm(body, cap, (0.0008, cap_z - 0.0004))


def battery(H: float, D: float, *, nub_h: float = 0.0015, nub_d: float = 0.0055) -> RevolveForm:
    """円筒形の乾電池。胴 → 平らな肩 → +極の突起（細いキャップ扱い）。"""
    R = D / 2
    cap_z = H - nub_h
    body: Profile = [(0.0, R * 0.93), (0.0006, R)] + [(cap_z - 0.0006, R), (cap_z, R * 0.93)]
    cap: Profile = [(cap_z, nub_d / 2), (H - 0.0003, nub_d / 2), (H, nub_d / 2 * 0.9)]
    return RevolveForm(body, cap, (0.0006, cap_z - 0.0003))


def draw_silhouette(form: RevolveForm, body_fill: str | None = "#8C8C8C", cap_fill: str = "#5A5A5A",
                    liquid: str | None = None, px: int = 1800, margin: int = 60) -> np.ndarray:
    """形を取るための側面の絵。body_fill が None なら輪郭線だけ（無色透明の液体として扱われる）。
    liquid を渡すと、輪郭線の内側の液面より下をその色で塗る（色の付いた飲み物）。"""
    H, D = form.height, form.diameter
    s = min(px / H, px / D)
    w, h = int(D * s) + 2 * margin, int(H * s) + 2 * margin
    img = Image.new("RGB", (w, h), "#FFFFFF")
    dr = ImageDraw.Draw(img)
    cx = w / 2

    def poly(pts: Profile) -> list[tuple[float, float]]:
        right = [(cx + r * s, margin + (H - z) * s) for z, r in pts]
        left = [(cx - r * s, margin + (H - z) * s) for z, r in reversed(pts)]
        return right + left

    body = poly(form.body)
    if body_fill is None:
        if liquid and form.liquid_top:
            inner = [(z, r - 0.0006) for z, r in form.body if z < form.liquid_top]
            inner.append((form.liquid_top, form.radius_at(form.liquid_top) - 0.0006))
            dr.polygon(poly(inner), fill=liquid)
        dr.line(body + body[:1], fill="#3C3C3C", width=4)
    else:
        dr.polygon(body, fill=body_fill)
    dr.polygon(poly(form.cap), fill=cap_fill)
    return np.asarray(img)
