"""店舗の内装・建具（store_env.py、カテゴリ environment）のテスト。"""

from dataclasses import asdict

import pytest

from agentic_usd_gen.fictional import store_env
from agentic_usd_gen.lighting import illuminance
from agentic_usd_gen.spec import CATEGORIES


@pytest.fixture(scope="module")
def products():
    return {slug: f() for slug, f in store_env.PRODUCTS.items()}


def test_all_environment_static_assembly(products):
    assert "environment" in CATEGORIES
    for slug, p in products.items():
        spec = p.spec()
        assert spec.category == "environment" and spec.static and spec.shape_class == "assembly", slug
        ProductSpec_round = type(spec).from_dict(spec.to_dict())
        assert ProductSpec_round.slug == slug


def test_ceiling_mounted(products):
    ceiling = {s for s, p in products.items() if p.mount == "ceiling"}
    assert ceiling == {"ceiling_panel", "ceiling_base_light", "downlight", "aisle_sign_hanging"}


@pytest.mark.parametrize("slug, link, kind, axis, limits", [
    ("toilet_door", "LeafLink", "revolute", "Z", [0.0, 90.0]),  # 左の蝶番で奥へ
    ("staff_office_door", "LeafLink", "revolute", "Z", [-90.0, 0.0]),  # 右の蝶番で奥へ
    ("backyard_swing_door", "LeafLink", "revolute", "Z", [-90.0, 90.0]),  # 両方向
    ("toilet_bowl", "LidLink", "revolute", "X", [-105.0, 0.0]),  # 便ふたは上へ
])
def test_hinged_parts(products, slug, link, kind, axis, limits):
    p = products[slug]
    (j,) = p.joints
    assert (j.link, j.type, j.axis, j.limits) == (link, kind, axis, limits)
    moving = [x for x in p.parts if x.link == link]
    assert moving and any(x.collision for x in moving)
    assert all(x.link in (None, link) for x in p.parts)


def test_automatic_door_slides_apart(products):
    p = products["automatic_door"]
    js = {j.link: j for j in p.joints}
    assert set(js) == {"Leaf0Link", "Leaf1Link"}
    assert all(j.type == "prismatic" and j.axis == "X" for j in js.values())
    assert js["Leaf0Link"].limits[0] < 0 == js["Leaf0Link"].limits[1]  # 左の戸は左へ
    assert js["Leaf1Link"].limits[0] == 0 < js["Leaf1Link"].limits[1]  # 右の戸は右へ


@pytest.mark.parametrize("slug, lo, hi", [("ceiling_base_light", 150, 400), ("downlight", 40, 150)])
def test_ceiling_lights_light_the_floor(products, slug, lo, hi):
    """天井の器具 1 台が、2 m 下の床（真下）を照らす照度の目安。"""
    lights = [asdict(x) for x in products[slug].lights]
    assert len(lights) == 1
    assert lo <= illuminance(lights, [0, 0, -2.0], [0, 0, 1]) <= hi


def test_sanitaryware_is_ceramic():
    from agentic_usd_gen.nonvisual import nonvisual_material
    from agentic_usd_gen.semantics import part_labels
    assert part_labels("ceramic", "glossy") == ["ceramic"]
    assert nonvisual_material({"labels": ["ceramic"]})[0] == "ceramic_glass"
    assert nonvisual_material({"labels": part_labels("fiberglass", "plastic")})[0] == "fiberglass"
