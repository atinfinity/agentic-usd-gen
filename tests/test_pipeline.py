"""Blender を使う結合テスト（Blender が無ければスキップ）。"""

import math
import zipfile

import numpy as np
import pytest
from PIL import Image
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

from tests.conftest import D, H
from agentic_usd_gen.shapes.revolve import (LIQUID_INSET, TURBID_ANISOTROPY, TURBID_TAU, WALL, BuildContext,
                                  RevolveBuilder, make_lid_texture)
from agentic_usd_gen.physics_runtimes import applied_schemas
from agentic_usd_gen.spec import Dimensions, ProductSpec
from agentic_usd_gen.usd_post import TURBID_CLARITY_K, export_usda, export_usdz, postprocess
from agentic_usd_gen.validate import check_usdz, validate
from agentic_usd_gen.vision import Landmarks


@pytest.fixture(scope="module")
def built(tmp_path_factory, bottle_png, blender):
    out = tmp_path_factory.mktemp("out")
    spec = ProductSpec(product_name="合成ボトル", slug="synthetic_bottle", shape_class="revolve",
                       dimensions=Dimensions(H, D), capacity_ml=500)
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), out, out / "debug", blender)
    result = RevolveBuilder().build(ctx)
    postprocess(result, spec.product_name)
    return spec, result


def test_structure(built):
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    root = stage.GetDefaultPrim()
    assert root.GetName() == "synthetic_bottle"
    assert {c.GetName() for c in root.GetChildren()} >= {"Body", "Cap", "Liquid", "Label", "_materials"}
    assert root.HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdPhysics.MassAPI(root).GetMassAttr().Get() == pytest.approx(0.52)
    assert stage.GetPrimAtPath("/synthetic_bottle/Body").HasAPI(UsdPhysics.CollisionAPI)
    assert not stage.GetPrimAtPath("/synthetic_bottle/Liquid").HasAPI(UsdPhysics.CollisionAPI)
    approx = UsdPhysics.MeshCollisionAPI(stage.GetPrimAtPath("/synthetic_bottle/Cap")).GetApproximationAttr().Get()
    assert approx == "convexHull"


def test_materials_have_mdl(built):
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    for name in ("PET", "CapMat", "LiquidMat", "LabelMat"):
        mat = UsdShade.Material.Get(stage, f"/synthetic_bottle/_materials/{name}")
        assert mat.GetSurfaceOutput().HasConnectedSource(), name
        assert mat.GetSurfaceOutput("mdl").HasConnectedSource(), name
        # SimReady の FET_006_OPENPBR: MaterialX の OpenPBR も繋ぐ
        src, _, _ = mat.GetSurfaceOutput("mtlx").GetConnectedSource()
        assert UsdShade.Shader(src.GetPrim()).GetIdAttr().Get() == "ND_open_pbr_surface_surfaceshader", name
    mdl = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LabelMat/MDL")
    assert mdl.GetInput("diffuse_texture").Get().path == "./textures/label.png"
    # ラベルの画像は OpenPBR の base_color にも sRGB で、粗さなどのテクスチャは none で繋ぐ
    tex = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LabelMat/OpenPBR_base_color")
    assert tex.GetInput("file").Get().path == "./textures/label.png"
    assert tex.GetInput("file").GetAttr().GetColorSpace() == "srgb_texture"
    rough = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LabelMat/OpenPBR_roughness")
    assert rough.GetInput("file").GetAttr().GetColorSpace() == "none"

    # SimReady の AA.001: 相対パスは ./ で始める（Blender が書いた UsdUVTexture も含む）。MDL はそのまま
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            v = attr.Get() if attr.GetTypeName() == "asset" else None
            if v and v.path and not v.path.endswith(".mdl"):
                assert v.path.startswith("./"), (attr.GetPath(), v.path)
    assert stage.GetDefaultPrim().GetAssetInfoByKey("identifier").path == "./synthetic_bottle.usd"


def _max_radius(stage, path):
    prim = stage.GetPrimAtPath(path)
    m = UsdGeom.Imageable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    pts = np.array([m.Transform(p) for p in UsdGeom.Mesh(prim).GetPointsAttr().Get()])
    return float(np.hypot(pts[:, 0], pts[:, 1]).max())


def test_liquid_overlaps_wall(built):
    """液体の外周は PET の壁の中（すき間なし）にある。境目を PET→液体 の 1 つにするため。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    gap = _max_radius(stage, "/synthetic_bottle/Body") - _max_radius(stage, "/synthetic_bottle/Liquid")
    assert gap == pytest.approx(WALL * LIQUID_INSET, abs=1e-4)
    assert 0 < gap < WALL


def test_liquid_absorption(built):
    """液体は OmniSurface の透過。色付きなら内径ぶんの深さで吸収し、無色なら吸収しない。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    mdl = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LiquidMat/MDL")
    assert mdl.GetSourceAssetSubIdentifier("mdl") == "OmniSurface"
    assert mdl.GetInput("enable_specular_transmission").Get() is True
    depth = mdl.GetInput("specular_transmission_scattering_depth").Get()
    color = mdl.GetInput("specular_transmission_color").Get()
    # 澄んだ液体は MDL では薄い膜（PET 越しに体積吸収が描かれないため）
    assert mdl.GetInput("thin_walled").Get() is True
    if depth > 0:
        assert depth == pytest.approx(2 * _max_radius(stage, "/synthetic_bottle/Liquid"), rel=0.05)
    else:
        assert tuple(color) == (1, 1, 1)
    # OpenPBR も同じ深さで透過させる
    pbr = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LiquidMat/OpenPBR")
    assert pbr.GetInput("transmission_weight").Get() == 1.0
    assert pbr.GetInput("transmission_depth").Get() == pytest.approx(depth)


def test_pet_thin_walled(built):
    """PET の壁は薄い膜として扱う（屈折させない）。屈折させると中の液体が白っぽく濁る。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    mdl = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/PET/MDL")
    assert mdl.GetSourceAssetSubIdentifier("mdl") == "OmniGlass"
    assert mdl.GetInput("thin_walled").Get() is True
    pbr = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/PET/OpenPBR")
    assert pbr.GetInput("transmission_weight").Get() == 1.0 and pbr.GetInput("geometry_thin_walled").Get() is True


def test_material_labels(built):
    """SimReady の SL.MAT.001: 物理マテリアルも含め、すべての Material に素材の意味ラベルがある。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    labels = {p.GetName(): list(p.GetAttribute("semantics:labels:material").Get())
              for p in stage.GetPrimAtPath("/synthetic_bottle/_materials").GetChildren()}
    assert labels == {"PET": ["plastic"], "CapMat": ["plastic"], "CapTopMat": ["plastic"], "LiquidMat": ["liquid"],
                      "LabelMat": ["plastic"], "LabelBackMat": ["plastic"], "PhysicsMaterial": ["plastic"]}


def test_transparency_attr(built):
    """透明な容器と澄んだ液体のメッシュに agenticUsdGen:transparency を付け、meta に一覧を残す。不透明な部品には付けない。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    assert r.meta["transparency"] == {"Body": "transparent", "Liquid": "transparent"}
    for name in ("Body", "Liquid"):
        attr = stage.GetPrimAtPath(f"/synthetic_bottle/{name}").GetAttribute("agenticUsdGen:transparency")
        assert attr.Get() == "transparent" and attr.GetTypeName() == "token" and attr.IsCustom()
        # 素通しの部品は RTX で影を落とさない（中身が黒くならないように）
        pv = UsdGeom.PrimvarsAPI(stage.GetPrimAtPath(f"/synthetic_bottle/{name}")).GetPrimvar("doNotCastShadows")
        assert pv.Get() is True and pv.GetInterpolation() == UsdGeom.Tokens.constant
    for name in ("Cap", "Label", "LabelBack"):
        prim = stage.GetPrimAtPath(f"/synthetic_bottle/{name}")
        assert not prim.GetAttribute("agenticUsdGen:transparency")
        assert not UsdGeom.PrimvarsAPI(prim).HasPrimvar("doNotCastShadows")


def test_display_color(built):
    """SimReady の DISP.001〜003: 描画するメッシュすべてに表示色。キャップは面ごと、透明な容器は不透明度も。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    for name in ("Body", "Cap", "Liquid", "Label", "LabelBack"):
        pv = UsdGeom.PrimvarsAPI(stage.GetPrimAtPath(f"/synthetic_bottle/{name}")).GetPrimvar("displayColor")
        cols = np.array(pv.Get())
        assert pv.GetTypeName() == "color3f[]" and ((cols >= 0) & (cols <= 1)).all(), name
    cap = UsdGeom.Mesh(stage.GetPrimAtPath("/synthetic_bottle/Cap"))
    pv = UsdGeom.PrimvarsAPI(cap).GetPrimvar("displayColor")
    assert pv.GetInterpolation() == "uniform" and len(pv.Get()) == len(cap.GetFaceVertexCountsAttr().Get())
    body = UsdGeom.PrimvarsAPI(stage.GetPrimAtPath("/synthetic_bottle/Body"))
    assert 0 < body.GetPrimvar("displayOpacity").Get()[0] < 0.5


def test_nonvisual_materials(built):
    """SimReady の FET_007: メッシュに割り当てた見た目のマテリアルに光学以外の属性。物理マテリアルには書かない。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    mats = stage.GetPrimAtPath("/synthetic_bottle/_materials")
    base = {p.GetName(): p.GetAttribute("omni:simready:nonvisual:base").Get() for p in mats.GetChildren()}
    assert base == {"PET": "plexiglass", "CapMat": "plastic", "CapTopMat": None, "LiquidMat": "water",
                    "LabelMat": "plastic", "LabelBackMat": "plastic", "PhysicsMaterial": None}
    assert mats.GetChild("LabelMat").GetAttribute("omni:simready:nonvisual:coating").Get() == "paint"


def test_grasp_lines(built):
    """SimReady の FET_005: 胴の直径を横切る把持の線（描画しない guide）。meta.json にも残す。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    curve = UsdGeom.BasisCurves(stage.GetPrimAtPath("/synthetic_bottle/grasp_identifier_01"))
    assert curve and curve.ComputePurpose() == UsdGeom.Tokens.guide
    a, b = np.array(curve.GetPointsAttr().Get())
    assert np.linalg.norm(b - a) == pytest.approx(2 * _max_radius(stage, "/synthetic_bottle/Body"), rel=0.1)
    assert [g["name"] for g in r.meta["grasp"]] == ["grasp_identifier_01"]


def test_label_back(built):
    """透明ボトルのラベルの裏面は、容器の表面とラベルの間に内向きに置き、白地に薄く絵柄が透けたテクスチャを貼る。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    root = "/synthetic_bottle"
    rb, rl, rk = (_max_radius(stage, f"{root}/{n}") for n in ("Body", "Label", "LabelBack"))
    assert rb < rk < rl
    # 法線は内向き（面の頂点の重心から、面の法線方向へ進むと軸に近づく）
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(f"{root}/LabelBack"))
    pts = np.array(mesh.GetPointsAttr().Get())
    idx = np.array(mesh.GetFaceVertexIndicesAttr().Get())
    counts = np.array(mesh.GetFaceVertexCountsAttr().Get())
    assert (counts == 4).all()
    q = pts[idx.reshape(-1, 4)]
    n = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0])
    c = q.mean(1)
    if mesh.GetOrientationAttr().Get() == UsdGeom.Tokens.leftHanded:
        n = -n
    assert (np.einsum("ij,ij->i", n[:, :2], c[:, :2]) < 0).mean() > 0.95
    mdl = UsdShade.Shader.Get(stage, f"{root}/_materials/LabelBackMat/MDL")
    assert mdl.GetInput("diffuse_texture").Get().path == "./textures/label_back.png"
    tex = r.usd_path.parent / "textures"
    front = np.asarray(Image.open(tex / "label.png").convert("RGB"), float)
    back = np.asarray(Image.open(tex / "label_back.png").convert("RGB"), float)
    assert back.mean() > front.mean() and back.std() < front.std()


def test_cap_knurl(built):
    """ねじキャップの側面には縦の溝の法線マップが付き、上面は溝のない別のマテリアルになる。"""
    _, r = built
    assert r.meta["profile"]["knurl"] is True
    stage = Usd.Stage.Open(str(r.usd_path))
    mats = "/synthetic_bottle/_materials"
    mdl = UsdShade.Shader.Get(stage, f"{mats}/CapMat/MDL")
    assert mdl.GetInput("normalmap_texture").Get().path == "./textures/cap_normal.png"
    assert not UsdShade.Shader.Get(stage, f"{mats}/CapTopMat/MDL").GetInput("normalmap_texture")
    assert (r.usd_path.parent / "textures" / "cap_normal.png").exists()
    # 上面の円だけ CapTopMat
    cap = stage.GetPrimAtPath("/synthetic_bottle/Cap")
    subsets = {UsdShade.MaterialBindingAPI(s).GetDirectBinding().GetMaterialPath().name: len(s.GetIndicesAttr().Get())
               for s in UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(cap))}
    assert subsets.get("CapTopMat") == 1


def test_material_finish(built):
    """キャップは PP、ラベルはフィルムの粗さ（素材の表 finish.py）。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    mats = "/synthetic_bottle/_materials"
    cap = UsdShade.Shader.Get(stage, f"{mats}/CapMat/MDL")
    assert cap.GetInput("reflection_roughness_constant").Get() == pytest.approx(0.55)
    assert r.materials["LabelMat"]["finish"] == "film"
    assert r.materials["LabelMat"]["roughness"] == pytest.approx(0.2)


def test_physics_material(built):
    """PET のボトルと PP のキャップは、プラスチックの物理マテリアル 1 つを共有する。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    pm = UsdPhysics.MaterialAPI(stage.GetPrimAtPath("/synthetic_bottle/_materials/PhysicsMaterial"))
    assert pm.GetStaticFrictionAttr().Get() == pytest.approx(0.35)
    assert pm.GetDynamicFrictionAttr().Get() == pytest.approx(0.28)
    assert [m["material"] for m in r.meta["physics_materials"]] == ["plastic"]
    assert r.meta["physics_materials"][0]["colliders"] == r.colliders
    # MuJoCo・Newton のスキーマ（FET_003）
    assert "NewtonMaterialAPI" in applied_schemas(pm.GetPrim())
    for name in r.colliders:
        prim = next(p for p in stage.Traverse() if p.GetName() == name and p.HasAPI(UsdPhysics.CollisionAPI))
        assert {"MjcCollisionAPI", "NewtonCollisionAPI", "NewtonMeshCollisionAPI"} <= set(applied_schemas(prim))


def _rz(stage, path):
    """メッシュの頂点の (半径, z)。"""
    prim = stage.GetPrimAtPath(path)
    m = UsdGeom.Imageable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    pts = np.array([m.Transform(p) for p in UsdGeom.Mesh(prim).GetPointsAttr().Get()])
    return np.stack([np.hypot(pts[:, 0], pts[:, 1]), pts[:, 2]], 1)


def test_can_ends(tmp_path, blender, monkeypatch):
    """缶は上面が巻き締めの縁の内側でくぼみ、底の中央がドームで持ち上がる。
    外形（凸包）と質量・重心は、細部を付けないときと同じ。"""
    import cv2

    from agentic_usd_gen.fictional import forms
    from agentic_usd_gen.shapes import details

    form = forms.aluminum_can(0.122, 0.066, top_d=0.054, label_margin=0.008)
    png = tmp_path / "can.png"
    Image.fromarray(forms.draw_silhouette(form)).save(png)

    def build(name):
        spec = ProductSpec(product_name="缶", slug=name, shape_class="revolve", capacity_ml=350,
                           dimensions=Dimensions(0.122, 0.066, 0.003, 0.054), container_material="aluminum")
        out = tmp_path / name
        ctx = BuildContext(spec, [png], None, Landmarks(**form.landmarks()), out, out / "debug", blender)
        result = RevolveBuilder().build(ctx)
        return result, Usd.Stage.Open(str(result.usd_path))

    r, stage = build("can")
    assert r.meta["profile"]["can_ends"] is True and "knurl" not in r.meta["profile"]
    cap, body = _rz(stage, "/can/Cap"), _rz(stage, "/can/Body")
    H = cap[:, 1].max()
    assert H - cap[:, 1].min() == pytest.approx(details.TOP_RECESS, abs=3e-4)  # 縁の下端より深くくぼむ
    center = body[body[:, 0] < 0.005]
    assert center[:, 1].min() == pytest.approx(details.DOME_RATIO * 0.066, abs=1.5e-3)  # 底の中央が持ち上がる

    monkeypatch.setattr(details, "is_can", lambda *a: False)
    r0, stage0 = build("plain")
    assert "can_ends" not in r0.meta["profile"]
    assert r.mass == r0.mass and r.center_of_mass == r0.center_of_mass

    def hull_area(st, root):
        pts = np.vstack([_rz(st, f"/{root}/Body"), _rz(st, f"/{root}/Cap")])
        pts = np.vstack([pts, pts * [-1, 1]]).astype(np.float32)
        return cv2.contourArea(cv2.convexHull(pts))

    assert hull_area(stage, "can") == pytest.approx(hull_area(stage0, "plain"), rel=1e-3)


def test_validate(built):
    spec, r = built
    rep = validate(r.usd_path, spec.dimensions)
    assert rep.ok, rep.errors
    assert rep.info["expected_mdl_issues"] > 0


def test_exports(built):
    _, r = built
    assert export_usda(r.usd_path).read_text().startswith("#usda")
    usdz = export_usdz(r.usd_path)
    names = zipfile.ZipFile(usdz).namelist()
    assert names[0].endswith(".usdc") and any(n.endswith("label.png") for n in names)
    assert check_usdz(usdz).ok
    # 把持の線（guide）は Quick Look が描いてしまうので usdz には入れない
    packed = Usd.Stage.Open(str(usdz))
    assert not packed.GetPrimAtPath("/synthetic_bottle/grasp_identifier_01")
    # OpenPBR（MaterialX）も Quick Look は描かないので入れない
    assert not any(str(UsdShade.Shader(p).GetIdAttr().Get()).startswith("ND_") for p in packed.Traverse()
                   if p.IsA(UsdShade.Shader))
    assert not packed.GetPrimAtPath("/synthetic_bottle/_materials/PET").HasAttribute("outputs:mtlx:surface")
    assert Usd.Stage.Open(str(r.usd_path)).GetPrimAtPath("/synthetic_bottle/grasp_identifier_01")


def test_opaque_container(tmp_path, bottle_png, blender):
    """不透明容器（紙カップ・缶）は液体を作らず、本体を不透明マテリアルにする。"""
    spec = ProductSpec(product_name="紙カップ", slug="paper_cup", shape_class="revolve",
                       dimensions=Dimensions(H, D), mass_kg=0.1, container_material="paper")
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    assert not stage.GetPrimAtPath(root.GetPath().AppendChild("Liquid"))
    mat = UsdShade.Material.Get(stage, root.GetPath().AppendPath("_materials/ContainerMat"))
    assert mat and mat.GetSurfaceOutput("mdl").HasConnectedSource()
    assert result.mass == pytest.approx(0.1)
    assert validate(result.usd_path, spec.dimensions).ok


@pytest.mark.parametrize("material,metallic", [("aluminum", 1.0), ("スチール", 1.0), ("paper", 0.0)])
def test_can_label_metallic(tmp_path, bottle_png, blender, material, metallic):
    """缶（アルミ・スチール）のラベルは金属（インクの濃い所は金属度マップで下げる）。紙の容器のラベルは非金属のまま。"""
    spec = ProductSpec(product_name="缶", slug="can", shape_class="revolve",
                       dimensions=Dimensions(H, D), mass_kg=0.1, container_material=material)
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    mats = stage.GetDefaultPrim().GetPath().AppendChild("_materials")
    mdl = UsdShade.Shader.Get(stage, mats.AppendPath("LabelMat/MDL"))
    assert mdl.GetInput("metallic_constant").Get() == pytest.approx(metallic)
    assert bool(mdl.GetInput("metallic_texture")) == bool(metallic)  # 金属度マップは金属のときだけ
    ps = UsdShade.Shader(next(c for c in stage.GetPrimAtPath(mats.AppendChild("LabelMat")).GetChildren()
                              if UsdShade.Shader(c).GetIdAttr().Get() == "UsdPreviewSurface"))
    inp = ps.GetInput("metallic")
    if metallic:
        assert inp.HasConnectedSource()
    else:
        assert not inp or (not inp.HasConnectedSource() and not inp.Get())
    body = UsdShade.Shader.Get(stage, mats.AppendPath("ContainerMat/MDL"))
    assert body.GetInput("metallic_constant").Get() == pytest.approx(metallic)


def test_translucent_container(tmp_path, bottle_png, blender):
    """半透明の容器（HDPE など）は中身の液体を作り、本体を半透明の膜（OmniSurface の thin_walled + 拡散透過）にする。"""
    spec = ProductSpec(product_name="漂白剤", slug="bleach", shape_class="revolve",
                       dimensions=Dimensions(H, D), mass_kg=0.5, container_material="HDPE (translucent)")
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    assert result.meta["profile"]["translucent"] == "translucent"
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    assert stage.GetPrimAtPath(root.GetPath().AppendChild("Liquid"))
    mdl = UsdShade.Shader.Get(stage, root.GetPath().AppendPath("_materials/ContainerMat/MDL"))
    assert mdl.GetSourceAssetSubIdentifier("mdl") == "OmniSurface"
    assert mdl.GetInput("thin_walled").Get() is True
    assert mdl.GetInput("enable_diffuse_transmission").Get() is True
    assert validate(result.usd_path, spec.dimensions).ok


def test_transparency_from_spec(tmp_path, bottle_png, blender):
    """素材名では不透明な容器（PP）も、spec の transparency で半透明にでき、中身の液体を作る。"""
    from agentic_usd_gen.spec import Colors

    spec = ProductSpec(product_name="カップ", slug="cup", shape_class="revolve", dimensions=Dimensions(H, D),
                       mass_kg=0.3, container_material="PP", transparency="frosted", colors=Colors(liquid="#7A4A2A"))
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    assert result.meta["profile"]["transparency"] == "frosted"
    assert result.materials["ContainerMat"]["role"] == "translucent" and "LiquidMat" in result.materials
    postprocess(result, spec.product_name)
    assert result.meta["transparency"]["Body"] == "translucent"


def test_glass_jar(tmp_path, bottle_png, blender):
    """ガラス瓶は PET と別のマテリアル（屈折率 1.52・薄い緑）で、壁と底が厚い。中身は厚い底の上から入れる。"""
    from agentic_usd_gen.shapes.revolve import GLASS_BOTTOM, GLASS_IOR, GLASS_WALL

    spec = ProductSpec(product_name="ジャム", slug="jam", shape_class="revolve",
                       dimensions=Dimensions(H, D), mass_kg=0.5, container_material="glass")
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    assert result.meta["profile"]["glass"] is True
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim().GetPath()
    mdl = UsdShade.Shader.Get(stage, root.AppendPath("_materials/GlassMat/MDL"))
    assert mdl.GetSourceAssetSubIdentifier("mdl") == "OmniGlass"
    assert mdl.GetInput("glass_ior").Get() == pytest.approx(GLASS_IOR)
    r, g, b = mdl.GetInput("glass_color").Get()
    assert g > r and g > b  # ごく薄い緑
    gap = _max_radius(stage, root.AppendPath("Body")) - _max_radius(stage, root.AppendPath("Liquid"))
    assert gap == pytest.approx(GLASS_WALL * LIQUID_INSET, abs=2e-4)
    liq = stage.GetPrimAtPath(root.AppendPath("Liquid"))
    m = UsdGeom.Imageable(liq).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    z0 = min(m.Transform(p)[2] for p in UsdGeom.Mesh(liq).GetPointsAttr().Get())
    assert z0 == pytest.approx(GLASS_BOTTOM - GLASS_WALL * LIQUID_INSET, abs=2e-4)
    assert validate(result.usd_path, spec.dimensions).ok


@pytest.mark.parametrize("turbidity", [None, 0.7])
def test_turbid_liquid(tmp_path, bottle_png, blender, turbidity):
    """濁った液体は、MDL では半透明の膜、OpenPBR では体積散乱になり、プレビューの不透明度も上がる。
    濁りが未設定なら商品名から推定する（オレンジ → 0.7）。"""
    from agentic_usd_gen.spec import Colors

    spec = ProductSpec(product_name="オレンジ 100%", slug="oj", shape_class="revolve", dimensions=Dimensions(H, D),
                       capacity_ml=500, colors=Colors(liquid="#F5A623", liquid_turbidity=turbidity))
    ctx = BuildContext(spec, [bottle_png], None, Landmarks(), tmp_path, tmp_path / "debug", blender)
    result = RevolveBuilder().build(ctx)
    assert result.meta["profile"]["turbidity"] == 0.7
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    mat = stage.GetDefaultPrim().GetPath().AppendPath("_materials/LiquidMat")
    mdl = UsdShade.Shader.Get(stage, mat.AppendChild("MDL"))
    # MDL（Isaac Sim）は半透明の膜。PET 越しに体積散乱が描かれないため
    assert mdl.GetInput("thin_walled").Get() is True
    assert mdl.GetInput("enable_diffuse_transmission").Get() is True
    tau = TURBID_TAU * 0.7**2.5  # 胴の中心を通る光の光学的な厚さ
    assert mdl.GetInput("specular_transmission_weight").Get() == pytest.approx(math.exp(-TURBID_CLARITY_K * tau),
                                                                               abs=1e-4)
    col = mdl.GetInput("diffuse_reflection_color").Get()
    assert col[0] > col[1] > col[2]  # オレンジ
    assert not mdl.GetInput("specular_transmission_scattering_color")
    # OpenPBR は体積散乱（散乱を追う描画器向け）
    pbr = UsdShade.Shader.Get(stage, mat.AppendChild("OpenPBR"))
    assert max(pbr.GetInput("transmission_scatter").Get()) > 0
    assert pbr.GetInput("transmission_scatter_anisotropy").Get() == pytest.approx(TURBID_ANISOTROPY)
    ps = [UsdShade.Shader(c) for c in stage.GetPrimAtPath(mat).GetChildren()
          if UsdShade.Shader(c) and UsdShade.Shader(c).GetIdAttr().Get() == "UsdPreviewSurface"]
    assert ps and ps[0].GetInput("opacity").Get() > 0.92


def test_clear_liquid_no_scatter(built):
    """澄んだ液体には散乱を書かない（今までと同じ見た目）。"""
    _, r = built
    stage = Usd.Stage.Open(str(r.usd_path))
    mdl = UsdShade.Shader.Get(stage, "/synthetic_bottle/_materials/LiquidMat/MDL")
    assert not mdl.GetInput("specular_transmission_scattering_color")
    assert "turbidity" not in r.meta["profile"]


def test_lid_top_image(tmp_path, bottle_png, blender):
    """vision.json の faces.top があれば、蓋の上面の円にだけその画像を貼る。"""
    lid = tmp_path / "lid.png"
    Image.fromarray(np.full((200, 200, 3), (200, 30, 30), np.uint8)).save(lid)
    spec = ProductSpec(product_name="カップ麺", slug="cup_with_lid", shape_class="revolve",
                       dimensions=Dimensions(H, D), mass_kg=0.1, container_material="paper")
    ctx = BuildContext(spec, [bottle_png, lid], 0, Landmarks(), tmp_path, tmp_path / "debug", blender,
                       faces={"top": 1})
    result = RevolveBuilder().build(ctx)
    assert "CapTopMat" in result.materials and (tmp_path / "textures" / "cap_top.png").exists()
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    subsets = UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(stage.GetPrimAtPath("/cup_with_lid/Cap")))
    top = [s for s in subsets if s.GetPrim().GetName() == "CapTopMat"]
    assert top and len(top[0].GetIndicesAttr().Get()) == 1  # 上面の円 1 枚だけ
    assert validate(result.usd_path, spec.dimensions).ok


def test_make_lid_texture():
    rgb = np.full((300, 400, 3), 255, np.uint8)
    rgb[50:250, 100:300] = (0, 0, 255)  # 白背景の上の蓋
    tex = make_lid_texture(rgb, "#00FF00", 0.05)
    n = tex.shape[0]
    assert tex.shape == (n, n, 3) and n == 256  # 直径 50 mm なら 512 だが、元の蓋は 200 px なので 256 で止める
    assert tuple(tex[0, 0]) == (0, 255, 0) and tuple(tex[n // 2, n // 2]) == (0, 0, 255)
