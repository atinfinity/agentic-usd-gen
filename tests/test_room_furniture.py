"""住宅・オフィスの部屋の家具（room_furniture）のテスト。"""

import pytest

from agentic_usd_gen.fictional import room_furniture
from agentic_usd_gen.shapes.assembly import described_size_warnings

ALL = room_furniture.PRODUCTS
TABLES = ("meeting_table_round", "meeting_table_oval", "coffee_table_oval", "side_table_round")


def test_count():
    assert len(ALL) == 13


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    p = ALL[slug]()
    spec = p.spec()
    assert spec.slug == slug and spec.shape_class == "assembly" and spec.mass_kg > 0 and spec.tags
    assert "幅 " in p.description and "奥行き " in p.description and "高さ " in p.description
    assert not described_size_warnings(p.description, p.dims), "説明の外形が寸法と 5% 以内で合うこと"


@pytest.mark.parametrize("slug", TABLES)
def test_round_and_oval_tops(slug):
    """天板は円柱（楕円は直径 X と Y が違う円柱）、脚は一本脚に十字か円盤のベース。"""
    parts = ALL[slug]().spec().parts
    top = next(p for p in parts if p.name == "Top")
    assert top.shape == "cylinder"
    assert (top.size[0] > top.size[1]) == ("oval" in slug)
    assert [p for p in parts if p.name.endswith("Column") and p.shape == "cylinder"]
    assert [p for p in parts if p.name.endswith(("Disc", "FootX"))]


@pytest.mark.parametrize("slug", ["meeting_table_round", "meeting_table_oval"])
def test_knees_fit_under_the_top(slug):
    """天板の下（座面の高さ 450 mm から、天板の下面の 30 mm 下まで）には、中ほどの脚のほかに何も無い。"""
    parts = ALL[slug]().spec().parts
    top = next(p for p in parts if p.name == "Top")
    under = top.center[2] - top.size[2] / 2
    seat = room_furniture.CHAIR_SEAT_Z
    for p in parts:
        lo, hi = p.center[2] - p.size[2] / 2, p.center[2] + p.size[2] / 2
        if hi <= seat or lo >= under - 0.031 or not p.collision:
            continue
        assert p.name.endswith("Column"), p.name
        assert abs(p.center[1]) + p.size[1] / 2 < 0.10, f"{p.name} は天板の中ほどにある"


def test_chair_has_no_rail_under_the_front():
    """椅子は座面の下に前の横桟が無く、座面がテーブルの天板（高さ 720 mm の下面）より低い。"""
    parts = room_furniture.stacking_chair().spec().parts
    seat = next(p for p in parts if p.name == "Seat")
    assert seat.center[2] + seat.size[2] / 2 == pytest.approx(room_furniture.CHAIR_SEAT_Z)
    assert seat.center[2] + seat.size[2] / 2 < 0.72 - 0.025
    assert not [p for p in parts if p.size[0] > 0.3 and p.center[2] < 0.40]


def test_stack_has_six_chairs_each_a_little_higher():
    one = room_furniture.stacking_chair()
    stack = room_furniture.stacking_chair_stack()
    seats = sorted((p for p in stack.parts if p.name.endswith("Seat")), key=lambda p: p.center[2])
    assert len(seats) == 6 and len(stack.parts) == 6 * len(one.parts)
    dz = [b.center[2] - a.center[2] for a, b in zip(seats, seats[1:])]
    dy = [b.center[1] - a.center[1] for a, b in zip(seats, seats[1:])]
    assert all(0.05 < z < 0.10 for z in dz) and all(0 < y < 0.03 for y in dy)
    assert stack.dims.height == pytest.approx(one.dims.height + 5 * room_furniture.STACK_DZ)


def test_tv_screen():
    p = room_furniture.tv_cart()
    spec = p.spec()
    screens = [x for x in spec.parts if x.finish == "screen"]
    assert len(screens) == 1 and screens[0].faces == {"front": 0} and not screens[0].collision
    w, _, h = screens[0].size
    assert (w ** 2 + h ** 2) ** 0.5 / 0.0254 == pytest.approx(65, abs=0.5)  # 65 型
    assert spec.screen_places == room_furniture.SCREEN_PLACES and "any" not in spec.screen_places


def test_floor_lamp_light():
    spec = room_furniture.floor_lamp().spec()
    assert len(spec.lights) == 1 and spec.lights[0].kelvin <= 3000
    assert [p for p in spec.parts if p.finish == "light"]
