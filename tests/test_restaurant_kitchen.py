"""飲食店の業務用厨房機器のテスト。"""

import pytest

from agentic_usd_gen.fictional import restaurant_kitchen as rk

from .test_super_fixtures import _shelves

SHELF = {"kitchen_fridge_2door", "cold_table", "gas_range", "sink_2bowl", "work_table_steel",
         "kitchen_rack"}  # 物を置く水平の板（天板・棚板）のある物
JOINTS = {"kitchen_fridge_2door": [("revolute", "Z")] * 2, "cold_table": [("revolute", "Z")] * 2,
          "gas_range": [("revolute", "X")], "dishwasher_door": [("prismatic", "Z")]}


def test_count():
    assert len(rk.PRODUCTS) == 9


@pytest.mark.parametrize("slug", sorted(rk.PRODUCTS))
def test_spec(slug):
    spec = rk.PRODUCTS[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags and "kitchen" in spec.tags
    assert spec.static and spec.category == "fixture" and not spec.picture_places
    if slug in SHELF:
        assert _shelves(spec), "物を置く水平の板があること"
    joints = spec.joints or []
    assert [(j.type, j.axis) for j in joints] == JOINTS.get(slug, [])
    links = {p.link for p in spec.parts if p.link}
    for j in joints:
        assert j.link in links, "関節の link に部品があること"


def test_rack_four_shelves():
    names = _shelves(rk.kitchen_rack().spec())
    assert sorted(n for n in names if n.startswith("Shelf")) == ["Shelf0", "Shelf1", "Shelf2", "Shelf3"]


def test_doors_open_forward():
    """扉は手前（−Y）に開く：右端の蝶番は正、左端の蝶番は負の向き。"""
    for j in rk.cold_table().spec().joints:
        assert j.limits == ([-100.0, 0.0] if j.anchor[0] < 0 else [0.0, 100.0])
    for j in rk.kitchen_fridge_2door().spec().joints:
        assert j.anchor[0] > 0 and j.limits == [0.0, 100.0]


def test_hood_on_ceiling():
    assert rk.exhaust_hood().spec().mount == "ceiling"
