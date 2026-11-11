"""把持の線（SimReady の FET_005。GSP.001）。

ロボットのハンドが物体をつかむ向きを、物体を横切る線（BasisCurves。名前は grasp_identifier_NN）で示す。
線の 2 点はハンドの指が当たる所で、線の向きに指を閉じる。高さの中ほどの断面で幅の狭いほうの向きに引くので、
円柱（ボトル・缶・カップ）は直径、箱・袋は短い辺（厚み）を横切る。描画しない（purpose = guide）。
什器（床に固定する static）には付けない。
"""

from __future__ import annotations

import numpy as np
from pxr import Gf, Usd, UsdGeom, Vt

PREFIX = "grasp_identifier"
WIDTH = 0.002  # 表示用の線の太さ [m]
COLOR = Gf.Vec3f(0.0, 0.8, 0.2)


def _render_edges(root: Usd.Prim) -> np.ndarray:
    """描画するメッシュの辺（ルートの座標系）。形は (辺の数, 2, 3)。"""
    cache = UsdGeom.XformCache()
    inv = cache.GetLocalToWorldTransform(root).GetInverse()
    edges: list[np.ndarray] = []
    for prim in Usd.PrimRange(root):
        mesh = UsdGeom.Mesh(prim)
        if not mesh or UsdGeom.Imageable(prim).ComputePurpose() not in (UsdGeom.Tokens.default_,
                                                                         UsdGeom.Tokens.render):
            continue
        p, counts, idx = (a.Get() for a in (mesh.GetPointsAttr(), mesh.GetFaceVertexCountsAttr(),
                                            mesh.GetFaceVertexIndicesAttr()))
        if not p or not counts or not idx:
            continue
        m = cache.GetLocalToWorldTransform(prim) * inv
        pts = np.asarray(p, float) @ np.asarray(m.ExtractRotationMatrix(), float) + np.asarray(
            m.ExtractTranslation(), float)
        idx, counts = np.asarray(idx), np.asarray(counts)
        ends = np.cumsum(counts)
        nxt = np.arange(1, len(idx) + 1)
        nxt[ends - 1] = ends - counts  # 面の最後の頂点は最初の頂点へ戻る
        edges.append(pts[np.stack([idx, idx[nxt]], 1)])
    return np.concatenate(edges) if edges else np.zeros((0, 2, 3))


def cross_section(edges: np.ndarray, z: float) -> np.ndarray:
    """高さ z の水平面と辺の交点。"""
    z0, z1 = edges[:, 0, 2], edges[:, 1, 2]
    hit = (np.minimum(z0, z1) <= z) & (np.maximum(z0, z1) >= z) & (z0 != z1)
    e = edges[hit]
    t = (z - e[:, 0, 2]) / (e[:, 1, 2] - e[:, 0, 2])
    return e[:, 0] + t[:, None] * (e[:, 1] - e[:, 0])


def grasp_line(edges: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """高さの中ほどの断面で、幅の狭いほうの向き（x か y）に物体を横切る線の 2 点。メッシュがなければ None。

    断面は辺と水平面の交点から求めるので、頂点の少ないメッシュ（箱・かごの枠）でも外形をとれる。
    """
    if len(edges) == 0:
        return None
    z = edges[:, :, 2]
    zc = (z.min() + z.max()) / 2
    sl = cross_section(edges, zc)
    if len(sl) == 0:  # 中ほどに面がない（宙に浮いた部品だけなど）。全体の外形で決める
        sl = edges.reshape(-1, 3)
    lo, hi = sl[:, :2].min(0), sl[:, :2].max(0)
    axis = int(np.argmin(hi - lo))
    other = 1 - axis
    mid = (lo[other] + hi[other]) / 2
    a, b = np.zeros(3), np.zeros(3)
    a[axis], b[axis] = lo[axis], hi[axis]
    a[other] = b[other] = mid
    a[2] = b[2] = zc
    return a, b


def write_grasp_lines(stage: Usd.Stage, root: Usd.Prim) -> list[dict]:
    """把持の線を書き、[{name, points, width}] を返す（width は指の開き [m]）。"""
    line = grasp_line(_render_edges(root))
    if line is None:
        return []
    a, b = line
    name = f"{PREFIX}_01"
    curve = UsdGeom.BasisCurves.Define(stage, root.GetPath().AppendChild(name))
    curve.CreateTypeAttr(UsdGeom.Tokens.linear)
    curve.CreateCurveVertexCountsAttr(Vt.IntArray([2]))
    curve.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*a), Gf.Vec3f(*b)]))
    curve.CreateWidthsAttr(Vt.FloatArray([WIDTH]))
    curve.SetWidthsInterpolation(UsdGeom.Tokens.constant)
    curve.CreatePurposeAttr(UsdGeom.Tokens.guide)
    curve.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant).Set(Vt.Vec3fArray([COLOR]))
    # 自分で計算すると float の丸めで USD の計算とずれ、SimReady の VG.002（extent が違う）になる
    curve.CreateExtentAttr(UsdGeom.BasisCurves.ComputeExtent(curve.GetPointsAttr().Get(), curve.GetWidthsAttr().Get()))
    return [{"name": name, "points": [[round(float(v), 4) for v in p] for p in (a, b)],
             "width": round(float(np.linalg.norm(b - a)), 4)}]
