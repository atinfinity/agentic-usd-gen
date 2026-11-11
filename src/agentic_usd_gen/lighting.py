"""什器に内蔵する照明（ケース内の LED・ランプ。spec.Light）を USD に書く。

照明（UsdLux の RectLight）と照明の面（finish が light の部品）の発光は、ルートの Lighting バリアントの On に入れる。
既定は On。合成データの生成では Off に切り替えて、ケースの照明を消せる。
発光の値はバリアントの中だけに書く（バリアントの外に書くと、そちらが強くて切り替わらない）。

光量の目安は、ワールドの天井照明（事務所の例：1.2 × 0.3 m の面光源・8000 nit・
2.4 m 間隔）の下で棚の前面が受ける照度。illuminance で面光源からの照度を数えて合わせる（遮るものは数えない）。
"""

from __future__ import annotations

import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade

from .openpbr import set_emission as set_openpbr_emission

VARIANT_SET = "Lighting"
VARIANTS = ("On", "Off")
DEFAULT_VARIANT = "On"
LIGHTS_SCOPE = "Lights"
# 照明の面（LED の帯・乳白のカバー）の輝度 [cd/m²]。天井照明の下の白い紙（およそ 200 cd/m²）よりずっと明るく、
# 点いているのがひと目でわかるくらい
LIGHT_SURFACE_LUMINANCE = 3000.0


def rotation_matrix(deg: list[float]) -> np.ndarray:
    """XYZ の順に回すオイラー角 [度] の回転行列（spec の Part・Light の rotation と同じ）。"""
    rx, ry, rz = np.radians(deg)
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def illuminance(lights: list[dict], point, normal, samples: int = 24) -> float:
    """面光源（RectLight。intensity は輝度 [nit]、光は回す前の -Z 向き）から point の面（向き normal）が受ける照度 [lx]。
    面光源を小さな升に分け、E = Σ L·cosθ₁·cosθ₂·dA / r² で足す。遮るものは数えない。"""
    p, n = np.asarray(point, float), np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    total = 0.0
    for x in lights:
        R = rotation_matrix(x.get("rotation") or [0, 0, 0])
        w, h = x["size"]
        u = (np.arange(samples) + 0.5) / samples - 0.5
        gx, gy = np.meshgrid(u * w, u * h)
        pts = np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], 1) @ R.T + x["center"]
        out = R @ [0, 0, -1]  # 光の出る向き
        d = p - pts
        r2 = (d * d).sum(1)
        r = np.sqrt(r2)
        cos_e = np.clip(d @ out / r, 0, None)
        cos_r = np.clip(-(d @ n) / r, 0, None)
        total += float(x["intensity"] * (cos_e * cos_r / r2).sum() * w * h / samples ** 2)
    return total


def _set_light_surface(mat: UsdShade.Material, color: Gf.Vec3f) -> None:
    """照明の面のマテリアルを color の色で光らせる（UsdPreviewSurface・OmniPBR・OpenPBR）。"""
    stage = mat.GetPrim().GetStage()
    ps = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("Principled_BSDF"))
    if ps:
        ps.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(color)
    mdl = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("MDL"))
    if mdl:
        mdl.CreateInput("enable_emission", Sdf.ValueTypeNames.Bool).Set(True)
        mdl.CreateInput("emissive_color", Sdf.ValueTypeNames.Color3f).Set(color)
        mdl.CreateInput("emissive_intensity", Sdf.ValueTypeNames.Float).Set(LIGHT_SURFACE_LUMINANCE)
    set_openpbr_emission(mat, color, LIGHT_SURFACE_LUMINANCE)


def _define_light(stage: Usd.Stage, path: Sdf.Path, light: dict) -> UsdLux.RectLight:
    rl = UsdLux.RectLight.Define(stage, path)
    w, h = light["size"]
    rl.CreateWidthAttr(float(w))
    rl.CreateHeightAttr(float(h))
    rl.CreateIntensityAttr(float(light["intensity"]))
    rl.CreateNormalizeAttr(False)
    rl.CreateEnableColorTemperatureAttr(True)
    rl.CreateColorTemperatureAttr(float(light["kelvin"]))
    xf = UsdGeom.Xformable(rl)
    xf.AddTranslateOp().Set(Gf.Vec3d(*light["center"]))
    rot = light.get("rotation") or [0, 0, 0]
    if any(rot):
        xf.AddRotateXYZOp().Set(Gf.Vec3f(*rot))
    return rl


def write_lighting(stage: Usd.Stage, root: Usd.Prim, lights: list[dict], materials: dict[str, dict]) -> list[str]:
    """照明と照明の面の発光を Lighting バリアント（On・Off、既定 On）に書く。書いた照明の名前を返す。
    materials は Blender のマテリアル名 → パラメータ（light が True のものを光らせる）。"""
    surfaces = {name: p for name, p in materials.items() if p.get("light")}
    if not lights and not surfaces:
        return []
    vset = root.GetVariantSets().AddVariantSet(VARIANT_SET)
    for v in VARIANTS:
        vset.AddVariant(v)
    vset.SetVariantSelection("On")
    with vset.GetVariantEditContext():
        scope = UsdGeom.Xform.Define(stage, root.GetPath().AppendChild(LIGHTS_SCOPE))
        for light in lights:
            _define_light(stage, scope.GetPath().AppendChild(light["name"]), light)
        mats = root.GetPath().AppendChild("_materials")
        from .usd_post import srgb_to_linear  # usd_post がこのモジュールを読むので、ここで読む

        for name, p in surfaces.items():
            mat = UsdShade.Material.Get(stage, mats.AppendChild(name))
            if mat:
                _set_light_surface(mat, srgb_to_linear(p.get("color") or "#FFFFFF"))
    vset.SetVariantSelection(DEFAULT_VARIANT)
    return [x["name"] for x in lights]
