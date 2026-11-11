"""箱（box）形状のテスト。"""

import numpy as np
import pytest
from PIL import Image
from pxr import Usd, UsdShade

from agentic_usd_gen.shapes.box import BOX_BEVEL, CELL, FACES, BoxBuilder, bevel_width, box_mesh, cell_uv, face_layout, make_texture
from agentic_usd_gen.shapes.revolve import BuildContext
from agentic_usd_gen.spec import Dimensions, ProductSpec
from agentic_usd_gen.usd_post import postprocess
from agentic_usd_gen.validate import validate
from agentic_usd_gen.vision import Landmarks

W, D, H = 0.12, 0.05, 0.18


def test_faces_point_outward():
    for name, (corners, _) in face_layout(W, D, H).items():
        c = np.asarray(corners)
        normal = np.cross(c[1] - c[0], c[3] - c[0])
        center = c.mean(axis=0) - (0, 0, H / 2)
        assert np.dot(normal, center) > 0, name


def test_box_mesh_closed():
    m = box_mesh(W, D, H)
    assert len(m["vertices"]) == 8 and len(m["faces"]) == 6
    v = np.asarray(m["vertices"])
    assert v.max(axis=0) - v.min(axis=0) == pytest.approx((W, D, H))
    # 各辺がちょうど 2 面に共有される（閉じた多面体）
    edges = {}
    for f in m["faces"]:
        for a, b in zip(f, f[1:] + f[:1]):
            edges[frozenset((a, b))] = edges.get(frozenset((a, b)), 0) + 1
    assert set(edges.values()) == {2}


def test_texture_cells():
    front = np.zeros((40, 30, 3), np.uint8)
    front[:] = (255, 0, 0)
    tex = make_texture({"front": front}, (10, 20, 30))
    assert tex.shape == (2 * CELL, 3 * CELL, 3)
    assert tuple(tex[100, 100]) == (255, 0, 0)  # 左上のセルが正面
    assert tuple(tex[100, CELL + 100]) == (10, 20, 30)
    u0, v0, u1, v1 = cell_uv(FACES.index("front"))
    assert 0 < u0 < u1 < 1 / 3 and 0.5 < v0 < v1 < 1


def test_box_build(tmp_path, blender):
    img = np.full((360, 240, 3), (30, 90, 200), np.uint8)
    Image.fromarray(img).save(tmp_path / "front.png")
    Image.fromarray(img[:, :100]).save(tmp_path / "side.png")
    spec = ProductSpec(product_name="合成の箱", slug="synthetic_box", shape_class="box",
                       dimensions=Dimensions(H, W, depth=D), mass_kg=0.2)
    ctx = BuildContext(spec, [tmp_path / "front.png", tmp_path / "side.png"], 0, Landmarks(),
                       tmp_path / "out", tmp_path / "debug", blender, faces={"right": 1, "left": 1})
    result = BoxBuilder().build(ctx)
    assert result.meta["profile"]["faces"] == ["front", "left", "right"]
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"])
    assert rep.ok, rep.errors
    stage = Usd.Stage.Open(str(result.usd_path))
    mat = UsdShade.Material.Get(stage, stage.GetDefaultPrim().GetPath().AppendPath("_materials/BoxMat"))
    assert mat and mat.GetSurfaceOutput("mdl").HasConnectedSource()


def test_bevel_width():
    # 既定値は小さい箱では短い辺の 1 割まで、指定値は 1/4 まで、0 は面取りなし
    assert bevel_width(None, (W, D, H), BOX_BEVEL) == BOX_BEVEL
    assert bevel_width(None, (0.1, 0.004, 0.1), BOX_BEVEL) == pytest.approx(0.0004)
    assert bevel_width(0.1, (W, D, H), BOX_BEVEL) == pytest.approx(0.25 * D)
    assert bevel_width(0, (W, D, H), BOX_BEVEL) == 0


def test_spec_bevel_roundtrip():
    d = {"product_name": "x", "shape_class": "box", "dimensions": {"height": H, "diameter": W, "depth": D}}
    assert "bevel" not in ProductSpec.from_dict(d).to_dict()  # 省略時は既存の仕様と同じ出力
    assert ProductSpec.from_dict({**d, "bevel": 0.001}).to_dict()["bevel"] == 0.001
