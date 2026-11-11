"""ドラッグストアの什器（drug_fixtures）と商品（drug_medicine・drug_cosmetics・drug_baby）のテスト。"""

import pytest

from agentic_usd_gen.fictional import drug_baby, drug_cosmetics, drug_fixtures, drug_medicine

from .test_super_fixtures import PLACES, _shelves

GOODS = {**drug_medicine.PRODUCTS, **drug_cosmetics.PRODUCTS, **drug_baby.PRODUCTS}


@pytest.mark.parametrize("slug", sorted(drug_fixtures.PRODUCTS))
def test_fixture_spec(slug):
    spec = drug_fixtures.PRODUCTS[slug]().spec()
    assert spec.static and spec.slug == slug
    if slug == "waiting_bench_3seat":  # 絵柄のない待合のベンチ
        assert not spec.picture_places
        return
    assert spec.picture_places and set(spec.picture_places) <= PLACES | {"drugstore"}
    assert [p for p in spec.parts if p.faces and p.blank is not None], "看板・POP は無地に切り替えられること"
    if slug != "prescription_sign_hanging":
        assert _shelves(spec), "商品を並べる水平の板があること"


def test_moving_parts():
    case = drug_fixtures.PRODUCTS["locked_medicine_case"]().spec()
    assert len(case.joints) == 2 and all(j.type == "prismatic" for j in case.joints)
    rack = drug_fixtures.PRODUCTS["rotating_accessory_rack"]().spec()
    assert len(rack.joints) == 1 and rack.joints[0].type == "revolute" and rack.joints[0].axis == "Z"
    assert rack.joints[0].limits is None, "回転ラックは限界なしで回り続けること"


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods_spec(slug):
    spec = GOODS[slug]().spec()
    assert not spec.static and spec.mass_kg > 0 and spec.slug == slug
    assert GOODS[slug]().description and spec.tags


# 商品 → 並べる什器。商品を並べるツールはこの什器の棚板に並べる
HOME = {**{s: "medicine_shelf_gondola" for s in drug_medicine.PRODUCTS},
        **{s: "cosmetics_tester_stand" for s in drug_cosmetics.PRODUCTS},
        **{s: "baby_care_shelf" for s in drug_baby.PRODUCTS}}
HEAD = 0.01  # 商品を並べるツールが商品の上に空ける隙間 [m]


def _levels(spec):
    """棚板ごとの（上面の高さ, 短辺, 上の部品までの空き or None）。上の部品は値札レールなども含める（商品を並べるツールより厳しめ）。"""
    names, out = set(_shelves(spec)), []
    for b in spec.parts:
        if b.name not in names:
            continue
        (x, y, z), (w, d, t) = b.center, b.size
        top = z + t / 2
        above = [p.center[2] - p.size[2] / 2 for p in spec.parts
                 if p is not b and p.center[2] - p.size[2] / 2 >= top - 1e-6
                 and abs(p.center[0] - x) < (p.size[0] + w) / 2 and abs(p.center[1] - y) < (p.size[1] + d) / 2]
        out.append((top, min(w, d), min(above) - top if above else None))
    return sorted(out)


def test_home_covers_goods():
    assert set(HOME) == set(GOODS) and set(HOME.values()) <= set(drug_fixtures.PRODUCTS)


@pytest.mark.parametrize("slug", sorted(GOODS))
def test_goods_fit_bottom_level(slug):
    """大きな商品は一番下の段に置くので、どの商品も並べる什器の一番下の段に入ること（1 kg のプロテインの袋など）。"""
    dims = GOODS[slug]().spec().dimensions
    depth = dims.depth if dims.depth is not None else dims.diameter
    top, side, clear = _levels(drug_fixtures.PRODUCTS[HOME[slug]]().spec())[0]
    assert clear is None or dims.height + HEAD <= clear, f"{slug} {dims.height} m > 空き {clear} m（{HOME[slug]}）"
    assert min(dims.diameter, depth) <= side
