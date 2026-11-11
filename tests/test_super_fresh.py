"""スーパーの生鮮・惣菜・大容量の商品（super_fresh）のテスト。"""

import pytest

from agentic_usd_gen.fictional import super_fresh as sf

TRAYS = ["pork_komagire_tray", "chicken_thigh_tray", "ground_meat_tray", "sashimi_assorted_tray",
         "salmon_fillet_tray", "fried_food_pack", "sushi_pack", "bento_large"]


@pytest.mark.parametrize("slug", sorted(sf.PRODUCTS))
def test_specs_build(slug):
    prod = sf.PRODUCTS[slug]()
    spec = prod.spec()
    assert spec.slug == slug
    assert not prod.static and prod.mass_kg > 0  # 手に取って動かせる商品
    assert prod.category in ("food", "beverage")
    for p in spec.parts:
        for idx in (p.faces or {}).values():
            assert 0 <= idx < len(prod.images)


@pytest.mark.parametrize("slug", TRAYS + ["egg_10pack"])
def test_packs_fit_inside_their_wrap(slug):
    """中身の部品はラップ・フタの内側に収まり、当たり判定はトレーとフタだけ。"""
    prod = sf.PRODUCTS[slug]()
    W, D, H = prod.dims.diameter, prod.dims.depth, prod.dims.height
    for p in prod.parts:
        if p.material == "food":
            assert not p.collision
            assert p.center[2] + p.size[2] / 2 <= H + 1e-6, p.name
            assert abs(p.center[0]) <= W / 2 and abs(p.center[1]) <= D / 2, p.name
    assert any(p.collision for p in prod.parts)


def test_masses_are_realistic():
    assert 10.0 <= sf.rice_bag_10kg().mass_kg <= 10.3  # 中身 10 kg と袋
    assert 12.0 <= sf.water_2l_case_6().mass_kg <= 13.0  # 2 L × 6 本と段ボール
    assert 8.5 <= sf.drink_cardboard_case_24().mass_kg <= 9.5  # 350 ml 缶 × 24
    assert 0.6 <= sf.egg_10pack().mass_kg <= 0.7  # M サイズ 10 個
    assert all(0.1 <= sf.PRODUCTS[s]().mass_kg <= 1.0 for s in TRAYS)
