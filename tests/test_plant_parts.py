"""葉・萼・管・実の部品形状と、部品を出し入れするバリアント（イチゴの苗）のテスト。"""

import re

import numpy as np
import pytest
from pxr import Usd, UsdGeom

from agentic_usd_gen.fictional.farm import strawberry_growing_rack, strawberry_plant_pot
from agentic_usd_gen.shapes.assembly import fruit_mesh, leaf_mesh, star_mesh, tube_mesh
from agentic_usd_gen.spec import Dimensions, Part, ProductSpec
from agentic_usd_gen.usd_post import write_part_variants


def _bounds(mesh):
    v = np.asarray(mesh["vertices"])
    return v.min(0), v.max(0)


def test_leaf_mesh_base_and_teeth():
    plain = leaf_mesh(0.1, 0.06, 0.01)
    toothed = leaf_mesh(0.1, 0.06, 0.01, teeth=7, columns=2)
    lo, hi = _bounds(toothed)
    assert lo[0] == pytest.approx(-0.05) and hi[0] == pytest.approx(0.05)
    assert hi[1] <= 0.03 + 1e-9 and lo[1] >= -0.03 - 1e-9
    base = [v for v in toothed["vertices"] if v[0] == pytest.approx(-0.05)]
    assert len(base) == 1 and base[0][1] == 0  # 付け根は 1 点
    assert len(toothed["faces"]) > len(plain["faces"])
    assert len(toothed["uvs"]) == len(toothed["faces"])


def test_star_mesh_lobes_and_rings():
    m = star_mesh(0.04, 0.04, 0.004, [[5, 0.4, 1.0]])
    assert len(m["faces"]) == 10  # 5 裂片 × 2 点の扇
    fine = star_mesh(0.04, 0.04, 0.004, [[5, 0.4, 1.0]], samples=4, rings=2)
    assert len(fine["faces"]) == 40
    lo, hi = _bounds(fine)
    assert hi[0] == pytest.approx(0.02) and hi[2] == pytest.approx(0.004)


def test_fruit_mesh_tip_at_origin():
    m = fruit_mesh(0.03, 0.03, 0.04, n=12, atlas=True)
    lo, hi = _bounds(m)
    assert lo[2] == 0 and hi[2] == pytest.approx(0.04)
    assert hi[0] == pytest.approx(0.015)
    tip = [v for v in m["vertices"] if v[2] == 0]
    assert tip == [[0.0, 0.0, 0.0]]
    u = np.asarray([uv for f in m["uvs"] for uv in f])
    assert u.min() >= 0 and u.max() <= 1


def test_tube_mesh_follows_path():
    path = [[0, 0, 0], [0.05, 0, 0.02], [0.1, 0, 0]]
    m = tube_mesh(path, 0.004, 0.002, n=6)
    assert len(m["vertices"]) == 18
    assert len(m["faces"]) == 2 * 6 + 2  # 側面と両端
    lo, hi = _bounds(m)
    assert -0.003 < lo[0] < 0 and 0.1 < hi[0] < 0.103
    assert hi[2] == pytest.approx(0.02 + 0.002, abs=1e-3)


def _spec(**kw):
    parts = [Part(name="A", shape="box", size=(0.1, 0.1, 0.1), center=(0, 0, 0.05)),
             Part(name="B", shape="box", size=(0.1, 0.1, 0.1), center=(0, 0, 0.15), **kw)]
    return ProductSpec(product_name="x", slug="x", shape_class="assembly", dimensions=Dimensions(0.2, 0.1, depth=0.1), parts=parts,
                       variant_sets={"Stage": ["Big", "Small"]})


def test_variant_spec_checks():
    _spec(show={"Stage": ["Big"]})._check_variants()
    with pytest.raises(ValueError, match="variant_sets にありません"):
        _spec(show={"Size": ["Big"]})._check_variants()
    with pytest.raises(ValueError, match="バリアントセット Stage"):
        _spec(show={"Stage": ["Huge"]})._check_variants()


def test_write_part_variants_combine():
    stage = Usd.Stage.CreateInMemory()
    root = stage.DefinePrim("/a", "Xform")
    for n in ("Pot", "Leaf", "Red", "Green"):
        UsdGeom.Mesh.Define(stage, f"/a/{n}")
    shows = {"Leaf": {"Stage": ["Grown"]}, "Red": {"Stage": ["Grown"], "Ripe": ["Red"]},
             "Green": {"Stage": ["Grown"], "Ripe": ["Green"]}}
    out = write_part_variants(root, {"Stage": ["Grown", "Seedling"], "Ripe": ["Red", "Green"]}, shows)
    assert out["Stage"]["default"] == "Grown" and out["Ripe"]["parts"]["Red"] == ["Red"]

    def visible():
        return sorted(p.GetName() for p in root.GetChildren()
                      if UsdGeom.Imageable(p).ComputeVisibility() != UsdGeom.Tokens.invisible)

    assert visible() == ["Leaf", "Pot", "Red"]
    root.GetVariantSet("Ripe").SetVariantSelection("Green")
    assert visible() == ["Green", "Leaf", "Pot"]
    root.GetVariantSet("Stage").SetVariantSelection("Seedling")
    assert visible() == ["Pot"]


def test_pot_variants_and_rack_individuality():
    pot = strawberry_plant_pot()
    assert pot.variant_sets == {"Stage": ["Fruiting", "Flowering", "Seedling"],
                                "Ripeness": ["Mixed", "Green", "White", "Red"]}
    seedling = [p for p in pot.parts if p.show and "Seedling" in p.show.get("Stage", [])]
    assert seedling and not any("Ripeness" in p.show for p in seedling)
    fruit = [p for p in pot.parts if p.shape == "fruit"]
    assert fruit and all(p.show["Stage"] == ["Fruiting"] for p in fruit)
    for ripe in ("Green", "White", "Red"):
        assert any(ripe in p.show.get("Ripeness", []) for p in fruit)
    pot.spec()._check_variants()

    rack = strawberry_growing_rack()
    plants: dict[str, int] = {}
    for p in rack.parts:
        if p.shape == "leaf":
            plant = re.match(r"P\d+", p.name).group()
            plants[plant] = plants.get(plant, 0) + 1
    assert len(set(plants.values())) > 1  # 株ごとに葉の数が違う
