"""Isaac Sim の Python で動かす落下テスト（agentic-usd-gen-droptest から呼ぶ。usd-core の環境では動かない）。

アセットごとに、床（静的な平面）と物理シーンだけのステージをメモリ上に作り、2 回動かす。描画はせず、PhysX を固定の刻みで直接進める（速い）。
  落下: 書き出したままの向きで、底を --height だけ浮かせて落とす（跳ね・突き抜け・静止・ずれを見る）
  傾け置き: --tilt 度だけ傾けて床すれすれに置く（真っすぐだと、立たない形も釣り合ったまま立ってしまう。
            傾けたまま高くから落とすと、角から着地した勢いで普通の商品も倒れる・滑るので、落下とは分ける）
ルートの剛体（本体）の毎ステップの位置・姿勢から、重心の高さ・傾き・速さの推移をまとめ、1 アセット 1 行の JSON で書き出す。
判定（倒れた・跳ねすぎ・突き抜け・静止までの時間）は agentic-usd-gen-droptest 側で行う（drop_test.py）。

    $ISAACSIM_PYTHON drop_sim.py --out raw.jsonl [--height 0.2] [--tilt 2] [--seconds 5] a.usd b.usd ...

什器（キネマティックな剛体）も、重心と質量を確かめるため、テストの間だけ動く剛体にして落とす（ファイルは変えない）。
天井付けの什器（--ceiling に渡したもの）は、上下を返して取り付け面を下にして落とす（ドームカメラは書き出したままだと半球が下で転がる）。
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
ap.add_argument("--height", type=float, default=0.2, help="[m] 落とす高さ（床から底面まで）")
ap.add_argument("--seconds", type=float, default=5.0, help="[s] 落としてから見る時間")
ap.add_argument("--tilt", type=float, default=2.0, help="[度] 傾け置きの傾き（0 なら傾け置きをしない）")
ap.add_argument("--hz", type=float, default=60.0, help="物理の刻み [Hz]（既定は Isaac Sim と同じ 60）")
ap.add_argument("--ceiling", action="append", default=[], help="天井付けのアセット（上下を返して落とす。何度でも指定できる）")
args = ap.parse_args()

from isaacsim import SimulationApp  # noqa: E402

app = SimulationApp({"headless": True})

import omni.physx  # noqa: E402
from pxr import Gf, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics, UsdUtils  # noqa: E402

SIM = omni.physx.get_physx_simulation_interface()
PX = omni.physx.get_physx_interface()
ASSET = Sdf.Path("/World/Drop/Asset")


def build(usd: str, height: float, tilt_deg: float, flip: bool = False) -> tuple[Usd.Stage, dict]:
    """床・物理シーン・落とすアセットのステージ。アセットはファイルを参照し、変更はこのステージ（メモリ）にだけ書く。
    flip なら X 軸のまわりに 180° 回し、上面（天井付けの取り付け面）を下にして置く。"""
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.81)
    px = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    px.CreateEnableGPUDynamicsAttr(False)  # 1 体だけなので CPU で十分。GPU の CUDA エラーで止まることもない
    px.CreateBroadphaseTypeAttr("MBP")
    px.CreateTimeStepsPerSecondAttr(args.hz)

    # 床: 静的な平面（コリジョンだけ）。摩擦・反発はアセット側の物理マテリアルと平均される（PhysX の既定）
    plane = UsdGeom.Plane.Define(stage, "/World/Floor")
    plane.CreateAxisAttr("Z")
    plane.CreateWidthAttr(20.0)
    plane.CreateLengthAttr(20.0)
    UsdPhysics.CollisionAPI.Apply(plane.GetPrim())

    # 参照するアセットのルートの変換は残したいので、外側の Xform を持ち上げる
    drop = UsdGeom.Xform.Define(stage, ASSET.GetParentPath())
    asset = stage.DefinePrim(ASSET)
    asset.GetReferences().AddReference(usd)
    stage.Load()

    info: dict = {}
    bodies = [p for p in Usd.PrimRange(asset, Usd.TraverseInstanceProxies()) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    if not bodies:
        raise RuntimeError("剛体がない（RigidBodyAPI の付いたプリムがない）")
    root = bodies[0]  # ルート（本体）。可動部はその下に入れ子
    rb = UsdPhysics.RigidBodyAPI(root)
    info["kinematic"] = bool(rb.GetKinematicEnabledAttr().Get())
    if info["kinematic"]:
        rb.GetKinematicEnabledAttr().Set(False)  # テストの間だけ動く剛体にする
    mass = UsdPhysics.MassAPI(root)
    info["mass_kg"] = mass.GetMassAttr().Get() if mass else None
    com = mass.GetCenterOfMassAttr().Get() if mass else None
    info["com_local"] = list(com) if com is not None else [0.0, 0.0, 0.0]
    info["bodies"] = len(bodies)
    info["colliders"] = sum(1 for p in Usd.PrimRange(asset, Usd.TraverseInstanceProxies())
                            if p.HasAPI(UsdPhysics.CollisionAPI))

    # 置いたままの向き（flip なら上下を返した向き）での接地面と重心（静的に倒れ始める角度の元。drop_test.py）
    flip_rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), 180.0 if flip else 0.0)
    xf = UsdGeom.XformCache()
    c = flip_rot.TransformDir(xf.GetLocalToWorldTransform(root).Transform(Gf.Vec3d(*info["com_local"])))
    raw_pts = collider_points(stage)  # 書き出したままの向き（drop の変換はまだない）
    pts = [flip_rot.TransformDir(v) for v in raw_pts]
    if not pts:
        raise RuntimeError("コリジョンのメッシュがない")
    info["com_rest_z"] = c[2] - min(v[2] for v in pts)
    info["support_margin_m"] = support_margin(pts, c)

    # x と y の間の水平な軸のまわりに tilt_deg 度傾け、いちばん低い頂点を床から height の高さに
    tilt = flip_rot * Gf.Rotation(Gf.Vec3d(1, 1, 0).GetNormalized(), tilt_deg)  # 上下を返してから傾ける
    low = min(tilt.TransformDir(v)[2] for v in raw_pts)
    drop.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(0, 0, height - low))
    drop.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(tilt.GetQuat())  # 回してから持ち上げる
    info["root"] = str(root.GetPath())
    info["mount"] = "ceiling" if flip else "floor"
    return stage, info


def collider_points(stage: Usd.Stage) -> list[Gf.Vec3d]:
    """コリジョンのメッシュの頂点（世界座標）。PhysX は落とした後の剛体の姿勢を USD に書き戻すので、後でも使える。"""
    xf = UsdGeom.XformCache()
    pts: list[Gf.Vec3d] = []
    for p in Usd.PrimRange(stage.GetPrimAtPath(ASSET), Usd.TraverseInstanceProxies()):
        if p.HasAPI(UsdPhysics.CollisionAPI) and p.IsA(UsdGeom.Mesh):
            m = xf.GetLocalToWorldTransform(p)
            pts += [m.Transform(Gf.Vec3d(v)) for v in (UsdGeom.Mesh(p).GetPointsAttr().Get() or [])]
    return pts


def _hull(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """2 次元の凸包（反時計回り）。"""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def support_margin(pts: list[Gf.Vec3d], com: Gf.Vec3d) -> float:
    """重心の真下から接地面（底から 2 mm 以内の頂点の凸包）の縁までの最短距離 [m]。外にはみ出していれば負。
    重心の高さとの比で、静かに傾けたとき倒れ始める角度が分かる（薄いカードなどは 0 に近い）。"""
    low = min(v[2] for v in pts)
    hull = _hull([(v[0], v[1]) for v in pts if v[2] < low + 0.002])
    if len(hull) < 3:
        return 0.0  # 点か線でしか接していない
    best, inside = math.inf, True
    for (ax, ay), (bx, by) in zip(hull, hull[1:] + hull[:1]):
        ex, ey = bx - ax, by - ay
        signed = (ex * (com[1] - ay) - ey * (com[0] - ax)) / (math.hypot(ex, ey) or 1e-12)  # 反時計回りなので内側が正
        inside &= signed >= 0
        best = min(best, abs(signed))
    return best if inside else -best


def pose(path: str):
    t = PX.get_rigidbody_transformation(path)
    if not t.get("ret_val"):
        return None
    p, q = t["position"], t["rotation"]  # rotation は (x, y, z, w)
    return Gf.Vec3d(*p), Gf.Quatd(q[3], q[0], q[1], q[2])


def run(usd: str, height: float, tilt_deg: float = 0.0, flip: bool = False) -> dict:
    stage, info = build(usd, height, tilt_deg, flip)
    stage_id = UsdUtils.StageCache.Get().Insert(stage).ToLongInt()
    SIM.attach_stage(stage_id)
    try:
        dt = 1.0 / args.hz
        com_local = Gf.Vec3d(*info["com_local"])
        up = Gf.Vec3d(0, 0, -1 if flip else 1)  # 剛体の座標で、置いたときに上を向いている軸（傾きはここから測る）
        series = []  # [t, 重心の x, y, z, 傾き(度), 並進の速さ, 回転の速さ(rad/s)]
        prev = None
        n = int(round(args.seconds * args.hz))
        for i in range(n + 1):
            if i:
                SIM.simulate(dt, (i - 1) * dt)
                SIM.fetch_results()
            ps = pose(info["root"])
            if ps is None:
                return {**info, "error": "PhysX から剛体の姿勢を取れない"}
            p, q = ps
            rot = Gf.Rotation(q)
            c = p + rot.TransformDir(com_local)
            tilt = math.degrees(math.acos(max(-1.0, min(1.0, rot.TransformDir(up)[2]))))
            if prev is None:
                v = w = 0.0
            else:
                v = (c - prev[0]).GetLength() / dt
                dq = (q * prev[1].GetInverse()).GetNormalized()
                w = 2 * math.acos(max(-1.0, min(1.0, abs(dq.GetReal())))) / dt
            prev = (c, q)
            series.append([round(i * dt, 5), c[0], c[1], c[2], tilt, v, w])
            if not all(math.isfinite(x) for x in (c[0], c[1], c[2])):
                break  # 爆発（NaN）
        info["settled_min_z"] = min(v[2] for v in collider_points(stage))  # 頂点で測る（傾いた箱は軸に揃えると膨らむ）
        info["series"] = series
        return info
    finally:
        SIM.detach_stage()
        UsdUtils.StageCache.Get().Erase(Usd.StageCache.Id.FromLongInt(stage_id))


def _finite(x):
    """JSON に NaN・inf を書かない（爆発したときは None）。"""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, list):
        return [_finite(v) for v in x]
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    return x


ceiling = set(args.ceiling)
with open(args.out, "a") as f:
    for usd in args.usd:
        t0 = time.time()
        flip = usd in ceiling
        try:
            res = run(usd, args.height, flip=flip)
            if args.tilt > 0:  # 傾け置き（床から 1 mm）。傾きの推移だけ使う
                res["placed_series"] = run(usd, 0.001, args.tilt, flip)["series"]
                res["placed_tilt"] = args.tilt
        except Exception as e:  # noqa: BLE001  1 点の失敗で全体を止めない
            res = {"error": f"{type(e).__name__}: {e}"}
        res.update(usd=usd, height=args.height, seconds=args.seconds, hz=args.hz, wall_s=round(time.time() - t0, 2))
        f.write(json.dumps(_finite(res), ensure_ascii=False) + "\n")
        f.flush()
        print(f"[drop_sim] {usd} {res.get('error', 'ok')} ({res['wall_s']} s)", file=sys.stderr, flush=True)

app.close()
