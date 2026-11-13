"""Claude の web search / web fetch で商品の寸法と画像候補を集める。"""

from __future__ import annotations

from .llm import nullable, request_json
from .spec import CATEGORIES, FINISHES, ORIENTATIONS, PART_SHAPES, PROFILE_SHAPES, SHAPE_CLASSES, TRANSPARENCIES, ProductSpec

SYSTEM = """\
あなたはロボットシミュレーション用 3D アセットを作るための商品リサーチ担当です。
web_search と web_fetch を使って、指定された商品の実物の外形寸法と、形状抽出に使える商品画像を調べてください。

寸法について:
- メーカー公式、容器メーカーの仕様、EC サイトの「商品サイズ」表記を優先し、根拠の URL を sources に必ず残す。
- 商品名が日本語なら日本市場の商品として調べる（国によってボトル形状が違う）。
- 単位はメートル。height はキャップ込みの全高、diameter は胴の最大径。
- 袋菓子などの袋（pouch）は、height にシールからシールまでの長さ、diameter にそれと直交する幅（どちらも平らな状態のフィルム寸法）、depth に膨らんだときの厚さを入れる。
- 箱（box）は、height に高さ、diameter に正面の横幅、depth に奥行きを入れる（正面 = 商品名が大きく見える面）。
- orientation は、チョコバーのようにシールが左右にある横長の袋を寝かせて置くものなら "lying"、それ以外は "upright"。
- キャップ寸法や総質量が見つからない場合は、同種容器の一般的な値から推定してよいが、notes に「推定」と明記する。
- notes・container_material・画像の source_page と description・sources の note は、書くことがなければ空文字にする。
- mass_kg は中身込みの総質量。

画像について:
- image_candidates には画像ファイルそのものの URL（jpg/png/webp）を 3〜8 件入れる。HTML ページの URL は不可。
- 真横から撮った、白や単色の背景で、商品 1 本だけが直立して写っている画像を優先する。
- 斜めからの写真、複数本の集合写真、手に持った写真は避ける。

colors は見た目の代表色（#RRGGBB）。liquid は中身が無色透明なら null。
container_material は容器の素材（PET / glass / PP / PS / HDPE / aluminum / paper / film など）。
transparency は回転体の容器の透け方で、中身がそのまま見えるなら "transparent"（PET・ガラス瓶・PS や透明 PP のカップ）、
すりガラスのように後ろがぼやけて透けるなら "frosted"、乳白の樹脂（HDPE のボトル・ヨーグルトのカップ）なら "translucent"、
中が見えない（着色した樹脂・缶・紙）なら "opaque"。袋・箱・assembly、分からないときは null。
liquid_turbidity は中身の濁り（0 = 澄んでいる〜1 = ほぼ不透明。オレンジジュース 0.7、牛乳・ミルクティー 0.95、スポーツドリンク 0.25、お茶・炭酸・水 0）。分からなければ null（商品名から推定する）。
shape_class は回転体（ボトル・缶・瓶・カップなど）なら "revolve"、ピロー包装の袋なら "pouch"、箱型なら "box"、
セルフレジ・サイネージ・棚のように直方体と円柱の組み合わせで表すものなら "assembly"。
回転体では depth を null にする。箱の image_candidates は正面を真正面から撮った画像を優先する。
category は飲料なら "beverage"、食品（菓子・即席めんなど）なら "food"、日用品（化粧品・電池・紙製品など）なら "household"、
店舗の什器・機器なら "fixture"、床・壁・天井・照明・ドア・掲示物など店舗の内装・建具なら "environment"。

assembly のとき（それ以外は parts を空、static を false にする）:
- dimensions は全体の外形で、height = 高さ、diameter = 正面の横幅、depth = 奥行き。
- parts に部品を並べる。座標はメートル、Z が上、正面は -Y、原点は底面の中心。
  size は box なら [幅 X, 奥行き Y, 高さ Z]、cylinder なら [直径 X, 直径 Y, 高さ Z]。center は部品の中心、
  rotation は XYZ 順のオイラー角 [度]（傾いた画面など。不要なら [0,0,0]）。
- finish は表面の種類（matte / plastic / metal / glossy / glass / frosted / translucent / screen / light。液晶の画面・光る看板は screen、照明の光るカバー・LED は light、透明な窓・扉は glass、
  すりガラス・ビニール傘・半透明のフィルムのように後ろがぼやけて透けるものは frosted、乳白の樹脂（HDPE のボトル・ヨーグルトのカップ）は translucent）。
- material は部品の素材を英語 1 語で（wood / food / paper など）。finish から分かる plastic・metal・glass なら空文字。
- faces は box 部品の面に貼る画像の番号（image_candidates の順番）を、[front, right, back, left, top, bottom] の順に 6 個並べる。
  画像のない面は -1。どの面にも貼らない部品は空の配列にする。
- 床に据え置く什器は static を true にする（剛体にせず、動かないコリジョンにする）。
tags は検索用の短い語を 3〜8 個（ブランド・種類・味・用途など。日本語と英語を混ぜてよい。カテゴリと形状は自動で足すので不要）。
slug は英小文字とアンダースコアの短い識別子（例: green_tea_600ml_pet）。
"""

# 構造化出力のスキーマは、null を許す項目（anyOf）を 16 個までしか持てない。
# 文字列の「なし」は空文字、faces の「なし」は -1・空の配列で受け取り、_normalize() で None に戻す。
_STR = {"type": "string"}
_NUM = {"type": "number"}
_HEX = {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}

_VEC3 = {"type": "array", "items": _NUM}
_FACE_NAMES = ("front", "right", "back", "left", "top", "bottom")
# 面ごとのオブジェクトにすると、検索ツールと一緒に送ったときに「文法が大きすぎる」と拒否される
_FACES = {"type": "array", "items": {"type": "integer"}}
_PART = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "shape", "size", "center", "rotation", "color", "finish", "faces", "collision", "material"],
    "properties": {
        "name": _STR,
        "shape": {"type": "string", "enum": [s for s in PART_SHAPES if s not in PROFILE_SHAPES]},
        "size": _VEC3,
        "center": _VEC3,
        "rotation": _VEC3,
        "color": nullable(_HEX),
        "finish": {"type": "string", "enum": list(FINISHES)},
        "faces": _FACES,
        "collision": {"type": "boolean"},
        "material": _STR,
    },
}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "product_name", "slug", "shape_class", "dimensions", "capacity_ml", "mass_kg",
        "container_material", "orientation", "category", "colors", "image_candidates", "sources", "notes",
        "parts", "static", "tags", "transparency",
    ],
    "properties": {
        "product_name": _STR,
        "slug": _STR,
        "shape_class": {"type": "string", "enum": list(SHAPE_CLASSES)},
        "dimensions": {
            "type": "object",
            "additionalProperties": False,
            "required": ["height", "diameter", "cap_height", "cap_diameter", "depth"],
            "properties": {
                "height": _NUM,
                "diameter": _NUM,
                "cap_height": nullable(_NUM),
                "cap_diameter": nullable(_NUM),
                "depth": nullable(_NUM),
            },
        },
        "capacity_ml": nullable(_NUM),
        "mass_kg": nullable(_NUM),
        "container_material": _STR,
        "transparency": nullable({"type": "string", "enum": list(TRANSPARENCIES)}),
        "orientation": {"type": "string", "enum": list(ORIENTATIONS)},
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "colors": {
            "type": "object",
            "additionalProperties": False,
            "required": ["cap", "liquid", "label_base", "liquid_turbidity"],
            "properties": {"cap": nullable(_HEX), "liquid": nullable(_HEX), "label_base": nullable(_HEX),
                           "liquid_turbidity": nullable(_NUM)},
        },
        "image_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["url", "source_page", "description"],
                "properties": {"url": _STR, "source_page": _STR, "description": _STR},
            },
        },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["url", "note"],
                "properties": {"url": _STR, "note": _STR},
            },
        },
        "notes": _STR,
        "parts": {"type": "array", "items": _PART},
        "static": {"type": "boolean"},
        "tags": {"type": "array", "items": _STR},
    },
}

TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 10},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 10},
]


def search_product(product_name: str, model: str) -> ProductSpec:
    data = request_json(
        model=model,
        system=SYSTEM,
        content=f"商品名: {product_name}",
        schema=SCHEMA,
        tools=TOOLS,
        effort="high",
    )
    return ProductSpec.from_dict(_normalize(data))


def _none_if_blank(d: dict, *keys: str) -> None:
    for k in keys:
        if isinstance(d.get(k), str) and not d[k].strip():
            d[k] = None


def _faces(v: list[int] | None) -> dict | None:
    """[front, right, back, left, top, bottom] の番号（-1 = なし）を、面の名前をキーにした辞書に直す。"""
    nums = [n if isinstance(n, int) and n >= 0 else None for n in (v or [])][: len(_FACE_NAMES)]
    if not any(n is not None for n in nums):
        return None
    return dict(zip(_FACE_NAMES, nums + [None] * (len(_FACE_NAMES) - len(nums))))


def _normalize(data: dict) -> dict:
    """スキーマの都合で空文字・-1・空の配列にした「なし」を None に戻す。"""
    _none_if_blank(data, "notes", "container_material")
    for c in data.get("image_candidates") or []:
        _none_if_blank(c, "source_page", "description")
    for src in data.get("sources") or []:
        _none_if_blank(src, "note")
    for part in data.get("parts") or []:
        _none_if_blank(part, "material")
        part["faces"] = _faces(part.get("faces"))
    return data
