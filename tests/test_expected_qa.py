"""発表の想定質問：構成案の「## 想定質問」の表（4問）・役割「想定質問」の枚（1枚に2組）・骨組みとカード・部品 s.qa_pairs。"""
import re
import shutil

import pytest

import scaffold
import structures
from zemi import Deck


@pytest.fixture
def outline(root):
    return (root / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")


def marks(res):
    return {item: m for m, item, _ in res}


def test_example_outline_has_four_questions(outline):
    items = structures.expected_qa(outline)
    assert [k for k, *_ in items] == ["Q1", "Q2", "Q3", "Q4"]
    assert all(back for *_, back in items)
    assert marks(structures.check_expected_qa(outline))["想定質問"] == "✔"


def test_missing_or_short_section_is_flagged(outline):
    no_sec = re.sub(r"^## 想定質問.*?(?=^## )", "", outline, flags=re.S | re.M)
    no_sec = re.sub(r"^\| 1[56] .*\n", "", no_sec, flags=re.M)
    res = structures.check_expected_qa(no_sec)
    assert marks(res)["想定質問"] == "△" and "表が無い" in res[0][2]
    three = re.sub(r"^\| Q4 .*\n", "", outline, flags=re.M)
    res = structures.check_expected_qa(three)
    assert marks(res)["想定質問"] == "△" and "3問" in res[0][2]
    assert structures.check_expected_qa(outline, "memo") == []        # 講座の設計メモには当てない（確認問題がある）


def test_scaffold_fills_pairs_and_cards(root, tmp_path):
    for f in ("outline.md", "outline_review.md"):
        shutil.copy2(root / "examples" / "zemi" / f, tmp_path / f)
    assert scaffold.main([str(tmp_path)]) == 0
    b = (tmp_path / "build.py").read_text(encoding="utf-8")
    assert b.count("s.qa_pairs([") == 2 and '("Q1", "雑音が偶然そろっただけではないのか"' in b and '("Q4",' in b
    compile(b, "build.py", "exec")
    c = (tmp_path / "cards" / "15.md").read_text(encoding="utf-8")
    assert "戻る枚：13枚目（青帯「雑音で偶然起きる頻度は、20万年に1回未満」）" in c
    assert "戻る枚はスライドには書かない" in c


def test_qa_pairs_places_two_sets(tmp_path):
    deck = Deck(workdir=tmp_path / "build", valign="top")
    s = deck.slide("質疑応答")
    s.heading("想定質問")
    s.at(1.0, 1.9)
    box = s.qa_pairs([("Q1", "質問の1つ目", "回答の1行目\n2行目"), ("Q2", "質問の2つ目", "回答")])
    shapes = [sh for sh in s.slide.shapes if sh.has_text_frame]
    qs = [sh for sh in shapes if sh.name == "想定質問"]
    ans = [sh for sh in shapes if sh.name == "回答"]
    assert len(qs) == 2 and len(ans) == 2
    assert qs[1].top > ans[0].top + ans[0].height                    # 2組目は1組目の回答の下
    assert ans[0].text_frame.text.startswith("⇒ 回答の1行目")
    assert box.h > 0
