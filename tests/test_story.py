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
    assert marks(outline) == {"問いの深め": "✔", "話の筋": "✔", "前の枚から": "✔", "話の型": "✔", "型と図": "✔"}


def test_missing_story_blocks(outline):
    text = re.sub(r"## 話の筋.*?(?=## 構成)", "", outline, flags=re.S)
    assert marks(text)["話の筋"] == "✘"


def test_question_must_be_a_question(outline):
    text = outline.replace("ないと言えるか？", "ないと言えるか")
    assert marks(text)["話の筋"] == "△"


def test_answer_must_come_late(outline):
    text = outline.replace("BH連星の合体 | 13 |", "BH連星の合体 | 5 |")
    assert marks(text)["話の筋"] == "△"


def test_long_and_run_and_no_but_warn(outline):
    text = re.sub(r"\| (しかし|だから)（[^）]*） \|", "| そして（並べる） |", outline)
    res = {i: (m, t) for m, i, t in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}
    mark, msg = res["前の枚から"]
    assert mark == "✘" and "「そして」が続く" in msg and "「しかし」が1つも無い" in msg


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
    assert mark == ("✘" if "「そして」が続く" in msg else "△") and "出しっぱなし" in msg


def test_split_link():
    assert story.split_link("しかし（壁）") == ("しかし", "壁")
    assert story.split_link("だから:手段") == ("だから", "手段")
    assert story.split_link("—") == ("—", "")


def test_beat_figs_cover_every_arc():
    """全部の型の拍に、おすすめの図の目的がある（拍と同じ数・選択肢の目的だけ）。"""
    import figplan
    for arc in story.ARCS:
        figs = story.BEAT_FIGS[arc[0]]
        assert len(figs) == len(arc[4]), arc[0]
        assert all(p in figplan.PURPOSE_NAMES for t in figs for p in t), arc[0]
    assert "模式図" in story.figs_table("今の形から由来へ")


def test_fig_check_no_schema(outline):
    """仕組みの拍がある型で、模式図・資料の図が1枚も無ければ △。拍に合わない図も △。"""
    import figplan
    text = re.sub(r"仕組み：(模式図|資料の図)", "観点：表", outline)
    text = re.sub(r"実物：資料の図", "観点：表", text)
    res = {item: (mark, d) for mark, item, d in story.check(text, "outline", story.body_numbers(text, "outline"), "構成案")}
    assert res["型と図"][0] == "✘" and ("模式図が1枚も無い" in res["型と図"][1] or "型の拍に合わない図" in res["型と図"][1])


def test_figs_table_shows_pitfalls():
    """--figs は型ごとの陥りやすいミスも見せる。制度・由来の型では、要件を表に並べずに判定の流れ図を、とすすめる。"""
    t = story.figs_table("今の形から由来へ")
    assert "陥りやすいミス" in t and "判定の流れ図" in t
    assert all(story.ARC_PITFALLS.get(a[0]) for a in story.ARCS)   # どの型にもミスの例がある


def test_many_tables_without_decision_warn(outline):
    """判定の拍がある型で、表が3枚以上あって判定の流れ図が無ければ △。"""
    text = re.sub(r"\| (仕組み|比べる|実物|違い|推移|判定)：[^|]*\|", "| 観点：表：要件の一覧 |", outline)   # 見本の判定の流れ図（9枚目）も表に
    body = story.body_numbers(text, "outline")
    res = story.fig_check(text, "outline", body)
    assert not any("判定の流れ図が無い" in d for _, _, d in res)        # 論文紹介（方法から）には判定の拍が無い
    text = re.sub(r"^話の型：.*$", "話の型：論文紹介（問題から）", text, flags=re.M)
    res = story.fig_check(text, "outline", body)
    assert res and res[0][0] == "✘" and "判定の流れ図が無い" in res[0][2]
