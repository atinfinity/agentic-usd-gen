"""マテリアルの意味ラベル（SimReady の SL.MAT.001: すべての Material に semantics:labels:material を付ける）。

ラベルは英語の素材名（plastic / metal / glass / paper / wood / liquid / food など）。
"""

from __future__ import annotations

# 容器の素材（spec.json の container_material。日本語のこともある）→ ラベル。上から順に当てる
_KEYWORDS: list[tuple[tuple[str, ...], list[str]]] = [
    (("alumi", "アルミ"), ["metal", "aluminum"]),
    (("steel", "スチール", "tin", "ブリキ"), ["metal", "steel"]),
    # 陶器・FRP は名前に glass を含むことがあるので、ガラスより先に当てる
    (("ceramic", "陶器", "porcelain", "磁器"), ["ceramic"]),
    (("fiberglass", "frp"), ["fiberglass"]),
    (("glass", "ガラス", "瓶"), ["glass"]),
    (("paper", "紙", "cardboard", "段ボール", "carton"), ["paper"]),
    (("wood", "木"), ["wood"]),
    (("metal", "金属"), ["metal"]),
    (("plastic", "pet", "ペット", "film", "フィルム", "urethane", "ウレタン", "樹脂", "polyethylene", "ポリエチレン",
      "hdpe", "ldpe", "vinyl", "ビニール"), ["plastic"]),
]
FINISH_LABELS = {"metal": ["metal"], "glass": ["glass"]}  # 部品の finish → ラベル（それ以外は plastic）
LIQUID = ["liquid"]

# 中身の濁り（0 = 澄んでいる 〜 1 = ほぼ不透明）。商品名・タグの語から推定する。上から順に当てる
_TURBIDITY: list[tuple[tuple[str, ...], float]] = [
    (("牛乳", "ミルク", "milk", "ラテ", "latte", "カフェオレ", "乳飲料", "乳酸菌", "飲むヨーグルト", "豆乳",
      "カルピス", "スムージー", "smoothie", "ごまドレッシング", "sesame dressing", "クリーミー", "creamy"), 0.95),
    (("炭酸", "ソーダ", "soda", "サイダー", "cider", "コーラ", "cola", "スパークリング", "sparkling"), 0.0),
    (("オレンジ", "orange", "混濁", "にごり", "濁り", "野菜ジュース", "トマト", "tomato", "ポタージュ"), 0.7),
    (("スポーツドリンク", "sports drink", "イオン飲料", "経口補水"), 0.25),
]


def liquid_turbidity(product_name: str, tags: list[str] | None = None) -> float:
    """商品名とタグから中身の濁りを推定する。当てはまらなければ 0（澄んでいる）。"""
    text = " ".join([product_name, *(tags or [])]).lower()
    for keys, value in _TURBIDITY:
        if any(k in text for k in keys):
            return value
    return 0.0


def _match(material: str) -> list[str] | None:
    m = material.lower()
    for keys, labels in _KEYWORDS:
        if any(k in m for k in keys):
            return list(labels)
    return None


def container_labels(container_material: str | None, default: str = "plastic") -> list[str]:
    """容器の素材のラベル。不明なら default。"""
    if not container_material:
        return [default]
    return _match(container_material) or [default]


def part_labels(material: str | None, finish: str) -> list[str]:
    """組み合わせの部品のラベル。Part.material があればそれ（知らない語はそのまま）、なければ finish から決める。"""
    if material:
        return _match(material) or [material.strip().lower()]
    return list(FINISH_LABELS.get(finish, ["plastic"]))
