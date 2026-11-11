"""スーパーの青果（super_produce）の仕様のテスト。"""

import pytest

from agentic_usd_gen.fictional import super_produce
from agentic_usd_gen.spec import ProductSpec


@pytest.mark.parametrize("slug", sorted(super_produce.PRODUCTS))
def test_produce_spec(slug):
    prod = super_produce.PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.slug == slug and spec.shape_class == "assembly" and spec.category == "food"
    assert 0.1 < prod.mass_kg < 2.0
    assert any(p.collision for p in spec.parts)  # 動く剛体になる当たり判定がある
    assert "produce" in spec.tags and prod.description
    # 値札（ダミーのバーコード付き）を貼った面がある
    assert any(p.faces for p in spec.parts)
    assert ProductSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_only_strawberry_uses_photo():
    photos = {s: f().photos for s, f in super_produce.PRODUCTS.items()}
    assert photos.pop("strawberry_pack") == ["strawberry"]
    assert not any(photos.values())
