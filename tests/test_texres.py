import pytest

from agentic_usd_gen.fictional.paint import Canvas, canvas_px_per_mm
from agentic_usd_gen.texres import MAX_PX, PX_PER_MM, density, draw_px_per_mm, record, texture_px


def test_texture_px_from_size():
    # 1 mm あたり 8 px 以上になる 2 のべき乗に切り上げる
    assert texture_px(0.2) == 2048  # 1600 px → 2048
    assert texture_px(0.33) == 4096  # 2L ボトルの円周くらい
    assert texture_px(0.05) == 512
    for length in (0.01, 0.05, 0.12, 0.3, 0.5):
        n = texture_px(length)
        assert n & (n - 1) == 0
        assert n >= min(length * 1000 * PX_PER_MM, MAX_PX)


def test_texture_px_caps():
    assert texture_px(2.0) == MAX_PX  # 什器のような大きな面も 4096 で止める
    assert texture_px(0.3, max_px=2048) == 2048
    assert texture_px(0.001) == 64  # 小さすぎる面も最低 64 px


def test_texture_px_source_limit():
    # 元の画像を大きく超えて引き伸ばさない（元の解像度にいちばん近い 2 のべき乗まで）
    assert texture_px(0.3, source_px=1000) == 1024
    assert texture_px(0.3, source_px=600) == 512
    assert texture_px(0.05, source_px=5000) == 512  # 元が大きくても実寸で決まる


def test_record_density():
    meta = {}
    record(meta, "label.png", (2048, 900), 2048, 0.2)
    assert meta["textures"]["label.png"] == {"size": [2048, 900], "px_per_mm": 10.24}
    assert density(4096, 0.33) == 12.41


@pytest.mark.parametrize("length", [0.03, 0.1, 0.204, 0.289, 0.4, 0.6, 1.2])
def test_draw_px_per_mm(length):
    """その密度で描いた画像を貼ると、上限で頭打ちになる辺を除いて目安の密度以上になる。"""
    s = draw_px_per_mm(length)
    src = length * 1000 * s
    n = texture_px(length, src)
    assert n == texture_px(length)  # 元の画像が小さくて頭打ちにならない
    if n < MAX_PX:
        assert s >= PX_PER_MM and n / (length * 1000) >= PX_PER_MM
    else:
        assert src <= MAX_PX * 1.01  # 上限を大きく超えて描かない


def test_canvas_px_per_mm():
    c = Canvas(120, 60)  # 省略時は下限の密度
    assert c.s == canvas_px_per_mm(120, 60) >= PX_PER_MM
    assert Canvas(120, 60, 20.0).s == 20.0  # 指定が下限より細かければそのまま
    assert Canvas(120, 60, 2.0).s == c.s  # 粗い指定は下限まで上げる
    # 長い辺がテクスチャの上限を超える密度にはしない
    big = Canvas(1070, 470, 1.5)
    assert max(big.img.size) <= MAX_PX
