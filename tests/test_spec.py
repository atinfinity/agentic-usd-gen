import numpy as np
import pytest

from agentic_usd_gen.spec import Dimensions, Part, ProductSpec, cache_key, make_slug, parse_dims_override


def test_make_slug():
    assert make_slug("Green-Tea 600ml PET") == "green_tea_600ml_pet"
    assert make_slug("500ml") == "a_500ml"
    assert make_slug("緑茶・ほうじ茶") == "asset"


def test_cache_key_keeps_japanese():
    assert cache_key("緑茶・ほうじ茶 600ml/PET") == "緑茶・ほうじ茶_600ml_PET"


def test_parse_dims_override():
    assert parse_dims_override("H=0.205, D=0.065,cap_h=0.016") == {
        "height": 0.205, "diameter": 0.065, "cap_height": 0.016}
    with pytest.raises(ValueError):
        parse_dims_override("W=1")


def test_spec_roundtrip(tmp_path):
    d = {"product_name": "テスト", "slug": "Test Bottle", "shape_class": "revolve",
         "dimensions": {"height": 0.2, "diameter": 0.06, "cap_height": None, "cap_diameter": None},
         "capacity_ml": 500, "colors": {"cap": "#FF0000", "liquid": None, "label_base": None}}
    spec = ProductSpec.from_dict(d)
    assert spec.slug == "test_bottle"
    assert spec.total_mass_kg() == pytest.approx(0.52)
    spec.save(tmp_path / "s.json")
    assert ProductSpec.load(tmp_path / "s.json") == spec


def test_is_transparent():
    from agentic_usd_gen.shapes.revolve import is_transparent

    assert is_transparent(None) and is_transparent("PET") and is_transparent("ガラス瓶")
    assert not is_transparent("paper") and not is_transparent("アルミ缶")


def test_is_glass():
    from agentic_usd_gen.shapes.revolve import is_glass

    assert is_glass("glass") and is_glass("ガラス瓶") and is_glass("瓶")
    assert not is_glass("PET") and not is_glass(None) and not is_glass("frosted glass")


def test_glass_mass():
    """ガラス瓶は容器が重い。質量が不明なら 表面積 × 肉厚 × 密度 で見積もる。"""
    from agentic_usd_gen.profile import parametric_profile
    from agentic_usd_gen.shapes.revolve import GLASS_BOTTOM, GLASS_DENSITY, GLASS_WALL, _mass_properties

    prof = parametric_profile(Dimensions(0.1, 0.07), {"cap": None, "liquid": None, "label_base": None})
    m_pet, _ = _mass_properties(prof, None, 300)
    m_glass, _ = _mass_properties(prof, None, 300, GLASS_WALL, bottom=GLASS_BOTTOM, density=GLASS_DENSITY)
    assert m_pet == pytest.approx(0.3 * 1.04 * 1.04, rel=0.01)  # 中身（密度 1040）+ 4%
    assert 0.1 < m_glass - 0.3 * 1.04 < 0.3  # 瓶だけで 100〜300 g


def test_fictional_products(tmp_path):
    """架空の商品: 実在の出典を持たず、素材の出典（CC0 写真・OFL の書体）を持つ spec とキャッシュを書く。"""
    import json

    from agentic_usd_gen.fictional.base import write
    from agentic_usd_gen.fictional.registry import PRODUCTS
    from agentic_usd_gen.spec import ProductSpec

    assert len(PRODUCTS) == 565
    for name in ("cup_noodle_tall", "potato_chips_bag"):
        d = write(PRODUCTS[name](), tmp_path)
        spec = ProductSpec.load(d / "spec.json")
        assert spec.slug == name and spec.fictional and not spec.sources and not spec.image_candidates
        assert "fictional" in spec.tags
        assert any(c["title"] == "Noto Sans JP" for c in spec.image_credits)
        vision = json.loads((d / "vision.json").read_text())
        n = len(vision["images"])
        assert all((d / "images" / f"{i:02d}.png").exists() for i in range(n))
    assert vision.get("faces") == {"front": 0, "back": 1} and n == 2  # 袋は表と裏の 2 枚


def test_fictional_photos_are_public_domain():
    from agentic_usd_gen.fictional.paint import photo_manifest

    for pid, m in photo_manifest().items():
        assert m["license"].startswith(("CC0", "Public domain", "PD")), (pid, m["license"])


def test_ean13_check_digit():
    from agentic_usd_gen.fictional.paint import ean_check

    assert ean_check("490123456789") == 4  # 既知の例


def test_translucency():
    from agentic_usd_gen.shapes.revolve import is_transparent, translucency

    assert translucency("HDPE") == "translucent" and translucency("半透明のポリエチレン") == "translucent"
    assert translucency("frosted glass") == "frosted" and translucency("すりガラス") == "frosted"
    assert translucency("PET") is None and translucency(None) is None
    assert not is_transparent("frosted glass")  # 半透明は透明より先に当てる


@pytest.mark.parametrize("material,want", [
    (None, "transparent"), ("PET", "transparent"), ("ガラス瓶", "transparent"),
    ("PS", "transparent"), ("OPS（透明カップ）", "transparent"), ("透明 PP", "transparent"), ("clear PP", "transparent"),
    ("acrylic", "transparent"), ("PC", "transparent"),
    ("PP", "opaque"), ("plastic", "opaque"), ("paper", "opaque"), ("アルミ缶", "opaque"), ("cups", "opaque"),
    ("不透明 PET", "opaque"), ("opaque PS", "opaque"),
    ("半透明の PP", "translucent"), ("HDPE", "translucent"), ("すりガラス", "frosted"),
])
def test_container_transparency(material, want):
    from agentic_usd_gen.shapes.revolve import container_transparency

    assert container_transparency(material) == want


def test_transparency_override():
    """spec の transparency は素材名からの推定より優先する。"""
    from agentic_usd_gen.shapes.revolve import is_glass, is_transparent, translucency

    assert translucency("PP", "frosted") == "frosted" and not is_transparent("PP", "frosted")
    assert not is_transparent("PET", "opaque") and not is_glass("glass", "opaque")
    assert is_glass("glass", "transparent") and is_transparent("plastic", "transparent")
    base = dict(product_name="x", slug="x", shape_class="revolve", dimensions=Dimensions(0.1, 0.05))
    spec = ProductSpec(**base, transparency="frosted")
    assert ProductSpec.from_dict(spec.to_dict()).transparency == "frosted"
    assert "transparency" not in ProductSpec(**base).to_dict()
    with pytest.raises(ValueError, match="transparency"):
        ProductSpec(**base, transparency="clear")


def test_collision_approximation_spec():
    base = dict(product_name="x", slug="x", shape_class="assembly", dimensions=Dimensions(0.1, 0.05))
    parts = [Part("A", "box", [0.1, 0.1, 0.1], [0, 0, 0.05], collision_approximation="convexDecomposition"),
             Part("B", "box", [0.1, 0.1, 0.1], [0, 0, 0.15])]
    spec = ProductSpec(**base, parts=parts, collision_approximation={"B": "boundingCube"})
    assert spec.collision_approximations() == {"A": "convexDecomposition", "B": "boundingCube"}
    d = spec.to_dict()
    assert "collision_approximation" not in d["parts"][1]
    assert ProductSpec.from_dict(d).collision_approximations() == spec.collision_approximations()
    assert "collision_approximation" not in ProductSpec(**base).to_dict()
    with pytest.raises(ValueError, match="sdf"):
        ProductSpec(**base, collision_approximation={"Body": "sdf"})


def test_label_back_texture():
    from agentic_usd_gen.shapes.revolve import LABEL_BACK_COLOR, label_back_texture

    tex = np.zeros((4, 8, 3), np.uint8)
    tex[:, :4] = (200, 0, 0)
    back = label_back_texture(tex, show=0.15)
    assert back.shape == tex.shape and back.dtype == np.uint8
    assert tuple(back[0, 5]) == tuple(round(c * 0.85) for c in LABEL_BACK_COLOR)
    assert back[0, 0, 0] > back[0, 0, 1]  # 表の絵柄がうっすら残る
    assert (label_back_texture(tex, show=0.0) == LABEL_BACK_COLOR).all()


def test_petaloid_body_uses_decomposition():
    """花形の底のボトルは、PhysX の凸包で脚先が潰れて倒れるので、本体を既定で凸分解にする。"""
    base = dict(product_name="x", slug="x", shape_class="revolve")
    assert ProductSpec(**base, dimensions=Dimensions(0.31, 0.092)).collision_approximations() == {}
    spec = ProductSpec(**base, dimensions=Dimensions(0.31, 0.092, lobes=[5, 0.034, 0.42]))
    assert spec.collision_approximations() == {"Body": "convexDecomposition"}
    assert "collision_approximation" not in spec.to_dict()  # 既定は spec.json に書かない
    spec = ProductSpec(**base, dimensions=Dimensions(0.31, 0.092, lobes=[5, 0.034, 0.42]),
                       collision_approximation={"Body": "convexHull"})
    assert spec.collision_approximations() == {"Body": "convexHull"}  # 明示した指定が優先


def test_mount():
    """mount（天井付けなど）は往復し、既定の floor は出さない。ドームカメラと天井吊りサイネージは ceiling。"""
    from agentic_usd_gen.fictional.products import digital_signage_ceiling_3x
    from agentic_usd_gen.fictional.store_equipment import security_camera_dome

    base = dict(product_name="x", slug="x", shape_class="assembly", dimensions=Dimensions(0.1, 0.05))
    spec = ProductSpec(**base, mount="ceiling")
    assert ProductSpec.from_dict(spec.to_dict()).mount == "ceiling"
    assert "mount" not in ProductSpec(**base).to_dict()
    with pytest.raises(ValueError, match="mount"):
        ProductSpec(**base, mount="wall")
    assert security_camera_dome().spec().mount == "ceiling"
    assert digital_signage_ceiling_3x().spec().mount == "ceiling"
