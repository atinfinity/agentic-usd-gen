"""見た目の検証（visual_check）のテスト。Claude の呼び出しは差し替える。"""

import json
import logging

import numpy as np
import pytest
from PIL import Image

from agentic_usd_gen import visual_check as vc


def _png(path, color=(200, 30, 30)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.full((40, 30, 3), color, np.uint8)).save(path)
    return path


def _asset(root, slug, cache, previews=("front", "34", "top"), **meta):
    d = root / slug
    d.mkdir(parents=True, exist_ok=True)
    for v in previews:
        _png(d / "debug" / f"preview_{v}.png")
    (d / "meta.json").write_text(json.dumps({"product_name": f"商品 {slug}", "cache_dir": str(cache), **meta}))
    return d


@pytest.fixture
def cache(tmp_path):
    c = tmp_path / "cache" / "x"
    for i in range(8):
        _png(c / "images" / f"{i:02d}.png")
    return c


@pytest.fixture
def fake(monkeypatch):
    """slug ごとに点を返す偽の request_json。呼び出しの中身も記録する。"""
    scores: dict[str, int] = {}
    calls: list[dict] = []

    def request_json(*, model, system, content, schema, tools=None, effort="high"):
        calls.append({"model": model, "content": content, "schema": schema, "effort": effort})
        name = content[-1]["text"].removeprefix("商品名: 商品 ")
        return {"score": scores.get(name, 90), "summary": f"{name} の要約",
                "issues": [{"kind": "seam", "severity": "low", "detail": "継ぎ目"},
                           {"kind": "unknown", "severity": "low", "detail": "捨てる"}]}

    monkeypatch.setattr(vc, "request_json", request_json)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    return scores, calls


def test_check_visual_content(tmp_path, cache, fake):
    _, calls = fake
    d = _asset(tmp_path / "out", "a", cache)
    a = vc.load_asset(d)
    assert len(a.sources) == vc.MAX_SOURCES and [p.name for p in a.previews] == [
        "preview_34.png", "preview_front.png", "preview_top.png"]
    res = vc.run_one(a, "m")
    assert res["score"] == 90 and [i["kind"] for i in res["issues"]] == ["seam"]  # 未知の種類は捨てる
    c = calls[0]
    assert c["effort"] == "medium" and c["schema"] is vc.SCHEMA
    texts = [b["text"] for b in c["content"] if b["type"] == "text"]
    assert texts[0] == "元画像 0:" and "プレビュー（front）:" in texts and texts[-1] == "商品名: 商品 a"
    assert sum(b["type"] == "image" for b in c["content"]) == vc.MAX_SOURCES + 3
    meta = json.loads((d / "meta.json").read_text())
    assert meta["visual_check"]["score"] == 90 and meta["visual_check"]["model"] == "m"
    assert "visual_check_previous" not in meta
    # もう一度検証すると、前の結果は visual_check_previous に移る
    fake[0]["a"] = 60
    vc.run_one(vc.load_asset(d), "m")
    meta = json.loads((d / "meta.json").read_text())
    assert meta["visual_check"]["score"] == 60 and meta["visual_check_previous"]["score"] == 90


def test_missing_inputs(tmp_path, cache, fake):
    no_prev = vc.load_asset(_asset(tmp_path / "out", "a", cache, previews=()))
    with pytest.raises(ValueError, match="プレビュー"):
        vc.run_one(no_prev, "m")
    no_src = vc.load_asset(_asset(tmp_path / "out", "b", tmp_path / "nothing"))
    with pytest.raises(ValueError, match="元画像"):
        vc.run_one(no_src, "m")
    # --image で渡した画像は image_used から拾う
    img = _png(tmp_path / "side.png")
    a = vc.load_asset(_asset(tmp_path / "out", "c", tmp_path / "nothing", image_used=str(img)))
    assert a.sources == [img]


def test_main_lists_low_and_regressions(tmp_path, cache, fake, capsys):
    scores, _ = fake
    out = tmp_path / "out"
    for s in ("good", "low", "drop"):
        _asset(out, s, cache)
    _asset(out, "broken", cache, previews=())
    scores.update(good=95, low=50, drop=88)
    # 前回 drop は 99 点だった
    m = json.loads((out / "drop" / "meta.json").read_text())
    m["visual_check"] = {"score": 99}
    (out / "drop" / "meta.json").write_text(json.dumps(m))

    report = tmp_path / "report.json"
    assert vc.main([str(out), "--report", str(report), "--jobs", "2"]) == 0
    text = capsys.readouterr().out
    assert "3/4 件を検証" in text and "点の低いもの: low" in text and "drop（99→88）" in text
    lines = text.splitlines()
    assert lines[1].split()[:2] == ["50", "low"] and "プレビューがない" in lines[4]  # 点の低い順、失敗は最後
    rows = {r["slug"]: r for r in json.loads(report.read_text())}
    assert rows["good"]["score"] == 95 and rows["broken"]["score"] is None


def test_baseline(tmp_path, cache, fake, capsys):
    scores, _ = fake
    _asset(tmp_path / "new", "a", cache)
    _asset(tmp_path / "old", "a", cache, visual_check={"score": 92})
    scores["a"] = 70
    vc.main([str(tmp_path / "new" / "a"), "--baseline", str(tmp_path / "old")])
    assert "a（92→70）" in capsys.readouterr().out


def test_no_credentials(tmp_path, cache, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(vc, "load_dotenv", lambda: None)
    monkeypatch.setattr(vc, "request_json", lambda **k: pytest.fail("呼ばない"))
    d = _asset(tmp_path / "out", "a", cache)
    assert vc.main([str(d)]) == 0
    assert "visual_check" not in json.loads((d / "meta.json").read_text())


def test_cli_keeps_previous(tmp_path, bottle_png, blender, monkeypatch, caplog):
    """agentic-usd-gen で作り直しても前回の点は visual_check_previous に残る。--preview なしの --visual-check は省略する。"""
    from agentic_usd_gen import cli

    caplog.set_level(logging.WARNING, logger="agentic_usd_gen")  # ほかのテストがルートのレベルを上げていても拾う
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    out = tmp_path / "out"
    args = ["テスト", "--dims", "H=0.205,D=0.065", "--image", str(bottle_png), "--slug", "t", "--out", str(out),
            "--cache", str(tmp_path / "cache"), "--blender", blender, "--visual-check"]
    meta_path = out / "t" / "meta.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps({"visual_check": {"score": 81}}))
    assert cli.main(args) == 0
    meta = json.loads(meta_path.read_text())
    assert meta["visual_check_previous"]["score"] == 81 and "visual_check" not in meta
    assert "--preview" in caplog.text
    cli.main(args)  # もう一度作り直しても消えない
    assert json.loads(meta_path.read_text())["visual_check_previous"]["score"] == 81
