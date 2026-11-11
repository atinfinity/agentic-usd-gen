"""プレビューの透明な部品の検査（preview_check）のテスト。合成したプレビューとマスクを使う。"""

import json

import numpy as np
import pytest
from PIL import Image

from agentic_usd_gen import preview_check as pc

BG = (177, 177, 177)
H, W = 200, 120


def _write(debug, liquid_rgb, clear_rgb, views=("front", "34")):
    """上 1/4 が中身のない透明な容器、その下が液体、中ほどに不透明なラベルのあるボトルのプレビューとマスク。"""
    masks = debug / "masks"
    masks.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.full((16, 16, 3), BG, np.uint8)).save(masks / "background.png")
    body = np.zeros((H, W), bool)
    body[20:190, 20:100] = True
    label = np.zeros_like(body)
    label[90:120, 20:100] = True
    liquid = body.copy()
    liquid[:60] = False
    liquid &= ~label
    clear = body & ~label
    for view in views:
        img = np.zeros((H, W, 4), np.uint8)
        img[body] = (*clear_rgb, 255)
        img[liquid] = (*liquid_rgb, 255)
        img[label] = (200, 30, 30, 255)
        Image.fromarray(img).save(debug / f"preview_{view}.png")
        for name, m in (("liquid", liquid), ("clear", clear), ("opaque", label)):
            a = np.zeros((H, W, 4), np.uint8)
            a[m] = 255
            Image.fromarray(a).save(masks / f"{view}_{name}.png")


def test_lab():
    assert np.allclose(pc.srgb_to_lab([255, 255, 255]), [100, 0, 0], atol=0.1)
    assert np.allclose(pc.srgb_to_lab([0, 0, 0]), [0, 0, 0], atol=0.1)
    assert pc.rgb_hex(pc.hex_rgb("#3A1A0E")) == "#3A1A0E"
    # 色のない液体はほぼ背景のまま、色のある液体は背景より暗く色が付く
    assert np.linalg.norm(pc.srgb_to_lab(pc.expected_liquid(None, BG)) - pc.srgb_to_lab(BG)) < 3
    exp = pc.expected_liquid("#F7A21B", BG)
    assert exp[0] > exp[1] > exp[2] and exp.max() <= 177.5
    # 濃い液体（コーラ）は映り込みで黒に近い灰色に見える
    cola = pc.expected_liquid("#3A1A0E", BG)
    assert 50 < cola.min() and cola.max() < 75


def test_ok(tmp_path):
    exp = pc.expected_liquid("#F7A21B", BG)
    _write(tmp_path, tuple(int(v) for v in exp), BG)
    res = pc.check(tmp_path, "#F7A21B")
    assert res["warnings"] == [] and res["liquid"]["delta_e"] < 1 and abs(res["clear"]["delta_l"]) < 1
    assert res["liquid"]["pixels"] > pc.MIN_PIXELS and res["clear"]["pixels"] > pc.MIN_PIXELS


@pytest.mark.parametrize("liquid,clear,expect", [
    ((235, 235, 235), BG, "液体の色"),  # 白く濁る
    ((5, 5, 5), BG, "液体の色"),  # 真っ黒（明るい色の液体）
    (BG, BG, "液体の色"),  # 色のある液体が見えない（背景のまま）
    (None, (40, 40, 40), "暗すぎる"),  # 容器が黒く沈む
    (None, (255, 255, 255), "明るすぎる"),  # 容器が白く飛ぶ
])
def test_warns(tmp_path, liquid, clear, expect):
    exp = tuple(int(v) for v in pc.expected_liquid("#F7A21B", BG))
    _write(tmp_path, liquid or exp, clear)
    res = pc.check(tmp_path, "#F7A21B")
    assert len(res["warnings"]) == 1 and expect in res["warnings"][0]


# 液体を真っ黒に描くと、表面の映り込み（背景の 1 割ほど）だけが見える
REFLECTION_ONLY = (59, 59, 59)


@pytest.mark.parametrize("color,warns", [
    ("#9A5A2A", True),  # ほうじ茶: 茶色に見えるはずが黒い
    ("#8E1426", True),  # ジャム
    ("#3A1A0E", False),  # コーラ: もともと黒に近く見えるので、真っ黒でも見た目は正しい
])
def test_dark_liquid_black(tmp_path, color, warns):
    _write(tmp_path, REFLECTION_ONLY, BG)
    assert bool(pc.check(tmp_path, color)["warnings"]) == warns


def test_dark_liquid_ok(tmp_path):
    """濃い液体が正常に（映り込みで少し明るく）描かれていれば警告しない。"""
    for color in ("#9A5A2A", "#8E1426", "#3A1A0E", "#5B2A08"):
        _write(tmp_path, tuple(int(v) for v in pc.expected_liquid(color, BG)), BG)
        assert pc.check(tmp_path, color)["warnings"] == []


def test_colorless_liquid(tmp_path):
    """色のない液体（水）は背景と同じに見えればよい。"""
    _write(tmp_path, BG, BG)
    assert pc.check(tmp_path, None)["warnings"] == []


def test_no_masks(tmp_path):
    assert pc.check(tmp_path, "#FFFFFF") is None  # 透明な部品がなければマスクを描かない


def _hide_liquid(debug):
    for v in ("front", "34"):
        Image.fromarray(np.zeros((H, W, 4), np.uint8)).save(debug / "masks" / f"{v}_liquid.png")


def _info(debug, liquid, translucent=0):
    (debug / "masks" / "info.json").write_text(json.dumps({"liquid": liquid, "translucent": translucent}))


def test_hidden_liquid(tmp_path):
    """液体がほとんど見えなければ色は測らない。液体がないはずの商品なら警告もしない。"""
    _write(tmp_path, BG, BG)
    _hide_liquid(tmp_path)
    res = pc.check(tmp_path, "#3A1A0E")
    assert "liquid" not in res and res["warnings"] == []


def test_liquid_missing(tmp_path):
    """液体があるはずなのに、メッシュがない・見えないときは警告する。半透明の容器の奥なら見えないのが正しい。"""
    _write(tmp_path, BG, BG)
    _hide_liquid(tmp_path)
    assert pc.check(tmp_path, "#3A1A0E", liquid_expected=True)["warnings"] == []  # info.json のない古い描画
    _info(tmp_path, liquid=0)
    assert "メッシュがない" in pc.check(tmp_path, "#3A1A0E", liquid_expected=True)["warnings"][0]
    _info(tmp_path, liquid=1)
    assert "ほとんど見えない" in pc.check(tmp_path, "#3A1A0E", liquid_expected=True)["warnings"][0]
    _info(tmp_path, liquid=1, translucent=1)
    assert pc.check(tmp_path, "#3A1A0E", liquid_expected=True)["warnings"] == []
    # 見えていれば警告しない
    _write(tmp_path, tuple(int(v) for v in pc.expected_liquid("#3A1A0E", BG)), BG)
    assert pc.check(tmp_path, "#3A1A0E", liquid_expected=True)["warnings"] == []
