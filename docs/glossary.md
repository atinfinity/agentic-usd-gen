# 用語

このドキュメントで説明なしに使っている言葉です。

| 言葉 | 意味 |
|---|---|
| slug | アセットの名前。英小文字・数字・`_` で書く（例: `soda_pet_500ml`）。出力のフォルダ名と、USD のルート Prim の名前になる。架空の商品は slug で指定する（`agentic-usd-gen-fictional --list` で一覧） |
| `shape_class` | 形状の種類。`revolve`（回転体）・`pouch`（袋）・`box`（箱）・`assembly`（部品の組み合わせ）の 4 つ（[形状と spec.json](shapes.md)） |
| `spec.json` | 作る物の寸法・形状・色・質量・部品などを書いたファイル。検索の結果か、架空の商品の定義から作られる。編集して作り直せる（[spec.json と検索キャッシュ](shapes.md#specjson-と検索キャッシュ)） |
| `vision.json` | どの画像を使うか、キャップ・ラベル・液面がどの高さにあるか、どの面にどの画像を貼るかを書いたファイル |
| キャッシュ（`cache/`） | `spec.json`・`vision.json`・画像を商品ごとに置くフォルダ。あれば検索し直さない。架空の商品は `cache/fictional/<品名>/` |
| `out/` | 作ったアセットが入るフォルダ（`out/<slug>/`）。USD・テクスチャ・`meta.json`・プレビューが入る（[出力](output.md)） |
| `assets/` | `agentic-usd-gen-export` で書き出した、リポジトリで管理する形のアセット。分類・版ごとのフォルダとレイヤーに分かれる（[リポジトリ管理用の書き出し](export.md)） |
| アセット | 1 つの商品・什器の USD と、そのテクスチャなどのまとまり |
| USD（OpenUSD） | 3D シーンを記述するファイル形式。`.usd`（バイナリ）・`.usda`（テキスト）・`.usdz`（1 つにまとめたもの）がある |
| Prim | USD の中の 1 つの要素（メッシュ・マテリアル・関節など）。ルート Prim は、アセットのいちばん上の要素 |
| レイヤー | USD を分けて書いたファイル。書き出したアセットは、形・マテリアル・物理などを別のレイヤーに分ける |
| バリアント | 1 つのアセットの中で切り替えられる見た目や状態（画面の表示、照明の点灯、絵柄など）。USD の VariantSet（[バリアント](shapes.md#バリアント)） |
| SimReady | シミュレーションで使える USD アセットの要件を NVIDIA がまとめたもの。`agentic-usd-gen-simready` で確かめる（[検証](validation.md)） |
| 要件 ID | `NP.005`・`FET_005` のような SimReady の番号（[SimReady の要件 ID](validation.md#simready-の要件-id)） |
| MDL・MaterialX・OpenPBR | マテリアル（表面の見た目）の書き方。MDL は Isaac Sim・Omniverse 向け、MaterialX の OpenPBR はそれ以外のレンダラー向けに付ける（[リポジトリ管理用の書き出し](export.md)） |
| 剛体・コリジョン | 物理の設定。剛体は動く物、コリジョンは当たり判定の形 |
| `static` | 動かない什器・内装にする指定。剛体を付けず、コリジョンだけにする（[据え置きと取り付け](shapes.md#据え置きと取り付け)） |
| 関節 | 扉・ふた・引き出しなど、動く部分のつなぎ方（[関節](shapes.md#関節)） |
| 把持の線 | ロボットがつかむ位置を表す線（[把持の線](export.md#把持の線)） |
| 落下テスト | Isaac Sim でアセットを落として、すり抜け・跳ね・静止を確かめるテスト（[検証](validation.md#落下テスト)） |
