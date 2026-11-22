"""paint.edge_shade computes only the band along the edges: the same pixels as the formula on every pixel."""

import numpy as np
import pytest

from agentic_usd_gen.fictional import paint


def _full(img, px, amount):  # the formula on the whole grid (the earlier version)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]).astype(np.float32)
    k = 1 - amount * np.clip(1 - d / max(px, 1), 0, 1) ** 2
    return np.clip(img.astype(np.float32) * k[..., None], 0, 255).astype(np.uint8)


@pytest.mark.parametrize("shape", [(1, 1, 3), (3, 7, 3), (40, 25, 4), (120, 90, 3)])
@pytest.mark.parametrize("px", [0, 1, 6, 20, 200])
def test_edge_shade_is_the_full_formula(shape, px):
    img = np.random.default_rng(px).integers(0, 256, shape, dtype=np.uint8)
    out = paint.edge_shade(img, px, 0.12)
    assert out.dtype == np.uint8 and np.array_equal(out, _full(img, px, 0.12))


def test_edge_shade_leaves_the_input():
    img = np.full((30, 30, 3), 200, np.uint8)
    paint.edge_shade(img, 5)
    assert (img == 200).all()


def test_edge_shade_gray_and_float():
    gray = np.full((10, 12), 200, np.uint8)
    out = paint.edge_shade(gray, 3)
    assert out.shape == gray.shape and out.dtype == np.uint8 and out[0, 0] < 200 and out[5, 6] == 200
    f = np.full((10, 12, 3), 300.0, np.float32)
    out = paint.edge_shade(f, 3)
    assert out.dtype == np.uint8 and (out <= 255).all() and out[5, 6, 0] == 255
