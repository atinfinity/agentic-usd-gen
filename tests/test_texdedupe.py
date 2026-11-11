"""同じ中身のテクスチャを 1 つにまとめるテスト。"""

import numpy as np
from PIL import Image
from pxr import Sdf, Usd, UsdShade, UsdUtils

from agentic_usd_gen.isaac_layout import split_layers
from agentic_usd_gen.texdedupe import dedupe_textures, referenced_names


def _png(path, color):
    Image.fromarray(np.full((8, 8, 3), color, np.uint8)).save(path)


def _stage(tmp_path, names):
    """names の画像を 1 つずつ貼った材質のある USD。バリアントの中でも 1 つ参照する。"""
    usd = tmp_path / "a.usd"
    stage = Usd.Stage.CreateNew(str(usd))
    root = stage.DefinePrim("/Root", "Xform")
    stage.SetDefaultPrim(root)
    for i, name in enumerate(names):
        mat = UsdShade.Material.Define(stage, f"/Root/M{i}")
        tex = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild("Tex"))
        tex.CreateIdAttr("UsdUVTexture")
        tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(f"./textures/{name}"))
    vset = root.GetVariantSets().AddVariantSet("Picture")
    vset.AddVariant("Blank")
    vset.SetVariantSelection("Blank")
    with vset.GetVariantEditContext():
        UsdShade.Shader(stage.GetPrimAtPath("/Root/M1/Tex")).GetInput("file").Set(Sdf.AssetPath("./textures/b.png"))
    stage.Save()
    return usd


def _files(stage_path):
    layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(stage_path))
    return sorted(a.rsplit("/", 1)[-1] for a in assets), unresolved


def test_dedupe_textures(tmp_path):
    tex = tmp_path / "textures"
    tex.mkdir()
    for name in ("a.png", "b.png", "c.png", "Header.png"):
        _png(tex / name, (200, 40, 40))  # すべて同じ中身
    _png(tex / "d.png", (10, 20, 30))
    usd = _stage(tmp_path, ["a.png", "b.png", "c.png", "d.png", "Header.png"])

    mapping = dedupe_textures(usd, tex, keep={"Header.png"})

    assert mapping == {"b.png": "a.png", "c.png": "a.png"}  # 名前で参照される Header.png は残し、寄せもしない
    assert sorted(p.name for p in tex.iterdir()) == ["Header.png", "a.png", "d.png"]
    stage = Usd.Stage.Open(str(usd))
    files = [UsdShade.Shader(stage.GetPrimAtPath(f"/Root/M{i}/Tex")).GetInput("file").Get().path for i in range(5)]
    assert files == ["./textures/a.png", "./textures/a.png", "./textures/a.png", "./textures/d.png",
                     "./textures/Header.png"]  # ./ を保つ（split_layers が ../ に直す目印）
    # payloads/ に分けても、すべての参照が解決できる
    split_layers(usd)
    files, unresolved = _files(usd)
    assert unresolved == []
    assert files == ["Header.png", "a.png", "d.png"]


def test_dedupe_nothing(tmp_path):
    tex = tmp_path / "textures"
    tex.mkdir()
    _png(tex / "a.png", (1, 2, 3))
    _png(tex / "b.png", (4, 5, 6))
    usd = _stage(tmp_path, ["a.png", "b.png"])
    assert dedupe_textures(usd, tex) == {}
    assert dedupe_textures(usd, tmp_path / "none") == {}


def test_referenced_names():
    asset = {"picture": {"materials": [{"image": "./textures/Header.png", "blank": "./textures/Header_Blank.png"}]},
             "usd": "x.usd", "tags": ["textures"]}
    assert referenced_names(asset) == {"Header.png", "Header_Blank.png"}


def test_dedupe_exported(tmp_path):
    """書き出し済み（payloads/ に分けたあと）のアセットにも使える。"""
    from agentic_usd_gen.texdedupe import main

    d = tmp_path / "assets" / "fixture" / "x" / "simready_usd"
    tex = d / "textures"
    tex.mkdir(parents=True)
    for name in ("a.png", "b.png", "Header.png"):
        _png(tex / name, (200, 40, 40))
    (d / "asset.json").write_text('{"picture": {"materials": [{"image": "./textures/Header.png"}]}}')
    usd = _stage(d, ["a.png", "b.png", "Header.png"])
    split_layers(usd)
    main([str(tmp_path / "assets")])
    assert sorted(p.name for p in tex.iterdir()) == ["Header.png", "a.png"]
    files, unresolved = _files(usd)
    assert unresolved == [] and files == ["Header.png", "a.png"]
