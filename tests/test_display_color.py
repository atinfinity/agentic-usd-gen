"""表示色（primvars:displayColor・displayOpacity。SimReady の DISP.001〜003）のテスト。合成したステージを使う。"""

import numpy as np
import pytest
from PIL import Image
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt

from agentic_usd_gen.usd_post import DISPLAY_GREY, display_color, srgb_to_linear, texture_mean, write_display_colors


def _material(stage, name, opacity=None):
    mat = UsdShade.Material.Define(stage, f"/a/_materials/{name}")
    sh = UsdShade.Shader.Define(stage, f"/a/_materials/{name}/Principled_BSDF")
    sh.CreateIdAttr("UsdPreviewSurface")
    if opacity is not None:
        sh.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    return mat


def _quad_strip(stage, path, faces):
    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * faces))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([0, 1, 2, 3] * faces))
    mesh.CreatePointsAttr(Vt.Vec3fArray([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]))
    return mesh


@pytest.fixture
def stage():
    st = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(st, "/a")
    return st


def _close(a, b, tol=1e-4):
    return all(abs(x - y) < tol for x, y in zip(a, b, strict=True))


def test_constant_and_opacity(stage):
    """1 つのマテリアルだけのメッシュは constant。透明なマテリアルなら displayOpacity も書く。"""
    pet = _material(stage, "PET", opacity=0.15)
    body = _quad_strip(stage, "/a/Body", 3)
    UsdShade.MaterialBindingAPI.Apply(body.GetPrim()).Bind(pet)
    assert write_display_colors(stage, stage.GetPrimAtPath("/a"), {"PET": {"color": "#FF8000"}}) == 1
    pv = UsdGeom.PrimvarsAPI(body).GetPrimvar("displayColor")
    assert pv.GetInterpolation() == "constant" and pv.GetTypeName() == "color3f[]"
    assert len(pv.Get()) == 1 and _close(pv.Get()[0], srgb_to_linear("#FF8000"))
    op = UsdGeom.PrimvarsAPI(body).GetPrimvar("displayOpacity")
    assert op.GetInterpolation() == "constant" and list(op.Get()) == [pytest.approx(0.15)]


def test_uniform_per_face(stage):
    """面ごとにマテリアルを分けたメッシュは、面の数だけの色（uniform）。不透明なら displayOpacity は書かない。"""
    _material(stage, "CapMat")
    top = _material(stage, "CapTopMat")
    cap = _quad_strip(stage, "/a/Cap", 4)
    UsdShade.MaterialBindingAPI.Apply(cap.GetPrim()).Bind(UsdShade.Material.Get(stage, "/a/_materials/CapMat"))
    sub = UsdGeom.Subset.CreateGeomSubset(cap, "top", UsdGeom.Tokens.face, Vt.IntArray([1, 3]),
                                          familyName="materialBind")
    UsdShade.MaterialBindingAPI.Apply(sub.GetPrim()).Bind(top)
    write_display_colors(stage, stage.GetPrimAtPath("/a"),
                         {"CapMat": {"color": "#FF0000"}, "CapTopMat": {"color": "#0000FF"}})
    pv = UsdGeom.PrimvarsAPI(cap).GetPrimvar("displayColor")
    red, blue = srgb_to_linear("#FF0000"), srgb_to_linear("#0000FF")
    assert pv.GetInterpolation() == "uniform" and len(pv.Get()) == 4
    assert [_close(c, blue) for c in pv.Get()] == [False, True, False, True]
    assert _close(pv.Get()[0], red)
    assert not UsdGeom.PrimvarsAPI(cap).GetPrimvar("displayOpacity").HasValue()


def test_skips_guide_and_grey_fallback(stage):
    """guide（当たり判定の可視化など）には書かない。マテリアルのないメッシュは 18% グレー。"""
    guide = _quad_strip(stage, "/a/Collider", 1)
    guide.CreatePurposeAttr(UsdGeom.Tokens.guide)
    bare = _quad_strip(stage, "/a/Bare", 1)
    assert write_display_colors(stage, stage.GetPrimAtPath("/a"), {}) == 1
    assert not UsdGeom.PrimvarsAPI(guide).GetPrimvar("displayColor").HasValue()
    assert _close(UsdGeom.PrimvarsAPI(bare).GetPrimvar("displayColor").Get()[0], DISPLAY_GREY)


def test_texture_mean(tmp_path):
    """テクスチャの平均（線形）。透明な画素は数えない。"""
    a = np.zeros((10, 20, 4), np.uint8)
    a[:, :10] = (255, 255, 255, 255)
    a[:, 10:] = (0, 0, 0, 255)
    Image.fromarray(a).save(tmp_path / "half.png")
    assert _close(texture_mean(tmp_path / "half.png"), (0.5, 0.5, 0.5), 1e-3)
    a[:, 10:, 3] = 0  # 黒い半分を透明に
    Image.fromarray(a).save(tmp_path / "masked.png")
    assert _close(texture_mean(tmp_path / "masked.png"), (1, 1, 1), 1e-3)
    assert texture_mean(tmp_path / "none.png") is None


def test_display_color_prefers_texture(tmp_path):
    Image.fromarray(np.full((4, 4, 3), (0, 255, 0), np.uint8)).save(tmp_path / "g.png")
    assert _close(display_color({"texture": str(tmp_path / "g.png"), "color": "#FF0000"}), (0, 1, 0))
    # 読めないテクスチャならマテリアルの色、それもなければグレー
    assert _close(display_color({"texture": str(tmp_path / "x.png"), "color": "#FF0000"}), (1, 0, 0))
    assert display_color(None) == Gf.Vec3f(DISPLAY_GREY)
