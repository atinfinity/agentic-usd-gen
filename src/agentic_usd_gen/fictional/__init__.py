"""架空のパッケージの商品を生成する（公開用のアセット）。

    agentic-usd-gen-fictional --all --out out/fictional --preview
    agentic-usd-gen-fictional cup_noodle_tall potato_chips_bag --no-build

商品ごとに検索キャッシュと同じ形（spec.json / vision.json / images/）を書き、通常の生成（agentic-usd-gen）に渡す。
実在の商品名・ブランド名・ロゴ・商品写真は使わない。写真はパブリックドメイン（CC0 など）の素材を合成する。
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .. import cli
from .base import write
from .paint import recording
from .registry import PRODUCTS

log = logging.getLogger("agentic_usd_gen.fictional")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-fictional", description="架空のパッケージの商品を生成する（公開用）")
    p.add_argument("products", nargs="*", metavar="slug", help=f"商品（{', '.join(PRODUCTS)}）")
    p.add_argument("--all", action="store_true", help="すべての商品")
    p.add_argument("--cache", type=Path, default=Path("cache/fictional"), help="キャッシュ（既定: cache/fictional）")
    p.add_argument("--no-build", action="store_true", help="キャッシュだけ書き、USD は作らない")
    # 値を取る agentic-usd-gen のオプションはここで受けて渡す（位置引数の商品と取り違えないように）
    p.add_argument("--out", help="出力先（agentic-usd-gen に渡す）")
    p.add_argument("--blender", help="Blender の実行ファイル（agentic-usd-gen に渡す）")
    args, rest = p.parse_known_args(argv)  # 残り（--preview・--usdz など）は agentic-usd-gen に渡す
    rest += [x for k in ("out", "blender") if getattr(args, k) for x in (f"--{k}", getattr(args, k))]
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    names = list(PRODUCTS) if args.all else args.products
    unknown = [n for n in names if n not in PRODUCTS]
    if not names or unknown:
        p.error(f"商品を指定してください（未知: {', '.join(unknown)}）" if unknown else "商品か --all を指定してください")
    status = 0
    for n in names:
        with recording() as canvases:
            product = PRODUCTS[n]()
        write(product, args.cache, canvases)
        log.info("架空の商品: %s（%s）", product.name, product.slug)
        if not args.no_build:
            status |= cli.main([product.name, "--cache", str(args.cache), *rest])
    return status


if __name__ == "__main__":
    sys.exit(main())
