"""MuJoCo・Newton のコリジョンのスキーマ（SimReady の FET_003_MUJOCO・FET_003_NEWTON）。

物理は UsdPhysics で書き（PhysX・Isaac Sim はそれを読む）、その上に各シミュレータのスキーマを足す。
- MuJoCo: コライダーに MjcCollisionAPI（MUJOCO.COL.001）。MuJoCo はメッシュを凸包で扱うので、
  凸包（convexHull）のメッシュと、メッシュ以外の形状だけに付ける（MUJOCO.COL.002）
- Newton: コライダーに NewtonCollisionAPI と、メッシュなら NewtonMeshCollisionAPI（NEWTON.COL.001）。
  SDF（NewtonSDFCollisionAPI）は使わない。物理マテリアルに NewtonMaterialAPI（NEWTON.MAT.001）
値はどれも書かず、各シミュレータの既定にする。スキーマは usd-core に登録されていないので、名前で付ける。
"""

from __future__ import annotations

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

MJC_COLLISION = "MjcCollisionAPI"
NEWTON_COLLISION = "NewtonCollisionAPI"
NEWTON_MESH_COLLISION = "NewtonMeshCollisionAPI"
NEWTON_MATERIAL = "NewtonMaterialAPI"
RUNTIME_SCHEMAS = (MJC_COLLISION, NEWTON_COLLISION, NEWTON_MESH_COLLISION, NEWTON_MATERIAL)


def applied_schemas(prim: Usd.Prim) -> list[str]:
    """付いているスキーマの名前。GetAppliedSchemas() は登録されていないスキーマを返さないので、こちらで見る。"""
    return list(prim.GetPrimTypeInfo().GetAppliedAPISchemas())


def _add(prim: Usd.Prim, schema: str) -> None:
    if schema not in applied_schemas(prim):
        prim.AddAppliedSchema(schema)


def apply_runtime_schemas(root: Usd.Prim) -> dict[str, list[str]]:
    """root の下のコライダーと物理マテリアルにスキーマを付け、{"mujoco": [...], "newton": [...]}（コライダー名）を返す。"""
    out: dict[str, list[str]] = {"mujoco": [], "newton": []}
    for prim in Usd.PrimRange(root):
        if prim.IsA(UsdShade.Material) and prim.HasAPI(UsdPhysics.MaterialAPI):
            _add(prim, NEWTON_MATERIAL)
            continue
        if not prim.IsA(UsdGeom.Gprim) or not prim.HasAPI(UsdPhysics.CollisionAPI):
            continue
        is_mesh = prim.IsA(UsdGeom.Mesh)
        approx = (UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()
                  if prim.HasAPI(UsdPhysics.MeshCollisionAPI) else None)
        if not is_mesh or approx == UsdPhysics.Tokens.convexHull:
            _add(prim, MJC_COLLISION)
            out["mujoco"].append(prim.GetName())
        _add(prim, NEWTON_COLLISION)
        if is_mesh:
            _add(prim, NEWTON_MESH_COLLISION)
        out["newton"].append(prim.GetName())
    return out
