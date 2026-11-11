"""Blender 内で動くスクリプトの共通処理（マテリアル作成・USD 書き出し）。"""

import math

import bmesh
import bpy

SHARP_ANGLE = math.radians(40)


def srgb_to_linear(hex_color):
    def conv(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return tuple(conv(int(hex_color[i : i + 2], 16)) for i in (1, 3, 5))


EMISSION_STRENGTH = 0.7  # 光る画面（emissive）の明るさ。プレビューの照明の下で、画像が少し明るく見えるくらい


def material(name, color, roughness, transmission=0.0, ior=1.5, texture=None, metallic=0.0, emissive=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["Metallic"].default_value = metallic
    if texture:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(texture)
        tex.extension = "REPEAT"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if emissive:
            mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = EMISSION_STRENGTH
    return mat


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def finish_mesh(mesh, name):
    """法線を整えてスムーズシェードし、オブジェクトとしてシーンに置く。"""
    mesh.validate()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=SHARP_ANGLE)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build_object(spec, mats):
    mesh = bpy.data.meshes.new(spec["name"])
    mesh.from_pydata(spec["vertices"], [], spec["faces"])
    uv = mesh.uv_layers.new(name="st")
    for poly, uvs in zip(mesh.polygons, spec["uvs"]):
        for li, uv_co in zip(poly.loop_indices, uvs):
            uv.data[li].uv = uv_co
    # 面の向きを外向きにそろえる
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = finish_mesh(mesh, spec["name"])
    obj.data.materials.append(mats[spec["material"]])
    if spec.get("bevel"):
        add_bevel(obj, spec["bevel"])
    return obj


def add_bevel(obj, width):
    """角を丸く面取りする（書き出し時に適用される）。法線は面取りの外の平らな面をまっすぐに保つ。"""
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = 3
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(30)
    mod.harden_normals = True


def materials_from_cfg(cfg_materials):
    """build.json の materials（{name: {color, roughness, ...}}）から Blender のマテリアルを作る。"""
    return {
        name: material(name, srgb_to_linear(m.get("color", "#FFFFFF")), m.get("roughness", 0.4),
                       transmission=m.get("transmission", 0.0), ior=m.get("ior", 1.5),
                       texture=m.get("texture"), metallic=m.get("metallic", 0.0),
                       emissive=m.get("emissive", False))
        for name, m in cfg_materials.items()
    }


def export_usd(cfg):
    if cfg.get("blend_path"):
        bpy.ops.wm.save_as_mainfile(filepath=cfg["blend_path"])

    bpy.ops.wm.usd_export(
        filepath=cfg["usd_path"],
        root_prim_path="/" + cfg["root_name"],
        merge_parent_xform=True,
        visible_objects_only=False,
        export_materials=True,
        generate_preview_surface=True,
        export_textures_mode="KEEP",
        relative_paths=True,
        export_uvmaps=True,
        rename_uvmaps=True,
        export_normals=True,
        export_cameras=False,
        export_lights=False,
        convert_world_material=False,
        export_custom_properties=False,
        author_blender_name=False,
        evaluation_mode="RENDER",
        convert_scene_units="METERS",
    )
    print("AGENTIC_USD_GEN_EXPORTED", cfg["usd_path"])
