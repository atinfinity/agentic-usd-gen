# agentic-usd-gen

商品名から寸法と画像を検索し、Blender で 3D モデルを作って Isaac Sim 向けの USD を書き出すツールです。
Claude が寸法と画像を調べ、Blender が形を作り、OpenUSD（`pxr`）が物理とマテリアルを付けて検証します。

> [!IMPORTANT]
> NVIDIA の公式のものではありません。Isaac Sim・Omniverse・SimReady は NVIDIA Corporation の商標です。

## 入口は 2 つ

| 入口 | 何をするか | API キー | 作ったアセットの公開 |
|---|---|---|---|
| `agentic-usd-gen "商品名"` | 実在の商品を検索し、商品ページの画像をテクスチャにして作る | 要る | できない |
| `agentic-usd-gen-fictional` | [架空の商品](fictional.md) 565 点（商品・什器・内装）を、実在の商品名・ロゴ・商品写真を使わずに描いて作る | 要らない | できる |

> [!CAUTION]
> `agentic-usd-gen "商品名"` で作ったアセットは、実在の商品の画像を含みます。画像の権利は元の権利者にあるので、そのアセット（テクスチャ・USD）を公開・再配布しないでください。公開するアセットは `agentic-usd-gen-fictional` で作ります。

`agentic-usd-gen "商品名"` の処理の流れ（回転体の場合）:

![処理の流れ: 商品名から、(1) Claude が検索で寸法・色・画像 URL を取得、(2) 画像をダウンロード、(3) Claude の画像認識で側面画像とキャップ・ラベル・液面の位置を判定、(4) OpenCV で輪郭から半径プロファイルを作成、(5) Blender で回転体を作って USD に書き出し、(6) pxr で物理・MDL マテリアルを付けて検証し、USD アセットができる](pipeline.svg)

## 試す

[uv](https://docs.astral.sh/uv/) と Blender 4.x が要ります。架空の商品なら API キーは要りません。

```sh
git clone https://github.com/atinfinity/agentic-usd-gen.git && cd agentic-usd-gen
uv sync
uv run agentic-usd-gen-fictional soda_pet_500ml --out out/fictional --preview
```

準備とオプションの詳しい説明は、リポジトリの [README](https://github.com/atinfinity/agentic-usd-gen#readme) にあります。

## 作ってから確かめるまで

![コマンドとフォルダの関係: agentic-usd-gen か agentic-usd-gen-fictional で out/ に作り、agentic-usd-gen-export で assets/ に書き出す。out/ は agentic-usd-gen-visual で、assets/ は agentic-usd-gen-simready・agentic-usd-gen-droptest・agentic-usd-gen-jointtest で確かめる](commands.svg)

| ページ | 内容 |
|---|---|
| [形状と spec.json](shapes.md) | 回転体・袋・箱・部品の組み合わせの作り方と、`spec.json` に書ける項目（関節・照明・バリアントなど） |
| [架空の商品](fictional.md) | 公開できるアセットの一覧と作り方 |
| [出力](output.md) | `out/<slug>/` の中身、USD の内容、透明・半透明の部品（深度センサー向け） |
| [書き出し](export.md) | `agentic-usd-gen-export`、レイヤー構成、バージョン、メタデータ・マテリアル・物理マテリアル |
| [検証](validation.md) | SimReady・落下テスト・関節の開閉テスト・見た目の検証 |
| [macOS でのプレビュー](macos-preview.md) | Quick Look などでの確認と、MDL・MaterialX の想定内のエラー |
| [USD Search](usd-search.md) | NVIDIA USD Search で `assets/` を検索する設定例 |
| [ソースの構成](structure.md) | ファイルごとの役割 |

## ライセンス

コードは [Apache License 2.0](https://github.com/atinfinity/agentic-usd-gen/blob/main/LICENSE) です。同梱している書体・写真は、それぞれのライセンスに従います（[NOTICE](https://github.com/atinfinity/agentic-usd-gen/blob/main/NOTICE)）。
