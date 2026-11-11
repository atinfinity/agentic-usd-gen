"""スーパーの売場の什器（super_fixtures）のテスト。"""

import pytest

from agentic_usd_gen.fictional.super_fixtures import PRODUCTS

PLACES = {"shop", "convenience_store", "supermarket", "cafe", "restaurant"}


def _shelves(spec):
    """棚板の検出の条件（厚さ 5 cm 以下・短辺 12 cm 以上・面積 0.03 m² 以上）の水平な部品。"""
    out = []
    for p in spec.parts:
        if p.shape != "box" or any(abs(r) > 0.5 for r in (p.rotation or [0, 0, 0])):
            continue
        a, b, t = p.size
        if t <= 0.05 and min(a, b) >= 0.12 and a * b >= 0.03:
            out.append(p.name)
    return out


@pytest.mark.parametrize("slug", sorted(PRODUCTS))
def test_fixture_spec(slug):
    prod = PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.static and spec.slug == slug
    assert spec.picture_places and set(spec.picture_places) <= PLACES
    blanks = [p for p in spec.parts if p.faces and p.blank is not None]
    assert blanks, "POP・看板は無地に切り替えられること"
    if slug != "banana_hanger":
        assert _shelves(spec), "商品を並べる水平の板があること"


def test_freezer_lids_are_not_shelves():
    spec = PRODUCTS["island_freezer_double"]().spec()
    assert not any(n.startswith("Lid") for n in _shelves(spec))
    assert len(spec.joints) == 4 and all(j.type == "prismatic" for j in spec.joints)


def test_reach_in_freezer_doors():
    spec = PRODUCTS["reach_in_freezer_5door"]().spec()
    assert len(spec.joints) == 5
    assert sum(n.startswith("Shelf") for n in _shelves(spec)) == 25
