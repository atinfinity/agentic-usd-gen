"""袋（ピロー包装: ポテトチップスなど）の生成。

平らな袋（幅 W × 高さ H のフィルム）が中身で膨らんだ形を作る。
- 上下の端はシール（厚さ 0）。そこから中央に向かって厚くなり、中央で最大厚さ depth になる
- 各高さの断面は、表と裏が円弧のレンズ形。円弧の長さはフィルム幅 W のまま保つので、膨らむほど見かけの幅が縮む
- 高さ方向も同様に、中心線の長さが H のまま保たれるよう縮める
正面の写真を表面に、裏面画像があれば裏面に（なければ正面を流用して）貼る。
裏面画像は vision.json の faces の back で指定する（front で正面の画像番号も指定できる）。
spec.json に parts があれば本体に部品（フタなど）を足す（assembly.attach_parts）。

dimensions.gusset（底マチ）があれば底を閉じた平らな面にする（米袋などの自立する袋）。底の厚さが gusset で、
そこから上のシールに向かって薄くなる。dimensions.square（超楕円の指数）があれば断面を円弧のレンズ形ではなく
角の丸い四角にする（マチのある袋の箱に近い胴）。どちらもフィルムの幅 W は断面の周の半分のまま保つ。

orientation が "lying" なら、シールを左右に向けて正面を上にして寝かせる（チョコバーなど横長の袋）。
このとき画像はシールが左右にある横長の向きのまま使う。
"""

from __future__ import annotations

import json
import logging

import numpy as np
from PIL import Image

from ..blender_runner import run_script
from ..semantics import container_labels
from ..texres import record, texture_px
from .revolve import BuildContext, BuildResult

log = logging.getLogger(__name__)

NU = 48  # 幅方向の分割数（片面）
NV = 96  # 高さ方向の分割数
SEAL = 0.012  # 上下シールの幅 [m]
SEAL_HALF = 0.0003  # シール部の半厚（表裏の面が重ならないよう少しだけ離す）[m]
BULGE_EXP = 0.6  # 厚さの立ち上がり（小さいほど肩が張る）
DEFAULT_DEPTH_RATIO = 0.22  # 厚さが不明なときの幅に対する比率


def half_thickness(sv: np.ndarray, H: float, depth: float, gusset: float | None = None) -> np.ndarray:
    """高さ方向の弧長 sv（0..H）での半厚。両端は 0。
    gusset（底マチの厚さ）があれば、底（sv = 0）は半厚 gusset / 2 の平らな底で、上のシールだけが 0 になる。"""
    if not gusset:
        p = np.clip((sv - SEAL) / (H - 2 * SEAL), 0, 1)
    else:
        # sin の山の途中（厚さが gusset になる位置 p0 ≤ 0.5）から始め、上のシールで 0 にする
        p0 = np.arcsin(min(gusset / depth, 1.0) ** (1 / BULGE_EXP)) / np.pi
        p = p0 + (1 - p0) * np.clip(sv / (H - SEAL), 0, 1)
    t = 0.5 * depth * np.sin(np.pi * p) ** BULGE_EXP
    t = np.maximum(t, SEAL_HALF)
    t[sv >= H] = 0.0
    if not gusset:
        t[sv <= 0] = 0.0
    return t


def lens_angle(L: float, t: float) -> float:
    """弧長 L・矢高 t の円弧の半角 θ を二分法で求める（t/L = (1-cosθ)/(2θ)）。"""
    if t <= 0:
        return 0.0
    target = t / L
    lo, hi = 1e-9, np.pi - 1e-9
    for _ in range(80):
        mid = (lo + hi) / 2
        if (1 - np.cos(mid)) / (2 * mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def arc_xy(L: float, t: float, a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """弧長比 a（0..1、左端→右端）での円弧上の点 (x, y)。y は弦からの膨らみ（端で 0、中央で t）。"""
    th = lens_angle(L, t)
    if th == 0:
        return (a - 0.5) * L, np.zeros_like(a)
    R = L / (2 * th)
    phi = th * (2 * a - 1)
    return R * np.sin(phi), R * (np.cos(phi) - np.cos(th))


def superellipse_xy(L: float, t: float, a: np.ndarray, n: float) -> tuple[np.ndarray, np.ndarray]:
    """弧長 L の超楕円の半分（|x/A|^n + |y/t|^n = 1 の y ≥ 0 側）上で、弧長比 a（0..1、左端→右端）の点 (x, y)。
    半幅 A は弧長が L になるよう二分法で決める。t が 0 なら平らな線分。"""
    if t <= 0:
        return (a - 0.5) * L, np.zeros_like(a)
    th = np.linspace(np.pi, 0, 2001)  # 左端（θ = π）から右端へ
    ux = np.sign(np.cos(th)) * np.abs(np.cos(th)) ** (2 / n)
    uy = np.abs(np.sin(th)) ** (2 / n)

    def length(A):
        return float(np.sum(np.hypot(np.diff(A * ux), np.diff(t * uy))))

    lo, hi = 0.0, L / 2
    for _ in range(60):
        mid = (lo + hi) / 2
        if length(mid) < L:
            lo = mid
        else:
            hi = mid
    A = (lo + hi) / 2
    x, y = A * ux, t * uy
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    return np.interp(a * s[-1], s, x), np.interp(a * s[-1], s, y)


def pouch_mesh(W: float, H: float, depth: float, gusset: float | None = None, square: float | None = None) -> dict:
    """閉じた袋のメッシュ。戻り値は vertices / faces / uvs（面ごと）/ 断面積から求めた重心 z。
    gusset（底マチの厚さ [m]）があれば底を平らな面で閉じる。square（超楕円の指数）があれば断面を角の丸い四角にする。"""
    sv = np.linspace(0, H, NV + 1)
    t = half_thickness(sv, H, depth, gusset)
    # 中心線の弧長を保って z を決める
    dz = np.sqrt(np.maximum(np.diff(sv) ** 2 - np.diff(t) ** 2, 0))
    z = np.concatenate([[0], np.cumsum(dz)])
    a = np.linspace(0, 1, NU + 1)

    xs = np.zeros((NV + 1, NU + 1))
    ys = np.zeros((NV + 1, NU + 1))
    area = np.zeros(NV + 1)
    for j in range(NV + 1):
        xs[j], ys[j] = superellipse_xy(W, t[j], a, square) if square and square != 2 else arc_xy(W, t[j], a)
        area[j] = 2 * np.trapezoid(ys[j], xs[j])  # 表裏 2 枚の円弧で囲まれる面積

    # 頂点: 表面（y = -膨らみ、-Y が正面）は全点、裏面は外周（左右端・上下端）を表面と共有
    verts: list[list[float]] = []
    front = np.zeros((NV + 1, NU + 1), int)
    for j in range(NV + 1):
        for i in range(NU + 1):
            front[j, i] = len(verts)
            verts.append([xs[j, i], -ys[j, i], z[j]])
    back = front.copy()
    for j in range(0 if gusset else 1, NV):  # 底マチがあれば底の縁も表裏で分ける
        for i in range(1, NU):
            back[j, i] = len(verts)
            verts.append([xs[j, i], ys[j, i], z[j]])

    faces, uvs = [], []
    v = sv / H
    for j in range(NV):
        for i in range(NU):
            # 表: テクスチャの左半分。裏: 右半分（裏から見て左が +X なので左右反転）
            faces.append([front[j, i], front[j, i + 1], front[j + 1, i + 1], front[j + 1, i]])
            uvs.append([[0.5 * a[i], v[j]], [0.5 * a[i + 1], v[j]], [0.5 * a[i + 1], v[j + 1]], [0.5 * a[i], v[j + 1]]])
            faces.append([back[j, i], back[j + 1, i], back[j + 1, i + 1], back[j, i + 1]])
            ub0, ub1 = 0.5 + 0.5 * (1 - a[i]), 0.5 + 0.5 * (1 - a[i + 1])
            uvs.append([[ub0, v[j]], [ub0, v[j + 1]], [ub1, v[j + 1]], [ub1, v[j]]])
    if gusset:
        # 底: 表と裏の縁を結ぶ面（下向き）。左右の端は表裏が同じ頂点なので三角形。色は正面の下端の帯
        for i in range(NU):
            quad = [front[0, i], back[0, i], back[0, i + 1], front[0, i + 1]]
            uv = [[0.5 * a[i], 0.0], [0.5 * a[i], 0.002], [0.5 * a[i + 1], 0.002], [0.5 * a[i + 1], 0.0]]
            keep = [k for k in range(4) if k == 0 or quad[k] != quad[k - 1]]
            if quad[keep[-1]] == quad[0]:
                keep.pop()
            faces.append([quad[k] for k in keep])
            uvs.append([uv[k] for k in keep])

    com_z = float(np.trapezoid(area * z, z) / np.trapezoid(area, z))
    return {
        "vertices": [[float(c) for c in p] for p in verts],
        "faces": [[int(i) for i in f] for f in faces],
        "uvs": uvs,
        "com_z": com_z,
        "size": (float(xs.max() - xs.min()), float(2 * ys.max()), float(z[-1])),
    }


def lay_flat(mesh: dict) -> dict:
    """立てた袋を、正面（-Y）が上（+Z）、シールが左右（±X）になるよう寝かせる。原点は底面の中心のまま。

    (x, y, z) → (z - 高さ/2, -x, -y + 半厚)。行列式 +1 の回転なので面の向きは変わらない。
    立てた袋の画像の左端（-X）が寝かせた袋の奥（+Y）、下端が左（-X）に来るので、
    上から見ると横長の画像がそのまま読める向きになる。
    """
    sx, sy, sz = mesh["size"]
    v = np.asarray(mesh["vertices"])
    flat = np.stack([v[:, 2] - sz / 2, -v[:, 0], -v[:, 1] + sy / 2], axis=1)
    return {**mesh, "vertices": [[float(c) for c in p] for p in flat],
            "com": (mesh["com_z"] - sz / 2, 0.0, sy / 2), "size": (sz, sx, sy)}


def trim_background(rgb: np.ndarray, tol: float = 18.0) -> np.ndarray:
    """周囲が単色の背景なら商品部分だけを切り出す。袋いっぱいに写っている画像はそのまま返す。"""
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float32)
    bg = np.median(border, axis=0)
    if np.mean(np.linalg.norm(border - bg, axis=1) < tol) < 0.9:
        return rgb
    mask = np.linalg.norm(rgb.astype(np.float32) - bg, axis=2) > tol
    ys, xs = np.nonzero(mask)
    if ys.size < 0.05 * mask.size:
        return rgb
    return rgb[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]


def make_texture(front: np.ndarray, back: np.ndarray | None, W: float, H: float) -> np.ndarray:
    """表と裏を横に並べたテクスチャ（左半分が表）。高さの画素数は袋の長さ H [m] から決める（texres）。"""
    imgs = (front, back if back is not None else front)
    th = texture_px(H, min(img.shape[0] for img in imgs))
    w = max(16, int(th * W / H))
    halves = [np.asarray(Image.fromarray(img).resize((w, th), Image.LANCZOS)) for img in imgs]
    return np.concatenate(halves, axis=1)


class PouchBuilder:
    def build(self, ctx: BuildContext) -> BuildResult:
        spec = ctx.spec
        W, H = spec.dimensions.diameter, spec.dimensions.height
        depth = spec.dimensions.depth or DEFAULT_DEPTH_RATIO * W
        lying = spec.orientation == "lying"
        tex_dir = ctx.out_dir / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        ctx.debug_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []
        if not spec.dimensions.depth:
            warnings.append(f"厚さが不明なため幅の {DEFAULT_DEPTH_RATIO:.0%} と仮定しました")

        labels = container_labels(spec.container_material, "plastic")
        materials = {"BagMat": {"role": "label", "labels": labels, "color": spec.colors.label_base or "#CCCCCC"}}
        image_used = None
        tex_meta: dict = {}
        if ctx.images:
            faces = ctx.faces or {}
            i = faces.get("front", ctx.preferred_image if ctx.preferred_image is not None else 0)
            # 裏面は vision.json の faces に back があるときだけ使う。2 枚目以降の画像を勝手には使わない
            # （検索した画像は別商品・別アングルのことが多い）。なければ正面を流用する
            j = faces.get("back")
            if j is not None and not 0 <= j < len(ctx.images):
                warnings.append(f"裏面の画像番号 {j} がありません")
                j = None
            sides = []
            for k, label in ((i, "画像"), (j, "裏面の画像")):
                if k is None:
                    sides.append(None)
                    continue
                img = trim_background(np.asarray(Image.open(ctx.images[k]).convert("RGB")))
                if lying:
                    # 横長の画像（シールが左右）を、立てた袋と同じ縦長（シールが上下）に回す
                    img = np.ascontiguousarray(np.rot90(img, 1))
                aspect = img.shape[1] / img.shape[0]
                if abs(aspect / (W / H) - 1) > 0.1:
                    warnings.append(f"{label}の縦横比 {aspect:.3f} が袋の寸法 {W / H:.3f} と 10% 以上ずれています")
                sides.append(img)
            tex_path = tex_dir / "label.png"
            tex = make_texture(sides[0], sides[1], W, H)
            Image.fromarray(tex).save(tex_path)
            record(tex_meta, "label.png", tex.shape[1::-1], tex.shape[0], H)
            materials["BagMat"].update(texture=str(tex_path.resolve()), texture_rel="./textures/label.png")
            image_used = str(ctx.images[i]) if j is None else {"front": str(ctx.images[i]), "back": str(ctx.images[j])}
        else:
            warnings.append("画像がないため無地の袋にしました")
        mesh = pouch_mesh(W, H, depth, spec.dimensions.gusset, spec.dimensions.square)
        mesh = lay_flat(mesh) if lying else {**mesh, "com": (0.0, 0.0, mesh["com_z"])}
        objects = [{"name": "Body", "vertices": mesh["vertices"], "faces": mesh["faces"], "uvs": mesh["uvs"],
                    "material": "BagMat"}]
        com, expected, colliders = mesh["com"], mesh["size"], ["Body"]
        if spec.parts:
            from .assembly import attach_parts  # assembly が pouch を import するので循環を避ける

            v = np.asarray(mesh["vertices"])
            att = attach_parts(ctx, v.min(0), v.max(0), {"Body"}, warnings, tex_dir)
            objects[0]["vertices"] = (v + att["shift"]).tolist()
            objects += att["objects"]
            materials.update(att["materials"])
            com = tuple(float(c) for c in np.asarray(com) + att["shift"])
            expected, colliders = att["size"], colliders + att["colliders"]
            if att["textures"]:
                tex_meta.setdefault("textures", {}).update(att["textures"])
            if att["images"]:
                image_used = {"body": image_used, **att["images"]}
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
            meta={"image": image_used, "warnings": warnings, **tex_meta,
                  "profile": {"flat_size": [W, H], "depth": depth, "orientation": spec.orientation,
                              **({"gusset": spec.dimensions.gusset} if spec.dimensions.gusset else {}),
                              **({"square": spec.dimensions.square} if spec.dimensions.square else {}),
                              "inflated_size": mesh["size"], "expected_size": expected,
                              **({"parts": [o["name"] for o in objects[1:]]} if spec.parts else {})},
                  "colors": {"label_base": spec.colors.label_base}},
        )
