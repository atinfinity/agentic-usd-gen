"""光る画面（部品の finish が screen）の表示を Screen バリアントで切り替える（サイネージ）。

On（既定）は画面の画像を光らせたまま、Off は消えた液晶（黒くつやのある面、発光なし）にする。
店以外のワールド（工場・倉庫など）に置くとき、サイネージに店の広告が映らないようにするため。

画面のメッシュの割り当て（material:binding）はバリアントの中だけに書き、On は元のマテリアル、Off は
`<名前>_Off` のマテリアルを割り当てる（バリアントの外に割り当てを残すと、そちらが強くて切り替わらない）。
"""

from __future__ import annotations

from pxr import Sdf, Usd, UsdGeom, UsdShade

from .nonvisual import ATTRIBUTES_ATTR, BASE_ATTR, COATING_ATTR

VARIANT_SET = "Screen"
VARIANTS = ("On", "Off")
DEFAULT_VARIANT = "On"
OFF_SUFFIX = "_Off"
# 消えた液晶：ほぼ黒で、表面のガラスがつやつやしている
OFF_COLOR = "#060708"
OFF_ROUGHNESS = 0.12
BINDING = "material:binding"


def screen_materials(materials: dict[str, dict]) -> list[str]:
    """画像を光らせる画面のマテリアルの名前（finish が screen で画像があるもの）。"""
    return sorted(n for n, p in materials.items() if p.get("emissive") and p.get("texture_rel"))


def _define_off_material(stage: Usd.Stage, on: UsdShade.Material) -> UsdShade.Material:
    """on と並べて、消えた画面のマテリアル（UsdPreviewSurface・OmniPBR・OpenPBR）を作る。"""
    from .usd_post import _setup_material, set_material_labels  # usd_post がこのモジュールを読むので、ここで読む

    path = on.GetPath().GetParentPath().AppendChild(on.GetPath().name + OFF_SUFFIX)
    mat = UsdShade.Material.Define(stage, path)
    ps = UsdShade.Shader.Define(stage, path.AppendChild("Principled_BSDF"))
    ps.CreateIdAttr("UsdPreviewSurface")
    mat.CreateSurfaceOutput().ConnectToSource(ps.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    _setup_material(mat, {"role": "solid", "color": OFF_COLOR, "roughness": OFF_ROUGHNESS, "metallic": 0.0})
    src = on.GetPrim()
    labels = src.GetAttribute("semantics:labels:material")
    set_material_labels(mat.GetPrim(), list(labels.Get()) if labels and labels.Get() else ["glass"])
    # 光学以外の属性（nonvisual）は元の画面と同じ
    for name in (BASE_ATTR, COATING_ATTR, ATTRIBUTES_ATTR):
        a = src.GetAttribute(name)
        if a and a.HasAuthoredValue():
            mat.GetPrim().CreateAttribute(name, a.GetTypeName()).Set(a.Get())
    return mat


def bound_meshes(root: Usd.Prim, mats: set[Sdf.Path]) -> list[tuple[Usd.Prim, Sdf.Path]]:
    """mats のどれかを直接割り当てたメッシュ（面の組 GeomSubset も含む）と、そのマテリアル。"""
    out = []
    for prim in Usd.PrimRange(root):
        if not (UsdGeom.Gprim(prim) or prim.IsA(UsdGeom.Subset)):
            continue
        rel = prim.GetRelationship(BINDING)
        targets = rel.GetTargets() if rel else []
        if len(targets) == 1 and targets[0] in mats:
            out.append((prim, targets[0]))
    return out


def write_binding_variant(root: Usd.Prim, name: str, variants: tuple[str, ...], default: str,
                          bound: list[tuple[Usd.Prim, Sdf.Path]], swap: dict[str, dict[Sdf.Path, Sdf.Path]]) -> None:
    """bound のメッシュの割り当てをバリアント name に移す。swap[バリアント][元のマテリアル] が差し替え先（無ければ元のまま）。"""
    for prim, _ in bound:
        prim.RemoveProperty(BINDING)
    vset = root.GetVariantSets().AddVariantSet(name)
    for v in variants:
        vset.AddVariant(v)
    for v in variants:
        vset.SetVariantSelection(v)
        with vset.GetVariantEditContext():
            for prim, target in bound:
                prim.CreateRelationship(BINDING).SetTargets([swap.get(v, {}).get(target, target)])
    vset.SetVariantSelection(default)


def write_screen_variant(stage: Usd.Stage, root: Usd.Prim, materials: dict[str, dict]) -> list[str]:
    """画面のメッシュの割り当てを Screen バリアント（On・Off、既定 On）に移す。切り替えたマテリアルの名前を返す。"""
    names = screen_materials(materials)
    mats_path = root.GetPath().AppendChild("_materials")
    on_mats = {mats_path.AppendChild(n): UsdShade.Material.Get(stage, mats_path.AppendChild(n)) for n in names}
    on_mats = {p: m for p, m in on_mats.items() if m}
    bound = bound_meshes(root, set(on_mats))
    if not bound:
        return []
    used = {t for _, t in bound}
    off_mats = {p: _define_off_material(stage, m) for p, m in on_mats.items() if p in used}
    write_binding_variant(root, VARIANT_SET, VARIANTS, DEFAULT_VARIANT, bound,
                          {"Off": {p: m.GetPath() for p, m in off_mats.items()}})
    return sorted(p.name for p in off_mats)
