"""架空の製品のデザイン: 窓（住宅・店舗のアルミサッシ）とカーテン・ロールスクリーン。

store_env.py と同じく、実在のメーカー名・品番は使わず、形と寸法は同じ種類の製品の一般的な値にする。
カテゴリは environment。窓は壁の開口に入れる建具で、原点は枠の下端の中央、正面（-Y）が室内側。
障子・網戸・すべり出しの戸は関節で動く（引き違いは X 方向のスライド、すべり出しは縦軸の回転で外へ開く）。
"""

from __future__ import annotations

import math

from ..spec import Colors, Dimensions, Joint, Part
from .base import Product
from .paint import Canvas, mix
from .store_env import ALU, ALU_DARK, ENV, GLASS, STAINLESS, _img, _p

FROSTED = "#E6ECEF"  # 型板ガラス（浴室・トイレ）
SCREEN = "#3A4046"  # 網戸の網
FABRIC = "#C9B596"  # カーテン（ベージュ）
LACE = "#F4F2EC"  # レースのカーテン
ROLL = "#E7E1D3"  # ロールスクリーンの生地
WHITE_ALU = "#E8E8E4"  # 白の枠・樹脂の部品

F = 0.040  # 枠の見付け
SASH_D = 0.020  # 障子の見込み
SASH_Y = (-0.013, 0.013)  # 室内側・室外側のレールの位置
SCREEN_Y = 0.030  # 網戸のレール


def _frame(W: float, H: float, D: float, color: str, sill: float = F) -> list[Part]:
    """窓の枠（縦枠 2 本・上枠・下枠）。W・H は外寸、原点は下端の中央。"""
    return [_p("FrameL", "box", (F, D, H), (-W / 2 + F / 2, 0, H / 2), color, "metal", material="aluminum", bevel=0.002),
            _p("FrameR", "box", (F, D, H), (W / 2 - F / 2, 0, H / 2), color, "metal", material="aluminum", bevel=0.002),
            _p("FrameT", "box", (W - 2 * F, D, F), (0, 0, H - F / 2), color, "metal", material="aluminum", bevel=0.002),
            _p("FrameB", "box", (W - 2 * F, D, sill), (0, 0, sill / 2), color, "metal", material="aluminum",
               bevel=0.002)]


def _sash(prefix: str, x: float, y: float, w: float, h: float, z0: float, color: str, glass: str, finish_: str,
          stile: float = 0.032, rail_b: float = 0.040, depth: float = SASH_D) -> list[Part]:
    """框（かまち）の付いたガラスの障子（中心 x、下端 z0）。"""
    gz = z0 + rail_b + (h - stile - rail_b) / 2
    return [_p(f"{prefix}Glass", "box", (w - 2 * stile + 0.01, 0.006, h - stile - rail_b + 0.01), (x, y, gz), glass,
               finish_, material="glass", bevel=0),
            _p(f"{prefix}StileL", "box", (stile, depth, h), (x - w / 2 + stile / 2, y, z0 + h / 2), color, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}StileR", "box", (stile, depth, h), (x + w / 2 - stile / 2, y, z0 + h / 2), color, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}RailT", "box", (w - 2 * stile, depth, stile), (x, y, z0 + h - stile / 2), color, "metal",
               material="aluminum", bevel=0.002),
            _p(f"{prefix}RailB", "box", (w - 2 * stile, depth, rail_b), (x, y, z0 + rail_b / 2), color, "metal",
               material="aluminum", bevel=0.002)]


def _links(parts: list[Part], prefix: str, link: str) -> list[Part]:
    for p in parts:
        p.link = link
    return parts


def _sliding(slug: str, name: str, W: float, H: float, *, frosted: bool = False, screen: bool = True,
             color: str = ALU, mass: float, tags: list[str], description: str) -> Product:
    """引き違い窓（障子 2 枚。室内から見て右の障子が室内側）。網戸は右の外側。"""
    D = 0.070
    glass, gfin = (FROSTED, "frosted") if frosted else (GLASS, "glass")
    ov = 0.030  # 召し合わせの重なり
    inner_w = W - 2 * F
    sw = (inner_w + ov) / 2
    sh = H - 2 * F - 0.004
    z0 = F + 0.002
    xr, xl = inner_w / 2 - sw / 2, -(inner_w / 2 - sw / 2)
    stroke = sw - ov - 0.01
    parts = _frame(W, H, D, color)
    room = _links(_sash("Inner", xr, SASH_Y[0], sw, sh, z0, color, glass, gfin), "Inner", "InnerLink")
    # クレセント錠（室内側の障子の召し合わせの框に付く）
    room += _links([_p("InnerLockBase", "box", (0.020, 0.012, 0.060), (xr - sw / 2 + 0.016, SASH_Y[0] - SASH_D / 2 - 0.006,
                                                                      z0 + sh / 2), STAINLESS, "metal",
                       collision=False, material="steel", bevel=0.003),
                    _p("InnerLockLever", "box", (0.050, 0.008, 0.012), (xr - sw / 2 + 0.006, SASH_Y[0] - SASH_D / 2 - 0.014,
                                                                       z0 + sh / 2 + 0.012), STAINLESS, "metal",
                       collision=False, material="steel", bevel=0.003)], "Inner", "InnerLink")
    outer = _links(_sash("Outer", xl, SASH_Y[1], sw, sh, z0, color, glass, gfin), "Outer", "OuterLink")
    parts += room + outer
    joints = [Joint(link="InnerLink", anchor=[xr, SASH_Y[0], z0 + sh / 2], type="prismatic", axis="X",
                    limits=[-stroke, 0.0]),
              Joint(link="OuterLink", anchor=[xl, SASH_Y[1], z0 + sh / 2], type="prismatic", axis="X",
                    limits=[0.0, stroke])]
    if screen:
        s = 0.020
        net = [_p("ScreenNet", "box", (sw - 2 * s + 0.006, 0.002, sh - 2 * s + 0.006), (xr, SCREEN_Y, z0 + sh / 2),
                  SCREEN, "frosted", material="fiberglass", bevel=0),
               _p("ScreenStileL", "box", (s, 0.008, sh), (xr - sw / 2 + s / 2, SCREEN_Y, z0 + sh / 2), color, "metal",
                  material="aluminum", bevel=0.001),
               _p("ScreenStileR", "box", (s, 0.008, sh), (xr + sw / 2 - s / 2, SCREEN_Y, z0 + sh / 2), color, "metal",
                  material="aluminum", bevel=0.001),
               _p("ScreenRailT", "box", (sw - 2 * s, 0.008, s), (xr, SCREEN_Y, z0 + sh - s / 2), color, "metal",
                  material="aluminum", bevel=0.001),
               _p("ScreenRailB", "box", (sw - 2 * s, 0.008, s), (xr, SCREEN_Y, z0 + s / 2), color, "metal",
                  material="aluminum", bevel=0.001)]
        parts += _links(net, "Screen", "ScreenLink")
        joints.append(Joint(link="ScreenLink", anchor=[xr, SCREEN_Y, z0 + sh / 2], type="prismatic", axis="X",
                            limits=[-stroke, 0.0]))
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D + 0.006), mass_kg=mass, static=True, material="aluminum",
                   description=description + f"障子（InnerLink・OuterLink）は X 方向のスライドの関節で、{stroke * 1000:.0f} mm まで開く。"
                   + ("網戸（ScreenLink）も同じ向きに動く。" if screen else "") + "正面（-Y）が室内側。",
                   tags=["窓", "サッシ", "アルミサッシ", "引き違い窓", "建具", "内装", "window", "sliding window",
                         "aluminum window", *tags],
                   colors=Colors(label_base=color), images=[], parts=parts, joints=joints)


def sliding_window_waist() -> Product:
    """引き違いの腰窓（幅 1690・高さ 1170 mm）。住宅の居室の窓で、床から 0.9 m ほどの高さに付く。"""
    return _sliding("sliding_window_waist", "引き違いの腰窓 1690×1170（網戸付き）", 1.69, 1.17, mass=24.0,
                    tags=["腰窓", "居室の窓", "waist window", "house window", "bedroom window", "living room window"],
                    description="形は住宅の居室に多いアルミの引き違いの腰窓（枠の外寸 1690 × 1170 mm、見込み 70 mm、"
                                "透明のガラス・クレセント錠・網戸）で、寸法・質量は代表値。")


def sliding_window_floor() -> Product:
    """引き違いの掃き出し窓（幅 1690・高さ 2030 mm）。床まであり、ベランダ・庭に出られる。"""
    return _sliding("sliding_window_floor", "引き違いの掃き出し窓 1690×2030（網戸付き）", 1.69, 2.03, mass=42.0,
                    tags=["掃き出し窓", "テラス窓", "ベランダの窓", "floor-length window", "patio window",
                          "balcony window", "sliding glass door"],
                    description="形は住宅のリビングに多いアルミの引き違いの掃き出し窓（枠の外寸 1690 × 2030 mm、"
                                "見込み 70 mm、床まであるのでベランダ・庭に出られる。透明のガラス・クレセント錠・網戸）で、"
                                "寸法・質量は代表値。")


def bathroom_window() -> Product:
    """浴室・トイレの小さな引き違い窓（幅 640・高さ 570 mm、型板ガラス）。"""
    return _sliding("bathroom_window", "浴室・トイレの小窓 640×570（型板ガラス・網戸付き）", 0.64, 0.57, frosted=True,
                    color=WHITE_ALU, mass=8.0,
                    tags=["小窓", "浴室の窓", "トイレの窓", "型板ガラス", "すりガラス", "small window",
                          "bathroom window", "toilet window", "frosted window", "obscure glass"],
                    description="形は浴室・トイレ・洗面所に多い小さなアルミの引き違い窓（枠の外寸 640 × 570 mm、見込み 70 mm、"
                                "白い枠、外が見えない型板ガラス・網戸）で、寸法・質量は代表値。")



def shop_front_window() -> Product:
    """店先の 4 枚引き違いの掃き出しサッシ（幅 3600・高さ 2200 mm）。八百屋・花屋の開け放した店先。"""
    W, H, D = 3.60, 2.20, 0.070
    color = ALU
    ov = 0.030
    inner_w = W - 2 * F
    sw = (inner_w + 2 * ov) / 4
    sh = H - 2 * F - 0.004
    z0 = F + 0.002
    stroke = sw - ov - 0.01
    parts = _frame(W, H, D, color)
    joints = []
    # 左から 1〜4 枚目。両端（1・4）は外のレール、中の 2 枚（2・3）は室内側のレールで、中央で突き合わせる。
    # 端の障子は中央へ、中の障子は端の障子の前へ開く。クレセント錠は中の障子の外側の框。
    offsets = (0.0, sw - ov, 2 * sw - ov, 3 * sw - 2 * ov)
    limits = ([0.0, stroke], [-stroke, 0.0], [0.0, stroke], [-stroke, 0.0])
    for i in range(4):
        x = -inner_w / 2 + sw / 2 + offsets[i]
        y = SASH_Y[1] if i in (0, 3) else SASH_Y[0]
        name = f"Sash{i + 1}"
        sash = _sash(name, x, y, sw, sh, z0, color, GLASS, "glass")
        if i in (1, 2):
            xl = x - sw / 2 + 0.016 if i == 1 else x + sw / 2 - 0.016
            sash.append(_p(f"{name}Lock", "box", (0.020, 0.012, 0.060), (xl, y - SASH_D / 2 - 0.006, z0 + 1.0),
                           STAINLESS, "metal", collision=False, material="steel", bevel=0.003))
        parts += _links(sash, name, f"{name}Link")
        joints.append(Joint(link=f"{name}Link", anchor=[x, y, z0 + sh / 2], type="prismatic", axis="X",
                            limits=limits[i]))
    return Product(slug="shop_front_window", name="店先の 4 枚引き違いサッシ 3600×2200", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=D), mass_kg=95.0, static=True,
                   material="aluminum",
                   description="形は八百屋・花屋・商店の店先に多いアルミの 4 枚引き違いの掃き出しサッシ（枠の外寸 3600 × 2200 mm、"
                               f"見込み 70 mm、透明のガラス、網戸なし）で、寸法・質量は代表値。両端の障子は外のレール、中の 2 枚は"
                               f"室内側のレールで、どれも X 方向のスライドの関節（Sash1Link〜Sash4Link）で {stroke * 1000:.0f} mm まで動く。"
                               "全部を左右に寄せると店先が半分開く。正面（-Y）が室内側。",
                   tags=["窓", "サッシ", "アルミサッシ", "引き違い窓", "4 枚引き違い", "店先", "店舗の窓", "掃き出し窓", "建具",
                         "内装", "window", "sliding window", "aluminum window", "shop front", "storefront",
                         "storefront window", "shop window", "wide window", "sliding glass door"],
                   colors=Colors(label_base=color), images=[], parts=parts, joints=joints)


def fixed_window() -> Product:
    """はめ殺しの FIX 窓（幅 1190・高さ 1170 mm）。開かない採光の窓で、オフィス・店にも合う。"""
    W, H, D = 1.19, 1.17, 0.070
    color = ALU_DARK
    parts = _frame(W, H, D, color)
    parts.append(_p("Glass", "box", (W - 2 * F + 0.01, 0.008, H - 2 * F + 0.01), (0, 0, H / 2), GLASS, "glass",
                    material="glass", bevel=0))
    for k, y in enumerate((-0.008, 0.008)):  # ガラスを押さえるビード（グレージングガスケット）
        parts += [_p(f"Bead{k}T", "box", (W - 2 * F, 0.006, 0.010), (0, y, H - F - 0.005), "#202224", "matte",
                     collision=False, material="rubber", bevel=0),
                  _p(f"Bead{k}B", "box", (W - 2 * F, 0.006, 0.010), (0, y, F + 0.005), "#202224", "matte",
                     collision=False, material="rubber", bevel=0)]
    return Product(slug="fixed_window", name="はめ殺しの FIX 窓 1190×1170", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D), mass_kg=22.0, static=True, material="aluminum",
                   description="形は住宅・オフィス・店の採光用のアルミのはめ殺し窓（枠の外寸 1190 × 1170 mm、見込み 70 mm、"
                               "ダークブロンズの枠・透明の 1 枚ガラス）で、寸法・質量は代表値。開かない。正面（-Y）が室内側。"
                               "横に並べると連窓になる。",
                   tags=["窓", "FIX 窓", "はめ殺し窓", "固定窓", "採光窓", "サッシ", "建具", "内装", "window",
                         "fixed window", "picture window", "office window", "aluminum window"],
                   colors=Colors(label_base=color), images=[], parts=parts)


def casement_window() -> Product:
    """縦すべり出し窓（幅 405・高さ 970 mm）。左の縦軸で外へ開く。キッチン・階段・廊下に多い細長い窓。"""
    W, H, D = 0.405, 0.97, 0.070
    color = ALU
    parts = _frame(W, H, D, color)
    lw, lh = W - 2 * F - 0.004, H - 2 * F - 0.004
    z0, y = F + 0.002, 0.008
    x0 = -W / 2 + F + 0.002  # 吊り元（左）
    leaf = _sash("Leaf", 0, y, lw, lh, z0, color, GLASS, "glass", stile=0.035, rail_b=0.035, depth=0.032)
    # 室内側のオペレーターハンドル（下枠）と、召し合わせ側の締め金具
    parts += [_p("OperatorBase", "box", (0.090, 0.030, 0.030), (0.03, -D / 2 - 0.015, F + 0.015), WHITE_ALU, "plastic",
                 collision=False, bevel=0.004),
              _p("OperatorHandle", "box", (0.016, 0.070, 0.016), (0.06, -D / 2 - 0.050, F + 0.030), WHITE_ALU, "plastic",
                 collision=False, bevel=0.005)]
    leaf.append(_p("LeafLatch", "box", (0.014, 0.012, 0.070), (lw / 2 - 0.018, y - 0.016 - 0.006, z0 + lh / 2), STAINLESS,
                   "metal", collision=False, material="steel", bevel=0.003))
    parts += _links(leaf, "Leaf", "LeafLink")
    return Product(slug="casement_window", name="縦すべり出し窓 405×970", shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=D + 0.085), mass_kg=9.0, static=True, material="aluminum",
                   description="形はキッチン・階段・廊下に多い細長いアルミの縦すべり出し窓（枠の外寸 405 × 970 mm、見込み 70 mm、"
                               "透明のガラス・室内側のオペレーターハンドル）で、寸法・質量は代表値。戸（LeafLink）は左の縦軸の"
                               "回転の関節で外（+Y）へ 70° まで開く（実物はすべり出しのアームで吊り元も動くが、回転で近似）。"
                               "正面（-Y）が室内側。",
                   tags=["窓", "すべり出し窓", "縦すべり出し窓", "サッシ", "建具", "内装", "window", "casement window",
                         "narrow window", "kitchen window", "aluminum window"],
                   colors=Colors(label_base=color), images=[], parts=parts,
                   joints=[Joint(link="LeafLink", anchor=[x0, y + 0.016, z0 + lh / 2], limits=[0.0, 70.0])])


# ---------------------------------------------------------------- カーテン・ロールスクリーン


def _weave(color: str, seed: int):
    """布の織り目（ごく弱い横縞と縦縞）。"""
    c = Canvas(256, 256, None, color, seed)
    for k in range(0, 256, 4):
        c.line([(0, k), (256, k)], mix(color, "#000000", 0.06), 1)
        c.line([(k, 0), (k, 256)], mix(color, "#FFFFFF", 0.06), 1)
    return _img(c, "paper", seed, 0.25)


def _pleats(prefix: str, x0: float, x1: float, y: float, z0: float, h: float, n: int, color: str, finish_: str,
            depth: float, face: int | None) -> list[Part]:
    """ひだ（交互に向きを変えた細い板）で x0〜x1 を埋める。depth はひだの山と谷の差。"""
    pw = (x1 - x0) / n
    ang = math.degrees(math.atan2(depth, pw))
    length = math.hypot(pw, depth) + 0.002
    out = []
    for k in range(n):
        cx = x0 + pw * (k + 0.5)
        out.append(_p(f"{prefix}{k:02d}", "box", (length, 0.004, h), (cx, y, z0 + h / 2), color, finish_,
                      rot=(0, 0, ang if k % 2 else -ang), faces={"front": face, "back": face} if face is not None else None,
                      collision=False, material="fabric", bevel=0))
    return out


def _curtain(slug: str, name: str, W: float, drop: float, *, mass: float, tags: list[str], description: str) -> Product:
    """レール付きのカーテン（厚手 2 枚を両側に寄せ、レースは閉じる）。原点は生地の下端の中央、正面（-Y）が室内側。

    レールは上端。窓の枠の外寸より左右 0.1 m ずつ広く、上枠の 0.05〜0.1 m 上に付ける。
    """
    rail_h = 0.030
    H = drop + rail_h + 0.01
    gather = 0.30  # 寄せた厚手の幅（片側）
    y_drape, y_lace, y_rail = -0.045, 0.020, -0.012
    fab, lace = _weave(FABRIC, 7101), _weave(LACE, 7102)
    parts = [_p("Rail", "box", (W, 0.030, rail_h), (0, y_rail, H - rail_h / 2), WHITE_ALU, "plastic", material="aluminum",
                bevel=0.004),
             _p("RailCapL", "box", (0.020, 0.040, 0.040), (-W / 2 - 0.010, y_rail, H - rail_h / 2), WHITE_ALU, "plastic",
                collision=False, bevel=0.004),
             _p("RailCapR", "box", (0.020, 0.040, 0.040), (W / 2 + 0.010, y_rail, H - rail_h / 2), WHITE_ALU, "plastic",
                collision=False, bevel=0.004)]
    z0 = 0.0
    parts += _pleats("Lace", -W / 2 + 0.02, W / 2 - 0.02, y_lace, z0 + 0.01, drop - 0.01, 28, LACE, "frosted", 0.025, 1)
    parts += _pleats("DrapeL", -W / 2, -W / 2 + gather, y_drape, z0, drop, 8, FABRIC, "matte", 0.060, 0)
    parts += _pleats("DrapeR", W / 2 - gather, W / 2, y_drape, z0, drop, 8, FABRIC, "matte", 0.060, 0)
    parts += [_p(f"Tieback{s}", "box", (gather + 0.02, 0.085, 0.040), (sx * (W / 2 - gather / 2), y_drape, z0 + drop * 0.45),
                 mix(FABRIC, "#000000", 0.15), "matte", collision=False, material="fabric", bevel=0.01)
              for s, sx in (("L", -1), ("R", 1))]
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W + 0.04, depth=0.12), mass_kg=mass, static=True, material="fabric",
                   description=description + "厚手の 2 枚はタッセルで両側に寄せ、レースは閉じた形。生地には当たり判定が無い"
                               "（レールだけ）。正面（-Y）が室内側。",
                   tags=["カーテン", "カーテンレール", "レースのカーテン", "窓まわり", "内装", "curtain", "curtains",
                         "drapes", "sheer curtain", "window treatment", *tags],
                   colors=Colors(label_base=FABRIC), images=[fab, lace], parts=parts, mount="floor")


def curtain_waist_window() -> Product:
    return _curtain("curtain_waist_window", "腰窓用のカーテン（厚手 2 枚・レース、レール付き）幅 1.9 m・丈 1.35 m",
                    1.90, 1.35, mass=4.5, tags=["腰窓", "waist window"],
                    description="形は住宅の腰窓（幅 1690 mm）に掛けるカーテン（レール幅 1.9 m、丈 1350 mm＝窓の下端より 15 cm 長い、"
                                "ベージュの厚手のひだ 2 枚と白いレース）で、寸法・質量は代表値。")


def curtain_floor_window() -> Product:
    return _curtain("curtain_floor_window", "掃き出し窓用のカーテン（厚手 2 枚・レース、レール付き）幅 1.9 m・丈 2.1 m",
                    1.90, 2.08, mass=6.5, tags=["掃き出し窓", "floor-length curtain"],
                    description="形は住宅の掃き出し窓（幅 1690 mm）に掛けるカーテン（レール幅 1.9 m、丈 2080 mm＝床から 1 cm 浮く、"
                                "ベージュの厚手のひだ 2 枚と白いレース）で、寸法・質量は代表値。")


def roll_screen() -> Product:
    """ロールスクリーン（幅 1.75 m、生地を半分ほど下ろした形）。上端を窓の上枠の上に付ける。原点は下端の中央。"""
    W, case_h, drop, bar = 1.75, 0.070, 0.62, 0.025
    H = case_h + drop + bar
    cloth = _weave(ROLL, 7111)
    parts = [_p("Case", "box", (W, 0.075, case_h), (0, 0, H - case_h / 2), WHITE_ALU, "plastic", material="aluminum",
                bevel=0.008),
             _p("Cloth", "box", (W - 0.04, 0.002, drop + 0.01), (0, -0.010, bar + drop / 2), ROLL, "translucent",
                faces={"front": 0, "back": 0}, collision=False, material="fabric", bevel=0),
             _p("BottomBar", "box", (W - 0.04, 0.018, bar), (0, -0.010, bar / 2), WHITE_ALU, "plastic",
                material="aluminum", bevel=0.004),
             _p("Cord", "cylinder", (0.004, 0.004, 0.42), (W / 2 - 0.08, -0.020, H - case_h - 0.21), "#E0DCD2", "matte",
                collision=False, material="fabric", segments=8),
             _p("CordWeight", "cylinder", (0.016, 0.016, 0.040), (W / 2 - 0.08, -0.020, H - case_h - 0.44), WHITE_ALU,
                "plastic", collision=False, segments=16)]
    return Product(slug="roll_screen", name="ロールスクリーン 幅 1.75 m（生地を半分下ろした形）", shape_class="assembly",
                   category=ENV, dims=Dimensions(H, W, depth=0.075), mass_kg=3.2, static=True, material="fabric",
                   description="形は住宅・オフィスの窓に付けるロールスクリーン（幅 1.75 m、上のケースに巻き取る、"
                               "生成りの遮光でない生地を 0.62 m 下ろした形、操作のコード）で、寸法・質量は代表値。"
                               "上端を窓の上枠の上に付ける。生地には当たり判定が無い。正面（-Y）が室内側。",
                   tags=["ロールスクリーン", "ブラインド", "窓まわり", "内装", "roll screen", "roller blind",
                         "roller shade", "window blind", "window treatment"],
                   colors=Colors(label_base=ROLL), images=[cloth], parts=parts)


PRODUCTS = {f.__name__: f for f in (
    sliding_window_waist, sliding_window_floor, bathroom_window, shop_front_window, fixed_window, casement_window,
    curtain_waist_window, curtain_floor_window, roll_screen,
)}
