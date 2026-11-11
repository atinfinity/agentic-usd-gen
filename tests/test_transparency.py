"""透明・半透明のマテリアルの判定（usd_post.material_transparency）。"""

import pytest
from pxr import Sdf, Usd, UsdGeom, UsdShade

from agentic_usd_gen.usd_post import mark_transparency, material_transparency


@pytest.mark.parametrize("params, expected", [
    ({"role": "pet"}, "transparent"),
    ({"role": "glass"}, "transparent"),
    ({"role": "translucent"}, "translucent"),
    ({"role": "liquid"}, "transparent"),
    ({"role": "liquid", "turbidity": 0.25}, "transparent"),  # スポーツドリンク
    ({"role": "liquid", "turbidity": 0.95}, "translucent"),  # 牛乳
    ({"role": "container"}, None),
    ({"role": "label"}, None),
    ({"role": "cap"}, None),
    ({"role": "solid"}, None),
    (None, None),
])
def test_material_transparency(params, expected):
    assert material_transparency(params) == expected


def test_mark_transparency_no_shadow():
    """素通しのメッシュと液体に primvars:doNotCastShadows を付け、ほかの半透明・不透明からは外す（作り直しで消える）。
    濁った液体（半透明）も影を落とさない（落とすと RTX Real-Time でボトルの肩と底が黒くなる）。"""
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/item").GetPrim()
    materials = {"PET": {"role": "pet"}, "Milk": {"role": "liquid", "turbidity": 0.95}, "CapMat": {"role": "cap"},
                 "HDPE": {"role": "translucent"}}
    for mesh, mat in (("Body", "PET"), ("Liquid", "Milk"), ("Cap", "CapMat"), ("Jug", "HDPE")):
        prim = UsdGeom.Mesh.Define(stage, f"/item/{mesh}").GetPrim()
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(UsdShade.Material.Define(stage, f"/item/_materials/{mat}"))
    # 前回は不透明な部品にも付いていた、とする
    UsdGeom.PrimvarsAPI(stage.GetPrimAtPath("/item/Cap")).CreatePrimvar(
        "doNotCastShadows", Sdf.ValueTypeNames.Bool, UsdGeom.Tokens.constant).Set(True)

    assert mark_transparency(stage, root, materials) == {"Body": "transparent", "Liquid": "translucent",
                                                         "Jug": "translucent"}
    for name in ("Body", "Liquid"):
        pv = UsdGeom.PrimvarsAPI(stage.GetPrimAtPath(f"/item/{name}")).GetPrimvar("doNotCastShadows")
        assert pv.Get() is True and pv.GetInterpolation() == UsdGeom.Tokens.constant
    for name in ("Jug", "Cap"):
        assert not UsdGeom.PrimvarsAPI(stage.GetPrimAtPath(f"/item/{name}")).HasPrimvar("doNotCastShadows")
