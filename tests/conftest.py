import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tests.synth import make_bottle
from agentic_usd_gen.blender_runner import CANDIDATES

H, D = 0.205, 0.065


def _blender() -> str | None:
    import os

    for c in [os.environ.get("BLENDER"), shutil.which("blender"), *CANDIDATES]:
        if c and Path(c).exists():
            return c
    return None


@pytest.fixture(scope="session")
def bottle_rgb() -> np.ndarray:
    return make_bottle()


@pytest.fixture(scope="session")
def bottle_png(tmp_path_factory, bottle_rgb) -> Path:
    p = tmp_path_factory.mktemp("img") / "synth.png"
    Image.fromarray(bottle_rgb).save(p)
    return p


@pytest.fixture(scope="session")
def blender() -> str:
    b = _blender()
    if not b:
        pytest.skip("Blender が見つからない")
    return b
