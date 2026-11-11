"""Tests for the home-center and 100-yen-shop goods and fixtures (hc_tools, hc_garden, hc_daily, hc_fixtures)."""

import pytest

from agentic_usd_gen.fictional import hc_daily, hc_fixtures, hc_garden, hc_tools

PLACES = {"shop", "home_center", "hundred_yen_shop"}
GOODS = {**hc_tools.PRODUCTS, **hc_garden.PRODUCTS, **hc_daily.PRODUCTS}
MOVABLE = {"wood_pallet", "plastic_pallet", "platform_cart"}  # fixtures that are dynamic rigid bodies
SIGNS = {s for s in hc_fixtures.PRODUCTS if s.startswith("section_sign_")}


def _shelves(spec):
    """Horizontal parts that shelf detection takes as boards (<= 5 cm thick, short side >= 12 cm,
    area >= 0.03 m^2)."""
    out = []
    for p in spec.parts:
        if p.shape != "box" or any(abs(r) > 0.5 for r in (p.rotation or [0, 0, 0])):
            continue
        a, b, t = p.size
        if t <= 0.05 and min(a, b) >= 0.12 and a * b >= 0.03:
            out.append(p)
    return out


def _faces_ok(prod, spec):
    for p in spec.parts:
        for idx in (p.faces or {}).values():
            assert 0 <= idx < len(prod.images), p.name


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods(slug):
    prod = GOODS[slug]()
    spec = prod.spec()
    assert spec.slug == slug and spec.fictional
    assert not prod.static and prod.mass_kg > 0  # goods are dynamic rigid bodies
    assert not prod.picture_places
    _faces_ok(prod, spec)


@pytest.mark.parametrize("slug", sorted(hc_fixtures.PRODUCTS))
def test_fixtures(slug):
    prod = hc_fixtures.PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.slug == slug
    assert spec.static == (slug not in MOVABLE)
    _faces_ok(prod, spec)
    if spec.picture_places:
        assert set(spec.picture_places) <= PLACES
        assert any(p.faces and p.blank is not None for p in spec.parts), "POP can switch to a plain board"
    if slug in SIGNS:
        assert prod.mount == "ceiling" and not _shelves(spec)
    else:
        assert _shelves(spec), "a horizontal board to stock goods on"


def test_signs_and_pallets_have_pictures_only_where_needed():
    assert not hc_fixtures.wood_pallet().picture_places and not hc_fixtures.platform_cart().picture_places
    assert hc_fixtures.hundred_yen_gondola().picture_places == hc_fixtures.HUNDRED_PLACES


def test_pegboard_hooks_do_not_collide():
    for f in (hc_fixtures.pegboard_gondola, hc_fixtures.pegboard_wall_tools):
        parts = f().parts
        hooks = [p for p in parts if p.name.startswith("Hook")]
        assert len(hooks) == 18 and not any(p.collision for p in hooks)
    tools = hc_fixtures.pegboard_wall_tools()
    hung = [p for p in tools.parts if p.name[:2] in ("sd", "pl", "tm", "sc")]
    assert hung and not any(p.collision for p in hung)


def test_bins_are_boards_with_walls_outside():
    """The 100-yen gondola's bin floors are boards, and the bin walls stand outside each floor's footprint."""
    spec = hc_fixtures.hundred_yen_gondola().spec()
    floors = [p for p in _shelves(spec) if p.name.endswith("Floor")]
    assert len(floors) == 6
    for f in floors:
        x0, x1 = f.center[0] - f.size[0] / 2, f.center[0] + f.size[0] / 2
        y0, y1 = f.center[1] - f.size[1] / 2, f.center[1] + f.size[1] / 2
        for w in (p for p in spec.parts if p.name.startswith(f.name[:-5]) and p is not f):
            wx0, wx1 = w.center[0] - w.size[0] / 2, w.center[0] + w.size[0] / 2
            wy0, wy1 = w.center[1] - w.size[1] / 2, w.center[1] + w.size[1] / 2
            inside_x = wx0 > x0 + 1e-6 and wx1 < x1 - 1e-6
            inside_y = wy0 > y0 + 1e-6 and wy1 < y1 - 1e-6
            assert not (inside_x and inside_y) and not (wx0 >= x0 - 1e-6 and wx1 <= x1 + 1e-6
                                                        and wy0 >= y0 - 1e-6 and wy1 <= y1 + 1e-6), w.name


def test_top_deck_of_tall_rack_is_stock():
    """The rack's top deck carries static stock cartons covering most of it (so fill leaves it alone)."""
    prod = hc_fixtures.hc_tall_rack()
    top = max((p for p in prod.parts if p.name.startswith("Deck")), key=lambda p: p.center[2])
    stock = [p for p in prod.parts if p.name.startswith("Stock")]
    area = sum(p.size[0] * p.size[1] for p in stock)
    assert area >= 0.5 * top.size[0] * top.size[1]
    assert all(abs(p.center[2] - p.size[2] / 2 - (top.center[2] + top.size[2] / 2)) < 1e-6 for p in stock)



def test_tall_rack_top_stock_can_be_removed():
    """TopStock = None hides the cartons on the top deck (rows of these racks looked like a warehouse)."""
    spec = hc_fixtures.hc_tall_rack().spec()
    assert spec.variant_sets == {"TopStock": ["Boxes", "None"]}
    stock = [p for p in spec.parts if p.name.startswith("Stock")]
    assert stock and all(p.show == {"TopStock": ["Boxes"]} for p in stock)
    assert all(not p.show for p in spec.parts if not p.name.startswith("Stock"))


def test_masses_are_realistic():
    assert 20 <= hc_fixtures.wood_pallet().mass_kg <= 30  # T11 wooden pallet
    assert 6.5 <= hc_garden.soil_bag().mass_kg <= 8  # 14 L of potting soil
    assert 2.0 <= hc_daily.lumber_2x4().mass_kg <= 3.2  # SPF 38 x 89 x 1820
