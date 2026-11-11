"""回転体の細部（キャップの溝・缶の上面と底）の単体テスト。"""

import numpy as np

from agentic_usd_gen.fictional import forms
from agentic_usd_gen.shapes import details


def _pts(prof):
    return [[z, r] for z, r in prof]


def test_detail_kinds():
    pet = forms.pet_bottle(0.205, 0.065, label=(0.06, 0.12), liquid_top=0.17)
    can = forms.aluminum_can(0.122, 0.066, top_d=0.054)
    stick = forms.stick(0.068, 0.016, cap_h=0.022, label=(0.002, 0.04))
    jar = forms.jar(0.09, 0.06, cap_h=0.012, cap_d=0.062, label=(0.01, 0.06))
    tin = forms.tin(0.022, 0.075, lid_h=0.012)
    assert details.is_screw_cap(_pts(pet.cap), _pts(pet.body), metal=False)
    assert not details.is_screw_cap(_pts(pet.cap), _pts(pet.body), metal=True)
    assert not details.is_screw_cap(_pts(stick.cap), _pts(stick.body), metal=False)  # 胴と同じ太さ
    assert not details.is_screw_cap(_pts(jar.cap), _pts(jar.body), metal=False)  # 広口の蓋
    assert details.is_can(_pts(can.cap), _pts(can.body), metal=True)
    assert not details.is_can(_pts(can.cap), _pts(can.body), metal=False)
    assert not details.is_can(_pts(tin.cap), _pts(tin.body), metal=True)  # 高い蓋の平たい缶


def test_knurl_normal_map():
    """溝は周方向（u）にだけ変わり、上下の端には付かない。"""
    cap = [[0.185, 0.015], [0.2035, 0.015], [0.205, 0.0138]]
    nmap, px_per_m = details.knurl_normal_map(cap)
    h, w, _ = nmap.shape
    assert w & (w - 1) == 0 and w >= 1024
    assert px_per_m == w / (2 * np.pi * 0.015)
    x = nmap[..., 0].astype(int)
    mid = x[h // 2]
    n = round(2 * np.pi * 0.015 / details.KNURL_PITCH)
    assert mid.max() - mid.min() > 60  # はっきりした溝
    assert ((mid > 128) & (np.roll(mid, 1) <= 128)).sum() == n  # 溝の本数（周の継ぎ目もつながる）
    assert np.abs(x[0] - 128).max() <= 1 and np.abs(x[-1] - 128).max() <= 1  # 上下の端は平ら
    assert np.abs(nmap[h // 2, :, 1].astype(int) - 128).max() <= 2  # 縦方向には傾かない


def test_can_rings_inside_outline():
    """缶の上面のくぼみと底のドームは外形の内側（凸包が変わらない）。"""
    can = forms.aluminum_can(0.122, 0.066, top_d=0.054)
    cap, body = _pts(can.cap), _pts(can.body)
    H, rt = cap[-1][0], max(r for _, r in cap)
    recess = details.can_top_recess(cap)
    assert all(z <= H and r < rt for z, r in recess)
    assert H - min(z for z, _ in recess) == details.TOP_RECESS
    inner = details.can_cap_bottom(cap, recess)
    assert inner[0][0] == cap[0][0] and inner[0][1] < cap[0][1]
    dome = details.can_bottom_dome(body, 0.066)
    assert all(0 <= z <= details.DOME_RATIO * 0.066 + 1e-9 and r < body[0][1] for z, r in dome)
    assert dome[-1][0] > 0.009  # 中央は約 1 cm 持ち上がる
    assert all(a[1] > b[1] for a, b in zip(dome, dome[1:]))  # 外 → 中央
