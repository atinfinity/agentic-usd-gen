"""架空の商品のデザイン: ドラッグストアの化粧品（化粧水・乳液・ファンデーション・口紅・マスカラ・コットン）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .drug_medicine import BOX_FACES, pkg_box
from .paint import Canvas, finish, mix
from .products import INK, _face, _pump_bottle

WHITE = "#FFFFFF"


def _cosme_label(form, bg: str, accent: str, seed: int, en: str, title: str, sub: str, size: str, back: str,
                 photo: str | None = None) -> "np.ndarray":
    c = label_canvas(form, bg, seed=seed)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, mix(bg, WHITE, 0.5), bg)
    c.rect(fx - W * 0.12, 6, fx + W * 0.12, 6.4, fill=accent)
    c.text(fx, 12, en, 3.2, accent, 700, spacing=1.0, max_w=W * 0.3)
    c.text(fx, H * 0.38, title, 7.5, INK, 900, max_w=W * 0.32)
    c.text(fx, H * 0.38 + 8, sub, 2.8, accent, 700, max_w=W * 0.32)
    if photo:
        c.photo(photo, fx - 9, H * 0.38 + 13, fx + 9, H * 0.38 + 25, shape="ellipse", feather=1.0)
    c.text(fx, H - 6, size, 3.6, accent, 800)
    c.paragraph(0.25 * W - 15, 6, 0.25 * W + 15, back + "\n" + NOTICE, 1.6, INK, 400)
    c.barcode(0.5 * W - 7, H - 16, 14, 10)
    return finish(c.array(), "film", seed, 0.5)


def lotion_bottle() -> Product:
    form = forms.pet_bottle(0.19, 0.06, shoulder=0.10, neck_r=0.011, cap_h=0.032, cap_r=0.016,
                            label=(0.015, 0.135), liquid_top=0.15)
    label = _cosme_label(form, "#EAF4FA", "#3C84B8", 9601, "MOIST LOTION", "化粧水", "しっとり  高保湿", "200mL",
                         "【使用方法】洗顔後、適量を手のひらかコットンにとり、顔全体になじませてください。\n"
                         "【成分】水、グリセリン、BG、ヒアルロン酸Na、セラミドNP、フェノキシエタノール", "lavender")
    return Product(slug="lotion_bottle", name="化粧水 しっとり 200mL", category="household", mass_kg=0.25,
                   capacity_ml=200, material="PET",
                   description="形は一般的な化粧水のボトル（高さ 190 mm・胴径 60 mm、背の高いねじ蓋）で、寸法・質量は代表値。",
                   tags=["化粧水", "ローション", "スキンケア", "化粧品", "lotion", "toner", "skin care"],
                   photos=["lavender"], colors=Colors(cap="#E8EEF3", liquid="#EEF6FB", label_base="#EAF4FA"),
                   **revolve(form, label=label, body_fill=None, liquid="#EEF6FB"))


def milky_lotion_bottle() -> Product:
    form, pump = _pump_bottle(0.055, 0.135, (0.012, 0.108), "#F2EDE6")
    label = _cosme_label(form, "#FBF3EA", "#B07A4A", 9611, "MILKY LOTION", "乳液", "うるおいを閉じこめる", "150mL",
                         "【使用方法】化粧水のあと、適量を手にとり、顔全体にやさしくなじませてください。\n"
                         "【成分】水、スクワラン、グリセリン、BG、ステアリン酸グリセリル、カルボマー")
    kw = revolve(form, label=label, body_fill="#EFE6DA", depth=0.04)
    return Product(slug="milky_lotion_bottle", name="乳液 うるおい 150mL ポンプ", category="household", mass_kg=0.2,
                   capacity_ml=150, material="plastic", parts=pump,
                   description="形は一般的なポンプ式の乳液ボトル（高さ約 185 mm・幅 55 mm・奥行き 40 mm の楕円断面）で、寸法・質量は代表値。",
                   tags=["乳液", "ミルク", "スキンケア", "化粧品", "milky lotion", "emulsion", "skin care"],
                   colors=Colors(cap="#F2EDE6", label_base="#FBF3EA"), **kw)


def foundation_compact() -> Product:
    form = forms.tin(0.018, 0.072, lid_h=0.010)
    gold, dark = "#C8A667", "#2B2522"
    c = label_canvas(form, dark, seed=9621)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#3A322D", "#1E1916")
    c.rect(0, H / 2 - 0.3, W, H / 2 + 0.3, fill=gold)
    label = finish(c.array(), "plastic", 9621, 0.4)
    t = top_canvas(form, dark, seed=9622)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#3E3530", "#1C1714")
    t.ellipse(4, 4, d - 4, d - 4, outline=gold, width=0.5)
    t.text(d / 2, d * 0.42, "POWDER", 5.0, gold, 700, spacing=1.2)
    t.text(d / 2, d * 0.54, "FOUNDATION", 3.0, gold, 700, spacing=0.8)
    t.text(d / 2, d * 0.66, "ナチュラルオークル", 2.6, mix(gold, WHITE, 0.3), 600)
    top = finish(t.array(), "plastic", 9622, 0.4)
    return Product(slug="foundation_compact", name="パウダーファンデーション ナチュラルオークル", category="household",
                   mass_kg=0.05, material="plastic",
                   description="形は一般的なパウダーファンデーションの丸いコンパクト（径 72 mm・厚さ 18 mm）を蓋付きの平たい容器で近似した"
                               "もので、寸法・質量は代表値。ヒンジと中のパフ・鏡は省略。",
                   tags=["ファンデーション", "パウダーファンデーション", "コンパクト", "化粧品", "メイク", "foundation",
                         "compact", "makeup"],
                   colors=Colors(cap=dark, label_base=dark), **revolve(form, label=label, top=top, body_fill=dark))


def _stick_label(form, base: str, accent: str, seed: int, en: str, ja: str, sub: str) -> "np.ndarray":
    c = label_canvas(form, base, seed=seed)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, mix(base, WHITE, 0.15), base)
    c.rect(0, H - 2, W, H, fill=accent)
    c.vtext(fx, 4, en, min(2.6, (H - 10) / max(1, len(en)) / 1.05), accent, 800)
    c.text(0.25 * W, H * 0.3, ja, 1.6, accent, 700, max_w=W * 0.4)
    c.text(0.25 * W, H * 0.45, sub, 1.3, mix(accent, WHITE, 0.3), 600, max_w=W * 0.4)
    c.barcode(0.25 * W - 4.5, H * 0.58, 9, 7)
    return finish(c.array(), "plastic", seed, 0.4)


def lipstick() -> Product:
    form = forms.stick(0.075, 0.020, cap_h=0.04, label=(0.002, 0.073))
    black, red = "#1B1B1D", "#B3263E"
    label = _stick_label(form, black, "#D9B26A", 9631, "ROUGE", "口紅  ローズレッド", "化粧品  3.5g")
    return Product(slug="lipstick", name="口紅 ローズレッド", category="household", mass_kg=0.025, material="plastic",
                   description="形は一般的な口紅の円筒形のケース（高さ 75 mm・径 20 mm、キャップをかぶせた状態）で、寸法・質量は代表値。"
                               "細く背が高いので、立てて並べると倒れやすい。",
                   tags=["口紅", "リップスティック", "ルージュ", "化粧品", "メイク", "lipstick", "makeup"],
                   colors=Colors(cap=black, label_base=red), **revolve(form, label=label, body_fill=black))


def mascara() -> Product:
    form = forms.stick(0.12, 0.016, cap_h=0.05, label=(0.003, 0.118))
    label = _stick_label(form, "#22232A", "#C9CCD6", 9641, "MASCARA", "マスカラ  ロング", "ウォータープルーフ")
    return Product(slug="mascara", name="マスカラ ロング ウォータープルーフ", category="household", mass_kg=0.02,
                   material="plastic",
                   description="形は一般的なマスカラの細長い容器（高さ 120 mm・径 16 mm、ブラシの柄を兼ねたキャップ）で、寸法・質量は代表値。"
                               "細く背が高いので、立てて置くと倒れやすい（ふつうは寝かせるか吊り下げで陳列）。",
                   tags=["マスカラ", "化粧品", "メイク", "アイメイク", "mascara", "makeup"],
                   colors=Colors(cap="#22232A", label_base="#22232A"), **revolve(form, label=label, body_fill="#22232A"))


def cotton_pads_pack() -> Product:
    bg, accent, dark = "#FBF1F4", "#D46A8A", "#7A2E46"
    imgs = pkg_box(85, 55, 120, seed=9651, kind="film", bg=bg, accent=accent, dark=dark, title="コットン",
                   sub="化粧水がよくなじむ  やわらか", mark=None, badge="80枚", en="COTTON PADS",
                   photo=("berries", (0.2, 0.2, 0.8, 0.8)), recycle=("プラ",),
                   back="【品名】化粧用パフ\n【素材】綿100%\n【サイズ】約 5 cm × 6 cm\n"
                        "【使用上の注意】お肌に異常があるときは使用しないでください。")
    return Product(slug="cotton_pads_pack", name="化粧用コットン 80枚入", shape_class="box", category="household",
                   dims=Dimensions(0.12, 0.085, depth=0.055), mass_kg=0.04, material="film",
                   description="形は一般的な化粧用コットンの袋入り（高さ 120 mm・幅 85 mm・奥行き 55 mm）を箱で近似したもので、"
                               "寸法・質量は代表値。",
                   tags=["コットン", "化粧用コットン", "パフ", "スキンケア", "cotton pads", "cosmetic cotton"],
                   photos=["berries"], colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


PRODUCTS = {p.__name__: p for p in (lotion_bottle, milky_lotion_bottle, foundation_compact, lipstick, mascara,
                                     cotton_pads_pack)}
