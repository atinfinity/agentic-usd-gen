"""ファミレス・食堂の皿に盛った料理のテスト。"""

import pytest

from agentic_usd_gen.fictional import restaurant_food

ALL = restaurant_food.PRODUCTS


def test_count():
    assert len(ALL) == 10


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags
    assert spec.category == "food" and not spec.static
    food = [p for p in spec.parts if p.material == "food"]
    ware = [p for p in spec.parts if p.material != "food"]
    assert food and all(not p.collision for p in food), "料理の部品はコリジョンなし"
    assert any(p.collision for p in ware), "器はコリジョンあり"
