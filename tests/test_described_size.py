"""説明の「幅・奥行き・高さ」は外形で、寸法と 5% 以内で合う（取っ手・扉・キャスターの出っ張りを含めた値）。"""

import pytest

from agentic_usd_gen.fictional import (
    elec_fixtures,
    interior,
    misc_shops,
    products,
    restaurant_kitchen,
    specialty_shops,
    store_env,
    super_checkout,
)
from agentic_usd_gen.shapes.assembly import described_size_warnings

FIXED = {
    "shopping_basket": products, "hand_wash_basin": store_env, "sample_table": super_checkout,
    "appliance_display_platform": elec_fixtures, "kitchen_fridge_2door": restaurant_kitchen,
    "cold_table": restaurant_kitchen, "gas_range": restaurant_kitchen, "floor_fryer": restaurant_kitchen,
    "sink_2bowl": restaurant_kitchen, "dishwasher_door": restaurant_kitchen, "wood_slat_wall_panel": interior,
    "chrome_wire_shelf": misc_shops, "nightstand": specialty_shops, "wardrobe": specialty_shops,
}


@pytest.mark.parametrize("slug", sorted(FIXED))
def test_description_gives_the_outer_size(slug):
    p = getattr(FIXED[slug], slug)()
    assert described_size_warnings(p.description, p.dims) == []
