"""素材ごとの摩擦・反発係数（physics_material.py）。"""

import pytest

from agentic_usd_gen.physics_material import CONTACTS, contact_for, physics_key
from agentic_usd_gen.semantics import container_labels
from agentic_usd_gen.spec import Dimensions, ProductSpec


@pytest.mark.parametrize("role,material,key", [
    ("pet", "PET", "plastic"),
    ("cap", None, "plastic"),  # PP のキャップも物理はプラスチック
    ("label", "film", "film"),  # 袋
    ("label", "紙", "paper"),  # 紙箱
    ("container", "アルミ", "aluminum"),
    ("glass", "ガラス", "glass"),
    (None, None, "plastic"),  # マテリアルが分からない部品
])
def test_physics_key(role, material, key):
    assert physics_key(role, container_labels(material) if material else None) == key


def test_table_targets():
    """目安（静止摩擦）どおりで、動摩擦は静止摩擦より小さい。"""
    assert CONTACTS["aluminum"].static_friction == pytest.approx(0.30)
    assert CONTACTS["plastic"].static_friction == pytest.approx(0.35)
    assert CONTACTS["paper"].static_friction == pytest.approx(0.50)
    assert CONTACTS["film"].static_friction == pytest.approx(0.40)
    assert CONTACTS["glass"].static_friction == pytest.approx(0.30)
    assert all(c.dynamic_friction < c.static_friction and 0 <= c.restitution <= 1 for c in CONTACTS.values())


def test_overrides():
    """素材名の上書きに、部品名の上書きを重ねる。"""
    ov = {"paper": {"static_friction": 0.6}, "Lid": {"restitution": 0.3, "color": "#fff"}}
    c = contact_for("paper", "Lid", ov)
    assert (c.static_friction, c.dynamic_friction, c.restitution) == (0.6, 0.40, 0.3)
    assert contact_for("paper", "Body", ov).restitution == CONTACTS["paper"].restitution
    assert contact_for("unknown") == CONTACTS["plastic"]


def test_spec_roundtrip():
    spec = ProductSpec(product_name="x", slug="x", shape_class="revolve", dimensions=Dimensions(0.1, 0.05),
                       physics_materials={"paper": {"static_friction": 0.6}})
    d = spec.to_dict()
    assert ProductSpec.from_dict(d).physics_materials == {"paper": {"static_friction": 0.6}}
    assert "physics_materials" not in ProductSpec(product_name="x", slug="x", shape_class="revolve", dimensions=Dimensions(0.1, 0.05)).to_dict()
