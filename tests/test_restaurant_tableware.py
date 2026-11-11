"""Restaurant tableware ."""

import pytest

from agentic_usd_gen.fictional import restaurant_tableware

ALL = restaurant_tableware.PRODUCTS
PLATES = {"dinner_plate", "deep_plate"}
VESSELS = PLATES | {"donburi_bowl", "rice_bowl", "soup_bowl", "water_glass", "beer_mug", "water_pitcher"}
GLASSES = {"water_glass", "beer_mug", "water_pitcher"}


def test_count():
    assert len(ALL) == 10


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert spec.category == "household" and not spec.static and not spec.picture_places
    assert any(ord(ch) > 0x3000 for ch in spec.product_name)  # Japanese name
    assert all(p.collision_approximation in (None, "convexHull") for p in spec.parts), "never SDF"


@pytest.mark.parametrize("slug", sorted(VESSELS))
def test_vessel_is_closed_revolve(slug):
    body = ALL[slug]().spec().parts[0]
    assert body.shape == "revolve" and body.collision
    prof = body.profile
    assert prof[0] == [0.0, 0.0] and prof[-1][0] == 0.0  # closed at both centers
    assert prof[-1][1] > 0  # hollow: the inner bottom is above the outer bottom


@pytest.mark.parametrize("slug", sorted(PLATES))
def test_plate_has_flat_foot(slug):
    prof = ALL[slug]().spec().parts[0].profile
    assert prof[1][1] == 0 and prof[1][0] >= 0.5  # foot ring at least half the radius


@pytest.mark.parametrize("slug", sorted(GLASSES))
def test_glass_finish(slug):
    spec = ALL[slug]().spec()
    assert spec.parts[0].finish == "glass"
    assert all(not p.collision for p in spec.parts if p.material in ("water", "ice", "food"))


def test_mug_handle_on_plus_x():
    parts = {p.name: p for p in ALL["beer_mug"]().spec().parts}
    assert parts["Handle"].center[0] > 0
    parts = {p.name: p for p in ALL["water_pitcher"]().spec().parts}
    assert parts["HandleGrip"].center[0] > 0 > parts["Spout"].center[0]
