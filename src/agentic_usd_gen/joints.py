"""可動部（扉など）の剛体と関節（SimReady の FET_004。RB.MB.001・JT.001〜003・RB.011・RB.012）。

組み合わせ（assembly）の部品のうち link の付いたものを、ルートの下の Xform（<ルート>/<link>）にまとめて剛体にする。
ルート（本体）の剛体の中に入れ子になるので、本体とは関節（RevoluteJoint・PrismaticJoint）で必ずつなぐ（RB.012）。
質量は総質量から体積比で分けた分を可動部に書き、本体には残りを書く（RB.011）。

什器（static）の本体はキネマティックな剛体（床に固定）のままにする。キネマティックな剛体にはアーティキュレーションを
付けられない（JT.ART.003）ので、関節は普通の（最大座標の）関節として解く。動く商品ではルートに ArticulationRootAPI を付ける。
"""

from __future__ import annotations

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

JOINT_NAME = "Joint"


def body_mass(mass: float, com: tuple[float, float, float], links: list[dict]) -> tuple[float, Gf.Vec3f]:
    """総質量・重心から可動部の分を除いた、本体の質量と重心。"""
    m = mass - sum(lk["mass"] for lk in links)
    moment = Gf.Vec3d(*com) * mass - sum((Gf.Vec3d(*lk["center_of_mass"]) * lk["mass"] for lk in links), Gf.Vec3d())
    return m, Gf.Vec3f(moment / m)


def _move(stage: Usd.Stage, src: Sdf.Path, dst: Sdf.Path) -> None:
    layer = stage.GetRootLayer()
    if not Sdf.CopySpec(layer, src, layer, dst):
        raise RuntimeError(f"{src} を {dst} に移せませんでした")
    _move_variant_opinions(layer, src, dst)
    stage.RemovePrim(src)


def _move_variant_opinions(layer: Sdf.Layer, src: Sdf.Path, dst: Sdf.Path) -> None:
    """ルートのバリアント（Picture・Screen 等）の中にある src の意見（マテリアルの割り当て）も dst へ移す。

    バリアントの中の意見は <ルート>{set=値}<部品> にあるので、部品を可動部の下へ移すとそのままでは宙に浮く。
    """
    root = layer.GetPrimAtPath(src.GetParentPath())
    if root is None:
        return
    rel_dst = dst.MakeRelativePath(src.GetParentPath())
    for set_name, vset in root.variantSets.items():
        for var_name, var in vset.variants.items():
            spec = var.primSpec
            child = spec.nameChildren.get(src.name)
            if child is None:
                continue
            base = src.GetParentPath().AppendVariantSelection(set_name, var_name)
            target = base.AppendPath(rel_dst)
            Sdf.CreatePrimInLayer(layer, target)
            if not Sdf.CopySpec(layer, child.path, layer, target):
                raise RuntimeError(f"{child.path} を {target} に移せませんでした")
            del spec.nameChildren[src.name]


def build_links(stage: Usd.Stage, root: Usd.Prim, links: list[dict], kinematic: bool) -> list[dict]:
    """可動部の剛体と関節を作り、[{link, type, axis, anchor, limits, mass, parts}]（メタデータ用）を返す。

    部品のメッシュの頂点はルートの座標系なので、可動部の Xform は変換なし（ルートと同じ座標系）にする。
    関節の位置（localPos0・localPos1）も両方の剛体で同じ値になる。
    """
    out = []
    for lk in links:
        path = root.GetPath().AppendChild(lk["name"])
        UsdGeom.Xform.Define(stage, path)
        for name in lk["parts"]:
            _move(stage, root.GetPath().AppendChild(name), path.AppendChild(name))
        prim = stage.GetPrimAtPath(path)
        UsdPhysics.RigidBodyAPI.Apply(prim)
        mass = UsdPhysics.MassAPI.Apply(prim)
        mass.CreateMassAttr(lk["mass"])
        mass.CreateCenterOfMassAttr(Gf.Vec3f(*lk["center_of_mass"]))

        j = lk["joint"]
        kind = UsdPhysics.RevoluteJoint if j["type"] == "revolute" else UsdPhysics.PrismaticJoint
        joint = kind.Define(stage, path.AppendChild(JOINT_NAME))
        joint.CreateBody0Rel().SetTargets([root.GetPath()])
        joint.CreateBody1Rel().SetTargets([path])
        joint.CreateAxisAttr(j["axis"])
        anchor = Gf.Vec3f(*j["anchor"])
        joint.CreateLocalPos0Attr(anchor)
        joint.CreateLocalPos1Attr(anchor)
        if j["limits"] is not None:  # None は限界なし（スキーマの既定 -inf〜inf のまま。回り続ける）
            joint.CreateLowerLimitAttr(j["limits"][0])
            joint.CreateUpperLimitAttr(j["limits"][1])
        out.append({"link": lk["name"], **j, "anchor": [round(a, 4) for a in j["anchor"]],
                    "mass": round(lk["mass"], 3), "parts": list(lk["parts"])})
    if links and not kinematic:
        UsdPhysics.ArticulationRootAPI.Apply(root)
    return out
