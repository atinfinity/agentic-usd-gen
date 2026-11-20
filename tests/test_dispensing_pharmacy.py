"""調剤薬局の機器・什器（pharmacy_dispensary）、受付・待合い（pharmacy_counter）、医療用医薬品と調剤用品
（pharmacy_rx_goods）のテスト。"""

import pytest

from agentic_usd_gen.fictional import (
    pharmacy_counter,
    pharmacy_dispensary,
    pharmacy_rx_goods,
)

from .test_super_fixtures import PLACES, _shelves

ALL = {**pharmacy_dispensary.PRODUCTS, **pharmacy_counter.PRODUCTS, **pharmacy_rx_goods.PRODUCTS}
FIXTURES = {s: f for s, f in ALL.items() if f().spec().static}
GOODS = {s: f for s, f in ALL.items() if s not in FIXTURES}


def test_split():
    assert len(ALL) == 30
    assert len(FIXTURES) == 12 and len(GOODS) == 18
    assert {"electronic_balance", "medicine_bag_printer", "acrylic_splash_guard", "number_ticket_machine"} <= set(GOODS)


@pytest.mark.parametrize("slug", sorted(FIXTURES))
def test_fixture_spec(slug):
    spec = FIXTURES[slug]().spec()
    assert spec.slug == slug and spec.category in ("fixture", "environment")
    assert set(spec.picture_places) <= PLACES | {"drugstore"}
    if spec.picture_places:
        assert [p for p in spec.parts if p.faces and p.blank is not None], "案内の板は無地に切り替えられること"


@pytest.mark.parametrize("slug", ["picking_shelf_rack", "medicine_cart", "powder_dispensing_table", "dispensing_sink"])
def test_shelves(slug):
    assert _shelves(ALL[slug]().spec()), "物を並べる水平の板があること"


def test_narcotics_safe_door():
    spec = pharmacy_dispensary.narcotics_safe().spec()
    assert len(spec.joints) == 1
    j = spec.joints[0]
    assert j.type == "revolute" and j.limits == [0.0, 100.0]
    assert any(p.link == j.link and p.collision for p in spec.parts), "扉に当たり判定があること"


def test_lights_and_screens():
    for f in (pharmacy_dispensary.powder_dispensing_table, pharmacy_dispensary.clean_bench):
        assert f().spec().lights
    for f in (pharmacy_dispensary.tablet_packaging_machine, pharmacy_dispensary.audit_workstation,
              pharmacy_counter.number_ticket_machine, pharmacy_counter.face_auth_card_reader):
        assert [p for p in f().spec().parts if p.finish == "screen" and p.faces]


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods_spec(slug):
    spec = GOODS[slug]().spec()
    assert not spec.static and spec.mass_kg > 0 and spec.slug == slug
    assert GOODS[slug]().description and spec.tags


def test_rx_names_are_generic():
    """医療用医薬品は一般名で、会社名は架空（説明にそう書く）。"""
    for f in (pharmacy_rx_goods.ptp_medicine_box, pharmacy_rx_goods.suppository_box,
              pharmacy_rx_goods.compress_patch_bag, pharmacy_rx_goods.powder_stock_bottle):
        p = f()
        assert "処方箋医薬品" in p.tags and "架空" in p.description


def test_mortar_is_hollow_for_collision():
    """乳鉢の鉢は中の空いた回転体で、当たり判定は凸分解。凸包だと上が平らにふさがり、錠剤が中に入らない。"""
    spec = pharmacy_rx_goods.mortar_and_pestle().spec()
    bowl = next(p for p in spec.parts if p.name == "Bowl")
    assert bowl.shape == "revolve" and bowl.collision and bowl.material == "ceramic"
    assert spec.collision_approximations()["Bowl"] == "convexDecomposition"
    H = bowl.size[2]
    inner_bottom = bowl.profile[-1]  # 断面の最後は内側の底の中心
    assert inner_bottom[0] == 0 and (1 - inner_bottom[1]) * H > 0.045  # 縁から 45 mm より深くくぼむ
    assert all(p.material == "ceramic" for p in spec.parts if p.collision)
