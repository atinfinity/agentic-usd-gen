"""Wikidata の Q コード（SimReady の SR.004）のテスト。"""

from agentic_usd_gen.qcode import FALLBACK, is_qcode, lookup


def test_lookup_specific_first():
    assert lookup("coffee_machine", "fixture") == "Q211841"  # coffee より先
    assert lookup("green_tea_bag_box", "food") == "Q863250"  # green_tea より先
    assert lookup("milk_tea_pet_500ml", "beverage") == "Q1884224"  # milk より先


def test_word_boundary():
    assert lookup("chocolate_bar", "food") == "Q1361086"  # cola に当たらない
    assert lookup("gummy_candy_pouch", "food") == "Q12964402"  # gum に当たらない


def test_fallbacks():
    assert lookup("mystery_drink", "beverage") == "Q40050"
    assert lookup("mystery", None) == FALLBACK
    assert lookup("cola_pet_1500ml", "beverage", override="Q42") == "Q42"
    assert lookup("cola_pet_1500ml", "beverage", override="cola") == "Q134041"  # 形が違えば無視
    assert is_qcode("Q1") and not is_qcode("q1") and not is_qcode("")
