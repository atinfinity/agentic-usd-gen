"""架空の商品のデザイン: ドラッグストアの医薬品・健康食品（かぜ薬・胃腸薬・頭痛薬・目薬・湿布・ビタミン・サプリ・プロテイン）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
医薬品のリスク区分（第1類・指定第2類・第2類・第3類）の表示は、外箱の正面の枠囲みの文字で示す。
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from ..spec import Colors, Dimensions
from . import forms
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .drug_fixtures import _capsule, _cross
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _face, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}
WHITE = "#FFFFFF"

Icon = Callable[[Canvas, float, float, float], None]


def pkg_box(W: float, D: float, H: float, *, seed: int, kind: str, bg: str, accent: str, dark: str, title: str,
            sub: str, mark: str | None, badge: str, back: str, en: str, icon: Icon | None = None,
            photo: tuple[str, tuple] | None = None, recycle: tuple[str, ...] = ("紙",), main: str = "front"
            ) -> list[np.ndarray]:
    """医薬品・日用品の外箱の 6 面（正面・裏・右・左・上・底）。寸法は mm（W 幅・D 奥行き・H 高さ）。

    main="top" は寝かせて置く平たい箱（湿布など）で、上面に正面と同じ絵柄を描き、正面は細い帯にする。
    mark はリスク区分などの枠囲みの文字、badge は内容量。icon は (canvas, cx, cy, r) の手続き的な絵。
    """

    def base(w: float, h: float, sd: int) -> Canvas:
        c = Canvas(w, h, None, bg, sd)
        c.gradient(0, 0, w, h, mix(bg, WHITE, 0.4), bg)
        c.rect(0, h - max(1.5, h * 0.05), w, h, fill=dark)
        return c

    def design(w: float, h: float, sd: int) -> Canvas:
        c = base(w, h, sd)
        u = min(w, h)
        band = max(4.0, h * 0.13)
        c.rect(0, 0, w, band, fill=accent)
        c.text(w / 2, band / 2, en, band * 0.42, WHITE, 800, max_w=w * 0.9, spacing=0.4)
        y = band + u * 0.04
        if mark:
            mh = max(3.0, u * 0.09)
            mw = c.text(w * 0.06 + 1, y + mh / 2, mark, mh * 0.62, accent, 900, anchor="lm", max_w=w * 0.6)
            c.rect(w * 0.06, y, w * 0.06 + mw + 2, y + mh, outline=accent, width=max(0.25, mh * 0.06))
            y += mh + u * 0.04
        ts = min(h * 0.16, w * 0.85 / max(1, len(title)))
        c.text(w / 2, y + ts * 0.6, title, ts, dark, 900, max_w=w * 0.9)
        y += ts * 1.25
        ss = min(h * 0.055, w * 0.9 / max(1, len(sub)) * 1.0)
        c.text(w / 2, y + ss * 0.6, sub, ss, INK, 700, max_w=w * 0.92)
        y += ss * 1.4
        bottom = h - max(1.5, h * 0.05) - u * 0.04
        r = min((bottom - y) * 0.42, w * 0.22)
        cx = w * 0.32 if w > h * 0.6 else w / 2
        cy = y + (bottom - y) / 2
        if photo:
            c.photo(photo[0], cx - r * 1.3, cy - r, cx + r * 1.3, cy + r, shape="ellipse", feather=r * 0.08,
                    crop=photo[1])
        elif icon and r > 2:
            icon(c, cx, cy, r)
        bs = min(r * 0.55, w * 0.1) if w > h * 0.6 else min(h * 0.05, w * 0.12)
        bx = w * 0.74 if w > h * 0.6 else w / 2
        by = cy if w > h * 0.6 else bottom - bs
        if w > h * 0.6:
            c.ellipse(bx - bs * 2.1, by - bs * 1.2, bx + bs * 2.1, by + bs * 1.2, fill=accent)
            c.text(bx, by, badge, bs, WHITE, 900, max_w=bs * 3.8)
        else:
            c.text(bx, by - bs * 0.2, badge, bs, accent, 900, max_w=w * 0.9)
        return c

    def info(w: float, h: float, sd: int) -> Canvas:
        c = base(w, h, sd)
        m = min(w, h) * 0.05
        size = max(1.3, min(w, h) / 40)
        c.rect(m, m, w - m, h * 0.72, fill=WHITE, radius=1)
        c.paragraph(m + 1, m + 1, w - m - 1, back + "\n" + NOTICE, size, INK, 400)
        bw = min(w * 0.45, 38)
        c.rect(m, h * 0.75, m + bw + 2, h * 0.75 + bw * 0.6 + 2, fill=WHITE, radius=1)
        c.barcode(m + 1, h * 0.75 + 1, bw, bw * 0.6)
        rs = min(bw * 0.3, h * 0.12)
        for k, lab in enumerate(recycle):
            c.recycle(w - m - rs * (0.7 + 1.5 * k), h * 0.75 + bw * 0.3, rs, lab, dark)
        return c

    def side(w: float, h: float, sd: int) -> Canvas:
        c = base(w, h, sd)
        c.rect(0, 0, w, max(3.0, h * 0.08), fill=accent)
        vs = min(w * 0.6, h * 0.7 / max(1, len(title)))
        c.vtext(w / 2, h * 0.12 + vs, title, vs, dark, 900)
        return c

    def strip(w: float, h: float, sd: int, s: str) -> Canvas:
        c = base(w, h, sd)
        c.text(w / 2, h * 0.45, s, min(h * 0.4, w * 0.9 / max(1, len(s))), dark, 900, max_w=w * 0.92)
        return c

    if main == "top":
        fr = strip(W, H, seed, f"{title}  {badge}")
        tp = design(W, D, seed + 4)
        bt = info(W, D, seed + 5)
        bk = strip(W, H, seed + 1, sub)
    else:
        fr = design(W, H, seed)
        bk = info(W, H, seed + 1)
        tp = strip(W, D, seed + 4, f"{title}  {badge}")
        bt = strip(W, D, seed + 5, "使用期限 2029.09  ロット A1")
    sides = [side(D, H, seed + 2), side(D, H, seed + 3)] if main != "top" else \
        [strip(D, H, seed + 2, title), strip(D, H, seed + 3, badge)]
    return [_face(c.array(), kind, seed + 10 + i, 0.8) for i, c in enumerate((fr, bk, *sides, tp, bt))]


def _box_product(slug: str, name: str, dims: Dimensions, mass: float, desc: str, tags: list[str], imgs, bg: str,
                 category: str = "household", material: str = "paper", photos: list[str] | None = None) -> Product:
    return Product(slug=slug, name=name, shape_class="box", category=category, dims=dims, mass_kg=mass,
                   material=material, description=desc, tags=tags, photos=photos or [],
                   colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


# ---------------------------------------------------------------- 箱の医薬品


def cold_medicine_box() -> Product:
    bg, accent, dark = "#EAF1FB", "#1E5AA8", "#0F2F63"
    imgs = pkg_box(95, 40, 120, seed=9401, kind="paper", bg=bg, accent=accent, dark=dark, title="かぜ薬",
                   sub="のどの痛み・発熱・鼻水に  錠剤", mark="指定第②類医薬品", badge="60錠", en="COLD RELIEF",
                   icon=_capsule,
                   back="【効能】かぜの諸症状（のどの痛み、発熱、鼻水、鼻づまり、くしゃみ、せき、たん、悪寒、頭痛）の緩和\n"
                        "【用法・用量】15歳以上 1回3錠 1日3回 食後なるべく30分以内に服用\n"
                        "【使用上の注意】服用後、乗物又は機械類の運転操作をしないでください。")
    return _box_product("cold_medicine_box", "総合かぜ薬 錠剤 60錠", Dimensions(0.12, 0.095, depth=0.04), 0.07,
                        "形は一般的な総合かぜ薬の外箱（高さ 120 mm・幅 95 mm・奥行き 40 mm、立てて置く）で、寸法・質量は代表値。",
                        ["かぜ薬", "風邪薬", "総合かぜ薬", "医薬品", "指定第2類医薬品", "cold medicine", "medicine box"],
                        imgs, bg)


def stomach_medicine_box() -> Product:
    bg, accent, dark = "#EAF6EE", "#2E8B57", "#164A2E"
    imgs = pkg_box(120, 45, 90, seed=9411, kind="paper", bg=bg, accent=accent, dark=dark, title="胃腸薬",
                   sub="胃もたれ・胸やけ・食べすぎに  細粒", mark="第②類医薬品", badge="32包", en="STOMACH CARE",
                   photo=("mint", (0.15, 0.1, 0.85, 0.9)),
                   back="【効能】胃もたれ、胸やけ、食べすぎ、飲みすぎ、胃部不快感、消化不良、胃痛\n"
                        "【用法・用量】15歳以上 1回1包 1日3回 食後に服用\n"
                        "【成分】炭酸水素ナトリウム、ケイ酸アルミン酸マグネシウム、ケイヒ末、ウイキョウ末")
    return _box_product("stomach_medicine_box", "胃腸薬 細粒 32包", Dimensions(0.09, 0.12, depth=0.045), 0.08,
                        "形は一般的な分包の胃腸薬の外箱（高さ 90 mm・幅 120 mm・奥行き 45 mm）で、寸法・質量は代表値。",
                        ["胃腸薬", "胃薬", "医薬品", "第2類医薬品", "stomach medicine", "antacid", "medicine box"],
                        imgs, bg, photos=["mint"])


def headache_medicine_box() -> Product:
    bg, accent, dark = "#FCEDEE", "#C62F3A", "#6E1219"
    imgs = pkg_box(90, 30, 110, seed=9421, kind="paper", bg=bg, accent=accent, dark=dark, title="頭痛薬",
                   sub="頭痛・生理痛・歯痛に  速く効く", mark="指定第②類医薬品", badge="24錠", en="PAIN RELIEF",
                   icon=_cross,
                   back="【効能】頭痛・月経痛（生理痛）・歯痛・抜歯後の疼痛・咽喉痛・関節痛・神経痛・腰痛・肩こり痛の鎮痛、悪寒・発熱時の解熱\n"
                        "【用法・用量】15歳以上 1回2錠 1日3回まで 服用間隔は4時間以上\n"
                        "【使用上の注意】空腹時をさけて服用してください。")
    return _box_product("headache_medicine_box", "解熱鎮痛薬 24錠", Dimensions(0.11, 0.09, depth=0.03), 0.03,
                        "形は一般的な解熱鎮痛薬の外箱（高さ 110 mm・幅 90 mm・奥行き 30 mm）で、寸法・質量は代表値。",
                        ["頭痛薬", "解熱鎮痛薬", "鎮痛剤", "医薬品", "指定第2類医薬品", "headache medicine", "pain reliever",
                         "medicine box"], imgs, bg)


def eye_drops_box() -> Product:
    bg, accent, dark = "#E6F4FA", "#1689C7", "#0B456A"
    imgs = pkg_box(45, 25, 105, seed=9431, kind="paper", bg=bg, accent=accent, dark=dark, title="目薬",
                   sub="目の疲れ・充血に", mark="第②類医薬品", badge="12mL", en="EYE DROPS",
                   photo=("lake", (0.2, 0.2, 0.8, 0.8)),
                   back="【効能】目の疲れ、結膜充血、目のかゆみ、目のかすみ、眼病予防\n"
                        "【用法・用量】1回1〜2滴、1日5〜6回点眼\n"
                        "【使用上の注意】容器の先をまぶた・まつ毛に触れさせないでください。開封後はなるべく早く使ってください。")
    return _box_product("eye_drops_box", "目薬 疲れ目・充血 12mL", Dimensions(0.105, 0.045, depth=0.025), 0.025,
                        "形は一般的な目薬の外箱（高さ 105 mm・幅 45 mm・奥行き 25 mm、中に 12 mL の点眼容器）で、寸法・質量は代表値。"
                        "細く背が高いので、棚では倒れやすい。",
                        ["目薬", "点眼薬", "医薬品", "第2類医薬品", "eye drops", "medicine box"], imgs, bg,
                        photos=["lake"])


def cold_compress_pack() -> Product:
    bg, accent, dark = "#EEF5FB", "#2F6DB5", "#173A66"
    imgs = pkg_box(190, 145, 25, seed=9441, kind="film", bg=bg, accent=accent, dark=dark, title="冷感湿布",
                   sub="肩こり・腰痛・筋肉痛に  はがれにくい", mark="第③類医薬品", badge="24枚", en="COOL PAIN RELIEF PATCH",
                   icon=_cross, recycle=("プラ",), main="top",
                   back="【効能】肩こり、腰痛、筋肉痛、筋肉疲労、打撲、ねんざ、関節痛\n"
                        "【用法・用量】1日1〜2回、患部に貼ってください。\n"
                        "【使用上の注意】傷口・湿疹・かぶれのある部位には使わないでください。")
    return _box_product("cold_compress_pack", "冷感湿布 24枚入", Dimensions(0.025, 0.19, depth=0.145), 0.2,
                        "形は一般的な湿布（パップ剤）の袋（幅 190 mm・奥行き 145 mm・厚さ 25 mm、寝かせて置く）を箱で近似したもので、"
                        "寸法・質量は代表値。チャックは省略。",
                        ["湿布", "冷湿布", "パップ剤", "医薬品", "第3類医薬品", "cold compress", "pain relief patch"],
                        imgs, bg, material="film")


# ---------------------------------------------------------------- ボトル（ビタミン・サプリ）


def _bottle_label(form, bg: str, accent: str, dark: str, seed: int, title: str, sub: str, mark: str, count: str,
                  en: str, icon: Icon | None, back: str, photo: tuple | None = None) -> np.ndarray:
    c = label_canvas(form, bg, seed=seed)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, mix(bg, WHITE, 0.3), bg)
    c.rect(0, 0, W, 4, fill=accent)
    c.rect(0, H - 3, W, H, fill=dark)
    c.text(fx, 8, en, 2.8, accent, 800, spacing=0.4, max_w=W * 0.3)
    c.text(fx, 15, mark, 2.6, INK, 700, max_w=W * 0.3)
    c.text(fx, 24, title, 8.0, dark, 900, max_w=W * 0.32)
    c.text(fx, 32, sub, 3.0, INK, 700, max_w=W * 0.32)
    r = min(H - 44, 10)
    if photo:
        c.photo(photo[0], fx - r * 1.4, 37, fx + r * 1.4, 37 + 2 * r, shape="ellipse", feather=1.0, crop=photo[1])
    elif icon and r > 3:
        icon(c, fx, 37 + r, r)
    c.text(fx, H - 6.5, count, 4.0, accent, 900)
    c.paragraph(0.25 * W - 16, 6, 0.25 * W + 16, back + "\n" + NOTICE, 1.7, INK, 400)
    c.barcode(0.5 * W - 8, H - 18, 16, 11)
    return finish(c.array(), "film", seed, 0.6)


def vitamin_bottle() -> Product:
    form = forms.jar(0.105, 0.058, cap_h=0.022, cap_d=0.052, label=(0.010, 0.078))
    amber = "#7A3E0E"
    label = _bottle_label(form, "#FFF5E0", "#E08A12", "#6A3A06", 9451, "ビタミンC", "疲れ・肌あれに  錠剤",
                          "第③類医薬品", "120錠", "VITAMIN C", None,
                          "【効能】しみ・そばかす・日やけによる色素沈着の緩和、歯ぐきからの出血の予防\n"
                          "【用法・用量】15歳以上 1回2錠 1日3回まで", photo=("lemon", (0.1, 0.1, 0.9, 0.9)))
    return Product(slug="vitamin_bottle", name="ビタミンC 錠剤 120錠", category="household", mass_kg=0.08,
                   material="plastic",
                   description="形は一般的なビタミン剤の白いプラスチックボトル（高さ 105 mm・胴径 58 mm、白いねじ蓋）で、寸法・質量は代表値。",
                   tags=["ビタミン", "ビタミンC", "ビタミン剤", "医薬品", "第3類医薬品", "vitamin", "vitamin bottle"],
                   photos=["lemon"], colors=Colors(cap="#F4F4F2", label_base="#FFF5E0"),
                   **revolve(form, label=label, body_fill=amber))


def supplement_bottle() -> Product:
    form = forms.jar(0.12, 0.062, cap_h=0.024, cap_d=0.05, label=(0.010, 0.088))
    form.square = 4.0
    label = _bottle_label(form, "#EEF6E8", "#4C9A2A", "#24501A", 9461, "マルチビタミン", "12種のビタミン・ミネラル",
                          "栄養機能食品", "180粒", "SUPPLEMENT", _capsule,
                          "【名称】ビタミン・ミネラル含有食品\n【召し上がり方】1日2粒を目安に、水またはぬるま湯でお召し上がりください。\n"
                          "【原材料】還元麦芽糖水あめ、ビタミンC、酸化マグネシウム、ナイアシン、ビタミンE")
    return Product(slug="supplement_bottle", name="マルチビタミン サプリメント 180粒", category="food", mass_kg=0.13,
                   material="plastic",
                   description="形は一般的なサプリメントの角の丸い四角のボトル（高さ 120 mm・幅 62 mm、ねじ蓋）で、寸法・質量は代表値。",
                   tags=["サプリメント", "サプリ", "マルチビタミン", "栄養機能食品", "健康食品", "supplement",
                         "supplement bottle"],
                   colors=Colors(cap="#FFFFFF", label_base="#EEF6E8"),
                   **revolve(form, label=label, body_fill="#E4E8DC"))


# ---------------------------------------------------------------- プロテイン（自立する袋）


def protein_bag() -> Product:
    W, H = 220.0, 300.0
    navy, brown, white = "#1D2A44", "#8A5530", WHITE
    c = Canvas(W, H, None, navy, seed=9471)
    c.gradient(0, 0, W, H, "#26365A", "#141D30")
    seal_crimp(c, 0, 0, W, 14, "#3A4A6E", 2.0)
    c.rect(0, 14, W, 22, fill=brown)
    c.text(W / 2, 18, "WHEY PROTEIN  ━  CHOCOLATE", 4.4, white, 800, spacing=0.8)
    c.text(W / 2, 48, "ホエイ", 18, white, 900)
    c.text(W / 2, 76, "プロテイン", 30, white, 900, max_w=W - 20)
    c.text(W / 2, 100, "たんぱく質 20g ／ 1食あたり", 8, "#F2C230", 800, max_w=W - 20)
    c.photo("chocolate", 30, 112, W - 30, 220, shape="round", radius=8, feather=2.0, crop=(0.40, 0.20, 0.88, 0.56))  # 袋の銘柄・カードを避ける
    c.rect(W / 2 - 70, 232, W / 2 + 70, 252, fill=brown, radius=10)
    c.text(W / 2, 242, "ミルクチョコレート風味", 8.4, white, 800)
    c.text(W / 2, 272, "1kg", 14, white, 900)
    img = trim_safe(edge_shade(finish(c.array(), "film", 9471, 1.0), 25, 0.16))
    b = Canvas(W, H, None, navy, seed=9472)
    b.gradient(0, 0, W, H, "#26365A", "#141D30")
    seal_crimp(b, 0, 0, W, 14, "#3A4A6E", 2.0)
    b.rect(14, 28, W - 14, 196, fill=white, radius=4)
    yb = b.paragraph(20, 34, W - 20, "【名称】乳たんぱく加工食品\n【原材料名】乳清たんぱく、ココアパウダー、デキストリン、"
                     "食塩／乳化剤、甘味料、香料\n【内容量】1kg\n【お召し上がり方】付属のスプーン2杯（約30g）を水200mlに"
                     "溶かしてお召し上がりください。\n【保存方法】直射日光・高温多湿を避けて保存してください。", 5.0, INK, 400)
    b.table(20, yb + 4, W - 20, "栄養成分表示（1食30gあたり）",
            [("エネルギー", "118kcal"), ("たんぱく質", "20.1g"), ("脂質", "2.0g"), ("炭水化物", "4.8g"), ("食塩相当量", "0.3g")],
            4.6)
    b.rect(14, 206, W - 14, H - 14, fill=white, radius=4)
    b.barcode(22, 214, 70, 44)
    b.recycle(124, 236, 20, "プラ", navy, sub="袋")
    b.paragraph(150, 214, W - 20, NOTICE, 4.0, INK, 500)
    back = trim_safe(edge_shade(finish(b.array(), "film", 9472, 1.0), 25, 0.16))
    return Product(slug="protein_bag", name="ホエイプロテイン チョコレート風味 1kg", shape_class="pouch", category="food",
                   dims=Dimensions(0.30, 0.22, depth=0.10, gusset=0.10, square=3), mass_kg=1.05, material="film",
                   description="形は一般的な 1 kg 入りのプロテインのスタンドパック（高さ 300 mm・幅 220 mm・厚さ約 100 mm、底マチで自立）"
                               "で、寸法・質量は代表値。チャックは省略。",
                   tags=["プロテイン", "ホエイプロテイン", "健康食品", "スポーツ", "protein", "protein powder", "whey protein"],
                   photos=["chocolate"], colors=Colors(label_base=navy), images=[img, back], faces={"front": 0, "back": 1})


PRODUCTS = {p.__name__: p for p in (cold_medicine_box, stomach_medicine_box, headache_medicine_box, eye_drops_box,
                                     cold_compress_pack, vitamin_bottle, supplement_bottle, protein_bag)}
