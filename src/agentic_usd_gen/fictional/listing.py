"""架空の商品の一覧（slug・分類・形状・品名）。

品名は定義の関数を呼ばないと分からず、呼ぶと絵柄まで描く（全点で数分かかる）。
そこで一覧を data/fictional_index.tsv に置き、--list はそれを読む。定義を足したり品名を変えたりしたら、次で作り直す。

    uv run python -m agentic_usd_gen.fictional.listing
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

INDEX = Path(__file__).resolve().parent.parent / "data" / "fictional_index.tsv"
REFRESH = "uv run python -m agentic_usd_gen.fictional.listing"


class Row(NamedTuple):
    slug: str
    category: str
    shape_class: str
    name: str


def row_of(product) -> Row:
    return Row(product.slug, product.category, product.shape_class, product.name)


def load(path: Path = INDEX) -> dict[str, Row]:
    rows = (Row(*line.split("\t")) for line in path.read_text(encoding="utf-8").splitlines() if line)
    return {r.slug: r for r in rows}


def build(slugs=None) -> list[Row]:
    """定義を呼んで一覧を作る（絵柄を描くので遅い）。"""
    from .paint import recording
    from .registry import PRODUCTS

    rows = []
    for slug in slugs if slugs is not None else PRODUCTS:
        with recording():
            rows.append(row_of(PRODUCTS[slug]()))
    return rows


def rows(words: list[str] | None = None) -> list[Row]:
    """定義の順に並べた一覧。words があれば、すべての語をどこかの列に含む行だけ（大文字・小文字は区別しない）。"""
    from .registry import PRODUCTS

    index = load()
    missing = [s for s in PRODUCTS if s not in index]  # 一覧を作り直していない定義は、その場で呼ぶ
    index.update({r.slug: r for r in build(missing)})
    out = [index[s] for s in PRODUCTS]
    for w in (w.lower() for w in words or []):
        out = [r for r in out if any(w in col.lower() for col in r)]
    return out


def format_rows(rs: list[Row]) -> str:
    """列をそろえた文字列。品名は全角を含むので、そろえなくてよい最後の列に置く。"""
    widths = [max((len(r[i]) for r in rs), default=0) for i in range(3)]
    return "\n".join("  ".join([*(r[i].ljust(widths[i]) for i in range(3)), r.name]) for r in rs)


def main() -> int:
    rs = build()
    INDEX.write_text("".join("\t".join(r) + "\n" for r in rs), encoding="utf-8")
    print(f"{INDEX}: {len(rs)} 点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
