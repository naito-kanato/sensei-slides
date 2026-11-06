"""図の案とスライドの図の突き合わせ（figplan.py）と、流れ図の上限。"""
from pptx import Presentation

import figplan as fp


def test_planned_kind():
    assert fp.planned_kind("学習の2段階の流れ図") == "流れ図"
    assert fp.planned_kind("表：推定値と 90% の範囲") == "表"
    assert fp.planned_kind("経路図に所要時間・休息・駐車場所") == "図"
    assert fp.planned_kind("—") is None


def test_slide_numbers_and_limit():
    assert fp.slide_numbers("8–9") == [8, 9] and fp.slide_numbers("12") == [12]
    assert [fp.flow_limit(n) for n in (5, 10, 12, 16)] == [2, 2, 3, 4]      # 本文4枚に1枚、最低2枚


def test_course_example_follows_its_plan(built):
    work = built / "examples" / "course" / "_work" / "AI活用講座_01"
    prs = Presentation(built / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx")
    plan = fp.plan_from_text((work / "memo.md").read_text(encoding="utf-8"), "memo")
    assert fp.actual_kinds(prs.slides[3]) == {"流れ図"}                     # 4枚目：学習の2段階
    assert "図" in fp.actual_kinds(prs.slides[1])                          # 2枚目：棒グラフ
    assert fp.mismatches(prs, plan, skip={1, 12, 13, 14, 15}) == []
    plan[2] = "—"                                                           # 案から図を消すと…（図は残っていてよい）
    plan[4] = "—"                                                           # 案に無い流れ図は見つかる
    assert fp.mismatches(prs, plan, skip={1, 12, 13, 14, 15}) == [(4, "図の案に無い流れ図")]


def test_too_many_flows_need_a_reason():
    assert fp.flow_check(8, 11, "", "設計メモ")[0] is None                   # 上限 2枚を超える
    assert fp.flow_check(8, 11, "流れ図の理由：手順の講座", "設計メモ")[0] == "✔"
    assert fp.flow_check(2, 10, "", "設計メモ")[0] == "✔"
