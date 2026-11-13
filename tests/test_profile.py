import numpy as np
import pytest

from tests import synth
from tests.conftest import D, H
from agentic_usd_gen.label import label_circumference, label_size, make_label_texture
from agentic_usd_gen.profile import build_profile, extract_silhouette, parametric_profile
from agentic_usd_gen.shapes.revolve import _mass_properties, _rdp
from agentic_usd_gen.spec import Dimensions
from agentic_usd_gen.vision import Landmarks

DIMS = Dimensions(H, D)


def px_to_z(row: int) -> float:
    return (synth.BOTTOM - row) / (synth.BOTTOM - synth.TOP) * H


@pytest.fixture(scope="module")
def sil(bottle_rgb):
    return extract_silhouette(bottle_rgb)


@pytest.fixture(scope="module")
def prof(bottle_rgb, sil):
    return build_profile(bottle_rgb, sil, DIMS, Landmarks(), {})


def test_silhouette(sil):
    assert abs(sil.top - synth.TOP) <= 2 and abs(sil.bottom - synth.BOTTOM) <= 2
    assert sil.radius.max() == pytest.approx(synth.R_BODY, abs=2)
    assert sil.quality((900, 600, 3)) > 0.5


def test_profile_dimensions(prof):
    assert prof.height == pytest.approx(H)
    assert prof.r.max() == pytest.approx(D / 2, rel=0.01)
    assert prof.radius_at(px_to_z(130)) == pytest.approx(D / 2 * synth.R_NECK / synth.R_BODY, rel=0.05)


def test_profile_landmarks(prof):
    assert prof.liquid_top_z == pytest.approx(px_to_z(synth.LIQUID_TOP), abs=0.003)
    z0, z1 = prof.label_z
    assert z0 == pytest.approx(px_to_z(synth.LABEL[1]), abs=0.003)
    assert z1 == pytest.approx(px_to_z(synth.LABEL[0]), abs=0.003)
    assert prof.colors["cap"].upper().startswith("#C")  # 赤いキャップ


def test_landmarks_override_heuristics(bottle_rgb, sil):
    ratio = (synth.CAP_BOTTOM - synth.TOP) / (synth.BOTTOM - synth.TOP)
    p = build_profile(bottle_rgb, sil, DIMS, Landmarks(cap_bottom=ratio), {})
    assert p.cap_z == pytest.approx(px_to_z(synth.CAP_BOTTOM), abs=0.002)
    assert not any("キャップ" in w for w in p.warnings)


def test_label_texture(bottle_rgb, sil, prof):
    tex = make_label_texture(bottle_rgb, sil, prof)
    h, w, _ = tex.shape
    # 幅は円周の実寸と写真の解像度から決まる 2 のべき乗（この写真ではラベルの円周が 1000 px ほど）
    assert (w, h) == label_size(prof, label_circumference(prof) * sil.height_px / prof.height)
    assert w == 1024 and 16 <= h < w
    front = tex[:, int(w * (0.75 - 0.15))]  # 正面（u=0.75）の少し横はラベルの赤
    assert front[:, 0].mean() > 150 and front[:, 1].mean() < 80
    back = tex[:, int(w * 0.25)]  # 裏側は地色で埋める
    assert np.ptp(back.astype(int), axis=0).max() < 10


def test_parametric_profile():
    p = parametric_profile(DIMS, {"cap": "#FF0000"})
    assert p.height == pytest.approx(H)
    assert p.r.max() == pytest.approx(D / 2)
    assert np.all(np.diff(p.z) >= 0) and 0 < p.cap_z < H


def test_mass_properties(prof):
    mass, com = _mass_properties(prof, 0.53, 500)
    assert mass == 0.53 and 0.25 * H < com < 0.55 * H
    est, _ = _mass_properties(prof, None, None)
    assert 0.3 < est < 0.8  # 内容積から推定（500ml 前後）


def test_rdp():
    pts = np.stack([np.linspace(0, 1, 50), np.zeros(50)], 1)
    assert len(_rdp(pts, 1e-6)) == 2


def test_silhouette_of_clear_bottle():
    """透明なボトルは輪郭が途切れた細い線になる。線の内側を埋めて、左右とも外形を取る。"""
    rgb = synth.make_clear_bottle()
    sil = extract_silhouette(rgb)
    assert abs(sil.top - synth.TOP) <= 2 and abs(sil.bottom - synth.BOTTOM) <= 2
    body = sil.radius[synth.SHOULDER_BOTTOM - sil.top : synth.BOTTOM - 20 - sil.top]
    assert body.min() == pytest.approx(synth.R_BODY, abs=3)
    assert sil.asymmetry < 0.02 and abs(sil.tilt) < 0.005
    assert sil.quality(rgb.shape) > 0.5


def test_silhouette_ignores_caption_below():
    """商品のすぐ下にある注記の文字は、輪郭に含めない。"""
    rgb = synth.make_bottle()
    for x in range(synth.CX - 110, synth.CX + 110, 10):
        rgb[synth.BOTTOM + 8 : synth.BOTTOM + 16, x : x + 4] = (40, 40, 40)
    sil = extract_silhouette(rgb)
    assert abs(sil.bottom - synth.BOTTOM) <= 2


def _ctx(images, preferred=None):
    from types import SimpleNamespace

    return SimpleNamespace(images=images, preferred_image=preferred, spec=SimpleNamespace(dimensions=DIMS))


def test_select_image_skips_wrong_aspect(tmp_path, bottle_png):
    """輪郭がきれいでも、縦横比が寸法と合わない画像（ラベルの拡大など）は形を取るのに使わない。"""
    from PIL import Image

    from agentic_usd_gen.shapes.revolve import _select_image

    closeup = np.full((500, 500, 3), 255, np.uint8)
    closeup[150:350, 80:420] = (60, 140, 210)
    p = tmp_path / "closeup.png"
    Image.fromarray(closeup).save(p)

    assert _select_image(_ctx([p])) is None
    assert _select_image(_ctx([p, bottle_png]))[0] == bottle_png
    assert _select_image(_ctx([p, bottle_png], preferred=0))[0] == bottle_png
