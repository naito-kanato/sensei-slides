"""「推論距離：測るだけ」：監査して穴を記録するが、手当てはしない（inference-distance.md 8節）。"""
from pathlib import Path

import brief
import cards
import check_outline as co
import guide
from slide_profile import measure_only

ROWS = """## 推論距離
- [3] 「A ⇒ B」｜用語｜要2｜補う前提：Aの中身｜使う所：3｜架け方：括弧で一言
- [5] 「I ⇒ J」｜論拠｜深｜補う前提：Iの背景｜使う所：なし｜架け方：原稿の ※
"""


def outline(measure: bool) -> str:
    rows = "| 聞き手のテーマへの詳しさ | 初学者 |\n" + ("| 推論距離 | 測るだけ |\n" if measure else "")
    return ("# 構成案\n\n## オプション\n\n| オプション | 今の値 |\n|---|---|\n" + rows
            + "\n聞き手の前提知識：知っている＝波／知らない＝SN 比\n\n## 構成\n")


def make_work(tmp_path: Path, measure: bool) -> Path:
    work = tmp_path / "_work" / "X"
    work.mkdir(parents=True)
    (work / "outline.md").write_text(outline(measure), encoding="utf-8")
    (work / "outline_review.md").write_text(ROWS, encoding="utf-8")
    return work


def test_option_is_read_from_table_and_memo_line():
    assert measure_only(outline(True)) and not measure_only(outline(False))
    assert measure_only("## 1. 学習者とゴール\n- 推論距離：測るだけ\n")
    assert not measure_only("")


def test_check_records_holes_without_asking_for_care(tmp_path):
    for measure, mark in ((False, "✘"), (True, "・")):
        work = make_work(tmp_path / str(measure), measure)
        text = (work / "outline.md").read_text(encoding="utf-8")
        res = {item: (m, msg) for m, item, msg in co.reasoning(work / "outline.md", text, require_review=True)}
        assert res["推論距離の手当て"][0] == mark
    assert "測るだけ" in res["推論距離の手当て"][1] and "[3]" in res["推論距離の手当て"][1]


def test_cards_get_no_deep_rows(tmp_path):
    work = make_work(tmp_path / "a", False)
    plan = work / "outline.md"
    plan.write_text(plan.read_text(encoding="utf-8").replace("| 初学者 |", "| かなり知っている |"), encoding="utf-8")
    assert cards.deep_rows(work, "outline") == {5: ["Iの背景"]}   # 直す回（かなり知っている聞き手）は渡す
    assert cards.deep_rows(make_work(tmp_path / "b", True), "outline") == {}


def test_briefs_switch_lines(tmp_path):
    fix = brief.build("直しの担当", str(make_work(tmp_path / "a", False)), "発表")
    assert "inference-distance 5" in fix and "測るだけ" not in fix and "[直す]" not in fix
    fix = brief.build("直しの担当", str(make_work(tmp_path / "b", True)), "発表")
    assert "inference-distance 5" not in fix and "測るだけ" in fix and "[測る]" not in fix
    final = brief.build("完成後のレビュー担当", str(make_work(tmp_path / "c", True)), "発表")
    assert "D1" in final and "[測る]" not in final


def test_rules_have_a_section(capsys):
    assert guide.main(["inference-distance", "8"]) == 0
    assert "測るだけ" in capsys.readouterr().out


def test_fix_brief_keeps_plan_before_fix(tmp_path, monkeypatch):
    """直しの担当の依頼文を出すと、直す前の構成案・設計メモの写しが残る（もうあれば上書きしない。--peek では作らない）。"""
    monkeypatch.chdir(tmp_path)
    work = make_work(tmp_path, False)
    before = work / "outline_直す前.md"
    brief.build("直しの担当", str(work), "発表")              # --peek（数えない）では作らない
    assert not before.exists()
    brief.build("直しの担当", str(work), "発表", count=True)
    assert before.read_text(encoding="utf-8") == outline(False)
    (work / "outline.md").write_text("直したあと", encoding="utf-8")
    brief.build("直しの担当", str(work), "発表", count=True)  # 2回目の起動：最初の直しの前の版のまま
    assert before.read_text(encoding="utf-8") == outline(False)
    brief.build("レビュー担当", str(work), "発表", count=True)  # ほかの担当では作らない
    assert not (work / "memo_直す前.md").exists()


def test_fix_brief_keeps_memo_for_course(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    work = tmp_path / "_work" / "X講座_01"
    work.mkdir(parents=True)
    (work / "memo.md").write_text("## 1. 学習者とゴール\n", encoding="utf-8")
    brief.build("直しの担当", str(work), count=True)
    assert (work / "memo_直す前.md").read_text(encoding="utf-8") == "## 1. 学習者とゴール\n"
    assert not (work / "outline_直す前.md").exists()
