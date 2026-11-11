"""カフェ・パン屋の什器と商品のテスト。"""

import pytest

from agentic_usd_gen.fictional import bakery, cafe

from .test_super_fixtures import _shelves

ALL = {**cafe.PRODUCTS, **bakery.PRODUCTS}
FIXTURES = {"cafe_order_counter", "espresso_machine", "cafe_menu_board", "cafe_sofa_bench", "tray_return_station",
            "bakery_display_shelf", "bakery_display_table", "tray_tong_station"}
PICTURE = {"cafe_order_counter", "cafe_menu_board", "tray_return_station", "bakery_display_shelf",
           "tray_tong_station"}  # 店の文面・看板のある什器
SHELF = {"cafe_order_counter", "espresso_machine", "tray_return_station", "bakery_display_shelf", "bakery_display_table",
         "tray_tong_station", "cafe_table_square", "bread_tray_bakery"}  # 物を置く板のある物（丸テーブルは円柱の天板）
PLACES = {"cafe", "restaurant", "bakery", "supermarket", "convenience_store", "shop"}


def test_count():
    assert len(cafe.PRODUCTS) == 9 and len(bakery.PRODUCTS) == 9


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert spec.static == (slug in FIXTURES)
    if slug in PICTURE:
        assert spec.picture_places and set(spec.picture_places) <= PLACES
        assert [p for p in spec.parts if p.faces and p.blank is not None], "看板・メニューは無地に切り替えられること"
    else:
        assert not spec.picture_places
    if slug in SHELF:
        assert _shelves(spec), "物を置く水平の板があること"


def test_bakery_shelf_trays():
    """陳列棚は 4 段 × 2 枚のトレーの底板が棚板になり、縁・桟は棚板にならない。"""
    names = _shelves(bakery.bakery_display_shelf().spec())
    assert sum(n.endswith("Plate") for n in names) == 8
    assert not [n for n in names if "Rim" in n or "Rail" in n]


def test_bakery_table_two_steps():
    """平台は手前と奥の 2 段 × 2 枚のトレーの底板だけが棚板になる（台の箱・奥の段・縁は棚板にならない）。"""
    spec = bakery.bakery_display_table().spec()
    names = _shelves(spec)
    assert sorted(names) == ["Tray00Plate", "Tray01Plate", "Tray10Plate", "Tray11Plate"]
    z = {p.name: p.center[2] for p in spec.parts}
    assert z["Tray10Plate"] - z["Tray00Plate"] > 0.1  # 奥の段が高い


@pytest.mark.parametrize("slug", ["croissant", "anpan", "curry_bread", "baguette", "shokupan_loaf"])
def test_bread_has_collision(slug):
    spec = ALL[slug]().spec()
    assert spec.category == "food" and all(p.collision and p.material == "food" for p in spec.parts)
