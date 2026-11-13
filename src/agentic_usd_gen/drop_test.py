"""Isaac Sim で書き出したアセットを床に落とし、倒れ・跳ね・突き抜け・静止までの時間を確かめる（agentic-usd-gen-droptest）。

1 点につき 2 回動かす。落下（まっすぐ --height から落とす）で跳ね・突き抜け・静止・ずれ・倒れを、
傾け置き（--tilt 度傾けて床すれすれに置く）で、少しずれて置かれても立っていられるかを見る。

落とすのは Isaac Sim の Python で動く isaac/drop_sim.py（描画なしで PhysX を直接進める）。ここではそれを呼び出し、
返ってきた重心の高さ・傾き・速さの推移から判定して一覧にする。判定はここだけで行うので、Isaac Sim がなくてもテストできる。

Isaac Sim の Python は --isaac-python、環境変数 ISAACSIM_PYTHON（pip 版の venv の python）、
ISAACSIM_PATH の python.sh（既定 ~/isaacsim）の順に探す。

天井付けの什器（隣の asset.json の mount が ceiling）は、上下を返して取り付け面を下にして落とす。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .simready import find_assets

SIM_SCRIPT = Path(__file__).parent / "isaac" / "drop_sim.py"
G = 9.81


@dataclass
class Limits:
    max_tilt_deg: float = 15.0  # これより傾いて止まり、
    min_com_drop: float = 0.1  # 重心が置いたときの高さからこの割合以上下がったら「倒れた」（寝かせた円筒が転がっただけは除く）
    max_bounce: float = 0.25  # 跳ね返った高さ（重心）÷ 重心が落ちた高さ（倒れなければ落とした高さ）。これを超えたら「跳ねすぎ」
    max_sink_m: float = 0.01  # 床より下に出たコリジョンの深さ。超えたら「突き抜け」
    max_drift_m: float = 0.05  # 止まった位置の水平のずれ。超えたら「転がった・滑った」
    still_speed: float = 0.01  # [m/s] これより遅く
    still_spin: float = 0.1  # [rad/s] これより回転が遅ければ静止とみなす
    still_hold_s: float = 0.5  # 最後にこの時間以上止まっていれば「静止した」
    min_stand_deg: float = 5.0  # 倒れ始める角度がこれ未満の形（薄いカード・細長い傘など）は、倒れても想定内
    # 倒すのに重心を持ち上げる高さ（角の上まで）が落とした高さのこの割合未満の形（立てた薄い本など）は、
    # 落としたときの着地のわずかな回転で倒れても想定内（傾け置きの判定はそのまま）
    min_tip_rise: float = 0.01


@dataclass
class Result:
    asset: str
    passed: bool
    problems: list[str] = field(default_factory=list)  # 不合格の理由（日本語の短い文）
    notes: list[str] = field(default_factory=list)  # 合否に含めない注記（立てて置けない形が倒れた、など）
    kinematic: bool = False  # 什器（床に固定）。テストの間だけ動く剛体にして落とした
    mount: str = "floor"  # ceiling なら上下を返して（取り付け面を下にして）落とした
    mass_kg: float | None = None
    center_of_mass_m: list[float] | None = None
    tilt_deg: float | None = None  # 落下で止まったときの傾き
    placed_tilt_deg: float | None = None  # 傾け置きで止まったときの傾き（傾け置きをしなければ None）
    bounce_m: float | None = None  # 着地後に重心が跳ね上がった高さ（止まった高さから）
    bounce_ratio: float | None = None  # bounce_m ÷ 落とした高さ
    stand_angle_deg: float | None = None  # 置いた向きのまま静かに傾けたとき倒れ始める角度（接地面と重心から）
    sink_m: float | None = None  # 床より下に出たコリジョンの深さ
    drift_m: float | None = None  # 止まった位置の水平のずれ
    settle_time_s: float | None = None  # 落とし始めてから静止するまで（静止しなければ None）
    height_m: float | None = None
    seconds: float | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def judge(raw: dict, limits: Limits = Limits()) -> Result:
    """drop_sim.py の 1 行分を判定する。"""
    usd = raw.get("usd", "?")
    res = Result(asset=usd, passed=False, kinematic=bool(raw.get("kinematic")), mount=raw.get("mount") or "floor",
                 mass_kg=_r(raw.get("mass_kg"), 4),
                 center_of_mass_m=[_r(v, 4) for v in raw["com_local"]] if raw.get("com_local") else None,
                 height_m=raw.get("height"), seconds=raw.get("seconds"))
    if raw.get("error"):
        res.error = raw["error"]
        res.problems.append(f"実行できない: {raw['error']}")
        return res
    series = raw.get("series") or []
    if not series or any(v is None for row in series for v in row):
        res.error = "PhysX の計算が発散した（NaN）"
        res.problems.append("爆発した（姿勢が NaN）")
        return res

    t = [row[0] for row in series]
    x, y, z = ([row[i] for row in series] for i in (1, 2, 3))
    tilt, speed, spin = ([row[i] for row in series] for i in (4, 5, 6))
    h = raw["height"]

    res.tilt_deg = round(tilt[-1], 2)
    placed = raw.get("placed_series") or []
    if placed and all(v is not None for row in placed for v in row):
        res.placed_tilt_deg = round(placed[-1][4], 2)
    margin, com_z = raw.get("support_margin_m"), raw.get("com_rest_z")  # com_z: 置いたときの重心の高さ（床から）

    def tipped(deg: float | None, final_z: float) -> bool:
        return deg is not None and deg > limits.max_tilt_deg and (
            not com_z or final_z < com_z * (1 - limits.min_com_drop))

    res.drift_m = round(math.hypot(x[-1] - x[0], y[-1] - y[0]), 4)
    res.bounce_m = round(bounce(t, z, h), 4)
    # 跳ねは重心が落ちた高さと比べる。立てて置けない背の高い形（扉など）は倒れて重心が落とした高さより大きく落ち、
    # その分強く床を打つので、落とした高さと比べると跳ねすぎに見える
    fall = max(h, z[0] - min(z)) if z else h
    res.bounce_ratio = round(res.bounce_m / fall, 3) if fall > 0 else None
    sink = -raw["settled_min_z"] if raw.get("settled_min_z") is not None else None
    res.sink_m = round(max(0.0, sink), 4) if sink is not None else None
    res.settle_time_s = settle_time(t, speed, spin, limits)
    if margin is not None and com_z:
        res.stand_angle_deg = round(math.degrees(math.atan2(margin, com_z)), 2)
    # 立てて置けない形が倒れて転がったのは形のとおりなので、合否に含めない（重心・質量の誤りではない）
    unstandable = res.stand_angle_deg is not None and res.stand_angle_deg < limits.min_stand_deg
    # 倒すのに重心を持ち上げる高さ。立てた本（厚さ 24 mm・高さ 188 mm）は 0.8 mm で、0.2 m から落とすと
    # 着地のエネルギーのわずかでも回転に回れば倒れる（実物も同じ）
    rise = math.hypot(margin, com_z) - com_z if margin is not None and com_z else None
    drop_tippy = unstandable or (rise is not None and rise < limits.min_tip_rise * h)

    if res.sink_m is not None and res.sink_m > limits.max_sink_m:
        res.problems.append(f"床を突き抜けた（{res.sink_m * 1000:.0f} mm 下）")
    fell = tipped(res.tilt_deg, z[-1])
    checks = [("落とすと", res.tilt_deg, fell, drop_tippy)]
    if res.placed_tilt_deg is not None:
        checks.append((f"{raw.get('placed_tilt', 0):g}° 傾けて置くと", res.placed_tilt_deg,
                       tipped(res.placed_tilt_deg, placed[-1][3]), unstandable))
    for what, deg, bad, expected in checks:
        if not bad:
            continue
        if unstandable:
            res.notes.append(f"立てて置けない形なので、{what}倒れた（{deg:.0f}°。倒れ始める角度 {res.stand_angle_deg:.1f}°）")
        elif expected:
            res.notes.append(f"倒すのに重心を {rise * 1000:.1f} mm 持ち上げるだけの形なので、{what}倒れた"
                             f"（{deg:.0f}°。倒れ始める角度 {res.stand_angle_deg:.1f}°）")
        else:
            res.problems.append(f"{what}倒れた（{deg:.0f}°）" + (
                f"。倒れ始める角度は {res.stand_angle_deg:.1f}° あり、重心かコリジョンの形を確かめる"
                if res.stand_angle_deg is not None else ""))
    if res.bounce_ratio is not None and res.bounce_ratio > limits.max_bounce:
        res.problems.append(f"跳ねすぎ（重心が落ちた高さの {res.bounce_ratio:.0%}）")
    if res.settle_time_s is None:
        res.problems.append(f"{res.seconds:g} 秒で静止しない")
    if res.drift_m > limits.max_drift_m and not (drop_tippy and fell):
        res.problems.append(f"転がった・滑った（{res.drift_m * 100:.0f} cm）")
    res.passed = not res.problems
    return res


def bounce(t: list[float], z: list[float], height: float) -> float:
    """着地（自由落下で床に届く時刻）の後に、重心がそれまでの最低点からいちばん上がった高さ。
    倒れると重心は下がるだけなので、跳ねとは数えない。"""
    t_land = math.sqrt(2 * height / G) if height > 0 else 0.0
    low, best = math.inf, 0.0
    for ti, zi in zip(t, z):
        if ti < t_land:
            continue
        low = min(low, zi)
        best = max(best, zi - low)
    return best


def settle_time(t: list[float], speed: list[float], spin: list[float], limits: Limits = Limits()) -> float | None:
    """最後に動いていた時刻の次（以後ずっと止まっている）。最後の still_hold_s 秒が止まっていなければ None。"""
    last_moving = None
    for i in range(len(t) - 1, -1, -1):
        if speed[i] >= limits.still_speed or spin[i] >= limits.still_spin:
            last_moving = i
            break
    if last_moving is None:
        return 0.0
    if last_moving + 1 >= len(t) or t[-1] - t[last_moving + 1] < limits.still_hold_s:
        return None
    return round(t[last_moving + 1], 3)


def _r(v, n):
    return round(v, n) if isinstance(v, (int, float)) else None


def find_isaac_python(explicit: str | None = None) -> str:
    root = Path(os.environ.get("ISAACSIM_PATH", Path.home() / "isaacsim"))
    for c in [explicit, os.environ.get("ISAACSIM_PYTHON"), str(root / "python.sh")]:
        if c and Path(c).is_file():
            return c
    raise FileNotFoundError("Isaac Sim の Python が見つかりません。--isaac-python か環境変数 ISAACSIM_PYTHON"
                            "（pip 版の venv の python）・ISAACSIM_PATH（python.sh のあるフォルダ）で指定してください")


def mount_of(usd: Path) -> str:
    """隣の asset.json（usd がこのファイルのもの）の mount。なければ floor。"""
    aj = usd.parent / "asset.json"
    try:
        meta = json.loads(aj.read_text())
    except (OSError, ValueError):
        return "floor"
    if meta.get("usd") not in (None, usd.name):
        return "floor"
    return meta.get("mount") or "floor"


def simulate(assets: list[Path], python: str, height: float, seconds: float, hz: float, log: Path,
             tilt: float = 2.0) -> list[dict]:
    """drop_sim.py を Isaac Sim の Python で 1 回起動し、全アセットを順に落とす。途中で落ちても、そこまでの結果は返す。"""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "raw.jsonl"
        ceiling = [a for a in assets if mount_of(a) == "ceiling"]
        cmd = [python, str(SIM_SCRIPT), "--out", str(out), "--height", str(height), "--seconds", str(seconds),
               "--hz", str(hz), "--tilt", str(tilt), *(f"--ceiling={a.resolve()}" for a in ceiling),
               *(str(a.resolve()) for a in assets)]
        env = {**os.environ, "OMNI_KIT_ACCEPT_EULA": "YES"}  # ないと EULA の確認で止まる
        with log.open("w") as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=tmp)
        rows = [json.loads(line) for line in out.read_text().splitlines()] if out.exists() else []
    done = {r["usd"] for r in rows}
    for a in assets:
        if str(a.resolve()) not in done:
            rows.append({"usd": str(a.resolve()), "error": f"Isaac Sim が途中で終了した（終了コード {proc.returncode}。{log}）"})
    return rows


def _print(res: Result, base: Path) -> None:
    mark = "OK" if res.passed else "NG"
    try:
        name = Path(res.asset).relative_to(base)
    except ValueError:
        name = Path(res.asset)
    if res.error:
        print(f"{mark} {name}  {'・'.join(res.problems)}")
        return
    settle = f"{res.settle_time_s:.2f} 秒" if res.settle_time_s is not None else "-"
    fixed = ("  什器" if res.kinematic else "") + ("（天井付け。上下を返して落とした）" if res.mount == "ceiling" else "")
    placed = f"・傾け置き {res.placed_tilt_deg:.1f}°" if res.placed_tilt_deg is not None else ""
    print(f"{mark} {name}  静止 {settle}・傾き {res.tilt_deg:.1f}°・跳ね {res.bounce_m * 1000:.0f} mm"
          f"・ずれ {res.drift_m * 1000:.0f} mm{placed}{fixed}")
    for p in res.problems:
        print(f"   {p}")
    for n in res.notes:
        print(f"   （注）{n}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-droptest",
                                description="Isaac Sim（headless）でアセットを床に落とし、倒れ・跳ね・突き抜け・静止までの時間を確かめる")
    p.add_argument("paths", nargs="*", type=Path, help="USD ファイルかフォルダ（既定: assets/）")
    p.add_argument("--height", type=float, default=0.2, help="[m] 落とす高さ（床から底面まで。既定 0.2）")
    p.add_argument("--seconds", type=float, default=8.0,
                   help="[s] 落としてから見る時間（既定 8。戸・障子などの可動部が止まるまでに 5 秒を超える内装があるため）")
    p.add_argument("--tilt", type=float, default=2.0, help="[度] 傾け置きの傾き（既定 2。0 なら傾け置きをしない）")
    p.add_argument("--hz", type=float, default=60.0, help="物理の刻み [Hz]（既定は Isaac Sim と同じ 60）")
    p.add_argument("--max-tilt", type=float, default=Limits.max_tilt_deg, help="[度] これより傾いたら倒れたとみなす")
    p.add_argument("--max-bounce", type=float, default=Limits.max_bounce, help="跳ね返った高さ ÷ 重心が落ちた高さの上限")
    p.add_argument("--max-drift", type=float, default=Limits.max_drift_m, help="[m] 止まった位置の水平のずれの上限")
    p.add_argument("--output", type=Path, help="結果を JSON で書き出す先")
    p.add_argument("--series", action="store_true", help="JSON に重心・傾き・速さの推移も入れる")
    p.add_argument("--isaac-python", help="Isaac Sim の Python（python.sh か、pip 版の venv の python）")
    p.add_argument("--log", type=Path, help="Isaac Sim のログの書き出し先（既定: 一時ファイル）")
    args = p.parse_args(argv)

    try:
        python = find_isaac_python(args.isaac_python)
    except FileNotFoundError as e:
        sys.exit(str(e))
    assets = find_assets(args.paths or [Path("assets")])
    if not assets:
        sys.exit("落とす USD が見つかりません")
    base = Path(os.path.commonpath([a.resolve().parent for a in assets]))  # 一覧ではここからの相対パスで出す
    log = args.log or Path(tempfile.gettempdir()) / "agentic-usd-gen-droptest.log"
    print(f"{len(assets)} 点を落とします（高さ {args.height} m・{args.seconds:g} 秒。Isaac Sim のログ: {log}）", flush=True)

    limits = Limits(max_tilt_deg=args.max_tilt, max_bounce=args.max_bounce, max_drift_m=args.max_drift)
    raws = simulate(assets, python, args.height, args.seconds, args.hz, log, args.tilt)
    pairs = sorted(((judge(r, limits), r) for r in raws), key=lambda p: (p[0].passed, p[0].asset))
    results = [res for res, _ in pairs]
    for res in results:
        _print(res, base)
    if args.output:
        out = []
        for res, raw in pairs:
            d = res.to_dict()
            if args.series:
                cols = ["t", "com_x", "com_y", "com_z", "tilt_deg", "speed", "spin"]
                for key in ("series", "placed_series"):
                    if raw.get(key):
                        d[key] = {"columns": cols, "rows": raw[key]}
            out.append(d)
        args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    failed = sum(not r.passed for r in results)
    print(f"\n合格: {len(results) - failed} / {len(results)} 点")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
