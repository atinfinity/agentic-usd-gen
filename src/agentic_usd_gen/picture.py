"""店向けの絵柄（広告・メニュー・求人など）を Picture バリアントで無地に切り替える（ポスター・看板）。

Default（既定）は描いた絵柄のまま、Blank は部品の blank（spec.Part）の無地の面にする。店以外のワールド
（工場・倉庫など）にポスターや看板を置くとき、からあげの広告や店のメニューが出ないようにするため。
画面（screen.py）と違って光らないので、Off（消えた画面）ではなく無地の紙・板にする。

Blank のマテリアル `<名前>_Blank` は元のマテリアルを写し、色のテクスチャと粗さ・法線のテクスチャだけを
無地のもの（`<名前>_Blank.png` と、そこから作ったもの）に差し替える（紙の凹凸はそのまま、文字の跡は残さない）。

光る看板（冷蔵ケースのヘッダー等）は画面でもあるので、Screen バリアントも同じ面の割り当てを持つ。そのときは
Picture を Screen より前に並べ（前のバリアントセットが強い）、Default では何も書かず Screen（On / Off）に任せ、
Blank だけ無地のマテリアルを割り当てる。Blank は Screen より強いので、Screen が Off でも光る無地の面になる。
"""

from __future__ import annotations

from pxr import Sdf, Usd, UsdShade

from .screen import BINDING, bound_meshes, write_binding_variant
from .screen import VARIANT_SET as SCREEN_SET

VARIANT_SET = "Picture"
VARIANTS = ("Default", "Blank")
DEFAULT_VARIANT = "Default"
BLANK_SUFFIX = "_Blank"


def picture_materials(materials: dict[str, dict]) -> list[str]:
    """絵柄を無地に切り替えられるマテリアルの名前（部品に blank があり、画像を貼ったもの）。"""
    return sorted(n for n, p in materials.items() if p.get("blank_texture_rel") and p.get("texture_rel"))


def _rel(path: str) -> str:
    return path.removeprefix("./")


def _define_blank_material(stage: Usd.Stage, src: Sdf.Path, params: dict) -> Sdf.Path:
    """src を写して、テクスチャを無地のものに差し替えたマテリアルを作る。"""
    from .usd_post import write_surface_maps  # usd_post がこのモジュールを読むので、ここで読む

    blank = {**params, "texture": params["blank_texture"], "texture_rel": params["blank_texture_rel"]}
    blank.pop("maps", None)
    write_surface_maps(blank)
    swap = {_rel(params["texture_rel"]): blank["texture_rel"]}
    for kind, rel in (params.get("maps") or {}).items():
        if kind in (blank.get("maps") or {}):
            swap[_rel(rel)] = "./" + _rel(blank["maps"][kind])

    dst = src.GetParentPath().AppendChild(src.name + BLANK_SUFFIX)
    layer = stage.GetEditTarget().GetLayer()
    if not Sdf.CopySpec(layer, src, layer, dst):
        raise RuntimeError(f"マテリアル {src} を写せませんでした")
    for prim in Usd.PrimRange(stage.GetPrimAtPath(dst)):
        for attr in prim.GetAttributes():
            if attr.GetTypeName() != Sdf.ValueTypeNames.Asset or not attr.HasAuthoredValue():
                continue
            v = attr.Get()
            new = swap.get(_rel(v.path)) if v is not None else None
            if new:
                attr.Set(Sdf.AssetPath(new))
    return dst


def write_picture_variant(stage: Usd.Stage, root: Usd.Prim, materials: dict[str, dict]) -> list[str]:
    """絵柄の面の割り当てを Picture バリアント（Default・Blank、既定 Default）に移す。切り替えたマテリアルの名前を返す。"""
    mats_path = root.GetPath().AppendChild("_materials")
    names = [n for n in picture_materials(materials) if UsdShade.Material.Get(stage, mats_path.AppendChild(n))]
    bound = bound_meshes(root, {mats_path.AppendChild(n) for n in names})
    if not bound:
        return []
    used = sorted({t for _, t in bound})
    blank = {p: _define_blank_material(stage, p, materials[p.name]) for p in used}
    lit = [(prim, t) for prim, t in bound if _in_screen_variant(root, prim)]
    if not lit:
        write_binding_variant(root, VARIANT_SET, VARIANTS, DEFAULT_VARIANT, bound, {"Blank": blank})
        return [p.name for p in used]
    plain = [b for b in bound if b not in lit]
    for prim, _ in plain:
        prim.RemoveProperty(BINDING)
    vset = root.GetVariantSets().AddVariantSet(VARIANT_SET)
    for v in VARIANTS:
        vset.AddVariant(v)
    for v in VARIANTS:
        vset.SetVariantSelection(v)
        with vset.GetVariantEditContext():
            for prim, target in plain:
                prim.CreateRelationship(BINDING).SetTargets([blank[target] if v == "Blank" else target])
            if v == "Blank":
                for prim, target in lit:
                    prim.CreateRelationship(BINDING).SetTargets([blank[target]])
    vset.SetVariantSelection(DEFAULT_VARIANT)
    # 前のバリアントセットが強いので、Picture を Screen より前に置く
    spec = root.GetStage().GetEditTarget().GetPrimSpecForScenePath(root.GetPath())
    names = list(spec.variantSetNameList.prependedItems)
    names.remove(VARIANT_SET)
    names.insert(names.index(SCREEN_SET), VARIANT_SET)
    spec.variantSetNameList.prependedItems = names
    return [p.name for p in used]


def _in_screen_variant(root: Usd.Prim, prim: Usd.Prim) -> bool:
    """prim の割り当てが Screen バリアントの中にあるか（光る看板）。"""
    if SCREEN_SET not in root.GetVariantSets().GetNames():
        return False
    rel = prim.GetRelationship(BINDING)
    return bool(rel) and any("{" + SCREEN_SET + "=" in str(spec.path) for spec in rel.GetPropertyStack())
