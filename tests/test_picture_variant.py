"""店向けの絵柄の Picture バリアント（Default = 絵柄、Blank = 無地）のテスト。"""

import numpy as np
import pytest
from PIL import Image
from pxr import Sdf, Usd, UsdGeom, UsdShade

from agentic_usd_gen.catalog import _picture, _picture_text
from agentic_usd_gen.fictional import store_env
from agentic_usd_gen.fictional.products import a_frame_sign
from agentic_usd_gen.nonvisual import BASE_ATTR
from agentic_usd_gen.picture import VARIANT_SET, picture_materials, write_picture_variant
from agentic_usd_gen.spec import Dimensions, Part, ProductSpec
from agentic_usd_gen.usd_post import _connect_maps, _setup_material, write_surface_maps


def _picture_stage(tmp_path):
    """ポスターの紙（絵柄と無地のテクスチャ・粗さなどのマップ付き）と枠のメッシュ。"""
    tex_dir = tmp_path / "textures"
    tex_dir.mkdir()
    img = np.full((32, 32, 3), 230, np.uint8)
    img[8:24, 8:24] = (200, 30, 30)  # 絵柄
    Image.fromarray(img).save(tex_dir / "Poster.png")
    Image.fromarray(np.full((32, 32, 3), 240, np.uint8)).save(tex_dir / "Poster_Blank.png")
    stage = Usd.Stage.CreateInMemory()
    root = stage.DefinePrim("/a", "Xform")
    params = {}
    for name in ("PosterMat", "FrameMat"):
        mat = UsdShade.Material.Define(stage, f"/a/_materials/{name}")
        ps = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Principled_BSDF"))
        ps.CreateIdAttr("UsdPreviewSurface")
        mat.CreateSurfaceOutput().ConnectToSource(ps.CreateOutput("surface", Sdf.ValueTypeNames.Token))
        p = {"role": "solid", "color": "#FFFFFF", "roughness": 0.8, "labels": ["paper"]}
        if name == "PosterMat":
            p.update(texture=str(tex_dir / "Poster.png"), texture_rel="./textures/Poster.png",
                     blank_texture=str(tex_dir / "Poster_Blank.png"), blank_texture_rel="./textures/Poster_Blank.png")
            write_surface_maps(p)
        _setup_material(mat, p)
        _connect_maps(mat, p)
        mat.GetPrim().CreateAttribute(BASE_ATTR, Sdf.ValueTypeNames.Token).Set("paper")
        params[name] = p
        mesh = UsdGeom.Mesh.Define(stage, f"/a/{name.removesuffix('Mat')}")
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    return stage, root, params


def _bound(stage, path):
    mat, _ = UsdShade.MaterialBindingAPI(stage.GetPrimAtPath(path)).ComputeBoundMaterial()
    return mat.GetPath().name


def _assets(prim):
    return {a.Get().path for p in Usd.PrimRange(prim) for a in p.GetAttributes()
            if a.GetTypeName() == Sdf.ValueTypeNames.Asset and a.HasAuthoredValue()}


def test_picture_variant_switches_binding(tmp_path):
    stage, root, params = _picture_stage(tmp_path)
    assert picture_materials(params) == ["PosterMat"]
    assert write_picture_variant(stage, root, params) == ["PosterMat"]

    vset = root.GetVariantSets().GetVariantSet(VARIANT_SET)
    assert vset.GetVariantNames() == ["Blank", "Default"] and vset.GetVariantSelection() == "Default"
    assert _bound(stage, "/a/Poster") == "PosterMat"
    vset.SetVariantSelection("Blank")
    assert _bound(stage, "/a/Poster") == "PosterMat_Blank"
    assert _bound(stage, "/a/Frame") == "FrameMat"
    assert "material:binding" not in stage.GetRootLayer().GetPrimAtPath("/a/Poster").relationships


def test_blank_material_uses_blank_textures(tmp_path):
    """Blank は元のマテリアルの写しで、色と粗さ・法線のテクスチャだけが無地のものになる。"""
    stage, root, params = _picture_stage(tmp_path)
    write_picture_variant(stage, root, params)
    on = _assets(stage.GetPrimAtPath("/a/_materials/PosterMat"))
    blank = _assets(stage.GetPrimAtPath("/a/_materials/PosterMat_Blank"))
    assert "./textures/Poster.png" in on and not any("Blank" in x for x in on)
    assert "./textures/Poster_Blank.png" in blank
    assert not any(x.removeprefix("./").startswith("textures/Poster.") or "/Poster_r" in x or "/Poster_n" in x
                   for x in blank)
    assert any("Poster_Blank_" in x for x in blank)  # 無地から作った粗さ・法線
    assert (tmp_path / "textures" / "Poster_Blank_roughness.png").exists()
    # 光学以外の属性もそのまま
    assert stage.GetPrimAtPath("/a/_materials/PosterMat_Blank").GetAttribute(BASE_ATTR).Get() == "paper"


def test_lit_sign_blank_beats_screen(tmp_path):
    """光る看板（Screen バリアントもある面）：Default は Screen の On / Off に従い、Blank はどちらでも無地。"""
    from agentic_usd_gen.screen import VARIANT_SET as SCREEN_SET
    from agentic_usd_gen.screen import write_screen_variant

    stage, root, params = _picture_stage(tmp_path)
    params["PosterMat"]["emissive"] = True
    assert write_screen_variant(stage, root, params) == ["PosterMat"]
    assert write_picture_variant(stage, root, params) == ["PosterMat"]
    assert root.GetVariantSets().GetNames()[:2] == [VARIANT_SET, SCREEN_SET]
    vs = root.GetVariantSets()
    seen = {}
    for screen in ("On", "Off"):
        for pic in ("Default", "Blank"):
            vs.SetSelection(SCREEN_SET, screen)
            vs.SetSelection(VARIANT_SET, pic)
            seen[screen, pic] = _bound(stage, "/a/Poster")
    assert seen == {("On", "Default"): "PosterMat", ("Off", "Default"): "PosterMat_Off",
                    ("On", "Blank"): "PosterMat_Blank", ("Off", "Blank"): "PosterMat_Blank"}
    assert _bound(stage, "/a/Frame") == "FrameMat"


def test_no_variant_without_blank(tmp_path):
    stage, root, params = _picture_stage(tmp_path)
    assert write_picture_variant(stage, root, {"FrameMat": params["FrameMat"]}) == []
    assert not root.GetVariantSets().HasVariantSet(VARIANT_SET)


def test_catalog_picture_info():
    info = _picture([{"material": "PosterMat", "image": "./textures/Poster.png",
                      "blank_image": "./textures/Poster_Blank.png"}], ["convenience_store"])
    assert info["variant_set"] == "Picture" and info["default"] == "Default" and info["off"] == "Blank"
    assert info["materials"] == [{"name": "PosterMat", "image": "./textures/Poster.png", "off": "PosterMat_Blank",
                                  "blank_image": "./textures/Poster_Blank.png"}]
    assert info["places"] == ["convenience_store"]
    assert "Blank = 無地" in _picture_text(info) and "convenience_store" in _picture_text(info)
    assert "places" not in _picture([{"material": "M", "image": "a", "blank_image": "b"}], [])


def _spec(**part):
    return ProductSpec(product_name="x", slug="x", shape_class="assembly", dimensions=Dimensions(0.1, 0.1),
                       parts=[Part(name="P", shape="box", size=[0.1, 0.01, 0.1], center=[0, 0, 0.05], **part)])


def test_spec_blank_checks():
    assert _spec(faces={"front": 0}, blank="#FFFFFF").parts[0].blank == "#FFFFFF"
    with pytest.raises(ValueError, match="faces"):
        _spec(blank="#FFFFFF")
    with pytest.raises(ValueError, match="RRGGBB"):
        _spec(faces={"front": 0}, blank="white")
    d = _spec(faces={"front": 0}, blank=1).to_dict()
    assert d["parts"][0]["blank"] == 1 and ProductSpec.from_dict(d).parts[0].blank == 1
    assert "blank" not in _spec(faces={"front": 0}).to_dict()["parts"][0]


@pytest.mark.parametrize("make", [store_env.wall_poster, store_env.window_poster, store_env.aisle_sign_hanging,
                                  store_env.entrance_mat, a_frame_sign])
def test_store_pictures_have_blank_and_places(make):
    """店の広告・メニュー・求人・あいさつの入った掲示物は、無地に切り替えられて、合う場所を書いてある。"""
    prod = make()
    spec = prod.spec()
    assert spec.picture_places and set(spec.picture_places) <= {"shop", "convenience_store", "supermarket", "cafe",
                                                                 "restaurant"}
    blanks = [p for p in spec.parts if p.faces and p.blank is not None]
    assert blanks
    for p in blanks:
        if isinstance(p.blank, int):
            assert 0 <= p.blank < len(prod.images) and p.blank not in p.faces.values()


def test_catalog_picture_text():
    info = _picture([{"material": "SignMat", "image": "a", "blank_image": "b", "text": ["メンズ トップス", "MEN'S TOPS"],
                      "lang": "ja", "audience": ["men"]}], [])
    m = info["materials"][0]
    assert m["text"] == ["メンズ トップス", "MEN'S TOPS"] and m["lang"] == "ja" and m["audience"] == ["men"]
    assert "文字「メンズ トップス / MEN'S TOPS」" in _picture_text(info)


def test_sign_text_recorded_from_canvas(tmp_path):
    """看板に Canvas.text で描いた文字が、画像の隣の NN.text.json から絵柄のマテリアルに渡る。"""
    import json

    from agentic_usd_gen.fictional import apparel_fixtures
    from agentic_usd_gen.fictional.base import audience_of, lang_of, write
    from agentic_usd_gen.fictional.paint import Canvas, recording
    from agentic_usd_gen.shapes.assembly import picture_words

    with recording() as canvases:
        prod = apparel_fixtures.folded_wall_shelf()
    cache = write(prod, tmp_path, canvases)
    side = cache / "images" / "00.text.json"
    d = json.loads(side.read_text(encoding="utf-8"))
    assert "メンズ トップス" in d["text"] and d["lang"] == "ja" and d["audience"] == ["men"]
    assert picture_words([cache / "images" / "00.png"]) == d
    # 文字の無い画像・記録しないで書いたときは何も書かない（前回の分は消す）
    write(prod, tmp_path)
    assert not side.exists() and picture_words([cache / "images" / "00.png"]) == {}
    # 縦書きは 1 行、バーコードの数字は残さない
    c = Canvas(40, 120)
    c.vtext(20, 10, "おすすめ", 8)
    c.barcode(2, 90, 36, 20, "4901234567894")
    assert c.texts == ["おすすめ"]
    assert lang_of(["SALE"]) == "en" and audience_of(["KIDS & BABY"]) == ["kids", "baby"]
    assert audience_of(["レディース"]) == ["women"] and audience_of(["MENS"]) == ["men"]
    assert audience_of(["レディース", "WOMEN'S"]) == ["women"] and audience_of(["WOMENSWEAR"]) == []


@pytest.mark.parametrize("slug", ["gondola_shelf", "gondola_shelf_food", "gondola_shelf_daily", "gondola_shelf_bakery"])
def test_gondola_header_can_be_blank(slug):
    """ゴンドラの天板の売り場の表示（「お菓子・スナック」等）は無地にでき、合う店を書いてある（酒屋に出ていた）。"""
    from agentic_usd_gen.fictional import products

    spec = products.PRODUCTS[slug]().spec()
    header = next(p for p in spec.parts if p.name == "Header")
    assert header.blank == "#1F6F5C" and header.faces
    assert spec.picture_places == products.GONDOLA_PLACES[slug]
    assert "liquor_store" not in spec.picture_places


def test_reach_in_cooler_header_can_be_blank():
    """冷蔵ケースの看板（「冷たいお飲み物」）は無地にでき、清涼飲料を売らない店は合う店に入れない。"""
    from agentic_usd_gen.fictional import store_floor

    spec = store_floor.reach_in_cooler_3door().spec()
    header = next(p for p in spec.parts if p.name == "Header")
    assert header.blank == "#1C5FA8" and header.faces
    assert spec.picture_places == store_floor.COOLER_PLACES
    assert not {"liquor_store", "greengrocer", "florist"} & set(spec.picture_places)
