"""窓・カーテン・ロールスクリーン（windows.py、カテゴリ environment）のテスト。"""

import pytest

from agentic_usd_gen.fictional import registry, windows


@pytest.fixture(scope="module")
def products():
    return {slug: f() for slug, f in windows.PRODUCTS.items()}


def test_registered_static_environment(products):
    for slug, p in products.items():
        assert slug in registry.PRODUCTS
        spec = p.spec()
        assert spec.category == "environment" and spec.static and spec.shape_class == "assembly", slug
        assert type(spec).from_dict(spec.to_dict()).slug == slug


@pytest.mark.parametrize("slug, w, h", [
    ("sliding_window_waist", 1.69, 1.17), ("sliding_window_floor", 1.69, 2.03), ("bathroom_window", 0.64, 0.57),
    ("fixed_window", 1.19, 1.17), ("casement_window", 0.405, 0.97),
])
def test_window_frame_size(products, slug, w, h):
    """枠の外寸（幅・高さ）が開口の寸法になる。原点は枠の下端の中央。"""
    parts = [p for p in products[slug].parts if p.name.startswith("Frame")]
    xs = [p.center[0] + s * p.size[0] / 2 for p in parts for s in (-1, 1)]
    zs = [p.center[2] + s * p.size[2] / 2 for p in parts for s in (-1, 1)]
    assert min(xs) == pytest.approx(-w / 2) and max(xs) == pytest.approx(w / 2)
    assert min(zs) == pytest.approx(0.0) and max(zs) == pytest.approx(h)


@pytest.mark.parametrize("slug", ["sliding_window_waist", "sliding_window_floor", "bathroom_window"])
def test_sliding_sashes(products, slug):
    """室内側（-Y）の右の障子は左へ、室外側の左の障子は右へ、網戸は右の障子と一緒に左へ動く。"""
    js = {j.link: j for j in products[slug].joints}
    assert set(js) == {"InnerLink", "OuterLink", "ScreenLink"}
    assert all(j.type == "prismatic" and j.axis == "X" for j in js.values())
    assert js["InnerLink"].limits[0] < 0 == js["InnerLink"].limits[1]
    assert js["OuterLink"].limits[0] == 0 < js["OuterLink"].limits[1]
    assert js["InnerLink"].anchor[1] < 0 < js["OuterLink"].anchor[1] < js["ScreenLink"].anchor[1]
    assert js["InnerLink"].anchor[0] > 0 > js["OuterLink"].anchor[0]


def test_bathroom_glass_is_frosted(products):
    glass = [p for p in products["bathroom_window"].parts if p.name.endswith("Glass")]
    assert glass and all(p.finish == "frosted" for p in glass)


def test_casement_opens_outward(products):
    (j,) = products["casement_window"].joints
    assert (j.link, j.type, j.axis, j.limits) == ("LeafLink", "revolute", "Z", [0.0, 70.0])


@pytest.mark.parametrize("slug", ["curtain_waist_window", "curtain_floor_window", "roll_screen"])
def test_fabric_has_no_collider(products, slug):
    """生地（fabric）は当たり判定なし。レール・ケースなど固い部品だけが当たる。"""
    parts = products[slug].parts
    assert all(not p.collision for p in parts if p.material == "fabric")
    assert any(p.collision for p in parts)
