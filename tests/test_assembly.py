"""部品の組み合わせ（assembly）のテスト。"""

import math

import numpy as np
import pytest
from PIL import Image
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

from agentic_usd_gen.shapes.assembly import (AssemblyBuilder, cylinder_mesh, object_name, part_volume, prism_mesh,
                                    prism_outline, revolve_mesh, rotation_matrix, torus_mesh)
from agentic_usd_gen.shapes.revolve import BuildContext
from agentic_usd_gen.spec import Dimensions, Joint, Part, ProductSpec
from agentic_usd_gen.usd_post import _preview_shader, postprocess
from agentic_usd_gen.validate import validate
from agentic_usd_gen.vision import Landmarks


def test_rotation_matrix():
    R = rotation_matrix([90, 0, 0])
    assert np.allclose(R @ [0, 1, 0], [0, 0, 1])
    assert np.allclose(rotation_matrix([0, 0, 90]) @ [1, 0, 0], [0, 1, 0])


def test_cylinder_mesh():
    m = cylinder_mesh(0.02, 0.02, 0.1, n=16)
    v = np.asarray(m["vertices"])
    assert len(m["faces"]) == 18 and np.isclose(v[:, 0].max(), 0.01) and np.isclose(v[:, 2].max(), 0.1)


def test_torus_mesh():
    m = torus_mesh(0.34, 0.34, 0.02, n=32, m=8)
    v = np.asarray(m["vertices"])
    assert len(m["faces"]) == 32 * 8
    assert np.isclose(np.hypot(v[:, 0], v[:, 1]).max(), 0.17) and np.isclose(v[:, 2].min(), 0) and np.isclose(v[:, 2].max(), 0.02)
    vol = part_volume(Part("Ring", "torus", [0.34, 0.34, 0.02], [0, 0, 0]))
    assert np.isclose(vol, 2 * np.pi ** 2 * 0.16 * 0.01 ** 2)


def test_revolve_mesh():
    prof = [[0, 0], [1, 0], [0.5, 0.5], [1, 1], [0, 1]]
    m = revolve_mesh(0.04, 0.04, 0.1, prof, n=16)
    v = np.asarray(m["vertices"])
    assert len(v) == 2 + 3 * 16  # 両端は 1 点に閉じる
    assert len(m["faces"]) == 16 * 4  # 三角形の扇 2 つ + 四角形の帯 2 つ
    assert np.isclose(v[:, 0].max(), 0.02) and np.isclose(v[:, 2].max(), 0.1)
    # 端が閉じていない（半径 0 でない）ときは平らな面でふさぐ
    assert len(revolve_mesh(0.04, 0.04, 0.1, [[1, 0], [1, 1]], n=16)["faces"]) == 18
    cyl = part_volume(Part("C", "revolve", [0.04, 0.04, 0.1], [0, 0, 0], profile=[[1, 0], [1, 1]]))
    assert np.isclose(cyl, np.pi * 0.02 ** 2 * 0.1)


def test_prism_mesh():
    # 既定の断面は角の丸い二等辺三角形で、外形は幅 × 高さにちょうど収まる
    ol = prism_outline(0.10, 0.09)
    assert np.isclose(ol[:, 0].min(), -0.05) and np.isclose(ol[:, 0].max(), 0.05)
    assert np.isclose(ol[:, 1].min(), 0) and np.isclose(ol[:, 1].max(), 0.09)
    m = prism_mesh(0.10, 0.04, 0.09)
    v, n = np.asarray(m["vertices"]), len(ol)
    assert len(v) == 2 * n and len(m["faces"]) == n + 2  # 側面の帯 + 前後の断面
    assert np.isclose(v[:, 1].min(), -0.02) and np.isclose(v[:, 1].max(), 0.02)
    assert len(m["uvs"]) == len(m["faces"])
    # 角を丸めない長方形の断面なら体積は箱と同じ。丸めた三角形は外形を size に合わせて伸ばすので、三角形と箱の間
    rect = [[-0.5, 0, 0], [0.5, 0, 0], [0.5, 1, 0], [-0.5, 1, 0]]
    assert np.isclose(part_volume(Part("R", "prism", [0.1, 0.04, 0.09], [0, 0, 0], profile=rect)), 0.1 * 0.04 * 0.09)
    tri = part_volume(Part("T", "prism", [0.1, 0.04, 0.09], [0, 0, 0]))
    assert 0.1 * 0.09 / 2 * 0.04 < tri < 0.7 * 0.1 * 0.09 * 0.04


def test_revolve_needs_profile(tmp_path):
    spec = ProductSpec(product_name="テストびん", slug="test_bottle", shape_class="assembly",
                       dimensions=Dimensions(0.1, 0.04), parts=[Part("Bottle", "revolve", [0.04, 0.04, 0.1], [0, 0, 0.05])])
    ctx = BuildContext(spec, [], 0, Landmarks(), tmp_path, tmp_path / "debug", None)
    with pytest.raises(ValueError, match="profile"):
        AssemblyBuilder().build(ctx)


def test_object_name():
    used = set()
    assert object_name("画面", used) == "Part"
    assert object_name("base-plate", used) == "base_plate"
    assert object_name("base plate", used) == "base_plate_2"
    assert object_name("2nd", used) == "P_2nd"


def _kiosk(tmp_path, static):
    img_path = tmp_path / "screen.png"
    Image.fromarray(np.full((90, 160, 3), (20, 60, 200), np.uint8)).save(img_path)
    parts = [
        Part("Base", "box", [0.4, 0.3, 0.05], [0, 0, 0.025], color="#333333", finish="metal"),
        Part("Pole", "cylinder", [0.05, 0.05, 1.0], [0, 0, 0.55], color="#888888"),
        # 正面に 15° 傾けた画面。front に画像を貼る
        Part("Screen", "box", [0.32, 0.02, 0.18], [0, 0, 1.1], rotation=[-15, 0, 0], color="#111111",
             finish="glossy", faces={"front": 0, "back": None}),
    ]
    H = 1.1 + 0.5 * (0.18 * np.cos(np.radians(15)) + 0.02 * np.sin(np.radians(15)))
    spec = ProductSpec(product_name="テスト端末", slug="test_kiosk", shape_class="assembly",
                       dimensions=Dimensions(H, 0.4, depth=0.3), mass_kg=12.0, category="fixture",
                       parts=parts, static=static)
    out = tmp_path / "out"
    return BuildContext(spec, [img_path], 0, Landmarks(), out, out / "debug", None), spec


def test_build_static(tmp_path, blender):
    ctx, spec = _kiosk(tmp_path, static=True)
    ctx.blender = blender
    result = AssemblyBuilder().build(ctx)
    assert result.static and result.colliders == ["Base", "Pole", "Screen"]
    assert (ctx.out_dir / "textures" / "Screen.png").exists()
    assert not result.meta["warnings"], result.meta["warnings"]
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"],
                   static=True)
    assert rep.ok, rep.errors
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    # 床に固定するキネマティックな剛体（SimReady の RB.001）。質量も書く（RB.007）
    assert root.HasAPI(UsdPhysics.RigidBodyAPI) and UsdPhysics.MassAPI(root).GetMassAttr().Get() == 12.0
    assert UsdPhysics.RigidBodyAPI(root).GetKinematicEnabledAttr().Get()
    assert stage.GetPrimAtPath("/test_kiosk/Screen").HasAPI(UsdPhysics.CollisionAPI)
    labels = {p.GetName(): list(p.GetAttribute("semantics:labels:material").Get())
              for p in stage.GetPrimAtPath("/test_kiosk/_materials").GetChildren()}
    assert labels == {"BaseMat": ["metal"], "PoleMat": ["plastic"], "ScreenMat": ["plastic"],
                      "PhysicsMaterial": ["metal"], "PhysicsMaterial_plastic": ["plastic"]}
    # 素材の違う部品は別の物理マテリアル（金属の台座と樹脂の支柱・画面）
    def phys(name):
        prim = stage.GetPrimAtPath(f"/test_kiosk/{name}")
        return UsdShade.MaterialBindingAPI(prim).GetDirectBinding("physics").GetMaterialPath().name
    assert [phys(n) for n in ("Base", "Pole", "Screen")] == ["PhysicsMaterial", "PhysicsMaterial_plastic",
                                                              "PhysicsMaterial_plastic"]
    pm = {m["name"]: m for m in result.meta["physics_materials"]}
    assert pm["PhysicsMaterial"]["static_friction"] == 0.30 and pm["PhysicsMaterial_plastic"]["colliders"] == ["Pole", "Screen"]


def test_build_dynamic(tmp_path, blender):
    ctx, spec = _kiosk(tmp_path, static=False)
    ctx.blender = blender
    result = AssemblyBuilder().build(ctx)
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"])
    assert rep.ok, rep.errors
    assert 0 < result.center_of_mass[2] < spec.dimensions.height / 2  # 重い台座で重心が低い
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    assert root.HasAPI(UsdPhysics.RigidBodyAPI) and not UsdPhysics.RigidBodyAPI(root).GetKinematicEnabledAttr().Get()


def test_glass_finish(tmp_path, blender):
    """finish が glass の部品は透明マテリアル（OmniGlass）になる。"""
    ctx, spec = _kiosk(tmp_path, static=True)
    ctx.blender = blender
    spec.parts[0].finish = "glass"
    result = AssemblyBuilder().build(ctx)
    assert result.materials["BaseMat"]["role"] == "glass"
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    mdl = stage.GetPrimAtPath("/test_kiosk/_materials/BaseMat/MDL")
    assert mdl and mdl.GetAttribute("info:mdl:sourceAsset").Get().path == "OmniGlass.mdl"
    # 透明な部品だけに agenticUsdGen:transparency が付き、meta にも残る
    marked = result.meta["transparency"]
    assert set(marked.values()) == {"transparent"}
    for path in marked:
        prim = stage.GetPrimAtPath(f"/test_kiosk/{path}")
        assert prim.GetAttribute("agenticUsdGen:transparency").Get() == "transparent"
        assert UsdGeom.PrimvarsAPI(prim).GetPrimvar("doNotCastShadows").Get() is True
    opaque = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh) and str(p.GetPath())[len("/test_kiosk/"):] not in marked]
    assert opaque and all(not p.GetAttribute("agenticUsdGen:transparency") for p in opaque)
    assert mdl.GetAttribute("inputs:thin_walled").Get() is False  # 既定は中身の詰まった塊（屈折する）


def test_glass_thin_walled(tmp_path, blender):
    """thin_walled を付けた glass の部品は薄い膜（屈折しない）になる。PET のフタ・ブリスター・包装フィルム用。"""
    ctx, spec = _kiosk(tmp_path, static=True)
    ctx.blender = blender
    spec.parts[0].finish = "glass"
    spec.parts[0].thin_walled = True
    result = AssemblyBuilder().build(ctx)
    assert result.materials["BaseMat"]["thin_walled"] is True
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    mdl = stage.GetPrimAtPath("/test_kiosk/_materials/BaseMat/MDL")
    assert mdl.GetAttribute("inputs:thin_walled").Get() is True


@pytest.mark.parametrize("finish", ["frosted", "translucent"])
def test_translucent_finish(tmp_path, blender, finish):
    """finish が frosted / translucent の部品は半透明の膜（OmniSurface の thin_walled + 拡散透過）になる。"""
    ctx, spec = _kiosk(tmp_path, static=True)
    ctx.blender = blender
    spec.parts[0].finish = finish
    result = AssemblyBuilder().build(ctx)
    assert result.materials["BaseMat"]["role"] == "translucent"
    postprocess(result, spec.product_name)
    stage = Usd.Stage.Open(str(result.usd_path))
    mdl = UsdShade.Shader.Get(stage, "/test_kiosk/_materials/BaseMat/MDL")
    assert mdl.GetSourceAssetSubIdentifier("mdl") == "OmniSurface"
    assert mdl.GetInput("thin_walled").Get() is True
    assert mdl.GetInput("enable_diffuse_transmission").Get() is True
    clarity = mdl.GetInput("specular_transmission_weight").Get()
    assert 0 < clarity < 1
    preview = _preview_shader(UsdShade.Material.Get(stage, "/test_kiosk/_materials/BaseMat"))
    assert 0 < preview.GetInput("opacity").Get() < 1  # UsdPreviewSurface はオパシティで近似
    assert result.meta["transparency"] and set(result.meta["transparency"].values()) == {"translucent"}
    # 半透明の部品は影を落とす（doNotCastShadows を付けない）
    assert not any(UsdGeom.PrimvarsAPI(stage.GetPrimAtPath(f"/test_kiosk/{p}")).HasPrimvar("doNotCastShadows")
                   for p in result.meta["transparency"])


def test_collision_approximation(tmp_path, blender):
    """部品ごとにコリジョンの近似方法を選べる。指定のない部品は convexHull のまま。"""
    ctx, spec = _kiosk(tmp_path, static=False)
    ctx.blender = blender
    spec.parts[0].collision_approximation = "convexDecomposition"  # 部品の指定
    spec.collision_approximation = {"Pole": "meshSimplification", "Nothing": "boundingCube"}  # 全体の指定
    result = AssemblyBuilder().build(ctx)
    postprocess(result, spec.product_name, collision=spec.collision_approximations())
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"])
    assert rep.ok, rep.errors
    stage = Usd.Stage.Open(str(result.usd_path))
    approx = {n: UsdPhysics.MeshCollisionAPI(stage.GetPrimAtPath(f"/test_kiosk/{n}")).GetApproximationAttr().Get()
              for n in ("Base", "Pole", "Screen")}
    assert approx == {"Base": "convexDecomposition", "Pole": "meshSimplification", "Screen": "convexHull"}
    assert rep.info["collision_approximations"] == approx
    # 動く剛体の meshSimplification と、ない部品名は警告する
    assert any("meshSimplification" in w for w in rep.warnings)
    assert any("Nothing" in w for w in result.meta["warnings"])


@pytest.mark.parametrize("static", [False, True])
def test_build_links(tmp_path, blender, static):
    """link の付いた部品（画面）は別の剛体になり、回転の関節で本体につながる（SimReady の FET_004）。"""
    ctx, spec = _kiosk(tmp_path, static=static)
    ctx.blender = blender
    spec.parts[2].link = "ScreenLink"
    spec.joints = [Joint(link="ScreenLink", anchor=[0, 0, 1.03], limits=[-30.0, 15.0], axis="X")]
    result = AssemblyBuilder().build(ctx)
    (link,) = result.links
    assert link["parts"] == ["Screen"] and 0 < link["mass"] < 12.0
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"],
                   static=static)
    assert rep.ok, rep.errors
    assert rep.info["links"] == ["ScreenLink"]

    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    screen = stage.GetPrimAtPath("/test_kiosk/ScreenLink/Screen")
    assert screen and not stage.GetPrimAtPath("/test_kiosk/Screen")
    assert screen.HasAPI(UsdPhysics.CollisionAPI)
    body = stage.GetPrimAtPath("/test_kiosk/ScreenLink")
    assert body.HasAPI(UsdPhysics.RigidBodyAPI) and not UsdPhysics.RigidBodyAPI(body).GetKinematicEnabledAttr().Get()
    # 総質量は本体と可動部で分ける
    masses = [UsdPhysics.MassAPI(p).GetMassAttr().Get() for p in (root, body)]
    assert sum(masses) == pytest.approx(12.0, rel=1e-5)
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/test_kiosk/ScreenLink/Joint"))
    assert joint.GetBody0Rel().GetTargets() == [root.GetPath()]
    assert joint.GetBody1Rel().GetTargets() == [body.GetPath()]
    assert joint.GetAxisAttr().Get() == "X"
    assert (joint.GetLowerLimitAttr().Get(), joint.GetUpperLimitAttr().Get()) == (-30.0, 15.0)
    # 蝶番の位置は両方の剛体で同じ（可動部の Xform は変換なし）
    assert joint.GetLocalPos0Attr().Get() == joint.GetLocalPos1Attr().Get()
    assert joint.GetLocalPos0Attr().Get()[2] == pytest.approx(1.03, abs=1e-5)
    # キネマティックな本体（什器）にはアーティキュレーションを付けない（JT.ART.003）
    assert root.HasAPI(UsdPhysics.ArticulationRootAPI) is not static
    assert result.meta["joints"][0]["link"] == "ScreenLink"


def test_dome_mesh_top_projection():
    """dome 部品の top の画像は、真上から山の面に投影する（正面 -Y 側が画像の下、底面は塗りつぶしのセル）。"""
    from agentic_usd_gen.shapes.assembly import dome_mesh
    from agentic_usd_gen.shapes.box import FACES, cell_uv
    m = dome_mesh(0.10, 0.06, 0.03, 2.0, atlas=True)
    u0, v0, u1, v1 = cell_uv(FACES.index("top"))
    uv = {tuple(v): tuple(t) for f, us in zip(m["faces"][:-1], m["uvs"][:-1]) for v, t in zip((m["vertices"][i] for i in f), us)}
    top = uv[(0.0, 0.0, 0.03)]
    assert top == pytest.approx(((u0 + u1) / 2, (v0 + v1) / 2))
    front = min(uv, key=lambda v: v[1])  # いちばん手前の点は画像の下端
    assert uv[front][1] == pytest.approx(v0, abs=1e-6)
    assert len(m["uvs"]) == len(m["faces"])


def test_dome_mesh_arc_uv():
    """bread の山は頂点からの道のりで貼る：頂点が画像の中心、底の輪が画像に内接する楕円、中腹の輪は真上からより内側。"""
    from agentic_usd_gen.shapes.assembly import dome_mesh
    from agentic_usd_gen.shapes.box import FACES, cell_uv
    u0, v0, u1, v1 = cell_uv(FACES.index("top"))
    cu, cv, hu, hv = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2, (v1 - v0) / 2
    arc = dome_mesh(0.10, 0.06, 0.04, 2.2, atlas=True, arc=True)
    flat = dome_mesh(0.10, 0.06, 0.04, 2.2, atlas=True)
    radius = {}
    for name, m in (("arc", arc), ("flat", flat)):
        uv = {tuple(v): tuple(t) for f, us in zip(m["faces"][:-1], m["uvs"][:-1])
              for v, t in zip((m["vertices"][i] for i in f), us)}
        radius[name] = {v: math.hypot((t[0] - cu) / hu, (t[1] - cv) / hv) for v, t in uv.items()}
    assert radius["arc"][(0.0, 0.0, 0.04)] == pytest.approx(0.0, abs=1e-9)
    bottom = [v for v in radius["arc"] if v[2] == 0.0]
    assert all(radius["arc"][v] == pytest.approx(1.0, abs=1e-6) for v in bottom)
    mid = [v for v in radius["arc"] if 0.015 < v[2] < 0.03]
    assert mid and all(radius["arc"][v] < radius["flat"][v] for v in mid)  # 側面に画像の縁の細い帯だけが伸びない


def test_part_variants(tmp_path, blender):
    """variant_sets と部品の show で部品を出し入れするバリアントが付き、asset.json の variants に書き出す。"""
    from agentic_usd_gen.catalog import build_asset_json

    ctx, spec = _kiosk(tmp_path, static=True)
    ctx.blender = blender
    spec.variant_sets = {"Model": ["Screen", "Plain"]}
    spec.parts[2].show = {"Model": ["Screen"]}
    result = AssemblyBuilder().build(ctx)
    postprocess(result, spec.product_name)
    assert result.meta["variants"]["Model"]["parts"] == {"Screen": ["Screen"], "Plain": []}
    stage = Usd.Stage.Open(str(result.usd_path))
    root = stage.GetDefaultPrim()
    screen = UsdGeom.Imageable(stage.GetPrimAtPath("/test_kiosk/Screen"))
    assert root.GetVariantSet("Model").GetVariantSelection() == "Screen"
    assert screen.ComputeVisibility() == UsdGeom.Tokens.inherited
    root.GetVariantSet("Model").SetVariantSelection("Plain")
    assert screen.ComputeVisibility() == UsdGeom.Tokens.invisible
    meta = {"spec": spec.to_dict(), "validation": {"info": {}}, "variants": result.meta["variants"],
            "product_name": spec.product_name, "mass_kg": 12.0, "center_of_mass": [0, 0, 0.3]}
    asset = build_asset_json(meta, "test_kiosk", "fixture", 0.0)
    assert asset["variants"] == {"Model": {"variants": ["Screen", "Plain"], "default": "Screen"}}
