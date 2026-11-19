"""架空の商品のデザイン: 調剤薬局の調剤室で使う医療用医薬品と調剤用品（PTP の元箱・散剤の元瓶・投薬瓶・軟膏つぼ・坐薬・
吸入薬・分包紙のロール・乳鉢と乳棒・注射針の廃棄容器・酒精綿・使い捨て手袋・処方の湿布）。

実在の商品名・メーカー名・ロゴは使わない。医療用医薬品の名前は一般名（成分名）で書き、［ ］の中の会社名は架空。
形と寸法は同じ種類の物の一般的な値にする。
"""

from __future__ import annotations

from ..spec import Colors, Dimensions, Part
from . import forms
from .base import Product, label_canvas, revolve
from .drug_fixtures import _capsule, _cross
from .drug_medicine import _box_product, pkg_box
from .paint import Canvas, mix
from .products import INK, _box, _face

WHITE = "#FFFFFF"
MAKER = "［ひまわり製薬］"
RX_TAGS = ["医療用医薬品", "処方薬", "調剤", "調剤薬局", "薬局", "pharmacy", "prescription drug"]
SUPPLY_TAGS = ["調剤用品", "調剤", "調剤薬局", "薬局", "pharmacy supplies"]


def _rx_label(form, bg: str, accent: str, dark: str, seed: int, title: str, sub: str, count: str, back: str):
    """医療用医薬品の瓶の全周ラベル（正面に一般名・規格・会社名、裏に保管の注意）。"""
    c = label_canvas(form, bg, seed)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, mix(bg, WHITE, 0.3), bg)
    c.rect(0, 0, W, H * 0.12, fill=accent)
    c.rect(0, H - max(1.5, H * 0.05), W, H, fill=dark)
    c.text(fx, H * 0.06, "処方箋医薬品", H * 0.07, WHITE, 900, max_w=W * 0.3)
    c.text(fx, H * 0.30, title, H * 0.15, dark, 900, max_w=W * 0.34)
    c.text(fx, H * 0.48, sub, H * 0.08, INK, 700, max_w=W * 0.34)
    c.text(fx, H * 0.66, count, H * 0.12, accent, 900, max_w=W * 0.3)
    c.text(fx, H * 0.84, MAKER, H * 0.07, INK, 700, max_w=W * 0.3)
    c.paragraph(0.25 * W - W * 0.12, H * 0.18, 0.25 * W + W * 0.12, back, H * 0.055, INK, 400)
    c.barcode(0.5 * W - 6, H * 0.40, 12, H * 0.35)
    return _face(c.array(), "film", seed, 0.6, 4)


# ---------------------------------------------------------------- 箱の医療用医薬品


def ptp_medicine_box() -> Product:
    bg, accent, dark = "#F4F7FB", "#2457A6", "#0F2B5A"
    imgs = pkg_box(110, 60, 70, seed=13601, kind="paper", bg=bg, accent=accent, dark=dark,
                   title="アムロジピン錠 5mg", sub=f"PTP 10錠×10シート  {MAKER}", mark="処方箋医薬品", badge="100錠",
                   en="AMLODIPINE TABLETS 5mg", icon=_capsule,
                   back="【貯法】室温保存  【有効期間】3年\n"
                        "注意－医師等の処方箋により使用すること\n"
                        "【製造販売元】ひまわり製薬株式会社（架空）")
    return _box_product("ptp_medicine_box", "医療用医薬品の元箱 錠剤 PTP 100錠", Dimensions(0.07, 0.11, depth=0.06),
                        0.09,
                        "形は調剤薬局の棚に並ぶ一般的な医療用医薬品（錠剤）の元箱（幅 110 mm・奥行き 60 mm・高さ 70 mm、"
                        "PTP シート 10 錠×10 枚入り）で、寸法・質量は代表値。薬の名前は一般名で、会社名は架空。",
                        ["医療用医薬品", "元箱", "錠剤", "PTP", "処方箋医薬品", *RX_TAGS, "medicine box",
                         "tablet box"], imgs, bg)


def suppository_box() -> Product:
    bg, accent, dark = "#FFF6EE", "#D9622B", "#6E2A0B"
    imgs = pkg_box(100, 45, 55, seed=13611, kind="paper", bg=bg, accent=accent, dark=dark,
                   title="アセトアミノフェン坐剤 200", sub=f"小児用  1個ずつの包装  {MAKER}", mark="処方箋医薬品",
                   badge="50個", en="ACETAMINOPHEN SUPPOSITORIES", icon=_capsule,
                   back="【貯法】冷所保存（30℃以上では溶けることがあります）\n"
                        "注意－医師等の処方箋により使用すること\n【製造販売元】ひまわり製薬株式会社（架空）")
    return _box_product("suppository_box", "医療用 坐剤の元箱 50個", Dimensions(0.055, 0.10, depth=0.045), 0.12,
                        "形は調剤薬局で保管する一般的な医療用の坐剤（解熱剤）の元箱（幅 100 mm・奥行き 45 mm・高さ 55 mm）で、"
                        "寸法・質量は代表値。薬の名前は一般名で、会社名は架空。",
                        ["坐薬", "坐剤", "解熱剤", "元箱", "処方箋医薬品", *RX_TAGS, "suppository",
                         "medicine box"], imgs, bg)


def inhaler_box() -> Product:
    bg, accent, dark = "#EEF7F5", "#13897A", "#07433B"
    imgs = pkg_box(70, 45, 115, seed=13621, kind="paper", bg=bg, accent=accent, dark=dark,
                   title="吸入ステロイド", sub=f"ドライパウダー吸入器  60吸入  {MAKER}", mark="処方箋医薬品",
                   badge="1キット", en="INHALATION POWDER", icon=_cross,
                   back="【用法】1回1吸入 1日2回\n吸入後はうがいをしてください。\n"
                        "注意－医師等の処方箋により使用すること\n【製造販売元】ひまわり製薬株式会社（架空）")
    return _box_product("inhaler_box", "医療用 吸入薬（吸入器入り）の箱", Dimensions(0.115, 0.07, depth=0.045), 0.08,
                        "形は調剤薬局で渡す一般的な医療用の吸入薬（ドライパウダーの吸入器 1 個入り）の箱（幅 70 mm・奥行き 45 mm・"
                        "高さ 115 mm）で、寸法・質量は代表値。会社名は架空。",
                        ["吸入薬", "吸入器", "ぜんそく", "処方箋医薬品", *RX_TAGS, "inhaler", "medicine box"], imgs,
                        bg)


def compress_patch_bag() -> Product:
    bg, accent, dark = "#F2F6FA", "#4E6E91", "#22364E"
    imgs = pkg_box(180, 140, 15, seed=13631, kind="film", bg=bg, accent=accent, dark=dark,
                   title="ロキソプロフェン テープ 100mg", sub=f"10cm×14cm  7枚入  {MAKER}", mark="処方箋医薬品",
                   badge="7枚", en="LOXOPROFEN TAPE", icon=_cross, recycle=("プラ",), main="top",
                   back="【用法】1日1回、患部に貼付する。\n開封後はチャックを閉めて保管してください。\n"
                        "注意－医師等の処方箋により使用すること\n【製造販売元】ひまわり製薬株式会社（架空）")
    return _box_product("compress_patch_bag", "医療用 湿布（テープ剤）の袋 7枚", Dimensions(0.015, 0.18, depth=0.14),
                        0.07,
                        "形は調剤薬局で処方される一般的な医療用の湿布（テープ剤）の袋（幅 180 mm・奥行き 140 mm・厚さ 15 mm、"
                        "寝かせて置く）を箱で近似したもので、寸法・質量は代表値。薬の名前は一般名で、会社名は架空。",
                        ["湿布", "テープ剤", "貼り薬", "処方箋医薬品", *RX_TAGS, "pain relief patch",
                         "prescription patch"], imgs, bg, material="film")


# ---------------------------------------------------------------- 調剤用品の箱


def alcohol_swab_box() -> Product:
    bg, accent, dark = "#F1F6FC", "#3A7BD5", "#1A3D70"
    imgs = pkg_box(95, 95, 60, seed=13641, kind="paper", bg=bg, accent=accent, dark=dark, title="酒精綿",
                   sub="個包装  3cm×4cm  エタノール含浸", mark="一般医療機器", badge="200包", en="ALCOHOL SWABS",
                   icon=_cross,
                   back="【用途】注射部位・医療器具の清拭消毒\n【使用上の注意】火気に近づけないでください。\n"
                        "【製造販売元】あおぞらメディカル株式会社（架空）")
    return _box_product("alcohol_swab_box", "酒精綿 個包装 200包", Dimensions(0.06, 0.095, depth=0.095), 0.35,
                        "形は一般的な個包装のアルコール綿（酒精綿）の箱（幅 95 mm・奥行き 95 mm・高さ 60 mm）で、"
                        "寸法・質量は代表値。会社名は架空。",
                        ["酒精綿", "アルコール綿", "消毒綿", "衛生用品", *SUPPLY_TAGS, "alcohol swab",
                         "alcohol prep pad"], imgs, bg)


def disposable_gloves_box() -> Product:
    bg, accent, dark = "#F2F0FA", "#5B4FC4", "#2A2266"
    imgs = pkg_box(240, 125, 65, seed=13651, kind="paper", bg=bg, accent=accent, dark=dark, title="使い捨て手袋",
                   sub="ニトリル  パウダーフリー  Mサイズ", mark="左右兼用", badge="100枚", en="NITRILE GLOVES",
                   back="【材質】ニトリルゴム\n【使用上の注意】使い捨てです。熱いものには触れないでください。\n"
                        "【販売元】あおぞらメディカル株式会社（架空）")
    return _box_product("disposable_gloves_box", "ニトリルの使い捨て手袋 M 100枚", Dimensions(0.065, 0.24, depth=0.125),
                        0.45,
                        "形は一般的な箱入りの使い捨て手袋（幅 240 mm・奥行き 125 mm・高さ 65 mm、上から 1 枚ずつ取り出す）で、"
                        "寸法・質量は代表値。取り出し口は省略。会社名は架空。",
                        ["使い捨て手袋", "ニトリル手袋", "手袋", "衛生用品", *SUPPLY_TAGS, "disposable gloves",
                         "nitrile gloves"], imgs, bg)


# ---------------------------------------------------------------- 瓶（散剤の元瓶・投薬瓶・軟膏つぼ）


def powder_stock_bottle() -> Product:
    form = forms.jar(0.15, 0.085, cap_h=0.028, cap_d=0.078, label=(0.015, 0.105))
    label = _rx_label(form, "#FFF8EE", "#B5541C", "#5A2408", 13661, "酸化マグネシウム", "細粒 83%", "500g",
                      "【貯法】気密容器・室温保存\n使用後はふたを固く閉めてください。\n"
                      "注意－医師等の処方箋により使用すること")
    amber = "#7A3E0E"
    return Product(slug="powder_stock_bottle", name="散剤の元瓶 500g（褐色）", category="household", mass_kg=0.62,
                   material="plastic",
                   description="形は調剤薬局の散薬台に並ぶ一般的な散剤（粉薬）の褐色の広口瓶（高さ 150 mm・胴径 85 mm、"
                               "白いねじ蓋）で、寸法・質量は代表値。薬の名前は一般名で、会社名は架空。",
                   tags=["散剤", "粉薬", "元瓶", "薬瓶", "処方箋医薬品", *RX_TAGS, "powder medicine bottle",
                         "stock bottle"],
                   colors=Colors(cap="#F4F4F2", label_base="#FFF8EE"),
                   **revolve(form, label=label, body_fill=amber))


def syrup_dosing_bottle() -> Product:
    form = forms.pet_bottle(0.105, 0.040, shoulder=0.20, neck_r=0.0095, cap_h=0.016, cap_r=0.0115,
                            label=(0.010, 0.072), liquid_top=0.055)
    c = label_canvas(form, "#F6F8FA", 13671)
    W, H = c.w_mm, c.h_mm
    fx = 0.75 * W
    c.gradient(0, 0, W, H, "#FFFFFF", "#EEF2F5")
    for k in range(13):  # 目盛り（5 mL ごと、10 mL ごとに長い線と数字）
        y = H - 3 - k * (H - 8) / 12
        long_ = k % 2 == 0
        c.line([(fx - 13, y), (fx - (6 if long_ else 9), y)], "#2457A6", 0.35)
        if long_ and k:
            c.text(fx - 2, y, f"{k * 5}", 2.4, "#2457A6", 800, anchor="lm")
    c.rect(0.25 * W - 11, 4, 0.25 * W + 11, H - 4, fill=WHITE, outline="#2457A6", width=0.4, radius=1)
    c.text(0.25 * W, 9, "内 用 薬", 3.2, "#2457A6", 900)
    c.text(0.25 * W, 17, "1回 5mL  1日3回", 2.4, INK, 700, max_w=20)
    c.text(0.25 * W, 23, "毎食後  よく振って", 2.4, INK, 700, max_w=20)
    c.text(0.25 * W, H - 9, "なかよし調剤薬局", 2.0, INK, 700, max_w=20)
    c.rect(0, H - 1.2, W, H, fill="#C9D3DD")
    label = _face(c.array(), "film", 13671, 0.5, 3)
    pink = "#E98AA6"
    return Product(slug="syrup_dosing_bottle", name="投薬瓶 60mL（シロップ入り）", category="household", mass_kg=0.08,
                   capacity_ml=60, material="plastic",
                   description="形は調剤薬局で水剤（シロップ）を渡す一般的な目盛り付きの投薬瓶（高さ 105 mm・胴径 40 mm、"
                               "60 mL、白いキャップ、桃色のシロップ）で、寸法・質量は代表値。用法のラベルと薬局名は架空。",
                   tags=["投薬瓶", "水剤", "シロップ", "飲み薬", "目盛り", *SUPPLY_TAGS, "dosing bottle",
                         "syrup bottle"],
                   colors=Colors(cap="#F4F4F2", liquid=pink, label_base="#F6F8FA"),
                   **revolve(form, label=label, body_fill=None, liquid=pink))


def ointment_jar() -> Product:
    form = forms.jar(0.050, 0.060, cap_h=0.020, cap_d=0.062, label=(0.004, 0.028))
    c = label_canvas(form, WHITE, 13681)
    W, H = c.w_mm, c.h_mm
    c.gradient(0, 0, W, H, "#FFFFFF", "#F1F3F4")
    c.rect(0.75 * W - 30, 2, 0.75 * W + 30, H - 2, fill=WHITE, outline="#2E9E5B", width=0.4, radius=1)
    c.text(0.75 * W, 7, "外 用 薬", 3.6, "#2E9E5B", 900)
    c.text(0.75 * W, 14, "1日2回  患部に塗る", 2.6, INK, 700, max_w=56)
    c.text(0.75 * W, 20, "混合軟膏  20g", 2.6, INK, 700, max_w=56)
    c.text(0.25 * W, 12, "なかよし調剤薬局", 2.2, INK, 700, max_w=40)
    c.rect(0, H - 1.0, W, H, fill="#D5D8DA")
    label = _face(c.array(), "film", 13681, 0.5, 3)
    return Product(slug="ointment_jar", name="軟膏つぼ 20g（混合軟膏入り）", category="household", mass_kg=0.04,
                   material="plastic",
                   description="形は調剤薬局で混ぜ合わせた軟膏を渡す一般的な白い軟膏つぼ（高さ 50 mm・胴径 60 mm、ねじ蓋）で、"
                               "寸法・質量は代表値。用法のラベルと薬局名は架空。",
                   tags=["軟膏つぼ", "軟膏", "塗り薬", "外用薬", "容器", *SUPPLY_TAGS, "ointment jar",
                         "cream container"],
                   colors=Colors(cap="#F4F4F2", label_base=WHITE),
                   **revolve(form, label=label, body_fill="#F6F6F4"))


# ---------------------------------------------------------------- 分包紙のロール・乳鉢・廃棄容器（部品の組み合わせ）


def sachet_paper_roll() -> Product:
    D, W = 0.22, 0.08  # 外径・幅（横にして置く）
    core_d = 0.076
    wr = Canvas(220, 220, None, "#F4F7F5", 13691)  # 端面（巻いた紙の輪・紙管・品名のシール）
    wr.gradient(0, 0, 220, 220, "#FFFFFF", "#E6ECE8")
    for k in range(8):
        r = 108 - k * 9
        wr.ellipse(110 - r, 110 - r, 110 + r, 110 + r, outline="#D5DDD8", width=0.8)
    wr.ellipse(72, 72, 148, 148, fill="#B79A6E")
    wr.ellipse(84, 84, 136, 136, fill="#6E5A3E")
    wr.rect(70, 160, 150, 196, fill="#1F7A5C", radius=4)
    wr.text(110, 172, "分包紙", 12, WHITE, 900)
    wr.text(110, 188, "80mm", 9, WHITE, 800)
    wr.rect(0, 214, 220, 220, fill="#C9D3CD")
    wrap = _face(wr.array(), "paper", 13691, 0.8, 6)
    parts = [
        Part("Roll", "cylinder", [D, D, W], [0, 0, D / 2], color="#F4F7F5", finish="matte", rotation=[0.0, 90.0, 0.0],
             material="paper", faces={"top": 0, "bottom": 0}),
        Part("Core", "cylinder", [core_d, core_d, W + 0.004], [0, 0, D / 2], color="#B79A6E", finish="matte",
             rotation=[0.0, 90.0, 0.0], material="paper", collision=False),
        _box("Tail", (W, 0.06, 0.0015), (0, -0.03, 0.00075), "#F4F7F5", "matte", collision=False),
    ]
    return Product(slug="sachet_paper_roll", name="分包紙のロール 幅 80mm（グラシン・ラミネート）", shape_class="assembly",
                   category="household", dims=Dimensions(D, W, depth=D), mass_kg=1.6, static=False,
                   material="paper",
                   description="形は錠剤分包機・散剤分包機に掛ける一般的な分包紙のロール（外径 220 mm・幅 80 mm・紙管の径 76 mm、"
                               "横にして置き、端を少し引き出す）で、寸法・質量は代表値。印刷の文字は架空。",
                   tags=["分包紙", "分包紙ロール", "一包化", "ロール紙", *SUPPLY_TAGS, "sachet paper roll",
                         "packaging paper roll"], photos=[],
                   colors=Colors(label_base="#F4F7F5"), images=[wrap], parts=parts)


def mortar_and_pestle() -> Product:
    D, H = 0.15, 0.075  # 乳鉢の外径・高さ
    white = "#F2F1EC"
    t = 0.008
    parts = [Part("Foot", "cylinder", [0.08, 0.08, 0.012], [0, 0, 0.006], color=white, finish="glossy",
                  material="ceramic")]
    n = 4  # 鉢の壁を下から上へ広がる 4 段の輪で近似（内側は空洞）
    for k in range(n):
        z0 = 0.012 + k * (H - 0.012) / n
        h = (H - 0.012) / n
        d = 0.09 + (D - 0.09) * (k + 1) / n
        parts.append(Part(f"Wall{k}", "cylinder", [d, d, h], [0, 0, z0 + h / 2], color=white, finish="glossy",
                          material="ceramic", thin_walled=True))
    parts += [
        Part("Bowl", "cylinder", [D - 2 * t, D - 2 * t, 0.002], [0, 0, H - 0.001], color="#E7E5DD", finish="matte",
             collision=False, bevel=0),
        Part("Pestle", "cylinder", [0.03, 0.03, 0.15], [0.045, 0.0, H + 0.005], color=white, finish="glossy",
             rotation=[0.0, 60.0, 0.0], material="ceramic"),
    ]
    return Product(slug="mortar_and_pestle", name="乳鉢と乳棒（磁器・外径 150mm）", shape_class="assembly",
                   category="household", dims=Dimensions(0.1305, 0.1925, depth=D), mass_kg=0.9,
                   static=False, material="ceramic",
                   description="形は調剤薬局で錠剤を砕いたり散剤を混ぜたりする一般的な白い磁器の乳鉢（外径 150 mm・高さ 75 mm）"
                               "と、立てかけた乳棒（長さ 150 mm）で、寸法・質量は代表値。乳鉢の内側は段の付いた輪で近似。",
                   tags=["乳鉢", "乳棒", "すり鉢", "調剤器具", *SUPPLY_TAGS, "mortar and pestle", "pharmacy mortar"],
                   photos=[], colors=Colors(label_base=white), images=[], parts=parts)


def sharps_container() -> Product:
    W, D, H = 0.20, 0.13, 0.22
    yellow = "#F2C230"
    lb = Canvas(160, 130, None, yellow, 13701)
    lb.gradient(0, 0, 160, 130, "#F7D25A", "#EDB81F")
    lb.rect(10, 10, 150, 120, fill=WHITE, outline="#B3261E", width=2, radius=4)
    lb.ellipse(55, 18, 105, 62, outline="#B3261E", width=3)  # バイオハザードの代わりの注意の丸
    lb.text(80, 40, "!", 30, "#B3261E", 900)
    lb.text(80, 76, "使用済みの注射針", 14, "#B3261E", 900)
    lb.text(80, 96, "専用の廃棄容器", 12, INK, 800)
    lb.text(80, 112, "8分目まで入れたら薬局へ", 9, INK, 700)
    label = _face(lb.array(), "plastic", 13701, 0.6, 4)
    parts = [
        Part("Body", "box", [W, D, H - 0.03], [0, 0, (H - 0.03) / 2], color=yellow, finish="plastic",
             material="plastic", bevel=0.006),
        Part("Lid", "box", [W + 0.004, D + 0.004, 0.03], [0, 0, H - 0.015], color="#E53935", finish="plastic",
             material="plastic", bevel=0.004),
        _box("Opening", (0.07, 0.03, 0.002), (0.03, -0.01, H + 0.001), "#2B2E31", "matte", collision=False),
        _box("Label", (0.16, 0.002, 0.13), (0, -D / 2 - 0.001, 0.09), WHITE, "matte", {"front": 0},
             collision=False),
    ]
    return Product(slug="sharps_container", name="注射針の廃棄容器 3L", shape_class="assembly", category="household",
                   dims=Dimensions(H + 0.002, W + 0.004, depth=D + 0.004), mass_kg=0.35, static=False,
                   material="plastic",
                   description="形は在宅の自己注射で使った針を集める一般的な黄色の廃棄容器（幅 200 mm・奥行き 130 mm・高さ 220 mm、"
                               "赤いふたに投入口、前に注意のラベル）で、寸法・質量は代表値。ラベルの文字は架空。",
                   tags=["廃棄容器", "注射針", "針捨て", "医療廃棄物", *SUPPLY_TAGS, "sharps container",
                         "needle disposal box"], photos=[],
                   colors=Colors(label_base=yellow), images=[label], parts=parts)


PRODUCTS: dict[str, callable] = {f.__name__: f for f in (
    ptp_medicine_box, powder_stock_bottle, syrup_dosing_bottle, ointment_jar, suppository_box, inhaler_box,
    sachet_paper_roll, mortar_and_pestle, sharps_container, alcohol_swab_box, disposable_gloves_box,
    compress_patch_bag)}
