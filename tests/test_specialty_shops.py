"""専門店の什器と商品のテスト。"""

import pytest

from agentic_usd_gen.fictional import specialty_shops
from agentic_usd_gen.fictional.registry import PRODUCTS

ALL = specialty_shops.PRODUCTS

FIXTURES = ["road_bicycle", "city_bicycle", "bicycle_stand_rack", "basket_display_stand", "wagashi_showcase", "noren",
            "lp_record_bin", "ball_cart", "modern_bed", "wardrobe", "round_display_table", "cosmetics_tester_island",
            "postcard_spinner_rack", "shop_fix_window"]
GOODS = sorted(set(ALL) - set(FIXTURES))


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert PRODUCTS[slug] is ALL[slug]


@pytest.mark.parametrize("slug,words", [
    ("road_bicycle", {"bicycle", "road bike", "bicycle shop"}),
    ("city_bicycle", {"bicycle", "city bike", "bicycle shop"}),
    ("bicycle_helmet", {"helmet", "bicycle helmet"}),
    ("bicycle_stand_rack", {"bicycle rack", "bike stand"}),
    ("woven_basket", {"basket", "woven basket", "wicker basket"}),
    ("basket_display_stand", {"basket display", "basket stand"}),
    ("dango_pack", {"dango", "wagashi shop"}),
    ("manju_pack", {"manju", "wagashi shop"}),
    ("monaka_pack", {"monaka"}),
    ("yokan_bar", {"yokan"}),
    ("wagashi_gift_box", {"gift box", "wagashi gift box"}),
    ("wagashi_showcase", {"showcase", "wagashi showcase", "display case"}),
    ("noren", {"noren", "shop curtain"}),
    ("lp_record", {"LP record", "vinyl record", "record shop"}),
    ("lp_record_bin", {"record bin", "record crate"}),
    ("soccer_ball", {"soccer ball", "football", "ball"}),
    ("basketball", {"basketball", "ball"}),
    ("ball_cart", {"ball cart", "ball basket"}),
    ("tennis_racket", {"tennis racket", "racket"}),
    ("modern_bed", {"bed", "double bed", "furniture store"}),
    ("nightstand", {"nightstand", "bedside table"}),
    ("wardrobe", {"wardrobe", "closet"}),
    ("round_display_table", {"round display table", "display table"}),
    ("cosmetics_tester_island", {"tester stand", "cosmetics display"}),
    ("postcard_spinner_rack", {"spinner rack", "postcard rack", "rotating rack"}),
    ("shop_fix_window", {"shop window", "fixed window", "wide window"}),
    ("asian_noodle_bag", {"instant noodles", "asian grocery"}),
    ("jasmine_rice_bag", {"rice bag", "jasmine rice"}),
    ("chili_oil_jar", {"chili oil", "condiment"}),
    ("oyster_sauce_bottle", {"oyster sauce", "condiment"}),
])
def test_tags_match_search_queries(slug, words):
    """ワールドを組むツールが探す語（英訳）で見つかる。"""
    assert words <= set(ALL[slug]().spec().tags)


@pytest.mark.parametrize("slug", FIXTURES)
def test_fixtures_are_static(slug):
    assert ALL[slug]().spec().static


@pytest.mark.parametrize("slug", GOODS)
def test_goods_are_rigid(slug):
    assert not ALL[slug]().spec().static


def test_spinner_rack_turns():
    spec = ALL["postcard_spinner_rack"]().spec()
    assert [j.link for j in spec.joints] == ["SpinnerLink"]
    assert all(not p.collision for p in spec.parts if p.name.startswith("Card"))


def test_fix_window_is_wide():
    """幅 2〜3 m の店の窓（開口に合わせて 0.75〜1.33 倍に伸縮する）。"""
    spec = ALL["shop_fix_window"]().spec()
    assert spec.category == "environment" and 2.0 <= spec.dimensions.diameter <= 3.0


@pytest.mark.parametrize("slug,host", [("woven_basket", "Front"), ("wagashi_showcase", "GlassF"),
                                       ("lp_record_bin", "Front")])
def test_bottom_boards_sit_inside_the_walls(slug, host):
    """商品を並べる棚板（底）が壁の内側にあり、壁の下に埋もれない。"""
    parts = {p.name: p for p in ALL[slug]().spec().parts}
    bottom = parts.get("Bottom") or parts["Deck"]
    wall = parts[host]
    assert bottom.size[1] < wall.size[0] and bottom.size[0] < wall.size[0]


def test_bicycles_stand_on_both_tyres():
    for slug in ("road_bicycle", "city_bicycle"):
        parts = {p.name: p for p in ALL[slug]().spec().parts}
        for w in ("FrontTire", "RearTire"):
            assert parts[w].collision and abs(parts[w].center[2] - parts[w].size[0] / 2) < 1e-6
