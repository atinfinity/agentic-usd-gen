"""MuJoCo・Newton のコリジョンのスキーマ（physics_runtimes.py。SimReady の FET_003）のテスト。"""

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

from agentic_usd_gen.physics_runtimes import (
    MJC_COLLISION,
    NEWTON_COLLISION,
    NEWTON_MATERIAL,
    NEWTON_MESH_COLLISION,
    applied_schemas,
    apply_runtime_schemas,
)


def _collider(stage, path, approx=None, kind=UsdGeom.Mesh):
    prim = kind.Define(stage, path).GetPrim()
    UsdPhysics.CollisionAPI.Apply(prim)
    if approx:
        UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(approx)
    return prim


def test_apply_runtime_schemas():
    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/a").GetPrim()
    hull = _collider(stage, "/a/Body", "convexHull")
    decomp = _collider(stage, "/a/Basket", "convexDecomposition")
    cube = _collider(stage, "/a/Box", kind=UsdGeom.Cube)
    visual = UsdGeom.Mesh.Define(stage, "/a/Label").GetPrim()  # コリジョンのないメッシュ
    pmat = UsdShade.Material.Define(stage, "/a/_materials/PhysicsMaterial").GetPrim()
    UsdPhysics.MaterialAPI.Apply(pmat)
    vmat = UsdShade.Material.Define(stage, "/a/_materials/PET").GetPrim()

    out = apply_runtime_schemas(root)
    assert out == {"mujoco": ["Body", "Box"], "newton": ["Body", "Basket", "Box"]}
    schemas = {p.GetName(): set(applied_schemas(p)) for p in (hull, decomp, cube, visual, pmat, vmat)}
    assert {MJC_COLLISION, NEWTON_COLLISION, NEWTON_MESH_COLLISION} <= schemas["Body"]
    # MuJoCo はメッシュを凸包でしか扱えないので、凸包でないメッシュには付けない（MUJOCO.COL.002）
    assert MJC_COLLISION not in schemas["Basket"] and NEWTON_MESH_COLLISION in schemas["Basket"]
    # NewtonMeshCollisionAPI はメッシュだけ
    assert {MJC_COLLISION, NEWTON_COLLISION} <= schemas["Box"] and NEWTON_MESH_COLLISION not in schemas["Box"]
    assert not schemas["Label"] - {"MaterialBindingAPI"}
    assert NEWTON_MATERIAL in schemas["PhysicsMaterial"] and NEWTON_MATERIAL not in schemas["PET"]

    apply_runtime_schemas(root)  # 2 回呼んでも重ならない
    assert applied_schemas(hull).count(MJC_COLLISION) == 1
