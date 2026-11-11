"""部品の組み合わせ（セルフレジ・サイネージ・棚などの什器）の生成。

spec.json の parts に並べた直方体（box）・円柱（cylinder）・山形（dome / pointed_dome / bun / bread）・ドーナツ形（torus）・回転体（revolve）・
角の丸い柱（prism。三角柱など）を、それぞれ別のメッシュとして置く。
box 部品は faces に画像番号を書けば、その面に画像を貼る（画面・パネル・ロゴなど）。
全体は XY の中心が原点、底面が z=0 になるよう平行移動する。
"""

from __future__ import annotations

import json
from dataclasses import asdict
import logging
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image

from ..blender_runner import run_script
from ..semantics import part_labels
from ..spec import FINISHES, PART_SHAPES, PROFILE_SHAPES, TRANSLUCENCY, Joint, Part
from ..texres import record
from .box import (FACES, PART_BEVEL, bevel_width, box_mesh, border_color, cell_size, cell_uv, face_layout, hex_to_rgb,
                  make_texture)
from .pouch import trim_background
from .revolve import BuildContext, BuildResult

log = logging.getLogger(__name__)

CYLINDER_SEGMENTS = 48
DEFAULT_COLOR = "#BBBBBB"
FINISH_PARAMS = {  # 表面 → (粗さ, 金属度)
    "matte": (0.8, 0.0),
    "plastic": (0.45, 0.0),
    "metal": (0.3, 1.0),
    "glossy": (0.08, 0.0),
    "screen": (0.25, 0.0),  # 液晶の表面は少し艶消し（映り込みがぼやけて、画面の内容が読める）
    "light": (0.4, 0.0),  # 照明の乳白のカバー・LED の帯
    "glass": (0.02, 0.0),  # 透明（color はガラスの色味。ほぼ無色なら #F2F6F8 など明るい色）
    **{k: (rough, 0.0) for k, (_, rough) in TRANSLUCENCY.items()},  # 半透明（color は素材の色）
}
GLASS_IOR = 1.5
# つやのある硬い面（成形品・カード・液晶）。凹凸の法線があると、映り込みが歪んでシワに見える
SMOOTH_FINISHES = ("glossy", "screen", "light")


def rotation_matrix(deg: list[float]) -> np.ndarray:
    """X → Y → Z の順に回すオイラー角 [度] の回転行列。"""
    rx, ry, rz = (math.radians(a) for a in deg)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Z @ Y @ X


def cylinder_mesh(dx: float, dy: float, h: float, n: int = CYLINDER_SEGMENTS, atlas: bool = False,
                  cell: int | None = None) -> dict:
    """底面の中心が原点、軸が Z の（楕）円柱。UV は側面を横に一周、上下面は円形に割り当てる。

    atlas=True なら上下面を箱と同じテクスチャの top / bottom のセルに、側面を front のセル（塗りつぶし）に割り当てる。
    上面の画像は正面（-Y）側が画像の下、底面は正面側が画像の上（箱と同じ向き）。
    """
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.stack([dx / 2 * np.cos(a), dy / 2 * np.sin(a)], 1)
    verts = [[x, y, 0.0] for x, y in ring] + [[x, y, h] for x, y in ring]
    faces, uvs = [], []
    if atlas:
        cell_args = () if cell is None else (cell,)
        fu0, fv0, fu1, fv1 = cell_uv(FACES.index("front"), *cell_args)  # 画像のないセル（部品の色で塗る）
        cu = [(fu0 + fu1) / 2, (fv0 + fv1) / 2]

        def disk_uv(index: int, flip: bool) -> list[list[float]]:
            u0, v0, u1, v1 = cell_uv(index, *cell_args)
            return [[u0 + (u1 - u0) * (0.5 + 0.5 * math.cos(t)),
                     v0 + (v1 - v0) * (0.5 - 0.5 * math.sin(t) if flip else 0.5 + 0.5 * math.sin(t))] for t in a]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
        uvs.append([cu] * 4 if atlas else [[i / n, 0], [(i + 1) / n, 0], [(i + 1) / n, 1], [i / n, 1]])
    cap_uv = [[0.5 + 0.5 * math.cos(t), 0.5 + 0.5 * math.sin(t)] for t in a]
    faces.append(list(range(n))[::-1])
    uvs.append((disk_uv(FACES.index("bottom"), True) if atlas else cap_uv)[::-1])
    faces.append(list(range(n, 2 * n)))
    uvs.append(disk_uv(FACES.index("top"), False) if atlas else cap_uv)
    return {"vertices": verts, "faces": faces, "uvs": uvs}


DOME_POWER = {"dome": 2.0, "pointed_dome": 1.3, "bun": 2.6, "bread": 2.2}  # 断面 (r/R)^p + (z/h)^p = 1。p が小さいほどとがり、大きいほど肩が張る
ARC_UV = ("bread",)  # 画像を頂点からの道のりで貼る山（側面にも同じ密度で貼られ、縁が縦に伸びない）
DOME_RINGS = 24


def dome_mesh(dx: float, dy: float, h: float, p: float, n: int = CYLINDER_SEGMENTS, rings: int = DOME_RINGS,
              atlas: bool = False, cell: int | None = None, arc: bool = False) -> dict:
    """底面の中心が原点、底が平らで頂点がとがらず閉じる山。UV は側面を横に一周、底面は円形。

    atlas=True なら山の面に箱と同じテクスチャの top のセルを真上から投影する（正面 -Y 側が画像の下）。
    盛ったそば・ごはん・からあげなどの写真を、立体の山の形のまま貼れる。底面は front のセル（塗りつぶし）。
    arc=True なら真上からではなく、頂点からの道のりの割合を画像の中心からの距離にする（底の縁が画像に内接する楕円）。
    急な側面にも画像が同じ密度で貼られる（パンの焼き色の裾など）。
    """
    mesh = _dome_mesh(dx, dy, h, p, n, rings)
    if not atlas:
        return mesh
    cell_args = () if cell is None else (cell,)
    u0, v0, u1, v1 = cell_uv(FACES.index("top"), *cell_args)
    fu0, fv0, fu1, fv1 = cell_uv(FACES.index("front"), *cell_args)
    vs = mesh["vertices"]
    if arc:
        top_uv = [[u0 + (u1 - u0) * (0.5 + 0.5 * f * c), v0 + (v1 - v0) * (0.5 + 0.5 * f * s)]
                  for f, c, s in _arc_coords(dx, dy, h, p, n, rings)]
    else:
        top_uv = [[u0 + (u1 - u0) * (x / dx + 0.5), v0 + (v1 - v0) * (y / dy + 0.5)] for x, y, _ in vs]
    fill = [(fu0 + fu1) / 2, (fv0 + fv1) / 2]
    mesh["uvs"] = [[top_uv[i] for i in f] for f in mesh["faces"][:-1]] + [[fill] * len(mesh["faces"][-1])]
    return mesh


def _arc_coords(dx: float, dy: float, h: float, p: float, n: int, rings: int) -> list[tuple[float, float, float]]:
    """_dome_mesh の頂点ごとの (頂点からの道のりの割合, cos, sin)。道のりは平均の半径の断面で測る。"""
    th = np.linspace(0, np.pi / 2, rings + 1)[:-1]
    zs = h * np.sin(th) ** (2 / p)
    rs = (dx + dy) / 4 * np.cos(th) ** (2 / p)
    pr = np.concatenate([np.stack([rs, zs], 1), [[0.0, h]]])  # 底の輪 → 頂点
    seg = np.hypot(*np.diff(pr, axis=0).T)
    left = np.concatenate([np.cumsum(seg[::-1])[::-1], [0.0]]) / max(seg.sum(), 1e-12)  # 頂点までの残りの道のり
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    out = [(float(f), math.cos(t), math.sin(t)) for f in left[:-1] for t in a]
    return out + [(0.0, 1.0, 0.0)]


def _dome_mesh(dx: float, dy: float, h: float, p: float, n: int, rings: int) -> dict:
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    th = np.linspace(0, np.pi / 2, rings + 1)[:-1]  # 角度で刻むと頂上付近の輪が細かくなる
    zs = h * np.sin(th) ** (2 / p)
    rs = np.cos(th) ** (2 / p)
    verts, faces, uvs = [], [], []
    for z, s in zip(zs, rs):
        verts += [[dx / 2 * s * math.cos(t), dy / 2 * s * math.sin(t), float(z)] for t in a]
    top = len(verts)
    verts.append([0.0, 0.0, h])
    for k in range(rings):
        v0, v1 = k / rings, (k + 1) / rings
        for i in range(n):
            j = (i + 1) % n
            if k < rings - 1:
                faces.append([k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i])
                uvs.append([[i / n, v0], [(i + 1) / n, v0], [(i + 1) / n, v1], [i / n, v1]])
            else:
                faces.append([k * n + i, k * n + j, top])
                uvs.append([[i / n, v0], [(i + 1) / n, v0], [(i + 0.5) / n, 1.0]])
    faces.append(list(range(n))[::-1])
    uvs.append([[0.5 + 0.5 * math.cos(t), 0.5 + 0.5 * math.sin(t)] for t in a][::-1])
    return {"vertices": verts, "faces": faces, "uvs": uvs}


def torus_mesh(dx: float, dy: float, t: float, n: int = CYLINDER_SEGMENTS, m: int = 16) -> dict:
    """XY 面に寝かせたドーナツ形。外径 dx × dy、管の太さ t、底が z=0。UV は大きな輪を横、管の周りを縦に一周。"""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    b = np.linspace(0, 2 * np.pi, m, endpoint=False)
    rx, ry, r = (dx - t) / 2, (dy - t) / 2, t / 2
    verts = [[(rx + r * math.cos(v)) * math.cos(u), (ry + r * math.cos(v)) * math.sin(u), r + r * math.sin(v)]
             for u in a for v in b]
    faces, uvs = [], []
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            faces.append([i * m + j, i2 * m + j, i2 * m + j2, i * m + j2])
            uvs.append([[i / n, j / m], [(i + 1) / n, j / m], [(i + 1) / n, (j + 1) / m], [i / n, (j + 1) / m]])
    return {"vertices": verts, "faces": faces, "uvs": uvs}


def revolve_mesh(dx: float, dy: float, h: float, profile: list[list[float]], n: int = CYLINDER_SEGMENTS) -> dict:
    """断面 profile（[半径の割合, 高さの割合] を下から上へ）を Z 軸まわりに回した形。半径 0 の端は 1 点に閉じ、
    0 でない端は平らな面でふさぐ。UV は側面を横に一周（縦は断面に沿った長さの割合）、ふたは円形。"""
    prof = np.asarray(profile, float)
    if prof.ndim != 2 or prof.shape[1] != 2 or len(prof) < 2:
        raise ValueError("revolve の profile は [[半径, 高さ], ...] の 2 点以上です")
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    seg = np.hypot(np.diff(prof[:, 0]) * (dx + dy) / 4, np.diff(prof[:, 1]) * h)
    vs = np.concatenate([[0], np.cumsum(seg)]) / max(seg.sum(), 1e-9)
    verts, faces, uvs, rows = [], [], [], []
    for (s, z) in prof:  # 半径 0 の点は 1 頂点、それ以外は n 頂点の輪
        rows.append(len(verts))
        if s <= 1e-9:
            verts.append([0.0, 0.0, float(z * h)])
        else:
            verts += [[dx / 2 * s * math.cos(t), dy / 2 * s * math.sin(t), float(z * h)] for t in a]
    pole = [s <= 1e-9 for s in prof[:, 0]]
    for k in range(len(prof) - 1):
        r0, r1, v0, v1 = rows[k], rows[k + 1], vs[k], vs[k + 1]
        for i in range(n):
            j = (i + 1) % n
            if pole[k] and pole[k + 1]:
                continue
            if pole[k]:
                faces.append([r0, r1 + j, r1 + i][::-1])
                uvs.append([[(i + 0.5) / n, v0], [(i + 1) / n, v1], [i / n, v1]][::-1])
            elif pole[k + 1]:
                faces.append([r0 + i, r0 + j, r1])
                uvs.append([[i / n, v0], [(i + 1) / n, v0], [(i + 0.5) / n, v1]])
            else:
                faces.append([r0 + i, r0 + j, r1 + j, r1 + i])
                uvs.append([[i / n, v0], [(i + 1) / n, v0], [(i + 1) / n, v1], [i / n, v1]])
    cap_uv = [[0.5 + 0.5 * math.cos(t), 0.5 + 0.5 * math.sin(t)] for t in a]
    if not pole[0]:
        faces.append(list(range(rows[0], rows[0] + n))[::-1])
        uvs.append(cap_uv[::-1])
    if not pole[-1]:
        faces.append(list(range(rows[-1], rows[-1] + n)))
        uvs.append(cap_uv)
    return {"vertices": verts, "faces": faces, "uvs": uvs}


PRISM_PROFILE = [[-0.5, 0.0], [0.5, 0.0], [0.0, 1.0]]  # prism の断面の既定（底辺が下の二等辺三角形）
PRISM_ROUND = 0.12  # prism の角を丸める半径の既定（幅と高さの短いほうに対する割合）
PRISM_ARC = 10  # 角の丸みの分割数（1 区間 12° 前後。面取りの角度の閾値 30° より小さく、側面がなめらかに見える）


def prism_outline(w: float, h: float, profile: list[list[float]] | None = None) -> np.ndarray:
    """prism の断面（XZ 面）の外形 [[x, z], ...]（反時計回り、正面 -Y から見て）。

    profile は凸多角形の頂点 [x, z] か [x, z, 丸みの半径]（x は幅を 1 とした -0.5〜0.5、z は高さの割合 0〜1、
    半径は幅と高さの短いほうに対する割合。省略時は PRISM_ROUND）。角を円弧で丸めたあと、外形が幅 w × 高さ h に
    ちょうど収まるよう拡大する。
    """
    prof = profile or PRISM_PROFILE
    if len(prof) < 3 or any(len(q) not in (2, 3) for q in prof):
        raise ValueError("prism の profile は [[x, z], ...] か [[x, z, 半径], ...] の 3 点以上です")
    P = np.array([[q[0] * w, q[1] * h] for q in prof], float)
    radii = np.array([q[2] if len(q) == 3 else PRISM_ROUND for q in prof], float) * min(w, h)
    area2 = np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area2 < 0:
        P, radii = P[::-1], radii[::-1]
    n = len(P)
    out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        u, v = (a - b), (c - b)
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        half = math.acos(float(np.clip(u @ v, -1, 1))) / 2  # 内角の半分
        if radii[i] <= 0 or half <= 1e-6 or half >= math.pi / 2 - 1e-6:
            out.append(b)
            continue
        t = min(radii[i] / math.tan(half), 0.5 * lu, 0.5 * lv)  # 接点までの距離（辺の半分まで）
        r = t * math.tan(half)
        bis = (u + v) / np.linalg.norm(u + v)
        center = b + bis * r / math.sin(half)
        p0, p1 = b + u * t, b + v * t
        a0 = math.atan2(*(p0 - center)[::-1])
        a1 = math.atan2(*(p1 - center)[::-1])
        if a1 < a0:  # 反時計回りに回る
            a1 += 2 * math.pi
        for k in range(PRISM_ARC + 1):
            th = a0 + (a1 - a0) * k / PRISM_ARC
            out.append(center + r * np.array([math.cos(th), math.sin(th)]))
    out = np.array(out)
    lo, hi = out.min(0), out.max(0)
    return (out - lo) / (hi - lo) * [w, h] - [w / 2, 0]


def prism_mesh(w: float, d: float, h: float, profile: list[list[float]] | None = None, atlas: bool = False,
               cell: int | None = None) -> dict:
    """断面（XZ 面、prism_outline）を奥行き Y 方向に押し出した柱。底は z=0、奥行きは -d/2〜d/2。

    UV は正面（-Y）と背面（+Y）を断面の外接長方形に合わせて平行に投影し（背面は後ろから見た向き）、側面は外形に沿って横に一周。
    atlas=True なら正面・背面を箱と同じテクスチャの front / back のセルに、側面を top のセル（塗りつぶし）に割り当てる。
    """
    ol = prism_outline(w, h, profile)
    n = len(ol)
    verts = [[x, -d / 2, z] for x, z in ol] + [[x, d / 2, z] for x, z in ol]
    faces, uvs = [], []
    seg = np.hypot(*np.diff(np.vstack([ol, ol[:1]]), axis=0).T)
    us = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    cell_args = () if cell is None else (cell,)

    def planar(index: int | None, mirror: bool) -> list[list[float]]:
        u0, v0, u1, v1 = cell_uv(index, *cell_args) if index is not None else (0, 0, 1, 1)
        return [[u0 + (u1 - u0) * ((w / 2 - x) / w if mirror else (x + w / 2) / w), v0 + (v1 - v0) * z / h]
                for x, z in ol]
    if atlas:
        tu0, tv0, tu1, tv1 = cell_uv(FACES.index("top"), *cell_args)
        fill = [(tu0 + tu1) / 2, (tv0 + tv1) / 2]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, n + i, n + j, j])
        uvs.append([fill] * 4 if atlas else [[us[i], 0], [us[i], 1], [us[i + 1], 1], [us[i + 1], 0]])
    faces.append(list(range(n)))
    uvs.append(planar(FACES.index("front") if atlas else None, False))
    faces.append(list(range(2 * n - 1, n - 1, -1)))
    uvs.append(planar(FACES.index("back") if atlas else None, True)[::-1])
    return {"vertices": verts, "faces": faces, "uvs": uvs}


SHEET_SHAPES = ("leaf", "star")  # 厚みのない面（両面を描く）
TOP_SHAPES = (*DOME_POWER, *SHEET_SHAPES, "fruit")  # top の画像を山・面に投影する部品


def _top_uv(x: float, y: float, dx: float, dy: float, cell: int | None) -> list[float]:
    """真上から top のセルに投影した UV（正面 -Y 側が画像の下）。"""
    u0, v0, u1, v1 = cell_uv(FACES.index("top"), *(() if cell is None else (cell,)))
    return [u0 + (u1 - u0) * (x / dx + 0.5), v0 + (v1 - v0) * (y / dy + 0.5)]


def leaf_width(t: float) -> float:
    """葉の付け根（t=0）から先（t=1）までの幅の割合（最大 1）。くさび形の付け根、先の丸い倒卵形。"""
    return min(1.0, (t ** 0.75 * (1 - t) ** 0.35) / 0.4956)


def leaf_mesh(length: float, width: float, h: float, teeth: int = 0, columns: int = 1, atlas: bool = False,
              cell: int | None = None) -> dict:
    """付け根が (-length/2, 0, h/2)、先が +X の 1 枚の葉（厚みなし）。

    縁は先へ向いた鋸歯（片側 teeth 個、葉の 3 割より先）。主脈で V 字に少し折れ（縁が上）、長さ方向に h だけ反る
    （中ほどが上がり、先は付け根の高さまで垂れる）。columns は主脈から縁までの列の数。UV は真上から top のセル。
    """
    ts = [0.0, 0.06, 0.15, 0.3] if teeth else list(np.linspace(0, 1, 9)[:-1])
    if teeth:
        k = np.linspace(0.3, 0.97, 2 * teeth + 1)[1:]
        ts += [float(t) for t in k]
    ts.append(1.0)
    notch = {i for i in range(5, len(ts) - 1, 2)} if teeth else set()  # 歯と歯の間（内側へ切れ込む）
    fold = 0.22 * width / 2  # 縁の上がり
    verts, faces, uvs = [], [], []
    rows = []
    for i, t in enumerate(ts):
        x = -length / 2 + length * t
        hw = width / 2 * leaf_width(t) * (0.86 if i in notch else 1.0)
        zc = h / 2 + h * 4 * t * (1 - t) - h * 0.5 * t ** 3  # 中ほどが上がり、先が垂れる
        if hw <= 1e-9:
            rows.append([len(verts)])
            verts.append([x, 0.0, zc])
            continue
        row = []
        for c in range(-columns, columns + 1):
            f = c / columns
            row.append(len(verts))
            verts.append([x + (0.02 * length * abs(f) if teeth and i not in notch else 0.0), hw * f,
                          zc + fold * abs(f) ** 1.5])
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        if len(a) == 1:
            faces += [[a[0], b[j], b[j + 1]] for j in range(len(b) - 1)]
        elif len(b) == 1:
            faces += [[a[j], b[0], a[j + 1]] for j in range(len(a) - 1)]
        else:
            faces += [[a[j], b[j], b[j + 1], a[j + 1]] for j in range(len(a) - 1)]
    mesh = {"vertices": verts, "faces": faces}
    if atlas:
        mesh["uvs"] = [[_top_uv(verts[i][0], verts[i][1], length, width, cell) for i in f] for f in faces]
    else:
        mesh["uvs"] = [[[verts[i][0] / length + 0.5, verts[i][1] / width + 0.5] for i in f] for f in faces]
    return mesh


def star_outline(theta: np.ndarray, lobes: int, inner: float, power: float) -> np.ndarray:
    """放射状に裂けた形の半径の割合（theta=0 が裂片の先）。"""
    return inner + (1 - inner) * np.abs(np.cos(lobes * theta / 2)) ** power


def star_mesh(dx: float, dy: float, h: float, profile: list[list[float]] | None = None, samples: int = 2,
              rings: int = 1, atlas: bool = False, cell: int | None = None) -> dict:
    """中心が原点の放射状に裂けた面（萼片・花びら。厚みなし）。先ほど z が上がり、外周で h。

    samples は裂片 1 枚あたりの外周の点の数（2 なら先と切れ込みだけの星形）、rings は中心から外周までの輪の数。
    """
    lobes, inner, power = (list(profile[0]) + [5, 0.4, 1.0][len(profile[0]):]) if profile else (5, 0.4, 1.0)
    lobes = int(lobes)
    n = lobes * samples
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = star_outline(a, lobes, inner, power)
    verts = [[0.0, 0.0, 0.0]]
    for k in range(1, rings + 1):
        s = k / rings
        verts += [[dx / 2 * s * float(ri) * math.cos(t), dy / 2 * s * float(ri) * math.sin(t), h * (s * float(ri)) ** 2]
                  for ri, t in zip(r, a)]
    faces = [[0, 1 + i, 1 + (i + 1) % n] for i in range(n)]
    for k in range(rings - 1):
        o0, o1 = 1 + k * n, 1 + (k + 1) * n
        faces += [[o0 + i, o1 + i, o1 + (i + 1) % n, o0 + (i + 1) % n] for i in range(n)]
    mesh = {"vertices": verts, "faces": faces}
    if atlas:
        mesh["uvs"] = [[_top_uv(verts[i][0], verts[i][1], dx, dy, cell) for i in f] for f in faces]
    else:
        mesh["uvs"] = [[[verts[i][0] / dx + 0.5, verts[i][1] / dy + 0.5] for i in f] for f in faces]
    return mesh


# いちご形の断面 [半径の割合, 高さの割合]：とがった先 → いちばん太い肩 → へたの付く上の中心（少しくぼむ）
FRUIT_PROFILE = [[0, 0], [0.22, 0.06], [0.45, 0.2], [0.66, 0.38], [0.84, 0.57], [0.96, 0.74], [1.0, 0.84],
                 [0.94, 0.93], [0.72, 0.99], [0.4, 1.0], [0, 0.97]]


def fruit_mesh(dx: float, dy: float, h: float, profile: list[list[float]] | None = None, n: int = CYLINDER_SEGMENTS,
               atlas: bool = False, cell: int | None = None) -> dict:
    """先が原点（下）の閉じた回転体。atlas=True なら top のセルを先からの道のりで貼る（画像の中心が先、縁が上の中心）。"""
    prof = np.asarray(profile or FRUIT_PROFILE, float)
    xy = np.stack([prof[:, 0] * (dx + dy) / 4, prof[:, 1] * h], 1)
    seg = np.hypot(*np.diff(xy, axis=0).T)
    f = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-12)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    verts, ids, fs = [], [], []
    for (r, z), fi in zip(prof, f):
        if r <= 1e-9:
            ids.append([len(verts)])
            verts.append([0.0, 0.0, float(z * h)])
        else:
            ids.append(list(range(len(verts), len(verts) + n)))
            verts += [[dx / 2 * r * math.cos(t), dy / 2 * r * math.sin(t), float(z * h)] for t in a]
        fs.append(float(fi))
    faces, corners = [], []  # corners: 面の各頂点の (道のりの割合, 角度)
    for k in range(len(ids) - 1):
        lo, hi = ids[k], ids[k + 1]
        for i in range(n):
            j = (i + 1) % n
            ti, tj, tm = a[i], a[i] + 2 * np.pi / n, a[i] + np.pi / n
            if len(lo) == 1:
                faces.append([lo[0], hi[j], hi[i]])
                corners.append([(fs[k], tm), (fs[k + 1], tj), (fs[k + 1], ti)])
            elif len(hi) == 1:
                faces.append([lo[i], lo[j], hi[0]])
                corners.append([(fs[k], ti), (fs[k], tj), (fs[k + 1], tm)])
            else:
                faces.append([lo[i], lo[j], hi[j], hi[i]])
                corners.append([(fs[k], ti), (fs[k], tj), (fs[k + 1], tj), (fs[k + 1], ti)])
    if atlas:
        u0, v0, u1, v1 = cell_uv(FACES.index("top"), *(() if cell is None else (cell,)))
        uvs = [[[u0 + (u1 - u0) * (0.5 + 0.5 * fr * math.cos(t)), v0 + (v1 - v0) * (0.5 + 0.5 * fr * math.sin(t))]
                for fr, t in c] for c in corners]
    else:
        uvs = [[[t / (2 * np.pi), fr] for fr, t in c] for c in corners]
    return {"vertices": verts, "faces": faces, "uvs": uvs}


def tube_mesh(path: list[list[float]], d0: float, d1: float, n: int = 6) -> dict:
    """path の点を通る管。太さは始点 d0 から終点 d1 まで道のりで変わる。両端は平らにふさぐ。"""
    pts = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-12)
    tang = np.gradient(pts, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-12)
    ref = np.array([0.0, 0.0, 1.0]) if abs(tang[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(tang[0], ref)
    u /= np.linalg.norm(u)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    verts, faces, uvs = [], [], []
    for i, (p, t) in enumerate(zip(pts, tang)):
        u = u - t * np.dot(u, t)  # 前の輪の向きを引き継ぐ（ねじれない）
        u /= max(np.linalg.norm(u), 1e-12)
        w = np.cross(t, u)
        r = (d0 + (d1 - d0) * s[i]) / 2
        verts += [(p + r * (math.cos(q) * u + math.sin(q) * w)).tolist() for q in a]
    m = len(pts)
    for i in range(m - 1):
        for j in range(n):
            k = (j + 1) % n
            faces.append([i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j])
            uvs.append([[j / n, s[i]], [(j + 1) / n, s[i]], [(j + 1) / n, s[i + 1]], [j / n, s[i + 1]]])
    cap = [[0.5 + 0.5 * math.cos(q), 0.5 + 0.5 * math.sin(q)] for q in a]
    faces.append(list(range(n))[::-1])
    uvs.append(cap[::-1])
    faces.append(list(range((m - 1) * n, m * n)))
    uvs.append(cap)
    return {"vertices": verts, "faces": faces, "uvs": uvs}


def part_volume(p: Part) -> float:
    w, d, h = p.size
    if p.shape == "tube":
        pts = np.asarray(p.profile, float)
        length = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
        return math.pi * ((w + d) / 4) ** 2 * length
    if p.shape == "fruit":
        prof = np.asarray(p.profile or FRUIT_PROFILE, float)
        return float(abs(math.pi * w * d / 4 * h * np.trapezoid(prof[:, 0] ** 2, prof[:, 1])))
    if p.shape == "leaf":
        return w * d * 0.6 * 0.001  # 厚さ 1 mm の板
    if p.shape == "star":
        return math.pi * w * d / 4 * 0.6 * 0.001
    if p.shape == "prism":
        ol = prism_outline(w, h, p.profile)
        return float(abs(np.sum(ol[:, 0] * np.roll(ol[:, 1], -1) - np.roll(ol[:, 0], -1) * ol[:, 1])) / 2 * d)
    if p.shape == "torus":
        return 2 * math.pi ** 2 * ((w + d) / 4 - h / 2) * (h / 2) ** 2
    if p.shape == "revolve":
        prof = np.asarray(p.profile, float)
        return float(math.pi * w * d / 4 * h * np.trapezoid(prof[:, 0] ** 2, prof[:, 1]))
    if p.shape in DOME_POWER:
        z = np.linspace(0, 1, 201)
        s = np.clip(1 - z ** DOME_POWER[p.shape], 0, 1) ** (1 / DOME_POWER[p.shape])
        return float(math.pi * w * d / 4 * h * np.trapezoid(s ** 2, z))
    return w * d * h if p.shape == "box" else math.pi * w * d / 4 * h


def object_name(name: str, used: set[str]) -> str:
    """USD の prim 名に使える名前（英数字とアンダースコア、先頭は英字）。"""
    base = re.sub(r"\W", "_", name, flags=re.ASCII).strip("_") or "Part"
    if not base[0].isalpha():
        base = "P_" + base
    out, k = base, 2
    while out in used:
        out, k = f"{base}_{k}", k + 1
    used.add(out)
    return out


def part_objects(ctx: BuildContext, parts: list[Part], used: set[str], warnings: list[str],
                 tex_dir, tex_meta: dict) -> tuple[list[dict], dict, dict, list[float], list[list[float]]]:
    """部品ごとのメッシュ（Blender に渡す objects）・マテリアル・使った画像・体積・中心。頂点は numpy 配列のまま返す。

    書き出したテクスチャの大きさと画素密度は tex_meta["textures"] に足す。
    """
    objects, materials, images_used = [], {}, {}
    volumes, centers = [], []
    for p in parts:
        if p.shape not in PART_SHAPES:
            raise ValueError(f"部品 '{p.name}' の shape '{p.shape}' は未対応です（{', '.join(PART_SHAPES)}）")
        if p.shape in PROFILE_SHAPES and not p.profile:
            raise ValueError(f"部品 '{p.name}' の shape '{p.shape}' には profile（断面の形）が必要です")
        if p.finish not in FINISHES:
            warnings.append(f"部品 '{p.name}' の finish '{p.finish}' は未知のため plastic にしました")
            p.finish = "plastic"
        name = object_name(p.name, used)
        w, d, h = p.size
        see_through = p.finish == "glass" or p.finish in TRANSLUCENCY
        textured = p.shape in ("box", "cylinder", "prism", *TOP_SHAPES) and not see_through
        face_images = _face_images(ctx, p, warnings) if textured else {}
        cell, cell_len = cell_size(face_layout(w, d, h), face_images)
        if p.shape in DOME_POWER:
            mesh = dome_mesh(w, d, h, DOME_POWER[p.shape], n=p.segments or CYLINDER_SEGMENTS,
                             rings=max(4, (p.segments or CYLINDER_SEGMENTS) // 2), atlas=bool(face_images), cell=cell,
                             arc=p.shape in ARC_UV)
        elif p.shape == "leaf":
            teeth = 7 if p.segments is None else p.segments
            mesh = leaf_mesh(w, d, h, teeth=teeth, columns=1 if teeth <= 5 else 2, atlas=bool(face_images), cell=cell)
        elif p.shape == "star":
            fine = (p.segments or CYLINDER_SEGMENTS) >= 24
            mesh = star_mesh(w, d, h, p.profile, samples=4 if fine else 2, rings=2 if fine else 1,
                             atlas=bool(face_images), cell=cell)
        elif p.shape == "fruit":
            mesh = fruit_mesh(w, d, h, p.profile, n=p.segments or CYLINDER_SEGMENTS, atlas=bool(face_images), cell=cell)
        elif p.shape == "tube":
            mesh = tube_mesh(p.profile, w, d, n=p.segments or 6)
        elif p.shape == "torus":
            mesh = torus_mesh(w, d, h)
        elif p.shape == "revolve":
            mesh = revolve_mesh(w, d, h, p.profile)
        elif p.shape == "box":
            mesh = box_mesh(w, d, h, cell)
        elif p.shape == "prism":
            mesh = prism_mesh(w, d, h, p.profile, atlas=bool(face_images), cell=cell)
        else:
            mesh = cylinder_mesh(w, d, h, n=p.segments or CYLINDER_SEGMENTS, atlas=bool(face_images), cell=cell)
        R = rotation_matrix(p.rotation)
        v = np.asarray(mesh["vertices"]) - [0, 0, h / 2]  # 部品の中心を原点にしてから回す
        mesh["vertices"] = v @ R.T + p.center

        rough, metal = FINISH_PARAMS[p.finish]
        color = p.color or DEFAULT_COLOR
        mat = {"role": "solid", "color": color, "roughness": rough, "metallic": metal,
               "labels": part_labels(p.material, p.finish)}
        if p.finish in SMOOTH_FINISHES:
            mat["smooth"] = True  # 平らで硬いつやの面。法線・粗さのむらのテクスチャを付けない（usd_post.py）
        if p.finish == "screen":
            mat["emissive"] = True  # 画像を発光させる（usd_post.py）
        if p.finish == "light":
            mat["light"] = True  # 照明の面。Lighting バリアントの On で color の色に光る（usd_post.py）
        if p.finish == "glass":
            mat.update(role="glass", transmission=1.0, ior=GLASS_IOR, thin_walled=p.thin_walled)
        elif p.finish in TRANSLUCENCY:
            mat.update(role="translucent", clarity=TRANSLUCENCY[p.finish][0], transmission=TRANSLUCENCY[p.finish][0])
        if see_through and p.faces:
            warnings.append(f"部品 '{p.name}' は透ける素材（{p.finish}）のため faces の画像を貼りません")
        if face_images:
            fill = hex_to_rgb(p.color) if p.color else border_color(next(iter(face_images.values())))
            tex_path = tex_dir / f"{name}.png"
            tex = make_texture(face_images, fill, cell)
            Image.fromarray(tex).save(tex_path)
            record(tex_meta, f"{name}.png", tex.shape[1::-1], cell, cell_len)
            mat.update(texture=str(tex_path.resolve()), texture_rel=f"./textures/{name}.png")
            if p.blank is not None:
                # Picture バリアントの Blank（絵柄を抜いた無地の面）。同じ並びのテクスチャを別に作る（usd_post.py）
                blank_path = tex_dir / f"{name}_Blank.png"
                Image.fromarray(make_texture(_blank_images(ctx, p, face_images), fill, cell)).save(blank_path)
                mat.update(blank_texture=str(blank_path.resolve()), blank_texture_rel=f"./textures/{name}_Blank.png")
                words = picture_words([ctx.images[i] for f, i in (p.faces or {}).items() if f in face_images])
                if words:
                    mat["picture_text"] = words  # 絵柄に書いた文字（asset.json の picture.materials[]）
            images_used[name] = {f: str(ctx.images[i]) for f, i in (p.faces or {}).items() if f in face_images}
        materials[f"{name}Mat"] = mat
        bevel = bevel_width(p.bevel, p.size, PART_BEVEL) if p.shape in ("box", "prism") else 0.0
        objects.append({"name": name, "material": f"{name}Mat", "collision": p.collision, "bevel": bevel, **mesh})
        if p.shape in SHEET_SHAPES:
            objects[-1]["sheet"] = True
        volumes.append(part_volume(p))
        centers.append(p.center)
    return objects, materials, images_used, volumes, centers


def picture_words(images) -> dict:
    """貼った画像の文字（画像の隣の NN.text.json、agentic-usd-gen-fictional が書く）をまとめた {text, lang, audience?}。"""
    text, langs, aud = [], [], []
    for img in images:
        side = Path(img).with_suffix(".text.json")
        if not side.is_file():
            continue
        d = json.loads(side.read_text(encoding="utf-8"))
        text += [x for x in d.get("text") or [] if x not in text]
        langs += [d["lang"]] if d.get("lang") else []
        aud += [x for x in d.get("audience") or [] if x not in aud]
    if not text:
        return {}
    return {"text": text, "lang": "ja" if "ja" in langs else langs[0] if langs else "ja", **({"audience": aud} if aud else {})}


def attach_parts(ctx: BuildContext, body_lo, body_hi, used: set[str], warnings: list[str], tex_dir) -> dict:
    """回転体・袋・箱の本体に spec.parts の部品を足す（ポンプの頭・フタ・刃など）。

    部品の座標は本体の原点（底面の中心）を基準に、仕上がりの向き（寝かせた袋なら寝かせた後）で書く。
    本体と部品を合わせた外形が XY 中心・底面 z=0 になるよう、ずらす量 shift を返す（部品の頂点はずらし済み）。
    呼び出し側は本体の頂点と重心を shift だけずらす。
    """
    tex_meta: dict = {}
    objects, materials, images_used, _, _ = part_objects(ctx, ctx.spec.parts, used, warnings, tex_dir, tex_meta)
    allv = np.vstack([np.asarray([body_lo, body_hi])] + [o["vertices"] for o in objects])
    lo, hi = allv.min(0), allv.max(0)
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    for o in objects:
        o["vertices"] = (o["vertices"] + shift).tolist()
    return {"objects": objects, "materials": materials, "images": images_used, "shift": shift,
            "textures": tex_meta.get("textures", {}),
            "size": tuple(float(x) for x in hi - lo), "colliders": [o["name"] for o in objects if o["collision"]]}


class AssemblyBuilder:
    def build(self, ctx: BuildContext) -> BuildResult:
        spec = ctx.spec
        if not spec.parts:
            raise ValueError("assembly には spec.json の parts（部品のリスト）が必要です")
        tex_dir = ctx.out_dir / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        ctx.debug_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []

        used: set[str] = set()
        tex_meta: dict = {}
        objects, materials, images_used, volumes, centers = part_objects(ctx, spec.parts, used, warnings, tex_dir, tex_meta)

        # 全体を XY 中心・底面 z=0 にそろえる
        allv = np.vstack([o["vertices"] for o in objects])
        lo, hi = allv.min(0), allv.max(0)
        shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
        if np.abs(shift).max() > 0.001:
            log.info("部品全体を (%.4f, %.4f, %.4f) m 平行移動しました", *shift)
        for o in objects:
            o["vertices"] = (o["vertices"] + shift).tolist()
        size = hi - lo

        dims = spec.dimensions
        expected = (dims.diameter, dims.depth or float(size[1]), dims.height)
        for label, got, want in zip(("幅", "奥行き", "高さ"), size, expected):
            if abs(got - want) > 0.05 * want:
                warnings.append(f"部品を組み合わせた{label} {got:.3f} m が寸法 {want:.3f} m と 5% 以上ずれています")

        # 質量は体積比で部品に配り、重心はその加重平均とする（中空の筐体でも中身が詰まった扱い）
        vol = np.array(volumes)
        com = (np.array(centers) + shift).T @ vol / vol.sum()
        mass = spec.total_mass_kg()
        if not mass:
            mass = float(vol.sum() * 300.0)
            warnings.append(f"質量が不明なため体積から {mass:.1f} kg と仮定しました")
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
            mass=mass,
            center_of_mass=tuple(float(c) for c in com),
            colliders=[o["name"] for o in objects if o["collision"]],
            materials=materials,
            double_sided=[o["name"] for o in objects if o.get("sheet")],
            static=spec.static,
            physics_labels=_main_labels(objects, materials, volumes),
            links=link_bodies(spec.parts, spec.joints, objects, volumes, centers, shift, mass),
            lights=[{**asdict(x), "center": [float(c) for c in np.asarray(x.center) + shift]} for x in spec.lights],
            meta={"image": images_used or None,
                  "warnings": warnings, **tex_meta,
                  "profile": {"parts": [o["name"] for o in objects], "expected_size": expected,
                              "static": spec.static},
                  "part_variants": _part_variants(spec, objects),
                  "colors": {n: m["color"] for n, m in materials.items()}},
        )


def _part_variants(spec, objects: list[dict]) -> dict | None:
    """部品の出し入れのバリアント（usd_post.write_part_variants）。セット → 値、メッシュ名 → {セット: 表示する値}。"""
    if not spec.variant_sets:
        return None
    shows = {o["name"]: p.show for p, o in zip(spec.parts, objects) if p.show}
    return {"sets": spec.variant_sets, "shows": shows}


def link_bodies(parts: list[Part], joints: list[Joint], objects: list[dict], volumes: list[float],
                centers: list[list[float]], shift: np.ndarray, mass: float) -> list[dict]:
    """可動部ごとの部品（メッシュ名）・質量（体積比で総質量から分ける）・重心・関節。座標は平行移動したあとのもの。"""
    total = sum(volumes)
    out = []
    for j in joints:
        idx = [i for i, p in enumerate(parts) if p.link == j.link]
        v = np.array([volumes[i] for i in idx])
        c = np.array([centers[i] for i in idx], float) + shift
        out.append({"name": j.link, "parts": [objects[i]["name"] for i in idx],
                    "mass": float(mass * v.sum() / total),
                    "center_of_mass": [float(x) for x in c.T @ v / v.sum()],
                    "joint": {"type": j.type, "axis": j.axis,
                              "anchor": [float(a) for a in np.asarray(j.anchor, float) + shift],
                              "limits": None if j.limits is None else [float(x) for x in j.limits]}})
    return out


def _main_labels(objects: list[dict], materials: dict, volumes: list[float]) -> list[str]:
    """物理マテリアルのラベル。コリジョンのある部品のうち体積が最大のものの素材にする。"""
    cands = [(v, o) for v, o in zip(volumes, objects) if o["collision"]] or list(zip(volumes, objects))
    return list(materials[max(cands, key=lambda c: c[0])[1]["material"]]["labels"])


def _blank_images(ctx: BuildContext, p: Part, face_images: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """blank の面の画像（faces の画像と同じ大きさ）。色ならその単色、番号ならその画像。"""
    if isinstance(p.blank, str):
        rgb = hex_to_rgb(p.blank)
        return {f: np.full_like(img, rgb) for f, img in face_images.items()}
    src = trim_background(np.asarray(Image.open(ctx.images[p.blank]).convert("RGB")))
    return {f: np.asarray(Image.fromarray(src).resize(img.shape[1::-1], Image.LANCZOS))
            for f, img in face_images.items()}


def _face_images(ctx: BuildContext, p: Part, warnings: list[str]) -> dict[str, np.ndarray]:
    layout = face_layout(*p.size)
    out = {}
    for face, i in (p.faces or {}).items():
        allowed = {"box": FACES, "prism": ("front", "back"), **{k: ("top",) for k in TOP_SHAPES}}.get(
            p.shape, ("top", "bottom"))
        if face not in allowed:
            warnings.append(f"部品 '{p.name}' の未知の面 '{face}' を無視しました")
            continue
        if i is None:
            continue
        if not 0 <= i < len(ctx.images):
            warnings.append(f"部品 '{p.name}' の {face} の画像番号 {i} がありません")
            continue
        img = trim_background(np.asarray(Image.open(ctx.images[i]).convert("RGB")))
        fw, fh = layout[face][1]
        aspect = img.shape[1] / img.shape[0]
        if abs(aspect / (fw / fh) - 1) > 0.1:
            warnings.append(f"部品 '{p.name}' の {face} の画像の縦横比 {aspect:.3f} が "
                            f"寸法 {fw / fh:.3f} と 10% 以上ずれています")
        out[face] = img
    return out
