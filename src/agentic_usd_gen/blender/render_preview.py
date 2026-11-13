"""USD を Blender に読み戻してプレビュー画像を描画する（Blender 内で実行）。

使い方: Blender -b --python render_preview.py -- <usd_path> <out_dir> [samples] [thumbnail]
出力: preview_front.png / preview_34.png / preview_top.png と thumbnail.png（512px 四方、背景透過）。
透明な部品があれば、見た目の検査（preview_check.py）に使うマスクも masks/ に書く。
4 番目の引数に thumbnail を渡すと thumbnail.png だけを描画する。
天井付けの什器（隣の meta.json の spec.mount が ceiling）は、照明と斜めの視点を上下に返し、下から見上げて描く。
"""

import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


# 什器に内蔵する照明（UsdLux。lighting.py）の明るさの倍率。輝度 [nit] のまま読むと、プレビューの照明（下の Key・Fill・Rim）
# よりずっと明るく、ケースの中が白く飛ぶ。Isaac Sim の天井照明の下と同じく、中が棚の前面と同じくらいに見える倍率にする
PREVIEW_LIGHT_SCALE = 0.003


def add_light(name, kind, loc, energy, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    if kind == "AREA":
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    look_at(obj, Vector((0, 0, 0)))
    return obj


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


SHADOW_THROUGH = 0.7  # 透明なマテリアルを影の光線が通る割合


def mdl_inputs(usd_path):
    """USD のマテリアル名 → (MDL のモジュール名, 入力値の辞書)。透明なマテリアル（OmniGlass / OmniSurface）だけ。"""
    from pxr import Usd, UsdShade

    out = {}
    stage = Usd.Stage.Open(str(usd_path))  # 変数に持たないと、走査中にステージが消える
    for prim in stage.Traverse():
        if not prim.IsA(UsdShade.Shader):
            continue
        sh = UsdShade.Shader(prim)
        module = sh.GetSourceAssetSubIdentifier("mdl")
        if module in ("OmniGlass", "OmniSurface"):
            out[prim.GetParent().GetName()] = (module, {i.GetBaseName(): i.Get() for i in sh.GetInputs()})
    return out


def apply_transparent_materials(usd_path):
    """取り込んだ UsdPreviewSurface（オパシティで近似）を、MDL と同じ屈折・吸収のマテリアルに置き換える。

    Isaac Sim（RTX）での見え方にそろえるため。OmniGlass の glass_color は表面を通るたびにかかる色、
    OmniSurface の透過は深さ d を通った後に specular_transmission_color になる体積吸収。
    thin_walled の OmniGlass（PET の薄い壁）は屈折させない。拡散透過のある OmniSurface は半透明の膜。
    """
    mdl = mdl_inputs(usd_path)
    for mat in bpy.data.materials:
        key = mat.name.split(".")[0]
        if key not in mdl or not mat.use_nodes:
            continue
        module, inp = mdl[key]
        nt = mat.node_tree
        nt.nodes.clear()
        if module == "OmniSurface" and inp.get("enable_diffuse_transmission"):
            translucent_material(nt, inp)
            continue
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        output = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        # 影の光線は 7 割素通りさせる。透明な容器の中（ラベルの裏など）にも光が届き、黒く沈まない。
        # 全部通すと透明なボトルの影が消えるので少し残す
        light_path = nt.nodes.new("ShaderNodeLightPath")
        clear = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        through = nt.nodes.new("ShaderNodeMath")
        through.operation = "MULTIPLY"
        through.inputs[1].default_value = SHADOW_THROUGH
        nt.links.new(light_path.outputs["Is Shadow Ray"], through.inputs[0])
        nt.links.new(through.outputs[0], mix.inputs[0])
        nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        nt.links.new(clear.outputs["BSDF"], mix.inputs[2])
        nt.links.new(mix.outputs[0], output.inputs["Surface"])
        if module == "OmniGlass":
            tint = tuple(inp.get("glass_color", (1, 1, 1)))
            bsdf.inputs["Base Color"].default_value = (*tint, 1)
            bsdf.inputs["Roughness"].default_value = inp.get("frosting_roughness", 0.0)
            ior = inp.get("glass_ior", 1.5)
            if inp.get("thin_walled"):
                # 薄い膜: 屈折させず（IOR 1）、外向きの面にだけ反射のコートを載せる（内側の面で全反射させない）
                bsdf.inputs["IOR"].default_value = 1.0
                geo = nt.nodes.new("ShaderNodeNewGeometry")
                front = nt.nodes.new("ShaderNodeMath")
                front.operation = "SUBTRACT"
                front.inputs[0].default_value = 1.0
                nt.links.new(geo.outputs["Backfacing"], front.inputs[1])
                nt.links.new(front.outputs[0], bsdf.inputs["Coat Weight"])
                bsdf.inputs["Coat IOR"].default_value = ior
                bsdf.inputs["Coat Roughness"].default_value = 0.0
            else:
                bsdf.inputs["IOR"].default_value = ior
            continue
        tint = tuple(inp.get("specular_transmission_color", (1, 1, 1)))
        depth = inp.get("specular_transmission_scattering_depth", 0.0)
        bsdf.inputs["IOR"].default_value = inp.get("specular_reflection_ior", 1.5)
        bsdf.inputs["Roughness"].default_value = inp.get("specular_reflection_roughness", 0.0)
        if depth <= 0:
            bsdf.inputs["Base Color"].default_value = (*tint, 1)
            continue
        bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
        # 澄んだ液体（濁った液体は拡散透過のある薄い膜で、上の translucent_material）。式の定数の丸めで散乱が
        # わずかに残る（σt の 1e-5 倍ほど）ので、散乱も吸収に足す
        sigma_s, sigma_a = omnisurface_volume(tint, inp.get("specular_transmission_scattering_color") or (0, 0, 0), depth)
        sigma_a = [a + s for a, s in zip(sigma_a, sigma_s)]
        # Blender の吸収係数は (1 - color) × density
        density = max(sigma_a) or 1.0
        vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
        vol.inputs["Color"].default_value = (*(1 - s / density for s in sigma_a), 1)
        vol.inputs["Density"].default_value = density
        nt.links.new(vol.outputs["Volume"], output.inputs["Volume"])


def omnisurface_volume(transmission, scattering, depth):
    """OmniSurface の透過の入力（色・散乱の色・深さ）が表す (散乱係数, 吸収係数)。深さと同じ長さの単位の逆数。

    Isaac Sim 6.1 の OmniShared.mdl（compute_transmission_volume_coefficients）と同じ計算。
    usd_post.omnisurface_volume と同じ（Blender の中では agentic_usd_gen を読み込めないので写してある）。
    """
    m = max(scattering)
    sigma_s, sigma_a = [], []
    for t, s in zip(transmission, scattering):
        st = -math.log(max(t, 1e-5) / (1 + m)) / depth
        x = t * s
        a = st * (4.09712 + 4.20863 * x - math.sqrt(9.59217 + 41.6808 * x + 17.7126 * x * x)) ** 4
        sigma_a.append(a)
        sigma_s.append(st - a)
    return sigma_s, sigma_a


def transparent_prims(usd_path):
    """(透明なメッシュの名前 → 液体か, 半透明な部品の数)。透明なメッシュは、液体のマテリアルを持つものと、
    agenticUsdGen:transparency が transparent のもの。

    半透明（translucent）の部品は向こうが透けて見えないので、マスクでは不透明な部品と同じに扱う。
    """
    from pxr import Usd, UsdGeom, UsdShade

    out, translucent = {}, 0
    stage = Usd.Stage.Open(str(usd_path))
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
        labels = mat.GetPrim().GetAttribute("semantics:labels:material").Get() if mat else None
        liquid = bool(labels) and "liquid" in labels
        how = prim.GetAttribute("agenticUsdGen:transparency").Get()
        if liquid or how == "transparent":
            out[prim.GetName()] = liquid
        elif how == "translucent":
            translucent += 1
    return out, translucent


MASKS = {
    # 名前: 描くもの。どれも描くもの以外の不透明な部品で隠れる
    "liquid": "見えている液体（透明な部品は外す。半透明の部品の奥は隠れる）",
    "clear": "いちばん手前の透明な部品（液体以外）",
    "opaque": "不透明・半透明な部品（透明な部品は外す）",
}


def render_masks(usd_path, scene, views, render, out_dir):
    """透明な部品の検査用のマスク（白が対象）と、背景の明るさを masks/ に書く。透明な部品がなければ何もしない。

    info.json には液体・半透明な部品のメッシュの数を書く（液体が消えた・半透明の容器で隠れているの見分けに使う）。
    """
    trans, translucent = transparent_prims(usd_path)
    if not trans:
        return
    objs = [o for o in scene.objects if o.type == "MESH" and not o.is_shadow_catcher]
    kind = {o: trans.get(o.name.split(".")[0]) for o in objs}  # None: 不透明 / True: 液体 / False: 透明な容器
    mask_dir = out_dir / "masks"
    mask_dir.mkdir(exist_ok=True)
    (mask_dir / "info.json").write_text(json.dumps({"liquid": sum(trans.values()), "translucent": translucent}))

    hidden = {o: o.hide_render for o in scene.objects}
    saved = (scene.render.engine, scene.view_settings.view_transform, scene.view_settings.look,
             scene.view_settings.exposure)
    # 背景の明るさ（透明な容器ごしに見える背景の基準）。物を隠して背景だけを小さく描く
    for o in scene.objects:
        o.hide_render = True
    scene.render.film_transparent = False
    render(views["front"], mask_dir / "background.png", 16, 16, quiet=True)
    scene.render.film_transparent = True

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "OBJECT"
    scene.display.render_aa = "OFF"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    for name in MASKS:
        for o, k in kind.items():
            target = {"liquid": k is True, "clear": k is False, "opaque": k is None}[name]
            o.hide_render = name != "clear" and k is not None and not target
            o.color = (1, 1, 1, 1) if target else (0, 0, 0, 1)
        for view, direction in views.items():
            render(direction, mask_dir / f"{view}_{name}.png", 768, 1024, quiet=True)
    scene.render.engine, scene.view_settings.view_transform, scene.view_settings.look, \
        scene.view_settings.exposure = saved
    for o, h in hidden.items():
        o.hide_render = h


def translucent_material(nt, inp):
    """半透明の膜（OmniSurface の thin_walled + 拡散透過）。

    clarity（specular_transmission_weight）の割合は素通し、残りは subsurface_weight の割合で拡散透過・それ以外は拡散反射、
    表面に粗い鏡面反射。
    Cycles で粗い屈折を使うと、閉じた部品（傘の生地など）がレンズのように像を曲げるので、素通しはぼかさない。
    """
    col = (*tuple(inp.get("diffuse_reflection_color", (1, 1, 1))), 1)
    clarity = inp.get("specular_transmission_weight", 0.5)
    new = nt.nodes.new
    clear, trans, diff = new("ShaderNodeBsdfTransparent"), new("ShaderNodeBsdfTranslucent"), new("ShaderNodeBsdfDiffuse")
    gloss, fresnel = new("ShaderNodeBsdfGlossy"), new("ShaderNodeFresnel")
    for n in (clear, trans, diff):
        n.inputs["Color"].default_value = col
    gloss.inputs["Roughness"].default_value = inp.get("specular_reflection_roughness", 0.35)
    fresnel.inputs["IOR"].default_value = inp.get("specular_reflection_ior", 1.5)
    milky, body, top = new("ShaderNodeMixShader"), new("ShaderNodeMixShader"), new("ShaderNodeMixShader")
    milky.inputs[0].default_value = inp.get("subsurface_weight", 0.5)  # 素通しでない分のうち拡散透過の割合
    nt.links.new(diff.outputs[0], milky.inputs[1])
    nt.links.new(trans.outputs[0], milky.inputs[2])
    body.inputs[0].default_value = clarity
    nt.links.new(milky.outputs[0], body.inputs[1])
    nt.links.new(clear.outputs[0], body.inputs[2])
    nt.links.new(fresnel.outputs[0], top.inputs[0])
    nt.links.new(body.outputs[0], top.inputs[1])
    nt.links.new(gloss.outputs[0], top.inputs[2])
    # 影の光線は素通しと拡散透過の分だけ抜ける（重なった膜の奥まで光が届き、暗く沈まない）
    shadow, light_path = new("ShaderNodeMixShader"), new("ShaderNodeLightPath")
    through = new("ShaderNodeMath")
    through.operation = "MULTIPLY"
    through.inputs[1].default_value = clarity + (1 - clarity) * milky.inputs[0].default_value
    nt.links.new(light_path.outputs["Is Shadow Ray"], through.inputs[0])
    nt.links.new(through.outputs[0], shadow.inputs[0])
    nt.links.new(top.outputs[0], shadow.inputs[1])
    nt.links.new(new("ShaderNodeBsdfTransparent").outputs[0], shadow.inputs[2])
    nt.links.new(shadow.outputs[0], new("ShaderNodeOutputMaterial").inputs["Surface"])


def is_ceiling(usd_path):
    meta = usd_path.parent / "meta.json"
    if not meta.exists():
        return False
    meta = json.loads(meta.read_text())
    return (meta.get("spec") or {}).get("mount", meta.get("mount")) == "ceiling"


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    usd_path, out_dir = Path(argv[0]), Path(argv[1])
    samples = int(argv[2]) if len(argv) > 2 else 64
    thumbnail_only = len(argv) > 3 and argv[3] == "thumbnail"
    out_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=str(usd_path), import_materials=True, import_usd_preview=True,
                          import_guide=False,  # 把持の線（guide）は描かない
                          light_intensity_scale=PREVIEW_LIGHT_SCALE)
    apply_transparent_materials(usd_path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("USD にメッシュがありません")
    lo, hi = bounds(meshes)
    center = (lo + hi) / 2
    size = max(hi - lo)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.device = "CPU"
    # 透明な容器は面が何枚も重なる（PET の内外・液体・ラベル）。途中で打ち切られて黒くならないよう多めにする
    scene.cycles.max_bounces = 32
    scene.cycles.transmission_bounces = 32
    scene.cycles.transparent_max_bounces = 32
    scene.cycles.volume_bounces = 16  # 濁った液体の中で光が何度も散乱する
    scene.render.film_transparent = True  # 背景は透過、床は影だけ残す
    # Standard では白いパッケージの明るい面が 1.0 で切れて印刷が飛ぶ。AgX で明るい所をなだらかに丸め、
    # 色が浅くなりすぎないようコントラスト強めのルックにして、露出を少し下げる（サムネイルも同じ設定）
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.3

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    scene.world = world

    # 天井付けは下から見上げる。照明と視点の高さを上下に返し、影を受ける面は天井（上端）に置く
    up = -1 if is_ceiling(usd_path) else 1
    # 床（影だけを写すシャドウキャッチャー）
    bpy.ops.mesh.primitive_plane_add(size=size * 20, location=(center.x, center.y, lo.z if up > 0 else hi.z))
    bpy.context.active_object.is_shadow_catcher = True
    # 液体越しに床が見えると、照らされた白い板として写り中身が白っぽくなる。屈折の先には写さない
    bpy.context.active_object.visible_transmission = False

    d = size * 3
    add_light("Key", "AREA", center + Vector((-d, -d, d * up)), 22 * d * d, size * 2)
    add_light("Fill", "AREA", center + Vector((d, -d * 0.5, d * 0.5 * up)), 8 * d * d, size * 2)
    add_light("Rim", "AREA", center + Vector((0, d, d * up)), 12 * d * d, size * 2)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    def render(direction, path, res_x, res_y, quiet=False):
        scene.render.resolution_x, scene.render.resolution_y = res_x, res_y
        # 85mm で全体が収まる距離。センサー 36mm は画像の長辺に当たるので、狭い方向の画角で決める
        fov = 2 * math.atan(36 * min(res_x, res_y) / max(res_x, res_y) / 2 / cam_data.lens)
        # どの向きから見ても収まるよう、バウンディングボックスを包む球（少し余白付き）が画角に入る距離にする
        radius = (hi - lo).length / 2
        cam.location = center + direction.normalized() * (radius * 1.05 / math.sin(fov / 2))
        look_at(cam, center)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        if not quiet:
            print(f"rendered {path}")

    views = {
        "front": Vector((0, -1, 0.05)),
        "34": Vector((0.7, -0.7, 0.45 * up)),
        "top": Vector((0.0, -0.25, 1.0)),
    }
    if not thumbnail_only:
        shutil.rmtree(out_dir / "masks", ignore_errors=True)  # 前の描画のマスクを残さない
        for name, direction in views.items():
            render(direction, out_dir / f"preview_{name}.png", 768, 1024)
        render_masks(usd_path, scene, views, render, out_dir)
    render(views["34"], out_dir / "thumbnail.png", 512, 512)


main()
