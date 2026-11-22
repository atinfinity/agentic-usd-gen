"""usd_post.sort_children puts every prim's children in name order."""

import pytest
from pxr import Sdf

from agentic_usd_gen.usd_post import sort_children


def _names(layer, path):
    return list(layer.GetPrimAtPath(path).nameChildren.keys())


def test_children_sorted_and_content_kept(tmp_path):
    f = tmp_path / "a.usda"
    layer = Sdf.Layer.CreateNew(str(f))
    for p in ("/R/c/z", "/R/c/y", "/R/_materials/M", "/R/a", "/R/b"):
        Sdf.CreatePrimInLayer(layer, p).specifier = Sdf.SpecifierDef
    a = Sdf.AttributeSpec(layer.GetPrimAtPath("/R/c/z"), "v", Sdf.ValueTypeNames.Float)
    a.default = 1.5
    layer.defaultPrim = "R"
    layer.Save()

    sort_children(layer)
    got = Sdf.Layer.FindOrOpen(str(f))
    got.Reload()
    assert _names(got, "/R") == ["_materials", "a", "b", "c"]
    assert _names(got, "/R/c") == ["y", "z"]
    assert got.GetAttributeAtPath("/R/c/z.v").default == 1.5
    assert got.defaultPrim == "R"


@pytest.mark.parametrize("suffix", [".usd", ".usda"])  # Blender writes .usd as crate (binary)
def test_same_content_same_bytes(tmp_path, suffix):
    out = []
    for name, order in (("x", ("b", "a", "c")), ("y", ("c", "b", "a"))):
        f = tmp_path / f"{name}{suffix}"
        layer = Sdf.Layer.CreateNew(str(f))
        for n in order:
            spec = Sdf.CreatePrimInLayer(layer, f"/R/{n}")
            spec.specifier = Sdf.SpecifierDef
            Sdf.AttributeSpec(spec, f"attr_{n}", Sdf.ValueTypeNames.Float).default = float(len(n))
        layer.GetPrimAtPath("/R").nameChildrenOrder = list(order)  # an authored order is dropped too
        layer.Save()
        sort_children(layer)
        out.append(f.read_bytes())
        assert list(Sdf.Layer.FindOrOpen(str(f)).GetPrimAtPath("/R").nameChildrenOrder) == []
    assert out[0] == out[1]
