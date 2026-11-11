# 検証

書き出しのたびに次を確認し、結果を `meta.json` に記録します。

- ステージの規約
- バウンディングボックスと寸法の一致（許容 5%。袋は膨らむと縮むので、平らな寸法ではなく膨らんだ形の計算値と比べる。箱と部品の組み合わせは幅・奥行き・高さと比べる）
- 物理 API が付いていること（`static` ならキネマティックな剛体、それ以外は動く剛体で、どちらも質量があること）。
  可動部の剛体は質量があり、関節で本体につながっていること
- マテリアルの出力とテクスチャのパス
- OpenUSD の UsdValidation
- `.usdz` は `usdchecker --arkit`

Isaac Sim での落下・静止の確認は下の「落下テスト」で、扉・ふたの開閉の確認は「関節の開閉テスト」で行います（Isaac Sim のある環境で）。

## SimReady の検証

書き出したアセットが [SimReady Foundation](https://github.com/NVIDIA/simready-foundation) の規約に合っているかを、NVIDIA の [simready-validate](https://pypi.org/project/simready-validate/) で確かめます（既定のプロファイルは `Robotics-Prop`）。
検証ツールは任意の依存なので、使うときだけ入れます。

```sh
uv sync --extra simready
uv run agentic-usd-gen-simready                       # assets/ の下の .usd をすべて
uv run agentic-usd-gen-simready assets/food -v        # フォルダやファイルを指定。-v で不適合の場所と未対応の任意の機能も出す
uv run agentic-usd-gen-simready --output report.json  # 結果を JSON でも書き出す
```

> [!NOTE]
> Isaac Sim の入っていない環境（Mac など）では、MDL の参照先が見つからず `NP.008` が出ます。これは想定内として数え、合否に含めません。Isaac Sim の環境では `--strict-mdl` を付けて確かめます。

- 不適合は要件 ID（`NP.005` など）ごとにまとめて表示します。1 点でも不合格なら終了コードは 1 です。
- MDL（OmniPBR / OmniGlass / OmniSurface）は Isaac Sim に組み込まれているので、Mac では参照先が見つからず `NP.008` で落ちます。これは想定内として数え、合否に含めません。Isaac Sim の環境では `--strict-mdl` を付けて確かめます。
- `simready-validate` は MDL の検索パスではなく USD の resolver で参照を解決するので、Isaac Sim の環境でも `--strict-mdl` を付けるだけでは `NP.008` で落ちます。Isaac Sim の MDL のフォルダを resolver の検索パスに入れて動かします。Isaac Sim（Kit）自身は環境変数なしでこれらの MDL を解決します。

  ```sh
  export PXR_AR_DEFAULT_SEARCH_PATH=<Isaac Sim の venv>/lib/python3.12/site-packages/isaacsim/kit/mdl/core/Base
  uv run agentic-usd-gen-simready --strict-mdl
  ```

  Isaac Sim 6.1.0（pip 版、Linux）で、このツールで作った架空のアセット 139 点がこの方法で合格することを確認しました。RTX で描画しても、OmniGlass の透け方とラベルのテクスチャは崩れません。
- 任意の機能（把持・OpenPBR など）は満たさなくても合格です。`-v` では満たしていない理由（要件 ID と最初のメッセージ）も出します。

## 落下テスト

書き出したアセットを Isaac Sim（headless）で床に落とし、倒れ・跳ね・床の突き抜け・静止までの時間を確かめます。重心や質量の誤りを見つけるためのものです。
Isaac Sim の Python（上の SimReady の検証と同じ環境）で `src/agentic_usd_gen/isaac/drop_sim.py` を 1 回起動し、全点を順に落とします（描画なしで PhysX を直接進めるので、139 点で 1 分ほど）。
判定は usd-core の環境の `agentic-usd-gen-droptest` が行います。

```sh
export ISAACSIM_PYTHON=~/isaacsim-venv/bin/python   # pip 版の Isaac Sim の venv の python（または ISAACSIM_PATH に python.sh のあるフォルダ。既定 ~/isaacsim）
uv run agentic-usd-gen-droptest                              # assets/ の下の .usd をすべて
uv run agentic-usd-gen-droptest assets/beverage              # フォルダやファイルを指定
uv run agentic-usd-gen-droptest --output drop.json --series  # 結果を JSON でも書き出す（--series で重心・傾き・速さの推移も）
```

1 点につき 2 回動かします。

- **落下**: 書き出したままの向きで、底を `--height`（既定 0.2 m）浮かせてまっすぐ落とし、`--seconds`（既定 5 秒）見る。
- **傾け置き**: `--tilt`（既定 2°）傾けて床すれすれに置き、立っていられるかを見る（まっすぐ落とすと、立たない形も釣り合ったまま立ってしまうため）。

| 判定 | 不合格になる条件（既定） |
|---|---|
| 倒れた | 止まったときの傾きが 15° を超え（`--max-tilt`）、重心が置いたときより 1 割以上下がった（寝かせた円筒が転がっただけは除く） |
| 跳ねすぎ | 着地後に重心が跳ね上がった高さが、重心が落ちた高さ（倒れなければ落とした高さ。倒れた扉などは倒れた分も含む）の 25% を超えた（`--max-bounce`） |
| 床を突き抜けた | 止まったときにコリジョンの頂点が床より 10 mm を超えて下にある |
| 静止しない | 最後の 0.5 秒のうちに、重心が 1 cm/s 以上か、回転が 0.1 rad/s 以上で動いている |
| 転がった・滑った | 止まった位置が水平に 5 cm 以上ずれた（`--max-drift`） |

- 置いた向きの接地面（底から 2 mm 以内のコリジョンの頂点の凸包）と重心から、静かに傾けたとき倒れ始める角度を計算します。5° 未満の形（薄いカード・自立しない袋・細長い傘など）は、倒れても形のとおりなので合否に含めず、注記にします。
- 倒れ始める角度が十分あるのに倒れたものは、重心かコリジョンの形を確かめてください。
- 什器（キネマティックな剛体）も、テストの間だけ動く剛体にして落とします（ファイルは変えません）。
- 天井付けの什器（`asset.json` の `mount` が `ceiling`。仕様の `mount`）は、上下を返して取り付け面を下にして落とします。書き出したままの向きだと、ドーム型の監視カメラは半球が下になって転がるためです。
- 1 点でも不合格なら終了コードは 1 です。Isaac Sim のログは `--log`（既定は一時フォルダの `agentic-usd-gen-droptest.log`）に書きます。
- 物理の刻みは Isaac Sim の既定と同じ 60 Hz です（`--hz`）。Isaac Sim 6.1.0（pip 版）で確かめています。

## 関節の開閉テスト

扉・ふたなどの関節（RevoluteJoint・PrismaticJoint）を Isaac Sim（headless）で動かし、限界まで開閉できるか・限界で止まるかを確かめます。
落下テストと同じく、Isaac Sim の Python で `src/agentic_usd_gen/isaac/joint_sim.py` を 1 回起動し、判定は `agentic-usd-gen-jointtest` が行います。関節のない USD は除きます。

```sh
uv run agentic-usd-gen-jointtest                               # assets/ の下の、関節のある .usd をすべて
uv run agentic-usd-gen-jointtest assets/environment            # フォルダやファイルを指定
uv run agentic-usd-gen-jointtest --output joint.json --series  # 結果を JSON でも書き出す（--series で関節の位置の推移も）
```

- 本体は床に固定します（什器はもともとキネマティックな剛体。動く商品もテストの間だけ固定します）。
- 関節ごとに、下限・上限と、その外側（回転は 20°、直動は 0.2 m）を目標にして、その関節にだけ位置ドライブを付けて `--seconds`（既定 4 秒）動かします。ほかの関節は自由なままです。
- 関節の位置は、置いたままの姿勢を 0 とした角度（度）か距離（m）です。
- 一覧には、目標ごとに止まった位置と、いちばん大きく開いたときの可動部の重心の動き（例: `-X 0.38 m・+Y 0.42 m`）を出します。開く向きが仕様のとおりか（奥へ開く、タンク側へ上がる、など）はこれで確かめます。

| 判定 | 不合格になる条件（既定） |
|---|---|
| 届かない | 限界を狙って、限界より 3° か 20 mm 以上手前で止まった（`--reach-deg`・`--reach-m`）。枠や本体のコリジョンにぶつかっている |
| 限界を超えた | 限界の外を狙って、限界を 1° か 5 mm より超えて止まった |
| 止まらない | 最後の 0.5 秒に 0.2° か 2 mm より動いている |
| 本体が動いた | 床に固定した本体が 1 mm より動いた |

- 1 点でも不合格なら終了コードは 1 です。Isaac Sim のログは `--log`（既定は一時フォルダの `agentic-usd-gen-jointtest.log`）に書きます。
- このツールで作った関節のある架空のアセット 8 点（扉 5 点・便器のふた・ケースの扉）で、Isaac Sim 6.1.0（pip 版）で確かめています。

## 見た目の検証

プレビュー（`debug/preview_*.png`）と、生成に使った元画像（キャッシュの `images/`）を Claude の画像認識で比べ、再現の度合いを 0〜100 点で採点します。
API キー（`ANTHROPIC_API_KEY`）が要ります。なければ何もせずに終わります。

```sh
uv run agentic-usd-gen-fictional --all --out out/fictional --preview   # 先にプレビューを描く
uv run agentic-usd-gen-visual out/fictional                            # 全点を検証し、点の低い順に並べる
uv run agentic-usd-gen-visual out/fictional/cup_noodle_tall            # 1 点だけ
uv run agentic-usd-gen-visual out/fictional --baseline old/fictional   # 別の出力と比べる
uv run agentic-usd-gen-visual out/fictional --report visual.json       # 結果を JSON でも書き出す
```

- 結果は各アセットの `meta.json` の `visual_check` に書きます（`score`・`issues`・`summary`・`model`・`date`）。`issues` の `kind` は `seam`（継ぎ目）・`stretch`（伸び・歪み）・`flip`（反転）・`color`（色）・`missing`（欠け）・`shape`（形）・`other` です。
- 前回の結果は `visual_check_previous` に移します。`agentic-usd-gen` で作り直しても残すので、作り直してから検証すると、点が `--drop`（既定 10）以上下がったアセットを「点の下がったもの」として出せます。`--baseline` を付けると、前回の結果ではなく別の出力先の同じアセットと比べます。
- `--threshold`（既定 70）未満のアセットを「点の低いもの」として出します。`--jobs` で同時に問い合わせる数を変えられます（既定 4）。
- 照明・背景・反射の違いや、元画像にない面（底・裏）は減点しないように指示しています。点数は目安なので、低いものはプレビューを目で見て確かめてください。

### 透明な部品の見え方

透明な物体はプレビューで破綻しても（液体が白く濁る・真っ黒・見えないなど）気づきにくいので、`--preview` のときに画素の色でも確かめます（API キーは要りません）。
プレビューと一緒に、液体・透明な容器・不透明な部品を塗り分けたマスク（`debug/masks/`）を描き、正面と斜めの 2 方向で測ります。

- **液体**: 見えている液体の色（中央値）と期待の色との差が ΔE 18 を超えると警告します。期待の色は、液体の色（`colors.liquid`）を透かした背景に、表面の映り込み（背景の 1 割ほど）を足したものです（係数は液体のある架空の商品 20 点のプレビューに合わせました）。コーラ・醤油のような濃い液体は映り込みだけが見えて黒に近い灰色になるのが正しいので、真っ黒に描かれても警告しません。半透明の容器の奥の液体は、もともと白っぽく見えるので測りません。
- **透明な容器**: 中身も不透明な部品もない所（液面より上など）の明るさが、背景より L* で 20 以上暗い・明るいと警告します。
- **液体の欠け**: 液体があるはず（生成時に液面を決めた）なのに、USD に液体のメッシュがない、またはプレビューでほとんど見えない（400 px 未満。ラベルで覆われているなど）と警告します。液体のメッシュの数は `debug/masks/info.json` に書きます。
- 結果は `meta.json` の `preview_check`（期待の色・測った色・ΔE・ΔL*）に書き、警告は `warnings` にも入れます。`agentic-usd-gen-visual` も同じ検査をして一覧に出します（API キーがなければこの検査だけ行います）。
