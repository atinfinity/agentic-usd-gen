"""素材ごとの表面のつや（粗さ・金属度）。

マテリアルのロールと素材の意味ラベル（semantics.py）から素材を決め、表の値を引く。
spec.json の surfaces で、マテリアル名（CapMat・LabelMat など）か素材名（paper・pp など）ごとに上書きできる。
透明・半透明・液体のマテリアル（pet / glass / translucent / liquid）と、finish を指定する組み合わせの部品（solid）は
それぞれの決め方のままにする（solid だけはマテリアル名での上書きを受け付ける）。
"""

from __future__ import annotations

# 素材 → (粗さ, 金属度)
FINISHES: dict[str, tuple[float, float]] = {
    "pp": (0.55, 0.0),  # PP のキャップ・蓋（成形のままのつや消し気味の面）
    "plastic": (0.45, 0.0),  # そのほかの成形品（HDPE の容器など）
    "film": (0.20, 0.0),  # 光沢フィルムの袋・ラベル
    "paper": (0.65, 0.0),  # 紙パック・紙箱
    "aluminum": (0.30, 1.0),
    "steel": (0.35, 1.0),
    "metal": (0.30, 1.0),
    "wood": (0.62, 0.0),
    "food": (0.55, 0.0),
    "glass": (0.05, 0.0),
}
ROLES = ("container", "cap", "label")  # 表から値を引くロール


def material_key(role: str, labels: list[str] | None) -> str:
    """ロールと意味ラベルから、表の素材名を決める。"""
    labels = labels or []
    for key in ("aluminum", "steel", "metal", "glass", "paper", "wood", "food"):
        if key in labels:
            return key
    if role == "cap":
        return "pp"
    if role == "label":  # 袋・ラベルの印刷物
        return "film"
    return "plastic"


def apply_finishes(materials: dict[str, dict], overrides: dict[str, dict] | None = None) -> None:
    """materials（マテリアル名 → params）の roughness / metallic を素材の表と上書きから決める。"""
    overrides = overrides or {}
    for name, params in materials.items():
        role = params.get("role")
        if role in ROLES:
            key = material_key(role, params.get("labels"))
            rough, metallic = FINISHES[key]
            params.update(roughness=rough, metallic=metallic, finish=key)
            params.update(_pick(overrides.get(key)))
        elif role != "solid":
            continue
        params.update(_pick(overrides.get(name)))


def _pick(d: dict | None) -> dict:
    return {k: float(v) for k, v in (d or {}).items() if k in ("roughness", "metallic")}
