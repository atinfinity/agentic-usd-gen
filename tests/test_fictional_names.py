"""架空の商品に実在のメーカー・チェーン・商品の名前が入っていないことと、docs/fictional.md の点数の確認。

全品を描くと 2〜3 分かかるので、描いた文字ではなく src/agentic_usd_gen/fictional/ の文字列リテラル（描く文字・商品名・
タグ・説明の元）を調べる。絵柄そのものの確認は docs/fictional.md の「全品の絵柄を見る」の手順で行う。"""
import ast
import re
from collections import Counter
from pathlib import Path

from agentic_usd_gen.fictional import registry

ROOT = Path(__file__).resolve().parents[1]
FICTIONAL = ROOT / "src/agentic_usd_gen/fictional"

# 実在のメーカー・チェーン・商品の名前（部分一致）。足すときは下の ALLOWED も見直す
REAL_NAMES_JA = """
コカコーラ コカ・コーラ ペプシ サントリー 伊藤園 キリン アサヒ サッポロ ヤクルト カルピス ポカリ アクエリアス
お〜いお茶 おーいお茶 綾鷹 爽健美茶 午後の紅茶 三ツ矢 ファンタ スプライト ジョージア ネスカフェ ネスレ リプトン
明治 森永 ロッテ グリコ ブルボン 不二家 カルビー 湖池屋 亀田 日清 東洋水産 マルちゃん サッポロ一番 エースコック
カップヌードル どん兵衛 チキンラーメン ポッキー プリッツ じゃがりこ かっぱえびせん キットカット プリングルズ
チップスター ハッピーターン 味の素 キッコーマン ヤマサ ミツカン カゴメ キユーピー キューピー ハウス食品 エスビー
永谷園 丸美屋 ニッスイ マルハ 雪印 山崎製パン ヤマザキ パスコ フジパン
花王 ライオン ユニ・チャーム ユニチャーム 資生堂 カネボウ コーセー エステー アース製薬 小林製薬 大正製薬 ロート
サランラップ クレラップ キレイキレイ アタック ファブリーズ ムーニー パンパース メリーズ
セブンイレブン セブン-イレブン ローソン ファミリーマート ファミマ ミニストップ デイリーヤマザキ セイコーマート
イオン イトーヨーカドー 西友 ライフ マツモトキヨシ マツキヨ ウエルシア ツルハ スギ薬局 ダイソー セリア キャンドゥ
無印良品 ニトリ カインズ コーナン コメリ ユニクロ しまむら ヨドバシ ビックカメラ ヤマダ電機 ドン・キホーテ
スターバックス スタバ ドトール タリーズ コメダ マクドナルド ガスト サイゼリヤ デニーズ 吉野家 すき家
ソニー パナソニック シャープ 東芝 日立 三菱電機 富士通 キヤノン エプソン アップル 任天堂 ポケモン 遊戯王
ヤマト運輸 クロネコ 佐川 ゆうパック ジャンプ マガジン サンデー コロコロ シマノ ヨネックス ミズノ アシックス
トヨタ ホンダ ブリヂストン マキタ リョービ アイリスオーヤマ
""".split()
# 英字の名前（大文字小文字を区別せず、語として一致）。apple はりんごのタグに使うので入れない（アップル・iphone で見る）
REAL_NAMES_EN = """
coca-cola coke pepsi suntory kirin asahi sapporo yakult calpis pocari aquarius fanta sprite georgia nescafe nestle
lipton meiji morinaga lotte glico calbee nissin pringles kitkat kikkoman kagome kewpie ajinomoto kao shiseido
pampers lawson familymart seven-eleven 7-eleven ministop aeon daiso seria muji nitori uniqlo ikea costco amazon
starbucks doutor tullys mcdonalds sony panasonic toshiba hitachi sharp canon epson iphone nintendo pokemon
yamato sagawa shimano wilson yonex mizuno asics nike adidas puma toyota honda bridgestone makita ryobi
""".split()

# 実在の名前と同じつづりだが一般の語として使っているもの: 名前 → その名前を含んでよい言い回し
ALLOWED: dict[str, list[str]] = {
    "イオン": ["イオン飲料", "マイナスイオン", "リチウムイオン"],
    "ライフ": ["ドライフルーツ"],
    "ユニクロ": ["ユニクロめっき"],  # 亜鉛めっきの一種
    "グリコ": ["プロピレングリコール"],
    "マガジン": ["マガジンラック"],
}


def _literals() -> list[tuple[str, int, str]]:
    """(ファイル名, 行, 文字列)。docstring は除く。"""
    out = []
    for path in sorted(FICTIONAL.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    docs.add(id(first.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                out.append((path.name, node.lineno, node.value))
    return out


def _strip_allowed(text: str, name: str) -> str:
    for phrase in ALLOWED.get(name, []):
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    return text


def find_real_names(literals) -> list[str]:
    hits = []
    en = {n: re.compile(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", re.IGNORECASE) for n in REAL_NAMES_EN}
    for file, line, text in literals:
        for name in REAL_NAMES_JA:
            if name in text and name in _strip_allowed(text, name):
                hits.append(f"{file}:{line}: {name} in {text[:60]!r}")
        for name, pat in en.items():
            if pat.search(text) and pat.search(_strip_allowed(text, name)):
                hits.append(f"{file}:{line}: {name} in {text[:60]!r}")
    return hits


def test_no_real_names_in_fictional_products():
    literals = _literals()
    assert len(literals) > 5000  # 文字列を拾えている
    hits = find_real_names(literals)
    assert not hits, "実在の名前に見える文字列（一般の語なら ALLOWED に足す）:\n" + "\n".join(hits)


def test_the_check_finds_a_real_name():
    """検査そのものが働く: 実在の名前は見つけ、ALLOWED の言い回しは通す。"""
    assert find_real_names([("x.py", 1, "ポッキー チョコレート")])
    assert find_real_names([("x.py", 1, "SONY TV")])
    assert not find_real_names([("x.py", 1, "appleton pineapple")])  # 語の一部は数えない
    for name, phrases in ALLOWED.items():
        for phrase in phrases:
            assert not find_real_names([("x.py", 1, phrase)]), (name, phrase)
            assert name.lower() in phrase.lower(), (name, phrase)
    # 使われていない除外を残さない
    source = "\n".join(text for _, _, text in _literals())
    unused = [p for phrases in ALLOWED.values() for p in phrases if p not in source]
    assert not unused, unused


def test_fictional_doc_counts_match_the_registry():
    """docs/fictional.md の表（ファイルごとの点数）と合計が、定義と合っている。"""
    per_module = Counter(fn.__module__.rsplit(".", 1)[-1] for fn in registry.PRODUCTS.values())
    text = (ROOT / "docs/fictional.md").read_text(encoding="utf-8")
    total = int(re.search(r"^(\d+) ?点を定義しています", text, re.M).group(1))
    assert total == len(registry.PRODUCTS)
    seen = set()
    for row in re.findall(r"^\|[^|]+\|([^|]+)\|\s*(\d+)\s*\|", text, re.M):
        modules = re.findall(r"`(\w+)\.py`", row[0])
        assert modules, row
        assert sum(per_module[m] for m in modules) == int(row[1]), row
        seen.update(modules)
    assert seen == set(per_module)
