"""cards.py：確認問題と解答のカード・質問回答のカード・入れる量の上限。"""
import shutil

import pytest

import cards
import scaffold
import structures


@pytest.fixture
def zemi(root, tmp_path):
    w = tmp_path / "重力波"
    w.mkdir()
    for f in ("outline.md", "outline_review.md", "notes.md"):
        shutil.copy2(root / "examples" / "zemi" / f, w / f)
    return w


def test_quiz_links_and_cards(root, tmp_path):
    src = root / "examples" / "course" / "_work" / "AI活用講座_01"
    w = tmp_path / "AI活用講座_01"
    w.mkdir()
    for f in ("memo.md", "memo_review.md"):
        shutil.copy2(src / f, w / f)
    text = (w / "memo.md").read_text(encoding="utf-8")
    assert dict((i, m) for m, i, _ in structures.quiz_links(text))["確認問題のひもづけ"] == "✔"
    bad = text.replace("〔要素：題名・著者・DOI で検索／原文を開いて中身を確かめる／見つからなければ要確認〕", "")
    assert dict((i, m) for m, i, _ in structures.quiz_links(bad))["確認問題のひもづけ"] == "△"
    assert scaffold.main([str(w)]) == 0
    c = (w / "cards" / "14.md").read_text(encoding="utf-8")
    assert "削ってはいけない要素" in c and "2枚目で見たとおり" in c


def test_answer_cards_and_inline_limit(zemi):
    a = zemi / "質問回答"
    a.mkdir()
    long_note = "長い原稿。" * 600
    notes = (zemi / "notes.md").read_text(encoding="utf-8").replace("## 11\n", "## 11\n" + long_note + "\n", 1)
    (zemi / "notes.md").write_text(notes, encoding="utf-8")
    (a / "answers.md").write_text(
        "# 質問回答：重力波の初観測\n\n## 構成\n\n"
        "| # | ●見出し | コメント | 元の枚 | 青帯（結論） | 図で見せるもの | 本文の要点 | ノートへ | 本文の形 | 役割 |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | 表紙 | — | — | — | — | 題／質問への回答 | — | — | 表紙 |\n"
        "| 2 | 中性子星ではだめな理由 | #2 中性子星2つではなぜだめ？ | 11 | 中性子星2つでは質量が足りない | 棒2本 | 必要：70 M⊙ 以上〔II. Observation〕 / 中性子星：数倍まで〔資料外〕 / 結論 | — | ラベル | 本文 |\n",
        encoding="utf-8")
    assert scaffold.main([str(a)]) == 0
    c = (a / "cards" / "02.md").read_text(encoding="utf-8")
    assert "#2 中性子星2つではなぜだめ" in c and "元の枚：11枚目" in c and "{c:← 11枚目" in c
    assert "続きは元の notes.md" in c and c.count("長い原稿。") <= cards.INLINE_MAX // 5 + 1


def test_quiz_card_ids_not_doubled(root, tmp_path):
    """見出し（1-1〜1-3）と要点の両方に番号があっても、カードの問いは1-1・1-2・1-3を1回ずつ。"""
    import re
    src = root / "examples" / "course" / "_work" / "AI活用講座_01"
    w = tmp_path / "AI活用講座_01"
    w.mkdir()
    for f in ("memo.md", "memo_review.md"):
        shutil.copy2(src / f, w / f)
    assert scaffold.main([str(w)]) == 0
    for c in (w / "cards").glob("[0-9][0-9].md"):
        heads = re.findall(r"^## (\d+-\d+)", c.read_text(encoding="utf-8"), re.M)
        assert len(heads) == len(set(heads)), (c.name, heads)
