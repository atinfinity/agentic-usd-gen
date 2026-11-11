"""スーパーのレジまわり・売場の設備（super_checkout）のテスト。"""

import pytest

from agentic_usd_gen.fictional import super_checkout as sc

SHOP = {"shop", "convenience_store", "supermarket", "cafe", "restaurant"}


@pytest.mark.parametrize("slug", sorted(sc.PRODUCTS))
def test_specs_build(slug):
    prod = sc.PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.slug == slug and spec.parts
    for p in spec.parts:
        for idx in (p.faces or {}).values():
            assert 0 <= idx < len(prod.images)


@pytest.mark.parametrize("slug", ["section_sign_produce", "section_sign_meat", "section_sign_fish",
                                  "section_sign_deli", "sample_table"])
def test_pictures_have_blank_and_places(slug):
    spec = sc.PRODUCTS[slug]().spec()
    assert spec.picture_places and set(spec.picture_places) <= SHOP
    assert any(p.faces and p.blank is not None for p in spec.parts)


def test_mounts_and_physics():
    assert all(sc.PRODUCTS[s]().mount == "ceiling" for s in sc.PRODUCTS if s.startswith("section_sign_"))
    assert sc.produce_scale().static is False  # 台の上に置いて動かせる
    for s in ("checkout_lane_belt", "sacker_table", "cart_corral", "shelf_price_label_strip"):
        assert sc.PRODUCTS[s]().static
