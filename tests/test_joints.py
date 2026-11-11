"""可動部（扉など）の仕様の検査と、剛体・関節を書く処理（joints.py）のテスト。SimReady の FET_004。"""

import numpy as np
import pytest
from pxr import Gf, Usd, UsdGeom, UsdPhysics

from agentic_usd_gen.joints import body_mass, build_links
from agentic_usd_gen.shapes.assembly import link_bodies
from agentic_usd_gen.spec import Dimensions, Joint, Part, ProductSpec


def _parts(link="DoorLink", collision=True):
    return [
        Part("Body", "box", [0.6, 0.5, 1.0], [0, 0, 0.5]),
        Part("Door", "box", [0.6, 0.02, 1.0], [0, -0.26, 0.5], link=link, collision=collision),
    ]


def _spec(parts=None, joints=None, shape_class="assembly"):
    return ProductSpec(product_name="テスト棚", slug="test_cab", shape_class=shape_class,
                       dimensions=Dimensions(1.0, 0.6, depth=0.52), mass_kg=20.0, category="fixture",
                       parts=_parts() if parts is None else parts,
                       joints=[Joint(link="DoorLink", anchor=[-0.3, -0.27, 0.5], limits=[-90.0, 0.0])]
                       if joints is None else joints, static=True)


def test_spec_round_trip():
    spec = _spec()
    d = spec.to_dict()
    assert d["joints"][0] == {"link": "DoorLink", "anchor": [-0.3, -0.27, 0.5], "limits": [-90.0, 0.0],
                              "type": "revolute", "axis": "Z"}
    assert d["parts"][1]["link"] == "DoorLink" and "link" not in d["parts"][0]
    back = ProductSpec.from_dict(d)
    assert back.joints == spec.joints and back.parts[1].link == "DoorLink"
    # 可動部のない仕様は今までと同じ出力（joints・link を出さない）
    plain = _spec(parts=_parts(link=None), joints=[]).to_dict()
    assert "joints" not in plain and all("link" not in p for p in plain["parts"])


@pytest.mark.parametrize("kwargs, msg", [
    ({"joints": [Joint("DoorLink", [0, 0, 0], [0, 1], type="ball")]}, "type"),
    ({"joints": [Joint("DoorLink", [0, 0, 0], [0, 1], axis="W")]}, "axis"),
    ({"joints": [Joint("DoorLink", [0, 0], [0, 1])]}, "anchor"),
    ({"joints": [Joint("DoorLink", [0, 0, 0], [1, 0])]}, "limits"),
    ({"joints": []}, "対応していません"),
    ({"joints": [Joint("DoorLink", [0, 0, 0], [0, 1]), Joint("DoorLink", [0, 0, 0], [0, 1])]}, "2 つ以上"),
    ({"parts": _parts(link="Body")}, "重なって"),
    ({"parts": _parts(collision=False)}, "コリジョン"),
])
def test_spec_errors(kwargs, msg):
    with pytest.raises(ValueError, match=msg):
        _spec(**kwargs)


def test_spec_assembly_only():
    with pytest.raises(ValueError, match="assembly"):
        _spec(shape_class="box")


def test_link_bodies():
    spec = _spec()
    objects = [{"name": "Body"}, {"name": "Door"}]
    shift = np.array([0.0, 0.01, 0.0])
    (lk,) = link_bodies(spec.parts, spec.joints, objects, [3.0, 1.0], [[0, 0, 0.5], [0, -0.26, 0.5]], shift, 20.0)
    assert lk["name"] == "DoorLink" and lk["parts"] == ["Door"]
    assert lk["mass"] == pytest.approx(5.0)  # 体積比 1/4
    assert lk["center_of_mass"] == pytest.approx([0, -0.25, 0.5])
    assert lk["joint"] == {"type": "revolute", "axis": "Z", "anchor": pytest.approx([-0.3, -0.26, 0.5]),
                           "limits": [-90.0, 0.0]}


def test_body_mass():
    m, com = body_mass(20.0, (0, 0, 0.5), [{"mass": 5.0, "center_of_mass": [0, -0.4, 0.5]}])
    assert m == pytest.approx(15.0)
    # 総和の重心は元の重心に戻る
    assert Gf.IsClose(Gf.Vec3d(com) * 15 + Gf.Vec3d(0, -0.4, 0.5) * 5, Gf.Vec3d(0, 0, 10), 1e-5)


def _stage(kinematic):
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/cab").GetPrim()
    for name in ("Body", "Door"):
        UsdPhysics.CollisionAPI.Apply(UsdGeom.Cube.Define(stage, f"/cab/{name}").GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(root).CreateKinematicEnabledAttr(kinematic)
    return stage, root


@pytest.mark.parametrize("kinematic", [True, False])
def test_build_links(kinematic):
    stage, root = _stage(kinematic)
    links = [{"name": "DoorLink", "parts": ["Door"], "mass": 5.0, "center_of_mass": [0, -0.25, 0.5],
              "joint": {"type": "revolute", "axis": "Z", "anchor": [-0.3, -0.26000001, 0.5],
                        "limits": [-90.0, 0.0]}}]
    out = build_links(stage, root, links, kinematic=kinematic)
    assert out == [{"link": "DoorLink", "type": "revolute", "axis": "Z", "anchor": [-0.3, -0.26, 0.5],
                    "limits": [-90.0, 0.0], "mass": 5.0, "parts": ["Door"]}]
    # 部品は可動部の Xform の下に移り、コリジョンもそのまま
    assert not stage.GetPrimAtPath("/cab/Door")
    assert stage.GetPrimAtPath("/cab/DoorLink/Door").HasAPI(UsdPhysics.CollisionAPI)
    link = stage.GetPrimAtPath("/cab/DoorLink")
    assert link.HasAPI(UsdPhysics.RigidBodyAPI) and UsdPhysics.MassAPI(link).GetMassAttr().Get() == 5.0
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/cab/DoorLink/Joint"))
    assert joint.GetBody0Rel().GetTargets() == [root.GetPath()]
    assert joint.GetBody1Rel().GetTargets() == [link.GetPath()]
    assert joint.GetLocalPos0Attr().Get() == joint.GetLocalPos1Attr().Get()
    # キネマティックな本体にはアーティキュレーションを付けない（JT.ART.003）
    assert root.HasAPI(UsdPhysics.ArticulationRootAPI) is not kinematic


def test_build_prismatic():
    stage, root = _stage(False)
    links = [{"name": "DoorLink", "parts": ["Door"], "mass": 1.0, "center_of_mass": [0, 0, 0],
              "joint": {"type": "prismatic", "axis": "X", "anchor": [0, 0, 0], "limits": [0.0, 0.3]}}]
    build_links(stage, root, links, kinematic=False)
    joint = UsdPhysics.PrismaticJoint(stage.GetPrimAtPath("/cab/DoorLink/Joint"))
    assert joint and joint.GetAxisAttr().Get() == "X" and joint.GetUpperLimitAttr().Get() == pytest.approx(0.3)


def test_build_free_revolute():
    """limits が None の回転は限界を書かない（スキーマの既定 -inf〜inf のまま回り続ける）。"""
    import math

    stage, root = _stage(True)
    links = [{"name": "DoorLink", "parts": ["Door"], "mass": 1.0, "center_of_mass": [0, 0, 0],
              "joint": {"type": "revolute", "axis": "Z", "anchor": [0, 0, 0], "limits": None}}]
    out = build_links(stage, root, links, kinematic=True)
    assert out[0]["limits"] is None
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/cab/DoorLink/Joint"))
    assert not joint.GetLowerLimitAttr().HasAuthoredValue() and not joint.GetUpperLimitAttr().HasAuthoredValue()
    assert math.isinf(joint.GetLowerLimitAttr().Get()) and math.isinf(joint.GetUpperLimitAttr().Get())


def test_spec_free_revolute():
    spec = _spec(joints=[Joint(link="DoorLink", anchor=[0, 0, 0], limits=None)])
    assert ProductSpec.from_dict(spec.to_dict()).joints[0].limits is None
    with pytest.raises(ValueError, match="revolute だけ"):
        _spec(joints=[Joint(link="DoorLink", anchor=[0, 0, 0], limits=None, type="prismatic")])


def test_build_links_moves_variant_bindings():
    """Picture・Screen バリアントの中の割り当ても、部品と一緒に可動部の下へ移る。"""
    from pxr import UsdShade

    from agentic_usd_gen.screen import bound_meshes, write_binding_variant

    stage, root = _stage(True)
    mats = {n: UsdShade.Material.Define(stage, f"/cab/_materials/{n}") for n in ("Pic", "Pic_Blank")}
    UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/cab/Door")).Bind(mats["Pic"])
    bound = bound_meshes(root, {mats["Pic"].GetPath()})
    write_binding_variant(root, "Picture", ("Default", "Blank"), "Default", bound,
                          {"Blank": {mats["Pic"].GetPath(): mats["Pic_Blank"].GetPath()}})
    links = [{"name": "DoorLink", "parts": ["Door"], "mass": 1.0, "center_of_mass": [0, 0, 0],
              "joint": {"type": "revolute", "axis": "Z", "anchor": [0, 0, 0], "limits": [-90.0, 0.0]}}]
    build_links(stage, root, links, kinematic=True)
    door = stage.GetPrimAtPath("/cab/DoorLink/Door")
    vset = root.GetVariantSet("Picture")
    for v, name in (("Default", "Pic"), ("Blank", "Pic_Blank")):
        vset.SetVariantSelection(v)
        assert UsdShade.MaterialBindingAPI(door).ComputeBoundMaterial()[0].GetPath() == mats[name].GetPath()
    assert not stage.GetPrimAtPath("/cab/Door")


def test_no_links():
    stage, root = _stage(False)
    assert build_links(stage, root, [], kinematic=False) == []
    assert not root.HasAPI(UsdPhysics.ArticulationRootAPI)


def test_joints_text():
    from agentic_usd_gen.catalog import _joints_text

    text = _joints_text([
        {"link": "Door0Link", "type": "revolute", "axis": "Z", "limits": [-100.0, 0.0], "mass": 6.881},
        {"link": "LidLink", "type": "prismatic", "axis": "X", "limits": [0.0, 0.3], "mass": 1.0}])
    assert text == "Door0Link: 回転（Z 軸、-100〜0°、6.881 kg）、LidLink: スライド（X 軸、0〜0.3 m、1 kg）"
    free = _joints_text([{"link": "SpinnerLink", "type": "revolute", "axis": "Z", "limits": None, "mass": 4.0}])
    assert free == "SpinnerLink: 回転（Z 軸、限界なし（回り続ける）、4 kg）"
