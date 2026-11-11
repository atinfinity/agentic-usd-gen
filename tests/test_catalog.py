"""アセット書き出し（モデルカード・サムネイル・一覧）のテスト。"""

import json

import numpy as np
import pytest
from PIL import Image
from pxr import Usd, UsdPhysics, UsdSemantics

from agentic_usd_gen.catalog import main as export_main
from agentic_usd_gen.shapes.box import BoxBuilder
from agentic_usd_gen.shapes.revolve import BuildContext
from agentic_usd_gen.spec import Dimensions, ProductSpec
from agentic_usd_gen.usd_post import postprocess
from agentic_usd_gen.validate import validate
from agentic_usd_gen.vision import Landmarks


def _make_asset(tmp_path, blender):
    cache = tmp_path / "cache" / "合成の箱"
    (cache / "images").mkdir(parents=True)
    img = np.full((300, 200, 3), (200, 40, 40), np.uint8)
    Image.fromarray(img).save(cache / "images" / "00.png")
    spec = ProductSpec(product_name="合成の箱", slug="synthetic_box", shape_class="box",
                       dimensions=Dimensions(0.15, 0.10, depth=0.03), mass_kg=0.05, category="food")
    spec.save(cache / "spec.json")
    out = tmp_path / "out" / spec.slug
    ctx = BuildContext(spec, [cache / "images" / "00.png"], 0, Landmarks(), out, out / "debug", blender)
    result = BoxBuilder().build(ctx)
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"])
    Image.new("RGBA", (512, 512), (0, 0, 0, 0)).save(out / "debug" / "thumbnail.png")  # 描画は省略
    meta = {"product_name": spec.product_name, "cache_dir": str(cache), "spec": spec.to_dict(),
            "image_used": None, "mass_kg": result.mass, "center_of_mass": result.center_of_mass,
            "physics": True, "physics_materials": result.meta["physics_materials"], "model": "test", "warnings": [],
            "validation": {"ok": rep.ok, "errors": rep.errors, "info": rep.info}}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False))
    return out


def test_export(tmp_path, blender):
    _make_asset(tmp_path, blender)
    assets, recipes = tmp_path / "assets", tmp_path / "recipes"
    export_main(["--out", str(tmp_path / "out"), "--assets", str(assets), "--recipes", str(recipes)])

    d = assets / "food" / "synthetic_box" / "simready_usd"
    for name in ("synthetic_box.usd", "textures/label.png", "thumbnail.png", "README.md", "asset.json",
                 ".thumbs/256x256/synthetic_box.usd.png"):
        assert (d / name).exists(), name
    assert Image.open(d / ".thumbs/256x256/synthetic_box.usd.png").size == (256, 256)
    asset = json.loads((d / "asset.json").read_text())
    assert asset["size_m"] == [0.1, 0.03, 0.15]
    assert "合成の箱" in (d / "README.md").read_text()
    # Isaac Sim のレイヤー構成（FET_100_ISAAC）。入口から読み込むと形状と物理がそろう
    assert asset["layers"] == {r: f"payloads/synthetic_box_{r}.usd" for r in ("base", "meshes", "physics")}
    assert all((d / p).exists() for p in asset["layers"].values())
    entry = Usd.Stage.Open(str(d / "synthetic_box.usd"))
    assert entry.GetRootLayer().customLayerData["SimReady_Metadata"]
    body = entry.GetPrimAtPath("/synthetic_box/Body")
    assert body.HasAPI(UsdPhysics.CollisionAPI) and Usd.ModelAPI(entry.GetDefaultPrim()).GetKind() == "component"
    assert "payloads/" in (d / "README.md").read_text()
    # 摩擦・反発は素材（紙箱）の値と根拠をカードと asset.json に書く
    phys = asset["physics"]
    assert phys["materials"][0]["material"] == "paper" and phys["static_friction"] == 0.5
    assert phys["materials"][0]["colliders"] == ["Body"] and "friction_source" in phys
    assert "摩擦・反発係数の根拠" in (d / "README.md").read_text()
    assert json.loads((assets / "catalog.json").read_text())[0]["path"] == "food/synthetic_box/simready_usd"

    # 一覧のステージから参照とテクスチャが解決できる
    stage = Usd.Stage.Open(str(assets / "catalog.usda"))
    assert stage.GetPrimAtPath("/Catalog/synthetic_box/Body").IsValid()

    v = json.loads((recipes / "合成の箱" / "spec.json").read_text())
    assert v["category"] == "food"

    # カテゴリを変えて書き出し直すと古い場所は消える
    spec_path = tmp_path / "cache" / "合成の箱" / "spec.json"
    s = json.loads(spec_path.read_text())
    s["category"] = "household"
    spec_path.write_text(json.dumps(s, ensure_ascii=False))
    export_main(["--out", str(tmp_path / "out"), "--assets", str(assets)])
    assert not d.parent.exists() and (assets / "household" / "synthetic_box" / "simready_usd" / "asset.json").exists()


def test_simready_metadata(tmp_path, blender):
    """SimReady の SR.004: ルートレイヤーの customLayerData に SimReady_Metadata を書く。"""
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    export_main(args + ["--author", "テスト"])
    d = assets / "food" / "synthetic_box" / "simready_usd"
    a = json.loads((d / "asset.json").read_text())
    stage = Usd.Stage.Open(str(d / "synthetic_box.usd"))
    md = stage.GetRootLayer().customLayerData["SimReady_Metadata"]
    assert md["author"] == "テスト" and md["asset_name"] == "synthetic_box" and md["asset_type"] == "prop"
    assert md["asset_license"] == "proprietary" and md["category"] == "food"
    assert md["source_file"] == "合成の箱/spec.json" and md["usd_date_generated"] == a["generated_at"][:10]
    assert md["qcode"] == a["qcode"] == "Q2095"  # 表にない slug は食品の既定値
    assert md["rigid_body_count"] == 1 and isinstance(md["rigid_body_count"], int)
    assert list(md["asset_extents"]) == pytest.approx([0.1, 0.03, 0.15])
    assert md["mass"] == pytest.approx(0.05)

    # spec.json の qcode が優先され、author は引き継ぐ
    spec_path = tmp_path / "cache" / "合成の箱" / "spec.json"
    s = json.loads(spec_path.read_text())
    s["qcode"] = "Q1361086"
    spec_path.write_text(json.dumps(s, ensure_ascii=False))
    export_main(args)
    stage = Usd.Stage.Open(str(d / "synthetic_box.usd"))
    md = stage.GetRootLayer().customLayerData["SimReady_Metadata"]
    assert md["qcode"] == "Q1361086" and md["author"] == "テスト"


def test_migrates_old_layout(tmp_path, blender):
    """旧構成（<category>/<slug>/asset.json）の書き出しは消し、版を引き継ぐ。"""
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    old = assets / "food" / "synthetic_box"
    old.mkdir(parents=True)
    (old / "asset.json").write_text(json.dumps({"version": "1.2.0", "history": [], "author": "前の人",
                                                  "size_m": [0.1, 0.03, 0.15]}))
    (old / "synthetic_box.usd").write_text("#usda 1.0\n")
    export_main(["--out", str(tmp_path / "out"), "--assets", str(assets)])
    assert not (old / "synthetic_box.usd").exists() and not (old / "asset.json").exists()
    a = json.loads((old / "simready_usd" / "asset.json").read_text())
    assert a["version"] == "1.3.0" and a["author"] == "前の人"


def test_versioning(tmp_path, blender):
    out = _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    asset_json = assets / "food" / "synthetic_box" / "simready_usd" / "asset.json"

    export_main(args)
    a = json.loads(asset_json.read_text())
    assert a["version"] == "1.0.0" and a["history"][0]["changes"] == ["初版"]
    usd = asset_json.parent / "synthetic_box.usd"
    assert Usd.ModelAPI(Usd.Stage.Open(str(usd)).GetDefaultPrim()).GetAssetVersion() == "1.0.0"

    # 中身が同じなら版も履歴も変わらない
    export_main(args + ["-m", "無視される"])
    b = json.loads(asset_json.read_text())
    assert b["version"] == "1.0.0" and len(b["history"]) == 1 and b["generated_at"] == a["generated_at"]

    # テクスチャだけ変われば minor
    Image.fromarray(np.zeros((8, 8, 3), np.uint8)).save(out / "textures" / "label.png")
    export_main(args + ["-m", "ラベルを差し替え"])
    c = json.loads(asset_json.read_text())
    assert c["version"] == "1.1.0"
    assert c["history"][0]["changes"] == ["ラベルを差し替え", "テクスチャを更新"]
    assert "## 更新履歴" in (asset_json.parent / "README.md").read_text()

    # 外形が変われば major
    meta = json.loads((out / "meta.json").read_text())
    meta["validation"]["info"]["bbox_max"][2] += 0.01
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False))
    Image.fromarray(np.ones((8, 8, 3), np.uint8)).save(out / "textures" / "label.png")
    export_main(args)
    d = json.loads(asset_json.read_text())
    assert d["version"] == "2.0.0" and len(d["history"]) == 3
    assert any(ch.startswith("外形") for ch in d["history"][0]["changes"])


def test_search_metadata(tmp_path, blender):
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    asset_json = assets / "food" / "synthetic_box" / "simready_usd" / "asset.json"
    export_main(args)

    # tags は cache の spec.json に書き足せば、作り直さずに反映される（版は minor が上がる）
    spec_path = tmp_path / "cache" / "合成の箱" / "spec.json"
    s = json.loads(spec_path.read_text())
    s["tags"] = ["チョコ", "snack", "food"]
    spec_path.write_text(json.dumps(s, ensure_ascii=False))
    export_main(args)
    a = json.loads(asset_json.read_text())
    assert a["tags"][:4] == ["food", "食品", "box", "箱"] and a["tags"].count("food") == 1
    assert "チョコ" in a["tags"] and "snack" in a["tags"]
    assert a["description"].startswith("合成の箱（食品）の 3D モデル。")
    assert a["version"] == "1.1.0" and a["history"][0]["changes"] == ["検索用メタデータ（タグ・説明）を更新"]
    assert "| タグ |" in (asset_json.parent / "README.md").read_text()

    stage = Usd.Stage.Open(str(asset_json.parent / "synthetic_box.usd"))
    prim = stage.GetDefaultPrim()
    info = prim.GetAssetInfo()
    assert info["displayName"] == "合成の箱" and info["category"] == "food" and "チョコ" in list(info["tags"])
    assert prim.GetDisplayName() == "合成の箱" and prim.GetDocumentation() == a["description"]
    assert prim.GetAttribute("semantic:Semantics:params:semanticType").Get() == "class"
    assert prim.GetAttribute("semantic:Semantics:params:semanticData").Get() == "food"
    legacy = {prim.GetAttribute(n.replace("Type", "Data")).Get() for n in prim.GetPropertyNames()
              if n.endswith(":params:semanticType") and prim.GetAttribute(n).Get() == "tag"}
    assert legacy == set(a["tags"])
    assert list(UsdSemantics.LabelsAPI(prim, "class").GetLabelsAttr().Get()) == ["food"]
    assert list(UsdSemantics.LabelsAPI(prim, "tag").GetLabelsAttr().Get()) == a["tags"]


def test_license(tmp_path, blender):
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    asset_json = assets / "food" / "synthetic_box" / "simready_usd" / "asset.json"
    export_main(args)
    assert json.loads(asset_json.read_text())["license"] is None

    export_main(args + ["--license", "CC0-1.0"])
    usd = Usd.Stage.Open(str(asset_json.parent / "synthetic_box.usd"))
    assert usd.GetDefaultPrim().GetAssetInfoByKey("license") == "CC0-1.0"

    # 次の書き出しでは指定しなくても引き継ぐ。ライセンスだけでは版は上がらない
    export_main(args)
    d = json.loads(asset_json.read_text())
    assert d["license"] == "CC0-1.0" and d["version"] == "1.0.0"


def test_license_from_repo(tmp_path, blender):
    """新しいアセットは --license を付け忘れても、書き出し先の他のアセットと同じライセンスになる。"""
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    asset_json = assets / "food" / "synthetic_box" / "simready_usd" / "asset.json"
    # CC0 の既存アセット（別の slug）だけがある書き出し先を作る
    export_main(args + ["--license", "CC0-1.0"])
    other = assets / "food" / "other_box"
    asset_json.parents[1].rename(other)
    a = json.loads((other / "simready_usd" / "asset.json").read_text())
    (other / "simready_usd" / "asset.json").write_text(json.dumps({**a, "slug": "other_box"}))
    export_main(args)
    assert json.loads(asset_json.read_text())["license"] == "CC0-1.0"
    usd = Usd.Stage.Open(str(asset_json.parent / "synthetic_box.usd"))
    assert usd.GetDefaultPrim().GetAssetInfoByKey("license") == "CC0-1.0"


def test_front(tmp_path, blender):
    """正面の向き（front）は既定で -Y。spec.json で上書きでき、変われば版が上がる。"""
    _make_asset(tmp_path, blender)
    assets = tmp_path / "assets"
    args = ["--out", str(tmp_path / "out"), "--assets", str(assets)]
    asset_json = assets / "food" / "synthetic_box" / "simready_usd" / "asset.json"
    export_main(args)
    a = json.loads(asset_json.read_text())
    assert a["front"] == "-Y" and a["version"] == "1.0.0"
    assert "| 正面の向き | `-Y` |" in (asset_json.parent / "README.md").read_text()

    # front がない前回の書き出し（このしくみより前）からは、版を上げて履歴に書く
    a.pop("front")
    asset_json.write_text(json.dumps(a, ensure_ascii=False))
    export_main(args)
    b = json.loads(asset_json.read_text())
    assert b["front"] == "-Y" and b["version"] == "1.1.0"
    assert b["history"][0]["changes"] == ["正面の向き（front）を -Y に設定"]

    spec_path = tmp_path / "cache" / "合成の箱" / "spec.json"
    s = json.loads(spec_path.read_text())
    s["front"] = 90
    spec_path.write_text(json.dumps(s, ensure_ascii=False))
    export_main(args)
    c = json.loads(asset_json.read_text())
    assert c["front"] == 90 and c["version"] == "1.2.0"
    assert c["history"][0]["changes"] == ["正面の向き（front） -Y → 90"]
    assert "| 正面の向き | +X から 90° |" in (asset_json.parent / "README.md").read_text()

    # 書けない値は既定の -Y にする
    s["front"] = "front"
    spec_path.write_text(json.dumps(s, ensure_ascii=False))
    export_main(args)
    assert json.loads(asset_json.read_text())["front"] == "-Y"
