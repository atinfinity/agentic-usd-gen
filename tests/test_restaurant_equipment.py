"""ファミレスの客席まわり・配膳の備品のテスト。"""

import pytest

from agentic_usd_gen.fictional import restaurant_equipment

from .test_super_fixtures import _shelves

ALL = restaurant_equipment.PRODUCTS
FIXTURES = {"drink_bar", "deshap_counter"}  # 床置きの重い什器（動かない）
PICTURE = {"drink_bar", "waiting_board"}  # 店の文面のある物
SHELF = {"drink_bar", "serving_wagon", "serving_tray", "deshap_counter"}  # 物を置く板のある物
PLACES = {"restaurant"}


def test_count():
    assert len(ALL) == 5


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert spec.static == (slug in FIXTURES)
    if slug in PICTURE:
        assert spec.picture_places and set(spec.picture_places) <= PLACES
        assert [p for p in spec.parts if p.faces and p.blank is not None], "店の文面は無地に切り替えられること"
    else:
        assert not spec.picture_places
    if slug in SHELF:
        assert _shelves(spec), "物を置く水平の板があること"


def test_wagon_three_shelves():
    """ワゴンは 3 段の棚板が棚板になり、縁は棚板にならない。"""
    names = _shelves(restaurant_equipment.serving_wagon().spec())
    assert sorted(names) == ["Shelf0", "Shelf1", "Shelf2"]


def test_deshap_heat_lamps():
    spec = restaurant_equipment.deshap_counter().spec()
    assert len(spec.lights) == 3 and all(lt.kelvin < 3500 for lt in spec.lights)
    assert {"Top", "UpperShelf", "UnderShelf"} <= set(_shelves(spec))
