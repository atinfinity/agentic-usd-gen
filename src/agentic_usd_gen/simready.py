"""SimReady Foundation のプロファイルで書き出したアセットを検証する（agentic-usd-gen-simready）。

NVIDIA の simready-validate を使う。入っていなければ `uv sync --extra simready` で入れる。
OmniPBR / OmniGlass / OmniSurface の MDL は Isaac Sim に組み込まれているので、Mac では参照先が見つからず NP.008 で落ちる。
これは既定で想定内として数え、合否に含めない（Isaac Sim の環境では --strict-mdl で確かめる）。
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .isaac_layout import PAYLOADS

DEFAULT_PROFILE = "Robotics-Prop"
MDL_REQUIREMENT = "NP.008"  # 参照先のファイルが存在すること
_initialized = False


@dataclass
class Issue:
    code: str  # 要件 ID（例: NP.005）
    message: str
    at: str


@dataclass
class Result:
    asset: str
    profile: str
    version: str
    passed: bool
    issues: list[Issue] = field(default_factory=list)  # 合否に関わる不適合
    expected_mdl: list[Issue] = field(default_factory=list)  # 想定内として数えた MDL の不適合
    optional_failed: list[str] = field(default_factory=list)  # 満たしていない任意の機能
    optional_issues: dict[str, list[Issue]] = field(default_factory=dict)  # 任意の機能 → 満たしていない理由

    def to_dict(self) -> dict:
        return asdict(self)


def available() -> bool:
    try:
        import simready.validate  # noqa: F401
    except ImportError:
        return False
    return True


def _init():
    global _initialized
    import simready.validate as sv

    if not _initialized:
        logging.getLogger().setLevel(max(logging.getLogger().level, logging.ERROR))  # 非推奨の警告が大量に出る
        sv.initialize(rules_and_requirements_paths=[], features_paths=[], profiles_paths=[])  # 入っている tier を読む
        _initialized = True
    return sv


def _code(issue) -> str:
    """要件 ID を `com.nvidia.simready.NP.008` → `NP.008` の形で返す。"""
    req = getattr(issue, "requirement", None)
    return _short(str(getattr(req, "code", None) or getattr(issue, "code", "") or "")) or "?"


def _short(code: str) -> str:
    for prefix in ("com.nvidia.simready.", "com.nvidia.usd."):
        code = code.removeprefix(prefix)
    return code


def _as_list(v) -> list[str]:
    """features_summary の要件の一覧（文字列にした Python のリストのこともある）。"""
    if isinstance(v, str):
        try:
            v = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            return []
    return [str(x) for x in v] if isinstance(v, (list, tuple)) else []


def _is_expected_mdl(issue: Issue) -> bool:
    return issue.code == MDL_REQUIREMENT and ".mdl'" in issue.message


def check(usd_path: Path, profile: str = DEFAULT_PROFILE, version: str | None = None,
          strict_mdl: bool = False) -> Result | None:
    """1 つのアセットを検証する。プロファイルが見つからない・USD を開けないときは None。"""
    sv = _init()
    r = sv.validate_asset(sv.AssetValidationConfig(str(usd_path), profile, version))
    if r is None:
        return None
    res = Result(asset=str(usd_path), profile=r.profile_id, version=r.profile_version, passed=False)
    for raw in r.issues:
        issue = Issue(_code(raw), str(raw.message), str(getattr(raw, "at", "")))
        (res.expected_mdl if not strict_mdl and _is_expected_mdl(issue) else res.issues).append(issue)
    res.optional_failed = sorted(f for f, s in r.features_summary.items()
                                 if not s.get("passed") and not sv.is_blocking_failure(s))
    soft = [Issue(_code(raw), str(raw.message), str(getattr(raw, "at", ""))) for raw in getattr(r, "soft_issues", [])]
    for f in res.optional_failed:
        codes = {_short(c) for c in _as_list(r.features_summary[f].get("optional requirements"))}
        res.optional_issues[f] = [i for i in soft if i.code in codes]
    res.passed = not res.issues
    return res


def find_assets(paths: list[Path]) -> list[Path]:
    """ファイルはそのまま、フォルダはその下の .usd を集める。.thumbs などドットで始まるフォルダと、
    入口から読み込むレイヤー（payloads/。isaac_layout.py）は除く。"""
    found: list[Path] = []
    for p in paths:
        if p.is_dir():
            found += sorted(f for f in p.rglob("*.usd")
                            if not any(part.startswith(".") or part == PAYLOADS for part in f.relative_to(p).parts))
        else:
            found.append(p)
    return found


def _print(res: Result, verbose: bool) -> None:
    mark = "OK" if res.passed else "NG"
    note = f"（MDL の想定内 {len(res.expected_mdl)} 件）" if res.expected_mdl else ""
    print(f"{mark} {res.asset}  {res.profile} {res.version}{note}")
    by_code: dict[str, list[Issue]] = {}
    for i in res.issues:
        by_code.setdefault(i.code, []).append(i)
    for code, items in sorted(by_code.items()):
        print(f"   {code} × {len(items)}: {items[0].message}")
        if verbose:
            for i in items:
                print(f"      {i.at}")
    if verbose and res.optional_failed:
        print(f"   任意の機能で未対応: {', '.join(res.optional_failed)}")
        for f in res.optional_failed:
            by_code = {}
            for i in res.optional_issues.get(f, []):
                by_code.setdefault(i.code, []).append(i)
            for code, items in sorted(by_code.items()):
                print(f"      {f} {code} × {len(items)}: {items[0].message}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-simready", description="SimReady Foundation のプロファイルでアセットを検証する")
    p.add_argument("paths", nargs="*", type=Path, help="USD ファイルかフォルダ（既定: assets/）")
    p.add_argument("--profile", default=DEFAULT_PROFILE, help=f"プロファイル（既定: {DEFAULT_PROFILE}）")
    p.add_argument("--version", help="プロファイルの版（既定: 入っている中で最新）")
    p.add_argument("--strict-mdl", action="store_true",
                   help="MDL（OmniPBR / OmniGlass / OmniSurface）の参照先がないのも不適合として数える（Isaac Sim の環境用）")
    p.add_argument("--output", type=Path, help="結果を JSON で書き出す先")
    p.add_argument("-v", "--verbose", action="store_true", help="不適合をすべて表示し、未対応の任意の機能も出す")
    args = p.parse_args(argv)

    if not available():
        sys.exit("simready-validate が入っていません。`uv sync --extra simready` で入れてください")
    assets = find_assets(args.paths or [Path("assets")])
    if not assets:
        sys.exit("検証する USD が見つかりません")

    results: list[Result] = []
    failed = 0
    for a in assets:
        res = check(a, args.profile, args.version, args.strict_mdl)
        if res is None:
            print(f"NG {a}  検証できません（プロファイル {args.profile} がない、または USD を開けない）")
            failed += 1
            continue
        results.append(res)
        failed += not res.passed
        _print(res, args.verbose)
    if args.output:
        args.output.write_text(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2) + "\n")
    print(f"\n合格: {len(assets) - failed} / {len(assets)} 点（{args.profile}）")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
