"""書き出したアセットの中で、中身が同じテクスチャを 1 つのファイルにまとめる。

同じ商品を什器にいくつも並べると、部品の名前ごとに中身が同じ画像が書き出される
（有孔ボードの台紙 20 枚、袋の山など）。同じ中身のファイルは 1 つだけ残し、USD の参照をそれに向ける。
asset.json から名前で参照される画像（画面・掲示物の絵と Blank）は残し、ほかのファイルをそれに寄せることもしない
（ワールドを組むツールが画面の材質をファイル名で見つけて差し替えることがあるので、別の材質が同じファイルを指すと一緒に変わってしまう）。
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path, PurePosixPath

from pxr import Sdf, UsdUtils

log = logging.getLogger(__name__)


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def duplicate_map(tex_dir: Path, keep: set[str] = frozenset()) -> dict[str, str]:
    """{消すファイル名: 残すファイル名}。同じ中身のうち名前順で最初のものを残す。keep の名前は対象外。"""
    groups: dict[str, list[str]] = {}
    for p in sorted(tex_dir.iterdir()):
        if p.is_file() and p.name not in keep:
            groups.setdefault(_digest(p), []).append(p.name)
    return {dup: names[0] for names in groups.values() for dup in names[1:]}


def _retarget(path: str, mapping: dict[str, str], tex_dir_name: str) -> str:
    """アセットパス（./textures/<名前>）が消すファイルを指していれば、名前だけ残すファイルに替える（./ 等の前置きは保つ）。"""
    head, sep, name = path.rpartition("/")
    if sep and PurePosixPath(head).name == tex_dir_name and name in mapping:
        return f"{head}/{mapping[name]}"
    return path


def rewrite_layer(layer: Sdf.Layer, mapping: dict[str, str], tex_dir_name: str = "textures") -> int:
    """layer のアセットパス（バリアントの中も）を mapping に従って書き換え、書き換えた数を返す。"""
    count = 0

    def modify(path: str) -> str:
        nonlocal count
        new = _retarget(path, mapping, tex_dir_name)
        count += new != path
        return new

    UsdUtils.ModifyAssetPaths(layer, modify)
    return count


def dedupe_textures(usd_path: Path, tex_dir: Path, keep: set[str] = frozenset()) -> dict[str, str]:
    """usd_path（1 つのレイヤー）の参照する tex_dir の重複を消し、{消した名前: 残した名前} を返す。"""
    if not tex_dir.is_dir():
        return {}
    mapping = duplicate_map(tex_dir, keep)
    if not mapping:
        return {}
    layer = Sdf.Layer.FindOrOpen(str(usd_path))
    n = rewrite_layer(layer, mapping, tex_dir.name)
    layer.Save()
    before = sum(p.stat().st_size for p in tex_dir.iterdir() if p.is_file())
    for name in mapping:
        (tex_dir / name).unlink()
    after = sum(p.stat().st_size for p in tex_dir.iterdir() if p.is_file())
    log.info("%s: 同じ中身のテクスチャ %d 枚をまとめました（書き換えたパス %d 種、%.0f → %.0f MB）",
             usd_path.stem, len(mapping), n, before / 1e6, after / 1e6)
    return mapping


def referenced_names(obj) -> set[str]:
    """asset.json の値（入れ子）に現れる ./textures/<名前> のファイル名。"""
    out: set[str] = set()
    if isinstance(obj, dict):
        for v in obj.values():
            out |= referenced_names(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= referenced_names(v)
    elif isinstance(obj, str) and "textures/" in obj:
        out.add(PurePosixPath(obj).name)
    return out


def dedupe_exported(asset_dir: Path) -> dict[str, str]:
    """書き出し済みのアセット（<slug>/simready_usd、payloads/ に分けたレイヤー）の重複をまとめる。"""
    import json

    tex_dir = asset_dir / "textures"
    if not tex_dir.is_dir():
        return {}
    aj = asset_dir / "asset.json"
    keep = referenced_names(json.loads(aj.read_text())) if aj.exists() else set()
    mapping = duplicate_map(tex_dir, keep)
    if not mapping:
        return {}
    for path in sorted(asset_dir.glob("*.usd*")) + sorted(asset_dir.glob("payloads/*.usd*")):
        layer = Sdf.Layer.FindOrOpen(str(path))
        if rewrite_layer(layer, mapping, tex_dir.name):
            layer.Save()
    for name in mapping:
        (tex_dir / name).unlink()
    return mapping


def main(argv: list[str] | None = None) -> None:
    """agentic-usd-gen-dedupe-textures <assets>：書き出し済みのアセットすべての、同じ中身のテクスチャをまとめる。"""
    import argparse

    p = argparse.ArgumentParser(description=main.__doc__)
    p.add_argument("assets", type=Path, nargs="?", default=Path("assets"), help="書き出し先（既定: assets/）")
    args = p.parse_args(argv)
    total = 0
    for tex_dir in sorted(args.assets.glob("*/*/simready_usd/textures")):
        sizes = {f.name: f.stat().st_size for f in tex_dir.iterdir() if f.is_file()}
        mapping = dedupe_exported(tex_dir.parent)
        if mapping:
            saved = sum(sizes[n] for n in mapping)
            total += saved
            print(f"{tex_dir.parent.parent.name}: {len(mapping)} 枚をまとめました（{saved / 1e6:.0f} MB 減）")
    print(f"合計 {total / 1e6:.0f} MB 減")
