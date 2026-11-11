"""Tests for the backyard and logistics fixtures and materials (backyard)."""

import pytest

from agentic_usd_gen.fictional import backyard

STATIC = {"backyard_steel_rack", "inspection_table", "folding_container_stack"}


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


@pytest.mark.parametrize("slug", sorted(backyard.PRODUCTS))
def test_products(slug):
    prod = backyard.PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.slug == slug and spec.fictional and prod.mass_kg > 0
    assert spec.static == (slug in STATIC)
    assert not prod.picture_places
    for p in spec.parts:
        for idx in (p.faces or {}).values():
            assert 0 <= idx < len(prod.images), p.name
    if prod.shape_class == "assembly":
        lo, hi = backyard._bbox(spec.parts)
        assert abs(lo[2]) < 1e-6, "stands on the floor"
        assert (hi - lo)[0] == pytest.approx(prod.dims.diameter, abs=1e-3)
        assert (hi - lo)[1] == pytest.approx(prod.dims.depth, abs=1e-3)
        assert (hi - lo)[2] == pytest.approx(prod.dims.height, abs=1e-3)
        if not slug.startswith("pallet_jack"):
            assert _shelves(spec), "a horizontal board to stock goods on"


def test_steel_rack_has_four_boards_inside_the_frame():
    spec = backyard.backyard_steel_rack().spec()
    boards = [p for p in _shelves(spec) if p.name.startswith("Shelf")]
    assert len(boards) == 4
    assert [round(p.center[2] + p.size[2] / 2, 3) for p in boards] == [0.12, 0.66, 1.22, 1.78]
    for b in boards:
        x0, x1 = b.center[0] - b.size[0] / 2, b.center[0] + b.size[0] / 2
        y0, y1 = b.center[1] - b.size[1] / 2, b.center[1] + b.size[1] / 2
        top = b.center[2] + b.size[2] / 2
        for p in spec.parts:  # nothing else reaches into the space just above a board
            if p is b:
                continue
            px0, px1 = p.center[0] - p.size[0] / 2, p.center[0] + p.size[0] / 2
            py0, py1 = p.center[1] - p.size[1] / 2, p.center[1] + p.size[1] / 2
            pz0, pz1 = p.center[2] - p.size[2] / 2, p.center[2] + p.size[2] / 2
            overlap = px0 < x1 - 1e-6 and px1 > x0 + 1e-6 and py0 < y1 - 1e-6 and py1 > y0 + 1e-6
            assert not (overlap and pz1 > top + 1e-6 and pz0 < top + 0.3), (b.name, p.name)


def test_crate_walls_stand_outside_the_floor():
    for f in (backyard.bread_tray, backyard.folding_container):
        parts = f().parts
        floor = next(p for p in parts if p.name == "Floor")
        fx, fy = floor.size[0] / 2, floor.size[1] / 2
        for w in (p for p in parts if p.name.startswith("Wall")):
            inner_x = abs(w.center[0]) - w.size[0] / 2
            inner_y = abs(w.center[1]) - w.size[1] / 2
            assert inner_x >= fx - 1e-6 or inner_y >= fy - 1e-6, w.name


def test_loaded_cart_and_stacks_carry_fixed_contents():
    cart = backyard.roll_cage_cart_loaded()
    cartons = [p for p in cart.parts if p.name.startswith("Carton")]
    assert len(cartons) == 16 and all(p.collision for p in cartons)
    assert not cart.static and not cart.joints
    trays = {p.name[:5] for p in backyard.bread_tray_stack().parts if p.name.startswith("Tray")}
    assert len(trays) == 8
    wires = [p for p in backyard.roll_cage_cart().parts if "Wire" in p.name]
    assert wires and not any(p.collision for p in wires)


def test_masses_are_realistic():
    assert 25 <= backyard.roll_cage_cart().mass_kg <= 40
    assert 1.0 <= backyard.bread_tray().mass_kg <= 2.0
    assert 1.5 <= backyard.folding_container().mass_kg <= 3.0
    assert 60 <= backyard.pallet_jack().mass_kg <= 90
    assert backyard.carton_box_s().mass_kg < backyard.carton_box_m().mass_kg < backyard.carton_box_l().mass_kg
