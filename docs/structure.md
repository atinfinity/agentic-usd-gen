# ソースの構成

2行目からのファイルは、どれも`src/agentic_usd_gen/`の下にあります。

| ファイル | 役割 |
|---|---|
| `src/agentic_usd_gen/cli.py` | コマンドライン、全体の流れ |
| `search.py` / `vision.py` / `llm.py` | Claudeによる検索・画像判定 |
| `images.py` | 画像のダウンロード |
| `profile.py` / `label.py` | 輪郭抽出・半径プロファイル・ラベルの展開 |
| `shapes/` | 形状クラスごとの生成処理（`revolve`・`pouch`・`box`・`assembly`）。新しい形状はここに追加 |
| `blender/` | Blender内で動くスクリプト（回転体・任意メッシュのモデリング、プレビュー描画、共通処理） |
| `usd_post.py` / `validate.py` | USDの後処理と検証 |
| `joints.py` / `physics_runtimes.py` | 可動部の剛体と関節、MuJoCo・Newtonのスキーマ |
| `finish.py` / `physics_material.py` | 素材ごとの粗さ・金属度と、物理マテリアル（摩擦・反発） |
| `openpbr.py` / `nonvisual.py` | MaterialXのOpenPBRと、センサー向けの属性 |
| `grasp.py` / `qcode.py` | 把持の線と、商品の種類を表すWikidataのQコード |
| `lighting.py` | 什器に内蔵する照明（UsdLux）と`Lighting`バリアント |
| `screen.py` | 光る画面の`Screen`バリアント（On = 画像を映す / Off = 消えた画面） |
| `picture.py` | 店向けの絵柄の`Picture`バリアント（Default = 絵柄 / Blank = 無地） |
| `isaac_layout.py` | 書き出すUSDをIsaac Simのレイヤー構成（base・meshes・physics）に分ける |
| `catalog.py` | `agentic-usd-gen-export`（モデルカード・サムネイル・一覧の書き出し） |
| `simready.py` | `agentic-usd-gen-simready`（SimReady Foundationのプロファイルでの検証） |
| `drop_test.py` / `isaac/drop_sim.py` | `agentic-usd-gen-droptest`（Isaac Simでの落下テスト。`drop_sim.py`はIsaac SimのPythonで動く） |
| `joint_test.py` / `isaac/joint_sim.py` | `agentic-usd-gen-jointtest`（Isaac Simでの関節の開閉テスト。`joint_sim.py`はIsaac SimのPythonで動く） |
| `visual_check.py` | `agentic-usd-gen-visual`（プレビューと元画像を画像認識で比べる見た目の検証） |
| `fictional/` | `agentic-usd-gen-fictional`（架空の商品。`products.py`デザイン・`forms.py`形・`paint.py`描画） |
