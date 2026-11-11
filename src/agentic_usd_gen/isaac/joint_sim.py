"""Isaac Sim の Python で動かす関節（扉・ふた）の開閉テスト（agentic-usd-gen-jointtest から呼ぶ。usd-core の環境では動かない）。

関節（RevoluteJoint・PrismaticJoint）ごとに、目標を変えて何度か動かす。毎回、床と物理シーンだけのステージをメモリ上に作り、
アセットを参照して、その関節にだけ位置ドライブを付けて目標へ動かす。描画はせず、PhysX を固定の刻みで直接進める。
目標は下限・上限と、その外側（回転は 20°、直動は 0.2 m）。外側を狙ったときに限界で止まるかも見る。
本体（ルートの剛体）は床に固定する。什器はもともとキネマティックで、動く商品もテストの間だけキネマティックにする
（キネマティックな剛体にはアーティキュレーションを付けられないので、ArticulationRootAPI はこのステージで外す）。

毎ステップの関節の位置（回転は度、直動は m。置いたときの姿勢を 0 とする）と、可動部の重心の動き・本体のずれを、
1 アセット 1 行の JSON で書き出す。判定（届かない・限界を超えた・止まらない）は agentic-usd-gen-jointtest 側で行う（joint_test.py）。

    $ISAACSIM_PYTHON joint_sim.py --out raw.jsonl [--seconds 4] a.usd b.usd ...

Isaac Sim 6.1.0（pip 版）で動作確認。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("usd", nargs="+")
ap.add_argument("--out", required=True, help="結果を 1 アセット 1 行の JSON で追記する先")
ap.add_argument("--seconds", type=float, default=4.0, help="[s] 1 つの目標へ動かす時間")
ap.add_argument("--hz", type=float, default=60.0, help="物理の刻み [Hz]（既定は Isaac Sim と同じ 60）")
ap.add_argument("--over-deg", type=float, default=20.0, help="[度] 回転の関節で、限界の外を狙う量")
ap.add_argument("--over-m", type=float, default=0.2, help="[m] 直動の関節で、限界の外を狙う量")
args = ap.parse_args()

from isaacsim import SimulationApp  # noqa: E402

app = SimulationApp({"headless": True})

import omni.physx  # noqa: E402
from pxr import Gf, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics, UsdUtils  # noqa: E402

SIM = omni.physx.get_physx_simulation_interface()
PX = omni.physx.get_physx_interface()
ASSET = Sdf.Path("/World/Asset")
AXES = {"X": Gf.Vec3d(1, 0, 0), "Y": Gf.Vec3d(0, 1, 0), "Z": Gf.Vec3d(0, 0, 1)}
# 位置ドライブの強さ。回転は [N·m/度]・[N·m·s/度]、直動は [N/m]・[N·s/m]。扉 30 kg・ふた 1 kg のどちらも
# 0.3〜0.5 秒ほどで目標に着き、行き過ぎない（減衰が強め）
DRIVES = {"angular": (200.0, 50.0), "linear": (3000.0, 1500.0)}


def build(usd: str) -> tuple[Usd.Stage, dict]:
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.81)
    px = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    px.CreateEnableGPUDynamicsAttr(False)  # 少しの剛体だけなので CPU で十分
    px.CreateBroadphaseTypeAttr("MBP")
    px.CreateTimeStepsPerSecondAttr(args.hz)
    plane = UsdGeom.Plane.Define(stage, "/World/Floor")
    plane.CreateAxisAttr("Z")
    plane.CreateWidthAttr(20.0)
    plane.CreateLengthAttr(20.0)
    UsdPhysics.CollisionAPI.Apply(plane.GetPrim())
    asset = stage.DefinePrim(ASSET)
    asset.GetReferences().AddReference(usd)
    stage.Load()

    bodies = [p for p in Usd.PrimRange(asset, Usd.TraverseInstanceProxies()) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    if not bodies:
        raise RuntimeError("剛体がない（RigidBodyAPI の付いたプリムがない）")
    root = bodies[0]
    rb = UsdPhysics.RigidBodyAPI(root)
    info = {"kinematic": bool(rb.GetKinematicEnabledAttr().Get()), "root": str(root.GetPath())}
    if not info["kinematic"]:
        rb.GetKinematicEnabledAttr().Set(True)  # テストの間だけ床に固定する
        if root.HasAPI(UsdPhysics.ArticulationRootAPI):
            root.RemoveAPI(UsdPhysics.ArticulationRootAPI)
    return stage, info


def joint_prims(stage: Usd.Stage) -> list[Usd.Prim]:
    return [p for p in Usd.PrimRange(stage.GetPrimAtPath(ASSET), Usd.TraverseInstanceProxies())
            if p.IsA(UsdPhysics.RevoluteJoint) or p.IsA(UsdPhysics.PrismaticJoint)]


def joint_api(prim: Usd.Prim):
    return UsdPhysics.RevoluteJoint(prim) if prim.IsA(UsdPhysics.RevoluteJoint) else UsdPhysics.PrismaticJoint(prim)


FREE_TARGETS_DEG = (-90.0, 90.0)  # 限界なしの回転の関節を回す目標（±180° を超えると角度の読みが折り返す）


def _limit(v) -> float | None:
    return float(v) if v is not None and math.isfinite(v) and abs(v) < 1e6 else None


def pose(path: str):
    t = PX.get_rigidbody_transformation(path)
    if not t.get("ret_val"):
        return None
    p, q = t["position"], t["rotation"]  # rotation は (x, y, z, w)
    return Gf.Vec3d(*p), Gf.Quatd(q[3], q[0], q[1], q[2])


def run(usd: str, jpath: Sdf.Path, target: float) -> dict:
    """関節 jpath にだけ位置ドライブを付けて target へ動かす。ほかの関節はドライブなし（自由）のまま。"""
    stage, info = build(usd)
    prim = stage.GetPrimAtPath(jpath)
    j = joint_api(prim)
    revolute = prim.IsA(UsdPhysics.RevoluteJoint)
    body0, body1 = j.GetBody0Rel().GetTargets()[0], j.GetBody1Rel().GetTargets()[0]
    xf = UsdGeom.XformCache()
    m0 = xf.GetLocalToWorldTransform(stage.GetPrimAtPath(body0))
    rot0 = Gf.Rotation(Gf.Quatd(j.GetLocalRot0Attr().Get() or Gf.Quatf(1)))
    axis = m0.TransformDir(rot0.TransformDir(AXES[j.GetAxisAttr().Get()])).GetNormalized()  # 世界座標の関節の軸

    kind = "angular" if revolute else "linear"
    drive = UsdPhysics.DriveAPI.Apply(prim, kind)
    stiffness, damping = DRIVES[kind]
    drive.CreateStiffnessAttr(stiffness)
    drive.CreateDampingAttr(damping)
    drive.CreateMaxForceAttr(1e6)
    drive.CreateTargetPositionAttr(float(target))
    mass = UsdPhysics.MassAPI(stage.GetPrimAtPath(body1))
    com = mass.GetCenterOfMassAttr().Get() if mass else None
    com = Gf.Vec3d(*com) if com is not None and all(map(math.isfinite, com)) else Gf.Vec3d(0)

    sid = UsdUtils.StageCache.Get().Insert(stage).ToLongInt()
    SIM.attach_stage(sid)
    try:
        dt = 1.0 / args.hz
        series, first = [], None
        for i in range(int(round(args.seconds * args.hz)) + 1):
            if i:
                SIM.simulate(dt, (i - 1) * dt)
                SIM.fetch_results()
            ps = pose(str(body1))
            if ps is None:
                return {"error": "PhysX から可動部の姿勢を取れない"}
            p, q = ps
            if first is None:
                first = (p, q, p + Gf.Rotation(q).TransformDir(com))
            if revolute:  # 置いたときからの回転を、関節の軸のまわりの符号付きの角度にする
                dq = (q * first[1].GetInverse()).GetNormalized()
                pos = math.degrees(2 * math.atan2(Gf.Dot(Gf.Vec3d(dq.GetImaginary()), axis), dq.GetReal()))
            else:
                pos = Gf.Dot(p - first[0], axis)
            series.append([round(i * dt, 5), pos])
            if not math.isfinite(pos):
                break  # 爆発（NaN）
        c = p + Gf.Rotation(q).TransformDir(com)
        bp = pose(str(body0))
        return {"target": target, "series": series,
                "com_move": [c[k] - first[2][k] for k in range(3)],
                "body_moved_m": (bp[0] - m0.ExtractTranslation()).GetLength() if bp else None}
    finally:
        SIM.detach_stage()
        UsdUtils.StageCache.Get().Erase(Usd.StageCache.Id.FromLongInt(sid))


def test_asset(usd: str) -> dict:
    stage, info = build(usd)
    joints = []
    for prim in joint_prims(stage):
        j = joint_api(prim)
        revolute = prim.IsA(UsdPhysics.RevoluteJoint)
        lo, hi = _limit(j.GetLowerLimitAttr().Get()), _limit(j.GetUpperLimitAttr().Get())
        over = args.over_deg if revolute else args.over_m
        targets = sorted({*(t for t in (lo, hi) if t is not None),
                          *([lo - over] if lo is not None else []), *([hi + over] if hi is not None else [])})
        if revolute and lo is None and hi is None:  # 限界なしの回転（回転ラック）は両向きに回してみる
            targets = list(FREE_TARGETS_DEG)
        entry = {"joint": str(prim.GetPath()).replace(str(ASSET), "", 1), "type": "revolute" if revolute else "prismatic",
                 "axis": j.GetAxisAttr().Get(), "lower": lo, "upper": hi, "runs": []}
        for t in targets:
            try:
                entry["runs"].append(run(usd, prim.GetPath(), t))
            except Exception as e:  # noqa: BLE001  1 回の失敗で全体を止めない
                entry["runs"].append({"target": t, "error": f"{type(e).__name__}: {e}"})
        joints.append(entry)
    return {**info, "joints": joints}


def _finite(x):
    """JSON に NaN・inf を書かない（爆発したときは None）。"""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, list):
        return [_finite(v) for v in x]
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    return x


with open(args.out, "a") as f:
    for usd in args.usd:
        t0 = time.time()
        try:
            res = test_asset(usd)
        except Exception as e:  # noqa: BLE001  1 点の失敗で全体を止めない
            res = {"error": f"{type(e).__name__}: {e}"}
        res.update(usd=usd, seconds=args.seconds, hz=args.hz, wall_s=round(time.time() - t0, 2))
        f.write(json.dumps(_finite(res), ensure_ascii=False) + "\n")
        f.flush()
        print(f"[joint_sim] {usd} {res.get('error', 'ok')} ({res['wall_s']} s)", file=sys.stderr, flush=True)

app.close()
