"""光学以外のマテリアルの属性（nonvisual.py。SimReady の FET_007）のテスト。"""

import pytest
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Vt

from agentic_usd_gen.nonvisual import (ATTRIBUTES_ATTR, BASE_ATTR, BASES, COATING_ATTR, nonvisual_material,
                              write_nonvisual_materials)


@pytest.mark.parametrize("params, expected", [
    ({"role": "liquid"}, ("water", "none", ["visually_transparent"])),
    ({"role": "pet", "labels": ["plastic"]}, ("plexiglass", "none", ["visually_transparent"])),
    ({"role": "glass", "labels": ["glass"]}, ("clear_glass", "none", ["visually_transparent"])),
    ({"role": "translucent", "labels": ["glass"]}, ("frosted_glass", "none", ["visually_transparent"])),
    ({"role": "translucent", "labels": ["plastic"]}, ("plastic", "none", ["visually_transparent"])),
    ({"role": "container", "labels": ["metal", "aluminum"]}, ("aluminum", "none", [])),
    ({"role": "label", "labels": ["metal", "steel"], "texture": "x.png"}, ("steel", "paint", [])),
    ({"role": "label", "labels": ["paper"]}, ("paper", "paint", [])),  # 箱の印刷面
    ({"role": "cap", "labels": ["plastic"]}, ("plastic", "none", [])),
    ({"role": "cap", "labels": ["plastic"], "texture": "lid.png"}, ("plastic", "paint", [])),
    ({"role": "solid", "labels": ["metal"], "metallic": 1.0}, ("steel", "none", [])),
    ({"role": "solid", "labels": ["wood"]}, ("wood", "none", [])),
    ({"role": "solid", "labels": ["food"]}, ("skin", "none", [])),
    ({"role": "solid", "labels": ["rubber"]}, ("rubber", "none", [])),  # 一覧にある語はそのまま
    ({"role": "solid", "labels": ["urethane"]}, ("plastic", "none", [])),  # 一覧にない語は plastic
    ({"role": "solid", "labels": ["plastic"], "metallic": 0.9}, ("steel", "none", [])),  # 金属に見えるなら金属
    (None, ("plastic", "none", [])),
])
def test_nonvisual_material(params, expected):
    base, coating, attributes = nonvisual_material(params)
    assert (base, coating, attributes) == expected and base in BASES


def _quad(stage, path, faces=1):
    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * faces))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([0, 1, 2, 3] * faces))
    mesh.CreatePointsAttr(Vt.Vec3fArray([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]))
    return mesh


def test_write_only_bound_to_meshes():
    """メッシュに割り当てたマテリアルにだけ書く。物理マテリアル・面の組だけのマテリアル・guide のものには書かない（NVM.004）。"""
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(stage, "/a")
    mats = {n: UsdShade.Material.Define(stage, f"/a/_materials/{n}")
            for n in ("PET", "CapMat", "CapTopMat", "GuideMat", "PhysicsMaterial", "Unused")}
    body = _quad(stage, "/a/Body")
    UsdShade.MaterialBindingAPI.Apply(body.GetPrim()).Bind(mats["PET"])
    UsdShade.MaterialBindingAPI(body.GetPrim()).Bind(mats["PhysicsMaterial"], materialPurpose="physics")
    UsdPhysics.MaterialAPI.Apply(mats["PhysicsMaterial"].GetPrim())
    cap = _quad(stage, "/a/Cap", 2)
    UsdShade.MaterialBindingAPI.Apply(cap.GetPrim()).Bind(mats["CapMat"])
    sub = UsdGeom.Subset.CreateGeomSubset(cap, "top", UsdGeom.Tokens.face, Vt.IntArray([1]), familyName="materialBind")
    UsdShade.MaterialBindingAPI.Apply(sub.GetPrim()).Bind(mats["CapTopMat"])
    guide = _quad(stage, "/a/Guide")
    guide.CreatePurposeAttr(UsdGeom.Tokens.guide)
    UsdShade.MaterialBindingAPI.Apply(guide.GetPrim()).Bind(mats["GuideMat"])

    out = write_nonvisual_materials(stage, stage.GetPrimAtPath("/a"),
                                    {"PET": {"role": "pet"}, "CapMat": {"role": "cap", "labels": ["plastic"]}})
    assert out == {"CapMat": "plastic", "PET": "plexiglass"}
    pet = mats["PET"].GetPrim()
    assert pet.GetAttribute(BASE_ATTR).GetTypeName() == "token"
    assert pet.GetAttribute(COATING_ATTR).Get() == "none"
    attr = pet.GetAttribute(ATTRIBUTES_ATTR)
    assert attr.GetTypeName() == "token[]" and list(attr.Get()) == ["visually_transparent"]
    assert attr.GetNumTimeSamples() == 0  # NVM.006
    for n in ("CapTopMat", "GuideMat", "PhysicsMaterial", "Unused"):
        assert not mats[n].GetPrim().HasAttribute(BASE_ATTR), n
