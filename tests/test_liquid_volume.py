"""濁った液体の OmniSurface の入力（usd_post.omnisurface_turbid_inputs）。"""

import pytest
from pxr import Gf

from agentic_usd_gen.usd_post import _turbid_sigma_a, omnisurface_turbid_inputs, omnisurface_volume, srgb_to_linear


@pytest.mark.parametrize("hex_color, turbidity", [
    ("#F5A623", 0.7),   # オレンジジュース
    ("#C8A27A", 0.95),  # ミルクティー
    ("#E8EEF2", 0.25),  # スポーツドリンク
])
def test_round_trip(hex_color, turbidity):
    """Isaac Sim の OmniSurface と同じ計算で、狙った散乱係数・吸収係数に戻る。"""
    depth = 0.085
    sigma_s = 60 * turbidity**2.5 / depth
    sigma_a = _turbid_sigma_a(srgb_to_linear(hex_color), sigma_s, depth)
    color, scatter, d = omnisurface_turbid_inputs(sigma_a, sigma_s, depth)
    assert 0 < d <= depth and min(color) >= 0.002 and min(scatter) >= 0
    back_s, back_a = omnisurface_volume(color, scatter, d)
    assert back_s == pytest.approx([sigma_s] * 3, rel=1e-4)
    assert back_a == pytest.approx(sigma_a, rel=1e-4)


def test_scattering_coefficient_as_color_inverts_hue():
    """散乱係数をそのまま散乱の色に入れると、吸収の弱い赤ほど強く吸収されて色が反転する（オレンジジュースが青く見える）。"""
    _, sigma_a = omnisurface_volume(Gf.Vec3f(0.999, 0.926, 0.002), Gf.Vec3f(290.754, 290.754, 290.754), 0.0012075)
    assert sigma_a[0] > sigma_a[2]


def test_isaac_table_round_trip():
    """Isaac Sim の実測の表：明るさ → 散乱アルベド → 明るさで戻り、明るいほどアルベドが高い。"""
    from agentic_usd_gen.usd_post import isaac_turbid_albedo, isaac_turbid_reflectance

    prev = 0.0
    for r in (0.002, 0.005, 0.02, 0.1, 0.3, 0.5, 0.69):
        a = isaac_turbid_albedo(r)
        assert a > prev
        assert isaac_turbid_reflectance(a) == pytest.approx(r, abs=1e-6)
        prev = a
    assert isaac_turbid_albedo(0.9) == isaac_turbid_albedo(0.7)  # 表より明るい色は端で止める


def test_isaac_sigma_a_darker_target_needs_less_absorption():
    """Isaac は Christensen–Burley の式より暗く見えるので、同じ色でも吸収を弱くする。"""
    from agentic_usd_gen.usd_post import _isaac_turbid_sigma_a

    col, depth = srgb_to_linear("#C8A27A"), 0.085
    sigma_s = 60 * 0.95**2.5 / depth
    assert all(i < c for i, c in zip(_isaac_turbid_sigma_a(col, sigma_s, depth), _turbid_sigma_a(col, sigma_s, depth)))


def test_isaac_bright_color_keeps_hue():
    """Isaac で出せない明るい色（オレンジの赤 0.93）は 3 チャンネルの比を保って暗くする。赤だけ頭打ちにすると黄色に寄る。"""
    from agentic_usd_gen.usd_post import ISAAC_TURBID_MAX, _isaac_turbid_sigma_a, isaac_turbid_albedo, isaac_turbid_reflectance

    col, depth = srgb_to_linear("#F7A21B"), 0.085
    sigma_s = 60 * 0.7**2.5 / depth
    sigma_a = _isaac_turbid_sigma_a(col, sigma_s, depth)
    shown = [isaac_turbid_reflectance(sigma_s / (sigma_s + a)) for a in sigma_a]
    assert max(shown) == pytest.approx(ISAAC_TURBID_MAX, rel=1e-3)
    assert shown[0] / shown[1] == pytest.approx(col[0] / col[1], rel=1e-3)
    assert isaac_turbid_albedo(ISAAC_TURBID_MAX) < isaac_turbid_albedo(0.69)


def test_preview_table_is_a_copy():
    """Blender のプレビュー（agentic_usd_gen を読み込めない）に写した表が usd_post と同じ。"""
    import ast
    from pathlib import Path

    from agentic_usd_gen import usd_post

    src = (Path(usd_post.__file__).parent / "blender" / "render_preview.py").read_text()
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "ISAAC_TURBID_ALBEDO")
    assert ast.literal_eval(node.value) == usd_post.ISAAC_TURBID_ALBEDO


def test_turbid_diffuse_weight():
    """濁った液体に混ぜる拡散反射の割合：澄んだ・薄い濁りは 0、牛乳・ミルクティーは 1。"""
    from agentic_usd_gen.usd_post import turbid_diffuse_weight

    assert turbid_diffuse_weight(0.0) == 0 and turbid_diffuse_weight(0.25) == 0
    assert turbid_diffuse_weight(0.7) == pytest.approx(2 / 3)
    assert turbid_diffuse_weight(0.95) == 1
