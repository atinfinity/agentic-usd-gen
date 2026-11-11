"""書き出す USD を Isaac Sim のレイヤー構成に分ける（SimReady の FET_100_ISAAC。ISA.001）。

    <slug>.usd                    入口。ステージと SimReady のメタデータ、kind = component、base への reference
    payloads/<slug>_base.usd      physics と meshes をサブレイヤーで重ねる（physics が強い）
    payloads/<slug>_meshes.usd    形状・マテリアル（物理以外のすべて）
    payloads/<slug>_physics.usd   物理のスキーマ・属性（over）と、物理マテリアル・関節の Prim

1 つのレイヤーにまとまった USD を、Prim・属性・スキーマ単位で meshes と physics に振り分ける。
重ねた結果は元の USD と同じになる。テクスチャなどの相対パスは payloads/ から見たパスに直す。
"""

from __future__ import annotations

from pathlib import Path

from pxr import Kind, Sdf, UsdUtils

PAYLOADS = "payloads"
ROLES = ("base", "meshes", "physics")
# 物理のスキーマ（UsdPhysics・PhysX・MuJoCo・Newton）と属性の名前の先頭
PHYSICS_SCHEMAS = ("Physics", "Physx", "Mjc", "Newton")
PHYSICS_PROPS = ("physics:", "physx", "mjc:", "newton:", "material:binding:physics")
_STAGE_INFO = ("upAxis", "metersPerUnit", "kilogramsPerUnit", "timeCodesPerSecond", "startTimeCode",
               "endTimeCode")


def layer_paths(usd_path: Path) -> dict[str, Path]:
    """入口の USD に対する base・meshes・physics のレイヤーのパス。"""
    stem = usd_path.stem
    return {role: usd_path.parent / PAYLOADS / f"{stem}_{role}{usd_path.suffix}" for role in ROLES}


def _is_physics_prim(spec: Sdf.PrimSpec) -> bool:
    """Prim ごと物理のレイヤーに移すもの（関節と物理マテリアル）。"""
    if spec.typeName.startswith("Physics"):
        return True
    return spec.typeName == "Material" and "PhysicsMaterialAPI" in _schemas(spec)


def _schemas(spec: Sdf.PrimSpec) -> list[str]:
    if not spec.HasInfo("apiSchemas"):
        return []
    op = spec.GetInfo("apiSchemas")
    return list(op.explicitItems) + list(op.prependedItems) + list(op.appendedItems)


def _is_physics_schema(name: str) -> bool:
    return name.startswith(PHYSICS_SCHEMAS)


def _over(layer: Sdf.Layer, path: Sdf.Path) -> Sdf.PrimSpec:
    """path の Prim（なければ親も含めて over）を作る。"""
    return layer.GetPrimAtPath(path) or Sdf.CreatePrimInLayer(layer, path)


def _split_schemas(spec: Sdf.PrimSpec, physics: Sdf.Layer) -> None:
    op = spec.GetInfo("apiSchemas")
    moved = [s for s in _schemas(spec) if _is_physics_schema(s)]
    if not moved:
        return
    keep = Sdf.TokenListOp()
    if op.isExplicit:
        keep.explicitItems = [s for s in op.explicitItems if not _is_physics_schema(s)]
    else:
        keep.prependedItems = [s for s in op.prependedItems if not _is_physics_schema(s)]
        keep.appendedItems = [s for s in op.appendedItems if not _is_physics_schema(s)]
    spec.SetInfo("apiSchemas", keep)
    over = _over(physics, spec.path)
    over.SetInfo("apiSchemas", Sdf.TokenListOp.Create(prependedItems=moved))


def _split_prim(spec: Sdf.PrimSpec, meshes: Sdf.Layer, physics: Sdf.Layer) -> None:
    if _is_physics_prim(spec):
        parent = spec.path.GetParentPath()
        _over(physics, parent)
        Sdf.CopySpec(meshes, spec.path, physics, spec.path)
        del meshes.GetPrimAtPath(parent).nameChildren[spec.name]
        return
    if spec.HasInfo("apiSchemas"):
        _split_schemas(spec, physics)
    for prop in [p for p in spec.properties if p.name.startswith(PHYSICS_PROPS)]:
        _over(physics, spec.path)
        Sdf.CopySpec(meshes, prop.path, physics, prop.path)
        spec.RemoveProperty(prop)
    for child in list(spec.nameChildren):
        _split_prim(child, meshes, physics)


def _new_layer(path: Path, src: Sdf.Layer, default_prim: str) -> Sdf.Layer:
    path.parent.mkdir(parents=True, exist_ok=True)
    layer = Sdf.Layer.FindOrOpen(str(path))
    if layer:
        layer.Clear()  # 同じプロセスで書き直すとき、前の内容を残さない
    else:
        layer = Sdf.Layer.CreateNew(str(path))
    for key in _STAGE_INFO:
        if src.pseudoRoot.HasInfo(key):
            layer.pseudoRoot.SetInfo(key, src.pseudoRoot.GetInfo(key))
    layer.defaultPrim = default_prim
    return layer


def split_layers(usd_path: Path) -> dict[str, Path]:
    """usd_path（1 つのレイヤーの USD）を入口と base・meshes・physics に分けて上書きし、各レイヤーのパスを返す。"""
    src = Sdf.Layer.FindOrOpen(str(usd_path))
    src.Reload(force=True)
    root = src.defaultPrim
    if not root:
        raise ValueError(f"{usd_path}: defaultPrim がありません")
    paths = layer_paths(usd_path)

    meshes = _new_layer(paths["meshes"], src, root)
    meshes.TransferContent(src)
    meshes.customLayerData = {}  # SimReady のメタデータは入口に置く
    physics = _new_layer(paths["physics"], src, root)
    for spec in list(meshes.rootPrims):
        _split_prim(spec, meshes, physics)
    # payloads/ に移るので、./textures/... などの相対パスを入口から見た位置のままにする
    UsdUtils.ModifyAssetPaths(meshes, lambda p: f"../{p[2:]}" if p.startswith("./") else p)

    base = _new_layer(paths["base"], src, root)
    base.subLayerPaths = [f"./{paths['physics'].name}", f"./{paths['meshes'].name}"]

    entry = Sdf.Layer.CreateAnonymous(usd_path.suffix)
    for key in _STAGE_INFO:
        if src.pseudoRoot.HasInfo(key):
            entry.pseudoRoot.SetInfo(key, src.pseudoRoot.GetInfo(key))
    entry.defaultPrim = root
    entry.customLayerData = src.customLayerData
    src_root = src.GetPrimAtPath(Sdf.Path.absoluteRootPath.AppendChild(root))
    prim = Sdf.PrimSpec(entry, root, Sdf.SpecifierDef, src_root.typeName)
    prim.SetInfo("kind", Kind.Tokens.component)
    prim.referenceList.prependedItems.append(Sdf.Reference(f"./{PAYLOADS}/{paths['base'].name}"))

    for layer in (meshes, physics, base):
        layer.Save()
    src.TransferContent(entry)
    src.Save()
    return paths
