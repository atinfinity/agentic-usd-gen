"""Fictional products: books for a bookstore (hardcover, bunko, shinsho, large photo book, a stack of bunko).

As in products.py, no real titles, authors, publishers or logos are used. Covers are drawn from shapes only;
sizes are the common Japanese book formats. Barcodes are dummy EAN-13 in the in-store range (starting with 2).
Books stand upright (spine vertical) unless noted, with the front cover facing -Y.
"""

from __future__ import annotations

import numpy as np

from ..spec import Colors, Dimensions, Part
from .base import NOTICE, Product
from .drug_medicine import BOX_FACES
from .paint import Canvas, mix
from .products import INK, _face

WHITE, PAPER = "#FFFFFF", "#EFEBE1"
BOOK_TAGS = ["本", "書籍", "書店", "book", "bookstore"]


def _edges(W: float, H: float, D: float, seed: int, spine_right: bool, spine_color: str) -> list[Canvas]:
    """The page block: fore edge (D x H) and top / bottom edges (W x D) with the spine side colored."""
    ed = Canvas(D, H, 10, PAPER, seed)
    for k in range(int(D * 4)):
        ed.line([(k / 4, 0), (k / 4, H)], mix(PAPER, "#A9A39A", 0.2 + 0.2 * (k % 4 == 0)), 0.05)
    tp, bt = Canvas(W, D, 6, PAPER, seed + 1), Canvas(W, D, 6, PAPER, seed + 2)
    for e in (tp, bt):
        for k in range(int(D * 1.5)):
            e.line([(0, k * D / int(D * 1.5)), (W, k * D / int(D * 1.5))], mix(PAPER, "#A9A39A", 0.3), 0.06)
    # the spine side of the top face is on the same side as the spine; the bottom face is mirrored
    sx_top = (W - 2, W) if spine_right else (0, 2)
    sx_bot = (0, 2) if spine_right else (W - 2, W)
    tp.rect(sx_top[0], 0, sx_top[1], D, fill=spine_color)
    bt.rect(sx_bot[0], 0, sx_bot[1], D, fill=spine_color)
    return [ed, tp, bt]


def _back_cover(W: float, H: float, seed: int, bg: str, accent: str, blurb: str, price: str, label: str) -> Canvas:
    b = Canvas(W, H, 8, bg, seed)
    b.gradient(0, 0, W, H, mix(bg, WHITE, 0.25), bg)
    b.rect(0, 0, W, H * 0.035, fill=accent)  # colored bands at the top and bottom edges
    b.rect(0, H * 0.965, W, H, fill=accent)
    m = W * 0.08
    b.rect(m, m, W - m, H * 0.45, fill=WHITE, outline=accent, width=0.4)
    b.paragraph(m + 3, m + 3, W - m - 3, blurb, max(2.4, W / 34), INK, 500)
    bw = min(36.0, W * 0.38)
    b.barcode(W - m - bw, H * 0.55, bw, bw * 0.38)
    b.barcode(W - m - bw, H * 0.55 + bw * 0.5, bw, bw * 0.38)
    b.text(m, H * 0.58, "書籍コード（ダミー）", max(2.0, W / 45), INK, 600, anchor="lm")
    b.text(m, H * 0.64, f"定価 {price}", max(3.0, W / 28), INK, 900, anchor="lm")
    b.text(m, H * 0.69, label, max(2.2, W / 42), INK, 700, anchor="lm")
    b.text(W / 2, H * 0.93, NOTICE, max(1.8, W / 50), INK, 500, max_w=W - 8)
    return b


def _spine(D: float, H: float, seed: int, bg: str, fg: str, title: str, author: str, label: str) -> Canvas:
    sp = Canvas(D, H, 10, bg, seed)
    sp.gradient(0, 0, D, H, mix(bg, WHITE, 0.15), bg)
    size = min(D * 0.62, (H * 0.55) / max(1, len(title)) / 1.05)
    sp.vtext(D / 2, 6 + size / 2, title, size, fg, 900, gap=0.05)
    asz = min(D * 0.45, size * 0.7)
    sp.vtext(D / 2, H * 0.66, author, asz, fg, 700, gap=0.05)
    sp.rect(D * 0.15, H - 16, D * 0.85, H - 15.6, fill=fg)
    sp.text(D / 2, H - 9, label[:2], min(D * 0.4, 3.6), fg, 800)
    return sp


def _faces(canvases, kind: str, seed: int) -> list[np.ndarray]:
    return [_face(c.array(), kind, seed + i, 0.5) for i, c in enumerate(canvases)]


def _novel_cover(W: float, H: float, seed: int, bg: str, accent: str, title: str, author: str, label: str,
                 obi: str | None, motif: str) -> Canvas:
    """A vertical-text novel cover: a simple landscape drawn from shapes, the title set vertically."""
    c = Canvas(W, H, 8, bg, seed)
    c.gradient(0, 0, W, H, mix(bg, WHITE, 0.35), bg)
    if motif == "sea":
        c.rect(0, H * 0.48, W, H, fill=mix(accent, "#000000", 0.2))
        c.ellipse(W * 0.15, H * 0.30, W * 0.42, H * 0.30 + W * 0.27, fill="#F7E3B2")
        for k in range(6):
            y = H * 0.52 + k * H * 0.05
            c.line([(W * 0.1, y), (W * 0.9, y + 1)], mix(accent, WHITE, 0.4), 0.3)
    elif motif == "forest":
        for k in range(7):
            x = W * (0.05 + 0.14 * k)
            h = H * (0.25 + 0.08 * (k % 3))
            c.polygon([(x, H * 0.75), (x + W * 0.08, H * 0.75 - h), (x + W * 0.16, H * 0.75)],
                      fill=mix(accent, "#000000", 0.1 * (k % 3)))
        c.rect(0, H * 0.75, W, H, fill=mix(accent, "#000000", 0.35))
    else:  # "city": windows of tall buildings at night
        for k in range(5):
            x0 = W * (0.04 + 0.19 * k)
            top = H * (0.35 + 0.07 * ((k * 3) % 4))
            c.rect(x0, top, x0 + W * 0.16, H, fill=mix(accent, "#000000", 0.3 + 0.08 * (k % 2)))
            y = top + 4
            while y < H - 4:
                for i in range(3):
                    if c.rng.random() < 0.55:
                        wx = x0 + 2 + i * W * 0.05
                        c.rect(wx, y, wx + W * 0.025, y + 2.2, fill="#FFE9A8")
                y += 5
    # the title in a white box, set vertically on the right (right-bound book)
    ts = min(W * 0.12, (H * 0.55) / max(1, len(title)) / 1.05)
    bx = W - W * 0.08 - ts * 1.6
    c.rect(bx, 6, W - W * 0.08, 6 + ts * 1.05 * len(title) + ts * 0.8, fill=WHITE)
    c.vtext(bx + ts * 0.8, 6 + ts * 0.9, title, ts, INK, 900)
    c.vtext(W * 0.12, 8, author, min(W * 0.06, 5.0), WHITE, 800)
    c.text(W * 0.12, H - (H * 0.17 if obi else 0) - 5, label, min(W * 0.05, 3.6), WHITE, 800, anchor="lm")
    if obi:  # the paper band
        c.gradient(0, H * 0.82, W, H, "#FFE14D", "#F5D23A", horizontal=True)
        c.text(W / 2, H * 0.87, obi, min(W * 0.065, 6.0), "#C62828", 900, max_w=W - 8)
        c.text(W / 2, H * 0.94, "累計 10 万部（架空）", min(W * 0.045, 4.0), INK, 800, max_w=W - 8)
    return c


def _novel(slug: str, name: str, W: float, H: float, D: float, mass: float, seed: int, bg: str, accent: str,
           title: str, author: str, label: str, price: str, obi: str | None, motif: str, blurb: str,
           description: str, tags: list[str], parts: list[Part] | None = None) -> Product:
    fr = _novel_cover(W, H, seed, bg, accent, title, author, label, obi, motif)
    bk = _back_cover(W, H, seed + 1, mix(bg, WHITE, 0.55), accent, blurb, price, label)
    sp = _spine(D, H, seed + 2, bg, WHITE, title, author, label)
    ed, tp, bt = _edges(W, H, D, seed + 3, True, bg)
    # BOX_FACES order: front, back, right (spine of a right-bound book), left (fore edge), top, bottom
    imgs = _faces((fr, bk, sp, ed, tp, bt), "paper", seed)
    return Product(slug=slug, name=name, shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=mass, material="paper",
                   description=description, tags=[*tags, *BOOK_TAGS], photos=[], colors=Colors(label_base=bg),
                   images=imgs, faces=BOX_FACES, parts=parts or [])


def hardcover_book() -> Product:
    """A 四六判 hardcover novel with a dust jacket and a paper band."""
    return _novel("hardcover_book", "単行本 小説 四六判 ハードカバー", 128.0, 188.0, 24.0, 0.42, 9801, "#24476B",
                  "#5C8DB8", "潮騒の灯台", "架空 二郎", "架空書房", "1,870円", "本屋さんが選んだ一冊", "sea",
                  "灯台守の祖父が遺した一冊の日誌。夏の終わり、少女は海辺の町でその続きを書きはじめる。"
                  "静かな港町を舞台にした長編小説。",
                  "形は一般的な四六判のハードカバーの単行本（128 × 188 mm・厚さ 24 mm、カバーと帯付き、右綴じ）を立てた箱で"
                  "近似したもので、寸法・質量は代表値。題名・作者名・出版社名・あらすじ・表紙の絵はすべて架空。",
                  ["単行本", "小説", "ハードカバー", "四六判", "hardcover", "novel", "hardback book"])


def bunko_paperback() -> Product:
    """A 文庫判 paperback (A6)."""
    return _novel("bunko_paperback", "文庫本 小説 文庫判", 105.0, 148.0, 15.0, 0.17, 9811, "#3E6B3A", "#6E9E5A",
                  "森のほとりの図書館", "架空 三郎", "架空文庫", "770円", "映画化決定（架空）", "forest",
                  "森の奥にある小さな図書館には、返されたことのない本が一冊だけある。司書見習いの青年と、"
                  "毎週土曜に来る少女の物語。",
                  "形は一般的な文庫本（文庫判 105 × 148 mm・厚さ 15 mm、カバーと帯付き、右綴じ）を立てた箱で近似したもので、"
                  "寸法・質量は代表値。題名・作者名・あらすじ・表紙の絵はすべて架空。",
                  ["文庫", "文庫本", "小説", "文庫判", "A6", "paperback", "bunko", "pocket book"])


def shinsho_book() -> Product:
    """A 新書判 non-fiction paperback (the plain cover style of a 新書 series)."""
    W, H, D = 103.0, 182.0, 11.0
    seed, bg, band = 9821, "#F3F0E8", "#1F5A8C"
    title, author, label = "はじめての都市計画", "架空 四郎", "架空新書"
    c = Canvas(W, H, 8, bg, seed)
    c.gradient(0, 0, W, H, "#FBF9F4", bg)
    c.gradient(0, 0, W, H * 0.07, mix(band, WHITE, 0.15), band, horizontal=True)
    c.text(W / 2, H * 0.035, label, 4.0, WHITE, 800, spacing=1.0)
    ts = 9.0
    c.vtext(W * 0.70, 26, title, ts, INK, 900)
    c.vtext(W * 0.40, 30, author, 5.0, INK, 700)
    for k in range(4):  # a small map motif
        c.line([(W * 0.08, H * 0.62 + k * 7), (W * 0.32, H * 0.60 + k * 7)], mix(band, WHITE, 0.4), 0.6)
        c.line([(W * 0.10 + k * 6, H * 0.57), (W * 0.12 + k * 6, H * 0.84)], mix(band, WHITE, 0.4), 0.6)
    c.gradient(0, H * 0.86, W, H, "#FFE14D", "#F5D23A", horizontal=True)
    c.text(W / 2, H * 0.90, "まちはどうやってできるのか", 5.2, "#C62828", 900, max_w=W - 8)
    c.text(W / 2, H * 0.96, "新しい教養の入門書", 3.8, INK, 800)
    bk = _back_cover(W, H, seed + 1, bg, band, "道路、公園、駅前の広場。毎日通る道はだれが、どのように決めているのか。"
                                               "身近な例から都市計画の考え方をやさしく解説する。", "990円", label)
    sp = _spine(D, H, seed + 2, band, WHITE, title, author, label)
    ed, tp, bt = _edges(W, H, D, seed + 3, True, band)
    imgs = _faces((c, bk, sp, ed, tp, bt), "paper", seed)
    return Product(slug="shinsho_book", name="新書 教養 新書判", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=0.16, material="paper",
                   description="形は一般的な新書（新書判 103 × 182 mm・厚さ 11 mm、帯付き、右綴じ）を立てた箱で近似したもので、"
                               "寸法・質量は代表値。題名・作者名・叢書名・あらすじはすべて架空。",
                   tags=["新書", "新書判", "教養", "paperback", "shinsho", *BOOK_TAGS], photos=[],
                   colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


def large_photo_book() -> Product:
    """A large-format (A4 variant) photo book, left-bound with horizontal text."""
    W, H, D = 225.0, 300.0, 18.0
    seed, bg, accent = 9831, "#1C2A33", "#7FB3C8"
    title, author, label = "NORTHERN LIGHTS", "写真・架空 五郎", "架空出版"
    c = Canvas(W, H, 6, bg, seed)
    c.gradient(0, 0, W, H * 0.7, "#0D1B2A", "#25475B")
    for k in range(5):  # an aurora drawn from soft bands
        y = H * (0.18 + 0.06 * k)
        c.polygon([(0, y + 30), (W * 0.3, y), (W * 0.6, y + 20), (W, y - 10), (W, y + 4), (W * 0.6, y + 34),
                   (W * 0.3, y + 14), (0, y + 44)], fill=mix("#5BE3A6", "#25475B", 0.25 + 0.12 * k))
    for _ in range(60):
        x, y = c.rng.uniform(0, W), c.rng.uniform(0, H * 0.3)
        c.ellipse(x - 0.4, y - 0.4, x + 0.4, y + 0.4, fill="#FFFFFF")
    c.polygon([(0, H * 0.78), (W * 0.25, H * 0.66), (W * 0.45, H * 0.74), (W * 0.7, H * 0.62), (W, H * 0.72),
               (W, H), (0, H)], fill="#0B1218")
    c.text(W / 2, H * 0.84, title, 16.0, WHITE, 800, spacing=2.0)
    c.text(W / 2, H * 0.90, "極北の夜空 写真集", 7.0, accent, 800)
    c.text(W / 2, H * 0.95, author, 5.0, mix(accent, WHITE, 0.5), 700)
    bk = _back_cover(W, H, seed + 1, "#E9EEF1", "#25475B", "極北の冬、氷点下 30 度の夜に撮りためたオーロラと星空の写真 120 点を"
                                                           "大判で収める。撮影地の地図と撮影データ付き。", "4,950円", label)
    sp = Canvas(D, H, 10, bg, seed + 2)  # the spine of a left-bound book with horizontal text, rotated
    sp.gradient(0, 0, D, H, "#25475B", bg)
    sp.vtext(D / 2, 12, "極北の夜空", 7.5, WHITE, 900)
    sp.vtext(D / 2, H * 0.55, "架空五郎", 5.0, accent, 700)
    sp.text(D / 2, H - 10, "架空", 4.0, WHITE, 800)
    ed, tp, bt = _edges(W, H, D, seed + 3, False, bg)
    # left-bound: the spine is the left face, the fore edge is the right face
    imgs = _faces((c, bk, ed, sp, tp, bt), "paper", seed)
    return Product(slug="large_photo_book", name="大型本 写真集 A4変型判", shape_class="box", category="household",
                   dims=Dimensions(H / 1000, W / 1000, depth=D / 1000), mass_kg=1.2, material="paper",
                   description="形は一般的な大判の写真集（A4 変型判 225 × 300 mm・厚さ 18 mm、ハードカバー、左綴じ）を立てた箱で"
                               "近似したもので、寸法・質量は代表値。題名・作者名・出版社名・表紙の絵はすべて架空。",
                   tags=["大型本", "写真集", "画集", "A4", "photo book", "coffee table book", "large book",
                         *BOOK_TAGS], photos=[], colors=Colors(label_base=bg), images=imgs, faces=BOX_FACES)


def bunko_stack() -> Product:
    """Five bunko paperbacks of the same title lying in a stack, cover up (the way 平台 displays pile new books).

    One box textured as five books keeps the texture size of a single book (one part per book would be five atlases).
    """
    W, H, D, n = 105.0, 148.0, 15.0, 5
    T = D * n
    seed, bg, accent = 9841, "#7A3B2E", "#C87A4A"
    title, author, label = "夕焼け坂の喫茶店", "架空 六郎", "架空文庫"
    cover = _novel_cover(W, H, seed, bg, accent, title, author, label, "本屋大賞ノミネート（架空）", "city")
    back = _back_cover(W, H, seed + 1, mix(bg, WHITE, 0.6), accent, "坂の上の小さな喫茶店には、夕方五時にだけ開く"
                                                                    "もうひとつの扉がある。心がほどける連作短編集。",
                       "748円", label)

    def layers(w: float, sd: int, spine_at: str | None) -> Canvas:
        """A side of the stack: five page blocks between thin covers; spine_at puts the colored spine on that end."""
        c = Canvas(w, T, 10, PAPER, sd)
        for k in range(n):
            y0 = k * D
            c.rect(0, y0, w, y0 + 0.6, fill=bg)  # covers above and below each page block
            c.rect(0, y0 + D - 0.6, w, y0 + D, fill=bg)
            for m in range(int(D * 3)):
                yy = y0 + 0.8 + m * (D - 1.6) / int(D * 3)
                c.line([(0, yy), (w, yy)], mix(PAPER, "#A9A39A", 0.25), 0.05)
            if spine_at == "left":
                c.rect(0, y0, 1.5, y0 + D, fill=bg)
            elif spine_at == "right":
                c.rect(w - 1.5, y0, w, y0 + D, fill=bg)
        return c

    def spines() -> Canvas:
        c = Canvas(H, T, 10, bg, seed + 5)
        for k in range(n):
            y0 = k * D
            c.gradient(0, y0, H, y0 + D, mix(bg, WHITE, 0.18), bg)
            c.line([(0, y0 + D - 0.2), (H, y0 + D - 0.2)], mix(bg, "#000000", 0.4), 0.3)
            c.text(H * 0.42, y0 + D / 2, title, D * 0.5, WHITE, 900, max_w=H * 0.62)
            c.text(H * 0.86, y0 + D / 2, label, D * 0.3, WHITE, 800, max_w=H * 0.2)
        return c

    # front (-Y) is the bottom edge of the books, back (+Y) the top edge; the spines face +X (right)
    imgs = _faces((cover, back, spines(), layers(H, seed + 6, None), layers(W, seed + 7, "right"),
                   layers(W, seed + 8, "left")), "paper", seed)
    faces = {"top": 0, "bottom": 1, "right": 2, "left": 3, "back": 4, "front": 5}
    return Product(slug="bunko_stack", name="文庫本の平積み 5冊", shape_class="box", category="household",
                   dims=Dimensions(T / 1000, W / 1000, depth=H / 1000), mass_kg=0.85, material="paper",
                   description="形は書店の平台に表紙を上にして積む同じ文庫本 5 冊（文庫判 105 × 148 mm・厚さ 15 mm × 5 冊）を"
                               "1 つの箱で近似したもので、寸法・質量は代表値。5 冊で 1 つの剛体。題名・作者名・表紙の絵は"
                               "すべて架空。",
                   tags=["文庫", "平積み", "本の山", "新刊", "文庫本", "book stack", "pile of books", "bunko",
                         *BOOK_TAGS], photos=[], colors=Colors(label_base=bg), images=imgs, faces=faces)


PRODUCTS = {f.__name__: f for f in (hardcover_book, bunko_paperback, shinsho_book, large_photo_book, bunko_stack)}
