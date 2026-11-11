"""すべての架空の商品（slug → 定義を返す関数）。"""

from __future__ import annotations

from . import (drug_baby, drug_cosmetics, drug_fixtures, drug_medicine, super_checkout, super_fixtures, super_fresh, super_produce, conv_deli, conv_snacks, drinks_more, goods_more, store_more,
               conv_drinks, conv_food, conv_goods, conv_sweets, drinks_large, food_fresh_snack, food_pantry, household_cleaning,
               household_personal, products, store_counter, store_env, store_equipment, store_floor)

PRODUCTS = {**products.PRODUCTS, **food_pantry.PRODUCTS, **food_fresh_snack.PRODUCTS, **household_cleaning.PRODUCTS,
            **household_personal.PRODUCTS, **conv_drinks.PRODUCTS, **conv_food.PRODUCTS, **conv_goods.PRODUCTS,
            **store_equipment.PRODUCTS, **store_floor.PRODUCTS, **store_counter.PRODUCTS,
            **conv_sweets.PRODUCTS, **drinks_large.PRODUCTS,
            **conv_deli.PRODUCTS, **conv_snacks.PRODUCTS, **drinks_more.PRODUCTS, **goods_more.PRODUCTS,
            **store_more.PRODUCTS, **store_env.PRODUCTS, **super_fixtures.PRODUCTS,
            **super_checkout.PRODUCTS, **super_produce.PRODUCTS, **super_fresh.PRODUCTS,
            **drug_fixtures.PRODUCTS, **drug_medicine.PRODUCTS, **drug_cosmetics.PRODUCTS, **drug_baby.PRODUCTS}
assert len(PRODUCTS) == sum(len(m.PRODUCTS) for m in (products, food_pantry, food_fresh_snack, household_cleaning,
                                                       household_personal, conv_drinks, conv_food, conv_goods,
                                                       store_equipment, store_floor, store_counter, conv_sweets,
                                                       drinks_large, conv_deli, conv_snacks, drinks_more,
                                                       goods_more, store_more, store_env, super_fixtures,
                                                       super_checkout, super_produce, super_fresh,
                                                       drug_fixtures, drug_medicine, drug_cosmetics, drug_baby)), "slug が重複しています"

# Home center and 100-yen shop. A separate block keeps merges simple.
from . import hc_daily, hc_fixtures, hc_garden, hc_tools  # noqa: E402

for _m in (hc_tools, hc_garden, hc_daily, hc_fixtures):
    _dup = PRODUCTS.keys() & _m.PRODUCTS.keys()
    assert not _dup, f"slug が重複しています: {sorted(_dup)}"
    PRODUCTS.update(_m.PRODUCTS)

# Bookstore, electronics store and apparel store. A separate block keeps merges simple.
from . import apparel_fixtures, apparel_goods, book_fixtures, book_goods, elec_fixtures, elec_goods  # noqa: E402

for _m in (book_goods, book_fixtures, elec_goods, elec_fixtures, apparel_goods, apparel_fixtures):
    _dup = PRODUCTS.keys() & _m.PRODUCTS.keys()
    assert not _dup, f"slug が重複しています: {sorted(_dup)}"
    PRODUCTS.update(_m.PRODUCTS)

# Backyard and logistics fixtures and materials. A separate block keeps merges simple.
from . import backyard  # noqa: E402

_dup = PRODUCTS.keys() & backyard.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(backyard.PRODUCTS)

# Cafe and bakery. A separate block keeps merges simple.
from . import bakery, cafe  # noqa: E402

for _m in (cafe, bakery):
    _dup = PRODUCTS.keys() & _m.PRODUCTS.keys()
    assert not _dup, f"slug が重複しています: {sorted(_dup)}"
    PRODUCTS.update(_m.PRODUCTS)

# More products for the existing sales floors.
from . import shelf_more  # noqa: E402

for _m in (shelf_more,):
    _dup = PRODUCTS.keys() & _m.PRODUCTS.keys()
    assert not _dup, f"slug が重複しています: {sorted(_dup)}"
    PRODUCTS.update(_m.PRODUCTS)

# Plant factory: strawberry growing racks, a potted plant and AGV guide tape (not store goods).
from . import farm  # noqa: E402

_dup = PRODUCTS.keys() & farm.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(farm.PRODUCTS)

# Windows, curtains and roll screens: building fittings for homes, offices and shops.
from . import windows  # noqa: E402

_dup = PRODUCTS.keys() & windows.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(windows.PRODUCTS)

# Family restaurant and izakaya: seating, tabletop goods, tableware, plated dishes, service equipment and the kitchen.
# A separate block keeps merges simple.
from . import (restaurant_dining, restaurant_equipment, restaurant_food, restaurant_kitchen,  # noqa: E402
               restaurant_tableware)

for _m in (restaurant_dining, restaurant_tableware, restaurant_food, restaurant_equipment, restaurant_kitchen):
    _dup = PRODUCTS.keys() & _m.PRODUCTS.keys()
    assert not _dup, f"slug が重複しています: {sorted(_dup)}"
    PRODUCTS.update(_m.PRODUCTS)

# Interior finishes and ceiling equipment: partitions, floor and wall finishes, ceiling fittings.
# A separate block keeps merges simple.
from . import interior  # noqa: E402

_dup = PRODUCTS.keys() & interior.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(interior.PRODUCTS)

# Florist, toy store, pet shop, shoe store and optician goods.
# A separate block keeps merges simple.
from . import store_kinds  # noqa: E402

_dup = PRODUCTS.keys() & store_kinds.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(store_kinds.PRODUCTS)

# Fixtures and goods of various shops and rooms: home decor, pet
# shop cases, liquor store displays, store fixtures, electronics, garden centre, whiteboard and wheelchair.
from . import misc_shops  # noqa: E402

_dup = PRODUCTS.keys() & misc_shops.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(misc_shops.PRODUCTS)

# Specialty shops: bicycle
# shop, woven baskets, wagashi shop, record shop, sports shop, furniture, cosmetics, souvenir shop, Asian grocery.
from . import specialty_shops  # noqa: E402

_dup = PRODUCTS.keys() & specialty_shops.PRODUCTS.keys()
assert not _dup, f"slug が重複しています: {sorted(_dup)}"
PRODUCTS.update(specialty_shops.PRODUCTS)
