"""架空の商品のデザイン: ドラッグストアのベビー・介護用品（紙おむつ・粉ミルク・おしりふき・大人用おむつ）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .drug_fixtures import _baby
from .drug_medicine import BOX_FACES, pkg_box
from .paint import finish, mix
from .products import INK

WHITE = "#FFFFFF"


def _pack(slug: str, name: str, dims: Dimensions, mass: float, imgs, bg: str, desc: str, tags: list[str],
          photos: list[str] | None = None, material: str = "film", category: str = "household") -> Product:
    return Product(slug=slug, name=name, shape_class="box", category=category, dims=dims, mass_kg=mass,
                   material=material, description=desc, tags=tags, photos=photos or [],
                   colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


def baby_diaper_pack() -> Product:
    bg, accent, dark = "#EAF4FC", "#3A8DDE", "#1A4F86"
    imgs = pkg_box(390, 190, 360, seed=9701, kind="film", bg=bg, accent=accent, dark=dark, title="紙おむつ",
                   sub="テープタイプ  Mサイズ（6〜11kg）  ふんわり通気", mark="Mサイズ", badge="64枚", en="BABY DIAPERS",
                   icon=_baby, recycle=("プラ",),
                   back="【品名】乳幼児用紙おむつ（テープタイプ）\n【サイズ】M（6〜11kg）\n"
                        "【材料】表面材：ポリオレフィン不織布　吸水材：綿状パルプ、高分子吸水材　防水材：ポリエチレンフィルム\n"
                        "【使用上の注意】汚れたおむつはすぐに取り替えてください。お子さまの手の届かない所に保管してください。")
    return _pack("baby_diaper_pack", "紙おむつ テープ Mサイズ 64枚", Dimensions(0.36, 0.39, depth=0.19), 2.2, imgs, bg,
                 "形は一般的な乳幼児用紙おむつのパック（高さ 360 mm・幅 390 mm・奥行き 190 mm、持ち手は省略）を箱で近似したもので、"
                 "寸法・質量は代表値。",
                 ["紙おむつ", "おむつ", "ベビー用品", "テープタイプ", "baby diapers", "diaper pack"])


def adult_diaper_pack() -> Product:
    bg, accent, dark = "#EEF3EA", "#5E8C4A", "#2F4A24"
    imgs = pkg_box(330, 230, 400, seed=9711, kind="film", bg=bg, accent=accent, dark=dark, title="大人用紙パンツ",
                   sub="うす型  長時間 安心  Lサイズ（ウエスト 75〜100cm）", mark="介護用品", badge="20枚",
                   en="ADULT PANTS", photo=("tea_field", (0.0, 0.2, 1.0, 0.8)), recycle=("プラ",),
                   back="【品名】大人用紙おむつ（パンツタイプ）\n【サイズ】L（ウエスト 75〜100cm）\n"
                        "【材料】表面材：ポリオレフィン不織布　吸水材：綿状パルプ、高分子吸水材\n"
                        "【使用上の注意】汚れたら早めに取り替えてください。")
    return _pack("adult_diaper_pack", "大人用紙パンツ うす型 Lサイズ 20枚", Dimensions(0.40, 0.33, depth=0.23), 1.9, imgs,
                 bg, "形は一般的な大人用紙パンツのパック（高さ 400 mm・幅 330 mm・奥行き 230 mm）を箱で近似したもので、寸法・質量は代表値。",
                 ["大人用おむつ", "紙パンツ", "介護用品", "尿もれ", "adult diapers", "incontinence pants"], ["tea_field"])


def baby_wipes_3pack() -> Product:
    bg, accent, dark = "#F2F8FC", "#4BB3C9", "#1E5E6E"
    imgs = pkg_box(200, 120, 180, seed=9721, kind="film", bg=bg, accent=accent, dark=dark, title="おしりふき",
                   sub="水99%  厚手  ノンアルコール", mark=None, badge="80枚×3", en="BABY WIPES", icon=_baby,
                   recycle=("プラ",),
                   back="【品名】ウェットティシュー\n【成分】水、PG、BG、ポリアミノプロピルビグアナイド\n"
                        "【使用上の注意】トイレに流さないでください。開封後はフタをしっかり閉めてください。")
    return _pack("baby_wipes_3pack", "おしりふき 厚手 80枚×3個パック", Dimensions(0.18, 0.20, depth=0.12), 1.4, imgs, bg,
                 "形は一般的なおしりふきの 3 個パック（詰め替えの袋を 3 段に重ねてフィルムで包んだもの、高さ 180 mm・幅 200 mm・"
                 "奥行き 120 mm）を箱で近似したもので、寸法・質量は代表値。",
                 ["おしりふき", "ウェットティッシュ", "ベビー用品", "baby wipes", "wet wipes"])


def formula_milk_can() -> Product:
    form = forms.jar(0.175, 0.127, cap_h=0.03, cap_d=0.13, label=(0.008, 0.14))
    bg, accent, dark = "#FFFFFF", "#E8A33A", "#6E4A12"
    c = label_canvas(form, bg, seed=9731)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#FFF2DC")
    c.rect(0, 0, W, 8, fill=accent)
    c.rect(0, H - 6, W, H, fill=dark)
    c.text(fx, 4, "INFANT FORMULA", 4.0, WHITE, 800, spacing=1.0)
    c.text(fx, 22, "育児用ミルク", 14, dark, 900, max_w=W * 0.3)
    c.text(fx, 34, "0か月〜1歳ごろ  母乳に近い栄養", 4.0, INK, 700, max_w=W * 0.3)
    c.photo("milk", fx - 26, 42, fx + 26, 92, shape="ellipse", feather=2.0)
    _baby(c, fx + 34, 72, 10)
    c.rect(fx - 30, 100, fx + 30, 112, fill=accent, radius=6)
    c.text(fx, 106, "大缶 800g", 7.0, WHITE, 900)
    c.text(fx, H - 3, "調製粉乳", 3.4, WHITE, 800)
    c.paragraph(0.25 * W - 38, 12, 0.25 * W + 38,
                "【名称】調製粉乳\n【原材料名】乳糖、調整脂肪、ホエイパウダー、たんぱく質濃縮ホエイパウダー、"
                "でんぷん分解物／ミネラル類、ビタミン類\n【内容量】800g\n【調乳方法】一度沸騰させた70℃以上のお湯で溶かし、"
                "人肌に冷ましてから与えてください。付属のスプーン1杯で20mlになります。\n" + NOTICE, 3.0, INK, 400)
    c.barcode(0.25 * W - 16, 96, 32, 20)
    c.recycle(0.5 * W, 104, 10, "スチール", dark, kind="can")
    label = finish(c.array(), "metal", 9731, 0.5)
    t = top_canvas(form, accent, seed=9732)
    d = t.w_mm
    t.gradient(0, 0, d, d, mix(accent, WHITE, 0.2), accent)
    t.ellipse(6, 6, d - 6, d - 6, outline=WHITE, width=1.0)
    t.text(d / 2, d * 0.45, "育児用ミルク", 12, WHITE, 900)
    t.text(d / 2, d * 0.58, "800g", 7, WHITE, 800)
    top = finish(t.array(), "plastic", 9732, 0.4)
    return Product(slug="formula_milk_can", name="育児用ミルク 大缶 800g", category="food", mass_kg=0.98, material="steel",
                   description="形は一般的な粉ミルクの大缶（高さ 175 mm・径 127 mm、プラスチックの蓋）で、寸法・質量は代表値。",
                   tags=["粉ミルク", "育児用ミルク", "ミルク缶", "ベビー用品", "infant formula", "formula milk", "baby formula"],
                   photos=["milk"], colors=Colors(cap=accent, label_base=bg),
                   **revolve(form, label=label, top=top, body_fill="#C9CCD0"))


PRODUCTS = {p.__name__: p for p in (baby_diaper_pack, formula_milk_can, baby_wipes_3pack, adult_diaper_pack)}
