"""生成した USD の検証（Isaac Sim を使わずに Mac 上で確認できる範囲）。"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from pxr import Ar, Usd, UsdGeom, UsdPhysics, UsdShade, UsdValidation

from .spec import COLLISION_APPROXIMATIONS, Dimensions

DIM_TOL = 0.05  # 寸法の許容誤差（相対）
ORIGIN_TOL = 0.001  # 原点ずれの許容量 [m]


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _bbox(stage: Usd.Stage, prim: Usd.Prim) -> tuple[tuple[float, ...], tuple[float, ...]]:
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    r = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    return tuple(r.GetMin()), tuple(r.GetMax())


def validate(usd_path: Path, dims: Dimensions | None = None, physics: bool = True,
             expected_size: tuple[float, float, float] | None = None, static: bool = False) -> Report:
    """expected_size（幅・厚さ・高さ）を渡すと寸法表記の代わりにそれと比べる。
    袋は膨らむと高さが縮むので、平らな寸法ではなく膨らんだ形の計算値で確かめる。
    static ならキネマティックな剛体（床に固定）であることを確かめる。"""
    rep = Report()
    stage = Usd.Stage.Open(str(usd_path))
    if stage is None:
        rep.errors.append(f"USD を開けません: {usd_path}")
        return rep

    root = stage.GetDefaultPrim()
    if not root:
        rep.errors.append("defaultPrim が未設定")
        return rep
    if UsdGeom.GetStageMetersPerUnit(stage) != 1.0:
        rep.errors.append(f"metersPerUnit が 1 ではない: {UsdGeom.GetStageMetersPerUnit(stage)}")
    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z:
        rep.errors.append(f"upAxis が Z ではない: {UsdGeom.GetStageUpAxis(stage)}")

    lo, hi = _bbox(stage, root)
    size = [hi[i] - lo[i] for i in range(3)]
    rep.info["bbox_min"], rep.info["bbox_max"] = list(lo), list(hi)
    if abs(lo[2]) > ORIGIN_TOL:
        rep.errors.append(f"底面が z=0 にない: z_min={lo[2]:.4f}")
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    if abs(cx) > ORIGIN_TOL or abs(cy) > ORIGIN_TOL:
        rep.errors.append(f"XY の中心が原点にない: ({cx:.4f}, {cy:.4f})")
    if expected_size:
        for name, got, want in zip(("幅", "厚さ", "高さ"), sorted(size[:2], reverse=True) + [size[2]],
                                   sorted(expected_size[:2], reverse=True) + [expected_size[2]]):
            if abs(got - want) > DIM_TOL * want:
                rep.errors.append(f"{name}が計算値と合わない: {got:.4f} m（期待 {want:.4f} m）")
    elif dims:
        if abs(size[2] - dims.height) > DIM_TOL * dims.height:
            rep.errors.append(f"高さが寸法と合わない: {size[2]:.4f} m（期待 {dims.height:.4f} m）")
        width = max(size[0], size[1])
        if abs(width - dims.diameter) > DIM_TOL * dims.diameter:
            rep.errors.append(f"直径・幅が寸法と合わない: {width:.4f} m（期待 {dims.diameter:.4f} m）")
        if dims.depth:
            thick = min(size[0], size[1])
            if abs(thick - dims.depth) > DIM_TOL * dims.depth:
                rep.errors.append(f"厚さが寸法と合わない: {thick:.4f} m（期待 {dims.depth:.4f} m）")

    if physics:
        mass = UsdPhysics.MassAPI(root).GetMassAttr().Get() if root.HasAPI(UsdPhysics.MassAPI) else None
        rep.info["mass"] = mass
        rep.info["static"] = static
        if not root.HasAPI(UsdPhysics.RigidBodyAPI):
            rep.errors.append("RigidBodyAPI がない")
        kinematic = bool(UsdPhysics.RigidBodyAPI(root).GetKinematicEnabledAttr().Get())
        if static:
            if not kinematic:
                rep.errors.append("static なのにキネマティックな剛体になっていない")
        elif kinematic:
            rep.errors.append("static ではないのにキネマティックな剛体になっている")
        if not mass or mass <= 0:
            rep.errors.append("質量が未設定")  # キネマティックでも要る（SimReady の RB.007）
        colliders = [str(p.GetPath()) for p in Usd.PrimRange(root) if p.HasAPI(UsdPhysics.CollisionAPI)]
        rep.info["colliders"] = colliders
        approx = {}
        for path in colliders:
            prim = stage.GetPrimAtPath(path)
            a = UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() if prim.HasAPI(
                UsdPhysics.MeshCollisionAPI) else None
            approx[prim.GetName()] = str(a or "none")
            if approx[prim.GetName()] not in COLLISION_APPROXIMATIONS:
                rep.errors.append(f"{path}: コリジョンの近似方法が不正: {approx[prim.GetName()]}")
            elif approx[prim.GetName()] == "meshSimplification" and not kinematic:
                # PhysX は動く剛体の三角形メッシュのコリジョンを扱えず、凸包に置き換える
                rep.warnings.append(f"{path}: 動く剛体に meshSimplification（PhysX では凸包として扱われる）")
        rep.info["collision_approximations"] = approx
        if not colliders:
            rep.errors.append("コリジョンが 1 つもない")
        # 可動部（扉など）の剛体は質量を持ち、関節で本体につながる（joints.py。SimReady の RB.011・RB.012）
        jointed = {t for p in Usd.PrimRange(root) if p.IsA(UsdPhysics.Joint)
                   for t in UsdPhysics.Joint(p).GetBody1Rel().GetTargets()}
        links = [p for p in Usd.PrimRange(root) if p != root and p.HasAPI(UsdPhysics.RigidBodyAPI)]
        for link in links:
            m = UsdPhysics.MassAPI(link).GetMassAttr().Get() if link.HasAPI(UsdPhysics.MassAPI) else None
            if not m or m <= 0:
                rep.errors.append(f"{link.GetPath()}: 可動部の質量が未設定")
            if link.GetPath() not in jointed:
                rep.errors.append(f"{link.GetPath()}: 可動部が関節で本体につながっていない")
        if links:
            rep.info["links"] = [p.GetName() for p in links]

    resolver = Ar.GetResolver()
    for prim in Usd.PrimRange(root):
        if prim.IsA(UsdShade.Material) and not prim.GetAttribute("semantics:labels:material").Get():
            rep.errors.append(f"{prim.GetPath()}: 素材の意味ラベル（semantics:labels:material）がない")
        if prim.IsA(UsdShade.Material) and not prim.HasAPI(UsdPhysics.MaterialAPI):
            mat = UsdShade.Material(prim)
            if not mat.GetSurfaceOutput().HasConnectedSource():
                rep.errors.append(f"{prim.GetPath()}: surface 出力が未接続")
            if not mat.GetSurfaceOutput("mdl").HasConnectedSource():
                rep.warnings.append(f"{prim.GetPath()}: MDL 出力がない（Isaac Sim では PreviewSurface で描画）")
        if prim.IsA(UsdShade.Shader):
            for inp in UsdShade.Shader(prim).GetInputs():
                v = inp.Get()
                if hasattr(v, "path") and v.path and not v.path.endswith(".mdl"):
                    resolved = v.resolvedPath or resolver.Resolve(
                        resolver.CreateIdentifier(v.path, Ar.ResolvedPath(str(usd_path.resolve())))
                    )
                    if not resolved:
                        rep.errors.append(f"{prim.GetPath()}.{inp.GetBaseName()}: テクスチャが見つからない {v.path}")

    # OpenUSD 標準の検証。MDL（Isaac Sim 組み込みの OmniPBR/OmniGlass/OmniSurface）は Mac では解決できないので想定内として扱う。
    # MaterialX のノード（OpenPBR）も usd-core には usdMtlx がなく Sdr で引けないので、MaterialX の標準ライブラリに
    # あるものは想定内とする
    ctx = UsdValidation.ValidationContext(UsdValidation.ValidationRegistry().GetOrLoadAllValidators())
    expected = 0
    for e in ctx.Validate(stage):
        msg = f"{e.GetName()}: {e.GetMessage()}"
        if _is_expected_mdl(e.GetMessage()) or _is_known_mtlx(e.GetMessage()):
            expected += 1
        elif e.GetType() == UsdValidation.ValidationErrorType.Error:
            rep.errors.append(msg)
        else:
            rep.warnings.append(msg)
    rep.info["expected_mdl_issues"] = expected
    return rep


def _is_expected_mdl(message: str) -> bool:
    return ".mdl'" in message or "sourceType 'mdl'" in message


_MTLX_MISSING = re.compile(r"shaderId '(ND_\w+)' specified on shader prim .* not found in sdrRegistry")


@cache
def _mtlx_nodedefs() -> frozenset[str]:
    """MaterialX の標準ライブラリにある nodedef の名前。MaterialX がなければ空。"""
    try:
        import MaterialX as mx
    except ImportError:
        return frozenset()
    doc = mx.createDocument()
    mx.loadLibraries(mx.getDefaultDataLibraryFolders(), mx.getDefaultDataSearchPath(), doc)
    return frozenset(nd.getName() for nd in doc.getNodeDefs())


def _is_known_mtlx(message: str) -> bool:
    m = _MTLX_MISSING.search(message)
    return bool(m) and m.group(1) in _mtlx_nodedefs()


def check_usdz(usdz_path: Path) -> Report:
    """Quick Look / RealityKit 互換性を Xcode 付属の usdchecker --arkit で確認する。"""
    rep = Report()
    exe = shutil.which("usdchecker") or ("/usr/bin/usdchecker" if Path("/usr/bin/usdchecker").exists() else None)
    if not exe:
        rep.warnings.append("usdchecker が見つからないため usdz の検証を省略")
        return rep
    p = subprocess.run([exe, "--arkit", str(usdz_path)], capture_output=True, text=True)
    lines = [ln for ln in (p.stdout + p.stderr).splitlines() if ln.startswith(("Error", "Warning:"))
             and "Coding Error" not in ln]
    if p.returncode != 0:
        rep.errors += lines or ["usdchecker --arkit が失敗"]
    else:
        rep.warnings += [ln for ln in lines if ln.startswith("Warning:") and "secondary thread" not in ln]
    return rep
