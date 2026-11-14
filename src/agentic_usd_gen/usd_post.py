"""Blender が書き出した USD に、Isaac Sim 向けの設定を追記する。

- ステージ規約（メートル、Z 軸が上、defaultPrim、kind=component）
- 物理（RigidBody、Mass、凸包コリジョン、摩擦）。什器（static）はキネマティックな剛体（動かない）にする。
  UsdPhysics のみ使い PhysxSchema は使わない。MuJoCo・Newton のコリジョンのスキーマも付ける（physics_runtimes.py）。
  可動部（扉など）は別の剛体にして関節で本体につなぐ（joints.py）
- マテリアル: Blender 由来の UsdPreviewSurface を調整し、Isaac Sim の RTX 用に MDL 出力と、
  MaterialX の OpenPBR 出力（SimReady の FET_006_OPENPBR。openpbr.py）を追加。
  色テクスチャがあれば粗さ・金属度・法線のテクスチャを作って両方に繋ぐ（surface.py）
- SimReady の要件: すべての Material に素材の意味ラベル（SL.MAT.001）、相対パスは ./ で始める（AA.001）、
  描画するメッシュに表示色（displayColor。DISP.001〜003）、見た目のマテリアルに光学以外の属性（NVM.001〜006。nonvisual.py）
"""

from __future__ import annotations

import math
from pathlib import Path, PurePosixPath

from pxr import (
    Gf,
    Kind,
    Sdf,
    Usd,
    UsdGeom,
    UsdPhysics,
    UsdSemantics,
    UsdShade,
    UsdUtils,
    Vt,
)

from .finish import apply_finishes
from .grasp import PREFIX as GRASP_PREFIX
from .grasp import write_grasp_lines
from .nonvisual import write_nonvisual_materials
from .openpbr import add_openpbr
from .openpbr import connect_emission as connect_openpbr_emission
from .openpbr import connect_maps as connect_openpbr_maps
from .physics_material import contact_for, physics_key
from .joints import body_mass, build_links
from .lighting import write_lighting
from .picture import write_picture_variant
from .screen import write_screen_variant
from .physics_runtimes import apply_runtime_schemas
from .shapes.revolve import BuildResult
from .spec import DEFAULT_COLLISION
from .surface import surface_kind, write_maps


def srgb_to_linear(hex_color: str) -> Gf.Vec3f:
    def conv(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    return Gf.Vec3f(*(conv(int(hex_color[i : i + 2], 16)) for i in (1, 3, 5)))


# 光る画面（部品の finish が screen）。白の明るさ [cd/m²] は店のサイネージくらいで、
# 天井照明の下の白い紙（Isaac Sim の照明のプリセットで 200 cd/m² 前後）より少し明るい
SCREEN_LUMINANCE = 300.0
SCREEN_DIFFUSE = 0.3  # 液晶は消えていると黒いので、拡散反射（照明を受けて見える画像）は弱める


def _preview_shader(mat: UsdShade.Material) -> UsdShade.Shader | None:
    for child in mat.GetPrim().GetChildren():
        sh = UsdShade.Shader(child)
        if sh and sh.GetIdAttr().Get() == "UsdPreviewSurface":
            return sh
    return None


def _turbid_sigma_a(col: Gf.Vec3f, sigma_s: float, depth: float) -> list[float]:
    """濁った液体の吸収係数 σa [1/m]（チャンネルごと）。

    濁った液体は、光が表面の近くで散乱して戻ってくるので、内径ぶんの吸収ではほとんど色が付かない（白っぽくなる）。
    そこで、散乱して戻る光の色がちょうど液体の色 col（線形）になる散乱アルベド α を Christensen–Burley の式で求め、
    吸収係数を σa = σs (1 - α) / α にする。澄んだ液体としての吸収（内径ぶんで col）より弱くはしない。
    """
    sigma_a = []
    for c in col:
        r = min(max(c, 1e-3), 0.999)
        albedo = 1 - (4.09712 + 4.20863 * r - math.sqrt(9.59217 + 41.6808 * r + 17.7126 * r * r)) ** 2
        sigma_a.append(max(-math.log(max(c, 1e-3)) / depth, sigma_s * (1 - albedo) / albedo))
    return sigma_a


# 濁った液体（Isaac Sim 用の MDL）：散乱されずに素通しになる割合 exp(-k τ) の k と、素通しでない分のうち拡散透過の割合。
# PET 越しの見た目を、胴を外して体積散乱で描いた液体とスポーツドリンク・オレンジジュース・
# ミルクティーで見比べて決めた
TURBID_CLARITY_K = 0.15
TURBID_DIFFUSE_TRANSMISSION = 0.3


def _turbid_absorption(col: Gf.Vec3f, sigma_s: float, depth: float) -> tuple[Gf.Vec3f, float]:
    """濁った液体の吸収（OpenPBR の透過の色と深さ）。戻り値は (exp(-σa 深さ), 深さ [m])。

    深さは、透過の色が小さくなりすぎない（0.002 以上）ように短くする（σa は変わらない）。
    """
    sigma_a = _turbid_sigma_a(col, sigma_s, depth)
    if max(sigma_a) > 0:
        depth = min(depth, -math.log(0.002) / max(sigma_a))
    return Gf.Vec3f(*(math.exp(-a * depth) for a in sigma_a)), depth


def _omni_albedo(x: float) -> float:
    """OmniSurface（OmniShared.mdl の compute_albedo）の関数。x = 透過の色 × 散乱の色。0 で 1、1 で 0.03。"""
    return 4.09712 + 4.20863 * x - math.sqrt(9.59217 + 41.6808 * x + 17.7126 * x * x)


def omnisurface_volume(transmission: Gf.Vec3f, scattering: Gf.Vec3f, depth: float) -> tuple[list[float], list[float]]:
    """OmniSurface の透過の入力（色・散乱の色・深さ [m]）が表す (散乱係数 σs, 吸収係数 σa) [1/m]。

    Isaac Sim 6.1 の OmniShared.mdl（compute_transmission_volume_coefficients）と同じ計算：
    σt = -ln(色 / (1 + max(散乱の色))) / 深さ、σa = σt f(色 × 散乱の色)^4、σs = σt - σa。
    """
    m = max(scattering)
    sigma_s, sigma_a = [], []
    for t, s in zip(transmission, scattering):
        st = -math.log(max(t, 1e-5) / (1 + m)) / depth
        a = st * _omni_albedo(t * s) ** 4
        sigma_a.append(a)
        sigma_s.append(st - a)
    return sigma_s, sigma_a


def _add_mdl(mat: UsdShade.Material, module: str, inputs: dict[str, tuple[Sdf.ValueTypeName, object]]) -> None:
    sh = UsdShade.Shader.Define(mat.GetPrim().GetStage(), mat.GetPath().AppendChild("MDL"))
    sh.CreateImplementationSourceAttr(UsdShade.Tokens.sourceAsset)
    sh.SetSourceAsset(Sdf.AssetPath(f"{module}.mdl"), "mdl")
    sh.SetSourceAssetSubIdentifier(module, "mdl")
    for name, (vtype, value) in inputs.items():
        inp = sh.CreateInput(name, vtype)
        inp.Set(value)
        if vtype == Sdf.ValueTypeNames.Asset:
            inp.GetAttr().SetColorSpace("sRGB")
    mat.CreateSurfaceOutput("mdl").ConnectToSource(sh.CreateOutput("out", Sdf.ValueTypeNames.Token))


def _setup_material(mat: UsdShade.Material, params: dict) -> None:
    role = params["role"]
    ps = _preview_shader(mat)
    F, C, B, A = (Sdf.ValueTypeNames.Float, Sdf.ValueTypeNames.Color3f, Sdf.ValueTypeNames.Bool,
                  Sdf.ValueTypeNames.Asset)

    def preview(**kw: object) -> None:
        if ps is None:
            return
        for k, v in kw.items():
            vt = C if isinstance(v, Gf.Vec3f) else F
            ps.CreateInput(k, vt).Set(v)

    if role == "pet":
        col = srgb_to_linear(params["color"])
        # 透明 PET は拡散反射がほぼ無い。白い拡散色だと中の液体が白っぽく濁るので暗くし、鏡面反射で見せる
        preview(diffuseColor=col * 0.05, opacity=0.15, ior=1.57, roughness=0.05)
        # 壁は 0.4mm と薄く、実物でも光はほとんど曲がらないので、薄い膜として扱う（屈折させない）。
        # 屈折させると、薄い壁の中を光が行き来して全体が白っぽく濁り、肩に暗い帯が出る
        _add_mdl(mat, "OmniGlass", {"glass_color": (C, col), "glass_ior": (F, 1.57),
                                     "frosting_roughness": (F, 0.0), "thin_walled": (B, True)})
        add_openpbr(mat, {"base_color": col, "specular_roughness": 0.05, "specular_ior": 1.57,
                          "transmission_weight": 1.0, "transmission_color": col, "geometry_thin_walled": True})
    elif role == "liquid":
        col = srgb_to_linear(params["color"])
        clear = params.get("transmission", 0) >= 1.0
        turbidity = params.get("turbidity", 0.0)  # 濁った液体ほど不透明に近づける
        base = 0.25 if clear else 0.92
        preview(diffuseColor=col, opacity=round(base + (1 - base) * turbidity, 3), ior=1.34, roughness=0.02)
        # OmniGlass の色は表面を通るたびに一律にかかるだけで、厚みで濃くならない。OmniSurface の透過は、
        # 深さ（scattering_depth）を与えると「その距離を通った後の色」になる体積吸収なので、そちらを使う
        depth = params.get("absorption_depth") or 0.0
        mpu = UsdGeom.GetStageMetersPerUnit(mat.GetPrim().GetStage())
        tint = Gf.Vec3f(*(max(c, 1e-3) for c in col)) if depth else Gf.Vec3f(1, 1, 1)
        # 濁った液体は体積散乱（params["scattering"] は散乱係数 [1/m]）。OpenPBR（散乱を追う描画器向け）だけ体積で描く
        sigma_s = params.get("scattering", 0.0) * mpu
        # Isaac Sim の RTX（Real-Time・パストレースとも）では、薄い膜（PET の胴）を通した先の液体の体積（吸収・散乱）が
        # 描かれず、胴が白っぽく濁って液体の色が見えない。MDL では液体も薄い膜にする
        if sigma_s and depth:
            # 濁った液体：半透明の膜（translucent と同じ形）。胴の中心を通る光のうち散乱されずに抜ける割合
            # exp(-k τ)（τ = 散乱係数 × 内径）だけ素通しにし、残りは液体の色で拡散反射・拡散透過させる
            clarity = math.exp(-TURBID_CLARITY_K * params["scattering"] * params["absorption_depth"])
            _add_mdl(mat, "OmniSurface", {
                "diffuse_reflection_weight": (F, 1.0),
                "diffuse_reflection_color": (C, col),
                "specular_reflection_roughness": (F, 0.02),
                "specular_reflection_ior": (F, 1.34),
                "enable_specular_transmission": (B, True),
                "specular_transmission_weight": (F, round(clarity, 4)),
                "specular_transmission_color": (C, col),
                "enable_diffuse_transmission": (B, True),
                "subsurface_weight": (F, TURBID_DIFFUSE_TRANSMISSION),
                "subsurface_transmission_color": (C, col),
                "thin_walled": (B, True),
            })
            tint, depth = _turbid_absorption(col, params["scattering"], depth)
        else:
            # 澄んだ液体：色は体積吸収（深さ＝内径）のときと同じでよい。薄い膜でも、PET を外して体積吸収で描いた
            # 液体とほぼ同じ濃さになる
            _add_mdl(mat, "OmniSurface", {
                "diffuse_reflection_weight": (F, 0.0),
                "specular_reflection_roughness": (F, 0.02),
                "specular_reflection_ior": (F, 1.34),
                "enable_specular_transmission": (B, True),
                "specular_transmission_weight": (F, 1.0),
                "specular_transmission_color": (C, tint),
                "specular_transmission_scattering_depth": (F, depth / mpu),
                "thin_walled": (B, True),
            })
        # OpenPBR の媒質: 消散 μt = -ln(transmission_color) / depth、散乱 μs = transmission_scatter / depth
        # （深さはステージの長さ）。MDL と同じ吸収 σa と散乱 σs になるように、色に散乱のぶんの減衰も含める
        extra = (sigma_s / mpu) * depth if depth else 0.0  # σs [1/m] × 深さ [m]
        add_openpbr(mat, {"base_color": col, "specular_roughness": 0.02, "specular_ior": 1.34,
                          "transmission_weight": 1.0,
                          "transmission_color": Gf.Vec3f(*(max(c * math.exp(-extra), 1e-4) for c in tint)),
                          "transmission_depth": depth / mpu,
                          **({"transmission_scatter": Gf.Vec3f(extra, extra, extra),
                              "transmission_scatter_anisotropy": params.get("anisotropy", 0.0)} if extra else {})})
    elif role == "container":
        col = srgb_to_linear(params["color"])
        metallic = params.get("metallic", 0.0)
        rough = params.get("roughness", 0.3 if metallic else 0.5)
        preview(diffuseColor=col, roughness=rough, metallic=metallic, opacity=1.0)
        _add_mdl(mat, "OmniPBR", {"diffuse_color_constant": (C, col), "reflection_roughness_constant": (F, rough),
                                   "metallic_constant": (F, metallic)})
        add_openpbr(mat, {"base_color": col, "base_metalness": metallic, "specular_roughness": rough})
    elif role == "cap":
        # キャップ・蓋。texture_rel があれば蓋の上面の画像
        col = srgb_to_linear(params["color"])
        rough, metallic = params.get("roughness", 0.4), params.get("metallic", 0.0)
        preview(roughness=rough, metallic=metallic)
        if not params.get("texture_rel"):
            preview(diffuseColor=col)
        tex = ({"diffuse_texture": (A, Sdf.AssetPath(params["texture_rel"]))} if params.get("texture_rel")
               else {"diffuse_color_constant": (C, col)})
        _add_mdl(mat, "OmniPBR", {**tex, "reflection_roughness_constant": (F, rough),
                                   "metallic_constant": (F, metallic)})
        add_openpbr(mat, {"base_metalness": metallic, "specular_roughness": rough,
                          **({} if params.get("texture_rel") else {"base_color": col})},
                    base_texture=params.get("texture_rel"))
    elif role == "solid":
        # 組み合わせ形状の部品。画像があれば貼り、なければ単色
        col = srgb_to_linear(params["color"])
        rough, metallic = params.get("roughness", 0.45), params.get("metallic", 0.0)
        preview(roughness=rough, metallic=metallic, opacity=1.0)
        if not params.get("texture_rel"):
            preview(diffuseColor=col)
        tex = ({"diffuse_texture": (A, Sdf.AssetPath(params["texture_rel"]))} if params.get("texture_rel")
               else {"diffuse_color_constant": (C, col)})
        _add_mdl(mat, "OmniPBR", {**tex, "reflection_roughness_constant": (F, rough),
                                   "metallic_constant": (F, metallic)})
        add_openpbr(mat, {"base_metalness": metallic, "specular_roughness": rough,
                          **({} if params.get("texture_rel") else {"base_color": col})},
                    base_texture=params.get("texture_rel"))
        if params.get("emissive") and params.get("texture_rel"):
            _add_emission(mat, params["texture_rel"])
    elif role == "glass":
        # 組み合わせ形状の透明な部品（ショーケースの窓など）とガラス瓶。color はガラスの色味
        col = srgb_to_linear(params["color"])
        ior = params.get("ior", 1.5)
        preview(diffuseColor=col * 0.05, opacity=0.15, ior=ior, roughness=params.get("roughness", 0.02))
        _add_mdl(mat, "OmniGlass", {"glass_color": (C, col), "glass_ior": (F, ior), "frosting_roughness": (F, 0.0),
                                     "thin_walled": (B, bool(params.get("thin_walled", False)))})
        add_openpbr(mat, {"base_color": col, "specular_roughness": params.get("roughness", 0.02), "specular_ior": ior,
                          "transmission_weight": 1.0, "transmission_color": col,
                          "geometry_thin_walled": bool(params.get("thin_walled", False))})
    elif role == "translucent":
        # 半透明の素材（乳白の樹脂・すりガラス・ビニール）。薄い膜として扱い、clarity の割合だけ
        # ぼやけて素通しになり（後ろや中身がにじんで見える）、残りは光を拡散させて通す・返す（白く濁る）
        col = srgb_to_linear(params["color"])
        clarity, rough = params.get("clarity", 0.5), params.get("roughness", 0.35)
        # 素通しでない分のうち拡散透過の割合（MDL）。濁った液体を入れた容器は 1（拡散反射なし。shapes/revolve.py）
        diffuse_transmission = params.get("diffuse_transmission", 0.7)
        preview(diffuseColor=col, opacity=round(1 - 0.6 * clarity, 3), ior=1.5, roughness=rough)
        _add_mdl(mat, "OmniSurface", {
            "diffuse_reflection_weight": (F, 1.0),
            "diffuse_reflection_color": (C, col),
            "specular_reflection_roughness": (F, rough),
            "specular_reflection_ior": (F, 1.5),
            "enable_specular_transmission": (B, True),
            "specular_transmission_weight": (F, clarity),
            "specular_transmission_color": (C, col),
            # 素通しでない分の 7 割を拡散透過（thin_walled では subsurface が拡散透過になる）。
            # 拡散反射が多いと白く光って中身が見えなくなる
            "enable_diffuse_transmission": (B, True),
            "subsurface_weight": (F, diffuse_transmission),
            "subsurface_transmission_color": (C, col),
            "thin_walled": (B, True),
        })
        # 薄い膜（thin_walled）では subsurface が拡散透過になる（MDL と同じ考え方）
        add_openpbr(mat, {"base_color": col, "specular_roughness": rough, "specular_ior": 1.5,
                          "transmission_weight": clarity, "transmission_color": col,
                          "subsurface_weight": 0.7, "subsurface_color": col, "geometry_thin_walled": True})
    elif role == "label":
        # 缶（metallic > 0）は金属に直接印刷したもの。白・黒のインクの所は金属度マップ（surface.py）で非金属にする
        metallic = params.get("metallic", 0.0)
        rough = params.get("roughness", 0.3 if metallic else 0.35)
        preview(roughness=rough, metallic=metallic)
        _add_mdl(mat, "OmniPBR", {"diffuse_texture": (A, Sdf.AssetPath(params["texture_rel"])),
                                   "reflection_roughness_constant": (F, rough), "metallic_constant": (F, metallic)})
        add_openpbr(mat, {"base_metalness": metallic, "specular_roughness": rough}, base_texture=params["texture_rel"])


def _add_emission(mat: UsdShade.Material, rel: str) -> None:
    """画面の画像を発光させる（UsdPreviewSurface の emissiveColor・OmniPBR・OpenPBR）。拡散反射は弱める。"""
    stage = mat.GetPrim().GetStage()
    F, C, B, A = (Sdf.ValueTypeNames.Float, Sdf.ValueTypeNames.Color3f, Sdf.ValueTypeNames.Bool,
                  Sdf.ValueTypeNames.Asset)
    ps = _preview_shader(mat)
    if ps is not None:
        diffuse = ps.GetInput("diffuseColor")
        src = diffuse.GetConnectedSource() if diffuse else None
        if src and src[0]:
            tex = UsdShade.Shader(src[0].GetPrim())
            k = SCREEN_DIFFUSE
            tex.CreateInput("scale", Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(k, k, k, 1))
            st = tex.GetInput("st")
            emis = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Emissive_Texture"))
            emis.CreateIdAttr("UsdUVTexture")
            emis.CreateInput("file", A).Set(Sdf.AssetPath(rel))
            emis.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
            if st and st.GetConnectedSource()[0]:
                s_src, s_name, _ = st.GetConnectedSource()
                emis.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(s_src, s_name)
            for w in ("wrapS", "wrapT"):
                emis.CreateInput(w, Sdf.ValueTypeNames.Token).Set("repeat")
            ps.CreateInput("emissiveColor", C).ConnectToSource(emis.CreateOutput("rgb", Sdf.ValueTypeNames.Float3))
    mdl = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("MDL"))
    if mdl:
        mdl.CreateInput("enable_emission", B).Set(True)
        inp = mdl.CreateInput("emissive_color_texture", A)
        inp.Set(Sdf.AssetPath(rel))
        inp.GetAttr().SetColorSpace("sRGB")
        mdl.CreateInput("emissive_intensity", F).Set(SCREEN_LUMINANCE)
        mdl.CreateInput("diffuse_tint", C).Set(Gf.Vec3f(SCREEN_DIFFUSE, SCREEN_DIFFUSE, SCREEN_DIFFUSE))
    connect_openpbr_emission(mat, rel, SCREEN_LUMINANCE, SCREEN_DIFFUSE)


def write_surface_maps(params: dict) -> None:
    """色テクスチャのあるマテリアルに、粗さ・金属度・法線のテクスチャを作って params["maps"] に入れる。

    つやのある硬い面（smooth。部品の finish が glossy・screen）では作らない（粗さは一定、凹凸なし）。
    """
    if not params.get("texture") or not params.get("texture_rel") or params.get("smooth"):
        return
    role = params["role"]
    kind = surface_kind(role, params.get("labels"), params.get("metallic", 0.0))
    base = params.get("roughness")  # 素材の表（finish.py）や部品の finish で決めた粗さを地にする
    rel_dir = PurePosixPath(params["texture_rel"]).parent
    paths = write_maps(Path(params["texture"]), kind, base)
    params["maps"] = {name: f"{rel_dir}/{p.name}" for name, p in paths.items()}
    params["surface"] = kind


def _connect_maps(mat: UsdShade.Material, params: dict) -> None:
    """params["maps"] のテクスチャを UsdPreviewSurface・OmniPBR・OpenPBR に繋ぐ。非カラーなので色空間は raw（none）。"""
    maps = params.get("maps")
    if not maps:
        return
    stage = mat.GetPrim().GetStage()
    F, A, F2, F4 = (Sdf.ValueTypeNames.Float, Sdf.ValueTypeNames.Asset, Sdf.ValueTypeNames.Float2,
                    Sdf.ValueTypeNames.Float4)
    ps = _preview_shader(mat)
    if ps is not None:
        reader = next((UsdShade.Shader(c) for c in mat.GetPrim().GetChildren()
                       if UsdShade.Shader(c).GetIdAttr().Get() == "UsdPrimvarReader_float2"), None)
        if reader is None:
            reader = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("uvmap"))
            reader.CreateIdAttr("UsdPrimvarReader_float2")
            reader.CreateInput("varname", Sdf.ValueTypeNames.String).Set("st")
        st = reader.CreateOutput("result", F2)
        for name, rel in maps.items():
            tex = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild(f"{name.capitalize()}_Texture"))
            tex.CreateIdAttr("UsdUVTexture")
            tex.CreateInput("file", A).Set(Sdf.AssetPath(rel))
            tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")
            tex.CreateInput("st", F2).ConnectToSource(st)
            for w in ("wrapS", "wrapT"):
                tex.CreateInput(w, Sdf.ValueTypeNames.Token).Set("repeat")
            if name == "normal":
                # 0〜1 に詰めた法線を -1〜1 に戻す（usdchecker --arkit の要件）
                tex.CreateInput("scale", F4).Set(Gf.Vec4f(2, 2, 2, 1))
                tex.CreateInput("bias", F4).Set(Gf.Vec4f(-1, -1, -1, 0))
                out = tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
                ps.CreateInput("normal", Sdf.ValueTypeNames.Normal3f).ConnectToSource(out)
            else:
                ps.CreateInput(name, F).ConnectToSource(tex.CreateOutput("r", F))
    mdl = UsdShade.Shader.Get(stage, mat.GetPath().AppendChild("MDL"))
    if mdl:
        inputs = {"roughness": ("reflectionroughness_texture", "reflection_roughness_texture_influence"),
                  "metallic": ("metallic_texture", "metallic_texture_influence"),
                  "normal": ("normalmap_texture", None)}
        for name, rel in maps.items():
            tex_in, influence = inputs[name]
            inp = mdl.CreateInput(tex_in, A)
            inp.Set(Sdf.AssetPath(rel))
            inp.GetAttr().SetColorSpace("raw")
            if influence:
                mdl.CreateInput(influence, F).Set(1.0)
    connect_openpbr_maps(mat, maps)


def set_material_labels(prim: Usd.Prim, labels: list[str]) -> None:
    """マテリアルに素材の意味ラベル（semantics:labels:material）を付ける。"""
    UsdSemantics.LabelsAPI.Apply(prim, "material").CreateLabelsAttr().Set(Vt.TokenArray(labels or ["plastic"]))


def _dot_relative(path: str) -> str | None:
    """相対パスに ./ を付けた形。直す必要がなければ None。MDL は Isaac Sim の検索パスで解決するのでそのまま。"""
    if (not path or path.startswith(("./", "../", "/")) or "://" in path or ":" in path[:3]
            or path.endswith(".mdl")):
        return None
    return f"./{path}"


def normalize_asset_paths(stage: Usd.Stage) -> int:
    """アセットのパス（テクスチャなど）を ./ で始まる形にそろえる（SimReady の AA.001）。直した数を返す。"""
    fixed = 0
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if attr.GetTypeName() != Sdf.ValueTypeNames.Asset or not attr.HasAuthoredValue():
                continue
            v = attr.Get()
            new = _dot_relative(v.path) if v is not None else None
            if new:
                attr.Set(Sdf.AssetPath(new))
                fixed += 1
    return fixed


def write_part_variants(root: Usd.Prim, sets: dict[str, list[str]], shows: dict[str, dict[str, list[str]]]) -> dict:
    """部品（root 直下のメッシュ）を出し入れするバリアントセットを作る。値の先頭を既定にする。

    各値では表示しない部品だけに visibility = invisible を書く（inherited は書かない）ので、セットを組み合わせると
    どのセットでも表示する部品だけが見える。書いたセット → {variants, default, parts（値 → 表示する部品）}を返す。
    """
    out = {}
    for name, values in sets.items():
        vset = root.GetVariantSets().AddVariantSet(name)
        for v in values:
            vset.AddVariant(v)
        parts: dict[str, list[str]] = {}
        for v in values:
            vset.SetVariantSelection(v)
            with vset.GetVariantEditContext():
                for mesh, show in shows.items():
                    if name in show and v not in show[name]:
                        UsdGeom.Imageable(root.GetChild(mesh)).CreateVisibilityAttr(UsdGeom.Tokens.invisible)
            parts[v] = sorted(m for m, show in shows.items() if name in show and v in show[name])
        vset.SetVariantSelection(values[0])
        out[name] = {"variants": list(values), "default": values[0], "parts": parts}
    return out


def postprocess(result: BuildResult, product_name: str, physics: bool = True,
                surfaces: dict[str, dict] | None = None, physics_materials: dict[str, dict] | None = None,
                collision: dict[str, str] | None = None) -> None:
    """surfaces は spec.json の surfaces（マテリアル名か素材名 → roughness / metallic の上書き）。
    physics_materials は spec.json の physics_materials（素材名かコリジョンの部品名 → 摩擦・反発の上書き）。
    使った物理マテリアルは result.meta["physics_materials"] に残す。
    collision はコリジョンの部品名 → 近似方法（spec.collision_approximations()）。指定のない部品は convexHull。"""
    apply_finishes(result.materials, surfaces)
    stage = Usd.Stage.Open(str(result.usd_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = stage.GetPrimAtPath(f"/{result.root_name}")
    stage.SetDefaultPrim(root)
    Usd.ModelAPI(root).SetKind(Kind.Tokens.component)
    root.SetAssetInfoByKey("name", product_name)
    root.SetAssetInfoByKey("identifier", Sdf.AssetPath(f"./{result.usd_path.name}"))

    mats_path = root.GetPath().AppendChild("_materials")
    for name, params in result.materials.items():
        mat = UsdShade.Material.Get(stage, mats_path.AppendChild(name))
        if mat:
            write_surface_maps(params)
            _setup_material(mat, params)
            _connect_maps(mat, params)
            set_material_labels(mat.GetPrim(), params.get("labels") or ["plastic"])
    normalize_asset_paths(stage)

    for name in result.double_sided:
        mesh = UsdGeom.Mesh.Get(stage, root.GetPath().AppendChild(name))
        if mesh:
            mesh.CreateDoubleSidedAttr(True)

    write_display_colors(stage, root, result.materials)
    write_nonvisual_materials(stage, root, result.materials)
    # 把持の線（FET_005）。床に固定する什器はつかまないので付けない
    grasp = [] if result.static else write_grasp_lines(stage, root)
    if grasp:
        result.meta["grasp"] = grasp
    else:
        result.meta.pop("grasp", None)

    # 内蔵の照明と照明の面の発光（Lighting バリアント）
    # 光る画面の表示（Screen バリアント。Off は消えた液晶）
    screens = write_screen_variant(stage, root, result.materials)
    if screens:
        # 画面のマテリアルと映している画像（入口の USD から見たパス）。ワールド側で画像を差し替えるときに使う
        result.meta["screens"] = [{"material": n, "image": result.materials[n]["texture_rel"]} for n in screens]
    else:
        result.meta.pop("screens", None)

    # 店向けの絵柄（Picture バリアント。Blank は文字・写真を抜いた無地の面）
    pictures = write_picture_variant(stage, root, result.materials)
    if pictures:
        result.meta["pictures"] = [{"material": n, "image": result.materials[n]["texture_rel"],
                                    "blank_image": result.materials[n]["blank_texture_rel"],
                                    **(result.materials[n].get("picture_text") or {})} for n in pictures]
    else:
        result.meta.pop("pictures", None)

    # 部品の出し入れ（育ち具合・熟し具合など。spec の variant_sets と部品の show）
    pv = result.meta.get("part_variants")
    if pv:
        result.meta["variants"] = write_part_variants(root, pv["sets"], pv["shows"])
    else:
        result.meta.pop("variants", None)

    lights = write_lighting(stage, root, result.lights, result.materials)
    if lights:
        result.meta["lights"] = lights
    else:
        result.meta.pop("lights", None)

    see_through = mark_transparency(stage, root, result.materials)
    if see_through:
        result.meta["transparency"] = see_through
    else:
        result.meta.pop("transparency", None)

    if physics:
        body = UsdPhysics.RigidBodyAPI.Apply(root)
        if result.static:
            # 什器は床に固定する。SimReady の RB.001（剛体が 1 つ以上）を満たすためキネマティックな剛体にする
            body.CreateKinematicEnabledAttr(True)
        # キネマティックでも質量は書く（SimReady の RB.007。シミュレーションでは使われない）
        # 可動部（扉など）があれば、その分を除いた本体の質量・重心を書く
        m, com = body_mass(result.mass, result.center_of_mass, result.links)
        mass = UsdPhysics.MassAPI.Apply(root)
        mass.CreateMassAttr(m)
        mass.CreateCenterOfMassAttr(com)

        for name in sorted(set(collision or {}) - set(result.colliders)):
            result.meta.setdefault("warnings", []).append(
                f"collision_approximation の {name} はコリジョンの部品にない（{', '.join(result.colliders)}）")
        groups = _physics_groups(stage, root, result, physics_materials or {})
        result.meta["physics_materials"] = []
        for i, (gname, g) in enumerate(groups.items()):
            pmat = UsdShade.Material.Define(stage, mats_path.AppendChild(
                "PhysicsMaterial" if i == 0 else f"PhysicsMaterial_{gname}"))
            c = contact_for(g["key"], g["collider"], physics_materials)
            papi = UsdPhysics.MaterialAPI.Apply(pmat.GetPrim())
            papi.CreateStaticFrictionAttr(c.static_friction)
            papi.CreateDynamicFrictionAttr(c.dynamic_friction)
            papi.CreateRestitutionAttr(c.restitution)
            set_material_labels(pmat.GetPrim(), g["labels"])
            result.meta["physics_materials"].append(
                {"name": pmat.GetPath().name, "material": g["key"], "colliders": g["prims"],
                 "static_friction": c.static_friction, "dynamic_friction": c.dynamic_friction,
                 "restitution": c.restitution})
            for prim in g["prims"]:
                prim = stage.GetPrimAtPath(root.GetPath().AppendChild(prim))
                UsdPhysics.CollisionAPI.Apply(prim)
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                    (collision or {}).get(prim.GetName(), DEFAULT_COLLISION))
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(
                    pmat, UsdShade.Tokens.weakerThanDescendants, "physics"
                )
        # MuJoCo・Newton のスキーマ（FET_003_MUJOCO・FET_003_NEWTON）。MuJoCo はメッシュを凸包でしか扱えない
        runtimes = apply_runtime_schemas(root)
        hull_only = sorted(set(runtimes["newton"]) - set(runtimes["mujoco"]))
        if hull_only:
            result.meta.setdefault("warnings", []).append(
                f"MuJoCo は凸包のコリジョンしか扱えないので、{', '.join(hull_only)} には MjcCollisionAPI を付けない")
        # 可動部の剛体と関節（FET_004）。部品を可動部の Xform の下へ移すので、部品名で引く処理より後に置く
        joints = build_links(stage, root, result.links, kinematic=result.static)
        if joints:
            result.meta["joints"] = joints
            moved = {name: f"{j['link']}/{name}" for j in joints for name in j["parts"]}
            if result.meta.get("transparency"):
                result.meta["transparency"] = {moved.get(k, k): v for k, v in result.meta["transparency"].items()}
        else:
            result.meta.pop("joints", None)

    stage.GetRootLayer().Save()


DISPLAY_GREY = Gf.Vec3f(0.18, 0.18, 0.18)  # マテリアルのないメッシュの表示色（線形の 18% グレー）


def texture_mean(path: str | Path) -> Gf.Vec3f | None:
    """テクスチャの平均の色（線形）。透明な画素は除く。読めなければ None。"""
    import numpy as np
    from PIL import Image

    try:
        im = Image.open(path).convert("RGBA")
    except OSError:
        return None
    im.thumbnail((256, 256))
    a = np.asarray(im, float) / 255
    c = a[..., :3]
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    w = a[..., 3]
    if w.sum() <= 0:
        return None
    mean = (lin * w[..., None]).sum((0, 1)) / w.sum()
    return Gf.Vec3f(*(float(v) for v in mean))


def display_color(params: dict | None) -> Gf.Vec3f:
    """マテリアルの表示色（線形）。テクスチャがあれば画像の平均、なければマテリアルの色。"""
    params = params or {}
    col = texture_mean(params["texture"]) if params.get("texture") else None
    if col is None and params.get("color"):
        col = srgb_to_linear(params["color"])
    col = col if col is not None else DISPLAY_GREY
    return Gf.Vec3f(*(min(max(v, 0.0), 1.0) for v in col))


def _display_opacity(mat: UsdShade.Material | None) -> float | None:
    """透明・半透明のマテリアルの不透明度（UsdPreviewSurface の opacity）。不透明なら None。"""
    ps = _preview_shader(mat) if mat else None
    inp = ps.GetInput("opacity") if ps else None
    v = inp.Get() if inp and not inp.HasConnectedSource() else None
    return float(v) if v is not None and v < 1.0 else None


def write_display_colors(stage: Usd.Stage, root: Usd.Prim, materials: dict[str, dict]) -> int:
    """描画するメッシュに表示色（primvars:displayColor）を書く（SimReady の DISP.001〜003）。書いた数を返す。

    マテリアルを読まない描画（ビューポートの簡易表示など）で使われる。色は割り当てたマテリアルから決め、
    面ごとにマテリアルを分けたメッシュは面ごとの色（uniform）にする。透明・半透明の部品は displayOpacity も書く。
    """
    cache: dict[str, Gf.Vec3f] = {}

    def color_of(name: str | None) -> Gf.Vec3f:
        if name not in cache:
            cache[name] = display_color(materials.get(name or ""))
        return cache[name]

    n = 0
    for prim in Usd.PrimRange(root):
        gprim = UsdGeom.Gprim(prim)
        if not gprim or UsdGeom.Imageable(prim).ComputePurpose() not in (UsdGeom.Tokens.default_,
                                                                          UsdGeom.Tokens.render):
            continue
        direct = UsdShade.MaterialBindingAPI(prim).GetDirectBinding().GetMaterialPath()
        face_mats: list[str | None] | None = None
        mesh = UsdGeom.Mesh(prim)
        subsets = UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(prim)) if mesh else []
        if subsets:
            count = len(mesh.GetFaceVertexCountsAttr().Get() or [])
            face_mats = [direct.name if direct else None] * count
            for sub in subsets:
                path = UsdShade.MaterialBindingAPI(sub.GetPrim()).GetDirectBinding().GetMaterialPath()
                if path:
                    for i in sub.GetIndicesAttr().Get() or []:
                        if 0 <= i < count:
                            face_mats[i] = path.name
        if face_mats and len(set(face_mats)) > 1:
            pv = gprim.CreateDisplayColorPrimvar(UsdGeom.Tokens.uniform)
            pv.Set(Vt.Vec3fArray([color_of(m) for m in face_mats]))
        else:
            name = face_mats[0] if face_mats else (direct.name if direct else None)
            gprim.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant).Set(Vt.Vec3fArray([color_of(name)]))
        main = _bound_material(prim)
        opacity = _display_opacity(UsdShade.Material.Get(stage, root.GetPath().AppendChild("_materials")
                                                         .AppendChild(main))) if main else None
        if opacity is not None:
            gprim.CreateDisplayOpacityPrimvar(UsdGeom.Tokens.constant).Set(Vt.FloatArray([opacity]))
        n += 1
    return n


TRANSPARENCY_ATTR = "agenticUsdGen:transparency"
NO_SHADOW_PRIMVAR = "doNotCastShadows"  # RTX の影を落とさない（primvars:doNotCastShadows）
TURBID_LIQUID = 0.5  # これ以上濁った液体は translucent（深度センサーで面が取れることもある）


def material_transparency(params: dict | None) -> str | None:
    """見た目のマテリアルの透け方。transparent（素通し）/ translucent（半透明）/ None（不透明）。"""
    role = (params or {}).get("role")
    if role in ("pet", "glass"):
        return "transparent"
    if role == "translucent":
        return "translucent"
    if role == "liquid":
        return "translucent" if params.get("turbidity", 0.0) >= TURBID_LIQUID else "transparent"
    return None


def mark_transparency(stage: Usd.Stage, root: Usd.Prim, materials: dict[str, dict]) -> dict[str, str]:
    """透明・半透明のメッシュに agenticUsdGen:transparency（token）を書き、ルートからの相対パス → 透け方を返す。

    深度センサーの加工用（実機の深度カメラは透明・半透明の物体の深度を測りにくい）。
    面ごとにマテリアルを分けたメッシュは、いちばん面の多いマテリアルで決める。

    素通しの（transparent）メッシュと液体には primvars:doNotCastShadows = true も書く。Isaac Sim の RTX Real-Time では
    OmniGlass・透過の OmniSurface も不透明な影を落とし、ケースや包装の中身、ボトルの下半分が黒くなるため。
    濁った液体（translucent）も、影を落とすとボトルの肩と底が黒くなる。
    それ以外の半透明の（translucent）メッシュは実物でも影ができるので落とす。"""
    out: dict[str, str] = {}
    for prim in Usd.PrimRange(root):
        if not prim.IsA(UsdGeom.Mesh):
            continue
        params = materials.get(_bound_material(prim) or "")
        kind = material_transparency(params)
        attr = prim.GetAttribute(TRANSPARENCY_ATTR)
        if kind:
            prim.CreateAttribute(TRANSPARENCY_ATTR, Sdf.ValueTypeNames.Token, custom=True).Set(kind)
            out[str(prim.GetPath().MakeRelativePath(root.GetPath()))] = kind
        elif attr:
            prim.RemoveProperty(TRANSPARENCY_ATTR)
        primvars = UsdGeom.PrimvarsAPI(prim)
        if kind == "transparent" or (params or {}).get("role") == "liquid":
            primvars.CreatePrimvar(NO_SHADOW_PRIMVAR, Sdf.ValueTypeNames.Bool, UsdGeom.Tokens.constant).Set(True)
        elif primvars.HasPrimvar(NO_SHADOW_PRIMVAR):
            primvars.RemovePrimvar(NO_SHADOW_PRIMVAR)
    return out


def _bound_material(prim: Usd.Prim) -> str | None:
    """メッシュに割り当てた見た目のマテリアルの名前。面ごとに分けていれば、いちばん面の多いもの。"""
    direct = UsdShade.MaterialBindingAPI(prim).GetDirectBinding().GetMaterialPath()
    if direct:
        return direct.name
    best = None
    for s in UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(prim)):
        path = UsdShade.MaterialBindingAPI(s.GetPrim()).GetDirectBinding().GetMaterialPath()
        n = len(s.GetIndicesAttr().Get() or [])
        if path and (best is None or n > best[0]):
            best = (n, path.name)
    return best[1] if best else None


def _physics_groups(stage: Usd.Stage, root: Usd.Prim, result: BuildResult, overrides: dict) -> dict[str, dict]:
    """コリジョンの部品を、物理の素材ごと（部品名で上書きした部品はその部品だけ）にまとめる。"""
    groups: dict[str, dict] = {}
    for name in result.colliders:
        prim = stage.GetPrimAtPath(root.GetPath().AppendChild(name))
        if not prim:
            continue
        params = result.materials.get(_bound_material(prim) or "")
        if params:
            role, labels = params.get("role"), params.get("labels") or result.physics_labels
        else:
            role, labels = None, result.physics_labels
        key = physics_key(role, labels)
        own = name in overrides
        g = groups.setdefault(name if own else key,
                              {"key": key, "collider": name if own else None, "labels": list(labels), "prims": []})
        g["prims"].append(name)
    return groups


def export_usda(usd_path: Path) -> Path:
    out = usd_path.with_suffix(".usda")
    Sdf.Layer.FindOrOpen(str(usd_path)).Export(str(out))
    return out


def export_usdz(usd_path: Path) -> Path:
    """Quick Look 用の usdz。MDL は Isaac Sim 組み込みで解決できず、OpenPBR（MaterialX）も Quick Look は描かないので、
    両方を取り除いた複製から作る。
    把持の線（guide）も Quick Look は描いてしまうので取り除く。"""
    out = usd_path.with_suffix(".usdz")
    tmp = usd_path.with_name(f"{usd_path.stem}_quicklook.usdc")  # テクスチャの相対パスを保つため同じフォルダに置く
    try:
        Sdf.Layer.FindOrOpen(str(usd_path)).Export(str(tmp))
        stage = Usd.Stage.Open(str(tmp))
        for prim in list(stage.Traverse()):
            if prim.IsA(UsdShade.Material):
                prim.RemoveProperty("outputs:mdl:surface")
                prim.RemoveProperty("outputs:mtlx:surface")
            elif ((prim.IsA(UsdShade.Shader) and (UsdShade.Shader(prim).GetImplementationSource() == "sourceAsset"
                                                  or str(UsdShade.Shader(prim).GetIdAttr().Get()).startswith("ND_")))
                  or (prim.IsA(UsdGeom.BasisCurves) and prim.GetName().startswith(GRASP_PREFIX))):
                stage.RemovePrim(prim.GetPath())
        stage.GetRootLayer().Save()
        if not UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(tmp)), str(out)):
            raise RuntimeError("usdz の作成に失敗しました")
    finally:
        tmp.unlink(missing_ok=True)
    return out
