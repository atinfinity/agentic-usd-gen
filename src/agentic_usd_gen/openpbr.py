"""OpenPBR のマテリアル（SimReady の FET_006_OPENPBR。VM.PBR.001〜003・VM.TEX.004）。

見た目のマテリアルに MaterialX の OpenPBR Surface（ND_open_pbr_surface_surfaceshader）を足し、
outputs:mtlx:surface に繋ぐ。UsdPreviewSurface と MDL はそのまま残す（使う側が対応する出力を選ぶ）。
テクスチャは MaterialX の image ノードで読む。色のテクスチャは srgb_texture、データ（粗さ・金属度・法線）は none。
UV は image ノードの既定（UV0。USD では primvars:st）を使う。
"""

from __future__ import annotations

from pxr import Gf, Sdf, UsdShade

SURFACE_ID = "ND_open_pbr_surface_surfaceshader"
NAME = "OpenPBR"
SRGB = "srgb_texture"
DATA = "none"
IOR_RANGE = (1.0, 3.0)  # VM.PBR.002

_F, _C, _B, _A, _V3 = (Sdf.ValueTypeNames.Float, Sdf.ValueTypeNames.Color3f, Sdf.ValueTypeNames.Bool,
                       Sdf.ValueTypeNames.Asset, Sdf.ValueTypeNames.Float3)
# テクスチャのマップ名（surface.py）→ OpenPBR の入力
_MAP_INPUTS = {"roughness": "specular_roughness", "metallic": "base_metalness", "normal": "geometry_normal"}


def _clamp01(x: float) -> float:
    return min(max(float(x), 0.0), 1.0)


def _value(name: str, value: object) -> tuple[Sdf.ValueTypeName, object]:
    if isinstance(value, bool):
        return _B, value
    if isinstance(value, Gf.Vec3f):
        return _C, Gf.Vec3f(*(_clamp01(c) for c in value))
    v = float(value)
    if name.endswith("_ior"):
        v = min(max(v, IOR_RANGE[0]), IOR_RANGE[1])
    elif name not in ("transmission_depth", "emission_luminance", "subsurface_radius"):
        v = _clamp01(v)
    return _F, v


def surface_shader(mat: UsdShade.Material) -> UsdShade.Shader:
    return UsdShade.Shader.Get(mat.GetPrim().GetStage(), mat.GetPath().AppendChild(NAME))


def _image(mat: UsdShade.Material, name: str, rel: str, kind: str, colorspace: str) -> UsdShade.Output:
    """MaterialX の image ノード（ND_image_<kind>）を作り、出力を返す。"""
    tex = UsdShade.Shader.Define(mat.GetPrim().GetStage(), mat.GetPath().AppendChild(f"{NAME}_{name}"))
    tex.CreateIdAttr(f"ND_image_{kind}")
    f = tex.CreateInput("file", _A)
    f.Set(Sdf.AssetPath(rel))
    f.GetAttr().SetColorSpace(colorspace)  # VM.TEX.004: ファイルを持つ属性に書く
    out_type = {"color3": _C, "float": _F, "vector3": _V3}[kind]
    return tex.CreateOutput("out", out_type)


def add_openpbr(mat: UsdShade.Material, inputs: dict[str, object], base_texture: str | None = None) -> UsdShade.Shader:
    """OpenPBR Surface を作って outputs:mtlx:surface に繋ぐ。値は範囲（VM.PBR.002）に収める。

    base_texture があれば base_color をその画像（sRGB）にする。
    """
    sh = UsdShade.Shader.Define(mat.GetPrim().GetStage(), mat.GetPath().AppendChild(NAME))
    sh.CreateIdAttr(SURFACE_ID)
    for name, value in inputs.items():
        vtype, v = _value(name, value)
        sh.CreateInput(name, vtype).Set(v)
    if base_texture:
        sh.CreateInput("base_color", _C).ConnectToSource(_image(mat, "base_color", base_texture, "color3", SRGB))
    mat.CreateSurfaceOutput("mtlx").ConnectToSource(sh.CreateOutput("out", Sdf.ValueTypeNames.Token))
    return sh


def connect_emission(mat: UsdShade.Material, texture: str, luminance: float, base_weight: float) -> None:
    """画像（sRGB）を発光の色にする。luminance は白（1, 1, 1）の明るさ [cd/m²]。拡散反射は base_weight 倍に弱める。"""
    sh = surface_shader(mat)
    if not sh:
        return
    sh.CreateInput("emission_luminance", _F).Set(float(luminance))
    sh.CreateInput("emission_color", _C).ConnectToSource(_image(mat, "emission_color", texture, "color3", SRGB))
    sh.CreateInput("base_weight", _F).Set(_clamp01(base_weight))


def connect_maps(mat: UsdShade.Material, maps: dict[str, str]) -> None:
    """粗さ・金属度・法線のテクスチャ（surface.py）を OpenPBR に繋ぐ。データなので色空間は none。"""
    sh = surface_shader(mat)
    if not sh:
        return
    for name, rel in maps.items():
        target = _MAP_INPUTS[name]
        if name == "normal":
            # 0〜1 に詰めた接空間の法線を、normalmap ノードでワールドの法線に直す
            nm = UsdShade.Shader.Define(mat.GetPrim().GetStage(), mat.GetPath().AppendChild(f"{NAME}_normalmap"))
            nm.CreateIdAttr("ND_normalmap_float")
            nm.CreateInput("in", _V3).ConnectToSource(_image(mat, name, rel, "vector3", DATA))
            sh.CreateInput(target, _V3).ConnectToSource(nm.CreateOutput("out", _V3))
        else:
            sh.CreateInput(target, _F).ConnectToSource(_image(mat, name, rel, "float", DATA))


def set_emission(mat: UsdShade.Material, color: Gf.Vec3f, luminance: float) -> None:
    """一様な色（線形）で光らせる。luminance は白（1, 1, 1）の明るさ [cd/m²]。照明の面（lighting.py）に使う。"""
    sh = surface_shader(mat)
    if not sh:
        return
    sh.CreateInput("emission_luminance", _F).Set(float(luminance))
    sh.CreateInput("emission_color", _C).Set(Gf.Vec3f(*(_clamp01(c) for c in color)))
