# 準備と使い方

入れ方、API キーが要る場合、2 つのコマンドの使い方とオプションです。言葉の意味は [用語](glossary.md) にまとめています。

## 準備

- Python 3.12 以上と [uv](https://docs.astral.sh/uv/)
- Blender 4.x（macOS は `/Applications/Blender.app` に置くか、`--blender` / 環境変数 `BLENDER` で場所を指定。Windows・Ubuntu は [プレビュー](preview.md)）
- Anthropic API キー（実在の商品を検索して新しく作るときだけ。下記）

Isaac Sim は、作る・書き出す・SimReady の検証には要りません。要るのは、任意の確認である落下テストと関節の開閉テストだけです（[検証](validation.md)）。

```sh
git clone https://github.com/atinfinity/agentic-usd-gen.git && cd agentic-usd-gen
uv sync
cp .env.example .env   # 商品名から検索して作るときだけ。ANTHROPIC_API_KEY=... を記入
```

架空の商品だけを作るなら、`.env` は要りません。

> [!IMPORTANT]
> `src/agentic_usd_gen/blender/` のスクリプトは Blender の中で動き、Blender の Python API（`bpy`）を使います。Blender 本体は含みません。

> [!WARNING]
> 商品名から検索して作ると、Anthropic API の料金がかかります（既定のモデルは `claude-opus-5-5`。検索・画像認識・`--visual-check` で呼びます）。下の「キーがなくても動く」場合は、料金はかかりません。

API キーを使うのは、商品名から寸法・形状・画像を検索するとき（`search.py`）と、画像から使う 1 枚とキャップ・ラベルの位置を決めるとき（`vision.py`）だけです。次の場合はキーがなくても動きます。

- 検索キャッシュ（`cache/<商品名>/` の `spec.json`・`vision.json`）がある商品の作り直し（`--refresh` を付けない限り検索しない）
- `agentic-usd-gen-fictional`（架空の商品。キャッシュを自分で書いてから生成する）
- `agentic-usd-gen-export`、テスト
- `--dims` と `--image` で寸法と画像を手で渡したとき（検索を省略し、部位の位置は経験則で決める）

## 使い方

実在の商品を検索して作る例です。

```sh
uv run agentic-usd-gen "緑茶 600ml PET" --usdz --preview
```

`<商品名>` には検索したい商品の名前を入れます。名前に空白があるときは、シェルが 1 つの引数として渡すように引用符で囲みます（例: `agentic-usd-gen "緑茶 600ml PET"`）。空白がなければ引用符は要りません。

架空の商品を作る例です（API キーは要りません）。

```sh
uv run agentic-usd-gen-fictional soda_pet_500ml --out out/fictional --preview
```

- `soda_pet_500ml` は作る商品の名前（slug）です。ほかの slug に替えたり、空白で区切っていくつも並べたりできます。`--all` を付けると 565 点すべてを作ります。
- 指定できる slug は `uv run agentic-usd-gen-fictional --list` で、分類・形状・品名と一緒に一覧できます（何も作りません）。後ろに語を並べると絞り込めます（例: `--list pouch food`）。分野ごとのまとめは [架空の商品](fictional.md) にあります。
- 下の表のオプションは、`--dims`・`--image`・`--slug`・`--refresh` など検索して作るとき専用のものを除いて、`agentic-usd-gen-fictional` にもそのまま渡せます。

`agentic-usd-gen` のオプション:

| オプション | 説明 |
|---|---|
| `--out DIR` | 出力先（既定 `out/`）。アセットは `<出力先>/<slug>/` にできる（[出力](output.md)） |
| `--cache DIR` | 検索結果と画像を置くキャッシュ（既定 `cache/`） |
| `--blender PATH` | Blender の実行ファイルの場所 |
| `--dims H=0.205,D=0.065[,CAP_H=..,CAP_D=..,T=..]` | 寸法を上書き（メートル）。袋は H がシール間の長さ、D が幅、T が厚さ。箱は D が正面の横幅、T が奥行き |
| `--image PATH` | 側面画像を直接指定する（複数指定可）。指定するとダウンロードしない |
| `--slug NAME` | 出力名とルート Prim 名 |
| `--orientation upright\|lying` | 置き方（袋のみ。既定は `spec.json` の `orientation`、なければ `upright`） |
| `--refresh` | キャッシュを使わず検索し直す |
| `--model` | Claude のモデル（既定 `claude-opus-5-5`） |
| `--usda` / `--usdz` | テキスト版 / Quick Look 用 usdz も書き出す |
| `--preview` | Blender（Cycles）で正面・斜め・上からのプレビューを描画する |
| `--visual-check` | プレビューと元画像を画像認識で比べ、見た目の点数を `meta.json` に書く（`--preview` と API キーが要る。[見た目の検証](validation.md#見た目の検証)） |
| `--no-physics` | 剛体・質量・コリジョンを付けない |

形状ごとの寸法の決め方と、`spec.json` に書ける項目（部品・関節・照明・バリアントなど）は [形状と spec.json](shapes.md) にあります。

作ったあとは、`agentic-usd-gen-export` でリポジトリ管理用の形に書き出し、検証のコマンドで確かめます。

![コマンドとフォルダの関係: agentic-usd-gen か agentic-usd-gen-fictional で out/ に作り、agentic-usd-gen-export で assets/ に書き出す。out/ は agentic-usd-gen-visual で、assets/ は agentic-usd-gen-simready・agentic-usd-gen-droptest・agentic-usd-gen-jointtest で確かめる](commands.svg)
