"""商品の種類を表す Wikidata の Q コード（SimReady の SR.004 の qcode）を決める。

spec.json に qcode があればそれを使う。なければ slug に含まれる語を上から順に照らし、
どれにも当たらなければカテゴリの既定値を使う。表の Q コードは Wikidata で確かめたもの。
"""

from __future__ import annotations

import re

# slug に含まれる語 → Q コード。_ 区切りの語の単位で照らす（chocolate に cola は当たらない）。
# より具体的な語を先に置く（coffee_machine は coffee より先、など）
_KEYWORDS: list[tuple[str, str]] = [
    # 店舗の設備
    ("a_frame_sign", "Q690700"),  # sandwich board
    ("atm", "Q81235"),  # automated teller machine
    ("bun_steamer", "Q1158805"),  # food steamer
    ("self_checkout", "Q1568124"),
    ("checkout_counter", "Q20820316"),  # checkout
    ("chest_freezer", "Q20191013"),
    ("coffee_machine", "Q211841"),  # coffeemaker
    ("digital_signage", "Q756568"),
    ("stool", "Q33163"),
    ("gondola_shelf", "Q45242859"),  # shelf
    ("hot_snack_case", "Q55611850"),  # food warmer
    ("oden_warmer", "Q55611850"),
    ("hot_water_dispenser", "Q16630809"),
    ("magazine_rack", "Q107194252"),
    ("microwave", "Q127956"),
    ("copier", "Q279433"),  # multifunction printer
    ("showcase", "Q21012173"),  # refrigerated display case
    ("cooler", "Q21012173"),
    ("security_camera", "Q334415"),
    ("shopping_basket", "Q1308084"),
    ("shopping_cart", "Q796894"),
    ("trash_station", "Q4743886"),  # recycling bin
    # 飲料
    ("beer", "Q44"),
    ("chuhai", "Q1047326"),
    ("energy_drink", "Q215754"),
    ("nutrition_drink", "Q215754"),
    ("sports_drink", "Q949948"),
    ("lactic_drink", "Q3506176"),  # fermented milk product
    ("milk_tea", "Q1884224"),
    ("milk", "Q8495"),
    ("instant_coffee", "Q858049"),
    ("chilled_cup_coffee", "Q841774"),  # latte
    ("canned_coffee", "Q5032637"),
    ("can_coffee", "Q5032637"),
    ("coffee", "Q8486"),
    ("green_tea_bag", "Q863250"),  # tea bag
    ("green_tea", "Q484083"),
    ("barley_tea", "Q31625"),
    ("hojicha", "Q1652744"),
    ("mineral_water", "Q178921"),
    ("sparkling_water", "Q264554"),  # carbonated water
    ("cola", "Q134041"),
    ("soda", "Q147538"),  # soft drink
    ("orange_juice", "Q219059"),
    ("vegetable_juice", "Q1501257"),
    ("jelly_drink", "Q4545971"),  # gelatin dessert
    # 食品
    ("bento", "Q380532"),
    ("gum", "Q130878"),
    ("cookie", "Q13266"),
    ("candy_bag", "Q1788872"),  # cough drop（のど飴）
    ("gummy", "Q12964402"),
    ("chocolate_bar", "Q1361086"),
    ("cooked_rice", "Q523224"),
    ("rice_bag", "Q5090"),  # rice
    ("rice_cracker", "Q198788"),  # senbei
    ("cream_puff", "Q2513811"),
    ("miso_soup", "Q471866"),
    ("yakisoba", "Q1144102"),
    ("cup_noodle", "Q13163896"),
    ("instant_ramen", "Q1051265"),
    ("curry_roux", "Q115618401"),  # curry sauce
    ("retort_curry", "Q701870"),  # Japanese curry
    ("daifuku", "Q1067842"),
    ("dorayaki", "Q1051482"),
    ("fish_sausage", "Q11674068"),
    ("fried_chicken", "Q1104399"),  # karaage
    ("granola", "Q119203"),
    ("ice_bar", "Q855373"),  # ice pop
    ("ice_cream", "Q13233"),
    ("rock_ice", "Q488463"),  # ice cube
    ("mackerel_can", "Q5032629"),  # canned fish
    ("tuna_can", "Q5711293"),
    ("peach_can", "Q67891942"),  # canned peaches
    ("mayonnaise", "Q167893"),
    ("melon_pan", "Q1919688"),
    ("mint_tablet", "Q5254978"),  # mint confectionery
    ("mont_blanc", "Q182940"),  # dessert
    ("natto", "Q505711"),
    ("potato_chips", "Q173265"),
    ("processed_cheese", "Q1570052"),
    ("pudding", "Q125999569"),  # custard pudding
    ("roll_cake", "Q320657"),  # Swiss roll
    ("salad", "Q9266"),
    ("salt_pepper", "Q7405972"),
    ("dressing", "Q1572278"),
    ("sliced_bread", "Q27645375"),
    ("stick_snack", "Q123093204"),  # cheese stick
    ("snack", "Q749316"),
    ("soy_sauce", "Q229385"),
    ("spaghetti", "Q20026"),
    ("jam", "Q74048276"),  # fruit preserves
    ("shortcake", "Q2706994"),
    ("tiramisu", "Q131582"),
    ("tofu", "Q177378"),
    ("yogurt", "Q13317"),
    # 日用品
    ("aa_battery", "Q1195592"),
    ("adhesive_bandage", "Q216054"),
    ("aluminum_foil", "Q447349"),
    ("ballpoint_pen", "Q160137"),
    ("bath_salts", "Q798972"),
    ("cleaner", "Q1974312"),  # cleaning product
    ("body_soap", "Q1267611"),  # shower gel
    ("pocket_tissue", "Q4795516"),  # facial tissue
    ("box_tissue", "Q4795516"),
    ("cooling_gel", "Q11395322"),
    ("cotton_swab", "Q12201"),
    ("deodorant", "Q309035"),
    ("deodorizer", "Q2419566"),  # air freshener
    ("dish_soap", "Q1517816"),
    ("face_mask", "Q10282403"),
    ("food_wrap", "Q356700"),  # plastic wrap
    ("hand_sanitizer", "Q520181"),
    ("hand_soap", "Q97925317"),  # liquid soap
    ("insect_repellent", "Q123682686"),
    ("bleach", "Q407204"),  # sodium hypochlorite
    ("sponge", "Q1210980"),
    ("laundry_detergent", "Q910284"),
    ("lip_balm", "Q1518347"),
    ("mouthwash", "Q518968"),
    ("newspaper", "Q11032"),
    ("paper_towel", "Q1151042"),
    ("gift_card", "Q554910"),
    ("rubber_gloves", "Q1039512"),
    ("shampoo", "Q180204"),
    ("skin_cream", "Q3006091"),  # moisturizer
    ("stockings", "Q276389"),  # pantyhose
    ("sunscreen", "Q827658"),
    ("toilet_paper", "Q5840"),
    ("toothbrush", "Q134205"),
    ("toothpaste", "Q35855"),
    ("trash_bags", "Q1197414"),  # bin bag
    ("usb_cable", "Q106763309"),
    ("umbrella", "Q41607"),
    ("magazine", "Q41298"),
    ("wet_wipes", "Q2916237"),
    # 汎用（最後に照らす）
    ("water", "Q1049049"),  # bottled water
    ("juice", "Q8492"),
    ("cheese", "Q10943"),
    ("cake", "Q13276"),
    ("counter", "Q14745"),  # furniture
]

CATEGORY_DEFAULTS = {
    "beverage": "Q40050",  # drink
    "food": "Q2095",  # food
    "household": "Q369594",  # household goods
    "fixture": "Q14745",  # furniture
}
FALLBACK = "Q223557"  # physical object

_QCODE = re.compile(r"^Q\d+$")


def is_qcode(s: str | None) -> bool:
    return bool(s and _QCODE.match(s))


def lookup(slug: str, category: str | None = None, override: str | None = None) -> str:
    """slug（とカテゴリ）から Q コードを返す。override が正しい形ならそれを優先する。"""
    if is_qcode(override):
        return override
    padded = f"_{slug}_"
    for word, q in _KEYWORDS:
        if f"_{word}_" in padded:
            return q
    return CATEGORY_DEFAULTS.get(category or "", FALLBACK)
