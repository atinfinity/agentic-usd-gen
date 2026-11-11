"""形状クラスの登録。shape_class 名から生成処理を引く。"""

from __future__ import annotations

from typing import Protocol

from . import assembly, box, pouch, revolve


class ShapeBuilder(Protocol):
    def build(self, ctx: "revolve.BuildContext") -> "revolve.BuildResult": ...


BUILDERS: dict[str, ShapeBuilder] = {
    "revolve": revolve.RevolveBuilder(),
    "pouch": pouch.PouchBuilder(),
    "box": box.BoxBuilder(),
    "assembly": assembly.AssemblyBuilder(),
}


def get_builder(shape_class: str) -> ShapeBuilder:
    try:
        return BUILDERS[shape_class]
    except KeyError:
        raise NotImplementedError(
            f"形状クラス '{shape_class}' は未実装です（実装済み: {', '.join(BUILDERS)}）"
        ) from None
