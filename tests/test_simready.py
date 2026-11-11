"""SimReady Foundation の検証（agentic-usd-gen-simready）のテスト。simready-validate がなければ飛ばす。"""

import json

import pytest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

pytest.importorskip("simready.validate")

from agentic_usd_gen.simready import check, find_assets, main  # noqa: E402


def _make_usd(path, mdl: bool):
    """剛体の箱 1 つ。mdl なら Isaac Sim 組み込みの OmniPBR を参照するマテリアルを付ける。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, "/box")
    stage.SetDefaultPrim(root.GetPrim())
    cube = UsdGeom.Cube.Define(stage, "/box/Body")
    cube.CreateSizeAttr(0.1)
    cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.05))
    UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
    UsdPhysics.MassAPI.Apply(root.GetPrim()).CreateMassAttr(0.2)
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    if mdl:
        mat = UsdShade.Material.Define(stage, "/box/_materials/Mat")
        sh = UsdShade.Shader.Define(stage, "/box/_materials/Mat/MDL")
        sh.SetSourceAsset(Sdf.AssetPath("OmniPBR.mdl"), "mdl")
        sh.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
        mat.CreateSurfaceOutput("mdl").ConnectToSource(sh.ConnectableAPI(), "out")
        UsdShade.MaterialBindingAPI.Apply(cube.GetPrim()).Bind(mat)
    stage.Save()
    return path


def test_mdl_is_expected_by_default(tmp_path):
    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    res = check(usd)
    assert res is not None and res.profile == "Robotics-Prop"
    assert res.expected_mdl and all(i.code == "NP.008" for i in res.expected_mdl)
    assert not any(i.code == "NP.008" and ".mdl'" in i.message for i in res.issues)

    strict = check(usd, strict_mdl=True)
    assert not strict.expected_mdl
    assert any(i.code == "NP.008" for i in strict.issues)
    assert not strict.passed


def test_reports_requirement_codes(tmp_path):
    res = check(_make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=False))
    codes = {i.code for i in res.issues}
    assert "SR.004" in codes  # 出所のメタデータを書いていない
    assert all("." in c and not c.startswith("com.") for c in codes)
    assert not res.passed


def test_cli(tmp_path, capsys):
    _make_usd(tmp_path / "assets" / "box" / "usd" / "box.usd", mdl=True)
    (tmp_path / "assets" / "box" / "usd" / ".thumbs").mkdir()
    (tmp_path / "assets" / "box" / "usd" / ".thumbs" / "x.usd").write_text("#usda 1.0\n")
    (tmp_path / "assets" / "box" / "usd" / "payloads").mkdir()
    (tmp_path / "assets" / "box" / "usd" / "payloads" / "box_base.usd").write_text("#usda 1.0\n")
    assert [p.name for p in find_assets([tmp_path / "assets"])] == ["box.usd"]  # .thumbs・payloads は除く

    out = tmp_path / "report.json"
    assert main([str(tmp_path / "assets"), "--output", str(out)]) == 1
    report = json.loads(out.read_text())
    assert len(report) == 1 and report[0]["passed"] is False
    assert "合格: 0 / 1 点" in capsys.readouterr().out


@pytest.mark.parametrize("approx", ["convexDecomposition", "meshSimplification", "boundingCube"])
def test_collision_approximation(tmp_path, approx):
    """コリジョンの近似方法を変えても、convexHull のときと同じ要件しか落ちない（新しい不適合が出ない）。"""
    def codes(name, a):
        path = tmp_path / name / "usd" / f"{name}.usd"
        path.parent.mkdir(parents=True)
        stage = Usd.Stage.CreateNew(str(path))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(stage, f"/{name}")
        stage.SetDefaultPrim(root.GetPrim())
        mesh = UsdGeom.Mesh.Define(stage, f"/{name}/Body")
        mesh.CreatePointsAttr([(x, y, z) for z in (0, 0.1) for y in (-0.05, 0.05) for x in (-0.05, 0.05)])
        mesh.CreateFaceVertexCountsAttr([4] * 6)
        mesh.CreateFaceVertexIndicesAttr([0, 2, 3, 1, 4, 5, 7, 6, 0, 1, 5, 4, 2, 6, 7, 3, 0, 4, 6, 2, 1, 3, 7, 5])
        UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
        UsdPhysics.MassAPI.Apply(root.GetPrim()).CreateMassAttr(0.2)
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr(a)
        stage.Save()
        return {(i.code, i.message.replace(name, "ASSET")) for i in check(path).issues}

    assert codes("box_test", approx) == codes("box_hull", "convexHull")


def test_nonvisual_materials(tmp_path):
    """光学以外の属性を書けば FET_007 を満たす。書かなければ未対応の理由（NVM の要件）を拾う。"""
    from agentic_usd_gen.nonvisual import write_nonvisual_materials

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    before = check(usd)
    assert "FET_007_STANDARD" in before.optional_failed
    assert {i.code for i in before.optional_issues["FET_007_STANDARD"]} >= {"NVM.001", "NVM.002", "NVM.003"}

    stage = Usd.Stage.Open(str(usd))
    write_nonvisual_materials(stage, stage.GetDefaultPrim(), {"Mat": {"role": "label", "labels": ["paper"]}})
    stage.Save()
    after = check(usd)
    assert "FET_007_STANDARD" not in after.optional_failed and "FET_007_STANDARD" not in after.optional_issues


def test_grasp_lines(tmp_path):
    """把持の線を書けば GSP.001 を満たす（FET_005 には物理マテリアル PMT.001 も要るが、この箱にはない）。"""
    from agentic_usd_gen.grasp import write_grasp_lines

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    before = check(usd)
    assert "FET_005_STANDARD" in before.optional_failed
    assert "GSP.001" in {i.code for i in before.optional_issues["FET_005_STANDARD"]}

    stage = Usd.Stage.Open(str(usd))
    # 把持の線はメッシュの頂点から決める。箱は Cube なので、線を引くための仮のメッシュを置いて後で消す
    mesh = UsdGeom.Mesh.Define(stage, "/box/Shell")
    mesh.CreatePointsAttr([(-0.05, -0.02, 0), (0.05, 0.02, 0.1)])
    mesh.CreateFaceVertexCountsAttr([2])
    mesh.CreateFaceVertexIndicesAttr([0, 1])
    assert write_grasp_lines(stage, stage.GetDefaultPrim())
    stage.RemovePrim("/box/Shell")
    stage.Save()
    after = check(usd)
    assert {i.code for i in after.optional_issues["FET_005_STANDARD"]} == {"PMT.001"}


def test_openpbr(tmp_path):
    """OpenPBR の出力を足せば FET_006_OPENPBR を満たす（テクスチャの色空間も含む）。"""
    import numpy as np
    from PIL import Image

    from agentic_usd_gen.openpbr import add_openpbr, connect_maps

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    assert "FET_006_OPENPBR" in check(usd).optional_failed

    (usd.parent / "textures").mkdir()
    for name in ("color", "rough", "normal"):
        Image.fromarray(np.full((4, 4, 3), 128, np.uint8)).save(usd.parent / "textures" / f"{name}.png")
    stage = Usd.Stage.Open(str(usd))
    mat = UsdShade.Material.Get(stage, "/box/_materials/Mat")
    add_openpbr(mat, {"base_metalness": 0.0, "specular_roughness": 0.4, "specular_ior": 1.5},
                base_texture="./textures/color.png")
    connect_maps(mat, {"roughness": "./textures/rough.png", "normal": "./textures/normal.png"})
    stage.Save()
    after = check(usd)
    assert "FET_006_OPENPBR" not in after.optional_failed, after.optional_issues.get("FET_006_OPENPBR")


def test_runtime_colliders(tmp_path):
    """MuJoCo・Newton のスキーマを付ければ FET_003_MUJOCO・FET_003_NEWTON を満たす。"""
    from agentic_usd_gen.physics_runtimes import apply_runtime_schemas

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    before = check(usd)
    assert "FET_003_MUJOCO" in before.optional_failed  # 箱は Cube なので Newton はメッシュの要件がなく元から通る

    stage = Usd.Stage.Open(str(usd))
    apply_runtime_schemas(stage.GetDefaultPrim())
    stage.Save()
    after = check(usd)
    for fet in ("FET_003_MUJOCO", "FET_003_NEWTON"):
        assert fet not in after.optional_failed, after.optional_issues.get(fet)


def test_multibody_joints(tmp_path):
    """可動部の剛体を関節で本体につなげば FET_004（剛体 2 つ以上・関節）を満たす。"""
    from agentic_usd_gen.joints import build_links
    from agentic_usd_gen.physics_runtimes import apply_runtime_schemas

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    before = check(usd)
    assert "FET_004_STANDARD" in before.optional_failed
    assert "RB.MB.001" in {i.code for i in before.optional_issues["FET_004_STANDARD"]}

    stage = Usd.Stage.Open(str(usd))
    lid = UsdGeom.Cube.Define(stage, "/box/Lid")
    lid.CreateSizeAttr(0.1)
    lid.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.15))
    UsdPhysics.CollisionAPI.Apply(lid.GetPrim())
    UsdPhysics.MassAPI(stage.GetDefaultPrim()).GetMassAttr().Set(0.15)
    build_links(stage, stage.GetDefaultPrim(), [
        {"name": "LidLink", "parts": ["Lid"], "mass": 0.05, "center_of_mass": [0, 0, 0.15],
         "joint": {"type": "revolute", "axis": "X", "anchor": [0, 0.05, 0.1], "limits": [0.0, 90.0]}}],
        kinematic=False)
    apply_runtime_schemas(stage.GetDefaultPrim())  # FET_004_MUJOCO・NEWTON は FET_003 のコライダーの要件も含む
    stage.Save()
    after = check(usd)
    fets = [f for f in before.optional_failed if f.startswith("FET_004")]
    assert set(fets) >= {"FET_004_STANDARD", "FET_004_PHYSX", "FET_004_NEWTON", "FET_004_MUJOCO"}
    for fet in fets:
        assert fet not in after.optional_failed, after.optional_issues.get(fet)


def test_isaac_composition(tmp_path):
    """入口と base・meshes・physics のレイヤーに分ければ FET_100_ISAAC を満たし、ほかの判定は変わらない。"""
    from agentic_usd_gen.isaac_layout import split_layers

    usd = _make_usd(tmp_path / "box" / "usd" / "box.usd", mdl=True)
    stage = Usd.Stage.Open(str(usd))
    Usd.ModelAPI(stage.GetDefaultPrim()).SetKind("component")
    stage.Save()
    before = check(usd)
    assert "FET_100_ISAAC" in before.optional_failed

    split_layers(usd)
    after = check(usd)
    assert "FET_100_ISAAC" not in after.optional_failed, after.optional_issues.get("FET_100_ISAAC")
    assert after.passed == before.passed
    assert set(after.optional_failed) == set(before.optional_failed) - {"FET_100_ISAAC"}
