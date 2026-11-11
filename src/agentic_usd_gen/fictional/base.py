"""架空の商品の定義（Product）と、生成に使うキャッシュ（spec.json・vision.json・images/）の書き出し。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from ..spec import Colors, Dimensions, Joint, Light, Part, ProductSpec, cache_key
from .forms import RevolveForm, draw_silhouette
from .paint import FONT_LICENSE, Canvas, photo_credit

NOTICE = "架空の商品です。実在の会社・商品とは関係ありません。"
FONT_CREDIT = {"subject": "書体", "title": "Noto Sans JP", "url": "https://fonts.google.com/noto/specimen/Noto+Sans+JP",
               "author": "Google / Adobe", "license": "SIL Open Font License 1.1",
               "license_url": "https://openfontlicense.org/open-font-license-official-text/"}
COMMON_TAGS = ["架空のパッケージ", "fictional"]


@dataclass
class Product:
    slug: str
    name: str
    shape_class: str
    category: str
    dims: Dimensions
    mass_kg: float
    images: list[np.ndarray]
    description: str  # 形と寸法の根拠（一般的な値であること）
    tags: list[str]
    photos: list[str] = field(default_factory=list)  # 合成した写真の ID（paint.photo_manifest）
    material: str | None = None
    capacity_ml: float | None = None
    orientation: str = "upright"
    colors: Colors = field(default_factory=Colors)
    faces: dict | None = None
    landmarks: dict | None = None
    parts: list[Part] = field(default_factory=list)
    static: bool = False
    mount: str = "floor"  # spec.MOUNTS
    joints: list[Joint] = field(default_factory=list)
    lights: list[Light] = field(default_factory=list)  # 内蔵の照明（Lighting バリアント）
    picture_places: list[str] = field(default_factory=list)  # 部品の blank の絵柄が合う場所（Picture バリアント）
    screen_places: list[str] = field(default_factory=list)  # 光る画面の画像が合う場所（Screen バリアント、"any" はどこでも）
    variant_sets: dict[str, list[str]] = field(default_factory=dict)  # 部品の出し入れのバリアント（Part.show）

    def spec(self) -> ProductSpec:
        notes = (f"{NOTICE}{self.description}"
                 f"テクスチャは agentic-usd-gen-fictional で描いたもので、写真はパブリックドメイン（CC0 など）の素材、書体は {FONT_LICENSE}。")
        return ProductSpec(
            product_name=self.name, slug=self.slug, shape_class=self.shape_class, dimensions=self.dims,
            capacity_ml=self.capacity_ml, mass_kg=self.mass_kg, container_material=self.material,
            orientation=self.orientation, category=self.category, colors=self.colors, notes=notes,
            parts=self.parts, joints=self.joints, lights=self.lights, static=self.static, mount=self.mount, picture_places=self.picture_places, screen_places=self.screen_places, variant_sets=self.variant_sets, tags=[*self.tags, *COMMON_TAGS], fictional=True,
            image_credits=[photo_credit(p) for p in dict.fromkeys(self.photos)] + [FONT_CREDIT],
        )


TEXT_SUFFIX = ".text.json"  # 画像 NN.png に描いた文字（NN.text.json）。絵柄のマテリアルの asset.json に写す
TEXT_MATCH = 24.0  # 画像と Canvas の画素の差（平均、0〜255）がこれ未満なら同じ絵（_face などの仕上げの分を許す）
AUDIENCE = (("men", ("メンズ", "紳士", "MEN'S", "MENS")), ("women", ("レディース", "婦人", "LADIES", "WOMEN")),
            ("kids", ("キッズ", "子ども", "こども", "子供", "KIDS")), ("baby", ("ベビー", "BABY")))


def lang_of(lines: list[str]) -> str:
    """ja（かな・漢字を含む）か en。"""
    return "ja" if any(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", x) for x in lines) else "en"


def audience_of(lines: list[str]) -> list[str]:
    """文字から分かる客層（men・women・kids・baby）。"""
    joined = " ".join(lines)
    up = joined.upper()
    def has(w: str) -> bool:  # 英語は語の途中に当てない（WOMEN'S の MEN'S）
        return bool(re.search(rf"(?<![A-Z]){re.escape(w)}(?![A-Z])", up)) if w.isascii() else w in joined

    return [k for k, words in AUDIENCE if any(has(w) for w in words)]


def image_texts(images: list[np.ndarray], canvases) -> dict[int, dict]:
    """画像の番号 → {text, lang, audience?}。描いた Canvas（paint.recording）のうち同じ大きさで画素が最も近いものの文字。"""
    out = {}
    for i, a in enumerate(images):
        best, err = None, TEXT_MATCH
        for c in canvases or []:
            if not c.texts:
                continue
            b = c.array()
            if b.shape[:2] != a.shape[:2]:
                continue
            e = float(np.abs(a[..., :3].astype(np.int16) - b[..., :3].astype(np.int16)).mean())
            if e < err:
                best, err = c, e
        if best is not None:
            lines = list(dict.fromkeys(best.texts))
            aud = audience_of(lines)
            out[i] = {"text": lines, "lang": lang_of(lines), **({"audience": aud} if aud else {})}
    return out


def write(product: Product, cache_root: Path, canvases=None) -> Path:
    """キャッシュを書き、そのディレクトリを返す。前回の画像のうち使わなくなった番号は消す。

    canvases（paint.recording で集めた Canvas）を渡すと、各画像に描いた文字を images/NN.text.json に書く。"""
    cache_dir = cache_root / cache_key(product.name)
    img_dir = cache_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, a in enumerate(product.images):
        p = img_dir / f"{i:02d}.png"
        Image.fromarray(a).save(p)
        paths.append(str(p.resolve()))
    for old in img_dir.glob("*.png"):
        if old.stem.isdigit() and int(old.stem) >= len(product.images):
            old.unlink()
    for old in img_dir.glob("*" + TEXT_SUFFIX):
        old.unlink()
    for i, t in image_texts(product.images, canvases).items():
        (img_dir / f"{i:02d}{TEXT_SUFFIX}").write_text(json.dumps(t, ensure_ascii=False, indent=2))
    product.spec().save(cache_dir / "spec.json")
    vision = {
        "images": paths,
        "best_index": 0,
        "landmarks": product.landmarks or {"cap_bottom": None, "label_top": None, "label_bottom": None,
                                           "liquid_top": None},
        "reason": "agentic-usd-gen-fictional が生成した架空のパッケージ",
    }
    if product.faces:
        vision["faces"] = product.faces
    (cache_dir / "vision.json").write_text(json.dumps(vision, ensure_ascii=False, indent=2))
    (img_dir / "sources.tsv").write_text(
        "index\turl\n" + "".join(f"{i}\tgenerated (agentic-usd-gen-fictional)\n" for i in range(len(paths))))
    return cache_dir


# ---------------------------------------------------------------- 回転体の補助


def label_canvas(form: RevolveForm, bg: str, seed: int = 0) -> Canvas:
    """全周ラベルのキャンバス（mm）。横 = 胴の円周、正面の中心は x = 0.75 × 幅、裏面は 0.25 × 幅。
    画素密度は円周の実寸から決める（texres）。"""
    z0, z1 = form.label
    return Canvas(form.label_circumference() * 1000, (z1 - z0) * 1000, None, bg, seed)


def top_canvas(form: RevolveForm, bg: str, seed: int = 0) -> Canvas:
    """キャップ（蓋）上面のキャンバス（mm）。画像の下が正面。画素密度は直径の実寸から決める（texres）。"""
    d_mm = 2 * max(r for _, r in form.cap) * 1000
    return Canvas(d_mm, d_mm, None, bg, seed)


def revolve(form: RevolveForm, *, label: np.ndarray, top: np.ndarray | None = None, body_fill: str | None = "#8C8C8C",
            liquid: str | None = None, depth: float | None = None, **kw) -> dict:
    """回転体の Product に渡す images・faces・landmarks・dims。

    depth（m）を胴の直径より小さくすると、断面が楕円の平たいボトルになる（横幅 = 直径、奥行き = depth）。
    ラベルの正面・裏面は平らな広い面に来る。キャップは丸のまま。
    """
    images = [draw_silhouette(form, body_fill, liquid=liquid), label]
    faces = {"side": 1}
    if top is not None:
        images.append(top)
        faces["top"] = 2
    cap_r = max(r for _, r in form.cap)
    dims = Dimensions(round(form.height, 4), round(form.diameter, 4), round(form.height - form.cap_z, 4),
                      round(2 * cap_r, 4), round(depth, 4) if depth else None, form.square,
                      form.lobes)
    return {"images": images, "faces": faces, "landmarks": form.landmarks(), "dims": dims, "shape_class": "revolve", **kw}
