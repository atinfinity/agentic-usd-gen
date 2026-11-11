"""光る画面（部品の finish が screen）とつやのある面（glossy）のマテリアルのテスト。"""

import numpy as np
from PIL import Image
from pxr import Sdf, Usd, UsdShade

from agentic_usd_gen.openpbr import surface_shader
from agentic_usd_gen.usd_post import SCREEN_DIFFUSE, SCREEN_LUMINANCE, _setup_material, write_surface_maps


def _blender_like_material(stage, rel):
    """Blender の書き出しと同じ形（UsdPreviewSurface の diffuseColor に画像を繋いだもの）を作る。"""
    mat = UsdShade.Material.Define(stage, "/a/_materials/ScreenMat")
    ps = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Principled_BSDF"))
    ps.CreateIdAttr("UsdPreviewSurface")
    uv = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("uvmap"))
    uv.CreateIdAttr("UsdPrimvarReader_float2")
    tex = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Image_Texture"))
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(rel))
    tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        uv.CreateOutput("result", Sdf.ValueTypeNames.Float2))
    ps.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3))
    return mat, ps, tex


def _params(tmp_path, **kw):
    tex = tmp_path / "Screen.png"
    Image.fromarray(np.full((64, 64, 3), 120, np.uint8)).save(tex)
    return {"role": "solid", "color": "#111111", "roughness": 0.25, "metallic": 0.0,
            "texture": str(tex), "texture_rel": "./textures/Screen.png", **kw}


def test_smooth_surfaces_get_no_maps(tmp_path):
    """glossy・screen の面には法線・粗さのむらのテクスチャを作らない。ほかの面には作る。"""
    smooth = _params(tmp_path, smooth=True)
    write_surface_maps(smooth)
    assert "maps" not in smooth
    plain = _params(tmp_path)
    write_surface_maps(plain)
    assert set(plain["maps"]) == {"roughness", "normal"}


def test_screen_emits_its_image(tmp_path):
    """画面の画像を UsdPreviewSurface・OmniPBR・OpenPBR の発光に繋ぎ、拡散反射を弱める。"""
    stage = Usd.Stage.CreateInMemory()
    mat, ps, tex = _blender_like_material(stage, "./textures/Screen.png")
    UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("MDL"))  # _add_mdl が作り直す
    _setup_material(mat, _params(tmp_path, smooth=True, emissive=True))

    src, _, _ = ps.GetInput("emissiveColor").GetConnectedSource()
    emis = UsdShade.Shader(src.GetPrim())
    assert emis.GetInput("file").Get().path == "./textures/Screen.png"
    assert emis.GetInput("st").GetConnectedSource()[0].GetPath().name == "uvmap"
    assert abs(tex.GetInput("scale").Get()[0] - SCREEN_DIFFUSE) < 1e-6

    mdl = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("MDL"))
    assert mdl.GetInput("enable_emission").Get() is True
    assert mdl.GetInput("emissive_color_texture").Get().path == "./textures/Screen.png"
    assert mdl.GetInput("emissive_intensity").Get() == SCREEN_LUMINANCE

    sh = surface_shader(mat)
    assert sh.GetInput("emission_luminance").Get() == SCREEN_LUMINANCE
    assert sh.GetInput("emission_color").GetConnectedSource()[0]
    assert abs(sh.GetInput("base_weight").Get() - SCREEN_DIFFUSE) < 1e-6


def test_glossy_does_not_emit(tmp_path):
    stage = Usd.Stage.CreateInMemory()
    mat, ps, _ = _blender_like_material(stage, "./textures/Screen.png")
    _setup_material(mat, _params(tmp_path, smooth=True))
    assert not ps.GetInput("emissiveColor")
    assert not surface_shader(mat).GetInput("emission_luminance")
