"""架空の商品のデザイン: 日用品（洗剤・掃除・台所・紙製品）。

products.py と同じく、実在の商品名・ブランド名・ロゴ・商品写真は使わず、形と寸法は同じ種類の商品の一般的な値にする。
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product, label_canvas, revolve, top_canvas
from .forms import RevolveForm, _arc
from .paint import Canvas, edge_shade, finish, mix, trim_safe
from .products import INK, _box, _cyl, _face, seal_crimp

BOX_FACES = {"front": 0, "back": 1, "right": 2, "left": 3, "top": 4, "bottom": 5}


def _info(c: Canvas, x0: float, y0: float, x1: float, rows: list[tuple[str, str]], caution: str, size: float,
          color: str = INK, bg: str = "#FFFFFF") -> float:
    """家庭用品品質表示（表）と使用上の注意・架空の表記。下端 y [mm] を返す。"""
    y = c.table(x0, y0, x1, "", rows, size, color, bg)
    y = c.paragraph(x0, y + size * 0.6, x1, caution, size * 0.95, color, 400)
    return c.paragraph(x0, y + size * 0.4, x1, NOTICE, size * 0.9, color, 500)


def _pouch_img(c: Canvas, seed: int, shade: int = 20) -> np.ndarray:
    return trim_safe(edge_shade(finish(c.array(), "film", seed, 1.0), shade, 0.15))


# ---------------------------------------------------------------- 回転体（ボトル・ジャー）


def dish_soap_bottle() -> Product:
    R, H = 0.031, 0.180
    body = [(0.0, R * 0.88)] + _arc(0.0005, 0.006, R * 0.93, R, 8, "out")[1:]
    body += [(0.128, R)] + _arc(0.128, 0.150, R, 0.012, 24, "cos")[1:] + [(0.155, 0.012)]
    cap = [(0.155, 0.0155), (0.166, 0.0155), (0.168, 0.0125), (0.176, 0.0062), (H, 0.0048)]
    form = RevolveForm(body, cap, (0.012, 0.118), liquid_top=0.136)
    green, white = "#3E8E3A", "#FFFFFF"
    c = label_canvas(form, white, seed=1601)
    W, Hh = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, Hh, "#FFFBE0", "#F9E77A")
    c.rect(0, 0, W, 4, fill=green)
    c.rect(0, Hh - 4, W, Hh, fill=green)
    # 断面が楕円なので、文字は平らな正面（fx ± 20 mm）と裏面（bx ± 22 mm）に寄せる
    c.photo("lemon", fx - 19, 52, fx + 19, 86, shape="ellipse", feather=2, shadow=1.0, crop=(0.1, 0.05, 0.9, 0.95))
    c.text(fx, 12, "DISH WASHING LIQUID", 2.4, green, 700, spacing=0.3, max_w=38)
    c.text(fx, 22, "食器用洗剤", 7.6, INK, 900, max_w=40)
    c.rect(fx - 18, 30, fx + 18, 38, fill=green, radius=4)
    c.text(fx, 34, "レモンの香り", 4.0, white, 800)
    c.text(fx, 44, "油汚れに すばやく泡切れ", 3.0, green, 700, max_w=38)
    c.text(fx, 91, "中性  手肌にやさしい", 3.0, INK, 700)
    c.text(fx, 98, "240ml", 4.8, INK, 900)
    rows = [("品名", "台所用合成洗剤"), ("用途", "食器・調理用具用"), ("液性", "中性"),
            ("成分", "界面活性剤（16% アルキルエーテル硫酸エステルナトリウム、脂肪酸アルカノールアミド）、安定化剤、香料"),
            ("正味量", "240ml"), ("使用量の目安", "水 1L に対して 0.75ml")]
    caution = ("【使用方法】スポンジに適量を取り、泡立てて洗い、水でよくすすいでください。\n"
               "【使用上の注意】用途外に使わない。子供の手の届く所に置かない。目に入ったときは、すぐに水で洗い流す。"
               "手荒れが気になる方は炊事用手袋を使用する。")
    y = _info(c, bx - 22, 6, bx + 22, rows, caution, 1.9)
    c.rect(bx - 22, y + 2, bx + 2, y + 18, fill=white)
    c.barcode(bx - 21, y + 3, 22, 14)
    c.recycle(bx + 8, y + 9, 6.5, "プラ", INK, sub="容器")
    c.recycle(bx + 17, y + 9, 6.5, "プラ", INK, sub="キャップ")
    label = finish(c.array(), "film", 1601, 0.6)
    return Product(slug="dish_soap_bottle", name="食器用洗剤 レモンの香り 240ml", category="household",
                   mass_kg=0.27, capacity_ml=240, material="polyethylene (translucent)",
                   description="形は一般的な台所用洗剤のボトル（高さ 180 mm・胴径 62 mm、注ぎ口付きのキャップ）で、寸法・質量は代表値。"
                               "断面は実物に多い楕円（幅 62 mm・奥行き 37 mm）。容器は半透明のポリエチレンで、黄色い中身が透けて見える。",
                   tags=["食器用洗剤", "台所用洗剤", "洗剤", "レモン", "dish soap", "detergent"], photos=["lemon"],
                   colors=Colors(cap="#3E8E3A", label_base="#F4F4F0", liquid="#E8C41C"),
                   **revolve(form, label=label, depth=0.037, body_fill=None, liquid="#E8C41C"))


def kitchen_bleach_bottle() -> Product:
    R, H = 0.036, 0.230
    body = [(0.0, R * 0.90)] + _arc(0.0005, 0.007, R * 0.94, R, 8, "out")[1:]
    body += [(0.165, R)] + _arc(0.165, 0.195, R, 0.017, 24, "cos")[1:] + [(0.200, 0.017)]
    cap = [(0.200, 0.0195), (0.2275, 0.0195), (H, 0.0180)]
    form = RevolveForm(body, cap, (0.016, 0.158), liquid_top=0.172)
    blue, red, white, yellow = "#1F5AA6", "#D3302F", "#FFFFFF", "#FFE14D"
    c = label_canvas(form, white, seed=1611)
    W, Hh = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, Hh, "#FFFFFF", "#E3EEF9")
    c.rect(0, 0, W, 5, fill=blue)
    c.rect(0, Hh - 5, W, Hh, fill=blue)
    # 断面が楕円なので、文字は平らな正面（fx ± 22 mm）と裏面（bx ± 24 mm）に寄せる
    c.text(fx, 14, "KITCHEN BLEACH", 3.0, blue, 700, spacing=0.4, max_w=42)
    c.text(fx, 28, "台所用", 7.0, blue, 900)
    c.text(fx, 43, "漂白剤", 12.0, blue, 900)
    c.text(fx, 56, "除菌・漂白・消臭", 4.2, INK, 800, max_w=42)
    c.rect(fx - 21, 62, fx + 21, 70, fill=blue, radius=4)
    c.text(fx, 66, "ふきん・まな板・食器に", 3.1, white, 800, max_w=39)
    # 塩素系の製品に必要な表示（まぜるな危険）
    c.rect(fx - 21, 78, fx + 21, 104, fill=yellow, outline=red, width=1.0)
    c.text(fx, 87, "まぜるな危険", 6.0, red, 900, max_w=39)
    c.text(fx, 98, "塩素系", 6.0, INK, 900)
    c.text(fx, 111, "酸性タイプの製品と", 2.8, red, 700)
    c.text(fx, 115.5, "一緒に使う（まぜる）と", 2.8, red, 700)
    c.text(fx, 120, "有害な塩素ガスが出て危険", 2.8, red, 700)
    c.text(fx, 132, "600ml", 6.0, blue, 900)
    rows = [("品名", "台所用漂白剤"), ("成分", "次亜塩素酸ナトリウム（塩素系）、水酸化ナトリウム（アルカリ剤）、界面活性剤"),
            ("液性", "アルカリ性"), ("内容量", "600ml"), ("用途", "ふきん・まな板・食器・プラスチック容器の除菌と漂白")]
    caution = ("【使用方法】水 5L に対してキャップ 1 杯（約 25ml）を薄めて 2 分つけ置き、水でよくすすぐ。\n"
               "【使用上の注意】酸性タイプの製品・食酢・アルコールと一緒に使わない。換気をよくし、使用時は炊事用手袋を使う。"
               "金属製の容器・色柄物には使わない。目に入ったら、こすらずにすぐ水で 15 分以上洗い流し、医師に相談する。"
               "子供の手の届く所に置かない。")
    y = _info(c, bx - 24, 9, bx + 24, rows, caution, 2.1)
    c.rect(bx - 24, y + 2, bx + 2, y + 20, fill=white)
    c.barcode(bx - 23, y + 3, 24, 16)
    c.recycle(bx + 9, y + 10, 7, "プラ", INK, sub="容器")
    c.recycle(bx + 19, y + 10, 7, "プラ", INK, sub="キャップ")
    c.text(bx, y + 26, "まぜるな危険  塩素系", 3.0, red, 900)
    label = finish(c.array(), "film", 1611, 0.6)
    t = top_canvas(form, white, seed=1612)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FFFFFF", "#D9E5F2")
    t.ellipse(1.5, 1.5, d - 1.5, d - 1.5, outline="#9FB3C8", width=0.6)
    t.text(d / 2, d / 2 - 5, "押しながら", 3.6, blue, 800)
    t.text(d / 2, d / 2 + 1, "回す", 3.6, blue, 800)
    t.polygon([(d / 2 - 4, d / 2 + 7), (d / 2 + 4, d / 2 + 7), (d / 2 + 4, d / 2 + 5), (d / 2 + 7, d / 2 + 8.5),
               (d / 2 + 4, d / 2 + 12), (d / 2 + 4, d / 2 + 10), (d / 2 - 4, d / 2 + 10)], fill=blue)
    top = finish(t.array(), "film", 1612, 0.5)
    return Product(slug="kitchen_bleach_bottle", name="台所用漂白剤 600ml", category="household",
                   mass_kg=0.69, capacity_ml=600, material="HDPE (translucent)",
                   description="形は一般的な台所用漂白剤のボトル（高さ 230 mm・胴径 72 mm、押しながら回す安全キャップ）で、寸法・質量は代表値。"
                               "断面は実物に多い扁平な楕円（幅 72 mm・奥行き 43 mm）。取っ手は省略した。"
                               "容器は乳白の HDPE で、中身の液面がうっすら透けて見える。",
                   tags=["漂白剤", "台所用漂白剤", "塩素系", "除菌", "kitchen bleach", "bleach"], photos=[],
                   colors=Colors(cap="#F4F6F8", label_base="#F4F6F8", liquid="#EDEBC4"),
                   **revolve(form, label=label, top=top, depth=0.043, body_fill=None, liquid="#EDEBC4"))


def deodorizer_gel_jar() -> Product:
    R, H = 0.038, 0.105
    body = [(0.0, R * 0.93)] + _arc(0.0005, 0.005, R * 0.96, R, 8, "out")[1:]
    body += [(0.080, R)] + _arc(0.080, 0.084, R, R * 0.95, 6, "cos")[1:]
    cap = [(0.084, 0.040), (0.097, 0.040)] + _arc(0.097, H, 0.040, 0.030, 8, "out")[1:]
    form = RevolveForm(body, cap, (0.008, 0.048), liquid_top=0.074)
    blue, navy, white = "#8FD0EA", "#1E5A8C", "#FFFFFF"
    c = label_canvas(form, white, seed=1621)
    W, Hh = c.w_mm, c.h_mm
    fx, bx = 0.75 * W, 0.25 * W
    c.gradient(0, 0, W, Hh, "#FFFFFF", "#D5EEF8")
    c.rect(0, 0, W, 3, fill=navy)
    c.rect(0, Hh - 3, W, Hh, fill=navy)
    c.pattern(0, 3, W, Hh - 3, "dots", mix(blue, white, 0.55), 5, 0.6)
    c.rect(fx - 34, 4.5, fx + 34, 30, fill=white, radius=4)
    c.text(fx, 9.5, "置き型消臭剤  お部屋用", 3.4, navy, 800)
    c.text(fx, 18.5, "消臭ゲル", 8.5, navy, 900)
    c.text(fx, 26.5, "せっけんの香り  約 1.5〜2 か月", 3.0, INK, 700)
    c.text(fx, Hh - 5.2, "400g", 3.6, navy, 900)
    c.text(fx - 48, 20, "DEODORIZER", 3.0, navy, 700, spacing=0.4)
    c.text(fx + 48, 20, "GEL", 3.4, navy, 800, spacing=0.4)
    rows = [("品名", "消臭芳香剤（ゲルタイプ）"), ("成分", "植物抽出消臭剤、香料、ゲル化剤、防腐剤"),
            ("内容量", "400g"), ("使用場所", "居間・寝室・玄関")]
    caution = ("【使用方法】キャップを外し、フィルムをはがしてからキャップを付け直す。\n"
               "【注意】子供やペットの手の届かない所に置く。食べられません。万一飲み込んだときは水を飲ませ、医師に相談する。")
    _info(c, bx - 34, 4.5, bx + 34, rows, caution, 1.7)
    c.rect(0.5 * W - 14, 5, 0.5 * W + 14, 25, fill=white)
    c.barcode(0.5 * W - 12, 7, 24, 16)
    c.recycle(0.5 * W - 7, 33, 6.5, "プラ", navy, sub="容器")
    c.recycle(0.5 * W + 7, 33, 6.5, "プラ", navy, sub="キャップ")
    label = finish(c.array(), "film", 1621, 0.5)
    t = top_canvas(form, white, seed=1622)
    d = t.w_mm
    t.gradient(0, 0, d, d, "#FFFFFF", "#E2EDF4")
    t.ellipse(1.5, 1.5, d - 1.5, d - 1.5, outline="#A9BCCB", width=0.6)
    for k in range(-3, 4):  # 香りの出るスリット
        y = d / 2 + k * 6.5
        half = (max(0.0, (d / 2 - 9) ** 2 - (k * 6.5) ** 2)) ** 0.5
        if half > 6:
            t.rect(d / 2 - half, y - 1.2, d / 2 + half, y + 1.2, fill="#B8CCDA", radius=1.2)
    t.rect(d / 2 - 15, d / 2 - 4, d / 2 + 15, d / 2 + 4, fill=white, radius=2)
    t.text(d / 2, d / 2, "消臭ゲル", 4.6, navy, 900)
    top = finish(t.array(), "film", 1622, 0.4)
    return Product(slug="deodorizer_gel_jar", name="置き型消臭剤 せっけんの香り 400g", category="household",
                   mass_kg=0.47, material="clear plastic",
                   description="形は一般的な置き型のゲル消臭剤（高さ 105 mm・胴径 80 mm、香りの出るスリット付きのキャップ）で、寸法・質量は代表値。"
                               "透明な容器の中のゲルを色付きの中身として表した。",
                   tags=["消臭剤", "置き型", "芳香剤", "ゲル", "deodorizer", "air freshener"], photos=[],
                   colors=Colors(cap="#F7F9FA", liquid=blue, label_base="#D5EEF8"),
                   **revolve(form, label=label, top=top, body_fill=None, liquid=blue))


# ---------------------------------------------------------------- 袋（パウチ）


def _steps(c: Canvas, x0: float, y0: float, x1: float, title: str, steps: list[str], color: str, size: float) -> float:
    """番号付きの手順（使い方）。下端 y [mm] を返す。"""
    c.text(x0, y0 + size * 0.7, title, size * 1.25, color, 900, anchor="lm")
    n = len(steps)
    gap = 2.0
    w = (x1 - x0 - gap * (n - 1)) / n
    top = y0 + size * 2.0
    h = size * 7.5
    for k, s in enumerate(steps):
        bx0 = x0 + k * (w + gap)
        c.rect(bx0, top, bx0 + w, top + h, fill="#FFFFFF", outline=color, width=0.5, radius=2)
        c.ellipse(bx0 + 1.5, top + 1.5, bx0 + 1.5 + size * 2.2, top + 1.5 + size * 2.2, fill=color)
        c.text(bx0 + 1.5 + size * 1.1, top + 1.5 + size * 1.1, str(k + 1), size * 1.4, "#FFFFFF", 900)
        c.paragraph(bx0 + 1.5, top + size * 3.2, bx0 + w - 1.5, s, size, INK, 600)
    return top + h


def laundry_detergent_refill() -> Product:
    W, H = 160.0, 260.0
    lilac, purple, white = "#D9CCEF", "#5B3F8C", "#FFFFFF"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 8, white, seed=seed)
        c.gradient(0, 0, W, H, "#FFFFFF", lilac)
        seal_crimp(c, 0, 0, W, 12, "#B9A6DD", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#9B83C8", 1.6)
        c.rect(0, 12, W, 13.5, fill=purple)
        c.rect(0, H - 13.5, W, H - 12, fill=purple)
        return c

    # 表: 商品名・香り・内容量だけ
    c = base(1631)
    c.rect(W - 38, 15, W - 8, 30, fill=purple, radius=3)
    c.text(W - 23, 22.5, "注ぎ口", 4.0, white, 800)
    c.polygon([(W - 30, 30), (W - 16, 30), (W - 23, 36)], fill=purple)
    c.text(14, 22, "つめかえ用", 6.0, purple, 900, anchor="lm")
    c.text(W / 2, 50, "液体洗濯洗剤", 15, INK, 900, max_w=W - 20)
    c.text(W / 2, 66, "LAUNDRY DETERGENT", 5.0, purple, 700, spacing=1.2)
    c.rect(W / 2 - 46, 74, W / 2 + 46, 86, fill=purple, radius=6)
    c.text(W / 2, 80, "やさしいフローラルの香り", 5.6, white, 800)
    c.photo("lavender", 14, 94, W - 14, 186, shape="round", radius=8, feather=3, crop=(0.0, 0.2, 1.0, 0.85))
    c.ellipse(W - 56, 166, W - 10, 212, fill=white, outline=purple, width=1.0)
    c.text(W - 33, 181, "720g", 8.0, purple, 900)
    c.text(W - 33, 193, "約 1.5 倍", 4.4, INK, 700)
    c.text(W - 33, 201, "（本体比）", 3.2, INK, 500)
    c.text(14, 200, "部屋干しにも", 6.0, purple, 900, anchor="lm")
    c.text(14, 211, "抗菌  消臭", 6.0, purple, 900, anchor="lm")
    for k, (a, b) in enumerate((("すすぎ", "1回OK"), ("ドラム式", "にも"), ("濃縮", "タイプ"))):
        x = 30 + k * 50
        c.ellipse(x - 17, 220, x + 17, 242, fill=white, outline=purple, width=0.8)
        c.text(x, 227.5, a, 4.0, purple, 800)
        c.text(x, 235, b, 4.0, purple, 800)
    front = _pouch_img(c, 1631)

    # 裏: 使い方・表示・バーコード
    b = base(1632)
    b.text(W / 2, 24, "液体洗濯洗剤  つめかえ用  720g", 5.0, purple, 900)
    y = _steps(b, 12, 32, W - 12, "つめかえ方",
               ["注ぎ口の上を切り取る。", "本体の注ぎ口に差し込み、ゆっくり注ぐ。", "袋を少しずつ傾け、最後まで注ぎ切る。"],
               purple, 4.4)
    b.rect(10, y + 5, W - 10, H - 18, fill=white, radius=3)
    rows = [("品名", "洗濯用合成洗剤"), ("用途", "綿・麻・合成繊維用"), ("液性", "中性"),
            ("成分", "界面活性剤（35% ポリオキシエチレンアルキルエーテル）、安定化剤、酵素、香料"), ("正味量", "720g"),
            ("使用量の目安", "水 30L に 20g（ドラム式は水 15L に 10g）")]
    caution = ("【使用上の注意】用途外に使わない。子供の手の届く所に置かない。認知症の方などの誤飲を防ぐため、置き場所に注意する。"
               "詰め替えるときは同じ種類の本体容器に入れ、他の製品と混ぜない。\n"
               "【応急処置】目に入ったら、こすらずにすぐ水で 15 分以上洗い流し、眼科医に相談する。飲み込んだときは水を飲ませるなどの処置をし、医師に相談する。")
    yb = _info(b, 14, y + 8, W - 14, rows, caution, 4.4)
    b.rect(14, yb + 3, 56, yb + 30, fill=white)
    b.barcode(16, yb + 5, 38, 23)
    b.recycle(76, yb + 15, 11, "プラ", purple, sub="袋")
    assert yb + 30 < H - 18, yb
    back = _pouch_img(b, 1632)
    return Product(slug="laundry_detergent_refill", name="液体洗濯洗剤 つめかえ用 720g", shape_class="pouch",
                   category="household", dims=Dimensions(0.26, 0.16, depth=0.06), mass_kg=0.75, material="film",
                   description="形は一般的な詰め替え用のスタンドパウチ（高さ 260 mm・幅 160 mm・厚さ 60 mm）で、寸法・質量は代表値。"
                               "底のマチと注ぎ口の突起は省略し、ピロー袋の形で近似した。表に商品名と内容量、裏に使い方と表示。",
                   tags=["洗濯洗剤", "詰め替え", "液体洗剤", "パウチ", "laundry detergent", "refill"], photos=["lavender"],
                   colors=Colors(label_base=lilac), images=[front, back], faces={"front": 0, "back": 1})


def trash_bags_45l() -> Product:
    L, Wd = 260.0, 190.0  # 寝かせた袋。画像は横長（左右がシール）
    green, white, mint = "#2F8F5B", "#FFFFFF", "#DDF1E4"

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 7, white, seed=seed)
        c.gradient(0, 0, L, Wd, "#F7FCF8", mint)
        seal_crimp(c, 0, 0, 9, Wd, "#CFE9D8", 1.4, vertical=True)
        seal_crimp(c, L - 9, 0, L, Wd, "#B9DFC6", 1.4, vertical=True)
        c.rect(9, 0, L - 9, 26, fill=green)
        c.text(L / 2, 13, "家庭用  ポリ袋  GARBAGE BAGS", 6.0, white, 800, spacing=0.5)
        return c

    def bag(c: Canvas, x: float, y: float, s: float) -> None:
        for pts in ([(x - 21, y), (x + 21, y), (x + 25, y + 60), (x - 25, y + 60)],
                    [(x - 17, y), (x - 7, y - 10), (x, y)], [(x, y), (x + 7, y - 10), (x + 17, y)]):
            pts = [(x + (px - x) * s, y + (py - y) * s) for px, py in pts]
            c.polygon(pts, fill="#FFFFFF")
            c.line(pts + pts[:1], green, 1.0)

    c = base(1641)
    c.text(22, 56, "ゴミ袋", 26, green, 900, anchor="lm")
    c.rect(124, 40, 190, 72, fill=green, radius=6)
    c.text(157, 56, "45L", 20, white, 900)
    c.text(22, 90, "半透明  10枚入", 10, INK, 800, anchor="lm")
    c.text(22, 106, "厚さ 0.025mm  丈夫で破れにくい", 6.0, green, 700, anchor="lm")
    bag(c, 222, 48, 1.0)
    c.text(222, 80, "650×800", 4.6, green, 800)
    c.text(222, 88, "mm", 3.6, green, 700)
    for k, (a, b2) in enumerate((("においが", "もれにくい"), ("口が", "しばりやすい"), ("中身が", "見える"))):
        x = 50 + k * 80
        c.rect(x - 34, 124, x + 34, 158, fill=white, outline=green, width=0.8, radius=6)
        c.text(x, 135, a, 6.0, green, 800)
        c.text(x, 147, b2, 6.0, green, 800)
    c.text(L / 2, 172, "地域の分別ルールにあわせてお使いください", 4.4, INK, 600)
    front = _pouch_img(c, 1641, 18)

    b = base(1642)
    b.text(20, 38, "ゴミ袋 45L 半透明 10枚入", 6.0, green, 900, anchor="lm")
    rows = [("品名", "ポリエチレン製ゴミ袋"), ("材質", "高密度ポリエチレン"), ("寸法", "650 × 800 mm（45L）"),
            ("厚さ", "0.025 mm"), ("入り数", "10枚"), ("耐冷温度", "-30℃")]
    caution = ("【使い方】袋を 1 枚ずつ取り出し、口を広げてゴミを入れ、口をしっかり結ぶ。\n"
               "【使用上の注意】火のそばに置かない。とがった物・熱い物を入れると破れることがある。"
               "乳幼児の手の届かない所に保管する（頭からかぶると窒息のおそれ）。ゴミの出し方は各自治体のルールに従う。")
    yb = _info(b, 20, 48, 164, rows, caution, 4.8)
    assert yb < Wd - 8, yb
    b.rect(172, 50, L - 18, 92, fill=white)
    b.barcode(176, 52, 62, 36)
    b.recycle(192, 116, 13, "プラ", green, sub="外袋")
    bag(b, 232, 108, 0.6)
    b.text(L - 50, 160, "半透明", 6.0, INK, 800)
    back = _pouch_img(b, 1642, 18)
    return Product(slug="trash_bags_45l", name="ゴミ袋 45L 半透明 10枚入", shape_class="pouch", category="household",
                   dims=Dimensions(0.26, 0.19, depth=0.015), mass_kg=0.2, material="film", orientation="lying",
                   description="形は一般的なポリ袋の外袋入りパッケージ（260 × 190 mm、厚さ 15 mm）で、寸法・質量は代表値。"
                               "表に商品名と容量、裏に表示と注意。",
                   tags=["ゴミ袋", "ポリ袋", "45L", "日用品", "garbage bags", "trash bags"], photos=[],
                   colors=Colors(label_base=mint), images=[front, back], faces={"front": 0, "back": 1})


def rubber_gloves() -> Product:
    W, H = 150.0, 300.0
    pink, rose, white, sky = "#F08AA8", "#B8336A", "#FFFFFF", "#E8F3FB"

    def base(seed: int) -> Canvas:
        c = Canvas(W, H, 6, white, seed=seed)
        c.gradient(0, 0, W, H, "#FFFFFF", "#FDE3EB")
        seal_crimp(c, 0, 0, W, 12, "#F7C3D3", 1.6)
        seal_crimp(c, 0, H - 12, W, H, "#EFA9BF", 1.6)
        # つり下げ用の台紙と穴（中央なので表裏で同じ位置）
        c.rect(0, 12, W, 40, fill=rose)
        c.rect(W / 2 - 14, 18, W / 2 + 14, 27, fill="#5A1A33", radius=4.5)
        return c

    def glove(c: Canvas, cx: float, py0: float, s: float) -> None:
        def P(x, y):
            return (cx + (x - cx) * s, py0 + (y - py0) * s)

        px0 = cx - 24
        for dx, top in ((-18, -32), (-6, -40), (6, -38), (18, -28)):
            (x0, y0), (x1, y1) = P(cx + dx - 5, py0 + top), P(cx + dx + 5, py0 + 6)
            c.rect(x0, y0, x1, y1, fill=pink, radius=5 * s)
        (x0, y0), (x1, y1) = P(px0, py0), P(px0 + 48, py0 + 50)
        c.rect(x0, y0, x1, y1, fill=pink, radius=8 * s)
        c.polygon([P(px0 + 2, py0 + 30), P(px0 - 16, py0 + 6), P(px0 - 22, py0 + 10), P(px0 - 6, py0 + 44)], fill=pink)
        (x0, y0), (x1, y1) = P(px0 - 24, py0 + 3), P(px0 - 12, py0 + 15)
        c.ellipse(x0, y0, x1, y1, fill=pink)
        (x0, y0), (x1, y1) = P(px0 - 2, py0 + 48), P(px0 + 50, py0 + 76)
        c.rect(x0, y0, x1, y1, fill=mix(pink, rose, 0.25), radius=3 * s)
        for k in range(4):
            c.line([P(px0 + 1, py0 + 54 + k * 5), P(px0 + 47, py0 + 54 + k * 5)], mix(pink, white, 0.4), 0.6)

    c = base(1651)
    c.text(W / 2, 34, "RUBBER GLOVES", 4.6, white, 700, spacing=1.0)
    c.text(W / 2, 58, "ゴム手袋", 18, rose, 900)
    c.text(W / 2, 75, "天然ゴム  内側すべり止め", 5.0, INK, 700)
    c.ellipse(W / 2 - 54, 86, W / 2 + 54, 226, fill=sky)
    glove(c, W / 2, 136, 1.05)
    c.ellipse(W - 54, 200, W - 12, 242, fill=rose)
    c.text(W - 33, 215, "M", 15, white, 900)
    c.text(W - 33, 231, "サイズ", 4.8, white, 800)
    c.text(14, 238, "1双入", 9.0, rose, 900, anchor="lm")
    for k, t in enumerate(("指先  すべり止め加工", "内側  植毛加工でムレにくい", "長めの袖口  水が入りにくい")):
        c.rect(12, 252 + k * 10, 15.5, 255.5 + k * 10, fill=rose)
        c.text(19, 253.8 + k * 10, t, 4.2, INK, 700, anchor="lm")
    front = _pouch_img(c, 1651)

    b = base(1652)
    b.text(W / 2, 34, "ゴム手袋  Mサイズ  1双", 5.0, white, 800)
    b.text(14, 52, "サイズの目安（手のひらまわり）", 5.0, rose, 900, anchor="lm")
    for k, (sz, rng) in enumerate((("S", "17〜19cm"), ("M", "19〜21cm"), ("L", "21〜23cm"))):
        x0 = 14 + k * 41
        on = sz == "M"
        b.rect(x0, 60, x0 + 38, 84, fill=rose if on else white, outline=rose, width=0.6, radius=3)
        b.text(x0 + 19, 68, sz, 7.0, white if on else rose, 900)
        b.text(x0 + 19, 79, rng, 4.0, white if on else INK, 700)
    glove(b, 40, 120, 0.55)
    b.line([(22, 135), (58, 135)], rose, 0.8)
    b.paragraph(70, 100, W - 14, "親指の付け根を通るように、手のひらのまわりをはかります。", 4.0, INK, 600)
    b.rect(10, 168, W - 10, H - 16, fill=white, radius=3)
    rows = [("品名", "家庭用手袋"), ("材質", "天然ゴム（内面：植毛加工）"), ("サイズ", "M（手のひらまわり 19〜21cm）"),
            ("耐熱温度", "70℃"), ("耐冷温度", "-20℃")]
    caution = ("【使用上の注意】天然ゴムでまれにかゆみ・かぶれ等のアレルギーが起こることがある。異常を感じたら使用を中止する。"
               "火のそばに置かない。塩素系の漂白剤・油・溶剤に長時間ふれると傷みが早くなる。使用後は水洗いし、陰干しする。")
    yb = _info(b, 14, 172, W - 14, rows, caution, 4.2)
    b.rect(14, yb + 3, 54, yb + 29, fill=white)
    b.barcode(16, yb + 5, 36, 22)
    b.recycle(72, yb + 14, 11, "プラ", rose, sub="袋")
    assert yb + 29 < H - 16, yb
    back = _pouch_img(b, 1652)
    return Product(slug="rubber_gloves", name="ゴム手袋 Mサイズ 1双", shape_class="pouch", category="household",
                   dims=Dimensions(0.30, 0.15, depth=0.02), mass_kg=0.07, material="film",
                   description="形は一般的な家庭用ゴム手袋の袋入りパッケージ（高さ 300 mm・幅 150 mm・厚さ 20 mm、上部につり下げ穴）で、"
                               "寸法・質量は代表値。つり下げ穴は絵で表した。表に商品名とサイズ、裏にサイズの目安と表示。",
                   tags=["ゴム手袋", "手袋", "炊事用", "掃除", "rubber gloves", "gloves"], photos=[],
                   colors=Colors(label_base="#FDE3EB"), images=[front, back], faces={"front": 0, "back": 1})


def wet_wipes_pack() -> Product:
    L, Wd, D = 200.0, 120.0, 0.045  # 寝かせた袋。画像は横長（左右がシール）
    teal, white, aqua = "#1E8C9A", "#FFFFFF", "#D3EEF1"
    LW, LD = 80.0, 44.0  # ふたの大きさ [mm]（中央）

    def base(seed: int) -> Canvas:
        c = Canvas(L, Wd, 9, white, seed=seed)
        c.gradient(0, 0, L, Wd, "#F4FBFC", aqua)
        c.pattern(0, 0, L, Wd, "waves", mix(aqua, teal, 0.15), 8, 0.5)
        seal_crimp(c, 0, 0, 8, Wd, "#C5E6EA", 1.2, vertical=True)
        seal_crimp(c, L - 8, 0, L, Wd, "#A9D9DF", 1.2, vertical=True)
        return c

    c = base(1661)
    # ふたは立体の部品。下の袋には取り出し口の縁だけ描く
    c.rect(L / 2 - LW / 2 - 2, Wd / 2 - LD / 2 - 2, L / 2 + LW / 2 + 2, Wd / 2 + LD / 2 + 2, fill="#C9D3D6", radius=8)
    c.text(16, 14, "WET WIPES", 5.0, teal, 800, anchor="lm", spacing=1.0)
    c.rect(L - 52, 8, L - 14, 22, fill=teal, radius=7)
    c.text(L - 33, 15, "80枚入", 6.0, white, 900)
    c.text(L / 2, 25, "ノンアルコール", 5.0, teal, 900)
    for k, t in enumerate(("手・口", "身のまわり", "水分 99%")):
        c.ellipse(14, 44 + k * 13, 46, 55 + k * 13, fill=white, outline=teal, width=0.5)
        c.text(30, 49.5 + k * 13, t, 3.6, teal, 800)
    c.text(L - 31, 52, "厚手", 9.0, teal, 900)
    c.text(L - 31, 66, "ふんわり", 4.4, INK, 700)
    c.text(L / 2, 96, "ウェットティッシュ", 11, teal, 900, max_w=L - 40)
    c.text(L / 2, 108, "150 × 200 mm  80枚", 4.4, INK, 700)
    front = _pouch_img(c, 1661, 16)

    b = base(1662)
    b.text(16, 14, "ウェットティッシュ  ノンアルコール  80枚入", 4.6, teal, 900, anchor="lm")
    rows = [("品名", "ウェットティシュ"), ("材質", "ポリエステル・レーヨン系不織布"),
            ("成分", "水、プロピレングリコール、BG、塩化セチルピリジニウム"), ("寸法・枚数", "150 × 200 mm・80枚")]
    caution = ("【使い方】ふたを開け、シールをはがして 1 枚ずつ取り出す。使用後はふたをしっかり閉める。\n"
               "【使用上の注意】トイレに流さない。肌に異常が出たら使用を中止する。直射日光・高温の所に置かない。")
    y = b.table(14, 24, 112, "", rows, 3.6, INK, white)
    y2 = b.paragraph(118, 24, L - 14, caution, 3.6, INK, 400)
    y3 = b.paragraph(118, y2 + 1.5, L - 14, NOTICE, 3.2, INK, 500)
    b.rect(14, y + 4, 56, y + 30, fill=white)
    b.barcode(16, y + 6, 38, 22)
    b.recycle(72, y + 16, 9, "プラ", teal, sub="袋")
    b.recycle(90, y + 16, 9, "プラ", teal, sub="ふた")
    assert y + 30 < Wd - 4 and y3 < Wd - 4, (y, y3)
    back = _pouch_img(b, 1662, 16)

    # ふたの上面（画像の下が正面 -Y）
    t = Canvas(LW, LD, 12, white, seed=1663)
    t.gradient(0, 0, LW, LD, "#FFFFFF", "#E4ECEF")
    t.rect(1.2, 1.2, LW - 1.2, LD - 1.2, outline="#C5D2D6", width=0.5, radius=6)
    t.text(LW / 2, LD / 2 - 3, "ウェットティッシュ", 6.0, teal, 900, max_w=LW - 10)
    t.text(LW / 2, LD / 2 + 7, "OPEN  ▼", 3.2, teal, 800, spacing=0.6)
    lid = finish(t.array(), "film", 1663, 0.4)

    # 袋の上面は中央で z = D。ふたの角（x ±40, y ±22 mm）では約 6 mm 低い。
    # 底を角に合わせ、中央は袋がふたにめり込む（厚さ 9 mm なので上面から袋は出ない）
    z0 = D - 0.0065
    parts = [_box("Lid", (LW / 1000, LD / 1000, 0.009), (0, 0, z0 + 0.0045), "#F2F5F6", "plastic",
                  faces={"top": 2}),
             _box("LidTab", (0.026, 0.006, 0.003), (0, -(LD / 2000 + 0.002), z0 + 0.0075), "#E2E9EB", "plastic")]
    return Product(slug="wet_wipes_pack", name="ウェットティッシュ ノンアルコール 80枚", shape_class="pouch",
                   category="household", dims=Dimensions(0.20, 0.12, depth=D), mass_kg=0.42, material="film",
                   orientation="lying",
                   description="形は一般的なふた付きのウェットティッシュの袋（200 × 120 mm、厚さ 45 mm、上面中央にプラスチックのふた）で、"
                               "寸法・質量は代表値。表に商品名と枚数、裏に使い方と表示。",
                   tags=["ウェットティッシュ", "ノンアルコール", "除菌", "日用品", "wet wipes", "wipes"], photos=[],
                   colors=Colors(label_base=aqua), images=[front, back, lid], faces={"front": 0, "back": 1},
                   parts=parts)


# ---------------------------------------------------------------- 箱


def _roll_box(*, W: float, D: float, H: float, seed: int, base: str, band: str, accent: str, title: str, size_txt: str,
              en: str, rows: list[tuple[str, str]], caution: str, front_extra) -> list:
    """ラップ・アルミホイルの細長い箱の 6 面。"""
    s = 1900 / W

    def face(w: float, h: float, k: int) -> Canvas:
        f = Canvas(w, h, s, base, seed + k)
        f.gradient(0, 0, w, h, mix(base, "#FFFFFF", 0.4), base)
        f.rect(0, 0, w, 2.5, fill=band)
        f.rect(0, h - 2.5, w, h, fill=band)
        return f

    fr = face(W, H, 0)
    fr.text(12, H * 0.42, title, H * 0.36, band, 900, anchor="lm")
    fr.text(12, H * 0.78, en, H * 0.12, accent, 700, anchor="lm", spacing=0.8)
    fr.rect(W - 92, 7, W - 10, H - 7, fill=band, radius=4)
    fr.text(W - 51, H / 2, size_txt, H * 0.30, "#FFFFFF", 900, max_w=76)
    front_extra(fr)
    bk = face(W, H, 1)
    y = bk.table(6, 5, 106, "", rows, 2.5, INK, "#FFFFFF")
    assert y < H - 3, y
    bk.paragraph(112, 5, W - 70, caution, 2.4, INK, 400)
    bk.paragraph(112, H - 9, W - 70, NOTICE, 2.1, INK, 500)
    bk.rect(W - 66, 5, W - 30, H - 5, fill="#FFFFFF")
    bk.barcode(W - 64, 7, 32, H - 14)
    bk.recycle(W - 16, H / 2, 10, "紙", band, sub="箱")
    sides = []
    for k in (2, 3):
        sd = face(D, H, k)
        sd.text(D / 2, H * 0.38, title, D * 0.14, band, 900, max_w=D - 6)
        sd.text(D / 2, H * 0.68, size_txt, D * 0.13, accent, 800, max_w=D - 6)
        sides.append(sd)
    tp = face(W, D, 4)
    tp.rect(8, 6, W - 8, D - 10, outline=mix(band, "#FFFFFF", 0.3), width=0.5, radius=2)
    tp.text(W / 2, D * 0.38, f"{title}  {size_txt}", D * 0.2, band, 900)
    tp.text(W / 2, D * 0.62, "ふたを閉めて、刃の上から押さえて切ってください", D * 0.09, INK, 700)
    bt = face(W, D, 5)
    bt.text(W / 2, D * 0.4, "刃に注意  けがをしないよう、刃に触れないでください", D * 0.1, "#C0392B", 800)
    bt.text(W / 2, D * 0.62, NOTICE, D * 0.08, INK, 500)
    return [_face(f.array(), "paper", seed + 10 + i) for i, f in enumerate((fr, bk, *sides, tp, bt))]


def _blade(W: float, D: float, H: float) -> Part:
    """前面の上端に沿った金属の刃（mm で受け取る）。前面から 0.2 mm 離して z-fighting を避ける。"""
    t, h = 0.0012, 0.006
    return Part("Blade", "box", [(W - 14) / 1000, t, h], [0, -(D / 2000 + 0.0002 + t / 2), H / 1000 - h / 2 - 0.0005],
                color="#B4BAC0", finish="metal")


def food_wrap_box() -> Product:
    W, D, H = 316.0, 50.0, 50.0
    green = "#2F8F4E"

    def extra(f: Canvas):
        f.rect(150, 10, 212, 22, fill="#E54B4B", radius=6)
        f.text(181, 16, "電子レンジ OK", 5.0, "#FFFFFF", 800)
        f.text(181, 30, "冷凍・冷蔵にも", 5.0, green, 800)
        f.text(181, 39, "耐熱 140℃", 5.0, INK, 700)

    rows = [("品名", "食品用ラップフィルム"), ("原料樹脂", "ポリ塩化ビニリデン"), ("添加剤", "脂肪酸誘導体（柔軟剤）"),
            ("耐熱温度", "140℃"), ("耐冷温度", "−60℃"), ("寸法", "30cm × 20m")]
    caution = ("【使用方法】必要な長さを引き出し、ふたを閉めて刃で切る。\n"
               "【注意】油分の多い食品に直接触れた状態で電子レンジにかけない。オーブン・グリルでは使用しない。")
    imgs = _roll_box(W=W, D=D, H=H, seed=1671, base="#F4FAF5", band=green, accent="#6BAF7E", title="食品用ラップ",
                     size_txt="30cm×20m", en="FOOD WRAP", rows=rows, caution=caution, front_extra=extra)
    return Product(slug="food_wrap_box", name="食品用ラップ 30cm×20m", shape_class="box", category="household",
                   dims=Dimensions(0.05, 0.316, depth=0.05), mass_kg=0.22, material="paper",
                   description="形は一般的な食品用ラップの化粧箱（幅 316 mm・奥行き 50 mm・高さ 50 mm、上面のふたと刃）で、寸法・質量は代表値。"
                               "刃は金属の細長い部品、ふたは絵で表した。",
                   tags=["ラップ", "食品用ラップ", "台所用品", "food wrap", "plastic wrap", "kitchen"], photos=[],
                   colors=Colors(label_base="#F4FAF5"), images=imgs, faces=BOX_FACES,
                   parts=[_blade(W, D, H)])


def aluminum_foil_box() -> Product:
    W, D, H = 265.0, 40.0, 40.0
    blue = "#24508F"

    def extra(f: Canvas):
        f.gradient(120, 9, 168, 31, "#E9ECEF", "#A9B0B7")
        f.rect(120, 9, 168, 31, outline="#7D858D", width=0.4)
        f.text(144, 20, "片面つや消し", 4.0, blue, 800)
        f.text(108, 35, "焼く・包む・ふたをする", 3.2, INK, 700, anchor="lm")

    rows = [("品名", "アルミニウムはく"), ("材質", "アルミニウム"), ("厚さ", "11 μm"), ("寸法", "25cm × 8m")]
    caution = ("【注意】電子レンジでは使用しない（火花が出ることがあります）。"
               "直火・オーブントースターの熱源に触れないようにする。酸・塩分の多い食品の長期保存には使わない。")
    imgs = _roll_box(W=W, D=D, H=H, seed=1731, base="#EEF2F7", band=blue, accent="#6F8DB8", title="アルミホイル",
                     size_txt="25cm×8m", en="ALUMINUM FOIL", rows=rows, caution=caution, front_extra=extra)
    return Product(slug="aluminum_foil_box", name="アルミホイル 25cm×8m", shape_class="box", category="household",
                   dims=Dimensions(0.04, 0.265, depth=0.04), mass_kg=0.12, material="paper",
                   description="形は一般的なアルミホイルの化粧箱（幅 265 mm・奥行き 40 mm・高さ 40 mm、上面のふたと刃）で、寸法・質量は代表値。"
                               "刃は金属の細長い部品、ふたは絵で表した。",
                   tags=["アルミホイル", "ホイル", "台所用品", "aluminum foil", "foil", "kitchen"], photos=[],
                   colors=Colors(label_base="#EEF2F7"), images=imgs, faces=BOX_FACES,
                   parts=[_blade(W, D, H)])


# ---------------------------------------------------------------- 組み合わせ


def bathroom_cleaner_trigger() -> Product:
    W, D, H = 90.0, 55.0, 175.0  # 胴（扁平なボトル）
    blue, navy, white = "#7CC6E8", "#174E7A", "#FFFFFF"
    s = 10
    fr = Canvas(W, H, s, white, 1691)
    fr.gradient(0, 0, W, H, "#EAF6FC", blue)
    fr.rect(0, 0, W, 4, fill=navy)
    fr.rect(0, H - 6, W, H, fill=navy)
    fr.text(W / 2, 14, "BATH CLEANER", 4.2, navy, 700, spacing=0.8)
    fr.text(W / 2, 32, "お風呂用", 11, navy, 900)
    fr.text(W / 2, 48, "洗剤", 15, navy, 900)
    fr.rect(8, 58, W - 8, 68, fill=navy, radius=5)
    fr.text(W / 2, 63, "泡スプレー  浴槽・床・壁に", 4.2, white, 800, max_w=W - 20)
    fr.photo("mint", 14, 76, W - 14, 124, shape="ellipse", feather=3, crop=(0.15, 0.15, 0.85, 0.85))
    fr.rect(W / 2 - 25, 128, W / 2 + 25, 137, fill=white, radius=4.5)
    fr.text(W / 2, 132.5, "ミントの香り", 4.6, navy, 800)
    fr.text(W / 2, 146, "中性  除菌もできる", 4.6, navy, 800)
    fr.text(W / 2, 160, "380ml", 7.0, navy, 900)
    fr.text(W / 2, H - 3, "STRAIGHT / SPRAY", 2.6, white, 700)
    bk = Canvas(W, H, s, white, 1692)
    bk.gradient(0, 0, W, H, "#EAF6FC", blue)
    bk.rect(0, 0, W, 4, fill=navy)
    bk.rect(0, H - 6, W, H, fill=navy)
    bk.rect(5, 8, W - 5, 150, fill=white, radius=3)
    rows = [("品名", "浴室用合成洗剤"), ("用途", "浴槽・浴室の床・壁・洗面器"), ("液性", "中性"),
            ("成分", "界面活性剤（1.5% アルキルアミンオキシド）、除菌剤、金属封鎖剤、香料"), ("内容量", "380ml")]
    caution = ("【使用方法】ノズルを「SPRAY」に回し、20cm ほど離して吹き付け、スポンジでこすって水でよく流す。\n"
               "【使用上の注意】用途外に使わない。人や顔に向けない。換気をよくして使う。目に入ったらすぐ水で洗い流す。"
               "子供の手の届く所に置かない。")
    y = _info(bk, 8, 11, W - 8, rows, caution, 2.6)
    assert y < 150, y
    bk.rect(W / 2 - 18, 152, W / 2 + 18, 167, fill=white)
    bk.barcode(W / 2 - 16, 153, 32, 13)
    bk.recycle(12, 160, 7, "プラ", white, sub="容器")
    bk.recycle(W - 12, 160, 7, "プラ", white, sub="トリガー")
    imgs = [_face(fr.array(), "film", 1693, 0.6), _face(bk.array(), "film", 1694, 0.6)]
    bw, bd, bh = W / 1000, D / 1000, H / 1000
    head = "#F5F7F8"
    parts = [_box("Body", (bw, bd, bh), (0, 0, bh / 2), blue, "plastic", faces={"front": 0, "back": 1}),
             _box("Shoulder", (0.070, 0.044, 0.014), (0, 0, bh + 0.006), blue, "plastic"),
             _cyl("Neck", (0.030, 0.030, 0.022), (0, 0, bh + 0.022), "#E9EEF1", "plastic"),
             _cyl("Collar", (0.035, 0.035, 0.012), (0, 0, bh + 0.036), head, "plastic"),
             # ヘッド: 縦のポンプ部 + 前後に寝かせた円筒（シリンダー）+ 前下のカバー + ノズル + トリガー
             _cyl("PumpBody", (0.032, 0.032, 0.028), (0, 0, bh + 0.056), head, "plastic"),
             Part("Barrel", "cylinder", [0.032, 0.032, 0.072], [0, -0.014, bh + 0.074], rotation=[90, 0, 0],
                  color=head, finish="plastic"),
             _box("Shroud", (0.030, 0.034, 0.020), (0, -0.032, bh + 0.062), head, "plastic"),
             Part("Nozzle", "cylinder", [0.018, 0.018, 0.010], [0, -0.055, bh + 0.074], rotation=[90, 0, 0],
                  color=navy, finish="plastic"),
             _box("Trigger", (0.016, 0.010, 0.042), (0, -0.040, bh + 0.030), head, "plastic", rotation=[-12, 0, 0])]
    top = bh + 0.090
    return Product(slug="bathroom_cleaner_trigger", name="お風呂用洗剤 スプレー ミントの香り 380ml", shape_class="assembly",
                   category="household", dims=Dimensions(round(top, 4), 0.09, depth=0.0875), mass_kg=0.46,
                   static=False, material="plastic",
                   description="形は一般的なトリガースプレー式の浴室用洗剤（扁平なボトルの胴 90 × 55 mm、全高 265 mm、"
                               "トリガーとノズルの付いたヘッド）で、寸法・質量は代表値。",
                   tags=["お風呂用洗剤", "浴室用洗剤", "スプレー", "掃除", "bath cleaner", "spray bottle"], photos=["mint"],
                   colors=Colors(label_base=blue), images=imgs, parts=parts)


def kitchen_sponge_3pack() -> Product:
    SW, SD, soft_h, scrub_h = 0.110, 0.075, 0.028, 0.010
    BW, BD, BH = 70.0, 79.0, 118.0  # 紙の帯（台紙）
    orange, white, green = "#E8742A", "#FFFFFF", "#2E8B57"
    softs = ("#F5D33B", "#F29BB5", "#7EC3E8")
    s = 14

    def band(seed: int) -> Canvas:
        f = Canvas(BW, BH, s, white, seed)
        f.gradient(0, 0, BW, BH, "#FFFFFF", "#FFE7D2")
        f.rect(0, 0, BW, 5, fill=orange)
        f.rect(0, BH - 5, BW, BH, fill=green)
        return f

    fr = band(1701)
    fr.text(BW / 2, 13, "KITCHEN SPONGE", 3.4, orange, 700, spacing=0.6)
    fr.text(BW / 2, 27, "キッチン", 9.0, INK, 900)
    fr.text(BW / 2, 40, "スポンジ", 9.0, INK, 900)
    fr.rect(BW / 2 - 24, 47, BW / 2 + 24, 57, fill=orange, radius=5)
    fr.text(BW / 2, 52, "3個入", 6.0, white, 900)
    for k, col in enumerate(softs):  # 2 層の絵
        y = 64 + k * 12
        fr.rect(14, y, BW - 14, y + 8, fill=col, radius=1.5)
        fr.rect(14, y + 8, BW - 14, y + 10.5, fill=green, radius=1)
    fr.text(BW / 2, 102, "やわらか面 ＋ 研磨面", 3.8, INK, 800)
    fr.text(BW / 2, 109, "泡立ちよく  水切れがよい", 3.2, green, 700)
    bk = band(1702)
    rows = [("品名", "台所用スポンジ"), ("材質", "ウレタンフォーム・ナイロン不織布（研磨剤付き）"),
            ("寸法", "110 × 75 × 38 mm"), ("耐熱温度", "90℃"), ("入り数", "3個")]
    caution = ("【注意】研磨面はフッ素樹脂加工・漆器・ガラス・鏡面仕上げの物には使わない。"
               "火のそばに置かない。使用後は水気をよく切り、乾かす。")
    y = _info(bk, 5, 8, BW - 5, rows, caution, 2.3)
    assert y < BH - 26, y
    bk.barcode(6, BH - 25, 30, 17)
    bk.recycle(BW - 22, BH - 16, 8, "紙", orange, sub="台紙")
    bk.recycle(BW - 9, BH - 16, 8, "プラ", green, sub="袋")
    imgs = [_face(fr.array(), "paper", 1703), _face(bk.array(), "paper", 1704)]
    parts = []
    for k, col in enumerate(softs):
        z0 = 0.002 + k * (soft_h + scrub_h)
        parts.append(_box(f"Sponge{k}", (SW, SD, soft_h), (0, 0, z0 + soft_h / 2), col, "matte"))
        parts.append(_box(f"Scrub{k}", (SW - 0.002, SD - 0.002, scrub_h), (0, 0, z0 + soft_h + scrub_h / 2), green,
                          "matte"))
    parts.append(_box("Band", (BW / 1000, BD / 1000, BH / 1000), (0, 0, BH / 2000), "#FFE7D2", "matte",
                      faces={"front": 0, "back": 1}))
    return Product(slug="kitchen_sponge_3pack", name="キッチンスポンジ 3個入", shape_class="assembly",
                   category="household", dims=Dimensions(0.118, 0.11, depth=0.079), mass_kg=0.045, static=False,
                   material="urethane",
                   description="形は一般的な 2 層（やわらか面と研磨面）のキッチンスポンジ 3 個を重ね、紙の帯を巻いた包装"
                               "（スポンジ 110 × 75 × 38 mm）で、寸法・質量は代表値。外側の透明な袋は省略。",
                   tags=["スポンジ", "キッチンスポンジ", "台所用品", "掃除", "kitchen sponge", "sponge"], photos=[],
                   colors=Colors(label_base="#FFE7D2"), images=imgs, parts=parts)


def _roll_band(W: float, D: float, H: float, seed: int, color: str, accent: str, front, back, side) -> list:
    """ロール製品の包装の帯（正面・裏・左右）。"""
    s = 1800 / W

    def face(w: float, h: float, k: int) -> Canvas:
        f = Canvas(w, h, s, "#FFFFFF", seed + k)
        f.gradient(0, 0, w, h, "#FFFFFF", mix(color, "#FFFFFF", 0.75))
        f.rect(0, 0, w, 4, fill=color)
        f.rect(0, h - 4, w, h, fill=accent)
        return f

    fr, bk, r, lf = face(W, H, 0), face(W, H, 1), face(D, H, 2), face(D, H, 3)
    front(fr)
    back(bk)
    side(r, 0)
    side(lf, 1)
    return [_face(f.array(), "film", seed + 10 + i, 0.6) for i, f in enumerate((fr, bk, r, lf))]


def paper_towel_2roll() -> Product:
    RD, RH = 0.115, 0.220
    BW, BD, BH = 236.0, 119.0, 90.0
    green, leaf, white = "#3C8D5A", "#9BCB6B", "#FFFFFF"

    def front(f: Canvas):
        f.text(14, 24, "キッチンペーパー", 15, green, 900, anchor="lm")
        f.text(14, 42, "KITCHEN PAPER TOWEL", 5.0, leaf, 700, anchor="lm", spacing=1.2)
        f.text(14, 58, "吸水力たっぷり  2枚重ね", 6.0, INK, 800, anchor="lm")
        f.text(14, 72, "油切り・水切り・ふき掃除に", 5.0, green, 700, anchor="lm")
        f.ellipse(BW - 70, 14, BW - 14, 70, fill=green)
        f.text(BW - 42, 34, "2", 16, white, 900)
        f.text(BW - 42, 50, "ロール", 6.0, white, 800)
        f.text(BW - 42, 60, "50カット", 4.4, white, 700)
        f.text(BW - 42, 80, "パルプ 100%", 4.4, green, 800)

    def back(f: Canvas):
        rows = [("品名", "キッチンタオル"), ("材質", "パルプ 100%"), ("寸法", "幅 22cm × 長さ 12.5m（50カット）・2枚重ね"),
                ("入り数", "2ロール")]
        caution = "【注意】水に溶けにくいので、トイレに流さないでください。火のそばに置かないでください。"
        y = f.table(10, 9, 130, "", rows, 3.2, INK, white)
        assert y < BH - 6, y
        f.paragraph(136, 9, BW - 62, caution, 3.0, INK, 400)
        f.paragraph(136, 50, BW - 62, NOTICE, 2.7, INK, 500)
        f.rect(BW - 56, 9, BW - 10, 42, fill=white)
        f.barcode(BW - 54, 11, 42, 29)
        f.recycle(BW - 44, 62, 11, "プラ", green, sub="包装")
        f.recycle(BW - 22, 62, 11, "紙", green, sub="芯")

    def side(f: Canvas, k: int):
        f.text(BD / 2, 28, "キッチン", 11, green, 900)
        f.text(BD / 2, 46, "ペーパー", 11, green, 900)
        f.text(BD / 2, 66, "2ロール" if k == 0 else "パルプ 100%", 7, INK, 800)

    imgs = _roll_band(BW, BD, BH, 1711, green, leaf, front, back, side)
    paper, core = "#F7F6F1", "#B88E5E"
    parts = []
    for k, x in enumerate((-RD / 2, RD / 2)):
        parts.append(_cyl(f"Roll{k}", (RD, RD, RH), (x, 0, RH / 2), paper, "matte"))
        parts.append(_cyl(f"Core{k}", (0.040, 0.040, RH + 0.0006), (x, 0, RH / 2), core, "matte", collision=False))
    parts.append(_box("Band", (BW / 1000, BD / 1000, BH / 1000), (0, 0, RH / 2), mix(green, white, 0.75), "plastic",
                      faces={"front": 0, "back": 1, "right": 2, "left": 3}))
    # 全体を包む透明フィルム（帯とロールの少し外側。底はロールの底と同じ面にならないよう 1 mm 下げる）
    fh = RH + 0.003
    parts.append(_box("Film", (BW / 1000 + 0.004, BD / 1000 + 0.004, fh), (0, 0, fh / 2 - 0.001), "#F2F6F8", "glass", thin_walled=True,
                      collision=False))
    return Product(slug="paper_towel_2roll", name="キッチンペーパー 2ロール", shape_class="assembly", category="household",
                   dims=Dimensions(round(fh, 4), round(BW / 1000 + 0.004, 4), depth=round(BD / 1000 + 0.004, 4)), mass_kg=0.42, static=False, material="paper",
                   description="形は一般的なキッチンペーパー 2 ロールのパック（ロール 直径 115 mm・幅 220 mm を 2 本立てて並べ、"
                               "印刷した包装の帯を巻き、全体を透明なフィルムで包んだ形）で、寸法・質量は代表値。",
                   tags=["キッチンペーパー", "キッチンタオル", "紙製品", "台所用品", "paper towel", "kitchen paper"], photos=[],
                   colors=Colors(label_base=paper), images=imgs, parts=parts)


def toilet_paper_12roll() -> Product:
    RD, RH, GAP = 0.115, 0.1138, 0.0004
    BW, BD, BH = 349.0, 234.0, 96.0
    blue, sky, white = "#2F6EB5", "#9CC7EC", "#FFFFFF"

    def front(f: Canvas):
        f.text(16, 26, "トイレットペーパー", 20, blue, 900, anchor="lm")
        f.text(16, 46, "TOILET TISSUE", 7.0, sky, 700, anchor="lm", spacing=2.0)
        f.text(16, 64, "ダブル  やわらか 2枚重ね", 8.0, INK, 800, anchor="lm")
        f.text(16, 80, "25m × 12ロール  水にとけます", 6.4, blue, 700, anchor="lm")
        f.ellipse(BW - 88, 10, BW - 14, 84, fill=blue)
        f.text(BW - 51, 38, "12", 22, white, 900)
        f.text(BW - 51, 61, "ロール", 8.0, white, 800)
        f.text(BW - 51, 73, "ダブル", 6.0, white, 700)

    def back(f: Canvas):
        rows = [("品名", "トイレットペーパー"), ("材質", "パルプ 100%"), ("寸法", "幅 114mm × 長さ 25m（2枚重ね）"),
                ("入り数", "12ロール"), ("ほぐれやすさ", "100秒以内")]
        caution = ("【注意】一度にたくさん流すと詰まることがあります。湿気の多い所・火のそばに置かないでください。"
                   "トイレットペーパー以外の紙は流さないでください。")
        y = f.table(12, 10, 170, "", rows, 4.0, INK, white)
        assert y < BH - 6, y
        f.paragraph(178, 10, BW - 80, caution, 3.8, INK, 400)
        f.paragraph(178, 58, BW - 80, NOTICE, 3.4, INK, 500)
        f.rect(BW - 72, 10, BW - 12, 50, fill=white)
        f.barcode(BW - 70, 12, 56, 36)
        f.recycle(BW - 58, 70, 14, "プラ", blue, sub="包装")
        f.recycle(BW - 28, 70, 14, "紙", blue, sub="芯")

    def side(f: Canvas, k: int):
        f.text(BD / 2, 28, "トイレットペーパー", 16, blue, 900, max_w=BD - 20)
        f.text(BD / 2, 52, "12ロール  ダブル" if k == 0 else "パルプ 100%", 11, INK, 800)
        f.text(BD / 2, 72, "持ち手は上面" if k == 0 else "25m", 8, blue, 700)

    imgs = _roll_band(BW, BD, BH, 1751, blue, sky, front, back, side)
    paper, core = "#FAFAF7", "#B88E5E"
    parts = []
    n = 0
    for layer in range(2):
        z = layer * (RH + GAP) + RH / 2
        for x in (-RD, 0.0, RD):
            for y in (-RD / 2, RD / 2):
                parts.append(_cyl(f"Roll{n:02d}", (RD, RD, RH), (x, y, z), paper, "matte"))
                parts.append(_cyl(f"Core{n:02d}", (0.040, 0.040, RH + GAP), (x, y, z), core, "matte", collision=False))
                n += 1
    total_h = 2 * RH + GAP
    parts.append(_box("Band", (BW / 1000, BD / 1000, BH / 1000), (0, 0, total_h / 2), mix(blue, white, 0.75), "plastic",
                      faces={"front": 0, "back": 1, "right": 2, "left": 3}))
    # 全体を包む透明フィルム（帯とロールの少し外側）。持ち手はフィルムの上に載せる
    fh = total_h + 0.003
    parts.append(_box("Film", (BW / 1000 + 0.004, BD / 1000 + 0.004, fh), (0, 0, fh / 2 - 0.001), "#F2F6F8", "glass", thin_walled=True,
                      collision=False))
    parts.append(_box("Handle", (0.040, 0.150, 0.003), (0, 0, fh - 0.001 + 0.0017), mix(blue, white, 0.6), "plastic",
                      collision=False))
    return Product(slug="toilet_paper_12roll", name="トイレットペーパー ダブル 12ロール", shape_class="assembly",
                   category="household", dims=Dimensions(round(fh + 0.0034, 4), round(BW / 1000 + 0.004, 4), depth=round(BD / 1000 + 0.004, 4)), mass_kg=1.35,
                   static=False, material="paper",
                   description="形は一般的なトイレットペーパー 12 ロールのパック（ロール 直径 115 mm・幅 114 mm を 3 × 2 × 2 段に積み、"
                               "印刷した包装の帯と上面の持ち手を付け、全体を透明なフィルムで包んだ形）で、寸法・質量は代表値。",
                   tags=["トイレットペーパー", "ダブル", "12ロール", "紙製品", "toilet paper", "toilet tissue"], photos=[],
                   colors=Colors(label_base=paper), images=imgs, parts=parts)


PRODUCTS = {f.__name__: f for f in (
    dish_soap_bottle, laundry_detergent_refill, kitchen_bleach_bottle, bathroom_cleaner_trigger, trash_bags_45l,
    food_wrap_box, aluminum_foil_box, kitchen_sponge_3pack, rubber_gloves, deodorizer_gel_jar, wet_wipes_pack,
    paper_towel_2roll, toilet_paper_12roll,
)}
