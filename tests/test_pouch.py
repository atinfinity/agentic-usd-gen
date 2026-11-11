"""袋（pouch）形状のテスト。"""

import numpy as np
import pytest
from pxr import Usd, UsdShade

from agentic_usd_gen.shapes.pouch import PouchBuilder, arc_xy, lay_flat, pouch_mesh, superellipse_xy, trim_background
from agentic_usd_gen.shapes.revolve import BuildContext
from agentic_usd_gen.spec import Dimensions, ProductSpec
from agentic_usd_gen.usd_post import postprocess
from agentic_usd_gen.validate import validate
from agentic_usd_gen.vision import Landmarks

W, H, T = 0.18, 0.26, 0.055


def test_arc_keeps_film_width():
    a = np.linspace(0, 1, 201)
    x, y = arc_xy(W, 0.02, a)
    assert np.sum(np.hypot(np.diff(x), np.diff(y))) == pytest.approx(W, rel=1e-3)
    assert y.max() == pytest.approx(0.02, rel=1e-3)
    assert x.max() - x.min() < W  # 膨らむと見かけの幅は縮む


def test_pouch_mesh_size():
    m = pouch_mesh(W, H, T)
    sx, sy, sz = m["size"]
    assert sx == pytest.approx(W)  # シール部は平らなので幅いっぱい
    assert sy == pytest.approx(T, rel=1e-3)
    assert 0.9 * H < sz < H
    assert 0.4 * sz < m["com_z"] < 0.6 * sz
    assert len(m["faces"]) == len(m["uvs"])


def test_superellipse_keeps_film_width():
    a = np.linspace(0, 1, 201)
    x, y = superellipse_xy(W, 0.02, a, 3)
    assert np.sum(np.hypot(np.diff(x), np.diff(y))) == pytest.approx(W, rel=2e-3)
    assert y.max() == pytest.approx(0.02, rel=1e-3)
    assert x[0] == pytest.approx(-x[-1]) and y[0] == pytest.approx(0, abs=1e-9)
    # 角ばるほど同じ厚さでも見かけの幅は狭くなる（周の多くが側面に回る）
    xa, _ = arc_xy(W, 0.02, a)
    assert x.max() < xa.max()


def test_gusset_bottom_stands():
    # 底マチの袋は底が平らな面になり、重心の真下から接地面の縁まで厚さの半分ほどの余裕がある（米袋）
    m = pouch_mesh(0.38, 0.58, 0.13, gusset=0.13, square=3)
    v = np.asarray(m["vertices"])
    low = v[v[:, 2] < 0.002]
    assert low[:, 1].max() == pytest.approx(0.065, rel=0.02)
    assert low[:, 1].min() == pytest.approx(-0.065, rel=0.02)
    assert m["com_z"] < pouch_mesh(0.38, 0.58, 0.13)["com_z"]  # 底が詰まった分、重心が下がる
    assert m["size"][0] == pytest.approx(0.38)  # 上のシールは平らで幅いっぱい
    # 閉じた面: どの辺もちょうど 2 つの面に使われる
    edges = {}
    for f in m["faces"]:
        assert len(set(f)) == len(f) >= 3
        for e in zip(f, f[1:] + f[:1]):
            k = tuple(sorted(e))
            edges[k] = edges.get(k, 0) + 1
    assert set(edges.values()) == {2}
    assert len(m["faces"]) == len(m["uvs"])


def test_lay_flat():
    m = pouch_mesh(0.051, 0.115, 0.02)
    f = lay_flat(m)
    v = np.asarray(f["vertices"])
    size = v.max(axis=0) - v.min(axis=0)
    assert size == pytest.approx(f["size"], abs=1e-6)
    assert size[0] > size[1] > size[2]  # シール方向が X、厚さが Z
    assert v[:, 2].min() == pytest.approx(0, abs=1e-9)
    assert (v.max(axis=0) + v.min(axis=0))[:2] == pytest.approx((0, 0), abs=1e-6)
    assert f["com"][2] == pytest.approx(size[2] / 2)
    # 正面（立てたとき -Y にある頂点）が上を向く
    front_top = v[np.asarray(m["vertices"])[:, 1] < -0.005]
    assert front_top[:, 2].min() > size[2] / 2


def test_trim_background():
    img = np.full((100, 80, 3), 255, np.uint8)
    img[10:90, 20:60] = (200, 160, 40)
    assert trim_background(img).shape[:2] == (80, 40)
    full = np.random.default_rng(0).integers(0, 255, (50, 40, 3), dtype=np.uint8)
    assert trim_background(full).shape == full.shape


def test_short_pouch_shrinks():
    # 横長の小袋（シールが短辺側）は膨らむと高さが 5% 以上縮むので、検証は計算値と比べる必要がある
    sz = pouch_mesh(0.115, 0.051, 0.02)["size"][2]
    assert sz < 0.95 * 0.051


@pytest.mark.parametrize("w,h,t,orientation", [(W, H, T, "upright"), (0.115, 0.051, 0.02, "upright"),
                                               (0.051, 0.115, 0.02, "lying")])
def test_pouch_build(tmp_path, blender, w, h, t, orientation):
    img = np.full((520, 360, 3), (240, 220, 120), np.uint8)
    img[200:300, 60:300] = (200, 40, 40)
    from PIL import Image

    Image.fromarray(img).save(tmp_path / "front.png")
    spec = ProductSpec(product_name="合成の袋", slug="synthetic_pouch", shape_class="pouch",
                       dimensions=Dimensions(h, w, depth=t), mass_kg=0.06, orientation=orientation)
    ctx = BuildContext(spec, [tmp_path / "front.png"], None, Landmarks(), tmp_path / "out", tmp_path / "debug", blender)
    result = PouchBuilder().build(ctx)
    postprocess(result, spec.product_name)
    rep = validate(result.usd_path, spec.dimensions, expected_size=result.meta["profile"]["expected_size"])
    assert rep.ok, rep.errors
    stage = Usd.Stage.Open(str(result.usd_path))
    mat = UsdShade.Material.Get(stage, stage.GetDefaultPrim().GetPath().AppendPath("_materials/BagMat"))
    assert mat and mat.GetSurfaceOutput("mdl").HasConnectedSource()
