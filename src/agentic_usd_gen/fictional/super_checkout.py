"""架空の商品のデザイン: スーパーのレジまわりと売場の設備（レジ台・サッカー台・カート置き場・試食台・計量器・値札・吊り看板）。

products.py・store_more.py と同じく、実在の店名・ブランド名・ロゴは使わず、形と寸法は同じ種類の什器の一般的な値にする。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import Product
from .paint import Canvas, finish, mix, trim_safe
from .products import INK, _box, _cyl
from .store_more import _rod

ENV = "environment"
WHITE = "#FFFFFF"
STEEL, STEEL_DARK = "#C4C7CB", "#9EA2A8"
STAINLESS = "#C9CDD1"
CHROME = "#D4D7DB"
DARK = "#2A2C30"
GREEN = "#2E7D32"
SHOP_PLACES = ["supermarket", "shop"]  # 売場の看板・試食の絵柄が合う場所（Picture バリアント）


def _img(c: Canvas, kind: str, seed: int, strength: float = 0.4) -> np.ndarray:
    return trim_safe(finish(c.array(), kind, seed, strength))


def _p(name, shape, size, center, color, finish_="plastic", rot=None, faces=None, collision=True, material=None,
       **kw) -> Part:
    return Part(name=name, shape=shape, size=list(size), center=list(center), rotation=list(rot or [0, 0, 0]),
                color=color, finish=finish_, faces=faces, collision=collision, material=material, **kw)


def _pos_screen(seed: int, items: list[tuple[str, str]], total: str) -> np.ndarray:
    """店員側の POS の会計画面（架空）。"""
    pos = Canvas(320, 240, 1600 / 320, WHITE, seed)
    pos.gradient(0, 0, 320, 240, WHITE, "#E9EEF3")
    pos.rect(0, 0, 320, 24, fill=GREEN)
    pos.text(10, 12, "登録", 12, WHITE, 900, anchor="lm")
    pos.text(310, 12, "レジ 3  担当 0215", 9, WHITE, 600, anchor="rm")
    y = 32.0
    for name, price in items:
        pos.text(12, y + 8, name, 10, INK, 600, anchor="lm")
        pos.text(200, y + 8, f"{price}円", 10, INK, 700, anchor="rm")
        pos.line([(8, y + 17), (206, y + 17)], "#CCD3DA", 0.6)
        y += 19
    pos.rect(214, 32, 312, 120, fill="#F4F7FA", outline="#CCD3DA", width=0.6, radius=5)
    pos.text(263, 52, f"合計 {len(items)}点", 9, INK, 700)
    pos.text(263, 84, total, 20, "#C0392B", 900)
    pos.text(263, 108, "（税込）", 8, INK, 500)
    for i, (t, col) in enumerate((("現金", "#2F6DB5"), ("クレジット", "#5B7FA6"), ("電子マネー", "#C0392B"),
                                  ("コード決済", "#2E8B57"), ("取消", "#7F8C8D"), ("小計", "#F2994A"))):
        x0 = 10 + (i % 3) * 102
        y0 = 150 + (i // 3) * 44
        pos.rect(x0, y0, x0 + 96, y0 + 38, fill=col, radius=6)
        pos.text(x0 + 48, y0 + 19, t, 11, WHITE, 800)
    return _img(pos, "screen", seed, 0.5)


# ---------------------------------------------------------------- ベルト付きレジ台


def checkout_lane_belt() -> Product:
    """スーパーのチェックアウトレーン（左にベルトコンベア、中央にスキャナー、右に精算済みのかごを置く台、レーン番号の柱）。
    お客さまは正面（-Y）側を左から右へ進み、店員は奥（+Y）側に立つ。
    """
    W, D, top = 2.10, 0.80, 0.86
    body_c, top_c, belt_c = "#E6E2DA", "#D9D6D0", "#26282B"
    fw, fh = W * 1000, 760.0  # お客さま側の前板
    fr = Canvas(fw, fh, None, body_c, 9101)
    fr.gradient(0, 0, fw, fh, "#EEEAE2", "#D8D2C6")
    fr.rect(0, fh - 120, fw, fh, fill=GREEN)
    fr.rect(0, fh - 128, fw, fh - 120, fill="#F2C230")
    fr.text(fw * 0.22, 220, "商品はベルトの上へ", 64, GREEN, 900)
    fr.text(fw * 0.22, 300, "PLEASE PLACE ITEMS ON THE BELT", 26, mix(GREEN, WHITE, 0.2), 800, spacing=3)
    fr.text(fw * 0.62, 220, "各種キャッシュレス決済", 52, INK, 900)
    fr.text(fw * 0.62, 290, "ご利用いただけます", 40, INK, 700)
    fr.text(fw * 0.88, 240, "→", 120, GREEN, 900)
    fr.text(fw / 2, fh - 60, "レジ袋は有料です  マイバッグをご利用ください", 44, WHITE, 800)
    front = _img(fr, "paper", 9101, 0.4)
    pos = _pos_screen(9102, [("キャベツ", "198"), ("豚こま切れ", "398"), ("たまご 10個", "258"), ("牛乳 1000ml", "228"),
                              ("食パン 6枚", "158"), ("バナナ", "178")], "1,418円")
    cd = Canvas(200, 130, 1200 / 200, "#0B0F14", 9103)  # お客さま向けの表示
    cd.gradient(0, 0, 200, 130, "#16202B", "#06090D")
    cd.rect(0, 0, 200, 18, fill=GREEN)
    cd.text(100, 9, "いらっしゃいませ", 8, WHITE, 700)
    cd.text(16, 52, "合計", 13, "#CCCCCC", 700, anchor="lm")
    cd.text(186, 52, "1,418円", 24, "#7CFC9A", 900, anchor="rm")
    cd.text(16, 96, "6点", 12, "#AAAAAA", 600, anchor="lm")
    cust = _img(cd, "screen", 9103, 0.5)
    ln = Canvas(220, 220, 6, "#1B5E20", 9104)  # レーン番号（光る箱）
    ln.gradient(0, 0, 220, 220, "#2E7D32", "#1B5E20")
    ln.rect(10, 10, 210, 210, outline=WHITE, width=4, radius=14)
    ln.text(110, 100, "3", 140, WHITE, 900)
    ln.text(110, 188, "レジ", 30, "#E8F5E9", 900)
    lane = _img(ln, "screen", 9104, 0.4)

    xb0, xb1 = -W / 2 + 0.03, -0.18  # ベルトの範囲
    xb, lb = (xb0 + xb1) / 2, xb1 - xb0
    xs = 0.05  # スキャナー
    xo0 = 0.28  # 精算済みのかごの台
    xo, lo = (xo0 + W / 2) / 2, W / 2 - xo0
    pole_h = 1.95 - top - 0.22
    parts: list[Part] = [
        _box("Plinth", (W - 0.06, D - 0.10, 0.08), (0, 0.03, 0.04), DARK, "matte"),
        _box("Body", (W, D - 0.04, top - 0.11 - 0.08), (0, 0.0, 0.08 + (top - 0.19) / 2), body_c, "plastic",
             {"front": 0}),
        # ベルト（左右に縁）
        _box("BeltBed", (lb, D - 0.04, 0.11), (xb, 0.0, top - 0.055), STEEL_DARK, "metal"),
        _box("Belt", (lb - 0.04, 0.44, 0.012), (xb, -0.05, top + 0.006), belt_c, "matte"),
        _box("BeltRailFront", (lb, 0.03, 0.05), (xb, -0.285, top + 0.015), STEEL, "metal"),
        _box("BeltRailBack", (lb, 0.03, 0.05), (xb, 0.185, top + 0.015), STEEL, "metal"),
        _box("BeltShelfBack", (lb, 0.16, 0.012), (xb, 0.28, top - 0.006), top_c, "glossy"),
        _cyl("BeltRoller", (0.05, 0.05, 0.44), (xb1 - 0.03, -0.05, top - 0.01), STEEL, "metal"),
        _box("Divider", (0.38, 0.04, 0.04), (xb - 0.15, -0.05, top + 0.032), "#E0A100", "plastic"),
        # スキャナー台
        _box("ScanTop", (xo0 - xb1, D - 0.04, 0.11), ((xb1 + xo0) / 2, 0.0, top - 0.055), top_c, "glossy"),
        _box("ScannerGlass", (0.28, 0.28, 0.004), (xs, -0.08, top + 0.002), "#101418", "glass", collision=False),
        _box("ScannerTower", (0.30, 0.09, 0.20), (xs, 0.115, top + 0.10), DARK, "plastic"),
        _box("ScannerWindow", (0.24, 0.004, 0.13), (xs, 0.068, top + 0.10), "#2A0E0E", "glass", collision=False),
        _box("PaymentTerminal", (0.09, 0.17, 0.045), (xs + 0.18, -0.26, top + 0.0225), "#1E1E1E", "plastic"),
        # POS（店員側を向く画面と、お客さま向けの表示）
        _box("PosBase", (0.30, 0.20, 0.10), (xs + 0.02, 0.28, top + 0.05), DARK),
        _cyl("PosPole", (0.045, 0.045, 0.14), (xs + 0.02, 0.30, top + 0.17), DARK, "plastic"),
        _box("PosScreen", (0.32, 0.04, 0.24), (xs + 0.02, 0.31, top + 0.36), "#1A1B1D", "screen", {"back": 1},
             [15, 0, 0]),
        _cyl("CustomerPole", (0.03, 0.03, 0.22), (xb1 + 0.04, 0.20, top + 0.11), DARK, "plastic"),
        _box("CustomerDisplay", (0.20, 0.03, 0.13), (xb1 + 0.04, 0.19, top + 0.285), "#1A1B1D", "screen",
             {"front": 2}, [-10, 0, 0]),
        _box("ReceiptPrinter", (0.14, 0.18, 0.13), (xs + 0.19, 0.27, top + 0.065), "#3A3C40"),
        # 精算済みのかごを置く台（0.10 m 低く、端と奥にガード）
        _box("BasketDeck", (lo, D - 0.04, 0.11 - 0.10), (xo, 0.0, top - 0.10 - 0.005), STEEL, "metal"),
        _box("BasketGuardFront", (lo, 0.02, 0.05), (xo, -(D - 0.04) / 2 + 0.01, top - 0.085), STEEL, "metal"),
        _box("BasketGuardEnd", (0.03, D - 0.04, 0.10), (W / 2 - 0.015, 0.0, top - 0.06), STEEL, "metal"),
        _box("BasketGuardBack", (lo, 0.03, 0.10), (xo, D / 2 - 0.035, top - 0.06), STEEL, "metal"),
        # レーン番号の柱（左奥）
        _cyl("LanePole", (0.05, 0.05, pole_h), (-W / 2 + 0.10, 0.30, top + pole_h / 2), STEEL, "metal"),
        _box("LaneNumber", (0.22, 0.12, 0.22), (-W / 2 + 0.10, 0.30, 1.95 - 0.11), "#1B5E20", "screen",
             {"front": 3, "back": 3}, collision=False),
    ]
    return Product(slug="checkout_lane_belt", name="ベルト付きレジ台（チェックアウトレーン）", shape_class="assembly",
                   category="fixture", dims=Dimensions(1.95, W, depth=D - 0.04), mass_kg=180.0, static=True,
                   material="steel",
                   description="形はスーパーの有人レジの一般的なチェックアウトレーン（全長 2100 mm・奥行き 760 mm・台の高さ 860 mm。"
                               "左に長さ 0.9 m のベルトコンベアと仕切り棒、中央にフラットスキャナーと縦のスキャナー、"
                               "POS と店員側の画面・お客さま向けの表示・レシートプリンター・決済端末、右に精算済みのかごを置く 100 mm 低い台、"
                               "左奥にレーン番号の柱（高さ 1950 mm））で、寸法・質量は代表値。ベルトは動かない。"
                               "お客さまの通る側が正面（-Y）。画面と表示は架空。",
                   tags=["チェックアウトレーン", "レジ台", "ベルトコンベア", "レジ", "POS", "スキャナー", "スーパー",
                         "店舗什器", "checkout lane", "checkout counter", "conveyor belt", "cash register",
                         "supermarket"],
                   colors=Colors(label_base=body_c), images=[front, pos, cust, lane], parts=parts)


# ---------------------------------------------------------------- サッカー台


def sacker_table() -> Product:
    """レジの後ろで買った物を袋に詰める台（両面から使う）。天板の下にかごを置く棚、中央の柱にロールのポリ袋。"""
    W, D, top_z, t = 1.50, 0.75, 0.72, 0.03
    top_c, frame = "#F1EFEA", "#B5B9BE"
    sg = Canvas(900, 160, None, GREEN, 9111)
    sg.gradient(0, 0, 900, 160, "#388E3C", "#1B5E20")
    sg.text(450, 62, "ポリ袋はご自由にお使いください", 54, WHITE, 900, max_w=860)
    sg.text(450, 124, "必要な分だけお取りください", 32, "#E8F5E9", 700)
    sign = _img(sg, "plastic", 9111, 0.3)
    parts: list[Part] = [
        _box("Top", (W, D, t), (0, 0, top_z - t / 2), top_c, "glossy"),
        _box("LowerShelf", (W - 0.08, D - 0.06, 0.02), (0, 0, 0.16), frame, "metal"),
        _box("Stretcher", (W - 0.10, 0.04, 0.04), (0, 0, 0.06), frame, "metal"),
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(_box(f"Leg{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", (0.04, 0.04, top_z - t),
                              (sx * (W / 2 - 0.04), sy * (D / 2 - 0.05), (top_z - t) / 2), frame, "metal"))
    post_h = 1.38  # 中央の柱と横棒（袋のロールと案内板）
    for sx in (-1, 1):
        parts.append(_rod(f"Post{'L' if sx < 0 else 'R'}", (sx * 0.55, 0, top_z), (sx * 0.55, 0, post_h), 0.03,
                          frame, collision=True))
    parts += [_rod("CrossBar", (-0.55, 0, post_h), (0.55, 0, post_h), 0.03, frame, collision=True),
              _box("Sign", (0.90, 0.008, 0.16), (0, 0, post_h + 0.095), GREEN, "plastic", {"front": 0, "back": 0},
                   collision=False)]
    for sy in (-1, 1):  # 柱の間にロールの袋を 2 本（両面から取れる）
        y = sy * 0.07
        nm = "F" if sy < 0 else "B"
        parts += [_rod(f"RollRod{nm}", (-0.55, y, 1.02), (0.55, y, 1.02), 0.012, CHROME),
                  _box(f"RollArm{nm}L", (0.012, 0.07, 0.012), (-0.55, y / 2, 1.02), CHROME, "metal",
                       collision=False),
                  _box(f"RollArm{nm}R", (0.012, 0.07, 0.012), (0.55, y / 2, 1.02), CHROME, "metal",
                       collision=False),
                  _p(f"BagRoll{nm}", "cylinder", (0.10, 0.10, 0.30), (0, y, 1.02), "#EEF3EE", "glossy",
                     rot=[0, 90, 0], collision=False, material="plastic")]
    return Product(slug="sacker_table", name="サッカー台（両面・ロール袋付き）", shape_class="assembly", category="fixture",
                   dims=Dimensions(post_h + 0.175, W, depth=D), mass_kg=38.0, static=True, material="steel",
                   description="形はスーパーのレジの後ろに置く一般的なサッカー台（幅 1500 mm・奥行き 750 mm・天板の高さ 720 mm、"
                               "両面から使う）で、天板の下にかごを置く棚、中央の柱にロールのポリ袋 2 本と案内板（高さ 1555 mm）。"
                               "寸法・質量は代表値。案内板の文は架空。",
                   tags=["サッカー台", "袋詰め台", "ロール袋", "ポリ袋", "スーパー", "店舗什器", "bagging table",
                         "packing table", "supermarket"],
                   colors=Colors(label_base=top_c), images=[sign], parts=parts)


# ---------------------------------------------------------------- カート置き場


def cart_corral() -> Product:
    """ショッピングカートを入れておくパイプの囲い（コの字。-X の端から入れる）。カートは別（shopping_cart）。"""
    L, D, H = 2.40, 0.90, 0.95
    pipe = "#C62828"
    sg = Canvas(600, 200, None, pipe, 9121)
    sg.gradient(0, 0, 600, 200, "#D32F2F", "#9E1B1B")
    sg.text(300, 80, "カート置き場", 72, WHITE, 900)
    sg.text(300, 156, "SHOPPING CARTS", 34, "#FFE0E0", 800, spacing=4)
    sign = _img(sg, "plastic", 9121, 0.3)
    x0, x1, y = -L / 2 + 0.06, L / 2 - 0.06, D / 2 - 0.06  # the 120 mm base plates stay inside L x D
    parts: list[Part] = []
    posts = [x0 + (x1 - x0) * i / 3 for i in range(4)]
    for sy in (-1, 1):
        nm = "F" if sy < 0 else "B"
        for i, x in enumerate(posts):
            parts += [_rod(f"Post{nm}{i}", (x, sy * y, 0.01), (x, sy * y, H - 0.024), 0.048, pipe, collision=True),
                      _cyl(f"BasePlate{nm}{i}", (0.12, 0.12, 0.01), (x, sy * y, 0.005), STEEL_DARK, "metal")]
        for z, k in ((0.45, "Low"), (H - 0.024, "Top")):
            parts.append(_rod(f"Rail{nm}{k}", (x0, sy * y, z), (x1, sy * y, z), 0.048, pipe, collision=True))
    for z, k in ((0.45, "Low"), (H - 0.024, "Top")):  # 奥の端（+X）を閉じる
        parts.append(_rod(f"EndRail{k}", (x1, -y, z), (x1, y, z), 0.048, pipe, collision=True))
    parts += [_rod("SignPost", (0, -y, H), (0, -y, H + 0.03), 0.02, STEEL),
              _box("Sign", (0.60, 0.008, 0.20), (0, -y, H + 0.13), pipe, "plastic", {"front": 0, "back": 0},
                   collision=False)]
    return Product(slug="cart_corral", name="カート置き場（パイプの囲い）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H + 0.23, L, depth=D), mass_kg=45.0, static=True, material="steel",
                   description="形は店の入口や駐車場に置く一般的なショッピングカートの置き場（長さ 2400 mm・幅 900 mm・"
                               "高さ 950 mm の丸パイプのコの字の囲い、-X の端が開いていてカートを 6〜8 台入れる。"
                               "上に表示板）で、寸法・質量は代表値。表示板は架空。カートは別のアセット。",
                   tags=["カート置き場", "カート", "囲い", "パイプ", "スーパー", "店舗什器", "cart corral",
                         "shopping cart corral", "cart return", "supermarket"],
                   colors=Colors(label_base=pipe), images=[sign], parts=parts)


# ---------------------------------------------------------------- 試食台


def sample_table() -> Product:
    """売場に出す試食台（折りたたみの台にクロス、前垂れに案内）。台の上にトレー・つまようじ立て・ペーパーナプキン。

    写真: karaage（CC0。前垂れに合成）
    """
    W, D, H = 0.90, 0.45, 0.72
    cloth = "#F5F0E6"
    c = Canvas(W * 1000, 520, None, cloth, 9131)
    c.gradient(0, 0, W * 1000, 520, "#FBF6EC", "#EADFCB")
    c.rect(0, 0, W * 1000, 70, fill="#C62828")
    c.text(W * 500, 36, "本日の試食", 40, WHITE, 900)
    c.photo("karaage", 120, 100, 780, 350, shape="round", radius=18, crop=(0.1, 0.1, 0.9, 0.8))
    c.text(W * 500, 410, "ご試食どうぞ", 64, "#B71C1C", 900)
    c.text(W * 500, 470, "おひとり様おひとつずつお取りください", 26, "#5D4037", 700)
    skirt = _img(c, "paper", 9131, 0.4)
    tc = Canvas(W * 1000, D * 1000, None, cloth, 9132)  # 天板のクロス（無地の布目）
    tc.gradient(0, 0, W * 1000, D * 1000, "#F7F2E8", "#EFE7D8")
    top_img = _img(tc, "paper", 9132, 0.6)
    parts: list[Part] = [
        _box("Top", (W, D, 0.025), (0, 0, H - 0.0125), cloth, "matte", {"top": 1}),
        _box("Skirt", (W + 0.01, 0.004, 0.52), (0, -D / 2 - 0.004, H - 0.26), cloth, "matte", {"front": 0},
             collision=False, blank="#F5F0E6"),
        _box("SkirtLeft", (0.004, D, 0.30), (-W / 2 - 0.004, 0, H - 0.15), cloth, "matte", collision=False),
        _box("SkirtRight", (0.004, D, 0.30), (W / 2 + 0.004, 0, H - 0.15), cloth, "matte", collision=False),
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(_box(f"Leg{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", (0.025, 0.025, H - 0.025),
                              (sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), (H - 0.025) / 2), STEEL, "metal"))
    parts += [_box("Stretcher", (W - 0.10, 0.02, 0.02), (0, D / 2 - 0.04, 0.12), STEEL, "metal"),
              _box("Tray", (0.36, 0.24, 0.02), (-0.12, -0.02, H + 0.01), "#2B2B2B", "glossy"),
              _box("Plate", (0.30, 0.18, 0.006), (-0.12, -0.02, H + 0.023), WHITE, "glossy", collision=False),
              _cyl("ToothpickCup", (0.04, 0.04, 0.07), (0.20, 0.05, H + 0.035), "#7FB3D5", "plastic"),
              _box("NapkinBox", (0.12, 0.10, 0.06), (0.32, 0.05, H + 0.03), WHITE, "matte")]
    for i in range(6):  # 皿の上の試食（ひと口大）
        parts.append(_p(f"Bite{i}", "bun", (0.035, 0.035, 0.022),
                        (-0.22 + (i % 3) * 0.10, -0.06 + (i // 3) * 0.08, H + 0.037), "#B5651D", "matte",
                        collision=False, material="food"))
    return Product(slug="sample_table", name="試食台（クロス・前垂れ付き）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H + 0.07, W + 0.018, depth=D + 0.012), mass_kg=9.0, static=True,
                   material="steel",
                   description="形はスーパーの売場に出す一般的な折りたたみの試食台（幅 900 mm・奥行き 450 mm・高さ 720 mm）に"
                               "クロスと前垂れを掛け、トレー・皿・つまようじ立て・ペーパーナプキンを載せたもので、寸法・質量は代表値。"
                               "台の上の物は台と一体の固定物。前垂れの案内は架空。",
                   tags=["試食台", "試食", "デモ販売", "テーブル", "スーパー", "店舗什器", "sampling table",
                         "food sample table", "demo table", "supermarket"],
                   photos=["karaage"], colors=Colors(label_base=cloth), images=[skirt, top_img], parts=parts,
                   picture_places=SHOP_PLACES)


# ---------------------------------------------------------------- 計量器


def produce_scale() -> Product:
    """台の上に置く計量器（ステンレスの皿、奥にキー、お客さま側を向いた表示部の柱）。値付け（ラベルプリンター付き）の形。"""
    W, D, f = 0.36, 0.42, 0.008  # f は足の高さ
    body_c = "#E9EAEC"
    dc = Canvas(240, 90, 6, "#0E1A12", 9141)
    dc.gradient(0, 0, 240, 90, "#13241A", "#07100A")
    for i, (lab, v) in enumerate((("重量 kg", "0.425"), ("単価 円/100g", "198"), ("値段 円", "841"))):
        x = 10 + i * 78
        dc.text(x + 34, 16, lab, 8, "#9CCC9C", 700)
        dc.rect(x, 26, x + 70, 74, fill="#0A140D", outline="#2E5E3A", width=0.6, radius=3)
        dc.text(x + 66, 52, v, 20, "#7CFC9A", 900, anchor="rm")
    disp = _img(dc, "screen", 9141, 0.4)
    kc = Canvas(200, 80, 8, "#D8DADD", 9142)  # 奥の操作キー（上面）
    kc.gradient(0, 0, 200, 80, "#E2E4E7", "#CDD0D4")
    for i in range(20):
        x0, y0 = (i % 10) * 20, (i // 10) * 40  # キーを縁まで並べる（縁が単色だと切り抜かれる）
        kc.rect(x0, y0, x0 + 20, y0 + 40, fill="#C5C8CD" if (i + i // 10) % 2 else "#DDDFE2")
        kc.rect(x0 + 1.5, y0 + 1.5, x0 + 18.5, y0 + 38.5, fill=WHITE if i < 10 else "#F2F3F5", outline="#9EA2A8",
                width=0.6, radius=2)
        kc.text(x0 + 10, y0 + 20, "1234567890CT+-×PLU印済"[i], 8, INK, 800)
    keys = _img(kc, "plastic", 9142, 0.3)
    parts: list[Part] = [
        _box("Base", (W, D, 0.10), (0, 0, f + 0.05), body_c, "plastic"),
        _box("PanSupport", (0.10, 0.10, 0.02), (0, -0.05, f + 0.11), DARK, "plastic"),
        _box("Pan", (0.34, 0.27, 0.012), (0, -0.065, f + 0.126), STAINLESS, "metal"),
        _box("Keypad", (0.20, 0.08, 0.012), (-0.06, D / 2 - 0.05, f + 0.106), "#D8DADD", "plastic", {"top": 1}),
        _box("Pole", (0.05, 0.05, 0.30), (0.11, D / 2 - 0.04, f + 0.25), body_c, "plastic"),
        _box("DisplayHead", (0.26, 0.06, 0.10), (0.05, D / 2 - 0.04, f + 0.45), body_c, "plastic"),
        _box("Display", (0.24, 0.004, 0.09), (0.05, D / 2 - 0.072, f + 0.45), "#0E1A12", "screen", {"front": 0},
             collision=False),
        _box("LabelSlot", (0.10, 0.006, 0.02), (W / 2 - 0.07, -D / 2 - 0.002, f + 0.06), DARK, "matte",
             collision=False),
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(_cyl(f"Foot{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", (0.03, 0.03, f),
                              (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), f / 2), DARK, "plastic"))
    H = f + 0.50
    return Product(slug="produce_scale", name="計量器（ラベルプリンター付き）", shape_class="assembly", category="fixture",
                   dims=Dimensions(H, W, depth=D + 0.005), mass_kg=8.0, material="plastic",
                   description="形は青果・量り売りの売場やバックヤードで使う一般的な値付けの計量器（幅 360 mm・奥行き 420 mm、"
                               "ステンレスの皿、奥にキー、表示部の柱（高さ 508 mm）、手前にラベルの出口）で、寸法・質量は代表値。"
                               "台や作業台の上に置く。表示（重量・単価・値段）は架空。",
                   tags=["計量器", "はかり", "スケール", "ラベルプリンター", "量り売り", "スーパー", "店舗什器",
                         "weighing scale", "label scale", "produce scale", "supermarket"],
                   colors=Colors(label_base=body_c), images=[disp, keys], parts=parts)


# ---------------------------------------------------------------- 値札のプライスレール


def shelf_price_label_strip() -> Product:
    """棚板の前面に付ける透明なプライスレール（長さ 900 mm）と、差し込んだ値札 4 枚。背面を棚の前縁に付ける。"""
    L, h, d = 0.90, 0.039, 0.012
    items = [("国産 りんご 1個", "128", "#C62828"), ("温州みかん 袋", "398", "#EF6C00"),
             ("トマト 4個パック", "298", "#C62828"), ("きゅうり 3本", "158", "#2E7D32")]
    hm = h * 1000
    c = Canvas(L * 1000, hm, 12, "#F4F4F2", 9151)
    c.gradient(0, 0, L * 1000, hm, "#F7F7F5", "#E9E9E6")
    tw = 210.0
    for i, (nm, price, col) in enumerate(items):
        x0 = 12 + i * (tw + 13)
        c.rect(x0, 2, x0 + tw, hm - 2, fill=WHITE, outline="#BDBDBD", width=0.3)
        c.rect(x0, 2, x0 + 6, hm - 2, fill=col)
        c.text(x0 + 12, 9, nm, 6.5, INK, 800, anchor="lm", max_w=125)
        c.text(x0 + 12, 18, "本体価格", 4, "#555555", 600, anchor="lm")
        c.text(x0 + 138, 22, price, 15, "#C62828", 900, anchor="rm")
        c.text(x0 + 140, 26, "円", 5, "#C62828", 800, anchor="lm")
        c.text(x0 + 12, 31, f"税込 {round(int(price) * 1.08)}円", 4.5, INK, 700, anchor="lm")
        c.barcode(x0 + 152, 6, 52, 24)
    img = _img(c, "film", 9151, 0.3)
    parts: list[Part] = [
        _box("Rail", (L, d - 0.002, h), (0, 0.001, h / 2), "#E6EEF2", "plastic"),
        _box("Labels", (L - 0.006, 0.001, h - 0.004), (0, -d / 2 + 0.0015, h / 2), WHITE, "matte", {"front": 0},
             collision=False),
        _box("Cover", (L, 0.001, h), (0, -d / 2 + 0.0005, h / 2), "#F2F6F8", "glass", collision=False,
             thin_walled=True),
    ]
    return Product(slug="shelf_price_label_strip", name="棚のプライスレール（値札 4 枚・900mm）", shape_class="assembly",
                   category="fixture", dims=Dimensions(h, L, depth=d), mass_kg=0.12, static=True, material="plastic",
                   description="形はゴンドラ・平台の棚板の前縁に付ける一般的な透明のプライスレール（長さ 900 mm・高さ 39 mm・"
                               "厚さ 12 mm）に、紙の値札（商品名・本体価格・税込価格・ダミーのバーコード）を 4 枚差したもので、"
                               "寸法・質量は代表値。背面を棚の前縁に付け、付けたまま動かないようキネマティック。値札の商品と値段は架空。",
                   tags=["プライスレール", "値札", "棚札", "プライスカード", "棚", "スーパー", "店舗什器",
                         "shelf price label", "price rail", "shelf edge label", "supermarket"],
                   colors=Colors(label_base="#F4F4F2"), images=[img], parts=parts)


# ---------------------------------------------------------------- 売場の吊り看板


def _meat_icon(c: Canvas, cx: float, cy: float, r: float):
    """骨付き肉の絵（使える写真が無いので描く）。骨は茶色の縁取りで背景から浮かせる。"""
    c.ellipse(cx - r, cy - r, cx + r, cy + r, fill="#FCE4EC")
    a, b = (cx + r * 0.05, cy + r * 0.05), (cx + r * 0.62, cy - r * 0.50)
    knobs = [(0.56, -0.70), (0.80, -0.46)]
    for col, grow in (("#6D4C41", 0.05), ("#FFF3D6", 0.0)):  # 縁取り → 骨
        c.line([a, b], col, r * (0.20 + 2 * grow))
        for dx, dy in knobs:
            k = 0.15 + grow
            c.ellipse(cx + r * (dx - k), cy + r * (dy - k), cx + r * (dx + k), cy + r * (dy + k), fill=col)
    c.ellipse(cx - r * 0.72, cy - r * 0.40, cx + r * 0.36, cy + r * 0.66, fill="#B71C1C", outline="#7F0000", width=6)
    c.ellipse(cx - r * 0.54, cy - r * 0.22, cx + r * 0.18, cy + r * 0.48, fill="#E57373")
    c.ellipse(cx - r * 0.34, cy - r * 0.04, cx - r * 0.02, cy + r * 0.26, fill="#FFCDD2")


def _section_sign(slug: str, name: str, ja: str, en: str, accent: str, photo: str | None, seed: int,
                  tags: list[str]) -> Product:
    """天井から 2 本のワイヤーで吊る売場名の看板（両面同じ）。上面が天井に付く。"""
    W, bh, t, drop = 1.20, 0.40, 0.012, 0.80
    H = bh + drop
    cw, ch = W * 1000, bh * 1000
    c = Canvas(cw, ch, None, accent, seed)
    c.gradient(0, 0, cw, ch, mix(accent, WHITE, 0.12), mix(accent, "#000000", 0.18))
    c.rect(0, ch - 30, cw, ch - 20, fill=WHITE)
    r = 140.0
    cx, cy = 190.0, ch / 2 - 12
    c.ellipse(cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8, fill=WHITE)
    if photo:
        c.photo(photo, cx - r, cy - r, cx + r, cy + r, shape="ellipse", crop=(0.15, 0.1, 0.85, 0.9))
    else:
        _meat_icon(c, cx, cy, r)
    c.text(cw / 2 + 170, 160, ja, 180, WHITE, 900, spacing=40)
    c.text(cw / 2 + 170, 300, en, 44, mix(accent, WHITE, 0.8), 800, spacing=6)
    img = _img(c, "plastic", seed, 0.3)
    parts = [_p("Board", "box", (W, t, bh), (0, 0, bh / 2), accent, "plastic", faces={"front": 0, "back": 0},
                bevel=0.004, blank=mix(accent, WHITE, 0.05)),
             _p("Rail", "box", (W, t + 0.008, 0.016), (0, 0, bh + 0.008), "#B9BEC4", "metal", collision=False,
                material="aluminum")]
    for k, x in enumerate((-W / 2 + 0.12, W / 2 - 0.12)):
        parts += [_p(f"Wire{k}", "cylinder", (0.0015, 0.0015, drop - 0.016), (x, 0, bh + 0.016 + (drop - 0.016) / 2),
                     STAINLESS, "metal", collision=False, material="steel"),
                  _p(f"CeilingPlate{k}", "cylinder", (0.040, 0.040, 0.006), (x, 0, H - 0.003), WHITE, "plastic",
                     collision=False)]
    return Product(slug=slug, name=name, shape_class="assembly", category=ENV,
                   dims=Dimensions(H, W, depth=0.040), mass_kg=3.2, static=True, mount="ceiling", material="plastic",
                   description="形はスーパーの売場の上に天井からワイヤーで吊る一般的な売場名の看板（1200 × 400 mm・厚さ 12 mm、"
                               "吊り下げ 800 mm）で、寸法・質量は代表値。上面（ワイヤーの座金）が天井に付く向き。"
                               f"表と裏に同じ「{ja}」を表示する。デザインは架空。",
                   tags=[*tags, "売場看板", "吊り看板", "売り場サイン", "スーパー", "内装", "section sign",
                         "hanging sign", "store signage", "supermarket"],
                   photos=[photo] if photo else [], colors=Colors(label_base=accent), images=[img], parts=parts,
                   picture_places=SHOP_PLACES)


def section_sign_produce() -> Product:
    """写真: strawberry（CC0。看板に合成）"""
    return _section_sign("section_sign_produce", "売場の吊り看板「青果」", "青果", "FRUITS & VEGETABLES", "#2E7D32",
                         "strawberry", 9161, ["青果", "野菜", "果物", "produce"])


def section_sign_meat() -> Product:
    return _section_sign("section_sign_meat", "売場の吊り看板「精肉」", "精肉", "MEAT", "#B71C1C", None, 9162,
                         ["精肉", "肉", "meat"])


def section_sign_fish() -> Product:
    """写真: tuna（CC0。看板に合成）"""
    return _section_sign("section_sign_fish", "売場の吊り看板「鮮魚」", "鮮魚", "FRESH FISH", "#1565C0", "tuna", 9163,
                         ["鮮魚", "魚", "fish", "seafood"])


def section_sign_deli() -> Product:
    """写真: karaage（CC0。看板に合成）"""
    return _section_sign("section_sign_deli", "売場の吊り看板「惣菜」", "惣菜", "DELI", "#E65100", "karaage", 9164,
                         ["惣菜", "デリ", "deli"])


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    checkout_lane_belt, sacker_table, cart_corral, sample_table, produce_scale, shelf_price_label_strip,
    section_sign_produce, section_sign_meat, section_sign_fish, section_sign_deli)}
