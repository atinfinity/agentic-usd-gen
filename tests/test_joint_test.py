"""関節の開閉テスト（agentic-usd-gen-jointtest）の判定のテスト。Isaac Sim は使わず、joint_sim.py の出力を合成して確かめる。"""

import pytest

from agentic_usd_gen.joint_test import Limits, direction, judge

HZ = 60.0


def _run(target, final, seconds=2.0, settle=1.0, body=0.0, com=(0.0, 0.0, 0.0)):
    """0 から final へ settle 秒で動き、その後止まる関節の位置の推移。"""
    n = int(seconds * HZ)
    series = [[i / HZ, final * min(1.0, i / HZ / settle)] for i in range(n + 1)]
    return {"target": target, "series": series, "com_move": list(com), "body_moved_m": body}


def _raw(runs, lower=0.0, upper=90.0, kind="revolute", **kw):
    raw = {"usd": "/a/door.usd", "kinematic": True, "hz": HZ, "seconds": 2.0,
           "joints": [{"joint": "/door/LeafLink/Joint", "type": kind, "axis": "Z", "lower": lower, "upper": upper,
                       "runs": runs}]}
    raw.update(kw)
    return raw


def _good_runs():
    return [_run(-20.0, 0.0), _run(0.0, 0.0), _run(90.0, 89.8, com=(-0.38, 0.42, 0.0)), _run(110.0, 90.05)]


def test_pass():
    res = judge(_raw(_good_runs()))
    assert res.passed, res.problems
    (j,) = res.joints
    assert j.reached["90"] == pytest.approx(89.8)
    assert j.open_move_m == [-0.38, 0.42, 0.0]


def test_does_not_reach_limit():
    """枠にぶつかって限界まで開かない。"""
    runs = _good_runs()
    runs[2] = _run(90.0, 60.0)
    res = judge(_raw(runs))
    assert not res.passed
    assert any("+90.0° まで届かない" in p for p in res.problems)


def test_passes_limit():
    runs = _good_runs()
    runs[3] = _run(110.0, 105.0)
    res = judge(_raw(runs))
    assert any("限界 +90.0° を超えた" in p for p in res.problems)
    runs = _good_runs()
    runs[0] = _run(-20.0, -10.0)  # 閉じる側の限界も
    assert any("限界 +0.0° を超えた" in p for p in judge(_raw(runs)).problems)


def test_not_settled_and_body_moved():
    runs = _good_runs()
    runs[2] = _run(90.0, 89.8, settle=1.9)  # 最後の 0.5 秒もまだ動いている
    runs[1] = _run(0.0, 0.0, body=0.01)
    res = judge(_raw(runs))
    assert any("止まらない" in p for p in res.problems)
    assert any("本体が動いた（10 mm）" in p for p in res.problems)


def test_prismatic_tolerance():
    runs = [_run(-0.2, 0.0), _run(0.0, 0.0), _run(0.78, 0.773, com=(0.77, 0, 0)), _run(0.98, 0.78)]
    res = judge(_raw(runs, 0.0, 0.78, kind="prismatic"))
    assert res.passed, res.problems
    assert not judge(_raw(runs, 0.0, 0.78, kind="prismatic"), Limits(reach_m=0.005)).passed


def test_error_and_nan():
    assert not judge({"usd": "/a.usd", "error": "boom"}).passed
    runs = _good_runs()
    runs[2]["series"][-1][1] = None
    assert any("爆発" in p for p in judge(_raw(runs)).problems)


def test_no_limits_and_dynamic_body():
    res = judge(_raw([], lower=None, upper=None, kinematic=False))
    assert res.passed
    assert any("限界が設定されていない" in n for n in res.notes)
    assert any("本体を床に固定した" in n for n in res.notes)


def test_free_revolute():
    """限界なしの回転（回転ラック）は、両向きに回して届けば合格。限界の判定はしない。"""
    res = judge(_raw([_run(-90.0, -89.7), _run(90.0, 89.6)], lower=None, upper=None))
    assert res.passed, res.problems
    assert any("限界なしの回転" in n for n in res.notes)
    assert res.joints[0].reached == {"-90": pytest.approx(-89.7), "90": pytest.approx(89.6)}
    stuck = judge(_raw([_run(-90.0, -10.0), _run(90.0, 89.6)], lower=None, upper=None))
    assert any("-90.0° まで回らない" in p for p in stuck.problems)


def test_direction():
    assert direction([-0.38, 0.42, 0.01]) == "-X 0.38 m・+Y 0.42 m"
    assert direction([0.0, 0.0, 0.0]) == "ほぼ動かない"
    assert direction(None) == "-"
