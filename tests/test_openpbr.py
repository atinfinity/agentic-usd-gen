"""OpenPBR のマテリアル（openpbr.py。SimReady の FET_006_OPENPBR）のテスト。合成したステージを使う。"""

import pytest
from pxr import Gf, Sdf, Usd, UsdShade

from agentic_usd_gen.openpbr import (
    DATA,
    SRGB,
    SURFACE_ID,
    add_openpbr,
    connect_maps,
    surface_shader,
)


@pytest.fixture
def stage():
    return Usd.Stage.CreateInMemory()


@pytest.fixture
def mat(stage):
    return UsdShade.Material.Define(stage, "/a/_materials/Mat")


def _source(inp):
    src, out_name, _ = inp.GetConnectedSource()
    return UsdShade.Shader(src.GetPrim()), out_name


def test_surface_output_and_ranges(mat):
    """outputs:mtlx:surface を OpenPBR に繋ぐ（VM.PBR.001）。値は範囲に収める（VM.PBR.002）。"""
    sh = add_openpbr(mat, {"base_color": Gf.Vec3f(1.2, 0.5, -0.1), "specular_ior": 4.0, "base_metalness": 1.5,
                           "transmission_depth": 2.0, "geometry_thin_walled": True})
    src, out_name = _source(mat.GetSurfaceOutput("mtlx"))
    assert src.GetPath() == sh.GetPath() and out_name == "out"
    assert sh.GetIdAttr().Get() == SURFACE_ID and sh.GetOutput("out").GetTypeName() == "token"
    assert tuple(sh.GetInput("base_color").Get()) == (1.0, 0.5, 0.0)
    assert sh.GetInput("base_color").GetTypeName() == Sdf.ValueTypeNames.Color3f
    assert sh.GetInput("specular_ior").Get() == 3.0
    assert sh.GetInput("base_metalness").Get() == 1.0
    assert sh.GetInput("transmission_depth").Get() == 2.0  # 深さは長さなので 1 で切らない
    thin = sh.GetInput("geometry_thin_walled")
    assert thin.Get() is True and thin.GetTypeName() == Sdf.ValueTypeNames.Bool
    assert surface_shader(mat).GetPath() == sh.GetPath()


def test_base_texture_is_srgb(mat):
    """色のテクスチャは image ノードで読み、ファイルの属性に srgb_texture を書く（VM.TEX.004）。"""
    sh = add_openpbr(mat, {"specular_roughness": 0.3}, base_texture="./textures/label.png")
    tex, out_name = _source(sh.GetInput("base_color"))
    assert tex.GetIdAttr().Get() == "ND_image_color3" and out_name == "out"
    f = tex.GetInput("file")
    assert f.Get().path == "./textures/label.png" and f.GetAttr().GetColorSpace() == SRGB


def test_connect_maps(mat):
    """粗さ・金属度は ND_image_float、法線は ND_image_vector3 → ND_normalmap_float。どれも色空間は none。"""
    sh = add_openpbr(mat, {"base_color": Gf.Vec3f(0.5, 0.5, 0.5)})
    connect_maps(mat, {"roughness": "./r.png", "metallic": "./m.png", "normal": "./n.png"})
    for name, file in (("specular_roughness", "./r.png"), ("base_metalness", "./m.png")):
        tex, _ = _source(sh.GetInput(name))
        assert tex.GetIdAttr().Get() == "ND_image_float"
        assert tex.GetInput("file").Get().path == file and tex.GetInput("file").GetAttr().GetColorSpace() == DATA
    nm, _ = _source(sh.GetInput("geometry_normal"))
    assert nm.GetIdAttr().Get() == "ND_normalmap_float"
    assert sh.GetInput("geometry_normal").GetTypeName() == Sdf.ValueTypeNames.Float3
    tex, _ = _source(nm.GetInput("in"))
    assert tex.GetIdAttr().Get() == "ND_image_vector3" and tex.GetInput("file").GetAttr().GetColorSpace() == DATA


def test_connect_maps_without_openpbr(mat):
    connect_maps(mat, {"roughness": "./r.png"})  # OpenPBR がなければ何もしない
    assert not mat.GetPrim().GetChildren()
