"""把持の線（grasp.py。SimReady の FET_005・GSP.001）のテスト。合成したステージを使う。"""

import numpy as np
import pytest
from pxr import Gf, Usd, UsdGeom, Vt

from agentic_usd_gen.grasp import (
    PREFIX,
    _render_edges,
    cross_section,
    grasp_line,
    write_grasp_lines,
)


def _cylinder(r=0.03, h=0.2, n=32, rings=21):
    """側面だけの円柱（四角形の面）。"""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = [(r * np.cos(a), r * np.sin(a), z) for z in np.linspace(0, h, rings) for a in t]
    faces = [[i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k]
             for i in range(rings - 1) for k in range(n)]
    return pts, faces


def _box(sx, sy, sz):
    """頂点 8 つの箱。高さの中ほどに頂点がない。"""
    pts = [(x * sx / 2, y * sy / 2, z * sz) for z in (0, 1) for y in (-1, 1) for x in (-1, 1)]
    faces = [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]]
    return pts, faces


def _mesh(stage, path, shape, purpose=None, translate=None):
    pts, faces = shape
    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, p)) for p in pts]))
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([len(f) for f in faces]))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([i for f in faces for i in f]))
    if purpose:
        mesh.CreatePurposeAttr(purpose)
    if translate:
        mesh.AddTranslateOp().Set(Gf.Vec3d(*translate))
    return mesh


def _edges(*shapes):
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/a").GetPrim()
    for i, shape in enumerate(shapes):
        _mesh(stage, f"/a/M{i}", shape)
    return _render_edges(root)


def test_cylinder_diameter():
    """円柱は高さの中ほどで直径を横切る。"""
    a, b = grasp_line(_edges(_cylinder()))
    assert a[2] == pytest.approx(0.1) and b[2] == pytest.approx(0.1)
    assert np.linalg.norm(b - a) == pytest.approx(0.06, abs=1e-3)
    assert np.linalg.norm((a + b)[:2] / 2) < 1e-3  # 軸を通る


@pytest.mark.parametrize("size, axis", [((0.18, 0.05, 0.25), 1), ((0.03, 0.09, 0.16), 0)])
def test_box_short_side(size, axis):
    """箱は短い辺（厚み）を横切る。頂点が上下にしかなくても、辺との交点で断面をとる。"""
    edges = _edges(_box(*size))
    assert len(cross_section(edges, size[2] / 2)) > 0
    a, b = grasp_line(edges)
    d = b - a
    assert abs(d[axis]) == pytest.approx(size[axis]) and abs(d[1 - axis]) < 1e-9 and d[2] == 0
    assert a[2] == pytest.approx(size[2] / 2)
    assert grasp_line(np.zeros((0, 2, 3))) is None


def test_write_grasp_lines():
    """BasisCurves（linear・2 点・guide）を書く。guide のメッシュ（当たり判定の可視化）は数えず、移動は反映する。"""
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/a").GetPrim()
    _mesh(stage, "/a/Body", _cylinder(), translate=(0.5, 0, 0))
    _mesh(stage, "/a/Collider", _box(1, 1, 1), purpose=UsdGeom.Tokens.guide)
    out = write_grasp_lines(stage, root)
    assert [g["name"] for g in out] == [f"{PREFIX}_01"] and out[0]["width"] == pytest.approx(0.06, abs=1e-3)
    curve = UsdGeom.BasisCurves(stage.GetPrimAtPath(f"/a/{PREFIX}_01"))
    assert curve and curve.GetTypeAttr().Get() == "linear"
    assert list(curve.GetCurveVertexCountsAttr().Get()) == [2]
    assert curve.ComputePurpose() == UsdGeom.Tokens.guide
    pts = np.array(curve.GetPointsAttr().Get())
    assert pts.mean(0) == pytest.approx((0.5, 0, 0.1), abs=1e-3)
    assert curve.GetExtentAttr().Get() == UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())


def test_extent_matches_usd():
    """extent は USD の計算と一致する（SimReady の VG.002）。float の丸めでずれやすい半端な寸法で確かめる。"""
    for r in (0.0610334, 0.0620669, 0.0333, 0.07131):
        stage = Usd.Stage.CreateInMemory()
        root = UsdGeom.Xform.Define(stage, "/a").GetPrim()
        _mesh(stage, "/a/Body", _cylinder(r=r, h=0.075, n=97))
        write_grasp_lines(stage, root)
        curve = UsdGeom.BasisCurves(stage.GetPrimAtPath(f"/a/{PREFIX}_01"))
        assert curve.GetExtentAttr().Get() == UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())


def test_write_nothing_without_meshes():
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/a").GetPrim()
    assert write_grasp_lines(stage, root) == []
    assert not stage.GetPrimAtPath(f"/a/{PREFIX}_01")
