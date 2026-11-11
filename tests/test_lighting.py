"""什器に内蔵する照明（spec.Light・finish light）のテスト。"""

from dataclasses import asdict

import pytest
from pxr import Gf, Sdf, Usd, UsdLux, UsdShade

from agentic_usd_gen.fictional.products import chest_freezer_showcase, open_showcase_multideck
from agentic_usd_gen.fictional.store_counter import bun_steamer, hot_snack_case, oden_warmer
from agentic_usd_gen.fictional.store_floor import reach_in_cooler_3door
from agentic_usd_gen.lighting import LIGHT_SURFACE_LUMINANCE, VARIANT_SET, illuminance, write_lighting
from agentic_usd_gen.openpbr import add_openpbr, surface_shader
from agentic_usd_gen.spec import ProductSpec


def _lamp_material(stage):
    """Blender の書き出しと同じ形（Principled_BSDF の UsdPreviewSurface）に MDL・OpenPBR を足したもの。"""
    mat = UsdShade.Material.Define(stage, "/a/_materials/LampMat")
    ps = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Principled_BSDF"))
    ps.CreateIdAttr("UsdPreviewSurface")
    ps.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1, 1, 1))
    UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("MDL"))
    add_openpbr(mat, {"base_color": Gf.Vec3f(1, 1, 1)})
    return mat, ps


def test_illuminance_of_small_light_far_away():
    """小さな面光源から遠い点では E = L·A / d²。向きが外れると 0。"""
    light = {"size": [0.1, 0.1], "center": [0, 0, 2.0], "intensity": 1000.0}
    assert illuminance([light], [0, 0, 0], [0, 0, 1]) == pytest.approx(1000 * 0.01 / 4, rel=0.01)
    assert illuminance([light], [0, 0, 0], [0, 0, -1]) == 0  # 下を向いた面
    up = {**light, "rotation": [180.0, 0, 0]}  # 上へ照らす
    assert illuminance([up], [0, 0, 0], [0, 0, 1]) == 0


def test_lights_only_for_assembly():
    base = {"product_name": "x", "dimensions": {"height": 1, "diameter": 1},
            "lights": [{"name": "A", "size": [0.1, 0.1], "center": [0, 0, 0.5]}]}
    with pytest.raises(ValueError, match="assembly"):
        ProductSpec.from_dict({**base, "shape_class": "box"})
    with pytest.raises(ValueError, match="重なって"):
        ProductSpec.from_dict({**base, "shape_class": "assembly", "lights": base["lights"] * 2})
    spec = ProductSpec.from_dict({**base, "shape_class": "assembly"})
    assert spec.lights[0].kelvin == 5000.0


def test_lighting_variant_switches_lights_and_glow(tmp_path):
    """照明と照明の面の発光は Lighting バリアントの On（既定）だけにあり、Off にすると消える。"""
    stage = Usd.Stage.CreateInMemory()
    root = stage.DefinePrim("/a", "Xform")
    mat, ps = _lamp_material(stage)
    light = {"name": "TopLux", "size": [0.5, 0.04], "center": [0, 0, 0.5], "rotation": [35.0, 0, 0],
             "intensity": 2500.0, "kelvin": 2800.0}
    names = write_lighting(stage, root, [light], {"LampMat": {"light": True, "color": "#FFFFFF"}})
    assert names == ["TopLux"]

    vset = root.GetVariantSets().GetVariantSet(VARIANT_SET)
    assert vset.GetVariantNames() == ["Off", "On"] and vset.GetVariantSelection() == "On"
    rl = UsdLux.RectLight(stage.GetPrimAtPath("/a/Lights/TopLux"))
    assert rl and rl.GetIntensityAttr().Get() == 2500.0 and rl.GetColorTemperatureAttr().Get() == 2800.0
    assert rl.GetEnableColorTemperatureAttr().Get() and not rl.GetNormalizeAttr().Get()
    mdl = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("MDL"))
    assert mdl.GetInput("enable_emission").Get() is True
    assert mdl.GetInput("emissive_intensity").Get() == LIGHT_SURFACE_LUMINANCE
    assert ps.GetInput("emissiveColor").Get() is not None
    assert surface_shader(mat).GetInput("emission_luminance").Get() == LIGHT_SURFACE_LUMINANCE

    vset.SetVariantSelection("Off")
    assert not stage.GetPrimAtPath("/a/Lights")
    assert not mdl.GetInput("enable_emission").Get()
    assert ps.GetInput("emissiveColor").Get() is None
    assert surface_shader(mat).GetInput("emission_luminance").Get() is None


def test_no_lighting_without_lights():
    stage = Usd.Stage.CreateInMemory()
    root = stage.DefinePrim("/a", "Xform")
    assert write_lighting(stage, root, [], {"M": {"color": "#FFFFFF"}}) == []
    assert not root.GetVariantSets().HasVariantSet(VARIANT_SET)


def _lights(product):
    return [asdict(x) for x in product.lights]


# 天井照明（事務所の例）の下の照度の目安：床・台（水平な面）は 1400〜1700 lx、棚の前面（鉛直な面）は 500〜1000 lx
def test_cooler_lights_product_fronts_like_shelf_fronts():
    """冷蔵ケースは扉の内側の縦の LED で、棚の上の商品の正面を照らす。"""
    lights = _lights(reach_in_cooler_3door())
    assert {x["kelvin"] for x in lights} <= {5700.0}
    for x in (-0.593, 0.0, 0.593):  # 扉ごとの中央
        for z in (0.50, 1.02):
            assert 500 <= illuminance(lights, [x, -0.17, z], [0, -1, 0]) <= 1000


@pytest.mark.parametrize("make, levels, warm", [
    (open_showcase_multideck, [(0.43, 0.15), (0.72, 0.13), (0.98, 0.11), (1.22, 0.09)], False),
    (hot_snack_case, [(0.20, 0.0), (0.33, 0.0), (0.46, 0.0)], True),
    (bun_steamer, [(0.227, -0.08), (0.365, -0.08), (0.505, -0.08)], True),
])
def test_case_shelves_lit_like_floor(make, levels, warm):
    """棚ごとの照明で、どの段の上も天井照明の下の台と同じくらい明るい。温蔵ケースは電球色。"""
    lights = _lights(make())
    assert {x["kelvin"] for x in lights} == ({2800.0} if warm else {5700.0})
    for z, y in levels:
        assert 700 <= illuminance(lights, [0, y, z], [0, 0, 1]) <= 2600


def test_chest_freezer_lit_through_glass_lids():
    """平型冷凍ショーケースは奥の覆いの下の LED で底の商品の上面を照らす。ふたは透けるガラス。"""
    product = chest_freezer_showcase()
    lids = [p for p in product.parts if p.name.startswith("GlassLid")]
    assert len(lids) == 2 and all(p.finish == "glass" for p in lids)
    lights = _lights(product)
    assert {x["kelvin"] for x in lights} == {5700.0}
    for y in (-0.25, -0.1, 0.05, 0.2):  # 手前は天井の光もふた越しに届くので、奥より暗くてよい
        for x in (0.0, 0.45):
            assert 300 <= illuminance(lights, [x, y, 0.46], [0, 0, 1]) <= 2600
    assert illuminance(lights, [0, -0.1, 0.46], [0, 0, 1]) >= 800


def test_oden_warmer_has_no_case_lighting():
    """おでん什器はふたのない鍋で、実物にも照明はない（天井の照明で見える）。"""
    assert not oden_warmer().lights


def test_catalog_lists_lighting():
    from agentic_usd_gen.catalog import _lighting, _lighting_text

    info = _lighting([{"name": "A", "intensity": 8000.0, "kelvin": 5700.0},
                      {"name": "B", "intensity": 15000.0, "kelvin": 5700.0}])
    assert info["variant_set"] == "Lighting" and info["default"] == "On"
    assert _lighting_text(info) == "RectLight 2 個（5700 K）。`Lighting` バリアント（On / Off、既定 On）で切り替え"


def test_cigarette_wall_lights_pack_fronts():
    """たばこ陳列棚は段ごとの手前の LED で、箱の正面を棚の前面と同じくらいに照らす。"""
    from agentic_usd_gen.fictional.store_more import cigarette_display_wall
    lights = _lights(cigarette_display_wall())
    assert len(lights) == 8 and {x["kelvin"] for x in lights} == {5700.0}
    for r in range(8):
        z = 0.06 + r * 0.1125 + 0.01 + 0.044  # 段ごとの箱の正面の中央
        for x in (0.0, 0.8):
            assert 400 <= illuminance(lights, [x, -0.1305, z], [0, -1, 0]) <= 1000
