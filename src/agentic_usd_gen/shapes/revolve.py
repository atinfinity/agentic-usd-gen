"""回転体（ボトル・缶・瓶・カップ）の生成。

側面画像 → 輪郭 → 半径プロファイル → Blender で回転 → USD。
画像が使えないときは寸法だけの簡易形状にする。
dimensions.depth が直径より小さければ胴の断面を楕円にする（平たいボトル。キャップは丸のまま）。
spec.json に parts があれば本体に部品（ポンプの頭など）を足す（assembly.attach_parts）。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from ..blender_runner import run_script
from . import details
from ..label import label_circumference, make_label_texture, wrap_texture
from ..texres import record, texture_px
from ..profile import RevolveProfile, build_profile, draw_debug, extract_silhouette, parametric_profile
from ..semantics import LIQUID, container_labels, liquid_turbidity
from ..spec import TRANSLUCENCY, ProductSpec
from ..vision import Landmarks

log = logging.getLogger(__name__)

SEGMENTS = 128
WALL = 0.0004  # PET の肉厚 [m]
OPAQUE_WALL = 0.0012  # 不透明容器（紙カップ・缶など）の肉厚 [m]
# 液体の外周は容器の壁の厚みの中央に置く（壁に半分食い込ませる）。すき間を空けると 空気→PET→空気→液体 と
# 境目が増え、レイトレースで全反射の白い縁が出る。実物の境目は PET→液体 の 1 つなので、それに近づける
LIQUID_INSET = 0.5  # 液体の外周の、容器の外面からの深さ（壁の厚みに対する比）
LABEL_OFFSET = 0.0003  # 容器表面からラベルまでの浮かせ量 [m]
LABEL_BACK_PRINT = 0.15  # 透明容器のラベルの裏面に透けて見える表の絵柄の濃さ（0 で白地だけ）
LABEL_BACK_COLOR = (244, 244, 240)  # ラベルの裏面の地の色（裏刷りの白インク）
RDP_TOL = 0.0001  # プロファイル間引きの許容誤差 [m]
PET_COLOR = "#F2F7F5"
LIQUID_DENSITY = 1040.0  # 清涼飲料のおおよその密度 [kg/m^3]
TRANSPARENT_KEYWORDS = ("pet", "glass", "clear", "transparent", "ペット", "ガラス", "瓶", "透明",
                        "polystyrene", "ポリスチレン", "acrylic", "アクリル", "polycarbonate", "ポリカーボネート")
# 透明な樹脂の略号（PS・OPS の透明カップ、PC・PMMA のケース）。短いので語として一致させる
TRANSPARENT_TOKENS = {"ps", "ops", "pc", "pmma"}
OPAQUE_KEYWORDS = ("opaque", "不透明")
# ガラス瓶。PET より屈折率が高く、壁も底もずっと厚い。ごく薄い緑の色味がある（ソーダ石灰ガラスの鉄分）
GLASS_KEYWORDS = ("glass", "ガラス", "瓶")
GLASS_WALL = 0.003  # 瓶の肉厚 [m]
GLASS_BOTTOM = 0.007  # 瓶の底の厚み [m]。底は胴より厚い
GLASS_COLOR = "#E4F2E8"
GLASS_IOR = 1.52
GLASS_DENSITY = 2500.0  # [kg/m^3]
# 壁は PET と同じく薄い膜として扱う（屈折させない）。屈折させると、壁に食い込ませた中身との境目で
# 光が散って中身が白っぽくくすむ。厚みは底と口の縁の見た目・質量・重心に効かせる
GLASS_THIN_WALLED = True
# 半透明の容器（すりガラス・乳白の樹脂）。透明より先に当てる（"frosted glass" は半透明）
TRANSLUCENT_KEYWORDS = {
    "frosted": ("frosted", "すりガラス", "くもりガラス"),
    "translucent": ("translucent", "半透明", "乳白", "hdpe", "ldpe", "polyethylene", "ポリエチレン"),
}
TRANSLUCENT_WALL = 0.0008  # 半透明の樹脂ボトル（HDPE など）の肉厚 [m]
TRANSLUCENT_COLOR = "#F4F4F0"  # 色の指定がない半透明の容器（無着色のポリエチレン）
# 濁った液体の散乱の強さ。胴の中心を通る光が散乱する回数の目安（光学的な厚さ）を TURBID_TAU × 濁り^2.5 にする。
# 濁り 0.25（スポーツドリンク）で約 2、0.7（オレンジジュース）で約 25、0.95（牛乳）で約 50
TURBID_TAU = 60.0
TURBID_ANISOTROPY = 0.2  # 散乱は少し前向き（果肉・乳脂肪の粒）
# 半透明の容器に濁った液体（濁り 0.5 以上。ケチャップなど）を入れたときの容器の MDL：素通しでない分をすべて拡散透過にする。
# Isaac Sim の RTX では、容器の拡散反射が少しでもある（0.9 でも）と白いもやがかかり、赤いケチャップが薄い桃色に見えた
TRANSLUCENT_TURBID = 0.5


def container_transparency(container_material: str | None, transparency: str | None = None) -> str:
    """容器の透け方（spec.TRANSPARENCIES のどれか）。spec の transparency があればそれ、なければ素材名から推定する。
    素材名は 不透明の明示 → 半透明（すりガラス・乳白の樹脂）→ 透明 の順に当てる（「半透明」「不透明」も「透明」を含むので）。
    不明（None）は従来どおり透明ボトルとして扱う。"""
    if transparency:
        return transparency
    if not container_material:
        return "transparent"
    m = container_material.lower()
    if any(k in m for k in OPAQUE_KEYWORDS):
        return "opaque"
    for kind, keys in TRANSLUCENT_KEYWORDS.items():
        if any(k in m for k in keys):
            return kind
    if any(k in m for k in TRANSPARENT_KEYWORDS) or TRANSPARENT_TOKENS & set(re.findall(r"[a-z]+", m)):
        return "transparent"
    return "opaque"


def translucency(container_material: str | None, transparency: str | None = None) -> str | None:
    """容器が半透明なら、その表面の種類（spec.TRANSLUCENCY のキー）。"""
    t = container_transparency(container_material, transparency)
    return t if t in TRANSLUCENCY else None


def is_glass(container_material: str | None, transparency: str | None = None) -> bool:
    """容器が透明なガラス瓶か（すりガラスは半透明なので含めない）。"""
    m = (container_material or "").lower()
    return is_transparent(container_material, transparency) and any(k in m for k in GLASS_KEYWORDS)


def is_transparent(container_material: str | None, transparency: str | None = None) -> bool:
    """容器が透明か。半透明の容器は透明ではない。"""
    return container_transparency(container_material, transparency) == "transparent"


@dataclass
class BuildContext:
    spec: ProductSpec
    images: list[Path]
    preferred_image: int | None
    landmarks: Landmarks
    out_dir: Path
    debug_dir: Path
    blender: str
    faces: dict[str, int] | None = None  # 面 → 画像番号（vision.json の faces。回転体は top = 蓋の上面、side = 全周ラベル）


@dataclass
class BuildResult:
    usd_path: Path
    root_name: str
    mass: float
    center_of_mass: tuple[float, float, float]
    colliders: list[str]
    materials: dict[str, dict]  # Blender のマテリアル名 → 役割と見た目のパラメータ
    double_sided: list[str]
    meta: dict = field(default_factory=dict)
    static: bool = False  # 床に固定する什器（キネマティックな剛体にし、質量は付けない）
    physics_labels: list[str] = field(default_factory=lambda: ["plastic"])  # 物理マテリアルの意味ラベル
    # 可動部（組み合わせのみ）。[{name, parts, mass, center_of_mass, joint: {type, axis, anchor, limits}}]。
    # mass・center_of_mass は総質量のうちの可動部の分
    links: list[dict] = field(default_factory=list)
    # 内蔵の照明（組み合わせのみ）。spec.Light を dict にしたもの。center は平行移動したあとの座標
    lights: list[dict] = field(default_factory=list)


def _rdp(pts: np.ndarray, tol: float) -> np.ndarray:
    """Ramer–Douglas–Peucker でポリラインを間引く。"""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / (np.linalg.norm(ab) + 1e-12)
    i = int(np.argmax(d))
    if d[i] <= tol:
        return np.array([a, b])
    return np.vstack([_rdp(pts[: i + 1], tol)[:-1], _rdp(pts[i:], tol)])


def label_back_texture(tex: np.ndarray, show: float = LABEL_BACK_PRINT) -> np.ndarray:
    """ラベルの裏面のテクスチャ。白地に表の絵柄を show の濃さで重ねる（容器の内側から見ると鏡写しになる）。"""
    rgb = np.asarray(tex)[..., :3].astype(np.float32)
    back = np.asarray(LABEL_BACK_COLOR, np.float32) * (1 - show) + rgb * show
    return np.clip(back + 0.5, 0, 255).astype(np.uint8)


def _section(prof: RevolveProfile, z0: float, z1: float, dr: float = 0.0, r_min: float = 0.0005) -> list[list[float]]:
    """z0..z1 の区間を切り出し、半径を dr だけずらした (z, r) 列。"""
    zs = np.concatenate([[z0], prof.z[(prof.z > z0) & (prof.z < z1)], [z1]])
    rs = np.maximum(np.interp(zs, prof.z, prof.r) + dr, r_min)
    pts = _rdp(np.stack([zs, rs], 1), RDP_TOL)
    return pts.tolist()


# 輪郭の縦横比と寸法の縦横比のずれがこれを超える画像は、形を取るのに使わない
MAX_ASPECT_ERROR = 0.4


def _select_image(ctx: BuildContext) -> tuple[Path, np.ndarray, object] | None:
    """画像認識の選択を優先し、だめなら輪郭の品質スコアが最も高い画像を使う。"""
    scored = []
    order = list(range(len(ctx.images)))
    if ctx.preferred_image is not None:
        order.remove(ctx.preferred_image)
        order.insert(0, ctx.preferred_image)
    for i in order:
        rgb = np.asarray(Image.open(ctx.images[i]).convert("RGB"))
        try:
            sil = extract_silhouette(rgb)
        except ValueError:
            continue
        q = sil.quality(rgb.shape)
        # 輪郭の縦横比が寸法と大きく違う画像は、側面の全体像ではない（ラベルの拡大、斜めからの写真など）
        dims = ctx.spec.dimensions
        aspect = (sil.height_px / (2 * sil.radius.max())) / (dims.height / dims.diameter)
        if abs(aspect - 1) > MAX_ASPECT_ERROR:
            log.info("画像 %s: 縦横比が寸法と %.0f%% 違うので使いません", ctx.images[i].name, abs(aspect - 1) * 100)
            q = 0.0
        log.info("画像 %s: 品質 %.3f", ctx.images[i].name, q)
        if i == ctx.preferred_image and q > 0:
            return ctx.images[i], rgb, sil
        scored.append((q, i, rgb, sil))
    scored = [s for s in scored if s[0] > 0]
    if not scored:
        return None
    q, i, rgb, sil = max(scored, key=lambda s: s[0])
    return ctx.images[i], rgb, sil


def make_lid_texture(rgb: np.ndarray, fill: str, diameter: float) -> np.ndarray:
    """蓋を真上から撮った画像を、蓋の円がちょうど収まる正方形にする。円の外は fill 色で塗る。

    一辺の画素数は蓋の直径 diameter [m] から決める（texres）。
    画像の下側が商品の正面（-Y）、右側が +X に貼られる。
    """
    from .pouch import trim_background  # pouch が revolve を import するので循環を避ける

    trimmed = trim_background(rgb)
    n = texture_px(diameter, min(trimmed.shape[:2]))
    out = np.asarray(Image.fromarray(trimmed).resize((n, n), Image.LANCZOS)).copy()
    v, u = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2
    out[(u - c) ** 2 + (v - c) ** 2 > (n / 2) ** 2] = [int(fill[i:i + 2], 16) for i in (1, 3, 5)]
    return out


def _mass_properties(prof: RevolveProfile, total_mass: float | None, capacity_ml: float | None,
                     wall: float = WALL, top: float | None = None, y_scale: float = 1.0,
                     square: float | None = None, bottom: float | None = None,
                     density: float | None = None) -> tuple[float, float]:
    """中身と容器の質量配分から重心高さを求める。戻り値は (質量, 重心 z)。

    中身は底の内面（bottom、既定は wall）から top（既定は液面、不明ならキャップ下端の 8 割）まで一様に詰まっているとみなす。
    total_mass が None なら、内容積から中身の質量を見積もり、容器分を足す。容器の密度 density があれば
    容器分は 表面積 × 肉厚（底は bottom）× 密度（ガラス瓶は重い）、なければ中身の 4%。
    """
    bottom = bottom or wall
    top = top or prof.liquid_top_z or prof.cap_z * 0.8
    zs = np.linspace(bottom, top, 200)
    rs = np.maximum(np.interp(zs, prof.z, prof.r) - wall, 0)
    dv = np.pi * rs**2 * y_scale
    if square and square != 2:
        # 超楕円の面積 ÷ 円の面積（角に近い太い部分だけ。首の細い部分も同じ倍率で近似）
        from math import gamma
        dv = dv * 4 * gamma(1 + 1 / square) ** 2 / gamma(1 + 2 / square) / np.pi
    vol = np.trapezoid(dv, zs)
    z_liq = np.trapezoid(dv * zs, zs) / vol if vol > 0 else top / 2
    m_liq = (capacity_ml * 1e-6 if capacity_ml else vol) * LIQUID_DENSITY
    # 容器は表面積で重み付け（底の円板は z = 0）
    da = 2 * np.pi * prof.r
    side = float(np.trapezoid(da, prof.z))
    z_side = float(np.trapezoid(da * prof.z, prof.z)) / side
    if density:
        m_side = side * wall * density
        m_bottom = np.pi * prof.r[0] ** 2 * bottom * density
        m_glass = m_side + m_bottom
        z_cont = (m_side * z_side + m_bottom * bottom / 2) / m_glass
    else:
        z_cont = z_side
    if total_mass is None:
        total_mass = m_liq + m_glass if density else m_liq * 1.04
    m_liq = min(m_liq, total_mass * 0.97)
    m_cont = total_mass - m_liq
    return total_mass, float((m_liq * z_liq + m_cont * z_cont) / total_mass)


class RevolveBuilder:
    def build(self, ctx: BuildContext) -> BuildResult:
        spec = ctx.spec
        dims = spec.dimensions
        spec_colors = {"cap": spec.colors.cap, "liquid": spec.colors.liquid, "label_base": spec.colors.label_base}
        tex_dir = ctx.out_dir / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        ctx.debug_dir.mkdir(parents=True, exist_ok=True)
        meta: dict = {}

        picked = _select_image(ctx) if ctx.images else None
        if picked:
            img_path, rgb, sil = picked
            # 側面の展開図が別にあるとき（架空の商品など）は、この画像は形を取るだけで、色は合わせない
            side = (ctx.faces or {}).get("side")
            from_photo = side is None or not 0 <= side < len(ctx.images)
            prof = build_profile(rgb, sil, dims, ctx.landmarks, spec_colors, match_image=from_photo)
            cv2.imwrite(str(ctx.debug_dir / "silhouette.png"), draw_debug(rgb, sil, prof))
            meta["image"] = str(img_path)
        else:
            prof = parametric_profile(dims, spec_colors)
            meta["image"] = None
        meta["warnings"] = prof.warnings
        for w in prof.warnings:
            log.warning(w)

        transparent = is_transparent(spec.container_material, spec.transparency)
        translucent = translucency(spec.container_material, spec.transparency)
        glass = is_glass(spec.container_material, spec.transparency)
        see_through = transparent or bool(translucent)  # 中身が見える
        wall = GLASS_WALL if glass else WALL if transparent else TRANSLUCENT_WALL if translucent else OPAQUE_WALL
        bottom = GLASS_BOTTOM if glass else wall  # 底の厚み
        # dimensions.depth が直径より小さければ、胴の断面を楕円にする（横幅 = diameter、奥行き = depth）
        y_scale = 1.0
        if dims.depth and dims.depth < dims.diameter * 0.98:
            y_scale = dims.depth / dims.diameter
        if not see_through:
            # 不透明容器は中が見えないので液体を作らない
            prof.liquid_top_z = None
            prof.colors["liquid"] = None

        H = prof.height
        neck_r = prof.radius_at(prof.cap_z - 0.001)
        neck_top = prof.cap_z + 0.6 * (H - prof.cap_z)
        above = prof.r[prof.z > prof.cap_z]
        cap_r = float(np.percentile(above, 90)) if len(above) else neck_r
        if cap_r < 0.8 * neck_r:
            # 乾電池の +極のように胴よりはっきり細いキャップ。胴は平らな肩で閉じ、キャップは輪郭どおりの太さにする
            cap_pts = [[z, min(r, cap_r)] for z, r in _section(prof, prof.cap_z, H)]
            body_pts = _section(prof, 0.0, prof.cap_z) + [[prof.cap_z, cap_r * 0.92], [neck_top, cap_r * 0.92]]
        else:
            # ボトルの口のように首を覆うキャップ。首より少し太くして、首の延長をキャップの中に隠す。
            # リップのように胴とキャップが同じ太さなら、胴の最大径は超えない
            cap_pts = _section(prof, prof.cap_z, H, r_min=min(neck_r + 0.0005, float(prof.r.max())))
            body_pts = _section(prof, 0.0, prof.cap_z) + [[neck_top, min(neck_r, cap_pts[0][1]) * 0.92]]

        body_labels = container_labels(spec.container_material)
        metal = "metal" in body_labels  # 缶（アルミ・スチール・ブリキ）
        parts: dict[str, dict] = {"Body": {"points": body_pts}, "Cap": {"points": cap_pts}}
        narrow_cap = cap_r < 0.8 * neck_r
        can = not narrow_cap and details.is_can(cap_pts, body_pts, metal)
        knurl = not narrow_cap and not can and details.is_screw_cap(cap_pts, body_pts, metal)
        if can:
            # 上面は巻き締めの縁の内側がくぼみ、底は中央が持ち上がる。胴はくぼみの中に見えないよう縁の下端で止める
            recess = details.can_top_recess(cap_pts)
            parts["Cap"].update(top=recess, bottom=details.can_cap_bottom(cap_pts, recess))
            parts["Body"] = {"points": _section(prof, 0.0, prof.cap_z),
                             "bottom": details.can_bottom_dome(body_pts, 2 * float(prof.r.max()))}
        liquid_color = prof.colors.get("liquid")
        if prof.liquid_top_z:
            inset = wall * LIQUID_INSET
            parts["Liquid"] = {"points": _section(prof, bottom - inset, prof.liquid_top_z, dr=-inset)}

        if glass:
            body_mat = {"name": "GlassMat", "role": "glass", "color": GLASS_COLOR, "ior": GLASS_IOR,
                        "thin_walled": GLASS_THIN_WALLED, "labels": body_labels}
        elif transparent:
            body_mat = {"name": "PET", "role": "pet", "color": PET_COLOR, "labels": body_labels}
        elif translucent:
            clarity, rough = TRANSLUCENCY[translucent]
            body_mat = {"name": "ContainerMat", "role": "translucent", "clarity": clarity, "roughness": rough,
                        "color": prof.colors.get("label_base") or TRANSLUCENT_COLOR, "labels": body_labels}
        else:
            body_mat = {"name": "ContainerMat", "role": "container",
                        "color": prof.colors.get("label_base") or "#F4F4F2", "metallic": 1.0 if metal else 0.0,
                        "labels": body_labels}
        cap_labels = ["metal"] if metal else ["plastic"]
        materials = {
            "Body": body_mat,
            "Cap": {"role": "cap", "color": prof.colors.get("cap") or "#DDDDDD", "labels": cap_labels},
        }
        if "Liquid" in parts:
            # 無色の液体は水として扱う
            # 色の付いた液体は、胴の中心を通る光（内径ぶん）がちょうど液体の色になるように吸収させる。
            # 濁った液体（ジュース・乳飲料など）は、さらに光を散乱させる（散乱係数は 1/m）
            liq_r = max(r for _, r in parts["Liquid"]["points"])
            liq_d = liq_r * (1 + y_scale)
            turbidity = spec.colors.liquid_turbidity
            if turbidity is None:
                turbidity = liquid_turbidity(spec.product_name, spec.tags)
            turbidity = min(max(float(turbidity), 0.0), 1.0)
            materials["Liquid"] = {"role": "liquid", "color": liquid_color or "#FFFFFF",
                                   "transmission": 0.6 if liquid_color else 1.0, "labels": LIQUID,
                                   "absorption_depth": round(liq_d, 5) if liquid_color or turbidity else 0.0}
            if turbidity:
                materials["Liquid"].update(turbidity=turbidity, anisotropy=TURBID_ANISOTROPY,
                                           scattering=round(TURBID_TAU * turbidity**2.5 / liq_d, 3))
            if translucent and turbidity >= TRANSLUCENT_TURBID:
                body_mat["diffuse_transmission"] = 1.0
        double_sided = ["Body"]
        if knurl:
            # ねじキャップの側面の縦の溝（法線マップ）。上面は溝を付けないので別のマテリアルにする
            nmap, px_per_m = details.knurl_normal_map(cap_pts)
            Image.fromarray(nmap).save(tex_dir / "cap_normal.png")
            record(meta, "cap_normal.png", nmap.shape[1::-1], px_per_m, 1.0)
            materials["Cap"]["maps"] = {"normal": "./textures/cap_normal.png"}
            materials["CapTop"] = {"role": "cap", "color": materials["Cap"]["color"], "labels": cap_labels}

        top = (ctx.faces or {}).get("top")
        if top is not None:
            if 0 <= top < len(ctx.images):
                lid_d = 2 * max(r for _, r in cap_pts)
                tex = make_lid_texture(np.asarray(Image.open(ctx.images[top]).convert("RGB")), materials["Cap"]["color"], lid_d)
                tex_path = tex_dir / "cap_top.png"
                Image.fromarray(tex).save(tex_path)
                record(meta, "cap_top.png", tex.shape[1::-1], tex.shape[1], lid_d)
                materials["CapTop"] = {"role": "cap", "color": materials["Cap"]["color"], "labels": cap_labels,
                                       "texture": str(tex_path.resolve()), "texture_rel": "./textures/cap_top.png"}
                meta["cap_top_image"] = str(ctx.images[top])
            else:
                meta["warnings"].append(f"蓋の上面の画像番号 {top} がありません")

        side = (ctx.faces or {}).get("side")  # 展開済みの全周ラベル画像（任意）
        if side is not None and not 0 <= side < len(ctx.images):
            meta["warnings"].append(f"全周ラベルの画像番号 {side} がありません")
            side = None
        if prof.label_z and (picked or side is not None):
            if side is not None:
                tex = wrap_texture(np.asarray(Image.open(ctx.images[side]).convert("RGB")), prof)
                meta["label_image"] = str(ctx.images[side])
            else:
                tex = make_label_texture(rgb, sil, prof)
            tex_path = tex_dir / "label.png"
            Image.fromarray(tex).save(tex_path)
            record(meta, "label.png", tex.shape[1::-1], tex.shape[1], label_circumference(prof))
            z0, z1 = prof.label_z
            parts["Label"] = {"points": _section(prof, z0, z1, dr=LABEL_OFFSET)}
            materials["Label"] = {"role": "label", "texture": str(tex_path.resolve()), "texture_rel": "./textures/label.png",
                                  "labels": ["plastic"] if see_through else body_labels}  # 透明ボトルのラベルはフィルム
            if metal and not see_through:
                materials["Label"]["metallic"] = 1.0  # 缶は金属に直接印刷する。インクの濃い所は金属度マップで下げる
            double_sided.append("Label")
            if see_through:
                # 容器越しに見えるラベルの裏面。容器の表面とラベルの間に内向きの面を置き、表の絵柄が裏から透けて見えないようにする
                back_path = tex_dir / "label_back.png"
                Image.fromarray(label_back_texture(tex)).save(back_path)
                parts["LabelBack"] = {"points": _section(prof, z0, z1, dr=LABEL_OFFSET / 2)}
                materials["LabelBack"] = {"role": "label", "texture": str(back_path.resolve()),
                                          "texture_rel": "./textures/label_back.png", "labels": ["plastic"]}

        known = spec.mass_kg or spec.capacity_ml
        # 不透明容器の中身は蓋の下端まで詰まっているとみなす
        mass, com_z = _mass_properties(prof, spec.total_mass_kg() if known else None, spec.capacity_ml, wall,
                                       top=None if see_through else prof.cap_z, y_scale=y_scale, square=dims.square,
                                       bottom=bottom, density=GLASS_DENSITY if glass else None)
        com = (0.0, 0.0, com_z)
        colliders = ["Body", "Cap"]
        extra: dict = {}
        if y_scale != 1.0:
            extra["y_scale"] = y_scale
        if dims.square and dims.square != 2:
            extra["square"] = dims.square
            extra["square_r"] = max(r for _, r in body_pts)  # この半径で角が最も立ち、首に向かって丸に戻る
        if dims.lobes:
            extra["lobes"] = dims.lobes
        expected = None
        if spec.parts:
            from .assembly import attach_parts  # assembly が revolve を import するので循環を避ける

            rx = max(r for pts in (body_pts, cap_pts) for _, r in pts)
            ry = max(max(r for _, r in body_pts) * y_scale, max(r for _, r in cap_pts))
            att = attach_parts(ctx, (-rx, -ry, 0.0), (rx, ry, H), set(parts), meta["warnings"], tex_dir)
            extra.update(objects=att["objects"], extra_materials=att["materials"], shift=att["shift"].tolist())
            com = tuple(float(c) for c in np.asarray(com) + att["shift"])
            colliders += att["colliders"]
            expected = att["size"]
            if att["textures"]:
                meta.setdefault("textures", {}).update(att["textures"])
            if att["images"]:
                meta["part_images"] = att["images"]
        usd_path = ctx.out_dir / f"{spec.slug}.usd"
        build = {
            "root_name": spec.slug,
            "segments": SEGMENTS,
            "wall_thickness": wall,
            **({"bottom_thickness": bottom} if bottom > wall else {}),
            "parts": parts,
            "materials": materials,
            "usd_path": str(usd_path.resolve()),
            "blend_path": str((ctx.debug_dir / "model.blend").resolve()),
            **extra,
        }
        build_json = ctx.debug_dir / "build.json"
        build_json.write_text(json.dumps(build, ensure_ascii=False, indent=2))
        run_script(ctx.blender, "build_revolve.py", build_json.resolve(), log_path=ctx.debug_dir / "blender_build.log")

        meta.update(
            profile={"cap_z": prof.cap_z, "liquid_top_z": prof.liquid_top_z,
                     "label_z": prof.label_z, "transparent": transparent,
                     "transparency": container_transparency(spec.container_material, spec.transparency),
                     **({"glass": True} if glass else {}),
                     **({"turbidity": materials["Liquid"]["turbidity"]}
                        if materials.get("Liquid", {}).get("turbidity") else {}),
                     **({"translucent": translucent} if translucent else {}),
                     **({"can_ends": True} if can else {}), **({"knurl": True} if knurl else {}),
                     **({"y_scale": y_scale} if y_scale != 1.0 else {}),
                     **({"parts": [o["name"] for o in extra["objects"]], "expected_size": expected}
                        if spec.parts else {})},
            colors=prof.colors,
        )
        return BuildResult(
            usd_path=usd_path,
            root_name=spec.slug,
            mass=mass,
            center_of_mass=com,
            colliders=colliders,
            materials={
                body_mat["name"]: body_mat,
                "CapMat": materials["Cap"],
                **({"CapTopMat": materials["CapTop"]} if "CapTop" in materials else {}),
                **({"LiquidMat": materials["Liquid"]} if "Liquid" in materials else {}),
                **({"LabelMat": materials["Label"]} if "Label" in materials else {}),
                **({"LabelBackMat": materials["LabelBack"]} if "LabelBack" in materials else {}),
                **extra.get("extra_materials", {}),
            },
            double_sided=double_sided,
            meta=meta,
            physics_labels=body_labels,
        )
