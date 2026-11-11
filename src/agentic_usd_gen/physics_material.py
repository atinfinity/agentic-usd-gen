"""物理マテリアル（摩擦・反発係数）を素材ごとに決める。

コリジョンの部品ごとに、割り当てた見た目のマテリアルのロールと意味ラベルから素材を決め（finish.material_key と同じ分類。
ただしプラスチックの成形品はキャップ・容器を区別せず plastic）、表の値を引く。素材が同じ部品は 1 つの物理マテリアルを共有する。
spec.json の physics_materials で、素材名かコリジョンの部品名ごとに上書きできる。

値は把持・すべりのシミュレーション用の概算（相手は乾いた樹脂やゴムの指・棚板くらいを想定）。
摩擦係数は相手の素材・表面の状態で大きく変わるので、実機に合わせる場合は上書きする。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .finish import material_key


@dataclass(frozen=True)
class Contact:
    static_friction: float
    dynamic_friction: float
    restitution: float


# 素材 → 摩擦・反発。静止摩擦は素材ごとの目安、動摩擦は静止摩擦の 0.8 倍（従来の 0.5 / 0.4 と同じ比）
CONTACTS: dict[str, Contact] = {
    "aluminum": Contact(0.30, 0.24, 0.15),
    "steel": Contact(0.30, 0.24, 0.15),
    "metal": Contact(0.30, 0.24, 0.15),
    "plastic": Contact(0.35, 0.28, 0.10),  # PET・PP・HDPE の成形品
    "film": Contact(0.40, 0.32, 0.05),  # 袋のフィルム（やわらかく、ほとんど跳ねない）
    "paper": Contact(0.50, 0.40, 0.05),
    "glass": Contact(0.30, 0.24, 0.15),
    "wood": Contact(0.45, 0.36, 0.10),
    "food": Contact(0.50, 0.40, 0.05),
}
DEFAULT = "plastic"
SOURCE = ("素材ごとの概算値（参考: Engineering ToolBox「Friction and Friction Coefficients」"
          "https://www.engineeringtoolbox.com/friction-coefficients-d_778.html）。"
          "動摩擦は静止摩擦の 0.8 倍。相手の素材・表面の状態で大きく変わる")


def physics_key(role: str | None, labels: list[str] | None) -> str:
    """見た目のマテリアルのロールと意味ラベルから、物理の素材名を決める。"""
    key = material_key(role or "container", labels)
    if key == "pp":
        return "plastic"
    return key if key in CONTACTS else DEFAULT


def contact_for(key: str, collider: str | None = None, overrides: dict[str, dict] | None = None) -> Contact:
    """素材 key の値に、素材名・部品名の上書き（この順に重ねる）をかけたもの。"""
    c = asdict(CONTACTS.get(key, CONTACTS[DEFAULT]))
    for k in (key, collider):
        c.update({n: float(v) for n, v in ((overrides or {}).get(k) or {}).items() if n in c})
    return Contact(**c)
