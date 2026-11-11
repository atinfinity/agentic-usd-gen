"""落下テスト（agentic-usd-gen-droptest）の判定のテスト。Isaac Sim は使わず、drop_sim.py の出力を合成して確かめる。"""

import json
import math
import subprocess

import pytest

from agentic_usd_gen import drop_test
from agentic_usd_gen.drop_test import Limits, bounce, find_isaac_python, judge, settle_time

HZ = 60.0
G = 9.81


def _series(height=0.2, com=0.1, seconds=3.0, tilt_end=0.0, x_end=0.0, rebound=0.0):
    """自由落下して着地し、（rebound だけ跳ねて）止まる重心の推移。tilt_end・x_end は着地後に徐々にそうなる。"""
    rows, dt = [], 1 / HZ
    t_land = math.sqrt(2 * height / G)
    n = int(seconds * HZ)
    for i in range(n + 1):
        t = i * dt
        if t < t_land:
            z, k = com + height - G * t * t / 2, 0.0
        else:
            k = min(1.0, (t - t_land) / 0.5)  # 着地から 0.5 秒で落ち着く
            z = com + rebound * math.sin(math.pi * k) if k < 1 else com
        rows.append([round(t, 5), x_end * k, 0.0, z, tilt_end * k, 0.0, 0.0])
    for i in range(1, len(rows)):  # 速さは差分から
        a, b = rows[i - 1], rows[i]
        rows[i][5] = math.dist(a[1:4], b[1:4]) / dt
        rows[i][6] = math.radians(abs(b[4] - a[4])) / dt
    return rows


def _raw(**kw):
    raw = {"usd": "/a/b.usd", "height": 0.2, "seconds": 3.0, "hz": HZ, "mass_kg": 0.5, "com_local": [0, 0, 0.1],
           "kinematic": False, "com_rest_z": 0.1, "support_margin_m": 0.03, "settled_min_z": 0.0,
           "series": _series(), "placed_series": _series(height=0.0), "placed_tilt": 2.0}
    raw.update(kw)
    return raw


def test_pass():
    res = judge(_raw())
    assert res.passed, res.problems
    assert res.stand_angle_deg == pytest.approx(math.degrees(math.atan(0.3)), abs=0.01)
    assert res.settle_time_s is not None and res.settle_time_s < 1.0
    assert res.bounce_m == pytest.approx(0.0, abs=1e-6)


def test_tipped():
    """倒れ始める角度が十分あるのに倒れた（重心が下がった）のは不合格。"""
    res = judge(_raw(series=_series(tilt_end=90, com=0.03), placed_series=_series(height=0, tilt_end=90, com=0.03)))
    assert not res.passed
    assert any(p.startswith("落とすと倒れた") for p in res.problems)
    assert any(p.startswith("2° 傾けて置くと倒れた") for p in res.problems)


def test_rolled_cylinder_is_not_tipped():
    """寝かせた円筒が転がって傾いただけ（重心の高さが変わらない）なら倒れたとしない。"""
    res = judge(_raw(placed_series=_series(height=0, tilt_end=19)))
    assert res.passed, res.problems
    assert res.placed_tilt_deg == pytest.approx(19)


def test_unstandable_is_note():
    """立てて置けない形（倒れ始める角度が 5° 未満）が倒れて転がったのは注記にする。"""
    res = judge(_raw(support_margin_m=0.0, series=_series(tilt_end=90, com=0.02, x_end=0.1),
                     placed_series=_series(height=0, tilt_end=90, com=0.02)))
    assert res.passed, res.problems
    assert len(res.notes) == 2 and "立てて置けない形" in res.notes[0]


def test_thin_upright_falling_on_drop_is_note():
    """立てた薄い本（倒れ始める角度 7°、倒すのに重心を 0.8 mm 上げるだけ）が落として倒れたのは注記。傾け置きで倒れたら不合格。"""
    book = dict(support_margin_m=0.012, com_rest_z=0.094, com_local=[0, 0, 0.094])
    res = judge(_raw(**book, series=_series(com=0.012, tilt_end=90, x_end=0.12), placed_series=_series(height=0, com=0.094)))
    assert res.passed, res.problems
    assert len(res.notes) == 1 and "0.8 mm" in res.notes[0]
    res = judge(_raw(**book, series=_series(com=0.012, tilt_end=90, x_end=0.12),
                     placed_series=_series(height=0, com=0.012, tilt_end=90)))
    assert not res.passed and any(p.startswith("2° 傾けて置くと倒れた") for p in res.problems)
    res = judge(_raw(**book, height=0.02, series=_series(height=0.02, com=0.012, tilt_end=90)))
    assert not res.passed  # 低く落として倒れるのは形のせいではない


def test_bounce_sink_drift():
    res = judge(_raw(series=_series(rebound=0.08, x_end=0.1), settled_min_z=-0.02))
    assert not res.passed
    text = " ".join(res.problems)
    assert "跳ねすぎ" in text and "床を突き抜けた（20 mm 下）" in text and "転がった・滑った（10 cm）" in text


def test_not_settled():
    rows = _series()
    for r in rows[-10:]:
        r[5] = 0.5
    res = judge(_raw(series=rows))
    assert res.settle_time_s is None
    assert "3 秒で静止しない" in res.problems


def test_error_and_nan():
    assert judge({"usd": "x", "error": "boom"}).problems == ["実行できない: boom"]
    rows = _series()
    rows[-1][3] = None
    res = judge(_raw(series=rows))
    assert not res.passed and res.problems == ["爆発した（姿勢が NaN）"]


def test_limits():
    raw = _raw(series=_series(x_end=0.07))
    assert not judge(raw).passed
    assert judge(raw, Limits(max_drift_m=0.1)).passed


def test_bounce_ignores_tipping_drop():
    """倒れて重心が下がるだけなら跳ねではない。"""
    t = [0.0, 0.3, 0.4, 0.5]
    assert bounce(t, [0.3, 0.1, 0.05, 0.05], 0.2) == 0.0
    assert bounce(t, [0.3, 0.1, 0.15, 0.1], 0.2) == pytest.approx(0.05)


def test_bounce_of_tipped_tall_shape_is_against_fall():
    """背の高い扉が倒れると重心は落とした高さより大きく落ちる。跳ねはその落ちた高さと比べる。"""
    t = [i / 60 for i in range(60)]
    z = [1.2 - 1.1 * min(1.0, ti / 0.6) for ti in t]  # 重心 1.2 m → 0.1 m に倒れる
    z[45] += 0.11  # 着地後に 0.11 m 跳ねる（落とした 0.2 m の 55%、落ちた 1.1 m の 10%）
    raw = _raw(series=[[ti, 0, 0, zi, 90 * min(1.0, ti / 0.6), 0, 0] for ti, zi in zip(t, z)],
               com_rest_z=1.0, support_margin_m=0.03)
    res = judge(raw)
    assert res.bounce_m == pytest.approx(0.11, abs=1e-3)
    assert res.bounce_ratio == pytest.approx(0.1, abs=0.01)
    assert not any("跳ねすぎ" in p for p in res.problems)


def test_settle_time():
    t = [i / 10 for i in range(11)]
    assert settle_time(t, [0.0] * 11, [0.0] * 11) == 0.0
    speed = [1.0] * 3 + [0.0] * 8
    assert settle_time(t, speed, [0.0] * 11) == pytest.approx(0.3)
    assert settle_time(t, [1.0] * 8 + [0.0] * 3, [0.0] * 11) is None  # 止まってから 0.5 秒たっていない


def test_find_isaac_python(tmp_path, monkeypatch):
    monkeypatch.delenv("ISAACSIM_PYTHON", raising=False)
    monkeypatch.setenv("ISAACSIM_PATH", str(tmp_path / "none"))
    with pytest.raises(FileNotFoundError):
        find_isaac_python()
    py = tmp_path / "python"
    py.write_text("")
    monkeypatch.setenv("ISAACSIM_PYTHON", str(py))
    assert find_isaac_python() == str(py)
    sh = tmp_path / "isaac" / "python.sh"
    sh.parent.mkdir()
    sh.write_text("")
    monkeypatch.delenv("ISAACSIM_PYTHON")
    monkeypatch.setenv("ISAACSIM_PATH", str(sh.parent))
    assert find_isaac_python() == str(sh)
    assert find_isaac_python(str(py)) == str(py)


def test_simulate_reports_missing(tmp_path, monkeypatch):
    """Isaac Sim が途中で落ちたら、結果のないアセットはエラーとして返す。"""
    a, b = tmp_path / "a.usd", tmp_path / "b.usd"

    def fake_run(cmd, **kw):
        assert kw["env"]["OMNI_KIT_ACCEPT_EULA"] == "YES"
        assert cmd[cmd.index("--tilt") + 1] == "2.0"
        out = cmd[cmd.index("--out") + 1]
        with open(out, "w") as f:
            f.write(json.dumps({"usd": str(a.resolve()), **_raw(usd=str(a.resolve()))}) + "\n")
        return subprocess.CompletedProcess(cmd, 139)

    monkeypatch.setattr(drop_test.subprocess, "run", fake_run)
    rows = drop_test.simulate([a, b], "python", 0.2, 3.0, HZ, tmp_path / "log.txt")
    assert len(rows) == 2
    assert judge(rows[0]).passed
    assert "終了コード 139" in rows[1]["error"]
    assert not judge(rows[1]).passed


def test_ceiling_mount_is_flipped(tmp_path, monkeypatch):
    """天井付け（asset.json の mount が ceiling）は --ceiling で渡し、結果に mount が残る。"""
    cam, box = tmp_path / "cam" / "cam.usd", tmp_path / "box" / "box.usd"
    for p, extra in ((cam, {"mount": "ceiling"}), (box, {})):
        p.parent.mkdir()
        p.write_text("")
        (p.parent / "asset.json").write_text(json.dumps({"usd": p.name, **extra}))
    assert drop_test.mount_of(cam) == "ceiling"
    assert drop_test.mount_of(box) == "floor"
    assert drop_test.mount_of(tmp_path / "none.usd") == "floor"

    def fake_run(cmd, **kw):
        assert f"--ceiling={cam.resolve()}" in cmd
        assert not any(c.startswith("--ceiling=") and "box" in c for c in cmd)
        with open(cmd[cmd.index("--out") + 1], "w") as f:
            f.write(json.dumps(_raw(usd=str(cam.resolve()), mount="ceiling")) + "\n")
            f.write(json.dumps(_raw(usd=str(box.resolve()))) + "\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(drop_test.subprocess, "run", fake_run)
    rows = drop_test.simulate([cam, box], "python", 0.2, 3.0, HZ, tmp_path / "log.txt")
    assert [judge(r).mount for r in rows] == ["ceiling", "floor"]
