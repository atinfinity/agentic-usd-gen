"""Claude の画像認識で、輪郭抽出に使う画像を選び、目印の高さを読み取る。

目印は「商品の上端を 0、下端を 1」とした比率で受け取る。ピクセル単位の輪郭は
OpenCV 側（profile.py）で求め、ここでの値は区間の切り分けにだけ使う。
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .llm import nullable, request_json

MAX_SIDE = 1024

SYSTEM = """\
あなたは商品写真から 3D モデルを作るための画像解析担当です。
渡された画像の中から、真横から撮影され、単色背景で、商品 1 本だけが直立している画像を 1 枚選んでください。
使える画像がなければ best_index を null にします。

選んだ画像について、商品の上端（キャップ頂部）を 0、下端（底面）を 1 とした縦方向の比率で以下を答えてください。
- cap_bottom: キャップの下端
- label_top / label_bottom: 胴に巻かれた不透明なラベルの上端と下端（ラベルがなければ null）
- liquid_top: 中身の液面（容器が不透明で見えない、または判断できなければ null）
"""

_RATIO = {"type": "number", "minimum": 0, "maximum": 1}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["best_index", "reason", "cap_bottom", "label_top", "label_bottom", "liquid_top"],
    "properties": {
        "best_index": nullable({"type": "integer"}),
        "reason": {"type": "string"},
        "cap_bottom": nullable(_RATIO),
        "label_top": nullable(_RATIO),
        "label_bottom": nullable(_RATIO),
        "liquid_top": nullable(_RATIO),
    },
}


@dataclass
class Landmarks:
    """商品の上端=0、下端=1 の比率。"""

    cap_bottom: float | None = None
    label_top: float | None = None
    label_bottom: float | None = None
    liquid_top: float | None = None


def _encode(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = base64.standard_b64encode(buf.getvalue()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}


def analyze_images(paths: list[Path], product_name: str, model: str) -> tuple[int | None, Landmarks, str]:
    content: list[dict] = []
    for i, p in enumerate(paths):
        content.append({"type": "text", "text": f"画像 {i}:"})
        content.append(_encode(p))
    content.append({"type": "text", "text": f"商品名: {product_name}"})

    data = request_json(model=model, system=SYSTEM, content=content, schema=SCHEMA, effort="medium")
    idx = data["best_index"]
    if idx is not None and not 0 <= idx < len(paths):
        idx = None
    lm = Landmarks(
        cap_bottom=data["cap_bottom"],
        label_top=data["label_top"],
        label_bottom=data["label_bottom"],
        liquid_top=data["liquid_top"],
    )
    return idx, lm, data["reason"]
