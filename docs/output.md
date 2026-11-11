# 出力

```
out/<slug>/
  <slug>.usd            # 本体（バイナリ crate 形式）
  <slug>.usda / .usdz   # オプション
  textures/label.png    # ラベルの展開テクスチャ（透明・半透明の容器は裏面の label_back.png も）
  meta.json             # 寸法・出典・質量・重心・テクスチャの画素密度・透明な部品・把持の線・警告・検証結果
  debug/                # silhouette.png（輪郭と部位の判定）、preview_*.png、thumbnail.png、masks/（透明な部品の検査用）、Blender のログと .blend
```

テクスチャの解像度は、貼る表面の実寸から決めます（1 mm あたり 8 px 以上になる 2 のべき乗、一辺は最大 4096 px）。
箱は 6 面を 1 枚に並べるので、1 面は最大 2048 px です。元の画像が小さいときは、それにいちばん近い 2 のべき乗までにとどめます。
実際の大きさと画素密度は `meta.json` の `textures` に記録します。

USD の内容は次のとおりです。

- ステージ: メートル単位（`metersPerUnit = 1`）、Z 軸が上、原点は底面の中心、`defaultPrim` 設定済み、`kind = component`
- `/<slug>`: `RigidBodyAPI` と `MassAPI`（中身込みの質量と重心）
  - `Body`・`Cap`: `CollisionAPI`（既定は凸包。部品ごとに変えられる）＋物理マテリアル（素材ごとの摩擦・反発。[書き出しとメタデータ](export.md#検索用のメタデータ)の表）
  - `Liquid`（透明・半透明の容器のみ）・`Label`: 見た目だけで、コリジョンなし
  - `_materials/*`: 各マテリアルが UsdPreviewSurface・MDL（`OmniGlass` / `OmniPBR` / `OmniSurface`）・MaterialX の OpenPBR（[書き出しとメタデータ](export.md#検索用のメタデータ)）の 3 つを持つ。液体は `OmniSurface` の透過で、色の付いた液体は胴の中心を通る光（内径ぶん）がちょうど液体の色になるよう体積吸収させる（縁は薄く、中心は濃く見える）。濁った液体（ジュース・乳飲料など。`colors.liquid_turbidity` が 0〜1、未設定なら商品名・タグから推定）は、さらに体積散乱（`specular_transmission_scattering_color` に散乱係数、`specular_transmission_scatter_anisotropy` に 0.2）を足し、胴の中心を通る光の光学的な厚さを 60 × 濁り^2.5 にする。UsdPreviewSurface では濁りに応じてオパシティを上げる。PET の容器とガラス瓶は `OmniGlass` の `thin_walled`（薄い膜。屈折させない。ガラス瓶は屈折率 1.52 と薄い緑の色味で、厚い底と口の縁は形で表す）。半透明の容器・部品は `OmniSurface` の `thin_walled` で、一部をぼやけたまま素通しにし（`frosted` は 7 割、`translucent` は 4.5 割）、残りは 7:3 で拡散透過と拡散反射にする。UsdPreviewSurface ではオパシティで近似する

物理には UsdPhysics だけを使い、PhysxSchema は使いません。

## 透明・半透明の部品（深度センサー向け）

実物の深度カメラ（ステレオ・ToF）は、透明・半透明の物体の深度をうまく測れません（欠損する、奥の背景の深度になる）。
合成データの深度は完璧なので、そのまま学習に使うと実機とずれます。加工できるよう、透明・半透明のメッシュにカスタム属性
`agenticUsdGen:transparency`（token）を付け、`meta.json` の `transparency` にも一覧（ルートからのパス → 透け方）を書きます。

| 値 | 付くメッシュ |
|---|---|
| `transparent` | 透明な容器（PET など）・ガラス瓶・`finish: glass` の部品、澄んだ液体（`colors.liquid_turbidity` が 0.5 未満） |
| `translucent` | 半透明の容器（HDPE・`frosted` など）・`finish: frosted` / `translucent` の部品、濁った液体（0.5 以上） |

不透明な部品（キャップ・ラベル・缶・紙パックなど）には付けません。1 つのメッシュの面ごとにマテリアルを分けている場合は、
いちばん面の多いマテリアルで決めます。

`transparent` のメッシュには `primvars:doNotCastShadows = true`（constant）も付け、影を落とさないようにします。
Isaac Sim の RTX Real-Time では `OmniGlass` や透過の `OmniSurface` も不透明な影を落とすため、付けないと
ケースの中の商品・包装の中身・ボトルの下半分が黒くなります。`translucent` は実物でも影ができるので付けません。

```json
"transparency": {"Body": "transparent", "Liquid": "transparent"}
```

Isaac Sim の Replicator では、インスタンスのセグメンテーション（プリムのパスが分かる）と深度を一緒に取り、
`agenticUsdGen:transparency` の付いたプリムの画素の深度を欠損（`inf`）にする、といった使い方ができます。

```python
import numpy as np
import omni.replicator.core as rep
import omni.usd

stage = omni.usd.get_context().get_stage()
rp = rep.create.render_product(camera, (1280, 720))
depth = rep.AnnotatorRegistry.get_annotator("distance_to_image_plane")
inst = rep.AnnotatorRegistry.get_annotator("instance_id_segmentation", init_params={"colorize": False})
depth.attach(rp)
inst.attach(rp)
rep.orchestrator.step()

d = depth.get_data().copy()
seg = inst.get_data()
for id_, path in seg["info"]["idToLabels"].items():
    attr = stage.GetPrimAtPath(path).GetAttribute("agenticUsdGen:transparency")
    if attr and attr.Get() == "transparent":  # translucent も欠損にするか、ノイズを足すかは用途に合わせる
        d[seg["data"] == int(id_)] = np.inf
```
