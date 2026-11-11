"""いろいろな店・部屋の什器と商品のテスト。"""

import pytest

from agentic_usd_gen.fictional import misc_shops
from agentic_usd_gen.fictional.registry import PRODUCTS

ALL = misc_shops.PRODUCTS


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert PRODUCTS[slug] is ALL[slug]


@pytest.mark.parametrize("slug,words", [
    ("throw_cushion", {"throw pillow", "cushion", "sofa pillow"}),
    ("area_rug", {"rug", "area rug", "carpet"}),
    ("tv_remote", {"remote control", "tv remote"}),
    ("beer_bottle_334ml", {"beer bottle", "beer"}),
    ("mobile_whiteboard", {"whiteboard"}),
    ("wheelchair", {"wheelchair"}),
])
def test_tags_match_search_queries(slug, words):
    """ワールドを組むツールが探す語で見つかる。"""
    assert words <= set(ALL[slug]().spec().tags)


def test_cushion_fits_the_decor_size():
    """飾りのクッションは立てて置く（長辺 0.3〜0.6 m、高さ 0.2〜0.5 m）。"""
    d = ALL["throw_cushion"]().spec().dimensions
    assert 0.3 <= max(d.diameter, d.depth) <= 0.6 and 0.2 <= d.height <= 0.5


def test_rug_is_flat():
    d = ALL["area_rug"]().spec().dimensions
    assert d.height <= 0.05 and max(d.diameter, d.depth) >= 1.0


def test_cage_wires_are_look_only():
    """ケージの細い網は見た目だけ。枠・トレー・支柱・横桟だけが当たる。"""
    spec = ALL["pet_wire_cage"]().spec()
    hit = {p.name for p in spec.parts if p.collision}
    assert "Tray" in hit and {"Post0", "Post1", "Post2", "Post3"} <= hit
    assert not any(n.startswith(("TopWire", "Bar")) for n in hit)


def test_beer_bottle_is_one_body():
    """王冠は瓶と同じ 1 つの剛体（SimReady のボトルはキャップが別の剛体で外れて落ちる）。"""
    spec = ALL["beer_bottle_334ml"]().spec()
    assert not spec.static and spec.category == "beverage"


@pytest.mark.parametrize("slug", ["ceiling_fan", "track_spotlights"])
def test_ceiling_fixtures_hang(slug):
    spec = ALL[slug]().spec()
    assert spec.mount == "ceiling" and spec.static


@pytest.mark.parametrize("slug", ["wine_step_rack", "wine_crate", "chrome_wire_shelf", "garden_bench_table",
                                  "device_display_table", "pet_wire_cage", "puppy_showcase", "aquarium_tank",
                                  "pet_treat_bulk_case", "mobile_whiteboard", "wheelchair"])
def test_fixtures_are_static(slug):
    assert ALL[slug]().spec().static


@pytest.mark.parametrize("slug", ["throw_cushion", "tv_remote", "beer_bottle_334ml", "laptop_open", "seedling_tray"])
def test_goods_are_rigid(slug):
    assert not ALL[slug]().spec().static
