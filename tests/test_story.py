"""話の筋（story.py）：筋の表と「前の枚から」の列の確認。"""
import re

import pytest

import story


@pytest.fixture
def outline(root):
    return (root / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")


def marks(text):
    return {item: mark for mark, item, _ in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}


def test_example_has_story(outline):
    assert marks(outline) == {"話の筋": "✔", "前の枚から": "✔"}


def test_missing_story_blocks(outline):
    text = re.sub(r"## 話の筋.*?(?=## 構成)", "", outline, flags=re.S)
    assert marks(text)["話の筋"] == "✘"


def test_question_must_be_a_question(outline):
    text = outline.replace("とらえられるか？", "とらえられるか")
    assert marks(text)["話の筋"] == "△"


def test_answer_must_come_late(outline):
    text = outline.replace("20万年に1回未満と示した | 13 |", "20万年に1回未満と示した | 5 |")
    assert marks(text)["話の筋"] == "△"


def test_long_and_run_and_no_but_warn(outline):
    text = re.sub(r"\| (しかし|だから)（[^）]*） \|", "| そして（並べる） |", outline)
    res = {i: (m, t) for m, i, t in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}
    mark, msg = res["前の枚から"]
    assert mark == "△" and "「そして」が続く" in msg and "「しかし」が1つも無い" in msg


def test_reason_allows_and_run(outline):
    """5〜9枚目を「そして」が5つ続く形にしても、理由が書いてあれば ✔。"""
    text = outline.replace("| だから（手段） |", "| そして（次へ） |").replace("| しかし（壁） |", "| そして（並べる） |")
    assert "そして」が続く" in link_msg(text)[1]
    assert marks(text + "\nつなぎの理由：装置の説明を順に並べる\n")["前の枚から"] == "✔"


def link_msg(text):
    return {i: (m, t) for m, i, t in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}["前の枚から"]


def test_kind_is_required(outline):
    mark, msg = link_msg(outline.replace("| しかし（壁） |", "| しかし |"))
    assert mark == "△" and "種類が無い" in msg


def test_unknown_kind_warns(outline):
    mark, msg = link_msg(outline.replace("| しかし（壁） |", "| しかし（驚き） |"))
    assert mark == "△" and "驚き" in msg


def test_open_doubt_warns(outline):
    """しかし（疑い）のあと、最後まで「だから」が無いと出しっぱなし。"""
    mark, msg = link_msg(outline.replace("| だから（帰結） |", "| そして（次へ） |"))
    assert mark == "△" and "出しっぱなし" in msg


def test_split_link():
    assert story.split_link("しかし（壁）") == ("しかし", "壁")
    assert story.split_link("だから:手段") == ("だから", "手段")
    assert story.split_link("—") == ("—", "")
