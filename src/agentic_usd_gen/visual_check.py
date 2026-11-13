"""プレビューと元画像を Claude の画像認識で比べ、見た目を自動で検証する。

    agentic-usd-gen-visual out/fictional                  # 出力先の全アセットを検証し、点の低い順に並べる
    agentic-usd-gen-visual out/fictional/cup_noodle_tall  # 1 つだけ
    agentic-usd-gen-visual out/fictional --baseline old/fictional  # 別の出力と比べて点の下がったものを出す

アセットの meta.json に visual_check（点数 0〜100・指摘・要約）を書く。前回の結果は visual_check_previous に残し、
点が下がったもの（回帰）を一覧に出す。プレビュー（debug/preview_*.png）は agentic-usd-gen --preview で描いておく。
あわせて、透明な部品の見え方（液体の色・容器の明るさ）を画素で確かめ、meta.json の preview_check に書く
（preview_check.py。API キーがなくても行う）。API キーがなければ画像認識の採点は省略する。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from . import llm, preview_check
from .llm import request_json
from .vision import _encode

log = logging.getLogger("agentic_usd_gen.visual")

KINDS = ("seam", "stretch", "flip", "color", "missing", "shape", "other")
SEVERITIES = ("low", "medium", "high")
THRESHOLD = 70  # これ未満を「点の低いもの」として出す
DROP = 10  # 前回・基準からこれ以上下がったら回帰
NO_KEY = "API キーがない"
MAX_SOURCES = 6  # 箱は 6 面

SYSTEM = """\
あなたは商品の 3D モデル（USD）の見た目を検品する担当です。
「元画像」は 3D モデルを作るときに使った商品の画像（側面の写真・展開したラベル・上面・箱の各面など）です。
「プレビュー」は作った 3D モデルを正面・斜め上・真上から描画したものです。
プレビューが元画像の商品をどれだけ忠実に再現しているかを 0〜100 の整数で採点し、問題を挙げてください。

採点の目安:
- 90〜100: 形・色・絵柄・文字の向きがほぼ元画像のとおり
- 70〜89: 小さな違い（継ぎ目がわずかに見える、色味が少し違うなど）がある
- 40〜69: 一目でわかる問題（絵柄の大きな伸び・ずれ、裏返り、部品の欠け、色の大きな違い）がある
- 0〜39: 別の商品に見える、形が崩れている、テクスチャがほぼ貼られていない

問題の種類（kind）:
- seam: テクスチャの継ぎ目・切れ目が目立つ
- stretch: 絵柄・文字が伸びる・縮む・歪む
- flip: 絵柄・文字が左右や上下に反転している、天地が逆
- color: 色・明るさが元画像と大きく違う
- missing: キャップ・ラベル・部品などが欠けている、テクスチャが貼られていない
- shape: 輪郭・比率・厚みなどの形が違う
- other: そのほか
照明や背景、描画の質感（反射・影）の違いは問題にしません。元画像にない面（底・裏など）は推測で減点しません。
"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["score", "issues", "summary"],
    "properties": {
        "score": {"type": "integer"},  # 構造化出力のスキーマは minimum・maximum を持てない。範囲は check_visual() で丸める
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "severity", "detail"],
                "properties": {
                    "kind": {"type": "string", "enum": list(KINDS)},
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "detail": {"type": "string"},
                },
            },
        },
        "summary": {"type": "string"},
    },
}


def check_visual(previews: list[Path], sources: list[Path], product_name: str, model: str) -> dict:
    """プレビューと元画像を比べ、{score, issues, summary} を返す。"""
    content: list[dict] = []
    for i, p in enumerate(sources):
        content += [{"type": "text", "text": f"元画像 {i}:"}, _encode(p)]
    for p in previews:
        content += [{"type": "text", "text": f"プレビュー（{p.stem.removeprefix('preview_')}）:"}, _encode(p)]
    content.append({"type": "text", "text": f"商品名: {product_name}"})
    data = request_json(model=model, system=SYSTEM, content=content, schema=SCHEMA, effort="medium")
    score = max(0, min(100, int(data["score"])))
    issues = [i for i in data.get("issues", []) if i.get("kind") in KINDS]
    return {"score": score, "issues": issues, "summary": data.get("summary", "")}


@dataclass
class Asset:
    dir: Path
    meta: dict
    previews: list[Path] = field(default_factory=list)
    sources: list[Path] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.dir.name


def find_assets(paths: list[Path]) -> list[Path]:
    """アセットのディレクトリ（meta.json のあるもの）か、それを並べた出力先から、アセットを集める。"""
    found: list[Path] = []
    for p in paths:
        if (p / "meta.json").exists():
            found.append(p)
        else:
            found += sorted(m.parent for m in p.glob("*/meta.json"))
    return found


def load_asset(d: Path) -> Asset:
    meta = json.loads((d / "meta.json").read_text())
    previews = sorted((d / "debug").glob("preview_*.png"))
    sources: list[Path] = []
    cache = meta.get("cache_dir")
    if cache:
        sources = sorted(Path(cache).glob("images/*.png"))[:MAX_SOURCES]
    if not sources and meta.get("image_used"):  # --image で渡した画像
        p = Path(meta["image_used"])
        sources = [p] if p.exists() else []
    return Asset(d, meta, previews, sources)


def run_one(asset: Asset, model: str) -> dict:
    """1 つのアセットを検証し、meta.json に書く。結果（visual_check）を返す。"""
    if not asset.previews:
        raise ValueError("プレビューがない（agentic-usd-gen --preview で描画する）")
    if not asset.sources:
        raise ValueError(f"元画像がない（{asset.meta.get('cache_dir')}/images）")
    res = check_visual(asset.previews, asset.sources, asset.meta.get("product_name", asset.slug), model)
    res |= {"model": model, "date": dt.datetime.now().isoformat(timespec="seconds"),
            "previews": [p.name for p in asset.previews], "sources": [str(p) for p in asset.sources]}
    meta = json.loads((asset.dir / "meta.json").read_text())  # 並列で動くので書く直前に読み直す
    if meta.get("visual_check"):
        meta["visual_check_previous"] = meta["visual_check"]
    meta["visual_check"] = res
    (asset.dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
    asset.meta = meta
    return res


def run_preview_check(asset: Asset) -> dict | None:
    """透明な部品の見え方を確かめ、meta.json の preview_check に書く。マスクがなければ None。"""
    res = preview_check.check(asset.dir / "debug", (asset.meta.get("colors") or {}).get("liquid"),
                              liquid_expected=bool((asset.meta.get("profile") or {}).get("liquid_top_z")))
    if res is not None:
        meta = json.loads((asset.dir / "meta.json").read_text())
        meta["preview_check"] = res
        (asset.dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
        asset.meta = meta
    return res


def previous_score(asset: Asset, baseline: Path | None) -> int | None:
    """比べる相手の点。--baseline があればそちらの同じアセット、なければ前回の結果。"""
    if baseline is not None:
        m = baseline / asset.slug / "meta.json"
        if not m.exists():
            return None
        return (json.loads(m.read_text()).get("visual_check") or {}).get("score")
    return (asset.meta.get("visual_check_previous") or {}).get("score")


def report(rows: list[dict], threshold: int, drop: int) -> str:
    """点の低い順の表と、点の低いもの・下がったものの一覧。"""
    lines: list[str] = []
    if any(r.get("error") != NO_KEY for r in rows):  # キーがなく採点していなければ表は出さない
        lines = [f"{'score':>5} {'prev':>5}  slug"]
        for r in sorted(rows, key=lambda r: (r["score"] is None, r["score"] or 0)):
            s = "-" if r["score"] is None else str(r["score"])
            prev = "" if r["previous"] is None else str(r["previous"])
            note = r.get("error") or r.get("summary", "")
            lines.append(f"{s:>5} {prev:>5}  {r['slug']}  {note}")
        scored = [r for r in rows if r["score"] is not None]
        low = [r["slug"] for r in sorted(scored, key=lambda r: r["score"]) if r["score"] < threshold]
        reg = [r for r in scored if r["previous"] is not None and r["previous"] - r["score"] >= drop]
        lines.append(f"\n{len(scored)}/{len(rows)} 件を検証。{threshold} 点未満: {len(low)} 件 / "
                     f"{drop} 点以上の低下: {len(reg)} 件")
        if low:
            lines.append("点の低いもの: " + ", ".join(low))
        if reg:
            lines.append("点の下がったもの: " + ", ".join(f"{r['slug']}（{r['previous']}→{r['score']}）" for r in reg))
    checked = [r for r in rows if r.get("transparency") is not None]
    warned = [r for r in checked if r["transparency"]]
    if checked:
        lines.append(f"透明な部品の見え方: {len(checked)} 件を検査、警告 {len(warned)} 件")
        lines += [f"  {r['slug']}: {w}" for r in warned for w in r["transparency"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-visual", description="プレビューと元画像を画像認識で比べ、見た目を検証する")
    p.add_argument("paths", nargs="+", type=Path, help="アセットのディレクトリ、またはそれを並べた出力先")
    p.add_argument("--baseline", type=Path, help="比べる出力先（同じ slug の visual_check と比べる）")
    p.add_argument("--model", default=llm.DEFAULT_MODEL, help=f"Claude のモデル（既定: {llm.DEFAULT_MODEL}）")
    p.add_argument("--threshold", type=int, default=THRESHOLD, help=f"点の低いものとする境目（既定: {THRESHOLD}）")
    p.add_argument("--drop", type=int, default=DROP, help=f"回帰とする点の下がり幅（既定: {DROP}）")
    p.add_argument("--jobs", type=int, default=4, help="同時に問い合わせる数（既定: 4）")
    p.add_argument("--report", type=Path, help="結果を JSON で書き出す")
    args = p.parse_args(argv)
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for noisy in ("httpx", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    scoring = llm.has_credentials()
    if not scoring:
        log.warning("ANTHROPIC_API_KEY がないため画像認識の採点を省略します（透明な部品の検査だけ行う）")
    dirs = find_assets(args.paths)
    if not dirs:
        p.error("meta.json のあるアセットが見つかりません")

    def one(d: Path) -> dict:
        asset = load_asset(d)
        row = {"slug": asset.slug, "dir": str(d), "score": None, "previous": None}
        pc = run_preview_check(asset)
        row["transparency"] = pc["warnings"] if pc else None
        if not scoring:
            row["error"] = NO_KEY
            return row
        try:
            res = run_one(asset, args.model)
            row |= {"score": res["score"], "summary": res["summary"], "issues": res["issues"]}
            log.info("%s: %d 点", asset.slug, res["score"])
        except (ValueError, llm.LLMError) as e:
            row["error"] = str(e)
            log.warning("%s: %s", asset.slug, e)
        row["previous"] = previous_score(asset, args.baseline)
        return row

    with ThreadPoolExecutor(max(1, args.jobs)) as ex:
        rows = list(ex.map(one, dirs))
    print(report(rows, args.threshold, args.drop))
    if args.report:
        args.report.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
