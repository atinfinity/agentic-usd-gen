"""コマンドライン: 商品名 → 検索 → 画像 → 3D モデル → Isaac Sim 向け USD。

例:
    uv run agentic-usd-gen "緑茶 600ml PET" --usdz --preview
    uv run agentic-usd-gen "テスト" --dims H=0.205,D=0.065 --image side.png   # API キーなしでも動く
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

from dotenv import load_dotenv

from . import llm, preview_check
from .blender_runner import find_blender, run_script
from .images import download_images
from .shapes import get_builder
from .shapes.revolve import BuildContext
from .spec import ORIENTATIONS, Dimensions, ProductSpec, cache_key, make_slug, parse_dims_override
from .usd_post import export_usda, export_usdz, postprocess
from .validate import check_usdz, validate
from .vision import Landmarks

log = logging.getLogger("agentic_usd_gen")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="agentic-usd-gen", description="商品名から Isaac Sim 用の USD アセットを生成する")
    p.add_argument("product", help="商品名（例: '緑茶 600ml PET'）")
    p.add_argument("--out", type=Path, default=Path("out"), help="出力先（既定: out/）")
    p.add_argument("--cache", type=Path, default=Path("cache"), help="検索キャッシュ（既定: cache/）")
    p.add_argument("--dims", help="寸法の上書き [m]: H=0.205,D=0.065[,CAP_H=..,CAP_D=..,T=..]（袋は D=幅, T=厚さ）")
    p.add_argument("--orientation", choices=ORIENTATIONS,
                   help="置き方（袋のみ）。lying は正面を上にして寝かせる（画像はシールが左右の横長のまま）")
    p.add_argument("--image", type=Path, action="append", help="側面画像を直接指定（複数可）。ダウンロードを省略")
    p.add_argument("--slug", help="出力名・ルート Prim 名")
    p.add_argument("--refresh", action="store_true", help="キャッシュを無視して検索し直す")
    p.add_argument("--model", default=llm.DEFAULT_MODEL, help=f"Claude のモデル（既定: {llm.DEFAULT_MODEL}）")
    p.add_argument("--usda", action="store_true", help="テキスト形式の .usda も書き出す")
    p.add_argument("--usdz", action="store_true", help="Quick Look 用の .usdz も書き出す")
    p.add_argument("--preview", action="store_true", help="Blender でプレビュー画像を描画する（debug/）")
    p.add_argument("--visual-check", action="store_true",
                   help="プレビューと元画像を画像認識で比べ、見た目の点数を meta.json に書く（--preview が要る）")
    p.add_argument("--no-physics", action="store_true", help="物理（剛体・質量・コリジョン）を付けない")
    p.add_argument("--blender", help="Blender 実行ファイルのパス")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def resolve_spec(args: argparse.Namespace, cache_dir: Path) -> ProductSpec:
    spec_path = cache_dir / "spec.json"
    dims_override = parse_dims_override(args.dims) if args.dims else {}
    if spec_path.exists() and not args.refresh:
        log.info("検索キャッシュを使用: %s", spec_path)
        spec = ProductSpec.load(spec_path)
    elif llm.has_credentials():
        from .search import search_product

        log.info("Claude (%s) で商品情報を検索中…", args.model)
        spec = search_product(args.product, args.model)
        spec.save(spec_path)
    else:
        if not {"height", "diameter"} <= dims_override.keys():
            sys.exit("ANTHROPIC_API_KEY がありません。.env に設定するか、--dims H=..,D=.. と --image で手動指定してください")
        log.warning("API キーがないため検索を省略し、指定された寸法だけで生成します")
        spec = ProductSpec(product_name=args.product, slug=make_slug(args.product), shape_class="revolve",
                           dimensions=Dimensions(**dims_override))

    if dims_override:
        spec = replace(spec, dimensions=replace(spec.dimensions, **dims_override))
    if args.slug:
        spec = replace(spec, slug=make_slug(args.slug))
    if args.orientation:
        spec = replace(spec, orientation=args.orientation)
    if spec.orientation not in ORIENTATIONS:
        sys.exit(f"未知の orientation: {spec.orientation}（使えるのは {', '.join(ORIENTATIONS)}）")
    if spec.orientation == "lying" and spec.shape_class != "pouch":
        sys.exit("orientation=lying は袋（pouch）だけで使えます")
    return spec


def resolve_images(args: argparse.Namespace, spec: ProductSpec, cache_dir: Path) -> list[Path]:
    if args.image:
        missing = [p for p in args.image if not p.exists()]
        if missing:
            sys.exit(f"画像が見つかりません: {', '.join(map(str, missing))}")
        return list(args.image)
    img_dir = cache_dir / "images"
    cached = sorted(img_dir.glob("[0-9][0-9].png"))
    if cached and not args.refresh:
        return cached
    if not spec.image_candidates:
        return []
    if img_dir.exists():
        shutil.rmtree(img_dir)
    log.info("画像をダウンロード中（候補 %d 件）…", len(spec.image_candidates))
    return download_images(spec, img_dir)


def resolve_landmarks(args: argparse.Namespace, spec: ProductSpec, images: list[Path],
                      cache_dir: Path) -> tuple[int | None, Landmarks, dict[str, int] | None]:
    """best の画像番号・部位の位置・箱の面ごとの画像番号（vision.json の faces、任意）。"""
    if not images:
        return None, Landmarks(), None
    vision_path = cache_dir / "vision.json"
    names = [str(p.resolve()) for p in images]
    if vision_path.exists() and not args.refresh:
        cached = json.loads(vision_path.read_text())
        # キャッシュの画像はファイル名で照合する（キャッシュをリポジトリへ移しても使えるように）
        cached_names = cached.get("images") or []
        same = (cached_names == names if args.image else
                [Path(p).name for p in cached_names] == [p.name for p in images])
        if same:
            return cached["best_index"], Landmarks(**cached["landmarks"]), cached.get("faces")
    if not llm.has_credentials():
        return None, Landmarks(), None
    from .vision import analyze_images

    log.info("画像認識で最適な画像と部位の位置を判定中…")
    try:
        best, lm, reason = analyze_images(images, spec.product_name, args.model)
    except llm.LLMError as e:
        log.warning("画像認識に失敗したため経験則で判定します: %s", e)
        return None, Landmarks(), None
    log.info("選択: %s（%s）", best, reason)
    vision_path.write_text(json.dumps({"images": names, "best_index": best, "landmarks": asdict(lm),
                                       "reason": reason}, ensure_ascii=False, indent=2))
    return best, lm, None


def visual_check(out_dir: Path, model: str, preview: bool) -> None:
    """プレビューと元画像を比べ、meta.json に visual_check を書く。できないときは警告だけ出す。"""
    from . import visual_check as vc

    if not preview:
        log.warning("--visual-check には --preview が要るため省略しました")
    elif not llm.has_credentials():
        log.warning("ANTHROPIC_API_KEY がないため見た目の検証を省略しました")
    else:
        log.info("見た目を検証中…")
        try:
            vc.run_one(vc.load_asset(out_dir), model)
        except (ValueError, llm.LLMError) as e:
            log.warning("見た目の検証に失敗しました: %s", e)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    if not args.verbose:
        for noisy in ("httpx", "anthropic", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    blender = find_blender(args.blender)
    cache_dir = args.cache / cache_key(args.product)
    cache_dir.mkdir(parents=True, exist_ok=True)

    spec = resolve_spec(args, cache_dir)
    log.info("寸法: 高さ %.4f m / 直径 %.4f m（形状: %s）", spec.dimensions.height, spec.dimensions.diameter,
             spec.shape_class)
    builder = get_builder(spec.shape_class)
    images = resolve_images(args, spec, cache_dir)
    if not images:
        log.warning("使える画像がないため寸法だけの簡易形状にします")
    best, landmarks, faces = resolve_landmarks(args, spec, images, cache_dir)

    out_dir = args.out / spec.slug
    debug_dir = out_dir / "debug"
    ctx = BuildContext(spec=spec, images=images, preferred_image=best, landmarks=landmarks,
                       out_dir=out_dir, debug_dir=debug_dir, blender=blender, faces=faces)
    log.info("Blender でモデリング中…")
    result = builder.build(ctx)
    if spec.transparency not in (None, "opaque") and spec.shape_class != "revolve":
        # 袋・箱は中身を作らないので透かすと空に見える。組み合わせは部品の finish で指定する
        result.meta.setdefault("warnings", []).append(
            f"transparency（{spec.transparency}）は回転体の容器だけに効く（{spec.shape_class} では無視）")
    postprocess(result, spec.product_name, physics=not args.no_physics, surfaces=spec.surfaces,
                physics_materials=spec.physics_materials, collision=spec.collision_approximations())
    outputs = {"usd": str(result.usd_path)}
    if args.usda:
        outputs["usda"] = str(export_usda(result.usd_path))

    profile = result.meta.get("profile") or {}
    report = validate(result.usd_path, spec.dimensions, physics=not args.no_physics,
                      expected_size=profile.get("expected_size"), static=result.static)
    if args.usdz:
        usdz = export_usdz(result.usd_path)
        outputs["usdz"] = str(usdz)
        zrep = check_usdz(usdz)
        report.errors += [f"usdz: {e}" for e in zrep.errors]
        report.warnings += [f"usdz: {w}" for w in zrep.warnings]

    pcheck = None
    if args.preview:
        log.info("プレビューを描画中…")
        run_script(blender, "render_preview.py", result.usd_path.resolve(), debug_dir.resolve(),
                   log_path=debug_dir / "blender_preview.log")
        outputs["preview"] = sorted(str(p) for p in debug_dir.glob("preview_*.png"))
        outputs["thumbnail"] = str(debug_dir / "thumbnail.png")
        # 透明な部品の見え方（液体の色・容器の明るさ）を画素で確かめる
        pcheck = preview_check.check(debug_dir, (result.meta.get("colors") or {}).get("liquid"),
                                     liquid_expected=bool(profile.get("liquid_top_z")))
        if pcheck:
            report.warnings += pcheck["warnings"]
        if args.usdz and shutil.which("qlmanage"):
            # Quick Look のサムネイル。GUI セッション外などで固まることがあるので時間を区切る
            try:
                subprocess.run(["qlmanage", "-t", "-s", "512", "-o", str(debug_dir), outputs["usdz"]],
                               capture_output=True, timeout=60)
            except subprocess.TimeoutExpired:
                log.warning("qlmanage のサムネイル作成がタイムアウトしたため省略しました")

    meta = {
        "product_name": spec.product_name,
        "cache_dir": str(cache_dir),
        "spec": spec.to_dict(),
        "image_used": result.meta.get("image"),
        "landmarks": asdict(landmarks),
        "profile": result.meta.get("profile"),
        "colors": result.meta.get("colors"),
        "textures": result.meta.get("textures"),  # テクスチャごとの大きさ [px] と画素密度 [px/mm]
        "mass_kg": result.mass,
        "center_of_mass": result.center_of_mass,
        "physics": not args.no_physics,
        "static": result.static,
        "physics_materials": result.meta.get("physics_materials"),  # 物理マテリアルごとの素材・部品・摩擦・反発
        "joints": result.meta.get("joints", []),  # 可動部（扉など）の関節・質量・部品
        "transparency": result.meta.get("transparency", {}),  # 透明・半透明のメッシュ（ルートからのパス → 透け方）
        "screens": result.meta.get("screens", []),  # 光る画面のマテリアルと画像（Screen バリアント）
        "pictures": result.meta.get("pictures", []),  # 店向けの絵柄のマテリアルと画像（Picture バリアント）
        "variants": result.meta.get("variants", {}),  # 部品を出し入れするバリアント（variant_sets）
        "model": args.model,
        "outputs": outputs,
        "warnings": result.meta.get("warnings", []) + report.warnings,
        "preview_check": pcheck,  # 透明な部品のプレビューでの見え方（--preview のときだけ）
        "validation": {"ok": report.ok, "errors": report.errors, "info": report.info},
    }
    meta_path = out_dir / "meta.json"
    if meta_path.exists():
        # 作り直しても見た目の検証の結果は残し、次の検証で回帰を見つけられるようにする
        old = json.loads(meta_path.read_text())
        if old.get("visual_check") or old.get("visual_check_previous"):
            meta["visual_check_previous"] = old.get("visual_check") or old["visual_check_previous"]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
    if args.visual_check:
        visual_check(out_dir, args.model, args.preview)

    for w in report.warnings:
        log.warning(w)
    for e in report.errors:
        log.error(e)
    print(f"\n出力: {result.usd_path}")
    for k, v in outputs.items():
        if k != "usd":
            print(f"  {k}: {v}")
    print(f"検証: {'OK' if report.ok else 'NG（meta.json を参照）'}")
    vc = json.loads(meta_path.read_text()).get("visual_check") if args.visual_check else None
    if vc:
        print(f"見た目: {vc['score']} 点  {vc['summary']}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
