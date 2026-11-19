"""薬局の什器（pharmacy_fixtures）と商品（pharmacy_goods）のテスト。"""

import pytest

from agentic_usd_gen.fictional import pharmacy_fixtures, pharmacy_goods

from .test_super_fixtures import PLACES, _shelves

FIXTURES = {s: f for s, f in pharmacy_fixtures.PRODUCTS.items() if s != "dispensing_tray"}
GOODS = {**pharmacy_goods.PRODUCTS, "dispensing_tray": pharmacy_fixtures.dispensing_tray}


@pytest.mark.parametrize("slug", sorted(FIXTURES))
def test_fixture_spec(slug):
    spec = FIXTURES[slug]().spec()
    assert spec.static and spec.slug == slug
    assert set(spec.picture_places) <= PLACES | {"drugstore"}
    if spec.picture_places:
        assert [p for p in spec.parts if p.faces and p.blank is not None], "案内の板は無地に切り替えられること"
    if slug in ("dispensing_drawer_cabinet", "medicine_refrigerator"):
        assert len(_shelves(spec)) >= 2, "薬を並べる水平の板があること"


def test_moving_parts():
    cab = pharmacy_fixtures.dispensing_drawer_cabinet().spec()
    assert len(cab.joints) == 9
    assert all(j.type == "prismatic" and j.axis == "Y" and j.limits == [-0.30, 0.0] for j in cab.joints)
    fridge = pharmacy_fixtures.medicine_refrigerator().spec()
    assert len(fridge.joints) == 1 and fridge.joints[0].type == "revolute" and fridge.lights
    for spec in (cab, fridge):
        links = {j.link for j in spec.joints}
        for link in links:
            assert any(p.link == link and p.collision for p in spec.parts), f"{link} に当たり判定があること"


def test_screens():
    for f in (pharmacy_fixtures.blood_pressure_kiosk, pharmacy_fixtures.queue_number_display):
        assert [p for p in f().spec().parts if p.finish == "screen" and p.faces]


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods_spec(slug):
    spec = GOODS[slug]().spec()
    assert not spec.static and spec.mass_kg > 0 and spec.slug == slug
    assert GOODS[slug]().description and spec.tags
