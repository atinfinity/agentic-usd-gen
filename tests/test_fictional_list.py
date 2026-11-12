"""agentic-usd-gen-fictional --list（slug・分類・形状・品名の一覧）。"""

from __future__ import annotations

import pytest

from agentic_usd_gen import cli, fictional
from agentic_usd_gen.fictional import listing
from agentic_usd_gen.fictional.registry import PRODUCTS


def test_index_has_every_definition_once_in_order():
    lines = listing.INDEX.read_text(encoding="utf-8").splitlines()
    assert all(len(line.split("\t")) == 4 for line in lines)
    assert [line.split("\t")[0] for line in lines] == list(PRODUCTS), f"作り直してください: {listing.REFRESH}"
    assert all(all(col.strip() for col in row) for row in listing.load().values())


def test_index_matches_the_definitions():
    # 全点を呼ぶと絵柄を描くので数分かかる。ここでは一定の間隔で抜き出して確かめる（作るときにも 1 点ずつ確かめている）
    sample = list(PRODUCTS)[::40]
    index = listing.load()
    assert listing.build(sample) == [index[s] for s in sample], f"作り直してください: {listing.REFRESH}"


def test_list_prints_one_line_each_and_builds_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "main", lambda *a, **k: pytest.fail("--list は何も作らない"))
    assert fictional.main(["--list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert [line.split()[0] for line in out] == list(PRODUCTS)
    row = next(line for line in out if line.startswith("soda_pet_500ml "))
    assert row.split()[1:3] == ["beverage", "revolve"] and listing.load()["soda_pet_500ml"].name in row
    assert list(tmp_path.iterdir()) == []


def test_list_filters_by_every_word(capsys):
    assert fictional.main(["--list", "POUCH", "food"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out and all("pouch" in line and "food" in line for line in out)  # 語はどの列にあってもよい
    assert len(out) < len(PRODUCTS)
    assert fictional.main(["--list", "そんな物はない"]) == 0
    assert capsys.readouterr().out == ""


def test_rows_fall_back_to_the_definition_when_the_index_is_behind(monkeypatch):
    index = listing.load()
    last = list(PRODUCTS)[-1]
    monkeypatch.setattr(listing, "load", lambda: {s: r for s, r in index.items() if s != last})
    assert listing.rows()[-1] == index[last]


def test_help_points_to_list_instead_of_naming_every_slug(capsys):
    with pytest.raises(SystemExit):
        fictional.main(["--help"])
    text = capsys.readouterr().out
    assert "--list" in text and "cup_noodle_tall" not in text
