"""素材ごとの表面のつや（finish.py）。"""

import pytest

from agentic_usd_gen.finish import FINISHES, apply_finishes, material_key
from agentic_usd_gen.semantics import container_labels
from agentic_usd_gen.spec import Dimensions, ProductSpec


@pytest.mark.parametrize("role,material,key", [
    ("cap", None, "pp"),
    ("label", "film", "film"),  # 袋
    ("label", "PET", "film"),  # 透明ボトルのラベル
    ("label", "紙", "paper"),  # 紙箱
    ("container", "アルミ", "aluminum"),
    ("container", "スチール", "steel"),
    ("container", "HDPE", "plastic"),
])
def test_material_key(role, material, key):
    assert material_key(role, container_labels(material)) == key


def test_table_targets():
    """目安の範囲に入っている。"""
    assert 0.5 <= FINISHES["pp"][0] <= 0.6
    assert 0.15 <= FINISHES["film"][0] <= 0.25
    assert 0.6 <= FINISHES["paper"][0] <= 0.7
    assert 0.25 <= FINISHES["aluminum"][0] <= 0.35 and FINISHES["aluminum"][1] == 1.0
    assert all(FINISHES[k][1] == 0.0 for k in ("pp", "film", "paper"))


def test_apply_finishes():
    mats = {
        "CapMat": {"role": "cap", "labels": ["plastic"]},
        "LabelMat": {"role": "label", "labels": ["paper"]},
        "ContainerMat": {"role": "container", "labels": ["metal", "aluminum"]},
        "PET": {"role": "pet", "labels": ["plastic"]},
        "Part0Mat": {"role": "solid", "roughness": 0.8, "metallic": 0.0},
    }
    apply_finishes(mats, {"paper": {"roughness": 0.7}, "CapMat": {"roughness": 0.5, "metallic": 0},
                          "Part0Mat": {"roughness": 0.2}})
    assert (mats["CapMat"]["roughness"], mats["CapMat"]["metallic"]) == (0.5, 0.0)  # 名前で上書き
    assert mats["LabelMat"]["roughness"] == 0.7  # 素材名で上書き
    assert (mats["ContainerMat"]["roughness"], mats["ContainerMat"]["metallic"]) == FINISHES["aluminum"]
    assert "roughness" not in mats["PET"]  # 透明な素材は対象外
    assert mats["Part0Mat"]["roughness"] == 0.2


def test_spec_surfaces_roundtrip():
    spec = ProductSpec(product_name="x", slug="x", shape_class="revolve", dimensions=Dimensions(0.1, 0.05))
    assert "surfaces" not in spec.to_dict()
    spec.surfaces = {"CapMat": {"roughness": 0.5}}
    assert ProductSpec.from_dict(spec.to_dict()).surfaces == {"CapMat": {"roughness": 0.5}}
