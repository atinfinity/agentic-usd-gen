"""書き出す USD を Isaac Sim のレイヤー構成に分ける処理（isaac_layout.py。SimReady の FET_100_ISAAC）のテスト。"""

import shutil

import pytest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

from agentic_usd_gen.isaac_layout import PHYSICS_PROPS, layer_paths, split_layers
from agentic_usd_gen.joints import build_links
from agentic_usd_gen.physics_runtimes import apply_runtime_schemas


def _make(path):
    """箱の本体とふた（関節でつなぐ）、テクスチャ付きのマテリアル、物理マテリアル。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "textures").mkdir()
    (path.parent / "textures" / "label.png").write_bytes(b"png")
    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, "/box").GetPrim()
    stage.SetDefaultPrim(root)
    Usd.ModelAPI(root).SetKind("component")
    stage.GetRootLayer().customLayerData = {"SimReady_Metadata": {"source": "test"}}
    for name, z in (("Body", 0.05), ("Lid", 0.15)):
        cube = UsdGeom.Cube.Define(stage, f"/box/{name}")
        cube.CreateSizeAttr(0.1)
        cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    mat = UsdShade.Material.Define(stage, "/box/_materials/Mat")
    tex = UsdShade.Shader.Define(stage, "/box/_materials/Mat/Tex")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set("./textures/label.png")
    UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/box/Body")).Bind(mat)
    pm = UsdShade.Material.Define(stage, "/box/_materials/PhysicsMaterial")
    UsdPhysics.MaterialAPI.Apply(pm.GetPrim()).CreateStaticFrictionAttr(0.5)
    UsdShade.MaterialBindingAPI(stage.GetPrimAtPath("/box/Body")).Bind(
        pm, UsdShade.Tokens.weakerThanDescendants, "physics")
    UsdPhysics.RigidBodyAPI.Apply(root)
    UsdPhysics.MassAPI.Apply(root).CreateMassAttr(0.15)
    build_links(stage, root, [{"name": "LidLink", "parts": ["Lid"], "mass": 0.05, "center_of_mass": [0, 0, 0.15],
                               "joint": {"type": "revolute", "axis": "X", "anchor": [0, 0.05, 0.1],
                                         "limits": [0.0, 90.0]}}], kinematic=False)
    apply_runtime_schemas(root)
    stage.Save()
    return path


def _snapshot(stage):
    """Prim ごとの型・スキーマ（順不同）・属性の値・関係の対象。"""
    out = {}
    for prim in stage.Traverse():
        props = {}
        for a in prim.GetAuthoredAttributes():
            v = a.Get()
            props[a.GetName()] = v.resolvedPath if isinstance(v, Sdf.AssetPath) else v
        for r in prim.GetAuthoredRelationships():
            props[r.GetName()] = r.GetTargets()
        out[str(prim.GetPath())] = (prim.GetTypeName(), sorted(prim.GetPrimTypeInfo().GetAppliedAPISchemas()), props)
    return out


def test_split_keeps_composition(tmp_path):
    usd = _make(tmp_path / "box" / "box.usd")
    before = _snapshot(Usd.Stage.Open(str(usd)))
    paths = split_layers(usd)
    assert paths == layer_paths(usd) and all(p.exists() for p in paths.values())
    assert paths["meshes"] == tmp_path / "box" / "payloads" / "box_meshes.usd"

    stage = Usd.Stage.Open(str(usd))
    # 重ねた結果は元と同じ（テクスチャも入口から見た同じファイルに解決する）
    assert _snapshot(stage) == before
    assert before["/box/_materials/Mat/Tex"][2]["inputs:file"].endswith("box/textures/label.png")

    # 入口は base への reference と kind・メタデータだけ
    entry = stage.GetRootLayer()
    (root,) = entry.rootPrims
    assert root.GetInfo("kind") == "component" and not root.nameChildren and not root.properties
    assert [r.assetPath for r in root.referenceList.prependedItems] == ["./payloads/box_base.usd"]
    assert entry.customLayerData["SimReady_Metadata"] == {"source": "test"}
    assert UsdGeom.GetStageUpAxis(stage) == "Z" and UsdGeom.GetStageMetersPerUnit(stage) == 1.0
    base = Sdf.Layer.FindOrOpen(str(paths["base"]))
    assert list(base.subLayerPaths) == ["./box_physics.usd", "./box_meshes.usd"]


def test_split_separates_physics(tmp_path):
    usd = _make(tmp_path / "box" / "box.usd")
    paths = split_layers(usd)
    meshes = Sdf.Layer.FindOrOpen(str(paths["meshes"]))
    physics = Sdf.Layer.FindOrOpen(str(paths["physics"]))

    def specs(layer):
        out = []
        layer.Traverse("/", lambda p: out.append(layer.GetObjectAtPath(p)))
        return [s for s in out if s]

    for spec in specs(meshes):
        if isinstance(spec, Sdf.PrimSpec):
            schemas = list(spec.GetInfo("apiSchemas").GetAddedOrExplicitItems()) if spec.HasInfo("apiSchemas") else []
            assert not [s for s in schemas if s.startswith(("Physics", "Mjc", "Newton"))], spec.path
            assert not spec.typeName.startswith("Physics"), spec.path
        else:
            assert not spec.name.startswith(PHYSICS_PROPS), spec.path
    # 物理のレイヤーは物理の属性と、関節・物理マテリアルの Prim だけ
    defined = {str(s.path) for s in specs(physics) if isinstance(s, Sdf.PrimSpec) and s.specifier == Sdf.SpecifierDef}
    assert defined == {"/box/LidLink/Joint", "/box/_materials/PhysicsMaterial"}
    assert physics.GetAttributeAtPath("/box.physics:mass").default == pytest.approx(0.15)
    assert physics.GetRelationshipAtPath("/box/Body.material:binding:physics")
    assert meshes.GetRelationshipAtPath("/box/Body.material:binding")
    assert meshes.GetAttributeAtPath("/box/_materials/Mat/Tex.inputs:file").default.path == "../textures/label.png"


def test_split_again(tmp_path):
    """同じプロセスで消して作り直したものを分け直しても、前のレイヤーの内容が残らない。"""
    usd = _make(tmp_path / "box" / "box.usd")
    split_layers(usd)
    shutil.rmtree(tmp_path / "box")
    usd = _make(tmp_path / "box" / "box.usd")
    paths = split_layers(usd)
    physics = Sdf.Layer.FindOrOpen(str(paths["physics"]))
    assert [p.name for p in physics.rootPrims] == ["box"]
    stage = Usd.Stage.Open(str(usd))
    assert stage.GetPrimAtPath("/box/LidLink/Joint").IsA(UsdPhysics.RevoluteJoint)
    assert len(stage.GetRootLayer().rootPrims) == 1
