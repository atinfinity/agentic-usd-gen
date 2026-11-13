# 用語

このドキュメントで説明なしに使っている言葉です。

| 言葉 | 意味 |
|---|---|
| slug | アセットの名前。英小文字・数字・`_`で書く（例: `soda_pet_500ml`）。出力のフォルダ名と、USDのルートPrimの名前になる。架空の商品はslugで指定する（`agentic-usd-gen-fictional --list`で一覧） |
| `shape_class` | 形状の種類。`revolve`（回転体）・`pouch`（袋）・`box`（箱）・`assembly`（部品の組み合わせ）の4つ（[形状とspec.json](shapes.md)） |
| `spec.json` | 作る物の寸法・形状・色・質量・部品などを書いたファイル。検索の結果か、架空の商品の定義から作られる。編集して作り直せる（[spec.jsonと検索キャッシュ](shapes.md#specjsonと検索キャッシュ)） |
| `vision.json` | どの画像を使うか、キャップ・ラベル・液面がどの高さにあるか、どの面にどの画像を貼るかを書いたファイル |
| キャッシュ（`cache/`） | `spec.json`・`vision.json`・画像を商品ごとに置くフォルダ。あれば検索し直さない。架空の商品は`cache/fictional/<品名>/` |
| `out/` | 作ったアセットが入るフォルダ（`out/<slug>/`）。USD・テクスチャ・`meta.json`・プレビューが入る（[出力](output.md)） |
| `assets/` | `agentic-usd-gen-export`で書き出した、リポジトリで管理する形のアセット。分類・版ごとのフォルダとレイヤーに分かれる（[リポジトリ管理用の書き出し](export.md)） |
| アセット | 1つの商品・什器のUSDと、そのテクスチャなどのまとまり |
| USD（OpenUSD） | 3Dシーンを記述するファイル形式。`.usd`（バイナリ）・`.usda`（テキスト）・`.usdz`（1つにまとめたもの）がある |
| Prim | USDの中の1つの要素（メッシュ・マテリアル・関節など）。ルートPrimは、アセットのいちばん上の要素 |
| レイヤー | USDを分けて書いたファイル。書き出したアセットは、形・マテリアル・物理などを別のレイヤーに分ける |
| バリアント | 1つのアセットの中で切り替えられる見た目や状態（画面の表示、照明の点灯、絵柄など）。USDのVariantSet（[バリアント](shapes.md#バリアント)） |
| SimReady | シミュレーションで使えるUSDアセットの要件をNVIDIAがまとめたもの。`agentic-usd-gen-simready`で確かめる（[検証](validation.md)） |
| 要件ID | `NP.005`・`FET_005`のようなSimReadyの番号（[SimReadyの要件ID](validation.md#simreadyの要件id)） |
| MDL・MaterialX・OpenPBR | マテリアル（表面の見た目）の書き方。MDLはIsaac Sim・Omniverse向け、MaterialXのOpenPBRはそれ以外のレンダラー向けに付ける（[リポジトリ管理用の書き出し](export.md)） |
| 剛体・コリジョン | 物理の設定。剛体は動く物、コリジョンは当たり判定の形 |
| `static` | 動かない什器・内装にする指定。剛体を付けず、コリジョンだけにする（[据え置きと取り付け](shapes.md#据え置きと取り付け)） |
| 関節 | 扉・ふた・引き出しなど、動く部分のつなぎ方（[関節](shapes.md#関節)） |
| 把持の線 | ロボットがつかむ位置を表す線（[把持の線](export.md#把持の線)） |
| 落下テスト | Isaac Simでアセットを落として、すり抜け・跳ね・静止を確かめるテスト（[検証](validation.md#落下テスト)） |
