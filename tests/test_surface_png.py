"""Surface maps are written losslessly in their own color type."""

import numpy as np
from PIL import Image

from agentic_usd_gen import surface


def test_maps_keep_pixels_and_mode(tmp_path):
    rng = np.random.default_rng(0)
    rgb = (rng.random((96, 128, 3)) * 255).astype(np.uint8)
    tex = tmp_path / "label.png"
    Image.fromarray(rgb).save(tex)
    want = surface.make_maps(rgb, "metal", None)
    paths = surface.write_maps(tex, "metal")
    assert set(paths) == set(want) and "metallic" in paths
    for name, p in paths.items():
        got = Image.open(p)
        assert got.mode == Image.fromarray(want[name]).mode  # a gray map stays gray: no palette
        ihdr = p.read_bytes()[24:26]  # bit depth, color type: 8-bit gray (0) or RGB (2), not reduced
        assert ihdr == bytes([8, 0 if want[name].ndim == 2 else 2])
        assert np.array_equal(np.asarray(got), want[name])


def test_same_input_same_bytes(tmp_path):
    rgb = np.full((64, 64, 3), 120, np.uint8)
    rgb[16:48, 16:48] = (200, 30, 30)
    out = []
    for d in ("a", "b"):
        (tmp_path / d).mkdir()
        tex = tmp_path / d / "label.png"
        Image.fromarray(rgb).save(tex)
        out.append({k: p.read_bytes() for k, p in surface.write_maps(tex, "film").items()})
    assert out[0] == out[1]
