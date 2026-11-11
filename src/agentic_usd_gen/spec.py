"""商品仕様（検索結果）のデータモデルと JSON 入出力。

寸法はすべてメートル、質量はキログラム、色は "#RRGGBB"。
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

SHAPE_CLASSES = ("revolve", "pouch", "box", "assembly")
ORIENTATIONS = ("upright", "lying")  # 立てて置く / 寝かせて置く（袋のみ）
MOUNTS = ("floor", "ceiling")  # 床に置く / 天井に付ける（上面が天井に付く向きで書き出す。什器向け）
CATEGORIES = ("beverage", "food", "household", "fixture", "environment")  # 書き出し時のフォルダ分け（飲料 / 食品 / 日用品 / 什器 / 内装）
PART_SHAPES = ("box", "cylinder", "dome", "pointed_dome", "bun", "bread", "torus", "revolve", "prism", "leaf", "star",
               "tube", "fruit")
PROFILE_SHAPES = ("revolve", "tube")  # profile（断面の形・通り道）が要る部品
# コリジョンの近似方法（UsdPhysics の physics:approximation）。既定は convexHull
COLLISION_APPROXIMATIONS = ("convexHull", "convexDecomposition", "meshSimplification", "boundingCube",
                            "boundingSphere")
DEFAULT_COLLISION = "convexHull"
# 部品の表面（粗さ・金属かどうか・透明か）。frosted はすりガラス・ビニールのように後ろがぼやけて透ける面、
# translucent は乳白の樹脂（洗剤ボトルの HDPE・ヨーグルトのカップ）のように白く濁って中身がうっすら見える面、
# screen は液晶・光る看板のように平らで、貼った画像が自分で光る面、light は照明の光る面（LED の帯・乳白のカバー）で、
# color の色で光る。light は什器の lights と同じく Lighting バリアントの On のときだけ光る
FINISHES = ("matte", "plastic", "metal", "glossy", "glass", "frosted", "translucent", "screen", "light")
# 半透明の表面 → (素通しの割合 clarity, 粗さ)。残りは光を拡散させて通す・返す
# 容器の透け方。transparent は中身がそのまま見える（PET・ガラス・PS の透明カップ）、frosted・translucent は半透明
# （FINISHES と同じ意味）、opaque は中が見えない
TRANSPARENCIES = ("transparent", "frosted", "translucent", "opaque")
TRANSLUCENCY = {"frosted": (0.7, 0.3), "translucent": (0.45, 0.4)}
# 関節の種類（UsdPhysics の RevoluteJoint・PrismaticJoint）と軸
JOINT_TYPES = ("revolute", "prismatic")
JOINT_AXES = ("X", "Y", "Z")


@dataclass
class Dimensions:
    """回転体の diameter は胴の最大径。depth を書くと胴の断面を楕円にする（diameter が横幅、depth が奥行き）。袋（pouch）では height をシールからシールまでの長さ、
    diameter を平らな状態の幅、depth を膨らんだ厚さとする（寝かせて置く袋でも同じ）。
    箱（box）と組み合わせ（assembly）では diameter を正面の横幅、depth を奥行きとする。"""

    height: float
    diameter: float
    cap_height: float | None = None
    cap_diameter: float | None = None
    depth: float | None = None
    square: float | None = None  # 回転体と袋。胴の断面を角の丸い四角（超楕円の指数。2 で円、大きいほど角ばる）にする
    lobes: list[float] | None = None  # 回転体のみ。炭酸ボトルの花形の底 [脚の数, 高さ m, くぼみの深さ（半径比）]
    gusset: float | None = None  # 袋のみ。底マチの厚さ [m]。底を平らに閉じて立つ袋にする（米袋など。depth 以下）


@dataclass
class Part:
    """組み合わせ（assembly）の部品。座標はメートル、Z 軸が上、正面は -Y。

    size は box なら [幅 X, 奥行き Y, 高さ Z]、cylinder なら [直径 X, 直径 Y, 高さ Z]（軸は Z）。
    dome は底が平らな半楕円体、pointed_dome は先のとがった山（クリームの絞り・いちごなど）、
    bun は肩の張ったまんじゅう形（中華まん・丸パンなど）で、size は cylinder と同じ。bread は bun より丸い山で、
    top の画像を頂点からの道のりで貼る（焼いたパン。側面に画像の縁が縦に伸びない）。
    torus は XY 面に寝かせたドーナツ形（椅子の足かけリングなど）で、size は [外径 X, 外径 Y, 管の太さ]。
    revolve は profile の断面を Z 軸まわりに回した形（くびれたボトルなど）で、size は cylinder と同じ。
    prism は断面（XZ 面）を奥行き Y 方向に押し出した角の丸い柱（おにぎり・サンドイッチの三角柱など）で、size は box と同じ。
    断面は profile の凸多角形 [[x, z], ...]（x は幅を 1 とした -0.5〜0.5、z は高さの割合。省略時は二等辺三角形）。
    leaf は縁がギザギザの 1 枚の葉（厚みのない面、両面）で、size は [長さ X, 幅 Y, 反りの高さ Z]。葉の付け根が -X の端、
    先が +X。中央の主脈で少し折れ、先へ向かって垂れる。segments は片側の鋸歯の数（0 で縁がなめらか）。
    star は放射状に裂けた平たい形（へたの萼片・花びら）で、size は cylinder と同じ（Z は先の反り上がり）。
    profile は [[裂片の数, 付け根の半径の割合, 先の形]]（先の形は 1 より大きいほど細くとがり、小さいほど丸い）。
    fruit は先が下（z=0）の丸みのある果実（いちご形）で、size は cylinder と同じ。profile は revolve と同じ断面
    [[半径, 高さ], ...]（先から上の中心まで。省略時はいちご形）。top の画像を先からの道のりで貼る（画像の中心が先、縁が上の中心）。
    tube は profile の点 [[x, y, z], ...]（center からの位置）を通る細い管（茎・つる）で、size は [始点の太さ, 終点の太さ, 0]。
    center は部品の中心。rotation は XYZ の順に回すオイラー角 [度]（回転の中心は部品の中心）。
    faces は box 部品の面（front/right/back/left/top/bottom、回す前の向き）→ 画像番号。cylinder 部品は top/bottom（円い端面）、
    prism 部品は front/back（断面の形の面）に貼れる。dome・pointed_dome・bun・bread 部品は top に貼れ、画像を真上から山の面に投影する
    （盛った料理の写真を立体のまま貼る）。
    """

    name: str
    shape: str
    size: list[float]
    center: list[float]
    rotation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    color: str | None = None
    finish: str = "plastic"
    faces: dict[str, int | None] | None = None
    collision: bool = True
    material: str | None = None  # 素材（food・wood など）。未設定なら finish から決める（マテリアルの意味ラベル）
    bevel: float | None = None  # box・prism 部品の角の面取りの幅 [m]。未設定なら大きさから決める。0 で面取りしない
    collision_approximation: str | None = None  # コリジョンの近似方法（COLLISION_APPROXIMATIONS）。未設定なら convexHull
    link: str | None = None  # 可動部（扉など）の名前。同じ link の部品は 1 つの剛体になり、joints の関節で本体につながる
    # revolve 部品の断面 [[半径, 高さ], ...]（下から上へ）。半径は size の半分、高さは size[2] を 1 とした割合。
    # prism 部品の断面 [[x, z], ...] か [[x, z, 角の丸みの半径], ...]（省略可。shapes/assembly.prism_outline）
    profile: list[list[float]] | None = None
    # finish が glass の部品を薄い膜（PET のフタ・ブリスター・包装フィルム）として扱い、屈折させない。
    # 中身の詰まった透明な塊のままだと、厚いガラスのブロック越しのように中身が大きく曲がって見える
    thin_walled: bool = False
    # 店向けの絵柄（広告・メニュー・求人など）の面。設定すると Picture バリアント（Default / Blank）を作り、Blank では
    # faces の画像の代わりに、この色（"#RRGGBB"）か、この番号の画像（文字・写真を抜いた無地の面）を貼る
    blank: str | int | None = None
    # cylinder・dome 系・tube・star の円周の分割数（未設定なら 48、tube は 6）。細い茎・小さな葉など、数の多い小さな部品を
    # 軽くする。leaf は片側の鋸歯の数
    segments: int | None = None
    # バリアントで出し入れする部品。バリアントセットの名前 → この部品を表示する値のリスト（ProductSpec.variant_sets）。
    # 書いていないセットでは常に表示する
    show: dict[str, list[str]] | None = None


@dataclass
class Joint:
    """可動部（部品の link）を本体につなぐ関節。組み合わせ（assembly）のみ。

    type は revolute（回転。扉・ふた）か prismatic（スライド。引き戸・引き出し）。axis は回転軸・動く向き（X/Y/Z）。
    anchor は関節の位置（部品の center と同じ座標。回転なら蝶番の軸上の点）。
    limits は動く範囲 [下限, 上限]（revolute は度、prismatic は m）。0 が spec に書いた形のときの位置。
    None は限界なし（revolute だけ。回転ラック・ターンテーブルのように回り続けるもの。±180° を限界にすると PhysX は
    止めにせず、角度の読みが折り返すだけになる）。
    向きは右ねじ（Z 軸なら上から見て反時計回りが正。正面は -Y なので、左端の蝶番で手前に開く扉は負の向き）。
    """

    link: str
    anchor: list[float]
    limits: list[float] | None
    type: str = "revolute"
    axis: str = "Z"


@dataclass
class Light:
    """什器に内蔵する照明（ケース内の LED・ランプ）。組み合わせ（assembly）のみ。UsdLux の RectLight にする。

    size は光る面の [幅 X, 奥行き Y]。光は回す前の -Z（真下）へ出る。center・rotation は部品と同じ座標・向き
    （rotation [90, 0, 0] で +Y（奥）向き、[-90, 0, 0] で -Y（手前）向き）。
    intensity は光る面の輝度 [nit]、kelvin は色温度（冷蔵 5000〜6500、温蔵 2700〜3000）。
    照明は Lighting バリアント（On・Off、既定 On）の On に入る。
    """

    name: str
    size: list[float]
    center: list[float]
    rotation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    intensity: float = 5000.0
    kelvin: float = 5000.0


@dataclass
class Colors:
    cap: str | None = None
    liquid: str | None = None  # None は無色透明（水など）
    label_base: str | None = None
    # 中身の濁り（0 = 澄んでいる 〜 1 = ほぼ不透明）。None なら商品名・タグから推定する（semantics.liquid_turbidity）
    liquid_turbidity: float | None = None


@dataclass
class ImageCandidate:
    url: str
    source_page: str | None = None
    description: str | None = None


@dataclass
class Source:
    url: str
    note: str | None = None


@dataclass
class ProductSpec:
    product_name: str
    slug: str
    shape_class: str
    dimensions: Dimensions
    capacity_ml: float | None = None
    mass_kg: float | None = None  # 中身込みの総質量
    container_material: str | None = None
    orientation: str = "upright"
    category: str | None = None  # CATEGORIES のいずれか。未設定なら書き出し時に推定する
    colors: Colors = field(default_factory=Colors)
    image_candidates: list[ImageCandidate] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    notes: str | None = None
    # assembly の部品。回転体・袋・箱では本体に足す部品（ポンプの頭・フタ・刃など。座標は本体の底面の中心が原点）
    parts: list[Part] = field(default_factory=list)
    bevel: float | None = None  # 箱（box）の本体の角の面取りの幅 [m]。未設定なら既定値。0 で面取りしない
    static: bool = False  # True なら床に固定（剛体にせず、コリジョンだけ付ける）。什器向け
    mount: str = "floor"  # MOUNTS のいずれか。ceiling は上面が天井に付く向き（落下テストは上下を返して落とす）
    tags: list[str] = field(default_factory=list)  # 検索用の語（ブランド・種類・味など）
    fictional: bool = False  # True なら架空の商品（実在の商品名・ロゴ・商品画像を使わないパッケージ）
    # テクスチャに合成した素材の出典（{subject, title, url, file_url, author, license, license_url}）
    image_credits: list[dict] = field(default_factory=list)
    # 表面のつやの上書き。マテリアル名（CapMat など）か素材名（paper・pp など、finish.py）→ {roughness, metallic}
    surfaces: dict[str, dict] = field(default_factory=dict)
    # 摩擦・反発の上書き。素材名（paper・film など、physics_material.py）かコリジョンの部品名
    # → {static_friction, dynamic_friction, restitution}
    physics_materials: dict[str, dict] = field(default_factory=dict)
    # 容器の透け方（TRANSPARENCIES）。未設定なら container_material から推定する。回転体の容器だけに効く
    transparency: str | None = None
    # コリジョンの近似方法の上書き。コリジョンの部品名（Body・Cap・組み合わせの部品名）→ COLLISION_APPROXIMATIONS のどれか
    collision_approximation: dict[str, str] = field(default_factory=dict)
    joints: list[Joint] = field(default_factory=list)  # 可動部の関節（組み合わせのみ。部品の link とセット）
    lights: list[Light] = field(default_factory=list)  # 内蔵の照明（組み合わせのみ。Lighting バリアントの On に入る）
    # 部品の blank（Picture バリアント）の絵柄が合う場所の種類（convenience_store・cafe など。asset.json の picture.places）
    picture_places: list[str] = field(default_factory=list)
    # 光る画面（Screen バリアント）の画像が合う場所の種類（asset.json の screen.places。"any" はどこでも）。空なら店向け
    screen_places: list[str] = field(default_factory=list)
    # 部品の出し入れのバリアントセット（組み合わせのみ）。名前 → 値のリスト（先頭が既定）。部品の show で使う。
    # 先に書いたセットほど強い（どのセットでも非表示の指定だけを書くので、順番で結果は変わらない）
    variant_sets: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> ProductSpec:
        return cls(
            product_name=d["product_name"],
            slug=make_slug(d.get("slug") or d["product_name"]),
            shape_class=d.get("shape_class") or "revolve",
            dimensions=Dimensions(**d["dimensions"]),
            capacity_ml=d.get("capacity_ml"),
            mass_kg=d.get("mass_kg"),
            container_material=d.get("container_material"),
            orientation=d.get("orientation") or "upright",
            category=d.get("category"),
            colors=Colors(**(d.get("colors") or {})),
            image_candidates=[ImageCandidate(**c) for c in d.get("image_candidates") or []],
            sources=[Source(**s) for s in d.get("sources") or []],
            notes=d.get("notes"),
            parts=[Part(**p) for p in d.get("parts") or []],
            bevel=d.get("bevel"),
            static=bool(d.get("static", False)),
            mount=d.get("mount") or "floor",
            tags=[str(t) for t in d.get("tags") or []],
            fictional=bool(d.get("fictional", False)),
            image_credits=[dict(c) for c in d.get("image_credits") or []],
            surfaces={str(k): dict(v) for k, v in (d.get("surfaces") or {}).items()},
            physics_materials={str(k): dict(v) for k, v in (d.get("physics_materials") or {}).items()},
            collision_approximation={str(k): str(v) for k, v in (d.get("collision_approximation") or {}).items()},
            transparency=d.get("transparency") or None,
            joints=[Joint(**j) for j in d.get("joints") or []],
            lights=[Light(**x) for x in d.get("lights") or []],
            picture_places=[str(x) for x in d.get("picture_places") or []],
            screen_places=[str(x) for x in d.get("screen_places") or []],
            variant_sets={str(k): [str(x) for x in v] for k, v in (d.get("variant_sets") or {}).items()},
        )

    def __post_init__(self):
        if self.mount not in MOUNTS:
            raise ValueError(f"mount が不正: {self.mount}（{', '.join(MOUNTS)}）")
        if self.transparency is not None and self.transparency not in TRANSPARENCIES:
            raise ValueError(f"transparency が不正: {self.transparency}（{', '.join(TRANSPARENCIES)}）")
        for name, v in self.collision_approximations().items():
            if v not in COLLISION_APPROXIMATIONS:
                raise ValueError(f"{name} の collision_approximation が不正: {v}（{', '.join(COLLISION_APPROXIMATIONS)}）")
        self._check_joints()
        self._check_lights()
        self._check_blanks()
        self._check_variants()

    def _check_variants(self) -> None:
        if self.variant_sets and self.shape_class != "assembly":
            raise ValueError("部品のバリアント（variant_sets）は組み合わせ（assembly）だけで使えます")
        for name, values in self.variant_sets.items():
            if not values or len(set(values)) != len(values):
                raise ValueError(f"バリアントセット {name} の値が空か重なっています")
        for p in self.parts:
            for name, values in (p.show or {}).items():
                if name not in self.variant_sets:
                    raise ValueError(f"部品 {p.name} の show のバリアントセット {name} が variant_sets にありません")
                bad = [v for v in values if v not in self.variant_sets[name]]
                if bad:
                    raise ValueError(f"部品 {p.name} の show の値 {bad} がバリアントセット {name} にありません")

    def _check_blanks(self) -> None:
        for p in self.parts:
            if p.blank is None:
                continue
            if not p.faces:
                raise ValueError(f"部品 {p.name} の blank は faces（画像を貼る面）のある部品だけに使えます")
            if isinstance(p.blank, str) and not re.fullmatch(r"#[0-9A-Fa-f]{6}", p.blank):
                raise ValueError(f"部品 {p.name} の blank が不正: {p.blank}（#RRGGBB の色か画像の番号）")

    def _check_lights(self) -> None:
        if not self.lights:
            return
        if self.shape_class != "assembly":
            raise ValueError("照明（lights）は組み合わせ（assembly）だけで使えます")
        names = [x.name for x in self.lights]
        if len(set(names)) != len(names):
            raise ValueError("照明の name が重なっています")
        for x in self.lights:
            if len(x.size) != 2 or min(x.size) <= 0 or len(x.center) != 3 or len(x.rotation) != 3:
                raise ValueError(f"照明 {x.name} の size（[幅, 奥行き]）・center・rotation が不正")
            if x.intensity <= 0 or not 1000 <= x.kelvin <= 10000:
                raise ValueError(f"照明 {x.name} の intensity（正の nit）か kelvin（1000〜10000）が不正")

    def _check_joints(self) -> None:
        links = {p.link for p in self.parts if p.link}
        if not links and not self.joints:
            return
        if self.shape_class != "assembly":
            raise ValueError("可動部（部品の link・joints）は組み合わせ（assembly）だけで使えます")
        names = {p.name for p in self.parts}
        if links & names:
            raise ValueError(f"link の名前が部品の名前と重なっています: {', '.join(sorted(links & names))}")
        jlinks = [j.link for j in self.joints]
        if len(set(jlinks)) != len(jlinks):
            raise ValueError("1 つの link に関節が 2 つ以上あります")
        if set(jlinks) != links:
            raise ValueError(f"link と joints が対応していません（部品の link: {sorted(links)}、joints: {sorted(jlinks)}）")
        for j in self.joints:
            if j.type not in JOINT_TYPES:
                raise ValueError(f"{j.link} の関節の type が不正: {j.type}（{', '.join(JOINT_TYPES)}）")
            if j.axis not in JOINT_AXES:
                raise ValueError(f"{j.link} の関節の axis が不正: {j.axis}（{', '.join(JOINT_AXES)}）")
            if j.limits is None and j.type != "revolute":
                raise ValueError(f"{j.link} の関節の limits がない（限界なしにできるのは revolute だけ）")
            if len(j.anchor) != 3 or j.limits is not None and (len(j.limits) != 2 or j.limits[0] > j.limits[1]):
                raise ValueError(f"{j.link} の関節の anchor（3 つ）か limits（[下限, 上限]）が不正")
            if all(p.link == j.link and not p.collision for p in self.parts if p.link == j.link):
                raise ValueError(f"{j.link} にコリジョンのある部品がありません")

    def collision_approximations(self) -> dict[str, str]:
        """コリジョンの部品名 → 近似方法（指定したものだけ）。部品の collision_approximation に、全体の指定を重ねる。

        花形の底（dimensions.lobes）の回転体は、本体を既定で convexDecomposition にする。PhysX は凸包の面の数を
        抑えるため、細い胴に面を使い切って底の脚先を 1 点に潰し、立てても倒れる。"""
        out = {p.name: p.collision_approximation for p in self.parts if p.collision_approximation}
        if self.dimensions.lobes and self.shape_class == "revolve":
            out = {"Body": "convexDecomposition"} | out
        return out | self.collision_approximation

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("square", "lobes", "gusset"):
            if d["dimensions"].get(k) is None:
                d["dimensions"].pop(k, None)  # 使わない項目は出さず、既存の仕様と同じ出力にする
        for k in ("bevel", "transparency"):
            if d.get(k) is None:
                d.pop(k, None)
        if d.get("mount") == "floor":
            d.pop("mount")  # 既定は出さず、既存の仕様と同じ出力にする
        for k in ("surfaces", "physics_materials", "collision_approximation", "joints", "lights", "picture_places",
                  "screen_places", "variant_sets"):
            if not d.get(k):
                d.pop(k, None)
        if d["colors"].get("liquid_turbidity") is None:
            d["colors"].pop("liquid_turbidity", None)
        for p in d["parts"]:
            for k in ("bevel", "collision_approximation", "link", "blank", "show"):
                if p.get(k) is None:
                    p.pop(k, None)
        return d

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, path: Path) -> ProductSpec:
        return cls.from_dict(json.loads(path.read_text()))

    def total_mass_kg(self) -> float:
        """総質量。未取得なら容量から推定する（液体密度 1.0 + 容器 4%）。"""
        if self.mass_kg:
            return self.mass_kg
        if self.capacity_ml:
            return self.capacity_ml * 1e-3 * 1.04
        return 0.1


def make_slug(text: str) -> str:
    """USD の Prim 名にも使える ASCII 識別子に変換する。"""
    s = unicodedata.normalize("NFKC", text).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s:
        s = "asset"
    if s[0].isdigit():
        s = "a_" + s
    return s


def cache_key(product_name: str) -> str:
    """検索キャッシュのディレクトリ名（日本語可、ファイル名に使えない文字だけ置換）。"""
    s = unicodedata.normalize("NFKC", product_name).strip()
    return re.sub(r"[\s/\\:*?\"<>|]+", "_", s)


def parse_dims_override(text: str) -> dict[str, float]:
    """`H=0.205,D=0.065,CAP_H=0.016,CAP_D=0.030[,T=0.05]` 形式（メートル）を解釈する。T は袋の厚さ。"""
    keys = {"H": "height", "D": "diameter", "CAP_H": "cap_height", "CAP_D": "cap_diameter", "T": "depth"}
    out: dict[str, float] = {}
    for part in text.split(","):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        k = k.strip().upper()
        if k not in keys:
            raise ValueError(f"未知の寸法キー: {k}（使えるのは {', '.join(keys)}）")
        out[keys[k]] = float(v)
    return out
