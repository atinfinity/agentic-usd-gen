# 貢献のしかた / Contributing

issue・pull request を歓迎します。日本語でも英語でも構いません。
Issues and pull requests are welcome, in Japanese or English.

## 開発の準備

```sh
uv sync --extra simready
uv run pytest
```

- Python 3.12 以上と [uv](https://docs.astral.sh/uv/) が要ります。
- Blender 4.x があると、USD を実際に書き出すテストも動きます（なければ飛ばします）。場所は環境変数 `BLENDER` で指定できます。
- テストは Anthropic API を呼びません。API キーは要りません。

## ドキュメント

`docs/` は [Zensical](https://zensical.org/) でサイトにします（設定は `zensical.toml`）。

```sh
uv run --group docs zensical serve    # http://localhost:8000 で確かめる
uv run --group docs zensical build    # site/ に書き出す
```

- GitHub でもサイトでも同じに見えるよう、箇条書きの中の箇条書き・表・コードは 4 つの空白で字下げし、箇条書きの前は 1 行空けてください。
- 図は Markdown の画像（`![説明](図.svg)`）で入れてください。

## pull request を出す前に

- `uv run pytest` が通ることを確かめてください。
- 変更の理由を pull request の説明に書いてください。見た目が変わる変更には、前後の画像があると助かります。
- 大きな変更は、先に issue で相談してください。

## 受け取れないもの

このリポジトリは、公開できる素材だけで成り立つようにしています。

> [!IMPORTANT]
> 実在の商品・店・会社の名前、ロゴ、キャラクター、商品写真を含む変更は受け取れません。

- 架空の商品（`src/agentic_usd_gen/fictional/`）には、一般的な品名（種類・味・容量）だけを使います。
- 実在の商品のラベルにある決まり文句や、特定の商品を連想させる色・柄・容器の形の組み合わせも避けてください。
- 写真を足すときは、CC0 かパブリックドメインのものに限ります。`src/agentic_usd_gen/data/photos/photos.json` に出典のページ・作者・ライセンスを書いてください。
- API キーや `.env` の中身を、issue・pull request・コミットに含めないでください。

## ライセンス

寄せられたコードは、このリポジトリと同じ [Apache License 2.0](LICENSE) で受け取ります（Apache License 2.0 の 5 条のとおり）。CLA や署名（DCO）は求めません。

## 行動規範

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) に従ってください。
