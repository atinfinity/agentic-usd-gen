"""光学以外のマテリアルの属性（SimReady の FET_007。NVM.001〜006）。

LiDAR・レーダーなどのセンサーのシミュレーション用に、描画するメッシュに割り当てた見た目のマテリアルへ
素材の種類（base）・表面の塗装（coating）・追加の性質（attributes）を書く。
マテリアルのロールと素材の意味ラベル（semantics.py）から決める。
"""

from __future__ import annotations

from pxr import Sdf, Usd, UsdGeom, UsdShade, Vt

BASE_ATTR = "omni:simready:nonvisual:base"
COATING_ATTR = "omni:simready:nonvisual:coating"
ATTRIBUTES_ATTR = "omni:simready:nonvisual:attributes"

# SimReady が認める base の値（NVM.002）。部品の material にこれらの語があればそのまま使う
BASES = {
    "aluminum", "steel", "oxidized_steel", "iron", "oxidized_iron", "silver", "brass", "bronze",
    "oxidized_Bronze_Patina", "tin",
    "plastic", "fiberglass", "carbon_fiber", "vinyl", "plexiglass", "pvc", "nylon", "polyester",
    "clear_glass", "frosted_glass", "one_way_mirror", "mirror", "ceramic_glass",
    "asphalt", "concrete", "leaf_grass", "dead_leaf_grass", "rubber", "wood", "bark", "cardboard", "paper",
    "fabric", "skin", "fur_hair", "leather", "marble", "brick", "stone", "gravel", "dirt", "mud", "water",
    "salt_water", "snow", "ice", "calibration_lambertian",
}
# 素材の意味ラベル → base。上から順に当てる
_LABEL_BASES = [
    ("aluminum", "aluminum"),
    ("steel", "steel"),
    ("metal", "steel"),  # 種類のわからない金属（家電の金具など）はステンレスとみなす
    ("ceramic", "ceramic_glass"),  # 衛生陶器・タイル（釉薬のかかった陶磁器）
    ("glass", "clear_glass"),
    ("paper", "paper"),
    ("wood", "wood"),
    ("food", "skin"),  # 食品は水分の多い生体組織として扱う（一覧にいちばん近いもの）
    ("liquid", "water"),
]
TRANSPARENT_ROLES = ("pet", "glass", "translucent", "liquid")


def nonvisual_material(params: dict | None) -> tuple[str, str, list[str]]:
    """見た目のマテリアルの params から (base, coating, attributes) を決める。"""
    params = params or {}
    role = params.get("role")
    labels = params.get("labels") or []
    if role == "liquid":
        base = "water"
    elif role == "glass":
        base = "clear_glass"
    elif role == "translucent" and "glass" in labels:
        base = "frosted_glass"
    elif role == "pet":
        base = "plexiglass"  # 透明な樹脂でいちばん近いもの（NVM.005: 透けるものは透明な素材にする）
    elif role == "translucent":
        base = "plastic"
    else:
        base = next((b for key, b in _LABEL_BASES if key in labels), None)
        base = base or next((x for x in labels if x in BASES), "plastic")
        if params.get("metallic", 0.0) >= 0.5 and base not in ("aluminum", "steel"):
            base = "steel"  # 金属に見えるなら金属にする（NVM.005）
    printed = bool(params.get("texture")) or role == "label"
    coating = "paint" if printed and role not in TRANSPARENT_ROLES else "none"
    attributes = ["visually_transparent"] if role in TRANSPARENT_ROLES else []
    return base, coating, attributes


def bound_materials(root: Usd.Prim) -> set[Sdf.Path]:
    """描画するメッシュに割り当てたマテリアル。物理マテリアルなどは含まない（NVM.004）。

    面の組（GeomSubset）だけに割り当てたマテリアル（キャップの天面など）は含めない。SimReady の検査は
    GeomSubset への割り当てを数えないので、書くと「割り当てのないマテリアルに書いた」（NVM.004）になる。
    """
    out: set[Sdf.Path] = set()
    for prim in Usd.PrimRange(root):
        if not UsdGeom.Gprim(prim):
            continue
        if UsdGeom.Imageable(prim).ComputePurpose() not in (UsdGeom.Tokens.default_, UsdGeom.Tokens.render):
            continue
        mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial(UsdShade.Tokens.full)
        if mat:
            out.add(mat.GetPath())
    return out


def write_nonvisual_materials(stage: Usd.Stage, root: Usd.Prim, materials: dict[str, dict]) -> dict[str, str]:
    """割り当てたマテリアルに光学以外の属性を書き、マテリアル名 → base を返す。"""
    out: dict[str, str] = {}
    for path in sorted(bound_materials(root)):
        prim = stage.GetPrimAtPath(path)
        base, coating, attributes = nonvisual_material(materials.get(path.name))
        prim.CreateAttribute(BASE_ATTR, Sdf.ValueTypeNames.Token).Set(base)
        prim.CreateAttribute(COATING_ATTR, Sdf.ValueTypeNames.Token).Set(coating)
        prim.CreateAttribute(ATTRIBUTES_ATTR, Sdf.ValueTypeNames.TokenArray).Set(Vt.TokenArray(attributes))
        out[path.name] = base
    return out
