"""箱（菓子箱・ティッシュ箱・紙パックなど）の生成。

幅 W（diameter）× 奥行き D（depth）× 高さ H の直方体を作り、各面に画像を貼る。
正面（-Y）には best の画像を使う。vision.json の faces に他の面の画像番号があればそれも貼り、
画像のない面はラベル地の色（なければ正面画像の縁の色）で塗る。
spec.json に parts があれば本体に部品（刃・取っ手など）を足す（assembly.attach_parts）。
角は Blender で面取りする（見た目だけ。幅は spec.json の bevel、既定 0.8 mm）。
"""

from __future__ import annotations

import json
import logging

import numpy as np
from PIL import Image

from ..blender_runner import run_script
from ..semantics import container_labels
from ..texres import record, texture_px
from .pouch import trim_background
from .revolve import BuildContext, BuildResult

log = logging.getLogger(__name__)

FACES = ("front", "right", "back", "left", "top", "bottom")
CELL = 1024  # 画像を貼らない箱のセルの画素数（UV の内側の余白を決めるだけ）
MAX_CELL = 2048  # 画像を貼る面のセルの上限。テクスチャ全体は横 3 × 縦 2 セル（最大 6144 × 4096）
GRID = (3, 2)  # テクスチャの面の並び（横 3 × 縦 2、FACES の順に左上から）
BOX_BEVEL = 0.0008  # 箱の本体の角の面取りの幅の既定値 [m]（紙箱の折り目くらい）
PART_BEVEL = 0.0015  # box 部品の面取りの幅の既定値 [m]（什器の板金・樹脂の角くらい）


def bevel_width(requested: float | None, size, default: float) -> float:
    """面取りの幅 [m]。未指定なら default を、いちばん短い辺の 1 割までに抑える。指定値は 1/4 まで（角が潰れないように）。"""
    shortest = min(size)
    if requested is None:
        return min(default, 0.1 * shortest)
    return max(0.0, min(requested, 0.25 * shortest))


def face_layout(W: float, D: float, H: float) -> dict[str, tuple[list[tuple[float, float, float]], tuple[float, float]]]:
    """各面の 4 隅（外から見て左下・右下・右上・左上）と、画像の縦横の実寸。

    正面は -Y、右面は +X。上面は正面側を手前（画像の下）、底面は正面側を奥（画像の上）にして見る。
    """
    a, b = W / 2, D / 2
    return {
        "front": ([(-a, -b, 0), (a, -b, 0), (a, -b, H), (-a, -b, H)], (W, H)),
        "right": ([(a, -b, 0), (a, b, 0), (a, b, H), (a, -b, H)], (D, H)),
        "back": ([(a, b, 0), (-a, b, 0), (-a, b, H), (a, b, H)], (W, H)),
        "left": ([(-a, b, 0), (-a, -b, 0), (-a, -b, H), (-a, b, H)], (D, H)),
        "top": ([(-a, -b, H), (a, -b, H), (a, b, H), (-a, b, H)], (W, D)),
        "bottom": ([(-a, b, 0), (a, b, 0), (a, -b, 0), (-a, -b, 0)], (W, D)),
    }


def cell_size(layout: dict, images: dict[str, np.ndarray]) -> tuple[int, float]:
    """画像を貼る面のセルの画素数と、その基準にした面のいちばん長い辺 [m]。

    セルは正方形で全部の面で同じ大きさなので、画像を貼る面のうちいちばん長い辺に密度を合わせる（texres）。
    """
    if not images:
        return CELL, 0.0
    length = max(max(layout[name][1]) for name in images)
    source = max(max(img.shape[:2]) for img in images.values())
    return texture_px(length, source, MAX_CELL), length


def cell_uv(index: int, cell: int = CELL) -> tuple[float, float, float, float]:
    """テクスチャ上の面のセル（u0, v0, u1, v1）。隣のセルがにじまないよう半画素内側にする。"""
    cols, rows = GRID
    col, row = index % cols, index // cols
    pad_u, pad_v = 0.5 / (cell * cols), 0.5 / (cell * rows)
    u0, u1 = col / cols + pad_u, (col + 1) / cols - pad_u
    v1, v0 = 1 - row / rows - pad_v, 1 - (row + 1) / rows + pad_v  # 画像の上端が v=1
    return u0, v0, u1, v1


def box_mesh(W: float, D: float, H: float, cell: int = CELL) -> dict:
    """閉じた直方体（頂点 8 個を共有）。UV は面ごとにテクスチャのセルへ割り当てる。"""
    layout = face_layout(W, D, H)
    verts: list[tuple[float, float, float]] = []
    faces, uvs = [], []
    for i, name in enumerate(FACES):
        corners, _ = layout[name]
        idx = []
        for c in corners:
            c = tuple(float(x) for x in c)
            if c not in verts:
                verts.append(c)
            idx.append(verts.index(c))
        faces.append(idx)
        u0, v0, u1, v1 = cell_uv(i, cell)
        uvs.append([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
    return {"vertices": [list(v) for v in verts], "faces": faces, "uvs": uvs}


def make_texture(images: dict[str, np.ndarray], fill: tuple[int, int, int], cell: int = CELL) -> np.ndarray:
    """面ごとの画像を GRID のセル（一辺 cell 画素）に並べたテクスチャ。画像のない面は fill で塗る。"""
    cols, rows = GRID
    tex = np.empty((cell * rows, cell * cols, 3), np.uint8)
    tex[:] = fill
    for i, name in enumerate(FACES):
        if name in images:
            col, row = i % cols, i // cols
            img = Image.fromarray(images[name]).resize((cell, cell), Image.LANCZOS)
            tex[row * cell : (row + 1) * cell, col * cell : (col + 1) * cell] = np.asarray(img)
    return tex


def border_color(img: np.ndarray) -> tuple[int, int, int]:
    border = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
    return tuple(int(c) for c in np.median(border, axis=0))


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


class BoxBuilder:
    def build(self, ctx: BuildContext) -> BuildResult:
        spec = ctx.spec
        W, H = spec.dimensions.diameter, spec.dimensions.height
        warnings: list[str] = []
        D = spec.dimensions.depth
        if not D:
            D = W
            warnings.append("奥行きが不明なため幅と同じと仮定しました")
        tex_dir = ctx.out_dir / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        ctx.debug_dir.mkdir(parents=True, exist_ok=True)
        layout = face_layout(W, D, H)

        # 面 → 画像番号。正面は faces の指定、なければ best、なければ 1 枚目
        face_index = dict(ctx.faces or {})
        if "front" not in face_index and ctx.images:
            face_index["front"] = ctx.preferred_image if ctx.preferred_image is not None else 0
        face_images: dict[str, np.ndarray] = {}
        for name, i in face_index.items():
            if name not in FACES:
                warnings.append(f"未知の面 '{name}' を無視しました（使えるのは {', '.join(FACES)}）")
                continue
            if i is None or not 0 <= i < len(ctx.images):
                continue
            img = trim_background(np.asarray(Image.open(ctx.images[i]).convert("RGB")))
            fw, fh = layout[name][1]
            aspect = img.shape[1] / img.shape[0]
            if abs(aspect / (fw / fh) - 1) > 0.1:
                warnings.append(f"{name} の画像の縦横比 {aspect:.3f} が寸法 {fw / fh:.3f} と 10% 以上ずれています")
            face_images[name] = img

        if spec.colors.label_base:
            fill = hex_to_rgb(spec.colors.label_base)
        elif "front" in face_images:
            fill = border_color(face_images["front"])
        else:
            fill = (204, 204, 204)
        fill_hex = "#%02X%02X%02X" % fill
        labels = container_labels(spec.container_material, "paper")
        materials = {"BoxMat": {"role": "label", "labels": labels, "color": fill_hex}}
        cell, cell_len = cell_size(layout, face_images)
        tex_meta: dict = {}
        if face_images:
            tex_path = tex_dir / "label.png"
            tex = make_texture(face_images, fill, cell)
            Image.fromarray(tex).save(tex_path)
            record(tex_meta, "label.png", tex.shape[1::-1], cell, cell_len)
            materials["BoxMat"].update(texture=str(tex_path.resolve()), texture_rel="./textures/label.png")
        else:
            warnings.append("画像がないため無地の箱にしました")

        mesh = box_mesh(W, D, H, cell)
        objects = [{"name": "Body", "vertices": mesh["vertices"], "faces": mesh["faces"], "uvs": mesh["uvs"],
                    "material": "BoxMat", "bevel": bevel_width(spec.bevel, (W, D, H), BOX_BEVEL)}]
        com, expected, colliders, part_images = (0.0, 0.0, H / 2), (W, D, H), ["Body"], {}
        if spec.parts:
            from .assembly import attach_parts  # assembly が box を import するので循環を避ける

            att = attach_parts(ctx, (-W / 2, -D / 2, 0.0), (W / 2, D / 2, H), {"Body"}, warnings, tex_dir)
            objects[0]["vertices"] = (np.asarray(mesh["vertices"]) + att["shift"]).tolist()
            objects += att["objects"]
            materials.update(att["materials"])
            com = tuple(float(c) for c in np.asarray(com) + att["shift"])
            expected, colliders, part_images = att["size"], colliders + att["colliders"], att["images"]
            if att["textures"]:
                tex_meta.setdefault("textures", {}).update(att["textures"])
        for w in warnings:
            log.warning(w)
        usd_path = ctx.out_dir / f"{spec.slug}.usd"
        build = {
            "root_name": spec.slug,
            "objects": objects,
            "materials": materials,
            "usd_path": str(usd_path.resolve()),
            "blend_path": str((ctx.debug_dir / "model.blend").resolve()),
        }
        build_json = ctx.debug_dir / "build.json"
        build_json.write_text(json.dumps(build))
        run_script(ctx.blender, "build_mesh.py", build_json.resolve(), log_path=ctx.debug_dir / "blender_build.log")

        return BuildResult(
            usd_path=usd_path,
            root_name=spec.slug,
            mass=spec.total_mass_kg(),
            center_of_mass=com,
            colliders=colliders,
            materials=materials,
            double_sided=[],
            physics_labels=labels,
            meta={"image": {n: str(ctx.images[face_index[n]]) for n in face_images} | part_images,
                  "warnings": warnings, **({"textures": tex_meta["textures"]} if tex_meta else {}),
                  "profile": {"faces": sorted(face_images), "expected_size": expected,
                              **({"parts": [o["name"] for o in objects[1:]]} if spec.parts else {})},
                  "colors": {"label_base": fill_hex}},
        )
