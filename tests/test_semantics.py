"""マテリアルの意味ラベルのテスト。"""

from agentic_usd_gen.semantics import container_labels, liquid_turbidity, part_labels


def test_container_labels():
    assert container_labels(None) == ["plastic"]
    assert container_labels(None, "paper") == ["paper"]
    assert container_labels("PET") == ["plastic"]
    assert container_labels("アルミ") == ["metal", "aluminum"]
    assert container_labels("steel") == ["metal", "steel"]
    assert container_labels("glass") == ["glass"]
    assert container_labels("紙") == ["paper"]
    assert container_labels("clear plastic") == ["plastic"]
    assert container_labels("film") == ["plastic"]
    assert container_labels("wood") == ["wood"]
    assert container_labels("HDPE (translucent)") == ["plastic"]
    assert container_labels("frosted glass") == ["glass"]


def test_part_labels():
    assert part_labels(None, "metal") == ["metal"]
    assert part_labels(None, "glass") == ["glass"]
    assert part_labels(None, "matte") == ["plastic"]
    assert part_labels(None, "frosted") == ["plastic"] and part_labels(None, "translucent") == ["plastic"]
    assert part_labels("food", "matte") == ["food"]
    assert part_labels("Wood", "plastic") == ["wood"]


def test_liquid_turbidity():
    """中身の濁りを商品名・タグから推定する。澄んだ飲み物は 0。"""
    assert liquid_turbidity("オレンジ 100% 1L") == 0.7
    assert liquid_turbidity("ミルクティー 500ml") == 0.95
    assert liquid_turbidity("スポーツドリンク 500ml") == 0.25
    assert liquid_turbidity("飲料", ["カフェラテ"]) == 0.95
    assert liquid_turbidity("ごまドレッシング 380ml") == 0.95
    assert liquid_turbidity("オレンジソーダ") == 0.0  # 炭酸は澄んでいる
    for name in ("緑茶 600ml", "コーラ 1.5L", "天然水 550ml", "麦茶 2L"):
        assert liquid_turbidity(name) == 0.0
