"""架空の商品のデザイン: 店舗の設備（売り場・イートイン）。

products.py と同じく、実在の商品名・ブランド名・ロゴは使わず、形と寸法は同じ種類の製品の一般的な値にする。
"""

from __future__ import annotations

import math
import random

from ..spec import Colors, Dimensions, Joint, Part
from .base import NOTICE, Product
from .paint import Canvas, finish, trim_safe
from .products import COOL_WHITE, INK, _box, _cyl, _lamp


# ---------------------------------------------------------------- リーチイン冷蔵ケース（ガラス扉 3 枚）

# 看板（「冷たいお飲み物」）が合う店。清涼飲料を売る店だけ（酒屋・八百屋・花屋は Blank にする）
COOLER_PLACES = ["convenience_store", "supermarket", "drugstore", "hundred_yen_shop", "bakery", "cafe", "restaurant"]


def reach_in_cooler_3door() -> Product:
    W, D, H = 1.86, 0.80, 2.0
    frame, dark, lining, shelf_c = "#3A3D42", "#24262A", "#F2F4F6", "#C9CCD0"
    base_h, head_h = 0.12, 0.26
    inner_w = W - 0.08
    door_pitch = inner_w / 3
    open_h = H - base_h - head_h  # 扉の開口の高さ
    zc_open = base_h + open_h / 2
    # 上の看板（光る）
    hw, hh = inner_w * 1000, 200.0
    c = Canvas(hw, hh, 2400 / hw, "#1C5FA8", 2701)
    c.gradient(0, 0, hw, hh, "#2A78C8", "#0E3D73")
    for k in range(12):  # 飾りの点
        x = 60 + k * (hw - 120) / 11
        c.ellipse(x - 5, 22 - 5, x + 5, 22 + 5, fill="#9CC8F0")
        c.ellipse(x - 5, hh - 22 - 5, x + 5, hh - 22 + 5, fill="#9CC8F0")
    c.text(hw / 2, 92, "冷たいお飲み物", 78, "#FFFFFF", 900)
    c.text(hw / 2, 150, "COLD DRINKS  ・  扉は静かにお閉めください", 26, "#D6E8FA", 700)
    header = trim_safe(finish(c.array(), "screen", 2701, 0.4))
    parts: list[Part] = [
        _box("Base", (W, D - 0.06, base_h), (0, 0.03, base_h / 2), dark, "metal"),
        _box("BaseGrille", (inner_w, 0.01, 0.09), (0, -D / 2 + 0.035, base_h / 2), "#141518", "matte",
             collision=False),
        _box("SideLeft", (0.04, D, H), (-W / 2 + 0.02, 0, H / 2), frame, "metal"),
        _box("SideRight", (0.04, D, H), (W / 2 - 0.02, 0, H / 2), frame, "metal"),
        _box("Back", (inner_w, 0.04, H - base_h), (0, D / 2 - 0.02, base_h + (H - base_h) / 2), lining, "plastic"),
        _box("Top", (inner_w, D, head_h), (0, 0, H - head_h / 2), dark, "metal"),
        _box("Header", (inner_w, 0.012, 0.20), (0, -D / 2 - 0.006, H - head_h / 2), "#1C5FA8", "screen", {"front": 0},
             collision=False, blank="#1C5FA8"),
        _box("Floor", (inner_w, D - 0.10, 0.02), (0, 0.01, base_h + 0.01), lining, "plastic"),
    ]
    for k in range(2):  # 扉の間の縦枠
        x = -inner_w / 2 + door_pitch * (k + 1)
        parts.append(_box(f"Mullion{k}", (0.04, 0.06, open_h), (x, -D / 2 + 0.05, zc_open), frame, "metal"))
    # 照明：扉の間の縦枠の裏と左右の内壁の前寄りに縦の LED（実物と同じく、扉の内側から奥へ照らす）
    lights = []
    for k, x in enumerate([-inner_w / 2 + 0.012, *(-inner_w / 2 + door_pitch * (j + 1) for j in range(2)),
                           inner_w / 2 - 0.012]):
        lamp, lux = _lamp(f"LedBar{k}", (0.02, 0.008, open_h - 0.08), (x, -D / 2 + 0.084, zc_open), "#F4F8FF",
                          20000.0, COOL_WHITE, facing="back")
        parts.append(lamp)
        lights.append(lux)
    joints: list[Joint] = []
    for d in range(3):
        x = -inner_w / 2 + door_pitch * (d + 0.5)
        for i in range(5):  # 棚とプライスレール
            z = base_h + 0.30 + i * 0.26
            parts += [_box(f"Shelf{d}_{i}", (door_pitch - 0.03, 0.56, 0.012), (x, 0.06, z), shelf_c, "metal"),
                      _box(f"PriceRail{d}_{i}", (door_pitch - 0.03, 0.008, 0.035), (x, 0.06 - 0.284, z + 0.006),
                           "#FFFFFF", "plastic", collision=False)]
        dw, dh, y = door_pitch - 0.012, open_h - 0.02, -D / 2
        parts += [_box(f"Door{d}", (dw, 0.02, dh), (x, y, zc_open), "#F2F6F8", "glass"),
                  _box(f"Door{d}StileL", (0.035, 0.026, dh), (x - dw / 2 + 0.0175, y, zc_open), dark, "metal",
                       collision=False),
                  _box(f"Door{d}StileR", (0.035, 0.026, dh), (x + dw / 2 - 0.0175, y, zc_open), dark, "metal",
                       collision=False),
                  _box(f"Door{d}RailT", (dw, 0.026, 0.05), (x, y, zc_open + dh / 2 - 0.025), dark, "metal",
                       collision=False),
                  _box(f"Door{d}RailB", (dw, 0.026, 0.07), (x, y, zc_open - dh / 2 + 0.035), dark, "metal",
                       collision=False)]
        hx = x + dw / 2 - 0.06  # 取っ手（扉の右寄り）
        parts += [_box(f"Door{d}Handle", (0.022, 0.026, 0.70), (hx, y - 0.043, zc_open), "#B8BCC0", "metal"),
                  _box(f"Door{d}HandlePostT", (0.016, 0.03, 0.016), (hx, y - 0.028, zc_open + 0.30), "#B8BCC0",
                       "metal", collision=False),
                  _box(f"Door{d}HandlePostB", (0.016, 0.03, 0.016), (hx, y - 0.028, zc_open - 0.30), "#B8BCC0",
                       "metal", collision=False)]
        # 扉は左端の蝶番で手前に開く（上から見て時計回り = Z 軸の負の向き）
        link = f"Door{d}Link"
        for p in parts:
            if p.name.startswith(f"Door{d}"):
                p.link = link
        joints.append(Joint(link=link, anchor=[x - dw / 2, y - 0.01, zc_open], limits=[-100.0, 0.0]))
    return Product(slug="reach_in_cooler_3door", name="リーチイン冷蔵ケース ガラス扉 3枚", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, W, depth=0.856), mass_kg=280.0, static=True, material="steel",
                   description="形はコンビニの壁面に並ぶ一般的なガラス扉の飲料用冷蔵ケース（扉 3 枚・棚 5 段）で、寸法・質量は代表値。"
                               "扉 3 枚（Door0Link〜Door2Link）は左端の蝶番で手前に 100° まで開く。上の看板は架空。"
                               "看板は Picture バリアントで無地にできる（Default＝「冷たいお飲み物」/ Blank＝地の青だけ。"
                               "酒屋・八百屋・花屋など清涼飲料を売らない店で使うとき）。",
                   tags=["リーチイン", "冷蔵ケース", "ガラス扉", "飲料", "店舗什器", "reach-in cooler",
                         "beverage cooler", "glass door"], photos=[], colors=Colors(label_base=frame),
                   images=[header], parts=parts, joints=joints, lights=lights, picture_places=COOLER_PLACES)


# ---------------------------------------------------------------- 分別ゴミ箱（3 口）


def trash_station_3() -> Product:
    W, D, H = 1.05, 0.45, 1.0
    body_c = "#E9EAEC"
    fw, fh = W * 1000, 920.0
    c = Canvas(fw, fh, 1600 / fh, body_c, 2711)
    c.gradient(0, 0, fw, fh, "#F2F3F4", "#DCDEE1")
    secs = [("かん・びん", "#E07B24", "hole"), ("ペットボトル", "#2F6DB5", "hole"), ("もえるゴミ", "#2E8B57", "flap")]
    cw = fw / 3
    for i, (lab, col, kind) in enumerate(secs):
        x0, xc = i * cw, i * cw + cw / 2
        c.rect(x0 + 12, 20, x0 + cw - 12, 130, fill=col, radius=10)
        c.text(xc, 75, lab, 38 if len(lab) <= 5 else 32, "#FFFFFF", 900)
        if kind == "hole":
            c.ellipse(xc - 62, 190, xc + 62, 314, fill=col)
            c.ellipse(xc - 52, 200, xc + 52, 304, fill="#0C0C0E")
        else:
            c.rect(xc - 120, 195, xc + 120, 310, fill=col, radius=14)
            c.rect(xc - 108, 205, xc + 108, 300, fill="#2A2C30", radius=10)
            c.text(xc, 252, "押す", 26, "#E6E6E6", 800)
        if i == 0:  # アイコン
            c.rect(xc - 70, 360, xc - 20, 450, fill="#C9CCD0", radius=6)
            c.ellipse(xc - 70, 352, xc - 20, 368, fill="#E6E8EA")
            c.polygon([(xc + 25, 450), (xc + 25, 395), (xc + 37, 375), (xc + 37, 352), (xc + 53, 352), (xc + 53, 375),
                       (xc + 65, 395), (xc + 65, 450)], fill="#3E8E5E")
        elif i == 1:
            c.polygon([(xc - 28, 455), (xc - 28, 392), (xc - 12, 372), (xc - 12, 352), (xc + 12, 352), (xc + 12, 372),
                       (xc + 28, 392), (xc + 28, 455)], fill="#BFE0F6", outline=col)
            c.rect(xc - 13, 342, xc + 13, 354, fill=col, radius=3)
        else:
            c.polygon([(xc - 55, 450), (xc - 45, 370), (xc + 45, 370), (xc + 55, 450)], fill="#FFFFFF", outline=col)
            c.text(xc, 412, "紙くず", 18, col, 800)
        note = ("中をすすいでください", "キャップ・ラベルは はずしてください", "紙くず・プラ容器など")[i]
        c.text(xc, 495, note, 18, INK, 700, max_w=cw - 30)
        # 下の扉
        c.rect(x0 + 18, 540, x0 + cw - 18, fh - 60, fill="#E3E5E8", radius=6)
        c.rect(x0 + 22, 544, x0 + cw - 22, fh - 64, fill="#EDEEF0", radius=5)
        c.rect(xc - 50, 570, xc + 50, 590, fill="#B5B8BC", radius=8)
        c.text(xc, fh - 100, "回収は店員がおこないます", 15, "#7A7E84", 600)
    for i in (1, 2):
        c.line([(i * cw, 10), (i * cw, fh - 30)], "#C4C7CB", 2)
    c.text(fw / 2, fh - 26, "ゴミの分別にご協力ください  ・  " + NOTICE, 14, "#6A6E74", 600)
    front = trim_safe(finish(c.array(), "metal", 2711, 0.4))
    # 天板（右に飲み残しの流し）
    tw, td = (W + 0.02) * 1000, (D + 0.02) * 1000
    t = Canvas(tw, td, 1600 / tw, "#5A5E64", 2712)
    t.gradient(0, 0, tw, td, "#686C72", "#4A4E54")  # 上下の差が小さいと、横長の画像で縁が単色に見える
    t.rect(tw * 0.70, 70, tw - 50, td - 70, fill="#9EA2A8", radius=20)
    t.rect(tw * 0.70 + 14, 84, tw - 64, td - 84, fill="#2A2C30", radius=14)
    t.pattern(tw * 0.70 + 40, 110, tw - 90, td - 110, "dots", "#6A6E74", 16, 3)
    t.text((tw * 0.70 + tw - 50) / 2, 50, "飲み残しはこちら", 26, "#FFFFFF", 900)
    t.text(tw * 0.35, td / 2 - 20, "ゴミ箱の上に", 30, "#E6E6E6", 800)
    t.text(tw * 0.35, td / 2 + 25, "物を置かないでください", 30, "#E6E6E6", 800)
    top = trim_safe(finish(t.array(), "metal", 2712, 0.4))
    parts = [_box("Plinth", (W - 0.02, D - 0.02, 0.04), (0, 0, 0.02), "#2A2C30", "matte"),
             _box("Body", (W, D, 0.92), (0, 0, 0.04 + 0.46), body_c, "plastic", {"front": 0}),
             _box("TopBoard", (W + 0.02, D + 0.02, 0.04), (0, 0, H - 0.02), "#5A5E64", "metal", {"top": 1})]
    return Product(slug="trash_station_3", name="分別ゴミ箱 3口（飲み残し流し付き）", shape_class="assembly",
                   category="fixture", dims=Dimensions(H, round(W + 0.02, 4), depth=round(D + 0.02, 4)), mass_kg=35.0,
                   static=True, material="steel",
                   description="形はコンビニの店内・店頭に置く一般的な分別ゴミ箱（かん・びん／ペットボトル／もえるゴミの 3 口、天板に飲み残しの流し）で、"
                               "寸法・質量は代表値。投入口と表示は前面の画像。",
                   tags=["ゴミ箱", "分別", "リサイクル", "店舗什器", "trash can", "recycling bin", "waste station"],
                   photos=[], colors=Colors(label_base=body_c), images=[front, top], parts=parts)


# ---------------------------------------------------------------- イートインのカウンター


def eat_in_counter() -> Product:
    W, D, top_z = 1.8, 0.45, 0.9
    wood, panel = "#B8865A", "#3A3D42"
    tw, td = W * 1000, D * 1000
    t = Canvas(tw, td, 2400 / tw, wood, 2721)
    t.gradient(0, 0, tw, td, "#C49464", "#AE7C4E")
    rng = random.Random(2721)
    for k in range(90):  # 木目
        y = rng.uniform(0, td)
        amp, per = rng.uniform(2, 8), rng.uniform(180, 420)
        pts = [(x, y + amp * math.sin(x / per + k)) for x in range(0, int(tw) + 20, 20)]
        t.line(pts, "#9C6C42" if k % 3 else "#D2A273", rng.uniform(0.8, 2.2))
    top = trim_safe(finish(t.array(), "paper", 2721, 0.3))
    sw, sh = 150.0, 200.0
    s = Canvas(sw, sh, 1200 / sh, "#FFFFFF", 2722)
    s.gradient(0, 0, sw, sh, "#FFFFFF", "#EEF4F0")
    s.rect(0, 0, sw, 34, fill="#2E8B57")
    s.text(sw / 2, 17, "イートインご利用の", 11, "#FFFFFF", 900)
    s.text(sw / 2, 46, "お客様へ", 13, "#2E8B57", 900)
    y = 66
    for line in ("お買い上げの商品は", "こちらでお召し上がり", "いただけます", "", "ゴミは分別して", "お捨てください", "",
                 "ご利用は 30 分以内で", "お願いします"):
        if line:
            s.text(sw / 2, y, line, 9, INK, 700)
        y += 13
    s.text(sw / 2, sh - 8, NOTICE, 5, "#8A8E94", 500)
    sign = trim_safe(finish(s.array(), "screen", 2722, 0.3))
    leg_h = top_z - 0.03
    foot = Part("FootRest", "cylinder", [0.03, 0.03, W - 0.08], [0, 0.13, 0.25], [0, 90, 0], color="#B8BCC0",
                finish="metal")
    parts = [_box("Top", (W, D, 0.03), (0, 0, top_z - 0.015), wood, "plastic", {"top": 0}),
             _box("BackPanel", (W - 0.06, 0.03, leg_h), (0, D / 2 - 0.05, leg_h / 2), panel, "plastic"),
             _box("EndLeft", (0.03, D - 0.04, leg_h), (-W / 2 + 0.03, 0.0, leg_h / 2), panel, "plastic"),
             _box("EndRight", (0.03, D - 0.04, leg_h), (W / 2 - 0.03, 0.0, leg_h / 2), panel, "plastic"),
             foot,
             _box("OutletPlate", (0.12, 0.006, 0.07), (-0.6, D / 2 - 0.068, 0.78), "#F2F2F0", "plastic",
                  collision=False),
             _box("SignBase", (0.16, 0.07, 0.01), (0.72, 0.14, top_z + 0.005), "#E8ECEF", "glass", collision=False),
             _box("Sign", (0.15, 0.004, 0.20), (0.72, 0.14, top_z + 0.11), "#FFFFFF", "plastic", {"front": 1},
                  [-8, 0, 0], collision=False)]
    return Product(slug="eat_in_counter", name="イートインのカウンター 1800mm", shape_class="assembly", category="fixture",
                   dims=Dimensions(round(top_z + 0.215, 4), W, depth=D), mass_kg=60.0, static=True, material="wood",
                   description="形はコンビニのイートインに置く一般的な窓向きのカウンター（天板の高さ 900 mm・足かけ付き、3 席ほど）で、"
                               "寸法・質量は代表値。椅子は eat_in_stool。卓上の案内は架空。",
                   tags=["イートイン", "カウンター", "テーブル", "店舗什器", "eat-in counter", "counter table"],
                   photos=[], colors=Colors(label_base=wood), images=[top, sign], parts=parts)


# ---------------------------------------------------------------- イートインの椅子


def eat_in_stool() -> Product:
    dark, chrome, seat_c = "#2A2C30", "#C9CCD0", "#5A3A2A"
    parts: list[Part] = [_cyl("Base", (0.42, 0.42, 0.02), (0, 0, 0.01), dark, "metal"),
                         _cyl("BaseHub", (0.12, 0.12, 0.04), (0, 0, 0.04), dark, "metal"),
                         _cyl("Pole", (0.05, 0.05, 0.58), (0, 0, 0.06 + 0.29), chrome, "metal"),
                         _cyl("SeatPlate", (0.20, 0.20, 0.02), (0, 0, 0.65), dark, "metal"),
                         _cyl("SeatEdge", (0.365, 0.365, 0.01), (0, 0, 0.665), "#3A2418", "plastic",
                              collision=False),
                         _cyl("Seat", (0.36, 0.36, 0.045), (0, 0, 0.6825), seat_c, "plastic"),
                         _cyl("SeatTop", (0.33, 0.33, 0.004), (0, 0, 0.707), "#64432F", "plastic", collision=False)]
    r, t = 0.16, 0.016  # 足かけのリング（管の中心の半径、管の太さ）
    parts.append(Part("FootRing", "torus", [2 * r + t, 2 * r + t, t], [0, 0, 0.30], color=chrome, finish="metal",
                      collision=False))
    parts += [_box("Spoke0", (2 * r, 0.012, 0.012), (0, 0, 0.30), chrome, "metal", collision=False),
              _box("Spoke1", (0.012, 2 * r, 0.012), (0, 0, 0.30), chrome, "metal", collision=False)]
    return Product(slug="eat_in_stool", name="イートインの椅子（丸座面スツール）", shape_class="assembly", category="fixture",
                   dims=Dimensions(0.709, 0.42, depth=0.42), mass_kg=5.0, static=False, material="steel",
                   description="形はイートインのカウンター用の一般的な丸い座面のスツール（座面の高さ約 700 mm・足かけリング付き）で、"
                               "寸法・質量は代表値。動かせる（static ではない）。",
                   tags=["イートイン", "椅子", "スツール", "カウンターチェア", "店舗什器", "stool", "bar stool", "chair"],
                   photos=[], colors=Colors(label_base=seat_c), images=[], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    reach_in_cooler_3door, trash_station_3, eat_in_counter, eat_in_stool)}
