"""内装の仕上げ材と天井の設備（interior.py、カテゴリ environment）のテスト。"""

import pytest

from agentic_usd_gen.fictional import interior, registry

WALL = {"wood_slat_wall_panel", "kitchen_tile_backsplash", "pegboard_wall_panel"}
CEILING = {"ceiling_ac_cassette", "ceiling_air_diffuser", "sprinkler_head", "smoke_detector", "ceiling_access_hatch",
           "emergency_light"}


@pytest.fixture(scope="module")
def products():
    return {slug: f() for slug, f in interior.PRODUCTS.items()}


def _box(p):
    """回転していない部品の範囲（180° の回転は範囲が変わらない。斜めの小物は外す）。"""
    if any(r % 180 for r in p.rotation):
        return None
    return [(c - s / 2, c + s / 2) for c, s in zip(p.center, p.size)]


def test_registered_static_environment(products):
    assert len(products) == 19
    for slug, p in products.items():
        assert slug in registry.PRODUCTS
        spec = p.spec()
        assert spec.category == "environment" and spec.static and spec.shape_class == "assembly", slug
        assert type(spec).from_dict(spec.to_dict()).slug == slug
        assert spec.mount == ("ceiling" if slug in CEILING else "floor"), slug


@pytest.mark.parametrize("slug", sorted(interior.PRODUCTS))
def test_parts_fill_the_dimensions(products, slug):
    """部品の範囲が寸法（幅・奥行き・高さ）と合い、底は z = 0、壁材の背面は y = 0。"""
    p = products[slug]
    boxes = [b for b in map(_box, p.parts) if b]
    lo = [min(b[i][0] for b in boxes) for i in range(3)]
    hi = [max(b[i][1] for b in boxes) for i in range(3)]
    assert hi[0] - lo[0] == pytest.approx(p.dims.diameter, abs=2e-3)
    assert hi[2] - lo[2] == pytest.approx(p.dims.height, abs=2e-3) and lo[2] == pytest.approx(0, abs=1e-6)
    assert hi[1] - lo[1] == pytest.approx(p.dims.depth, abs=0.12)
    if slug in WALL:
        assert hi[1] == pytest.approx(0, abs=1e-6) and hi[1] - lo[1] == pytest.approx(p.dims.depth, abs=1e-6)
    assert any(x.collision for x in p.parts)


def test_glass_door_opens_on_a_hinge(products):
    (j,) = products["glass_partition_door"].joints
    assert (j.link, j.type, j.axis, j.limits) == ("LeafLink", "revolute", "Z", [0.0, 90.0])
    leaf = [x for x in products["glass_partition_door"].parts if x.link == "LeafLink"]
    assert min(x.center[0] - x.size[0] / 2 for x in leaf if not any(x.rotation)) == pytest.approx(j.anchor[0])


def test_glass_has_a_manifestation_band(products):
    for slug in ("glass_partition", "glass_partition_door"):
        bands = [x for x in products[slug].parts if "Band" in x.name]
        assert len(bands) == 2 and all(not x.collision and 1.0 <= x.center[2] <= 1.1 for x in bands)
