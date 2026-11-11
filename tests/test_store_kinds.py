"""花屋・おもちゃ屋・ペットショップ・靴屋・眼鏡店の商品と什器のテスト。"""

import pytest

from agentic_usd_gen.fictional import store_kinds

ALL = store_kinds.PRODUCTS


@pytest.mark.parametrize("slug", sorted(ALL))
def test_spec(slug):
    spec = ALL[slug]().spec()
    assert spec.slug == slug and spec.mass_kg > 0 and spec.tags


def test_cut_flowers_collide_only_with_the_bucket():
    """花・茎・値札は当たり判定なし。桶だけが当たるので、剛体ごと立って花が転がらない。"""
    spec = store_kinds.cut_flower_bucket().spec()
    assert [p.name for p in spec.parts if p.collision] == ["Bucket"]
    assert spec.variant_sets == {"Flower": store_kinds.FLOWERS}
    for name in store_kinds.FLOWERS:
        shown = [p for p in spec.parts if p.show and name in p.show["Flower"]]
        assert len(shown) > 10, name
    assert {"cut flowers", "flower bouquet", "bouquet"} <= set(spec.tags)


def test_bucket_foot_is_flat():
    """PhysX は凸包を 64 頂点に減らす。床のすぐ上に面取りの輪があると、減らした凸包が傾いて立つ（3.7°）。"""
    spec = store_kinds.cut_flower_bucket().spec()
    bucket = next(p for p in spec.parts if p.name == "Bucket")
    outer_low = [z for r, z in bucket.profile if r > 0 and 0 < z * bucket.size[2] < 0.01]
    assert not outer_low


@pytest.mark.parametrize("slug,colliders", [("building_blocks_tub", {"Tub", "Lid"}), ("plush_bear", {"Body", "Head"}),
                                           ("toy_car_blister", {"Card"})])
def test_toys_collide_with_a_few_parts(slug, colliders):
    """中のブロック・手足・車は見た目だけ。当たり判定は外形の少数の部品。"""
    spec = ALL[slug]().spec()
    assert {p.name for p in spec.parts if p.collision} == colliders


def test_toy_tags_match_the_toy_store_stock():
    """toy_store の飾りを探す語で見つかる。"""
    tags = set().union(*(ALL[s]().spec().tags for s in ("toy_car_box", "building_blocks_tub", "plush_bear",
                                                         "toy_car_blister")))
    assert {"toy car", "building blocks", "stuffed animal", "toy box", "toy blister pack"} <= tags


def test_dog_toy_rests_on_its_knobs():
    """ほねは両端の 4 つの玉だけが当たり、底が床（z=0）にそろう。"""
    spec = store_kinds.dog_toy().spec()
    knobs = [p for p in spec.parts if p.collision]
    assert len(knobs) == 4 and all(p.name.startswith("Knob") for p in knobs)
    assert all(abs(p.center[2] - p.size[2] / 2) < 1e-9 for p in knobs)


def test_pet_tags_match_the_pet_shop_stock():
    """pet_shop の飾りを探す語で見つかる。"""
    from agentic_usd_gen.fictional import shelf_more
    tags = set().union(*(ALL[s]().spec().tags for s in ("cat_food_can", "dog_toy", "pet_toy_blister", "dog_treat_bag")),
                       shelf_more.dog_food_bag().spec().tags)
    assert {"pet food bag", "pet food can", "pet toy", "pet toy blister pack", "pet treat bag"} <= tags


def test_leather_shoe_stands_on_its_sole():
    """革靴は靴底だけが当たり、甲・かかとは見た目だけ。"""
    spec = store_kinds.leather_shoe().spec()
    assert [p.name for p in spec.parts if p.collision] == ["Sole"]


def test_shoe_tags_match_the_shoe_store_stock():
    """shoe_store の飾りを探す語で見つかる。スニーカーと靴箱は衣料品店のものを使う。"""
    from agentic_usd_gen.fictional import apparel_goods
    tags = set().union(*(ALL[s]().spec().tags for s in ("leather_shoe", "shoe_insole_pack", "shoelace_blister")),
                       apparel_goods.sneaker().spec().tags, apparel_goods.shoe_box().spec().tags)
    assert {"sneaker", "shoe box", "shoebox", "leather shoe", "shoe insole pack", "shoelace blister pack"} <= tags


def test_eyeglasses_stand_on_rims_and_temples():
    """眼鏡は枠とつるの先で立ち、レンズ・鼻あて・ブリッジは見た目だけ。"""
    spec = store_kinds.eyeglasses().spec()
    assert {p.name for p in spec.parts if p.collision} == {"RimL", "RimR", "TempleL", "TempleR"}


def test_eye_tags_match_the_optician_stock():
    """optician の飾りを探す語で見つかる。"""
    tags = set().union(*(ALL[s]().spec().tags for s in ("eyeglasses", "glasses_case", "glasses_cleaner_blister")))
    assert {"eyeglasses", "glasses case", "glasses cleaner blister pack"} <= tags
