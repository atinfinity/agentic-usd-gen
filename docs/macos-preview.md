# macOS でのプレビュー

- **Quick Look**: `--usdz` で作った `.usdz` を Finder でスペースキー。PreviewSurface で表示されます。
- **Reality Composer Pro**（Xcode に付属）: `.usdz` または `.usd` を開きます。
- **Blender**: `--preview` で `debug/preview_*.png` を描画します。`.usd` を Blender に直接読み込むこともできます。
- `usdview` は usd-core に含まれていません。

MDL（OmniPBR / OmniGlass / OmniSurface）は Isaac Sim に組み込まれているマテリアルなので、Mac では解決できません。
そのため検証では、MDL に関するエラーは想定内として扱います（`meta.json` の `expected_mdl_issues`）。
OpenPBR などの MaterialX のノードも、usd-core には MaterialX のプラグイン（usdMtlx）がないので OpenUSD の検証では見つかりません。
MaterialX の標準ライブラリ（`materialx` パッケージ）にあるノードは想定内として扱います。
