"""ファミレス・居酒屋の客席の家具と卓上の小物のテスト。"""

import pytest

from agentic_usd_gen.fictional import restaurant_dining

from .test_super_fixtures import _shelves

ALL = restaurant_dining.PRODUCTS
FIXTURES = {"booth_seat", "high_counter_table"}  # 床に固定
PICTURE = {"menu_stand"}  # 店のメニューの絵柄
SHELF = {"family_table_4", "family_table_2", "high_counter_table", "zataku_table"}  # 料理・食器を置く天板
PLACES = {"restaurant"}


def test_count():
    assert len(ALL) == 14


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert spec.static == (slug in FIXTURES)
    if slug in PICTURE:
        assert spec.picture_places and set(spec.picture_places) <= PLACES
        assert [p for p in spec.parts if p.faces and p.blank is not None], "メニューは無地に切り替えられること"
    else:
        assert not spec.picture_places
    if slug in SHELF:
        assert _shelves(spec), "物を置く水平の板があること"


def test_table_heights():
    z = {s: max(p.center[2] + p.size[2] / 2 for p in ALL[s]().spec().parts) for s in SHELF}
    assert z["family_table_4"] == pytest.approx(0.70) and z["zataku_table"] == pytest.approx(0.33)
    assert z["high_counter_table"] == pytest.approx(1.00)
