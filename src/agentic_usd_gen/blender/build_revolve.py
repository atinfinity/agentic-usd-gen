"""Blender 内で実行: 回転体プロファイルから容器・中身・キャップ（上面の画像も）・ラベルを作り USD に書き出す。

    Blender -b --factory-startup --python build_revolve.py -- build.json

build.json は agentic_usd_gen.shapes.revolve が書き出す。座標はメートル、Z 軸が上、原点は底面の中心。
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).parent))
from common import (build_object, export_usd, finish_mesh, material, materials_from_cfg, new_scene,  # noqa: E402
                    srgb_to_linear)


def _squircle(n, segments):
    """超楕円 |x|^n + |y|^n = 1 の周を弧長で等分した点（x = 1, y = 0 から反時計回り）。"""
    m = segments * 32
    pts = []
    for k in range(m + 1):
        t = 2 * math.pi * k / m
        c, s = math.cos(t), math.sin(t)
        pts.append((math.copysign(abs(c) ** (2 / n), c), math.copysign(abs(s) ** (2 / n), s)))
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    out, i = [], 0
    for j in range(segments):
        target = acc[-1] * j / segments
        while acc[i + 1] < target:
            i += 1
        f = (target - acc[i]) / (acc[i + 1] - acc[i])
        out.append((pts[i][0] + f * (pts[i + 1][0] - pts[i][0]), pts[i][1] + f * (pts[i + 1][1] - pts[i][1])))
    return out


def revolve(name, points, segments, close_bottom, close_top, y_scale=1.0, square=None, square_r=None, lobes=None,
            bottom=None, top=None, uv_r=None):
    """(z, r) の列（z 昇順）を Z 軸まわりに回転した Mesh オブジェクトを作る。

    UV は u = 角度 / 2π、v = 区間内の z 比率（円筒投影）。y_scale < 1 なら断面を Y 方向に縮めた楕円にする。
    square（超楕円の指数）を渡すと断面を角の丸い四角にする。半径が square_r に近いほど角ばり、首のように細いところは丸に戻す
    （u は周の弧長の比率）。lobes = [脚の数, 高さ, 深さ] なら、底から高さまでを脚の間でくぼませて花形の底にする。

    bottom / top は、列の最初・最後の輪から内側へ続ける (z, r) の輪（缶の底のドーム・上面のくぼみ）。
    それらの面と閉じた円は、半径 uv_r の円が UV の 0〜1 に収まる平面投影にする。top の面は最後に並ぶ。
    """
    bottom, top = list(bottom or []), list(top or [])
    rings = list(reversed(bottom)) + list(points) + top
    first, last = len(bottom), len(bottom) + len(points) - 1  # 輪郭の輪の範囲
    n_rings = len(rings)
    z_min, z_max = points[0][0], points[-1][0]
    uv_r = uv_r or max(r for _, r in rings)
    circle = [(math.cos(2 * math.pi * j / segments), math.sin(2 * math.pi * j / segments)) for j in range(segments)]
    square_pts = _squircle(square, segments) if square else None
    verts = []
    for z, r in rings:
        if square_pts:
            t = min(max((r / square_r - 0.5) / 0.45, 0.0), 1.0)
            t = t * t * (3 - 2 * t)
            ring = [(cx + t * (sx - cx), cy + t * (sy - cy)) for (cx, cy), (sx, sy) in zip(circle, square_pts)]
        else:
            ring = circle
        if lobes and z < lobes[1]:
            w = 0.5 + 0.5 * math.cos(math.pi * z / lobes[1])  # 底で 1、高さで 0
            ring = [(x * f, y * f) for (x, y), f in
                    zip(ring, (1 - lobes[2] * w * (0.5 - 0.5 * math.cos(lobes[0] * 2 * math.pi * j / segments))
                               for j in range(segments)))]
        for x, y in ring:
            verts.append((r * x, r * y * y_scale, z))

    def planar(k, j):
        x, y, _ = verts[k * segments + j % segments]
        return (0.5 + 0.5 * x / uv_r, 0.5 + 0.5 * y / (uv_r * y_scale))

    faces, face_uvs = [], []
    for k in range(n_rings - 1):
        flat = k < first or k >= last
        if not flat:
            v0 = (rings[k][0] - z_min) / (z_max - z_min)
            v1 = (rings[k + 1][0] - z_min) / (z_max - z_min)
        for j in range(segments):
            jn = (j + 1) % segments
            faces.append((k * segments + j, k * segments + jn, (k + 1) * segments + jn, (k + 1) * segments + j))
            if flat:
                face_uvs.append((planar(k, j), planar(k, j + 1), planar(k + 1, j + 1), planar(k + 1, j)))
            else:
                u0, u1 = j / segments, (j + 1) / segments
                face_uvs.append(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))

    def disk(ring, reverse, flat):
        idx = [ring * segments + j for j in range(segments)]
        if flat:
            uvs = [planar(ring, j) for j in range(segments)]
        else:
            uvs = [(0.5 + 0.5 * math.cos(2 * math.pi * j / segments), 0.5 + 0.5 * math.sin(2 * math.pi * j / segments))
                   for j in range(segments)]
        if reverse:
            idx.reverse()
            uvs.reverse()
        faces.append(tuple(idx))
        face_uvs.append(tuple(uvs))

    if close_bottom:
        disk(0, reverse=True, flat=bool(bottom))  # 法線を下向きに
    if close_top:
        disk(n_rings - 1, reverse=False, flat=bool(top))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    uv = mesh.uv_layers.new(name="st")
    for poly, uvs in zip(mesh.polygons, face_uvs):
        for li, uv_co in zip(poly.loop_indices, uvs):
            uv.data[li].uv = uv_co
    return finish_mesh(mesh, name)


def main():
    cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
    new_scene()

    seg = cfg["segments"]
    parts = cfg["parts"]
    ys = cfg.get("y_scale", 1.0)  # 胴・中身・ラベルの断面の縦横比（楕円のボトル）。キャップは丸のまま
    sq = {"square": cfg.get("square"), "square_r": cfg.get("square_r"),  # 角形のボトル。キャップは丸のまま
          "lobes": cfg.get("lobes")}  # 炭酸ボトルの花形の底
    mats = cfg["materials"]

    bm = mats["Body"]
    if bm["role"] == "glass":
        body_mat = material(bm["name"], srgb_to_linear(bm["color"]), 0.02, transmission=1.0, ior=bm["ior"])
    elif bm["role"] == "pet":
        body_mat = material(bm["name"], srgb_to_linear(bm["color"]), 0.05, transmission=1.0, ior=1.57)
    elif bm["role"] == "translucent":
        body_mat = material(bm["name"], srgb_to_linear(bm["color"]), bm["roughness"], transmission=bm["clarity"])
    else:
        body_mat = material(bm["name"], srgb_to_linear(bm["color"]), 0.4, metallic=bm.get("metallic", 0.0))
    objs = {}

    body = revolve("Body", parts["Body"]["points"], seg, close_bottom=True, close_top=False, y_scale=ys,
                   bottom=parts["Body"].get("bottom"), **sq)
    mod = body.modifiers.new("Wall", "SOLIDIFY")
    mod.thickness = cfg["wall_thickness"]
    mod.offset = -1.0
    bottom = cfg.get("bottom_thickness")
    if bottom:
        # 底を厚くする（ガラス瓶）。底の頂点ほど厚く、底から bottom の高さで胴の肉厚に戻す
        vg = body.vertex_groups.new(name="Bottom")
        for v in body.data.vertices:
            w = max(0.0, 1.0 - v.co.z / bottom)
            if w > 0:
                vg.add([v.index], w, "REPLACE")
        mod.thickness = bottom
        mod.vertex_group = "Bottom"
        mod.thickness_vertex_group = cfg["wall_thickness"] / bottom
    body.data.materials.append(body_mat)
    objs["Body"] = body

    cp = parts["Cap"]
    top = cp.get("top") or []
    # 缶の上面のくぼみは巻き締めの下まで下がるので、底は円で閉じずに縁の内側の輪（bottom）までにする
    cap = revolve("Cap", cp["points"], seg, close_bottom=not cp.get("bottom"), close_top=True,
                  bottom=cp.get("bottom"), top=top, uv_r=max(r for _, r in cp["points"]))
    cap.data.materials.append(material("CapMat", srgb_to_linear(mats["Cap"]["color"]), 0.4))
    if "CapTop" in mats:
        # 上面（最後に足した円と、缶ならくぼみの溝から内側の平らな面）だけ蓋の画像を貼る。巻き締めの上面と
        # くぼみの壁は平面投影だと画像が縦に引き伸ばされるので、側面と同じ材質のままにする。
        # 画像がなければ単色（側面に溝の法線マップがあるとき）
        ct = mats["CapTop"]
        cap.data.materials.append(material("CapTopMat", (1, 1, 1) if ct.get("texture") else srgb_to_linear(ct["color"]),
                                           0.4, texture=ct.get("texture")))
        n_flat = min(len(top), 2)  # くぼみの溝の底 → 平らな面へ上がる帯
        for poly in cap.data.polygons[-(1 + n_flat * seg):]:
            poly.material_index = 1
    objs["Cap"] = cap

    if "Liquid" in parts:
        liq = revolve("Liquid", parts["Liquid"]["points"], seg, close_bottom=True, close_top=True, y_scale=ys, **sq)
        m = mats["Liquid"]
        liq.data.materials.append(material("LiquidMat", srgb_to_linear(m["color"]), 0.02, transmission=m["transmission"], ior=1.34))
        objs["Liquid"] = liq

    if "Label" in parts:
        lab = revolve("Label", parts["Label"]["points"], seg, close_bottom=False, close_top=False, y_scale=ys, **sq)
        lab.data.materials.append(material("LabelMat", (1, 1, 1), 0.35, texture=mats["Label"]["texture"]))
        objs["Label"] = lab

    if "LabelBack" in parts:
        # 透明容器のラベルの裏面。法線を容器の内側へ向ける
        back = revolve("LabelBack", parts["LabelBack"]["points"], seg, close_bottom=False, close_top=False, y_scale=ys, **sq)
        back.data.flip_normals()
        back.data.materials.append(material("LabelBackMat", (1, 1, 1), 0.35, texture=mats["LabelBack"]["texture"]))
        objs["LabelBack"] = back

    # 本体に足す部品（ポンプの頭など）。頂点は Python 側で計算・平行移動済み
    if cfg.get("objects"):
        extra = materials_from_cfg(cfg["extra_materials"])
        for spec in cfg["objects"]:
            build_object(spec, extra)
    if cfg.get("shift"):
        # 本体と部品を合わせた外形が XY 中心・底面 z=0 になるよう、本体をずらす
        for obj in objs.values():
            obj.data.transform(Matrix.Translation(Vector(cfg["shift"])))

    export_usd(cfg)


main()
