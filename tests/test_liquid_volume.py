"""液体の OmniSurface の入力（usd_post.omnisurface_volume：Isaac Sim と同じ計算）。"""

from pxr import Gf

from agentic_usd_gen.usd_post import omnisurface_volume


def test_scattering_coefficient_as_color_inverts_hue():
    """散乱係数をそのまま散乱の色に入れると、吸収の弱い赤ほど強く吸収されて色が反転する（オレンジジュースが青く見える）。"""
    _, sigma_a = omnisurface_volume(Gf.Vec3f(0.999, 0.926, 0.002), Gf.Vec3f(290.754, 290.754, 290.754), 0.0012075)
    assert sigma_a[0] > sigma_a[2]
