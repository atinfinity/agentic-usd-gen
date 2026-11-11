"""生成済みのアセット（out/<slug>/）を、リポジトリで管理する形に書き出す。

    uv run agentic-usd-gen-export                      # out/ の検証 OK のアセットをすべて assets/ へ
    uv run agentic-usd-gen-export cup_noodle --recipes recipes

書き出し先の構成:
    assets/
      README.md                 一覧（サムネイル付き）
      catalog.json              全アセットの asset.json をまとめたもの
      catalog.usda              全アセットを並べて payload で読み込むステージ（見比べ用）
      <category>/<slug>/simready_usd/   SimReady の NP.005（<アセット名>/<中間フォルダ>/<アセット名>.usd）に合わせる
        <slug>.usd              入口。payloads/<slug>_base.usd を参照する。customLayerData に SimReady_Metadata
        payloads/               Isaac Sim のレイヤー構成（SimReady の FET_100_ISAAC。isaac_layout.py）
          <slug>_base.usd       physics と meshes を重ねる
          <slug>_meshes.usd     形状・マテリアル。textures/ を ../ で始まる相対パスで参照
          <slug>_physics.usd    剛体・コリジョン・物理マテリアル・関節
        textures/
        thumbnail.png           512px 四方、背景透過
        .thumbs/256x256/<slug>.usd.png   Omniverse / Isaac Sim のブラウザ用サムネイル
        README.md               モデルカード
        asset.json              機械可読のメタデータ（version・content_hash・history を含む）
    recipes/<キャッシュ名>/      （--recipes 指定時）spec.json・vision.json・images/。
                                `uv run agentic-usd-gen "<商品名>" --cache recipes` で再生成できる

バージョン管理:
    USD とテクスチャの中身のハッシュを前回の asset.json と比べ、変わったときだけ版を上げて history に記録する。
    外形が 1 mm 以上変わったら major、それ以外は minor を上げる（--bump で指定も可）。
    -m で変更内容を書ける（省略時は変わった項目から自動で作る）。版は USD の assetInfo.version にも書く。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdSemantics, Vt

from .blender_runner import find_blender, run_script
from .isaac_layout import split_layers
from .lighting import DEFAULT_VARIANT, VARIANT_SET, VARIANTS
from .picture import BLANK_SUFFIX as PICTURE_BLANK_SUFFIX
from .picture import DEFAULT_VARIANT as PICTURE_DEFAULT
from .picture import VARIANT_SET as PICTURE_VARIANT_SET
from .picture import VARIANTS as PICTURE_VARIANTS
from .screen import DEFAULT_VARIANT as SCREEN_DEFAULT
from .screen import OFF_SUFFIX as SCREEN_OFF_SUFFIX
from .screen import VARIANT_SET as SCREEN_VARIANT_SET
from .screen import VARIANTS as SCREEN_VARIANTS
from .texdedupe import dedupe_textures, referenced_names
from .qcode import lookup as lookup_qcode
from .spec import CATEGORIES
from .physics_material import CONTACTS, DEFAULT
from .physics_material import SOURCE as PHYSICS_SOURCE

log = logging.getLogger("agentic_usd_gen.export")

THUMB_SIZE = 256
SIMREADY_DIR = "simready_usd"  # <category>/<slug>/ の下に USD を置く中間フォルダ
SHAPE_LABELS = {"revolve": "回転体", "pouch": "袋（ピロー包装）", "box": "箱", "assembly": "部品の組み合わせ"}
CATEGORY_LABELS = {"beverage": "飲料", "food": "食品", "household": "日用品", "fixture": "什器", "environment": "内装",
                   "uncategorized": "未分類"}
LIMITATIONS = {
    "revolve": [
        "側面写真の輪郭から作った回転体です。凹凸・くびれは回転対称に近似しています。",
        "ラベルは正面の写真から見える範囲だけを貼り、裏側はラベル地の色で塗っています。",
        "キャップ・蓋も輪郭から作った回転体で、ねじ山や細かい形は再現していません。",
    ],
    "pouch": [
        "平らなフィルム寸法と厚さから作った枕形です。中身の偏りやしわは再現していません。",
        "裏面には正面と同じ画像を貼っています。",
    ],
    "box": [
        "直方体です。角の丸み・開け口・フラップは再現していません。",
        "画像のない面はラベル地の単色で塗っています。",
    ],
    "assembly": [
        "直方体と円柱の部品を組み合わせた簡略形状です。角の丸み・ボタン・配線・内部構造は再現していません。",
        "画像は指定した部品の面にだけ貼り、それ以外は単色で塗っています。",
        "重心は部品が中身の詰まった一様な物体だとして求めています。",
    ],
}


# 書き出すアセットのライセンス（SPDX 識別子 → 表示名・本文の URL）
LICENSES = {
    "CC0-1.0": ("CC0 1.0 全世界 パブリック・ドメイン提供", "https://creativecommons.org/publicdomain/zero/1.0/deed.ja"),
    "CC-BY-4.0": ("クリエイティブ・コモンズ 表示 4.0 国際", "https://creativecommons.org/licenses/by/4.0/deed.ja"),
}


def package_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("agentic-usd-gen")
    except PackageNotFoundError:
        return "unknown"


def package_author() -> str:
    """pyproject の authors の名前（メールアドレスは書かない）。"""
    from importlib.metadata import PackageNotFoundError, metadata

    try:
        m = metadata("agentic-usd-gen")
    except PackageNotFoundError:
        return "unknown"
    name = m.get("Author") or (m.get("Author-email") or "").split(" <")[0]
    return name.strip() or "unknown"


def find_cache_dir(meta: dict) -> Path | None:
    if meta.get("cache_dir"):
        return Path(meta["cache_dir"])
    used = meta.get("image_used")
    if isinstance(used, dict):  # 箱は面ごとの画像
        used = next(iter(used.values()), None)
    return Path(used).parents[1] if used else None  # cache/<キー>/images/NN.png


def resolve_category(meta: dict, cache_dir: Path | None) -> str:
    """cache の spec.json（あとから書き足せる）→ meta の spec → 容量の有無から推定、の順。"""
    spec_path = cache_dir / "spec.json" if cache_dir else None
    if spec_path and spec_path.exists():
        cat = json.loads(spec_path.read_text()).get("category")
        if cat:
            return cat
    spec = meta["spec"]
    if spec.get("category"):
        return spec["category"]
    return "beverage" if spec.get("capacity_ml") else "uncategorized"


def resolve_tags(meta: dict, cache_dir: Path | None) -> list[str]:
    """cache の spec.json の tags（あとから書き足せる）→ meta の spec の tags の順。"""
    spec_path = cache_dir / "spec.json" if cache_dir else None
    if spec_path and spec_path.exists():
        tags = json.loads(spec_path.read_text()).get("tags")
        if tags:
            return [str(t) for t in tags]
    return list(meta["spec"].get("tags") or [])


def ensure_thumbnail(asset_dir: Path, usd_path: Path, blender: str | None) -> Path | None:
    thumb = asset_dir / "debug" / "thumbnail.png"
    if thumb.exists() and thumb.stat().st_mtime >= usd_path.stat().st_mtime:
        return thumb
    if blender is None:
        try:
            blender = find_blender()
        except FileNotFoundError as e:
            log.warning("%s: サムネイルを描画できません（%s）", usd_path.stem, e)
            return thumb if thumb.exists() else None
    log.info("%s: サムネイルを描画中…", usd_path.stem)
    run_script(blender, "render_preview.py", usd_path.resolve(), thumb.parent.resolve(), 64, "thumbnail",
               log_path=thumb.parent / "blender_thumbnail.log")
    return thumb


FIRST_VERSION = "1.0.0"
SIZE_TOL = 0.001  # 外形の変化をそれ以上とみなす量 [m]


CONTAINER_NOUNS = ("bottle", "can", "carton", "box", "jar", "cup", "pouch", "bag")
_NOT_CONTENT = {"alcohol", "fictional", "static"}
SLUG_BOTTLE = {"bottle", "pump"}
SLUG_PACKAGE = ("bag", "pouch", "box")


def _is_english(tag: str) -> bool:
    return bool(re.fullmatch(r"[ -~]+", tag)) and bool(re.search(r"[A-Za-z]", tag))


def _is_size(tag: str) -> bool:
    return bool(re.fullmatch(r"[\d.]+\s*(?:ml|l|kg|g|mm|cm|p)?", tag, re.IGNORECASE))


def container_phrases(asset: dict, extra: list[str]) -> list[str]:
    """飲料・食品と、日用品のボトルの「中身 + 容器」の英語の句（green tea bottle・bottled green tea・coffee can・
    canned coffee・shampoo bottle）。

    自然な英語の検索（"green tea bottle"）では主名詞の容器がタグにないと当たらないため。
    中身は spec.json の tags の最初の英語の語（材質・容量・容器だけの語は除く）、容器は tags の容器の語
    （"PET bottle" → bottle、"juice box" → box）か、回転体の材質（PET・ガラス → bottle / jar、金属 → can）、
    樹脂の回転体はスラッグの bottle・pump（→ bottle）、袋・箱の食品はスラッグの bag・pouch・box で決める。
    日用品はスラッグでボトルと分かるものだけ。
    分からないものには作らない。"""
    # 樹脂の回転体はカップやケースも多いので、ボトルとはスラッグ（mayonnaise_bottle・shampoo_pump）で見分ける
    slug_bottle = asset["shape_class"] == "revolve" and bool(SLUG_BOTTLE & set(asset["slug"].split("_")))
    if asset["category"] not in ("beverage", "food") and not (asset["category"] == "household" and slug_bottle):
        return []
    english = [t.strip() for t in extra if t and _is_english(t)]
    material = asset.get("container_material")
    container = next((t.split()[-1].lower() for t in english if t.split()[-1].lower() in CONTAINER_NOUNS), None)
    if asset["category"] == "household":
        container = "bottle"
    elif container is None and asset["shape_class"] == "revolve":
        if material in ("PET", "glass"):
            container = "jar" if "jar" in asset["slug"].split("_") else "bottle"
        elif material in ("aluminum", "steel"):
            container = "can"
        elif slug_bottle:
            container = "bottle"
    if container is None and asset["category"] == "food":
        # 袋・箱の食品も、スラッグ（potato_chips_bag・curry_roux_box）で容器が分かるものだけ。最後の語を使う
        container = next((w for w in reversed(asset["slug"].split("_")) if w in SLUG_PACKAGE), None)
    content = None
    for t in english:
        words = t.split()
        if (t.lower() in _NOT_CONTENT or t == material or _is_size(t)
                or words[-1].lower() in CONTAINER_NOUNS or t.lower() in ("pet",)):
            continue
        content = re.sub(r"^(?:canned|bottled)\s+", "", t, flags=re.IGNORECASE)
        break
    if not container or not content:
        return []
    phrases = [f"{content} {container}"]
    if container == "bottle" and asset["category"] == "beverage":
        phrases.append(f"bottled {content}")
    if container == "can":
        phrases.append(f"canned {content}")
    have = {t.lower() for t in extra}
    return [p for p in phrases if p.lower() not in have]


def asset_tags(asset: dict, extra: list[str]) -> list[str]:
    """検索用のタグ。カテゴリ・形状・容器の材質（英語の識別子と日本語）に spec.json の tags と、
    飲料・食品の「中身 + 容器」の英語の句（container_phrases）を足す。"""
    cat, shape = asset["category"], asset["shape_class"]
    tags = [cat, CATEGORY_LABELS.get(cat), shape, SHAPE_LABELS.get(shape), asset.get("container_material"), *extra,
            *container_phrases(asset, extra)]
    if asset["physics"].get("static"):
        tags.append("static")
    out: list[str] = []
    for t in tags:
        t = str(t).strip() if t else ""
        if t and t not in out:
            out.append(t)
    return out


def asset_description(a: dict) -> str:
    """一覧や検索結果に出す 1 文の説明（日本語）。"""
    size = " × ".join(_mm(v) for v in a["size_m"]) + " mm" if a["size_m"] else "外形不明"
    place = "天井" if a.get("mount") == "ceiling" else "床"
    kind = f"{place}に固定する什器" if a["physics"].get("static") else "剛体"
    return (f"{a['name']}（{CATEGORY_LABELS.get(a['category'], a['category'])}）の 3D モデル。"
            f"{SHAPE_LABELS.get(a['shape_class'], a['shape_class'])}、外形 {size}（幅 × 奥行き × 高さ）、"
            f"質量 {a['mass_kg']:.3f} kg、{kind}。")


def metadata_hash(asset: dict) -> str:
    """USD に書き込む検索用メタデータ（名前・タグ・説明・カテゴリ）の SHA-256。"""
    keys = ("name", "category", "tags", "description", "qcode")
    return hashlib.sha256(json.dumps({k: asset.get(k) for k in keys}, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()


def content_hashes(usd_path: Path, tex_dir: Path) -> dict[str, str]:
    """USD とテクスチャそれぞれの中身の SHA-256（テクスチャはファイル名込み）。"""
    tex = hashlib.sha256()
    if tex_dir.is_dir():
        for f in sorted(tex_dir.rglob("*")):
            if f.is_file():
                tex.update(f.relative_to(tex_dir).as_posix().encode() + b"\0" + f.read_bytes())
    return {"usd": hashlib.sha256(usd_path.read_bytes()).hexdigest(), "textures": tex.hexdigest()}


def bump_version(version: str, part: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def describe_changes(prev: dict, cur: dict) -> list[str]:
    """前回の asset.json からの変更点（人が読む短い文）。"""
    out = []
    old_h, new_h = prev.get("content_hash") or {}, cur["content_hash"]
    if old_h.get("usd") != new_h["usd"]:
        out.append("形状・マテリアル（USD）を更新")
    if old_h.get("textures") != new_h["textures"]:
        out.append("テクスチャを更新")
    if old_h.get("metadata") != new_h.get("metadata"):
        out.append("検索用メタデータ（タグ・説明）を更新")
    if prev.get("size_m") and cur["size_m"] and prev["size_m"] != cur["size_m"]:
        out.append("外形 " + " × ".join(_mm(v) for v in prev["size_m"]) + " → "
                   + " × ".join(_mm(v) for v in cur["size_m"]) + " mm")
    if prev.get("mass_kg") is not None and abs(prev["mass_kg"] - cur["mass_kg"]) > 1e-6:
        out.append(f"質量 {prev['mass_kg']:.3f} → {cur['mass_kg']:.3f} kg")
    if prev.get("shape_class") != cur["shape_class"]:
        out.append(f"形状クラス {prev.get('shape_class')} → {cur['shape_class']}")
    old_c, new_c = prev.get("physics", {}).get("colliders"), cur["physics"]["colliders"]
    if old_c is not None and old_c != new_c:
        out.append(f"コリジョン {', '.join(old_c)} → {', '.join(new_c)}")
    old_a, new_a = prev.get("physics", {}).get("collision"), cur["physics"]["collision"]
    if old_a is not None and old_a != new_a:
        out.append(f"コリジョンの近似 {old_a} → {new_a}")
    if prev.get("category") != cur["category"]:
        out.append(f"カテゴリ {prev.get('category')} → {cur['category']}")
    if prev.get("front") != cur.get("front"):
        out.append(f"正面の向き（front）を {cur.get('front')} に設定" if prev.get("front") is None
                   else f"正面の向き（front） {prev['front']} → {cur.get('front')}")
    return out


def apply_version(asset: dict, prev: dict | None, message: str | None, bump: str) -> bool:
    """asset に version・history を入れる。版を上げたら True。"""
    date = asset["generated_at"]
    if prev is None or "version" not in prev:
        asset["version"] = FIRST_VERSION
        asset["history"] = [{"version": FIRST_VERSION, "date": date, "changes": [message or "初版"]}]
        return True
    asset["history"] = prev.get("history", [])
    if prev.get("content_hash") == asset["content_hash"] and prev.get("front") == asset.get("front"):
        asset["version"] = prev["version"]
        # 中身が同じなら生成日時も前回のまま（再生成しただけで日付が動かないように）
        asset["generated_at"] = prev.get("generated_at", date)
        return False
    if bump == "auto":
        moved = (not prev.get("size_m") or not asset["size_m"]
                 or any(abs(a - b) >= SIZE_TOL for a, b in zip(prev["size_m"], asset["size_m"])))
        bump = "major" if moved else "minor"
    asset["version"] = bump_version(prev["version"], bump)
    changes = ([message] if message else []) + describe_changes(prev, asset)
    asset["history"] = [{"version": asset["version"], "date": date, "changes": changes}] + asset["history"]
    return True


def write_usd_metadata(usd_path: Path, asset: dict) -> None:
    """書き出し先の USD のルート Prim に版・名前・カテゴリ・タグ・説明とセマンティックラベルを書く。

    - assetInfo: version・name（slug）に加え、displayName（日本語名）・category・tags・description
    - prim の displayName と documentation（Isaac Sim / Omniverse の UI に出る）
    - セマンティックラベル（Isaac Sim の Replicator と USD Search の検索対象）:
      旧形式 semantic:<inst>:params:semanticType/semanticData（class = カテゴリ、tag = 各タグ、name = 日本語名）と、
      新形式 UsdSemantics.LabelsAPI（semantics:labels:class / :tag）
    """
    # 同じプロセスで前に開いたレイヤーが残っていると、消して置き直したファイルではなく古い内容を使ってしまう
    old = Sdf.Layer.Find(str(usd_path))
    if old:
        old.Reload(force=True)
    stage = Usd.Stage.Open(str(usd_path))
    prim = stage.GetDefaultPrim()
    model = Usd.ModelAPI(prim)
    model.SetAssetVersion(asset["version"])
    prim.SetAssetInfoByKey("displayName", asset["name"])
    prim.SetAssetInfoByKey("category", asset["category"])
    prim.SetAssetInfoByKey("tags", Vt.StringArray(asset["tags"]))
    prim.SetAssetInfoByKey("description", asset["description"])
    if asset.get("license"):
        prim.SetAssetInfoByKey("license", asset["license"])
    prim.SetDisplayName(asset["name"])
    prim.SetDocumentation(asset["description"])

    labels = [("class", asset["category"])] + [("tag", t) for t in asset["tags"]] + [("name", asset["name"])]
    for i, (kind, data) in enumerate(labels):
        inst = "Semantics" if i == 0 else f"Semantics_{i}"
        prim.CreateAttribute(f"semantic:{inst}:params:semanticType", Sdf.ValueTypeNames.String,
                             custom=False).Set(kind)
        prim.CreateAttribute(f"semantic:{inst}:params:semanticData", Sdf.ValueTypeNames.String,
                             custom=False).Set(data)
    for kind in ("class", "tag"):
        values = [d for k, d in labels if k == kind]
        UsdSemantics.LabelsAPI.Apply(prim, kind).CreateLabelsAttr().Set(Vt.TokenArray(values))
    layer = stage.GetRootLayer()
    layer.customLayerData = {**layer.customLayerData, "SimReady_Metadata": simready_metadata(stage, asset)}
    layer.Save()


def simready_metadata(stage: Usd.Stage, asset: dict) -> dict:
    """SimReady の SR.004（出所のメタデータ）。ルートレイヤーの customLayerData に書く。"""
    rigid = sum(1 for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI))
    size = asset.get("size_m")
    if not size:
        r = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeWorldBound(
            stage.GetDefaultPrim()).ComputeAlignedRange()
        size = list(r.GetSize()) if not r.IsEmpty() else [0.0, 0.0, 0.0]
    return {
        "author": asset["author"],
        "asset_name": asset["slug"],
        "asset_type": "prop",
        "asset_license": asset.get("license") or "proprietary",
        "category": asset["category"],
        "source_file": asset["source_file"],
        "usd_date_generated": asset["generated_at"][:10],
        "qcode": asset["qcode"],
        "rigid_body_count": rigid,
        "asset_extents": Gf.Vec3f(*size),
        "mass": float(asset["mass_kg"]),
        "version": asset["version"],
    }


SHAPE_KEYS = ("square", "lobes")  # dimensions のうち長さでない形の指定（角形の断面・花形の底）


def _mm(v: float) -> str:
    return f"{v * 1000:.1f}"


def build_asset_json(meta: dict, slug: str, category: str, usd_mtime: float) -> dict:
    spec = meta["spec"]
    info = meta["validation"]["info"]
    lo, hi = info.get("bbox_min"), info.get("bbox_max")
    size = [round(h - l, 5) for l, h in zip(lo, hi)] if lo and hi else None
    return {
        "slug": slug,
        "name": meta["product_name"],
        "category": category,
        "shape_class": spec["shape_class"],
        "orientation": spec.get("orientation", "upright"),
        **({"mount": spec["mount"]} if spec.get("mount", "floor") != "floor" else {}),  # 天井付けなど（spec.MOUNTS）
        "usd": f"{slug}.usd",
        "thumbnail": "thumbnail.png",
        "size_m": size,  # バウンディングボックスの X（幅）× Y（奥行き）× Z（高さ）
        "dimensions_m": {k: v for k, v in spec["dimensions"].items() if k not in SHAPE_KEYS},
        **({"shape_options": opts} if (opts := {k: v for k, v in spec["dimensions"].items()
                                                if k in SHAPE_KEYS and v is not None}) else {}),
        **({"dimensions_scope": "body"}  # 回転体・袋・箱に部品を足したとき、dimensions は本体だけの寸法
           if spec.get("parts") and spec["shape_class"] != "assembly" else {}),
        "mass_kg": meta["mass_kg"],
        "center_of_mass_m": meta["center_of_mass"],
        "container_material": spec.get("container_material"),
        "capacity_ml": spec.get("capacity_ml"),
        "physics": {
            "enabled": meta.get("physics", True),
            "static": meta.get("static", False),
            **_collision(info),
            **_contact(meta),
            **({"joints": meta["joints"]} if meta.get("joints") else {}),
        },
        **({"lighting": _lighting(spec["lights"])} if spec.get("lights") else {}),
        **({"screen": _screen(meta["screens"], spec.get("screen_places"))} if meta.get("screens") else {}),
        **({"picture": _picture(meta["pictures"], spec.get("picture_places"))} if meta.get("pictures") else {}),
        # 部品の出し入れのバリアント（育ち具合など）。セット → 値のリストと既定
        **({"variants": {k: {"variants": v["variants"], "default": v["default"]} for k, v in meta["variants"].items()}}
           if meta.get("variants") else {}),
        "sources": spec.get("sources", []),
        "image_sources": [c["url"] for c in spec.get("image_candidates", [])],
        "fictional": bool(spec.get("fictional", False)),
        "image_credits": spec.get("image_credits", []),
        "notes": spec.get("notes"),
        "warnings": meta.get("warnings", []),
        "generated_at": datetime.fromtimestamp(usd_mtime, timezone.utc).isoformat(timespec="seconds"),
        "generator": {"tool": f"agentic-usd-gen {package_version()}", "model": meta.get("model")},
    }


def _collision(info: dict) -> dict:
    """コリジョンの部品と近似方法。collision は全部品が同じならその方法、混在なら mixed。"""
    names = [c.rsplit("/", 1)[-1] for c in info.get("colliders", [])]
    approx = {n: (info.get("collision_approximations") or {}).get(n, "convexHull") for n in names}
    kinds = set(approx.values())
    return {"collision": kinds.pop() if len(kinds) == 1 else "mixed", "colliders": names,
            **({"collision_approximations": approx} if len(kinds) > 1 or kinds != {"convexHull"} else {})}


def _collision_text(phys: dict) -> str:
    approx = phys.get("collision_approximations")
    if not approx or phys["collision"] != "mixed":
        return f"コリジョン {phys['collision']}（{', '.join(phys['colliders'])}）"
    return "コリジョン " + ", ".join(f"{n}: {a}" for n, a in approx.items())


def _lighting(lights: list[dict]) -> dict:
    """内蔵の照明（lighting.py）。ルートの Lighting バリアントで切り替える。"""
    return {"variant_set": VARIANT_SET, "variants": list(VARIANTS), "default": DEFAULT_VARIANT,
            "lights": [{"name": x["name"], "type": "RectLight", "intensity_nits": x["intensity"],
                        "kelvin": x["kelvin"]} for x in lights]}


def _lighting_text(lighting: dict) -> str:
    kelvins = "・".join(f"{k:g} K" for k in sorted({x["kelvin"] for x in lighting["lights"]}))
    return (f"RectLight {len(lighting['lights'])} 個（{kelvins}）。`{lighting['variant_set']}` バリアント"
            f"（{' / '.join(lighting['variants'])}、既定 {lighting['default']}）で切り替え")


def _screen(screens: list[dict], places: list[str] | None = None) -> dict:
    """光る画面（screen.py）。ルートの Screen バリアントで On（画像を映す）・Off（消えた液晶）を切り替える。

    places は映す画像が合う場所の種類（ワールドを組むツールが使う部屋の種類。"any" はどこでも＝誘導灯）。無ければ店向け。"""
    return {"variant_set": SCREEN_VARIANT_SET, "variants": list(SCREEN_VARIANTS), "default": SCREEN_DEFAULT,
            "materials": [{"name": x["material"], "image": x["image"], "off": x["material"] + SCREEN_OFF_SUFFIX}
                          for x in screens],
            **({"places": list(places)} if places else {})}


def _screen_text(screen: dict) -> str:
    names = ", ".join(f"`{x['name']}`" for x in screen["materials"])
    return (f"画面 {len(screen['materials'])} 面（{names}）。`{screen['variant_set']}` バリアント"
            f"（On = 画像を映す / Off = 消えた画面、既定 {screen['default']}）で切り替え"
            + (f"。合う場所 {', '.join(screen['places'])}" if screen.get("places") else ""))


def _picture(pictures: list[dict], places: list[str] | None) -> dict:
    """店向けの絵柄（picture.py）。ルートの Picture バリアントで Default（絵柄）・Blank（無地）を切り替える。

    places は絵柄が合う場所の種類（ワールドを組むツールが使う部屋の種類）。ほかの場所では Blank にするか画像を差し替える。
    text・lang・audience は絵柄に書いた文字・言語・客層（agentic-usd-gen-fictional の看板。fictional/base.py）。"""
    return {"variant_set": PICTURE_VARIANT_SET, "variants": list(PICTURE_VARIANTS), "default": PICTURE_DEFAULT,
            "off": PICTURE_VARIANTS[1],
            "materials": [{"name": x["material"], "image": x["image"], "off": x["material"] + PICTURE_BLANK_SUFFIX,
                           "blank_image": x["blank_image"],
                           **{k: x[k] for k in ("text", "lang", "audience") if x.get(k)}} for x in pictures],
            **({"places": list(places)} if places else {})}


def _picture_text(picture: dict) -> str:
    names = ", ".join(f"`{x['name']}`" for x in picture["materials"])
    places = f"。合う場所 {', '.join(picture['places'])}" if picture.get("places") else ""
    words = [" / ".join(x["text"][:3]).replace("|", "/") for x in picture["materials"] if x.get("text")]
    places += f"。文字「{'」「'.join(words)}」" if words else ""
    return (f"絵柄 {len(picture['materials'])} 面（{names}）。`{picture['variant_set']}` バリアント"
            f"（Default = 店向けの絵柄 / Blank = 無地、既定 {picture['default']}）で切り替え{places}")


JOINT_KINDS = {"revolute": ("回転", "°"), "prismatic": ("スライド", " m")}


def _joints_text(joints: list[dict]) -> str:
    out = []
    for j in joints:
        kind, unit = JOINT_KINDS[j["type"]]
        rng = "限界なし（回り続ける）" if j.get("limits") is None else f"{j['limits'][0]:g}〜{j['limits'][1]:g}{unit}"
        out.append(f"{j['link']}: {kind}（{j['axis']} 軸、{rng}、{j['mass']:g} kg）")
    return "、".join(out)


def _contact(meta: dict) -> dict:
    """physics の摩擦・反発。最初の物理マテリアル（主な部品）の値を代表にし、素材ごとの一覧を materials に入れる。"""
    mats = meta.get("physics_materials") or []
    if not mats:  # 物理マテリアルを素材ごとに分ける前に作ったアセット
        c = CONTACTS[DEFAULT]
        return {"static_friction": c.static_friction, "dynamic_friction": c.dynamic_friction,
                "restitution": c.restitution}
    keys = ("static_friction", "dynamic_friction", "restitution")
    return {**{k: mats[0][k] for k in keys}, "materials": mats, "friction_source": PHYSICS_SOURCE}


def _contact_text(phys: dict) -> str:
    mats = phys.get("materials") or [{"material": None, "colliders": [], **phys}]
    parts = []
    for m in mats:
        head = f"{m['material']}（{', '.join(m['colliders'])}）: " if len(mats) > 1 else (
            f"{m['material']}: " if m.get("material") else "")
        parts.append(f"{head}静止摩擦 {m['static_friction']} / 動摩擦 {m['dynamic_friction']} / "
                     f"反発 {m['restitution']}")
    return "；".join(parts)


def _front_text(front: str | float | None) -> str:
    if front is None:
        return "—"
    return f"`{front}`" if isinstance(front, str) else f"+X から {front:g}°"


def model_card(a: dict) -> str:
    dims = a["dimensions_m"]
    size = " × ".join(_mm(v) for v in a["size_m"]) + " mm" if a["size_m"] else "不明"
    phys = a["physics"]
    rows = [
        ("slug", f"`{a['slug']}`"),
        ("バージョン", a.get("version", "—")),
        ("カテゴリ", f"{CATEGORY_LABELS.get(a['category'], a['category'])}（`{a['category']}`）"),
        ("形状", f"{SHAPE_LABELS.get(a['shape_class'], a['shape_class'])}（`{a['shape_class']}`）"
                 + ("、寝かせた向き" if a["orientation"] == "lying" else "")),
        ("外形（幅 × 奥行き × 高さ）", size),
        ("正面の向き", _front_text(a.get("front"))),
        ("本体の寸法（部品を除く）" if a.get("dimensions_scope") == "body" else "元の寸法", "、".join(f"{k} {_mm(v)} mm" for k, v in dims.items() if v)),
        ("質量", f"{a['mass_kg']:.3f} kg"),
        ("重心", "(" + ", ".join(_mm(v) for v in a["center_of_mass_m"]) + ") mm"),
        ("容器の材質", a["container_material"] or "—"),
    ]
    if a.get("tags"):
        rows.append(("タグ", "、".join(a["tags"])))
    if a["capacity_ml"]:
        rows.append(("容量", f"{a['capacity_ml']:g} ml"))
    if phys["enabled"] and phys.get("static"):
        place = "天井" if a.get("mount") == "ceiling" else "床"
        rows.append(("物理", f"キネマティックな剛体（{place}に固定）、{_collision_text(phys)}、{_contact_text(phys)}"))
    elif phys["enabled"]:
        rows.append(("物理", f"RigidBody、{_collision_text(phys)}、{_contact_text(phys)}"))
    else:
        rows.append(("物理", "なし"))
    if phys["enabled"] and phys.get("joints"):
        rows.append(("可動部", _joints_text(phys["joints"])))
    if a.get("lighting"):
        rows.append(("照明", _lighting_text(a["lighting"])))
    if a.get("screen"):
        rows.append(("画面", _screen_text(a["screen"])))
    if a.get("picture"):
        rows.append(("絵柄", _picture_text(a["picture"])))
    if a.get("variants"):
        rows.append(("バリアント", "、".join(f"{k}（{' / '.join(v['variants'])}、既定 {v['default']}）"
                                           for k, v in a["variants"].items())))
    rows += [("生成日時", a["generated_at"]), ("生成", f"{a['generator']['tool']}（{a['generator']['model']}）")]

    out = [f"# {a['name']}", "", "![thumbnail](thumbnail.png)", ""]
    if a.get("description"):
        out += [a["description"], ""]
    out += ["| 項目 | 値 |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    out += [
        "",
        "## 使い方",
        "",
        "Z 軸が上、単位はメートル、原点は底面の中心です。ステージに参照で読み込みます。",
        *(["", f"`{a['usd']}` は入口で、中身は Isaac Sim のレイヤー構成（`payloads/` の base・meshes・physics）に分けています。"
            "物理は physics のレイヤーだけにあります。"] if a.get("layers") else []),
        "",
        "```python",
        "from pxr import Usd",
        "",
        "stage = Usd.Stage.Open(\"scene.usd\")",
        f"prim = stage.DefinePrim(\"/World/{a['slug']}\", \"Xform\")",
        f"prim.GetReferences().AddReference(\"<このフォルダ>/{a['usd']}\")",
        "```",
        "",
        "## 寸法・質量の根拠",
        "",
    ]
    out += [f"- {s['url']}" + (f" — {s['note']}" if s.get("note") else "") for s in a["sources"]] or ["- なし"]
    if a["physics"]["enabled"] and a["physics"].get("friction_source"):
        out += ["", "## 摩擦・反発係数の根拠", "", a["physics"]["friction_source"]]
    if a["notes"]:
        out += ["", "## 備考", "", a["notes"]]
    out += ["", "## 制約", ""] + [f"- {t}" for t in LIMITATIONS.get(a["shape_class"], [])]
    if a["warnings"]:
        out += ["", "## 生成時の警告", ""] + [f"- {w}" for w in a["warnings"]]
    if a.get("history"):
        out += ["", "## 更新履歴", ""]
        for h in a["history"]:
            out.append(f"- **{h['version']}**（{h['date'][:10]}）: " + "、".join(h["changes"]))
    if a.get("fictional"):
        out += ["", "## 架空のパッケージ", "",
                "実在の商品をもとにしていない架空のデザインです。実在の商品名・ブランド名・ロゴ・商品画像は使っていません。"
                "形と寸法・質量は同じ種類の商品の一般的な値です。バーコードはインストアコードの範囲（先頭 2）のダミーで、"
                "実在の商品コードではありません。",
                "", "## 素材の出典", ""]
        credits = a.get("image_credits") or []
        out += [f"- {c.get('subject') or c.get('title')}: [{c.get('title')}]({c.get('url')})"
                + (f"（{c['author']}）" if c.get("author") else "")
                + (f" — [{c['license']}]({c['license_url']})" if c.get("license_url") else f" — {c.get('license')}")
                for c in credits if c.get("url")] or ["- 写真なし"]
        out += [f"- {c['title']} — {c['license']}" for c in credits if not c.get("url")]
        if a.get("license") in LICENSES:
            title, url = LICENSES[a["license"]]
            out += ["", "## ライセンス", "", f"このモデル（USD・テクスチャ・メタデータ）は [{title}]({url})（`{a['license']}`）です。"
                    "合成した写真とフォントはそれぞれ上記のライセンスです。"]
        return "\n".join(out) + "\n"
    out += [
        "",
        "## 画像の出典",
        "",
        "テクスチャはメーカー・販売店の商品画像から作っています。権利はそれぞれの権利者にあるため、外部への公開・再配布はしないでください。",
        "",
    ]
    out += [f"- {u}" for u in a["image_sources"]] or ["- なし"]
    return "\n".join(out) + "\n"


def resolve_qcode(meta: dict, cache_dir: Path | None, slug: str, category: str) -> str:
    """cache の spec.json か meta の spec に qcode があればそれ、なければ slug から引く。"""
    override = meta["spec"].get("qcode")
    spec_path = cache_dir / "spec.json" if cache_dir else None
    if spec_path and spec_path.exists():
        override = json.loads(spec_path.read_text()).get("qcode") or override
    return lookup_qcode(slug, category, override)


# 正面の向き。agentic-usd-gen の形はどれも正面（箱の正面・袋の表・回転体のラベルの正面）が -Y。
# 寝かせた袋も、上から -Y 側に立つと表の画像が読める向きになる（shapes/pouch.py の lay_flat）
DEFAULT_FRONT = "-Y"
FRONT_AXES = ("+X", "-X", "+Y", "-Y")


def resolve_front(meta: dict, cache_dir: Path | None) -> str | float:
    """cache の spec.json か meta の spec に front（軸 "+X" などか、+X から反時計回りの度数）があればそれ、なければ -Y。"""
    front = meta["spec"].get("front")
    spec_path = cache_dir / "spec.json" if cache_dir else None
    if spec_path and spec_path.exists():
        front = json.loads(spec_path.read_text()).get("front", front)
    if front is None:
        return DEFAULT_FRONT
    if front in FRONT_AXES or (isinstance(front, (int, float)) and not isinstance(front, bool)):
        return front
    log.warning("front は %s か度数で書いてください（%r）。%s にします", " / ".join(FRONT_AXES), front, DEFAULT_FRONT)
    return DEFAULT_FRONT


def _previous_exports(assets_root: Path, slug: str) -> list[Path]:
    """同じ slug の前回の書き出し（<category>/<slug>/）。旧構成（asset.json が slug 直下）も含む。"""
    return [d for d in assets_root.glob(f"*/{slug}")
            if (d / SIMREADY_DIR / "asset.json").exists() or (d / "asset.json").exists()]


def repo_license(assets_root: Path) -> str | None:
    """書き出し先の既存アセットのライセンスがすべて同じならその値（新しいアセットの既定にする）。"""
    found = {json.loads(p.read_text()).get("license") for p in assets_root.glob(f"*/*/{SIMREADY_DIR}/asset.json")}
    found.discard(None)
    return found.pop() if len(found) == 1 else None


def export_asset(asset_dir: Path, assets_root: Path, blender: str | None, message: str | None = None,
                 bump: str = "auto", license: str | None = None, author: str | None = None) -> dict | None:
    meta_path = asset_dir / "meta.json"
    if not meta_path.exists():
        log.warning("%s: meta.json がないため省略します", asset_dir)
        return None
    meta = json.loads(meta_path.read_text())
    slug = meta["spec"]["slug"]
    usd_path = asset_dir / f"{slug}.usd"
    if not meta["validation"]["ok"]:
        log.warning("%s: 検証 NG のため省略します", slug)
        return None
    if not usd_path.exists():
        log.warning("%s: %s がないため省略します", slug, usd_path.name)
        return None

    cache_dir = find_cache_dir(meta)
    category = resolve_category(meta, cache_dir)
    if category not in CATEGORIES:
        log.warning("%s: カテゴリが未設定です（spec.json の category に %s のいずれかを書いてください）",
                    slug, " / ".join(CATEGORIES))
    thumb = ensure_thumbnail(asset_dir, usd_path, blender)

    # 指定がなければ前回の値、前回がなければ書き出し先の他のアセットと同じライセンス
    default_license = license or repo_license(assets_root)
    # 書き出し先は毎回作り直す。カテゴリが変わった場合に古い場所が残らないよう、同じ slug の書き出しを消す
    prev = None
    for old in _previous_exports(assets_root, slug):
        aj = old / SIMREADY_DIR / "asset.json"
        prev = json.loads((aj if aj.exists() else old / "asset.json").read_text())
        shutil.rmtree(old)
    dst = assets_root / category / slug / SIMREADY_DIR
    dst.mkdir(parents=True)
    shutil.copy2(usd_path, dst / usd_path.name)
    if (asset_dir / "textures").is_dir():
        shutil.copytree(asset_dir / "textures", dst / "textures")
    if thumb and thumb.exists():
        img = Image.open(thumb).convert("RGBA")
        img.save(dst / "thumbnail.png")
        small = dst / ".thumbs" / f"{THUMB_SIZE}x{THUMB_SIZE}" / f"{usd_path.name}.png"
        small.parent.mkdir(parents=True)
        img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS).save(small)

    asset = build_asset_json(meta, slug, category, usd_path.stat().st_mtime)
    asset["tags"] = asset_tags(asset, resolve_tags(meta, cache_dir))
    asset["description"] = asset_description(asset)
    asset["license"] = license or (prev or {}).get("license") or default_license
    if not asset["license"]:
        log.warning("%s: ライセンスが未設定です（--license で指定してください）", slug)
    asset["author"] = author or (prev or {}).get("author") or package_author()
    asset["qcode"] = resolve_qcode(meta, cache_dir, slug, category)
    asset["source_file"] = f"{cache_dir.name}/spec.json" if cache_dir else f"{asset_dir.name}/meta.json"
    asset["front"] = resolve_front(meta, cache_dir)
    asset["content_hash"] = {**content_hashes(usd_path, asset_dir / "textures"), "metadata": metadata_hash(asset)}
    if apply_version(asset, prev, message, bump):
        log.info("%s: バージョン %s → %s", slug, prev.get("version") if prev else "なし", asset["version"])
    dedupe_textures(dst / usd_path.name, dst / "textures", keep=referenced_names(asset))
    write_usd_metadata(dst / usd_path.name, asset)
    layers = split_layers(dst / usd_path.name)
    asset["layers"] = {role: p.relative_to(dst).as_posix() for role, p in layers.items()}
    if not (dst / "thumbnail.png").exists():
        asset["thumbnail"] = None
    (dst / "asset.json").write_text(json.dumps(asset, ensure_ascii=False, indent=2))
    (dst / "README.md").write_text(model_card(asset))
    log.info("%s → %s", slug, dst)
    return asset


def collect(assets_root: Path) -> list[tuple[Path, dict]]:
    return sorted(((p.parent, json.loads(p.read_text()))
                   for p in assets_root.glob(f"*/*/{SIMREADY_DIR}/asset.json")),
                  key=lambda x: (x[1]["category"], x[1]["slug"]))


def write_catalog(assets_root: Path) -> None:
    """assets/ にあるすべての asset.json（今回書き出していないものも含む）から一覧を作る。"""
    entries = collect(assets_root)
    catalog = [{**a, "path": d.relative_to(assets_root).as_posix()} for d, a in entries]
    (assets_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2))

    lines = ["# アセット一覧", "", f"{len(entries)} 点。各フォルダの README.md がモデルカードです。", ""]
    for cat in dict.fromkeys(a["category"] for _, a in entries):
        lines += [f"## {CATEGORY_LABELS.get(cat, cat)}", "", "| | 名前 | 版 | 形状 | 外形（mm） | 質量 |",
                  "|---|---|---|---|---|---|"]
        for d, a in entries:
            if a["category"] != cat:
                continue
            rel = d.relative_to(assets_root).as_posix()
            img = f'<img src="{rel}/thumbnail.png" width="96">' if a.get("thumbnail") else ""
            size = " × ".join(_mm(v) for v in a["size_m"]) if a["size_m"] else "—"
            lines.append(f"| {img} | [{a['name']}]({rel}/README.md) | {a.get('version', '—')} | {SHAPE_LABELS.get(a['shape_class'], '')} "
                         f"| {size} | {a['mass_kg']:.3f} kg |")
        lines.append("")
    lines += ["`catalog.usda` は全アセットを X 方向に並べて payload で読み込むステージです（物理付きなので、見比べるときは"
              "シミュレーションを止めておくか床を置いてください）。", ""]
    (assets_root / "README.md").write_text("\n".join(lines))
    write_catalog_stage(assets_root, entries)


def write_catalog_stage(assets_root: Path, entries: list[tuple[Path, dict]], gap: float = 0.05) -> None:
    # 同じプロセスで書き直せるよう、メモリ上で作ってから書き出す。中身は読み込まない（payload なので開くときに読む）
    stage = Usd.Stage.CreateInMemory(load=Usd.Stage.LoadNone)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/Catalog")
    stage.SetDefaultPrim(root.GetPrim())
    x = 0.0
    for d, a in entries:
        w = a["size_m"][0] if a["size_m"] else 0.1
        x += w / 2
        xf = UsdGeom.Xform.Define(stage, root.GetPath().AppendChild(a["slug"]))
        xf.AddTranslateOp().Set(Gf.Vec3d(x, 0, 0))
        xf.GetPrim().GetPayloads().AddPayload(f"./{d.relative_to(assets_root).as_posix()}/{a['usd']}")
        x += w / 2 + gap
    stage.GetRootLayer().Export(str(assets_root / "catalog.usda"))


def export_recipe(asset_dir: Path, recipes_root: Path) -> None:
    """検索キャッシュ（spec.json・vision.json・images/）を recipes/<キャッシュ名>/ に写す。"""
    meta = json.loads((asset_dir / "meta.json").read_text())
    cache_dir = find_cache_dir(meta)
    if not cache_dir or not (cache_dir / "spec.json").exists():
        log.warning("%s: 検索キャッシュが見つからないためレシピを省略します", asset_dir.name)
        return
    dst = recipes_root / cache_dir.name
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copy2(cache_dir / "spec.json", dst / "spec.json")
    if (cache_dir / "images").is_dir():
        shutil.copytree(cache_dir / "images", dst / "images")
    vision = cache_dir / "vision.json"
    if vision.exists():
        v = json.loads(vision.read_text())
        v["images"] = [f"images/{Path(p).name}" for p in v.get("images", [])]  # 絶対パスを持ち込まない
        (dst / "vision.json").write_text(json.dumps(v, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-usd-gen-export", description="生成済みアセットをリポジトリ管理用の形に書き出す")
    p.add_argument("slugs", nargs="*", help="書き出す slug（省略時は --out の下のすべて）")
    p.add_argument("--out", type=Path, default=Path("out"), help="生成結果のフォルダ（既定: out/）")
    p.add_argument("--assets", type=Path, default=Path("assets"), help="書き出し先（既定: assets/）")
    p.add_argument("--recipes", type=Path, help="検索キャッシュも書き出す先（例: recipes）")
    p.add_argument("--blender", help="Blender 実行ファイルのパス（サムネイルがないときに描画する）")
    p.add_argument("-m", "--message", help="更新履歴に書く変更内容（中身が変わったアセットにだけ付く）")
    p.add_argument("--bump", choices=("auto", "major", "minor", "patch"), default="auto",
                   help="中身が変わったときに上げる桁（既定 auto: 外形が変われば major、それ以外は minor）")
    p.add_argument("--license", choices=list(LICENSES),
                   help="アセットのライセンス（asset.json・USD・モデルカードに書く。省略時は前回の値、"
                        "新しいアセットは書き出し先の他のアセットがすべて同じならその値）")
    p.add_argument("--author", help="作成者（SimReady_Metadata の author。省略時は前回の値か pyproject の authors）")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    dirs = [args.out / s for s in args.slugs] if args.slugs else sorted(d for d in args.out.iterdir() if d.is_dir())
    missing = [d for d in dirs if not d.is_dir()]
    if missing:
        sys.exit(f"見つかりません: {', '.join(map(str, missing))}")
    args.assets.mkdir(parents=True, exist_ok=True)
    blender = None
    if args.blender:
        blender = find_blender(args.blender)
    exported = 0
    for d in dirs:
        if export_asset(d, args.assets, blender, args.message, args.bump, args.license, args.author):
            exported += 1
            if args.recipes:
                export_recipe(d, args.recipes)
    write_catalog(args.assets)
    print(f"\n書き出し: {exported} / {len(dirs)} 点 → {args.assets}（一覧: {args.assets / 'README.md'}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
