"""架空のパッケージの絵を描く道具。

文字（Noto Sans JP）・写真の合成・紙／フィルム／金属の質感・ダミーのバーコード・識別表示マーク・一括表示などを
mm 単位で描けるようにまとめる。写真は data/photos/ の CC0／パブリックドメインのものだけを使う。
"""

from __future__ import annotations

import json
import math
import re
import random
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..texres import MAX_PX, draw_px_per_mm

DATA = Path(__file__).resolve().parent.parent / "data"
FONT_PATH = DATA / "fonts" / "NotoSansJP[wght].ttf"
FONT_LICENSE = "Noto Sans JP（SIL Open Font License 1.1）"
PHOTO_DIR = DATA / "photos"


# ---------------------------------------------------------------- 文字


@lru_cache(maxsize=256)
def font(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT_PATH), max(6, int(size)))
    f.set_variation_by_axes([max(100, min(900, weight))])
    return f


# ---------------------------------------------------------------- 写真


@lru_cache(maxsize=1)
def photo_manifest() -> dict[str, dict]:
    return json.loads((PHOTO_DIR / "photos.json").read_text())


@lru_cache(maxsize=32)
def _photo(pid: str) -> Image.Image:
    return Image.open(PHOTO_DIR / photo_manifest()[pid]["file"]).convert("RGB")


def photo_credit(pid: str) -> dict:
    m = photo_manifest()[pid]
    return {"url": m["page"], "file_url": m["url"], "title": m["title"], "author": m["author"],
            "license": m["license"], "license_url": m.get("license_url"), "subject": m["subject"]}


def cover(img: Image.Image, size: tuple[int, int], crop: tuple[float, float, float, float] | None = None) -> Image.Image:
    """crop（0〜1 の x0, y0, x1, y1）の範囲を中心に、size をすき間なく覆うよう切り抜いて拡大する。"""
    W, H = img.size
    x0, y0, x1, y1 = crop or (0, 0, 1, 1)
    cx, cy = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H
    cw, ch = (x1 - x0) * W, (y1 - y0) * H
    aspect = size[0] / size[1]
    if cw / ch > aspect:
        cw = ch * aspect
    else:
        ch = cw / aspect
    cw, ch = min(cw, W), min(ch, H)
    left = min(max(cx - cw / 2, 0), W - cw)
    top = min(max(cy - ch / 2, 0), H - ch)
    return img.resize(size, Image.LANCZOS, box=(left, top, left + cw, top + ch))


# ---------------------------------------------------------------- 色


def rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a: str, b: str, t: float) -> str:
    ca, cb = rgb(a), rgb(b)
    return "#" + "".join(f"{int(round(x + (y - x) * t)):02X}" for x, y in zip(ca, cb))


# ---------------------------------------------------------------- キャンバス


def canvas_px_per_mm(w_mm: float, h_mm: float) -> float:
    """w_mm × h_mm の絵柄を描く画素密度の下限。どちらの辺もテクスチャの目安（8 px/mm）で頭打ちにならない値。

    ただし長い辺がテクスチャの上限（MAX_PX）を超える密度にはしない（それ以上は縮小されるだけ）。
    """
    s = max(draw_px_per_mm(w_mm / 1000), draw_px_per_mm(h_mm / 1000))
    return min(s, MAX_PX / max(w_mm, h_mm, 1e-6))


_RECORDING: list | None = None


@contextmanager
def recording():
    """この中で作った Canvas を順に集める（描いた文字 Canvas.texts を商品の画像と対応づけるため）。"""
    global _RECORDING
    prev, _RECORDING = _RECORDING, []
    try:
        yield _RECORDING
    finally:
        _RECORDING = prev


class Canvas:
    """mm 単位で描くキャンバス。原点は左上、x は右、y は下。

    text・vtext・paragraph で描いた文字は texts に描いた順に残る（バーコードの数字・識別マークは除く）。"""

    def __init__(self, w_mm: float, h_mm: float, px_per_mm: float | None = None, bg: str = "#FFFFFF", seed: int = 0):
        # 画素密度は、貼るテクスチャが目安（texres.PX_PER_MM）以上になる値を下限にする。省略時はその下限
        px_per_mm = max(px_per_mm or 0.0, canvas_px_per_mm(w_mm, h_mm))
        self.s = px_per_mm
        self.w_mm, self.h_mm = w_mm, h_mm
        self.img = Image.new("RGB", (max(16, round(w_mm * px_per_mm)), max(16, round(h_mm * px_per_mm))), bg)
        self.d = ImageDraw.Draw(self.img)
        self.rng = random.Random(seed)
        self.texts: list[str] = []
        self._quiet = 0  # 0 より大きい間は texts に残さない（1 文字ずつ描く縦書き・バーコードの数字）
        if _RECORDING is not None:
            _RECORDING.append(self)

    def _say(self, s: str) -> None:
        if not self._quiet and s.strip():
            self.texts.append(s.strip())

    @contextmanager
    def _silent(self):
        self._quiet += 1
        try:
            yield
        finally:
            self._quiet -= 1

    # 座標変換
    def p(self, v: float) -> float:
        return v * self.s

    def box(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
        return (x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s)

    # 図形
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=0.0, radius=0.0):
        b = self.box(x0, y0, x1, y1)
        w = max(1, round(width * self.s)) if outline else 0
        if radius:
            self.d.rounded_rectangle(b, radius=radius * self.s, fill=fill, outline=outline, width=w)
        else:
            self.d.rectangle(b, fill=fill, outline=outline, width=w)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, width=0.0):
        self.d.ellipse(self.box(x0, y0, x1, y1), fill=fill, outline=outline,
                       width=max(1, round(width * self.s)) if outline else 0)

    def line(self, pts, fill, width):
        self.d.line([(x * self.s, y * self.s) for x, y in pts], fill=fill, width=max(1, round(width * self.s)))

    def polygon(self, pts, fill=None, outline=None):
        self.d.polygon([(x * self.s, y * self.s) for x, y in pts], fill=fill, outline=outline)

    def gradient(self, x0, y0, x1, y1, top: str, bottom: str, horizontal: bool = False):
        b = [round(v) for v in self.box(x0, y0, x1, y1)]
        w, h = b[2] - b[0], b[3] - b[1]
        if w <= 0 or h <= 0:
            return
        t = np.linspace(0, 1, w if horizontal else h)[None, :, None] if horizontal else np.linspace(0, 1, h)[:, None, None]
        a, c = np.array(rgb(top), np.float32), np.array(rgb(bottom), np.float32)
        g = np.broadcast_to(a + (c - a) * t, (h, w, 3))
        self.img.paste(Image.fromarray(g.astype(np.uint8)), (b[0], b[1]))

    # 文字
    def text(self, x, y, s: str, size: float, fill="#000000", weight=700, anchor="mm", max_w: float | None = None,
             stroke: float = 0.0, stroke_fill: str | None = None, spacing: float = 0.0) -> float:
        """size は文字の高さ [mm]。max_w [mm] を超えるなら小さくする。描いた幅 [mm] を返す。"""
        self._say(s)
        px = max(6, round(size * self.s))
        f = font(px, weight)
        if spacing:
            return self._spaced(x, y, s, f, fill, anchor, spacing)
        if max_w:
            while self.d.textlength(s, font=f) > max_w * self.s and px > 6:
                px = int(px * 0.93)
                f = font(px, weight)
        sw = round(stroke * self.s) if stroke else 0
        self.d.text((x * self.s, y * self.s), s, font=f, fill=fill, anchor=anchor,
                    stroke_width=sw, stroke_fill=stroke_fill)
        return self.d.textlength(s, font=f) / self.s

    def _spaced(self, x, y, s, f, fill, anchor, spacing) -> float:
        widths = [self.d.textlength(ch, font=f) for ch in s]
        total = sum(widths) + spacing * self.s * (len(s) - 1)
        cx = x * self.s - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
        for ch, w in zip(s, widths):
            self.d.text((cx, y * self.s), ch, font=f, fill=fill, anchor="l" + anchor[1])
            cx += w + spacing * self.s
        return total / self.s

    def vtext(self, x, y, s: str, size: float, fill="#000000", weight=900, gap: float = 0.05):
        """縦書き（1 文字ずつ下へ）。(x, y) は 1 文字目の中心。"""
        self._say(s)
        with self._silent():
            for i, ch in enumerate(s):
                self.text(x, y + i * size * (1 + gap), ch, size, fill, weight)

    def wrap(self, s: str, size: float, x0: float, x1: float, weight=400) -> list[str]:
        """x0..x1 の幅で折り返した行（日本語は 1 文字単位）。"""
        f = font(max(6, round(size * self.s)), weight)
        max_w = (x1 - x0) * self.s
        lines = []
        for para in s.split("\n"):
            line = ""
            # 英数字のまとまり（15cm・40℃ など）は分けない。句読点は行頭に置かない
            for tok in re.findall(r"[A-Za-z0-9.,%℃°/+\-]+ ?|.", para):
                if self.d.textlength(line + tok, font=f) > max_w and line.strip() and tok not in "、。，．）」』":
                    lines.append(line.rstrip())
                    line = tok.lstrip()
                else:
                    line += tok
            lines.append(line)
        return lines

    def paragraph(self, x0, y0, x1, s: str, size: float, fill="#333333", weight=400, leading=1.45) -> float:
        """x0..x1 の幅で折り返して書く。最後の行の下端 y [mm] を返す。"""
        self._say(s)
        f = font(max(6, round(size * self.s)), weight)
        y = y0
        for line in self.wrap(s, size, x0, x1, weight):
            self.d.text((x0 * self.s, y * self.s), line, font=f, fill=fill, anchor="lt")
            y += size * leading
        return y

    # 写真
    def photo(self, pid: str, x0, y0, x1, y1, shape: str = "rect", crop=None, radius: float = 0.0,
              feather: float = 0.0, shadow: float = 0.0, border: str | None = None, border_w: float = 0.0):
        """写真を枠に合わせて貼る。shape は rect / round / ellipse。feather [mm] で縁をぼかす。"""
        b = [round(v) for v in self.box(x0, y0, x1, y1)]
        size = (max(1, b[2] - b[0]), max(1, b[3] - b[1]))
        ph = cover(_photo(pid), size, crop)
        mask = Image.new("L", size, 0)
        md = ImageDraw.Draw(mask)
        if shape == "ellipse":
            md.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=255)
        elif shape == "round":
            md.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius * self.s, fill=255)
        else:
            md.rectangle((0, 0, size[0], size[1]), fill=255)
        if feather:
            r = feather * self.s
            mask = mask.resize(size).filter(ImageFilter.GaussianBlur(r / 2))
            if shape == "rect":  # 縁から内側へフェードさせる
                m = np.asarray(mask, np.float32)
                yy, xx = np.mgrid[0:size[1], 0:size[0]]
                edge = np.minimum.reduce([xx, yy, size[0] - 1 - xx, size[1] - 1 - yy]).astype(np.float32)
                mask = Image.fromarray(np.clip(np.minimum(m, edge / max(r, 1) * 255), 0, 255).astype(np.uint8))
        if shadow:
            sh = Image.new("L", self.img.size, 0)
            off = round(shadow * self.s * 0.5)
            sh.paste(mask, (b[0] + off, b[1] + off))
            sh = sh.filter(ImageFilter.GaussianBlur(shadow * self.s))
            dark = Image.new("RGB", self.img.size, "#000000")
            self.img.paste(dark, (0, 0), sh.point(lambda v: int(v * 0.35)))
        self.img.paste(ph, (b[0], b[1]), mask)
        if border:
            w = max(1, round(border_w * self.s))
            if shape == "ellipse":
                self.d.ellipse(b, outline=border, width=w)
            else:
                self.d.rounded_rectangle(b, radius=radius * self.s, outline=border, width=w)

    # 部品
    def barcode(self, x0, y0, w: float, h: float, digits: str | None = None):
        """ダミーの EAN-13（先頭 20〜29 はインストアコードの範囲で、実在の商品コードと重ならない）。"""
        digits = digits or ("2" + str(self.rng.randint(0, 9)) + "".join(str(self.rng.randint(0, 9)) for _ in range(10)))
        digits = digits[:12] + str(ean_check(digits[:12]))
        self.rect(x0 - 1.5, y0 - 1, x0 + w + 1.5, y0 + h + 1, fill="#FFFFFF")
        bits = ean13_bits(digits)
        mod = w / len(bits)
        bar_h, guard_h = h * 0.78, h * 0.86
        guards = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
        for i, b in enumerate(bits):
            if b == "1":
                bh = guard_h if i in guards else bar_h
                self.rect(x0 + i * mod, y0, x0 + (i + 1) * mod, y0 + bh, fill="#111111")
        fs = min(h * 0.15, mod * 7)  # 6 桁が 42 モジュールに収まる大きさまで
        ty = y0 + bar_h + fs * 0.7
        with self._silent():
            self.text(x0 - fs * 0.6, ty, digits[0], fs, "#111111", 400)
            self.text(x0 + 24 * mod, ty, digits[1:7], fs, "#111111", 400, spacing=mod * 1.8)
            self.text(x0 + 71 * mod, ty, digits[7:], fs, "#111111", 400, spacing=mod * 1.8)

    def recycle(self, cx, cy, s: float, label: str, color="#222222", kind: str = "square", sub: str | None = None):
        """識別表示マーク（簡略形）。kind = square（プラ・紙）/ triangle（PET）/ can（アルミ・スチール）。s は一辺 [mm]。"""
        w = s * 0.09
        if kind == "triangle":
            pts = [(cx, cy - s * 0.45), (cx + s * 0.5, cy + s * 0.38), (cx - s * 0.5, cy + s * 0.38)]
            for k in range(3):
                a, b = pts[k], pts[(k + 1) % 3]
                m = (a[0] + (b[0] - a[0]) * 0.78, a[1] + (b[1] - a[1]) * 0.78)
                st = (a[0] + (b[0] - a[0]) * 0.12, a[1] + (b[1] - a[1]) * 0.12)
                self.line([st, m], color, w)
                self._arrow_head(m, (b[0] - a[0], b[1] - a[1]), s * 0.16, color)
            self.text(cx, cy + s * 0.08, "1", s * 0.32, color, 700)
            self.text(cx, cy + s * 0.68, label, s * 0.26, color, 700)
            return
        hw, hh = s * 0.5, s * (0.5 if kind == "square" else 0.62)
        x0, y0, x1, y1 = cx - hw, cy - hh, cx + hw, cy + hh
        r = s * 0.14
        # 左上から時計回りの角丸の四角を、2 か所切って矢印にする
        self.d.rounded_rectangle(self.box(x0, y0, x1, y1), radius=r * self.s, outline=color,
                                 width=max(1, round(w * self.s)))
        gap = s * 0.16
        for (gx, gy), dirv in (((cx, y0), (1, 0)), ((cx, y1), (-1, 0))):
            self.rect(gx - gap / 2, gy - w, gx + gap / 2, gy + w, fill=self._bg_at(gx, gy - w * 2))
            self._arrow_head((gx - dirv[0] * gap / 2 + dirv[0] * s * 0.06, gy), dirv, s * 0.16, color)
        self.text(cx, cy, label, s * (0.34 if len(label) <= 2 else 0.26), color, 700, max_w=hw * 1.7)
        if sub:
            self.text(cx, y1 + s * 0.22, sub, s * 0.2, color, 500)

    def _bg_at(self, x, y) -> tuple[int, int, int]:
        px = (min(max(0, round(x * self.s)), self.img.width - 1), min(max(0, round(y * self.s)), self.img.height - 1))
        return self.img.getpixel(px)

    def _arrow_head(self, tip, direction, size, color):
        dx, dy = direction
        n = math.hypot(dx, dy) or 1
        dx, dy = dx / n, dy / n
        px, py = -dy, dx
        x, y = tip
        self.polygon([(x + dx * size * 0.6, y + dy * size * 0.6),
                      (x - dx * size * 0.4 + px * size * 0.45, y - dy * size * 0.4 + py * size * 0.45),
                      (x - dx * size * 0.4 - px * size * 0.45, y - dy * size * 0.4 - py * size * 0.45)], fill=color)

    def table(self, x0, y0, x1, title: str, rows: list[tuple[str, str]], size: float, color="#222222",
              bg="#FFFFFF") -> float:
        """罫線付きの表（一括表示・栄養成分表示）。下端 y [mm] を返す。"""
        lh, lead = size * 1.6, 1.45  # 1 行の高さ、値を折り返したときの行送り
        key_w = max(len(k) for k, _ in rows) * size * 1.05 + size * 0.8 if rows else 0
        n_lines = [len(self.wrap(v, size, x0 + key_w, x1 - size * 0.3)) for _, v in rows]
        row_h = [lh + (n - 1) * size * lead for n in n_lines]
        h = sum(row_h) + (lh if title else 0) + size * 0.4
        self.rect(x0, y0, x1, y0 + h, fill=bg, outline=color, width=size * 0.08)
        y = y0 + size * 0.2
        if title:
            self.text((x0 + x1) / 2, y + lh / 2, title, size, color, 700)
            y += lh
            self.line([(x0, y), (x1, y)], color, size * 0.06)
        for (k, v), rh in zip(rows, row_h):
            self.text(x0 + size * 0.4, y + lh / 2, k, size, color, 600, anchor="lm")
            self.paragraph(x0 + key_w, y + (lh - size) / 2 - size * 0.05, x1 - size * 0.3, v, size, color, 400, lead)
            y += rh
        return y0 + h

    def pattern(self, x0, y0, x1, y1, kind: str, color: str, step: float, width: float = 0.4):
        if kind == "dots":
            yy = y0 + step / 2
            row = 0
            while yy < y1:
                xx = x0 + step / 2 + (step / 2 if row % 2 else 0)
                while xx < x1:
                    self.ellipse(xx - width, yy - width, xx + width, yy + width, fill=color)
                    xx += step
                yy += step
                row += 1
        elif kind == "stripes":
            xx = x0 - (y1 - y0)
            while xx < x1:
                self.line([(xx, y1), (xx + (y1 - y0), y0)], color, width)
                xx += step
        elif kind == "waves":
            yy = y0 + step / 2
            while yy < y1:
                pts = [(x, yy + step * 0.18 * math.sin(x / step * 2 * math.pi)) for x in np.arange(x0, x1, step / 8)]
                self.line(pts, color, width)
                yy += step

    def array(self) -> np.ndarray:
        return np.asarray(self.img)


# ---------------------------------------------------------------- バーコード


L_CODES = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
R_CODES = ["".join("1" if b == "0" else "0" for b in c) for c in L_CODES]
G_CODES = [c[::-1] for c in R_CODES]
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def ean_check(d12: str) -> int:
    s = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(d12))
    return (10 - s % 10) % 10


def ean13_bits(d: str) -> str:
    par = PARITY[int(d[0])]
    left = "".join((L_CODES if p == "L" else G_CODES)[int(c)] for p, c in zip(par, d[1:7]))
    right = "".join(R_CODES[int(c)] for c in d[7:13])
    return "101" + left + "01010" + right + "101"


# ---------------------------------------------------------------- 質感（描き終えた画像に重ねる）


def _noise(shape: tuple[int, int], seed: int, scale: float) -> np.ndarray:
    """低周波のノイズ（-1〜1）。scale は模様の大きさ [px]。"""
    rng = np.random.default_rng(seed)
    h, w = shape
    sh, sw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
    small = Image.fromarray(((rng.random((sh, sw)) * 255)).astype(np.uint8))
    big = np.asarray(small.resize((w, h), Image.BICUBIC), np.float32) / 127.5 - 1
    return big


def finish(img: np.ndarray, kind: str, seed: int = 0, strength: float = 1.0) -> np.ndarray:
    """紙（paper）・フィルム（film）・金属（metal）・画面（screen）の質感を足す。"""
    a = img.astype(np.float32)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    if kind == "paper":
        grain = rng.normal(0, 3.0, (h, w, 1))
        mottle = _noise((h, w), seed, max(h, w) / 12)[..., None] * 4.0
        fibers = np.asarray(Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8))
                            .filter(ImageFilter.BoxBlur(1)), np.float32)[..., None] / 255 - 0.5
        a = a + (grain + mottle + fibers * 6.0) * strength
    elif kind == "film":
        grain = rng.normal(0, 1.8, (h, w, 1))
        crinkle = _noise((h, max(2, w // 6)), seed, max(4, h / 30))
        crinkle = np.asarray(Image.fromarray(((crinkle + 1) * 127.5).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                             np.float32)[..., None] / 127.5 - 1
        sheen = np.sin(np.linspace(0, 3 * np.pi, w))[None, :, None] * 0.5 + 0.5
        a = a * (1 + 0.06 * crinkle * strength) + (grain + sheen * 10 * strength)
    elif kind == "metal":
        streak = rng.normal(0, 1, (h, 1, 1)) * 5.0 + rng.normal(0, 2.0, (h, w, 1))
        a = a + streak * strength
    elif kind == "screen":
        # 画素の格子（ごく弱く）と、左上からの映り込み
        yy, xx = np.mgrid[0:h, 0:w]
        glare = np.clip(1 - (xx / w + yy / h) * 0.9, 0, 1)[..., None] ** 3 * 18 * strength
        a = a + glare
    return np.clip(a, 0, 255).astype(np.uint8)


def edge_shade(img: np.ndarray, px: int, amount: float = 0.12) -> np.ndarray:
    """面の縁を少し暗くする（折り目・シールの陰）。"""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]).astype(np.float32)
    k = 1 - amount * np.clip(1 - d / max(px, 1), 0, 1) ** 2
    return np.clip(img.astype(np.float32) * k[..., None], 0, 255).astype(np.uint8)


def trim_safe(img: np.ndarray) -> np.ndarray:
    """生成側の trim_background で切り抜かれない（縁が単色に見えない）ことを確かめる。"""
    from ..shapes.pouch import trim_background

    t = trim_background(img)
    if t.shape != img.shape:
        raise ValueError(f"縁が単色のため切り抜かれます（{img.shape[:2]} → {t.shape[:2]}）")
    return img
