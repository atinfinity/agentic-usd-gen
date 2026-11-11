"""Isaac Sim で書き出したアセットの関節（扉・ふた）を動かし、限界まで開閉できるか・限界で止まるかを確かめる（agentic-usd-gen-jointtest）。

関節（RevoluteJoint・PrismaticJoint）ごとに、下限・上限と、その外側（回転は 20°、直動は 0.2 m）を目標にして位置ドライブで動かす。
本体は床に固定する（什器はもともとキネマティック。動く商品もテストの間だけ固定する）。

動かすのは Isaac Sim の Python で動く isaac/joint_sim.py（描画なしで PhysX を直接進める）。ここではそれを呼び出し、
返ってきた関節の位置の推移から判定して一覧にする。判定はここだけで行うので、Isaac Sim がなくてもテストできる。
Isaac Sim の Python の探し方は agentic-usd-gen-droptest と同じ（--isaac-python・ISAACSIM_PYTHON・ISAACSIM_PATH）。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .drop_test import find_isaac_python
from .simready import find_assets

SIM_SCRIPT = Path(__file__).parent / "isaac" / "joint_sim.py"
DIRECTIONS = ("X", "Y", "Z")


@dataclass
class Limits:
    reach_deg: float = 3.0  # 限界を狙って、これより手前で止まったら「届かない」（枠・本体にぶつかっている）
    reach_m: float = 0.02
    over_deg: float = 1.0  # 限界の外を狙って、限界をこれより超えて止まったら「限界を超えた」
    over_m: float = 0.005
    still_deg: float = 0.2  # 最後の 0.5 秒にこれより動いていたら「止まらない」
    still_m: float = 0.002
    body_m: float = 0.001  # 本体（床に固定）がこれより動いたら「本体が動いた」


@dataclass
class JointResult:
    joint: str
    type: str  # revolute / prismatic
    axis: str
    lower: float | None
    upper: float | None
    reached: dict[str, float] = field(default_factory=dict)  # 目標 → 止まった位置（回転は度、直動は m）
    open_move_m: list[float] | None = None  # 限界まで開いたときの可動部の重心の動き（0 からいちばん遠い限界）


@dataclass
class Result:
    asset: str
    passed: bool
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    kinematic: bool = True  # False なら動く商品。テストの間だけ本体を床に固定した
    joints: list[JointResult] = field(default_factory=list)
    seconds: float | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _unit(rev: bool) -> str:
    return "°" if rev else " m"


def _fmt(v: float, rev: bool) -> str:
    return f"{v:+.1f}°" if rev else f"{v:+.3f} m"


def direction(move: list[float] | None, min_m: float = 0.05) -> str:
    """重心の動きのうち、min_m 以上の成分（例: -X 0.38 m・+Y 0.42 m）。開き戸は横と前後の両方に動く。"""
    if not move:
        return "-"
    parts = [f"{'+' if v >= 0 else '-'}{a} {abs(v):.2f} m" for a, v in zip(DIRECTIONS, move) if abs(v) >= min_m]
    return "・".join(parts) or "ほぼ動かない"


def judge(raw: dict, limits: Limits = Limits()) -> Result:
    """joint_sim.py の 1 行分（1 アセット）を判定する。"""
    res = Result(asset=raw.get("usd", "?"), passed=False, kinematic=raw.get("kinematic", True) is not False,
                 seconds=raw.get("seconds"))
    if raw.get("error"):
        res.error = raw["error"]
        res.problems.append(f"実行できない: {raw['error']}")
        return res
    if not res.kinematic:
        res.notes.append("動く商品なので、テストの間だけ本体を床に固定した")
    hz = raw.get("hz") or 60.0
    for j in raw.get("joints") or []:
        rev = j["type"] == "revolute"
        name = j["joint"].rsplit("/", 2)[-2] if j["joint"].count("/") >= 2 else j["joint"]
        jr = JointResult(joint=j["joint"], type=j["type"], axis=j.get("axis") or "?", lower=j.get("lower"),
                         upper=j.get("upper"))
        res.joints.append(jr)
        lo, hi = jr.lower, jr.upper
        reach = limits.reach_deg if rev else limits.reach_m
        over = limits.over_deg if rev else limits.over_m
        still = limits.still_deg if rev else limits.still_m
        free = rev and lo is None and hi is None and bool(j.get("runs"))  # 限界なしの回転（回転ラック）
        if lo is None and hi is None and not free:
            res.notes.append(f"{name}: 限界が設定されていないので動かしていない")
            continue
        if free:
            res.notes.append(f"{name}: 限界なしの回転なので、両向きに回して届くかだけを見た")
        for run in j.get("runs") or []:
            t = run["target"]
            if run.get("error"):
                res.problems.append(f"{name}: {_fmt(t, rev)} へ動かせない（{run['error']}）")
                continue
            pos = [row[1] for row in run.get("series") or []]
            if not pos or any(v is None for v in pos):
                res.problems.append(f"{name}: {_fmt(t, rev)} へ動かすと爆発した（NaN）")
                continue
            final = pos[-1]
            jr.reached[f"{t:g}"] = round(final, 4)
            tail = pos[-int(hz / 2) - 1:]
            if max(tail) - min(tail) > still:
                res.problems.append(f"{name}: {_fmt(t, rev)} を狙うと止まらない（最後の 0.5 秒に "
                                    f"{max(tail) - min(tail):.3g}{_unit(rev)} 動いた）")
            moved = run.get("body_moved_m")
            if moved is not None and moved > limits.body_m:
                res.problems.append(f"{name}: 動かすと本体が動いた（{moved * 1000:.0f} mm）")
            if free:
                if abs((final - t + 180) % 360 - 180) > reach:
                    res.problems.append(f"{name}: {_fmt(t, rev)} まで回らない（{_fmt(final, rev)} で止まった。"
                                        "枠や本体にぶつかっていないか確かめる）")
                if jr.open_move_m is None:
                    jr.open_move_m = [round(v, 4) for v in run.get("com_move") or []] or None
            elif t in (lo, hi):  # 限界を狙った
                if abs(final - t) > reach:
                    res.problems.append(f"{name}: {_fmt(t, rev)} まで届かない（{_fmt(final, rev)} で止まった。"
                                        "枠や本体にぶつかっていないか確かめる）")
                far = max((v for v in (lo, hi) if v is not None), key=abs)
                if t == far and abs(far) > 0:
                    jr.open_move_m = [round(v, 4) for v in run.get("com_move") or []] or None
            else:  # 限界の外を狙った
                edge = lo if lo is not None and t < lo else hi
                if edge is not None and abs(final - edge) > over and (final - edge) * (t - edge) > 0:
                    res.problems.append(f"{name}: 限界 {_fmt(edge, rev)} を超えた（{_fmt(t, rev)} を狙うと "
                                        f"{_fmt(final, rev)} まで動いた）")
    if not res.joints:
        res.notes.append("関節がない")
    res.passed = not res.problems
    return res


def has_joints(usd: Path) -> bool:
    """USD に RevoluteJoint・PrismaticJoint があるか（ペイロードの中まで見る）。"""
    from pxr import Usd, UsdPhysics

    stage = Usd.Stage.Open(str(usd), Usd.Stage.LoadAll)
    return any(p.IsA(UsdPhysics.RevoluteJoint) or p.IsA(UsdPhysics.PrismaticJoint)
               for p in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()))


def simulate(assets: list[Path], python: str, seconds: float, hz: float, log: Path) -> list[dict]:
    """joint_sim.py を Isaac Sim の Python で 1 回起動し、全アセットを順に動かす。途中で落ちても、そこまでの結果は返す。"""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "raw.jsonl"
        cmd = [python, str(SIM_SCRIPT), "--out", str(out), "--seconds", str(seconds), "--hz", str(hz),
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
    print(f"{mark} {name}")
    for j in res.joints:
        rev = j.type == "revolute"
        link = j.joint.rsplit("/", 2)[-2] if j.joint.count("/") >= 2 else j.joint
        free = j.lower is None and j.upper is None
        rng = "限界なし" if free else " 〜 ".join("-" if v is None else _fmt(v, rev) for v in (j.lower, j.upper))
        stops = "・".join(f"{_fmt(float(t), rev)}→{_fmt(v, rev)}" for t, v in j.reached.items())
        move = "回すと重心" if free else "開くと重心"
        print(f"   {link}（{'回転' if rev else '直動'} {j.axis}。{rng}）  {stops}  {move} {direction(j.open_move_m)}")
    for p in res.problems:
        print(f"   {p}")
    for n in res.notes:
        print(f"   （注）{n}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-jointtest",
                                description="Isaac Sim（headless）でアセットの関節（扉・ふた）を動かし、限界まで開閉できるか・限界で止まるかを確かめる")
    p.add_argument("paths", nargs="*", type=Path, help="USD ファイルかフォルダ（既定: assets/）。関節のないものは除く")
    p.add_argument("--seconds", type=float, default=4.0, help="[s] 1 つの目標へ動かす時間（既定 4）")
    p.add_argument("--hz", type=float, default=60.0, help="物理の刻み [Hz]（既定は Isaac Sim と同じ 60）")
    p.add_argument("--reach-deg", type=float, default=Limits.reach_deg, help="[度] 限界からこれより手前で止まったら届かない")
    p.add_argument("--reach-m", type=float, default=Limits.reach_m, help="[m] 直動の関節で、同じく届かないとみなす量")
    p.add_argument("--output", type=Path, help="結果を JSON で書き出す先")
    p.add_argument("--series", action="store_true", help="JSON に関節の位置の推移も入れる")
    p.add_argument("--isaac-python", help="Isaac Sim の Python（python.sh か、pip 版の venv の python）")
    p.add_argument("--log", type=Path, help="Isaac Sim のログの書き出し先（既定: 一時ファイル）")
    args = p.parse_args(argv)

    try:
        python = find_isaac_python(args.isaac_python)
    except FileNotFoundError as e:
        sys.exit(str(e))
    found = find_assets(args.paths or [Path("assets")])
    assets = [a for a in found if has_joints(a)]
    if not assets:
        sys.exit("関節のある USD が見つかりません")
    base = Path(os.path.commonpath([a.resolve().parent for a in assets]))
    log = args.log or Path(tempfile.gettempdir()) / "agentic-usd-gen-jointtest.log"
    print(f"関節のある {len(assets)} 点を動かします（{len(found) - len(assets)} 点は関節がないので省略。"
          f"Isaac Sim のログ: {log}）", flush=True)

    limits = Limits(reach_deg=args.reach_deg, reach_m=args.reach_m)
    raws = simulate(assets, python, args.seconds, args.hz, log)
    pairs = sorted(((judge(r, limits), r) for r in raws), key=lambda p: (p[0].passed, p[0].asset))
    for res, _ in pairs:
        _print(res, base)
    if args.output:
        out = []
        for res, raw in pairs:
            d = res.to_dict()
            if args.series:
                d["series"] = {j["joint"]: {f"{r['target']:g}": r.get("series") for r in j.get("runs") or []}
                               for j in raw.get("joints") or []}
            out.append(d)
        args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    failed = sum(not r.passed for r, _ in pairs)
    print(f"\n合格: {len(pairs) - failed} / {len(pairs)} 点")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
