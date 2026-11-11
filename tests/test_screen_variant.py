"""光る画面の Screen バリアント（On = 画像を映す、Off = 消えた画面）のテスト。"""

import numpy as np
from PIL import Image
from pxr import Sdf, Usd, UsdGeom, UsdShade

from agentic_usd_gen.catalog import _screen, _screen_text
from agentic_usd_gen.nonvisual import BASE_ATTR
from agentic_usd_gen.screen import VARIANT_SET, screen_materials, write_screen_variant
from agentic_usd_gen.usd_post import _setup_material


def _screen_stage(tmp_path):
    """Blender の書き出しと同じ形の画面のマテリアルと、それを割り当てたメッシュ・枠のメッシュ。"""
    tex = tmp_path / "Screen.png"
    Image.fromarray(np.full((8, 8, 3), 120, np.uint8)).save(tex)
    stage = Usd.Stage.CreateInMemory()
    root = stage.DefinePrim("/a", "Xform")
    params = {}
    for name in ("ScreenMat", "FrameMat"):
        mat = UsdShade.Material.Define(stage, f"/a/_materials/{name}")
        ps = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Principled_BSDF"))
        ps.CreateIdAttr("UsdPreviewSurface")
        mat.CreateSurfaceOutput().ConnectToSource(ps.CreateOutput("surface", Sdf.ValueTypeNames.Token))
        p = {"role": "solid", "color": "#111111", "roughness": 0.25}
        if name == "ScreenMat":
            p.update(texture=str(tex), texture_rel="./textures/Screen.png", emissive=True, smooth=True)
        _setup_material(mat, p)
        mat.GetPrim().CreateAttribute(BASE_ATTR, Sdf.ValueTypeNames.Token).Set("glass")
        params[name] = p
        mesh = UsdGeom.Mesh.Define(stage, f"/a/{name.removesuffix('Mat')}")
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    return stage, root, params


def _bound(stage, path):
    mat, _ = UsdShade.MaterialBindingAPI(stage.GetPrimAtPath(path)).ComputeBoundMaterial()
    return mat.GetPath().name


def test_screen_variant_switches_binding(tmp_path):
    """画面のメッシュだけ Screen バリアントで割り当てが変わる。既定は On。"""
    stage, root, params = _screen_stage(tmp_path)
    assert screen_materials(params) == ["ScreenMat"]
    assert write_screen_variant(stage, root, params) == ["ScreenMat"]

    vset = root.GetVariantSets().GetVariantSet(VARIANT_SET)
    assert vset.GetVariantNames() == ["Off", "On"] and vset.GetVariantSelection() == "On"
    assert _bound(stage, "/a/Screen") == "ScreenMat"
    vset.SetVariantSelection("Off")
    assert _bound(stage, "/a/Screen") == "ScreenMat_Off"
    assert _bound(stage, "/a/Frame") == "FrameMat"
    # 割り当てはバリアントの中だけ（外に残ると切り替わらない）
    spec = stage.GetRootLayer().GetPrimAtPath("/a/Screen")
    assert "material:binding" not in spec.relationships


def test_off_material_is_dark_and_not_emissive(tmp_path):
    stage, root, params = _screen_stage(tmp_path)
    write_screen_variant(stage, root, params)
    off = stage.GetPrimAtPath("/a/_materials/ScreenMat_Off")
    mdl = UsdShade.Shader(off.GetChild("MDL"))
    assert not mdl.GetInput("enable_emission")
    assert not mdl.GetInput("diffuse_texture")
    col = mdl.GetInput("diffuse_color_constant").Get()
    assert max(col) < 0.01
    ps = UsdShade.Shader(off.GetChild("Principled_BSDF"))
    assert not ps.GetInput("emissiveColor")
    # 光学以外の属性は元の画面のものを写す
    assert off.GetAttribute(BASE_ATTR).Get() == "glass"


def test_no_variant_without_screens(tmp_path):
    stage, root, params = _screen_stage(tmp_path)
    plain = {"FrameMat": params["FrameMat"]}
    assert write_screen_variant(stage, root, plain) == []
    assert not root.GetVariantSets().HasVariantSet(VARIANT_SET)


def test_catalog_screen_info():
    info = _screen([{"material": "ScreenMat", "image": "./textures/Screen.png"}])
    assert info == {"variant_set": "Screen", "variants": ["On", "Off"], "default": "On",
                    "materials": [{"name": "ScreenMat", "image": "./textures/Screen.png", "off": "ScreenMat_Off"}]}
    assert "Off = 消えた画面" in _screen_text(info)


def test_catalog_screen_places():
    """screen_places goes to asset.json screen.places; the exit sign suits every place ("any")."""
    from agentic_usd_gen.fictional import registry

    info = _screen([{"material": "PanelMat", "image": "./textures/Panel.png"}], ["any"])
    assert info["places"] == ["any"]
    assert "合う場所 any" in _screen_text(info)
    assert "places" not in _screen([{"material": "M", "image": "./t.png"}])
    sign = registry.PRODUCTS["emergency_exit_sign"]().spec()
    assert sign.screen_places == ["any"] and not sign.picture_places
    assert type(sign).from_dict(sign.to_dict()).screen_places == ["any"]
