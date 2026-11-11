"""Blender 内で実行: Python 側で計算した頂点・面・UV からメッシュを作り USD に書き出す。

    Blender -b --factory-startup --python build_mesh.py -- build.json

build.json の objects は {name, vertices: [[x,y,z]], faces: [[i,...]], uvs: [[[u,v],...] 面ごと], material}。
materials は {name: {color, roughness, metallic?, transmission?, ior?, texture?}}。座標はメートル、Z 軸が上、原点は底面の中心。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import build_object, export_usd, materials_from_cfg, new_scene  # noqa: E402


def main():
    cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
    new_scene()
    mats = materials_from_cfg(cfg["materials"])
    for spec in cfg["objects"]:
        build_object(spec, mats)
    export_usd(cfg)


main()
