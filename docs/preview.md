# プレビュー

作ったUSDを目で確かめる方法です。OSによらない方法と、OSごとの方法があります。

| 方法 | macOS | Windows | Ubuntu | 見えるマテリアル |
|---|---|---|---|---|
| `--preview`（Blenderで画像を描く） | ○ | ○ | ○ | UsdPreviewSurface |
| Blenderに`.usd`を読み込む | ○ | ○ | ○ | UsdPreviewSurface |
| Isaac Simで開く | × | ○ | ○ | MDL（本番の見た目） |
| `usdview` | △ | ○ | ○ | UsdPreviewSurface |
| Quick Look・Reality Composer Pro | ○ | × | × | UsdPreviewSurface |

○ は使える、× は使えない、△ は自分でOpenUSDをビルドすれば使える、です。

> [!NOTE]
> 動作を確かめているのはmacOSと、GitHub ActionsのUbuntu（USDの書き出しと検証まで）です。Windowsでは確かめていません。

## どのOSでも使える方法

### `--preview`の画像

`--preview`を付けると、Blender（Cycles）で正面・斜め・上からの画像を`debug/preview_*.png`に描きます。画面のない環境（SSH先・CI）でも動きます。

```sh
uv run agentic-usd-gen-fictional soda_pet_500ml --out out/fictional --preview
```

Blenderは`--blender`、環境変数`BLENDER`、`PATH`の`blender`の順に探します。

### Blenderに読み込む

「ファイル → インポート → Universal Scene Description」で`<slug>.usd`を開きます。回して確かめたいときに使います。

## macOS

- **Blender**: `/Applications/Blender.app`に置けば、場所の指定は要りません。
- **Quick Look**: `--usdz`で作った`.usdz`をFinderでスペースキー。
- **Reality Composer Pro**（Xcodeに付属）: `.usdz`または`.usd`を開きます。
- **`usdview`**: usd-coreには含まれていません。使うならOpenUSDを自分でビルドします。
- Isaac SimはmacOSでは動きません。MDLの見た目は確かめられません（下の「MDLとMaterialX」）。

## Windows

- **Blender**: [blender.org](https://www.blender.org/download/)のインストーラーか`winget install BlenderFoundation.Blender`で入れます。`blender.exe`は`PATH`に入らないので、場所を指定します。

    ```powershell
    $env:BLENDER = "C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
    uv run agentic-usd-gen-fictional soda_pet_500ml --out out/fictional --preview
    ```

- **Isaac Sim**（Windows 11）: 「File → Open」で`<slug>.usd`を開きます。MDLのマテリアルで表示される、本番と同じ見た目です。
- **`usdview`**: NVIDIAが配っている[ビルド済みのOpenUSD](https://developer.nvidia.com/usd#section-getting-started)に入っています。展開したフォルダで次を実行します。

    ```powershell
    .\scripts\usdview_gui.bat C:\path\to\<slug>.usd
    ```

- `.usdz`をQuick Lookのように手軽に開く標準の手段はありません。Blenderか`usdview`を使います。

## Ubuntu

- **Blender**: `sudo snap install blender --classic`で入れると`PATH`に入ります。[blender.org](https://www.blender.org/download/)のtarを展開したときは`BLENDER`で場所を指定します。

    ```sh
    export BLENDER=~/blender/blender
    uv run agentic-usd-gen-fictional soda_pet_500ml --out out/fictional --preview
    ```

- 画面のないサーバーや最小構成の環境では、Blenderが使うライブラリが足りないことがあります。

    ```sh
    sudo apt-get install -y --no-install-recommends \
      libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 libgl1 libegl1
    ```

- **Isaac Sim**（Ubuntu 22.04 / 24.04）: 「File → Open」で`<slug>.usd`を開きます。MDLのマテリアルで表示される、本番と同じ見た目です。落下テストと関節の開閉テストもここで動きます（[検証](validation.md)）。
- **`usdview`**: NVIDIAが配っている[ビルド済みのOpenUSD](https://developer.nvidia.com/usd#section-getting-started)に入っています。展開したフォルダで次を実行します。

    ```sh
    ./scripts/usdview_gui.sh /path/to/<slug>.usd
    ```

## MDLとMaterialX

MDL（OmniPBR / OmniGlass / OmniSurface）はIsaac Simに組み込まれているマテリアルなので、Isaac Simの外（macOS、Blender、`usdview`）では解決できず、UsdPreviewSurfaceで表示されます。
そのため検証では、MDLに関するエラーは想定内として扱います（`meta.json`の`expected_mdl_issues`）。
OpenPBRなどのMaterialXのノードも、usd-coreにはMaterialXのプラグイン（usdMtlx）がないのでOpenUSDの検証では見つかりません。
MaterialXの標準ライブラリ（`materialx`パッケージ）にあるノードは想定内として扱います。
