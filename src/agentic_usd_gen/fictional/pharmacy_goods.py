"""架空の商品のデザイン: 薬局の小物（薬袋・お薬手帳・ピルケース）と一般用医薬品・衛生用品（鼻炎薬・漢方薬・軟膏・
うがい薬・消毒用エタノール・電子体温計・滅菌ガーゼ・伸縮包帯・使い捨てカイロ・コンタクトレンズの保存液）。

drug_medicine.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
医薬品のリスク区分は外箱の正面の枠囲みの文字で示す。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import Product, revolve
from .drug_fixtures import _capsule, _cross
from .drug_medicine import _bottle_label, _box_product, pkg_box
from .paint import Canvas, mix
from .products import INK, _face

WHITE = "#FFFFFF"
MED_TAGS = ["医薬品", "薬局", "ドラッグストア", "pharmacy"]


def _flat_faces(W: float, D: float, H: float, top: Canvas, side: str, seed: int, kind: str = "paper",
                bottom: Canvas | None = None) -> list[np.ndarray]:
    """寝かせて置く薄い物（袋・手帳）の 6 面（mm）。上面に絵柄、縁は無地の色。"""
    def plain(w: float, h: float, sd: int) -> Canvas:
        c = Canvas(w, h, None, side, sd)
        c.gradient(0, 0, w, h, mix(side, WHITE, 0.2), side)
        c.rect(0, h - max(1.0, h * 0.08), w, h, fill=mix(side, "#000000", 0.12))
        return c

    bt = bottom or plain(W, D, seed + 5)
    cs = (plain(W, H, seed), plain(W, H, seed + 1), plain(D, H, seed + 2), plain(D, H, seed + 3), top, bt)
    return [_face(c.array(), kind, seed + 10 + i, 0.8, 6) for i, c in enumerate(cs)]



def _warm(c: Canvas, cx: float, cy: float, r: float) -> None:
    """カイロの絵（だいだいの丸に白い「温」と、上に立ちのぼる湯気）。"""
    c.ellipse(cx - r, cy - r * 0.8, cx + r, cy + r * 1.2, fill="#F28C28")
    c.text(cx, cy + r * 0.2, "温", r * 1.1, WHITE, 900)
    for k in (-1, 0, 1):
        x = cx + k * r * 0.45
        c.line([(x, cy - r * 0.9), (x - r * 0.12, cy - r * 1.05), (x, cy - r * 1.2)], "#F2A65A", max(0.4, r * 0.06))


# ---------------------------------------------------------------- 薬袋・お薬手帳・ピルケース


def prescription_medicine_bag() -> Product:
    W, D, H = 130.0, 240.0, 12.0  # 寝かせて置く（幅 130・長さ 240・厚さ 12 mm）
    green = "#1F7A5C"
    c = Canvas(W, D, None, WHITE, 13201)
    c.gradient(0, 0, W, D, "#FFFFFF", "#F3F6F4")
    c.rect(0, 0, W, 10, fill=green)  # 折り返しの口
    c.text(W / 2, 30, "お くすり", 18, green, 900)
    c.rect(10, 46, W - 10, 48, fill=green)
    c.rect(20, 62, W - 20, 82, outline=INK, width=0.4)
    c.text(W - 30, 72, "様", 8, INK, 700)
    c.text(W / 2, 98, "内 服 薬", 13, INK, 900)
    rows = ["1日 3 回", "朝 ・ 昼 ・ 夕", "食後 30 分以内", "1回 1 錠  7 日分"]
    for k, s in enumerate(rows):
        y = 120 + k * 16
        c.rect(16, y - 4, 24, y + 4, outline=INK, width=0.4)
        c.text(30, y, s, 6.5, INK, 700, anchor="lm")
    c.line([(16, 120 - 2), (19, 120 + 2), (24, 120 - 5)], green, 0.8)
    c.rect(10, D - 42, W - 10, D - 12, fill="#EAF3EE", radius=2)
    c.text(W / 2, D - 33, "なかよし調剤薬局", 8, green, 900)
    c.text(W / 2, D - 21, "TEL 000-000-0000", 5, INK, 700)
    imgs = _flat_faces(W, D, H, c, "#F4F6F5", 13201)
    return _box_product("prescription_medicine_bag", "薬袋（内服薬・紙）", Dimensions(H / 1000, W / 1000, depth=D / 1000),
                        0.05,
                        "形は調剤薬局で処方薬を入れて渡す一般的な紙の薬袋（幅 130 mm・長さ 240 mm、薬が入って厚さ約 12 mm、"
                        "寝かせて置く）を箱で近似したもので、寸法・質量は代表値。口の折り返しは省略。薬局名と用法の文字は架空。",
                        ["薬袋", "くすり袋", "処方薬", "調剤", *MED_TAGS, "prescription bag", "medicine bag"], imgs,
                        "#F4F6F5")


def medication_notebook() -> Product:
    W, D, H = 105.0, 148.0, 5.0  # A6・寝かせて置く
    pink = "#E57A9A"
    c = Canvas(W, D, None, "#FCEFF3", 13211)
    c.gradient(0, 0, W, D, "#FFF6F8", "#F8DCE5")
    c.rect(0, 0, W, 34, fill=pink)
    c.text(W / 2, 17, "お薬手帳", 16, WHITE, 900)
    _capsule(c, W / 2, 62, 18)
    c.text(W / 2, 92, "MEDICATION RECORD", 5, pink, 800, spacing=0.4)
    for k, lab in enumerate(("お名前", "生年月日", "アレルギー")):
        y = 106 + k * 12
        c.text(12, y, lab, 4.5, INK, 700, anchor="lm")
        c.line([(36, y + 3), (W - 10, y + 3)], "#B8A2AA", 0.3)
    c.text(W / 2, D - 6, "受診のときは いつも お持ちください", 4.2, pink, 800)
    imgs = _flat_faces(W, D, H, c, "#F7F3F0", 13211, kind="paper")
    return _box_product("medication_notebook", "お薬手帳（A6）", Dimensions(H / 1000, W / 1000, depth=D / 1000), 0.04,
                        "形は薬局で処方薬の記録に使う一般的なお薬手帳（A6・105 × 148 mm・厚さ 5 mm、寝かせて置く）を箱で"
                        "近似したもので、寸法・質量は代表値。表紙の文字は架空。",
                        ["お薬手帳", "手帳", "処方薬", "調剤", *MED_TAGS, "medication notebook", "medicine record book"],
                        imgs, "#FCEFF3")


def pill_case_weekly() -> Product:
    n = 7
    cell, D, H = 0.026, 0.034, 0.022
    W = n * cell + 0.004
    base_c = "#F4F5F7"
    days = "月火水木金土日"
    lids = ["#E86A5C", "#F2A93B", "#F2D44A", "#6CC08A", "#4FA3D9", "#6D7FD6", "#B07CC6"]
    imgs, parts = [], [Part("Base", "box", [W, D, H - 0.004], [0, 0, (H - 0.004) / 2], color=base_c, finish="plastic",
                            material="plastic", bevel=0.002)]
    for k in range(n):
        c = Canvas(cell * 1000, D * 1000, None, lids[k], 13221 + k)
        c.gradient(0, 0, c.w_mm, c.h_mm, mix(lids[k], WHITE, 0.25), lids[k])
        c.text(c.w_mm / 2, c.h_mm * 0.45, days[k], 12, WHITE, 900)
        imgs.append(_face(c.array(), "plastic", 13221 + k, 0.3, 2))
        x = -W / 2 + 0.002 + cell * (k + 0.5)
        parts.append(Part(f"Lid{k}", "box", [cell - 0.0015, D - 0.002, 0.004], [x, 0, H - 0.002], color=lids[k],
                          finish="plastic", faces={"top": k}, material="plastic", bevel=0.001))
    return Product(slug="pill_case_weekly", name="ピルケース 1 週間（7 日分）", shape_class="assembly",
                   category="household", dims=Dimensions(H, round(W, 4), depth=D), mass_kg=0.05, static=False,
                   material="plastic",
                   description="形は一般的な 1 週間分のピルケース（7 室が横一列、幅 186 mm・奥行き 34 mm・高さ 22 mm、"
                               "曜日を書いた色ちがいのふた）で、寸法・質量は代表値。ふたは開かない。",
                   tags=["ピルケース", "薬入れ", "薬ケース", "1週間", "服薬", "薬局", "ドラッグストア", "pill case",
                         "weekly pill organizer"], photos=[],
                   colors=Colors(label_base=base_c), images=imgs, parts=parts)


# ---------------------------------------------------------------- 箱の医薬品・衛生用品


def allergy_medicine_box() -> Product:
    bg, accent, dark = "#EAF5F8", "#1B8FA6", "#0C4A57"
    imgs = pkg_box(90, 30, 110, seed=13231, kind="paper", bg=bg, accent=accent, dark=dark, title="鼻炎薬",
                   sub="鼻水・鼻づまり・くしゃみに  1日2回", mark="指定第②類医薬品", badge="24錠", en="NASAL RELIEF",
                   photo=("lavender", (0.15, 0.15, 0.85, 0.85)),
                   back="【効能】急性鼻炎、アレルギー性鼻炎又は副鼻腔炎による諸症状の緩和：くしゃみ、鼻みず、鼻づまり\n"
                        "【用法・用量】15歳以上 1回1錠 1日2回 朝夕に服用\n"
                        "【使用上の注意】服用後、乗物又は機械類の運転操作をしないでください。")
    return _box_product("allergy_medicine_box", "鼻炎薬 錠剤 24錠", Dimensions(0.11, 0.09, depth=0.03), 0.03,
                        "形は一般的な鼻炎薬の外箱（高さ 110 mm・幅 90 mm・奥行き 30 mm）で、寸法・質量は代表値。",
                        ["鼻炎薬", "鼻炎", "花粉", "アレルギー", "指定第2類医薬品", *MED_TAGS, "allergy medicine",
                         "nasal relief", "medicine box"], imgs, bg, photos=["lavender"])


def kampo_medicine_box() -> Product:
    bg, accent, dark = "#F6EFE2", "#8A5A2B", "#4A2E12"
    imgs = pkg_box(120, 50, 95, seed=13241, kind="paper", bg=bg, accent=accent, dark=dark, title="漢方薬",
                   sub="かぜのひきはじめ  顆粒  1包ずつ", mark="第②類医薬品", badge="12包", en="KAMPO GRANULES",
                   photo=("tea_leaves", (0.1, 0.1, 0.9, 0.9)),
                   back="【効能】体力中等度以上のものの次の諸症：感冒の初期（汗をかいていないもの）、鼻かぜ、頭痛、肩こり\n"
                        "【用法・用量】15歳以上 1回1包 1日3回 食前又は食間に水又は白湯で服用\n"
                        "【成分】カッコン、マオウ、タイソウ、ケイヒ、シャクヤク、カンゾウ、ショウキョウの乾燥エキス")
    return _box_product("kampo_medicine_box", "漢方薬 顆粒 12包", Dimensions(0.095, 0.12, depth=0.05), 0.06,
                        "形は一般的な分包の漢方薬（顆粒）の外箱（高さ 95 mm・幅 120 mm・奥行き 50 mm）で、寸法・質量は代表値。",
                        ["漢方薬", "漢方", "顆粒", "かぜ薬", "第2類医薬品", *MED_TAGS, "kampo medicine",
                         "herbal medicine", "medicine box"], imgs, bg, photos=["tea_leaves"])


def ointment_box() -> Product:
    bg, accent, dark = "#FFF3E6", "#E07A1F", "#7A3A06"
    imgs = pkg_box(150, 35, 35, seed=13251, kind="paper", bg=bg, accent=accent, dark=dark, title="皮ふの軟膏",
                   sub="かゆみ・湿疹・かぶれに", mark="指定第②類医薬品", badge="15g", en="SKIN OINTMENT",
                   icon=_cross,
                   back="【効能】湿疹、皮膚炎、かぶれ、かゆみ、虫さされ、あせも、じんましん\n"
                        "【用法・用量】1日数回、適量を患部に塗布してください。\n"
                        "【使用上の注意】目の周囲、粘膜等には使用しないでください。")
    return _box_product("ointment_box", "皮ふ用 軟膏 15g", Dimensions(0.035, 0.15, depth=0.035), 0.03,
                        "形は一般的な塗り薬（チューブ入りの軟膏）の細長い外箱（幅 150 mm・奥行き 35 mm・高さ 35 mm、横にして置く）"
                        "で、寸法・質量は代表値。",
                        ["軟膏", "塗り薬", "かゆみ止め", "皮膚薬", "指定第2類医薬品", *MED_TAGS, "ointment",
                         "skin cream", "medicine box"], imgs, bg)


def digital_thermometer_box() -> Product:
    bg, accent, dark = "#EEF3FA", "#3A6FC4", "#1B3766"
    imgs = pkg_box(60, 22, 160, seed=13261, kind="paper", bg=bg, accent=accent, dark=dark, title="電子体温計",
                   sub="わき専用  約15秒で予測", mark="管理医療機器", badge="1本入", en="THERMO",
                   icon=_cross,
                   back="【測定部位】わきの下\n【測定範囲】32.0〜42.0℃\n【電源】ボタン電池 1 個（付属）\n"
                        "【使用上の注意】測定前にわきの汗をよくふき取ってください。")
    return _box_product("digital_thermometer_box", "電子体温計 わき専用", Dimensions(0.16, 0.06, depth=0.022), 0.04,
                        "形は一般的な電子体温計の細長い外箱（高さ 160 mm・幅 60 mm・奥行き 22 mm、つり下げ穴は省略）で、"
                        "寸法・質量は代表値。",
                        ["体温計", "電子体温計", "医療機器", "検温", "薬局", "ドラッグストア", "digital thermometer",
                         "thermometer"], imgs, bg)


def sterile_gauze_box() -> Product:
    bg, accent, dark = "#F2F7FB", "#2F86C8", "#164466"
    imgs = pkg_box(100, 32, 130, seed=13271, kind="paper", bg=bg, accent=accent, dark=dark, title="滅菌ガーゼ",
                   sub="1枚ずつ個包装  7.5cm × 7.5cm", mark="一般医療機器", badge="10枚", en="STERILE GAUZE",
                   icon=_cross,
                   back="【品名】滅菌ガーゼ（個包装）\n【材質】綿 100%\n【滅菌方法】酸化エチレンガス滅菌\n"
                        "【使用上の注意】包装が破れているものは使わないでください。")
    return _box_product("sterile_gauze_box", "滅菌ガーゼ 個包装 10枚", Dimensions(0.13, 0.10, depth=0.032), 0.04,
                        "形は一般的な個包装の滅菌ガーゼの外箱（高さ 130 mm・幅 100 mm・奥行き 32 mm）で、寸法・質量は代表値。",
                        ["ガーゼ", "滅菌ガーゼ", "救急用品", "衛生用品", "薬局", "ドラッグストア", "sterile gauze",
                         "first aid"], imgs, bg)


def elastic_bandage_box() -> Product:
    bg, accent, dark = "#F7F1EA", "#C0623A", "#5E2A14"
    imgs = pkg_box(75, 75, 85, seed=13281, kind="paper", bg=bg, accent=accent, dark=dark, title="伸縮包帯",
                   sub="よく伸びて ずれにくい  幅7.5cm", mark="一般医療機器", badge="1巻", en="ELASTIC BANDAGE",
                   icon=_cross,
                   back="【品名】伸縮包帯\n【サイズ】幅 7.5cm × 長さ 4.5m（伸ばした長さ）\n【材質】綿、ポリウレタン\n"
                        "【使用上の注意】強く巻きすぎないでください。")
    return _box_product("elastic_bandage_box", "伸縮包帯 7.5cm × 4.5m", Dimensions(0.085, 0.075, depth=0.075), 0.06,
                        "形は一般的な伸縮包帯の外箱（高さ 85 mm・幅 75 mm・奥行き 75 mm、中に 1 巻）で、寸法・質量は代表値。",
                        ["包帯", "伸縮包帯", "救急用品", "衛生用品", "薬局", "ドラッグストア", "elastic bandage",
                         "first aid"], imgs, bg)


def body_warmer_pack() -> Product:
    bg, accent, dark = "#FDF0E8", "#E0461F", "#7A1E08"
    imgs = pkg_box(150, 60, 200, seed=13291, kind="film", bg=bg, accent=accent, dark=dark, title="使い捨てカイロ",
                   sub="貼らないタイプ  レギュラー  最高63℃", mark="持続 約12時間", badge="10個", en="HAND WARMER",
                   icon=_warm, recycle=("プラ",),
                   back="【品名】使い捨てカイロ（貼らないタイプ）\n【原材料】鉄粉、水、活性炭、バーミキュライト、吸水性樹脂、塩類\n"
                        "【使用上の注意】低温やけどに注意してください。就寝時には使用しないでください。")
    return _box_product("body_warmer_pack", "使い捨てカイロ 貼らない レギュラー 10個", Dimensions(0.20, 0.15, depth=0.06),
                        0.5,
                        "形は一般的な使い捨てカイロの外袋（高さ 200 mm・幅 150 mm・厚さ 60 mm、中に 10 個）を箱で近似したもので、"
                        "寸法・質量は代表値。",
                        ["カイロ", "使い捨てカイロ", "防寒", "冬物", "衛生用品", "ドラッグストア", "hand warmer",
                         "body warmer"], imgs, bg, material="film")


# ---------------------------------------------------------------- ボトル（うがい薬・消毒用エタノール・保存液）


def gargle_bottle() -> Product:
    form = forms.pet_bottle(0.16, 0.058, shoulder=0.18, neck_r=0.011, cap_h=0.022, cap_r=0.0145,
                            label=(0.020, 0.088), liquid_top=0.11)
    label = _bottle_label(form, "#FFF1E4", "#B5541C", "#5A2408", 13301, "うがい薬", "のどの殺菌・消毒に",
                          "第③類医薬品", "200mL", "GARGLE", _cross,
                          "【効能】口腔内及びのどの殺菌・消毒・洗浄、口臭の除去\n"
                          "【用法・用量】1回 2〜4mL を約 60mL の水にうすめ、1日数回うがいしてください。")
    return Product(slug="gargle_bottle", name="うがい薬 200mL", category="household", mass_kg=0.24, capacity_ml=200,
                   material="PET",
                   description="形は一般的なうがい薬の小さなボトル（高さ 160 mm・胴径 58 mm、白いキャップ、こい茶色の液）で、"
                               "寸法・質量は代表値。",
                   tags=["うがい薬", "うがい", "のど", "殺菌", "第3類医薬品", *MED_TAGS, "gargle", "mouth rinse"],
                   colors=Colors(cap="#F4F4F2", liquid="#5A1E08", label_base="#FFF1E4"),
                   **revolve(form, label=label, body_fill=None, liquid="#5A1E08"))


def antiseptic_ethanol_bottle() -> Product:
    form = forms.pet_bottle(0.20, 0.070, shoulder=0.15, neck_r=0.0125, cap_h=0.025, cap_r=0.016,
                            label=(0.025, 0.120), liquid_top=0.15)
    label = _bottle_label(form, "#EEF6FB", "#1D6FB8", "#0D3A63", 13311, "消毒用エタノール", "手指・皮ふの消毒に",
                          "第③類医薬品", "500mL", "ETHANOL", _cross,
                          "【効能】手指・皮膚の消毒、医療機器の消毒\n【成分】エタノール 76.9〜81.4vol%\n"
                          "【使用上の注意】火気厳禁。目に入らないようにしてください。")
    return Product(slug="antiseptic_ethanol_bottle", name="消毒用エタノール 500mL", category="household", mass_kg=0.46,
                   capacity_ml=500, material="plastic",
                   description="形は一般的な消毒用エタノールの白いボトル（高さ 200 mm・胴径 70 mm、ねじ蓋）で、寸法・質量は代表値。",
                   tags=["消毒用エタノール", "エタノール", "消毒液", "アルコール", "第3類医薬品", *MED_TAGS,
                         "ethanol", "antiseptic", "disinfectant"],
                   colors=Colors(cap="#1D6FB8", label_base="#EEF6FB"),
                   **revolve(form, label=label, body_fill="#F4F6F8"))


def contact_lens_solution_bottle() -> Product:
    form = forms.pet_bottle(0.175, 0.068, shoulder=0.16, neck_r=0.012, cap_h=0.028, cap_r=0.017,
                            label=(0.020, 0.098), liquid_top=0.12)
    label = _bottle_label(form, "#EAF6F4", "#1A9C8C", "#0B4F47", 13321, "保存液", "ソフトレンズ用  洗浄・すすぎ・消毒",
                          "医薬部外品", "360mL", "LENS SOLUTION", None,
                          "【用途】ソフトコンタクトレンズの洗浄・すすぎ・消毒・保存\n"
                          "【使用方法】レンズを指でこすり洗いし、すすいでからケースに入れ、本品を満たして 4 時間以上つけ置きしてください。",
                          photo=("lake", (0.2, 0.2, 0.8, 0.8)))
    return Product(slug="contact_lens_solution_bottle", name="コンタクトレンズ 保存液 360mL", category="household",
                   mass_kg=0.40, capacity_ml=360, material="plastic",
                   description="形は一般的なソフトコンタクトレンズ用の保存液の平たいボトル（高さ 175 mm・幅 68 mm・奥行き 46 mm）"
                               "を楕円断面の回転体で近似したもので、寸法・質量は代表値。",
                   tags=["保存液", "コンタクトレンズ", "コンタクト", "洗浄液", "医薬部外品", "薬局", "ドラッグストア",
                         "contact lens solution", "lens care"],
                   photos=["lake"], colors=Colors(cap="#1A9C8C", label_base="#EAF6F4"),
                   **revolve(form, label=label, body_fill="#F4F6F8", depth=0.046))


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    prescription_medicine_bag, medication_notebook, pill_case_weekly, allergy_medicine_box, kampo_medicine_box,
    ointment_box, digital_thermometer_box, sterile_gauze_box, elastic_bandage_box, body_warmer_pack, gargle_bottle,
    antiseptic_ethanol_bottle, contact_lens_solution_bottle)}
