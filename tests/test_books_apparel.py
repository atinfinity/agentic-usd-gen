"""書店・家電量販店・衣料品店の什器と商品のテスト。"""

import pytest

from agentic_usd_gen.fictional import apparel_fixtures, apparel_goods, book_fixtures, book_goods, elec_fixtures, elec_goods

from .test_super_fixtures import PLACES, _shelves

FIXTURES = {**book_fixtures.PRODUCTS, **elec_fixtures.PRODUCTS, **apparel_fixtures.PRODUCTS}
GOODS = {**book_goods.PRODUCTS, **elec_goods.PRODUCTS, **apparel_goods.PRODUCTS}
TRADES = {"bookstore", "electronics_store", "apparel_store", "shoe_store", "home_center"}  # batteries and bulbs also sell in home centers
NO_PICTURE = {"mannequin_standing", "fitting_room", "full_length_mirror"}  # 絵柄のない什器
NO_SHELF = {"bookstore_section_sign", "apparel_section_sign", *NO_PICTURE}  # 商品を並べない什器


@pytest.mark.parametrize("slug", sorted(FIXTURES))
def test_fixture_spec(slug):
    spec = FIXTURES[slug]().spec()
    assert spec.static and spec.slug == slug
    if slug in NO_PICTURE:
        assert not spec.picture_places
    else:
        assert spec.picture_places and set(spec.picture_places) <= PLACES | TRADES
        assert [p for p in spec.parts if p.faces and p.blank is not None], "看板・POP は無地に切り替えられること"
    if slug not in NO_SHELF:
        assert _shelves(spec), "商品を並べる水平の板があること"


def test_screen_and_signs():
    stand = FIXTURES["tv_display_stand"]().spec()
    assert [p for p in stand.parts if p.finish == "screen" and p.faces], "価格表示は Screen バリアントの画面であること"
    for slug in ("bookstore_section_sign", "apparel_section_sign"):
        assert FIXTURES[slug]().spec().mount == "ceiling"


def test_no_duplicate_slugs():
    from agentic_usd_gen.fictional import drug_fixtures, super_fixtures

    assert not FIXTURES.keys() & GOODS.keys()
    assert not (FIXTURES.keys() | GOODS.keys()) & (drug_fixtures.PRODUCTS.keys() | super_fixtures.PRODUCTS.keys())


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods_spec(slug):
    spec = GOODS[slug]().spec()
    assert not spec.static and spec.mass_kg > 0 and spec.slug == slug
    assert GOODS[slug]().description and spec.tags


def test_shoe_shelf_fits_a_shoe_store():
    """靴の壁面棚の見出し「シューズ」は靴屋にも合う。"""
    assert "shoe_store" in FIXTURES["shoe_wall_shelf"]().spec().picture_places
