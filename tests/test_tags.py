"""検索用のタグの「中身 + 容器」の英語の句（catalog.container_phrases / asset_tags）。"""

import pytest

from agentic_usd_gen.catalog import asset_tags, container_phrases


def _asset(slug, category="beverage", shape="revolve", material="PET"):
    return {"slug": slug, "category": category, "shape_class": shape, "container_material": material,
            "physics": {}}


@pytest.mark.parametrize("asset, extra, want", [
    # PET の飲料: 容器は "PET bottle" から。bottled も付ける
    (_asset("green_tea_pet_600ml"), ["PET", "緑茶", "ペットボトル", "green tea", "PET bottle"],
     ["green tea bottle", "bottled green tea"]),
    # 金属の回転体は can。すでにある句（canned coffee）は足さない
    (_asset("canned_coffee_185g", material="steel"), ["steel", "coffee", "canned coffee"], ["coffee can"]),
    # 中身の語の canned は外す（"canned peach can" にしない）
    (_asset("peach_can", "food", material="steel"), ["steel", "canned peach", "peach"], ["peach can"]),
    # 容量・材質は中身にしない。ガラスでも slug が jar なら jar
    (_asset("instant_coffee_jar", "food", material="glass"), ["glass", "200g", "instant coffee"], ["instant coffee jar"]),
    # 食品の瓶には bottled を付けない
    (_asset("soy_sauce_pet", "food"), ["PET", "soy sauce", "seasoning"], ["soy sauce bottle"]),
    # 容器の語のタグ（juice box）から容器を決める
    (_asset("vegetable_juice_pack_200ml", shape="box", material="paper"), ["paper", "vegetable juice", "juice box"],
     ["vegetable juice box"]),
    # 中身と容器がすでに 1 つの句（milk carton）なら何も足さない
    (_asset("milk_carton_1l", shape="assembly", material="paper"), ["paper", "1000ml", "milk", "milk carton"], []),
    # 袋・箱の食品はスラッグの bag・pouch・box から（green_tea_bag_box は最後の box）
    (_asset("potato_chips_bag", "food", "pouch", "film"), ["film", "potato chips", "snack"], ["potato chips bag"]),
    (_asset("green_tea_bag_box", "food", "box", "paper"), ["paper", "green tea", "tea bags"], ["green tea box"]),
    # すでにある句（rice bag）は足さない。スラッグで容器が分からないもの（chocolate_bar）には作らない
    (_asset("rice_bag_5kg", "food", "pouch", "film"), ["film", "5kg", "rice", "rice bag"], []),
    (_asset("chocolate_bar", "food", "pouch", "film"), ["film", "chocolate bar", "snack"], []),
    # 樹脂の回転体はスラッグの bottle・pump でボトルと分かるときだけ bottle。飲料でないので bottled は付けない
    (_asset("mayonnaise_bottle", "food", material="plastic"), ["plastic", "mayonnaise", "seasoning"],
     ["mayonnaise bottle"]),
    (_asset("pudding_cup", "food", material="plastic"), ["plastic", "pudding", "dessert"], []),
    # 日用品はスラッグでボトルと分かるものだけ（pump bottle は中身にしない）
    (_asset("shampoo_pump", "household", material="plastic"), ["plastic", "shampoo", "hair care", "pump bottle"],
     ["shampoo bottle"]),
    (_asset("deodorant_spray_150g", "household", material="aluminum"), ["aluminum", "deodorant", "spray"], []),
    (_asset("bathroom_cleaner_trigger", "household", "assembly", "plastic"), ["plastic", "bath cleaner", "spray bottle"],
     []),
])
def test_container_phrases(asset, extra, want):
    assert container_phrases(asset, extra) == want


def test_asset_tags_appends_phrases():
    """句は spec.json の tags のあとに付き、重ならない。"""
    tags = asset_tags(_asset("cola_pet_1500ml"), ["コーラ", "cola", "PET bottle", "cola bottle"])
    assert tags == ["beverage", "飲料", "revolve", "回転体", "PET", "コーラ", "cola", "PET bottle", "cola bottle",
                    "bottled cola"]
